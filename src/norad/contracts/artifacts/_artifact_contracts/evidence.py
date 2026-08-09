"""Computational status and evidence-reference semantic rules."""

from __future__ import annotations

from typing import Any

from .definitions import (
    CLUSTER_VALIDATION_REQUIREMENTS,
    CLUSTER_VALIDATION_TRIGGER_STATUSES,
    COMPUTATIONAL_STATUS_ROLE_REQUIREMENTS,
    ContractValidationError,
)


def require_status_evidence(
    *,
    label: str,
    status: str,
    evidence: list[dict[str, Any]],
    evidence_statuses: set[str],
) -> None:
    if status in evidence_statuses and not evidence:
        raise ContractValidationError(
            f"{label} status {status!r} requires at least one evidence record"
        )


def require_evidence_roles(
    *,
    label: str,
    evidence: list[dict[str, Any]],
    required_roles: set[str],
) -> None:
    observed_roles = {record["role"] for record in evidence}
    missing_roles = sorted(required_roles - observed_roles)
    if missing_roles:
        raise ContractValidationError(
            f"{label} requires evidence roles: " + ", ".join(missing_roles)
        )


def validate_evidence_references(
    evidence: list[dict[str, Any]],
    label: str,
    *,
    allow_shared_evidence_ids: bool,
) -> None:
    if not allow_shared_evidence_ids:
        for field in ("evidence_id", "role", "path"):
            if len({record[field] for record in evidence}) != len(evidence):
                raise ContractValidationError(
                    f"{label} contains duplicate evidence {field}"
                )
        return
    if len(
        {
            (
                record["evidence_id"],
                record["role"],
                record["path"],
                record["sha256"],
            )
            for record in evidence
        }
    ) != len(evidence):
        raise ContractValidationError(
            f"{label} contains a duplicate evidence reference"
        )


def validate_computational_statuses(
    *,
    label: str,
    local_testing: dict[str, Any],
    runtime_validation: dict[str, Any],
    cluster_validation: dict[str, Any],
    allow_shared_evidence_ids: bool = False,
) -> None:
    status_scopes = (
        ("local testing", local_testing),
        ("runtime validation", runtime_validation),
        ("cluster validation", cluster_validation),
    )
    for scope_name, scope in status_scopes:
        validate_evidence_references(
            scope["evidence"],
            f"{label} {scope_name}",
            allow_shared_evidence_ids=allow_shared_evidence_ids,
        )
    for scope_name, scope in status_scopes[:2]:
        scope_status = scope["status"]
        scope_evidence = scope["evidence"]
        scope_label = f"{label} {scope_name}"
        require_status_evidence(
            label=scope_label,
            status=scope_status,
            evidence=scope_evidence,
            evidence_statuses={"passed", "failed"},
        )
        if required_roles := COMPUTATIONAL_STATUS_ROLE_REQUIREMENTS[scope_name].get(
            scope_status
        ):
            require_evidence_roles(
                label=scope_label,
                evidence=scope_evidence,
                required_roles=required_roles,
            )
    if (
        runtime_validation["status"] == "blocked"
        and not runtime_validation["detail"].strip()
    ):
        raise ContractValidationError(
            f"{label} blocked runtime validation requires a detail"
        )
    cluster_statuses = {
        cluster_validation["dry_run_status"],
        cluster_validation["proof_status"],
    }
    if (
        CLUSTER_VALIDATION_TRIGGER_STATUSES & cluster_statuses
        and not (cluster_validation["evidence"])
    ):
        raise ContractValidationError(
            f"{label} passed, failed, or proven cluster validation requires "
            "at least one inspected evidence record"
        )
    for (
        scope_name,
        scope_field,
        triggering_statuses,
        required_roles,
    ) in CLUSTER_VALIDATION_REQUIREMENTS:
        if cluster_validation[scope_field] in triggering_statuses:
            require_evidence_roles(
                label=f"{label} {scope_name}",
                evidence=cluster_validation["evidence"],
                required_roles=required_roles,
            )
    if (
        cluster_validation["proof_status"] == "proven"
        and runtime_validation["status"] != "passed"
    ):
        raise ContractValidationError(
            f"{label} cluster proof requires passed runtime validation"
        )
