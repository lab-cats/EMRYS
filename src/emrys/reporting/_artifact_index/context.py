"""Artifact-index context assembly and stable-input rechecks."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from emrys.contracts.artifacts import api as contracts
from emrys.libraries.source_authority import matching_clean_checkout_head_commit

from .core import (
    canonical_digest,
    canonical_json_bytes,
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
)
from .reconciliation import (
    reconcile_native_transactions,
    reconcile_scope_transactions,
)
from .records import (
    build_artifact_record,
    build_index_rows,
    build_receipt_row,
    load_existing_receipt,
    producer_evidence,
    record_manifest,
    tsv_bytes,
    validate_existing_identity,
    validate_record_in_memory,
)
from .registry import ADAPTER_REGISTRY
from .validation import validate_existing_transaction

if TYPE_CHECKING:
    from emrys.libraries.source_authority import ArtifactSourceRoot, SourceCheckout


@dataclass(frozen=True, slots=True)
class ArtifactIdentityOps:
    """Explicit source-provenance observation used throughout publication."""

    matching_clean_checkout_head_commit: Callable[..., str | None] = (
        matching_clean_checkout_head_commit
    )


DEFAULT_ARTIFACT_IDENTITY_OPS = ArtifactIdentityOps()


def prepare_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: SourceCheckout,
    artifact_source_root: ArtifactSourceRoot,
    identity_ops: ArtifactIdentityOps = DEFAULT_ARTIFACT_IDENTITY_OPS,
) -> BuildContext:
    source_root = artifact_source_root.root
    if not contracts.SAFE_ID_RE.fullmatch(arguments.run_id):
        raise ArtifactIndexError("run_id must match [A-Za-z0-9][A-Za-z0-9._-]*")
    run_contract_path = arguments.run_contract.expanduser().resolve()
    inventory_path = arguments.inventory.expanduser().resolve()
    output_root = arguments.output_root.expanduser().resolve()
    run_contract, run_contract_file_sha256 = load_run_contract(run_contract_path)
    inventory_rows = contracts.validate_inventory(
        inventory_path,
        source_root=source_root,
    )
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
        source = contracts.resolve_contract_path(
            row["source_path"],
            source_root=source_root,
        )
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
            source_root=source_root,
        )

    started_at = utc_now()
    attempt_id = new_attempt_id(started_at)
    git_commit = identity_ops.matching_clean_checkout_head_commit(
        source_checkout=source_checkout,
        package_root=Path(__file__).resolve().parents[2],
    )
    if git_commit is None:
        raise ArtifactIndexError(
            "Artifact-index provenance requires a stable clean source checkout"
        )
    evidence = producer_evidence(git_commit, source_root=source_checkout.root)
    inspections = [
        inspect_source(
            row,
            ADAPTER_REGISTRY[row["adapter"]],
            source_root=source_root,
        )
        for row in inventory_rows
    ]
    apply_run_contract_checks(inspections, run_contract)
    reconcile_native_transactions(
        inspections,
        source_root=source_root,
    )
    reconcile_scope_transactions(inspections)

    validator = contracts.schema_validator("artifact-record")
    records: list[dict[str, Any]] = []
    record_bytes: list[bytes] = []
    for inspection, inventory_row in zip(inspections, inventory_rows, strict=True):
        record = build_artifact_record(
            run_id=arguments.run_id,
            run_contract=run_contract,
            inspection=inspection,
            implementation=evidence[inventory_row["step_id"]],
            git_commit=git_commit,
            created_at=started_at,
        )
        validate_record_in_memory(
            record,
            inventory_row,
            validator,
            source_root=source_root,
        )
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
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        run_id=arguments.run_id,
        run_contract_path=run_contract_path,
        run_contract=run_contract,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        output_dir=output_dir,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
        inspections=inspections,
        records=records,
        record_bytes=record_bytes,
        index_rows=index_rows,
        index_bytes=index_bytes,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        previous_receipt=existing,
        source_identity_observer=identity_ops.matching_clean_checkout_head_commit,
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
    if context.receipt_row["record_set_sha256"] != canonical_digest(
        record_manifest(context.index_rows)
    ):
        raise ArtifactIndexError("Generated record-set hash is inconsistent")
    if context.receipt_row["transaction_state"] != "complete":
        raise ArtifactIndexError("Generated receipt is not complete")


def recheck_inputs(context: BuildContext) -> None:
    if contracts.sha256_file(context.run_contract_path) != (
        context.run_contract_file_sha256
    ):
        raise ArtifactIndexError("Run-contract file changed after initial validation")
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
        expected_snapshot = inspection.snapshot
        # Rechecks may skip hashing, but every filesystem identity field must match.
        if expected_snapshot is None or not (
            expected_snapshot == replace(observed, sha256=expected_snapshot.sha256)
        ):
            raise ArtifactIndexError(
                "Declared source changed after initial inspection: "
                f"{inspection.row['source_path']}"
            )


def recheck_source_identity(context: BuildContext) -> None:
    """Re-attest the exact clean producer checkout bound into the receipt."""

    observed = context.source_identity_observer(
        source_checkout=context.source_checkout,
        package_root=Path(__file__).resolve().parents[2],
    )
    if observed != context.receipt_row["git_commit"]:
        raise ArtifactIndexError(
            "Artifact-index producer checkout changed after provenance attribution"
        )
