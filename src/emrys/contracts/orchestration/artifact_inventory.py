"""Run-bound artifact-layout expansion and validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    PROCESSING_STEP_IDS,
    AnalysisRevision,
)


_PROCESSING_PRODUCERS = {
    "00a": Path("stages/star_index/step_00a_build_star_index.sh"),
    "00b": Path("stages/gtf_to_bed12/converter.py"),
    "00c": Path("stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh"),
    "01": Path("stages/star_alignment/step_01_star_align.sh"),
    "02": Path("stages/canonical_bam/step_02_sort_index_bam.sh"),
    "02b": Path("evidence/canonical_bam_qc/step_02b_bam_qc.sh"),
    "03": Path(
        "evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh"
    ),
    "04": Path("stages/duplicate_marking/step_04_mark_duplicates.sh"),
    "05": Path("stages/split_n_cigar/step_05_split_n_cigar_reads.sh"),
    "06": Path("stages/mechanical_orientation/producer.py"),
    "07": Path("stages/partitioned_cohort_mpileup/producer.py"),
    "08": Path("stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R"),
}


def _processing_profile(source_root: Path) -> Mapping[str, Any]:
    return orchestration_contracts.load_record(
        source_root / "workflow/contracts/local_cmh_v2.json", "profile"
    )


def processing_tasks(source_root: Path) -> tuple[Mapping[str, Any], ...]:
    """Read fixed processing tasks from the admitted installed package."""
    profile = _processing_profile(source_root)
    return tuple(
        MappingProxyType(
            {
                **task,
                "producer_path": _PROCESSING_PRODUCERS[task["step_id"]],
                "predecessors": tuple(
                    edge["producer"]
                    for edge in profile["direct_edges"]
                    if edge["consumer"] == task["machine_key"]
                ),
            }
        )
        for task in profile["owner_tasks"]
    )


def processing_artifact_templates(source_root: Path) -> tuple[Mapping[str, Any], ...]:
    """Read base artifact ownership independently of a supplied Run profile."""
    return tuple(
        MappingProxyType(template)
        for template in _processing_profile(source_root)["artifact_templates"]
    )


def validate_processing_graph(profile: Mapping[str, Any], source_root: Path) -> None:
    """New Runs must describe the processing dependencies the backend executes."""
    tasks = processing_tasks(source_root)
    owners = {task["machine_key"] for task in tasks}
    expected = {
        (producer, task["machine_key"])
        for task in tasks
        for producer in task["predecessors"]
    }
    observed = {
        (edge["producer"], edge["consumer"])
        for edge in profile["direct_edges"]
        if edge["consumer"] in owners
    }
    if observed != expected:
        raise orchestration_contracts.ContractValidationError(
            "Processing dependencies do not match the supported processing graph"
        )


def _template_contexts(
    selector: str,
    source: Mapping[str, Any],
    analysis: AnalysisRevision,
) -> tuple[dict[str, str], ...]:
    reference_id = analysis.scope_id("reference")
    reference_fasta_path = str(source["reference"]["fasta"]["path"])
    reference_path = Path(reference_fasta_path)
    reference_dict_path = str(reference_path.with_name(f"{reference_path.stem}.dict"))
    cohort_id = analysis.scope_id("cohort")
    analysis_id = analysis.scope_id("analysis")
    shared = {
        "run_id": str(source["run_id"]),
        "reference_id": reference_id,
        "reference_fasta_path": reference_fasta_path,
        "reference_dict_path": reference_dict_path,
        "cohort_id": cohort_id,
        "analysis_id": analysis_id,
    }
    if selector == "reference":
        return ({**shared, "scope_id": reference_id},)
    if selector == "samples":
        return tuple(
            {
                **shared,
                "sample_id": str(row["sample_id"]),
                "scope_id": str(row["sample_id"]),
            }
            for row in source["samples"]["rows"]
        )
    if selector == "partitions":
        return tuple(
            {
                **shared,
                "partition_id": str(row["partition_id"]),
                "scope_id": analysis.scope_id(
                    "cohort_partition", str(row["partition_id"])
                ),
            }
            for row in source["partitions"]["rows"]
        )
    if selector == "cohort":
        return ({**shared, "scope_id": cohort_id},)
    if selector == "analysis":
        return ({**shared, "scope_id": analysis_id},)
    raise orchestration_contracts.ContractValidationError(
        f"Unsupported profile scope_selector: {selector}"
    )


def _expand_template(value: str, context: Mapping[str, str], label: str) -> str:
    try:
        expanded = value.format_map(dict(context))
    except (KeyError, ValueError) as exc:
        raise orchestration_contracts.ContractValidationError(
            f"Could not expand {label} {value!r}: {exc}"
        ) from exc
    if "{" in expanded or "}" in expanded:
        raise orchestration_contracts.ContractValidationError(
            f"Unresolved template syntax remains in {label}: {expanded}"
        )
    return expanded


def _validate_rows(rows: Sequence[Mapping[str, str]]) -> None:
    """Apply the artifact inventory's pure row semantics before serialization."""

    if not rows:
        raise orchestration_contracts.ContractValidationError(
            "Profile projects no artifact inventory rows"
        )
    seen_values = {"artifact_id": set(), "source_path": set()}
    closed_scopes: set[tuple[str, str, str]] = set()
    active_scope: tuple[str, str, str] | None = None
    for row in rows:
        for field in artifact_contracts.INVENTORY_HEADER[:-2]:
            if not artifact_contracts.SAFE_ID_RE.fullmatch(row[field]):
                raise orchestration_contracts.ContractValidationError(
                    f"Projected inventory {field} is not a safe ID: {row[field]}"
                )
        artifact_contracts.validate_resolved_path(
            row["source_path"], "Projected inventory source_path"
        )
        for field, seen in seen_values.items():
            value = row[field]
            if value in seen:
                raise orchestration_contracts.ContractValidationError(
                    f"Projected artifact inventory contains duplicate {field} values"
                )
            seen.add(value)
        scope = artifact_contracts.scope_key(dict(row))
        if active_scope is None:
            active_scope = scope
        elif scope != active_scope:
            closed_scopes.add(active_scope)
            if scope in closed_scopes:
                raise orchestration_contracts.ContractValidationError(
                    "Projected artifact inventory reopens logical scope: "
                    + "/".join(scope)
                )
            active_scope = scope


def project_rows(
    source: Mapping[str, Any],
    profile: Mapping[str, Any],
    analysis: AnalysisRevision,
    processing_source_root: Path | None = None,
    processing_artifact_paths: Mapping[tuple[str, str, str], Path] | None = None,
) -> tuple[dict[str, str], ...]:
    """Expand the fixed artifact templates into their admitted inventory rows."""

    rows: list[dict[str, str]] = []
    expected_scope = {
        "reference": "reference",
        "samples": "sample",
        "partitions": "cohort_partition",
        "cohort": "cohort",
        "analysis": "analysis",
    }
    templates_by_selector: dict[str, list[Mapping[str, Any]]] = {}
    selector_order: list[str] = []
    for template in profile["artifact_templates"]:
        selector = str(template["scope_selector"])
        if selector not in templates_by_selector:
            templates_by_selector[selector] = []
            selector_order.append(selector)
        templates_by_selector[selector].append(template)

    for selector in selector_order:
        for context in _template_contexts(selector, source, analysis):
            for template in templates_by_selector[selector]:
                scope_type = str(template["scope_type"])
                if expected_scope[selector] != scope_type:
                    raise orchestration_contracts.ContractValidationError(
                        "Artifact template scope_selector/scope_type mismatch: "
                        f"{selector}/{scope_type}"
                    )
                artifact_id = _expand_template(
                    str(template["artifact_id_template"]),
                    context,
                    "artifact_id_template",
                )
                source_path = _expand_template(
                    str(template["source_path_template"]),
                    context,
                    "source_path_template",
                )
                source_artifact = (
                    None
                    if processing_artifact_paths is None
                    else processing_artifact_paths.get(
                        (
                            str(template["step_id"]),
                            context["scope_id"],
                            str(template["adapter"]),
                        )
                    )
                )
                if source_artifact is not None:
                    source_path = str(source_artifact)
                if (
                    source_artifact is None
                    and processing_source_root is not None
                    and str(template["step_id"]) in PROCESSING_STEP_IDS
                    and not Path(source_path).is_absolute()
                ):
                    source_path = str(processing_source_root / source_path)
                rows.append(
                    {
                        "artifact_id": artifact_id,
                        "step_id": str(template["step_id"]),
                        "scope_type": scope_type,
                        "scope_id": context["scope_id"],
                        "adapter": str(template["adapter"]),
                        "source_path": source_path,
                        "required": "true" if template["required"] else "false",
                    }
                )

    _validate_rows(rows)
    return tuple(rows)
