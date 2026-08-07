"""Transaction and scientific-state reconciliation coordinators."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

from .contracts import contracts
from .core import issue
from .models import ArtifactIndexError, Inspection
from .reconcile_native import (
    mark_native_transaction_failed,
    reconcile_step00c,
    reconcile_step06,
    reconcile_step07,
    reconcile_step08,
)
from .reconcile_review import reconcile_step09c
from .reconcile_step09 import reconcile_step09

def reconcile_native_transactions(
    inspections: Sequence[Inspection],
) -> None:
    source_lookup = {
        inspection.resolved_path: inspection for inspection in inspections
    }
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        row = inspection.row
        grouped[(row["step_id"], row["scope_type"], row["scope_id"])].append(
            inspection
        )
    marker_adapters = {
        "00c": "step00c_reference_dict_v1",
        "06": "step06_orientation_counts_v1",
        "07": "step07_mpileup_receipt_v1",
        "08": "step08_summary_v1",
        "09": "step09_cmh_summary_v1",
        "09c": "step09c_review_summary_v1",
    }
    validators = {
        "00c": lambda members: reconcile_step00c(members),
        "06": lambda members: reconcile_step06(members),
        "07": lambda members: reconcile_step07(members),
        "08": lambda members: reconcile_step08(members, source_lookup),
        "09": lambda members: reconcile_step09(members, source_lookup),
        "09c": lambda members: reconcile_step09c(members, source_lookup),
    }
    dependency_order = {
        "00c": 0,
        "06": 1,
        "07": 2,
        "08": 3,
        "09": 4,
        "09c": 5,
    }
    ordered_scopes = sorted(
        grouped,
        key=lambda scope: (
            dependency_order.get(scope[0], len(dependency_order)),
            scope,
        ),
    )
    for scope in ordered_scopes:
        members = grouped[scope]
        step_id = scope[0]
        validator = validators.get(step_id)
        if validator is None or any(
            member.row["required"] == "true"
            and member.completion_status != "complete"
            for member in members
        ):
            continue
        try:
            validator(members)
        except ArtifactIndexError as exc:
            mark_native_transaction_failed(
                members,
                marker_adapters[step_id],
                f"Scope {scope!r}: {exc}",
            )
            # Propagate this scope failure before validating downstream
            # transactions that explicitly reference one of its members.
            reconcile_scope_transactions(members)


def reconcile_scope_transactions(inspections: Sequence[Inspection]) -> None:
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        row = inspection.row
        grouped[(row["step_id"], row["scope_type"], row["scope_id"])].append(
            inspection
        )
    for scope, members in grouped.items():
        blocking = [
            member
            for member in members
            if member.row["required"] == "true"
            and member.completion_status != "complete"
        ]
        if not blocking:
            continue
        blocking_ids = ", ".join(member.row["artifact_id"] for member in blocking)
        for member in members:
            if member.completion_status != "complete":
                continue
            member.completion_status = "incomplete"
            member.state_reason = (
                "Logical scope transaction is incomplete or invalid."
            )
            member.warnings.append(
                issue(
                    "scope_transaction_incomplete",
                    f"Scope {scope!r} has incomplete/invalid required "
                    f"artifacts: {blocking_ids}",
                    member.row["artifact_id"],
                )
            )


def resolve_scientific_states(
    inspections: Sequence[Inspection],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        row = inspection.row
        grouped[(row["step_id"], row["scope_type"], row["scope_id"])].append(
            inspection
        )
    resolved: dict[tuple[str, str, str], dict[str, Any]] = {}
    for scope, members in grouped.items():
        if scope[0] != "09c" or any(
            member.completion_status != "complete"
            for member in members
            if member.row["required"] == "true"
        ):
            continue
        summary = next(
            (
                member
                for member in members
                if member.row["adapter"] == "step09c_review_summary_v1"
            ),
            None,
        )
        if summary is None or summary.first_row is None:
            continue
        row = summary.first_row
        science_status = row.get("overall_science_status", "")
        if science_status not in {
            "evidence_incomplete",
            "science_review_complete_exploratory",
        }:
            summary.completion_status = "failed"
            summary.state_reason = "Review summary science status is invalid."
            summary.errors.append(
                issue(
                    "science_status_invalid",
                    "Step 09c cannot emit the reserved or unknown science "
                    f"status {science_status!r}",
                    summary.row["artifact_id"],
                )
            )
            reconcile_scope_transactions(members)
            continue
        orientation_status = row.get("orientation_status", "")
        if orientation_status not in {
            "provisional",
            "validated",
            "replacement_required",
        }:
            summary.completion_status = "failed"
            summary.state_reason = "Review summary orientation status is invalid."
            summary.errors.append(
                issue(
                    "orientation_status_invalid",
                    "Step 09c review summary has an unknown orientation "
                    f"status {orientation_status!r}",
                    summary.row["artifact_id"],
                )
            )
            reconcile_scope_transactions(members)
            continue
        orientation_policy = row.get("orientation_policy", "")
        if not contracts.SAFE_ID_RE.fullmatch(orientation_policy):
            summary.completion_status = "failed"
            summary.state_reason = "Review summary orientation policy is invalid."
            summary.errors.append(
                issue(
                    "orientation_policy_invalid",
                    "Step 09c review summary orientation policy must be a "
                    f"safe non-empty ID, observed {orientation_policy!r}",
                    summary.row["artifact_id"],
                )
            )
            reconcile_scope_transactions(members)
            continue
        resolved[scope] = {
            "overall_status": science_status,
            "orientation_status": orientation_status,
            "orientation_policy": orientation_policy,
            "review_id": scope[2],
        }
    return resolved
