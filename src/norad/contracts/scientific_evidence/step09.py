"""Validate the neutral Step 09 scientific-evidence output contract."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from norad.contracts.scientific_evidence import step08
from norad.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY,
    validate_legacy_orientation_policy as IS_LEGACY_ORIENTATION_POLICY,
)

ContractError = step08.ContractError
Table = step08.Table
NA_VALUE = step08.NA_VALUE
values_close = step08.values_close
read_tsv = step08.read_tsv

STEP09_RESULT_HEADER = (
    "analysis_id",
    "partition_id",
    "candidate_id",
    "orientation",
    "chromosome",
    "position",
    "alt_index",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "annotation_strand",
    "gene_ids",
    "transcript_ids",
    "is_cds",
    "is_five_prime_utr",
    "is_three_prime_utr",
    "is_exon",
    "is_intron",
    "qual",
    "filter",
    "info_alt_depth",
    "orientation_policy",
    "control_condition",
    "treatment_condition",
    "target_rna_change",
    "replicate_count",
    "test_status",
    "call_status",
    "background_condition",
    "background_status",
    "min_analysis_dp",
    "mean_analysis_dp",
    "mean_control_af",
    "mean_treatment_af",
    "treatment_control_difference",
    "max_background_af",
    "cmh_statistic",
    "cmh_degrees_freedom",
    "cmh_p_value",
    "cmh_fdr_bh",
    "common_odds_ratio",
)

STEP09_SUMMARY_HEADER = (
    "analysis_id",
    "cohort_id",
    "control_condition",
    "treatment_condition",
    "background_condition",
    "target_rna_change",
    "replicate_count",
    "sample_count",
    "candidate_count",
    "target_candidate_count",
    "successfully_tested_count",
    "not_target_change_count",
    "missing_counts_count",
    "low_coverage_count",
    "degenerate_table_count",
    "below_mean_dp_count",
    "background_not_passed_count",
    "fdr_not_met_count",
    "effect_not_met_count",
    "significant_up_count",
    "significant_down_count",
    "sample_manifest_path",
    "sample_manifest_sha256",
    "partition_manifest_path",
    "partition_manifest_sha256",
    "step08_sites_path",
    "step08_sites_sha256",
    "step08_inputs_path",
    "step08_inputs_sha256",
    "min_sample_dp",
    "mean_dp_threshold",
    "fdr_threshold",
    "common_or_threshold",
    "absolute_difference_threshold",
    "background_max_fraction",
    "multiple_testing_method",
    "cmh_alternative",
    "continuity_correction",
    "orientation_policy",
)

STEP09_MUTATION_HEADER = (
    "analysis_id",
    "rna_ref",
    "rna_alt",
    "mutation_type",
    "candidate_count",
    "candidate_fraction",
    "successfully_tested_count",
    "significant_up_count",
    "significant_down_count",
)

CANONICAL_MUTATIONS = (
    "A>C",
    "A>G",
    "A>T",
    "C>A",
    "C>G",
    "C>T",
    "G>A",
    "G>C",
    "G>T",
    "T>A",
    "T>C",
    "T>G",
)

STEP09_TEST_STATUSES = (
    "tested",
    "not_target_change",
    "missing_counts",
    "low_coverage",
    "degenerate_table",
)
STEP09_CALL_STATUSES = (
    "not_tested",
    "below_mean_dp",
    "background_not_passed",
    "fdr_not_met",
    "effect_not_met",
    "significant_up",
    "significant_down",
)
STEP09_BACKGROUND_STATUSES = (
    "disabled",
    "pass",
    "missing_counts",
    "low_coverage",
    "fail_fraction",
)

STEP09_STATUS_COUNT_FIELDS = (
    ("successfully_tested_count", "test_status", "tested"),
    ("not_target_change_count", "test_status", "not_target_change"),
    ("missing_counts_count", "test_status", "missing_counts"),
    ("low_coverage_count", "test_status", "low_coverage"),
    ("degenerate_table_count", "test_status", "degenerate_table"),
    ("below_mean_dp_count", "call_status", "below_mean_dp"),
    ("background_not_passed_count", "call_status", "background_not_passed"),
    ("fdr_not_met_count", "call_status", "fdr_not_met"),
    ("effect_not_met_count", "call_status", "effect_not_met"),
    ("significant_up_count", "call_status", "significant_up"),
    ("significant_down_count", "call_status", "significant_down"),
)


def parse_nonnegative_or_infinite(label: str, value: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        step08.fail(f"{label} must be numeric; got: {value}")
    if math.isnan(parsed) or parsed < 0:
        step08.fail(f"{label} must be non-negative and not NaN; got: {value}")
    return parsed


def resolve_recorded_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def validate_pdf(label: str, path: Path) -> None:
    path = step08.require_file(label, path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        step08.fail(f"Could not read {label}: {exc}")
    if not data.startswith(b"%PDF-"):
        step08.fail(f"{label} lacks a %PDF- signature: {path}")
    if b"%%EOF" not in data[-2048:]:
        step08.fail(f"{label} lacks a trailing %%EOF marker: {path}")


def count_status(rows: Sequence[Mapping[str, str]], column: str, value: str) -> int:
    return sum(row[column] == value for row in rows)


def paired_samples(
    sample_rows: Sequence[Mapping[str, str]],
    control: str,
    treatment: str,
) -> tuple[list[str], dict[str, tuple[str, str]]]:
    if control == treatment:
        step08.fail("Step 09 control and treatment conditions must differ.")
    analysis_rows = [
        row for row in sample_rows if row["condition"] in (control, treatment)
    ]
    replicates: list[str] = []
    for row in analysis_rows:
        if row["replicate"] not in replicates:
            replicates.append(row["replicate"])
    pairs: dict[str, tuple[str, str]] = {}
    for replicate in replicates:
        controls = [
            row["sample_id"]
            for row in sample_rows
            if row["condition"] == control and row["replicate"] == replicate
        ]
        treatments = [
            row["sample_id"]
            for row in sample_rows
            if row["condition"] == treatment and row["replicate"] == replicate
        ]
        if len(controls) != 1 or len(treatments) != 1:
            step08.fail(
                "Sample manifest must define exactly one control and one "
                f"treatment for replicate {replicate}."
            )
        pairs[replicate] = (controls[0], treatments[0])
    control_replicates = {
        row["replicate"] for row in sample_rows if row["condition"] == control
    }
    treatment_replicates = {
        row["replicate"] for row in sample_rows if row["condition"] == treatment
    }
    if control_replicates != treatment_replicates or len(replicates) < 2:
        step08.fail(
            "Sample manifest must define identical control/treatment replicate "
            "sets with at least two strata."
        )
    return replicates, pairs


def validate_step09_results(
    label: str,
    value: str | Path,
    sample_ids: Sequence[str],
    analysis_id: str,
    step08_sites: Sequence[Mapping[str, str]],
) -> Table:
    expected_header = (
        STEP09_RESULT_HEADER
        + tuple(f"DP__{sample}" for sample in sample_ids)
        + tuple(f"AD__{sample}" for sample in sample_ids)
        + tuple(f"AF__{sample}" for sample in sample_ids)
    )
    table = read_tsv(label, value, expected_header)
    step08.ensure_unique(table.rows, "candidate_id", label)
    sites_by_id = {row["candidate_id"]: row for row in step08_sites}
    metadata_columns = step08.STEP08_METADATA_HEADER
    sample_columns = tuple(
        f"{prefix}__{sample}" for prefix in ("DP", "AD", "AF") for sample in sample_ids
    )
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


def validate_step09_result_semantics(
    rows: Sequence[Mapping[str, str]],
    summary: Mapping[str, str],
    sample_rows: Sequence[Mapping[str, str]],
) -> None:
    target_ref, target_alt = summary["target_rna_change"].split(">")
    min_sample_dp = step08.parse_nonnegative_int(
        "Step 09 min_sample_dp", summary["min_sample_dp"]
    )
    mean_dp_threshold = step08.parse_number(
        "Step 09 mean_dp_threshold",
        summary["mean_dp_threshold"],
        nonnegative=True,
    )
    fdr_threshold = step08.parse_number(
        "Step 09 fdr_threshold", summary["fdr_threshold"], nonnegative=True
    )
    odds_threshold = step08.parse_number(
        "Step 09 common_or_threshold",
        summary["common_or_threshold"],
        nonnegative=True,
    )
    difference_threshold = step08.parse_number(
        "Step 09 absolute_difference_threshold",
        summary["absolute_difference_threshold"],
        nonnegative=True,
    )
    background_threshold = step08.parse_number(
        "Step 09 background_max_fraction",
        summary["background_max_fraction"],
        nonnegative=True,
    )
    if (
        min_sample_dp < 1
        or mean_dp_threshold is None
        or fdr_threshold is None
        or not 0 < fdr_threshold <= 1
        or odds_threshold is None
        or odds_threshold <= 1
        or difference_threshold is None
        or difference_threshold > 1
        or background_threshold is None
        or not 0 < background_threshold < 1
    ):
        step08.fail("Step 09 summary thresholds are outside the supported contract.")
    _, pairs = paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    analysis_samples = [sample_id for pair in pairs.values() for sample_id in pair]
    control_samples = [pair[0] for pair in pairs.values()]
    treatment_samples = [pair[1] for pair in pairs.values()]
    background_samples = [
        row["sample_id"]
        for row in sample_rows
        if row["condition"] == summary["background_condition"]
    ]
    tested_statistics: list[tuple[str, float, float]] = []
    for row in rows:
        is_target = row["rna_ref"] == target_ref and row["rna_alt"] == target_alt
        if is_target == (row["test_status"] == "not_target_change"):
            step08.fail(
                "Step 09 test_status does not match the declared target "
                f"change for candidate {row['candidate_id']}."
            )
        step08.validate_enum(
            "Step 09 background_status",
            row["background_status"],
            STEP09_BACKGROUND_STATUSES,
        )
        if summary["background_condition"] == NA_VALUE:
            if (
                row["background_status"] != "disabled"
                or row["max_background_af"] != NA_VALUE
            ):
                step08.fail(
                    "Step 09 background-disabled result contains a background claim."
                )
        else:
            background_dp = [row[f"DP__{sample}"] for sample in background_samples]
            background_ad = [row[f"AD__{sample}"] for sample in background_samples]
            background_missing = any(
                value == NA_VALUE for value in background_dp + background_ad
            )
            background_low = not background_missing and any(
                int(value) < min_sample_dp for value in background_dp
            )
            background_positive = not background_missing and all(
                int(value) > 0 for value in background_dp
            )
            background_af = (
                [
                    int(ad) / int(dp)
                    for dp, ad in zip(background_dp, background_ad, strict=True)
                ]
                if background_positive
                else []
            )
            if background_missing:
                expected_background_status = "missing_counts"
                expected_background_max = None
            elif background_low:
                expected_background_status = "low_coverage"
                expected_background_max = max(background_af) if background_af else None
            elif not background_af:
                step08.fail(
                    "Step 09 enabled background has zero depth at or above "
                    "the minimum depth threshold."
                )
            else:
                expected_background_max = max(background_af)
                expected_background_status = (
                    "pass"
                    if all(value < background_threshold for value in background_af)
                    else "fail_fraction"
                )
            observed_background_max = step08.parse_number(
                "Step 09 max_background_af",
                row["max_background_af"],
                allow_na=True,
                nonnegative=True,
            )
            if row[
                "background_status"
            ] != expected_background_status or not values_close(
                observed_background_max, expected_background_max
            ):
                step08.fail(
                    "Step 09 enabled-background status or maximum AF does "
                    f"not reconcile for candidate {row['candidate_id']}."
                )
        sample_dp = [row[f"DP__{sample}"] for sample in analysis_samples]
        sample_ad = [row[f"AD__{sample}"] for sample in analysis_samples]
        missing_counts = any(value == NA_VALUE for value in sample_dp + sample_ad)
        low_coverage = not missing_counts and any(
            int(value) < min_sample_dp for value in sample_dp
        )
        if missing_counts:
            for column in (
                "min_analysis_dp",
                "mean_analysis_dp",
                "mean_control_af",
                "mean_treatment_af",
                "treatment_control_difference",
            ):
                if row[column] != NA_VALUE:
                    step08.fail(
                        f"Step 09 {column} must be NA when analysis counts "
                        f"are missing for candidate {row['candidate_id']}."
                    )
        else:
            dp_values = [int(value) for value in sample_dp]
            observed_min_dp = step08.parse_number(
                "Step 09 min_analysis_dp",
                row["min_analysis_dp"],
                nonnegative=True,
            )
            observed_mean_dp = step08.parse_number(
                "Step 09 mean_analysis_dp",
                row["mean_analysis_dp"],
                nonnegative=True,
            )
            if not values_close(
                observed_min_dp, float(min(dp_values))
            ) or not values_close(
                observed_mean_dp,
                sum(dp_values) / len(dp_values),
            ):
                step08.fail(
                    "Step 09 depth metrics do not reconcile with immutable "
                    f"sample counts for candidate {row['candidate_id']}."
                )
            if all(value > 0 for value in dp_values):
                control_af_values = [
                    int(row[f"AD__{sample}"]) / int(row[f"DP__{sample}"])
                    for sample in control_samples
                ]
                treatment_af_values = [
                    int(row[f"AD__{sample}"]) / int(row[f"DP__{sample}"])
                    for sample in treatment_samples
                ]
                expected_control_af = sum(control_af_values) / len(control_af_values)
                expected_treatment_af = sum(treatment_af_values) / len(
                    treatment_af_values
                )
                expected_delta = expected_treatment_af - expected_control_af
                observed_control_af = step08.parse_number(
                    "Step 09 mean_control_af",
                    row["mean_control_af"],
                    nonnegative=True,
                )
                observed_treatment_af = step08.parse_number(
                    "Step 09 mean_treatment_af",
                    row["mean_treatment_af"],
                    nonnegative=True,
                )
                observed_delta = step08.parse_number(
                    "Step 09 treatment_control_difference",
                    row["treatment_control_difference"],
                )
                if (
                    not values_close(observed_control_af, expected_control_af)
                    or not values_close(observed_treatment_af, expected_treatment_af)
                    or not values_close(observed_delta, expected_delta)
                ):
                    step08.fail(
                        "Step 09 AF/delta metrics do not reconcile with "
                        "immutable sample counts for candidate "
                        f"{row['candidate_id']}."
                    )
            else:
                for column in (
                    "mean_control_af",
                    "mean_treatment_af",
                    "treatment_control_difference",
                ):
                    if row[column] != NA_VALUE:
                        step08.fail(
                            f"Step 09 {column} must be NA with zero analysis "
                            f"depth for candidate {row['candidate_id']}."
                        )
        if is_target:
            if missing_counts:
                expected_pretest_statuses = {"missing_counts"}
            elif low_coverage:
                expected_pretest_statuses = {"low_coverage"}
            else:
                expected_pretest_statuses = {"degenerate_table", "tested"}
            if row["test_status"] not in expected_pretest_statuses:
                step08.fail(
                    "Step 09 test_status conflicts with observed target "
                    "candidate count availability/coverage."
                )
        if row["test_status"] != "tested":
            if row["call_status"] != "not_tested":
                step08.fail(
                    "An untested Step 09 candidate must use call_status=not_tested."
                )
            for column in (
                "cmh_statistic",
                "cmh_degrees_freedom",
                "cmh_p_value",
                "cmh_fdr_bh",
                "common_odds_ratio",
            ):
                if row[column] != NA_VALUE:
                    step08.fail(
                        f"Untested Step 09 candidate {row['candidate_id']} "
                        f"must use {column}=NA."
                    )
            continue
        if row["call_status"] == "not_tested":
            step08.fail("A tested Step 09 candidate cannot use call_status=not_tested.")
        statistic = step08.parse_number(
            "Step 09 cmh_statistic", row["cmh_statistic"], nonnegative=True
        )
        degrees = step08.parse_number(
            "Step 09 cmh_degrees_freedom",
            row["cmh_degrees_freedom"],
            nonnegative=True,
        )
        p_value = step08.parse_number(
            "Step 09 cmh_p_value", row["cmh_p_value"], nonnegative=True
        )
        fdr = step08.parse_number(
            "Step 09 cmh_fdr_bh", row["cmh_fdr_bh"], nonnegative=True
        )
        odds = parse_nonnegative_or_infinite(
            "Step 09 common_odds_ratio", row["common_odds_ratio"]
        )
        mean_dp = step08.parse_number(
            "Step 09 mean_analysis_dp",
            row["mean_analysis_dp"],
            nonnegative=True,
        )
        control_af = step08.parse_number(
            "Step 09 mean_control_af",
            row["mean_control_af"],
            nonnegative=True,
        )
        treatment_af = step08.parse_number(
            "Step 09 mean_treatment_af",
            row["mean_treatment_af"],
            nonnegative=True,
        )
        delta = step08.parse_number(
            "Step 09 treatment_control_difference",
            row["treatment_control_difference"],
        )
        if (
            statistic is None
            or degrees != 1
            or p_value is None
            or p_value > 1
            or fdr is None
            or fdr > 1
            or mean_dp is None
            or control_af is None
            or control_af > 1
            or treatment_af is None
            or treatment_af > 1
            or delta is None
            or not values_close(delta, treatment_af - control_af)
        ):
            step08.fail("Step 09 tested-candidate statistics are malformed.")
        tested_statistics.append((row["candidate_id"], p_value, fdr))
        if mean_dp <= mean_dp_threshold:
            expected_call = "below_mean_dp"
        elif row["background_status"] not in ("disabled", "pass"):
            expected_call = "background_not_passed"
        elif fdr >= fdr_threshold:
            expected_call = "fdr_not_met"
        elif odds > odds_threshold and delta > difference_threshold:
            expected_call = "significant_up"
        elif odds < (1 / odds_threshold) and delta < -difference_threshold:
            expected_call = "significant_down"
        else:
            expected_call = "effect_not_met"
        if row["call_status"] != expected_call:
            step08.fail(
                "Step 09 call_status conflicts with the declared strict "
                f"thresholds for candidate {row['candidate_id']}."
            )
    if tested_statistics:
        p_values = [value[1] for value in tested_statistics]
        count = len(p_values)
        descending = sorted(
            range(count), key=lambda index: p_values[index], reverse=True
        )
        adjusted = [0.0] * count
        running = 1.0
        for rank, index in zip(range(count, 0, -1), descending, strict=True):
            running = min(running, count * p_values[index] / rank)
            adjusted[index] = min(1.0, running)
        for (candidate_id, p_value, observed), expected in zip(
            tested_statistics, adjusted, strict=True
        ):
            if observed < p_value or not values_close(observed, expected):
                step08.fail(
                    "Step 09 cmh_fdr_bh does not match global BH adjustment "
                    f"for candidate {candidate_id}."
                )


def validate_significant_subset(
    all_rows: Sequence[Mapping[str, str]],
    significant_rows: Sequence[Mapping[str, str]],
) -> None:
    expected = [
        row
        for row in all_rows
        if row["call_status"] in ("significant_up", "significant_down")
    ]
    if list(significant_rows) != expected:
        step08.fail(
            "Step 09 significant-sites table is not the exact ordered "
            "significant subset of all-sites."
        )


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
