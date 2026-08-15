"""Structured view-data projection for the static Jinja report template."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .models import (
    CANDIDATE_TERMINOLOGY,
    COMPUTATIONAL_STATUS_FIELDS,
    KNOWN_REPORT_ROLES,
    SCIENCE_BANNERS,
    ApprovedTable,
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


def _json_block(title: str, value: Any) -> dict[str, Any]:
    return {
        "kind": "json",
        "title": title,
        "payload": json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ),
    }


def _approved_table_blocks(table: ApprovedTable) -> list[dict[str, Any]]:
    controlled_titles = {
        "candidate_selection": "CMH-ranked candidates: approved selection summary",
        "candidate_adjudication": (
            "CMH-ranked candidates: approved adjudication summary"
        ),
    }
    blocks = [
        _table(
            f"approved-table-{table.table_id}",
            controlled_titles.get(table.role, table.title),
            table.header,
            table.display_rows,
        )
    ]
    if table.truncated:
        message = (
            f"Displayed {table.displayed_row_count} of {table.row_count} rows. "
            f"Full table: {table.path}. SHA-256: {table.sha256}. Approved by "
            f"{table.approved_by} under {table.approval_policy_version} at "
            f"{table.approved_at}."
        )
        blocks.append(_note(message, notice=True))
    else:
        message = (
            f"Explicit approved table: {table.path}. SHA-256: {table.sha256}. "
            f"Rows: {table.row_count}. Approved by {table.approved_by} under "
            f"{table.approval_policy_version} at {table.approved_at}."
        )
        blocks.append(_note(message))
    return blocks


def _tables_for_roles(
    tables_by_role: Mapping[str, Sequence[ApprovedTable]],
    roles: Sequence[str],
    empty_message: str,
) -> list[dict[str, Any]]:
    selected = [table for role in roles for table in tables_by_role.get(role, ())]
    if not selected:
        return [_empty(empty_message)]
    return [block for table in selected for block in _approved_table_blocks(table)]


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


def _key_qc(summary: Mapping[str, Any]) -> dict[str, Any]:
    adapters = {
        "step01_star_log_final_v1",
        "step02b_flagstat_v1",
        "step03_rseqc_infer_v1",
        "step04_markdup_metrics_v1",
    }
    by_sample: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    ambiguous: set[tuple[str, str]] = set()
    seen: set[tuple[str, str]] = set()
    sample_order: list[str] = []
    for artifact in summary["artifacts"]:
        adapter = artifact["adapter"]
        scope = artifact["scope"]
        if adapter not in adapters or scope["scope_type"] != "sample":
            continue
        sample_id = scope["scope_id"]
        if sample_id not in sample_order:
            sample_order.append(sample_id)
        key = (sample_id, adapter)
        if key in seen:
            ambiguous.add(key)
            by_sample[sample_id].pop(adapter, None)
            continue
        seen.add(key)
        if not (
            artifact["availability_status"] == "present"
            and artifact["completion_status"] == "complete"
        ):
            continue
        metric_ids = [metric["metric_id"] for metric in artifact["metrics"]]
        if len(metric_ids) != len(set(metric_ids)):
            ambiguous.add(key)
            continue
        by_sample[sample_id][adapter] = {
            metric["metric_id"]: metric["value"] for metric in artifact["metrics"]
        }
    for sample_id, adapter in ambiguous:
        by_sample[sample_id].pop(adapter, None)

    def metric(sample_id: str, adapter: str, metric_id: str) -> Any:
        return by_sample.get(sample_id, {}).get(adapter, {}).get(metric_id)

    if not sample_order:
        return _empty(
            "No complete sample-level STAR, flagstat, RSeQC, or Picard metrics "
            "are available in the canonical run summary."
        )
    return _table(
        "key-sample-qc",
        (
            "Selected exact artifact metrics copied from the canonical run "
            "summary; missing or ambiguous values are not inferred"
        ),
        (
            "Sample",
            "Input reads",
            "Mapped reads",
            "Unique mapped reads",
            "Unique mapping (%)",
            "Orientation fraction A",
            "Orientation fraction B",
            "Undetermined fraction",
            "Read pairs examined",
            "Duplicate pairs",
            "Duplicate fraction",
            "Estimated library size",
        ),
        (
            (
                sample_id,
                metric(sample_id, "step01_star_log_final_v1", "number_of_input_reads"),
                metric(sample_id, "step02b_flagstat_v1", "mapped_reads"),
                metric(
                    sample_id,
                    "step01_star_log_final_v1",
                    "uniquely_mapped_reads_number",
                ),
                metric(
                    sample_id,
                    "step01_star_log_final_v1",
                    "uniquely_mapped_reads",
                ),
                metric(
                    sample_id,
                    "step03_rseqc_infer_v1",
                    "fraction_explained_by__1_-_1-__2___2--",
                ),
                metric(
                    sample_id,
                    "step03_rseqc_infer_v1",
                    "fraction_explained_by__1___1--_2_-_2-",
                ),
                metric(
                    sample_id,
                    "step03_rseqc_infer_v1",
                    "fraction_failed_to_determine",
                ),
                metric(
                    sample_id,
                    "step04_markdup_metrics_v1",
                    "read_pairs_examined",
                ),
                metric(
                    sample_id,
                    "step04_markdup_metrics_v1",
                    "read_pair_duplicates",
                ),
                metric(
                    sample_id,
                    "step04_markdup_metrics_v1",
                    "percent_duplication",
                ),
                metric(
                    sample_id,
                    "step04_markdup_metrics_v1",
                    "estimated_library_size",
                ),
            )
            for sample_id in sample_order
        ),
    )


def _scientific_record(summary: Mapping[str, Any]) -> Mapping[str, Any] | None:
    record = summary["scientific_review"]["record"]
    return record if isinstance(record, Mapping) else None


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
    review = summary["scientific_review"]
    computational = _key_value_table(
        "computational-status",
        "Computational status dimensions",
        ((label, rollup[field]) for label, field in COMPUTATIONAL_STATUS_FIELDS),
    )
    scientific_rows: list[tuple[str, Any]] = [
        ("Overall science status", summary["science_status"]),
        ("Review record state", review["record_state"]),
    ]
    record = review["record"]
    if record is None:
        scientific_rows.extend(
            (
                ("Orientation status", "not available"),
                ("Orientation policy", "not available"),
            )
        )
    else:
        state = record["scientific_state"]
        scientific_rows.extend(
            (
                ("Orientation status", state["orientation_status"]),
                ("Orientation policy", state["orientation_policy"]),
                ("Orientation policy version", state["orientation_policy_version"]),
            )
        )
    scientific = _key_value_table(
        "scientific-status",
        "Scientific review status dimensions",
        scientific_rows,
    )
    failed = [
        (
            item["scope"]["step_id"],
            item["scope"]["scope_type"],
            item["scope"]["scope_id"],
        )
        for item in summary["expected_scopes"]
        if item["aggregate_state"] == "failed"
    ]
    failed_block: dict[str, Any]
    if failed:
        failed_block = {
            "kind": "notice_list",
            "title": "Failed expected scopes",
            "items": [
                f"{step} {scope_type} {scope_id} failed"
                for step, scope_type, scope_id in failed
            ],
        }
    else:
        failed_block = _note("Failed expected scopes: none.")
    return [
        {
            "kind": "panel_grid",
            "panels": (
                {"title": "Computational status", "block": computational},
                {"title": "Scientific status", "block": scientific},
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
        (
            "Every expected pipeline and review scope, including explicit "
            "missing, incomplete, failed, or externally unavailable evidence"
        ),
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
        return _empty(
            "No artifact-level QC metrics are present in the canonical run summary."
        )
    return _table(
        "qc-metrics",
        (
            "Canonical artifact-level QC metrics in stable artifact order; "
            "globally promoted indicates a unique top-level metric ID"
        ),
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


def _evidence_categories(summary: Mapping[str, Any]) -> dict[str, Any]:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "No normalized scientific-review record is present. Orientation, "
            "annotation, funnel, replicate, sensitivity, and adjudication "
            "evidence remain unavailable."
        )
    return _table(
        "science-evidence-categories",
        "Scientific evidence-category completeness",
        ("Category", "Status", "Evidence IDs", "Not-applicable reason"),
        (
            (
                category,
                value["status"],
                ", ".join(value["evidence_ids"]) or "None declared",
                value["not_applicable_reason"],
            )
            for category, value in record["evidence_categories"].items()
        ),
    )


def _limitations(summary: Mapping[str, Any]) -> dict[str, Any]:
    limitations = summary["limitations"]
    if not limitations:
        return _empty("No limitations are recorded in the canonical run summary.")
    return _table(
        "limitations",
        "Recorded limitations and their interpretation impact",
        (
            "Limitation",
            "Status",
            "Category",
            "Severity",
            "Description",
            "Impact",
            "Mitigation",
            "Owner",
            "Review date",
            "Evidence IDs",
        ),
        (
            (
                item["limitation_id"],
                item["status"],
                item.get("category"),
                item.get("severity"),
                item["description"],
                item["impact"],
                item.get("mitigation"),
                item.get("owner"),
                item.get("review_date"),
                ", ".join(item["evidence_ids"]) or "None declared",
            )
            for item in limitations
        ),
    )


def _decisions(summary: Mapping[str, Any]) -> dict[str, Any]:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "Background, matched-DNA, orthogonal-evidence, annotation, "
            "threshold, and adjudication decisions are unavailable because "
            "no scientific-review record is present."
        )
    return _table(
        "science-decisions",
        "Explicit scientific-review decision dimensions",
        (
            "Dimension",
            "Status",
            "Value",
            "Detail",
            "Reviewer",
            "Decision date",
            "Evidence IDs",
            "Rerun required",
            "Rerun scope",
        ),
        (
            (
                dimension,
                decision["status"],
                decision["value"],
                decision["detail"],
                decision["reviewer"],
                decision["decision_date"],
                ", ".join(decision["evidence_ids"]) or "None declared",
                decision.get("rerun_required"),
                decision["rerun_scope"],
            )
            for dimension, decision in record["decisions"].items()
        ),
    )


def _rerun_implications(summary: Mapping[str, Any]) -> dict[str, Any]:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "No review decisions are available from which to report explicit "
            "rerun implications. This report does not infer them."
        )
    return _table(
        "rerun-implications",
        (
            "Recorded rerun scopes copied from review decisions; no rerun is "
            "scheduled or executed by this report"
        ),
        ("Decision dimension", "Status", "Rerun required", "Rerun scope", "Detail"),
        (
            (
                dimension,
                decision["status"],
                decision.get("rerun_required"),
                decision["rerun_scope"],
                decision["detail"],
            )
            for dimension, decision in record["decisions"].items()
        ),
    )


def _evidence_index(summary: Mapping[str, Any]) -> dict[str, Any]:
    record = _scientific_record(summary)
    if record is None or not record["evidence_records"]:
        return _empty(
            "No scientific evidence index is present in the canonical run summary."
        )
    return _table(
        "science-evidence-index",
        "Explicit scientific evidence records",
        (
            "Evidence ID",
            "Category",
            "Analysis ID",
            "Status",
            "Path",
            "SHA-256",
            "Reviewer",
            "Owner",
            "Evidence date",
            "Policy version",
        ),
        (
            (
                evidence["evidence_id"],
                evidence["category"],
                evidence["analysis_id"],
                evidence["status"],
                evidence["source"]["path"] if evidence["source"] else None,
                evidence["source"]["sha256"] if evidence["source"] else None,
                evidence["reviewer"],
                evidence["owner"],
                evidence["evidence_date"],
                evidence["policy_version"],
            )
            for evidence in record["evidence_records"]
        ),
    )


def _input_artifacts(summary: Mapping[str, Any]) -> dict[str, Any]:
    record = _scientific_record(summary)
    if record is None:
        return _empty("No scientific-review input-artifact list is present.")
    return _table(
        "science-input-artifacts",
        "Scientific-review input artifacts",
        ("Role", "Artifact ID", "Path", "SHA-256", "Rows"),
        (
            (
                item["role"],
                item["artifact_id"],
                item["path"],
                item["sha256"],
                item["row_count"],
            )
            for item in record["input_artifacts"]
        ),
    )


def _science_methods(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    record = _scientific_record(summary)
    if record is None:
        return [
            _empty(
                "Scientific-review metadata, policies, selection rules, and "
                "computational evidence are unavailable because no normalized "
                "review record is present."
            )
        ]
    computational = record["computational_status"]
    evidence = computational["evidence"]
    evidence_block = (
        _table(
            "science-computational-evidence",
            "Computational evidence references declared by the review",
            ("Evidence ID", "Role", "Path", "SHA-256"),
            (
                (item["evidence_id"], item["role"], item["path"], item["sha256"])
                for item in evidence
            ),
        )
        if evidence
        else _empty(
            "The scientific-review record declares no computational evidence "
            "references."
        )
    )
    return [
        _key_value_table(
            "science-review-metadata",
            "Scientific-review metadata",
            record["review_metadata"].items(),
        ),
        _key_value_table(
            "science-policy-versions",
            "Scientific-review policy versions",
            record["policy_versions"].items(),
        ),
        _key_value_table(
            "science-selection-rules",
            "Preregistered selection and sensitivity rules",
            record["selection_rules"].items(),
        ),
        _key_value_table(
            "science-computational-status",
            "Computational status declared by the scientific review",
            (
                (label, computational[field])
                for label, field in COMPUTATIONAL_STATUS_FIELDS
            ),
        ),
        evidence_block,
    ]


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
        else _empty(
            "No execution-attempt lineage is recorded for this synthetic or "
            "not-attempted run."
        )
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
    superseded = ", ".join(summary["superseded_attempt_ids"]) or "None"
    return [
        attempt_block,
        selections,
        _note(f"Superseded run attempt IDs: {superseded}."),
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


def _table_inventory(tables: Sequence[ApprovedTable]) -> dict[str, Any]:
    if not tables:
        return _empty(
            "No full report tables were explicitly approved. The renderer did "
            "not discover or open any native pipeline output."
        )
    return _table(
        "approved-table-inventory",
        "Explicit report-table approvals and display policy",
        (
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
        (
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


def _tools(summary: Mapping[str, Any]) -> dict[str, Any]:
    if not summary["tools"]:
        return _empty("No aggregate software records are declared.")
    return _table(
        "software-provenance",
        "Aggregate software provenance",
        ("Tool", "Version", "Role", "Path", "SHA-256"),
        (
            (tool["name"], tool["version"], tool["role"], tool["path"], tool["sha256"])
            for tool in summary["tools"]
        ),
    )


def _issues(summary: Mapping[str, Any]) -> dict[str, Any]:
    rows = [
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
    if not rows:
        return _empty("No aggregate run-summary warnings or errors are recorded.")
    return _table(
        "run-summary-issues",
        "Aggregate warnings and errors",
        ("Level", "Code", "Message", "Artifact IDs", "Evidence IDs"),
        rows,
    )


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
    tables: Sequence[ApprovedTable],
    metadata: Mapping[str, str],
    *,
    computational_results: ComputationalResults | None = None,
    computational_unavailable_reason: str | None = None,
) -> dict[str, Any]:
    """Build deterministic data only; the Jinja template owns all markup."""

    tables_by_role: dict[str, list[ApprovedTable]] = defaultdict(list)
    for table in tables:
        tables_by_role[table.role].append(table)

    evidence_blocks = [
        _evidence_index(summary),
        *_tables_for_roles(
            tables_by_role,
            ("evidence_index",),
            "No separate evidence-index table was explicitly approved.",
        ),
        _input_artifacts(summary),
        *_science_methods(summary),
        *_attempt_lineage(summary),
        _artifact_appendix(summary),
        _table_inventory(tables),
        _tools(summary),
        _issues(summary),
        _json_block("Run-summary parameters", summary["parameters"]),
        _json_block("Run-summary provenance", summary["provenance"]),
        _report_provenance(metadata),
    ]
    unknown = [table for table in tables if table.role not in KNOWN_REPORT_ROLES]
    evidence_sections = [
        {
            "id": "run-identity-section",
            "title": "Run identity, inputs, hashes, and provenance",
            "blocks": [_run_identity(summary)],
        },
        {
            "id": "scope-matrix-section",
            "title": "Expected-step and missing-evidence matrix",
            "blocks": [_scope_matrix(summary)],
        },
        {
            "id": "evidence-methods-section",
            "title": "Evidence index and methods appendix",
            "blocks": evidence_blocks,
        },
    ]
    if unknown:
        evidence_sections.append(
            {
                "id": "other-approved-tables-section",
                "title": "Other explicitly approved report tables",
                "blocks": [
                    block
                    for table in unknown
                    for block in _approved_table_blocks(table)
                ],
            }
        )

    return {
        "run_id": summary["run_id"],
        "science_status": summary["science_status"],
        "science_class": summary["science_status"].replace("_", "-"),
        "banner": SCIENCE_BANNERS[summary["science_status"]],
        "candidate_terminology": CANDIDATE_TERMINOLOGY,
        "metadata": dict(metadata),
        "categories": (
            {
                "id": "computational-results-category",
                "title": "Computational results",
                "open": True,
                "sections": (
                    {
                        "id": "computational-results-section",
                        "title": (
                            "Computational results — not scientifically adjudicated"
                        ),
                        "blocks": _computational_result_blocks(
                            computational_results,
                            computational_unavailable_reason,
                        ),
                    },
                    {
                        "id": "key-qc-section",
                        "title": "Key per-sample QC",
                        "blocks": [_key_qc(summary)],
                    },
                ),
            },
            {
                "id": "overview-category",
                "title": "Overview",
                "open": False,
                "sections": (
                    {
                        "id": "status-section",
                        "title": "Computational and scientific status",
                        "blocks": _status_blocks(summary),
                    },
                    {
                        "id": "limitations-section",
                        "title": "Limitations and interpretation boundary",
                        "blocks": [
                            _limitations(summary),
                            *_tables_for_roles(
                                tables_by_role,
                                ("limitations",),
                                "No separate limitations table was explicitly approved.",
                            ),
                        ],
                    },
                ),
            },
            {
                "id": "qc-category",
                "title": "QC and orientation",
                "open": False,
                "sections": (
                    {
                        "id": "qc-orientation-section",
                        "title": (
                            "QC, orientation, annotation, and Step 07 to Step 09 funnel"
                        ),
                        "blocks": [
                            _qc_metrics(summary),
                            _evidence_categories(summary),
                            *_tables_for_roles(
                                tables_by_role,
                                (
                                    "orientation_locus_audit",
                                    "annotation_audit",
                                    "qc_funnel",
                                ),
                                (
                                    "No orientation-locus, annotation-audit, or "
                                    "QC-funnel table was explicitly approved. Statuses "
                                    "remain visible above; row content was not discovered."
                                ),
                            ),
                        ],
                    },
                ),
            },
            {
                "id": "replicate-category",
                "title": "Replicates and sensitivity",
                "open": False,
                "sections": (
                    {
                        "id": "replicate-sensitivity-section",
                        "title": "Replicate, sensitivity, and leave-one-pair-out summaries",
                        "blocks": _tables_for_roles(
                            tables_by_role,
                            (
                                "replicate_effects",
                                "sensitivity_matrix",
                                "leave_one_pair_out",
                            ),
                            (
                                "No replicate-effect, sensitivity, or leave-one-pair-out "
                                "table was explicitly approved."
                            ),
                        ),
                    },
                ),
            },
            {
                "id": "review-category",
                "title": "Review decisions",
                "open": False,
                "sections": (
                    {
                        "id": "candidate-section",
                        "title": "Separate Step 09c selection and adjudication",
                        "blocks": [
                            _note(
                                "These tables exist only when separately supplied "
                                "Step 09c review approvals are present. They do not "
                                "alter the computational tables above.",
                                notice=True,
                            ),
                            *_tables_for_roles(
                                tables_by_role,
                                ("candidate_selection", "candidate_adjudication"),
                                (
                                    "No Step 09c candidate-selection or adjudication "
                                    "table was explicitly approved."
                                ),
                            ),
                        ],
                    },
                    {
                        "id": "decisions-section",
                        "title": (
                            "Background, matched-DNA, orthogonal-evidence, and review decisions"
                        ),
                        "blocks": [
                            _decisions(summary),
                            *_tables_for_roles(
                                tables_by_role,
                                ("decisions",),
                                "No separate decision table was explicitly approved.",
                            ),
                        ],
                    },
                    {
                        "id": "rerun-section",
                        "title": "Rerun implications",
                        "blocks": [_rerun_implications(summary)],
                    },
                ),
            },
            {
                "id": "evidence-category",
                "title": "Evidence and provenance",
                "open": False,
                "sections": evidence_sections,
            },
        ),
    }
