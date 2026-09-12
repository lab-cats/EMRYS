"""Canonical deterministic run-summary document projection."""

from __future__ import annotations

import hashlib

from collections.abc import Callable
from pathlib import Path
from typing import Any

from emrys.reporting._run_summary.models import (
    PRODUCER,
    PRODUCER_VERSION,
    RUN_SUMMARY_SCHEMA_VERSION,
    RUN_SUMMARY_HEADER,
    QC_SUMMARY_HEADER,
)
from emrys.reporting._run_summary.projection import (
    _build_attempts,
    _build_expected_scopes,
    _build_limitations,
    _build_qc_metrics,
    _build_rollup,
    _build_tools,
    _issue_for_duplicate_metrics,
    _build_summary_rows,
    _build_qc_rows,
)
from emrys.reporting._run_summary.transaction import _path_hash, _stable_unique
from emrys.reporting._run_summary.validation import _validate_document
from emrys.reporting._artifact_index.core import canonical_json_bytes
from emrys.reporting._artifact_index.records import tsv_bytes


def build_summary(
    *,
    source_root: Path,
    output_dir: Path,
    run_id: str,
    run_contract: dict[str, Any],
    inventory_path: Path,
    inventory_sha256: str,
    inventory_size_bytes: int,
    inventory_rows: list[dict[str, str]],
    run_contract_path: Path,
    run_contract_file_sha256: str,
    publication: dict[str, Any],
    artifacts: list[dict[str, Any]],
    generated_at: str,
    git_commit: str,
    installed_package: dict[str, object],
    scientific_origin: dict[str, Any],
    analysis_policy_binding: dict[str, Any],
) -> tuple[dict[str, Any], bytes, bytes, bytes]:
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
        "run_contract_file": {
            "path": str(run_contract_path),
            "sha256": run_contract_file_sha256,
        },
        "publication": publication,
        "analysis_policy": analysis_policy_binding,
        "attempts": attempts,
        "superseded_attempt_ids": superseded_attempt_ids,
        "expected_scopes": expected_scopes,
        "artifacts": artifacts,
        "computational_rollup": _build_rollup(artifacts),
        "tools": _build_tools(artifacts),
        "parameters": parameters,
        "qc_metrics": qc_metrics,
        "limitations": _build_limitations(artifacts=artifacts),
        "warnings": _stable_unique(warnings),
        "errors": errors,
        "scientific_origin": scientific_origin,
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": git_commit,
            "installed_package": installed_package,
            "created_at": generated_at,
        },
    }
    tables = (
        tsv_bytes(
            RUN_SUMMARY_HEADER, _build_summary_rows(document, artifact_scope_order)
        ),
        tsv_bytes(QC_SUMMARY_HEADER, _build_qc_rows(document)),
    )
    document["tables"] = [
        {
            "path": str(output_dir / f"{run_id}.{suffix}"),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        }
        for suffix, payload in zip(
            ("run_summary.tsv", "qc_summary.tsv"), tables, strict=True
        )
    ]
    _validate_document(
        document, inventory_rows, inventory_path, source_root=source_root
    )
    return document, canonical_json_bytes(document), *tables


def admit_analysis_policy(
    path: Path | None,
    run_contract: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], Callable[[], None]]:
    """Bind the explicit current module policy and its immutable file identity."""

    from emrys.contracts.artifacts import api as contracts
    from emrys.contracts.orchestration import api as orchestration_contracts
    from emrys.reporting.transaction_validation import (
        _snapshot_receipt,
        ReportingTransactionError,
    )
    from .models import RunSummaryError

    if path is None:
        raise RunSummaryError(
            "Run results require an explicit current analysis module policy"
        )
    contracts.validate_resolved_path(str(path), "Analysis policy")
    try:
        snapshot = _snapshot_receipt(path)
    except ReportingTransactionError as exc:
        raise RunSummaryError(str(exc)) from exc
    policy = contracts.load_json_object_bytes(snapshot.payload, "Analysis policy")
    try:
        orchestration_contracts.validate_record("policy", policy)
    except orchestration_contracts.ContractValidationError as exc:
        raise RunSummaryError(f"Analysis policy is invalid: {exc}") from exc
    expected = run_contract["primary_analysis_policy_sha256"]
    if (
        snapshot.sha256 != expected
        or orchestration_contracts.canonical_sha256(policy) != expected
    ):
        raise RunSummaryError(
            "Analysis policy does not match the immutable run contract"
        )
    if policy["analysis_id"] != run_contract["primary_analysis_id"]:
        raise RunSummaryError("Analysis policy identifies another primary analysis")
    if policy["schema_version"] != "emrys.analysis-module-policy.v1":
        raise RunSummaryError("Run results require a current analysis module policy")
    binding = {
        "path": str(path),
        "sha256": snapshot.sha256,
        "size_bytes": snapshot.size_bytes,
    }

    def recheck() -> None:
        try:
            observed = _snapshot_receipt(path)
        except ReportingTransactionError as exc:
            raise RunSummaryError(str(exc)) from exc
        if observed != snapshot:
            raise RunSummaryError(f"Analysis policy changed after admission: {path}")

    return policy, binding, recheck
