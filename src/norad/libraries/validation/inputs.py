"""Stable input snapshots and reads for NORAD validators."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path

from norad.libraries.validation.errors import fail


@dataclass(frozen=True)
class Snapshot:
    device: int
    inode: int
    size: int
    mtime_ns: int


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


def require_unchanged(snapshots: dict[Path, Snapshot]) -> None:
    """Fail if any declared validator input changed after evidence collection."""

    for path, expected in snapshots.items():
        if regular_snapshot(path, f"Input {path.name}") != expected:
            fail(f"Input changed after validation: {path}")

