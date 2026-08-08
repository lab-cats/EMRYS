#!/usr/bin/env python3
"""Assemble one validated NORAD artifact transaction into a run summary.

The command is explicit-input-only and dry-run-first. It never discovers
pipeline outputs, invokes an analysis engine, or promotes computational or
scientific state. Execute mode publishes canonical JSON, two deterministic
TSV views, and a receipt last as one rollback-protected transaction.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if (src_root := str(Path(__file__).resolve().parents[2])) not in sys.path:
    sys.path.insert(0, src_root)

from norad.reporting import _run_summary_science as science
from norad.reporting import build_artifact_index as adapter
from norad.reporting._run_summary.approvals import (
    _normalize_report_table_approvals,
)
from norad.reporting._run_summary.inputs import (
    _capture_file_snapshot,
    _fail,
    _require_regular_file,
    _verify_file_snapshot,
    _verify_report_table_snapshot,
    parse_arguments,
)
from norad.reporting._run_summary.models import (
    PRODUCER,
    PRODUCER_VERSION,
    LEGACY_PRODUCER_VERSION,
    QC_SUMMARY_HEADER,
    REPORT_TABLE_APPROVALS_HEADER,
    RUN_SUMMARY_HEADER,
    RUN_SUMMARY_RECEIPT_HEADER,
    RUN_SUMMARY_SCHEMA_VERSION,
    BuildContext,
    FileSnapshot,
    RunSummaryError,
    adapter as _owner_adapter,
)
from norad.reporting._run_summary.projection import (
    _build_attempts,
    _build_expected_scopes,
    _build_limitations,
    _build_qc_metrics,
    _build_qc_rows,
    _build_rollup,
    _build_summary_rows,
    _build_tools,
    _default_scientific_review,
    _issue_for_duplicate_metrics,
)
from norad.reporting._run_summary.transaction import (
    _assert_output_directory_identity,
    _load_input_transaction,
    _new_attempt_id,
    _parse_history,
    _path_hash,
    _stable_unique,
)
from norad.reporting._run_summary.validation import (
    _build_receipt_row,
    _load_existing_summary_receipt,
    _validate_document,
    _validate_existing_summary,
)

contracts = adapter.contracts

if adapter is not _owner_adapter or adapter.contracts is not contracts:
    raise ImportError("run-summary modules did not resolve one adapter owner")
if science.contracts is not adapter.contracts:
    raise ImportError("artifact-contract consumers did not resolve one owner")


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
    scientific_review: dict[str, Any],
    approved_report_tables: list[dict[str, Any]],
    report_table_approvals_source: dict[str, Any] | None,
    generated_at: str,
    git_commit: str,
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
    if scientific_review["record_state"] != "present":
        warnings.append(
            {
                "code": "scientific_review_not_supplied",
                "message": (
                    "No explicit committed Step 09c review was normalized; "
                    "science status remains evidence_incomplete."
                ),
                "related_artifact_ids": [],
                "evidence": [],
            }
        )
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
        "report_table_approvals": report_table_approvals_source,
    }
    document = {
        "schema_name": "norad.run_summary",
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
        "scientific_review": scientific_review,
        "science_status": scientific_review["overall_status"],
        "tools": _build_tools(artifacts),
        "parameters": parameters,
        "qc_metrics": qc_metrics,
        "limitations": _build_limitations(
            artifacts=artifacts,
            scientific_review=scientific_review,
        ),
        "approved_report_tables": approved_report_tables,
        "candidate_terminology": "CMH-ranked candidates",
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


def prepare_context(arguments: argparse.Namespace) -> BuildContext:
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
    git_commit = adapter.get_git_commit()
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
    _validate_document(document, inventory_rows, inventory_path)
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
    )
    _recheck_inputs(context)
    return context


def _recheck_inputs(context: BuildContext) -> None:
    _assert_output_directory_identity(context.paths)
    for snapshot in context.input_snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)
    for snapshot in context.report_table_snapshots:
        _verify_report_table_snapshot(snapshot)
    adapter.validate_published_transaction(
        run_id=context.run_id,
        run_contract=context.run_contract,
        run_contract_path=context.run_contract_path,
        run_contract_file_sha256=context.run_contract_file_sha256,
        inventory_path=context.inventory_path,
        inventory_sha256=context.inventory_sha256,
        inventory_rows=context.inventory_rows,
        records_dir=context.records_dir,
        artifacts_path=context.artifacts_path,
        receipt_path=context.artifact_receipt_path,
        require_current_source_locations=True,
    )
    for snapshot in context.input_snapshots:
        _verify_file_snapshot("Artifact transaction input", snapshot)
    for snapshot in context.report_table_snapshots:
        _verify_report_table_snapshot(snapshot)
    if context.science_review_summary_path is not None:
        if contracts.sha256_file(context.science_review_summary_path) != (
            context.science_review_summary_sha256
        ):
            _fail("The explicit science-review summary changed")
        normalized = science.normalize_scientific_review(
            summary_path=context.science_review_summary_path,
            artifacts=context.artifacts,
            run_id=context.run_id,
            run_contract=context.run_contract,
            generated_at=context.document["generated_at"],
            git_commit=context.git_commit,
        )
        if normalized != context.document["scientific_review"]["record"]:
            _fail("The explicit scientific-review package changed")
    approval_source = context.document["parameters"]["report_table_approvals"]
    if context.report_table_approvals_path is None:
        if approval_source is not None or context.document["approved_report_tables"]:
            _fail("Run-summary approval state changed after preparation")
    elif (
        approval_source is None
        or approval_source["path"] != str(context.report_table_approvals_path)
        or approval_source["sha256"] != context.report_table_approvals_sha256
        or approval_source["row_count"]
        != len(context.document["approved_report_tables"])
    ):
        _fail("The explicit report-table approval package changed")


def _validate_receipt_against_context(
    context: BuildContext,
    receipt: Mapping[str, str],
) -> None:
    expected = {
        field: adapter.safe_tsv(context.receipt_row[field])
        for field in RUN_SUMMARY_RECEIPT_HEADER
    }
    if dict(receipt) != expected:
        _fail("Published run-summary receipt differs from the prepared receipt")


def validate_published_run_summary(context: BuildContext) -> None:
    _assert_output_directory_identity(context.paths)
    for path in context.paths.ordered_outputs:
        if path.is_symlink() or not path.is_file():
            _fail(f"Published run-summary output is unsafe or missing: {path}")
    if context.paths.summary_json.read_bytes() != context.summary_json_bytes:
        _fail("Published run-summary JSON differs from prepared bytes")
    if context.paths.summary_tsv.read_bytes() != context.summary_tsv_bytes:
        _fail("Published run-summary TSV differs from prepared bytes")
    if context.paths.qc_summary.read_bytes() != context.qc_summary_bytes:
        _fail("Published QC summary differs from prepared bytes")
    receipt = adapter.read_exact_tsv(
        context.paths.receipt,
        RUN_SUMMARY_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    _validate_receipt_against_context(context, receipt)
    document = contracts.load_json_object(
        context.paths.summary_json, "published run summary"
    )
    _validate_document(document, context.inventory_rows, context.inventory_path)
    _validate_existing_summary(
        paths=context.paths,
        receipt=receipt,
        expected_run_id=context.run_id,
        expected_run_contract=context.run_contract,
    )


def _write_recovery_marker(
    path: Path,
    message: str,
) -> None:
    try:
        path.write_text(message, encoding="utf-8")
    except OSError:
        pass


def publish_context(context: BuildContext) -> None:
    _assert_output_directory_identity(context.paths)
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_paths = tuple(
        context.paths.output_dir / f".{path.name}.{run_token}.tmp"
        for path in context.paths.ordered_outputs
    )
    backup_paths = tuple(
        context.paths.output_dir / f".{path.name}.{run_token}.previous"
        for path in context.paths.ordered_outputs
    )
    recovery_path = (
        context.paths.output_dir
        / f".{context.run_id}.run-summary.{run_token}.RECOVERY.txt"
    )
    for path in (*temp_paths, *backup_paths, recovery_path):
        if path.exists() or path.is_symlink():
            _fail(f"Run-token scratch path already exists: {path}")

    try:
        ownership = adapter.acquire_lock(context.paths.lock, context.run_id, run_token)
    except adapter.ArtifactIndexError as exc:
        _fail(str(exc))
    try:
        previous_signal_handlers = adapter.install_publication_signal_handlers()
    except BaseException as exc:
        try:
            adapter.release_owned_lock(context.paths.lock, ownership)
        except adapter.ArtifactIndexError as cleanup_exc:
            raise RunSummaryError(
                "Could not install run-summary publication signal handlers "
                f"and could not release the owned lock: {exc}; {cleanup_exc}"
            ) from exc
        if isinstance(exc, adapter.ArtifactIndexError):
            raise RunSummaryError(str(exc)) from exc
        raise RunSummaryError(
            f"Could not install run-summary publication signal handlers: {exc}"
        ) from exc

    had_previous = context.previous_receipt is not None
    backed_up = [False] * 4
    published = [False] * 4
    committed = False
    rollback_failed = False
    output_identity_lost = False
    try:
        _assert_output_directory_identity(context.paths)
        current_previous, current_previous_hash = _load_existing_summary_receipt(
            context.paths
        )
        if current_previous != context.previous_receipt or (
            current_previous_hash != context.previous_receipt_sha256
        ):
            _fail(
                "Run-summary predecessor changed after initial validation; "
                "prepare a fresh context"
            )
        if current_previous is not None:
            _validate_existing_summary(
                paths=context.paths,
                receipt=current_previous,
                expected_run_id=context.run_id,
                expected_run_contract=context.run_contract,
            )
        _recheck_inputs(context)

        payloads = (
            context.summary_json_bytes,
            context.summary_tsv_bytes,
            context.qc_summary_bytes,
            context.receipt_bytes,
        )
        _assert_output_directory_identity(context.paths)
        for path, payload in zip(temp_paths, payloads, strict=True):
            _assert_output_directory_identity(context.paths)
            adapter.write_bytes_exclusive(path, payload)
            _assert_output_directory_identity(context.paths)
        adapter.fsync_directory(context.paths.output_dir)

        if had_previous:
            _assert_output_directory_identity(context.paths)
            # Remove the old completion marker first.
            backup_order = (3, 0, 1, 2)
            for index in backup_order:
                _assert_output_directory_identity(context.paths)
                # Mark intent before rename so a handled signal immediately
                # after the filesystem operation cannot hide the backup.
                backed_up[index] = True
                os.replace(
                    context.paths.ordered_outputs[index],
                    backup_paths[index],
                )
                _assert_output_directory_identity(context.paths)

        # Publish data views first and the receipt last.
        _assert_output_directory_identity(context.paths)
        for index in range(4):
            _assert_output_directory_identity(context.paths)
            # As above, intent precedes the rename. Removal is idempotent if
            # the rename itself failed before changing the filesystem.
            published[index] = True
            os.replace(temp_paths[index], context.paths.ordered_outputs[index])
            _assert_output_directory_identity(context.paths)
        adapter.fsync_directory(context.paths.output_dir)
        validate_published_run_summary(context)
        _recheck_inputs(context)
        committed = True
    except Exception as exc:
        rollback_errors: list[str] = []

        try:
            _assert_output_directory_identity(context.paths)
        except RunSummaryError as identity_exc:
            rollback_failed = True
            output_identity_lost = True
            raise RunSummaryError(
                f"{exc}\nRun output directory identity changed during "
                "publication; path-based rollback and cleanup were skipped "
                "to avoid modifying a replacement directory. Preserve the "
                f"owned recovery state: {identity_exc}"
            ) from exc

        def rollback(label: str, operation: Any) -> None:
            nonlocal output_identity_lost
            if output_identity_lost:
                rollback_errors.append(
                    f"{label}: skipped after output directory identity changed"
                )
                return
            try:
                _assert_output_directory_identity(context.paths)
            except RunSummaryError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")
                return
            try:
                operation()
            except Exception as rollback_exc:  # pragma: no cover
                rollback_errors.append(f"{label}: {rollback_exc}")
                return
            try:
                _assert_output_directory_identity(context.paths)
            except RunSummaryError as identity_exc:
                output_identity_lost = True
                rollback_errors.append(f"{label}: {identity_exc}")

        def restore_prior_output(index: int) -> None:
            final_path = context.paths.ordered_outputs[index]
            backup_path = backup_paths[index]
            backup_exists = backup_path.exists() or backup_path.is_symlink()
            final_exists = final_path.exists() or final_path.is_symlink()
            if backup_exists:
                if final_exists:
                    adapter.remove_owned(final_path)
                os.replace(backup_path, final_path)
                return
            if final_exists:
                return
            raise RunSummaryError(
                f"Neither the prior final output nor its backup remains: {final_path}"
            )

        # Remove a new receipt first, then the data views.
        for index in (3, 2, 1, 0):
            if published[index]:
                rollback(
                    f"remove new {context.paths.ordered_outputs[index].name}",
                    lambda index=index: adapter.remove_owned(
                        context.paths.ordered_outputs[index]
                    ),
                )
        if had_previous:
            # Restore data first and the prior receipt last.
            for index in (0, 1, 2):
                if backed_up[index]:
                    rollback(
                        (f"restore prior {context.paths.ordered_outputs[index].name}"),
                        lambda index=index: restore_prior_output(index),
                    )
            if not rollback_errors and backed_up[3]:
                rollback(
                    "restore prior run-summary receipt",
                    lambda: restore_prior_output(3),
                )
            if not rollback_errors and context.previous_receipt is not None:
                validation_error_count = len(rollback_errors)

                def validate_restored_prior() -> None:
                    restored, restored_sha256 = _load_existing_summary_receipt(
                        context.paths
                    )
                    if restored is None:
                        _fail("Restored prior run-summary receipt is absent")
                    if (
                        restored != context.previous_receipt
                        or restored_sha256 != context.previous_receipt_sha256
                    ):
                        _fail(
                            "Restored prior run-summary receipt differs from "
                            "the validated predecessor"
                        )
                    _validate_existing_summary(
                        paths=context.paths,
                        receipt=restored,
                        expected_run_id=context.run_id,
                        expected_run_contract=context.run_contract,
                    )

                rollback(
                    "validate restored prior run-summary transaction",
                    validate_restored_prior,
                )
                if len(rollback_errors) > validation_error_count and (
                    context.paths.receipt.exists() or context.paths.receipt.is_symlink()
                ):
                    rollback(
                        "quarantine invalid restored run-summary receipt",
                        lambda: os.replace(
                            context.paths.receipt,
                            backup_paths[3],
                        ),
                    )
        if not rollback_errors:
            rollback(
                "durability-sync rollback",
                lambda: adapter.fsync_directory(context.paths.output_dir),
            )
        if rollback_errors:
            rollback_failed = True
            if not output_identity_lost:
                _write_recovery_marker(
                    recovery_path,
                    "Run-summary rollback was incomplete.\n"
                    f"Original error: {exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n",
                )
            raise RunSummaryError(
                f"{exc}\nRun-summary rollback was incomplete; preserve "
                f"the lock and recovery paths under {context.paths.output_dir}. "
                f"Rollback errors: {'; '.join(rollback_errors)}"
            ) from exc
        if isinstance(exc, RunSummaryError):
            raise
        raise RunSummaryError(str(exc)) from exc
    finally:
        cleanup_errors: list[str] = []
        directory_identity_safe = not output_identity_lost
        active = sys.exc_info()[1]
        try:
            if not rollback_failed:
                try:
                    _assert_output_directory_identity(context.paths)
                except RunSummaryError as exc:
                    directory_identity_safe = False
                    cleanup_errors.append(str(exc))
                cleanup_paths = []
                if not cleanup_errors:
                    cleanup_paths = list(temp_paths)
                    if committed:
                        cleanup_paths.extend(backup_paths)
                for path in cleanup_paths:
                    try:
                        _assert_output_directory_identity(context.paths)
                        adapter.remove_owned(path)
                        _assert_output_directory_identity(context.paths)
                    except RunSummaryError as exc:
                        directory_identity_safe = False
                        cleanup_errors.append(str(exc))
                        break
                    except OSError as exc:
                        cleanup_errors.append(f"{path}: {exc}")
                if not cleanup_errors:
                    try:
                        _assert_output_directory_identity(context.paths)
                        adapter.release_owned_lock(context.paths.lock, ownership)
                        _assert_output_directory_identity(context.paths)
                    except RunSummaryError as exc:
                        directory_identity_safe = False
                        cleanup_errors.append(str(exc))
                    except adapter.ArtifactIndexError as exc:
                        cleanup_errors.append(str(exc))
        except Exception as exc:
            cleanup_errors.append(f"publication cleanup was interrupted: {exc}")
        finally:
            try:
                adapter.restore_signal_handlers(previous_signal_handlers)
            except (OSError, ValueError) as exc:
                cleanup_errors.append(
                    f"could not restore publication signal handlers: {exc}"
                )
        if cleanup_errors:
            if directory_identity_safe:
                _write_recovery_marker(
                    recovery_path,
                    (
                        "Run-summary publication completed but owned cleanup "
                        "was incomplete.\n"
                        f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    ),
                )
            raise RunSummaryError(
                "Run-summary cleanup failed; preserve the lock and recovery "
                f"paths: {'; '.join(cleanup_errors)}"
            ) from active


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


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        context = prepare_context(arguments)
        print_context(context)
        if arguments.execute:
            publish_context(context)
            print(f"Published run summary: {context.paths.summary_json}")
            print(f"Published receipt last: {context.paths.receipt}")
        return 0
    except (
        RunSummaryError,
        adapter.ArtifactIndexError,
        contracts.ContractValidationError,
        science.RunSummaryScienceError,
        OSError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
