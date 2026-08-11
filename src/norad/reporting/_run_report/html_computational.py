"""Computational-status HTML sections for static NORAD run reports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .html_components import _empty, _escape, _key_value_table, _table
from .models import COMPUTATIONAL_STATUS_FIELDS, ApprovedTable


def _artifact_overview(summary: Mapping[str, Any]) -> str:
    rollup = summary["computational_rollup"]
    categories = (
        ("complete", rollup["complete_artifact_count"], "#287a5d"),
        ("missing", rollup["missing_artifact_count"], "#64748b"),
        ("incomplete", rollup["incomplete_artifact_count"], "#b7791f"),
        ("failed", rollup["failed_artifact_count"], "#b42318"),
        (
            "externally unavailable",
            rollup["externally_unavailable_artifact_count"],
            "#6b5ca5",
        ),
    )
    total = rollup["expected_artifact_count"]
    width = 720
    height = 82
    cursor = 0.0
    rectangles: list[str] = []
    for name, count, color in categories:
        segment = width * count / total if total else 0
        if count:
            rectangles.append(
                f'<rect x="{cursor:.3f}" y="18" width="{segment:.3f}" '
                f'height="30" fill="{color}"><title>'
                f"{_escape(name)}: {_escape(count)}</title></rect>"
            )
        cursor += segment
    accessible = ", ".join(f"{name}: {count}" for name, count, _ in categories)
    legend = "".join(
        f'<li class="legend-{_escape(name.replace(" ", "-"))}">'
        f"{_escape(name.title())}: {_escape(count)}</li>"
        for name, count, _ in categories
    )
    return (
        '<figure class="artifact-overview">\n'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="artifact-overview-title '
        'artifact-overview-description">\n'
        '<title id="artifact-overview-title">Expected artifact state overview'
        "</title>\n"
        '<desc id="artifact-overview-description">'
        f"{_escape(accessible)}</desc>\n"
        + "".join(rectangles)
        + f'<text x="0" y="70" font-size="14" fill="#17202a">'
        f"Expected artifacts: {_escape(total)}</text>\n"
        "</svg>\n"
        "<figcaption>Artifact availability is copied from the canonical run "
        "summary. This visualization is not validation evidence.</figcaption>\n"
        "</figure>\n"
        f'<ul class="artifact-legend" aria-label="Artifact state legend">'
        f"{legend}</ul>"
    )


def _failed_scope_summary(summary: Mapping[str, Any]) -> str:
    failed = [
        (
            scope_record["scope"]["step_id"],
            scope_record["scope"]["scope_type"],
            scope_record["scope"]["scope_id"],
        )
        for scope_record in summary["expected_scopes"]
        if scope_record["aggregate_state"] == "failed"
    ]
    if not failed:
        return '<p class="provenance-note">Failed expected scopes: none.</p>'
    items = "".join(
        f"<li>{_escape(step_id)} {_escape(scope_type)} {_escape(scope_id)} failed</li>"
        for step_id, scope_type, scope_id in failed
    )
    return (
        '<div class="notice"><p><strong>Failed expected scopes</strong></p>'
        f"<ul>{items}</ul></div>"
    )


def _render_run_identity(summary: Mapping[str, Any]) -> str:
    contract = summary["run_contract"]
    rows = (
        ("Run ID", summary["run_id"]),
        ("Run-summary schema", summary["schema_version"]),
        ("Summary state", summary["summary_state"]),
        ("Generated at", summary["generated_at"]),
        ("Run-contract SHA-256", contract["run_contract_sha256"]),
        ("Sample-manifest SHA-256", contract["sample_manifest_sha256"]),
        ("Reference-contract SHA-256", contract["reference_contract_sha256"]),
        ("Partition-manifest SHA-256", contract["partition_manifest_sha256"]),
        ("Primary analysis ID", contract["primary_analysis_id"]),
        (
            "Primary-analysis-policy SHA-256",
            contract["primary_analysis_policy_sha256"],
        ),
        ("Inventory path", summary["inventory"]["path"]),
        ("Inventory SHA-256", summary["inventory"]["sha256"]),
        ("Artifact receipt path", summary["artifact_receipt"]["path"]),
        ("Artifact receipt SHA-256", summary["artifact_receipt"]["sha256"]),
    )
    return _key_value_table(
        table_id="run-identity",
        caption="Immutable run identity and explicit source records",
        rows=rows,
    )


def _render_report_provenance(metadata: Mapping[str, str]) -> str:
    rows = (
        ("Run-summary input", metadata["run_summary_path"]),
        ("Run-summary input SHA-256", metadata["run_summary_sha256"]),
        (
            "Renderer",
            f"{metadata['renderer']} {metadata['renderer_version']}",
        ),
        ("Quarto executable", metadata["quarto_path"]),
        ("Quarto version", metadata["quarto_version"]),
        ("Quarto executable SHA-256", metadata["quarto_sha256"]),
        ("QMD template", metadata["qmd_template_path"]),
        ("QMD template SHA-256", metadata["qmd_template_sha256"]),
        ("CSS template", metadata["css_template_path"]),
        ("CSS template SHA-256", metadata["css_template_sha256"]),
    )
    return _key_value_table(
        table_id="report-renderer-provenance",
        caption="Static report renderer provenance",
        rows=rows,
    )


def _render_status_panels(summary: Mapping[str, Any]) -> str:
    rollup = summary["computational_rollup"]
    computational_rows = tuple(
        (label, rollup[field]) for label, field in COMPUTATIONAL_STATUS_FIELDS
    )
    review = summary["scientific_review"]
    scientific_rows: list[tuple[str, Any]] = [
        ("Overall science status", summary["science_status"]),
        ("Review record state", review["record_state"]),
    ]
    record = review["record"]
    if record is not None:
        state = record["scientific_state"]
        scientific_rows.extend(
            (
                ("Orientation status", state["orientation_status"]),
                ("Orientation policy", state["orientation_policy"]),
                (
                    "Orientation policy version",
                    state["orientation_policy_version"],
                ),
            )
        )
    else:
        scientific_rows.extend(
            (
                ("Orientation status", "not available"),
                ("Orientation policy", "not available"),
            )
        )
    computational = _key_value_table(
        table_id="computational-status",
        caption="Computational status dimensions",
        rows=computational_rows,
    )
    scientific = _key_value_table(
        table_id="scientific-status",
        caption="Scientific review status dimensions",
        rows=scientific_rows,
    )
    return (
        '<div class="panel-grid">\n'
        '<div class="status-panel"><h3>Computational status</h3>'
        f"{computational}</div>\n"
        '<div class="status-panel"><h3>Scientific status</h3>'
        f"{scientific}</div>\n"
        "</div>\n" + _artifact_overview(summary) + _failed_scope_summary(summary)
    )


def _render_scope_matrix(summary: Mapping[str, Any]) -> str:
    rows = []
    for scope_record in summary["expected_scopes"]:
        scope = scope_record["scope"]
        rows.append(
            (
                scope["step_id"],
                scope["scope_type"],
                scope["scope_id"],
                scope_record["aggregate_state"],
                *(scope_record[field] for _, field in COMPUTATIONAL_STATUS_FIELDS),
                ", ".join(scope_record["artifact_ids"]),
            )
        )
    return _table(
        table_id="expected-scope-matrix",
        caption=(
            "Every expected pipeline and review scope, including explicit "
            "missing, incomplete, failed, or externally unavailable evidence"
        ),
        header=(
            "Step",
            "Scope type",
            "Scope ID",
            "Evidence state",
            "Implementation",
            "Local test",
            "Runtime",
            "Cluster dry-run",
            "Cluster proof",
            "Artifact IDs",
        ),
        rows=rows,
    )


def _render_qc_metrics(summary: Mapping[str, Any]) -> str:
    promoted_ids = {metric["metric_id"] for metric in summary["qc_metrics"]}
    rows = [
        (
            artifact["artifact_id"],
            metric["metric_id"],
            metric["name"],
            metric["value"],
            metric["unit"],
            metric["status"],
            metric["metric_id"] in promoted_ids,
        )
        for artifact in summary["artifacts"]
        for metric in artifact["metrics"]
    ]
    if not rows:
        return _empty(
            "No artifact-level QC metrics are present in the canonical run summary."
        )
    return _table(
        table_id="qc-metrics",
        caption=(
            "Canonical artifact-level QC metrics in stable artifact order; "
            "globally promoted indicates a unique top-level metric ID"
        ),
        header=(
            "Artifact",
            "Metric ID",
            "Name",
            "Value",
            "Unit",
            "Status",
            "Globally promoted",
        ),
        rows=rows,
    )


def _render_attempt_lineage(summary: Mapping[str, Any]) -> str:
    attempts = summary["attempts"]
    if not attempts:
        attempt_table = _empty(
            "No execution-attempt lineage is recorded for this synthetic or "
            "not-attempted run."
        )
    else:
        attempt_table = _table(
            table_id="run-attempt-lineage",
            caption="Immutable run execution-attempt lineage",
            header=(
                "Attempt ID",
                "State",
                "Started",
                "Finished",
                "Exit code",
                "Supersedes",
                "Evidence count",
                "Warnings",
                "Errors",
            ),
            rows=(
                (
                    attempt["attempt_id"],
                    attempt["state"],
                    attempt["started_at"],
                    attempt["finished_at"],
                    attempt["exit_code"],
                    attempt["supersedes_attempt_id"],
                    len(attempt["evidence"]),
                    len(attempt["warnings"]),
                    len(attempt["errors"]),
                )
                for attempt in attempts
            ),
        )
    selections = _table(
        table_id="artifact-attempt-selections",
        caption="Selected and superseded attempt references by artifact",
        header=(
            "Artifact ID",
            "Selected attempt",
            "Attempt provenance",
            "Artifact attempt IDs",
        ),
        rows=(
            (
                artifact["artifact_id"],
                artifact["selected_attempt_id"],
                artifact["attempt_provenance_status"],
                ", ".join(attempt["attempt_id"] for attempt in artifact["attempts"])
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )
    superseded = ", ".join(summary["superseded_attempt_ids"]) or "None"
    return (
        attempt_table
        + "\n"
        + selections
        + f'<p class="provenance-note">Superseded run attempt IDs: '
        f"{_escape(superseded)}.</p>"
    )


def _render_artifact_appendix(summary: Mapping[str, Any]) -> str:
    return _table(
        table_id="artifact-evidence-index",
        caption="Expected artifact evidence and selected source records",
        header=(
            "Artifact ID",
            "Step",
            "Scope type",
            "Scope ID",
            "Required",
            "Availability",
            "Completion",
            "State reason",
            "Source path",
            "Source SHA-256",
            "Warning detail",
            "Error detail",
        ),
        rows=(
            (
                artifact["artifact_id"],
                artifact["scope"]["step_id"],
                artifact["scope"]["scope_type"],
                artifact["scope"]["scope_id"],
                artifact["expectation"]["required"],
                artifact["availability_status"],
                artifact["completion_status"],
                artifact["state_reason"],
                (
                    artifact["source"]["path"]
                    if artifact["source"] is not None
                    else "Not available"
                ),
                (
                    artifact["source"]["sha256"]
                    if artifact["source"] is not None
                    else "Not available"
                ),
                "; ".join(
                    f"{issue['code']}: {issue['message']}"
                    for issue in artifact["warnings"]
                )
                or "None",
                "; ".join(
                    f"{issue['code']}: {issue['message']}"
                    for issue in artifact["errors"]
                )
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )


def _render_tools(summary: Mapping[str, Any]) -> str:
    if not summary["tools"]:
        return _empty("No aggregate software records are declared.")
    return _table(
        table_id="software-provenance",
        caption="Aggregate software provenance",
        header=("Tool", "Version", "Role", "Path", "SHA-256"),
        rows=(
            (
                tool["name"],
                tool["version"],
                tool["role"],
                tool["path"],
                tool["sha256"],
            )
            for tool in summary["tools"]
        ),
    )


def _render_issues(summary: Mapping[str, Any]) -> str:
    rows = [
        (
            level[:-1],
            issue["code"],
            issue["message"],
            ", ".join(issue["related_artifact_ids"]) or "None declared",
            ", ".join(reference["evidence_id"] for reference in issue["evidence"])
            or "None declared",
        )
        for level in ("warnings", "errors")
        for issue in summary[level]
    ]
    if not rows:
        return _empty("No aggregate run-summary warnings or errors are recorded.")
    return _table(
        table_id="run-summary-issues",
        caption="Aggregate warnings and errors",
        header=("Level", "Code", "Message", "Artifact IDs", "Evidence IDs"),
        rows=rows,
    )


def _render_table_inventory(tables: Sequence[ApprovedTable]) -> str:
    if not tables:
        return _empty(
            "No full report tables were explicitly approved. The renderer did "
            "not discover or open any native pipeline output."
        )
    return _table(
        table_id="approved-table-inventory",
        caption="Explicit report-table approvals and display policy",
        header=(
            "Table ID",
            "Role",
            "Artifact ID",
            "Path",
            "SHA-256",
            "Full rows",
            "Displayed rows",
            "Truncated",
            "Approval policy",
            "Approved by",
            "Approved at",
        ),
        rows=(
            (
                table.table_id,
                table.role,
                table.artifact_id,
                table.path,
                table.sha256,
                table.row_count,
                table.displayed_row_count,
                table.truncated,
                table.approval_policy_version,
                table.approved_by,
                table.approved_at,
            )
            for table in tables
        ),
    )
