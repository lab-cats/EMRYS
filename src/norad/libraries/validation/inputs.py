"""Stable input snapshots and reads for NORAD validators."""

from __future__ import annotations

import stat
import subprocess
from collections.abc import Mapping
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


def require_executable(path: Path, label: str) -> None:
    """Fail unless path points to an executable regular file."""
    regular_snapshot(path, label)
    if not (path.stat().st_mode & 0o111):
        fail(f"{label} is not executable: {path}")


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


def read_bytes(path: Path, label: str) -> bytes:
    """Read file bytes while validating unchanged regular input snapshots."""
    before = regular_snapshot(path, label)
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    after = regular_snapshot(path, label)
    if before != after:
        fail(f"{label} changed while read: {path}")
    return data


def require_unchanged(snapshots: dict[Path, Snapshot]) -> None:
    """Fail if any declared validator input changed after evidence collection."""

    for path, expected in snapshots.items():
        if regular_snapshot(path, f"Input {path.name}") != expected:
            fail(f"Input changed after validation: {path}")


def lexical_path(path: Path) -> Path:
    """Return an absolute lexical path without resolving symlinks."""
    return path.expanduser().absolute()


def resolve_from_base(base_dir: Path, path: str | Path) -> Path:
    """Resolve a possibly-relative path against an explicit base and expand."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.expanduser().absolute()


def snapshots(paths: Mapping[str, Path], *, label: str) -> dict[Path, Snapshot]:
    """Build regular snapshots for a role->path map with a shared label prefix."""
    return {
        path: regular_snapshot(path, f"{label} {role}") for role, path in paths.items()
    }


def integer_stdout(result: subprocess.CompletedProcess[str], label: str) -> int:
    if result.returncode != 0:
        fail(f"{label} failed: {result.stderr}")
    try:
        value = int(result.stdout.strip())
    except ValueError:
        fail(f"{label} returned a noninteger count")
    if value < 0:
        fail(f"{label} returned a negative count")
    return value
