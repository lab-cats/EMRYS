"""Durable no-clobber publication and ownership-checked file claims."""

from __future__ import annotations

import os
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _link_exclusive(source: str, destination: str, parent: int) -> None:
    os.link(
        source,
        destination,
        src_dir_fd=parent,
        dst_dir_fd=parent,
        follow_symlinks=False,
    )


def publish_exclusive(
    path: Path,
    data: bytes,
    error: type[Exception],
    *,
    existing: str | None = None,
    replace_expected: bytes | None = None,
) -> None:
    """Publish complete bytes at an absent or exactly admitted name."""

    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise error("Secure create-exclusive publication is unavailable")
    parent_fd = -1
    current_fd = -1
    stage = f".{path.name}.{uuid.uuid4().hex}.emrys-stage"
    displaced: str | None = None
    try:
        parent_fd = os.open(
            path.parent,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
        parent_state = os.fstat(parent_fd)
        with os.fdopen(
            os.open(
                stage,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=parent_fd,
            ),
            "wb",
        ) as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), 0o600)
            os.fsync(stream.fileno())
            stage_state = os.fstat(stream.fileno())
        if replace_expected is None:
            _link_exclusive(stage, path.name, parent_fd)
        else:
            current_fd = os.open(
                path.name,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | os.O_NONBLOCK
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_fd,
            )
            current_state = os.fstat(current_fd)
            if not stat.S_ISREG(current_state.st_mode):
                raise error(f"Refusing to replace changed file: {path}")
            current_data = os.pread(current_fd, len(replace_expected) + 1, 0)
            if current_data != replace_expected:
                raise error(f"Refusing to replace changed file: {path}")
            displaced = f"{stage}.displaced"
            os.rename(
                path.name,
                displaced,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            moved = os.stat(displaced, dir_fd=parent_fd, follow_symlinks=False)
            same_file = os.path.samestat(current_state, moved)
            same_data = os.pread(current_fd, len(replace_expected) + 1, 0)
            if not same_file or same_data != replace_expected:
                try:
                    _link_exclusive(displaced, path.name, parent_fd)
                except FileExistsError as exc:
                    raise error(
                        f"Refusing to replace changed file; competing file retained at "
                        f"{path.parent / displaced}"
                    ) from exc
                os.unlink(displaced, dir_fd=parent_fd)
                displaced = None
                os.fsync(parent_fd)
                raise error(f"Refusing to replace changed file: {path}")
            try:
                _link_exclusive(stage, path.name, parent_fd)
            except FileExistsError as exc:
                os.unlink(displaced, dir_fd=parent_fd)
                displaced = None
                os.fsync(parent_fd)
                raise error(f"Refusing to replace changed file: {path}") from exc
        final_state = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        if (stage_state.st_dev, stage_state.st_ino) != (
            final_state.st_dev,
            final_state.st_ino,
        ):
            raise error(f"Publication did not retain the staged file: {path}")
        if displaced is not None:
            os.unlink(displaced, dir_fd=parent_fd)
            displaced = None
        try:
            os.unlink(stage, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.fsync(parent_fd)
        current_parent = path.parent.stat(follow_symlinks=False)
        if (parent_state.st_dev, parent_state.st_ino) != (
            current_parent.st_dev,
            current_parent.st_ino,
        ):
            raise error(f"Publication parent changed during publication: {path.parent}")
    except FileExistsError as exc:
        raise error(existing or f"Refusing to replace existing file: {path}") from exc
    except OSError as exc:
        raise error(f"Could not publish {path}: {exc}") from exc
    finally:
        if current_fd >= 0:
            os.close(current_fd)
        if parent_fd >= 0:
            try:
                os.unlink(stage, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            os.close(parent_fd)


def stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    """Return every stat field used to detect replacement or mutation."""
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


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


def _check_lock_parent(path: Path, descriptor: int) -> None:
    pinned = os.fstat(descriptor)
    current = path.parent.lstat()
    if path.parent.resolve(strict=True) != path.parent or (
        pinned.st_dev,
        pinned.st_ino,
    ) != (current.st_dev, current.st_ino):
        raise OSError(f"Publication lock parent changed: {path.parent}")


@contextmanager
def _lock_parent(path: Path) -> Iterator[int]:
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        _check_lock_parent(path, descriptor)
        yield descriptor
    finally:
        os.close(descriptor)


def acquire_lock(
    path: Path,
    payload: bytes,
    error_type: type[Exception],
    *,
    retain_on_failure: bool = False,
) -> os.stat_result:
    """Acquire durably; retain failed claims when interrupted mutation is ambiguous."""
    try:
        with _lock_parent(path) as parent:
            descriptor = os.open(
                path.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            owned: os.stat_result | None = None
            try:
                owned = os.fstat(descriptor)
                _write_durable(descriptor, payload)
                os.fsync(parent)
                _check_lock_parent(path, parent)
                completed = os.fstat(descriptor)
                current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if stat_identity(completed) != stat_identity(current):
                    raise error_type(f"Publication lock changed identity: {path}")
                return completed
            except BaseException as original:
                if not retain_on_failure:
                    try:
                        if owned is None:
                            owned = os.fstat(descriptor)
                        current = os.stat(
                            path.name, dir_fd=parent, follow_symlinks=False
                        )
                        if (current.st_dev, current.st_ino) != (
                            owned.st_dev,
                            owned.st_ino,
                        ):
                            raise error_type(
                                f"Publication lock changed identity: {path}"
                            )
                        os.unlink(path.name, dir_fd=parent)
                        os.fsync(parent)
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
    except FileExistsError as exc:
        raise error_type(f"Publication lock already exists: {path}") from exc
    except OSError as exc:
        raise error_type(f"Could not acquire publication lock {path}: {exc}") from exc


def release_lock(
    path: Path, owned: os.stat_result, payload: bytes, error_type: type[Exception]
) -> None:
    try:
        if path.resolve(strict=True) != path:
            raise error_type(f"Owned publication lock path changed: {path}")
        with _lock_parent(path) as parent:
            descriptor = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            try:
                with os.fdopen(descriptor, "rb", closefd=False) as stream:
                    before = os.fstat(descriptor)
                    content = stream.read(len(payload) + 1)
                    after = os.fstat(descriptor)
                current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if (
                    not stat.S_ISREG(before.st_mode)
                    or (before.st_dev, before.st_ino) != (owned.st_dev, owned.st_ino)
                    or stat_identity(before) != stat_identity(after)
                    or stat_identity(before) != stat_identity(current)
                    or content != payload
                ):
                    raise error_type(f"Owned lock identity or content changed: {path}")
                _check_lock_parent(path, parent)
                os.unlink(path.name, dir_fd=parent)
                os.fsync(parent)
            finally:
                os.close(descriptor)
    except OSError as exc:
        raise error_type(
            f"Could not release owned publication lock {path}: {exc}"
        ) from exc
