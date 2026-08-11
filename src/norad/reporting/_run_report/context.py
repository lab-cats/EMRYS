"""Validated render-context preparation for one explicit run summary."""

from __future__ import annotations

import argparse
import os
import stat

from .html_validation import (
    _validate_css_resources,
    build_qmd_bytes,
    validate_rendered_html,
)
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
    CSS_TEMPLATE,
    PRODUCER,
    PRODUCER_VERSION,
    QMD_TEMPLATE,
    QUARTO_VERSION,
    FileSnapshot,
    RenderContext,
)
from .runtime import _quarto_version


def _expected_html_identity(context: RenderContext) -> dict[str, str]:
    metadata = context.render_metadata
    return {
        "data-css-sha256": metadata["css_template_sha256"],
        "data-qmd-sha256": metadata["qmd_template_sha256"],
        "data-quarto-version": metadata["quarto_version"],
        "data-renderer-version": metadata["renderer_version"],
        "data-run-id": context.summary["run_id"],
        "data-run-summary-sha256": metadata["run_summary_sha256"],
    }


def prepare_context(arguments: argparse.Namespace) -> RenderContext:
    run_summary_path = _explicit_path(
        arguments.run_summary,
        "run-summary path",
    )
    run_summary_snapshot = _snapshot_regular(
        run_summary_path,
        "run-summary document",
    )
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
    template_snapshot = _snapshot_regular(
        QMD_TEMPLATE,
        "report QMD template",
    )
    css_snapshot = _snapshot_regular(
        CSS_TEMPLATE,
        "report CSS template",
    )
    quarto_path = _explicit_path(arguments.quarto_bin, "Quarto executable")
    quarto_snapshot = _snapshot_regular(
        quarto_path,
        "Quarto executable",
        executable=True,
    )
    _quarto_version(quarto_path)
    _assert_snapshot(quarto_snapshot, "Quarto executable")

    output_root = _explicit_path(arguments.output_root, "report output root")
    _reject_symlink_components(output_root, "report output root")
    output_dir = output_root / run_id
    output_html = output_dir / f"{run_id}.run_report.html"
    lock_path = output_dir / f".{run_id}.report-html.lock"
    for path, label in (
        (output_dir, "report output directory"),
        (output_html, "report HTML output"),
        (lock_path, "report lock"),
    ):
        _reject_symlink_components(path, label)

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
    previous_output_snapshot: FileSnapshot | None = None
    if os.path.lexists(output_html):
        metadata = output_html.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail(
                "Existing report output must be a regular non-symlink file: "
                f"{output_html}"
            )
        previous_output_snapshot = _snapshot_regular(
            output_html,
            "existing report output",
        )
        validate_rendered_html(
            output_html,
            expected_banner=None,
        )
        _assert_snapshot(
            previous_output_snapshot,
            "existing report output",
        )
    if os.path.lexists(lock_path):
        _fail(f"Report render lock already exists: {lock_path}")

    template_bytes = template_snapshot.path.read_bytes()
    css_bytes = css_snapshot.path.read_bytes()
    try:
        css_text = css_bytes.decode("utf-8")
    except UnicodeError as exc:
        _fail(f"Report CSS template is not UTF-8: {exc}")
    _validate_css_resources(css_text, "Report CSS template")
    render_metadata = {
        "css_template_path": str(css_snapshot.path),
        "css_template_sha256": css_snapshot.sha256,
        "qmd_template_path": str(template_snapshot.path),
        "qmd_template_sha256": template_snapshot.sha256,
        "quarto_path": str(quarto_snapshot.path),
        "quarto_sha256": quarto_snapshot.sha256,
        "quarto_version": QUARTO_VERSION,
        "renderer": PRODUCER,
        "renderer_version": PRODUCER_VERSION,
        "run_summary_path": str(run_summary_snapshot.path),
        "run_summary_sha256": run_summary_snapshot.sha256,
    }
    qmd_bytes = build_qmd_bytes(
        summary,
        tables,
        template_bytes=template_bytes,
        css_bytes=css_bytes,
        render_metadata=render_metadata,
    )
    for snapshot, label in (
        (run_summary_snapshot, "run-summary document"),
        (template_snapshot, "report QMD template"),
        (css_snapshot, "report CSS template"),
        (quarto_snapshot, "Quarto executable"),
    ):
        _assert_snapshot(snapshot, label)
    return RenderContext(
        run_summary_path=run_summary_path,
        run_summary_snapshot=run_summary_snapshot,
        summary=summary,
        tables=tables,
        template_snapshot=template_snapshot,
        css_snapshot=css_snapshot,
        quarto_path=quarto_path,
        quarto_snapshot=quarto_snapshot,
        output_root=output_root,
        output_dir=output_dir,
        output_html=output_html,
        lock_path=lock_path,
        previous_output_snapshot=previous_output_snapshot,
        render_metadata=render_metadata,
        qmd_bytes=qmd_bytes,
        execute=arguments.execute,
    )
