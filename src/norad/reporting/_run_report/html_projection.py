"""Deterministic HTML projection for static NORAD run reports."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from . import html_components as _components
from . import html_computational as _computational
from . import html_science as _science
from .models import (
    CANDIDATE_TERMINOLOGY,
    KNOWN_REPORT_ROLES,
    SCIENCE_BANNERS,
    ApprovedTable,
)

_artifact_overview = _computational._artifact_overview
_category = _components._category
_empty = _components._empty
_escape = _components._escape
_failed_scope_summary = _computational._failed_scope_summary
_fallback_render_metadata = _components._fallback_render_metadata
_key_value_table = _components._key_value_table
_render_approved_table = _components._render_approved_table
_render_artifact_appendix = _computational._render_artifact_appendix
_render_attempt_lineage = _computational._render_attempt_lineage
_render_decisions = _science._render_decisions
_render_evidence_categories = _science._render_evidence_categories
_render_evidence_index = _science._render_evidence_index
_render_input_artifacts = _science._render_input_artifacts
_render_issues = _computational._render_issues
_render_json_block = _components._render_json_block
_render_limitations = _science._render_limitations
_render_qc_metrics = _computational._render_qc_metrics
_render_report_provenance = _computational._render_report_provenance
_render_rerun_implications = _science._render_rerun_implications
_render_run_identity = _computational._render_run_identity
_render_science_methods = _science._render_science_methods
_render_scope_matrix = _computational._render_scope_matrix
_render_status_panels = _computational._render_status_panels
_render_table_inventory = _computational._render_table_inventory
_render_tools = _computational._render_tools
_scientific_record = _science._scientific_record
_section = _components._section
_status = _components._status
_status_class = _components._status_class
_table = _components._table
_tables_for_roles = _components._tables_for_roles

def build_report_body(
    summary: Mapping[str, Any],
    tables: Sequence[ApprovedTable],
    render_metadata: Mapping[str, str] | None = None,
) -> str:
    """Build deterministic escaped raw HTML for the static QMD view."""

    metadata = (
        dict(render_metadata)
        if render_metadata is not None
        else _fallback_render_metadata()
    )
    science_status = summary["science_status"]
    banner = SCIENCE_BANNERS[science_status]
    tables_by_role: dict[str, list[ApprovedTable]] = defaultdict(list)
    for table in tables:
        tables_by_role[table.role].append(table)

    overview = "\n".join(
        (
            _section(
                "status-section",
                "Computational and scientific status",
                _render_status_panels(summary),
            ),
            _section(
                "candidate-section",
                f"{CANDIDATE_TERMINOLOGY} and adjudication summaries",
                _tables_for_roles(
                    tables_by_role,
                    ("candidate_selection", "candidate_adjudication"),
                    (
                        "No candidate-selection or adjudication table was "
                        "explicitly approved. No candidate row is displayed "
                        "or inferred."
                    ),
                ),
            ),
            _section(
                "limitations-section",
                "Limitations and interpretation boundary",
                _render_limitations(summary)
                + "\n"
                + _tables_for_roles(
                    tables_by_role,
                    ("limitations",),
                    "No separate limitations table was explicitly approved.",
                ),
            ),
        )
    )
    qc_and_orientation = _section(
        "qc-orientation-section",
        "QC, orientation, annotation, and Step 07 to Step 09 funnel",
        _render_qc_metrics(summary)
        + "\n"
        + _render_evidence_categories(summary)
        + "\n"
        + _tables_for_roles(
            tables_by_role,
            (
                "orientation_locus_audit",
                "annotation_audit",
                "qc_funnel",
            ),
            (
                "No orientation-locus, annotation-audit, or QC-funnel table "
                "was explicitly approved. Statuses remain visible above; row "
                "content was not discovered."
            ),
        ),
    )
    replicates_and_sensitivity = _section(
        "replicate-sensitivity-section",
        "Replicate, sensitivity, and leave-one-pair-out summaries",
        _tables_for_roles(
            tables_by_role,
            (
                "replicate_effects",
                "sensitivity_matrix",
                "leave_one_pair_out",
            ),
            (
                "No replicate-effect, sensitivity, or leave-one-pair-out table "
                "was explicitly approved."
            ),
        ),
    )
    review_decisions = "\n".join(
        (
            _section(
                "decisions-section",
                ("Background, matched-DNA, orthogonal-evidence, and review decisions"),
                _render_decisions(summary)
                + "\n"
                + _tables_for_roles(
                    tables_by_role,
                    ("decisions",),
                    "No separate decision table was explicitly approved.",
                ),
            ),
            _section(
                "rerun-section",
                "Rerun implications",
                _render_rerun_implications(summary),
            ),
        )
    )
    evidence_and_provenance = "\n".join(
        (
            _section(
                "run-identity-section",
                "Run identity, inputs, hashes, and provenance",
                _render_run_identity(summary),
            ),
            _section(
                "scope-matrix-section",
                "Expected-step and missing-evidence matrix",
                _render_scope_matrix(summary),
            ),
            _section(
                "evidence-methods-section",
                "Evidence index and methods appendix",
                _render_evidence_index(summary)
                + "\n"
                + _tables_for_roles(
                    tables_by_role,
                    ("evidence_index",),
                    "No separate evidence-index table was explicitly approved.",
                )
                + "\n"
                + _render_input_artifacts(summary)
                + "\n"
                + _render_science_methods(summary)
                + "\n"
                + _render_attempt_lineage(summary)
                + "\n"
                + _render_artifact_appendix(summary)
                + "\n"
                + _render_table_inventory(tables)
                + "\n"
                + _render_tools(summary)
                + "\n"
                + _render_issues(summary)
                + "\n"
                + _render_json_block("Run-summary parameters", summary["parameters"])
                + "\n"
                + _render_json_block("Run-summary provenance", summary["provenance"])
                + "\n"
                + _render_report_provenance(metadata),
            ),
        )
    )
    unknown_tables = [table for table in tables if table.role not in KNOWN_REPORT_ROLES]
    if unknown_tables:
        evidence_and_provenance += "\n" + _section(
            "other-approved-tables-section",
            "Other explicitly approved report tables",
            "\n".join(_render_approved_table(table) for table in unknown_tables),
        )

    parts = [
        (
            '<main id="norad-report" tabindex="-1" '
            f'data-run-id="{_escape(summary["run_id"])}" '
            f'data-run-summary-sha256="{_escape(metadata["run_summary_sha256"])}" '
            f'data-renderer-version="{_escape(metadata["renderer_version"])}" '
            f'data-quarto-version="{_escape(metadata["quarto_version"])}" '
            f'data-qmd-sha256="{_escape(metadata["qmd_template_sha256"])}" '
            f'data-css-sha256="{_escape(metadata["css_template_sha256"])}">\n'
            f'<h1 id="norad-report-title">NORAD consolidated run report: '
            f"{_escape(summary['run_id'])}</h1>"
        ),
        (
            f'<div class="state-banner state-{_escape(science_status.replace("_", "-"))}" '
            'role="status" aria-live="polite">'
            f"{_escape(banner)}</div>"
        ),
        (
            '<p class="report-disclaimer">This report is a read-only view of '
            "declared evidence. Report generation is not evidence of local, "
            "runtime, cluster, scientific, or biological validation. Candidate "
            f"rows are described only as {_escape(CANDIDATE_TERMINOLOGY)}.</p>"
        ),
        (
            '<div class="report-category-tabs" role="group" '
            'aria-label="Report categories">'
        ),
        _category(
            "overview-category",
            "Overview",
            overview,
            open_by_default=True,
        ),
        _category(
            "qc-category",
            "QC and orientation",
            qc_and_orientation,
        ),
        _category(
            "replicate-category",
            "Replicates and sensitivity",
            replicates_and_sensitivity,
        ),
        _category(
            "review-category",
            "Review decisions",
            review_decisions,
        ),
        _category(
            "evidence-category",
            "Evidence and provenance",
            evidence_and_provenance,
        ),
        "</div>",
        (
            '<p class="report-disclaimer">End of report. '
            f"{_escape(banner)} Report generation did not change any recorded "
            "status.</p>\n</main>"
        ),
    ]
    return "\n\n".join(parts) + "\n"
