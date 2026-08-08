"""Published artifact-index transaction validation."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .contracts import contracts
from .core import canonical_digest
from .models import (
    ARTIFACT_INDEX_HEADER,
    ARTIFACT_INDEX_SCHEMA_VERSION,
    ARTIFACT_RECEIPT_HEADER,
    ARTIFACT_RECEIPT_SCHEMA_VERSION,
    ARTIFACT_SCHEMA_VERSION,
    PRODUCER,
    PRODUCER_VERSION,
    RUN_CONTRACT_FIELDS,
    SHA256_RE,
    ArtifactIndexError,
)
from .records import (
    build_index_rows,
    inventory_rows_from_published_index,
    read_exact_tsv,
    validate_record_in_memory,
)


def parse_nonnegative_receipt_int(value: str, field_name: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ArtifactIndexError(
            f"Published receipt field {field_name} is not a non-negative integer"
        )
    return int(value)


def validate_published_transaction(
    *,
    run_id: str,
    run_contract: Mapping[str, Any],
    run_contract_path: Path,
    run_contract_file_sha256: str,
    inventory_path: Path,
    inventory_sha256: str,
    inventory_rows: Sequence[dict[str, str]],
    records_dir: Path,
    artifacts_path: Path,
    receipt_path: Path,
    require_current_source_locations: bool,
) -> None:
    for label, path in (
        ("receipt", receipt_path),
        ("artifact index", artifacts_path),
    ):
        if path.is_symlink() or not path.is_file():
            raise ArtifactIndexError(
                f"Published {label} is not a regular owned file: {path}"
            )
    if records_dir.is_symlink() or not records_dir.is_dir():
        raise ArtifactIndexError(
            f"Published records path is not a regular owned directory: {records_dir}"
        )

    receipt_rows = read_exact_tsv(
        receipt_path,
        ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )
    receipt = receipt_rows[0]
    if receipt["run_id"] != run_id:
        raise ArtifactIndexError("Published receipt run_id is invalid")
    for field_name in RUN_CONTRACT_FIELDS:
        if receipt[field_name] != str(run_contract[field_name]):
            raise ArtifactIndexError(
                f"Published receipt run contract field is invalid: {field_name}"
            )
    for field_name in ("run_contract_path", "inventory_path"):
        if not receipt[field_name] or not Path(receipt[field_name]).is_absolute():
            raise ArtifactIndexError(
                f"Published receipt {field_name} must be an absolute path"
            )
    if not SHA256_RE.fullmatch(receipt["run_contract_file_sha256"]):
        raise ArtifactIndexError("Published receipt run-contract file hash is invalid")
    if require_current_source_locations:
        if receipt["run_contract_path"] != str(run_contract_path):
            raise ArtifactIndexError("Published receipt run-contract path is invalid")
        if receipt["run_contract_file_sha256"] != run_contract_file_sha256:
            raise ArtifactIndexError(
                "Published receipt run-contract file hash is invalid"
            )
        if receipt["inventory_path"] != str(inventory_path):
            raise ArtifactIndexError("Published receipt inventory path is invalid")
    if receipt["inventory_sha256"] != inventory_sha256:
        raise ArtifactIndexError("Published receipt inventory hash is invalid")
    for field_name, expected in (
        ("artifact_schema_version", ARTIFACT_SCHEMA_VERSION),
        ("artifact_index_schema_version", ARTIFACT_INDEX_SCHEMA_VERSION),
        ("artifact_receipt_schema_version", ARTIFACT_RECEIPT_SCHEMA_VERSION),
        ("producer", PRODUCER),
        ("producer_version", PRODUCER_VERSION),
    ):
        if receipt[field_name] != expected:
            raise ArtifactIndexError(
                f"Published receipt field is invalid: {field_name}"
            )
    if receipt["transaction_state"] != "complete":
        raise ArtifactIndexError("Published receipt transaction is not complete")
    if not contracts.SAFE_ID_RE.fullmatch(receipt["adapter_attempt_id"]):
        raise ArtifactIndexError("Published receipt adapter attempt ID is invalid")
    attempt_history = [
        value for value in receipt["adapter_attempt_history"].split(",") if value
    ]
    if (
        not attempt_history
        or len(attempt_history) != len(set(attempt_history))
        or attempt_history[-1] != receipt["adapter_attempt_id"]
        or any(not contracts.SAFE_ID_RE.fullmatch(value) for value in attempt_history)
    ):
        raise ArtifactIndexError("Published receipt adapter attempt history is invalid")
    expected_superseded = attempt_history[-2] if len(attempt_history) > 1 else ""
    if receipt["supersedes_adapter_attempt_id"] != expected_superseded:
        raise ArtifactIndexError(
            "Published receipt superseded adapter attempt is invalid"
        )
    if not re.fullmatch(r"[0-9a-f]{40,64}", receipt["git_commit"]):
        raise ArtifactIndexError("Published receipt Git commit is invalid")
    try:
        started_at = datetime.fromisoformat(
            receipt["started_at"].replace("Z", "+00:00")
        )
        finished_at = datetime.fromisoformat(
            receipt["finished_at"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ArtifactIndexError("Published receipt timestamps are invalid") from exc
    if (
        started_at.tzinfo is None
        or finished_at.tzinfo is None
        or finished_at < started_at
    ):
        raise ArtifactIndexError("Published receipt timestamp ordering is invalid")
    if receipt["artifacts_index_path"] != str(artifacts_path):
        raise ArtifactIndexError("Published receipt index path is invalid")
    if receipt["artifacts_index_sha256"] != contracts.sha256_file(artifacts_path):
        raise ArtifactIndexError("Published artifact-index hash is invalid")

    index_rows = read_exact_tsv(artifacts_path, ARTIFACT_INDEX_HEADER)
    if [row["artifact_id"] for row in index_rows] != [
        row["artifact_id"] for row in inventory_rows
    ]:
        raise ArtifactIndexError(
            "Published artifact index does not match inventory order"
        )
    expected_names = {
        f"{inventory_row['artifact_id']}.json" for inventory_row in inventory_rows
    }
    try:
        observed_entries = list(records_dir.iterdir())
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not inspect owned records directory: {exc}"
        ) from exc
    observed_names = {path.name for path in observed_entries}
    if observed_names != expected_names:
        raise ArtifactIndexError(
            "Published records directory has missing or unexpected files"
        )
    unsafe_entries = [
        path for path in observed_entries if path.is_symlink() or not path.is_file()
    ]
    if unsafe_entries:
        raise ArtifactIndexError(
            "Published records directory contains a non-regular owned entry: "
            + ", ".join(str(path) for path in unsafe_entries)
        )

    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["artifact-record"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    record_manifest: list[dict[str, str]] = []
    validated_index_rows: list[dict[str, str]] = []
    for index_row, inventory_row in zip(index_rows, inventory_rows, strict=True):
        expected_path = records_dir / f"{inventory_row['artifact_id']}.json"
        if index_row["record_path"] != str(expected_path):
            raise ArtifactIndexError(
                f"Published record path is invalid: {index_row['record_path']}"
            )
        observed_hash = contracts.sha256_file(expected_path)
        if index_row["record_sha256"] != observed_hash:
            raise ArtifactIndexError(
                f"Published record hash is invalid: {expected_path}"
            )
        try:
            payload = expected_path.read_bytes()
        except OSError as exc:
            raise ArtifactIndexError(
                f"Could not read published artifact record {expected_path}: {exc}"
            ) from exc
        record = contracts.load_json_object(
            expected_path,
            f"artifact record {inventory_row['artifact_id']}",
        )
        validate_record_in_memory(record, inventory_row, validator)
        if record["run_id"] != run_id or record["run_contract"] != run_contract:
            raise ArtifactIndexError(
                f"Published record has the wrong run identity: {expected_path}"
            )
        expected_index_row = build_index_rows(
            records=[record],
            record_bytes=[payload],
            records_dir=records_dir,
        )[0]
        if index_row != expected_index_row:
            raise ArtifactIndexError(
                "Published artifact-index row disagrees with its JSON record: "
                f"{inventory_row['artifact_id']}"
            )
        validated_index_rows.append(expected_index_row)
        record_manifest.append(
            {
                "artifact_id": inventory_row["artifact_id"],
                "record_path": str(expected_path),
                "record_sha256": observed_hash,
            }
        )
    if receipt["record_set_sha256"] != canonical_digest(record_manifest):
        raise ArtifactIndexError("Published record-set hash is invalid")

    availability = Counter(row["availability_status"] for row in validated_index_rows)
    completion = Counter(row["completion_status"] for row in validated_index_rows)
    required_count = sum(row["required"] == "true" for row in validated_index_rows)
    required_missing = sum(
        row["required"] == "true" and row["availability_status"] != "present"
        for row in validated_index_rows
    )
    expected_counts = {
        "inventory_row_count": len(inventory_rows),
        "artifact_record_count": len(validated_index_rows),
        "required_artifact_count": required_count,
        "required_missing_artifact_count": required_missing,
        "present_artifact_count": availability["present"],
        "missing_artifact_count": availability["missing"],
        "externally_unavailable_artifact_count": availability["externally_unavailable"],
        "unknown_artifact_count": availability["unknown"],
        "complete_artifact_count": completion["complete"],
        "not_attempted_artifact_count": completion["not_attempted"],
        "in_progress_artifact_count": completion["in_progress"],
        "incomplete_artifact_count": completion["incomplete"],
        "failed_artifact_count": completion["failed"],
        "warning_count": sum(int(row["warning_count"]) for row in validated_index_rows),
        "error_count": sum(int(row["error_count"]) for row in validated_index_rows),
        "published_output_count": len(validated_index_rows) + 2,
    }
    for field_name, expected in expected_counts.items():
        observed = parse_nonnegative_receipt_int(
            receipt[field_name],
            field_name,
        )
        if observed != expected:
            raise ArtifactIndexError(
                f"Published receipt rollup is invalid: {field_name}"
            )


def validate_existing_transaction(
    *,
    existing: Mapping[str, str],
    run_id: str,
    run_contract: Mapping[str, Any],
    records_dir: Path,
    artifacts_path: Path,
    receipt_path: Path,
) -> None:
    previous_inventory_rows = inventory_rows_from_published_index(artifacts_path)
    validate_published_transaction(
        run_id=run_id,
        run_contract=run_contract,
        run_contract_path=Path(existing["run_contract_path"]),
        run_contract_file_sha256=existing["run_contract_file_sha256"],
        inventory_path=Path(existing["inventory_path"]),
        inventory_sha256=existing["inventory_sha256"],
        inventory_rows=previous_inventory_rows,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        require_current_source_locations=False,
    )
