"""Deterministic status reduction for canonical run summaries."""

from __future__ import annotations

from typing import Any

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
