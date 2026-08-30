"""Assemble one validated EMRYS artifact transaction into a run summary.

The private builder is explicit-input-only. It never discovers pipeline outputs,
invokes an analysis engine, publishes files, or promotes computational or
scientific state.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import argparse

from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
    matching_checkout_head_commit,
)
from emrys.reporting import transaction_validation
from emrys.reporting._artifact_index import api as adapter
from emrys.reporting._run_summary import models
from emrys.reporting._run_summary.document import _build_document
from emrys.reporting._run_summary.models import BuildContext
from emrys.reporting._run_summary.projection import (
    _build_qc_rows,
    _build_summary_rows,
)
from emrys.reporting._run_summary.transaction import (
    _load_input_transaction,
    _new_attempt_id,
    _parse_history,
)
from emrys.reporting._run_summary.validation import (
    _build_receipt_row,
    _load_existing_summary_receipt,
    _validate_document,
    _validate_existing_summary,
)


@dataclass(frozen=True)
class RunSummaryBuildDeps:
    """Explicit build-time fault seams for run-summary preparation."""

    load_input_transaction: Callable[..., Any] = _load_input_transaction
    build_document: Callable[..., Any] = _build_document
    recheck_inputs: Callable[..., Any] = (
        transaction_validation.recheck_run_summary_inputs
    )
    matching_checkout_head_commit: Callable[..., str | None] = (
        matching_checkout_head_commit
    )


DEFAULT_RUN_SUMMARY_BUILD_DEPS = RunSummaryBuildDeps()


def prepare_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: SourceCheckout,
    artifact_source_root: ArtifactSourceRoot,
    deps: RunSummaryBuildDeps = DEFAULT_RUN_SUMMARY_BUILD_DEPS,
) -> BuildContext:
    source_root = artifact_source_root.root
    (
        artifact_receipt_path,
        artifact_receipt_sha256,
        artifact_receipt,
        run_contract_path,
        run_contract,
        run_contract_file_sha256,
        inventory_path,
        inventory_sha256,
        inventory_rows,
        artifacts_path,
        artifacts_sha256,
        records_dir,
        input_snapshots,
        artifacts,
        paths,
    ) = deps.load_input_transaction(
        run_id=arguments.run_id,
        artifact_receipt_value=arguments.artifact_receipt,
        output_root_value=arguments.output_root,
        source_root=source_root,
        expected_run_contract_path=getattr(
            arguments,
            "expected_run_contract_path",
            None,
        ),
        expected_inventory_path=getattr(
            arguments,
            "expected_inventory_path",
            None,
        ),
    )
    snapshot_by_path = {snapshot.path: snapshot for snapshot in input_snapshots}
    artifact_receipt_snapshot = snapshot_by_path[artifact_receipt_path]
    inventory_snapshot = snapshot_by_path[inventory_path]
    _parse_history(
        artifact_receipt,
        id_field="adapter_attempt_id",
        supersedes_field="supersedes_adapter_attempt_id",
        history_field="adapter_attempt_history",
    )
    git_commit = (
        deps.matching_checkout_head_commit(
            source_checkout=source_checkout,
            package_root=Path(__file__).resolve().parents[2],
        )
        or "local_build"
    )
    generated_at = artifact_receipt["finished_at"]
    started_at = adapter.utc_now()
    finished_at = started_at

    document, artifact_scope_order = deps.build_document(
        run_id=arguments.run_id,
        run_contract=run_contract,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_size_bytes=inventory_snapshot.size_bytes,
        inventory_rows=inventory_rows,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt_sha256=artifact_receipt_sha256,
        artifact_receipt_size_bytes=artifact_receipt_snapshot.size_bytes,
        artifact_receipt=artifact_receipt,
        artifacts=artifacts,
        generated_at=generated_at,
        git_commit=git_commit,
    )
    _validate_document(
        document,
        inventory_rows,
        inventory_path,
        source_root=source_root,
    )
    summary_json_bytes = adapter.canonical_json_bytes(document)
    summary_rows = _build_summary_rows(document, artifact_scope_order)
    summary_tsv_bytes = adapter.tsv_bytes(models.RUN_SUMMARY_HEADER, summary_rows)
    qc_rows = _build_qc_rows(document)
    qc_summary_bytes = adapter.tsv_bytes(models.QC_SUMMARY_HEADER, qc_rows)

    previous_receipt, previous_receipt_sha256 = _load_existing_summary_receipt(paths)
    previous_attempt_id: str | None = None
    previous_attempt_history: list[str] = []
    if previous_receipt is not None:
        _validate_existing_summary(
            paths=paths,
            receipt=previous_receipt,
            expected_run_id=arguments.run_id,
            expected_run_contract=run_contract,
            source_root=source_root,
        )
        previous_attempt_id, previous_attempt_history = _parse_history(
            previous_receipt,
            id_field="run_summary_attempt_id",
            supersedes_field="supersedes_run_summary_attempt_id",
            history_field="run_summary_attempt_history",
        )

    attempt_id = _new_attempt_id(started_at)
    receipt_row = _build_receipt_row(
        run_id=arguments.run_id,
        run_contract=run_contract,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt_sha256=artifact_receipt_sha256,
        artifact_receipt=artifact_receipt,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_row_count=len(inventory_rows),
        artifacts_path=artifacts_path,
        artifacts_sha256=artifacts_sha256,
        summary_json_path=paths.summary_json,
        summary_json_bytes=summary_json_bytes,
        summary_tsv_path=paths.summary_tsv,
        summary_tsv_bytes=summary_tsv_bytes,
        summary_tsv_row_count=len(summary_rows),
        qc_summary_path=paths.qc_summary,
        qc_summary_bytes=qc_summary_bytes,
        qc_summary_row_count=len(qc_rows),
        document=document,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        previous_attempt_history=previous_attempt_history,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
    )
    receipt_bytes = adapter.tsv_bytes(
        models.RUN_SUMMARY_RECEIPT_HEADER,
        [receipt_row],
    )
    context = BuildContext(
        run_id=arguments.run_id,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt=artifact_receipt,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        run_contract=run_contract,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        artifacts_path=artifacts_path,
        records_dir=records_dir,
        input_snapshots=input_snapshots,
        artifacts=artifacts,
        document=document,
        summary_json_bytes=summary_json_bytes,
        summary_rows=summary_rows,
        summary_tsv_bytes=summary_tsv_bytes,
        qc_summary_bytes=qc_summary_bytes,
        paths=paths,
        previous_receipt=previous_receipt,
        previous_receipt_sha256=previous_receipt_sha256,
        previous_attempt_id=previous_attempt_id,
        attempt_id=attempt_id,
        git_commit=git_commit,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
    )
    deps.recheck_inputs(context)
    return context
