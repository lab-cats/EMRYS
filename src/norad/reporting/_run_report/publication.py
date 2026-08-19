"""Receipt-last atomic publication for the two-view report transaction."""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from pathlib import Path
from typing import Any

from norad.reporting.report import ReportPublicationOps

from .context import expected_html_identity
from .inputs import _assert_input_recheck, _assert_snapshot, _fail, _snapshot_regular
from .models import (
    BOUNDARY_BANNER,
    FileSnapshot,
    LockOwnership,
    ReportContext,
    ReportRenderError,
)
from .receipt import (
    read_receipt_tsv,
    receipt_document,
    receipt_tsv_bytes,
    summary_tsv_bytes,
    validate_summary_tsv,
)
from .transaction import (
    _capture_moved_snapshot,
    _create_directories,
    _remove_empty_created_directories,
)
from .validation import validate_rendered_html


def _recheck_inputs(context: ReportContext) -> None:
    for recheck in context.input_rechecks:
        _assert_input_recheck(*recheck)


def _assert_predecessors(context: ReportContext) -> None:
    for path in context.stable_paths:
        previous = context.previous_snapshots.get(path)
        if previous is None:
            if os.path.lexists(path):
                _fail(f"Report output appeared after preflight: {path}")
        else:
            _assert_snapshot(previous, f"existing report output {path.name}")


def _assert_expected_bytes(path: Path, expected: bytes, label: str) -> FileSnapshot:
    snapshot = _snapshot_regular(path, label)
    if (
        snapshot.size_bytes != len(expected)
        or snapshot.sha256 != hashlib.sha256(expected).hexdigest()
    ):
        _fail(f"{label} differs from its deterministic projection: {path}")
    _assert_snapshot(snapshot, label)
    return snapshot


def _assert_receipted_outputs(document: dict[str, Any]) -> None:
    for output in document["outputs"]:
        path = Path(output["path"])
        snapshot = _snapshot_regular(path, f"receipted {output['kind']} output")
        if (
            snapshot.size_bytes != output["size_bytes"]
            or snapshot.sha256 != output["sha256"]
        ):
            _fail(f"Published report output does not match its receipt: {path}")
        _assert_snapshot(snapshot, f"receipted {output['kind']} output")


def publish_report(context: ReportContext, ops: ReportPublicationOps) -> None:
    created = _create_directories(context.output_dir)
    directory_meta = context.output_dir.lstat()
    directory_identity = (directory_meta.st_dev, directory_meta.st_ino)
    token = ops.make_token()
    stage = context.output_dir / f".run-report.{token}.tmp"
    recovery = (
        context.output_dir / f".{context.summary['run_id']}.report.{token}.RECOVERY.txt"
    )
    ownership: LockOwnership | None = None
    handlers: dict[int, Any] | None = None
    stage_identity: tuple[int, int] | None = None
    backups: dict[Path, tuple[Path, FileSnapshot]] = {}
    published: dict[Path, FileSnapshot] = {}
    committed = False
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
        handlers = ops.install_signal_handlers()
        ownership = ops.acquire_lock(context, token, ops.lock_write)
        assert_directory()
        _assert_predecessors(context)
        os.mkdir(stage, 0o700)
        metadata = stage.lstat()
        stage_identity = (metadata.st_dev, metadata.st_ino)
        _recheck_inputs(context)

        staged_scientific_html = stage / context.output_scientific_html.name
        ops.write_owned_file(staged_scientific_html, context.scientific_html_bytes)
        _assert_expected_bytes(
            staged_scientific_html,
            context.scientific_html_bytes,
            "staged scientific HTML report",
        )
        validate_rendered_html(
            staged_scientific_html,
            expected_banner=BOUNDARY_BANNER,
            expected_identity=expected_html_identity(context, "scientific"),
        )
        staged_evidence_html = stage / context.output_evidence_html.name
        ops.write_owned_file(staged_evidence_html, context.evidence_html_bytes)
        _assert_expected_bytes(
            staged_evidence_html,
            context.evidence_html_bytes,
            "staged evidence HTML report",
        )
        validate_rendered_html(
            staged_evidence_html,
            expected_banner=BOUNDARY_BANNER,
            expected_identity=expected_html_identity(context, "evidence"),
        )
        staged_summary = stage / context.output_summary_tsv.name
        summary_bytes = summary_tsv_bytes(context)
        ops.write_owned_file(staged_summary, summary_bytes)
        _assert_expected_bytes(staged_summary, summary_bytes, "staged run-summary TSV")
        validate_summary_tsv(staged_summary, context)
        staged_outputs = (
            (
                "scientific-report-html",
                "scientific_html",
                staged_scientific_html,
                context.output_scientific_html,
            ),
            (
                "evidence-report-html",
                "evidence_html",
                staged_evidence_html,
                context.output_evidence_html,
            ),
            (
                "run-summary-tsv",
                "run_summary_tsv",
                staged_summary,
                context.output_summary_tsv,
            ),
        )
        document = receipt_document(context, staged_outputs)
        staged_receipt = stage / context.output_receipt.name
        receipt_bytes = receipt_tsv_bytes(document)
        ops.write_owned_file(staged_receipt, receipt_bytes)
        _assert_expected_bytes(staged_receipt, receipt_bytes, "staged report receipt")
        if read_receipt_tsv(staged_receipt) != document:
            _fail("Staged report receipt did not round-trip deterministically")
        _recheck_inputs(context)
        assert_directory()
        _assert_predecessors(context)

        for final, snapshot in context.previous_snapshots.items():
            backup = context.output_dir / f".{final.name}.{token}.previous"
            if os.path.lexists(backup):
                _fail(f"Report backup path unexpectedly exists: {backup}")
            ops.link(final, backup)
            backup_snapshot = _capture_moved_snapshot(
                backup, snapshot, f"backed-up prior {final.name}"
            )
            backups[final] = (backup, backup_snapshot)
        for final in tuple(context.previous_snapshots):
            backup, backup_snapshot = backups[final]
            _capture_moved_snapshot(
                final,
                backup_snapshot,
                f"prior {final.name} after backup link",
            )
            ops.unlink(final)
            refreshed = _snapshot_regular(
                backup, f"prior {final.name} backup after unlink"
            )
            if (
                refreshed.device,
                refreshed.inode,
                refreshed.size_bytes,
                refreshed.sha256,
            ) != (
                backup_snapshot.device,
                backup_snapshot.inode,
                backup_snapshot.size_bytes,
                backup_snapshot.sha256,
            ):
                _fail(f"Prior report backup changed content or identity: {backup}")
            backups[final] = (backup, refreshed)
        ops.fsync_directory(context.output_dir)

        for _output_id, kind, staged, final in (
            *staged_outputs,
            ("receipt", "receipt", staged_receipt, context.output_receipt),
        ):
            if os.path.lexists(final):
                _fail(f"Final report path appeared during publication: {final}")
            staged_snapshot = _snapshot_regular(staged, f"staged {kind}")
            ops.link(staged, final)
            published[final] = _capture_moved_snapshot(
                final, staged_snapshot, f"published {kind}"
            )
            ops.fsync_file(final)
            ops.fsync_directory(context.output_dir)

        _assert_expected_bytes(
            context.output_scientific_html,
            context.scientific_html_bytes,
            "published scientific HTML report",
        )
        _assert_expected_bytes(
            context.output_evidence_html,
            context.evidence_html_bytes,
            "published evidence HTML report",
        )
        _assert_expected_bytes(
            context.output_summary_tsv,
            summary_bytes,
            "published run-summary TSV",
        )
        _assert_expected_bytes(
            context.output_receipt,
            receipt_bytes,
            "published report receipt",
        )
        if read_receipt_tsv(context.output_receipt) != document:
            _fail("Published report receipt differs from its staged document")
        _assert_receipted_outputs(document)
        validate_rendered_html(
            context.output_scientific_html,
            expected_banner=BOUNDARY_BANNER,
            expected_identity=expected_html_identity(context, "scientific"),
        )
        validate_rendered_html(
            context.output_evidence_html,
            expected_banner=BOUNDARY_BANNER,
            expected_identity=expected_html_identity(context, "evidence"),
        )
        validate_summary_tsv(context.output_summary_tsv, context)
        _recheck_inputs(context)
        committed = True
    except BaseException as original:
        rollback_errors: list[str] = []
        try:
            assert_directory()
            for final, snapshot in reversed(tuple(published.items())):
                if os.path.lexists(final):
                    _assert_snapshot(snapshot, f"owned published {final.name}")
                    ops.unlink(final)
            for final, (backup, backup_snapshot) in backups.items():
                if os.path.lexists(final):
                    _capture_moved_snapshot(
                        final,
                        backup_snapshot,
                        f"prior {final.name} that remained in place",
                    )
                    ops.unlink(backup)
                    continue
                _assert_snapshot(backup_snapshot, f"prior backup {backup.name}")
                ops.link(backup, final)
                _capture_moved_snapshot(
                    final, backup_snapshot, f"restored {final.name}"
                )
                ops.unlink(backup)
            ops.fsync_directory(context.output_dir)
        except BaseException as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            recovery_required = True
            ops.write_recovery_marker(
                recovery,
                "Report rollback was incomplete.\n"
                f"Original error: {original}\n"
                f"Rollback errors: {'; '.join(rollback_errors)}\n"
                f"Stage: {stage}\nLock: {context.lock_path}\n",
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
                ops.remove_owned_stage(stage, token, stage_identity)
                for _, (backup, backup_snapshot) in backups.items():
                    if os.path.lexists(backup):
                        if not committed:
                            _fail(f"Unexpected backup remains after rollback: {backup}")
                        _assert_snapshot(
                            backup_snapshot, f"committed backup {backup.name}"
                        )
                        ops.unlink(backup)
                ops.fsync_directory(context.output_dir)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if ownership is not None and not recovery_required and not cleanup_errors:
            try:
                ops.release_lock(ownership)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if handlers is not None:
            try:
                ops.restore_signal_handlers(handlers)
            except BaseException as exc:
                cleanup_errors.append(f"signal-handler restoration failed: {exc}")
        if cleanup_errors:
            ops.write_recovery_marker(
                recovery,
                "Report cleanup was incomplete.\n"
                f"Active error: {active}\n"
                f"Cleanup errors: {'; '.join(cleanup_errors)}\n",
            )
            raise ReportRenderError(
                "Report cleanup failed; preserve recovery evidence: "
                + "; ".join(cleanup_errors)
            ) from active
        if active is not None and not context.previous_snapshots:
            _remove_empty_created_directories(created)
