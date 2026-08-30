"""Stable input snapshots and reads for EMRYS validators."""

from __future__ import annotations

import errno
import os
import stat
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries.validation.errors import fail


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
    """Read exact bytes through a stable, no-follow descriptor binding."""
    return read_bytes_with_identity(path, label)[0]


def read_bytes_with_identity(
    path: Path,
    label: str,
    *,
    nonempty: bool = True,
) -> tuple[bytes, os.stat_result]:
    """Read stable bytes and return the bound descriptor identity."""

    return _read_bytes(path, label, limit=None, nonempty=nonempty)


def read_prefix(path: Path, label: str, length: int) -> bytes:
    """Read at most ``length`` bytes through a stable, no-follow binding."""
    if isinstance(length, bool) or not isinstance(length, int) or length < 1:
        raise ValueError("prefix length must be a positive integer")
    return _read_bytes(path, label, limit=length, nonempty=True)[0]


def _read_bytes(
    path: Path,
    label: str,
    *,
    limit: int | None,
    nonempty: bool,
) -> tuple[bytes, os.stat_result]:
    """Read a stable complete file or fixed prefix from one bound descriptor."""

    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        fail(f"{label} cannot be admitted without symbolic-link protection: {path}")
    flags = os.O_RDONLY | no_follow | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            fail(f"{label} must be a regular non-symlink file: {path}")
        if nonempty and before.st_size == 0:
            fail(f"{label} must be nonempty: {path}")
        _require_descriptor_path_binding(path, before, label)
        chunks: list[bytes] = []
        remaining = limit
        while remaining is None or remaining > 0:
            read_size = (
                1024 * 1024
                if remaining is None
                else min(remaining, 1024 * 1024)
            )
            chunk = os.read(descriptor, read_size)
            if not chunk:
                break
            chunks.append(chunk)
            if remaining is not None:
                remaining -= len(chunk)
        after = os.fstat(descriptor)
        _require_descriptor_path_binding(path, after, label)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            fail(f"{label} must be a regular non-symlink file: {path}")
        fail(f"{label} is unavailable: {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    data = b"".join(chunks)
    expected_size = before.st_size if limit is None else min(before.st_size, limit)
    if (
        _stable_file_state(before) != _stable_file_state(after)
        or len(data) != expected_size
    ):
        fail(f"{label} changed while read: {path}")
    return data, after


def _stable_file_state(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _require_descriptor_path_binding(
    path: Path,
    descriptor_state: os.stat_result,
    label: str,
) -> None:
    try:
        path_state = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        fail(f"{label} pathname changed while read: {path}: {exc}")
    if stat.S_ISLNK(path_state.st_mode) or (
        path_state.st_dev,
        path_state.st_ino,
    ) != (descriptor_state.st_dev, descriptor_state.st_ino):
        fail(f"{label} pathname changed while read: {path}")


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
