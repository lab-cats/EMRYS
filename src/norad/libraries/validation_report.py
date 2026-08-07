"""Shared validation-report rendering, validation, and publication protocol.

This file is an exact-path internal owner, not a public Python package API.
Stage validators retain their stage-specific parsing and checks.
"""

from __future__ import annotations

import csv
import os
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


HEADER = (
    "step_id",
    "scope_id",
    "check_id",
    "status",
    "observed",
    "expected",
    "detail",
)


class ValidationError(RuntimeError):
    """Raised when the validator contract or publication state is unsafe."""


@dataclass(frozen=True)
class Snapshot:
    device: int
    inode: int
    size: int
    mtime_ns: int


def fail(message: str) -> None:
    raise ValidationError(message)


def clean(value: object) -> str:
    return " ".join(str(value).replace("\x00", "").split())


def regular_snapshot(path: Path, label: str, *, nonempty: bool = True) -> Snapshot:
    try:
        value = path.lstat()
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        fail(f"{label} must be a regular non-symlink file: {path}")
    if nonempty and value.st_size == 0:
        fail(f"{label} must be nonempty: {path}")
    return Snapshot(value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def stable_text(path: Path, label: str) -> tuple[str, Snapshot]:
    before = regular_snapshot(path, label)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"{label} cannot be read as UTF-8: {path}: {exc}")
    after = regular_snapshot(path, label)
    if before != after:
        fail(f"{label} changed while read: {path}")
    return text, after


def render(rows: Sequence[Sequence[str]]) -> bytes:
    lines = ["\t".join(HEADER)]
    lines.extend("\t".join(clean(value) for value in values) for values in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_report(
    data: bytes,
    scope_id: str,
    *,
    step_id: str = "00a",
    check_ids: set[str] | None = None,
) -> None:
    try:
        reader = csv.DictReader(data.decode("utf-8").splitlines(), delimiter="\t")
    except UnicodeError as exc:
        fail(f"Validation report is not UTF-8: {exc}")
    if tuple(reader.fieldnames or ()) != HEADER:
        fail("Validation report header is invalid")
    expected_ids = check_ids or {
        "index_members",
        "fasta_identity",
        "gtf_identity",
        "contig_names_lengths",
        "sjdb_overhang",
    }
    rows = list(reader)
    if len(rows) != len(expected_ids):
        fail(
            f"Step {step_id} validation report must contain exactly "
            f"{len(expected_ids)} checks"
        )
    if any(None in item or any(value is None for value in item.values()) for item in rows):
        fail("Validation report contains an invalid row")
    if {item["check_id"] for item in rows} != expected_ids:
        fail("Validation report check IDs are invalid")
    if any(item["step_id"] != step_id or item["scope_id"] != scope_id for item in rows):
        fail("Validation report scope identity is invalid")
    if any(item["status"] not in {"pass", "fail"} for item in rows):
        fail("Validation report status is invalid")


def publish(
    path: Path,
    data: bytes,
    scope_id: str,
    *,
    step_id: str = "00a",
    check_ids: set[str] | None = None,
) -> None:
    parent = path.parent
    if not parent.exists() or parent.is_symlink() or not parent.is_dir():
        fail(f"Output parent must be an existing real directory: {parent}")
    if path.name != f"{scope_id}.validation.tsv":
        fail(f"Output basename must be {scope_id}.validation.tsv")
    lock = parent / f".{path.name}.lock"
    token = uuid.uuid4().hex
    staged = parent / f".{path.name}.{token}.tmp"
    previous = parent / f".{path.name}.{token}.previous"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail(f"Validation report lock already exists: {lock}")
    replaced = False
    try:
        os.write(descriptor, f"pid={os.getpid()}\nrun_token={token}\n".encode())
        with staged.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        validate_report(
            staged.read_bytes(), scope_id, step_id=step_id, check_ids=check_ids
        )
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file():
                fail(f"Existing validation report is unsafe: {path}")
            validate_report(
                path.read_bytes(), scope_id, step_id=step_id, check_ids=check_ids
            )
            os.replace(path, previous)
            replaced = True
        try:
            os.replace(staged, path)
            validate_report(
                path.read_bytes(), scope_id, step_id=step_id, check_ids=check_ids
            )
        except BaseException:
            if path.exists() and not path.is_symlink():
                path.unlink()
            if replaced and previous.exists():
                os.replace(previous, path)
            raise
        if previous.exists():
            previous.unlink()
    finally:
        if staged.exists() and not staged.is_symlink():
            staged.unlink()
        os.close(descriptor)
        if lock.exists() and not lock.is_symlink():
            lock.unlink()


_NORAD_VALIDATION_REPORT_READY = True
