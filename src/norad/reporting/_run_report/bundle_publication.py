"""Receipt-last atomic publication for multi-format report bundles."""

from __future__ import annotations

import os
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

from norad.reporting._run_report import html as html_report

from .bundle_context import _read_receipt_tsv
from .bundle_models import BundleContext
from .pdf_projection import _pdf_body, _run_quarto, _validate_pdf
from .receipt_projection import (
    _receipt_document,
    _receipt_tsv_bytes,
    _summary_tsv_bytes,
    _validate_summary_tsv,
)


def _fail(message: str) -> None:
    raise html_report.ReportRenderError(message)


def _recheck_inputs(context: BundleContext) -> None:
    html_report._recheck_inputs(context.html)
    html_report._assert_snapshot(context.pdf_template_snapshot, "PDF report template")


def _assert_predecessors(context: BundleContext) -> None:
    for path in context.stable_paths:
        previous = context.previous_snapshots.get(path)
        if previous is None:
            if os.path.lexists(path):
                _fail(f"Report output appeared after preflight: {path}")
        else:
            html_report._assert_snapshot(
                previous, f"existing report output {path.name}"
            )


def publish_bundle(context: BundleContext) -> None:
    created = html_report._create_directories(context.html.output_dir)
    directory_meta = context.html.output_dir.lstat()
    directory_identity = (directory_meta.st_dev, directory_meta.st_ino)
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    stage = context.html.output_dir / f".run-report-bundle.{token}.tmp"
    recovery = (
        context.html.output_dir
        / f".{context.html.summary['run_id']}.report-bundle.{token}.RECOVERY.txt"
    )
    ownership: html_report.LockOwnership | None = None
    handlers: dict[int, Any] | None = None
    stage_identity: tuple[int, int] | None = None
    backups: dict[Path, tuple[Path, html_report.FileSnapshot]] = {}
    published: dict[Path, html_report.FileSnapshot] = {}
    committed = False
    recovery_required = False

    def assert_directory() -> None:
        metadata = context.html.output_dir.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != directory_identity
        ):
            _fail("Report output directory changed identity during publication")

    try:
        handlers = html_report._install_publication_signal_handlers()
        ownership = html_report._acquire_lock(context.html, token)
        assert_directory()
        _assert_predecessors(context)
        os.mkdir(stage, 0o700)
        metadata = stage.lstat()
        stage_identity = (metadata.st_dev, metadata.st_ino)
        _recheck_inputs(context)
        staged_outputs: list[tuple[str, str, Path, Path, int | None]] = []
        if "html" in context.requested_formats:
            rendered_html = html_report._render_with_quarto(context.html, stage)
            staged_outputs.append(
                (
                    "run-report-html",
                    "html",
                    rendered_html,
                    context.html.output_html,
                    None,
                )
            )
        if "pdf" in context.requested_formats:
            source = stage / f"{context.html.summary['run_id']}.run_report_pdf.qmd"
            html_report._write_owned_file(source, _pdf_body(context))
            rendered_pdf = _run_quarto(
                context,
                stage,
                source=source,
                target="typst",
                output_name=context.output_pdf.name,
            )
            page_count = _validate_pdf(
                rendered_pdf,
                html_report.SCIENCE_BANNERS[context.html.summary["science_status"]],
            )
            staged_outputs.append(
                ("run-report-pdf", "pdf", rendered_pdf, context.output_pdf, page_count)
            )
        staged_summary = stage / context.output_summary_tsv.name
        html_report._write_owned_file(staged_summary, _summary_tsv_bytes(context))
        _validate_summary_tsv(staged_summary, context)
        staged_outputs.append(
            (
                "run-summary-tsv",
                "run_summary_tsv",
                staged_summary,
                context.output_summary_tsv,
                None,
            )
        )
        receipt_document = _receipt_document(context, staged_outputs)
        staged_receipt = stage / context.output_receipt.name
        html_report._write_owned_file(
            staged_receipt, _receipt_tsv_bytes(receipt_document)
        )
        read_back = _read_receipt_tsv(staged_receipt)
        if read_back != receipt_document:
            _fail("Staged report receipt did not round-trip deterministically")
        _recheck_inputs(context)
        assert_directory()
        _assert_predecessors(context)

        for final, snapshot in context.previous_snapshots.items():
            backup = context.html.output_dir / f".{final.name}.{token}.previous"
            if os.path.lexists(backup):
                _fail(f"Report backup path unexpectedly exists: {backup}")
            os.link(final, backup, follow_symlinks=False)
            backup_snapshot = html_report._capture_moved_snapshot(
                backup, snapshot, f"backed-up prior {final.name}"
            )
            backups[final] = (backup, backup_snapshot)
        for final in tuple(context.previous_snapshots):
            backup, backup_snapshot = backups[final]
            html_report._capture_moved_snapshot(
                final,
                backup_snapshot,
                f"prior {final.name} after backup link",
            )
            final.unlink()
            refreshed = html_report._snapshot_regular(
                backup,
                f"prior {final.name} backup after unlink",
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
        html_report._fsync_directory(context.html.output_dir)

        publication_order = [item for item in staged_outputs]
        publication_order.append(
            ("report-receipt", "receipt", staged_receipt, context.output_receipt, None)
        )
        for _, kind, staged, final, _ in publication_order:
            if os.path.lexists(final):
                _fail(f"Final report path appeared during publication: {final}")
            staged_snapshot = html_report._snapshot_regular(staged, f"staged {kind}")
            os.link(staged, final, follow_symlinks=False)
            published[final] = html_report._capture_moved_snapshot(
                final, staged_snapshot, f"published {kind}"
            )
            html_report._fsync_file(final)
            html_report._fsync_directory(context.html.output_dir)
        _read_receipt_tsv(context.output_receipt)
        if "html" in context.requested_formats:
            html_report.validate_rendered_html(
                context.html.output_html,
                expected_banner=html_report.SCIENCE_BANNERS[
                    context.html.summary["science_status"]
                ],
                expected_identity=html_report._expected_html_identity(context.html),
            )
        if "pdf" in context.requested_formats:
            _validate_pdf(
                context.output_pdf,
                html_report.SCIENCE_BANNERS[context.html.summary["science_status"]],
            )
        _validate_summary_tsv(context.output_summary_tsv, context)
        _recheck_inputs(context)
        committed = True
    except BaseException as original:
        rollback_errors: list[str] = []
        try:
            assert_directory()
            for final, snapshot in reversed(tuple(published.items())):
                if os.path.lexists(final):
                    html_report._assert_snapshot(
                        snapshot, f"owned published {final.name}"
                    )
                    final.unlink()
            for final, (backup, backup_snapshot) in backups.items():
                if os.path.lexists(final):
                    html_report._capture_moved_snapshot(
                        final,
                        backup_snapshot,
                        f"prior {final.name} that remained in place",
                    )
                    backup.unlink()
                    continue
                html_report._assert_snapshot(
                    backup_snapshot, f"prior backup {backup.name}"
                )
                os.link(backup, final, follow_symlinks=False)
                html_report._capture_moved_snapshot(
                    final, backup_snapshot, f"restored {final.name}"
                )
                backup.unlink()
            html_report._fsync_directory(context.html.output_dir)
        except BaseException as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            recovery_required = True
            html_report._write_recovery_marker(
                recovery,
                "Report bundle rollback was incomplete.\n"
                f"Original error: {original}\n"
                f"Rollback errors: {'; '.join(rollback_errors)}\n"
                f"Stage: {stage}\nLock: {context.html.lock_path}\n",
            )
            raise html_report.ReportRenderError(
                "Report bundle publication failed and rollback was incomplete; "
                "preserve the owned lock and recovery state"
            ) from original
        if isinstance(original, html_report.ReportRenderError):
            raise
        if isinstance(original, (KeyboardInterrupt, SystemExit)):
            raise
        raise html_report.ReportRenderError(str(original)) from original
    finally:
        cleanup_errors: list[str] = []
        active = sys.exc_info()[1]
        if not recovery_required:
            try:
                html_report._remove_owned_stage(stage, token, stage_identity)
                for _, (backup, backup_snapshot) in backups.items():
                    if os.path.lexists(backup):
                        if not committed:
                            _fail(f"Unexpected backup remains after rollback: {backup}")
                        html_report._assert_snapshot(
                            backup_snapshot, f"committed backup {backup.name}"
                        )
                        backup.unlink()
                html_report._fsync_directory(context.html.output_dir)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if ownership is not None and not recovery_required and not cleanup_errors:
            try:
                html_report._release_lock(ownership)
            except BaseException as exc:
                cleanup_errors.append(str(exc))
        if handlers is not None:
            html_report._restore_signal_handlers(handlers)
        if cleanup_errors:
            html_report._write_recovery_marker(
                recovery,
                "Report bundle cleanup was incomplete.\n"
                f"Active error: {active}\n"
                f"Cleanup errors: {'; '.join(cleanup_errors)}\n",
            )
            raise html_report.ReportRenderError(
                "Report bundle cleanup failed; preserve recovery evidence: "
                + "; ".join(cleanup_errors)
            ) from active
        if active is not None and not context.previous_snapshots:
            html_report._remove_empty_created_directories(created)
