"""Computational evidence, cross-category state, and summary assembly."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from .audits import (
    validate_annotation_evidence,
    validate_orientation_evidence,
    validate_qc_funnel,
    validate_replicate_effects,
)
from .contracts import (
    COMPUTATIONAL_SCOPE_PLAN_FIELDS,
    COMPUTATIONAL_SCOPE_ROLES,
    COMPUTATIONAL_VALIDATION_STATUSES,
    NA_VALUE,
    review_package,
    sha256_file,
    step08,
    step09,
)
from .intake import ReviewContext, category_is_complete, validate_iso_date
from ._review_candidates import (
    validate_candidate_adjudication,
    validate_candidate_selection,
)
from ._review_decisions import (
    validate_decisions,
    validate_limitations,
)
from ._review_sensitivity import (
    validate_leave_one_pair_out,
    validate_sensitivity_matrix,
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
                step08.fail(
                    "Computational validation exit_code must be an integer or NA."
                )
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
            plan_field = COMPUTATIONAL_SCOPE_PLAN_FIELDS[row["validation_scope"]]
            expected_status = plan[plan_field]
            if row["validation_status"] != expected_status:
                step08.fail(
                    f"Computational validation scope "
                    f"{row['validation_scope']} status "
                    f"{row['validation_status']} does not exactly support "
                    f"review-plan {plan_field}={expected_status}."
                )
    empty_complete = sorted(
        evidence_id for evidence_id, count in payload_counts.items() if count == 0
    )
    if empty_complete:
        step08.fail(
            "Complete computational-validation evidence must contain at "
            "least one validation scope row: " + ",".join(empty_complete)
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
            and COMPUTATIONAL_SCOPE_PLAN_FIELDS[row["validation_scope"]] == plan_field
            and row["validation_status"] == expected_status
        ]
        if not matching:
            step08.fail(
                f"{plan_field} is claimed in the review plan without matching "
                "computational-validation evidence."
            )
        matching_by_role = {
            COMPUTATIONAL_SCOPE_ROLES[row["validation_scope"]]: row for row in matching
        }
        missing_roles = sorted(required_roles - set(matching_by_role))
        if missing_roles:
            step08.fail(
                f"{plan_field}={expected_status} requires computational "
                "evidence roles: " + ",".join(missing_roles)
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
                "and hashes for evidence roles: " + ",".join(missing_paths)
            )
        if (
            plan_field
            in (
                "cluster_dry_run_status",
                "cluster_proof_status",
            )
            and expected_status in ("passed", "proven")
            and matching_by_role[
                (
                    "cluster_dry_run"
                    if plan_field == "cluster_dry_run_status"
                    else (
                        "cluster_scheduler"
                        if expected_status == "proven"
                        else "cluster_log"
                    )
                )
            ]["scheduler_state"]
            != "COMPLETED"
        ):
            step08.fail(f"{plan_field} claims require scheduler_state=COMPLETED.")
    if (
        review_package.aggregate_evidence_status(
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
    context: ReviewContext,
) -> tuple[dict[str, str], set[tuple[str, str]], set[tuple[str, str]]]:
    plan = context.plan
    evidence_rows = context.evidence_rows
    category_rows = context.category_rows
    candidates = {row["candidate_id"]: row for row in context.step09_all_rows}
    evidence_ids = {row["evidence_id"] for row in evidence_rows}
    primary_analysis_id = plan["primary_analysis_id"]
    for category, rows in category_rows.items():
        for row_number, row in enumerate(rows, start=2):
            if category not in ("sensitivity_matrix", "leave_one_pair_out") and (
                row["analysis_id"] != primary_analysis_id
            ):
                step08.fail(
                    f"{category} row {row_number} must reference the primary analysis."
                )
    validate_orientation_evidence(
        category_rows["orientation_locus_audit"],
        candidates,
        context.sample_rows,
        {row["partition_id"] for row in context.partition_rows},
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
        context.step08_input_rows,
        context.step09_all_rows,
        context.step09_summary["target_rna_change"],
        category_is_complete(evidence_rows, "qc_funnel"),
    )
    validate_replicate_effects(
        category_rows["replicate_effects"],
        candidates,
        context.sample_rows,
        context.step09_summary,
        category_is_complete(evidence_rows, "replicate_effects"),
    )
    validate_sensitivity_matrix(
        category_rows["sensitivity_matrix"],
        plan,
        context.artifacts["step09_summary"].path,
        context.step09_summary,
        context.input_hashes,
        category_is_complete(evidence_rows, "sensitivity_matrix"),
    )
    validate_leave_one_pair_out(
        category_rows["leave_one_pair_out"],
        plan,
        candidates,
        context.sample_rows,
        context.sample_ids,
        context.step09_summary,
        context.input_hashes,
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
        context.input_hashes,
    )

    if plan["overall_science_status"] == "science_review_complete_exploratory":
        for category in review_package.CATEGORY_ORDER:
            status = review_package.aggregate_evidence_status(evidence_rows, category)
            if status not in ("complete", "not_applicable"):
                step08.fail(
                    "science_review_complete_exploratory requires every "
                    f"evidence category complete or justified not_applicable; "
                    f"{category} is {status}."
                )
        if (
            review_package.aggregate_evidence_status(evidence_rows, "decisions")
            != "complete"
        ):
            step08.fail(
                "science_review_complete_exploratory requires explicit "
                "completed decisions."
            )
        if selected != adjudicated:
            step08.fail(
                "science_review_complete_exploratory requires complete "
                "candidate adjudication coverage."
            )
    if (
        plan["cluster_proof_status"] == "proven"
        and review_package.aggregate_evidence_status(
            evidence_rows, "computational_validation"
        )
        != "complete"
    ):
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
        "locus_selection_policy_version": plan["locus_selection_policy_version"],
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
        "orthogonal_evidence_decision": decisions.get("orthogonal_evidence", "pending"),
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
    for category in review_package.CATEGORY_ORDER:
        row[f"{category}_status"] = review_package.aggregate_evidence_status(
            context.evidence_rows, category
        )
    for key in review_package.INPUT_ARTIFACT_KEYS:
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
            "published_output_count": str(len(review_package.OUTPUT_SUFFIXES)),
            "transaction_state": "complete",
        }
    )
    if tuple(row) != review_package.REVIEW_SUMMARY_HEADER:
        step08.fail("Internal review-summary schema construction is inconsistent.")
    return row
