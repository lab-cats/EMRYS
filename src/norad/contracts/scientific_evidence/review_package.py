"""Define the neutral public Step 09c review-package contract."""

from __future__ import annotations

from typing import Mapping, Sequence


SCIENCE_STATUSES = (
    "evidence_incomplete",
    "science_review_complete_exploratory",
)
RESERVED_SCIENCE_STATUS = "biological_interpretation_ready"
EVIDENCE_STATUSES = ("missing", "incomplete", "complete", "not_applicable")
ORIENTATION_STATUSES = ("provisional", "validated", "replacement_required")
IMPLEMENTATION_STATUSES = ("not_implemented", "implemented")
LOCAL_TEST_STATUSES = ("not_run", "passed", "failed")
RUNTIME_VALIDATION_STATUSES = ("not_run", "blocked", "passed", "failed")
CLUSTER_DRY_RUN_STATUSES = ("not_run", "passed", "failed")
CLUSTER_PROOF_STATUSES = ("not_run", "proven", "failed")
DECISION_STATUSES = ("pending", "recorded")
DECISION_DIMENSIONS = (
    "orientation",
    "annotation",
    "thresholds",
    "background",
    "matched_dna",
    "orthogonal_evidence",
    "adjudication",
)
RERUN_SCOPES = (
    "none",
    "step09",
    "steps08_09",
    "steps07_09",
    "upstream_impact_review",
    "manual_only",
)
REVIEW_PLAN_HEADER = (
    "review_id",
    "primary_analysis_id",
    "superseded_analysis_ids",
    "plan_version",
    "plan_date",
    "reviewer",
    "decision_owner",
    "git_commit",
    "overall_science_status",
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
    "orientation_policy",
    "orientation_policy_version",
    "orientation_status",
    "locus_selection_policy_version",
    "locus_selection_rule",
    "locus_target_count",
    "required_orientations",
    "required_annotation_strands",
    "required_annotation_cases",
    "candidate_selection_policy_version",
    "candidate_selection_rule",
    "top_up_count",
    "top_down_count",
    "discordant_count",
    "near_threshold_count",
    "sensitivity_policy_version",
    "sensitivity_rule",
    "sensitivity_analysis_ids",
    "leave_one_pair_out_rule",
    "background_policy_version",
    "annotation_policy_version",
    "adjudication_policy_version",
    "software_versions",
    "review_completed_date",
    "notes",
)
ORIENTATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "locus_id",
    "candidate_id",
    "partition_id",
    "orientation",
    "chromosome",
    "position",
    "transcript_id",
    "transcript_strand",
    "sample_id",
    "condition",
    "replicate",
    "flag_group",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "raw_dp",
    "raw_ad",
    "raw_ref_count",
    "current_expected_rna_ref",
    "current_expected_rna_alt",
    "inverted_expected_rna_ref",
    "inverted_expected_rna_alt",
    "concordance_status",
    "reviewer",
    "review_date",
    "detail",
)

ANNOTATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "audit_id",
    "candidate_id",
    "chromosome",
    "position",
    "orientation",
    "annotation_strand",
    "case_type",
    "observed_gene_ids",
    "observed_transcript_ids",
    "observed_is_cds",
    "observed_is_five_prime_utr",
    "observed_is_three_prime_utr",
    "observed_is_exon",
    "observed_is_intron",
    "expected_gene_ids",
    "expected_transcript_ids",
    "expected_is_cds",
    "expected_is_five_prime_utr",
    "expected_is_three_prime_utr",
    "expected_is_exon",
    "expected_is_intron",
    "assignment_status",
    "ambiguity_status",
    "reviewer",
    "review_date",
    "detail",
)

QC_FUNNEL_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "scope_type",
    "partition_id",
    "orientation",
    "step07_declared_vcf_records",
    "step08_observed_vcf_records",
    "step08_observed_alt_alleles",
    "step08_supported_snvs",
    "step08_skipped_symbolic",
    "step08_skipped_non_snv",
    "step08_published_candidates",
    "step09_candidates",
    "step09_target_candidates",
    "step09_tested",
    "step09_not_target",
    "step09_missing_counts",
    "step09_low_coverage",
    "step09_degenerate",
    "step09_below_mean_dp",
    "step09_background_not_passed",
    "step09_fdr_not_met",
    "step09_effect_not_met",
    "step09_significant_up",
    "step09_significant_down",
    "reconciliation_status",
    "detail",
)

REPLICATE_EFFECTS_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "candidate_id",
    "partition_id",
    "orientation",
    "replicate",
    "control_sample",
    "treatment_sample",
    "control_dp",
    "control_ad",
    "control_af",
    "treatment_dp",
    "treatment_ad",
    "treatment_af",
    "treatment_control_difference",
    "direction_status",
    "reviewer",
    "review_date",
    "detail",
)

SENSITIVITY_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "is_primary",
    "analysis_summary_path",
    "analysis_summary_sha256",
    "parameter_set_id",
    "min_sample_dp",
    "mean_dp_threshold",
    "fdr_threshold",
    "common_or_threshold",
    "absolute_difference_threshold",
    "background_condition",
    "background_max_fraction",
    "target_rna_change",
    "candidate_count",
    "successfully_tested_count",
    "significant_up_count",
    "significant_down_count",
    "comparison_status",
    "reviewer",
    "review_date",
    "detail",
)

LEAVE_ONE_OUT_HEADER = (
    "review_id",
    "evidence_id",
    "primary_analysis_id",
    "omitted_replicate",
    "analysis_id",
    "all_sites_path",
    "all_sites_sha256",
    "summary_path",
    "summary_sha256",
    "candidate_id",
    "primary_call_status",
    "leave_one_out_test_status",
    "leave_one_out_call_status",
    "primary_delta",
    "leave_one_out_delta",
    "primary_common_or",
    "leave_one_out_common_or",
    "primary_fdr",
    "leave_one_out_fdr",
    "direction_concordance",
    "reviewer",
    "review_date",
    "detail",
)

CANDIDATE_SELECTION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "selection_set",
    "rank",
    "candidate_id",
    "selection_policy_version",
    "selection_reason",
    "ranking_metric",
    "ranking_value",
    "source_call_status",
    "source_fdr",
    "source_common_or",
    "source_delta",
    "reviewer",
    "review_date",
)

CANDIDATE_ADJUDICATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "candidate_id",
    "selection_set",
    "adjudication_status",
    "coverage_status",
    "base_quality_status",
    "mapping_quality_status",
    "read_position_status",
    "splice_status",
    "repeat_multimapping_status",
    "duplicate_status",
    "nearby_indel_status",
    "annotation_status",
    "polymorphism_status",
    "matched_dna_status",
    "orthogonal_evidence_status",
    "reason",
    "supporting_evidence_ids",
    "reviewer",
    "review_date",
)

DECISIONS_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "decision_id",
    "decision_dimension",
    "evidence_status",
    "decision_status",
    "decision_value",
    "rationale",
    "supporting_evidence_ids",
    "decision_owner",
    "decision_date",
    "policy_version",
    "rerun_required",
    "rerun_scope",
)

LIMITATIONS_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "limitation_id",
    "limitation_category",
    "limitation_status",
    "severity",
    "description",
    "impact",
    "mitigation",
    "owner",
    "review_date",
    "related_evidence_ids",
)

CATEGORY_HEADERS: dict[str, tuple[str, ...]] = {
    "orientation_locus_audit": ORIENTATION_HEADER,
    "annotation_audit": ANNOTATION_HEADER,
    "qc_funnel": QC_FUNNEL_HEADER,
    "replicate_effects": REPLICATE_EFFECTS_HEADER,
    "sensitivity_matrix": SENSITIVITY_HEADER,
    "leave_one_pair_out": LEAVE_ONE_OUT_HEADER,
    "candidate_selection": CANDIDATE_SELECTION_HEADER,
    "candidate_adjudication": CANDIDATE_ADJUDICATION_HEADER,
    "decisions": DECISIONS_HEADER,
    "limitations": LIMITATIONS_HEADER,
}
CATEGORY_ORDER = tuple(CATEGORY_HEADERS)
ALLOWED_EVIDENCE_CATEGORIES = CATEGORY_ORDER + ("computational_validation",)

EVIDENCE_INDEX_HEADER = (
    "review_id",
    "evidence_id",
    "evidence_category",
    "analysis_id",
    "source_path",
    "declared_sha256",
    "observed_sha256",
    "declared_row_count",
    "observed_row_count",
    "evidence_status",
    "not_applicable_reason",
    "reviewer",
    "owner",
    "evidence_date",
    "policy_version",
)

OUTPUT_SUFFIXES = (
    ("review_plan", "step09c_review_plan.tsv"),
    ("evidence_index", "step09c_evidence_index.tsv"),
    ("orientation_locus_audit", "step09c_orientation_locus_audit.tsv"),
    ("annotation_audit", "step09c_annotation_audit.tsv"),
    ("qc_funnel", "step09c_qc_funnel.tsv"),
    ("replicate_effects", "step09c_replicate_effects.tsv"),
    ("sensitivity_matrix", "step09c_sensitivity_matrix.tsv"),
    ("leave_one_pair_out", "step09c_leave_one_pair_out.tsv"),
    ("candidate_selection", "step09c_candidate_selection.tsv"),
    ("candidate_adjudication", "step09c_candidate_adjudication.tsv"),
    ("decisions", "step09c_decisions.tsv"),
    ("limitations", "step09c_limitations.tsv"),
    ("review_summary", "step09c_review_summary.tsv"),
)

INPUT_ARTIFACT_KEYS = (
    "sample_manifest",
    "partition_manifest",
    "step08_sites",
    "step08_inputs",
    "step08_summary",
    "step09_all_sites",
    "step09_significant_sites",
    "step09_summary",
    "step09_mutation_spectrum",
    "step09_mutation_spectrum_pdf",
    "step09_depth_delta_pdf",
    "review_plan",
    "evidence_manifest",
)

REVIEW_SUMMARY_BASE_HEADER = (
    "review_id",
    "primary_analysis_id",
    "superseded_analysis_ids",
    "plan_version",
    "plan_date",
    "reviewer",
    "decision_owner",
    "git_commit",
    "overall_science_status",
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
    "orientation_policy",
    "orientation_policy_version",
    "orientation_status",
    "locus_selection_policy_version",
    "locus_selection_rule",
    "locus_target_count",
    "required_orientations",
    "required_annotation_strands",
    "required_annotation_cases",
    "candidate_selection_policy_version",
    "candidate_selection_rule",
    "top_up_count",
    "top_down_count",
    "discordant_count",
    "near_threshold_count",
    "sensitivity_policy_version",
    "sensitivity_rule",
    "sensitivity_analysis_ids",
    "leave_one_pair_out_rule",
    "background_policy_version",
    "annotation_policy_version",
    "adjudication_policy_version",
    "background_decision",
    "matched_dna_decision",
    "orthogonal_evidence_decision",
    "annotation_decision",
    "thresholds_decision",
    "adjudication_decision",
    "orientation_decision",
    "evidence_record_count",
    "evidence_source_count",
    "selected_candidate_count",
    "adjudicated_candidate_count",
    "limitation_count",
)
REVIEW_SUMMARY_EVIDENCE_HEADER = tuple(
    f"{category}_status" for category in CATEGORY_ORDER
)
REVIEW_SUMMARY_ARTIFACT_HEADER = tuple(
    field
    for key in INPUT_ARTIFACT_KEYS
    for field in (f"{key}_path", f"{key}_sha256", f"{key}_row_count")
)
REVIEW_SUMMARY_TRAILING_HEADER = (
    "step09_analysis_dir",
    "software_versions",
    "review_completed_date",
    "notes",
    "published_output_count",
    "transaction_state",
)
REVIEW_SUMMARY_HEADER = (
    REVIEW_SUMMARY_BASE_HEADER
    + REVIEW_SUMMARY_EVIDENCE_HEADER
    + REVIEW_SUMMARY_ARTIFACT_HEADER
    + REVIEW_SUMMARY_TRAILING_HEADER
)

CONCORDANCE_STATUSES = (
    "concordant",
    "discordant",
    "ambiguous",
    "not_assessable",
)
ANNOTATION_ASSIGNMENT_STATUSES = (
    "match",
    "mismatch",
    "ambiguous",
    "not_assessable",
)
ANNOTATION_AMBIGUITY_STATUSES = (
    "unambiguous",
    "ambiguous",
    "not_assessable",
)
ADJUDICATION_STATUSES = ("pass", "flag", "fail", "not_assessed")
AUDIT_COMPONENT_STATUSES = (
    "pass",
    "flag",
    "fail",
    "not_assessed",
    "unavailable",
    "not_applicable",
)


def aggregate_evidence_status(
    rows: Sequence[Mapping[str, str]], category: str
) -> str:
    category_rows = [
        row for row in rows if row["evidence_category"] == category
    ]
    if not category_rows:
        return "missing"
    statuses = [row["evidence_status"] for row in category_rows]
    if all(status == "missing" for status in statuses):
        return "missing"
    if any(status in ("missing", "incomplete") for status in statuses):
        return "incomplete"
    if all(status == "not_applicable" for status in statuses):
        return "not_applicable"
    return "complete"
