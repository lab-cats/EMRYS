"""Artifact-index context assembly and stable-input rechecks."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .contracts import contracts
from .core import (
    canonical_digest,
    canonical_json_bytes,
    get_git_commit,
    load_run_contract,
    new_attempt_id,
    sha256_bytes,
    stat_source,
    utc_now,
    validate_inventory_registry,
)
from .inspection import apply_run_contract_checks, inspect_source
from .models import (
    ARTIFACT_INDEX_HEADER,
    ARTIFACT_RECEIPT_HEADER,
    ArtifactIndexError,
    BuildContext,
    SourceSnapshot,
)
from .reconciliation import (
    reconcile_native_transactions,
    reconcile_scope_transactions,
    resolve_scientific_states,
)
from .records import (
    build_artifact_record,
    build_index_rows,
    build_receipt_row,
    load_existing_receipt,
    producer_evidence,
    tsv_bytes,
    validate_existing_identity,
    validate_record_in_memory,
)
from .registry import ADAPTER_REGISTRY
from .validation import validate_existing_transaction

def prepare_context(arguments: argparse.Namespace) -> BuildContext:
    if not contracts.SAFE_ID_RE.fullmatch(arguments.run_id):
        raise ArtifactIndexError(
            "run_id must match [A-Za-z0-9][A-Za-z0-9._-]*"
        )
    run_contract_path = arguments.run_contract.expanduser().resolve()
    inventory_path = arguments.inventory.expanduser().resolve()
    output_root = arguments.output_root.expanduser().resolve()
    run_contract, run_contract_file_sha256 = load_run_contract(
        run_contract_path
    )
    inventory_rows = contracts.validate_inventory(inventory_path)
    validate_inventory_registry(inventory_rows)
    inventory_sha256 = contracts.sha256_file(inventory_path)
    output_dir = output_root / arguments.run_id
    records_dir = output_dir / "records"
    artifacts_path = output_dir / f"{arguments.run_id}.artifacts.tsv"
    receipt_path = output_dir / f"{arguments.run_id}.artifact_receipt.tsv"
    lock_path = output_dir / f".{arguments.run_id}.artifact-index.lock"
    if output_dir.is_symlink():
        raise ArtifactIndexError(
            f"Artifact-index output directory must not be a symlink: {output_dir}"
        )
    if lock_path.exists() or lock_path.is_symlink():
        raise ArtifactIndexError(
            f"Artifact-index output is locked; inspect owner metadata: {lock_path}"
        )
    for label, path in (
        ("run contract", run_contract_path),
        ("inventory", inventory_path),
    ):
        if path == output_dir or output_dir in path.parents:
            raise ArtifactIndexError(
                f"The {label} must not live inside its generated run directory"
            )
    for row in inventory_rows:
        source = contracts.resolve_contract_path(row["source_path"])
        if source == output_dir or output_dir in source.parents:
            raise ArtifactIndexError(
                "Inventory source paths must not point inside the generated "
                f"run directory: {row['source_path']}"
            )

    existing = load_existing_receipt(receipt_path, artifacts_path, records_dir)
    previous_attempt_id, attempt_history = validate_existing_identity(
        existing,
        run_contract,
    )
    if existing is not None:
        validate_existing_transaction(
            existing=existing,
            run_id=arguments.run_id,
            run_contract=run_contract,
            records_dir=records_dir,
            artifacts_path=artifacts_path,
            receipt_path=receipt_path,
        )

    started_at = utc_now()
    attempt_id = new_attempt_id(started_at)
    git_commit = get_git_commit()
    evidence = producer_evidence(git_commit)
    inspections = [
        inspect_source(row, ADAPTER_REGISTRY[row["adapter"]])
        for row in inventory_rows
    ]
    apply_run_contract_checks(inspections, run_contract)
    reconcile_native_transactions(inspections)
    reconcile_scope_transactions(inspections)
    scientific_states = resolve_scientific_states(inspections)

    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["artifact-record"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    records: list[dict[str, Any]] = []
    record_bytes: list[bytes] = []
    for inspection, inventory_row in zip(
        inspections, inventory_rows, strict=True
    ):
        scope = (
            inventory_row["step_id"],
            inventory_row["scope_type"],
            inventory_row["scope_id"],
        )
        record = build_artifact_record(
            run_id=arguments.run_id,
            run_contract=run_contract,
            inspection=inspection,
            implementation=evidence[inventory_row["step_id"]],
            scientific_state=scientific_states.get(scope),
            git_commit=git_commit,
            created_at=started_at,
        )
        validate_record_in_memory(record, inventory_row, validator)
        records.append(record)
        record_bytes.append(canonical_json_bytes(record))

    index_rows = build_index_rows(
        records=records,
        record_bytes=record_bytes,
        records_dir=records_dir,
    )
    index_bytes = tsv_bytes(ARTIFACT_INDEX_HEADER, index_rows)
    finished_at = utc_now()
    receipt_row = build_receipt_row(
        run_id=arguments.run_id,
        run_contract=run_contract,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_row_count=len(inventory_rows),
        artifacts_path=artifacts_path,
        index_bytes=index_bytes,
        index_rows=index_rows,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
    )
    receipt_bytes = tsv_bytes(ARTIFACT_RECEIPT_HEADER, [receipt_row])
    context = BuildContext(
        run_id=arguments.run_id,
        run_contract_path=run_contract_path,
        run_contract=run_contract,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        output_root=output_root,
        output_dir=output_dir,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
        git_commit=git_commit,
        producer_evidence=evidence,
        inspections=inspections,
        records=records,
        record_bytes=record_bytes,
        index_rows=index_rows,
        index_bytes=index_bytes,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
        started_at=started_at,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        previous_receipt=existing,
    )
    validate_context_in_memory(context)
    return context


def validate_context_in_memory(context: BuildContext) -> None:
    if [row["artifact_id"] for row in context.index_rows] != [
        row["artifact_id"] for row in context.inventory_rows
    ]:
        raise ArtifactIndexError(
            "Generated artifact index order differs from inventory order"
        )
    if context.receipt_row["artifacts_index_sha256"] != sha256_bytes(
        context.index_bytes
    ):
        raise ArtifactIndexError("Generated artifact index hash is inconsistent")
    manifest = [
        {
            "artifact_id": row["artifact_id"],
            "record_path": row["record_path"],
            "record_sha256": row["record_sha256"],
        }
        for row in context.index_rows
    ]
    if context.receipt_row["record_set_sha256"] != canonical_digest(manifest):
        raise ArtifactIndexError("Generated record-set hash is inconsistent")
    if context.receipt_row["transaction_state"] != "complete":
        raise ArtifactIndexError("Generated receipt is not complete")


def source_snapshot_matches(
    expected: SourceSnapshot,
    observed: SourceSnapshot,
) -> bool:
    return (
        expected.status,
        expected.size_bytes,
        expected.file_type,
        expected.link_target,
        expected.device,
        expected.inode,
        expected.mtime_ns,
        expected.ctime_ns,
    ) == (
        observed.status,
        observed.size_bytes,
        observed.file_type,
        observed.link_target,
        observed.device,
        observed.inode,
        observed.mtime_ns,
        observed.ctime_ns,
    )


def recheck_inputs(context: BuildContext) -> None:
    if contracts.sha256_file(context.run_contract_path) != (
        context.run_contract_file_sha256
    ):
        raise ArtifactIndexError(
            "Run-contract file changed after initial validation"
        )
    if contracts.sha256_file(context.inventory_path) != context.inventory_sha256:
        raise ArtifactIndexError("Inventory changed after initial validation")
    for inspection in context.inspections:
        observed = stat_source(
            inspection.resolved_path,
            hash_content=(
                inspection.snapshot is not None
                and inspection.snapshot.file_type == "hash_read_error"
            ),
        )
        if inspection.snapshot is None or not source_snapshot_matches(
            inspection.snapshot, observed
        ):
            raise ArtifactIndexError(
                "Declared source changed after initial inspection: "
                f"{inspection.row['source_path']}"
            )


def print_context(context: BuildContext, execute: bool) -> None:
    availability = Counter(
        inspection.availability_status for inspection in context.inspections
    )
    completion = Counter(
        inspection.completion_status for inspection in context.inspections
    )
    print("NORAD artifact-index context")
    print(f"  Mode: {'execute' if execute else 'dry-run'}")
    print(f"  Run ID: {context.run_id}")
    print(
        "  Run contract SHA-256: "
        f"{context.run_contract['run_contract_sha256']}"
    )
    print(f"  Run contract: {context.run_contract_path}")
    print(f"  Inventory: {context.inventory_path}")
    print(f"  Inventory artifacts: {len(context.inventory_rows)}")
    print(f"  Output directory: {context.output_dir}")
    print(f"  Records directory: {context.records_dir}")
    print(f"  Artifact index: {context.artifacts_path}")
    print(f"  Receipt (published last): {context.receipt_path}")
    print(f"  Adapter attempt ID: {context.attempt_id}")
    print(
        "  Availability: "
        + ", ".join(
            f"{status}={availability[status]}"
            for status in (
                "present",
                "missing",
                "externally_unavailable",
                "unknown",
            )
        )
    )
    print(
        "  Completion: "
        + ", ".join(
            f"{status}={completion[status]}"
            for status in (
                "complete",
                "not_attempted",
                "in_progress",
                "incomplete",
                "failed",
            )
        )
    )
    for inspection in context.inspections:
        print(
            "  Artifact: "
            f"{inspection.row['artifact_id']} "
            f"availability={inspection.availability_status} "
            f"completion={inspection.completion_status} "
            f"source={inspection.row['source_path']}"
        )
    if not execute:
        print(
            "Dry-run only. Add --execute to publish the artifact-index "
            "transaction."
        )
