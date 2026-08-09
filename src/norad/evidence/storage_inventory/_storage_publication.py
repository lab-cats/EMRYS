"""Atomic storage-evidence publication."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from norad.libraries import validation as report

from ._storage_contract import INVENTORY_HEADER, POLICY_HEADER, SUMMARY_HEADER, fail
from ._storage_measurement import validate


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
    backups = {
        key: output_root / f".{name}.{token}.previous" for key, name in names.items()
    }
    try:
        os.write(descriptor, f"pid={os.getpid()}\nrun_token={token}\n".encode())
        for key in names:
            with staged[key].open("xb") as handle:
                handle.write(generated[key])
                handle.flush()
                os.fsync(handle.fileno())
        if all(present):
            expected = {
                "inventory": (INVENTORY_HEADER, None),
                "policy": (POLICY_HEADER, None),
                "summary": (SUMMARY_HEADER, 1),
            }
            for key in names:  # noqa: PLC0206 - stable publication key order
                if finals[key].is_symlink() or not finals[key].is_file():
                    fail("Existing storage/retention output is unsafe")
                validate(
                    report.read_bytes(finals[key], f"Existing {names[key]}"),
                    expected[key][0],
                    expected[key][1],
                )
                os.replace(finals[key], backups[key])
        published = []
        try:
            for key in ("inventory", "policy", "summary"):
                os.replace(staged[key], finals[key])
                published.append(key)
        except BaseException:
            for key in published:
                if finals[key].exists():
                    finals[key].unlink()
            for key in names:
                if backups[key].exists():
                    os.replace(backups[key], finals[key])
            raise
        for path in backups.values():
            if path.exists():
                path.unlink()
    finally:
        for path in staged.values():
            if path.exists() and not path.is_symlink():
                path.unlink()
        os.close(descriptor)
        if lock.exists() and not lock.is_symlink():
            lock.unlink()
