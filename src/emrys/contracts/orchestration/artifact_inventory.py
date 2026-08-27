"""Run-bound expansion and validation of artifact-inventory adapters."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    EXECUTION_PROJECTION_SCHEMA_VERSION,
    analysis_revision_from_execution_fields,
)


def _template_contexts(
    selector: str,
    execution: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    successor = execution.get("schema_version") == EXECUTION_PROJECTION_SCHEMA_VERSION
    analysis_revision = (
        analysis_revision_from_execution_fields(execution) if successor else None
    )
    reference_id = (
        analysis_revision.scope_id("reference")
        if analysis_revision is not None
        else str(execution["reference"]["reference_id"])
    )
    reference_fasta_path = str(execution["reference"]["fasta"]["path"])
    reference_path = Path(reference_fasta_path)
    reference_dict_path = str(reference_path.with_name(f"{reference_path.stem}.dict"))
    cohort_id = (
        analysis_revision.scope_id("cohort")
        if analysis_revision is not None
        else str(execution["analysis"]["cohort_id"])
    )
    analysis_id = (
        analysis_revision.scope_id("analysis")
        if analysis_revision is not None
        else str(execution["analysis"]["primary_analysis_id"])
    )
    shared = {
        "run_id": str(execution["run_id"]),
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
            for row in execution["samples"]["rows"]
        )
    if selector == "partitions":
        return tuple(
            {
                **shared,
                "partition_id": str(row["partition_id"]),
                "scope_id": (
                    analysis_revision.scope_id(
                        "cohort_partition", str(row["partition_id"])
                    )
                    if analysis_revision is not None
                    else f"{cohort_id}__{row['partition_id']}"
                ),
            }
            for row in execution["partitions"]["rows"]
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
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
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
        for context in _template_contexts(selector, execution):
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
