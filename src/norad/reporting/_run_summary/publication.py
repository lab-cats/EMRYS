"""Receipt-last atomic publication for canonical run summaries."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any

from norad.reporting._artifact_index import api as adapter
from norad.reporting._run_summary import science_projection as science
from norad.reporting._run_summary.inputs import (
    _fail,
    _verify_file_snapshot,
    _verify_report_table_snapshot,
)
from norad.reporting._run_summary.models import (
    RUN_SUMMARY_RECEIPT_HEADER,
    BuildContext,
    RunSummaryError,
)
from norad.reporting._run_summary.transaction import (
    _assert_output_directory_identity,
)
from norad.reporting._run_summary.validation import (
    _load_existing_summary_receipt,
    _validate_document,
    _validate_existing_summary,
)

contracts = adapter.contracts


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
        source_root=context.source_checkout.root,
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
            source_root=context.source_checkout.root,
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
    expected = {
        field: adapter.safe_tsv(context.receipt_row[field])
        for field in RUN_SUMMARY_RECEIPT_HEADER
    }
    if dict(receipt) != expected:
        _fail("Published run-summary receipt differs from the prepared receipt")
    document = contracts.load_json_object(
        context.paths.summary_json, "published run summary"
    )
    _validate_document(
        document,
        context.inventory_rows,
        context.inventory_path,
        source_root=context.source_checkout.root,
    )
    _validate_existing_summary(
        paths=context.paths,
        receipt=receipt,
        expected_run_id=context.run_id,
        expected_run_contract=context.run_contract,
        source_root=context.source_checkout.root,
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
                source_root=context.source_checkout.root,
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
                        source_root=context.source_checkout.root,
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
