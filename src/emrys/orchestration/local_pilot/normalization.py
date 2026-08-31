"""Read-only Project admission for the current local CMH implementation."""

from __future__ import annotations

import glob
import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
    analysis_revision_from_execution_fields,
)
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.contracts.scientific_evidence import step08
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes, sha256_with_identity


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    return orchestration_contracts.load_json_object_bytes(data, label)


@dataclass(frozen=True, slots=True)
class AnalysisAdmission:
    """One selected, immutable Analysis admitted from a mutable Project."""

    name: str
    source_path: Path
    source_bytes: bytes
    _profile_bytes: bytes
    revision: AnalysisRevision
    _workflow_input_bytes: bytes
    _authored_path_bytes: bytes
    evidence_label: str | None

    @property
    def profile(self) -> dict[str, Any]:
        """Return the fixed workflow profile used to admit this Analysis."""

        return _json_object(self._profile_bytes, "Analysis profile")

    @property
    def workflow_inputs(self) -> dict[str, Any]:
        """Return the private backend projection; it is never Run authority."""

        return _json_object(self._workflow_input_bytes, "Analysis workflow inputs")

    @property
    def authored_paths(self) -> dict[str, Any]:
        """Return source spellings retained only for Attempt-v1 evidence."""

        return _json_object(self._authored_path_bytes, "Analysis authored paths")


@dataclass(frozen=True, slots=True)
class ProjectAdmission:
    """Immutable admission snapshot of one scientist-authored Project revision."""

    source_path: Path
    source_bytes: bytes
    analyses: tuple[AnalysisAdmission, ...]

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.source_bytes).hexdigest()

    def select_analysis(
        self,
        name: str | None = None,
        *,
        expected_revision: AnalysisRevision | None = None,
    ) -> AnalysisAdmission:
        """Select new work by name or resume an already-bound revision."""

        if expected_revision is not None:
            matches = tuple(
                analysis
                for analysis in self.analyses
                if analysis.revision.canonical_bytes
                == expected_revision.canonical_bytes
            )
            if not matches:
                raise orchestration_contracts.ContractValidationError(
                    "Project contains no Analysis matching the immutable Run"
                )
            return next(
                (analysis for analysis in matches if analysis.name == name),
                matches[0],
            )

        if name is None and len(self.analyses) == 1:
            return self.analyses[0]
        choices = ", ".join(analysis.name for analysis in self.analyses)
        if name is None:
            raise orchestration_contracts.ContractValidationError(
                "Project defines multiple Analyses; select one with --analysis: "
                + choices
            )
        match = next((item for item in self.analyses if item.name == name), None)
        if match is not None:
            return match
        raise orchestration_contracts.ContractValidationError(
            f"Unknown Analysis {name!r}; choose one of: {choices}"
        )


def _regular_file(path: Path, label: str) -> tuple[Path, bytes]:
    admitted_path = Path(os.path.abspath(path))
    try:
        return admitted_path, read_bytes(admitted_path, label)
    except ValidationError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc


def _regular_file_snapshot(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    """Admit one large input by streaming its identity without retaining bytes."""

    admitted_path = Path(os.path.abspath(path))
    try:
        digest, state = sha256_with_identity(admitted_path, label)
    except ValidationError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc
    return admitted_path, {
        "path": str(admitted_path),
        "size_bytes": state.st_size,
        "sha256": digest,
    }


def validate_authored_path(value: str, label: str) -> None:
    """Reject path spellings that Project authors cannot declare literally."""

    if not value or value != value.strip():
        raise orchestration_contracts.ContractValidationError(
            f"{label} must be a nonempty path without surrounding whitespace: {value}"
        )
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise orchestration_contracts.ContractValidationError(
            f"{label} contains an invalid control character"
        )
    if (
        value.startswith("~")
        or "$" in value
        or "{" in value
        or "}" in value
        or "\\" in value
        or glob.has_magic(value)
    ):
        raise orchestration_contracts.ContractValidationError(
            f"{label} must be an explicit normalized path without interpolation, "
            f"templates, or globs: {value}"
        )
    if "//" in value:
        raise orchestration_contracts.ContractValidationError(
            f"{label} must not contain redundant path separators: {value}"
        )
    candidate = Path(value)
    if value in {".", ".."} or any(part in {".", ".."} for part in candidate.parts):
        raise orchestration_contracts.ContractValidationError(
            f"{label} must not contain '.' or '..' path components: {value}"
        )


def _resolve_authored_path(value: str, base: Path, label: str) -> tuple[Path, bytes]:
    validate_authored_path(value, label)
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return _regular_file(candidate, label)


def _resolve_authored_snapshot(
    value: str,
    base: Path,
    label: str,
) -> tuple[Path, dict[str, Any]]:
    validate_authored_path(value, label)
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return _regular_file_snapshot(candidate, label)


def _snapshot(path: Path, data: bytes) -> dict[str, Any]:
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _load_profile(profile: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(profile, Mapping):
        value = dict(profile)
    else:
        authored_profile = os.fspath(profile)
        validate_authored_path(authored_profile, "Profile")
        profile_path = Path(authored_profile)
        if not profile_path.is_absolute():
            profile_path = Path.cwd() / profile_path
        admitted_path, profile_data = _regular_file(profile_path, "Profile")
        value = orchestration_contracts.load_json_object_bytes(
            profile_data,
            f"profile JSON {admitted_path}",
        )
    orchestration_contracts.validate_record("profile", value)
    return value


def _normalize_samples(
    manifest_path: Path,
    manifest_data: bytes,
    project_dir: Path,
) -> dict[str, Any]:
    try:
        table, _, rows = step08.validate_sample_manifest_bytes(
            manifest_data, manifest_path
        )
    except step08.ContractError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        r1_path, r1_snapshot = _resolve_authored_snapshot(
            row["r1_fastq"], project_dir, f"Sample manifest row {index} R1 FASTQ"
        )
        r2_path, r2_snapshot = _resolve_authored_snapshot(
            row["r2_fastq"], project_dir, f"Sample manifest row {index} R2 FASTQ"
        )
        if r1_path == r2_path:
            raise orchestration_contracts.ContractValidationError(
                f"Sample {row['sample_id']} R1 and R2 FASTQs must be distinct"
            )
        if r1_path.name.endswith(".gz") != r2_path.name.endswith(".gz"):
            raise orchestration_contracts.ContractValidationError(
                f"Sample {row['sample_id']} R1 and R2 FASTQs must use the same "
                "compression mode"
            )
        normalized = {
            "sample_id": row["sample_id"],
            "condition": row["condition"],
            "replicate": row["replicate"],
            "strandedness": row["strandedness"],
            "r1_fastq": r1_snapshot,
            "r2_fastq": r2_snapshot,
        }
        if "notes" in table.header:
            normalized["notes"] = row["notes"]
        normalized_rows.append(normalized)
    return {
        "manifest": _snapshot(manifest_path, manifest_data),
        "rows": normalized_rows,
    }


def _normalize_partitions(
    manifest_path: Path,
    manifest_data: bytes,
) -> dict[str, Any]:
    try:
        table = step08.validate_partition_manifest_bytes(manifest_data, manifest_path)
    except step08.ContractError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(table.rows, start=2):
        selector_value = row["selector_value"]
        selector_file = None
        if row["selector_type"] == "regions_file":
            path, selector_file = _resolve_authored_snapshot(
                selector_value,
                manifest_path.parent,
                f"Partition manifest row {index} regions file",
            )
            selector_value = str(path)
        normalized_rows.append(
            {
                "partition_id": row["partition_id"],
                "selector_type": row["selector_type"],
                "selector_value": selector_value,
                "selector_file": selector_file,
            }
        )
    return {
        "manifest": _snapshot(manifest_path, manifest_data),
        "rows": normalized_rows,
    }


def _admit_project_data(
    project_path: str | Path,
    project_data: bytes,
    profile: Mapping[str, Any] | str | Path,
    *,
    allow_legacy: bool = False,
) -> ProjectAdmission:
    """Admit prepared Project bytes at their intended canonical location."""

    resolved_project = Path(os.path.abspath(project_path))
    definition = orchestration_contracts.load_yaml_object_bytes(
        project_data,
        f"Project YAML {resolved_project}",
    )
    profile_record = _load_profile(profile)
    profile_bytes = orchestration_contracts.canonical_json_bytes(profile_record)
    profile_identity = {
        key: profile_record[key] for key in ("profile_id", "profile_version")
    }
    profile_identity["profile_sha256"] = orchestration_contracts.canonical_sha256(
        profile_record
    )
    project_dir = resolved_project.parent
    if definition.get("schema_version") == "emrys.request.v3":
        if not allow_legacy:
            raise orchestration_contracts.ContractValidationError(
                "emrys.request.v3 is historical; create an emrys.project.v1 Project"
            )
        orchestration_contracts.validate_record("request", definition)
        expected_profile = (
            f"{profile_record['profile_id']}.{profile_record['profile_version']}"
        )
        if definition["profile"] != expected_profile:
            raise orchestration_contracts.ContractValidationError(
                f"Historical Project profile {definition['profile']} does not match "
                f"{expected_profile}"
            )
        sample_manifest = definition["sample_manifest"]
        reference_definition = definition["reference"]
        analysis_specs = (
            (
                str(definition.get("label") or definition["analysis"]["id"]),
                definition["partition_manifest"],
                definition["analysis"],
                {
                    "reference": definition["reference"]["id"],
                    "cohort": definition["cohort_id"],
                    "analysis": definition["analysis"]["id"],
                },
                definition.get("label"),
            ),
        )
    else:
        orchestration_contracts.validate_record("project", definition)
        sample_manifest = definition["dataset"]["samples"]
        reference_definition = definition["reference"]
        analysis_specs = tuple(
            (name, item["partitions"], item, None, name)
            for name, item in sorted(definition["analyses"].items())
        )

    sample_path, sample_data = _resolve_authored_path(
        sample_manifest, project_dir, "Sample manifest"
    )
    samples = _normalize_samples(sample_path, sample_data, project_dir)

    _fasta_path, fasta_snapshot = _resolve_authored_snapshot(
        reference_definition["fasta"], project_dir, "Reference FASTA"
    )
    _gtf_path, gtf_snapshot = _resolve_authored_snapshot(
        reference_definition["gtf"], project_dir, "Reference GTF"
    )
    reference_input = {
        "fasta": fasta_snapshot,
        "gtf": gtf_snapshot,
        "star_index": dict(reference_definition["star_index"]),
    }
    partition_cache: dict[str, dict[str, Any]] = {}
    analyses: list[AnalysisAdmission] = []
    for (
        name,
        partition_manifest,
        analysis_definition,
        legacy_ids,
        label,
    ) in analysis_specs:
        authored_partition = str(partition_manifest)
        partitions = partition_cache.get(authored_partition)
        if partitions is None:
            partition_path, partition_data = _resolve_authored_path(
                authored_partition,
                project_dir,
                f"Analysis {name} partition manifest",
            )
            partitions = _normalize_partitions(partition_path, partition_data)
            partition_cache[authored_partition] = partitions
        scientific_policy = dict(analysis_definition)
        scientific_policy.pop("id", None)
        scientific_policy.pop("partitions", None)
        if "target_change" in scientific_policy:
            target = str(scientific_policy.pop("target_change"))
            scientific_policy["rna_ref"], scientific_policy["rna_alt"] = target.split(
                ">"
            )
        scientific_policy.setdefault("background_condition", None)
        revision = analysis_revision_from_execution_fields(
            {
                "samples": samples,
                "partitions": partitions,
                "reference": reference_input,
                "analysis": {"policy": scientific_policy},
            }
        )
        ids = dict(
            legacy_ids
            or {
                "reference": revision.scope_id("reference"),
                "cohort": revision.scope_id("cohort"),
                "analysis": revision.scope_id("analysis"),
            }
        )
        policy = {
            "schema_version": "emrys.analysis-policy.v1",
            "analysis_id": ids["analysis"],
            **scientific_policy,
        }
        reference = {
            "schema_version": "emrys.reference.v1",
            "reference_id": ids["reference"],
            **reference_input,
        }
        orchestration_contracts.validate_record("policy", policy)
        orchestration_contracts.validate_record("reference", reference)
        workflow_inputs = {
            "profile": profile_identity,
            "samples": samples,
            "partitions": partitions,
            "reference": reference,
            "analysis": {
                "cohort_id": ids["cohort"],
                "primary_analysis_id": ids["analysis"],
                "policy": policy,
                "policy_sha256": orchestration_contracts.canonical_sha256(policy),
            },
        }
        authored_paths = {
            "sample_manifest": sample_manifest,
            "partition_manifest": partition_manifest,
            "reference_fasta": reference_definition["fasta"],
            "reference_gtf": reference_definition["gtf"],
            "analysis_policy": None,
        }
        analyses.append(
            AnalysisAdmission(
                name=name,
                source_path=resolved_project,
                source_bytes=project_data,
                _profile_bytes=profile_bytes,
                revision=revision,
                _workflow_input_bytes=orchestration_contracts.canonical_json_bytes(
                    workflow_inputs
                ),
                _authored_path_bytes=orchestration_contracts.canonical_json_bytes(
                    authored_paths
                ),
                evidence_label=label,
            )
        )
    return ProjectAdmission(
        source_path=resolved_project,
        source_bytes=project_data,
        analyses=tuple(analyses),
    )


def _historical_execution_v1(
    analysis: AnalysisAdmission,
) -> tuple[dict[str, Any], bytes]:
    """Reconstruct exact execution.v1 only from a historical request-v3 source."""

    source = analysis.workflow_inputs
    fields = {
        key: source[key]
        for key in ("profile", "samples", "partitions", "reference", "analysis")
    }
    envelope = {
        "schema_version": "emrys.identity-envelope.v1",
        **fields,
    }
    digest = orchestration_contracts.canonical_sha256(envelope)
    execution = {
        "schema_version": "emrys.execution.v1",
        **fields,
        "identity_envelope": envelope,
        "identity_envelope_sha256": digest,
        "run_id": f"run-{digest}",
        "reporting_projection": {},
    }
    reporting = build_reporting_bundle(execution, analysis.profile)
    execution["reporting_projection"] = reporting.projection_references
    orchestration_contracts.validate_record(
        "execution", execution, profile=analysis.profile
    )
    return execution, orchestration_contracts.canonical_json_bytes(execution)


def admit_project(
    project_path: str | Path,
    profile: Mapping[str, Any] | str | Path,
    *,
    allow_legacy: bool = False,
) -> ProjectAdmission:
    """Admit one file-bound Project and all of its named Analyses."""

    authored_value = os.fspath(project_path)
    validate_authored_path(authored_value, "Project definition")
    authored_path = Path(authored_value)
    if not authored_path.is_absolute():
        authored_path = Path.cwd() / authored_path
    resolved_project, project_data = _regular_file(authored_path, "Project definition")
    return _admit_project_data(
        resolved_project,
        project_data,
        profile,
        allow_legacy=allow_legacy,
    )


__all__ = (
    "AnalysisAdmission",
    "ProjectAdmission",
    "admit_project",
    "validate_authored_path",
)
