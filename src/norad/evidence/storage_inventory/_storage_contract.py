"""Storage-root and retention-policy input contracts."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from norad.libraries import validation as report

ROOT_HEADER = (
    "storage_id",
    "path",
    "required",
    "purpose",
    "quota_bytes_expected",
    "notes",
)
POLICY_HEADER = (
    "policy_id",
    "storage_id",
    "artifact_class",
    "action",
    "retention_days",
    "approval_status",
    "approved_by",
    "approved_at",
    "notes",
)
INVENTORY_HEADER = (
    "storage_id",
    "declared_path",
    "resolved_path",
    "required",
    "purpose",
    "status",
    "tree_bytes",
    "file_count",
    "directory_count",
    "symlink_count",
    "filesystem_total_bytes",
    "filesystem_free_bytes",
    "filesystem_available_bytes",
    "quota_bytes_expected",
    "detail",
)
SUMMARY_HEADER = (
    "roots_sha256",
    "policy_sha256",
    "storage_root_count",
    "available_root_count",
    "missing_required_count",
    "measurement_error_count",
    "policy_row_count",
    "approved_policy_count",
    "pending_policy_count",
    "rejected_policy_count",
    "unapproved_storage_count",
    "overall_status",
)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ACTIONS = {"retain", "archive", "review_then_delete"}


class StorageError(report.ValidationError):
    pass


@dataclass(frozen=True)
class Root:
    storage_id: str
    declared_path: str
    path: Path
    required: bool
    purpose: str
    quota: str
    notes: str


@dataclass(frozen=True)
class Policy:
    values: tuple[str, ...]

    @property
    def storage_id(self) -> str:
        return self.values[1]

    @property
    def approval(self) -> str:
        return self.values[5]


def fail(message: str) -> None:
    raise StorageError(message)


def table(
    path: Path, header: tuple[str, ...], label: str
) -> tuple[bytes, list[dict[str, str]]]:
    data = report.read_bytes(path, label)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{label} is not UTF-8: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != header:
        fail(f"{label} header must be exactly: " + "\t".join(header))
    rows = list(reader)
    if not rows:
        fail(f"{label} must contain at least one row")
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            fail(f"{label} row {number} has invalid shape")
        if any(
            "\x00" in value or "\r" in value or "\n" in value for value in row.values()
        ):
            fail(f"{label} row {number} contains unsafe characters")
    return data, rows


def load_roots(path: Path) -> tuple[bytes, list[Root]]:
    data, rows = table(path, ROOT_HEADER, "Storage roots")
    roots: list[Root] = []
    ids: set[str] = set()
    paths: set[Path] = set()
    for number, row in enumerate(rows, 2):
        storage_id = row["storage_id"]
        if not SAFE_ID.fullmatch(storage_id) or storage_id in ids:
            fail(f"Storage roots row {number} has invalid or duplicate storage_id")
        ids.add(storage_id)
        declared = row["path"]
        candidate = Path(declared)
        if not candidate.is_absolute() or ".." in candidate.parts:
            fail(f"Storage roots row {number} path must be absolute without traversal")
        resolved = candidate.resolve(strict=False)
        if resolved in paths:
            fail(f"Storage roots row {number} resolves to a duplicate path")
        paths.add(resolved)
        if row["required"] not in {"true", "false"}:
            fail(f"Storage roots row {number} required must be true or false")
        quota = row["quota_bytes_expected"]
        if quota != "NA" and (not quota.isdigit() or int(quota) <= 0):
            fail(f"Storage roots row {number} quota must be NA or a positive integer")
        if not row["purpose"] or not row["notes"]:
            fail(f"Storage roots row {number} purpose and notes must be nonempty")
        roots.append(
            Root(
                storage_id,
                declared,
                resolved,
                row["required"] == "true",
                row["purpose"],
                quota,
                row["notes"],
            )
        )
    return data, roots


def parse_utc(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed <= datetime.now(timezone.utc)


def load_policy(path: Path, storage_ids: set[str]) -> tuple[bytes, list[Policy]]:
    data, rows = table(path, POLICY_HEADER, "Retention policy")
    policies: list[Policy] = []
    keys: set[tuple[str, str, str]] = set()
    policy_ids: set[str] = set()
    for number, row in enumerate(rows, 2):
        if not SAFE_ID.fullmatch(row["policy_id"]):
            fail(f"Retention policy row {number} has invalid policy_id")
        policy_ids.add(row["policy_id"])
        if row["storage_id"] not in storage_ids:
            fail(f"Retention policy row {number} names unknown storage_id")
        if not SAFE_ID.fullmatch(row["artifact_class"]):
            fail(f"Retention policy row {number} has invalid artifact_class")
        if row["action"] not in ACTIONS:
            fail(f"Retention policy row {number} has invalid action")
        days = row["retention_days"]
        if days != "indefinite" and (not days.isdigit() or int(days) < 0):
            fail(f"Retention policy row {number} has invalid retention_days")
        approval_status = row["approval_status"]
        if approval_status == "approved":
            if row["approved_by"] == "NA" or not parse_utc(row["approved_at"]):
                fail(
                    f"Retention policy row {number} approved record needs approver "
                    "and past UTC time"
                )
        elif approval_status in {"pending", "rejected"}:
            if row["approved_by"] != "NA" or row["approved_at"] != "NA":
                fail(
                    f"Retention policy row {number} non-approved record must use NA "
                    "approval fields"
                )
        else:
            fail(f"Retention policy row {number} has invalid approval_status")
        if not row["notes"]:
            fail(f"Retention policy row {number} notes must be nonempty")
        key = (row["storage_id"], row["artifact_class"], row["action"])
        if key in keys:
            fail(f"Retention policy row {number} duplicates a storage/class/action")
        keys.add(key)
        policies.append(Policy(tuple(row[field] for field in POLICY_HEADER)))
    if len(policy_ids) != 1:
        fail("Retention policy must contain exactly one policy_id")
    return data, policies
