"""One durable, no-clobber publication primitive for immutable small files."""

from __future__ import annotations

import os
import uuid
from pathlib import Path


def publish_exclusive(
    path: Path,
    data: bytes,
    error: type[Exception],
    *,
    existing: str | None = None,
) -> None:
    """Publish complete bytes at an absent name through one pinned parent."""

    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise error("Secure create-exclusive publication is unavailable")
    parent_fd = -1
    stage = f".{path.name}.{uuid.uuid4().hex}.emrys-stage"
    try:
        parent_fd = os.open(
            path.parent,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
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
        os.link(
            stage,
            path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        final_state = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        if (stage_state.st_dev, stage_state.st_ino) != (
            final_state.st_dev,
            final_state.st_ino,
        ):
            raise error(f"Publication did not retain the staged file: {path}")
        os.unlink(stage, dir_fd=parent_fd)
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
        if parent_fd >= 0:
            try:
                os.unlink(stage, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            os.close(parent_fd)
