"""Run-summary input transaction loading and stable value utilities."""

from __future__ import annotations

import json
import re
import stat
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as contracts
from norad.reporting._artifact_index import api as adapter

from .inputs import (
    _capture_file_snapshot,
    _fail,
    _load_json_bytes,
    _read_exact_tsv_bytes,
    _require_regular_file,
    _resolved_path,
    _verify_file_snapshot,
)
from .models import FileSnapshot, OutputPaths


def _assert_output_directory_identity(paths: OutputPaths) -> None:
    try:
        metadata = paths.output_dir.lstat()
        resolved = paths.output_dir.resolve(strict=True)
    except OSError as exc:
        _fail(f"Run output directory is unavailable: {paths.output_dir}: {exc}")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or resolved != paths.output_dir
        or metadata.st_dev != paths.output_dir_device
        or metadata.st_ino != paths.output_dir_inode
    ):
        _fail(
            "Run output directory identity changed after initial validation: "
            f"{paths.output_dir}"
        )


def _path_hash(
    path: Path,
    *,
    sha256: str,
    size_bytes: int,
    row_count: int | None,
    media_type: str,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256,
        "size_bytes": size_bytes,
        "row_count": row_count,
        "media_type": media_type,
    }


def _canonical_key(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _stable_unique(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    observed: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        key = _canonical_key(record)
        if key in observed:
            continue
        observed.add(key)
        result.append(record)
    return result


def _parse_history(
    receipt: Mapping[str, str],
    *,
    id_field: str,
    supersedes_field: str,
    history_field: str,
) -> tuple[str, list[str]]:
    attempt_id = receipt[id_field]
    history = [value for value in receipt[history_field].split(",") if value]
    if (
        not contracts.SAFE_ID_RE.fullmatch(attempt_id)
        or not history
        or history[-1] != attempt_id
        or len(history) != len(set(history))
        or any(not contracts.SAFE_ID_RE.fullmatch(value) for value in history)
    ):
        _fail(f"Receipt has an invalid {history_field}")
    expected_previous = history[-2] if len(history) > 1 else ""
    if receipt[supersedes_field] != expected_previous:
        _fail(f"Receipt has an invalid {supersedes_field}")
    return attempt_id, history


def _receipt_int(
    receipt: Mapping[str, str],
    field: str,
) -> int:
    value = receipt[field]
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        _fail(f"Receipt field {field} is not a non-negative integer")
    return int(value)


def _new_attempt_id(timestamp: str) -> str:
    compact = re.sub(r"[^0-9]", "", timestamp)[:14]
    return f"run-summary-{compact}-{uuid.uuid4().hex[:12]}"


def _load_input_transaction(
    *,
    run_id: str,
    artifact_receipt_value: Path,
    output_root_value: Path,
    source_root: Path,
) -> tuple[
    Path,
    str,
    dict[str, str],
    Path,
    dict[str, Any],
    str,
    Path,
    str,
    list[dict[str, str]],
    Path,
    str,
    Path,
    tuple[FileSnapshot, ...],
    list[dict[str, Any]],
    OutputPaths,
]:
    if not contracts.SAFE_ID_RE.fullmatch(run_id):
        _fail("run_id must match [A-Za-z0-9][A-Za-z0-9._-]*")
    artifact_receipt_path = _require_regular_file(
        "Artifact receipt", artifact_receipt_value
    )
    receipt_rows = adapter.read_exact_tsv(
        artifact_receipt_path,
        adapter.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )
    receipt = receipt_rows[0]
    if receipt["run_id"] != run_id:
        _fail("Artifact receipt run_id differs from --run-id")
    if receipt["transaction_state"] != "complete":
        _fail("Artifact receipt transaction_state is not complete")

    raw_output_root = _resolved_path(output_root_value)
    if raw_output_root.is_symlink() or not raw_output_root.is_dir():
        _fail(
            "Artifact output root must already be a regular directory: "
            f"{raw_output_root}"
        )
    try:
        output_root = raw_output_root.resolve(strict=True)
    except OSError as exc:
        _fail(f"Artifact output root cannot be resolved: {raw_output_root}: {exc}")
    raw_output_dir = output_root / run_id
    if raw_output_dir.is_symlink() or not raw_output_dir.is_dir():
        _fail(
            "Artifact output directory must already be a regular directory: "
            f"{raw_output_dir}"
        )
    try:
        output_dir = raw_output_dir.resolve(strict=True)
        output_dir_metadata = output_dir.lstat()
    except OSError as exc:
        _fail(f"Artifact output directory cannot be resolved: {raw_output_dir}: {exc}")
    if output_dir.parent != output_root or not stat.S_ISDIR(
        output_dir_metadata.st_mode
    ):
        _fail(
            "Artifact output directory must resolve directly beneath the "
            f"explicit output root: {raw_output_dir}"
        )
    if artifact_receipt_path.parent != output_dir:
        _fail(
            "Artifact receipt must be the exact receipt in "
            f"--output-root/<run_id>/: {artifact_receipt_path}"
        )
    expected_receipt_name = f"{run_id}.artifact_receipt.tsv"
    if artifact_receipt_path.name != expected_receipt_name:
        _fail(f"Artifact receipt basename must be {expected_receipt_name}")

    run_contract_path = _require_regular_file(
        "Run contract", receipt["run_contract_path"]
    )
    run_contract, run_contract_file_sha256 = adapter.load_run_contract(
        run_contract_path
    )
    inventory_path = _require_regular_file(
        "Artifact inventory", receipt["inventory_path"]
    )
    inventory_sha256 = contracts.sha256_file(inventory_path)
    inventory_rows = contracts.validate_inventory(
        inventory_path,
        source_root=source_root,
    )
    artifacts_path = _require_regular_file(
        "Artifact index", receipt["artifacts_index_path"]
    )
    if artifacts_path.parent != output_dir or artifacts_path.name != (
        f"{run_id}.artifacts.tsv"
    ):
        _fail("Artifact index path is outside the exact run output directory")
    records_dir = output_dir / "records"
    index_rows = adapter.read_exact_tsv(artifacts_path, adapter.ARTIFACT_INDEX_HEADER)

    record_paths: list[Path] = []
    record_hashes: list[str] = []
    artifacts: list[dict[str, Any]] = []
    for row in index_rows:
        record_path = _require_regular_file(
            f"Artifact record {row['artifact_id']}", row["record_path"]
        )
        record_paths.append(record_path)
        record_hashes.append(contracts.sha256_file(record_path))
        artifacts.append(
            contracts.load_json_object(
                record_path, f"artifact record {row['artifact_id']}"
            )
        )

    snapshots: list[FileSnapshot] = []
    receipt_payload, receipt_snapshot = _capture_file_snapshot(
        "Artifact receipt", artifact_receipt_path
    )
    if (
        _read_exact_tsv_bytes(
            label="Artifact receipt",
            path=artifact_receipt_path,
            payload=receipt_payload,
            header=adapter.ARTIFACT_RECEIPT_HEADER,
            exact_rows=1,
        )[0]
        != receipt
    ):
        _fail("Artifact receipt changed between parsing and snapshot capture")
    snapshots.append(receipt_snapshot)

    run_contract_payload, run_contract_snapshot = _capture_file_snapshot(
        "Run contract", run_contract_path
    )
    if (
        _load_json_bytes(
            label="Run contract",
            path=run_contract_path,
            payload=run_contract_payload,
        )
        != run_contract
        or run_contract_snapshot.sha256 != run_contract_file_sha256
    ):
        _fail("Run contract changed between validation and snapshot capture")
    snapshots.append(run_contract_snapshot)

    inventory_payload, inventory_snapshot = _capture_file_snapshot(
        "Artifact inventory", inventory_path
    )
    if (
        _read_exact_tsv_bytes(
            label="Artifact inventory",
            path=inventory_path,
            payload=inventory_payload,
            header=contracts.INVENTORY_HEADER,
        )
        != inventory_rows
        or inventory_snapshot.sha256 != inventory_sha256
    ):
        _fail("Artifact inventory changed between validation and snapshot capture")
    snapshots.append(inventory_snapshot)

    artifacts_payload, artifacts_snapshot = _capture_file_snapshot(
        "Artifact index", artifacts_path
    )
    if (
        _read_exact_tsv_bytes(
            label="Artifact index",
            path=artifacts_path,
            payload=artifacts_payload,
            header=adapter.ARTIFACT_INDEX_HEADER,
        )
        != index_rows
    ):
        _fail("Artifact index changed between parsing and snapshot capture")
    snapshots.append(artifacts_snapshot)

    for row, record_path, record_hash, artifact in zip(
        index_rows,
        record_paths,
        record_hashes,
        artifacts,
        strict=True,
    ):
        record_payload, record_snapshot = _capture_file_snapshot(
            f"Artifact record {row['artifact_id']}", record_path
        )
        if (
            _load_json_bytes(
                label=f"Artifact record {row['artifact_id']}",
                path=record_path,
                payload=record_payload,
            )
            != artifact
            or record_snapshot.sha256 != record_hash
        ):
            _fail(
                "Artifact record changed between parsing and snapshot capture: "
                f"{row['artifact_id']}"
            )
        snapshots.append(record_snapshot)

    adapter.validate_published_transaction(
        run_id=run_id,
        run_contract=run_contract,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=artifact_receipt_path,
        require_current_source_locations=True,
        source_root=source_root,
    )
    for snapshot in snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)

    paths = OutputPaths(
        output_dir=output_dir,
        output_dir_device=output_dir_metadata.st_dev,
        output_dir_inode=output_dir_metadata.st_ino,
        summary_json=output_dir / f"{run_id}.run_summary.json",
        summary_tsv=output_dir / f"{run_id}.run_summary.tsv",
        qc_summary=output_dir / f"{run_id}.qc_summary.tsv",
        receipt=output_dir / f"{run_id}.run_summary_receipt.tsv",
        lock=output_dir / f".{run_id}.run-summary.lock",
    )
    return (
        artifact_receipt_path,
        receipt_snapshot.sha256,
        receipt,
        run_contract_path,
        run_contract,
        run_contract_file_sha256,
        inventory_path,
        inventory_sha256,
        inventory_rows,
        artifacts_path,
        artifacts_snapshot.sha256,
        records_dir,
        tuple(snapshots),
        artifacts,
        paths,
    )
