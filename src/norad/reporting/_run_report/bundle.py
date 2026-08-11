"""Publish a validated NORAD HTML/PDF/TSV report bundle atomically.

This module coordinates the established HTML renderer with a deterministic
format-neutral PDF view. It consumes one explicit canonical run summary,
never discovers analysis inputs, and publishes a receipt last. Rendering does
not execute analysis or promote computational, scientific, or biological
state.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve()
src_root = str(_MODULE_PATH.parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.reporting._run_report import html as html_report

from . import bundle_context as _context
from . import bundle_models as _models
from . import bundle_publication as _publication
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
_read_receipt_tsv = _context._read_receipt_tsv
_tool_first_line = _context._tool_first_line
_validate_existing_bundle = _context._validate_existing_bundle
prepare_context = _context.prepare_context
_assert_predecessors = _publication._assert_predecessors
_recheck_inputs = _publication._recheck_inputs
publish_bundle = _publication.publish_bundle


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
