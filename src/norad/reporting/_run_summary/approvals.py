"""Run-bound report-table approval normalization."""

from __future__ import annotations

import re
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .inputs import (
    _capture_file_snapshot,
    _capture_report_table_snapshot,
    _fail,
    _read_exact_tsv_bytes,
    _require_contract_regular_file,
    _require_explicit_regular_file,
    _verify_file_snapshot,
    _verify_report_table_snapshot,
)
from .models import (
    REPORT_ROLE_ADAPTERS,
    REPORT_TABLE_APPROVALS_HEADER,
    FileSnapshot,
    RunSummaryError,
    adapter,
    contracts,
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
        started_at = datetime.fromisoformat(build_started_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RunSummaryError("approved_at is not a valid timestamp") from exc
    if approved_at.tzinfo is None or started_at.tzinfo is None:
        _fail("approved_at must include a timezone")
    if approved_at.astimezone(timezone.utc) > started_at.astimezone(timezone.utc):
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
    artifacts_by_id = {artifact["artifact_id"]: artifact for artifact in artifacts}
    observed_table_ids: set[str] = set()
    observed_sources: set[tuple[str, str]] = set()
    snapshots_by_path: OrderedDict[Path, FileSnapshot] = OrderedDict()
    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        if any(
            key is None or value is None or not isinstance(value, str)
            for key, value in row.items()
        ):
            _fail(
                "Report-table approvals manifest has a non-rectangular row "
                f"at line {row_number}"
            )
        if row["run_id"] != run_id:
            _fail(f"Report-table approval line {row_number} has the wrong run_id")
        if row["run_contract_sha256"] != run_contract["run_contract_sha256"]:
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
            _fail(f"Report-table approval {table_id!r} has unsupported role {role!r}")
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
            _fail(f"Report-table approval {table_id!r} must reference a TSV artifact")
        if source["row_count"] is None:
            _fail(
                f"Report-table approval {table_id!r} source has no declared row count"
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
                (f"Report-table approval {table_id!r} display_row_limit"),
            )
            if display_row_limit > declared_row_count:
                _fail(
                    f"Report-table approval {table_id!r} display_row_limit "
                    "must not exceed row_count"
                )
        if row["approval_status"] != "approved":
            _fail(
                f"Report-table approval {table_id!r} approval_status must be 'approved'"
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
        table_snapshot, observed_row_count = _capture_report_table_snapshot(
            f"Approved report table {table_id!r}",
            source_path,
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
