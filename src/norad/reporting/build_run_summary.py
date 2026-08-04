#!/usr/bin/env python3
"""Assemble one validated NORAD artifact transaction into a run summary.

The command is explicit-input-only and dry-run-first. It never discovers
pipeline outputs, invokes an analysis engine, or promotes computational or
scientific state. Execute mode publishes canonical JSON, two deterministic
TSV views, and a receipt last as one rollback-protected transaction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import sys
import uuid
from collections import Counter, OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

import _run_summary_science as science
import build_artifact_index as adapter


if science.contracts is not adapter.contracts:
    raise ImportError("artifact-contract consumers did not resolve one exact owner")
contracts = adapter.contracts


PRODUCER = "build_run_summary"
PRODUCER_VERSION = "1.1.0"
LEGACY_PRODUCER_VERSION = "1.0.0"
RUN_SUMMARY_SCHEMA_VERSION = "1.1.0"
RUN_SUMMARY_TSV_SCHEMA_VERSION = "1.0.0"
QC_SUMMARY_TSV_SCHEMA_VERSION = "1.0.0"
RUN_SUMMARY_RECEIPT_SCHEMA_VERSION = "1.0.0"
RUN_CONTRACT_FIELDS = adapter.RUN_CONTRACT_FIELDS

REPORT_TABLE_APPROVALS_HEADER = (
    "run_id",
    "run_contract_sha256",
    "table_id",
    "artifact_id",
    "role",
    "title",
    "path",
    "sha256",
    "row_count",
    "display_row_limit",
    "approval_status",
    "approval_policy_version",
    "approved_by",
    "approved_at",
)

REPORT_ROLE_ADAPTERS = {
    role: f"step09c_{role}_v1"
    for role in (
        "orientation_locus_audit",
        "annotation_audit",
        "qc_funnel",
        "replicate_effects",
        "sensitivity_matrix",
        "leave_one_pair_out",
        "candidate_selection",
        "candidate_adjudication",
        "decisions",
        "evidence_index",
        "limitations",
    )
}

RUN_SUMMARY_HEADER = (
    "run_id",
    "run_contract_sha256",
    "summary_state",
    "science_status",
    "artifact_order",
    "scope_order",
    "step_id",
    "scope_type",
    "scope_id",
    "artifact_id",
    "adapter",
    "required",
    "availability_status",
    "completion_status",
    "rollup_state",
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
    "source_path",
    "source_sha256",
    "source_row_count",
    "selected_attempt_id",
    "warning_count",
    "error_count",
)

QC_SUMMARY_HEADER = (
    "run_id",
    "artifact_order",
    "metric_order",
    "step_id",
    "scope_type",
    "scope_id",
    "artifact_id",
    "metric_id",
    "name",
    "value",
    "value_type",
    "unit",
    "status",
    "source_artifact_id",
)

RUN_SUMMARY_RECEIPT_HEADER = (
    "run_id",
    "run_contract_sha256",
    "sample_manifest_sha256",
    "reference_contract_sha256",
    "partition_manifest_sha256",
    "primary_analysis_id",
    "primary_analysis_policy_sha256",
    "artifact_receipt_path",
    "artifact_receipt_sha256",
    "artifact_adapter_attempt_id",
    "inventory_path",
    "inventory_sha256",
    "inventory_row_count",
    "artifacts_index_path",
    "artifacts_index_sha256",
    "artifact_record_count",
    "record_set_sha256",
    "run_summary_schema_version",
    "run_summary_tsv_schema_version",
    "qc_summary_tsv_schema_version",
    "run_summary_receipt_schema_version",
    "run_summary_json_path",
    "run_summary_json_sha256",
    "run_summary_json_size_bytes",
    "run_summary_tsv_path",
    "run_summary_tsv_sha256",
    "run_summary_tsv_row_count",
    "qc_summary_tsv_path",
    "qc_summary_tsv_sha256",
    "qc_summary_tsv_row_count",
    "science_review_summary_path",
    "science_review_summary_sha256",
    "summary_state",
    "science_status",
    "published_output_count",
    "run_summary_attempt_id",
    "supersedes_run_summary_attempt_id",
    "run_summary_attempt_history",
    "producer",
    "producer_version",
    "git_commit",
    "started_at",
    "finished_at",
    "transaction_state",
)


class RunSummaryError(RuntimeError):
    """Raised when a run summary cannot be built or safely published."""


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    sha256: str
    device: int
    inode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True)
class OutputPaths:
    output_dir: Path
    output_dir_device: int
    output_dir_inode: int
    summary_json: Path
    summary_tsv: Path
    qc_summary: Path
    receipt: Path
    lock: Path

    @property
    def ordered_outputs(self) -> tuple[Path, ...]:
        return (
            self.summary_json,
            self.summary_tsv,
            self.qc_summary,
            self.receipt,
        )


@dataclass
class BuildContext:
    run_id: str
    execute: bool
    artifact_receipt_path: Path
    artifact_receipt_sha256: str
    artifact_receipt: dict[str, str]
    run_contract_path: Path
    run_contract_file_sha256: str
    run_contract: dict[str, Any]
    inventory_path: Path
    inventory_sha256: str
    inventory_rows: list[dict[str, str]]
    artifacts_path: Path
    artifacts_sha256: str
    records_dir: Path
    index_rows: list[dict[str, str]]
    record_paths: list[Path]
    record_hashes: list[str]
    input_snapshots: tuple[FileSnapshot, ...]
    artifacts: list[dict[str, Any]]
    science_review_summary_path: Path | None
    science_review_summary_sha256: str | None
    report_table_approvals_path: Path | None
    report_table_approvals_sha256: str | None
    report_table_snapshots: tuple[FileSnapshot, ...]
    document: dict[str, Any]
    summary_json_bytes: bytes
    summary_rows: list[dict[str, Any]]
    summary_tsv_bytes: bytes
    qc_rows: list[dict[str, Any]]
    qc_summary_bytes: bytes
    paths: OutputPaths
    previous_receipt: dict[str, str] | None
    previous_receipt_sha256: str | None
    previous_attempt_id: str | None
    previous_attempt_history: list[str]
    attempt_id: str
    git_commit: str
    started_at: str
    finished_at: str
    receipt_row: dict[str, Any]
    receipt_bytes: bytes


def parse_arguments(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic run summary from one complete NORAD "
            "artifact-adapter receipt. Dry-run is the default."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--artifact-receipt",
        required=True,
        type=Path,
        help="Exact completed artifact-adapter receipt TSV.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Artifact output root containing <run_id>/.",
    )
    parser.add_argument(
        "--science-review-summary",
        type=Path,
        help=(
            "Optional exact committed Step 09c review-summary TSV. It is "
            "never discovered automatically."
        ),
    )
    parser.add_argument(
        "--report-table-approvals",
        type=Path,
        help=(
            "Optional exact report-table approvals TSV. It is never "
            "discovered automatically and must be bound to this run and its "
            "explicit Step 09c scientific-review artifacts."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the four-file transaction; otherwise only validate.",
    )
    return parser.parse_args(argv)


def _fail(message: str) -> None:
    raise RunSummaryError(message)


def _resolved_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(Path(value).expanduser())))


def _require_regular_file(label: str, value: str | Path) -> Path:
    path = _resolved_path(value)
    try:
        metadata = path.lstat()
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(metadata.st_mode):
        _fail(f"{label} must not be a symbolic link: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        _fail(f"{label} is not a regular file: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} cannot be resolved: {path}: {exc}")
    if not resolved.is_file():
        _fail(f"{label} does not resolve to a regular file: {path}")
    return resolved


def _capture_file_snapshot(
    label: str,
    path: Path,
) -> tuple[bytes, FileSnapshot]:
    if path.is_symlink():
        _fail(f"{label} became a symbolic link: {path}")
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                _fail(f"{label} is not a regular file: {path}")
            payload = stream.read()
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except OSError as exc:
        _fail(f"Could not capture {label} {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    current_identity = (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_ctime_ns,
    )
    if (
        before_identity != after_identity
        or before_identity != current_identity
        or len(payload) != before.st_size
        or stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
    ):
        _fail(f"{label} changed while its immutable snapshot was captured: {path}")
    snapshot = FileSnapshot(
        path=path,
        sha256=adapter.sha256_bytes(payload),
        device=before.st_dev,
        inode=before.st_ino,
        size_bytes=before.st_size,
        mtime_ns=before.st_mtime_ns,
        ctime_ns=before.st_ctime_ns,
    )
    return payload, snapshot


def _verify_file_snapshot(label: str, expected: FileSnapshot) -> None:
    _payload, observed = _capture_file_snapshot(label, expected.path)
    if observed != expected:
        _fail(
            f"{label} changed after its immutable snapshot was captured: "
            f"{expected.path}"
        )


def _read_exact_tsv_bytes(
    *,
    label: str,
    path: Path,
    payload: bytes,
    header: Sequence[str],
    exact_rows: int | None = None,
) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(
            io.StringIO(text, newline=""),
            delimiter="\t",
            strict=True,
        )
        if tuple(reader.fieldnames or ()) != tuple(header):
            _fail(f"{label} has an invalid TSV header: {path}")
        rows = list(reader)
    except RunSummaryError:
        raise
    except (UnicodeError, csv.Error) as exc:
        _fail(f"Could not parse {label} {path}: {exc}")
    if exact_rows is not None and len(rows) != exact_rows:
        _fail(
            f"{label} must contain {exact_rows} rows; observed {len(rows)}: "
            f"{path}"
        )
    return rows


def _load_json_bytes(
    *,
    label: str,
    path: Path,
    payload: bytes,
) -> dict[str, Any]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=contracts.reject_duplicate_json_keys,
            parse_constant=contracts.reject_nonstandard_json_constant,
        )
    except contracts.ContractValidationError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"Could not parse {label} {path}: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label} must contain a JSON object: {path}")
    return value


def _reject_symlink_components(path: Path, label: str) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if not os.path.lexists(current):
            continue
        try:
            metadata = current.lstat()
        except OSError as exc:
            _fail(f"Could not inspect {label} component {current}: {exc}")
        if stat.S_ISLNK(metadata.st_mode):
            _fail(f"{label} must not traverse a symbolic link: {current}")


def _require_explicit_regular_file(
    label: str,
    value: str | Path,
) -> Path:
    try:
        contracts.validate_resolved_path(str(value), label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    lexical = _resolved_path(value)
    _reject_symlink_components(lexical, label)
    resolved = _require_regular_file(label, lexical)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved


def _require_contract_regular_file(label: str, value: str) -> Path:
    try:
        contracts.validate_resolved_path(value, label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    declared = Path(value)
    lexical = (
        declared
        if declared.is_absolute()
        else contracts.REPO_ROOT / declared
    ).absolute()
    _reject_symlink_components(lexical, label)
    resolved = _require_regular_file(label, lexical)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved


def _capture_report_table_snapshot(
    label: str,
    path: Path,
) -> tuple[FileSnapshot, int]:
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                _fail(f"{label} is not a regular file: {path}")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            stream.seek(0)
            wrapper = io.TextIOWrapper(
                stream,
                encoding="utf-8",
                newline="",
            )
            try:
                reader = csv.reader(wrapper, delimiter="\t", strict=True)
                try:
                    header = next(reader)
                except StopIteration:
                    _fail(f"{label} is empty: {path}")
                if not header or any(not column for column in header):
                    _fail(f"{label} has a blank TSV header column: {path}")
                if len(header) != len(set(header)):
                    _fail(f"{label} has duplicate TSV header columns: {path}")
                row_count = 0
                for row_number, row in enumerate(reader, start=2):
                    if len(row) != len(header):
                        _fail(
                            f"{label} row {row_number} has {len(row)} fields; "
                            f"expected {len(header)}: {path}"
                        )
                    row_count += 1
            finally:
                wrapper.detach()
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except RunSummaryError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not inspect {label} {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    current_identity = (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_ctime_ns,
    )
    if (
        before_identity != after_identity
        or before_identity != current_identity
        or stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
    ):
        _fail(f"{label} changed while it was inspected: {path}")
    return (
        FileSnapshot(
            path=path,
            sha256=digest.hexdigest(),
            device=before.st_dev,
            inode=before.st_ino,
            size_bytes=before.st_size,
            mtime_ns=before.st_mtime_ns,
            ctime_ns=before.st_ctime_ns,
        ),
        row_count,
    )


def _verify_report_table_snapshot(expected: FileSnapshot) -> None:
    observed, _row_count = _capture_report_table_snapshot(
        "Approved report table",
        expected.path,
    )
    if observed != expected:
        _fail(
            "Approved report table changed after its immutable snapshot was "
            f"captured: {expected.path}"
        )


def _canonical_nonnegative_integer(value: str, label: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        _fail(f"{label} must be a canonical non-negative integer")
    return int(value)


def _parse_approval_timestamp(value: str, build_started_at: str) -> str:
    if not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
        r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
        value,
    ):
        _fail(
            "approved_at must be a canonical UTC timestamp ending in Z with "
            "second precision"
        )
    try:
        approved_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        started_at = datetime.fromisoformat(
            build_started_at.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RunSummaryError("approved_at is not a valid timestamp") from exc
    if approved_at.tzinfo is None or started_at.tzinfo is None:
        _fail("approved_at must include a timezone")
    if approved_at.astimezone(timezone.utc) > started_at.astimezone(
        timezone.utc
    ):
        _fail("approved_at must not be later than the run-summary attempt")
    return value


def _normalize_report_table_approvals(
    *,
    manifest_value: Path,
    run_id: str,
    run_contract: Mapping[str, Any],
    artifacts: Sequence[dict[str, Any]],
    scientific_review: Mapping[str, Any],
    build_started_at: str,
) -> tuple[
    Path,
    FileSnapshot,
    list[dict[str, Any]],
    tuple[FileSnapshot, ...],
]:
    manifest_path = _require_explicit_regular_file(
        "Report-table approvals manifest",
        manifest_value,
    )
    payload, manifest_snapshot = _capture_file_snapshot(
        "Report-table approvals manifest",
        manifest_path,
    )
    rows = _read_exact_tsv_bytes(
        label="Report-table approvals manifest",
        path=manifest_path,
        payload=payload,
        header=REPORT_TABLE_APPROVALS_HEADER,
    )
    if not rows:
        _fail(
            "A supplied report-table approvals manifest must contain at least "
            "one run-bound approval row; omit the option when no tables are "
            "approved"
        )
    if scientific_review["record_state"] != "present":
        _fail(
            "Report-table approvals require the exact committed Step 09c "
            "science-review summary"
        )
    review_id = scientific_review["record"]["review_id"]
    artifacts_by_id = {
        artifact["artifact_id"]: artifact for artifact in artifacts
    }
    observed_table_ids: set[str] = set()
    observed_sources: set[tuple[str, str]] = set()
    snapshots_by_path: OrderedDict[Path, FileSnapshot] = OrderedDict()
    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        if any(
            key is None
            or value is None
            or not isinstance(value, str)
            for key, value in row.items()
        ):
            _fail(
                "Report-table approvals manifest has a non-rectangular row "
                f"at line {row_number}"
            )
        if row["run_id"] != run_id:
            _fail(
                f"Report-table approval line {row_number} has the wrong run_id"
            )
        if row["run_contract_sha256"] != run_contract[
            "run_contract_sha256"
        ]:
            _fail(
                "Report-table approval line "
                f"{row_number} has the wrong run_contract_sha256"
            )
        for field in (
            "table_id",
            "artifact_id",
            "role",
            "approval_policy_version",
            "approved_by",
        ):
            if not contracts.SAFE_ID_RE.fullmatch(row[field]):
                _fail(
                    f"Report-table approval line {row_number} field {field} "
                    "must be a safe non-empty ID"
                )
        table_id = row["table_id"]
        if table_id in observed_table_ids:
            _fail(f"Duplicate report-table approval table_id: {table_id}")
        observed_table_ids.add(table_id)
        title = row["title"]
        if (
            not title
            or title.strip() != title
            or any(character in title for character in "\t\r\n")
        ):
            _fail(
                f"Report-table approval {table_id!r} title must be one "
                "trimmed non-empty line"
            )
        role = row["role"]
        expected_adapter = REPORT_ROLE_ADAPTERS.get(role)
        if expected_adapter is None:
            _fail(
                f"Report-table approval {table_id!r} has unsupported role "
                f"{role!r}"
            )
        artifact = artifacts_by_id.get(row["artifact_id"])
        if artifact is None:
            _fail(
                f"Report-table approval {table_id!r} references an unknown "
                f"artifact: {row['artifact_id']}"
            )
        scope = artifact["scope"]
        if (
            artifact["completion_status"] != "complete"
            or artifact["adapter"] != expected_adapter
            or scope["step_id"] != "09c"
            or scope["scope_type"] != "scientific_review"
            or scope["scope_id"] != review_id
        ):
            _fail(
                f"Report-table approval {table_id!r} does not match the "
                f"complete active Step 09c artifact contract for role {role!r}"
            )
        declared_path = row["path"]
        sources = [
            source
            for source in (
                artifact["source"],
                *artifact["members"],
            )
            if source is not None and source["path"] == declared_path
        ]
        if len(sources) != 1:
            _fail(
                f"Report-table approval {table_id!r} path must match exactly "
                "one source or member of its named artifact"
            )
        source = sources[0]
        if source["media_type"] != "text/tab-separated-values":
            _fail(
                f"Report-table approval {table_id!r} must reference a TSV "
                "artifact"
            )
        if source["row_count"] is None:
            _fail(
                f"Report-table approval {table_id!r} source has no declared "
                "row count"
            )
        declared_sha256 = row["sha256"]
        if not adapter.SHA256_RE.fullmatch(declared_sha256):
            _fail(
                f"Report-table approval {table_id!r} sha256 must be lowercase "
                "hexadecimal"
            )
        declared_row_count = _canonical_nonnegative_integer(
            row["row_count"],
            f"Report-table approval {table_id!r} row_count",
        )
        if (
            declared_sha256 != source["sha256"]
            or declared_row_count != source["row_count"]
        ):
            _fail(
                f"Report-table approval {table_id!r} hash or row count does "
                "not match its artifact record"
            )
        if row["display_row_limit"] == "NA":
            display_row_limit: int | None = None
        else:
            display_row_limit = _canonical_nonnegative_integer(
                row["display_row_limit"],
                (
                    f"Report-table approval {table_id!r} "
                    "display_row_limit"
                ),
            )
            if display_row_limit > declared_row_count:
                _fail(
                    f"Report-table approval {table_id!r} display_row_limit "
                    "must not exceed row_count"
                )
        if row["approval_status"] != "approved":
            _fail(
                f"Report-table approval {table_id!r} approval_status must be "
                "'approved'"
            )
        source_path = _require_contract_regular_file(
            f"Approved report table {table_id!r}",
            declared_path,
        )
        source_key = (str(source_path), declared_sha256)
        if source_key in observed_sources:
            _fail(
                "A physical report-table source may be approved only once: "
                f"{declared_path}"
            )
        observed_sources.add(source_key)
        table_snapshot, observed_row_count = (
            _capture_report_table_snapshot(
                f"Approved report table {table_id!r}",
                source_path,
            )
        )
        if (
            table_snapshot.sha256 != declared_sha256
            or table_snapshot.size_bytes != source["size_bytes"]
            or observed_row_count != declared_row_count
        ):
            _fail(
                f"Approved report table {table_id!r} current file differs "
                "from its exact artifact and approval record"
            )
        snapshots_by_path[source_path] = table_snapshot
        records.append(
            {
                "table_id": table_id,
                "artifact_id": row["artifact_id"],
                "role": role,
                "title": title,
                "path": declared_path,
                "sha256": declared_sha256,
                "row_count": declared_row_count,
                "display_row_limit": display_row_limit,
                "approval": {
                    "status": "approved",
                    "policy_version": row["approval_policy_version"],
                    "approved_by": row["approved_by"],
                    "approved_at": _parse_approval_timestamp(
                        row["approved_at"],
                        build_started_at,
                    ),
                },
            }
        )
    _verify_file_snapshot(
        "Report-table approvals manifest",
        manifest_snapshot,
    )
    for snapshot in snapshots_by_path.values():
        _verify_report_table_snapshot(snapshot)
    return (
        manifest_path,
        manifest_snapshot,
        records,
        tuple(snapshots_by_path.values()),
    )


def _assert_output_directory_identity(paths: OutputPaths) -> None:
    try:
        metadata = paths.output_dir.lstat()
        resolved = paths.output_dir.resolve(strict=True)
    except OSError as exc:
        _fail(f"Run output directory is unavailable: {paths.output_dir}: {exc}")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or resolved != paths.output_dir
        or metadata.st_dev != paths.output_dir_device
        or metadata.st_ino != paths.output_dir_inode
    ):
        _fail(
            "Run output directory identity changed after initial validation: "
            f"{paths.output_dir}"
        )


def _path_hash(
    path: Path,
    *,
    sha256: str,
    size_bytes: int,
    row_count: int | None,
    media_type: str,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256,
        "size_bytes": size_bytes,
        "row_count": row_count,
        "media_type": media_type,
    }


def _canonical_key(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _stable_unique(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    observed: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        key = _canonical_key(record)
        if key in observed:
            continue
        observed.add(key)
        result.append(record)
    return result


def _parse_history(
    receipt: Mapping[str, str],
    *,
    id_field: str,
    supersedes_field: str,
    history_field: str,
) -> tuple[str, list[str]]:
    attempt_id = receipt[id_field]
    history = [value for value in receipt[history_field].split(",") if value]
    if (
        not contracts.SAFE_ID_RE.fullmatch(attempt_id)
        or not history
        or history[-1] != attempt_id
        or len(history) != len(set(history))
        or any(not contracts.SAFE_ID_RE.fullmatch(value) for value in history)
    ):
        _fail(f"Receipt has an invalid {history_field}")
    expected_previous = history[-2] if len(history) > 1 else ""
    if receipt[supersedes_field] != expected_previous:
        _fail(f"Receipt has an invalid {supersedes_field}")
    return attempt_id, history


def _receipt_int(
    receipt: Mapping[str, str],
    field: str,
) -> int:
    value = receipt[field]
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        _fail(f"Receipt field {field} is not a non-negative integer")
    return int(value)


def _new_attempt_id(timestamp: str) -> str:
    compact = re.sub(r"[^0-9]", "", timestamp)[:14]
    return f"run-summary-{compact}-{uuid.uuid4().hex[:12]}"


def _load_input_transaction(
    *,
    run_id: str,
    artifact_receipt_value: Path,
    output_root_value: Path,
) -> tuple[
    Path,
    str,
    dict[str, str],
    Path,
    dict[str, Any],
    str,
    Path,
    str,
    list[dict[str, str]],
    Path,
    str,
    list[dict[str, str]],
    Path,
    list[Path],
    list[str],
    tuple[FileSnapshot, ...],
    list[dict[str, Any]],
    OutputPaths,
]:
    if not contracts.SAFE_ID_RE.fullmatch(run_id):
        _fail("run_id must match [A-Za-z0-9][A-Za-z0-9._-]*")
    artifact_receipt_path = _require_regular_file(
        "Artifact receipt", artifact_receipt_value
    )
    receipt_rows = adapter.read_exact_tsv(
        artifact_receipt_path,
        adapter.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )
    receipt = receipt_rows[0]
    if receipt["run_id"] != run_id:
        _fail("Artifact receipt run_id differs from --run-id")
    if receipt["transaction_state"] != "complete":
        _fail("Artifact receipt transaction_state is not complete")

    raw_output_root = _resolved_path(output_root_value)
    if raw_output_root.is_symlink() or not raw_output_root.is_dir():
        _fail(
            "Artifact output root must already be a regular directory: "
            f"{raw_output_root}"
        )
    try:
        output_root = raw_output_root.resolve(strict=True)
    except OSError as exc:
        _fail(f"Artifact output root cannot be resolved: {raw_output_root}: {exc}")
    raw_output_dir = output_root / run_id
    if raw_output_dir.is_symlink() or not raw_output_dir.is_dir():
        _fail(
            "Artifact output directory must already be a regular directory: "
            f"{raw_output_dir}"
        )
    try:
        output_dir = raw_output_dir.resolve(strict=True)
        output_dir_metadata = output_dir.lstat()
    except OSError as exc:
        _fail(f"Artifact output directory cannot be resolved: {raw_output_dir}: "
              f"{exc}")
    if (
        output_dir.parent != output_root
        or not stat.S_ISDIR(output_dir_metadata.st_mode)
    ):
        _fail(
            "Artifact output directory must resolve directly beneath the "
            f"explicit output root: {raw_output_dir}"
        )
    if artifact_receipt_path.parent != output_dir:
        _fail(
            "Artifact receipt must be the exact receipt in "
            f"--output-root/<run_id>/: {artifact_receipt_path}"
        )
    expected_receipt_name = f"{run_id}.artifact_receipt.tsv"
    if artifact_receipt_path.name != expected_receipt_name:
        _fail(f"Artifact receipt basename must be {expected_receipt_name}")

    run_contract_path = _require_regular_file(
        "Run contract", receipt["run_contract_path"]
    )
    run_contract, run_contract_file_sha256 = adapter.load_run_contract(
        run_contract_path
    )
    inventory_path = _require_regular_file(
        "Artifact inventory", receipt["inventory_path"]
    )
    inventory_sha256 = contracts.sha256_file(inventory_path)
    inventory_rows = contracts.validate_inventory(inventory_path)
    artifacts_path = _require_regular_file(
        "Artifact index", receipt["artifacts_index_path"]
    )
    if artifacts_path.parent != output_dir or artifacts_path.name != (
        f"{run_id}.artifacts.tsv"
    ):
        _fail("Artifact index path is outside the exact run output directory")
    records_dir = output_dir / "records"
    index_rows = adapter.read_exact_tsv(
        artifacts_path, adapter.ARTIFACT_INDEX_HEADER
    )

    record_paths: list[Path] = []
    record_hashes: list[str] = []
    artifacts: list[dict[str, Any]] = []
    for row in index_rows:
        record_path = _require_regular_file(
            f"Artifact record {row['artifact_id']}", row["record_path"]
        )
        record_paths.append(record_path)
        record_hashes.append(contracts.sha256_file(record_path))
        artifacts.append(
            contracts.load_json_object(
                record_path, f"artifact record {row['artifact_id']}"
            )
        )

    snapshots: list[FileSnapshot] = []
    receipt_payload, receipt_snapshot = _capture_file_snapshot(
        "Artifact receipt", artifact_receipt_path
    )
    if _read_exact_tsv_bytes(
        label="Artifact receipt",
        path=artifact_receipt_path,
        payload=receipt_payload,
        header=adapter.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0] != receipt:
        _fail("Artifact receipt changed between parsing and snapshot capture")
    snapshots.append(receipt_snapshot)

    run_contract_payload, run_contract_snapshot = _capture_file_snapshot(
        "Run contract", run_contract_path
    )
    if (
        _load_json_bytes(
            label="Run contract",
            path=run_contract_path,
            payload=run_contract_payload,
        )
        != run_contract
        or run_contract_snapshot.sha256 != run_contract_file_sha256
    ):
        _fail("Run contract changed between validation and snapshot capture")
    snapshots.append(run_contract_snapshot)

    inventory_payload, inventory_snapshot = _capture_file_snapshot(
        "Artifact inventory", inventory_path
    )
    if (
        _read_exact_tsv_bytes(
            label="Artifact inventory",
            path=inventory_path,
            payload=inventory_payload,
            header=contracts.INVENTORY_HEADER,
        )
        != inventory_rows
        or inventory_snapshot.sha256 != inventory_sha256
    ):
        _fail("Artifact inventory changed between validation and snapshot capture")
    snapshots.append(inventory_snapshot)

    artifacts_payload, artifacts_snapshot = _capture_file_snapshot(
        "Artifact index", artifacts_path
    )
    if (
        _read_exact_tsv_bytes(
            label="Artifact index",
            path=artifacts_path,
            payload=artifacts_payload,
            header=adapter.ARTIFACT_INDEX_HEADER,
        )
        != index_rows
    ):
        _fail("Artifact index changed between parsing and snapshot capture")
    snapshots.append(artifacts_snapshot)

    for row, record_path, record_hash, artifact in zip(
        index_rows,
        record_paths,
        record_hashes,
        artifacts,
        strict=True,
    ):
        record_payload, record_snapshot = _capture_file_snapshot(
            f"Artifact record {row['artifact_id']}", record_path
        )
        if (
            _load_json_bytes(
                label=f"Artifact record {row['artifact_id']}",
                path=record_path,
                payload=record_payload,
            )
            != artifact
            or record_snapshot.sha256 != record_hash
        ):
            _fail(
                "Artifact record changed between parsing and snapshot capture: "
                f"{row['artifact_id']}"
            )
        snapshots.append(record_snapshot)

    adapter.validate_published_transaction(
        run_id=run_id,
        run_contract=run_contract,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=artifact_receipt_path,
        require_current_source_locations=True,
    )
    for snapshot in snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)

    paths = OutputPaths(
        output_dir=output_dir,
        output_dir_device=output_dir_metadata.st_dev,
        output_dir_inode=output_dir_metadata.st_ino,
        summary_json=output_dir / f"{run_id}.run_summary.json",
        summary_tsv=output_dir / f"{run_id}.run_summary.tsv",
        qc_summary=output_dir / f"{run_id}.qc_summary.tsv",
        receipt=output_dir / f"{run_id}.run_summary_receipt.tsv",
        lock=output_dir / f".{run_id}.run-summary.lock",
    )
    return (
        artifact_receipt_path,
        receipt_snapshot.sha256,
        receipt,
        run_contract_path,
        run_contract,
        run_contract_file_sha256,
        inventory_path,
        inventory_sha256,
        inventory_rows,
        artifacts_path,
        artifacts_snapshot.sha256,
        index_rows,
        records_dir,
        record_paths,
        record_hashes,
        tuple(snapshots),
        artifacts,
        paths,
    )


def _artifact_statuses(artifact: Mapping[str, Any]) -> dict[str, str]:
    return contracts.artifact_status_dimensions(dict(artifact))


def _build_expected_scopes(
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    grouped: OrderedDict[
        tuple[str, str, str], list[dict[str, Any]]
    ] = OrderedDict()
    for artifact in artifacts:
        scope = artifact["scope"]
        key = (
            scope["step_id"],
            scope["scope_type"],
            scope["scope_id"],
        )
        grouped.setdefault(key, []).append(artifact)

    expected_scopes: list[dict[str, Any]] = []
    artifact_scope_order: dict[str, int] = {}
    for scope_order, (key, scope_artifacts) in enumerate(grouped.items(), 1):
        warnings = _stable_unique(
            issue
            for artifact in scope_artifacts
            for issue in artifact["warnings"]
        )
        errors = _stable_unique(
            issue
            for artifact in scope_artifacts
            for issue in artifact["errors"]
        )
        status_values = {
            field: contracts.aggregate_equal_or_mixed(
                _artifact_statuses(artifact)[field]
                for artifact in scope_artifacts
            )
            for field in (
                "implementation_status",
                "local_test_status",
                "runtime_validation_status",
                "cluster_dry_run_status",
                "cluster_proof_status",
            )
        }
        expected_scopes.append(
            {
                "scope": {
                    "step_id": key[0],
                    "scope_type": key[1],
                    "scope_id": key[2],
                },
                "artifact_ids": [
                    artifact["artifact_id"] for artifact in scope_artifacts
                ],
                "aggregate_state": contracts.aggregate_artifact_state(
                    scope_artifacts
                ),
                **status_values,
                "warnings": warnings,
                "errors": errors,
            }
        )
        for artifact in scope_artifacts:
            artifact_scope_order[artifact["artifact_id"]] = scope_order
    return expected_scopes, artifact_scope_order


def _build_attempts(
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    attempts: list[dict[str, Any]] = []
    attempt_index: dict[str, dict[str, Any]] = {}
    superseded: list[str] = []
    for artifact in artifacts:
        for attempt in artifact["attempts"]:
            attempt_id = attempt["attempt_id"]
            prior = attempt_index.get(attempt_id)
            if prior is not None:
                if prior != attempt:
                    _fail(
                        f"Artifact attempt {attempt_id!r} has conflicting "
                        "definitions"
                    )
                continue
            copy = dict(attempt)
            attempt_index[attempt_id] = copy
            attempts.append(copy)
            parent = attempt["supersedes_attempt_id"]
            if parent is not None and parent not in superseded:
                superseded.append(parent)
    return attempts, superseded


def _build_rollup(
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    states = Counter(
        contracts.artifact_rollup_state(artifact) for artifact in artifacts
    )
    result: dict[str, Any] = {
        "expected_artifact_count": len(artifacts),
        "complete_artifact_count": states["complete"],
        "missing_artifact_count": states["missing"],
        "incomplete_artifact_count": states["incomplete"],
        "failed_artifact_count": states["failed"],
        "externally_unavailable_artifact_count": states[
            "externally_unavailable"
        ],
    }
    for field in (
        "implementation_status",
        "local_test_status",
        "runtime_validation_status",
        "cluster_dry_run_status",
        "cluster_proof_status",
    ):
        result[field] = contracts.aggregate_equal_or_mixed(
            _artifact_statuses(artifact)[field] for artifact in artifacts
        )
    return result


def _build_tools(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _stable_unique(
        tool for artifact in artifacts for tool in artifact["tools"]
    )


def _build_qc_metrics(
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str]]:
    counts = Counter(
        metric["metric_id"]
        for artifact in artifacts
        for metric in artifact["metrics"]
    )
    metrics = [
        dict(metric)
        for artifact in artifacts
        for metric in artifact["metrics"]
        if counts[metric["metric_id"]] == 1
    ]
    duplicate_ids = {
        metric_id for metric_id, count in counts.items() if count > 1
    }
    return metrics, duplicate_ids


def _default_scientific_review() -> dict[str, Any]:
    return {
        "record_state": "missing",
        "source": None,
        "record": None,
        "overall_status": "evidence_incomplete",
    }


def _build_limitations(
    *,
    artifacts: list[dict[str, Any]],
    scientific_review: Mapping[str, Any],
) -> list[dict[str, Any]]:
    def generated_id(base: str, existing: set[str]) -> str:
        candidate = base
        counter = 1
        while candidate in existing:
            candidate = f"{base}.generated{counter}"
            counter += 1
        existing.add(candidate)
        return candidate

    record = scientific_review.get("record")
    limitations = (
        [dict(item) for item in record["limitations"]]
        if isinstance(record, Mapping)
        else [
            {
                "limitation_id": "scientific_review_not_supplied",
                "status": "open",
                "description": (
                    "No explicit committed Step 09c review summary was "
                    "supplied to the run-summary builder."
                ),
                "impact": (
                    "Scientific review remains incomplete and biological "
                    "interpretation is not permitted."
                ),
                "evidence_ids": [],
            }
        ]
    )
    used_ids = {
        limitation["limitation_id"] for limitation in limitations
    }
    incomplete_required = [
        artifact["artifact_id"]
        for artifact in artifacts
        if artifact["expectation"]["required"]
        and contracts.artifact_rollup_state(artifact) != "complete"
    ]
    if incomplete_required:
        limitations.append(
            {
                "limitation_id": generated_id(
                    "required_artifacts_not_complete",
                    used_ids,
                ),
                "status": "open",
                "description": (
                    "One or more required expected artifacts are not complete."
                ),
                "impact": (
                    "The run summary is structurally complete, but downstream "
                    "consumers must retain the explicit incomplete states."
                ),
                "evidence_ids": [],
            }
        )
    return _stable_unique(limitations)


def _issue_for_duplicate_metrics(
    duplicate_ids: set[str],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not duplicate_ids:
        return None
    related = [
        artifact["artifact_id"]
        for artifact in artifacts
        if any(
            metric["metric_id"] in duplicate_ids
            for metric in artifact["metrics"]
        )
    ]
    return {
        "code": "duplicate_qc_metric_ids_not_promoted",
        "message": (
            "Repeated artifact metric IDs remain available inside artifacts "
            "and the QC TSV but are not copied into the globally unique "
            "top-level qc_metrics array."
        ),
        "related_artifact_ids": related,
        "evidence": [],
    }


def _build_document(
    *,
    run_id: str,
    run_contract: dict[str, Any],
    inventory_path: Path,
    inventory_sha256: str,
    inventory_size_bytes: int,
    inventory_rows: list[dict[str, str]],
    artifact_receipt_path: Path,
    artifact_receipt_sha256: str,
    artifact_receipt_size_bytes: int,
    artifact_receipt: dict[str, str],
    artifacts: list[dict[str, Any]],
    scientific_review: dict[str, Any],
    approved_report_tables: list[dict[str, Any]],
    report_table_approvals_source: dict[str, Any] | None,
    generated_at: str,
    git_commit: str,
) -> tuple[dict[str, Any], dict[str, int]]:
    expected_scopes, artifact_scope_order = _build_expected_scopes(artifacts)
    attempts, superseded_attempt_ids = _build_attempts(artifacts)
    qc_metrics, duplicate_metric_ids = _build_qc_metrics(artifacts)
    warnings = _stable_unique(
        issue for artifact in artifacts for issue in artifact["warnings"]
    )
    duplicate_warning = _issue_for_duplicate_metrics(
        duplicate_metric_ids, artifacts
    )
    if duplicate_warning is not None:
        warnings.append(duplicate_warning)
    if scientific_review["record_state"] != "present":
        warnings.append(
            {
                "code": "scientific_review_not_supplied",
                "message": (
                    "No explicit committed Step 09c review was normalized; "
                    "science status remains evidence_incomplete."
                ),
                "related_artifact_ids": [],
                "evidence": [],
            }
        )
    errors = _stable_unique(
        issue for artifact in artifacts for issue in artifact["errors"]
    )
    parameters = {
        "artifact_parameters": [
            {
                "artifact_id": artifact["artifact_id"],
                "values": artifact["parameters"],
            }
            for artifact in artifacts
            if artifact["parameters"]
        ],
        "adapter_transaction": {
            "adapter_attempt_id": artifact_receipt["adapter_attempt_id"],
            "supersedes_adapter_attempt_id": (
                artifact_receipt["supersedes_adapter_attempt_id"] or None
            ),
            "adapter_attempt_history": [
                value
                for value in artifact_receipt[
                    "adapter_attempt_history"
                ].split(",")
                if value
            ],
        },
        "report_table_approvals": report_table_approvals_source,
    }
    document = {
        "schema_name": "norad.run_summary",
        "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "record_type": "run_summary",
        "run_id": run_id,
        "run_contract": run_contract,
        "summary_state": "complete",
        "generated_at": generated_at,
        "inventory": _path_hash(
            inventory_path,
            sha256=inventory_sha256,
            size_bytes=inventory_size_bytes,
            row_count=len(inventory_rows),
            media_type="text/tab-separated-values",
        ),
        "artifact_receipt": _path_hash(
            artifact_receipt_path,
            sha256=artifact_receipt_sha256,
            size_bytes=artifact_receipt_size_bytes,
            row_count=1,
            media_type="text/tab-separated-values",
        ),
        "attempts": attempts,
        "superseded_attempt_ids": superseded_attempt_ids,
        "expected_scopes": expected_scopes,
        "artifacts": artifacts,
        "computational_rollup": _build_rollup(artifacts),
        "scientific_review": scientific_review,
        "science_status": scientific_review["overall_status"],
        "tools": _build_tools(artifacts),
        "parameters": parameters,
        "qc_metrics": qc_metrics,
        "limitations": _build_limitations(
            artifacts=artifacts,
            scientific_review=scientific_review,
        ),
        "approved_report_tables": approved_report_tables,
        "candidate_terminology": "CMH-ranked candidates",
        "warnings": _stable_unique(warnings),
        "errors": errors,
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": git_commit,
            "created_at": generated_at,
        },
    }
    return document, artifact_scope_order


def _metric_value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def _build_summary_rows(
    document: Mapping[str, Any],
    artifact_scope_order: Mapping[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_order, artifact in enumerate(document["artifacts"], 1):
        source = artifact["source"]
        statuses = _artifact_statuses(artifact)
        rows.append(
            {
                "run_id": document["run_id"],
                "run_contract_sha256": document["run_contract"][
                    "run_contract_sha256"
                ],
                "summary_state": document["summary_state"],
                "science_status": document["science_status"],
                "artifact_order": artifact_order,
                "scope_order": artifact_scope_order[
                    artifact["artifact_id"]
                ],
                "step_id": artifact["scope"]["step_id"],
                "scope_type": artifact["scope"]["scope_type"],
                "scope_id": artifact["scope"]["scope_id"],
                "artifact_id": artifact["artifact_id"],
                "adapter": artifact["adapter"],
                "required": (
                    "true" if artifact["expectation"]["required"] else "false"
                ),
                "availability_status": artifact["availability_status"],
                "completion_status": artifact["completion_status"],
                "rollup_state": contracts.artifact_rollup_state(artifact),
                **statuses,
                "source_path": "" if source is None else source["path"],
                "source_sha256": "" if source is None else source["sha256"],
                "source_row_count": (
                    ""
                    if source is None or source["row_count"] is None
                    else source["row_count"]
                ),
                "selected_attempt_id": artifact["selected_attempt_id"] or "",
                "warning_count": len(artifact["warnings"]),
                "error_count": len(artifact["errors"]),
            }
        )
    return rows


def _build_qc_rows(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_order, artifact in enumerate(document["artifacts"], 1):
        for metric_order, metric in enumerate(artifact["metrics"], 1):
            value = metric["value"]
            rows.append(
                {
                    "run_id": document["run_id"],
                    "artifact_order": artifact_order,
                    "metric_order": metric_order,
                    "step_id": artifact["scope"]["step_id"],
                    "scope_type": artifact["scope"]["scope_type"],
                    "scope_id": artifact["scope"]["scope_id"],
                    "artifact_id": artifact["artifact_id"],
                    "metric_id": metric["metric_id"],
                    "name": metric["name"],
                    "value": json.dumps(
                        value,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                        allow_nan=False,
                    ),
                    "value_type": _metric_value_type(value),
                    "unit": metric["unit"] or "",
                    "status": metric["status"],
                    "source_artifact_id": (
                        metric["source_artifact_id"] or ""
                    ),
                }
            )
    return rows


def _validate_document(
    document: dict[str, Any],
    inventory_rows: list[dict[str, str]],
    inventory_path: Path,
) -> None:
    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["run-summary"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(
            str(part) for part in error.absolute_path
        ),
    )
    if errors:
        details = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: "
            f"{error.message}"
            for error in errors
        )
        _fail(f"Run summary failed Draft 2020-12 validation:\n{details}")
    try:
        contracts.validate_run_summary_semantics(document)
        contracts.reconcile_document_inventory(
            "run-summary", document, inventory_rows, inventory_path
        )
    except contracts.ContractValidationError as exc:
        _fail(f"Run summary failed semantic validation: {exc}")


def _load_existing_summary_receipt(
    paths: OutputPaths,
) -> tuple[dict[str, str] | None, str | None]:
    states = tuple(path.exists() or path.is_symlink() for path in paths.ordered_outputs)
    if any(states) and not all(states):
        _fail(
            "Existing run-summary output set is partial; preserve it for "
            f"recovery: {paths.output_dir}"
        )
    if not any(states):
        return None, None
    for path in paths.ordered_outputs:
        if path.is_symlink() or not path.is_file():
            _fail(f"Existing run-summary output is unsafe: {path}")
    receipt = adapter.read_exact_tsv(
        paths.receipt,
        RUN_SUMMARY_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    return receipt, contracts.sha256_file(paths.receipt)


def _validate_existing_summary(
    *,
    paths: OutputPaths,
    receipt: Mapping[str, str],
    expected_run_id: str,
    expected_run_contract: Mapping[str, Any],
) -> dict[str, Any]:
    if receipt["run_id"] != expected_run_id:
        _fail("Existing run-summary receipt has the wrong run_id")
    for field in RUN_CONTRACT_FIELDS:
        if receipt[field] != str(expected_run_contract[field]):
            _fail(
                "Existing run-summary receipt has a different immutable "
                f"run-contract field: {field}"
            )
    if receipt["transaction_state"] != "complete":
        _fail("Existing run-summary receipt is not complete")
    for field, expected in (
        ("producer", PRODUCER),
        ("run_summary_schema_version", RUN_SUMMARY_SCHEMA_VERSION),
        ("run_summary_tsv_schema_version", RUN_SUMMARY_TSV_SCHEMA_VERSION),
        ("qc_summary_tsv_schema_version", QC_SUMMARY_TSV_SCHEMA_VERSION),
        (
            "run_summary_receipt_schema_version",
            RUN_SUMMARY_RECEIPT_SCHEMA_VERSION,
        ),
    ):
        if receipt[field] != expected:
            _fail(f"Existing run-summary receipt field is invalid: {field}")
    if receipt["producer_version"] not in {
        LEGACY_PRODUCER_VERSION,
        PRODUCER_VERSION,
    }:
        _fail(
            "Existing run-summary receipt field is invalid: producer_version"
        )
    _parse_history(
        receipt,
        id_field="run_summary_attempt_id",
        supersedes_field="supersedes_run_summary_attempt_id",
        history_field="run_summary_attempt_history",
    )
    if not re.fullmatch(r"[0-9a-f]{40,64}", receipt["git_commit"]):
        _fail("Existing run-summary receipt Git commit is invalid")
    try:
        started_at = datetime.fromisoformat(
            receipt["started_at"].replace("Z", "+00:00")
        )
        finished_at = datetime.fromisoformat(
            receipt["finished_at"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RunSummaryError(
            "Existing run-summary receipt timestamps are invalid"
        ) from exc
    if (
        started_at.tzinfo is None
        or finished_at.tzinfo is None
        or finished_at < started_at
    ):
        _fail("Existing run-summary receipt timestamp ordering is invalid")
    expected_paths = {
        "run_summary_json_path": paths.summary_json,
        "run_summary_tsv_path": paths.summary_tsv,
        "qc_summary_tsv_path": paths.qc_summary,
    }
    for field, expected_path in expected_paths.items():
        if receipt[field] != str(expected_path):
            _fail(f"Existing run-summary receipt path is invalid: {field}")
    for path_field, hash_field in (
        ("run_summary_json_path", "run_summary_json_sha256"),
        ("run_summary_tsv_path", "run_summary_tsv_sha256"),
        ("qc_summary_tsv_path", "qc_summary_tsv_sha256"),
    ):
        path = _require_regular_file(
            f"Existing {path_field}", receipt[path_field]
        )
        if contracts.sha256_file(path) != receipt[hash_field]:
            _fail(f"Existing run-summary output hash differs: {path}")

    document = contracts.load_json_object(
        paths.summary_json, "existing run summary"
    )
    if paths.summary_json.read_bytes() != adapter.canonical_json_bytes(document):
        _fail("Existing run-summary JSON is not canonical")
    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["run-summary"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    schema_errors = list(validator.iter_errors(document))
    if schema_errors:
        _fail("Existing run-summary JSON fails its schema")
    try:
        contracts.validate_run_summary_semantics(document)
    except contracts.ContractValidationError as exc:
        _fail(f"Existing run-summary JSON is semantically invalid: {exc}")
    if receipt["git_commit"] != document["provenance"]["git_commit"]:
        _fail(
            "Existing run-summary receipt Git commit differs from its "
            "canonical JSON provenance"
        )
    if (
        receipt["producer"] != document["provenance"]["producer"]
        or receipt["producer_version"]
        != document["provenance"]["producer_version"]
    ):
        _fail(
            "Existing run-summary receipt producer differs from its "
            "canonical JSON provenance"
        )
    adapter_transaction = document["parameters"]["adapter_transaction"]
    if (
        receipt["artifact_adapter_attempt_id"]
        != adapter_transaction["adapter_attempt_id"]
    ):
        _fail(
            "Existing run-summary receipt adapter attempt differs from its "
            "canonical JSON provenance"
        )
    expected_summary_rows = _build_summary_rows(
        document,
        {
            artifact_id: scope_order
            for scope_order, scope in enumerate(
                document["expected_scopes"], 1
            )
            for artifact_id in scope["artifact_ids"]
        },
    )
    if paths.summary_tsv.read_bytes() != adapter.tsv_bytes(
        RUN_SUMMARY_HEADER, expected_summary_rows
    ):
        _fail("Existing run-summary TSV differs from its canonical JSON")
    expected_qc_rows = _build_qc_rows(document)
    if paths.qc_summary.read_bytes() != adapter.tsv_bytes(
        QC_SUMMARY_HEADER, expected_qc_rows
    ):
        _fail("Existing QC summary TSV differs from its canonical JSON")
    if receipt["run_summary_tsv_row_count"] != str(
        len(expected_summary_rows)
    ):
        _fail("Existing run-summary TSV row count is invalid")
    if receipt["qc_summary_tsv_row_count"] != str(len(expected_qc_rows)):
        _fail("Existing QC summary TSV row count is invalid")
    if receipt["published_output_count"] != "4":
        _fail("Existing run-summary receipt published_output_count is invalid")
    if _receipt_int(receipt, "run_summary_json_size_bytes") != (
        paths.summary_json.stat().st_size
    ):
        _fail("Existing run-summary JSON byte size is invalid")
    if _receipt_int(receipt, "artifact_record_count") != len(
        document["artifacts"]
    ):
        _fail("Existing run-summary artifact count is invalid")
    if _receipt_int(receipt, "inventory_row_count") != (
        document["inventory"]["row_count"]
    ):
        _fail("Existing run-summary inventory row count is invalid")
    if receipt["inventory_path"] != document["inventory"]["path"] or (
        receipt["inventory_sha256"] != document["inventory"]["sha256"]
    ):
        _fail("Existing receipt inventory provenance differs from JSON")
    if (
        receipt["artifact_receipt_path"]
        != document["artifact_receipt"]["path"]
        or receipt["artifact_receipt_sha256"]
        != document["artifact_receipt"]["sha256"]
    ):
        _fail("Existing adapter-receipt provenance differs from JSON")
    for field in (
        "inventory_sha256",
        "artifacts_index_sha256",
        "artifact_receipt_sha256",
        "record_set_sha256",
        "run_summary_json_sha256",
        "run_summary_tsv_sha256",
        "qc_summary_tsv_sha256",
    ):
        if not adapter.SHA256_RE.fullmatch(receipt[field]):
            _fail(f"Existing run-summary receipt hash is invalid: {field}")
    review = document["scientific_review"]
    if review["record_state"] == "present":
        if (
            receipt["science_review_summary_path"]
            != review["source"]["path"]
            or receipt["science_review_summary_sha256"]
            != review["source"]["sha256"]
        ):
            _fail(
                "Existing science-review provenance differs between receipt "
                "and JSON"
            )
    elif (
        receipt["science_review_summary_path"]
        or receipt["science_review_summary_sha256"]
    ):
        _fail(
            "Existing receipt claims a science summary while JSON has none"
        )
    approval_source = document["parameters"].get(
        "report_table_approvals",
    )
    if receipt["producer_version"] == LEGACY_PRODUCER_VERSION:
        if approval_source is not None or document["approved_report_tables"]:
            _fail(
                "Legacy run-summary predecessor must not claim report-table "
                "approvals"
            )
    elif "report_table_approvals" not in document["parameters"]:
        _fail(
            "Current run-summary predecessor is missing explicit "
            "report-table approval provenance"
        )
    elif approval_source is None:
        if document["approved_report_tables"]:
            _fail(
                "Existing run summary has approvals without their manifest "
                "provenance"
            )
    elif approval_source["row_count"] != len(
        document["approved_report_tables"]
    ):
        _fail(
            "Existing report-table approval provenance row count differs "
            "from its canonical JSON records"
        )
    if receipt["summary_state"] != document["summary_state"] or (
        receipt["science_status"] != document["science_status"]
    ):
        _fail("Existing run-summary receipt status differs from JSON")
    return document


def _build_receipt_row(
    *,
    run_id: str,
    run_contract: Mapping[str, Any],
    artifact_receipt_path: Path,
    artifact_receipt_sha256: str,
    artifact_receipt: Mapping[str, str],
    inventory_path: Path,
    inventory_sha256: str,
    inventory_row_count: int,
    artifacts_path: Path,
    artifacts_sha256: str,
    summary_json_path: Path,
    summary_json_bytes: bytes,
    summary_tsv_path: Path,
    summary_tsv_bytes: bytes,
    summary_tsv_row_count: int,
    qc_summary_path: Path,
    qc_summary_bytes: bytes,
    qc_summary_row_count: int,
    science_review_summary_path: Path | None,
    science_review_summary_sha256: str | None,
    document: Mapping[str, Any],
    attempt_id: str,
    previous_attempt_id: str | None,
    previous_attempt_history: Sequence[str],
    git_commit: str,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        **{field: run_contract[field] for field in RUN_CONTRACT_FIELDS},
        "artifact_receipt_path": str(artifact_receipt_path),
        "artifact_receipt_sha256": artifact_receipt_sha256,
        "artifact_adapter_attempt_id": artifact_receipt[
            "adapter_attempt_id"
        ],
        "inventory_path": str(inventory_path),
        "inventory_sha256": inventory_sha256,
        "inventory_row_count": inventory_row_count,
        "artifacts_index_path": str(artifacts_path),
        "artifacts_index_sha256": artifacts_sha256,
        "artifact_record_count": len(document["artifacts"]),
        "record_set_sha256": artifact_receipt["record_set_sha256"],
        "run_summary_schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "run_summary_tsv_schema_version": RUN_SUMMARY_TSV_SCHEMA_VERSION,
        "qc_summary_tsv_schema_version": QC_SUMMARY_TSV_SCHEMA_VERSION,
        "run_summary_receipt_schema_version": (
            RUN_SUMMARY_RECEIPT_SCHEMA_VERSION
        ),
        "run_summary_json_path": str(summary_json_path),
        "run_summary_json_sha256": adapter.sha256_bytes(summary_json_bytes),
        "run_summary_json_size_bytes": len(summary_json_bytes),
        "run_summary_tsv_path": str(summary_tsv_path),
        "run_summary_tsv_sha256": adapter.sha256_bytes(summary_tsv_bytes),
        "run_summary_tsv_row_count": summary_tsv_row_count,
        "qc_summary_tsv_path": str(qc_summary_path),
        "qc_summary_tsv_sha256": adapter.sha256_bytes(qc_summary_bytes),
        "qc_summary_tsv_row_count": qc_summary_row_count,
        "science_review_summary_path": (
            ""
            if science_review_summary_path is None
            else document["scientific_review"]["source"]["path"]
        ),
        "science_review_summary_sha256": (
            science_review_summary_sha256 or ""
        ),
        "summary_state": document["summary_state"],
        "science_status": document["science_status"],
        "published_output_count": 4,
        "run_summary_attempt_id": attempt_id,
        "supersedes_run_summary_attempt_id": previous_attempt_id or "",
        "run_summary_attempt_history": ",".join(
            [*previous_attempt_history, attempt_id]
        ),
        "producer": PRODUCER,
        "producer_version": PRODUCER_VERSION,
        "git_commit": git_commit,
        "started_at": started_at,
        "finished_at": finished_at,
        "transaction_state": "complete",
    }


def prepare_context(arguments: argparse.Namespace) -> BuildContext:
    (
        artifact_receipt_path,
        artifact_receipt_sha256,
        artifact_receipt,
        run_contract_path,
        run_contract,
        run_contract_file_sha256,
        inventory_path,
        inventory_sha256,
        inventory_rows,
        artifacts_path,
        artifacts_sha256,
        index_rows,
        records_dir,
        record_paths,
        record_hashes,
        input_snapshots,
        artifacts,
        paths,
    ) = _load_input_transaction(
        run_id=arguments.run_id,
        artifact_receipt_value=arguments.artifact_receipt,
        output_root_value=arguments.output_root,
    )
    snapshot_by_path = {
        snapshot.path: snapshot for snapshot in input_snapshots
    }
    artifact_receipt_snapshot = snapshot_by_path[artifact_receipt_path]
    inventory_snapshot = snapshot_by_path[inventory_path]
    _parse_history(
        artifact_receipt,
        id_field="adapter_attempt_id",
        supersedes_field="supersedes_adapter_attempt_id",
        history_field="adapter_attempt_history",
    )
    git_commit = adapter.get_git_commit()
    generated_at = artifact_receipt["finished_at"]
    started_at = adapter.utc_now()
    finished_at = started_at

    science_path: Path | None = None
    science_sha256: str | None = None
    scientific_review = _default_scientific_review()
    if arguments.science_review_summary is not None:
        science_path = _require_regular_file(
            "Science-review summary", arguments.science_review_summary
        )
        _science_payload, science_snapshot = _capture_file_snapshot(
            "Science-review summary", science_path
        )
        science_sha256 = science_snapshot.sha256
        try:
            record = science.normalize_scientific_review(
                summary_path=science_path,
                artifacts=artifacts,
                run_id=arguments.run_id,
                run_contract=run_contract,
                generated_at=generated_at,
                git_commit=git_commit,
            )
        except science.RunSummaryScienceError as exc:
            _fail(str(exc))
        _verify_file_snapshot("Science-review summary", science_snapshot)
        input_snapshots = (*input_snapshots, science_snapshot)
        source = record["review_summary"]
        scientific_review = {
            "record_state": "present",
            "source": dict(source),
            "record": record,
            "overall_status": record["scientific_state"]["overall_status"],
        }

    approvals_path: Path | None = None
    approvals_sha256: str | None = None
    approval_records: list[dict[str, Any]] = []
    approval_table_snapshots: tuple[FileSnapshot, ...] = ()
    approval_source: dict[str, Any] | None = None
    if arguments.report_table_approvals is not None:
        (
            approvals_path,
            approvals_snapshot,
            approval_records,
            approval_table_snapshots,
        ) = _normalize_report_table_approvals(
            manifest_value=arguments.report_table_approvals,
            run_id=arguments.run_id,
            run_contract=run_contract,
            artifacts=artifacts,
            scientific_review=scientific_review,
            build_started_at=started_at,
        )
        approvals_sha256 = approvals_snapshot.sha256
        input_snapshots = (*input_snapshots, approvals_snapshot)
        approval_source = _path_hash(
            approvals_path,
            sha256=approvals_snapshot.sha256,
            size_bytes=approvals_snapshot.size_bytes,
            row_count=len(approval_records),
            media_type="text/tab-separated-values",
        )

    document, artifact_scope_order = _build_document(
        run_id=arguments.run_id,
        run_contract=run_contract,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_size_bytes=inventory_snapshot.size_bytes,
        inventory_rows=inventory_rows,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt_sha256=artifact_receipt_sha256,
        artifact_receipt_size_bytes=artifact_receipt_snapshot.size_bytes,
        artifact_receipt=artifact_receipt,
        artifacts=artifacts,
        scientific_review=scientific_review,
        approved_report_tables=approval_records,
        report_table_approvals_source=approval_source,
        generated_at=generated_at,
        git_commit=git_commit,
    )
    _validate_document(document, inventory_rows, inventory_path)
    summary_json_bytes = adapter.canonical_json_bytes(document)
    summary_rows = _build_summary_rows(document, artifact_scope_order)
    summary_tsv_bytes = adapter.tsv_bytes(RUN_SUMMARY_HEADER, summary_rows)
    qc_rows = _build_qc_rows(document)
    qc_summary_bytes = adapter.tsv_bytes(QC_SUMMARY_HEADER, qc_rows)

    previous_receipt, previous_receipt_sha256 = (
        _load_existing_summary_receipt(paths)
    )
    previous_attempt_id: str | None = None
    previous_attempt_history: list[str] = []
    if previous_receipt is not None:
        _validate_existing_summary(
            paths=paths,
            receipt=previous_receipt,
            expected_run_id=arguments.run_id,
            expected_run_contract=run_contract,
        )
        previous_attempt_id, previous_attempt_history = _parse_history(
            previous_receipt,
            id_field="run_summary_attempt_id",
            supersedes_field="supersedes_run_summary_attempt_id",
            history_field="run_summary_attempt_history",
        )

    attempt_id = _new_attempt_id(started_at)
    receipt_row = _build_receipt_row(
        run_id=arguments.run_id,
        run_contract=run_contract,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt_sha256=artifact_receipt_sha256,
        artifact_receipt=artifact_receipt,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_row_count=len(inventory_rows),
        artifacts_path=artifacts_path,
        artifacts_sha256=artifacts_sha256,
        summary_json_path=paths.summary_json,
        summary_json_bytes=summary_json_bytes,
        summary_tsv_path=paths.summary_tsv,
        summary_tsv_bytes=summary_tsv_bytes,
        summary_tsv_row_count=len(summary_rows),
        qc_summary_path=paths.qc_summary,
        qc_summary_bytes=qc_summary_bytes,
        qc_summary_row_count=len(qc_rows),
        science_review_summary_path=science_path,
        science_review_summary_sha256=science_sha256,
        document=document,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        previous_attempt_history=previous_attempt_history,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
    )
    receipt_bytes = adapter.tsv_bytes(
        RUN_SUMMARY_RECEIPT_HEADER, [receipt_row]
    )
    context = BuildContext(
        run_id=arguments.run_id,
        execute=arguments.execute,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt_sha256=artifact_receipt_sha256,
        artifact_receipt=artifact_receipt,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        run_contract=run_contract,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        artifacts_path=artifacts_path,
        artifacts_sha256=artifacts_sha256,
        records_dir=records_dir,
        index_rows=index_rows,
        record_paths=record_paths,
        record_hashes=record_hashes,
        input_snapshots=input_snapshots,
        artifacts=artifacts,
        science_review_summary_path=science_path,
        science_review_summary_sha256=science_sha256,
        report_table_approvals_path=approvals_path,
        report_table_approvals_sha256=approvals_sha256,
        report_table_snapshots=approval_table_snapshots,
        document=document,
        summary_json_bytes=summary_json_bytes,
        summary_rows=summary_rows,
        summary_tsv_bytes=summary_tsv_bytes,
        qc_rows=qc_rows,
        qc_summary_bytes=qc_summary_bytes,
        paths=paths,
        previous_receipt=previous_receipt,
        previous_receipt_sha256=previous_receipt_sha256,
        previous_attempt_id=previous_attempt_id,
        previous_attempt_history=previous_attempt_history,
        attempt_id=attempt_id,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
    )
    _recheck_inputs(context)
    return context


def _recheck_inputs(context: BuildContext) -> None:
    _assert_output_directory_identity(context.paths)
    for snapshot in context.input_snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)
    for snapshot in context.report_table_snapshots:
        _verify_report_table_snapshot(snapshot)
    adapter.validate_published_transaction(
        run_id=context.run_id,
        run_contract=context.run_contract,
        run_contract_path=context.run_contract_path,
        run_contract_file_sha256=context.run_contract_file_sha256,
        inventory_path=context.inventory_path,
        inventory_sha256=context.inventory_sha256,
        inventory_rows=context.inventory_rows,
        records_dir=context.records_dir,
        artifacts_path=context.artifacts_path,
        receipt_path=context.artifact_receipt_path,
        require_current_source_locations=True,
    )
    for snapshot in context.input_snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)
    for snapshot in context.report_table_snapshots:
        _verify_report_table_snapshot(snapshot)
    if context.science_review_summary_path is not None:
        if contracts.sha256_file(context.science_review_summary_path) != (
            context.science_review_summary_sha256
        ):
            _fail("The explicit science-review summary changed")
        normalized = science.normalize_scientific_review(
            summary_path=context.science_review_summary_path,
            artifacts=context.artifacts,
            run_id=context.run_id,
            run_contract=context.run_contract,
            generated_at=context.document["generated_at"],
            git_commit=context.git_commit,
        )
        if normalized != context.document["scientific_review"]["record"]:
            _fail("The explicit scientific-review package changed")
    approval_source = context.document["parameters"][
        "report_table_approvals"
    ]
    if context.report_table_approvals_path is None:
        if approval_source is not None or context.document[
            "approved_report_tables"
        ]:
            _fail("Run-summary approval state changed after preparation")
    elif (
        approval_source is None
        or approval_source["path"] != str(
            context.report_table_approvals_path
        )
        or approval_source["sha256"]
        != context.report_table_approvals_sha256
        or approval_source["row_count"]
        != len(context.document["approved_report_tables"])
    ):
        _fail("The explicit report-table approval package changed")


def _validate_receipt_against_context(
    context: BuildContext,
    receipt: Mapping[str, str],
) -> None:
    expected = {
        field: adapter.safe_tsv(context.receipt_row[field])
        for field in RUN_SUMMARY_RECEIPT_HEADER
    }
    if dict(receipt) != expected:
        _fail("Published run-summary receipt differs from the prepared receipt")


def validate_published_run_summary(context: BuildContext) -> None:
    _assert_output_directory_identity(context.paths)
    for path in context.paths.ordered_outputs:
        if path.is_symlink() or not path.is_file():
            _fail(f"Published run-summary output is unsafe or missing: {path}")
    if context.paths.summary_json.read_bytes() != context.summary_json_bytes:
        _fail("Published run-summary JSON differs from prepared bytes")
    if context.paths.summary_tsv.read_bytes() != context.summary_tsv_bytes:
        _fail("Published run-summary TSV differs from prepared bytes")
    if context.paths.qc_summary.read_bytes() != context.qc_summary_bytes:
        _fail("Published QC summary differs from prepared bytes")
    receipt = adapter.read_exact_tsv(
        context.paths.receipt,
        RUN_SUMMARY_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    _validate_receipt_against_context(context, receipt)
    document = contracts.load_json_object(
        context.paths.summary_json, "published run summary"
    )
    _validate_document(document, context.inventory_rows, context.inventory_path)
    _validate_existing_summary(
        paths=context.paths,
        receipt=receipt,
        expected_run_id=context.run_id,
        expected_run_contract=context.run_contract,
    )


def _write_recovery_marker(
    path: Path,
    message: str,
) -> None:
    try:
        path.write_text(message, encoding="utf-8")
    except OSError:
        pass


def publish_context(context: BuildContext) -> None:
    _assert_output_directory_identity(context.paths)
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_paths = tuple(
        context.paths.output_dir / f".{path.name}.{run_token}.tmp"
        for path in context.paths.ordered_outputs
    )
    backup_paths = tuple(
        context.paths.output_dir / f".{path.name}.{run_token}.previous"
        for path in context.paths.ordered_outputs
    )
    recovery_path = (
        context.paths.output_dir
        / f".{context.run_id}.run-summary.{run_token}.RECOVERY.txt"
    )
    for path in (*temp_paths, *backup_paths, recovery_path):
        if path.exists() or path.is_symlink():
            _fail(f"Run-token scratch path already exists: {path}")

    try:
        ownership = adapter.acquire_lock(
            context.paths.lock, context.run_id, run_token
        )
    except adapter.ArtifactIndexError as exc:
        _fail(str(exc))
    try:
        previous_signal_handlers = (
            adapter.install_publication_signal_handlers()
        )
    except BaseException as exc:
        try:
            adapter.release_owned_lock(context.paths.lock, ownership)
        except adapter.ArtifactIndexError as cleanup_exc:
            raise RunSummaryError(
                "Could not install run-summary publication signal handlers "
                f"and could not release the owned lock: {exc}; {cleanup_exc}"
            ) from exc
        if isinstance(exc, adapter.ArtifactIndexError):
            raise RunSummaryError(str(exc)) from exc
        raise RunSummaryError(
            "Could not install run-summary publication signal handlers: "
            f"{exc}"
        ) from exc

    had_previous = context.previous_receipt is not None
    backed_up = [False] * 4
    published = [False] * 4
    committed = False
    rollback_failed = False
    output_identity_lost = False
    try:
        _assert_output_directory_identity(context.paths)
        current_previous, current_previous_hash = (
            _load_existing_summary_receipt(context.paths)
        )
        if current_previous != context.previous_receipt or (
            current_previous_hash != context.previous_receipt_sha256
        ):
            _fail(
                "Run-summary predecessor changed after initial validation; "
                "prepare a fresh context"
            )
        if current_previous is not None:
            _validate_existing_summary(
                paths=context.paths,
                receipt=current_previous,
                expected_run_id=context.run_id,
                expected_run_contract=context.run_contract,
            )
        _recheck_inputs(context)

        payloads = (
            context.summary_json_bytes,
            context.summary_tsv_bytes,
            context.qc_summary_bytes,
            context.receipt_bytes,
        )
        _assert_output_directory_identity(context.paths)
        for path, payload in zip(temp_paths, payloads, strict=True):
            _assert_output_directory_identity(context.paths)
            adapter.write_bytes_exclusive(path, payload)
            _assert_output_directory_identity(context.paths)
        adapter.fsync_directory(context.paths.output_dir)

        if had_previous:
            _assert_output_directory_identity(context.paths)
            # Remove the old completion marker first.
            backup_order = (3, 0, 1, 2)
            for index in backup_order:
                _assert_output_directory_identity(context.paths)
                # Mark intent before rename so a handled signal immediately
                # after the filesystem operation cannot hide the backup.
                backed_up[index] = True
                os.replace(
                    context.paths.ordered_outputs[index],
                    backup_paths[index],
                )
                _assert_output_directory_identity(context.paths)

        # Publish data views first and the receipt last.
        _assert_output_directory_identity(context.paths)
        for index in range(4):
            _assert_output_directory_identity(context.paths)
            # As above, intent precedes the rename. Removal is idempotent if
            # the rename itself failed before changing the filesystem.
            published[index] = True
            os.replace(temp_paths[index], context.paths.ordered_outputs[index])
            _assert_output_directory_identity(context.paths)
        adapter.fsync_directory(context.paths.output_dir)
        validate_published_run_summary(context)
        _recheck_inputs(context)
        committed = True
    except Exception as exc:
        rollback_errors: list[str] = []

        try:
            _assert_output_directory_identity(context.paths)
        except RunSummaryError as identity_exc:
            rollback_failed = True
            output_identity_lost = True
            raise RunSummaryError(
                f"{exc}\nRun output directory identity changed during "
                "publication; path-based rollback and cleanup were skipped "
                "to avoid modifying a replacement directory. Preserve the "
                f"owned recovery state: {identity_exc}"
            ) from exc

        def rollback(label: str, operation: Any) -> None:
            nonlocal output_identity_lost
            if output_identity_lost:
                rollback_errors.append(
                    f"{label}: skipped after output directory identity changed"
                )
                return
            try:
                _assert_output_directory_identity(context.paths)
            except RunSummaryError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")
                return
            try:
                operation()
            except Exception as rollback_exc:  # pragma: no cover
                rollback_errors.append(f"{label}: {rollback_exc}")
                return
            try:
                _assert_output_directory_identity(context.paths)
            except RunSummaryError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")

        def restore_prior_output(index: int) -> None:
            final_path = context.paths.ordered_outputs[index]
            backup_path = backup_paths[index]
            backup_exists = backup_path.exists() or backup_path.is_symlink()
            final_exists = final_path.exists() or final_path.is_symlink()
            if backup_exists:
                if final_exists:
                    adapter.remove_owned(final_path)
                os.replace(backup_path, final_path)
                return
            if final_exists:
                return
            raise RunSummaryError(
                "Neither the prior final output nor its backup remains: "
                f"{final_path}"
            )

        # Remove a new receipt first, then the data views.
        for index in (3, 2, 1, 0):
            if published[index]:
                rollback(
                    f"remove new {context.paths.ordered_outputs[index].name}",
                    lambda index=index: adapter.remove_owned(
                        context.paths.ordered_outputs[index]
                    ),
                )
        if had_previous:
            # Restore data first and the prior receipt last.
            for index in (0, 1, 2):
                if backed_up[index]:
                    rollback(
                        (
                            "restore prior "
                            f"{context.paths.ordered_outputs[index].name}"
                        ),
                        lambda index=index: restore_prior_output(index),
                    )
            if not rollback_errors and backed_up[3]:
                rollback(
                    "restore prior run-summary receipt",
                    lambda: restore_prior_output(3),
                )
            if not rollback_errors and context.previous_receipt is not None:
                validation_error_count = len(rollback_errors)

                def validate_restored_prior() -> None:
                    restored, restored_sha256 = (
                        _load_existing_summary_receipt(context.paths)
                    )
                    if restored is None:
                        _fail("Restored prior run-summary receipt is absent")
                    if (
                        restored != context.previous_receipt
                        or restored_sha256
                        != context.previous_receipt_sha256
                    ):
                        _fail(
                            "Restored prior run-summary receipt differs from "
                            "the validated predecessor"
                        )
                    _validate_existing_summary(
                        paths=context.paths,
                        receipt=restored,
                        expected_run_id=context.run_id,
                        expected_run_contract=context.run_contract,
                    )

                rollback(
                    "validate restored prior run-summary transaction",
                    validate_restored_prior,
                )
                if (
                    len(rollback_errors) > validation_error_count
                    and (
                        context.paths.receipt.exists()
                        or context.paths.receipt.is_symlink()
                    )
                ):
                    rollback(
                        "quarantine invalid restored run-summary receipt",
                        lambda: os.replace(
                            context.paths.receipt,
                            backup_paths[3],
                        ),
                    )
        if not rollback_errors:
            rollback(
                "durability-sync rollback",
                lambda: adapter.fsync_directory(context.paths.output_dir),
            )
        if rollback_errors:
            rollback_failed = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery_path,
                    "Run-summary rollback was incomplete.\n"
                    f"Original error: {exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n",
                )
            raise RunSummaryError(
                f"{exc}\nRun-summary rollback was incomplete; preserve "
                f"the lock and recovery paths under {context.paths.output_dir}. "
                f"Rollback errors: {'; '.join(rollback_errors)}"
            ) from exc
        if isinstance(exc, RunSummaryError):
            raise
        raise RunSummaryError(str(exc)) from exc
    finally:
        cleanup_errors: list[str] = []
        directory_identity_safe = not output_identity_lost
        active = sys.exc_info()[1]
        try:
            if not rollback_failed:
                try:
                    _assert_output_directory_identity(context.paths)
                except RunSummaryError as exc:
                    directory_identity_safe = False
                    cleanup_errors.append(str(exc))
                cleanup_paths = []
                if not cleanup_errors:
                    cleanup_paths = list(temp_paths)
                    if committed:
                        cleanup_paths.extend(backup_paths)
                for path in cleanup_paths:
                    try:
                        _assert_output_directory_identity(context.paths)
                        adapter.remove_owned(path)
                        _assert_output_directory_identity(context.paths)
                    except RunSummaryError as exc:
                        directory_identity_safe = False
                        cleanup_errors.append(str(exc))
                        break
                    except OSError as exc:
                        cleanup_errors.append(f"{path}: {exc}")
                if not cleanup_errors:
                    try:
                        _assert_output_directory_identity(context.paths)
                        adapter.release_owned_lock(
                            context.paths.lock, ownership
                        )
                        _assert_output_directory_identity(context.paths)
                    except RunSummaryError as exc:
                        directory_identity_safe = False
                        cleanup_errors.append(str(exc))
                    except adapter.ArtifactIndexError as exc:
                        cleanup_errors.append(str(exc))
        except Exception as exc:
            cleanup_errors.append(
                f"publication cleanup was interrupted: {exc}"
            )
        finally:
            try:
                adapter.restore_signal_handlers(previous_signal_handlers)
            except (OSError, ValueError) as exc:
                cleanup_errors.append(
                    f"could not restore publication signal handlers: {exc}"
                )
        if cleanup_errors:
            if directory_identity_safe:
                _write_recovery_marker(
                    recovery_path,
                    (
                        "Run-summary publication completed but owned cleanup "
                        "was incomplete.\n"
                        f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    ),
                )
            raise RunSummaryError(
                "Run-summary cleanup failed; preserve the lock and recovery "
                f"paths: {'; '.join(cleanup_errors)}"
            ) from active


def print_context(context: BuildContext) -> None:
    mode = "execute" if context.execute else "dry-run"
    rollup = context.document["computational_rollup"]
    print("NORAD run-summary context")
    print(f"  Mode: {mode}")
    print(f"  Run ID: {context.run_id}")
    print(f"  Artifact receipt: {context.artifact_receipt_path}")
    print(f"  Adapter attempt: {context.artifact_receipt['adapter_attempt_id']}")
    print(f"  Expected artifacts: {len(context.artifacts)}")
    print(f"  Expected scopes: {len(context.document['expected_scopes'])}")
    print(f"  Complete artifacts: {rollup['complete_artifact_count']}")
    print(f"  Missing artifacts: {rollup['missing_artifact_count']}")
    print(f"  Incomplete artifacts: {rollup['incomplete_artifact_count']}")
    print(f"  Failed artifacts: {rollup['failed_artifact_count']}")
    print(
        "  Externally unavailable artifacts: "
        f"{rollup['externally_unavailable_artifact_count']}"
    )
    print(f"  Science status: {context.document['science_status']}")
    if context.report_table_approvals_path is None:
        print("  Report-table approvals: not supplied")
    else:
        print(
            "  Report-table approvals: "
            f"{context.report_table_approvals_path}"
        )
    print(
        "  Approved report tables: "
        f"{len(context.document['approved_report_tables'])}"
    )
    print(f"  Output JSON: {context.paths.summary_json}")
    print(f"  Output TSV: {context.paths.summary_tsv}")
    print(f"  QC TSV: {context.paths.qc_summary}")
    print(f"  Receipt (published last): {context.paths.receipt}")
    print(f"  Run-summary attempt: {context.attempt_id}")
    if not context.execute:
        print("Dry-run complete; no run-summary files were written.")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        context = prepare_context(arguments)
        print_context(context)
        if arguments.execute:
            publish_context(context)
            print(f"Published run summary: {context.paths.summary_json}")
            print(f"Published receipt last: {context.paths.receipt}")
        return 0
    except (
        RunSummaryError,
        adapter.ArtifactIndexError,
        contracts.ContractValidationError,
        science.RunSummaryScienceError,
        OSError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
