"""Canonical document, predecessor, and receipt validation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts
from emrys.reporting._artifact_index import api as adapter

from .inputs import _fail, _require_regular_file
from .models import (
    MODULAR_PRODUCER_VERSION,
    MODULAR_RUN_SUMMARY_SCHEMA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    QC_SUMMARY_HEADER,
    QC_SUMMARY_TSV_SCHEMA_VERSION,
    RUN_CONTRACT_FIELDS,
    RUN_SUMMARY_HEADER,
    RUN_SUMMARY_RECEIPT_HEADER,
    RUN_SUMMARY_RECEIPT_SCHEMA_VERSION,
    RUN_SUMMARY_SCHEMA_VERSION,
    RUN_SUMMARY_TSV_SCHEMA_VERSION,
    OutputPaths,
    RunSummaryError,
)
from .projection import _build_qc_rows, _build_summary_rows
from .transaction import _parse_history, _receipt_int


def _validate_document(
    document: dict[str, Any],
    inventory_rows: list[dict[str, str]],
    inventory_path: Path,
    *,
    source_root: Path,
) -> None:
    errors = sorted(
        contracts.schema_validator(
            "run-summary", str(document.get("schema_version", ""))
        ).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        details = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        _fail(f"Run summary failed Draft 2020-12 validation:\n{details}")
    try:
        contracts.validate_run_summary_semantics(
            document,
            source_root=source_root,
        )
        contracts.reconcile_document_inventory(
            "run-summary",
            document,
            inventory_rows,
            inventory_path,
            source_root=source_root,
        )
    except contracts.ContractValidationError as exc:
        _fail(f"Run summary failed semantic validation: {exc}")


def _load_existing_summary_receipt(
    paths: OutputPaths,
) -> tuple[dict[str, str] | None, str | None]:
    states = tuple(path.exists() or path.is_symlink() for path in paths.ordered_outputs)
    if any(states) and not all(states):
        _fail(
            "Existing run-summary output set is partial; preserve it for "
            f"recovery: {paths.output_dir}"
        )
    if not any(states):
        return None, None
    for path in paths.ordered_outputs:
        if path.is_symlink() or not path.is_file():
            _fail(f"Existing run-summary output is unsafe: {path}")
    receipt = adapter.read_exact_tsv(
        paths.receipt,
        RUN_SUMMARY_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    return receipt, contracts.sha256_file(paths.receipt)


def _validate_existing_summary(
    *,
    paths: OutputPaths,
    receipt: Mapping[str, str],
    expected_run_id: str,
    expected_run_contract: Mapping[str, Any],
    source_root: Path,
) -> dict[str, Any]:
    if receipt["run_id"] != expected_run_id:
        _fail("Existing run-summary receipt has the wrong run_id")
    for field in RUN_CONTRACT_FIELDS:
        if receipt[field] != str(expected_run_contract[field]):
            _fail(
                "Existing run-summary receipt has a different immutable "
                f"run-contract field: {field}"
            )
    if receipt["transaction_state"] != "complete":
        _fail("Existing run-summary receipt is not complete")
    for field, expected in (
        ("producer", PRODUCER),
        ("run_summary_tsv_schema_version", RUN_SUMMARY_TSV_SCHEMA_VERSION),
        ("qc_summary_tsv_schema_version", QC_SUMMARY_TSV_SCHEMA_VERSION),
        (
            "run_summary_receipt_schema_version",
            RUN_SUMMARY_RECEIPT_SCHEMA_VERSION,
        ),
    ):
        if receipt[field] != expected:
            _fail(f"Existing run-summary receipt field is invalid: {field}")
    version_pairs = {
        RUN_SUMMARY_SCHEMA_VERSION: PRODUCER_VERSION,
        MODULAR_RUN_SUMMARY_SCHEMA_VERSION: MODULAR_PRODUCER_VERSION,
    }
    if (
        receipt["run_summary_schema_version"] not in version_pairs
        or receipt["producer_version"]
        != version_pairs[receipt["run_summary_schema_version"]]
    ):
        _fail("Existing run-summary receipt field is invalid: producer_version")
    _parse_history(
        receipt,
        id_field="run_summary_attempt_id",
        supersedes_field="supersedes_run_summary_attempt_id",
        history_field="run_summary_attempt_history",
    )
    if not (
        receipt["git_commit"] == "local_build"
        or re.fullmatch(r"[0-9a-f]{40,64}", receipt["git_commit"])
    ):
        _fail("Existing run-summary receipt Git commit is invalid")
    try:
        started_at = datetime.fromisoformat(
            receipt["started_at"].replace("Z", "+00:00")
        )
        finished_at = datetime.fromisoformat(
            receipt["finished_at"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RunSummaryError(
            "Existing run-summary receipt timestamps are invalid"
        ) from exc
    if (
        started_at.tzinfo is None
        or finished_at.tzinfo is None
        or finished_at < started_at
    ):
        _fail("Existing run-summary receipt timestamp ordering is invalid")
    expected_paths = {
        "run_summary_json_path": paths.summary_json,
        "run_summary_tsv_path": paths.summary_tsv,
        "qc_summary_tsv_path": paths.qc_summary,
    }
    for field, expected_path in expected_paths.items():
        if receipt[field] != str(expected_path):
            _fail(f"Existing run-summary receipt path is invalid: {field}")
    for path_field, hash_field in (
        ("run_summary_json_path", "run_summary_json_sha256"),
        ("run_summary_tsv_path", "run_summary_tsv_sha256"),
        ("qc_summary_tsv_path", "qc_summary_tsv_sha256"),
    ):
        path = _require_regular_file(f"Existing {path_field}", receipt[path_field])
        if contracts.sha256_file(path) != receipt[hash_field]:
            _fail(f"Existing run-summary output hash differs: {path}")

    document = contracts.load_json_object(paths.summary_json, "existing run summary")
    if paths.summary_json.read_bytes() != adapter.canonical_json_bytes(document):
        _fail("Existing run-summary JSON is not canonical")
    schema_errors = list(
        contracts.schema_validator(
            "run-summary", str(document.get("schema_version", ""))
        ).iter_errors(document)
    )
    if schema_errors:
        _fail("Existing run-summary JSON fails its schema")
    try:
        contracts.validate_run_summary_semantics(
            document,
            source_root=source_root,
        )
    except contracts.ContractValidationError as exc:
        _fail(f"Existing run-summary JSON is semantically invalid: {exc}")
    if receipt["git_commit"] != document["provenance"]["git_commit"]:
        _fail(
            "Existing run-summary receipt Git commit differs from its "
            "canonical JSON provenance"
        )
    if receipt["run_summary_schema_version"] != document["schema_version"]:
        _fail("Existing run-summary receipt schema differs from its canonical JSON")
    if (
        receipt["producer"] != document["provenance"]["producer"]
        or receipt["producer_version"] != document["provenance"]["producer_version"]
    ):
        _fail(
            "Existing run-summary receipt producer differs from its "
            "canonical JSON provenance"
        )
    adapter_transaction = document["parameters"]["adapter_transaction"]
    if (
        receipt["artifact_adapter_attempt_id"]
        != adapter_transaction["adapter_attempt_id"]
    ):
        _fail(
            "Existing run-summary receipt adapter attempt differs from its "
            "canonical JSON provenance"
        )
    expected_summary_rows = _build_summary_rows(
        document,
        {
            artifact_id: scope_order
            for scope_order, scope in enumerate(document["expected_scopes"], 1)
            for artifact_id in scope["artifact_ids"]
        },
    )
    if paths.summary_tsv.read_bytes() != adapter.tsv_bytes(
        RUN_SUMMARY_HEADER, expected_summary_rows
    ):
        _fail("Existing run-summary TSV differs from its canonical JSON")
    expected_qc_rows = _build_qc_rows(document)
    if paths.qc_summary.read_bytes() != adapter.tsv_bytes(
        QC_SUMMARY_HEADER, expected_qc_rows
    ):
        _fail("Existing QC summary TSV differs from its canonical JSON")
    if receipt["run_summary_tsv_row_count"] != str(len(expected_summary_rows)):
        _fail("Existing run-summary TSV row count is invalid")
    if receipt["qc_summary_tsv_row_count"] != str(len(expected_qc_rows)):
        _fail("Existing QC summary TSV row count is invalid")
    if receipt["published_output_count"] != "4":
        _fail("Existing run-summary receipt published_output_count is invalid")
    if _receipt_int(receipt, "run_summary_json_size_bytes") != (
        paths.summary_json.stat().st_size
    ):
        _fail("Existing run-summary JSON byte size is invalid")
    if _receipt_int(receipt, "artifact_record_count") != len(document["artifacts"]):
        _fail("Existing run-summary artifact count is invalid")
    if (
        _receipt_int(receipt, "inventory_row_count")
        != (document["inventory"]["row_count"])
    ):
        _fail("Existing run-summary inventory row count is invalid")
    if receipt["inventory_path"] != document["inventory"]["path"] or (
        receipt["inventory_sha256"] != document["inventory"]["sha256"]
    ):
        _fail("Existing receipt inventory provenance differs from JSON")
    if (
        receipt["artifact_receipt_path"] != document["artifact_receipt"]["path"]
        or receipt["artifact_receipt_sha256"] != document["artifact_receipt"]["sha256"]
    ):
        _fail("Existing adapter-receipt provenance differs from JSON")
    for field in (
        "inventory_sha256",
        "artifacts_index_sha256",
        "artifact_receipt_sha256",
        "record_set_sha256",
        "run_summary_json_sha256",
        "run_summary_tsv_sha256",
        "qc_summary_tsv_sha256",
    ):
        if not adapter.SHA256_RE.fullmatch(receipt[field]):
            _fail(f"Existing run-summary receipt hash is invalid: {field}")
    if receipt["summary_state"] != document["summary_state"] or (
        receipt["interpretation_boundary"]
        != str(document.get("interpretation_boundary", ""))
    ):
        _fail("Existing run-summary receipt status differs from JSON")
    return document


def _build_receipt_row(
    *,
    run_id: str,
    run_contract: Mapping[str, Any],
    artifact_receipt_path: Path,
    artifact_receipt_sha256: str,
    artifact_receipt: Mapping[str, str],
    inventory_path: Path,
    inventory_sha256: str,
    inventory_row_count: int,
    artifacts_path: Path,
    artifacts_sha256: str,
    summary_json_path: Path,
    summary_json_bytes: bytes,
    summary_tsv_path: Path,
    summary_tsv_bytes: bytes,
    summary_tsv_row_count: int,
    qc_summary_path: Path,
    qc_summary_bytes: bytes,
    qc_summary_row_count: int,
    document: Mapping[str, Any],
    attempt_id: str,
    previous_attempt_id: str | None,
    previous_attempt_history: Sequence[str],
    git_commit: str,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        **{field: run_contract[field] for field in RUN_CONTRACT_FIELDS},
        "artifact_receipt_path": str(artifact_receipt_path),
        "artifact_receipt_sha256": artifact_receipt_sha256,
        "artifact_adapter_attempt_id": artifact_receipt["adapter_attempt_id"],
        "inventory_path": str(inventory_path),
        "inventory_sha256": inventory_sha256,
        "inventory_row_count": inventory_row_count,
        "artifacts_index_path": str(artifacts_path),
        "artifacts_index_sha256": artifacts_sha256,
        "artifact_record_count": len(document["artifacts"]),
        "record_set_sha256": artifact_receipt["record_set_sha256"],
        "run_summary_schema_version": document["schema_version"],
        "run_summary_tsv_schema_version": RUN_SUMMARY_TSV_SCHEMA_VERSION,
        "qc_summary_tsv_schema_version": QC_SUMMARY_TSV_SCHEMA_VERSION,
        "run_summary_receipt_schema_version": (RUN_SUMMARY_RECEIPT_SCHEMA_VERSION),
        "run_summary_json_path": str(summary_json_path),
        "run_summary_json_sha256": adapter.sha256_bytes(summary_json_bytes),
        "run_summary_json_size_bytes": len(summary_json_bytes),
        "run_summary_tsv_path": str(summary_tsv_path),
        "run_summary_tsv_sha256": adapter.sha256_bytes(summary_tsv_bytes),
        "run_summary_tsv_row_count": summary_tsv_row_count,
        "qc_summary_tsv_path": str(qc_summary_path),
        "qc_summary_tsv_sha256": adapter.sha256_bytes(qc_summary_bytes),
        "qc_summary_tsv_row_count": qc_summary_row_count,
        "summary_state": document["summary_state"],
        "interpretation_boundary": str(document.get("interpretation_boundary", "")),
        "published_output_count": 4,
        "run_summary_attempt_id": attempt_id,
        "supersedes_run_summary_attempt_id": previous_attempt_id or "",
        "run_summary_attempt_history": ",".join(
            [*previous_attempt_history, attempt_id]
        ),
        "producer": PRODUCER,
        "producer_version": document["provenance"]["producer_version"],
        "git_commit": git_commit,
        "started_at": started_at,
        "finished_at": finished_at,
        "transaction_state": "complete",
    }
