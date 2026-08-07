#!/usr/bin/env python3
"""Measure explicit storage roots and record retention policy without mutation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import stat
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from norad.libraries import validation as report


ROOT_HEADER = (
    "storage_id", "path", "required", "purpose", "quota_bytes_expected", "notes",
)
POLICY_HEADER = (
    "policy_id", "storage_id", "artifact_class", "action", "retention_days",
    "approval_status", "approved_by", "approved_at", "notes",
)
INVENTORY_HEADER = (
    "storage_id", "declared_path", "resolved_path", "required", "purpose",
    "status", "tree_bytes", "file_count", "directory_count", "symlink_count",
    "filesystem_total_bytes", "filesystem_free_bytes",
    "filesystem_available_bytes", "quota_bytes_expected", "detail",
)
SUMMARY_HEADER = (
    "roots_sha256", "policy_sha256", "storage_root_count", "available_root_count",
    "missing_required_count", "measurement_error_count", "policy_row_count",
    "approved_policy_count", "pending_policy_count", "rejected_policy_count",
    "unapproved_storage_count", "overall_status",
)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ACTIONS = {"retain", "archive", "review_then_delete"}
APPROVALS = {"approved", "pending", "rejected"}


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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", required=True, type=Path)
    parser.add_argument("--retention-policy", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def read_regular(path: Path, label: str) -> bytes:
    try:
        before = report.regular_snapshot(path, label)
    except report.ValidationError as exc:
        fail(str(exc))
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    try:
        after = report.regular_snapshot(path, label)
    except report.ValidationError as exc:
        fail(str(exc))
    if before != after:
        fail(f"{label} changed while read: {path}")
    return data


def table(path: Path, header: tuple[str, ...], label: str) -> tuple[bytes, list[dict[str, str]]]:
    data = read_regular(path, label)
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
        if any("\x00" in value or "\r" in value or "\n" in value for value in row.values()):
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
        roots.append(Root(
            storage_id, declared, resolved, row["required"] == "true",
            row["purpose"], quota, row["notes"],
        ))
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
        approval = row["approval_status"]
        if approval not in APPROVALS:
            fail(f"Retention policy row {number} has invalid approval_status")
        if approval == "approved":
            if row["approved_by"] == "NA" or not parse_utc(row["approved_at"]):
                fail(f"Retention policy row {number} approved record needs approver and past UTC time")
        elif row["approved_by"] != "NA" or row["approved_at"] != "NA":
            fail(f"Retention policy row {number} non-approved record must use NA approval fields")
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


def measure(root: Root) -> tuple[object, ...]:
    try:
        metadata = root.path.lstat()
    except OSError as exc:
        status = "missing_required" if root.required else "missing_optional"
        return (
            root.storage_id, root.declared_path, str(root.path),
            str(root.required).lower(), root.purpose, status,
            "NA", "NA", "NA", "NA", "NA", "NA", "NA", root.quota, report.clean(exc),
        )
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        return (
            root.storage_id, root.declared_path, str(root.path),
            str(root.required).lower(), root.purpose, "invalid",
            "NA", "NA", "NA", "NA", "NA", "NA", "NA", root.quota,
            "root is not a real directory",
        )
    tree_bytes = 0
    file_count = 0
    directory_count = 1
    symlink_count = 0
    try:
        for current, directories, files in os.walk(root.path, followlinks=False):
            kept_directories = []
            for name in directories:
                candidate = Path(current) / name
                if candidate.is_symlink():
                    symlink_count += 1
                else:
                    directory_count += 1
                    kept_directories.append(name)
            directories[:] = kept_directories
            for name in files:
                candidate = Path(current) / name
                item = candidate.lstat()
                if stat.S_ISLNK(item.st_mode):
                    symlink_count += 1
                elif stat.S_ISREG(item.st_mode):
                    file_count += 1
                    tree_bytes += item.st_size
        fs = os.statvfs(root.path)
    except OSError as exc:
        return (
            root.storage_id, root.declared_path, str(root.path),
            str(root.required).lower(), root.purpose, "measurement_error",
            "NA", "NA", "NA", "NA", "NA", "NA", "NA", root.quota, report.clean(exc),
        )
    return (
        root.storage_id, root.declared_path, str(root.path),
        str(root.required).lower(), root.purpose, "available",
        tree_bytes, file_count, directory_count, symlink_count,
        fs.f_blocks * fs.f_frsize, fs.f_bfree * fs.f_frsize,
        fs.f_bavail * fs.f_frsize, root.quota, root.notes,
    )


def render_tsv(header: Iterable[str], rows: Iterable[Iterable[object]]) -> bytes:
    output = ["\t".join(header)]
    output.extend("\t".join(report.clean(value) for value in row) for row in rows)
    return ("\n".join(output) + "\n").encode()


def outputs(
    roots_data: bytes,
    policy_data: bytes,
    roots: Sequence[Root],
    policies: Sequence[Policy],
) -> dict[str, bytes]:
    inventory_rows = [measure(root) for root in roots]
    statuses = [str(row[5]) for row in inventory_rows]
    approvals = [policy.approval for policy in policies]
    approved_storage = {
        policy.storage_id for policy in policies if policy.approval == "approved"
    }
    unapproved = sum(root.storage_id not in approved_storage for root in roots)
    overall = "pass"
    if (
        any(status in {"missing_required", "invalid", "measurement_error"} for status in statuses)
        or unapproved
        or any(approval == "rejected" for approval in approvals)
    ):
        overall = "fail"
    summary = (
        hashlib.sha256(roots_data).hexdigest(),
        hashlib.sha256(policy_data).hexdigest(),
        len(roots), statuses.count("available"), statuses.count("missing_required"),
        statuses.count("measurement_error") + statuses.count("invalid"),
        len(policies), approvals.count("approved"), approvals.count("pending"),
        approvals.count("rejected"), unapproved, overall,
    )
    return {
        "inventory": render_tsv(INVENTORY_HEADER, inventory_rows),
        "policy": render_tsv(POLICY_HEADER, (policy.values for policy in policies)),
        "summary": render_tsv(SUMMARY_HEADER, [summary]),
    }


def validate(data: bytes, header: tuple[str, ...], count: int | None = None) -> None:
    reader = csv.DictReader(data.decode().splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != header:
        fail("Generated storage output has invalid header")
    rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        fail("Generated storage output has invalid row shape")
    if count is not None and len(rows) != count:
        fail("Generated storage output has invalid row count")


def publish(output_root: Path, generated: dict[str, bytes]) -> None:
    if not output_root.exists() or output_root.is_symlink() or not output_root.is_dir():
        fail(f"Output root must be an existing real directory: {output_root}")
    names = {
        "inventory": "storage_inventory.tsv",
        "policy": "retention_policy.tsv",
        "summary": "storage_retention_summary.tsv",
    }
    finals = {key: output_root / value for key, value in names.items()}
    present = [path.exists() for path in finals.values()]
    if any(present) and not all(present):
        fail("Existing storage/retention outputs are incomplete")
    lock = output_root / ".storage-inventory-retention.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail(f"Storage inventory lock already exists: {lock}")
    token = uuid.uuid4().hex
    staged = {key: output_root / f".{name}.{token}.tmp" for key, name in names.items()}
    backups = {key: output_root / f".{name}.{token}.previous" for key, name in names.items()}
    try:
        os.write(descriptor, f"pid={os.getpid()}\nrun_token={token}\n".encode())
        for key in names:
            with staged[key].open("xb") as handle:
                handle.write(generated[key]); handle.flush(); os.fsync(handle.fileno())
        if all(present):
            expected = {
                "inventory": (INVENTORY_HEADER, None),
                "policy": (POLICY_HEADER, None),
                "summary": (SUMMARY_HEADER, 1),
            }
            for key in names:
                if finals[key].is_symlink() or not finals[key].is_file():
                    fail("Existing storage/retention output is unsafe")
                validate(
                    read_regular(finals[key], f"Existing {names[key]}"),
                    expected[key][0],
                    expected[key][1],
                )
                os.replace(finals[key], backups[key])
        published = []
        try:
            for key in ("inventory", "policy", "summary"):
                os.replace(staged[key], finals[key]); published.append(key)
        except BaseException:
            for key in published:
                if finals[key].exists(): finals[key].unlink()
            for key in names:
                if backups[key].exists(): os.replace(backups[key], finals[key])
            raise
        for path in backups.values():
            if path.exists(): path.unlink()
    finally:
        for path in staged.values():
            if path.exists() and not path.is_symlink(): path.unlink()
        os.close(descriptor)
        if lock.exists() and not lock.is_symlink(): lock.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        roots_data, roots = load_roots(args.roots)
        policy_data, policies = load_policy(
            args.retention_policy, {root.storage_id for root in roots}
        )
        generated = outputs(roots_data, policy_data, roots, policies)
        validate(generated["inventory"], INVENTORY_HEADER, len(roots))
        validate(generated["policy"], POLICY_HEADER, len(policies))
        validate(generated["summary"], SUMMARY_HEADER, 1)
        print(f"Storage roots: {args.roots}")
        print(f"Retention policy: {args.retention_policy}")
        print(f"Output root: {args.output_root}")
        print("Evidence boundary: read-only measurement and policy recording; no storage is altered.")
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        if read_regular(args.roots, "Storage roots") != roots_data:
            fail("Storage roots changed after measurement")
        if read_regular(args.retention_policy, "Retention policy") != policy_data:
            fail("Retention policy changed after measurement")
        publish(args.output_root, generated)
        print(f"Published storage/retention report: {args.output_root}")
        return 0
    except StorageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
