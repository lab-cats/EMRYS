"""Shared file identity, path guards, and owned publication operations."""

from __future__ import annotations

import os
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    sha256: str
    device: int
    inode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int


def stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    """Return every stat field used to detect replacement or mutation."""
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


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


def _write_durable(descriptor: int, payload: bytes) -> None:
    while payload:
        written = os.write(descriptor, payload)
        if written <= 0:
            raise OSError("Publication write made no progress")
        payload = payload[written:]
    os.fsync(descriptor)


def write_bytes_exclusive(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        _write_durable(descriptor, payload)
    finally:
        os.close(descriptor)


def fsync_path(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def acquire_lock(
    path: Path, payload: bytes, error_type: type[Exception]
) -> os.stat_result:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise error_type(f"Publication lock already exists: {path}") from exc
    except OSError as exc:
        raise error_type(f"Could not acquire publication lock {path}: {exc}") from exc
    owned: os.stat_result | None = None
    try:
        owned = os.fstat(descriptor)
        _write_durable(descriptor, payload)
        return os.fstat(descriptor)
    except BaseException as original:
        try:
            if owned is None:
                owned = os.fstat(descriptor)
            current = path.lstat()
            if (current.st_dev, current.st_ino) != (owned.st_dev, owned.st_ino):
                raise error_type(f"Publication lock changed identity: {path}")
            path.unlink()
        except (OSError, error_type) as cleanup:
            raise error_type(
                "Publication lock acquisition was interrupted and owned cleanup "
                f"could not be proved: {cleanup}"
            ) from original
        if isinstance(original, OSError):
            raise error_type(
                f"Could not write publication lock {path}: {original}"
            ) from original
        raise
    finally:
        os.close(descriptor)


def release_lock(
    path: Path, owned: os.stat_result, payload: bytes, error_type: type[Exception]
) -> None:
    try:
        if path.resolve(strict=True) != path:
            raise error_type(f"Owned publication lock path changed: {path}")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                before = os.fstat(descriptor)
                content = stream.read()
                after = os.fstat(descriptor)
            current = path.lstat()
            if (
                not stat.S_ISREG(before.st_mode)
                or (before.st_dev, before.st_ino) != (owned.st_dev, owned.st_ino)
                or stat_identity(before) != stat_identity(after)
                or stat_identity(before) != stat_identity(current)
                or content != payload
            ):
                raise error_type(f"Owned lock identity or content changed: {path}")
            path.unlink()
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise error_type(
            f"Could not release owned publication lock {path}: {exc}"
        ) from exc


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
