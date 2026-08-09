"""Shared constants and immutable context for report-bundle rendering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from norad.reporting._run_report import html as html_report

contracts = html_report.contracts

_MODULE_PATH = Path(__file__).resolve()
PRODUCER = "render_run_report"
PRODUCER_VERSION = "1.1.0"
REPORT_RECEIPT_SCHEMA_VERSION = "1.1.0"
PDF_TEMPLATE = _MODULE_PATH.parent.parent / "templates" / "run_report_pdf.qmd"
PDF_BODY_MARKER = "{{NORAD_REPORT_PDF_BODY}}"
RECEIPT_HEADER = (
    "schema_name",
    "schema_version",
    "run_id",
    "attempt_id",
    "generated_at",
    "science_status",
    "requested_formats",
    "output_id",
    "kind",
    "path",
    "sha256",
    "size_bytes",
    "media_type",
    "self_contained",
    "page_count",
    "state_banner_every_page",
    "report_receipt_json",
)
SUMMARY_HEADER = (
    "run_id",
    "science_status",
    "step_id",
    "scope_type",
    "scope_id",
    "aggregate_state",
    *contracts.RUN_SUMMARY_STATUS_FIELDS,
    "warning_count",
    "error_count",
)
PDF_SECTION_MARKERS = (
    "NORAD consolidated run report",
    "Run identity",
    "Evidence status",
    "Limitations",
    "CMH-ranked candidates",
    "Evidence and methods",
)


@dataclass(frozen=True)
class BundleContext:
    html: html_report.RenderContext
    formats: str
    requested_formats: tuple[str, ...]
    pdf_template_snapshot: html_report.FileSnapshot
    output_pdf: Path
    output_summary_tsv: Path
    output_receipt: Path
    stable_paths: tuple[Path, ...]
    previous_snapshots: Mapping[Path, html_report.FileSnapshot]
    pandoc_version: str
    execute: bool

    @property
    def input_snapshots(self) -> tuple[html_report.FileSnapshot, ...]:
        return (*self.html.input_snapshots, self.pdf_template_snapshot)
