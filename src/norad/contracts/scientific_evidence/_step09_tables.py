"""Step 09 table loading and cross-input reconciliation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from norad.contracts.scientific_evidence import step08
from norad.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY,
)
from norad.libraries.alignments.orientation import (
    validate_legacy_orientation_policy as IS_LEGACY_ORIENTATION_POLICY,
)

from ._step09_definitions import (
    CANONICAL_MUTATIONS,
    NA_VALUE,
    STEP09_CALL_STATUSES,
    STEP09_MUTATION_HEADER,
    STEP09_RESULT_HEADER,
    STEP09_STATUS_COUNT_FIELDS,
    STEP09_SUMMARY_HEADER,
    STEP09_TEST_STATUSES,
)
from ._step09_support import count_status, paired_samples, resolve_recorded_path

Table = step08.Table
read_tsv = step08.read_tsv
values_close = step08.values_close


def validate_step09_results(
    label: str,
    value: str | Path,
    sample_ids: Sequence[str],
    analysis_id: str,
    step08_sites: Sequence[Mapping[str, str]],
) -> Table:
    expected_header = step08.sample_block_header(STEP09_RESULT_HEADER, sample_ids)
    table = read_tsv(label, value, expected_header)
    step08.ensure_unique(table.rows, "candidate_id", label)
    sites_by_id = {row["candidate_id"]: row for row in step08_sites}
    metadata_columns = step08.STEP08_METADATA_HEADER
    sample_columns = step08.sample_block_header((), sample_ids)
    for row_number, row in enumerate(table.rows, start=2):
        if row["analysis_id"] != analysis_id:
            step08.fail(f"{label} row {row_number} has the wrong analysis_id.")
        site = sites_by_id.get(row["candidate_id"])
        if site is None:
            step08.fail(f"{label} references an unknown Step 08 candidate.")
        for column in metadata_columns + sample_columns:
            if row[column] != site[column]:
                step08.fail(
                    f"{label} row {row_number} {column} differs from "
                    "the Step 08 candidate."
                )
        step08.validate_enum(
            f"{label} row {row_number} test_status",
            row["test_status"],
            STEP09_TEST_STATUSES,
        )
        step08.validate_enum(
            f"{label} row {row_number} call_status",
            row["call_status"],
            STEP09_CALL_STATUSES,
        )
        step08.parse_nonnegative_int(
            f"{label} row {row_number} replicate_count",
            row["replicate_count"],
        )
    return table


def validate_step09_summary(
    value: str | Path,
    analysis_id: str,
    cohort_id: str,
    sample_ids: Sequence[str],
    sample_rows: Sequence[Mapping[str, str]],
    all_rows: Sequence[Mapping[str, str]],
    sample_manifest: Path,
    partition_manifest: Path,
    step08_sites: Path,
    step08_inputs: Path,
    sample_hash: str,
    partition_hash: str,
    sites_hash: str,
    inputs_hash: str,
    step08_orientation_policy: str,
) -> Table:
    step08.validate_safe_id("analysis_id", analysis_id)
    step08.validate_safe_id("cohort_id", cohort_id)
    table = read_tsv("Step 09 summary", value, STEP09_SUMMARY_HEADER)
    if len(table.rows) != 1:
        step08.fail("Step 09 summary must contain exactly one data row.")
    row = table.rows[0]
    if row["analysis_id"] != analysis_id:
        step08.fail("Step 09 summary analysis_id differs from its directory.")
    if row["cohort_id"] != cohort_id:
        step08.fail("Step 09 summary cohort_id differs from the Step 08 receipt.")
    step08.validate_safe_id("control_condition", row["control_condition"])
    step08.validate_safe_id("treatment_condition", row["treatment_condition"])
    if row["background_condition"] != NA_VALUE:
        step08.validate_safe_id("background_condition", row["background_condition"])
    if (
        row["multiple_testing_method"] != "BH"
        or row["cmh_alternative"] != "two.sided"
        or row["continuity_correction"] != "TRUE"
    ):
        step08.fail("Step 09 summary does not declare the approved CMH contract.")
    expected_paths = {
        "sample_manifest_path": sample_manifest,
        "partition_manifest_path": partition_manifest,
        "step08_sites_path": step08_sites,
        "step08_inputs_path": step08_inputs,
    }
    for column, expected in expected_paths.items():
        if resolve_recorded_path(row[column]) != expected:
            step08.fail(f"Step 09 summary {column} differs from the explicit input.")
    expected_hashes = {
        "sample_manifest_sha256": sample_hash,
        "partition_manifest_sha256": partition_hash,
        "step08_sites_sha256": sites_hash,
        "step08_inputs_sha256": inputs_hash,
    }
    for column, expected in expected_hashes.items():
        step08.validate_hash(f"Step 09 summary {column}", row[column])
        if row[column] != expected:
            step08.fail(f"Step 09 summary {column} is stale.")
    if step08.parse_nonnegative_int(
        "Step 09 summary sample_count", row["sample_count"]
    ) != len(sample_ids):
        step08.fail("Step 09 summary sample_count differs from the sample manifest.")
    if step08.parse_nonnegative_int(
        "Step 09 summary candidate_count", row["candidate_count"]
    ) != len(all_rows):
        step08.fail("Step 09 summary candidate_count differs from all-sites.")
    target_change = row["target_rna_change"]
    if not re.fullmatch(r"[ACGT]>[ACGT]", target_change):
        step08.fail("Step 09 summary target_rna_change must be a canonical SNV.")
    target_ref, target_alt = target_change.split(">")
    expected_target_count = sum(
        result["rna_ref"] == target_ref and result["rna_alt"] == target_alt
        for result in all_rows
    )
    if (
        step08.parse_nonnegative_int(
            "Step 09 summary target_candidate_count",
            row["target_candidate_count"],
        )
        != expected_target_count
    ):
        step08.fail("Step 09 summary target candidate count does not reconcile.")
    for summary_column, result_column, status in STEP09_STATUS_COUNT_FIELDS:
        expected = count_status(all_rows, result_column, status)
        if (
            step08.parse_nonnegative_int(
                f"Step 09 summary {summary_column}", row[summary_column]
            )
            != expected
        ):
            step08.fail(f"Step 09 summary {summary_column} does not reconcile.")
    replicates, _ = paired_samples(
        sample_rows, row["control_condition"], row["treatment_condition"]
    )
    if step08.parse_nonnegative_int(
        "Step 09 summary replicate_count", row["replicate_count"]
    ) != len(replicates):
        step08.fail("Step 09 summary replicate_count differs from the sample manifest.")
    if (
        not IS_LEGACY_ORIENTATION_POLICY(step08_orientation_policy)[0]
        or not IS_LEGACY_ORIENTATION_POLICY(row["orientation_policy"])[0]
        or row["orientation_policy"] != step08_orientation_policy
    ):
        step08.fail(
            "Step 09 summary and Step 08 must use "
            f"orientation_policy={LEGACY_PROVISIONAL_ORIENTATION_POLICY}."
        )
    if any(
        result["orientation_policy"] != row["orientation_policy"] for result in all_rows
    ):
        step08.fail("Step 09 results contain an inconsistent orientation policy.")
    background = row["background_condition"]
    if background != NA_VALUE:
        if background in (row["control_condition"], row["treatment_condition"]):
            step08.fail("Step 09 background condition must be independent.")
        if not any(sample["condition"] == background for sample in sample_rows):
            step08.fail("Step 09 background condition is absent from the manifest.")
    expected_result_context = {
        "control_condition": row["control_condition"],
        "treatment_condition": row["treatment_condition"],
        "target_rna_change": row["target_rna_change"],
        "replicate_count": row["replicate_count"],
        "background_condition": row["background_condition"],
        "orientation_policy": row["orientation_policy"],
    }
    for result in all_rows:
        for column, expected in expected_result_context.items():
            if result[column] != expected:
                step08.fail(
                    f"Step 09 all-sites {column} differs from the summary "
                    f"for candidate {result['candidate_id']}."
                )
    return table


def validate_mutation_spectrum(
    value: str | Path,
    analysis_id: str,
    all_rows: Sequence[Mapping[str, str]],
) -> Table:
    table = read_tsv("Step 09 mutation spectrum", value, STEP09_MUTATION_HEADER)
    if [row["mutation_type"] for row in table.rows] != list(CANONICAL_MUTATIONS):
        step08.fail("Step 09 mutation spectrum must contain the canonical 12 SNVs.")
    total = len(all_rows)
    for row in table.rows:
        mutation_type = row["mutation_type"]
        ref, alt = mutation_type.split(">")
        if (
            row["analysis_id"] != analysis_id
            or row["rna_ref"] != ref
            or row["rna_alt"] != alt
        ):
            step08.fail("Step 09 mutation spectrum identity columns do not reconcile.")
        selected = [
            result
            for result in all_rows
            if result["rna_ref"] == ref and result["rna_alt"] == alt
        ]
        expected_counts = {
            "candidate_count": len(selected),
            "successfully_tested_count": count_status(
                selected, "test_status", "tested"
            ),
            "significant_up_count": count_status(
                selected, "call_status", "significant_up"
            ),
            "significant_down_count": count_status(
                selected, "call_status", "significant_down"
            ),
        }
        for column, expected in expected_counts.items():
            if (
                step08.parse_nonnegative_int(
                    f"Step 09 mutation spectrum {column}", row[column]
                )
                != expected
            ):
                step08.fail(f"Step 09 mutation spectrum {column} does not reconcile.")
        fraction = step08.parse_number(
            "Step 09 mutation spectrum candidate_fraction",
            row["candidate_fraction"],
            nonnegative=True,
        )
        expected_fraction = 0.0 if total == 0 else len(selected) / total
        if (
            fraction is None
            or fraction > 1
            or not values_close(fraction, expected_fraction)
        ):
            step08.fail("Step 09 mutation spectrum candidate_fraction is invalid.")
    return table
