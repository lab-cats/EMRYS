"""Step 09 candidate, significance, and multiple-testing semantics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from norad.contracts.scientific_evidence import step08

from ._step09_definitions import NA_VALUE, STEP09_BACKGROUND_STATUSES
from ._step09_support import paired_samples, parse_nonnegative_or_infinite

values_close = step08.values_close


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
