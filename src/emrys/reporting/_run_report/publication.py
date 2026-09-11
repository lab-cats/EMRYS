"""Receipt-last atomic publication for the two-view report transaction."""

from __future__ import annotations

import contextlib
import os
import stat
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from emrys.libraries.source_authority import admit_installed_package
from emrys.reporting import _files, _signals

from .context import recheck_evidence_context
from .inputs import (
    _assert_input_recheck,
    _fail,
    _reject_symlink_components,
    _snapshot_regular,
)
from .models import FileSnapshot, ReportContext, ReportRenderError
from .receipt import output_bytes
from .validation import validate_projected_outputs


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


def _recheck_inputs(context: ReportContext) -> None:
    if (
        admit_installed_package(root=context.installed_package.root).record
        != context.installed_package.record
    ):
        _fail("Installed report package changed after admission")
    for recheck in context.input_rechecks:
        _assert_input_recheck(*recheck)
    if context.evidence_context is not None:
        recheck_evidence_context(context.evidence_context, context.run_summary_snapshot)


def _assert_outputs_absent(context: ReportContext) -> None:
    if context.previous_snapshots:
        _fail(
            "Report publication requires absent outputs; existing transactions are read-only"
        )
    for path in context.stable_paths:
        if os.path.lexists(path):
            _fail(f"Report output appeared after preflight: {path}")


def publish_report(context: ReportContext) -> None:
    _assert_outputs_absent(context)
    created = _create_directories(context.output_dir)
    directory_meta = context.output_dir.lstat()
    directory_identity = (directory_meta.st_dev, directory_meta.st_ino)
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    stage = context.output_dir / f".run-report.{token}.tmp"
    recovery = (
        context.output_dir / f".{context.summary['run_id']}.report.{token}.RECOVERY.txt"
    )
    lock_payload = (
        "owner\tEMRYS_REPORT\n"
        f"pid\t{os.getpid()}\n"
        f"token\t{token}\n"
        f"run_id\t{context.summary['run_id']}\n"
        f"run_summary_sha256\t{context.run_summary_snapshot.sha256}\n"
    ).encode("utf-8")
    ownership: os.stat_result | None = None
    handlers: dict[int, Any] | None = None
    stage_identity: tuple[int, int] | None = None
    publication_anchors: dict[Path, FileSnapshot] = {}
    recovery_required = False

    def assert_directory() -> None:
        metadata = context.output_dir.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != directory_identity
        ):
            _fail("Report output directory changed identity during publication")

    try:
        handlers = _signals.install(ReportRenderError, "Report", "report publication")
        ownership = _files.acquire_lock(
            context.lock_path, lock_payload, ReportRenderError
        )
        assert_directory()
        _assert_outputs_absent(context)
        os.mkdir(stage, 0o700)
        metadata = stage.lstat()
        stage_identity = (metadata.st_dev, metadata.st_ino)
        _recheck_inputs(context)

        projected = output_bytes(context)
        staged_paths = tuple(stage / path.name for path in context.stable_paths)
        for path, payload in zip(staged_paths, projected, strict=True):
            _files.write_bytes_exclusive(path, payload)
        validate_projected_outputs(context, staged_paths, projected)
        _recheck_inputs(context)
        assert_directory()
        _assert_outputs_absent(context)
        _files.fsync_path(stage)
        _files.fsync_path(context.output_dir)

        for staged, final in zip(staged_paths, context.stable_paths, strict=True):
            if os.path.lexists(final):
                _fail(f"Final report path appeared during publication: {final}")
            staged_snapshot = _snapshot_regular(staged, "staged report output")
            publication_anchors[final] = staged_snapshot
            assert_directory()
            os.link(staged, final, follow_symlinks=False)
            assert_directory()
            _capture_moved_snapshot(final, staged_snapshot, "published report output")
            _files.fsync_path(final)
            _files.fsync_path(context.output_dir)

        validate_projected_outputs(context, context.stable_paths, projected)
        _recheck_inputs(context)
    except BaseException as original:
        rollback_errors: list[str] = []
        try:
            assert_directory()
            for final, anchor in reversed(tuple(publication_anchors.items())):
                try:
                    assert_directory()
                    if os.path.lexists(final):
                        _capture_moved_snapshot(
                            anchor.path, anchor, f"publication anchor for {final.name}"
                        )
                        _capture_moved_snapshot(
                            final, anchor, f"owned published {final.name}"
                        )
                        assert_directory()
                        final.unlink()
                except BaseException as rollback_exc:
                    rollback_errors.append(str(rollback_exc))
            assert_directory()
            _files.fsync_path(context.output_dir)
        except BaseException as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            recovery_required = True
            with contextlib.suppress(OSError, ReportRenderError):
                assert_directory()
                _files.write_bytes_exclusive(
                    recovery,
                    (
                        "Report rollback was incomplete.\n"
                        f"Original error: {original}\n"
                        f"Rollback errors: {'; '.join(rollback_errors)}\n"
                        f"Stage: {stage}\nLock: {context.lock_path}\n"
                    ).encode("utf-8"),
                )
            raise ReportRenderError(
                "Report publication failed and rollback was incomplete; preserve "
                "the owned lock and recovery state"
            ) from original
        if isinstance(original, ReportRenderError):
            raise
        if isinstance(original, (KeyboardInterrupt, SystemExit)):
            raise
        raise ReportRenderError(str(original)) from original
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required:
            try:
                assert_directory()
                _files.remove_owned_stage(
                    stage, token, stage_identity, ReportRenderError
                )
                assert_directory()
                _files.fsync_path(context.output_dir)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if ownership is not None and not recovery_required and not cleanup_errors:
            try:
                assert_directory()
                _files.release_lock(
                    context.lock_path, ownership, lock_payload, ReportRenderError
                )
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if handlers is not None:
            try:
                _signals.restore(handlers)
            except BaseException as exc:
                cleanup_errors.append(f"signal-handler restoration failed: {exc}")
        if cleanup_errors:
            with contextlib.suppress(OSError, ReportRenderError):
                assert_directory()
                _files.write_bytes_exclusive(
                    recovery,
                    (
                        "Report cleanup was incomplete.\n"
                        f"Active error: {active}\n"
                        f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    ).encode("utf-8"),
                )
            raise ReportRenderError(
                "Report cleanup failed; preserve recovery evidence: "
                + "; ".join(cleanup_errors)
            ) from active
        if active is not None and not recovery_required:
            assert_directory()
            _remove_empty_created_directories(created)
