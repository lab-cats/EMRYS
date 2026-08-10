"""Scientific decision and limitation review checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .contracts import NA_VALUE, review_package, step08
from .intake import split_ids, validate_iso_date, validate_supporting_ids


def validate_decisions(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    evidence_rows: Sequence[Mapping[str, str]],
    complete: bool,
) -> dict[str, str]:
    step08.ensure_unique(rows, "decision_id", "Scientific decisions")
    evidence_status_by_id = {
        row["evidence_id"]: row["evidence_status"] for row in evidence_rows
    }
    evidence_ids = set(evidence_status_by_id)
    seen: set[str] = set()
    decisions: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        dimension = row["decision_dimension"]
        step08.validate_enum(
            f"Scientific decisions row {row_number} dimension",
            dimension,
            review_package.DECISION_DIMENSIONS,
        )
        if dimension in seen:
            step08.fail("Scientific decisions contains duplicate decision dimensions.")
        seen.add(dimension)
        step08.validate_enum(
            "Scientific decision evidence_status",
            row["evidence_status"],
            review_package.EVIDENCE_STATUSES,
        )
        if complete and row["evidence_status"] not in (
            "complete",
            "not_applicable",
        ):
            step08.fail(
                "A complete science review cannot retain a missing or "
                "incomplete decision evidence status."
            )
        step08.validate_enum(
            "Scientific decision decision_status",
            row["decision_status"],
            review_package.DECISION_STATUSES,
        )
        step08.validate_enum(
            "Scientific decision rerun_scope",
            row["rerun_scope"],
            review_package.RERUN_SCOPES,
        )
        if row["rerun_required"] not in ("TRUE", "FALSE"):
            step08.fail("Scientific decision rerun_required must be TRUE or FALSE.")
        supporting_ids = split_ids(
            "Scientific decision supporting_evidence_ids",
            row["supporting_evidence_ids"],
        )
        for evidence_id in supporting_ids:
            if evidence_id not in evidence_ids:
                step08.fail(
                    "Scientific decision supporting_evidence_ids references "
                    f"unknown evidence_id {evidence_id}."
                )
        step08.require_text("Scientific decision rationale", row["rationale"])
        step08.require_text("Scientific decision owner", row["decision_owner"])
        step08.validate_safe_id(
            "Scientific decision policy_version",
            row["policy_version"],
        )
        if row["decision_status"] == "recorded":
            if row["evidence_status"] not in (
                "complete",
                "not_applicable",
            ):
                step08.fail(
                    "Recorded scientific decisions require their own "
                    "evidence_status to be complete or not_applicable."
                )
            if not supporting_ids:
                step08.fail(
                    "Recorded scientific decisions require at least one "
                    "supporting evidence ID."
                )
            unsupported = [
                evidence_id
                for evidence_id in supporting_ids
                if evidence_status_by_id[evidence_id]
                not in ("complete", "not_applicable")
            ]
            if unsupported:
                step08.fail(
                    "Recorded scientific decisions cannot cite missing or "
                    "incomplete evidence: " + ",".join(unsupported)
                )
            step08.require_text("Scientific decision value", row["decision_value"])
            validate_iso_date("Scientific decision decision_date", row["decision_date"])
            decisions[dimension] = row["decision_value"]
        else:
            if supporting_ids:
                step08.fail(
                    "Pending scientific decisions must not cite supporting "
                    "evidence IDs."
                )
            if row["decision_value"] != NA_VALUE or row["decision_date"] != NA_VALUE:
                step08.fail(
                    "Pending scientific decisions must use NA for value and date."
                )
            decisions[dimension] = "pending"
        if (row["rerun_required"] == "FALSE") != (row["rerun_scope"] == "none"):
            step08.fail(
                "Scientific decision rerun_required must be FALSE exactly "
                "when rerun_scope=none."
            )
    if complete and seen != set(review_package.DECISION_DIMENSIONS):
        step08.fail(
            "Complete scientific decisions do not cover every decision dimension."
        )
    if complete and any(value == "pending" for value in decisions.values()):
        step08.fail("A complete science review cannot contain pending decisions.")
    if (
        decisions.get("orientation") not in (None, "pending")
        and decisions["orientation"] != plan["orientation_status"]
    ):
        step08.fail(
            "The recorded orientation decision must equal plan orientation_status."
        )
    return decisions


def validate_limitations(
    rows: Sequence[Mapping[str, str]], evidence_ids: set[str]
) -> None:
    step08.ensure_unique(rows, "limitation_id", "Scientific limitations")
    for row in rows:
        step08.validate_safe_id(
            "Scientific limitation limitation_id",
            row["limitation_id"],
        )
        for column in (
            "limitation_category",
            "severity",
            "description",
            "impact",
            "mitigation",
            "owner",
        ):
            step08.require_text(f"Scientific limitation {column}", row[column])
        step08.validate_enum(
            "Scientific limitation limitation_status",
            row["limitation_status"],
            ("active", "open", "accepted", "resolved"),
        )
        validate_iso_date("Scientific limitation review_date", row["review_date"])
        validate_supporting_ids(
            "Scientific limitation related_evidence_ids",
            row["related_evidence_ids"],
            evidence_ids,
        )
