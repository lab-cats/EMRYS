"""Candidate selection and adjudication review checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .contracts import review_package, step08
from .intake import (
    validate_candidate_reference,
    validate_iso_date,
    validate_supporting_ids,
)


def validate_candidate_selection(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    candidates: Mapping[str, Mapping[str, str]],
    complete: bool,
) -> set[tuple[str, str]]:
    expected_sets = {
        "top_up": step08.parse_nonnegative_int("top_up_count", plan["top_up_count"]),
        "top_down": step08.parse_nonnegative_int(
            "top_down_count", plan["top_down_count"]
        ),
        "discordant": step08.parse_nonnegative_int(
            "discordant_count", plan["discordant_count"]
        ),
        "near_threshold": step08.parse_nonnegative_int(
            "near_threshold_count", plan["near_threshold_count"]
        ),
    }
    seen: set[tuple[str, str]] = set()
    ranks: dict[str, list[int]] = {key: [] for key in expected_sets}
    for row_number, row in enumerate(rows, start=2):
        selection_set = row["selection_set"]
        if selection_set not in expected_sets:
            step08.fail("Candidate selection contains an unknown selection_set.")
        key = (selection_set, row["candidate_id"])
        if key in seen:
            step08.fail("Candidate selection contains a duplicate candidate/set pair.")
        seen.add(key)
        result = validate_candidate_reference(
            f"Candidate selection row {row_number}",
            row["candidate_id"],
            candidates,
        )
        rank = step08.parse_nonnegative_int("Candidate selection rank", row["rank"])
        if rank < 1:
            step08.fail("Candidate selection rank must be at least 1.")
        ranks[selection_set].append(rank)
        if (
            row["selection_policy_version"]
            != plan["candidate_selection_policy_version"]
        ):
            step08.fail("Candidate selection policy version differs from the plan.")
        expected_values = {
            "source_call_status": result["call_status"],
            "source_fdr": result["cmh_fdr_bh"],
            "source_common_or": result["common_odds_ratio"],
            "source_delta": result["treatment_control_difference"],
        }
        for column, expected in expected_values.items():
            if row[column] != expected:
                step08.fail(
                    f"Candidate selection row {row_number} {column} differs "
                    "from Step 09."
                )
        validate_iso_date("Candidate selection review_date", row["review_date"])
    for selection_set, values in ranks.items():
        if values != list(range(1, len(values) + 1)):
            step08.fail(
                f"Candidate selection ranks for {selection_set} must be "
                "contiguous and ordered."
            )
        if complete and len(values) != expected_sets[selection_set]:
            step08.fail(
                f"Complete candidate selection count for {selection_set} "
                "differs from the plan."
            )
    return seen


def validate_candidate_adjudication(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    selected: set[tuple[str, str]],
    evidence_ids: set[str],
    complete: bool,
) -> set[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        validate_candidate_reference(
            f"Candidate adjudication row {row_number}",
            row["candidate_id"],
            candidates,
        )
        key = (row["selection_set"], row["candidate_id"])
        if key not in selected:
            step08.fail("Candidate adjudication is not part of candidate selection.")
        if key in seen:
            step08.fail(
                "Candidate adjudication contains a duplicate candidate/set pair."
            )
        seen.add(key)
        validate_supporting_ids(
            "Candidate adjudication supporting_evidence_ids",
            row["supporting_evidence_ids"],
            evidence_ids,
        )
        validate_iso_date("Candidate adjudication review_date", row["review_date"])
        step08.validate_enum(
            "Candidate adjudication adjudication_status",
            row["adjudication_status"],
            review_package.ADJUDICATION_STATUSES,
        )
        for column in review_package.ADJUDICATION_COMPONENT_FIELDS:
            step08.validate_enum(
                f"Candidate adjudication {column}",
                row[column],
                review_package.AUDIT_COMPONENT_STATUSES,
            )
        component_values = [
            row[column] for column in review_package.ADJUDICATION_COMPONENT_FIELDS
        ]
        if row["adjudication_status"] == "pass" and any(
            status in ("flag", "fail") for status in component_values
        ):
            step08.fail(
                "Candidate adjudication status=pass conflicts with a "
                "flagged or failed component."
            )
        for column in (
            "reason",
            "reviewer",
        ):
            step08.require_text(f"Candidate adjudication {column}", row[column])
    if complete and seen != selected:
        step08.fail("Complete candidate adjudication does not cover every selection.")
    return seen
