"""Step 09 headers and controlled vocabularies."""

from __future__ import annotations

from norad.contracts.scientific_evidence import step08

NA_VALUE = step08.NA_VALUE

STEP09_RESULT_HEADER = (
    "analysis_id",
    *step08.STEP08_METADATA_HEADER,
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
