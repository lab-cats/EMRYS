"""Validated context preparation for one explicit HTML report transaction."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import stat
from importlib.resources import files
from pathlib import Path

from .inputs import (
    _assert_snapshot,
    _explicit_path,
    _fail,
    _load_run_summary,
    _read_approved_table,
    _reject_symlink_components,
    _snapshot_regular,
)
from .models import (
    CSS_RESOURCE,
    JINJA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    SCIENCE_BANNERS,
    TEMPLATE_RESOURCE,
    FileSnapshot,
    ReportContext,
)
from .receipt import read_receipt_tsv
from .validation import render_html
from .view import build_view


def expected_html_identity(context: ReportContext) -> dict[str, str]:
    metadata = context.render_metadata
    return {
        "data-css-sha256": metadata["css_sha256"],
        "data-jinja-version": metadata["jinja_version"],
        "data-renderer-version": metadata["renderer_version"],
        "data-run-id": context.summary["run_id"],
        "data-run-summary-sha256": metadata["run_summary_sha256"],
        "data-template-sha256": metadata["template_sha256"],
    }


def _resource_snapshot(resource: str, label: str) -> FileSnapshot:
    traversable = files("norad.reporting").joinpath(resource)
    return _snapshot_regular(Path(str(traversable)), label)


def _validate_output_root(output_root: Path, output_dir: Path) -> None:
    if os.path.lexists(output_root):
        metadata = output_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output root must be a non-symlink directory when it "
                f"exists: {output_root}"
            )
    if os.path.lexists(output_dir):
        metadata = output_dir.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail(
                "Report output directory must be a non-symlink directory when "
                f"it exists: {output_dir}"
            )


def _existing_outputs(
    output_dir: Path,
    output_html: Path,
    output_summary_tsv: Path,
    output_receipt: Path,
    legacy_pdf: Path,
) -> dict[Path, FileSnapshot]:
    known = (output_html, output_summary_tsv, output_receipt, legacy_pdf)
    present = [path for path in known if os.path.lexists(path)]
    if not present:
        return {}
    if legacy_pdf in present or not os.path.lexists(output_receipt):
        _fail(
            "Existing report outputs use the retired v1 contract or are "
            "incomplete. Use a fresh output root or an explicitly approved migration; "
            "the v2 publisher will not adopt or overwrite them."
        )
    try:
        document = read_receipt_tsv(output_receipt)
    except Exception as exc:
        _fail(
            "Existing report receipt is not the active v2 contract. Use a fresh "
            f"output root or an explicitly approved migration: {exc}"
        )
    snapshots: dict[Path, FileSnapshot] = {}
    for output in document["outputs"]:
        path = Path(output["path"])
        if path.parent != output_dir:
            _fail("Existing report receipt output is outside its run directory")
        snapshot = _snapshot_regular(path, f"existing {output['kind']} output")
        if (
            snapshot.sha256 != output["sha256"]
            or snapshot.size_bytes != output["size_bytes"]
        ):
            _fail(f"Existing report output does not match its receipt: {path}")
        snapshots[path] = snapshot
    receipt_snapshot = _snapshot_regular(output_receipt, "existing report receipt")
    snapshots[output_receipt] = receipt_snapshot
    if set(present) != set(snapshots):
        _fail("Existing report outputs differ from the active v2 receipt")
    return snapshots


def prepare_context(arguments: argparse.Namespace) -> ReportContext:
    run_summary_path = _explicit_path(arguments.run_summary, "run-summary path")
    run_summary_snapshot = _snapshot_regular(run_summary_path, "run-summary document")
    summary = _load_run_summary(run_summary_path)
    _assert_snapshot(run_summary_snapshot, "run-summary document")
    run_id = summary["run_id"]
    expected_name = f"{run_id}.run_summary.json"
    if run_summary_path.name != expected_name or run_summary_path.parent.name != run_id:
        _fail(
            "Canonical run-summary input must use "
            f"<run-id>/{expected_name}; observed {run_summary_path}"
        )

    tables = tuple(
        _read_approved_table(record) for record in summary["approved_report_tables"]
    )
    template_snapshot = _resource_snapshot(TEMPLATE_RESOURCE, "report Jinja template")
    css_snapshot = _resource_snapshot(CSS_RESOURCE, "report CSS resource")
    installed_jinja = importlib.metadata.version("Jinja2")
    if installed_jinja != JINJA_VERSION:
        _fail(
            f"Installed Jinja2 version must match the lock: observed "
            f"{installed_jinja}; expected {JINJA_VERSION}"
        )

    output_root = _explicit_path(arguments.output_root, "report output root")
    _reject_symlink_components(output_root, "report output root")
    output_dir = output_root / run_id
    output_html = output_dir / f"{run_id}.run_report.html"
    output_summary_tsv = output_dir / f"{run_id}.run_summary.tsv"
    output_receipt = output_dir / f"{run_id}.report_outputs.tsv"
    legacy_pdf = output_dir / f"{run_id}.run_report.pdf"
    lock_path = output_dir / f".{run_id}.report.lock"
    stable_paths = (output_html, output_summary_tsv, output_receipt)
    for path in (output_dir, *stable_paths, legacy_pdf, lock_path):
        _reject_symlink_components(path, "report publication path")
    _validate_output_root(output_root, output_dir)
    if os.path.lexists(lock_path):
        _fail(f"Report publication lock already exists: {lock_path}")
    previous = _existing_outputs(
        output_dir,
        output_html,
        output_summary_tsv,
        output_receipt,
        legacy_pdf,
    )

    try:
        css = css_snapshot.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(f"Could not read report CSS resource: {exc}")
    metadata = {
        "css_path": f"norad.reporting/{CSS_RESOURCE}",
        "css_sha256": css_snapshot.sha256,
        "jinja_version": JINJA_VERSION,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
        "state_banner": SCIENCE_BANNERS[summary["science_status"]],
        "template_path": f"norad.reporting/{TEMPLATE_RESOURCE}",
        "template_sha256": template_snapshot.sha256,
    }
    html_bytes = render_html(build_view(summary, tables, metadata), css)
    for snapshot, label in (
        (run_summary_snapshot, "run-summary document"),
        (template_snapshot, "report Jinja template"),
        (css_snapshot, "report CSS resource"),
    ):
        _assert_snapshot(snapshot, label)
    return ReportContext(
        run_summary_path=run_summary_path,
        run_summary_snapshot=run_summary_snapshot,
        summary=summary,
        tables=tables,
        template_snapshot=template_snapshot,
        css_snapshot=css_snapshot,
        output_root=output_root,
        output_dir=output_dir,
        output_html=output_html,
        output_summary_tsv=output_summary_tsv,
        output_receipt=output_receipt,
        lock_path=lock_path,
        stable_paths=stable_paths,
        previous_snapshots=previous,
        render_metadata=metadata,
        html_bytes=html_bytes,
        execute=arguments.execute,
    )
