"""Scientific-review plan validation."""

from __future__ import annotations

from pathlib import Path

from norad.libraries.alignments import orientation as alignment_orientation

from ._intake_support import split_ids, validate_iso_date
from .contracts import NA_VALUE, Table, read_tsv, review_package, step08


def validate_review_plan(
    value: str | Path, review_id: str
) -> tuple[Table, dict[str, str], set[str]]:
    table = read_tsv("Scientific review plan", value, review_package.REVIEW_PLAN_HEADER)
    if len(table.rows) != 1:
        step08.fail("Scientific review plan must contain exactly one data row.")
    plan = table.rows[0]
    if plan["review_id"] != review_id:
        step08.fail("Scientific review plan review_id differs from --review-id.")
    step08.validate_safe_id("review_id", plan["review_id"])
    step08.validate_safe_id("primary_analysis_id", plan["primary_analysis_id"])
    requested_status = plan["overall_science_status"]
    if requested_status == review_package.RESERVED_SCIENCE_STATUS:
        step08.fail(
            "biological_interpretation_ready is reserved and cannot be "
            "produced by Step 09c."
        )
    step08.validate_enum(
        "overall_science_status", requested_status, review_package.SCIENCE_STATUSES
    )
    step08.validate_enum(
        "implementation_status",
        plan["implementation_status"],
        review_package.IMPLEMENTATION_STATUSES,
    )
    step08.validate_enum(
        "local_test_status",
        plan["local_test_status"],
        review_package.LOCAL_TEST_STATUSES,
    )
    step08.validate_enum(
        "runtime_validation_status",
        plan["runtime_validation_status"],
        review_package.RUNTIME_VALIDATION_STATUSES,
    )
    step08.validate_enum(
        "cluster_dry_run_status",
        plan["cluster_dry_run_status"],
        review_package.CLUSTER_DRY_RUN_STATUSES,
    )
    step08.validate_enum(
        "cluster_proof_status",
        plan["cluster_proof_status"],
        review_package.CLUSTER_PROOF_STATUSES,
    )
    step08.validate_enum(
        "orientation_status",
        plan["orientation_status"],
        review_package.ORIENTATION_STATUSES,
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
    if required_orientations != list(alignment_orientation.ORIENTATIONS):
        step08.fail(
            "required_orientations must be exactly "
            f"{','.join(alignment_orientation.ORIENTATIONS)} in that order."
        )
    required_strands = plan["required_annotation_strands"].split(",")
    if required_strands != ["+", "-"]:
        step08.fail("required_annotation_strands must be exactly +,-.")
    step08.require_text("required_annotation_cases", plan["required_annotation_cases"])
    superseded = split_ids("superseded_analysis_ids", plan["superseded_analysis_ids"])
    sensitivity = split_ids(
        "sensitivity_analysis_ids", plan["sensitivity_analysis_ids"]
    )
    if plan["primary_analysis_id"] in superseded + sensitivity:
        step08.fail(
            "The primary analysis cannot also be superseded or a sensitivity run."
        )
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
                "An exploratory-complete science review requires review_completed_date."
            )
    elif plan["review_completed_date"] != NA_VALUE:
        step08.fail(
            "evidence_incomplete must use review_completed_date=NA so that "
            "review completion is not overstated."
        )
    return table, plan, allowed_analyses
