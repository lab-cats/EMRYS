"""Sensitivity and leave-one-pair-out review checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .contracts import Table, read_tsv, review_package, sha256_file, step08, step09
from .intake import (
    split_ids,
    validate_candidate_reference,
    validate_iso_date,
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
    result_header = step08.sample_block_header(step09.STEP09_RESULT_HEADER, sample_ids)
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
