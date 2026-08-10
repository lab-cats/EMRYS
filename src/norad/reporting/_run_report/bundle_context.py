"""Validated bundle-context preparation and predecessor intake."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from norad.reporting._run_report import html as html_report

from .bundle_models import PDF_TEMPLATE, RECEIPT_HEADER, BundleContext
from .receipt_projection import _validate_receipt


def _fail(message: str) -> None:
    raise html_report.ReportRenderError(message)


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
