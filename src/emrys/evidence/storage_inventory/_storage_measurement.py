"""Read-only storage measurement and evidence rendering."""

from __future__ import annotations

import csv
import hashlib
import os
import stat
from collections.abc import Iterable, Sequence
from pathlib import Path

from emrys.libraries import validation as report

from ._storage_contract import (
    INVENTORY_HEADER,
    POLICY_HEADER,
    SUMMARY_HEADER,
    Policy,
    Root,
    fail,
)


def measure(root: Root) -> tuple[object, ...]:
    try:
        metadata = root.path.lstat()
    except OSError as exc:
        status = "missing_required" if root.required else "missing_optional"
        return (
            root.storage_id,
            root.declared_path,
            str(root.path),
            str(root.required).lower(),
            root.purpose,
            status,
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            root.quota,
            report.clean(exc),
        )
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        return (
            root.storage_id,
            root.declared_path,
            str(root.path),
            str(root.required).lower(),
            root.purpose,
            "invalid",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            root.quota,
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
            root.storage_id,
            root.declared_path,
            str(root.path),
            str(root.required).lower(),
            root.purpose,
            "measurement_error",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            "NA",
            root.quota,
            report.clean(exc),
        )
    return (
        root.storage_id,
        root.declared_path,
        str(root.path),
        str(root.required).lower(),
        root.purpose,
        "available",
        tree_bytes,
        file_count,
        directory_count,
        symlink_count,
        fs.f_blocks * fs.f_frsize,
        fs.f_bfree * fs.f_frsize,
        fs.f_bavail * fs.f_frsize,
        root.quota,
        root.notes,
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
        any(
            status in {"missing_required", "invalid", "measurement_error"}
            for status in statuses
        )
        or unapproved
        or any(approval == "rejected" for approval in approvals)
    ):
        overall = "fail"
    summary = (
        hashlib.sha256(roots_data).hexdigest(),
        hashlib.sha256(policy_data).hexdigest(),
        len(roots),
        statuses.count("available"),
        statuses.count("missing_required"),
        statuses.count("measurement_error") + statuses.count("invalid"),
        len(policies),
        approvals.count("approved"),
        approvals.count("pending"),
        approvals.count("rejected"),
        unapproved,
        overall,
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
