"""Publish a validated NORAD HTML/PDF/TSV report bundle atomically.

This module coordinates the established HTML renderer with a deterministic
format-neutral PDF view. It consumes one explicit canonical run summary,
never discovers analysis inputs, and publishes a receipt last. Rendering does
not execute analysis or promote computational, scientific, or biological
state.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import stat
import subprocess
import sys
import uuid
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.reporting._run_report import html as html_report

from . import bundle_models as _models
from . import pdf_projection as _pdf
from . import receipt_projection as _receipt

contracts = html_report.contracts


BundleContext = _models.BundleContext
PDF_BODY_MARKER = _models.PDF_BODY_MARKER
PDF_SECTION_MARKERS = _models.PDF_SECTION_MARKERS
PDF_TEMPLATE = _models.PDF_TEMPLATE
PRODUCER = _models.PRODUCER
PRODUCER_VERSION = _models.PRODUCER_VERSION
RECEIPT_HEADER = _models.RECEIPT_HEADER
REPORT_RECEIPT_SCHEMA_VERSION = _models.REPORT_RECEIPT_SCHEMA_VERSION
SUMMARY_HEADER = _models.SUMMARY_HEADER
_markdown_escape = _pdf._markdown_escape
_pdf_body = _pdf._pdf_body
_pdf_candidate_summary = _pdf._pdf_candidate_summary
_pdf_code = _pdf._pdf_code
_pdf_hash = _pdf._pdf_hash
_run_quarto = _pdf._run_quarto
_validate_pdf = _pdf._validate_pdf
_receipt_document = _receipt._receipt_document
_receipt_tsv_bytes = _receipt._receipt_tsv_bytes
_summary_tsv_bytes = _receipt._summary_tsv_bytes
_truncations = _receipt._truncations
_validate_receipt = _receipt._validate_receipt
_validate_summary_tsv = _receipt._validate_summary_tsv

def _fail(message: str) -> None:
    raise html_report.ReportRenderError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render one canonical NORAD run summary as an atomic static "
            "HTML/PDF/TSV bundle. Dry-run is the default."
        )
    )
    parser.add_argument("--run-summary", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--quarto-bin", required=True, type=Path)
    parser.add_argument(
        "--formats",
        choices=("html", "pdf", "all"),
        default="all",
    )
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def _tool_first_line(path: Path, arguments: Sequence[str], label: str) -> str:
    command = [str(path), *arguments]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=html_report._sanitized_tool_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail(f"Could not inspect {label}: {exc}")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        _fail(f"Could not inspect {label}: {detail}")
    line = result.stdout.splitlines()[0].strip() if result.stdout else ""
    if not line:
        _fail(f"{label} returned no version text")
    return line


def _read_receipt_tsv(path: Path) -> dict[str, Any]:
    snapshot = html_report._snapshot_regular(path, "report output receipt")
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != RECEIPT_HEADER:
                _fail("Existing report receipt has an unexpected header")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not read existing report receipt: {exc}")
    if not rows:
        _fail("Existing report receipt must contain output rows")
    values = {row["report_receipt_json"] for row in rows}
    if len(values) != 1:
        _fail("Existing report receipt rows disagree on canonical JSON")
    try:
        document = json.loads(values.pop())
    except json.JSONDecodeError as exc:
        _fail(f"Existing report receipt JSON is invalid: {exc}")
    _validate_receipt(document)
    if [row["output_id"] for row in rows] != [
        item["output_id"] for item in document["outputs"]
    ]:
        _fail("Existing report receipt row order differs from its JSON record")
    html_report._assert_snapshot(snapshot, "report output receipt")
    return document




def _validate_existing_bundle(
    receipt_path: Path,
    output_dir: Path,
    known_paths: Sequence[Path],
) -> dict[Path, html_report.FileSnapshot]:
    present = [path for path in known_paths if os.path.lexists(path)]
    if not present:
        return {}
    if not os.path.lexists(receipt_path):
        html_only = len(present) == 1 and present[0].name.endswith(".run_report.html")
        if not html_only:
            _fail(
                "Existing report outputs are incomplete: only a valid "
                "HTML-only predecessor may exist without a bundle receipt"
            )
        snapshot = html_report._snapshot_regular(present[0], "HTML-only predecessor")
        html_report.validate_rendered_html(present[0], expected_banner=None)
        html_report._assert_snapshot(snapshot, "HTML-only predecessor")
        return {present[0]: snapshot}
    document = _read_receipt_tsv(receipt_path)
    snapshots: dict[Path, html_report.FileSnapshot] = {}
    declared: list[Path] = []
    for output in document["outputs"]:
        path = Path(output["path"])
        if path.parent != output_dir:
            _fail("Existing report receipt output is outside its run directory")
        snapshot = html_report._snapshot_regular(
            path, f"existing {output['kind']} output"
        )
        if (
            snapshot.sha256 != output["sha256"]
            or snapshot.size_bytes != output["size_bytes"]
        ):
            _fail(f"Existing report output does not match its receipt: {path}")
        declared.append(path)
        snapshots[path] = snapshot
    receipt_snapshot = html_report._snapshot_regular(
        receipt_path, "existing report receipt"
    )
    snapshots[receipt_path] = receipt_snapshot
    unexpected = set(present) - set(declared) - {receipt_path}
    if unexpected:
        _fail(
            "Existing report directory contains known outputs not declared by "
            f"its receipt: {sorted(str(path) for path in unexpected)}"
        )
    return snapshots


def prepare_context(arguments: argparse.Namespace) -> BundleContext:
    requested = ("html", "pdf") if arguments.formats == "all" else (arguments.formats,)
    base_arguments = argparse.Namespace(
        run_summary=arguments.run_summary,
        output_root=arguments.output_root,
        quarto_bin=arguments.quarto_bin,
        formats="html",
        execute=arguments.execute,
    )
    html_context = html_report.prepare_context(base_arguments)
    run_id = html_context.summary["run_id"]
    output_pdf = html_context.output_dir / f"{run_id}.run_report.pdf"
    output_summary_tsv = html_context.output_dir / f"{run_id}.run_summary.tsv"
    output_receipt = html_context.output_dir / f"{run_id}.report_outputs.tsv"
    bundle_lock = html_context.output_dir / f".{run_id}.report-bundle.lock"
    html_context = replace(
        html_context,
        lock_path=bundle_lock,
        previous_output_snapshot=None,
    )
    pdf_template_snapshot = html_report._snapshot_regular(
        PDF_TEMPLATE,
        "PDF report template",
    )
    stable_paths = tuple(
        path
        for path in (
            html_context.output_html,
            output_pdf,
            output_summary_tsv,
            output_receipt,
        )
    )
    for path in (*stable_paths, bundle_lock):
        html_report._reject_symlink_components(path, "report bundle path")
    if os.path.lexists(bundle_lock):
        _fail(f"Report bundle lock already exists: {bundle_lock}")
    previous = _validate_existing_bundle(
        output_receipt,
        html_context.output_dir,
        stable_paths,
    )
    pandoc_version = (
        _tool_first_line(
            html_context.quarto_path,
            ("pandoc", "--version"),
            "bundled Pandoc",
        )
        .removeprefix("pandoc ")
        .strip()
    )
    return BundleContext(
        html=html_context,
        formats=arguments.formats,
        requested_formats=requested,
        pdf_template_snapshot=pdf_template_snapshot,
        output_pdf=output_pdf,
        output_summary_tsv=output_summary_tsv,
        output_receipt=output_receipt,
        stable_paths=stable_paths,
        previous_snapshots=previous,
        pandoc_version=pandoc_version,
        execute=arguments.execute,
    )


























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


def print_plan(context: BundleContext) -> None:
    print("NORAD static run-report bundle plan:")
    print(f"  Mode: {'execute' if context.execute else 'dry-run'}")
    print(f"  Run ID: {context.html.summary['run_id']}")
    print(f"  Run summary: {context.html.run_summary_path}")
    print(f"  Run-summary SHA-256: {context.html.run_summary_snapshot.sha256}")
    print(f"  Requested formats: {','.join(context.requested_formats)}")
    print(f"  Science status: {context.html.summary['science_status']}")
    print(
        f"  State banner: {html_report.SCIENCE_BANNERS[context.html.summary['science_status']]}"
    )
    print(f"  Quarto: {context.html.quarto_path}")
    print(f"  Pandoc: {context.pandoc_version}")
    if "html" in context.requested_formats:
        print(f"  HTML output: {context.html.output_html}")
    if "pdf" in context.requested_formats:
        print(f"  PDF output: {context.output_pdf}")
    print(f"  Summary TSV: {context.output_summary_tsv}")
    print(f"  Receipt (published last): {context.output_receipt}")
    print("  Report meaning: rendering does not establish validation.")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        context = prepare_context(parse_arguments(argv))
        print_plan(context)
        if context.execute:
            publish_bundle(context)
            print(f"Published report bundle: {context.output_receipt}")
        else:
            print(
                "Dry-run only. Add --execute to publish; no output, lock, or "
                "scratch path was created."
            )
        return 0
    except html_report.ReportRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
