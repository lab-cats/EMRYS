"""Assemble one validated NORAD artifact transaction into a run summary.

The command is explicit-input-only and dry-run-first. It never discovers
pipeline outputs, invokes an analysis engine, or promotes computational or
scientific state. Execute mode publishes canonical JSON, two deterministic
TSV views, and a receipt last as one rollback-protected transaction.
"""

from __future__ import annotations

import os as os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import argparse

from norad.reporting._artifact_index import api as adapter
from norad.reporting._run_summary import document as _document
from norad.reporting._run_summary import inputs as _inputs
from norad.reporting._run_summary import models as _models
from norad.reporting._run_summary import projection as _projection
from norad.reporting._run_summary import publication as _publication
from norad.reporting._run_summary import science_projection as science
from norad.reporting._run_summary import transaction as _transaction
from norad.reporting._run_summary.approvals import (
    _normalize_report_table_approvals,
)
from norad.reporting._run_summary.inputs import (
    _capture_file_snapshot,
    _fail,
    _require_regular_file,
    _verify_file_snapshot,
)
from norad.reporting._run_summary.models import (
    QC_SUMMARY_HEADER,
    RUN_SUMMARY_HEADER,
    RUN_SUMMARY_RECEIPT_HEADER,
    BuildContext,
    FileSnapshot,
    RunSummaryError,
)
from norad.reporting._run_summary.models import (
    adapter as _owner_adapter,
)
from norad.reporting._run_summary.projection import (
    _build_qc_rows,
    _build_summary_rows,
    _default_scientific_review,
)
from norad.reporting._run_summary.transaction import (
    _load_input_transaction,
    _new_attempt_id,
    _parse_history,
    _path_hash,
)
from norad.reporting._run_summary.validation import (
    _build_receipt_row,
    _load_existing_summary_receipt,
    _validate_document,
    _validate_existing_summary,
)

contracts = adapter.contracts

# These assignments intentionally preserve the established direct-import
# compatibility surface while implementation ownership stays private.
LEGACY_PRODUCER_VERSION = _models.LEGACY_PRODUCER_VERSION
PRODUCER = _models.PRODUCER
PRODUCER_VERSION = _models.PRODUCER_VERSION
REPORT_TABLE_APPROVALS_HEADER = _models.REPORT_TABLE_APPROVALS_HEADER
RUN_SUMMARY_SCHEMA_VERSION = _models.RUN_SUMMARY_SCHEMA_VERSION
_build_document = _document._build_document
_build_attempts = _projection._build_attempts
_build_expected_scopes = _projection._build_expected_scopes
_build_limitations = _projection._build_limitations
_build_qc_metrics = _projection._build_qc_metrics
_build_rollup = _projection._build_rollup
_build_tools = _projection._build_tools
_issue_for_duplicate_metrics = _projection._issue_for_duplicate_metrics
_assert_output_directory_identity = _transaction._assert_output_directory_identity
_stable_unique = _transaction._stable_unique
_verify_report_table_snapshot = _inputs._verify_report_table_snapshot
_recheck_inputs = _publication._recheck_inputs
_validate_receipt_against_context = _publication._validate_receipt_against_context
_write_recovery_marker = _publication._write_recovery_marker
publish_context = _publication.publish_context
validate_published_run_summary = _publication.validate_published_run_summary


if adapter is not _owner_adapter or adapter.contracts is not contracts:
    raise ImportError("run-summary modules did not resolve one adapter owner")
if science.contracts is not adapter.contracts:
    raise ImportError("artifact-contract consumers did not resolve one owner")


def prepare_context(
    arguments: argparse.Namespace,
    *,
    source_checkout: adapter.SourceCheckout,
) -> BuildContext:
    source_root = source_checkout.root
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
        index_rows,
        records_dir,
        record_paths,
        record_hashes,
        input_snapshots,
        artifacts,
        paths,
    ) = _load_input_transaction(
        run_id=arguments.run_id,
        artifact_receipt_value=arguments.artifact_receipt,
        output_root_value=arguments.output_root,
        source_root=source_root,
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
    git_commit = adapter.get_git_commit(
        source_root=source_root,
        sanitize_git_routing=True,
    )
    generated_at = artifact_receipt["finished_at"]
    started_at = adapter.utc_now()
    finished_at = started_at

    science_path: Path | None = None
    science_sha256: str | None = None
    scientific_review = _default_scientific_review()
    if arguments.science_review_summary is not None:
        science_path = _require_regular_file(
            "Science-review summary", arguments.science_review_summary
        )
        _science_payload, science_snapshot = _capture_file_snapshot(
            "Science-review summary", science_path
        )
        science_sha256 = science_snapshot.sha256
        try:
            record = science.normalize_scientific_review(
                summary_path=science_path,
                artifacts=artifacts,
                run_id=arguments.run_id,
                run_contract=run_contract,
                generated_at=generated_at,
                git_commit=git_commit,
                source_root=source_root,
            )
        except science.RunSummaryScienceError as exc:
            _fail(str(exc))
        _verify_file_snapshot("Science-review summary", science_snapshot)
        input_snapshots = (*input_snapshots, science_snapshot)
        source = record["review_summary"]
        scientific_review = {
            "record_state": "present",
            "source": dict(source),
            "record": record,
            "overall_status": record["scientific_state"]["overall_status"],
        }

    approvals_path: Path | None = None
    approvals_sha256: str | None = None
    approval_records: list[dict[str, Any]] = []
    approval_table_snapshots: tuple[FileSnapshot, ...] = ()
    approval_source: dict[str, Any] | None = None
    if arguments.report_table_approvals is not None:
        (
            approvals_path,
            approvals_snapshot,
            approval_records,
            approval_table_snapshots,
        ) = _normalize_report_table_approvals(
            manifest_value=arguments.report_table_approvals,
            run_id=arguments.run_id,
            run_contract=run_contract,
            artifacts=artifacts,
            scientific_review=scientific_review,
            build_started_at=started_at,
            source_root=source_root,
        )
        approvals_sha256 = approvals_snapshot.sha256
        input_snapshots = (*input_snapshots, approvals_snapshot)
        approval_source = _path_hash(
            approvals_path,
            sha256=approvals_snapshot.sha256,
            size_bytes=approvals_snapshot.size_bytes,
            row_count=len(approval_records),
            media_type="text/tab-separated-values",
        )

    document, artifact_scope_order = _build_document(
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
        scientific_review=scientific_review,
        approved_report_tables=approval_records,
        report_table_approvals_source=approval_source,
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
    summary_tsv_bytes = adapter.tsv_bytes(RUN_SUMMARY_HEADER, summary_rows)
    qc_rows = _build_qc_rows(document)
    qc_summary_bytes = adapter.tsv_bytes(QC_SUMMARY_HEADER, qc_rows)

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
        science_review_summary_path=science_path,
        science_review_summary_sha256=science_sha256,
        document=document,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        previous_attempt_history=previous_attempt_history,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
    )
    receipt_bytes = adapter.tsv_bytes(RUN_SUMMARY_RECEIPT_HEADER, [receipt_row])
    context = BuildContext(
        run_id=arguments.run_id,
        execute=arguments.execute,
        artifact_receipt_path=artifact_receipt_path,
        artifact_receipt_sha256=artifact_receipt_sha256,
        artifact_receipt=artifact_receipt,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        run_contract=run_contract,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        artifacts_path=artifacts_path,
        artifacts_sha256=artifacts_sha256,
        records_dir=records_dir,
        index_rows=index_rows,
        record_paths=record_paths,
        record_hashes=record_hashes,
        input_snapshots=input_snapshots,
        artifacts=artifacts,
        science_review_summary_path=science_path,
        science_review_summary_sha256=science_sha256,
        report_table_approvals_path=approvals_path,
        report_table_approvals_sha256=approvals_sha256,
        report_table_snapshots=approval_table_snapshots,
        document=document,
        summary_json_bytes=summary_json_bytes,
        summary_rows=summary_rows,
        summary_tsv_bytes=summary_tsv_bytes,
        qc_rows=qc_rows,
        qc_summary_bytes=qc_summary_bytes,
        paths=paths,
        previous_receipt=previous_receipt,
        previous_receipt_sha256=previous_receipt_sha256,
        previous_attempt_id=previous_attempt_id,
        previous_attempt_history=previous_attempt_history,
        attempt_id=attempt_id,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
        source_checkout=source_checkout,
    )
    _recheck_inputs(context)
    return context


def print_context(context: BuildContext) -> None:
    mode = "execute" if context.execute else "dry-run"
    rollup = context.document["computational_rollup"]
    print("NORAD run-summary context")
    print(f"  Mode: {mode}")
    print(f"  Run ID: {context.run_id}")
    print(f"  Artifact receipt: {context.artifact_receipt_path}")
    print(f"  Adapter attempt: {context.artifact_receipt['adapter_attempt_id']}")
    print(f"  Expected artifacts: {len(context.artifacts)}")
    print(f"  Expected scopes: {len(context.document['expected_scopes'])}")
    print(f"  Complete artifacts: {rollup['complete_artifact_count']}")
    print(f"  Missing artifacts: {rollup['missing_artifact_count']}")
    print(f"  Incomplete artifacts: {rollup['incomplete_artifact_count']}")
    print(f"  Failed artifacts: {rollup['failed_artifact_count']}")
    print(
        "  Externally unavailable artifacts: "
        f"{rollup['externally_unavailable_artifact_count']}"
    )
    print(f"  Science status: {context.document['science_status']}")
    if context.report_table_approvals_path is None:
        print("  Report-table approvals: not supplied")
    else:
        print(f"  Report-table approvals: {context.report_table_approvals_path}")
    print(
        f"  Approved report tables: {len(context.document['approved_report_tables'])}"
    )
    print(f"  Output JSON: {context.paths.summary_json}")
    print(f"  Output TSV: {context.paths.summary_tsv}")
    print(f"  QC TSV: {context.paths.qc_summary}")
    print(f"  Receipt (published last): {context.paths.receipt}")
    print(f"  Run-summary attempt: {context.attempt_id}")
    if not context.execute:
        print("Dry-run complete; no run-summary files were written.")


def build_from_args(arguments: argparse.Namespace) -> int:
    """Build one run summary from grouped command arguments."""
    try:
        source_checkout = adapter.admit_source_checkout(
            root=arguments.source_checkout,
            package_root=Path(__file__).resolve().parents[2],
        )
        context = prepare_context(
            arguments,
            source_checkout=source_checkout,
        )
        print_context(context)
        if arguments.execute:
            publish_context(context)
            print(f"Published run summary: {context.paths.summary_json}")
            print(f"Published receipt last: {context.paths.receipt}")
        return 0
    except (
        RunSummaryError,
        adapter.ArtifactIndexError,
        adapter.SourceCheckoutError,
        contracts.ContractValidationError,
        science.RunSummaryScienceError,
        OSError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
