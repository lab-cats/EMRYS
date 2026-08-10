"""Scientific-review HTML sections for static NORAD run reports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .html_components import _empty, _key_value_table, _table
from .models import COMPUTATIONAL_STATUS_FIELDS


def _scientific_record(summary: Mapping[str, Any]) -> Mapping[str, Any] | None:
    record = summary["scientific_review"]["record"]
    return record if isinstance(record, Mapping) else None


def _render_evidence_categories(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "No normalized scientific-review record is present. Orientation, "
            "annotation, funnel, replicate, sensitivity, and adjudication "
            "evidence remain unavailable."
        )
    rows = []
    for category, value in record["evidence_categories"].items():
        rows.append(
            (
                category,
                value["status"],
                ", ".join(value["evidence_ids"]) or "None declared",
                value["not_applicable_reason"],
            )
        )
    return _table(
        table_id="science-evidence-categories",
        caption="Scientific evidence-category completeness",
        header=("Category", "Status", "Evidence IDs", "Not-applicable reason"),
        rows=rows,
    )


def _render_limitations(summary: Mapping[str, Any]) -> str:
    limitations = summary["limitations"]
    if not limitations:
        return _empty("No limitations are recorded in the canonical run summary.")
    return _table(
        table_id="limitations",
        caption="Recorded limitations and their interpretation impact",
        header=(
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
        rows=(
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


def _render_decisions(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "Background, matched-DNA, orthogonal-evidence, annotation, "
            "threshold, and adjudication decisions are unavailable because "
            "no scientific-review record is present."
        )
    rows = []
    for dimension, decision in record["decisions"].items():
        rows.append(
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
        )
    return _table(
        table_id="science-decisions",
        caption="Explicit scientific-review decision dimensions",
        header=(
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
        rows=rows,
    )


def _render_rerun_implications(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "No review decisions are available from which to report explicit "
            "rerun implications. This report does not infer them."
        )
    rows = [
        (
            dimension,
            decision["status"],
            decision.get("rerun_required"),
            decision["rerun_scope"],
            decision["detail"],
        )
        for dimension, decision in record["decisions"].items()
    ]
    return _table(
        table_id="rerun-implications",
        caption=(
            "Recorded rerun scopes copied from review decisions; no rerun is "
            "scheduled or executed by this report"
        ),
        header=(
            "Decision dimension",
            "Status",
            "Rerun required",
            "Rerun scope",
            "Detail",
        ),
        rows=rows,
    )


def _render_evidence_index(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None or not record["evidence_records"]:
        return _empty(
            "No scientific evidence index is present in the canonical run summary."
        )
    return _table(
        table_id="science-evidence-index",
        caption="Explicit scientific evidence records",
        header=(
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
        rows=(
            (
                evidence["evidence_id"],
                evidence["category"],
                evidence["analysis_id"],
                evidence["status"],
                (
                    evidence["source"]["path"]
                    if evidence["source"] is not None
                    else "Not available"
                ),
                (
                    evidence["source"]["sha256"]
                    if evidence["source"] is not None
                    else "Not available"
                ),
                evidence["reviewer"],
                evidence["owner"],
                evidence["evidence_date"],
                evidence["policy_version"],
            )
            for evidence in record["evidence_records"]
        ),
    )


def _render_input_artifacts(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty("No scientific-review input-artifact list is present.")
    return _table(
        table_id="science-input-artifacts",
        caption="Scientific-review input artifacts",
        header=("Role", "Artifact ID", "Path", "SHA-256", "Rows"),
        rows=(
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


def _render_science_methods(summary: Mapping[str, Any]) -> str:
    record = _scientific_record(summary)
    if record is None:
        return _empty(
            "Scientific-review metadata, policies, selection rules, and "
            "computational evidence are unavailable because no normalized "
            "review record is present."
        )
    metadata = _key_value_table(
        table_id="science-review-metadata",
        caption="Scientific-review metadata",
        rows=record["review_metadata"].items(),
    )
    policies = _key_value_table(
        table_id="science-policy-versions",
        caption="Scientific-review policy versions",
        rows=record["policy_versions"].items(),
    )
    rules = _key_value_table(
        table_id="science-selection-rules",
        caption="Preregistered selection and sensitivity rules",
        rows=record["selection_rules"].items(),
    )
    computational = record["computational_status"]
    status_rows = tuple(
        (label, computational[field]) for label, field in COMPUTATIONAL_STATUS_FIELDS
    )
    status_table = _key_value_table(
        table_id="science-computational-status",
        caption="Computational status declared by the scientific review",
        rows=status_rows,
    )
    evidence = computational["evidence"]
    evidence_table = (
        _table(
            table_id="science-computational-evidence",
            caption="Computational evidence references declared by the review",
            header=("Evidence ID", "Role", "Path", "SHA-256"),
            rows=(
                (
                    item["evidence_id"],
                    item["role"],
                    item["path"],
                    item["sha256"],
                )
                for item in evidence
            ),
        )
        if evidence
        else _empty(
            "The scientific-review record declares no computational evidence "
            "references."
        )
    )
    return "\n".join((metadata, policies, rules, status_table, evidence_table))
