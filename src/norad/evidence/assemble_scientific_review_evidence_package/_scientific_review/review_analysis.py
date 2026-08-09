"""Sensitivity, candidate-review, decision, and limitation checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .contracts import (
    NA_VALUE,
    Table,
    read_tsv,
    review_package,
    sha256_file,
    step08,
    step09,
)
from .intake import (
    split_ids,
    validate_candidate_reference,
    validate_iso_date,
    validate_supporting_ids,
)


def validate_analysis_file_reference(
    label: str,
    path_value: str,
    hash_value: str,
    expected_header: Sequence[str],
    input_hashes: dict[Path, str],
) -> Table:
    path = step08.require_file(label, step09.resolve_recorded_path(path_value))
    step08.validate_hash(f"{label} SHA-256", hash_value)
    observed_hash = sha256_file(path)
    if hash_value != observed_hash:
        step08.fail(f"{label} SHA-256 differs from the declared value.")
    table = read_tsv(label, path, expected_header)
    input_hashes[path] = observed_hash
    return table


def validate_sensitivity_matrix(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    primary_summary_path: Path,
    primary_summary: Mapping[str, str],
    input_hashes: dict[Path, str],
    complete: bool,
) -> None:
    step08.ensure_unique(rows, "parameter_set_id", "Sensitivity matrix")
    expected_ids = {
        plan["primary_analysis_id"],
        *split_ids("sensitivity_analysis_ids", plan["sensitivity_analysis_ids"]),
    }
    observed_ids: set[str] = set()
    primary_count = 0
    for row_number, row in enumerate(rows, start=2):
        analysis_id = row["analysis_id"]
        if analysis_id not in expected_ids:
            step08.fail("Sensitivity matrix references an undeclared analysis.")
        if analysis_id in observed_ids:
            step08.fail("Sensitivity matrix contains duplicate analysis IDs.")
        observed_ids.add(analysis_id)
        is_primary = row["is_primary"]
        if is_primary not in ("TRUE", "FALSE"):
            step08.fail("Sensitivity matrix is_primary must be TRUE or FALSE.")
        summary_table = validate_analysis_file_reference(
            f"Sensitivity summary row {row_number}",
            row["analysis_summary_path"],
            row["analysis_summary_sha256"],
            step09.STEP09_SUMMARY_HEADER,
            input_hashes,
        )
        if len(summary_table.rows) != 1:
            step08.fail("A sensitivity analysis summary must have exactly one row.")
        summary = summary_table.rows[0]
        if summary["analysis_id"] != analysis_id:
            step08.fail("Sensitivity matrix analysis_id differs from its summary.")
        if is_primary == "TRUE":
            primary_count += 1
            if analysis_id != plan["primary_analysis_id"]:
                step08.fail("Only the primary analysis may use is_primary=TRUE.")
            if summary_table.path != primary_summary_path:
                step08.fail(
                    "Primary sensitivity row must reference the Step 09 summary."
                )
            if summary != primary_summary:
                step08.fail("Primary sensitivity summary differs from Step 09.")
        elif analysis_id == plan["primary_analysis_id"]:
            step08.fail("The primary sensitivity row must use is_primary=TRUE.")
        for column in review_package.SENSITIVITY_SUMMARY_FIELDS:
            if row[column] != summary[column]:
                step08.fail(
                    f"Sensitivity matrix row {row_number} {column} "
                    "differs from its analysis summary."
                )
        validate_iso_date("Sensitivity matrix review_date", row["review_date"])
    if complete and (observed_ids != expected_ids or primary_count != 1):
        step08.fail("Complete sensitivity matrix does not cover all declared analyses.")


def validate_leave_one_pair_out(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    candidates: Mapping[str, Mapping[str, str]],
    sample_rows: Sequence[Mapping[str, str]],
    sample_ids: Sequence[str],
    summary: Mapping[str, str],
    input_hashes: dict[Path, str],
    complete: bool,
) -> None:
    replicate_order, _ = step09.paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    replicates = set(replicate_order)
    result_header = (
        step09.STEP09_RESULT_HEADER
        + tuple(f"DP__{sample}" for sample in sample_ids)
        + tuple(f"AD__{sample}" for sample in sample_ids)
        + tuple(f"AF__{sample}" for sample in sample_ids)
    )
    seen: set[tuple[str, str]] = set()
    analysis_by_replicate: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        if row["primary_analysis_id"] != plan["primary_analysis_id"]:
            step08.fail("Leave-one-pair-out row has the wrong primary_analysis_id.")
        step08.validate_safe_id("Leave-one-pair-out analysis_id", row["analysis_id"])
        prior_analysis = analysis_by_replicate.setdefault(
            row["omitted_replicate"], row["analysis_id"]
        )
        if prior_analysis != row["analysis_id"]:
            step08.fail(
                "Leave-one-pair-out rows for one omitted replicate must "
                "reference one immutable analysis ID."
            )
        if row["omitted_replicate"] not in replicates:
            step08.fail("Leave-one-pair-out row references an unknown replicate.")
        primary = validate_candidate_reference(
            f"Leave-one-pair-out row {row_number}",
            row["candidate_id"],
            candidates,
        )
        key = (row["candidate_id"], row["omitted_replicate"])
        if key in seen:
            step08.fail("Leave-one-pair-out evidence contains a duplicate comparison.")
        seen.add(key)
        all_table = validate_analysis_file_reference(
            f"Leave-one-pair-out all-sites row {row_number}",
            row["all_sites_path"],
            row["all_sites_sha256"],
            result_header,
            input_hashes,
        )
        summary_table = validate_analysis_file_reference(
            f"Leave-one-pair-out summary row {row_number}",
            row["summary_path"],
            row["summary_sha256"],
            step09.STEP09_SUMMARY_HEADER,
            input_hashes,
        )
        if len(summary_table.rows) != 1 or (
            summary_table.rows[0]["analysis_id"] != row["analysis_id"]
        ):
            step08.fail("Leave-one-pair-out summary identity is invalid.")
        matched = [
            candidate
            for candidate in all_table.rows
            if candidate["candidate_id"] == row["candidate_id"]
        ]
        if len(matched) != 1:
            step08.fail(
                "Leave-one-pair-out all-sites must contain the referenced "
                "candidate exactly once."
            )
        alternate = matched[0]
        expected_values = {
            "primary_call_status": primary["call_status"],
            "leave_one_out_test_status": alternate["test_status"],
            "leave_one_out_call_status": alternate["call_status"],
            "primary_delta": primary["treatment_control_difference"],
            "leave_one_out_delta": alternate["treatment_control_difference"],
            "primary_common_or": primary["common_odds_ratio"],
            "leave_one_out_common_or": alternate["common_odds_ratio"],
            "primary_fdr": primary["cmh_fdr_bh"],
            "leave_one_out_fdr": alternate["cmh_fdr_bh"],
        }
        for column, expected in expected_values.items():
            if row[column] != expected:
                step08.fail(
                    f"Leave-one-pair-out row {row_number} {column} differs "
                    "from its analysis result."
                )
        validate_iso_date("Leave-one-pair-out review_date", row["review_date"])
    if len(set(analysis_by_replicate.values())) != len(analysis_by_replicate):
        step08.fail(
            "Each leave-one-pair-out replicate must use a distinct analysis ID."
        )
    if complete and set(analysis_by_replicate) != replicates:
        step08.fail(
            "Complete leave-one-pair-out evidence must cover every "
            "manifest-defined replicate."
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
            row[column]
            for column in review_package.ADJUDICATION_COMPONENT_FIELDS
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
