"""Read-only admission and canonical normalization for the local CMH pilot."""

from __future__ import annotations

import errno
import glob
import hashlib
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
    analysis_revision_from_execution_fields,
)
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.contracts.scientific_evidence import step08, step09


class _ClosedSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that also closes keys and merge behavior."""

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                raise orchestration_contracts.ContractValidationError(
                    "YAML merge keys are not allowed"
                )
        super().flatten_mapping(node)

    def construct_mapping(
        self,
        node: yaml.MappingNode,
        deep: bool = False,
    ) -> dict[str, Any]:
        self.flatten_mapping(node)
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise orchestration_contracts.ContractValidationError(
                    "Every YAML mapping key must be a string"
                )
            if key in result:
                raise orchestration_contracts.ContractValidationError(
                    f"Duplicate YAML mapping key: {key}"
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


@dataclass(frozen=True, slots=True)
class NormalizationBundle:
    """Admitted scientific inputs plus non-identity source provenance."""

    request_path: Path
    request_bytes: bytes
    _profile_bytes: bytes
    analysis_revision: AnalysisRevision
    projection_source_bytes: bytes

    @property
    def request_sha256(self) -> str:
        """Return the exact authored-source digest from immutable bytes."""

        return hashlib.sha256(self.request_bytes).hexdigest()

    @property
    def request(self) -> dict[str, Any]:
        """Return a fresh authored-request view for compatibility callers."""

        return _load_yaml_object(self.request_bytes, self.request_path)

    @property
    def profile(self) -> dict[str, Any]:
        """Return a fresh admitted-profile view; it is not shared authority."""

        return orchestration_contracts.load_json_object_bytes(
            self._profile_bytes,
            "normalized profile",
        )

    @property
    def projection_source(self) -> dict[str, Any]:
        """Return a fresh construction view; it is never Run authority."""

        return orchestration_contracts.load_json_object_bytes(
            self.projection_source_bytes,
            "normalized construction source",
        )

    def historical_execution_v1(self) -> tuple[dict[str, Any], bytes]:
        """Reconstruct only an existing v1 Run for historical resume admission."""

        source = self.projection_source
        envelope = {
            "schema_version": "emrys.identity-envelope.v1",
            **{key: source[key] for key in ("profile", "samples", "partitions", "reference", "analysis")},
        }
        digest = orchestration_contracts.canonical_sha256(envelope)
        execution = {
            "schema_version": "emrys.execution.v1",
            **{key: source[key] for key in ("profile", "samples", "partitions", "reference", "analysis")},
            "identity_envelope": envelope,
            "identity_envelope_sha256": digest,
            "run_id": f"run-{digest}",
            "reporting_projection": {},
        }
        reporting = build_reporting_bundle(execution, self.profile)
        execution["reporting_projection"] = reporting.projection_references
        orchestration_contracts.validate_record("execution", execution, profile=self.profile)
        return execution, orchestration_contracts.canonical_json_bytes(execution)


_READ_CHUNK_BYTES = 1024 * 1024


def _stable_file_state(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _require_descriptor_path_binding(
    path: Path,
    descriptor_state: os.stat_result,
    label: str,
) -> None:
    try:
        path_state = os.stat(path, follow_symlinks=False)
    except FileNotFoundError as exc:
        raise orchestration_contracts.ContractValidationError(
            f"{label} pathname changed while it was being admitted: {path}"
        ) from exc
    except OSError as exc:
        raise orchestration_contracts.ContractValidationError(
            f"Could not verify {label} pathname {path}: {exc}"
        ) from exc
    if stat.S_ISLNK(path_state.st_mode):
        raise orchestration_contracts.ContractValidationError(
            f"{label} must not be a symlink: {path}"
        )
    if (path_state.st_dev, path_state.st_ino) != (
        descriptor_state.st_dev,
        descriptor_state.st_ino,
    ):
        raise orchestration_contracts.ContractValidationError(
            f"{label} pathname changed while it was being admitted: {path}"
        )


def _regular_file(path: Path, label: str) -> tuple[Path, bytes]:
    admitted_path = Path(os.path.abspath(path))
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        raise orchestration_contracts.ContractValidationError(
            "This platform cannot admit files without following symbolic links"
        )
    flags = os.O_RDONLY | no_follow | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(admitted_path, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise orchestration_contracts.ContractValidationError(
                f"{label} is not a regular file: {admitted_path}"
            )
        _require_descriptor_path_binding(admitted_path, before, label)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, _READ_CHUNK_BYTES):
            chunks.append(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
        _require_descriptor_path_binding(admitted_path, after, label)
    except FileNotFoundError as exc:
        raise orchestration_contracts.ContractValidationError(
            f"{label} does not exist: {admitted_path}"
        ) from exc
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise orchestration_contracts.ContractValidationError(
                f"{label} must not be a symlink: {admitted_path}"
            ) from exc
        raise orchestration_contracts.ContractValidationError(
            f"Could not read {label} {admitted_path}: {exc}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if not data:
        raise orchestration_contracts.ContractValidationError(
            f"{label} must be nonempty: {admitted_path}"
        )
    if (
        _stable_file_state(before) != _stable_file_state(after)
        or len(data) != before.st_size
    ):
        raise orchestration_contracts.ContractValidationError(
            f"{label} changed while it was being admitted: {admitted_path}"
        )
    return admitted_path, data


def _regular_file_snapshot(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    """Admit one large input by streaming its identity without retaining bytes."""

    admitted_path = Path(os.path.abspath(path))
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        raise orchestration_contracts.ContractValidationError(
            "This platform cannot admit files without following symbolic links"
        )
    flags = os.O_RDONLY | no_follow | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    digest = hashlib.sha256()
    observed_size = 0
    try:
        descriptor = os.open(admitted_path, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise orchestration_contracts.ContractValidationError(
                f"{label} is not a regular file: {admitted_path}"
            )
        _require_descriptor_path_binding(admitted_path, before, label)
        while chunk := os.read(descriptor, _READ_CHUNK_BYTES):
            digest.update(chunk)
            observed_size += len(chunk)
        after = os.fstat(descriptor)
        _require_descriptor_path_binding(admitted_path, after, label)
    except FileNotFoundError as exc:
        raise orchestration_contracts.ContractValidationError(
            f"{label} does not exist: {admitted_path}"
        ) from exc
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise orchestration_contracts.ContractValidationError(
                f"{label} must not be a symlink: {admitted_path}"
            ) from exc
        raise orchestration_contracts.ContractValidationError(
            f"Could not read {label} {admitted_path}: {exc}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if observed_size == 0:
        raise orchestration_contracts.ContractValidationError(
            f"{label} must be nonempty: {admitted_path}"
        )
    if (
        _stable_file_state(before) != _stable_file_state(after)
        or observed_size != before.st_size
    ):
        raise orchestration_contracts.ContractValidationError(
            f"{label} changed while it was being admitted: {admitted_path}"
        )
    return admitted_path, {
        "path": str(admitted_path),
        "size_bytes": observed_size,
        "sha256": digest.hexdigest(),
    }


def _validate_authored_path(value: str, label: str) -> None:
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
    _validate_authored_path(value, label)
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return _regular_file(candidate, label)


def _resolve_authored_snapshot(
    value: str,
    base: Path,
    label: str,
) -> tuple[Path, dict[str, Any]]:
    _validate_authored_path(value, label)
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


def _load_yaml_object(data: bytes, path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(data.decode("utf-8"), Loader=_ClosedSafeLoader)
    except orchestration_contracts.ContractValidationError:
        raise
    except (UnicodeError, yaml.YAMLError) as exc:
        raise orchestration_contracts.ContractValidationError(
            f"Could not parse request YAML {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise orchestration_contracts.ContractValidationError(
            f"Request YAML must contain one mapping object: {path}"
        )
    return value


def _load_profile(profile: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(profile, Mapping):
        value = dict(profile)
    else:
        authored_profile = os.fspath(profile)
        _validate_authored_path(authored_profile, "Profile")
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
    request_dir: Path,
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
            row["r1_fastq"], request_dir, f"Sample manifest row {index} R1 FASTQ"
        )
        r2_path, r2_snapshot = _resolve_authored_snapshot(
            row["r2_fastq"], request_dir, f"Sample manifest row {index} R2 FASTQ"
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


def _policy(request: Mapping[str, Any]) -> dict[str, Any]:
    analysis = dict(request["analysis"])
    analysis_id = analysis.pop("id")
    analysis.setdefault("background_condition", None)
    value = {
        "schema_version": "emrys.analysis-policy.v1",
        "analysis_id": analysis_id,
        **analysis,
    }
    orchestration_contracts.validate_record("policy", value)
    if value["control_condition"] == value["treatment_condition"]:
        raise orchestration_contracts.ContractValidationError(
            "Control and treatment conditions must differ"
        )
    if value["rna_ref"] == value["rna_alt"]:
        raise orchestration_contracts.ContractValidationError(
            "RNA reference and alternate alleles must differ"
        )
    return value


def normalize_request(
    request_path: str | Path,
    profile: Mapping[str, Any] | str | Path,
) -> NormalizationBundle:
    """Admit one request without writing and return its canonical execution."""

    authored_request_value = os.fspath(request_path)
    _validate_authored_path(authored_request_value, "Request")
    authored_request = Path(authored_request_value)
    if not authored_request.is_absolute():
        authored_request = Path.cwd() / authored_request
    resolved_request, request_data = _regular_file(authored_request, "Request")
    request = _load_yaml_object(request_data, resolved_request)
    orchestration_contracts.validate_record("request", request)
    profile_record = _load_profile(profile)
    expected_profile = (
        f"{profile_record['profile_id']}.{profile_record['profile_version']}"
    )
    if request["profile"] != expected_profile:
        raise orchestration_contracts.ContractValidationError(
            f"Request profile {request['profile']} does not match {expected_profile}"
        )
    request_dir = resolved_request.parent

    sample_path, sample_data = _resolve_authored_path(
        request["sample_manifest"], request_dir, "Sample manifest"
    )
    partition_path, partition_data = _resolve_authored_path(
        request["partition_manifest"], request_dir, "Partition manifest"
    )
    samples = _normalize_samples(sample_path, sample_data, request_dir)
    partitions = _normalize_partitions(partition_path, partition_data)
    policy = _policy(request)
    try:
        step09.paired_samples(
            samples["rows"],
            policy["control_condition"],
            policy["treatment_condition"],
        )
    except step08.ContractError as exc:
        raise orchestration_contracts.ContractValidationError(str(exc)) from exc
    background_condition = policy["background_condition"]
    if background_condition is not None and not any(
        row["condition"] == background_condition for row in samples["rows"]
    ):
        raise orchestration_contracts.ContractValidationError(
            f"Declared background_condition has no sample rows: {background_condition}"
        )

    _fasta_path, fasta_snapshot = _resolve_authored_snapshot(
        request["reference"]["fasta"], request_dir, "Reference FASTA"
    )
    _gtf_path, gtf_snapshot = _resolve_authored_snapshot(
        request["reference"]["gtf"], request_dir, "Reference GTF"
    )
    reference = {
        "schema_version": "emrys.reference.v1",
        "reference_id": request["reference"]["id"],
        "fasta": fasta_snapshot,
        "gtf": gtf_snapshot,
        "star_index": dict(request["reference"]["star_index"]),
    }
    orchestration_contracts.validate_record("reference", reference)

    profile_identity = {
        "profile_id": profile_record["profile_id"],
        "profile_version": profile_record["profile_version"],
        "profile_sha256": orchestration_contracts.canonical_sha256(profile_record),
    }
    analysis = {
        "cohort_id": request["cohort_id"],
        "primary_analysis_id": policy["analysis_id"],
        "policy": policy,
        "policy_sha256": orchestration_contracts.canonical_sha256(policy),
    }
    projection_source = {
        "profile": profile_identity,
        "samples": samples,
        "partitions": partitions,
        "reference": reference,
        "analysis": analysis,
    }
    analysis_revision = analysis_revision_from_execution_fields(projection_source)
    return NormalizationBundle(
        request_path=resolved_request,
        request_bytes=request_data,
        _profile_bytes=orchestration_contracts.canonical_json_bytes(profile_record),
        analysis_revision=analysis_revision,
        projection_source_bytes=orchestration_contracts.canonical_json_bytes(
            projection_source
        ),
    )


__all__ = (
    "NormalizationBundle",
    "normalize_request",
)
