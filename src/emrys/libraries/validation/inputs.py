"""Stable input snapshots and reads for EMRYS validators."""

from __future__ import annotations

import errno
import hashlib
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

    data, state = _read_file(path, label, nonempty=nonempty)
    assert isinstance(data, bytes)
    return data, state


def sha256_with_identity(
    path: Path,
    label: str,
    *,
    nonempty: bool = True,
) -> tuple[str, os.stat_result]:
    """Hash one stable file without retaining its contents."""

    digest, state = _read_file(path, label, nonempty=nonempty, digest_only=True)
    assert isinstance(digest, str)
    return digest, state


def directory_entries_with_identity(
    path: Path,
    label: str,
) -> tuple[tuple[str, ...], os.stat_result]:
    """List one stable real directory through a no-follow descriptor."""

    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        fail(f"{label} cannot be admitted without symbolic-link protection: {path}")
    flags = os.O_RDONLY | no_follow | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            fail(f"{label} must be a real directory: {path}")
        entries = tuple(sorted(os.listdir(descriptor)))
        after = os.fstat(descriptor)
        current = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if not (
        _stable_directory_state(before)
        == _stable_directory_state(after)
        == _stable_directory_state(current)
    ):
        fail(f"{label} changed while inspected: {path}")
    return entries, after


def read_prefix(path: Path, label: str, length: int) -> bytes:
    """Read at most ``length`` bytes through a stable, no-follow binding."""
    if isinstance(length, bool) or not isinstance(length, int) or length < 1:
        raise ValueError("prefix length must be a positive integer")
    data, _state = _read_file(path, label, limit=length)
    assert isinstance(data, bytes)
    return data


def _read_file(
    path: Path,
    label: str,
    *,
    limit: int | None = None,
    nonempty: bool = True,
    digest_only: bool = False,
) -> tuple[bytes | str, os.stat_result]:
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
        digest = hashlib.sha256() if digest_only else None
        observed_size = 0
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
            observed_size += len(chunk)
            if digest is not None:
                digest.update(chunk)
            else:
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
    expected_size = before.st_size if limit is None else min(before.st_size, limit)
    if (
        _stable_file_state(before) != _stable_file_state(after)
        or observed_size != expected_size
    ):
        fail(f"{label} changed while read: {path}")
    return (digest.hexdigest() if digest is not None else b"".join(chunks)), after


def _stable_file_state(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _stable_directory_state(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
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
    if stat.S_ISLNK(path_state.st_mode) or _stable_file_state(
        path_state
    ) != _stable_file_state(descriptor_state):
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
