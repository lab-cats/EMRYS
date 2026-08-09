"""Deterministic status reduction for canonical run summaries."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .core import ContractValidationError

RUN_SUMMARY_STATUS_FIELDS = (
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
)
AGGREGATE_ARTIFACT_STATES = (
    "failed",
    "incomplete",
    "missing",
    "externally_unavailable",
)


def artifact_rollup_state(artifact: dict[str, Any]) -> str:
    if artifact["completion_status"] in {"complete", "failed"}:
        return artifact["completion_status"]
    availability_status = artifact["availability_status"]
    if availability_status in {"missing", "externally_unavailable"}:
        return availability_status
    return "incomplete"


def aggregate_equal_or_mixed(values: Iterable[str]) -> str:
    observed = list(values)
    if not observed:
        raise ContractValidationError("cannot aggregate an empty status set")
    return observed[0] if len(set(observed)) == 1 else "mixed"


def aggregate_artifact_state(artifacts: list[dict[str, Any]]) -> str:
    required_artifacts = [
        artifact for artifact in artifacts if artifact["expectation"]["required"]
    ]
    considered = required_artifacts or artifacts
    states = [artifact_rollup_state(artifact) for artifact in considered]
    return next(
        (state for state in AGGREGATE_ARTIFACT_STATES if state in states),
        "complete",
    )


def artifact_status_dimensions(artifact: dict[str, Any]) -> dict[str, str]:
    return {
        "implementation_status": artifact["implementation"]["status"],
        "local_test_status": artifact["local_testing"]["status"],
        "runtime_validation_status": artifact["runtime_validation"]["status"],
        "cluster_dry_run_status": artifact["cluster_validation"]["dry_run_status"],
        "cluster_proof_status": artifact["cluster_validation"]["proof_status"],
    }


def scope_key(scope: dict[str, Any]) -> tuple[str, str, str]:
    return scope["step_id"], scope["scope_type"], scope["scope_id"]
