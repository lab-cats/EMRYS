"""Canonical deterministic run-summary document projection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from emrys.reporting._run_summary.models import (
    PRODUCER,
    PRODUCER_VERSION,
    RUN_SUMMARY_SCHEMA_VERSION,
)
from emrys.reporting._run_summary.projection import (
    _build_attempts,
    _build_expected_scopes,
    _build_limitations,
    _build_qc_metrics,
    _build_rollup,
    _build_tools,
    _issue_for_duplicate_metrics,
)
from emrys.reporting._run_summary.transaction import _path_hash, _stable_unique


def _build_document(
    *,
    run_id: str,
    run_contract: dict[str, Any],
    inventory_path: Path,
    inventory_sha256: str,
    inventory_size_bytes: int,
    inventory_rows: list[dict[str, str]],
    artifact_receipt_path: Path,
    artifact_receipt_sha256: str,
    artifact_receipt_size_bytes: int,
    artifact_receipt: dict[str, str],
    artifacts: list[dict[str, Any]],
    generated_at: str,
    git_commit: str,
    analysis_policy_path: Path,
    analysis_policy_sha256: str,
    analysis_policy_size_bytes: int,
    analysis_policy: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    expected_scopes, artifact_scope_order = _build_expected_scopes(artifacts)
    attempts, superseded_attempt_ids = _build_attempts(artifacts)
    qc_metrics, duplicate_metric_ids = _build_qc_metrics(artifacts)
    warnings = _stable_unique(
        issue for artifact in artifacts for issue in artifact["warnings"]
    )
    duplicate_warning = _issue_for_duplicate_metrics(duplicate_metric_ids, artifacts)
    if duplicate_warning is not None:
        warnings.append(duplicate_warning)
    errors = _stable_unique(
        issue for artifact in artifacts for issue in artifact["errors"]
    )
    parameters = {
        "artifact_parameters": [
            {
                "artifact_id": artifact["artifact_id"],
                "values": artifact["parameters"],
            }
            for artifact in artifacts
            if artifact["parameters"]
        ],
        "adapter_transaction": {
            "adapter_attempt_id": artifact_receipt["adapter_attempt_id"],
            "supersedes_adapter_attempt_id": (
                artifact_receipt["supersedes_adapter_attempt_id"] or None
            ),
            "adapter_attempt_history": [
                value
                for value in artifact_receipt["adapter_attempt_history"].split(",")
                if value
            ],
        },
    }
    document = {
        "schema_name": "emrys.run_summary",
        "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "record_type": "run_summary",
        "run_id": run_id,
        "run_contract": run_contract,
        "summary_state": "complete",
        "generated_at": generated_at,
        "inventory": _path_hash(
            inventory_path,
            sha256=inventory_sha256,
            size_bytes=inventory_size_bytes,
            row_count=len(inventory_rows),
            media_type="text/tab-separated-values",
        ),
        "artifact_receipt": _path_hash(
            artifact_receipt_path,
            sha256=artifact_receipt_sha256,
            size_bytes=artifact_receipt_size_bytes,
            row_count=1,
            media_type="text/tab-separated-values",
        ),
        "attempts": attempts,
        "superseded_attempt_ids": superseded_attempt_ids,
        "expected_scopes": expected_scopes,
        "artifacts": artifacts,
        "computational_rollup": _build_rollup(artifacts),
        "tools": _build_tools(artifacts),
        "parameters": parameters,
        "qc_metrics": qc_metrics,
        "limitations": _build_limitations(artifacts=artifacts),
        "analysis_policy": {
            "path": str(analysis_policy_path),
            "sha256": analysis_policy_sha256,
            "size_bytes": analysis_policy_size_bytes,
            "record": analysis_policy,
        },
        "warnings": _stable_unique(warnings),
        "errors": errors,
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": git_commit,
            "created_at": generated_at,
        },
    }
    return document, artifact_scope_order
