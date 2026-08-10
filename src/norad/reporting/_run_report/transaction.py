"""Atomic-file, lock, and recovery primitives for report publication."""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from norad.reporting import _signals

from .html_validation import validate_rendered_html
from .inputs import (
    _assert_snapshot,
    _fail,
    _reject_symlink_components,
    _snapshot_regular,
)
from .models import FileSnapshot, LockOwnership, RenderContext, ReportRenderError


def _create_directories(path: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while not os.path.lexists(current):
        missing.append(current)
        if current == current.parent:
            break
        current = current.parent
    if os.path.lexists(current):
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(f"Report output ancestor is not a non-symlink directory: {current}")
    created: list[Path] = []
    try:
        for directory in reversed(missing):
            os.mkdir(directory, 0o755)
            created.append(directory)
    except OSError as exc:
        for directory in reversed(created):
            with contextlib.suppress(OSError):
                directory.rmdir()
        _fail(f"Could not create report output directory {path}: {exc}")
    _reject_symlink_components(path, "report output directory")
    return created


def _remove_empty_created_directories(created: Sequence[Path]) -> None:
    for directory in reversed(created):
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            break


def _lock_payload(context: RenderContext, token: str) -> str:
    return (
        "owner\tNORAD_REPORT_HTML\n"
        f"pid\t{os.getpid()}\n"
        f"token\t{token}\n"
        f"run_id\t{context.summary['run_id']}\n"
        f"run_summary_sha256\t{context.run_summary_snapshot.sha256}\n"
    )


def _acquire_lock(context: RenderContext, token: str) -> LockOwnership:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(context.lock_path, flags, 0o600)
    except FileExistsError:
        _fail(f"Report render lock already exists: {context.lock_path}")
    except OSError as exc:
        _fail(f"Could not create report render lock {context.lock_path}: {exc}")
    metadata: os.stat_result | None = None
    try:
        metadata = os.fstat(descriptor)
        payload = _lock_payload(context, token).encode("utf-8")
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    except BaseException as original_exc:
        if metadata is None:
            try:
                metadata = os.fstat(descriptor)
            except OSError:
                metadata = None
        os.close(descriptor)
        try:
            if metadata is None:
                raise ReportRenderError("Could not capture owned report-lock identity")
            current = context.lock_path.lstat()
            if current.st_dev != metadata.st_dev or current.st_ino != metadata.st_ino:
                raise ReportRenderError(
                    "Report lock changed identity during interrupted "
                    f"acquisition: {context.lock_path}"
                )
            context.lock_path.unlink()
        except (OSError, ReportRenderError) as cleanup_exc:
            raise ReportRenderError(
                "Report lock acquisition was interrupted and owned cleanup "
                f"could not be proved: {cleanup_exc}"
            ) from original_exc
        raise
    os.close(descriptor)
    assert metadata is not None
    return LockOwnership(
        path=context.lock_path,
        token=token,
        device=metadata.st_dev,
        inode=metadata.st_ino,
    )


def _release_lock(ownership: LockOwnership) -> None:
    snapshot = _snapshot_regular(ownership.path, "owned report render lock")
    try:
        payload = ownership.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read owned report render lock: {exc}")
    if (
        snapshot.device != ownership.device
        or snapshot.inode != ownership.inode
        or f"token\t{ownership.token}\n" not in payload
    ):
        _fail(
            "Report render lock identity or ownership changed; refusing "
            f"cleanup: {ownership.path}"
        )
    ownership.path.unlink()


def _install_publication_signal_handlers() -> dict[int, Any]:
    return _signals.install(ReportRenderError, "Report", "report publication")


def _snapshot_at(snapshot: FileSnapshot, path: Path) -> FileSnapshot:
    return FileSnapshot(
        path=path,
        sha256=snapshot.sha256,
        device=snapshot.device,
        inode=snapshot.inode,
        size_bytes=snapshot.size_bytes,
        mtime_ns=snapshot.mtime_ns,
        ctime_ns=snapshot.ctime_ns,
    )


def _capture_moved_snapshot(
    path: Path,
    expected: FileSnapshot,
    label: str,
) -> FileSnapshot:
    current = _snapshot_regular(path, label)
    stable_identity = (
        current.device,
        current.inode,
        current.size_bytes,
        current.mtime_ns,
        current.sha256,
    )
    expected_identity = (
        expected.device,
        expected.inode,
        expected.size_bytes,
        expected.mtime_ns,
        expected.sha256,
    )
    if stable_identity != expected_identity:
        _fail(f"{label} changed identity or content during publication: {path}")
    return current


def _assert_predecessor(context: RenderContext) -> None:
    previous = context.previous_output_snapshot
    if previous is None:
        if os.path.lexists(context.output_html):
            _fail(
                "Report output appeared after initial validation; prepare a "
                f"fresh render context: {context.output_html}"
            )
        return
    _assert_snapshot(previous, "existing report output")
    validate_rendered_html(
        context.output_html,
        expected_banner=None,
    )
    _assert_snapshot(previous, "existing report output")


def _write_recovery_marker(path: Path, message: str) -> None:
    with contextlib.suppress(OSError, ReportRenderError):
        _write_owned_file(path, message.encode("utf-8"))


def _write_owned_file(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_owned_stage(
    path: Path,
    token: str,
    identity: tuple[int, int] | None,
) -> None:
    if not os.path.lexists(path):
        return
    metadata = path.lstat()
    if (
        token not in path.name
        or identity is None
        or (metadata.st_dev, metadata.st_ino) != identity
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail(f"Refusing to remove unverified report staging path: {path}")
    shutil.rmtree(path)


def _recheck_inputs(context: RenderContext) -> None:
    labels = (
        "run-summary document",
        "report QMD template",
        "report CSS template",
        "Quarto executable",
        *(f"approved report table {table.table_id!r}" for table in context.tables),
    )
    for snapshot, label in zip(context.input_snapshots, labels):
        _assert_snapshot(snapshot, label)


_restore_signal_handlers = _signals.restore
