"""Computational-only view projection for the static Jinja report."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .models import (
    BOUNDARY_BANNER,
    CANDIDATE_TERMINOLOGY,
    COMPUTATIONAL_STATUS_FIELDS,
    ComputationalResults,
    ComputationalTable,
)


def _display(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _table(
    table_id: str,
    caption: str,
    header: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    row_headers: bool = False,
) -> dict[str, Any]:
    materialized = [tuple(_display(value) for value in row) for row in rows]
    return {
        "kind": "table",
        "id": table_id,
        "caption": caption,
        "header": tuple(header),
        "rows": materialized,
        "row_headers": row_headers,
        "wide": len(header) > 6,
    }


def _key_value_table(
    table_id: str,
    caption: str,
    rows: Iterable[tuple[str, Any]],
) -> dict[str, Any]:
    return _table(
        table_id,
        caption,
        ("Field", "Value"),
        rows,
        row_headers=True,
    )


def _empty(message: str) -> dict[str, Any]:
    return {"kind": "empty", "message": message}


def _note(message: str, *, notice: bool = False) -> dict[str, Any]:
    return {"kind": "note", "message": message, "notice": notice}


_COMPUTATIONAL_RESULT_COLUMNS = (
    "candidate_id",
    "partition_id",
    "orientation",
    "chromosome",
    "position",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "gene_ids",
    "test_status",
    "call_status",
    "min_analysis_dp",
    "mean_analysis_dp",
    "mean_control_af",
    "mean_treatment_af",
    "treatment_control_difference",
    "cmh_p_value",
    "cmh_fdr_bh",
    "common_odds_ratio",
)


def _computational_source_note(table: ComputationalTable) -> dict[str, Any]:
    qualifier = (
        f"Displayed {table.displayed_row_count} of {table.row_count} rows."
        if table.truncated
        else f"Displayed all {table.row_count} rows."
    )
    return _note(
        f"{qualifier} Exact completed artifact: {table.path}. SHA-256: "
        f"{table.sha256}. Size: {table.size_bytes} bytes.",
        notice=table.truncated,
    )


def _computational_result_table(table: ComputationalTable) -> dict[str, Any]:
    columns = (
        *_COMPUTATIONAL_RESULT_COLUMNS,
        *(column for column in table.header if column.startswith("DP__")),
        *(column for column in table.header if column.startswith("AD__")),
        *(column for column in table.header if column.startswith("AF__")),
    )
    indices = tuple(table.header.index(column) for column in columns)
    return _table(
        table.table_id,
        table.title,
        columns,
        (tuple(row[index] for index in indices) for row in table.display_rows),
    )


def _computational_result_blocks(
    results: ComputationalResults | None,
    unavailable_reason: str | None,
) -> list[dict[str, Any]]:
    boundary = _note(
        "COMPUTATIONAL RESULTS — NOT SCIENTIFICALLY ADJUDICATED. "
        "Threshold-passing rows are CMH-ranked candidates, not validated "
        "RNA-editing sites or biological conclusions.",
        notice=True,
    )
    if results is None:
        return [
            boundary,
            _empty(
                unavailable_reason
                or (
                    "The exact complete primary-analysis Step 09 result trio is "
                    "not available. No computational candidate row was inferred."
                )
            ),
        ]
    summary_table = results.summary
    summary = dict(
        zip(summary_table.header, summary_table.display_rows[0], strict=True)
    )
    summary_fields = (
        ("Analysis ID", "analysis_id"),
        ("Control condition", "control_condition"),
        ("Treatment condition", "treatment_condition"),
        ("Target RNA change", "target_rna_change"),
        ("Replicate count", "replicate_count"),
        ("Sample count", "sample_count"),
        ("All candidate rows", "candidate_count"),
        ("Target-change rows", "target_candidate_count"),
        ("Successfully tested rows", "successfully_tested_count"),
        ("Significant-up rows", "significant_up_count"),
        ("Significant-down rows", "significant_down_count"),
        ("Minimum sample DP", "min_sample_dp"),
        ("Mean DP threshold", "mean_dp_threshold"),
        ("FDR threshold", "fdr_threshold"),
        ("Common OR threshold", "common_or_threshold"),
        ("Absolute AF-difference threshold", "absolute_difference_threshold"),
        ("Background maximum fraction", "background_max_fraction"),
        ("Multiple-testing method", "multiple_testing_method"),
        ("CMH alternative", "cmh_alternative"),
        ("Continuity correction", "continuity_correction"),
        ("Orientation policy", "orientation_policy"),
    )
    return [
        boundary,
        _key_value_table(
            "computational-analysis-summary",
            "Step 09 counts, design, and declared thresholds",
            ((label, summary[field]) for label, field in summary_fields),
        ),
        _computational_source_note(summary_table),
        _computational_result_table(results.significant_sites),
        _computational_source_note(results.significant_sites),
        _computational_result_table(results.all_sites),
        _computational_source_note(results.all_sites),
    ]


_KEY_QC_METRICS = (
    ("Input reads", "number_of_input_reads"),
    ("Mapped reads", "mapped_reads"),
    ("Unique mapped reads", "uniquely_mapped_reads_number"),
    ("Unique mapping (%)", "uniquely_mapped_reads"),
    ("Read pairs examined", "read_pairs_examined"),
    ("Duplicate pairs", "read_pair_duplicates"),
    ("Duplicate fraction", "percent_duplication"),
    ("Estimated library size", "estimated_library_size"),
)


def _key_qc(summary: Mapping[str, Any]) -> dict[str, Any]:
    values: dict[str, dict[str, Any]] = defaultdict(dict)
    sample_order: list[str] = []
    ambiguous: set[tuple[str, str]] = set()
    for artifact in summary["artifacts"]:
        scope = artifact["scope"]
        if scope["scope_type"] != "sample":
            continue
        sample_id = scope["scope_id"]
        if sample_id not in sample_order:
            sample_order.append(sample_id)
        if not (
            artifact["availability_status"] == "present"
            and artifact["completion_status"] == "complete"
        ):
            continue
        for metric in artifact["metrics"]:
            metric_id = metric["metric_id"]
            key = sample_id, metric_id
            if key in ambiguous:
                continue
            if metric_id in values[sample_id]:
                values[sample_id].pop(metric_id, None)
                ambiguous.add(key)
                continue
            values[sample_id][metric_id] = metric["value"]
    if not sample_order:
        return _empty(
            "No sample-level QC metrics are available in the canonical run summary."
        )
    return _table(
        "key-sample-qc",
        "Selected exact sample-level metrics; missing or ambiguous values are not inferred",
        ("Sample", *(label for label, _ in _KEY_QC_METRICS)),
        (
            (
                sample_id,
                *(values[sample_id].get(metric_id) for _, metric_id in _KEY_QC_METRICS),
            )
            for sample_id in sample_order
        ),
    )


def _artifact_overview(summary: Mapping[str, Any]) -> dict[str, Any]:
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
    cursor = 0.0
    segments = []
    legend = []
    for name, count, color in categories:
        segment_width = width * count / total if total else 0
        if count:
            segments.append(
                {
                    "x": f"{cursor:.3f}",
                    "width": f"{segment_width:.3f}",
                    "color": color,
                    "name": name,
                    "count": count,
                }
            )
        legend.append({"name": name, "count": count})
        cursor += segment_width
    return {
        "kind": "artifact_overview",
        "width": width,
        "height": 82,
        "total": total,
        "segments": segments,
        "legend": legend,
        "description": ", ".join(f"{name}: {count}" for name, count, _ in categories),
    }


def _status_blocks(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    rollup = summary["computational_rollup"]
    failed = [
        item["scope"]
        for item in summary["expected_scopes"]
        if item["aggregate_state"] == "failed"
    ]
    failed_block = (
        {
            "kind": "notice_list",
            "title": "Failed expected scopes",
            "items": [
                f"{scope['step_id']} {scope['scope_type']} {scope['scope_id']} failed"
                for scope in failed
            ],
        }
        if failed
        else _note("Failed expected scopes: none.")
    )
    return [
        {
            "kind": "panel_grid",
            "panels": (
                {
                    "title": "Computational status",
                    "block": _key_value_table(
                        "computational-status",
                        "Computational status dimensions",
                        (
                            (label, rollup[field])
                            for label, field in COMPUTATIONAL_STATUS_FIELDS
                        ),
                    ),
                },
                {
                    "title": "Interpretation boundary",
                    "block": _key_value_table(
                        "interpretation-boundary",
                        "Fixed NORAD output boundary",
                        (
                            ("Boundary", summary["interpretation_boundary"]),
                            ("Candidate terminology", summary["candidate_terminology"]),
                            ("Biological validation", "outside NORAD"),
                        ),
                    ),
                },
            ),
        },
        _artifact_overview(summary),
        failed_block,
    ]


def _run_identity(summary: Mapping[str, Any]) -> dict[str, Any]:
    contract = summary["run_contract"]
    return _key_value_table(
        "run-identity",
        "Immutable run identity and explicit source records",
        (
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
        ),
    )


def _scope_matrix(summary: Mapping[str, Any]) -> dict[str, Any]:
    return _table(
        "expected-scope-matrix",
        "Every expected computational scope, including explicit incomplete states",
        (
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
        (
            (
                item["scope"]["step_id"],
                item["scope"]["scope_type"],
                item["scope"]["scope_id"],
                item["aggregate_state"],
                *(item[field] for _, field in COMPUTATIONAL_STATUS_FIELDS),
                ", ".join(item["artifact_ids"]),
            )
            for item in summary["expected_scopes"]
        ),
    )


def _qc_metrics(summary: Mapping[str, Any]) -> dict[str, Any]:
    promoted = {metric["metric_id"] for metric in summary["qc_metrics"]}
    rows = [
        (
            artifact["artifact_id"],
            metric["metric_id"],
            metric["name"],
            metric["value"],
            metric["unit"],
            metric["status"],
            metric["metric_id"] in promoted,
        )
        for artifact in summary["artifacts"]
        for metric in artifact["metrics"]
    ]
    if not rows:
        return _empty("No artifact-level QC metrics are present.")
    return _table(
        "qc-metrics",
        "Canonical artifact-level QC metrics in stable artifact order",
        (
            "Artifact",
            "Metric ID",
            "Name",
            "Value",
            "Unit",
            "Status",
            "Globally promoted",
        ),
        rows,
    )


def _limitations(summary: Mapping[str, Any]) -> dict[str, Any]:
    limitations = summary["limitations"]
    if not limitations:
        return _empty("No computational limitations are recorded in the run summary.")
    return _table(
        "limitations",
        "Recorded computational limitations and their impact",
        ("Limitation", "Status", "Description", "Impact", "Evidence IDs"),
        (
            (
                item["limitation_id"],
                item["status"],
                item["description"],
                item["impact"],
                ", ".join(item["evidence_ids"]) or "None declared",
            )
            for item in limitations
        ),
    )


def _attempt_lineage(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    attempts = summary["attempts"]
    attempt_block = (
        _table(
            "run-attempt-lineage",
            "Immutable run execution-attempt lineage",
            (
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
            (
                (
                    item["attempt_id"],
                    item["state"],
                    item["started_at"],
                    item["finished_at"],
                    item["exit_code"],
                    item["supersedes_attempt_id"],
                    len(item["evidence"]),
                    len(item["warnings"]),
                    len(item["errors"]),
                )
                for item in attempts
            ),
        )
        if attempts
        else _empty("No execution-attempt lineage is recorded.")
    )
    selections = _table(
        "artifact-attempt-selections",
        "Selected and superseded attempt references by artifact",
        (
            "Artifact ID",
            "Selected attempt",
            "Attempt provenance",
            "Artifact attempt IDs",
        ),
        (
            (
                artifact["artifact_id"],
                artifact["selected_attempt_id"],
                artifact["attempt_provenance_status"],
                ", ".join(item["attempt_id"] for item in artifact["attempts"])
                or "None",
            )
            for artifact in summary["artifacts"]
        ),
    )
    return [
        attempt_block,
        selections,
        _note(
            "Superseded run attempt IDs: "
            + (", ".join(summary["superseded_attempt_ids"]) or "None")
            + "."
        ),
    ]


def _artifact_appendix(summary: Mapping[str, Any]) -> dict[str, Any]:
    return _table(
        "artifact-evidence-index",
        "Expected artifact evidence and selected source records",
        (
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
        (
            (
                artifact["artifact_id"],
                artifact["scope"]["step_id"],
                artifact["scope"]["scope_type"],
                artifact["scope"]["scope_id"],
                artifact["expectation"]["required"],
                artifact["availability_status"],
                artifact["completion_status"],
                artifact["state_reason"],
                artifact["source"]["path"] if artifact["source"] else None,
                artifact["source"]["sha256"] if artifact["source"] else None,
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


def _tools_and_issues(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    tools = (
        _table(
            "software-provenance",
            "Aggregate software provenance",
            ("Tool", "Version", "Role", "Path", "SHA-256"),
            (
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
        if summary["tools"]
        else _empty("No aggregate software records are declared.")
    )
    issue_rows = [
        (
            level[:-1],
            issue["code"],
            issue["message"],
            ", ".join(issue["related_artifact_ids"]) or "None declared",
            ", ".join(item["evidence_id"] for item in issue["evidence"])
            or "None declared",
        )
        for level in ("warnings", "errors")
        for issue in summary[level]
    ]
    issues = (
        _table(
            "run-summary-issues",
            "Aggregate warnings and errors",
            ("Level", "Code", "Message", "Artifact IDs", "Evidence IDs"),
            issue_rows,
        )
        if issue_rows
        else _empty("No aggregate run-summary warnings or errors are recorded.")
    )
    return [tools, issues]


def _report_provenance(metadata: Mapping[str, str]) -> dict[str, Any]:
    return _key_value_table(
        "report-renderer-provenance",
        "Static report renderer provenance",
        (
            ("Run-summary input", metadata["run_summary_path"]),
            ("Run-summary input SHA-256", metadata["run_summary_sha256"]),
            ("Renderer", f"{metadata['renderer']} {metadata['renderer_version']}"),
            ("Jinja2 version", metadata["jinja_version"]),
            ("HTML template", metadata["template_path"]),
            ("HTML template SHA-256", metadata["template_sha256"]),
            ("CSS resource", metadata["css_path"]),
            ("CSS resource SHA-256", metadata["css_sha256"]),
        ),
    )


def build_view(
    summary: Mapping[str, Any],
    metadata: Mapping[str, str],
    *,
    computational_results: ComputationalResults | None = None,
    computational_unavailable_reason: str | None = None,
) -> dict[str, Any]:
    """Build the complete deterministic computational report view."""

    return {
        "run_id": summary["run_id"],
        "candidate_terminology": CANDIDATE_TERMINOLOGY,
        "interpretation_boundary": summary["interpretation_boundary"],
        "boundary_class": "computational-boundary",
        "banner": BOUNDARY_BANNER,
        "metadata": dict(metadata),
        "categories": (
            {
                "id": "computational-category",
                "title": "Computational results",
                "open": True,
                "sections": (
                    {
                        "id": "computational-results-section",
                        "title": "Step 09 computational candidates",
                        "blocks": _computational_result_blocks(
                            computational_results,
                            computational_unavailable_reason,
                        ),
                    },
                    {
                        "id": "key-qc-section",
                        "title": "Key sample QC",
                        "blocks": (_key_qc(summary),),
                    },
                ),
            },
            {
                "id": "overview-category",
                "title": "Run overview",
                "open": False,
                "sections": (
                    {
                        "id": "run-identity-section",
                        "title": "Run identity",
                        "blocks": (_run_identity(summary),),
                    },
                    {
                        "id": "status-section",
                        "title": "Computational status",
                        "blocks": tuple(_status_blocks(summary)),
                    },
                    {
                        "id": "limitations-section",
                        "title": "Computational limitations",
                        "blocks": (_limitations(summary),),
                    },
                    {
                        "id": "scope-matrix-section",
                        "title": "Expected computational scopes",
                        "blocks": (_scope_matrix(summary),),
                    },
                ),
            },
            {
                "id": "evidence-category",
                "title": "QC and evidence",
                "open": False,
                "sections": (
                    {
                        "id": "qc-metrics-section",
                        "title": "QC metrics",
                        "blocks": (_qc_metrics(summary),),
                    },
                    {
                        "id": "attempt-lineage-section",
                        "title": "Attempt lineage",
                        "blocks": tuple(_attempt_lineage(summary)),
                    },
                    {
                        "id": "artifact-appendix-section",
                        "title": "Artifact appendix",
                        "blocks": (_artifact_appendix(summary),),
                    },
                ),
            },
            {
                "id": "provenance-category",
                "title": "Provenance",
                "open": False,
                "sections": (
                    {
                        "id": "tools-issues-section",
                        "title": "Tools and issues",
                        "blocks": tuple(_tools_and_issues(summary)),
                    },
                    {
                        "id": "report-provenance-section",
                        "title": "Report provenance",
                        "blocks": (_report_provenance(metadata),),
                    },
                ),
            },
        ),
    }
