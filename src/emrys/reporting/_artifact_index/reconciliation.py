"""Artifact transaction reconciliation coordinators."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING

from emrys.contracts.artifacts import api as contracts

from .core import issue
from .models import ArtifactIndexError, Inspection
from .reconcile_native import (
    NativeSourceIndex,
    mark_native_transaction_failed,
    reconcile_step00c,
    reconcile_step06,
    reconcile_step07,
    reconcile_step08,
)
from .reconcile_step09 import reconcile_step09
from .reconcile_step10 import reconcile_step10

if TYPE_CHECKING:
    from pathlib import Path


def _group_by_scope(
    inspections: Sequence[Inspection],
) -> dict[tuple[str, str, str], list[Inspection]]:
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        grouped[contracts.scope_key(inspection.row)].append(inspection)
    return grouped


def reconcile_native_transactions(
    inspections: Sequence[Inspection],
    *,
    source_root: Path,
) -> None:
    sources = NativeSourceIndex(
        source_root=source_root,
        by_path={inspection.resolved_path: inspection for inspection in inspections},
    )
    grouped = _group_by_scope(inspections)
    marker_adapters = {
        "00c": "step00c_reference_dict_v1",
        "06": "step06_orientation_counts_v1",
        "07": "step07_mpileup_receipt_v1",
        "08": "step08_inputs_v1",
        "09": "step09_cmh_summary_v1",
        "10": "step10_context_receipt_v1",
    }
    validators = {
        "00c": reconcile_step00c,
        "06": reconcile_step06,
        "07": partial(reconcile_step07, sources=sources),
        "08": partial(reconcile_step08, sources=sources),
        "09": partial(reconcile_step09, sources=sources),
        "10": partial(reconcile_step10, sources=sources),
    }
    dependency_order = dict(zip(validators, range(len(validators)), strict=True))
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
            member.row["required"] == "true" and member.completion_status != "complete"
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
    grouped = _group_by_scope(inspections)
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
            member.state_reason = "Logical scope transaction is incomplete or invalid."
            member.warnings.append(
                issue(
                    "scope_transaction_incomplete",
                    f"Scope {scope!r} has incomplete/invalid required "
                    f"artifacts: {blocking_ids}",
                    member.row["artifact_id"],
                )
            )
