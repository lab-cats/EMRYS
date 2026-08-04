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
import importlib.util
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence


_STEP08_MODULE_NAME = "_norad_step08_scientific_evidence_contract"
_STEP08_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "scientific_evidence"
    / "step08.py"
).resolve(strict=False)
_STEP08_READY_ATTRIBUTE = "_NORAD_STEP08_CONTRACT_READY"


def _validated_step08_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 08 scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _STEP08_MODULE_PATH:
        raise ImportError(
            "cached Step 08 scientific-evidence contract resolves to "
            f"{module_path}, expected {_STEP08_MODULE_PATH}"
        )
    if getattr(module, _STEP08_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 08 scientific-evidence contract is partially initialized"
        )
    return module


def _load_step08_contract() -> object:
    cached = sys.modules.get(_STEP08_MODULE_NAME)
    if cached is not None:
        return _validated_step08_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _STEP08_MODULE_NAME, _STEP08_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 08 module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_STEP08_MODULE_NAME, module)
    if existing is not module:
        return _validated_step08_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _STEP08_READY_ATTRIBUTE, True)
        _validated_step08_contract(module)
    except BaseException:
        if sys.modules.get(_STEP08_MODULE_NAME) is module:
            del sys.modules[_STEP08_MODULE_NAME]
        raise
    return module


try:
    step08 = _load_step08_contract()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 08 scientific-evidence contract at "
        f"{_STEP08_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


_STEP09_MODULE_NAME = "_norad_step09_scientific_evidence_contract"
_STEP09_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "scientific_evidence"
    / "step09.py"
).resolve(strict=False)
_STEP09_READY_ATTRIBUTE = "_NORAD_STEP09_CONTRACT_READY"


def _validated_step09_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 09 scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _STEP09_MODULE_PATH:
        raise ImportError(
            "cached Step 09 scientific-evidence contract resolves to "
            f"{module_path}, expected {_STEP09_MODULE_PATH}"
        )
    if getattr(module, _STEP09_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 09 scientific-evidence contract is partially initialized"
        )
    return module


def _load_step09_contract() -> object:
    cached = sys.modules.get(_STEP09_MODULE_NAME)
    if cached is not None:
        return _validated_step09_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _STEP09_MODULE_NAME, _STEP09_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 09 module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_STEP09_MODULE_NAME, module)
    if existing is not module:
        return _validated_step09_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _STEP09_READY_ATTRIBUTE, True)
        _validated_step09_contract(module)
    except BaseException:
        if sys.modules.get(_STEP09_MODULE_NAME) is module:
            del sys.modules[_STEP09_MODULE_NAME]
        raise
    return module


try:
    step09 = _load_step09_contract()
    if step09.step08 is not step08:
        raise ImportError(
            "Step 09c and Step 09 resolved different Step 08 contract objects"
        )
    if (
        step09.ContractError is not step08.ContractError
        or step09.Table is not step08.Table
    ):
        raise ImportError("Step 09 contract resolved different shared identities")
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 09 scientific-evidence contract at "
        f"{_STEP09_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


ContractError = step08.ContractError
NA_VALUE = step08.NA_VALUE
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
COMPUTATIONAL_SCOPE_ROLES = {
    "local_fixture_tests": "local_test",
    "local_test": "local_test",
    "runtime_validation": "runtime_output",
    "runtime_log": "runtime_log",
    "runtime_output": "runtime_output",
    "cluster_dry_run": "cluster_dry_run",
    "cluster_proof": "cluster_output",
    "cluster_scheduler": "cluster_scheduler",
    "cluster_log": "cluster_log",
    "cluster_output": "cluster_output",
}
COMPUTATIONAL_SCOPE_PLAN_FIELDS = {
    "local_fixture_tests": "local_test_status",
    "local_test": "local_test_status",
    "runtime_validation": "runtime_validation_status",
    "runtime_log": "runtime_validation_status",
    "runtime_output": "runtime_validation_status",
    "cluster_dry_run": "cluster_dry_run_status",
    "cluster_proof": "cluster_proof_status",
    "cluster_scheduler": "cluster_proof_status",
    "cluster_log": "cluster_proof_status",
    "cluster_output": "cluster_proof_status",
}

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
COMPUTATIONAL_VALIDATION_STATUSES = (
    "not_run",
    "blocked",
    "passed",
    "failed",
    "proven",
)


Table = step08.Table
values_close = step08.values_close
sha256_file = step08.sha256_file
read_tsv = step08.read_tsv
resolve_recorded_path = step09.resolve_recorded_path


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


def validate_iso_date(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        step08.fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")
    if parsed.isoformat() != value:
        step08.fail(f"{label} must be an ISO date (YYYY-MM-DD); got: {value}")



def complement_base(value: str) -> str:
    complements = {"A": "T", "C": "G", "G": "C", "T": "A"}
    if value not in complements:
        step08.fail(f"Expected a canonical DNA base; got: {value}")
    return complements[value]


def split_ids(label: str, value: str) -> list[str]:
    if value == NA_VALUE:
        return []
    parts = value.split(",")
    if any(not part or part.strip() != part for part in parts):
        step08.fail(f"{label} must be comma-separated safe IDs or NA; got: {value}")
    for part in parts:
        step08.validate_safe_id(label, part)
    if len(parts) != len(set(parts)):
        step08.fail(f"{label} contains duplicate IDs: {value}")
    return parts


def require_directory(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_dir():
        step08.fail(f"{label} does not exist or is not a directory: {path}")
    return path.resolve()


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


def resolve_declared_path(value: str, source_file: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = source_file.parent / path
    return path.resolve()



def register_artifact(
    artifacts: dict[str, Artifact],
    input_hashes: dict[Path, str],
    key: str,
    artifact: Artifact,
) -> None:
    if key in artifacts:
        step08.fail(f"Internal artifact key was registered twice: {key}")
    artifacts[key] = artifact
    input_hashes[artifact.path] = artifact.sha256



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



def validate_review_plan(
    value: str | Path, review_id: str
) -> tuple[Table, dict[str, str], set[str]]:
    table = read_tsv("Scientific review plan", value, REVIEW_PLAN_HEADER)
    if len(table.rows) != 1:
        step08.fail("Scientific review plan must contain exactly one data row.")
    plan = table.rows[0]
    if plan["review_id"] != review_id:
        step08.fail("Scientific review plan review_id differs from --review-id.")
    step08.validate_safe_id("review_id", plan["review_id"])
    step08.validate_safe_id("primary_analysis_id", plan["primary_analysis_id"])
    requested_status = plan["overall_science_status"]
    if requested_status == RESERVED_SCIENCE_STATUS:
        step08.fail(
            "biological_interpretation_ready is reserved and cannot be "
            "produced by Step 09c."
        )
    step08.validate_enum(
        "overall_science_status", requested_status, SCIENCE_STATUSES
    )
    step08.validate_enum(
        "implementation_status",
        plan["implementation_status"],
        IMPLEMENTATION_STATUSES,
    )
    step08.validate_enum(
        "local_test_status", plan["local_test_status"], LOCAL_TEST_STATUSES
    )
    step08.validate_enum(
        "runtime_validation_status",
        plan["runtime_validation_status"],
        RUNTIME_VALIDATION_STATUSES,
    )
    step08.validate_enum(
        "cluster_dry_run_status",
        plan["cluster_dry_run_status"],
        CLUSTER_DRY_RUN_STATUSES,
    )
    step08.validate_enum(
        "cluster_proof_status",
        plan["cluster_proof_status"],
        CLUSTER_PROOF_STATUSES,
    )
    step08.validate_enum(
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
        "git_commit",
        "orientation_policy",
        "orientation_policy_version",
        "locus_selection_policy_version",
        "candidate_selection_policy_version",
        "sensitivity_policy_version",
        "background_policy_version",
        "annotation_policy_version",
        "adjudication_policy_version",
    ):
        step08.validate_safe_id(
            f"Scientific review plan {column}",
            plan[column],
        )
    for column in (
        "reviewer",
        "decision_owner",
        "locus_selection_rule",
        "candidate_selection_rule",
        "sensitivity_rule",
        "leave_one_pair_out_rule",
        "software_versions",
        "notes",
    ):
        step08.require_text(f"Scientific review plan {column}", plan[column])
    for column in (
        "locus_target_count",
        "top_up_count",
        "top_down_count",
        "discordant_count",
        "near_threshold_count",
    ):
        step08.parse_nonnegative_int(f"Scientific review plan {column}", plan[column])
    required_orientations = split_ids(
        "required_orientations", plan["required_orientations"]
    )
    if required_orientations != list(step08.ORIENTATIONS):
        step08.fail(
            "required_orientations must be exactly "
            "FWD_like,REV_like in that order."
        )
    required_strands = plan["required_annotation_strands"].split(",")
    if required_strands != ["+", "-"]:
        step08.fail("required_annotation_strands must be exactly +,-.")
    step08.require_text(
        "required_annotation_cases", plan["required_annotation_cases"]
    )
    superseded = split_ids(
        "superseded_analysis_ids", plan["superseded_analysis_ids"]
    )
    sensitivity = split_ids(
        "sensitivity_analysis_ids", plan["sensitivity_analysis_ids"]
    )
    if plan["primary_analysis_id"] in superseded + sensitivity:
        step08.fail("The primary analysis cannot also be superseded or a sensitivity run.")
    overlap = sorted(set(superseded) & set(sensitivity))
    if overlap:
        step08.fail(
            "Superseded and sensitivity analysis IDs must be disjoint; "
            f"overlap: {','.join(overlap)}."
        )
    allowed_analyses = {
        plan["primary_analysis_id"],
        *superseded,
        *sensitivity,
    }
    if plan["cluster_proof_status"] == "proven" and (
        plan["runtime_validation_status"] != "passed"
        or plan["cluster_dry_run_status"] != "passed"
    ):
        step08.fail(
            "cluster_proof_status=proven requires runtime and cluster "
            "dry-run status passed."
        )
    if requested_status == "science_review_complete_exploratory":
        if plan["review_completed_date"] == NA_VALUE:
            step08.fail(
                "An exploratory-complete science review requires "
                "review_completed_date."
            )
    elif plan["review_completed_date"] != NA_VALUE:
        step08.fail(
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
    plan: Mapping[str, str],
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
    step08.ensure_unique(manifest.rows, "evidence_id", "Scientific evidence manifest")
    for category in CATEGORY_ORDER:
        if not any(
            row["evidence_category"] == category for row in manifest.rows
        ):
            step08.fail(
                "Scientific evidence manifest must explicitly represent "
                f"category {category}."
            )
    primary_analysis_id = plan["primary_analysis_id"]
    superseded_analyses = set(
        split_ids(
            "superseded_analysis_ids",
            plan["superseded_analysis_ids"],
        )
    )
    sensitivity_analyses = set(
        split_ids(
            "sensitivity_analysis_ids",
            plan["sensitivity_analysis_ids"],
        )
    )
    allowed_analyses = {
        primary_analysis_id,
        *superseded_analyses,
        *sensitivity_analyses,
    }
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
        step08.validate_safe_id("evidence_id", row["evidence_id"])
        step08.validate_enum(
            f"Evidence manifest row {row_number} category",
            row["evidence_category"],
            ALLOWED_EVIDENCE_CATEGORIES,
        )
        step08.validate_enum(
            f"Evidence manifest row {row_number} status",
            row["evidence_status"],
            EVIDENCE_STATUSES,
        )
        category_allowed_analyses = (
            {primary_analysis_id, *sensitivity_analyses}
            if row["evidence_category"]
            in ("sensitivity_matrix", "leave_one_pair_out")
            else {primary_analysis_id}
        )
        if row["analysis_id"] not in category_allowed_analyses:
            step08.fail(
                f"Evidence manifest row {row_number} category "
                f"{row['evidence_category']} cannot use analysis_id "
                f"{row['analysis_id']}."
            )
        for column in ("reviewer", "owner"):
            step08.require_text(
                f"Evidence manifest row {row_number} {column}", row[column]
            )
        step08.validate_safe_id(
            f"Evidence manifest row {row_number} policy_version",
            row["policy_version"],
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
                step08.fail(
                    f"Evidence {row['evidence_id']} with status {status} "
                    "must use NA for source path, hash, and row count."
                )
            if status == "not_applicable":
                step08.require_text(
                    f"Evidence {row['evidence_id']} not_applicable_reason",
                    row["not_applicable_reason"],
                )
            elif row["not_applicable_reason"] != NA_VALUE:
                step08.fail(
                    "Missing evidence must use not_applicable_reason=NA."
                )
            observed_path = NA_VALUE
            observed_hash = NA_VALUE
            observed_count = NA_VALUE
        else:
            if row["evidence_date"] == NA_VALUE:
                step08.fail(
                    f"Evidence {row['evidence_id']} with status {status} "
                    "must record evidence_date."
                )
            if row["not_applicable_reason"] != NA_VALUE:
                step08.fail(
                    "Complete or incomplete evidence must use "
                    "not_applicable_reason=NA."
                )
            source_path = resolve_declared_path(
                row["source_path"], manifest.path
            )
            source_path = step08.require_file(
                f"Evidence source {row['evidence_id']}", source_path
            )
            if source_path in source_paths:
                step08.fail(
                    "Scientific evidence manifest declares the same source "
                    f"path more than once: {source_path}"
                )
            source_paths.add(source_path)
            step08.validate_hash(
                f"Evidence {row['evidence_id']} source_sha256",
                row["source_sha256"],
            )
            observed_hash = sha256_file(source_path)
            if observed_hash != row["source_sha256"]:
                step08.fail(
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
            declared_count = step08.parse_nonnegative_int(
                f"Evidence {row['evidence_id']} source_row_count",
                row["source_row_count"],
            )
            if declared_count != len(source_table.rows):
                step08.fail(
                    f"Evidence source row count differs for "
                    f"{row['evidence_id']}."
                )
            for source_row_number, payload in enumerate(
                source_table.rows, start=2
            ):
                if payload["review_id"] != review_id:
                    step08.fail(
                        f"Evidence {row['evidence_id']} payload row "
                        f"{source_row_number} has the wrong review_id."
                    )
                if payload["evidence_id"] != row["evidence_id"]:
                    step08.fail(
                        f"Evidence {row['evidence_id']} payload row "
                        f"{source_row_number} has the wrong evidence_id."
                    )
                if row["evidence_category"] in (
                    "sensitivity_matrix",
                    "leave_one_pair_out",
                ):
                    if payload["analysis_id"] not in {
                        primary_analysis_id,
                        *sensitivity_analyses,
                    }:
                        step08.fail(
                            f"Evidence {row['evidence_id']} payload "
                            "references an analysis_id outside the primary "
                            "and declared sensitivity analyses."
                        )
                elif payload["analysis_id"] != row["analysis_id"]:
                    step08.fail(
                        f"Evidence {row['evidence_id']} payload references "
                        "an analysis_id different from its manifest row."
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
            step08.fail(f"{label} references unknown evidence_id {evidence_id}.")


def category_is_complete(
    evidence_rows: Sequence[Mapping[str, str]], category: str
) -> bool:
    return aggregate_evidence_status(evidence_rows, category) == "complete"


def validate_candidate_reference(
    label: str, candidate_id: str, candidates: Mapping[str, Mapping[str, str]]
) -> Mapping[str, str]:
    result = candidates.get(candidate_id)
    if result is None:
        step08.fail(f"{label} references unknown candidate_id {candidate_id}.")
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
    step08.ensure_unique(rows, "locus_id", "Orientation locus audit")
    samples = {row["sample_id"]: row for row in sample_rows}
    observed_orientations: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        step08.validate_safe_id("Orientation audit locus_id", row["locus_id"])
        result = validate_candidate_reference(
            f"Orientation audit row {row_number}",
            row["candidate_id"],
            candidates,
        )
        if row["partition_id"] not in partition_ids:
            step08.fail("Orientation audit references an unknown partition.")
        step08.validate_enum(
            "Orientation audit orientation", row["orientation"], step08.ORIENTATIONS
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
            step08.fail("Orientation audit candidate identity differs from Step 09.")
        sample = samples.get(row["sample_id"])
        if sample is None:
            step08.fail("Orientation audit references an unknown sample.")
        if (
            row["condition"] != sample["condition"]
            or row["replicate"] != sample["replicate"]
        ):
            step08.fail("Orientation audit sample metadata differs from the manifest.")
        expected_transcripts = result["transcript_ids"].split(";")
        if result["transcript_ids"] == NA_VALUE:
            valid_transcript = row["transcript_id"] == NA_VALUE
        else:
            valid_transcript = row["transcript_id"] in expected_transcripts
        if not valid_transcript:
            step08.fail(
                "Orientation audit transcript_id is not part of the "
                "Step 09 candidate annotation."
            )
        if row["transcript_strand"] != result["annotation_strand"]:
            step08.fail(
                "Orientation audit transcript_strand differs from the "
                "candidate annotation strand."
            )
        expected_flags = (
            ("99", "147")
            if row["orientation"] == "FWD_like"
            else ("83", "163")
        )
        if row["flag_group"] not in expected_flags:
            step08.fail(
                "Orientation audit flag_group is incompatible with its "
                "mechanical orientation."
            )
        raw_dp = step08.parse_nonnegative_int("Orientation audit raw_dp", row["raw_dp"])
        raw_ad = step08.parse_nonnegative_int("Orientation audit raw_ad", row["raw_ad"])
        raw_ref = step08.parse_nonnegative_int(
            "Orientation audit raw_ref_count", row["raw_ref_count"]
        )
        if raw_ad > raw_dp or raw_ref + raw_ad != raw_dp:
            step08.fail("Orientation audit raw count arithmetic is invalid.")
        sample_id = row["sample_id"]
        if (
            row["raw_dp"] != result[f"DP__{sample_id}"]
            or row["raw_ad"] != result[f"AD__{sample_id}"]
        ):
            step08.fail(
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
                step08.fail(
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
            step08.fail(
                "Orientation audit expected alleles do not match the current "
                "and inverted candidate interpretations."
            )
        step08.validate_enum(
            "Orientation audit concordance_status",
            row["concordance_status"],
            CONCORDANCE_STATUSES,
        )
        validate_iso_date("Orientation audit review_date", row["review_date"])
        step08.require_text("Orientation audit reviewer", row["reviewer"])
        step08.require_text("Orientation audit detail", row["detail"])
    if complete and len(rows) != step08.parse_nonnegative_int(
        "Scientific review plan locus_target_count", plan["locus_target_count"]
    ):
        step08.fail(
            "Complete orientation audit row count differs from "
            "locus_target_count."
        )
    if complete and rows and observed_orientations != set(step08.ORIENTATIONS):
        step08.fail("Complete orientation audit must cover both required orientations.")
    del review_id


def validate_annotation_evidence(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    plan: Mapping[str, str],
    complete: bool,
) -> None:
    step08.ensure_unique(rows, "audit_id", "Annotation audit")
    observed_cases: set[str] = set()
    observed_strands: set[str] = set()
    observed_orientations: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        result = validate_candidate_reference(
            f"Annotation audit row {row_number}",
            row["candidate_id"],
            candidates,
        )
        step08.validate_enum(
            "Annotation audit orientation", row["orientation"], step08.ORIENTATIONS
        )
        if row["annotation_strand"] not in ("+", "-"):
            step08.fail("Annotation audit annotation_strand must be + or -.")
        if any(
            row[column] != result[column]
            for column in (
                "chromosome",
                "position",
                "orientation",
                "annotation_strand",
            )
        ):
            step08.fail("Annotation audit candidate identity differs from Step 09.")
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
                step08.fail(
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
                step08.fail(f"Annotation audit {column} must be TRUE or FALSE.")
        for column in ("expected_gene_ids", "expected_transcript_ids"):
            step08.require_text(f"Annotation audit {column}", row[column], allow_na=True)
        step08.validate_enum(
            "Annotation audit assignment_status",
            row["assignment_status"],
            ANNOTATION_ASSIGNMENT_STATUSES,
        )
        step08.validate_enum(
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
            step08.fail(
                "Annotation audit assignment_status=match conflicts with "
                "observed/expected fields."
            )
        if row["assignment_status"] == "mismatch" and expected_matches:
            step08.fail(
                "Annotation audit assignment_status=mismatch has no observed "
                "difference."
            )
        observed_cases.add(row["case_type"])
        observed_strands.add(row["annotation_strand"])
        observed_orientations.add(row["orientation"])
        validate_iso_date("Annotation audit review_date", row["review_date"])
        step08.require_text("Annotation audit reviewer", row["reviewer"])
        step08.require_text("Annotation audit detail", row["detail"])
    if complete:
        required_cases = set(plan["required_annotation_cases"].split(","))
        if not required_cases.issubset(observed_cases):
            step08.fail("Complete annotation audit is missing required case types.")
        if observed_strands != {"+", "-"}:
            step08.fail("Complete annotation audit must cover both annotation strands.")
        if observed_orientations != set(step08.ORIENTATIONS):
            step08.fail("Complete annotation audit must cover both orientations.")


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
                    step09.count_status(selected, "test_status", "tested")
                ),
                "step09_not_target": str(
                    step09.count_status(
                        selected, "test_status", "not_target_change"
                    )
                ),
                "step09_missing_counts": str(
                    step09.count_status(selected, "test_status", "missing_counts")
                ),
                "step09_low_coverage": str(
                    step09.count_status(selected, "test_status", "low_coverage")
                ),
                "step09_degenerate": str(
                    step09.count_status(
                        selected, "test_status", "degenerate_table"
                    )
                ),
                "step09_below_mean_dp": str(
                    step09.count_status(selected, "call_status", "below_mean_dp")
                ),
                "step09_background_not_passed": str(
                    step09.count_status(
                        selected, "call_status", "background_not_passed"
                    )
                ),
                "step09_fdr_not_met": str(
                    step09.count_status(selected, "call_status", "fdr_not_met")
                ),
                "step09_effect_not_met": str(
                    step09.count_status(selected, "call_status", "effect_not_met")
                ),
                "step09_significant_up": str(
                    step09.count_status(selected, "call_status", "significant_up")
                ),
                "step09_significant_down": str(
                    step09.count_status(selected, "call_status", "significant_down")
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
            step08.fail("QC funnel contains a duplicate partition/orientation scope.")
        seen.add(scope)
        expected = expected_by_scope.get(scope)
        if expected is None:
            step08.fail("QC funnel references an undeclared partition/orientation.")
        for column in compared_columns:
            if row[column] != expected[column]:
                step08.fail(
                    f"QC funnel {scope[0]}/{scope[1]} {column} "
                    "does not reconcile."
                )
    if complete and seen != set(expected_by_scope):
        step08.fail("Complete QC funnel does not cover every partition/orientation.")


def validate_replicate_effects(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    sample_rows: Sequence[Mapping[str, str]],
    summary: Mapping[str, str],
    complete: bool,
) -> None:
    replicates, pairs = step09.paired_samples(
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
            step08.fail(
                "Replicate-effects evidence may only summarize successfully "
                "tested candidates."
            )
        replicate = row["replicate"]
        if replicate not in replicates:
            step08.fail("Replicate-effects evidence references an unknown replicate.")
        key = (row["candidate_id"], replicate)
        if key in seen:
            step08.fail("Replicate-effects evidence contains a duplicate stratum row.")
        seen.add(key)
        control_sample, treatment_sample = pairs[replicate]
        if (
            row["control_sample"] != control_sample
            or row["treatment_sample"] != treatment_sample
        ):
            step08.fail("Replicate-effects sample pairing differs from the manifest.")
        if any(
            row[column] != result[column]
            for column in ("partition_id", "orientation")
        ):
            step08.fail("Replicate-effects candidate scope differs from Step 09.")
        for prefix, sample in (
            ("control", control_sample),
            ("treatment", treatment_sample),
        ):
            for metric in ("dp", "ad", "af"):
                if row[f"{prefix}_{metric}"] != result[
                    f"{metric.upper()}__{sample}"
                ]:
                    step08.fail(
                        "Replicate-effects counts differ from Step 09 "
                        f"for candidate {row['candidate_id']}."
                    )
        control_af = step08.parse_number("Replicate-effects control_af", row["control_af"])
        treatment_af = step08.parse_number(
            "Replicate-effects treatment_af", row["treatment_af"]
        )
        delta = step08.parse_number(
            "Replicate-effects treatment_control_difference",
            row["treatment_control_difference"],
        )
        if (
            control_af is None
            or treatment_af is None
            or delta is None
            or not values_close(delta, treatment_af - control_af)
        ):
            step08.fail("Replicate-effects treatment-control difference is invalid.")
        expected_direction = (
            "concordant_up"
            if delta > 0
            else ("concordant_down" if delta < 0 else "no_change")
        )
        if row["direction_status"] != expected_direction:
            step08.fail(
                "Replicate-effects direction_status conflicts with the "
                "treatment-control difference."
            )
        validate_iso_date("Replicate-effects review_date", row["review_date"])
    if complete:
        if not rows:
            step08.fail(
                "Complete replicate-effects evidence must contain at least "
                "one tested candidate."
            )
        candidate_replicates: dict[str, set[str]] = {}
        for candidate_id, replicate in seen:
            candidate_replicates.setdefault(candidate_id, set()).add(replicate)
        for candidate_id, observed in candidate_replicates.items():
            if observed != set(replicates):
                step08.fail(
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
                step08.fail("Primary sensitivity row must reference the Step 09 summary.")
            if summary != primary_summary:
                step08.fail("Primary sensitivity summary differs from Step 09.")
        elif analysis_id == plan["primary_analysis_id"]:
            step08.fail("The primary sensitivity row must use is_primary=TRUE.")
        for column in summary_fields:
            if row[column] != summary[column]:
                step08.fail(
                    f"Sensitivity matrix row {row_number} {column} "
                    "differs from its analysis summary."
                )
        validate_iso_date("Sensitivity matrix review_date", row["review_date"])
    if complete and (
        observed_ids != expected_ids or primary_count != 1
    ):
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
        if row["selection_policy_version"] != plan[
            "candidate_selection_policy_version"
        ]:
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
            step08.fail("Candidate adjudication contains a duplicate candidate/set pair.")
        seen.add(key)
        validate_supporting_ids(
            "Candidate adjudication supporting_evidence_ids",
            row["supporting_evidence_ids"],
            evidence_ids,
        )
        validate_iso_date(
            "Candidate adjudication review_date", row["review_date"]
        )
        step08.validate_enum(
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
            step08.validate_enum(
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
        row["evidence_id"]: row["evidence_status"]
        for row in evidence_rows
    }
    evidence_ids = set(evidence_status_by_id)
    seen: set[str] = set()
    decisions: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        dimension = row["decision_dimension"]
        step08.validate_enum(
            f"Scientific decisions row {row_number} dimension",
            dimension,
            DECISION_DIMENSIONS,
        )
        if dimension in seen:
            step08.fail("Scientific decisions contains duplicate decision dimensions.")
        seen.add(dimension)
        step08.validate_enum(
            "Scientific decision evidence_status",
            row["evidence_status"],
            EVIDENCE_STATUSES,
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
            DECISION_STATUSES,
        )
        step08.validate_enum(
            "Scientific decision rerun_scope",
            row["rerun_scope"],
            RERUN_SCOPES,
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
                    "incomplete evidence: "
                    + ",".join(unsupported)
                )
            step08.require_text("Scientific decision value", row["decision_value"])
            validate_iso_date(
                "Scientific decision decision_date", row["decision_date"]
            )
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
        if (row["rerun_required"] == "FALSE") != (
            row["rerun_scope"] == "none"
        ):
            step08.fail(
                "Scientific decision rerun_required must be FALSE exactly "
                "when rerun_scope=none."
            )
    if complete and seen != set(DECISION_DIMENSIONS):
        step08.fail("Complete scientific decisions do not cover every decision dimension.")
    if complete and any(value == "pending" for value in decisions.values()):
        step08.fail("A complete science review cannot contain pending decisions.")
    if (
        decisions.get("orientation") not in (None, "pending")
        and decisions["orientation"] != plan["orientation_status"]
    ):
        step08.fail(
            "The recorded orientation decision must equal plan "
            "orientation_status."
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


def validate_computational_evidence(
    rows: Sequence[Mapping[str, str]],
    plan: Mapping[str, str],
    evidence_rows: Sequence[Mapping[str, str]],
    input_hashes: dict[Path, str],
) -> None:
    seen: dict[str, Mapping[str, str]] = {}
    seen_roles: dict[str, str] = {}
    complete_evidence_ids = {
        row["evidence_id"]
        for row in evidence_rows
        if row["evidence_category"] == "computational_validation"
        and row["evidence_status"] == "complete"
    }
    payload_counts = {evidence_id: 0 for evidence_id in complete_evidence_ids}
    for row_number, row in enumerate(rows, start=2):
        step08.validate_enum(
            "Computational validation scope",
            row["validation_scope"],
            tuple(COMPUTATIONAL_SCOPE_ROLES),
        )
        if row["validation_scope"] in seen:
            step08.fail("Computational validation contains a duplicate scope.")
        seen[row["validation_scope"]] = row
        role = COMPUTATIONAL_SCOPE_ROLES[row["validation_scope"]]
        if role in seen_roles:
            step08.fail(
                "Computational validation scopes "
                f"{seen_roles[role]} and {row['validation_scope']} both map "
                f"to evidence role {role}."
            )
        seen_roles[role] = row["validation_scope"]
        step08.validate_enum(
            f"Computational validation row {row_number} status",
            row["validation_status"],
            COMPUTATIONAL_VALIDATION_STATUSES,
        )
        step08.require_text(
            f"Computational validation row {row_number} reviewer",
            row["reviewer"],
        )
        step08.require_text(
            f"Computational validation row {row_number} notes",
            row["notes"],
        )
        validate_iso_date(
            f"Computational validation row {row_number} evidence_date",
            row["evidence_date"],
        )
        if row["exit_code"] != NA_VALUE:
            if not re.fullmatch(r"-?[0-9]+", row["exit_code"]):
                step08.fail("Computational validation exit_code must be an integer or NA.")
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
            step08.fail("Computational validation scheduler_state is unsupported.")
        if row["validation_status"] in ("passed", "proven") and (
            row["exit_code"] != "0"
            or row["scheduler_state"] not in (NA_VALUE, "COMPLETED")
        ):
            step08.fail(
                "Passed/proven computational validation requires exit_code=0 "
                "and a non-failing scheduler state."
            )
        path_is_na = row["evidence_path"] == NA_VALUE
        hash_is_na = row["evidence_sha256"] == NA_VALUE
        if path_is_na != hash_is_na:
            step08.fail(
                "Computational validation evidence path and hash must both "
                "be present or both be NA."
            )
        if not path_is_na:
            path = step08.require_file(
                "Computational validation evidence",
                step09.resolve_recorded_path(row["evidence_path"]),
            )
            step08.validate_hash(
                "Computational validation evidence_sha256",
                row["evidence_sha256"],
            )
            observed = sha256_file(path)
            if observed != row["evidence_sha256"]:
                step08.fail("Computational validation evidence hash differs.")
            input_hashes[path] = observed
        if row["evidence_id"] in complete_evidence_ids:
            payload_counts[row["evidence_id"]] += 1
            plan_field = COMPUTATIONAL_SCOPE_PLAN_FIELDS[
                row["validation_scope"]
            ]
            expected_status = plan[plan_field]
            if row["validation_status"] != expected_status:
                step08.fail(
                    f"Computational validation scope "
                    f"{row['validation_scope']} status "
                    f"{row['validation_status']} does not exactly support "
                    f"review-plan {plan_field}={expected_status}."
                )
    empty_complete = sorted(
        evidence_id
        for evidence_id, count in payload_counts.items()
        if count == 0
    )
    if empty_complete:
        step08.fail(
            "Complete computational-validation evidence must contain at "
            "least one validation scope row: "
            + ",".join(empty_complete)
        )
    claim_specs = {
        ("local_test_status", "passed"): {"local_test"},
        ("local_test_status", "failed"): {"local_test"},
        ("runtime_validation_status", "passed"): {
            "runtime_log",
            "runtime_output",
        },
        ("runtime_validation_status", "failed"): {"runtime_log"},
        ("cluster_dry_run_status", "passed"): {"cluster_dry_run"},
        ("cluster_dry_run_status", "failed"): {"cluster_dry_run"},
        ("cluster_proof_status", "proven"): {
            "cluster_scheduler",
            "cluster_log",
            "cluster_output",
        },
        ("cluster_proof_status", "failed"): {"cluster_log"},
    }
    for (plan_field, expected_status), required_roles in claim_specs.items():
        if plan[plan_field] != expected_status:
            continue
        matching = [
            row
            for row in rows
            if row["evidence_id"] in complete_evidence_ids
            and COMPUTATIONAL_SCOPE_PLAN_FIELDS[row["validation_scope"]]
            == plan_field
            and row["validation_status"] == expected_status
        ]
        if not matching:
            step08.fail(
                f"{plan_field} is claimed in the review plan without matching "
                "computational-validation evidence."
            )
        matching_by_role = {
            COMPUTATIONAL_SCOPE_ROLES[row["validation_scope"]]: row
            for row in matching
        }
        missing_roles = sorted(required_roles - set(matching_by_role))
        if missing_roles:
            step08.fail(
                f"{plan_field}={expected_status} requires computational "
                "evidence roles: "
                + ",".join(missing_roles)
            )
        roles_requiring_payload_paths = (
            required_roles
            if plan_field
            in (
                "runtime_validation_status",
                "cluster_dry_run_status",
                "cluster_proof_status",
            )
            else set()
        )
        missing_paths = sorted(
            role
            for role in roles_requiring_payload_paths
            if matching_by_role[role]["evidence_path"] == NA_VALUE
            or matching_by_role[role]["evidence_sha256"] == NA_VALUE
        )
        if missing_paths:
            step08.fail(
                f"{plan_field}={expected_status} requires explicit paths "
                "and hashes for evidence roles: "
                + ",".join(missing_paths)
            )
        if plan_field in (
            "cluster_dry_run_status",
            "cluster_proof_status",
        ) and expected_status in ("passed", "proven") and matching_by_role[
            (
                "cluster_dry_run"
                if plan_field == "cluster_dry_run_status"
                else (
                    "cluster_scheduler"
                    if expected_status == "proven"
                    else "cluster_log"
                )
            )
        ]["scheduler_state"] != "COMPLETED":
            step08.fail(f"{plan_field} claims require scheduler_state=COMPLETED.")
    if (
        aggregate_evidence_status(
            evidence_rows, "computational_validation"
        )
        == "complete"
        and not rows
    ):
        step08.fail(
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
                step08.fail(
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
        evidence_rows,
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
                step08.fail(
                    "science_review_complete_exploratory requires every "
                    f"evidence category complete or justified not_applicable; "
                    f"{category} is {status}."
                )
        if aggregate_evidence_status(evidence_rows, "decisions") != "complete":
            step08.fail(
                "science_review_complete_exploratory requires explicit "
                "completed decisions."
            )
        if selected != adjudicated:
            step08.fail(
                "science_review_complete_exploratory requires complete "
                "candidate adjudication coverage."
            )
    if plan["cluster_proof_status"] == "proven" and aggregate_evidence_status(
        evidence_rows, "computational_validation"
    ) != "complete":
        step08.fail(
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
        step08.fail("Internal review-summary schema construction is inconsistent.")
    return row


def build_context(arguments: argparse.Namespace) -> tuple[
    ReviewContext,
    dict[str, tuple[tuple[str, ...], list[dict[str, str]]]],
]:
    step08.validate_safe_id("review_id", arguments.review_id)
    artifacts: dict[str, Artifact] = {}
    input_hashes: dict[Path, str] = {}

    plan_table, plan, _allowed_analyses = validate_review_plan(
        arguments.review_plan, arguments.review_id
    )
    register_artifact(
        artifacts,
        input_hashes,
        "review_plan",
        artifact_from_table("Scientific review plan", plan_table),
    )
    sample_table, sample_ids, sample_rows = step08.validate_sample_manifest(
        arguments.sample_manifest
    )
    register_artifact(
        artifacts,
        input_hashes,
        "sample_manifest",
        artifact_from_table("Sample manifest", sample_table),
    )
    partition_table = step08.validate_partition_manifest(
        arguments.partition_manifest
    )
    register_artifact(
        artifacts,
        input_hashes,
        "partition_manifest",
        artifact_from_table("Partition manifest", partition_table),
    )
    sample_hash = artifacts["sample_manifest"].sha256
    partition_hash = artifacts["partition_manifest"].sha256

    step08_inputs = step08.validate_step08_inputs(
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
    step08_sites = step08.validate_step08_sites(
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
    step08_summary = step08.validate_step08_summary(
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
        step08.fail(
            "Step 09 analysis directory basename must equal "
            "primary_analysis_id."
        )
    paths = step09_paths(analysis_dir, analysis_id)
    all_sites = step09.validate_step09_results(
        "Step 09 all-sites",
        paths["step09_all_sites"],
        sample_ids,
        analysis_id,
        step08_sites.rows,
    )
    if [row["candidate_id"] for row in all_sites.rows] != [
        row["candidate_id"] for row in step08_sites.rows
    ]:
        step08.fail(
            "Step 09 all-sites candidate order/universe differs from Step 08."
        )
    register_artifact(
        artifacts,
        input_hashes,
        "step09_all_sites",
        artifact_from_table("Step 09 all-sites", all_sites),
    )
    significant = step09.validate_step09_results(
        "Step 09 significant-sites",
        paths["step09_significant_sites"],
        sample_ids,
        analysis_id,
        step08_sites.rows,
    )
    step09.validate_significant_subset(all_sites.rows, significant.rows)
    register_artifact(
        artifacts,
        input_hashes,
        "step09_significant_sites",
        artifact_from_table("Step 09 significant-sites", significant),
    )
    step09_summary_table = step09.validate_step09_summary(
        paths["step09_summary"],
        analysis_id,
        step08_inputs.rows[0]["cohort_id"],
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
    step09.validate_step09_result_semantics(
        all_sites.rows, step09_summary_table.rows[0], sample_rows
    )
    register_artifact(
        artifacts,
        input_hashes,
        "step09_summary",
        artifact_from_table("Step 09 summary", step09_summary_table),
    )
    mutation = step09.validate_mutation_spectrum(
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
        pdf_path = step08.require_file(label, paths[key])
        step09.validate_pdf(label, pdf_path)
        register_artifact(
            artifacts,
            input_hashes,
            key,
            artifact_from_binary(label, pdf_path),
        )
    if plan["orientation_policy"] != step09_summary_table.rows[0][
        "orientation_policy"
    ]:
        step08.fail("Scientific review plan orientation policy differs from Step 09.")

    evidence_manifest, evidence_rows, category_rows, evidence_index = (
        validate_evidence_manifest(
            arguments.evidence_manifest,
            arguments.review_id,
            plan,
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
        step08.fail("Internal Step 09c output ordering is inconsistent.")
    return context, output_tables


def confirm_inputs_unchanged(input_hashes: Mapping[Path, str]) -> None:
    for path, expected_hash in input_hashes.items():
        if not path.is_file():
            step08.fail(f"An input disappeared before publication: {path}")
        observed_hash = sha256_file(path)
        if observed_hash != expected_hash:
            step08.fail(f"An input changed before publication: {path}")


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
        step08.fail(
            "Step 09c output is locked; inspect and preserve the owner "
            f"metadata before recovery: {lock_path}"
        )
    except OSError as exc:
        step08.fail(f"Could not acquire Step 09c lock {lock_path}: {exc}")
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
        step08.fail(f"Could not write Step 09c lock metadata: {exc}")


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
            step08.fail(f"Staged Step 09c {key} content changed after writing.")
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
        step08.fail(f"Could not create Step 09c output directory {output_dir}: {exc}")
    if not output_dir.is_dir():
        step08.fail(f"Step 09c output path is not a directory: {output_dir}")

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
            step08.fail(
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
            step08.fail("Refusing to reuse an existing Step 09c run-token path.")
        except OSError as exc:
            step08.fail(f"Could not create Step 09c transaction paths: {exc}")

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
                step08.fail(f"Published Step 09c {key} content is invalid.")
            if sha256_file(final.path) != staged_hashes[key]:
                step08.fail(f"Published Step 09c {key} hash is invalid.")
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
                step08.fail(
                    f"{exc}\nStep 09c rollback was incomplete; lock and "
                    f"recovery paths were retained: {lock_path}"
                )
        if isinstance(exc, ContractError):
            raise
        step08.fail(f"Step 09c publication failed: {exc}")
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
