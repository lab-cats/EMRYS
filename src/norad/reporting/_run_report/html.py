"""Render one canonical NORAD run summary as a static report bundle.

The command is explicit-input-only and dry-run-first. It validates one
``norad.run_summary`` v1.1 document and may read only the TSVs explicitly
authorized by that document's ``approved_report_tables`` records. It never
discovers pipeline outputs, executes analysis code, installs software, or
promotes computational or scientific status.
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

from norad.contracts.artifacts import validate_artifact_contracts as _contracts

from . import context as _context
from . import html_projection as _projection
from . import html_publication as _publication
from . import html_validation as _validation
from . import inputs as _inputs
from . import models as _models
from . import runtime as _runtime
from . import transaction as _transaction

ACTIVE_RESOURCE_ATTRIBUTES = _models.ACTIVE_RESOURCE_ATTRIBUTES
BODY_MARKER = _models.BODY_MARKER
CANDIDATE_TERMINOLOGY = _models.CANDIDATE_TERMINOLOGY
CSS_MARKER = _models.CSS_MARKER
CSS_RESOURCE_RE = _models.CSS_RESOURCE_RE
CSS_TEMPLATE = _models.CSS_TEMPLATE
EXECUTABLE_QMD_RE = _models.EXECUTABLE_QMD_RE
EXPECTED_QMD_BODY = _models.EXPECTED_QMD_BODY
EXPECTED_QMD_FRONTMATTER = _models.EXPECTED_QMD_FRONTMATTER
PRODUCER = _models.PRODUCER
PRODUCER_VERSION = _models.PRODUCER_VERSION
QMD_TEMPLATE = _models.QMD_TEMPLATE
QUARTO_VERSION = _models.QUARTO_VERSION
REMOTE_URI_RE = _models.REMOTE_URI_RE
REPORT_SECTION_IDS = _models.REPORT_SECTION_IDS
RUN_SUMMARY_SCHEMA_VERSION = _models.RUN_SUMMARY_SCHEMA_VERSION
SAFE_RENDER_PATH = _models.SAFE_RENDER_PATH
SCIENCE_BANNERS = _models.SCIENCE_BANNERS
ApprovedTable = _models.ApprovedTable
FileSnapshot = _models.FileSnapshot
LockOwnership = _models.LockOwnership
RenderContext = _models.RenderContext
ReportRenderError = _models.ReportRenderError
contracts = _contracts

_artifact_overview = _projection._artifact_overview
_category = _projection._category
_empty = _projection._empty
_escape = _projection._escape
_failed_scope_summary = _projection._failed_scope_summary
_fallback_render_metadata = _projection._fallback_render_metadata
_key_value_table = _projection._key_value_table
_render_approved_table = _projection._render_approved_table
_render_artifact_appendix = _projection._render_artifact_appendix
_render_attempt_lineage = _projection._render_attempt_lineage
_render_decisions = _projection._render_decisions
_render_evidence_categories = _projection._render_evidence_categories
_render_evidence_index = _projection._render_evidence_index
_render_input_artifacts = _projection._render_input_artifacts
_render_issues = _projection._render_issues
_render_json_block = _projection._render_json_block
_render_limitations = _projection._render_limitations
_render_qc_metrics = _projection._render_qc_metrics
_render_report_provenance = _projection._render_report_provenance
_render_rerun_implications = _projection._render_rerun_implications
_render_run_identity = _projection._render_run_identity
_render_science_methods = _projection._render_science_methods
_render_scope_matrix = _projection._render_scope_matrix
_render_status_panels = _projection._render_status_panels
_render_table_inventory = _projection._render_table_inventory
_render_tools = _projection._render_tools
_scientific_record = _projection._scientific_record
_section = _projection._section
_status = _projection._status
_status_class = _projection._status_class
_table = _projection._table
_tables_for_roles = _projection._tables_for_roles
build_report_body = _projection.build_report_body
_assert_snapshot = _inputs._assert_snapshot
_explicit_path = _inputs._explicit_path
_fail = _inputs._fail
_load_run_summary = _inputs._load_run_summary
_read_approved_table = _inputs._read_approved_table
_reject_symlink_components = _inputs._reject_symlink_components
_resolve_contract_file = _inputs._resolve_contract_file
_snapshot_regular = _inputs._snapshot_regular
ReportHTMLInspector = _validation.ReportHTMLInspector
_validate_css_resources = _validation._validate_css_resources
build_qmd_bytes = _validation.build_qmd_bytes
validate_qmd_template = _validation.validate_qmd_template
validate_rendered_html = _validation.validate_rendered_html
_expected_html_identity = _context._expected_html_identity
prepare_context = _context.prepare_context
_quarto_version = _runtime._quarto_version
_run_quarto_process = _runtime._run_quarto_process
_sanitized_tool_environment = _runtime._sanitized_tool_environment
_source_date_epoch = _runtime._source_date_epoch
_terminate_process_group = _runtime._terminate_process_group
_acquire_lock = _transaction._acquire_lock
_assert_predecessor = _transaction._assert_predecessor
_capture_moved_snapshot = _transaction._capture_moved_snapshot
_create_directories = _transaction._create_directories
_fsync_directory = _transaction._fsync_directory
_fsync_file = _transaction._fsync_file
_install_publication_signal_handlers = _transaction._install_publication_signal_handlers
_lock_payload = _transaction._lock_payload
_recheck_inputs = _transaction._recheck_inputs
_release_lock = _transaction._release_lock
_remove_empty_created_directories = _transaction._remove_empty_created_directories
_remove_owned_stage = _transaction._remove_owned_stage
_restore_signal_handlers = _transaction._restore_signal_handlers
_snapshot_at = _transaction._snapshot_at
_write_owned_file = _transaction._write_owned_file
_write_recovery_marker = _transaction._write_recovery_marker
_render_with_quarto = _publication._render_with_quarto
publish_report = _publication.publish_report


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render one validated NORAD run-summary JSON as a static, "
            "self-contained HTML report. Dry-run is the default."
        )
    )
    parser.add_argument(
        "--run-summary",
        required=True,
        type=Path,
        help="Explicit canonical <run-id>.run_summary.json input.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    parser.add_argument(
        "--quarto-bin",
        required=True,
        type=Path,
        help=f"Explicit Quarto {QUARTO_VERSION} executable.",
    )
    parser.add_argument(
        "--formats",
        choices=("html", "pdf", "all"),
        default="all",
        help=(
            "Presentation format. The default all publishes HTML and PDF; "
            "every mode also publishes a deterministic summary TSV and "
            "receipt."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the validated HTML report. Omit for dry-run.",
    )
    return parser.parse_args(argv)


def print_plan(context: RenderContext) -> None:
    mode = "execute" if context.execute else "dry-run"
    print("NORAD static run-report plan:")
    print(f"  Mode: {mode}")
    print(f"  Run ID: {context.summary['run_id']}")
    print(f"  Run summary: {context.run_summary_path}")
    print(f"  Run-summary SHA-256: {context.run_summary_snapshot.sha256}")
    print(f"  Science status: {context.summary['science_status']}")
    print(f"  State banner: {SCIENCE_BANNERS[context.summary['science_status']]}")
    print(f"  Approved report tables: {len(context.tables)}")
    for table in context.tables:
        print(
            f"    {table.table_id}: {table.path} "
            f"(rows={table.row_count}, display={table.displayed_row_count}, "
            f"sha256={table.sha256})"
        )
    print(f"  Quarto: {context.quarto_path}")
    print(f"  Quarto version: {QUARTO_VERSION}")
    print(f"  QMD template: {context.template_snapshot.path}")
    print(f"  CSS template: {context.css_snapshot.path}")
    print(f"  HTML output: {context.output_html}")
    print(
        "  Report meaning: rendering does not establish computational or "
        "scientific validation."
    )


def html_core_main(argv: Sequence[str] | None = None) -> int:
    """Run the established HTML core used by the bundle coordinator."""

    try:
        arguments = parse_arguments(argv)
        if arguments.formats != "html":
            _fail("The internal HTML core accepts only --formats html")
        context = prepare_context(arguments)
        print_plan(context)
        if context.execute:
            publish_report(context)
            print(f"Published self-contained HTML report: {context.output_html}")
        else:
            print(
                "Dry-run only. Add --execute to publish the HTML report; no "
                "output, lock, or scratch path was created."
            )
        return 0
    except ReportRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the owner-private HTML-only entry point."""

    return html_core_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
