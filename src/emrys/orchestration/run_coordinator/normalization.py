"""Read-only Project admission for the current local CMH implementation."""

from __future__ import annotations

import glob
import hashlib
import os
import zlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from emrys.analyses import (
    BUILTIN_PAIRED_CMH_MODULE_ID,
    AnalysisInputContextV1,
    AnalysisModuleLoadError,
    LoadedAnalysisModuleV1,
    admit_configuration,
    compose_profile,
    load_analysis_module,
    module_identity_record,
)
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
    _analysis_partition_from_execution_fields,
    analysis_revision_from_execution_fields,
    normalize_star_index_policy,
)
from emrys.libraries.validation.mpileup import selector_file_semantics
from emrys.contracts.scientific_evidence import step08
from emrys.libraries.exclusive_publication import stat_identity
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    Snapshot,
    read_bytes,
    regular_snapshot,
    sha256_with_identity,
)
from emrys.libraries.validation.tsv import tsv_bytes


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
    module: LoadedAnalysisModuleV1
    evidence_label: str | None
    selected_sample_manifest_bytes: bytes | None = None

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
    dataset_sample_count: int
    _input_snapshots: tuple[tuple[Path, Snapshot], ...] = ()

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.source_bytes).hexdigest()

    def require_inputs_unchanged(self) -> None:
        """Reject an input whose filesystem identity changed after admission."""

        for path, expected in self._input_snapshots:
            try:
                observed = regular_snapshot(path, f"Project input {path.name}")
            except ValidationError as exc:
                raise orchestration_contracts.ContractValidationError(str(exc)) from exc
            if observed != expected:
                raise orchestration_contracts.ContractValidationError(
                    f"Project input changed after admission: {path}"
                )

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


@dataclass(frozen=True, slots=True)
class _SampleInputAdmission:
    samples_bytes: bytes
    project_dir: Path
    snapshots: tuple[tuple[Path, Snapshot], ...]
    max_read_length: int


class _FastqInspection:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.part = self.records = self.sequence_length = self.max_read_length = 0
        self.line_length = self.line_first = self.line_last = 0
        self.decoder = zlib.decompressobj(31) if path.name.endswith(".gz") else None

    def observe(self, data: bytes) -> None:
        while data and self.decoder is not None:
            if self.decoder.eof:
                data = data.lstrip(b"\0")
                if not data:
                    return
                self.decoder = zlib.decompressobj(31)
            plain = self.decoder.decompress(data, 1_000_001)
            data = self.decoder.unconsumed_tail or self.decoder.unused_data
            self._plain(plain)
        if self.decoder is None:
            self._plain(data)

    def _plain(self, data: bytes) -> None:
        *lines, tail = data.split(b"\n")
        for fragment in lines:
            self._fragment(fragment)
            self._line()
        self._fragment(tail)

    def _fragment(self, fragment: bytes) -> None:
        if not fragment.isascii():
            self._fail("non-ASCII record")
        if fragment:
            if self.line_length == 0:
                self.line_first = fragment[0]
            self.line_length += len(fragment)
            self.line_last = fragment[-1]

    def _line(self) -> None:
        length = self.line_length - (self.line_last == 13)
        if self.part == 0:
            if self.line_first != 64:
                self._fail("record header does not start with '@'")
        elif self.part == 1:
            if not length:
                self._fail("record sequence is empty")
            self.sequence_length = length
        elif self.part == 2:
            if self.line_first != 43:
                self._fail("record separator does not start with '+'")
        else:
            if length != self.sequence_length:
                self._fail("record sequence and quality lengths differ")
            self.records += 1
            self.max_read_length = max(self.max_read_length, self.sequence_length)
        self.part = (self.part + 1) % 4
        self.line_length = self.line_first = self.line_last = 0

    def finish(self) -> int:
        if self.decoder is not None:
            self._plain(self.decoder.flush())
            if not self.decoder.eof:
                self._fail("truncated gzip stream")
        if self.line_length:
            self._line()
        if self.part or not self.records:
            self._fail("incomplete FASTQ record")
        return self.max_read_length

    def _fail(self, reason: str) -> None:
        raise orchestration_contracts.ContractValidationError(
            f"FASTQ is malformed at record {self.records + 1}: {self.path}: {reason}"
        )


def _regular_file(path: Path, label: str) -> tuple[Path, bytes]:
    admitted_path = Path(os.path.abspath(path))
    try:
        return admitted_path, read_bytes(admitted_path, label)
    except ValidationError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc


def _regular_file_snapshot(
    path: Path,
    label: str,
    input_snapshots: dict[Path, Snapshot] | None = None,
    observe: Callable[[bytes], None] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Admit one large input by streaming its identity without retaining bytes."""

    admitted_path = Path(os.path.abspath(path))
    try:
        digest, state = sha256_with_identity(admitted_path, label, observe=observe)
    except ValidationError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc
    if input_snapshots is not None:
        input_snapshots[admitted_path] = Snapshot(*stat_identity(state))
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


def _authored_path(value: str, base: Path, label: str) -> Path:
    validate_authored_path(value, label)
    path = Path(value)
    return Path(os.path.abspath(path if path.is_absolute() else base / path))


def _resolve_authored_path(
    value: str,
    base: Path,
    label: str,
    prepared_files: Mapping[Path, bytes] | None = None,
) -> tuple[Path, bytes]:
    candidate = _authored_path(value, base, label)
    if prepared_files is not None and candidate in prepared_files:
        return candidate, prepared_files[candidate]
    return _regular_file(candidate, label)


def _resolve_authored_snapshot(
    value: str,
    base: Path,
    label: str,
    input_snapshots: dict[Path, Snapshot] | None = None,
) -> tuple[Path, dict[str, Any]]:
    return _regular_file_snapshot(
        _authored_path(value, base, label), label, input_snapshots
    )


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
        profile_path = _authored_path(os.fspath(profile), Path.cwd(), "Profile")
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
    input_snapshots: dict[Path, Snapshot] | None = None,
    inspect_fastqs: bool = False,
) -> tuple[dict[str, Any], step08.Table, int]:
    try:
        table, _, rows = step08.validate_sample_manifest_bytes(
            manifest_data, manifest_path
        )
    except step08.ContractError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc
    normalized_rows: list[dict[str, Any]] = []
    fastq_cache: dict[Path, tuple[dict[str, Any], int]] = {}

    def admit_fastq(path: Path, label: str) -> dict[str, Any]:
        if not inspect_fastqs:
            return _regular_file_snapshot(path, label, input_snapshots)[1]
        cached = fastq_cache.get(path)
        if cached is None:
            inspection = _FastqInspection(path)
            try:
                _path, record = _regular_file_snapshot(
                    path, label, input_snapshots, inspection.observe
                )
                maximum = inspection.finish()
            except zlib.error as exc:
                inspection._fail(f"invalid gzip stream ({exc})")
            cached = (record, maximum)
            fastq_cache[path] = cached
        return cached[0]

    for index, row in enumerate(rows, start=2):
        r1_label = f"Sample manifest row {index} R1 FASTQ"
        r2_label = f"Sample manifest row {index} R2 FASTQ"
        r1_path = _authored_path(row["r1_fastq"], project_dir, r1_label)
        r2_path = _authored_path(row["r2_fastq"], project_dir, r2_label)
        if r1_path == r2_path:
            raise orchestration_contracts.ContractValidationError(
                f"Sample {row['sample_id']} R1 and R2 FASTQs must be distinct"
            )
        if r1_path.name.endswith(".gz") != r2_path.name.endswith(".gz"):
            raise orchestration_contracts.ContractValidationError(
                f"Sample {row['sample_id']} R1 and R2 FASTQs must use the same "
                "compression mode"
            )
        r1_snapshot = admit_fastq(r1_path, r1_label)
        r2_snapshot = admit_fastq(r2_path, r2_label)
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
    return (
        {
            "manifest": _snapshot(manifest_path, manifest_data),
            "rows": normalized_rows,
        },
        table,
        max((length for _record, length in fastq_cache.values()), default=0),
    )


def _admit_sample_inputs(
    manifest_path: Path,
    manifest_data: bytes,
    project_dir: Path,
    inspect_fastqs: bool = False,
) -> _SampleInputAdmission:
    project_dir = Path(os.path.abspath(project_dir))
    snapshots: dict[Path, Snapshot] = {}
    samples, _table, max_read_length = _normalize_samples(
        manifest_path,
        manifest_data,
        project_dir,
        snapshots,
        inspect_fastqs=inspect_fastqs,
    )
    return _SampleInputAdmission(
        orchestration_contracts.canonical_json_bytes(samples),
        project_dir,
        tuple(snapshots.items()),
        max_read_length,
    )


def _normalize_partitions(
    manifest_path: Path,
    manifest_data: bytes,
    input_snapshots: dict[Path, Snapshot] | None = None,
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
                input_snapshots,
            )
            selector_value = str(path)
            selector_format, selector_compression = selector_file_semantics(path)
        normalized_rows.append(
            {
                "partition_id": row["partition_id"],
                "selector_type": row["selector_type"],
                "selector_value": selector_value,
                "selector_file": selector_file,
                **(
                    {
                        "selector_format": selector_format,
                        "selector_compression": selector_compression,
                    }
                    if selector_file is not None
                    else {}
                ),
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
    prepared_files: Mapping[Path, bytes] | None = None,
    sample_inputs: _SampleInputAdmission | None = None,
) -> ProjectAdmission:
    """Admit prepared Project bytes at their intended canonical location."""

    resolved_project = Path(os.path.abspath(project_path))
    definition = orchestration_contracts.load_yaml_object_bytes(
        project_data,
        f"Project YAML {resolved_project}",
    )
    profile_record = _load_profile(profile)
    project_dir = resolved_project.parent
    prepared = (
        None
        if prepared_files is None
        else {
            Path(os.path.abspath(path)): data for path, data in prepared_files.items()
        }
    )
    input_snapshots: dict[Path, Snapshot] = {}
    try:
        orchestration_contracts.validate_record("project", definition)
    except orchestration_contracts.ContractValidationError as exc:
        raise orchestration_contracts.ContractValidationError(
            f"{exc}\nProject setup accepts emrys.project.v1. Preserve the original "
            "bundle and use `emrys init NAME` for guided setup, or correct a current "
            "Project using configs/README.md. Legacy fields are not translated."
        ) from exc
    sample_manifest = definition["dataset"]["samples"]
    reference_definition = definition["reference"]
    analysis_specs = tuple(sorted(definition["analyses"].items()))

    sample_path, sample_data = _resolve_authored_path(
        sample_manifest, project_dir, "Sample manifest", prepared
    )
    if sample_inputs is None:
        sample_inputs = _admit_sample_inputs(sample_path, sample_data, project_dir)
    samples = _json_object(sample_inputs.samples_bytes, "Prepared sample admission")
    if sample_inputs.project_dir != project_dir or samples["manifest"] != _snapshot(
        sample_path, sample_data
    ):
        raise orchestration_contracts.ContractValidationError(
            "Prepared sample admission does not match the Project sample manifest"
        )
    sample_table = step08.validate_sample_manifest_bytes(sample_data, sample_path)[0]
    input_snapshots.update(sample_inputs.snapshots)
    dataset_sample_ids = {str(row["sample_id"]) for row in samples["rows"]}

    _fasta_path, fasta_snapshot = _resolve_authored_snapshot(
        reference_definition["fasta"],
        project_dir,
        "Reference FASTA",
        input_snapshots,
    )
    _gtf_path, gtf_snapshot = _resolve_authored_snapshot(
        reference_definition["gtf"],
        project_dir,
        "Reference GTF",
        input_snapshots,
    )
    reference_input = {
        "fasta": fasta_snapshot,
        "gtf": gtf_snapshot,
        "star_index": normalize_star_index_policy(reference_definition["star_index"]),
    }
    partition_cache: dict[str, dict[str, Any]] = {}
    analyses: list[AnalysisAdmission] = []
    for name, analysis_definition in analysis_specs:
        partition_manifest = analysis_definition["partitions"]
        selected_sample_manifest_bytes = None
        selected_samples = samples
        declared_sample_ids = analysis_definition.get("sample_ids")
        if declared_sample_ids is not None:
            selected_ids = {str(sample_id) for sample_id in declared_sample_ids}
            unknown = sorted(selected_ids - dataset_sample_ids)
            if unknown:
                raise orchestration_contracts.ContractValidationError(
                    f"Analysis {name} selects unknown sample IDs: {', '.join(unknown)}"
                )
            if selected_ids != dataset_sample_ids:
                selected_samples = {
                    **samples,
                    "rows": [
                        row
                        for row in samples["rows"]
                        if row["sample_id"] in selected_ids
                    ],
                }
                selected_sample_manifest_bytes = tsv_bytes(
                    sample_table.header,
                    (
                        row
                        for row in sample_table.rows
                        if row["sample_id"] in selected_ids
                    ),
                )
        authored_partition = str(partition_manifest)
        partitions = partition_cache.get(authored_partition)
        if partitions is None:
            partition_path, partition_data = _resolve_authored_path(
                authored_partition,
                project_dir,
                f"Analysis {name} partition manifest",
                prepared,
            )
            partitions = _normalize_partitions(
                partition_path, partition_data, input_snapshots
            )
            partition_cache[authored_partition] = partitions
        try:
            module = load_analysis_module(
                str(analysis_definition.get("module", BUILTIN_PAIRED_CMH_MODULE_ID))
            )
            admitted_profile = compose_profile(profile_record, module.descriptor)
        except AnalysisModuleLoadError as exc:
            raise orchestration_contracts.ContractValidationError(
                f"Analysis {name} module admission failed: {exc}"
            ) from exc
        if "module" in analysis_definition:
            configuration = analysis_definition["config"]
        else:
            configuration = {
                key: value
                for key, value in analysis_definition.items()
                if key not in {"partitions", "sample_ids"}
            }
        try:
            scientific_policy = admit_configuration(
                module.descriptor,
                configuration,
                AnalysisInputContextV1(
                    samples=tuple(
                        {
                            key: row[key]
                            for key in (
                                "sample_id",
                                "condition",
                                "replicate",
                                "strandedness",
                            )
                        }
                        for row in selected_samples["rows"]
                    ),
                    partitions=tuple(
                        _analysis_partition_from_execution_fields(row)
                        for row in partitions["rows"]
                    ),
                    reference={
                        "fasta_sha256": reference_input["fasta"]["sha256"],
                        "gtf_sha256": reference_input["gtf"]["sha256"],
                    },
                ),
            )
        except (AnalysisModuleLoadError, TypeError, ValueError) as exc:
            raise orchestration_contracts.ContractValidationError(
                f"Analysis {name} module admission failed: {exc}"
            ) from exc
        policy_body = {
            "schema_version": "emrys.analysis-module-policy.v1",
            "module": module_identity_record(module),
            "implementation_sha256": module.provider.package.sha256,
            "configuration": scientific_policy,
        }
        profile_bytes = orchestration_contracts.canonical_json_bytes(admitted_profile)
        profile_identity = {
            key: admitted_profile[key] for key in ("profile_id", "profile_version")
        }
        profile_identity["profile_sha256"] = orchestration_contracts.canonical_sha256(
            admitted_profile
        )
        revision = analysis_revision_from_execution_fields(
            {
                "samples": selected_samples,
                "partitions": partitions,
                "reference": reference_input,
                "analysis": {"policy": policy_body},
            }
        )
        ids = {
            scope: revision.scope_id(scope)
            for scope in ("reference", "cohort", "analysis")
        }
        policy = {
            **policy_body,
            "analysis_id": ids["analysis"],
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
            "samples": selected_samples,
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
                module=module,
                evidence_label=name,
                selected_sample_manifest_bytes=selected_sample_manifest_bytes,
            )
        )
    return ProjectAdmission(
        source_path=resolved_project,
        source_bytes=project_data,
        analyses=tuple(analyses),
        dataset_sample_count=len(samples["rows"]),
        _input_snapshots=tuple(
            sorted(input_snapshots.items(), key=lambda item: item[0])
        ),
    )


def admit_project(
    project_path: str | Path,
    profile: Mapping[str, Any] | str | Path,
) -> ProjectAdmission:
    """Admit one file-bound Project and all of its named Analyses."""

    authored_path = _authored_path(
        os.fspath(project_path), Path.cwd(), "Project definition"
    )
    resolved_project, project_data = _regular_file(authored_path, "Project definition")
    return _admit_project_data(
        resolved_project,
        project_data,
        profile,
    )


__all__ = (
    "AnalysisAdmission",
    "ProjectAdmission",
    "admit_project",
    "validate_authored_path",
)
