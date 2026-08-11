"""Validated atomic publication of one static HTML report."""

from __future__ import annotations

import os
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

from .context import _expected_html_identity
from .html_validation import validate_rendered_html
from .inputs import _assert_snapshot, _fail, _snapshot_regular
from .models import (
    SCIENCE_BANNERS,
    FileSnapshot,
    LockOwnership,
    RenderContext,
    ReportRenderError,
)
from .runtime import (
    _run_quarto_process,
    _sanitized_tool_environment,
    _source_date_epoch,
)
from .transaction import (
    _acquire_lock,
    _assert_predecessor,
    _capture_moved_snapshot,
    _create_directories,
    _fsync_directory,
    _fsync_file,
    _install_publication_signal_handlers,
    _recheck_inputs,
    _release_lock,
    _remove_empty_created_directories,
    _remove_owned_stage,
    _restore_signal_handlers,
    _write_owned_file,
    _write_recovery_marker,
)


def _render_with_quarto(
    context: RenderContext,
    stage: Path,
) -> Path:
    run_id = context.summary["run_id"]
    qmd_path = stage / f"{run_id}.run_report.qmd"
    output_name = f"{run_id}.run_report.html"
    output_path = stage / output_name
    project_path = stage / "_quarto.yml"
    _write_owned_file(qmd_path, context.qmd_bytes)
    project_bytes = (
        f"project:\n  type: default\n  render:\n    - {qmd_path.name}\n"
    ).encode()
    _write_owned_file(project_path, project_bytes)
    command = [
        str(context.quarto_path),
        "render",
        qmd_path.name,
        "--to",
        "html",
        "--output",
        output_name,
        "--no-execute",
    ]
    environment = _sanitized_tool_environment()
    environment["SOURCE_DATE_EPOCH"] = _source_date_epoch(context.summary)
    environment["DENO_DIR"] = str(stage / ".deno")
    runtime_tmp = stage / ".runtime-tmp"
    runtime_tmp.mkdir(mode=0o700)
    environment["TMPDIR"] = str(runtime_tmp)
    returncode, standard_output, standard_error = _run_quarto_process(
        command, stage, environment, _fail
    )
    if returncode != 0:
        detail = standard_error.strip() or standard_output.strip()
        _fail(f"Quarto render failed with exit {returncode}: {detail}")
    if standard_error.strip():
        print(standard_error.rstrip(), file=sys.stderr)
    for child in stage.iterdir():
        if child.is_dir() and child.name.endswith("_files"):
            _fail(
                "Quarto created a sidecar resource directory despite the "
                f"self-contained contract: {child}"
            )
    validate_rendered_html(
        output_path,
        expected_banner=SCIENCE_BANNERS[context.summary["science_status"]],
        expected_identity=_expected_html_identity(context),
    )
    return output_path


def publish_report(context: RenderContext) -> None:
    created = _create_directories(context.output_dir)
    output_dir_metadata = context.output_dir.lstat()
    output_dir_identity = (
        output_dir_metadata.st_dev,
        output_dir_metadata.st_ino,
    )
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    stage = context.output_dir / f".run-report.{token}.tmp"
    backup = context.output_dir / f".{context.output_html.name}.{token}.previous"
    recovery = (
        context.output_dir
        / f".{context.summary['run_id']}.report-html.{token}.RECOVERY.txt"
    )
    ownership: LockOwnership | None = None
    previous_signal_handlers: dict[int, Any] | None = None
    backed_up = False
    published = False
    committed = False
    recovery_required = False
    output_identity_lost = False
    stage_identity: tuple[int, int] | None = None
    rendered_snapshot: FileSnapshot | None = None
    backup_snapshot: FileSnapshot | None = None
    published_snapshot: FileSnapshot | None = None

    def assert_output_dir_identity() -> None:
        if not os.path.lexists(context.output_dir):
            _fail(
                "Report output directory disappeared during publication: "
                f"{context.output_dir}"
            )
        metadata = context.output_dir.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != output_dir_identity
        ):
            _fail(
                "Report output directory changed identity during publication: "
                f"{context.output_dir}"
            )

    try:
        previous_signal_handlers = _install_publication_signal_handlers()
        ownership = _acquire_lock(context, token)
        assert_output_dir_identity()
        _assert_predecessor(context)
        os.mkdir(stage, 0o700)
        stage_metadata = stage.lstat()
        stage_identity = (stage_metadata.st_dev, stage_metadata.st_ino)
        _recheck_inputs(context)
        rendered = _render_with_quarto(context, stage)
        rendered_snapshot = _snapshot_regular(
            rendered,
            "validated staged HTML report",
        )
        _fsync_file(rendered)
        _recheck_inputs(context)
        assert_output_dir_identity()
        _assert_predecessor(context)
        if os.path.lexists(backup):
            _fail(f"Report backup path unexpectedly exists: {backup}")
        if context.previous_output_snapshot is not None:
            backed_up = True
            os.link(
                context.output_html,
                backup,
                follow_symlinks=False,
            )
            backup_snapshot = _capture_moved_snapshot(
                backup,
                context.previous_output_snapshot,
                "backed-up prior HTML report",
            )
            _fsync_directory(context.output_dir)
            _capture_moved_snapshot(
                context.output_html,
                context.previous_output_snapshot,
                "existing report output",
            )
            context.output_html.unlink()
            _fsync_directory(context.output_dir)
        published = True
        os.link(
            rendered,
            context.output_html,
            follow_symlinks=False,
        )
        published_snapshot = _capture_moved_snapshot(
            context.output_html,
            rendered_snapshot,
            "newly published HTML report",
        )
        _fsync_file(context.output_html)
        _fsync_directory(context.output_dir)
        validate_rendered_html(
            context.output_html,
            expected_banner=SCIENCE_BANNERS[context.summary["science_status"]],
            expected_identity=_expected_html_identity(context),
        )
        _recheck_inputs(context)
        assert_output_dir_identity()
        committed = True
    except BaseException as original_exc:
        if committed:
            if isinstance(original_exc, ReportRenderError):
                raise
            if isinstance(original_exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise ReportRenderError(str(original_exc)) from original_exc
        rollback_errors: list[str] = []

        try:
            assert_output_dir_identity()
        except ReportRenderError as identity_exc:
            output_identity_lost = True
            recovery_required = True
            raise ReportRenderError(
                f"{original_exc}\nReport output directory identity changed "
                "during publication; path-based rollback was skipped to avoid "
                "modifying a replacement directory. Preserve the owned lock "
                f"and recovery state: {identity_exc}"
            ) from original_exc

        def rollback(label: str, operation: Any) -> None:
            nonlocal output_identity_lost
            try:
                assert_output_dir_identity()
            except ReportRenderError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")
                return
            try:
                operation()
                assert_output_dir_identity()
            except BaseException as rollback_exc:
                rollback_errors.append(f"{label}: {rollback_exc}")

        def remove_new_report() -> None:
            if not os.path.lexists(context.output_html):
                return
            if published_snapshot is None:
                if rendered_snapshot is None:
                    _fail(
                        "A final report exists but no owned staged report "
                        "snapshot was captured"
                    )
                _capture_moved_snapshot(
                    context.output_html,
                    rendered_snapshot,
                    "owned newly published HTML report",
                )
            else:
                _assert_snapshot(
                    published_snapshot,
                    "owned newly published HTML report",
                )
            context.output_html.unlink()

        def restore_prior_report() -> None:
            previous = context.previous_output_snapshot
            if previous is None:
                _fail("No prior report was declared for rollback")
            if os.path.lexists(backup):
                if backup_snapshot is None:
                    backup_snapshot_local = _capture_moved_snapshot(
                        backup,
                        previous,
                        "owned prior-report backup",
                    )
                else:
                    _assert_snapshot(
                        backup_snapshot,
                        "owned prior-report backup",
                    )
                    backup_snapshot_local = backup_snapshot
                if os.path.lexists(context.output_html):
                    _capture_moved_snapshot(
                        context.output_html,
                        previous,
                        "prior HTML report that remained during backup",
                    )
                    backup.unlink()
                    return
                os.link(
                    backup,
                    context.output_html,
                    follow_symlinks=False,
                )
                _capture_moved_snapshot(
                    context.output_html,
                    backup_snapshot_local,
                    "restored prior HTML report",
                )
                backup.unlink()
                return
            if os.path.lexists(context.output_html):
                _capture_moved_snapshot(
                    context.output_html,
                    previous,
                    "prior HTML report that remained in place",
                )
                return
            _fail(
                "Neither the validated prior report nor its owned backup "
                f"remains: {context.output_html}"
            )

        if published:
            rollback("remove owned new report", remove_new_report)
        if context.previous_output_snapshot is not None and backed_up:
            if not rollback_errors:
                rollback("restore validated prior report", restore_prior_report)
        elif context.previous_output_snapshot is not None:
            rollback(
                "verify prior report remained in place",
                restore_prior_report,
            )
        elif os.path.lexists(context.output_html):
            rollback(
                "remove unexpected first-publication output",
                remove_new_report,
            )
        if not rollback_errors:
            rollback(
                "durability-sync report rollback",
                lambda: _fsync_directory(context.output_dir),
            )
        if rollback_errors:
            recovery_required = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery,
                    "Report HTML rollback was incomplete.\n"
                    f"Original error: {original_exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Backup: {backup}\n"
                    f"Lock: {context.lock_path}\n",
                )
            raise ReportRenderError(
                "Report publication failed and rollback was incomplete. "
                "Preserve the owned lock and recovery state under "
                f"{context.output_dir}. Rollback errors: " + "; ".join(rollback_errors)
            ) from original_exc
        backed_up = False
        published = False
        if isinstance(original_exc, ReportRenderError):
            raise
        if isinstance(original_exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise ReportRenderError(str(original_exc)) from original_exc
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required and not output_identity_lost:
            try:
                assert_output_dir_identity()
                _remove_owned_stage(stage, token, stage_identity)
            except Exception as exc:
                cleanup_errors.append(f"owned stage cleanup failed: {exc}")
            if not cleanup_errors and os.path.lexists(backup):
                try:
                    if not committed or backup_snapshot is None:
                        _fail("Unexpected report backup remains after rollback")
                    _assert_snapshot(
                        backup_snapshot,
                        "owned committed report backup",
                    )
                    backup.unlink()
                    _fsync_directory(context.output_dir)
                except Exception as exc:
                    cleanup_errors.append(f"owned backup cleanup failed: {exc}")
        if (
            ownership is not None
            and not recovery_required
            and not output_identity_lost
            and not cleanup_errors
        ):
            try:
                _release_lock(ownership)
            except Exception as exc:
                cleanup_errors.append(f"owned lock cleanup failed: {exc}")
        if previous_signal_handlers is not None:
            try:
                _restore_signal_handlers(previous_signal_handlers)
            except BaseException as exc:
                cleanup_errors.append(f"signal-handler restoration failed: {exc}")
        if cleanup_errors:
            recovery_required = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery,
                    "Report HTML publication cleanup was incomplete.\n"
                    f"Active error: {active}\n"
                    f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    f"Stage: {stage}\n"
                    f"Backup: {backup}\n"
                    f"Lock: {context.lock_path}\n",
                )
            raise ReportRenderError(
                "Report publication cleanup failed; preserve the owned lock "
                f"and recovery state under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active
        if (
            active is not None
            and not recovery_required
            and not os.path.lexists(context.output_html)
        ):
            _remove_empty_created_directories(created)
