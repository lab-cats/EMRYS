"""Status, science, and deterministic tabular run-summary projections."""

from __future__ import annotations

import json
from collections import Counter, OrderedDict
from collections.abc import Mapping
from typing import Any

from norad.contracts.artifacts import api as contracts

from .inputs import _fail
from .transaction import _stable_unique


def _artifact_statuses(artifact: Mapping[str, Any]) -> dict[str, str]:
    return contracts.artifact_status_dimensions(dict(artifact))


def _scope_statuses(scope_artifacts: list[dict[str, Any]]) -> dict[str, str]:
    return {
        field: contracts.aggregate_equal_or_mixed(
            _artifact_statuses(artifact)[field] for artifact in scope_artifacts
        )
        for field in contracts.RUN_SUMMARY_STATUS_FIELDS
    }


def _build_expected_scopes(
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    grouped: OrderedDict[tuple[str, str, str], list[dict[str, Any]]] = OrderedDict()
    for artifact in artifacts:
        key = contracts.scope_key(artifact["scope"])
        grouped.setdefault(key, []).append(artifact)

    expected_scopes: list[dict[str, Any]] = []
    artifact_scope_order: dict[str, int] = {}
    for scope_order, (key, scope_artifacts) in enumerate(grouped.items(), 1):
        warnings = _stable_unique(
            issue for artifact in scope_artifacts for issue in artifact["warnings"]
        )
        errors = _stable_unique(
            issue for artifact in scope_artifacts for issue in artifact["errors"]
        )
        status_values = _scope_statuses(scope_artifacts)
        expected_scopes.append(
            {
                "scope": {
                    "step_id": key[0],
                    "scope_type": key[1],
                    "scope_id": key[2],
                },
                "artifact_ids": [
                    artifact["artifact_id"] for artifact in scope_artifacts
                ],
                "aggregate_state": contracts.aggregate_artifact_state(scope_artifacts),
                **status_values,
                "warnings": warnings,
                "errors": errors,
            }
        )
        for artifact in scope_artifacts:
            artifact_scope_order[artifact["artifact_id"]] = scope_order
    return expected_scopes, artifact_scope_order


def _build_attempts(
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    attempts: list[dict[str, Any]] = []
    attempt_index: dict[str, dict[str, Any]] = {}
    superseded: list[str] = []
    for artifact in artifacts:
        for attempt in artifact["attempts"]:
            attempt_id = attempt["attempt_id"]
            prior = attempt_index.get(attempt_id)
            if prior is not None:
                if prior != attempt:
                    _fail(
                        f"Artifact attempt {attempt_id!r} has conflicting definitions"
                    )
                continue
            copy = dict(attempt)
            attempt_index[attempt_id] = copy
            attempts.append(copy)
            parent = attempt["supersedes_attempt_id"]
            if parent is not None and parent not in superseded:
                superseded.append(parent)
    return attempts, superseded


def _build_rollup(
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    states = Counter(
        contracts.artifact_rollup_state(artifact) for artifact in artifacts
    )
    result: dict[str, Any] = {
        "expected_artifact_count": len(artifacts),
        "complete_artifact_count": states["complete"],
        "missing_artifact_count": states["missing"],
        "incomplete_artifact_count": states["incomplete"],
        "failed_artifact_count": states["failed"],
        "externally_unavailable_artifact_count": states["externally_unavailable"],
    }
    for field, value in _scope_statuses(artifacts).items():
        result[field] = value
    return result


def _build_tools(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _stable_unique(tool for artifact in artifacts for tool in artifact["tools"])


def _build_qc_metrics(
    artifacts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str]]:
    counts = Counter(
        metric["metric_id"] for artifact in artifacts for metric in artifact["metrics"]
    )
    metrics = [
        dict(metric)
        for artifact in artifacts
        for metric in artifact["metrics"]
        if counts[metric["metric_id"]] == 1
    ]
    duplicate_ids = {metric_id for metric_id, count in counts.items() if count > 1}
    return metrics, duplicate_ids


def _default_scientific_review() -> dict[str, Any]:
    return {
        "record_state": "missing",
        "source": None,
        "record": None,
        "overall_status": "evidence_incomplete",
    }


def _build_limitations(
    *,
    artifacts: list[dict[str, Any]],
    scientific_review: Mapping[str, Any],
) -> list[dict[str, Any]]:
    def generated_id(base: str, existing: set[str]) -> str:
        candidate = base
        counter = 1
        while candidate in existing:
            candidate = f"{base}.generated{counter}"
            counter += 1
        existing.add(candidate)
        return candidate

    record = scientific_review.get("record")
    limitations = (
        [dict(item) for item in record["limitations"]]
        if isinstance(record, Mapping)
        else [
            {
                "limitation_id": "scientific_review_not_supplied",
                "status": "open",
                "description": (
                    "No explicit committed Step 09c review summary was "
                    "supplied to the run-summary builder."
                ),
                "impact": (
                    "Scientific review remains incomplete and biological "
                    "interpretation is not permitted."
                ),
                "evidence_ids": [],
            }
        ]
    )
    used_ids = {limitation["limitation_id"] for limitation in limitations}
    incomplete_required = [
        artifact["artifact_id"]
        for artifact in artifacts
        if artifact["expectation"]["required"]
        and contracts.artifact_rollup_state(artifact) != "complete"
    ]
    if incomplete_required:
        limitations.append(
            {
                "limitation_id": generated_id(
                    "required_artifacts_not_complete",
                    used_ids,
                ),
                "status": "open",
                "description": (
                    "One or more required expected artifacts are not complete."
                ),
                "impact": (
                    "The run summary is structurally complete, but downstream "
                    "consumers must retain the explicit incomplete states."
                ),
                "evidence_ids": [],
            }
        )
    return _stable_unique(limitations)


def _issue_for_duplicate_metrics(
    duplicate_ids: set[str],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not duplicate_ids:
        return None
    related = [
        artifact["artifact_id"]
        for artifact in artifacts
        if any(metric["metric_id"] in duplicate_ids for metric in artifact["metrics"])
    ]
    return {
        "code": "duplicate_qc_metric_ids_not_promoted",
        "message": (
            "Repeated artifact metric IDs remain available inside artifacts "
            "and the QC TSV but are not copied into the globally unique "
            "top-level qc_metrics array."
        ),
        "related_artifact_ids": related,
        "evidence": [],
    }


def _metric_value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def _build_summary_rows(
    document: Mapping[str, Any],
    artifact_scope_order: Mapping[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_order, artifact in enumerate(document["artifacts"], 1):
        source = artifact["source"]
        statuses = _artifact_statuses(artifact)
        rows.append(
            {
                "run_id": document["run_id"],
                "run_contract_sha256": document["run_contract"]["run_contract_sha256"],
                "summary_state": document["summary_state"],
                "science_status": document["science_status"],
                "artifact_order": artifact_order,
                "scope_order": artifact_scope_order[artifact["artifact_id"]],
                "step_id": artifact["scope"]["step_id"],
                "scope_type": artifact["scope"]["scope_type"],
                "scope_id": artifact["scope"]["scope_id"],
                "artifact_id": artifact["artifact_id"],
                "adapter": artifact["adapter"],
                "required": (
                    "true" if artifact["expectation"]["required"] else "false"
                ),
                "availability_status": artifact["availability_status"],
                "completion_status": artifact["completion_status"],
                "rollup_state": contracts.artifact_rollup_state(artifact),
                **statuses,
                "source_path": "" if source is None else source["path"],
                "source_sha256": "" if source is None else source["sha256"],
                "source_row_count": (
                    ""
                    if source is None or source["row_count"] is None
                    else source["row_count"]
                ),
                "selected_attempt_id": artifact["selected_attempt_id"] or "",
                "warning_count": len(artifact["warnings"]),
                "error_count": len(artifact["errors"]),
            }
        )
    return rows


def _build_qc_rows(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_order, artifact in enumerate(document["artifacts"], 1):
        for metric_order, metric in enumerate(artifact["metrics"], 1):
            value = metric["value"]
            rows.append(
                {
                    "run_id": document["run_id"],
                    "artifact_order": artifact_order,
                    "metric_order": metric_order,
                    "step_id": artifact["scope"]["step_id"],
                    "scope_type": artifact["scope"]["scope_type"],
                    "scope_id": artifact["scope"]["scope_id"],
                    "artifact_id": artifact["artifact_id"],
                    "metric_id": metric["metric_id"],
                    "name": metric["name"],
                    "value": json.dumps(
                        value,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                        allow_nan=False,
                    ),
                    "value_type": _metric_value_type(value),
                    "unit": metric["unit"] or "",
                    "status": metric["status"],
                    "source_artifact_id": (metric["source_artifact_id"] or ""),
                }
            )
    return rows
