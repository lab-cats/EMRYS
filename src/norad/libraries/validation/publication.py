"""Transactional publication for step-validation reports."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from norad.libraries.validation.errors import fail
from norad.libraries.validation.report import validate_report


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
