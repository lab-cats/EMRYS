"""Receipt-last atomic publication for canonical run summaries."""

from __future__ import annotations

import os
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts
from emrys.reporting import transaction_validation
from emrys.reporting._artifact_index import api as adapter
from emrys.reporting._run_summary.inputs import _fail
from emrys.reporting._run_summary.models import (
    RUN_SUMMARY_RECEIPT_HEADER,
    BuildContext,
    OutputPaths,
    RunSummaryError,
)
from emrys.reporting._run_summary.transaction import (
    _assert_output_directory_identity,
)
from emrys.reporting._run_summary.validation import (
    _validate_document,
    _validate_existing_summary,
)


def validate_published_run_summary(
    context: BuildContext,
) -> None:
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
        source_root=context.artifact_source_root.root,
    )
    _validate_existing_summary(
        paths=context.paths,
        receipt=receipt,
        expected_run_id=context.run_id,
        expected_run_contract=context.run_contract,
        source_root=context.artifact_source_root.root,
    )


def _write_recovery_marker(
    paths: OutputPaths,
    path: Path,
    message: str,
) -> None:
    try:
        _assert_output_directory_identity(paths)
        path.write_text(message, encoding="utf-8")
    except (OSError, RunSummaryError):
        pass


def publish_context(
    context: BuildContext,
) -> None:
    _assert_output_directory_identity(context.paths)
    if context.previous_receipt is not None:
        _fail("Run-summary publication requires absent outputs")
    for path in context.paths.ordered_outputs:
        if os.path.lexists(path):
            _fail(f"Run-summary publication requires absent outputs: {path}")
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_paths = tuple(
        context.paths.output_dir / f".{path.name}.{run_token}.tmp"
        for path in context.paths.ordered_outputs
    )
    recovery_path = (
        context.paths.output_dir
        / f".{context.run_id}.run-summary.{run_token}.RECOVERY.txt"
    )
    for path in (*temp_paths, recovery_path):
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

    anchors: list[tuple[int, int]] = []
    published = [False] * 4
    rollback_failed = False
    output_identity_lost = False
    try:
        _assert_output_directory_identity(context.paths)
        for path in context.paths.ordered_outputs:
            if os.path.lexists(path):
                _fail(f"Run-summary publication requires absent outputs: {path}")
        transaction_validation.recheck_run_summary_inputs(context)

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
            metadata = path.lstat()
            anchors.append((metadata.st_dev, metadata.st_ino))
            _assert_output_directory_identity(context.paths)
        adapter.fsync_directory(context.paths.output_dir)

        # Publish data views first and the receipt last.
        _assert_output_directory_identity(context.paths)
        for index in range(4):
            _assert_output_directory_identity(context.paths)
            # Retain the temporary inode through rollback, including a signal
            # immediately after linking and a failed link to a foreign final.
            published[index] = True
            os.link(
                temp_paths[index],
                context.paths.ordered_outputs[index],
                follow_symlinks=False,
            )
            metadata = context.paths.ordered_outputs[index].lstat()
            if (metadata.st_dev, metadata.st_ino) != anchors[index]:
                _fail("Run-summary output identity changed during publication")
            _assert_output_directory_identity(context.paths)
        adapter.fsync_directory(context.paths.output_dir)
        validate_published_run_summary(context)
        transaction_validation.recheck_run_summary_inputs(context)
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

        def remove_published(index: int) -> None:
            final = context.paths.ordered_outputs[index]
            if not os.path.lexists(final):
                return
            anchor = temp_paths[index].lstat()
            current = final.lstat()
            if (
                not stat.S_ISREG(anchor.st_mode)
                or not stat.S_ISREG(current.st_mode)
                or (anchor.st_dev, anchor.st_ino) != anchors[index]
                or (current.st_dev, current.st_ino) != anchors[index]
            ):
                _fail(f"Run-summary output ownership changed; preserve: {final}")
            final.unlink()

        # Remove only inode-proven outputs, receipt first, keeping foreign files.
        for index in (3, 2, 1, 0):
            if published[index]:
                rollback(
                    f"remove new {context.paths.ordered_outputs[index].name}",
                    lambda index=index: remove_published(index),
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
                    context.paths,
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
                    context.paths,
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
