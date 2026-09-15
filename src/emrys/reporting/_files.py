"""Shared file identity, path guards, and owned publication operations."""

from __future__ import annotations

import os
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from emrys.libraries.exclusive_publication import stat_identity


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    sha256: str
    device: int
    inode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int


def stable_snapshot(
    path: Path,
    sha256: str,
    states: tuple[os.stat_result, os.stat_result, os.stat_result],
    fail: Callable[[str], NoReturn],
    changed_message: str,
    observed_size: int | None = None,
) -> FileSnapshot:
    """Build a snapshot only when identity and optional read size stayed stable."""
    before, after, current = states
    changed = (
        stat_identity(before) != stat_identity(after)
        or stat_identity(before) != stat_identity(current)
        or (observed_size is not None and observed_size != before.st_size)
        or stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
    )
    if changed:
        fail(changed_message)
    return FileSnapshot(
        path=path,
        sha256=sha256,
        device=before.st_dev,
        inode=before.st_ino,
        size_bytes=before.st_size,
        mtime_ns=before.st_mtime_ns,
        ctime_ns=before.st_ctime_ns,
    )


def reject_symlink_components(
    path: Path,
    label: str,
    fail: Callable[[str], NoReturn],
) -> None:
    """Reject existing symlinks while preserving the caller's error type."""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if not os.path.lexists(current):
            continue
        try:
            metadata = current.lstat()
        except OSError as exc:
            fail(f"Could not inspect {label} component {current}: {exc}")
        if stat.S_ISLNK(metadata.st_mode):
            fail(f"{label} must not traverse a symbolic link: {current}")


def fsync_path(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def remove_owned_stage(
    path: Path,
    token: str,
    identity: tuple[int, int] | None,
    error_type: type[Exception],
) -> None:
    if not os.path.lexists(path):
        return
    metadata = path.lstat()
    if (
        token not in path.name
        or identity != (metadata.st_dev, metadata.st_ino)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        raise error_type(f"Refusing to remove unverified staging path: {path}")
    shutil.rmtree(path)
