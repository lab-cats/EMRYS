"""Artifact records, deterministic indexes, identities, and receipts."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import contracts
from .core import canonical_digest, safe_tsv, sha256_bytes
from .models import (
    ARTIFACT_INDEX_HEADER,
    ARTIFACT_INDEX_SCHEMA_VERSION,
    ARTIFACT_RECEIPT_HEADER,
    ARTIFACT_RECEIPT_SCHEMA_VERSION,
    ARTIFACT_SCHEMA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    RUN_CONTRACT_FIELDS,
    ArtifactIndexError,
    Inspection,
)
from .rosters import STEP_PRODUCERS


def producer_evidence(git_commit: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for step_id, relative_path in STEP_PRODUCERS.items():
        path = contracts.REPO_ROOT / relative_path
        if not path.is_file():
            raise ArtifactIndexError(
                f"Registered producer path is missing: {relative_path}"
            )
        result[step_id] = {
            "status": "implemented",
            "git_commit": git_commit,
            "evidence": [
                {
                    "evidence_id": f"implementation_{step_id}",
                    "role": "implementation",
                    "path": relative_path,
                    "sha256": contracts.sha256_file(path),
                }
            ],
        }
    return result


def build_artifact_record(
    *,
    run_id: str,
    run_contract: dict[str, Any],
    inspection: Inspection,
    implementation: dict[str, Any],
    scientific_state: dict[str, Any] | None,
    git_commit: str,
    created_at: str,
) -> dict[str, Any]:
    return {
        "schema_name": "norad.artifact_record",
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "record_type": "artifact_record",
        "run_id": run_id,
        "run_contract": run_contract,
        "artifact_id": inspection.row["artifact_id"],
        "scope": {
            "step_id": inspection.row["step_id"],
            "scope_type": inspection.row["scope_type"],
            "scope_id": inspection.row["scope_id"],
        },
        "adapter": inspection.row["adapter"],
        "expectation": {
            "required": inspection.row["required"] == "true",
            "source_path": inspection.row["source_path"],
        },
        "availability_status": inspection.availability_status,
        "completion_status": inspection.completion_status,
        "state_reason": inspection.state_reason,
        "attempt_provenance_status": inspection.attempt_provenance_status,
        "attempts": [],
        "selected_attempt_id": None,
        "implementation": implementation,
        "local_testing": {"status": "not_run", "evidence": []},
        "runtime_validation": {
            "status": "not_run",
            "detail": None,
            "evidence": [],
        },
        "cluster_validation": {
            "dry_run_status": "not_run",
            "proof_status": "not_run",
            "evidence": [],
        },
        "source": inspection.source,
        "members": [],
        "tools": [],
        "parameters": inspection.parameters,
        "metrics": inspection.metrics,
        "scientific_state": scientific_state,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": git_commit,
            "created_at": created_at,
        },
    }


def validate_record_in_memory(
    record: dict[str, Any],
    inventory_row: dict[str, str],
    validator: Draft202012Validator,
) -> None:
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed schema:\n{detail}"
        )
    try:
        contracts.validate_artifact_semantics(record)
        contracts.reconcile_artifact_inventory_row(record, inventory_row)
    except contracts.ContractValidationError as exc:
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed semantic "
            f"validation: {exc}"
        ) from exc


def build_index_rows(
    *,
    records: Sequence[dict[str, Any]],
    record_bytes: Sequence[bytes],
    records_dir: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record, payload in zip(records, record_bytes, strict=True):
        source = record["source"] or {}
        science = record["scientific_state"] or {}
        rows.append(
            {
                "run_id": record["run_id"],
                "run_contract_sha256": record["run_contract"]["run_contract_sha256"],
                "artifact_id": record["artifact_id"],
                "step_id": record["scope"]["step_id"],
                "scope_type": record["scope"]["scope_type"],
                "scope_id": record["scope"]["scope_id"],
                "adapter": record["adapter"],
                "source_path": record["expectation"]["source_path"],
                "required": str(record["expectation"]["required"]).lower(),
                "availability_status": record["availability_status"],
                "completion_status": record["completion_status"],
                "attempt_provenance_status": record["attempt_provenance_status"],
                "selected_attempt_id": safe_tsv(record["selected_attempt_id"]),
                **contracts.artifact_status_dimensions(record),
                "science_status": safe_tsv(science.get("overall_status")),
                "orientation_status": safe_tsv(science.get("orientation_status")),
                "orientation_policy": safe_tsv(science.get("orientation_policy")),
                "review_id": safe_tsv(science.get("review_id")),
                "source_sha256": safe_tsv(source.get("sha256")),
                "source_size_bytes": safe_tsv(source.get("size_bytes")),
                "source_row_count": safe_tsv(source.get("row_count")),
                "source_media_type": safe_tsv(source.get("media_type")),
                "warning_count": str(len(record["warnings"])),
                "error_count": str(len(record["errors"])),
                "record_path": str(records_dir / f"{record['artifact_id']}.json"),
                "record_sha256": sha256_bytes(payload),
                "record_schema_version": record["schema_version"],
            }
        )
    return rows


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:

    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(header),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: safe_tsv(row[field]) for field in header})
    return stream.getvalue().encode("utf-8")


def load_existing_receipt(
    receipt_path: Path,
    artifacts_path: Path,
    records_dir: Path,
) -> dict[str, str] | None:
    owned = tuple(
        path.exists() or path.is_symlink()
        for path in (receipt_path, artifacts_path, records_dir)
    )
    if any(owned) and not all(owned):
        raise ArtifactIndexError(
            "Existing artifact-index output set is incomplete; preserve it "
            f"for recovery: {receipt_path.parent}"
        )
    if not any(owned):
        return None
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise ArtifactIndexError(
            f"Existing artifact receipt is not a regular owned file: {receipt_path}"
        )
    if artifacts_path.is_symlink() or not artifacts_path.is_file():
        raise ArtifactIndexError(
            f"Existing artifact index is not a regular owned file: {artifacts_path}"
        )
    if records_dir.is_symlink() or not records_dir.is_dir():
        raise ArtifactIndexError(
            f"Existing records path is not a regular owned directory: {records_dir}"
        )
    rows = read_exact_tsv(
        receipt_path,
        ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )
    return rows[0]


def read_exact_tsv(
    path: Path,
    header: Sequence[str],
    *,
    exact_rows: int | None = None,
) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != tuple(header):
                raise ArtifactIndexError(f"TSV header is invalid: {path}")
            rows = list(reader)
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ArtifactIndexError(f"Could not read TSV {path}: {exc}") from exc
    if exact_rows is not None and len(rows) != exact_rows:
        raise ArtifactIndexError(
            f"TSV {path} must contain {exact_rows} rows; observed {len(rows)}"
        )
    return rows


def validate_existing_identity(
    existing: Mapping[str, str] | None,
    run_contract: Mapping[str, Any],
) -> tuple[str | None, list[str]]:
    if existing is None:
        return None, []
    for field_name in RUN_CONTRACT_FIELDS:
        if existing[field_name] != str(run_contract[field_name]):
            raise ArtifactIndexError(
                "Existing run_id is bound to a different immutable run "
                f"contract field: {field_name}"
            )
    if existing["transaction_state"] != "complete":
        raise ArtifactIndexError("Existing artifact receipt is not complete")
    history = [
        value for value in existing["adapter_attempt_history"].split(",") if value
    ]
    if not history or history[-1] != existing["adapter_attempt_id"]:
        raise ArtifactIndexError(
            "Existing artifact receipt attempt history is inconsistent"
        )
    if len(history) != len(set(history)):
        raise ArtifactIndexError(
            "Existing artifact receipt attempt history contains duplicates"
        )
    return existing["adapter_attempt_id"], history


def inventory_rows_from_published_index(
    artifacts_path: Path,
) -> list[dict[str, str]]:
    index_rows = read_exact_tsv(artifacts_path, ARTIFACT_INDEX_HEADER)
    return [
        {field_name: row[field_name] for field_name in contracts.INVENTORY_HEADER}
        for row in index_rows
    ]


def build_receipt_row(
    *,
    run_id: str,
    run_contract: Mapping[str, Any],
    run_contract_path: Path,
    run_contract_file_sha256: str,
    inventory_path: Path,
    inventory_sha256: str,
    inventory_row_count: int,
    artifacts_path: Path,
    index_bytes: bytes,
    index_rows: Sequence[Mapping[str, str]],
    attempt_id: str,
    previous_attempt_id: str | None,
    attempt_history: Sequence[str],
    git_commit: str,
    started_at: str,
    finished_at: str,
) -> dict[str, str]:
    availability = Counter(row["availability_status"] for row in index_rows)
    completion = Counter(row["completion_status"] for row in index_rows)
    record_manifest = [
        {
            "artifact_id": row["artifact_id"],
            "record_path": row["record_path"],
            "record_sha256": row["record_sha256"],
        }
        for row in index_rows
    ]
    required_count = sum(row["required"] == "true" for row in index_rows)
    required_missing = sum(
        row["required"] == "true" and row["availability_status"] != "present"
        for row in index_rows
    )
    return {
        "run_id": run_id,
        "run_contract_sha256": str(run_contract["run_contract_sha256"]),
        "run_contract_path": str(run_contract_path),
        "run_contract_file_sha256": run_contract_file_sha256,
        "sample_manifest_sha256": str(run_contract["sample_manifest_sha256"]),
        "reference_contract_sha256": str(run_contract["reference_contract_sha256"]),
        "partition_manifest_sha256": str(run_contract["partition_manifest_sha256"]),
        "primary_analysis_id": str(run_contract["primary_analysis_id"]),
        "primary_analysis_policy_sha256": str(
            run_contract["primary_analysis_policy_sha256"]
        ),
        "inventory_path": str(inventory_path),
        "inventory_sha256": inventory_sha256,
        "inventory_row_count": str(inventory_row_count),
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_index_schema_version": ARTIFACT_INDEX_SCHEMA_VERSION,
        "artifact_receipt_schema_version": ARTIFACT_RECEIPT_SCHEMA_VERSION,
        "artifacts_index_path": str(artifacts_path),
        "artifacts_index_sha256": sha256_bytes(index_bytes),
        "artifact_record_count": str(len(index_rows)),
        "record_set_sha256": canonical_digest(record_manifest),
        "required_artifact_count": str(required_count),
        "required_missing_artifact_count": str(required_missing),
        "present_artifact_count": str(availability["present"]),
        "missing_artifact_count": str(availability["missing"]),
        "externally_unavailable_artifact_count": str(
            availability["externally_unavailable"]
        ),
        "unknown_artifact_count": str(availability["unknown"]),
        "complete_artifact_count": str(completion["complete"]),
        "not_attempted_artifact_count": str(completion["not_attempted"]),
        "in_progress_artifact_count": str(completion["in_progress"]),
        "incomplete_artifact_count": str(completion["incomplete"]),
        "failed_artifact_count": str(completion["failed"]),
        "warning_count": str(sum(int(row["warning_count"]) for row in index_rows)),
        "error_count": str(sum(int(row["error_count"]) for row in index_rows)),
        "published_output_count": str(len(index_rows) + 2),
        "adapter_attempt_id": attempt_id,
        "supersedes_adapter_attempt_id": previous_attempt_id or "",
        "adapter_attempt_history": ",".join([*attempt_history, attempt_id]),
        "producer": PRODUCER,
        "producer_version": PRODUCER_VERSION,
        "git_commit": git_commit,
        "started_at": started_at,
        "finished_at": finished_at,
        "transaction_state": "complete",
    }
