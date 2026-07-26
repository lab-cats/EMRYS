#!/usr/bin/env python3
"""Validate and publish an explicit Step 09c scientific-review evidence set.

This program is intentionally read-only with respect to Steps 08 and 09. It
does not run R, recompute CMH statistics, discover inputs by glob, or infer
reviewer decisions. Dry-run is the default. Execute mode publishes thirteen
validated TSV files as one rollback-protected transaction, with the review
summary written last as the commit marker.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class ContractError(RuntimeError):
    """Raised when an explicit scientific-review contract is invalid."""


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NA_VALUE = "NA"
ORIENTATIONS = ("FWD_like", "REV_like")
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

EVIDENCE_MANIFEST_HEADER = (
    "evidence_id",
    "evidence_category",
    "analysis_id",
    "source_path",
    "source_sha256",
    "source_row_count",
    "evidence_status",
    "not_applicable_reason",
    "reviewer",
    "owner",
    "evidence_date",
    "policy_version",
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

COMPUTATIONAL_VALIDATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "validation_scope",
    "validation_status",
    "evidence_path",
    "evidence_sha256",
    "scheduler_state",
    "exit_code",
    "reviewer",
    "evidence_date",
    "notes",
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

STEP08_METADATA_HEADER = (
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
)

STEP08_INPUTS_HEADER = (
    "cohort_id",
    "partition_id",
    "selector_type",
    "selector_value",
    "orientation",
    "step07_receipt_path",
    "step07_receipt_sha256",
    "vcf_path",
    "vcf_sha256",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "annotation_gtf",
    "annotation_gtf_sha256",
    "sample_count",
    "declared_vcf_record_count",
    "observed_vcf_record_count",
    "observed_alt_allele_count",
    "supported_snv_count",
    "skipped_symbolic_count",
    "skipped_non_snv_count",
    "published_candidate_count",
    "orientation_policy",
)

STEP08_SUMMARY_HEADER = (
    "cohort_id",
    "partition_count",
    "step07_receipt_count",
    "input_vcf_count",
    "sample_count",
    "observed_vcf_record_count",
    "observed_alt_allele_count",
    "supported_snv_count",
    "skipped_symbolic_count",
    "skipped_non_snv_count",
    "published_candidate_count",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "annotation_gtf",
    "annotation_gtf_sha256",
    "orientation_policy",
)

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

SAMPLE_MANIFEST_REQUIRED = (
    "sample_id",
    "r1_fastq",
    "r2_fastq",
    "strandedness",
    "condition",
    "replicate",
)
SAMPLE_MANIFEST_ALLOWED = SAMPLE_MANIFEST_REQUIRED + ("notes",)
PARTITION_MANIFEST_HEADER = (
    "partition_id",
    "selector_type",
    "selector_value",
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
COMPUTATIONAL_VALIDATION_STATUSES = (
    "not_run",
    "blocked",
    "passed",
    "failed",
    "proven",
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


@dataclass
class Table:
    header: tuple[str, ...]
    rows: list[dict[str, str]]
    path: Path


@dataclass
class Artifact:
    label: str
    path: Path
    sha256: str
    row_count: str


@dataclass
class ReviewContext:
    review_id: str
    plan: dict[str, str]
    evidence_rows: list[dict[str, str]]
    category_rows: dict[str, list[dict[str, str]]]
    evidence_index_rows: list[dict[str, str]]
    artifacts: dict[str, Artifact]
    input_hashes: dict[Path, str]
    sample_ids: list[str]
    sample_rows: list[dict[str, str]]
    partition_rows: list[dict[str, str]]
    step08_input_rows: list[dict[str, str]]
    step08_site_rows: list[dict[str, str]]
    step09_all_rows: list[dict[str, str]]
    step09_significant_rows: list[dict[str, str]]
    step09_summary: dict[str, str]
    output_paths: dict[str, Path]


def fail(message: str) -> None:
    raise ContractError(message)


def validate_safe_id(label: str, value: str) -> None:
    if not SAFE_ID_RE.fullmatch(value):
        fail(
            f"{label} must match [A-Za-z0-9][A-Za-z0-9._-]*; got: {value}"
        )


def validate_enum(label: str, value: str, allowed: Sequence[str]) -> None:
    if value not in allowed:
        fail(f"{label} must be one of {', '.join(allowed)}; got: {value}")


def validate_iso_date(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")
    if parsed.isoformat() != value:
        fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")


def parse_nonnegative_int(label: str, value: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        fail(f"{label} must be a non-negative integer; got: {value}")
    return int(value)


def parse_number(
    label: str, value: str, *, allow_na: bool = False, nonnegative: bool = False
) -> float | None:
    if allow_na and value == NA_VALUE:
        return None
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label} must be numeric; got: {value}")
    if not math.isfinite(parsed):
        fail(f"{label} must be finite; got: {value}")
    if nonnegative and parsed < 0:
        fail(f"{label} must be non-negative; got: {value}")
    return parsed


def parse_nonnegative_or_infinite(label: str, value: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label} must be numeric; got: {value}")
    if math.isnan(parsed) or parsed < 0:
        fail(f"{label} must be non-negative and not NaN; got: {value}")
    return parsed


def values_close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=1.5e-8, abs_tol=1.5e-8)


def complement_base(value: str) -> str:
    complements = {"A": "T", "C": "G", "G": "C", "T": "A"}
    if value not in complements:
        fail(f"Expected a canonical DNA base; got: {value}")
    return complements[value]


def split_ids(label: str, value: str) -> list[str]:
    if value == NA_VALUE:
        return []
    parts = value.split(",")
    if any(not part or part.strip() != part for part in parts):
        fail(f"{label} must be comma-separated safe IDs or NA; got: {value}")
    for part in parts:
        validate_safe_id(label, part)
    if len(parts) != len(set(parts)):
        fail(f"{label} contains duplicate IDs: {value}")
    return parts


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        fail(f"Could not hash {path}: {exc}")
    return digest.hexdigest()


def require_file(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        fail(f"{label} does not exist or is not a regular file: {path}")
    if path.stat().st_size == 0:
        fail(f"{label} is empty: {path}")
    return path.resolve()


def require_directory(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_dir():
        fail(f"{label} does not exist or is not a directory: {path}")
    return path.resolve()


def read_tsv(
    label: str,
    value: str | Path,
    expected_header: Sequence[str] | None = None,
) -> Table:
    path = require_file(label, value)
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            raw_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")
    if not raw_rows:
        fail(f"{label} is empty: {path}")
    header = tuple(raw_rows[0])
    if any(not column for column in header):
        fail(f"{label} contains an empty header field: {path}")
    if len(header) != len(set(header)):
        fail(f"{label} contains duplicate header fields: {path}")
    if expected_header is not None and header != tuple(expected_header):
        fail(
            f"{label} header is invalid: {path}\n"
            f"Expected: {' | '.join(expected_header)}\n"
            f"Observed: {' | '.join(header)}"
        )
    rows: list[dict[str, str]] = []
    for index, values in enumerate(raw_rows[1:], start=2):
        if len(values) != len(header):
            fail(
                f"{label} row {index} has {len(values)} fields; "
                f"expected {len(header)}: {path}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    return Table(header=header, rows=rows, path=path)


def write_tsv(path: Path, header: Sequence[str], rows: Iterable[Mapping[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def artifact_from_table(label: str, table: Table) -> Artifact:
    return Artifact(
        label=label,
        path=table.path,
        sha256=sha256_file(table.path),
        row_count=str(len(table.rows)),
    )


def artifact_from_binary(label: str, path: Path) -> Artifact:
    return Artifact(
        label=label,
        path=path,
        sha256=sha256_file(path),
        row_count=NA_VALUE,
    )


def ensure_unique(rows: Sequence[Mapping[str, str]], column: str, label: str) -> None:
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        value = row[column]
        if not value:
            fail(f"{label} row {row_number} has an empty {column}.")
        if value in seen:
            fail(f"{label} contains duplicate {column}: {value}")
        seen.add(value)


def resolve_declared_path(value: str, source_file: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = source_file.parent / path
    return path.resolve()


def resolve_recorded_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def validate_pdf(label: str, path: Path) -> None:
    path = require_file(label, path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"Could not read {label}: {exc}")
    if not data.startswith(b"%PDF-"):
        fail(f"{label} lacks a %PDF- signature: {path}")
    if b"%%EOF" not in data[-2048:]:
        fail(f"{label} lacks a trailing %%EOF marker: {path}")


def require_text(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    if not value or value.strip() != value:
        fail(f"{label} must be non-empty and have no surrounding whitespace.")


def validate_hash(label: str, value: str) -> None:
    if not SHA256_RE.fullmatch(value):
        fail(f"{label} must be a lowercase SHA-256 value; got: {value}")


def count_status(
    rows: Sequence[Mapping[str, str]], column: str, value: str
) -> int:
    return sum(row[column] == value for row in rows)


def register_artifact(
    artifacts: dict[str, Artifact],
    input_hashes: dict[Path, str],
    key: str,
    artifact: Artifact,
) -> None:
    if key in artifacts:
        fail(f"Internal artifact key was registered twice: {key}")
    artifacts[key] = artifact
    input_hashes[artifact.path] = artifact.sha256


def validate_sample_manifest(
    value: str | Path,
) -> tuple[Table, list[str], list[dict[str, str]]]:
    table = read_tsv("Sample manifest", value)
    if table.header not in (SAMPLE_MANIFEST_REQUIRED, SAMPLE_MANIFEST_ALLOWED):
        fail(
            "Sample manifest must have the exact Step 09 schema, with optional "
            "notes as the final column."
        )
    if not table.rows:
        fail("Sample manifest contains no sample rows.")
    ensure_unique(table.rows, "sample_id", "Sample manifest")
    for row_number, row in enumerate(table.rows, start=2):
        for column in SAMPLE_MANIFEST_REQUIRED:
            require_text(
                f"Sample manifest row {row_number} {column}", row[column]
            )
        validate_safe_id("sample_id", row["sample_id"])
        validate_safe_id("replicate", row["replicate"])
        if row["strandedness"] not in (
            "forward",
            "reverse",
            "unstranded",
            "unknown",
        ):
            fail(
                "Sample manifest row "
                f"{row_number} has invalid strandedness: {row['strandedness']}"
            )
    return table, [row["sample_id"] for row in table.rows], table.rows


def validate_partition_manifest(value: str | Path) -> Table:
    table = read_tsv(
        "Partition manifest", value, PARTITION_MANIFEST_HEADER
    )
    if not table.rows:
        fail("Partition manifest contains no partition rows.")
    ensure_unique(table.rows, "partition_id", "Partition manifest")
    for row_number, row in enumerate(table.rows, start=2):
        for column in PARTITION_MANIFEST_HEADER:
            require_text(
                f"Partition manifest row {row_number} {column}", row[column]
            )
        validate_safe_id("partition_id", row["partition_id"])
        validate_enum(
            f"Partition manifest row {row_number} selector_type",
            row["selector_type"],
            ("region", "regions_file"),
        )
    return table


def validate_step08_inputs(
    value: str | Path,
    sample_ids: Sequence[str],
    partitions: Sequence[Mapping[str, str]],
    sample_hash: str,
    partition_hash: str,
) -> Table:
    table = read_tsv("Step 08 input receipt", value, STEP08_INPUTS_HEADER)
    expected = [
        (partition, orientation)
        for partition in partitions
        for orientation in ORIENTATIONS
    ]
    if len(table.rows) != len(expected):
        fail(
            "Step 08 input receipt is not the complete declared partition "
            "x orientation set."
        )
    cohort_ids: set[str] = set()
    annotation_paths: set[str] = set()
    annotation_hashes: set[str] = set()
    for index, (row, (partition, orientation)) in enumerate(
        zip(table.rows, expected, strict=True), start=2
    ):
        if (
            row["partition_id"] != partition["partition_id"]
            or row["selector_type"] != partition["selector_type"]
            or row["selector_value"] != partition["selector_value"]
            or row["orientation"] != orientation
        ):
            fail(
                "Step 08 input receipt is not ordered as the declared "
                "partition x {FWD_like, REV_like} universe."
            )
        cohort_ids.add(row["cohort_id"])
        annotation_paths.add(row["annotation_gtf"])
        annotation_hashes.add(row["annotation_gtf_sha256"])
        require_text(f"Step 08 input receipt row {index} cohort_id", row["cohort_id"])
        validate_safe_id("cohort_id", row["cohort_id"])
        for path_column in ("step07_receipt_path", "vcf_path", "annotation_gtf"):
            require_text(
                f"Step 08 input receipt row {index} {path_column}",
                row[path_column],
            )
        for hash_column in (
            "step07_receipt_sha256",
            "vcf_sha256",
            "sample_manifest_sha256",
            "partition_manifest_sha256",
            "annotation_gtf_sha256",
        ):
            validate_hash(
                f"Step 08 input receipt row {index} {hash_column}",
                row[hash_column],
            )
        if row["sample_manifest_sha256"] != sample_hash:
            fail("Step 08 input receipt sample manifest hash is stale.")
        if row["partition_manifest_sha256"] != partition_hash:
            fail("Step 08 input receipt partition manifest hash is stale.")
        counts = {
            column: parse_nonnegative_int(
                f"Step 08 input receipt row {index} {column}", row[column]
            )
            for column in (
                "sample_count",
                "declared_vcf_record_count",
                "observed_vcf_record_count",
                "observed_alt_allele_count",
                "supported_snv_count",
                "skipped_symbolic_count",
                "skipped_non_snv_count",
                "published_candidate_count",
            )
        }
        if counts["sample_count"] != len(sample_ids):
            fail("Step 08 input receipt sample_count differs from the manifest.")
        if counts["declared_vcf_record_count"] != counts["observed_vcf_record_count"]:
            fail("Step 08 declared and observed VCF record counts differ.")
        if counts["observed_alt_allele_count"] != (
            counts["supported_snv_count"]
            + counts["skipped_symbolic_count"]
            + counts["skipped_non_snv_count"]
        ):
            fail("Step 08 alternate-allele counts do not reconcile.")
        if counts["published_candidate_count"] != counts["supported_snv_count"]:
            fail("Step 08 published and supported SNV counts do not reconcile.")
        require_text(
            f"Step 08 input receipt row {index} orientation_policy",
            row["orientation_policy"],
        )
    if len(cohort_ids) != 1:
        fail("Step 08 input receipt contains multiple cohort IDs.")
    if len(annotation_paths) != 1 or len(annotation_hashes) != 1:
        fail("Step 08 input receipt contains inconsistent annotation provenance.")
    if len({row["orientation_policy"] for row in table.rows}) != 1:
        fail("Step 08 input receipt contains multiple orientation policies.")
    return table


def validate_step08_sites(
    value: str | Path,
    sample_ids: Sequence[str],
    partitions: Sequence[Mapping[str, str]],
    step08_inputs: Sequence[Mapping[str, str]],
) -> Table:
    expected_header = (
        STEP08_METADATA_HEADER
        + tuple(f"DP__{sample}" for sample in sample_ids)
        + tuple(f"AD__{sample}" for sample in sample_ids)
        + tuple(f"AF__{sample}" for sample in sample_ids)
    )
    table = read_tsv("Step 08 sites table", value, expected_header)
    ensure_unique(table.rows, "candidate_id", "Step 08 sites table")
    partition_ids = {row["partition_id"] for row in partitions}
    policies = {row["orientation_policy"] for row in step08_inputs}
    published_by_scope = {
        (row["partition_id"], row["orientation"]): parse_nonnegative_int(
            "Step 08 published_candidate_count",
            row["published_candidate_count"],
        )
        for row in step08_inputs
    }
    observed_by_scope = {key: 0 for key in published_by_scope}
    for row_number, row in enumerate(table.rows, start=2):
        require_text(
            f"Step 08 sites row {row_number} candidate_id",
            row["candidate_id"],
        )
        if row["partition_id"] not in partition_ids:
            fail(
                f"Step 08 sites row {row_number} references an unknown partition."
            )
        validate_enum(
            f"Step 08 sites row {row_number} orientation",
            row["orientation"],
            ORIENTATIONS,
        )
        scope = (row["partition_id"], row["orientation"])
        observed_by_scope[scope] += 1
        if row["orientation_policy"] not in policies:
            fail("Step 08 sites table orientation policy differs from its receipt.")
        parse_nonnegative_int(
            f"Step 08 sites row {row_number} position", row["position"]
        )
        alt_index = parse_nonnegative_int(
            f"Step 08 sites row {row_number} alt_index", row["alt_index"]
        )
        if alt_index < 1:
            fail("Step 08 alt_index must be at least 1.")
        for sample in sample_ids:
            dp_value = row[f"DP__{sample}"]
            ad_value = row[f"AD__{sample}"]
            dp = (
                None
                if dp_value == NA_VALUE
                else parse_nonnegative_int(
                    f"Step 08 sites row {row_number} DP__{sample}",
                    dp_value,
                )
            )
            ad = (
                None
                if ad_value == NA_VALUE
                else parse_nonnegative_int(
                    f"Step 08 sites row {row_number} AD__{sample}",
                    ad_value,
                )
            )
            af = parse_number(
                f"Step 08 sites row {row_number} AF__{sample}",
                row[f"AF__{sample}"],
                allow_na=True,
                nonnegative=True,
            )
            if (dp is None) != (ad is None):
                fail(
                    f"Step 08 sites row {row_number} has one-sided DP/AD "
                    f"missingness for sample {sample}."
                )
            if dp is None:
                if af is not None:
                    fail(
                        f"Step 08 sites row {row_number} has AF without "
                        f"DP/AD for sample {sample}."
                    )
                continue
            assert ad is not None
            if ad > dp or (af is not None and af > 1):
                fail(
                    f"Step 08 sites row {row_number} has inconsistent counts "
                    f"for sample {sample}."
                )
            if dp == 0:
                if ad != 0 or af is not None:
                    fail(
                        f"Step 08 sites row {row_number} has invalid zero-depth "
                        f"counts for sample {sample}."
                    )
                continue
            if af is None or not values_close(af, ad / dp):
                fail(
                    f"Step 08 sites row {row_number} AF__{sample} does not "
                    "equal AD/DP."
                )
    if observed_by_scope != published_by_scope:
        fail(
            "Step 08 sites counts do not reconcile by partition and orientation."
        )
    return table


def validate_step08_summary(
    value: str | Path,
    sample_ids: Sequence[str],
    partitions: Sequence[Mapping[str, str]],
    step08_inputs: Sequence[Mapping[str, str]],
    step08_sites: Sequence[Mapping[str, str]],
    sample_hash: str,
    partition_hash: str,
) -> Table:
    table = read_tsv("Step 08 summary", value, STEP08_SUMMARY_HEADER)
    if len(table.rows) != 1:
        fail("Step 08 summary must contain exactly one data row.")
    row = table.rows[0]
    if row["sample_manifest_sha256"] != sample_hash:
        fail("Step 08 summary sample manifest hash is stale.")
    if row["partition_manifest_sha256"] != partition_hash:
        fail("Step 08 summary partition manifest hash is stale.")
    expected_counts = {
        "partition_count": len(partitions),
        "step07_receipt_count": len(partitions),
        "input_vcf_count": len(step08_inputs),
        "sample_count": len(sample_ids),
        "published_candidate_count": len(step08_sites),
    }
    aggregate_columns = (
        "observed_vcf_record_count",
        "observed_alt_allele_count",
        "supported_snv_count",
        "skipped_symbolic_count",
        "skipped_non_snv_count",
    )
    for column in aggregate_columns:
        expected_counts[column] = sum(
            parse_nonnegative_int(
                f"Step 08 input receipt {column}", input_row[column]
            )
            for input_row in step08_inputs
        )
    for column, expected in expected_counts.items():
        if parse_nonnegative_int(f"Step 08 summary {column}", row[column]) != expected:
            fail(f"Step 08 summary {column} does not reconcile.")
    first = step08_inputs[0]
    for column in (
        "cohort_id",
        "annotation_gtf",
        "annotation_gtf_sha256",
        "orientation_policy",
    ):
        if row[column] != first[column]:
            fail(f"Step 08 summary {column} differs from the input receipt.")
    return table


def paired_samples(
    sample_rows: Sequence[Mapping[str, str]],
    control: str,
    treatment: str,
) -> tuple[list[str], dict[str, tuple[str, str]]]:
    if control == treatment:
        fail("Step 09 control and treatment conditions must differ.")
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
            fail(
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
        fail(
            "Sample manifest must define identical control/treatment replicate "
            "sets with at least two strata."
        )
    return replicates, pairs


def step09_paths(analysis_dir: Path, analysis_id: str) -> dict[str, Path]:
    return {
        "step09_all_sites": analysis_dir / f"{analysis_id}.cmh_all_sites.tsv",
        "step09_significant_sites": (
            analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        "step09_summary": analysis_dir / f"{analysis_id}.cmh_summary.tsv",
        "step09_mutation_spectrum": (
            analysis_dir / f"{analysis_id}.mutation_spectrum.tsv"
        ),
        "step09_mutation_spectrum_pdf": (
            analysis_dir / f"{analysis_id}.mutation_spectrum.pdf"
        ),
        "step09_depth_delta_pdf": (
            analysis_dir / f"{analysis_id}.depth_delta.pdf"
        ),
    }


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
    ensure_unique(table.rows, "candidate_id", label)
    sites_by_id = {row["candidate_id"]: row for row in step08_sites}
    metadata_columns = STEP08_METADATA_HEADER
    sample_columns = tuple(
        f"{prefix}__{sample}"
        for prefix in ("DP", "AD", "AF")
        for sample in sample_ids
    )
    for row_number, row in enumerate(table.rows, start=2):
        if row["analysis_id"] != analysis_id:
            fail(f"{label} row {row_number} has the wrong analysis_id.")
        site = sites_by_id.get(row["candidate_id"])
        if site is None:
            fail(f"{label} references an unknown Step 08 candidate.")
        for column in metadata_columns + sample_columns:
            if row[column] != site[column]:
                fail(
                    f"{label} row {row_number} {column} differs from "
                    "the Step 08 candidate."
                )
        validate_enum(
            f"{label} row {row_number} test_status",
            row["test_status"],
            STEP09_TEST_STATUSES,
        )
        validate_enum(
            f"{label} row {row_number} call_status",
            row["call_status"],
            STEP09_CALL_STATUSES,
        )
        parse_nonnegative_int(
            f"{label} row {row_number} replicate_count",
            row["replicate_count"],
        )
    return table


def validate_step09_summary(
    value: str | Path,
    analysis_id: str,
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
    table = read_tsv("Step 09 summary", value, STEP09_SUMMARY_HEADER)
    if len(table.rows) != 1:
        fail("Step 09 summary must contain exactly one data row.")
    row = table.rows[0]
    if row["analysis_id"] != analysis_id:
        fail("Step 09 summary analysis_id differs from its directory.")
    if (
        row["multiple_testing_method"] != "BH"
        or row["cmh_alternative"] != "two.sided"
        or row["continuity_correction"] != "TRUE"
    ):
        fail("Step 09 summary does not declare the approved CMH contract.")
    expected_paths = {
        "sample_manifest_path": sample_manifest,
        "partition_manifest_path": partition_manifest,
        "step08_sites_path": step08_sites,
        "step08_inputs_path": step08_inputs,
    }
    for column, expected in expected_paths.items():
        if resolve_recorded_path(row[column]) != expected:
            fail(f"Step 09 summary {column} differs from the explicit input.")
    expected_hashes = {
        "sample_manifest_sha256": sample_hash,
        "partition_manifest_sha256": partition_hash,
        "step08_sites_sha256": sites_hash,
        "step08_inputs_sha256": inputs_hash,
    }
    for column, expected in expected_hashes.items():
        validate_hash(f"Step 09 summary {column}", row[column])
        if row[column] != expected:
            fail(f"Step 09 summary {column} is stale.")
    if parse_nonnegative_int(
        "Step 09 summary sample_count", row["sample_count"]
    ) != len(sample_ids):
        fail("Step 09 summary sample_count differs from the sample manifest.")
    if parse_nonnegative_int(
        "Step 09 summary candidate_count", row["candidate_count"]
    ) != len(all_rows):
        fail("Step 09 summary candidate_count differs from all-sites.")
    target_change = row["target_rna_change"]
    if not re.fullmatch(r"[ACGT]>[ACGT]", target_change):
        fail("Step 09 summary target_rna_change must be a canonical SNV.")
    target_ref, target_alt = target_change.split(">")
    expected_target_count = sum(
        result["rna_ref"] == target_ref and result["rna_alt"] == target_alt
        for result in all_rows
    )
    if parse_nonnegative_int(
        "Step 09 summary target_candidate_count",
        row["target_candidate_count"],
    ) != expected_target_count:
        fail("Step 09 summary target candidate count does not reconcile.")
    for summary_column, result_column, status in STEP09_STATUS_COUNT_FIELDS:
        expected = count_status(all_rows, result_column, status)
        if parse_nonnegative_int(
            f"Step 09 summary {summary_column}", row[summary_column]
        ) != expected:
            fail(f"Step 09 summary {summary_column} does not reconcile.")
    replicates, _ = paired_samples(
        sample_rows, row["control_condition"], row["treatment_condition"]
    )
    if parse_nonnegative_int(
        "Step 09 summary replicate_count", row["replicate_count"]
    ) != len(replicates):
        fail("Step 09 summary replicate_count differs from the sample manifest.")
    if row["orientation_policy"] != step08_orientation_policy:
        fail("Step 09 summary orientation policy differs from Step 08.")
    if any(result["orientation_policy"] != row["orientation_policy"] for result in all_rows):
        fail("Step 09 results contain an inconsistent orientation policy.")
    background = row["background_condition"]
    if background != NA_VALUE:
        if background in (row["control_condition"], row["treatment_condition"]):
            fail("Step 09 background condition must be independent.")
        if not any(sample["condition"] == background for sample in sample_rows):
            fail("Step 09 background condition is absent from the manifest.")
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
                fail(
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
    min_sample_dp = parse_nonnegative_int(
        "Step 09 min_sample_dp", summary["min_sample_dp"]
    )
    mean_dp_threshold = parse_number(
        "Step 09 mean_dp_threshold",
        summary["mean_dp_threshold"],
        nonnegative=True,
    )
    fdr_threshold = parse_number(
        "Step 09 fdr_threshold", summary["fdr_threshold"], nonnegative=True
    )
    odds_threshold = parse_number(
        "Step 09 common_or_threshold",
        summary["common_or_threshold"],
        nonnegative=True,
    )
    difference_threshold = parse_number(
        "Step 09 absolute_difference_threshold",
        summary["absolute_difference_threshold"],
        nonnegative=True,
    )
    if (
        mean_dp_threshold is None
        or fdr_threshold is None
        or not 0 < fdr_threshold <= 1
        or odds_threshold is None
        or odds_threshold <= 1
        or difference_threshold is None
    ):
        fail("Step 09 summary thresholds are outside the supported contract.")
    _, pairs = paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    analysis_samples = [
        sample_id for pair in pairs.values() for sample_id in pair
    ]
    control_samples = [pair[0] for pair in pairs.values()]
    treatment_samples = [pair[1] for pair in pairs.values()]
    for row in rows:
        is_target = (
            row["rna_ref"] == target_ref and row["rna_alt"] == target_alt
        )
        if is_target == (row["test_status"] == "not_target_change"):
            fail(
                "Step 09 test_status does not match the declared target "
                f"change for candidate {row['candidate_id']}."
            )
        validate_enum(
            "Step 09 background_status",
            row["background_status"],
            STEP09_BACKGROUND_STATUSES,
        )
        if summary["background_condition"] == NA_VALUE:
            if (
                row["background_status"] != "disabled"
                or row["max_background_af"] != NA_VALUE
            ):
                fail(
                    "Step 09 background-disabled result contains a "
                    "background claim."
                )
        sample_dp = [row[f"DP__{sample}"] for sample in analysis_samples]
        sample_ad = [row[f"AD__{sample}"] for sample in analysis_samples]
        missing_counts = any(
            value == NA_VALUE for value in sample_dp + sample_ad
        )
        low_coverage = (
            not missing_counts
            and any(int(value) < min_sample_dp for value in sample_dp)
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
                    fail(
                        f"Step 09 {column} must be NA when analysis counts "
                        f"are missing for candidate {row['candidate_id']}."
                    )
        else:
            dp_values = [int(value) for value in sample_dp]
            observed_min_dp = parse_number(
                "Step 09 min_analysis_dp",
                row["min_analysis_dp"],
                nonnegative=True,
            )
            observed_mean_dp = parse_number(
                "Step 09 mean_analysis_dp",
                row["mean_analysis_dp"],
                nonnegative=True,
            )
            if (
                not values_close(observed_min_dp, float(min(dp_values)))
                or not values_close(
                    observed_mean_dp,
                    sum(dp_values) / len(dp_values),
                )
            ):
                fail(
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
                expected_control_af = sum(control_af_values) / len(
                    control_af_values
                )
                expected_treatment_af = sum(treatment_af_values) / len(
                    treatment_af_values
                )
                expected_delta = expected_treatment_af - expected_control_af
                observed_control_af = parse_number(
                    "Step 09 mean_control_af",
                    row["mean_control_af"],
                    nonnegative=True,
                )
                observed_treatment_af = parse_number(
                    "Step 09 mean_treatment_af",
                    row["mean_treatment_af"],
                    nonnegative=True,
                )
                observed_delta = parse_number(
                    "Step 09 treatment_control_difference",
                    row["treatment_control_difference"],
                )
                if (
                    not values_close(observed_control_af, expected_control_af)
                    or not values_close(
                        observed_treatment_af, expected_treatment_af
                    )
                    or not values_close(observed_delta, expected_delta)
                ):
                    fail(
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
                        fail(
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
                fail(
                    "Step 09 test_status conflicts with observed target "
                    "candidate count availability/coverage."
                )
        if row["test_status"] != "tested":
            if row["call_status"] != "not_tested":
                fail(
                    "An untested Step 09 candidate must use "
                    "call_status=not_tested."
                )
            for column in (
                "cmh_statistic",
                "cmh_degrees_freedom",
                "cmh_p_value",
                "cmh_fdr_bh",
                "common_odds_ratio",
            ):
                if row[column] != NA_VALUE:
                    fail(
                        f"Untested Step 09 candidate {row['candidate_id']} "
                        f"must use {column}=NA."
                    )
            continue
        if row["call_status"] == "not_tested":
            fail("A tested Step 09 candidate cannot use call_status=not_tested.")
        statistic = parse_number(
            "Step 09 cmh_statistic", row["cmh_statistic"], nonnegative=True
        )
        degrees = parse_number(
            "Step 09 cmh_degrees_freedom",
            row["cmh_degrees_freedom"],
            nonnegative=True,
        )
        p_value = parse_number(
            "Step 09 cmh_p_value", row["cmh_p_value"], nonnegative=True
        )
        fdr = parse_number(
            "Step 09 cmh_fdr_bh", row["cmh_fdr_bh"], nonnegative=True
        )
        odds = parse_nonnegative_or_infinite(
            "Step 09 common_odds_ratio", row["common_odds_ratio"]
        )
        mean_dp = parse_number(
            "Step 09 mean_analysis_dp",
            row["mean_analysis_dp"],
            nonnegative=True,
        )
        control_af = parse_number(
            "Step 09 mean_control_af",
            row["mean_control_af"],
            nonnegative=True,
        )
        treatment_af = parse_number(
            "Step 09 mean_treatment_af",
            row["mean_treatment_af"],
            nonnegative=True,
        )
        delta = parse_number(
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
            fail("Step 09 tested-candidate statistics are malformed.")
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
            fail(
                "Step 09 call_status conflicts with the declared strict "
                f"thresholds for candidate {row['candidate_id']}."
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
        fail(
            "Step 09 significant-sites table is not the exact ordered "
            "significant subset of all-sites."
        )


def validate_mutation_spectrum(
    value: str | Path,
    analysis_id: str,
    all_rows: Sequence[Mapping[str, str]],
) -> Table:
    table = read_tsv(
        "Step 09 mutation spectrum", value, STEP09_MUTATION_HEADER
    )
    if [row["mutation_type"] for row in table.rows] != list(CANONICAL_MUTATIONS):
        fail("Step 09 mutation spectrum must contain the canonical 12 SNVs.")
    total = len(all_rows)
    for row in table.rows:
        mutation_type = row["mutation_type"]
        ref, alt = mutation_type.split(">")
        if (
            row["analysis_id"] != analysis_id
            or row["rna_ref"] != ref
            or row["rna_alt"] != alt
        ):
            fail("Step 09 mutation spectrum identity columns do not reconcile.")
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
            if parse_nonnegative_int(
                f"Step 09 mutation spectrum {column}", row[column]
            ) != expected:
                fail(f"Step 09 mutation spectrum {column} does not reconcile.")
        fraction = parse_number(
            "Step 09 mutation spectrum candidate_fraction",
            row["candidate_fraction"],
            nonnegative=True,
        )
        expected_fraction = 0.0 if total == 0 else len(selected) / total
        if fraction is None or fraction > 1 or not values_close(
            fraction, expected_fraction
        ):
            fail("Step 09 mutation spectrum candidate_fraction is invalid.")
    return table


def validate_review_plan(
    value: str | Path, review_id: str
) -> tuple[Table, dict[str, str], set[str]]:
    table = read_tsv("Scientific review plan", value, REVIEW_PLAN_HEADER)
    if len(table.rows) != 1:
        fail("Scientific review plan must contain exactly one data row.")
    plan = table.rows[0]
    if plan["review_id"] != review_id:
        fail("Scientific review plan review_id differs from --review-id.")
    validate_safe_id("review_id", plan["review_id"])
    validate_safe_id("primary_analysis_id", plan["primary_analysis_id"])
    requested_status = plan["overall_science_status"]
    if requested_status == RESERVED_SCIENCE_STATUS:
        fail(
            "biological_interpretation_ready is reserved and cannot be "
            "produced by Step 09c."
        )
    validate_enum(
        "overall_science_status", requested_status, SCIENCE_STATUSES
    )
    validate_enum(
        "implementation_status",
        plan["implementation_status"],
        IMPLEMENTATION_STATUSES,
    )
    validate_enum(
        "local_test_status", plan["local_test_status"], LOCAL_TEST_STATUSES
    )
    validate_enum(
        "runtime_validation_status",
        plan["runtime_validation_status"],
        RUNTIME_VALIDATION_STATUSES,
    )
    validate_enum(
        "cluster_dry_run_status",
        plan["cluster_dry_run_status"],
        CLUSTER_DRY_RUN_STATUSES,
    )
    validate_enum(
        "cluster_proof_status",
        plan["cluster_proof_status"],
        CLUSTER_PROOF_STATUSES,
    )
    validate_enum(
        "orientation_status",
        plan["orientation_status"],
        ORIENTATION_STATUSES,
    )
    validate_iso_date("plan_date", plan["plan_date"])
    validate_iso_date(
        "review_completed_date",
        plan["review_completed_date"],
        allow_na=True,
    )
    for column in (
        "plan_version",
        "reviewer",
        "decision_owner",
        "git_commit",
        "orientation_policy",
        "orientation_policy_version",
        "locus_selection_policy_version",
        "locus_selection_rule",
        "candidate_selection_policy_version",
        "candidate_selection_rule",
        "sensitivity_policy_version",
        "sensitivity_rule",
        "leave_one_pair_out_rule",
        "background_policy_version",
        "annotation_policy_version",
        "adjudication_policy_version",
        "software_versions",
        "notes",
    ):
        require_text(f"Scientific review plan {column}", plan[column])
    for column in (
        "locus_target_count",
        "top_up_count",
        "top_down_count",
        "discordant_count",
        "near_threshold_count",
    ):
        parse_nonnegative_int(f"Scientific review plan {column}", plan[column])
    required_orientations = split_ids(
        "required_orientations", plan["required_orientations"]
    )
    if required_orientations != list(ORIENTATIONS):
        fail(
            "required_orientations must be exactly "
            "FWD_like,REV_like in that order."
        )
    required_strands = plan["required_annotation_strands"].split(",")
    if required_strands != ["+", "-"]:
        fail("required_annotation_strands must be exactly +,-.")
    require_text(
        "required_annotation_cases", plan["required_annotation_cases"]
    )
    superseded = split_ids(
        "superseded_analysis_ids", plan["superseded_analysis_ids"]
    )
    sensitivity = split_ids(
        "sensitivity_analysis_ids", plan["sensitivity_analysis_ids"]
    )
    if plan["primary_analysis_id"] in superseded + sensitivity:
        fail("The primary analysis cannot also be superseded or a sensitivity run.")
    allowed_analyses = {
        plan["primary_analysis_id"],
        *superseded,
        *sensitivity,
    }
    if plan["cluster_proof_status"] == "proven" and (
        plan["runtime_validation_status"] != "passed"
        or plan["cluster_dry_run_status"] != "passed"
    ):
        fail(
            "cluster_proof_status=proven requires runtime and cluster "
            "dry-run status passed."
        )
    if requested_status == "science_review_complete_exploratory":
        if plan["review_completed_date"] == NA_VALUE:
            fail(
                "An exploratory-complete science review requires "
                "review_completed_date."
            )
    elif plan["review_completed_date"] != NA_VALUE:
        fail(
            "evidence_incomplete must use review_completed_date=NA so that "
            "review completion is not overstated."
        )
    return table, plan, allowed_analyses


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


def validate_evidence_manifest(
    value: str | Path,
    review_id: str,
    allowed_analyses: set[str],
    input_hashes: dict[Path, str],
) -> tuple[
    Table,
    list[dict[str, str]],
    dict[str, list[dict[str, str]]],
    list[dict[str, str]],
]:
    manifest = read_tsv(
        "Scientific evidence manifest", value, EVIDENCE_MANIFEST_HEADER
    )
    ensure_unique(manifest.rows, "evidence_id", "Scientific evidence manifest")
    for category in CATEGORY_ORDER:
        if not any(
            row["evidence_category"] == category for row in manifest.rows
        ):
            fail(
                "Scientific evidence manifest must explicitly represent "
                f"category {category}."
            )
    source_paths: set[Path] = set()
    payload_by_category = {
        category: [] for category in ALLOWED_EVIDENCE_CATEGORIES
    }
    evidence_index_rows: list[dict[str, str]] = []
    evidence_order = {category: index for index, category in enumerate(
        ALLOWED_EVIDENCE_CATEGORIES
    )}
    normalized_manifest_rows: list[dict[str, str]] = []
    for row_number, original in enumerate(manifest.rows, start=2):
        row = dict(original)
        validate_safe_id("evidence_id", row["evidence_id"])
        validate_enum(
            f"Evidence manifest row {row_number} category",
            row["evidence_category"],
            ALLOWED_EVIDENCE_CATEGORIES,
        )
        validate_enum(
            f"Evidence manifest row {row_number} status",
            row["evidence_status"],
            EVIDENCE_STATUSES,
        )
        if row["analysis_id"] not in allowed_analyses:
            fail(
                f"Evidence manifest row {row_number} references undeclared "
                f"analysis_id {row['analysis_id']}."
            )
        for column in ("reviewer", "owner", "policy_version"):
            require_text(
                f"Evidence manifest row {row_number} {column}", row[column]
            )
        validate_iso_date(
            f"Evidence manifest row {row_number} evidence_date",
            row["evidence_date"],
            allow_na=True,
        )
        status = row["evidence_status"]
        if status in ("missing", "not_applicable"):
            if any(
                row[column] != NA_VALUE
                for column in (
                    "source_path",
                    "source_sha256",
                    "source_row_count",
                )
            ):
                fail(
                    f"Evidence {row['evidence_id']} with status {status} "
                    "must use NA for source path, hash, and row count."
                )
            if status == "not_applicable":
                require_text(
                    f"Evidence {row['evidence_id']} not_applicable_reason",
                    row["not_applicable_reason"],
                )
            elif row["not_applicable_reason"] != NA_VALUE:
                fail(
                    "Missing evidence must use not_applicable_reason=NA."
                )
            observed_path = NA_VALUE
            observed_hash = NA_VALUE
            observed_count = NA_VALUE
        else:
            if row["not_applicable_reason"] != NA_VALUE:
                fail(
                    "Complete or incomplete evidence must use "
                    "not_applicable_reason=NA."
                )
            source_path = resolve_declared_path(
                row["source_path"], manifest.path
            )
            source_path = require_file(
                f"Evidence source {row['evidence_id']}", source_path
            )
            if source_path in source_paths:
                fail(
                    "Scientific evidence manifest declares the same source "
                    f"path more than once: {source_path}"
                )
            source_paths.add(source_path)
            validate_hash(
                f"Evidence {row['evidence_id']} source_sha256",
                row["source_sha256"],
            )
            observed_hash = sha256_file(source_path)
            if observed_hash != row["source_sha256"]:
                fail(
                    f"Evidence source hash differs for {row['evidence_id']}."
                )
            expected_header = (
                COMPUTATIONAL_VALIDATION_HEADER
                if row["evidence_category"] == "computational_validation"
                else CATEGORY_HEADERS[row["evidence_category"]]
            )
            source_table = read_tsv(
                f"Evidence source {row['evidence_id']}",
                source_path,
                expected_header,
            )
            declared_count = parse_nonnegative_int(
                f"Evidence {row['evidence_id']} source_row_count",
                row["source_row_count"],
            )
            if declared_count != len(source_table.rows):
                fail(
                    f"Evidence source row count differs for "
                    f"{row['evidence_id']}."
                )
            for source_row_number, payload in enumerate(
                source_table.rows, start=2
            ):
                if payload["review_id"] != review_id:
                    fail(
                        f"Evidence {row['evidence_id']} payload row "
                        f"{source_row_number} has the wrong review_id."
                    )
                if payload["evidence_id"] != row["evidence_id"]:
                    fail(
                        f"Evidence {row['evidence_id']} payload row "
                        f"{source_row_number} has the wrong evidence_id."
                    )
                if (
                    row["evidence_category"] != "leave_one_pair_out"
                    and payload["analysis_id"] not in allowed_analyses
                ):
                    fail(
                        f"Evidence {row['evidence_id']} payload references "
                        "an undeclared analysis."
                    )
                if row["evidence_category"] == "leave_one_pair_out":
                    validate_safe_id(
                        "leave-one-pair-out analysis_id",
                        payload["analysis_id"],
                    )
            if row["evidence_category"] in payload_by_category:
                payload_by_category[row["evidence_category"]].extend(
                    source_table.rows
                )
            input_hashes[source_path] = observed_hash
            observed_path = str(source_path)
            observed_count = str(len(source_table.rows))
        normalized_manifest_rows.append(row)
        evidence_index_rows.append(
            {
                "review_id": review_id,
                "evidence_id": row["evidence_id"],
                "evidence_category": row["evidence_category"],
                "analysis_id": row["analysis_id"],
                "source_path": observed_path,
                "declared_sha256": row["source_sha256"],
                "observed_sha256": observed_hash,
                "declared_row_count": row["source_row_count"],
                "observed_row_count": observed_count,
                "evidence_status": status,
                "not_applicable_reason": row["not_applicable_reason"],
                "reviewer": row["reviewer"],
                "owner": row["owner"],
                "evidence_date": row["evidence_date"],
                "policy_version": row["policy_version"],
            }
        )
    sort_key = lambda item: (
        evidence_order[item["evidence_category"]],
        item["evidence_id"],
    )
    normalized_manifest_rows.sort(key=sort_key)
    evidence_index_rows.sort(key=sort_key)
    return (
        manifest,
        normalized_manifest_rows,
        payload_by_category,
        evidence_index_rows,
    )


def validate_supporting_ids(
    label: str, value: str, evidence_ids: set[str]
) -> None:
    for evidence_id in split_ids(label, value):
        if evidence_id not in evidence_ids:
            fail(f"{label} references unknown evidence_id {evidence_id}.")


def category_is_complete(
    evidence_rows: Sequence[Mapping[str, str]], category: str
) -> bool:
    return aggregate_evidence_status(evidence_rows, category) == "complete"


def validate_candidate_reference(
    label: str, candidate_id: str, candidates: Mapping[str, Mapping[str, str]]
) -> Mapping[str, str]:
    result = candidates.get(candidate_id)
    if result is None:
        fail(f"{label} references unknown candidate_id {candidate_id}.")
    return result


def validate_orientation_evidence(
    rows: Sequence[Mapping[str, str]],
    review_id: str,
    candidates: Mapping[str, Mapping[str, str]],
    sample_rows: Sequence[Mapping[str, str]],
    partition_ids: set[str],
    plan: Mapping[str, str],
    complete: bool,
) -> None:
    ensure_unique(rows, "locus_id", "Orientation locus audit")
    samples = {row["sample_id"]: row for row in sample_rows}
    observed_orientations: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        validate_safe_id("Orientation audit locus_id", row["locus_id"])
        result = validate_candidate_reference(
            f"Orientation audit row {row_number}",
            row["candidate_id"],
            candidates,
        )
        if row["partition_id"] not in partition_ids:
            fail("Orientation audit references an unknown partition.")
        validate_enum(
            "Orientation audit orientation", row["orientation"], ORIENTATIONS
        )
        observed_orientations.add(row["orientation"])
        if any(
            row[column] != result[column]
            for column in (
                "partition_id",
                "orientation",
                "chromosome",
                "position",
                "genomic_ref",
                "genomic_alt",
                "rna_ref",
                "rna_alt",
            )
        ):
            fail("Orientation audit candidate identity differs from Step 09.")
        sample = samples.get(row["sample_id"])
        if sample is None:
            fail("Orientation audit references an unknown sample.")
        if (
            row["condition"] != sample["condition"]
            or row["replicate"] != sample["replicate"]
        ):
            fail("Orientation audit sample metadata differs from the manifest.")
        expected_transcripts = result["transcript_ids"].split(";")
        if result["transcript_ids"] == NA_VALUE:
            valid_transcript = row["transcript_id"] == NA_VALUE
        else:
            valid_transcript = row["transcript_id"] in expected_transcripts
        if not valid_transcript:
            fail(
                "Orientation audit transcript_id is not part of the "
                "Step 09 candidate annotation."
            )
        if row["transcript_strand"] != result["annotation_strand"]:
            fail(
                "Orientation audit transcript_strand differs from the "
                "candidate annotation strand."
            )
        expected_flags = (
            ("99", "147")
            if row["orientation"] == "FWD_like"
            else ("83", "163")
        )
        if row["flag_group"] not in expected_flags:
            fail(
                "Orientation audit flag_group is incompatible with its "
                "mechanical orientation."
            )
        raw_dp = parse_nonnegative_int("Orientation audit raw_dp", row["raw_dp"])
        raw_ad = parse_nonnegative_int("Orientation audit raw_ad", row["raw_ad"])
        raw_ref = parse_nonnegative_int(
            "Orientation audit raw_ref_count", row["raw_ref_count"]
        )
        if raw_ad > raw_dp or raw_ref + raw_ad != raw_dp:
            fail("Orientation audit raw count arithmetic is invalid.")
        sample_id = row["sample_id"]
        if (
            row["raw_dp"] != result[f"DP__{sample_id}"]
            or row["raw_ad"] != result[f"AD__{sample_id}"]
        ):
            fail(
                "Orientation audit raw counts differ from the Step 09 "
                "candidate/sample counts."
            )
        for allele_column in (
            "current_expected_rna_ref",
            "current_expected_rna_alt",
            "inverted_expected_rna_ref",
            "inverted_expected_rna_alt",
        ):
            if row[allele_column] not in ("A", "C", "G", "T"):
                fail(
                    f"Orientation audit {allele_column} must be a DNA base."
                )
        if (
            row["current_expected_rna_ref"] != result["rna_ref"]
            or row["current_expected_rna_alt"] != result["rna_alt"]
            or row["inverted_expected_rna_ref"]
            != complement_base(result["rna_ref"])
            or row["inverted_expected_rna_alt"]
            != complement_base(result["rna_alt"])
        ):
            fail(
                "Orientation audit expected alleles do not match the current "
                "and inverted candidate interpretations."
            )
        validate_enum(
            "Orientation audit concordance_status",
            row["concordance_status"],
            CONCORDANCE_STATUSES,
        )
        validate_iso_date("Orientation audit review_date", row["review_date"])
        require_text("Orientation audit reviewer", row["reviewer"])
        require_text("Orientation audit detail", row["detail"])
    if complete and len(rows) != parse_nonnegative_int(
        "Scientific review plan locus_target_count", plan["locus_target_count"]
    ):
        fail(
            "Complete orientation audit row count differs from "
            "locus_target_count."
        )
    if complete and rows and observed_orientations != set(ORIENTATIONS):
        fail("Complete orientation audit must cover both required orientations.")
    del review_id


def validate_annotation_evidence(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    plan: Mapping[str, str],
    complete: bool,
) -> None:
    ensure_unique(rows, "audit_id", "Annotation audit")
    observed_cases: set[str] = set()
    observed_strands: set[str] = set()
    observed_orientations: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        result = validate_candidate_reference(
            f"Annotation audit row {row_number}",
            row["candidate_id"],
            candidates,
        )
        validate_enum(
            "Annotation audit orientation", row["orientation"], ORIENTATIONS
        )
        if row["annotation_strand"] not in ("+", "-"):
            fail("Annotation audit annotation_strand must be + or -.")
        if any(
            row[column] != result[column]
            for column in (
                "chromosome",
                "position",
                "orientation",
                "annotation_strand",
            )
        ):
            fail("Annotation audit candidate identity differs from Step 09.")
        observed_mapping = {
            "observed_gene_ids": result["gene_ids"],
            "observed_transcript_ids": result["transcript_ids"],
            "observed_is_cds": result["is_cds"],
            "observed_is_five_prime_utr": result["is_five_prime_utr"],
            "observed_is_three_prime_utr": result["is_three_prime_utr"],
            "observed_is_exon": result["is_exon"],
            "observed_is_intron": result["is_intron"],
        }
        for column, expected in observed_mapping.items():
            if row[column] != expected:
                fail(
                    f"Annotation audit {column} differs from the Step 09 "
                    "candidate annotation."
                )
        for column in (
            "expected_is_cds",
            "expected_is_five_prime_utr",
            "expected_is_three_prime_utr",
            "expected_is_exon",
            "expected_is_intron",
        ):
            if row[column] not in ("TRUE", "FALSE"):
                fail(f"Annotation audit {column} must be TRUE or FALSE.")
        for column in ("expected_gene_ids", "expected_transcript_ids"):
            require_text(f"Annotation audit {column}", row[column], allow_na=True)
        validate_enum(
            "Annotation audit assignment_status",
            row["assignment_status"],
            ANNOTATION_ASSIGNMENT_STATUSES,
        )
        validate_enum(
            "Annotation audit ambiguity_status",
            row["ambiguity_status"],
            ANNOTATION_AMBIGUITY_STATUSES,
        )
        expected_mapping = {
            "expected_gene_ids": row["observed_gene_ids"],
            "expected_transcript_ids": row["observed_transcript_ids"],
            "expected_is_cds": row["observed_is_cds"],
            "expected_is_five_prime_utr": row["observed_is_five_prime_utr"],
            "expected_is_three_prime_utr": row["observed_is_three_prime_utr"],
            "expected_is_exon": row["observed_is_exon"],
            "expected_is_intron": row["observed_is_intron"],
        }
        expected_matches = all(
            row[column] == expected
            for column, expected in expected_mapping.items()
        )
        if row["assignment_status"] == "match" and not expected_matches:
            fail(
                "Annotation audit assignment_status=match conflicts with "
                "observed/expected fields."
            )
        if row["assignment_status"] == "mismatch" and expected_matches:
            fail(
                "Annotation audit assignment_status=mismatch has no observed "
                "difference."
            )
        observed_cases.add(row["case_type"])
        observed_strands.add(row["annotation_strand"])
        observed_orientations.add(row["orientation"])
        validate_iso_date("Annotation audit review_date", row["review_date"])
        require_text("Annotation audit reviewer", row["reviewer"])
        require_text("Annotation audit detail", row["detail"])
    if complete:
        required_cases = set(plan["required_annotation_cases"].split(","))
        if not required_cases.issubset(observed_cases):
            fail("Complete annotation audit is missing required case types.")
        if observed_strands != {"+", "-"}:
            fail("Complete annotation audit must cover both annotation strands.")
        if observed_orientations != set(ORIENTATIONS):
            fail("Complete annotation audit must cover both orientations.")


def expected_qc_rows(
    review_id: str,
    evidence_id: str,
    analysis_id: str,
    step08_inputs: Sequence[Mapping[str, str]],
    all_rows: Sequence[Mapping[str, str]],
    target_rna_change: str,
) -> list[dict[str, str]]:
    target_ref, target_alt = target_rna_change.split(">")
    result: list[dict[str, str]] = []
    for input_row in step08_inputs:
        selected = [
            row
            for row in all_rows
            if row["partition_id"] == input_row["partition_id"]
            and row["orientation"] == input_row["orientation"]
        ]
        target = [
            row
            for row in selected
            if row["rna_ref"] == target_ref and row["rna_alt"] == target_alt
        ]
        result.append(
            {
                "review_id": review_id,
                "evidence_id": evidence_id,
                "analysis_id": analysis_id,
                "scope_type": "partition_orientation",
                "partition_id": input_row["partition_id"],
                "orientation": input_row["orientation"],
                "step07_declared_vcf_records": input_row[
                    "declared_vcf_record_count"
                ],
                "step08_observed_vcf_records": input_row[
                    "observed_vcf_record_count"
                ],
                "step08_observed_alt_alleles": input_row[
                    "observed_alt_allele_count"
                ],
                "step08_supported_snvs": input_row["supported_snv_count"],
                "step08_skipped_symbolic": input_row["skipped_symbolic_count"],
                "step08_skipped_non_snv": input_row["skipped_non_snv_count"],
                "step08_published_candidates": input_row[
                    "published_candidate_count"
                ],
                "step09_candidates": str(len(selected)),
                "step09_target_candidates": str(len(target)),
                "step09_tested": str(
                    count_status(selected, "test_status", "tested")
                ),
                "step09_not_target": str(
                    count_status(selected, "test_status", "not_target_change")
                ),
                "step09_missing_counts": str(
                    count_status(selected, "test_status", "missing_counts")
                ),
                "step09_low_coverage": str(
                    count_status(selected, "test_status", "low_coverage")
                ),
                "step09_degenerate": str(
                    count_status(selected, "test_status", "degenerate_table")
                ),
                "step09_below_mean_dp": str(
                    count_status(selected, "call_status", "below_mean_dp")
                ),
                "step09_background_not_passed": str(
                    count_status(
                        selected, "call_status", "background_not_passed"
                    )
                ),
                "step09_fdr_not_met": str(
                    count_status(selected, "call_status", "fdr_not_met")
                ),
                "step09_effect_not_met": str(
                    count_status(selected, "call_status", "effect_not_met")
                ),
                "step09_significant_up": str(
                    count_status(selected, "call_status", "significant_up")
                ),
                "step09_significant_down": str(
                    count_status(selected, "call_status", "significant_down")
                ),
                "reconciliation_status": "reconciled",
                "detail": "Mechanically reconciled from declared Step 08/09 inputs.",
            }
        )
    return result


def validate_qc_funnel(
    rows: Sequence[Mapping[str, str]],
    review_id: str,
    analysis_id: str,
    step08_inputs: Sequence[Mapping[str, str]],
    all_rows: Sequence[Mapping[str, str]],
    target_rna_change: str,
    complete: bool,
) -> None:
    seen: set[tuple[str, str]] = set()
    expected_by_scope = {
        (row["partition_id"], row["orientation"]): row
        for row in expected_qc_rows(
            review_id,
            rows[0]["evidence_id"] if rows else "unused",
            analysis_id,
            step08_inputs,
            all_rows,
            target_rna_change,
        )
    }
    compared_columns = tuple(
        column
        for column in QC_FUNNEL_HEADER
        if column
        not in (
            "review_id",
            "evidence_id",
            "analysis_id",
            "detail",
        )
    )
    for row in rows:
        scope = (row["partition_id"], row["orientation"])
        if scope in seen:
            fail("QC funnel contains a duplicate partition/orientation scope.")
        seen.add(scope)
        expected = expected_by_scope.get(scope)
        if expected is None:
            fail("QC funnel references an undeclared partition/orientation.")
        for column in compared_columns:
            if row[column] != expected[column]:
                fail(
                    f"QC funnel {scope[0]}/{scope[1]} {column} "
                    "does not reconcile."
                )
    if complete and seen != set(expected_by_scope):
        fail("Complete QC funnel does not cover every partition/orientation.")


def validate_replicate_effects(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    sample_rows: Sequence[Mapping[str, str]],
    summary: Mapping[str, str],
    complete: bool,
) -> None:
    replicates, pairs = paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    seen: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        result = validate_candidate_reference(
            f"Replicate-effects row {row_number}",
            row["candidate_id"],
            candidates,
        )
        if result["test_status"] != "tested":
            fail(
                "Replicate-effects evidence may only summarize successfully "
                "tested candidates."
            )
        replicate = row["replicate"]
        if replicate not in replicates:
            fail("Replicate-effects evidence references an unknown replicate.")
        key = (row["candidate_id"], replicate)
        if key in seen:
            fail("Replicate-effects evidence contains a duplicate stratum row.")
        seen.add(key)
        control_sample, treatment_sample = pairs[replicate]
        if (
            row["control_sample"] != control_sample
            or row["treatment_sample"] != treatment_sample
        ):
            fail("Replicate-effects sample pairing differs from the manifest.")
        if any(
            row[column] != result[column]
            for column in ("partition_id", "orientation")
        ):
            fail("Replicate-effects candidate scope differs from Step 09.")
        for prefix, sample in (
            ("control", control_sample),
            ("treatment", treatment_sample),
        ):
            for metric in ("dp", "ad", "af"):
                if row[f"{prefix}_{metric}"] != result[
                    f"{metric.upper()}__{sample}"
                ]:
                    fail(
                        "Replicate-effects counts differ from Step 09 "
                        f"for candidate {row['candidate_id']}."
                    )
        control_af = parse_number("Replicate-effects control_af", row["control_af"])
        treatment_af = parse_number(
            "Replicate-effects treatment_af", row["treatment_af"]
        )
        delta = parse_number(
            "Replicate-effects treatment_control_difference",
            row["treatment_control_difference"],
        )
        if (
            control_af is None
            or treatment_af is None
            or delta is None
            or not values_close(delta, treatment_af - control_af)
        ):
            fail("Replicate-effects treatment-control difference is invalid.")
        expected_direction = (
            "concordant_up"
            if delta > 0
            else ("concordant_down" if delta < 0 else "no_change")
        )
        if row["direction_status"] != expected_direction:
            fail(
                "Replicate-effects direction_status conflicts with the "
                "treatment-control difference."
            )
        validate_iso_date("Replicate-effects review_date", row["review_date"])
    if complete:
        if not rows:
            fail(
                "Complete replicate-effects evidence must contain at least "
                "one tested candidate."
            )
        candidate_replicates: dict[str, set[str]] = {}
        for candidate_id, replicate in seen:
            candidate_replicates.setdefault(candidate_id, set()).add(replicate)
        for candidate_id, observed in candidate_replicates.items():
            if observed != set(replicates):
                fail(
                    "Complete replicate-effects evidence must cover every "
                    f"replicate for candidate {candidate_id}."
                )


def validate_analysis_file_reference(
    label: str,
    path_value: str,
    hash_value: str,
    expected_header: Sequence[str],
    input_hashes: dict[Path, str],
) -> Table:
    path = require_file(label, resolve_recorded_path(path_value))
    validate_hash(f"{label} SHA-256", hash_value)
    observed_hash = sha256_file(path)
    if hash_value != observed_hash:
        fail(f"{label} SHA-256 differs from the declared value.")
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
    ensure_unique(rows, "parameter_set_id", "Sensitivity matrix")
    expected_ids = {
        plan["primary_analysis_id"],
        *split_ids(
            "sensitivity_analysis_ids", plan["sensitivity_analysis_ids"]
        ),
    }
    observed_ids: set[str] = set()
    primary_count = 0
    summary_fields = (
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
    )
    for row_number, row in enumerate(rows, start=2):
        analysis_id = row["analysis_id"]
        if analysis_id not in expected_ids:
            fail("Sensitivity matrix references an undeclared analysis.")
        if analysis_id in observed_ids:
            fail("Sensitivity matrix contains duplicate analysis IDs.")
        observed_ids.add(analysis_id)
        is_primary = row["is_primary"]
        if is_primary not in ("TRUE", "FALSE"):
            fail("Sensitivity matrix is_primary must be TRUE or FALSE.")
        summary_table = validate_analysis_file_reference(
            f"Sensitivity summary row {row_number}",
            row["analysis_summary_path"],
            row["analysis_summary_sha256"],
            STEP09_SUMMARY_HEADER,
            input_hashes,
        )
        if len(summary_table.rows) != 1:
            fail("A sensitivity analysis summary must have exactly one row.")
        summary = summary_table.rows[0]
        if summary["analysis_id"] != analysis_id:
            fail("Sensitivity matrix analysis_id differs from its summary.")
        if is_primary == "TRUE":
            primary_count += 1
            if analysis_id != plan["primary_analysis_id"]:
                fail("Only the primary analysis may use is_primary=TRUE.")
            if summary_table.path != primary_summary_path:
                fail("Primary sensitivity row must reference the Step 09 summary.")
            if summary != primary_summary:
                fail("Primary sensitivity summary differs from Step 09.")
        elif analysis_id == plan["primary_analysis_id"]:
            fail("The primary sensitivity row must use is_primary=TRUE.")
        for column in summary_fields:
            if row[column] != summary[column]:
                fail(
                    f"Sensitivity matrix row {row_number} {column} "
                    "differs from its analysis summary."
                )
        validate_iso_date("Sensitivity matrix review_date", row["review_date"])
    if complete and (
        observed_ids != expected_ids or primary_count != 1
    ):
        fail("Complete sensitivity matrix does not cover all declared analyses.")


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
    replicate_order, _ = paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    replicates = set(replicate_order)
    result_header = (
        STEP09_RESULT_HEADER
        + tuple(f"DP__{sample}" for sample in sample_ids)
        + tuple(f"AD__{sample}" for sample in sample_ids)
        + tuple(f"AF__{sample}" for sample in sample_ids)
    )
    seen: set[tuple[str, str]] = set()
    analysis_by_replicate: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        if row["primary_analysis_id"] != plan["primary_analysis_id"]:
            fail("Leave-one-pair-out row has the wrong primary_analysis_id.")
        validate_safe_id("Leave-one-pair-out analysis_id", row["analysis_id"])
        prior_analysis = analysis_by_replicate.setdefault(
            row["omitted_replicate"], row["analysis_id"]
        )
        if prior_analysis != row["analysis_id"]:
            fail(
                "Leave-one-pair-out rows for one omitted replicate must "
                "reference one immutable analysis ID."
            )
        if row["omitted_replicate"] not in replicates:
            fail("Leave-one-pair-out row references an unknown replicate.")
        primary = validate_candidate_reference(
            f"Leave-one-pair-out row {row_number}",
            row["candidate_id"],
            candidates,
        )
        key = (row["candidate_id"], row["omitted_replicate"])
        if key in seen:
            fail("Leave-one-pair-out evidence contains a duplicate comparison.")
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
            STEP09_SUMMARY_HEADER,
            input_hashes,
        )
        if len(summary_table.rows) != 1 or (
            summary_table.rows[0]["analysis_id"] != row["analysis_id"]
        ):
            fail("Leave-one-pair-out summary identity is invalid.")
        matched = [
            candidate
            for candidate in all_table.rows
            if candidate["candidate_id"] == row["candidate_id"]
        ]
        if len(matched) != 1:
            fail(
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
                fail(
                    f"Leave-one-pair-out row {row_number} {column} differs "
                    "from its analysis result."
                )
        validate_iso_date("Leave-one-pair-out review_date", row["review_date"])
    if len(set(analysis_by_replicate.values())) != len(analysis_by_replicate):
        fail(
            "Each leave-one-pair-out replicate must use a distinct analysis ID."
        )
    if complete and set(analysis_by_replicate) != replicates:
        fail(
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
        "top_up": parse_nonnegative_int("top_up_count", plan["top_up_count"]),
        "top_down": parse_nonnegative_int(
            "top_down_count", plan["top_down_count"]
        ),
        "discordant": parse_nonnegative_int(
            "discordant_count", plan["discordant_count"]
        ),
        "near_threshold": parse_nonnegative_int(
            "near_threshold_count", plan["near_threshold_count"]
        ),
    }
    seen: set[tuple[str, str]] = set()
    ranks: dict[str, list[int]] = {key: [] for key in expected_sets}
    for row_number, row in enumerate(rows, start=2):
        selection_set = row["selection_set"]
        if selection_set not in expected_sets:
            fail("Candidate selection contains an unknown selection_set.")
        key = (selection_set, row["candidate_id"])
        if key in seen:
            fail("Candidate selection contains a duplicate candidate/set pair.")
        seen.add(key)
        result = validate_candidate_reference(
            f"Candidate selection row {row_number}",
            row["candidate_id"],
            candidates,
        )
        rank = parse_nonnegative_int("Candidate selection rank", row["rank"])
        if rank < 1:
            fail("Candidate selection rank must be at least 1.")
        ranks[selection_set].append(rank)
        if row["selection_policy_version"] != plan[
            "candidate_selection_policy_version"
        ]:
            fail("Candidate selection policy version differs from the plan.")
        expected_values = {
            "source_call_status": result["call_status"],
            "source_fdr": result["cmh_fdr_bh"],
            "source_common_or": result["common_odds_ratio"],
            "source_delta": result["treatment_control_difference"],
        }
        for column, expected in expected_values.items():
            if row[column] != expected:
                fail(
                    f"Candidate selection row {row_number} {column} differs "
                    "from Step 09."
                )
        validate_iso_date("Candidate selection review_date", row["review_date"])
    for selection_set, values in ranks.items():
        if values != list(range(1, len(values) + 1)):
            fail(
                f"Candidate selection ranks for {selection_set} must be "
                "contiguous and ordered."
            )
        if complete and len(values) != expected_sets[selection_set]:
            fail(
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
            fail("Candidate adjudication is not part of candidate selection.")
        if key in seen:
            fail("Candidate adjudication contains a duplicate candidate/set pair.")
        seen.add(key)
        validate_supporting_ids(
            "Candidate adjudication supporting_evidence_ids",
            row["supporting_evidence_ids"],
            evidence_ids,
        )
        validate_iso_date(
            "Candidate adjudication review_date", row["review_date"]
        )
        validate_enum(
            "Candidate adjudication adjudication_status",
            row["adjudication_status"],
            ADJUDICATION_STATUSES,
        )
        for column in (
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
        ):
            validate_enum(
                f"Candidate adjudication {column}",
                row[column],
                AUDIT_COMPONENT_STATUSES,
            )
        component_values = [
            row[column]
            for column in (
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
            )
        ]
        if row["adjudication_status"] == "pass" and any(
            status in ("flag", "fail") for status in component_values
        ):
            fail(
                "Candidate adjudication status=pass conflicts with a "
                "flagged or failed component."
            )
        for column in (
            "reason",
            "reviewer",
        ):
            require_text(f"Candidate adjudication {column}", row[column])
    if complete and seen != selected:
        fail("Complete candidate adjudication does not cover every selection.")
    return seen


def validate_decisions(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    evidence_ids: set[str],
    complete: bool,
) -> dict[str, str]:
    ensure_unique(rows, "decision_id", "Scientific decisions")
    seen: set[str] = set()
    decisions: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        dimension = row["decision_dimension"]
        validate_enum(
            f"Scientific decisions row {row_number} dimension",
            dimension,
            DECISION_DIMENSIONS,
        )
        if dimension in seen:
            fail("Scientific decisions contains duplicate decision dimensions.")
        seen.add(dimension)
        validate_enum(
            "Scientific decision evidence_status",
            row["evidence_status"],
            EVIDENCE_STATUSES,
        )
        if complete and row["evidence_status"] not in (
            "complete",
            "not_applicable",
        ):
            fail(
                "A complete science review cannot retain a missing or "
                "incomplete decision evidence status."
            )
        validate_enum(
            "Scientific decision decision_status",
            row["decision_status"],
            DECISION_STATUSES,
        )
        validate_enum(
            "Scientific decision rerun_scope",
            row["rerun_scope"],
            RERUN_SCOPES,
        )
        if row["rerun_required"] not in ("TRUE", "FALSE"):
            fail("Scientific decision rerun_required must be TRUE or FALSE.")
        validate_supporting_ids(
            "Scientific decision supporting_evidence_ids",
            row["supporting_evidence_ids"],
            evidence_ids,
        )
        require_text("Scientific decision rationale", row["rationale"])
        require_text("Scientific decision owner", row["decision_owner"])
        require_text("Scientific decision policy_version", row["policy_version"])
        if row["decision_status"] == "recorded":
            require_text("Scientific decision value", row["decision_value"])
            validate_iso_date(
                "Scientific decision decision_date", row["decision_date"]
            )
            decisions[dimension] = row["decision_value"]
        else:
            if row["decision_value"] != NA_VALUE or row["decision_date"] != NA_VALUE:
                fail(
                    "Pending scientific decisions must use NA for value and date."
                )
            decisions[dimension] = "pending"
    if complete and seen != set(DECISION_DIMENSIONS):
        fail("Complete scientific decisions do not cover every decision dimension.")
    if complete and any(value == "pending" for value in decisions.values()):
        fail("A complete science review cannot contain pending decisions.")
    if (
        decisions.get("orientation") not in (None, "pending")
        and decisions["orientation"] != plan["orientation_status"]
    ):
        fail(
            "The recorded orientation decision must equal plan "
            "orientation_status."
        )
    return decisions


def validate_limitations(
    rows: Sequence[Mapping[str, str]], evidence_ids: set[str]
) -> None:
    ensure_unique(rows, "limitation_id", "Scientific limitations")
    for row in rows:
        for column in (
            "limitation_category",
            "limitation_status",
            "severity",
            "description",
            "impact",
            "mitigation",
            "owner",
        ):
            require_text(f"Scientific limitation {column}", row[column])
        validate_iso_date("Scientific limitation review_date", row["review_date"])
        validate_supporting_ids(
            "Scientific limitation related_evidence_ids",
            row["related_evidence_ids"],
            evidence_ids,
        )


def validate_computational_evidence(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    evidence_rows: Sequence[Mapping[str, str]],
    input_hashes: dict[Path, str],
) -> None:
    seen: dict[str, Mapping[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        validate_safe_id(
            "Computational validation scope", row["validation_scope"]
        )
        if row["validation_scope"] in seen:
            fail("Computational validation contains a duplicate scope.")
        seen[row["validation_scope"]] = row
        validate_enum(
            f"Computational validation row {row_number} status",
            row["validation_status"],
            COMPUTATIONAL_VALIDATION_STATUSES,
        )
        require_text(
            f"Computational validation row {row_number} reviewer",
            row["reviewer"],
        )
        require_text(
            f"Computational validation row {row_number} notes",
            row["notes"],
        )
        validate_iso_date(
            f"Computational validation row {row_number} evidence_date",
            row["evidence_date"],
        )
        if row["exit_code"] != NA_VALUE:
            if not re.fullmatch(r"-?[0-9]+", row["exit_code"]):
                fail("Computational validation exit_code must be an integer or NA.")
        if row["scheduler_state"] not in (
            NA_VALUE,
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            "TIMEOUT",
            "OUT_OF_MEMORY",
            "PREEMPTED",
            "UNKNOWN",
        ):
            fail("Computational validation scheduler_state is unsupported.")
        if row["validation_status"] in ("passed", "proven") and (
            row["exit_code"] != "0"
            or row["scheduler_state"] not in (NA_VALUE, "COMPLETED")
        ):
            fail(
                "Passed/proven computational validation requires exit_code=0 "
                "and a non-failing scheduler state."
            )
        path_is_na = row["evidence_path"] == NA_VALUE
        hash_is_na = row["evidence_sha256"] == NA_VALUE
        if path_is_na != hash_is_na:
            fail(
                "Computational validation evidence path and hash must both "
                "be present or both be NA."
            )
        if not path_is_na:
            path = require_file(
                "Computational validation evidence",
                resolve_recorded_path(row["evidence_path"]),
            )
            validate_hash(
                "Computational validation evidence_sha256",
                row["evidence_sha256"],
            )
            observed = sha256_file(path)
            if observed != row["evidence_sha256"]:
                fail("Computational validation evidence hash differs.")
            input_hashes[path] = observed
    claims = {
        "runtime_validation": (
            plan["runtime_validation_status"] == "passed",
            "passed",
        ),
        "cluster_dry_run": (
            plan["cluster_dry_run_status"] == "passed",
            "passed",
        ),
        "cluster_proof": (
            plan["cluster_proof_status"] == "proven",
            "proven",
        ),
    }
    for scope, (claimed, expected_status) in claims.items():
        if not claimed:
            continue
        evidence = seen.get(scope)
        if evidence is None or evidence["validation_status"] != expected_status:
            fail(
                f"{scope} is claimed in the review plan without matching "
                "computational-validation evidence."
            )
        if (
            evidence["evidence_path"] == NA_VALUE
            or evidence["evidence_sha256"] == NA_VALUE
        ):
            fail(
                f"{scope} claims require an explicit evidence path and hash."
            )
        if scope in ("cluster_dry_run", "cluster_proof") and (
            evidence["scheduler_state"] != "COMPLETED"
        ):
            fail(f"{scope} claims require scheduler_state=COMPLETED.")
    if (
        aggregate_evidence_status(
            evidence_rows, "computational_validation"
        )
        == "complete"
        and not rows
    ):
        fail(
            "Complete computational_validation evidence must contain at "
            "least one explicit validation record."
        )


def validate_evidence_payloads(
    review_id: str,
    plan: Mapping[str, str],
    evidence_rows: Sequence[Mapping[str, str]],
    category_rows: Mapping[str, list[dict[str, str]]],
    sample_ids: Sequence[str],
    sample_rows: Sequence[Mapping[str, str]],
    partition_rows: Sequence[Mapping[str, str]],
    step08_inputs: Sequence[Mapping[str, str]],
    step09_all: Sequence[Mapping[str, str]],
    step09_summary: Mapping[str, str],
    primary_summary_path: Path,
    input_hashes: dict[Path, str],
) -> tuple[dict[str, str], set[tuple[str, str]], set[tuple[str, str]]]:
    candidates = {row["candidate_id"]: row for row in step09_all}
    evidence_ids = {row["evidence_id"] for row in evidence_rows}
    primary_analysis_id = plan["primary_analysis_id"]
    for category, rows in category_rows.items():
        for row_number, row in enumerate(rows, start=2):
            if category not in ("sensitivity_matrix", "leave_one_pair_out") and (
                row["analysis_id"] != primary_analysis_id
            ):
                fail(
                    f"{category} row {row_number} must reference the "
                    "primary analysis."
                )
    validate_orientation_evidence(
        category_rows["orientation_locus_audit"],
        review_id,
        candidates,
        sample_rows,
        {row["partition_id"] for row in partition_rows},
        plan,
        category_is_complete(evidence_rows, "orientation_locus_audit"),
    )
    validate_annotation_evidence(
        category_rows["annotation_audit"],
        candidates,
        plan,
        category_is_complete(evidence_rows, "annotation_audit"),
    )
    validate_qc_funnel(
        category_rows["qc_funnel"],
        review_id,
        primary_analysis_id,
        step08_inputs,
        step09_all,
        step09_summary["target_rna_change"],
        category_is_complete(evidence_rows, "qc_funnel"),
    )
    validate_replicate_effects(
        category_rows["replicate_effects"],
        candidates,
        sample_rows,
        step09_summary,
        category_is_complete(evidence_rows, "replicate_effects"),
    )
    validate_sensitivity_matrix(
        category_rows["sensitivity_matrix"],
        plan,
        primary_summary_path,
        step09_summary,
        input_hashes,
        category_is_complete(evidence_rows, "sensitivity_matrix"),
    )
    validate_leave_one_pair_out(
        category_rows["leave_one_pair_out"],
        plan,
        candidates,
        sample_rows,
        sample_ids,
        step09_summary,
        input_hashes,
        category_is_complete(evidence_rows, "leave_one_pair_out"),
    )
    selected = validate_candidate_selection(
        category_rows["candidate_selection"],
        plan,
        candidates,
        category_is_complete(evidence_rows, "candidate_selection"),
    )
    adjudicated = validate_candidate_adjudication(
        category_rows["candidate_adjudication"],
        candidates,
        selected,
        evidence_ids,
        category_is_complete(evidence_rows, "candidate_adjudication"),
    )
    decisions = validate_decisions(
        category_rows["decisions"],
        plan,
        evidence_ids,
        category_is_complete(evidence_rows, "decisions"),
    )
    validate_limitations(category_rows["limitations"], evidence_ids)
    validate_computational_evidence(
        category_rows["computational_validation"],
        plan,
        evidence_rows,
        input_hashes,
    )

    if plan["overall_science_status"] == "science_review_complete_exploratory":
        for category in CATEGORY_ORDER:
            status = aggregate_evidence_status(evidence_rows, category)
            if status not in ("complete", "not_applicable"):
                fail(
                    "science_review_complete_exploratory requires every "
                    f"evidence category complete or justified not_applicable; "
                    f"{category} is {status}."
                )
        if aggregate_evidence_status(evidence_rows, "decisions") != "complete":
            fail(
                "science_review_complete_exploratory requires explicit "
                "completed decisions."
            )
        if selected != adjudicated:
            fail(
                "science_review_complete_exploratory requires complete "
                "candidate adjudication coverage."
            )
    if plan["cluster_proof_status"] == "proven" and aggregate_evidence_status(
        evidence_rows, "computational_validation"
    ) != "complete":
        fail(
            "cluster_proof_status=proven requires complete explicit "
            "computational_validation evidence."
        )
    return decisions, selected, adjudicated


def make_review_summary(
    context: ReviewContext,
    decisions: Mapping[str, str],
    selected: set[tuple[str, str]],
    adjudicated: set[tuple[str, str]],
    analysis_dir: Path,
) -> dict[str, str]:
    plan = context.plan
    row = {
        "review_id": context.review_id,
        "primary_analysis_id": plan["primary_analysis_id"],
        "superseded_analysis_ids": plan["superseded_analysis_ids"],
        "plan_version": plan["plan_version"],
        "plan_date": plan["plan_date"],
        "reviewer": plan["reviewer"],
        "decision_owner": plan["decision_owner"],
        "git_commit": plan["git_commit"],
        "overall_science_status": plan["overall_science_status"],
        "implementation_status": plan["implementation_status"],
        "local_test_status": plan["local_test_status"],
        "runtime_validation_status": plan["runtime_validation_status"],
        "cluster_dry_run_status": plan["cluster_dry_run_status"],
        "cluster_proof_status": plan["cluster_proof_status"],
        "orientation_policy": plan["orientation_policy"],
        "orientation_policy_version": plan["orientation_policy_version"],
        "orientation_status": plan["orientation_status"],
        "locus_selection_policy_version": plan[
            "locus_selection_policy_version"
        ],
        "locus_selection_rule": plan["locus_selection_rule"],
        "locus_target_count": plan["locus_target_count"],
        "required_orientations": plan["required_orientations"],
        "required_annotation_strands": plan["required_annotation_strands"],
        "required_annotation_cases": plan["required_annotation_cases"],
        "candidate_selection_policy_version": plan[
            "candidate_selection_policy_version"
        ],
        "candidate_selection_rule": plan["candidate_selection_rule"],
        "top_up_count": plan["top_up_count"],
        "top_down_count": plan["top_down_count"],
        "discordant_count": plan["discordant_count"],
        "near_threshold_count": plan["near_threshold_count"],
        "sensitivity_policy_version": plan["sensitivity_policy_version"],
        "sensitivity_rule": plan["sensitivity_rule"],
        "sensitivity_analysis_ids": plan["sensitivity_analysis_ids"],
        "leave_one_pair_out_rule": plan["leave_one_pair_out_rule"],
        "background_policy_version": plan["background_policy_version"],
        "annotation_policy_version": plan["annotation_policy_version"],
        "adjudication_policy_version": plan["adjudication_policy_version"],
        "background_decision": decisions.get("background", "pending"),
        "matched_dna_decision": decisions.get("matched_dna", "pending"),
        "orthogonal_evidence_decision": decisions.get(
            "orthogonal_evidence", "pending"
        ),
        "annotation_decision": decisions.get("annotation", "pending"),
        "thresholds_decision": decisions.get("thresholds", "pending"),
        "adjudication_decision": decisions.get("adjudication", "pending"),
        "orientation_decision": decisions.get("orientation", "pending"),
        "evidence_record_count": str(len(context.evidence_rows)),
        "evidence_source_count": str(
            sum(
                row["evidence_status"] in ("complete", "incomplete")
                for row in context.evidence_rows
            )
        ),
        "selected_candidate_count": str(len(selected)),
        "adjudicated_candidate_count": str(len(adjudicated)),
        "limitation_count": str(len(context.category_rows["limitations"])),
    }
    for category in CATEGORY_ORDER:
        row[f"{category}_status"] = aggregate_evidence_status(
            context.evidence_rows, category
        )
    for key in INPUT_ARTIFACT_KEYS:
        artifact = context.artifacts[key]
        row[f"{key}_path"] = str(artifact.path)
        row[f"{key}_sha256"] = artifact.sha256
        row[f"{key}_row_count"] = artifact.row_count
    row.update(
        {
            "step09_analysis_dir": str(analysis_dir),
            "software_versions": plan["software_versions"],
            "review_completed_date": plan["review_completed_date"],
            "notes": plan["notes"],
            "published_output_count": str(len(OUTPUT_SUFFIXES)),
            "transaction_state": "complete",
        }
    )
    if tuple(row) != REVIEW_SUMMARY_HEADER:
        fail("Internal review-summary schema construction is inconsistent.")
    return row


def build_context(arguments: argparse.Namespace) -> tuple[
    ReviewContext,
    dict[str, tuple[tuple[str, ...], list[dict[str, str]]]],
]:
    validate_safe_id("review_id", arguments.review_id)
    artifacts: dict[str, Artifact] = {}
    input_hashes: dict[Path, str] = {}

    plan_table, plan, allowed_analyses = validate_review_plan(
        arguments.review_plan, arguments.review_id
    )
    register_artifact(
        artifacts,
        input_hashes,
        "review_plan",
        artifact_from_table("Scientific review plan", plan_table),
    )
    sample_table, sample_ids, sample_rows = validate_sample_manifest(
        arguments.sample_manifest
    )
    register_artifact(
        artifacts,
        input_hashes,
        "sample_manifest",
        artifact_from_table("Sample manifest", sample_table),
    )
    partition_table = validate_partition_manifest(arguments.partition_manifest)
    register_artifact(
        artifacts,
        input_hashes,
        "partition_manifest",
        artifact_from_table("Partition manifest", partition_table),
    )
    sample_hash = artifacts["sample_manifest"].sha256
    partition_hash = artifacts["partition_manifest"].sha256

    step08_inputs = validate_step08_inputs(
        arguments.step08_inputs,
        sample_ids,
        partition_table.rows,
        sample_hash,
        partition_hash,
    )
    register_artifact(
        artifacts,
        input_hashes,
        "step08_inputs",
        artifact_from_table("Step 08 input receipt", step08_inputs),
    )
    step08_sites = validate_step08_sites(
        arguments.step08_sites,
        sample_ids,
        partition_table.rows,
        step08_inputs.rows,
    )
    register_artifact(
        artifacts,
        input_hashes,
        "step08_sites",
        artifact_from_table("Step 08 sites table", step08_sites),
    )
    step08_summary = validate_step08_summary(
        arguments.step08_summary,
        sample_ids,
        partition_table.rows,
        step08_inputs.rows,
        step08_sites.rows,
        sample_hash,
        partition_hash,
    )
    register_artifact(
        artifacts,
        input_hashes,
        "step08_summary",
        artifact_from_table("Step 08 summary", step08_summary),
    )

    analysis_dir = require_directory(
        "Step 09 analysis directory", arguments.step09_analysis_dir
    )
    analysis_id = plan["primary_analysis_id"]
    if analysis_dir.name != analysis_id:
        fail(
            "Step 09 analysis directory basename must equal "
            "primary_analysis_id."
        )
    paths = step09_paths(analysis_dir, analysis_id)
    all_sites = validate_step09_results(
        "Step 09 all-sites",
        paths["step09_all_sites"],
        sample_ids,
        analysis_id,
        step08_sites.rows,
    )
    if [row["candidate_id"] for row in all_sites.rows] != [
        row["candidate_id"] for row in step08_sites.rows
    ]:
        fail(
            "Step 09 all-sites candidate order/universe differs from Step 08."
        )
    register_artifact(
        artifacts,
        input_hashes,
        "step09_all_sites",
        artifact_from_table("Step 09 all-sites", all_sites),
    )
    significant = validate_step09_results(
        "Step 09 significant-sites",
        paths["step09_significant_sites"],
        sample_ids,
        analysis_id,
        step08_sites.rows,
    )
    validate_significant_subset(all_sites.rows, significant.rows)
    register_artifact(
        artifacts,
        input_hashes,
        "step09_significant_sites",
        artifact_from_table("Step 09 significant-sites", significant),
    )
    step09_summary_table = validate_step09_summary(
        paths["step09_summary"],
        analysis_id,
        sample_ids,
        sample_rows,
        all_sites.rows,
        sample_table.path,
        partition_table.path,
        step08_sites.path,
        step08_inputs.path,
        sample_hash,
        partition_hash,
        artifacts["step08_sites"].sha256,
        artifacts["step08_inputs"].sha256,
        step08_inputs.rows[0]["orientation_policy"],
    )
    validate_step09_result_semantics(
        all_sites.rows, step09_summary_table.rows[0], sample_rows
    )
    register_artifact(
        artifacts,
        input_hashes,
        "step09_summary",
        artifact_from_table("Step 09 summary", step09_summary_table),
    )
    mutation = validate_mutation_spectrum(
        paths["step09_mutation_spectrum"], analysis_id, all_sites.rows
    )
    register_artifact(
        artifacts,
        input_hashes,
        "step09_mutation_spectrum",
        artifact_from_table("Step 09 mutation spectrum", mutation),
    )
    for key, label in (
        ("step09_mutation_spectrum_pdf", "Step 09 mutation-spectrum PDF"),
        ("step09_depth_delta_pdf", "Step 09 depth-delta PDF"),
    ):
        pdf_path = require_file(label, paths[key])
        validate_pdf(label, pdf_path)
        register_artifact(
            artifacts,
            input_hashes,
            key,
            artifact_from_binary(label, pdf_path),
        )
    if plan["orientation_policy"] != step09_summary_table.rows[0][
        "orientation_policy"
    ]:
        fail("Scientific review plan orientation policy differs from Step 09.")

    evidence_manifest, evidence_rows, category_rows, evidence_index = (
        validate_evidence_manifest(
            arguments.evidence_manifest,
            arguments.review_id,
            allowed_analyses,
            input_hashes,
        )
    )
    register_artifact(
        artifacts,
        input_hashes,
        "evidence_manifest",
        artifact_from_table(
            "Scientific evidence manifest", evidence_manifest
        ),
    )

    output_dir = Path(arguments.output_root).expanduser().resolve() / arguments.review_id
    output_paths = {
        key: output_dir / f"{arguments.review_id}.{suffix}"
        for key, suffix in OUTPUT_SUFFIXES
    }
    context = ReviewContext(
        review_id=arguments.review_id,
        plan=plan,
        evidence_rows=evidence_rows,
        category_rows=category_rows,
        evidence_index_rows=evidence_index,
        artifacts=artifacts,
        input_hashes=input_hashes,
        sample_ids=sample_ids,
        sample_rows=sample_rows,
        partition_rows=partition_table.rows,
        step08_input_rows=step08_inputs.rows,
        step08_site_rows=step08_sites.rows,
        step09_all_rows=all_sites.rows,
        step09_significant_rows=significant.rows,
        step09_summary=step09_summary_table.rows[0],
        output_paths=output_paths,
    )
    decisions, selected, adjudicated = validate_evidence_payloads(
        arguments.review_id,
        plan,
        evidence_rows,
        category_rows,
        sample_ids,
        sample_rows,
        partition_table.rows,
        step08_inputs.rows,
        all_sites.rows,
        step09_summary_table.rows[0],
        step09_summary_table.path,
        input_hashes,
    )
    summary_row = make_review_summary(
        context, decisions, selected, adjudicated, analysis_dir
    )
    output_tables: dict[
        str, tuple[tuple[str, ...], list[dict[str, str]]]
    ] = {
        "review_plan": (REVIEW_PLAN_HEADER, [dict(plan)]),
        "evidence_index": (EVIDENCE_INDEX_HEADER, evidence_index),
    }
    for category in CATEGORY_ORDER:
        output_tables[category] = (
            CATEGORY_HEADERS[category],
            category_rows[category],
        )
    output_tables["review_summary"] = (
        REVIEW_SUMMARY_HEADER,
        [summary_row],
    )
    if tuple(output_tables) != tuple(key for key, _ in OUTPUT_SUFFIXES):
        fail("Internal Step 09c output ordering is inconsistent.")
    return context, output_tables


def confirm_inputs_unchanged(input_hashes: Mapping[Path, str]) -> None:
    for path, expected_hash in input_hashes.items():
        if not path.is_file():
            fail(f"An input disappeared before publication: {path}")
        observed_hash = sha256_file(path)
        if observed_hash != expected_hash:
            fail(f"An input changed before publication: {path}")


def acquire_lock(lock_path: Path, review_id: str, run_token: str) -> None:
    metadata = (
        f"review_id\t{review_id}\n"
        f"pid\t{os.getpid()}\n"
        f"run_token\t{run_token}\n"
        f"created_date\t{date.today().isoformat()}\n"
    )
    try:
        descriptor = os.open(
            lock_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        fail(
            "Step 09c output is locked; inspect and preserve the owner "
            f"metadata before recovery: {lock_path}"
        )
    except OSError as exc:
        fail(f"Could not acquire Step 09c lock {lock_path}: {exc}")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(metadata)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        try:
            lock_path.unlink()
        except OSError:
            pass
        fail(f"Could not write Step 09c lock metadata: {exc}")


def remove_owned_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def validate_staged_outputs(
    directory: Path,
    output_tables: Mapping[
        str, tuple[tuple[str, ...], list[dict[str, str]]]
    ],
    output_paths: Mapping[str, Path],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, (header, rows) in output_tables.items():
        staged = directory / output_paths[key].name
        table = read_tsv(f"Staged Step 09c {key}", staged, header)
        if table.rows != rows:
            fail(f"Staged Step 09c {key} content changed after writing.")
        hashes[key] = sha256_file(staged)
    return hashes


def rollback_publication(
    output_paths: Mapping[str, Path],
    backup_dir: Path,
    had_previous: bool,
    previous_hashes: Mapping[str, str],
) -> list[str]:
    failures: list[str] = []
    if not had_previous:
        for key, _ in reversed(OUTPUT_SUFFIXES):
            final = output_paths[key]
            if final.exists():
                try:
                    final.unlink()
                except OSError as exc:
                    failures.append(f"remove new {final}: {exc}")
    else:
        restore_order = [
            key for key, _ in OUTPUT_SUFFIXES if key != "review_summary"
        ] + ["review_summary"]
        for key in restore_order:
            backup = backup_dir / output_paths[key].name
            final = output_paths[key]
            if not backup.exists():
                if not final.exists():
                    failures.append(
                        f"prior output and backup are both missing for {final}"
                    )
                continue
            if final.exists():
                try:
                    final.unlink()
                except OSError as exc:
                    failures.append(f"remove replacement {final}: {exc}")
                    continue
            try:
                os.replace(backup, final)
            except OSError as exc:
                failures.append(f"restore {final}: {exc}")
        for key, _ in OUTPUT_SUFFIXES:
            final = output_paths[key]
            if not final.is_file():
                failures.append(f"restored prior output is missing: {final}")
                continue
            try:
                observed = sha256_file(final)
            except ContractError as exc:
                failures.append(str(exc))
                continue
            if observed != previous_hashes.get(key):
                failures.append(f"restored prior output hash differs: {final}")
    return failures


def publish_outputs(
    context: ReviewContext,
    output_tables: Mapping[
        str, tuple[tuple[str, ...], list[dict[str, str]]]
    ],
) -> None:
    output_dir = next(iter(context.output_paths.values())).parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fail(f"Could not create Step 09c output directory {output_dir}: {exc}")
    if not output_dir.is_dir():
        fail(f"Step 09c output path is not a directory: {output_dir}")

    lock_path = output_dir / f".{context.review_id}.step09c.lock"
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_dir = output_dir / f".{context.review_id}.step09c.{run_token}.tmp"
    backup_dir = output_dir / f".{context.review_id}.step09c.{run_token}.previous"
    acquire_lock(lock_path, context.review_id, run_token)
    keep_recovery = False
    had_previous = False
    previous_hashes: dict[str, str] = {}
    publication_started = False
    try:
        existing = {
            key: path.exists() for key, path in context.output_paths.items()
        }
        existing_count = sum(existing.values())
        if existing_count not in (0, len(context.output_paths)):
            fail(
                "Refusing to replace an incomplete/partial Step 09c output "
                "transaction; "
                "preserve it for inspection."
            )
        had_previous = existing_count == len(context.output_paths)
        if had_previous:
            previous_hashes = {
                key: sha256_file(path)
                for key, path in context.output_paths.items()
            }
        try:
            temp_dir.mkdir()
            if had_previous:
                backup_dir.mkdir()
        except FileExistsError:
            fail("Refusing to reuse an existing Step 09c run-token path.")
        except OSError as exc:
            fail(f"Could not create Step 09c transaction paths: {exc}")

        for key, (header, rows) in output_tables.items():
            write_tsv(temp_dir / context.output_paths[key].name, header, rows)
        staged_hashes = validate_staged_outputs(
            temp_dir, output_tables, context.output_paths
        )
        confirm_inputs_unchanged(context.input_hashes)

        if had_previous:
            summary_key = "review_summary"
            os.replace(
                context.output_paths[summary_key],
                backup_dir / context.output_paths[summary_key].name,
            )
            publication_started = True
            for key, _ in OUTPUT_SUFFIXES:
                if key == summary_key:
                    continue
                os.replace(
                    context.output_paths[key],
                    backup_dir / context.output_paths[key].name,
                )
        publication_started = True
        for key, _ in OUTPUT_SUFFIXES:
            if key == "review_summary":
                continue
            os.replace(
                temp_dir / context.output_paths[key].name,
                context.output_paths[key],
            )
        os.replace(
            temp_dir / context.output_paths["review_summary"].name,
            context.output_paths["review_summary"],
        )

        for key, (header, rows) in output_tables.items():
            final = read_tsv(
                f"Published Step 09c {key}",
                context.output_paths[key],
                header,
            )
            if final.rows != rows:
                fail(f"Published Step 09c {key} content is invalid.")
            if sha256_file(final.path) != staged_hashes[key]:
                fail(f"Published Step 09c {key} hash is invalid.")
        confirm_inputs_unchanged(context.input_hashes)
    except Exception as exc:
        if publication_started:
            rollback_failures = rollback_publication(
                context.output_paths,
                backup_dir,
                had_previous,
                previous_hashes,
            )
            if rollback_failures:
                keep_recovery = True
                recovery = output_dir / (
                    f".{context.review_id}.step09c.{run_token}.RECOVERY.txt"
                )
                try:
                    recovery.write_text(
                        "Step 09c rollback was incomplete.\n"
                        + "\n".join(rollback_failures)
                        + "\n",
                        encoding="utf-8",
                    )
                except OSError:
                    pass
                fail(
                    f"{exc}\nStep 09c rollback was incomplete; lock and "
                    f"recovery paths were retained: {lock_path}"
                )
        if isinstance(exc, ContractError):
            raise
        fail(f"Step 09c publication failed: {exc}")
    finally:
        if not keep_recovery:
            cleanup_failures: list[str] = []
            for owned in (temp_dir, backup_dir):
                try:
                    remove_owned_path(owned)
                except OSError as exc:
                    cleanup_failures.append(f"remove {owned}: {exc}")
            try:
                lock_path.unlink()
            except FileNotFoundError:
                cleanup_failures.append(
                    f"owned lock disappeared before cleanup: {lock_path}"
                )
            except OSError as exc:
                cleanup_failures.append(f"remove lock {lock_path}: {exc}")
            if cleanup_failures:
                raise ContractError(
                    "Step 09c cleanup was incomplete; inspect owned paths: "
                    + "; ".join(cleanup_failures)
                )


def print_resolved_context(context: ReviewContext, execute: bool) -> None:
    print("Step 09c scientific-validation evidence package")
    print(f"Mode: {'execute' if execute else 'dry-run'}")
    print(f"Review ID: {context.review_id}")
    print(f"Primary analysis ID: {context.plan['primary_analysis_id']}")
    print(
        "Overall science status: "
        f"{context.plan['overall_science_status']}"
    )
    print(
        "Computational status: "
        f"implementation={context.plan['implementation_status']}; "
        f"local_tests={context.plan['local_test_status']}; "
        f"runtime={context.plan['runtime_validation_status']}; "
        f"cluster_dry_run={context.plan['cluster_dry_run_status']}; "
        f"cluster_proof={context.plan['cluster_proof_status']}"
    )
    print("Validated immutable inputs:")
    for key in INPUT_ARTIFACT_KEYS:
        artifact = context.artifacts[key]
        print(
            f"  {key}: {artifact.path} "
            f"(sha256={artifact.sha256}, rows={artifact.row_count})"
        )
    print("Declared outputs (review summary is the final transaction marker):")
    for key, _ in OUTPUT_SUFFIXES:
        print(f"  {key}: {context.output_paths[key]}")
    if not execute:
        print("Dry-run complete; no output directory or final files were created.")


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and summarize explicit Step 09c scientific-review "
            "evidence. Dry-run is the default."
        )
    )
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--sample-manifest", required=True)
    parser.add_argument("--partition-manifest", required=True)
    parser.add_argument("--step08-sites", required=True)
    parser.add_argument("--step08-inputs", required=True)
    parser.add_argument("--step08-summary", required=True)
    parser.add_argument("--step09-analysis-dir", required=True)
    parser.add_argument("--review-plan", required=True)
    parser.add_argument("--evidence-manifest", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the validated 13-file transaction.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        context, output_tables = build_context(arguments)
        print_resolved_context(context, arguments.execute)
        if arguments.execute:
            publish_outputs(context, output_tables)
            print(
                "Step 09c publication complete; review summary published last: "
                f"{context.output_paths['review_summary']}"
            )
        return 0
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: Step 09c failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
