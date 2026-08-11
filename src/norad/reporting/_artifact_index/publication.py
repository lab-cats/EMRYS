"""Receipt-last publication workflow for the artifact-index builder."""

from __future__ import annotations

import contextlib
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from norad.reporting import _signals

from .models import ArtifactIndexError, BuildContext, LockOwnership


def write_bytes_exclusive(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not write temporary file {path}: {exc}"
        ) from exc


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not open directory for durability sync {path}: {exc}"
        ) from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not durability-sync directory {path}: {exc}"
        ) from exc
    finally:
        os.close(descriptor)


def acquire_lock(
    lock_path: Path,
    run_id: str,
    run_token: str,
) -> LockOwnership:
    payload = (
        f"run_id\t{run_id}\npid\t{os.getpid()}\nrun_token\t{run_token}\n"
    ).encode()
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise ArtifactIndexError(
            f"Artifact-index output is locked; inspect owner metadata: {lock_path}"
        ) from exc
    except OSError as exc:
        raise ArtifactIndexError(f"Could not acquire lock {lock_path}: {exc}") from exc
    stat_result = os.fstat(descriptor)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        try:
            lock_path.unlink()
        except OSError as cleanup_exc:
            raise ArtifactIndexError(
                "Could not write lock metadata and could not remove the "
                f"incomplete owned lock {lock_path}: {exc}; {cleanup_exc}"
            ) from exc
        raise ArtifactIndexError(f"Could not write lock metadata: {exc}") from exc
    return LockOwnership(
        device=stat_result.st_dev,
        inode=stat_result.st_ino,
        run_token=run_token,
    )


def release_owned_lock(
    lock_path: Path,
    ownership: LockOwnership,
) -> None:
    try:
        if lock_path.is_symlink():
            raise ArtifactIndexError(
                f"Owned lock was replaced by a symlink: {lock_path}"
            )
        with lock_path.open(encoding="utf-8") as stream:
            stat_result = os.fstat(stream.fileno())
            payload = stream.read()
    except FileNotFoundError as exc:
        raise ArtifactIndexError(
            f"Owned lock disappeared before cleanup: {lock_path}"
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise ArtifactIndexError(
            f"Could not verify owned lock before cleanup: {lock_path}: {exc}"
        ) from exc
    if (
        stat_result.st_dev != ownership.device
        or stat_result.st_ino != ownership.inode
        or f"run_token\t{ownership.run_token}\n" not in payload
    ):
        raise ArtifactIndexError(
            f"Owned lock identity changed before cleanup: {lock_path}"
        )
    try:
        lock_path.unlink()
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not remove verified owned lock {lock_path}: {exc}"
        ) from exc


def remove_owned(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def install_publication_signal_handlers() -> dict[int, Any]:
    return _signals.install(ArtifactIndexError, "Artifact-index", "publication")


restore_signal_handlers = _signals.restore


def publish_context(context: BuildContext, *, facade: Any) -> None:
    """Publish through the facade's live, fault-injectable operations."""

    if context.output_dir.is_symlink():
        raise ArtifactIndexError(
            "Artifact-index output directory became a symlink after initial "
            f"validation: {context.output_dir}"
        )
    if context.output_dir.exists() and not context.output_dir.is_dir():
        raise ArtifactIndexError(
            f"Artifact-index output path is not a directory: {context.output_dir}"
        )
    context.output_dir.mkdir(parents=True, exist_ok=True)
    if context.output_dir.is_symlink() or not context.output_dir.is_dir():
        raise ArtifactIndexError(
            f"Artifact-index output directory is unsafe: {context.output_dir}"
        )
    run_token = f"{facade.os.getpid()}-{facade.uuid.uuid4().hex}"
    temp_records = context.output_dir / f".artifact-index.{run_token}.tmp.records"
    temp_index = context.output_dir / f".artifact-index.{run_token}.tmp.tsv"
    temp_receipt = context.output_dir / f".artifact-receipt.{run_token}.tmp.tsv"
    backup_records = (
        context.output_dir / f".artifact-index.{run_token}.previous.records"
    )
    backup_index = context.output_dir / f".artifact-index.{run_token}.previous.tsv"
    backup_receipt = context.output_dir / f".artifact-receipt.{run_token}.previous.tsv"
    recovery_path = context.output_dir / f".artifact-index.{run_token}.RECOVERY.txt"
    owned_scratch = (
        temp_records,
        temp_index,
        temp_receipt,
        backup_records,
        backup_index,
        backup_receipt,
        recovery_path,
    )
    for path in owned_scratch:
        if path.exists() or path.is_symlink():
            raise ArtifactIndexError(
                f"Run-token scratch path already exists; refusing: {path}"
            )
    lock_ownership = facade.acquire_lock(
        context.lock_path,
        context.run_id,
        run_token,
    )
    try:
        previous_signal_handlers = facade.install_publication_signal_handlers()
    except BaseException as exc:
        try:
            facade.release_owned_lock(context.lock_path, lock_ownership)
        except ArtifactIndexError as cleanup_exc:
            raise ArtifactIndexError(
                "Could not install publication signal handlers and could "
                f"not release the owned lock: {exc}; {cleanup_exc}"
            ) from exc
        if isinstance(exc, ArtifactIndexError):
            raise
        raise ArtifactIndexError(
            f"Could not install publication signal handlers: {exc}"
        ) from exc
    had_previous = False
    backed_up_records = False
    backed_up_index = False
    backed_up_receipt = False
    published_records = False
    published_index = False
    published_receipt = False
    publication_committed = False
    rollback_failed = False
    try:
        existing = facade.load_existing_receipt(
            context.receipt_path,
            context.artifacts_path,
            context.records_dir,
        )
        had_previous = existing is not None
        locked_previous_attempt_id, locked_attempt_history = (
            facade.validate_existing_identity(
                existing,
                context.run_contract,
            )
        )
        if (
            existing != context.previous_receipt
            or locked_previous_attempt_id != context.previous_attempt_id
            or locked_attempt_history != context.attempt_history
        ):
            raise ArtifactIndexError(
                "Artifact-index predecessor changed after initial inspection; "
                "retry from a fresh dry-run/context"
            )
        if existing is not None:
            facade.validate_existing_transaction(
                existing=existing,
                run_id=context.run_id,
                run_contract=context.run_contract,
                records_dir=context.records_dir,
                artifacts_path=context.artifacts_path,
                receipt_path=context.receipt_path,
                source_root=context.source_checkout.root,
            )

        temp_records.mkdir()
        for record, payload in zip(context.records, context.record_bytes, strict=True):
            facade.write_bytes_exclusive(
                temp_records / f"{record['artifact_id']}.json",
                payload,
            )
        facade.fsync_directory(temp_records)
        facade.write_bytes_exclusive(temp_index, context.index_bytes)
        # Receipt is intentionally staged last.
        facade.write_bytes_exclusive(temp_receipt, context.receipt_bytes)
        facade.recheck_inputs(context)

        if had_previous:
            facade.os.replace(context.receipt_path, backup_receipt)
            backed_up_receipt = True
            facade.os.replace(context.artifacts_path, backup_index)
            backed_up_index = True
            facade.os.replace(context.records_dir, backup_records)
            backed_up_records = True
        facade.os.replace(temp_records, context.records_dir)
        published_records = True
        facade.os.replace(temp_index, context.artifacts_path)
        published_index = True
        facade.os.replace(temp_receipt, context.receipt_path)
        published_receipt = True
        facade.fsync_directory(context.output_dir)

        facade.validate_published_transaction(
            run_id=context.run_id,
            run_contract=context.run_contract,
            run_contract_path=context.run_contract_path,
            run_contract_file_sha256=context.run_contract_file_sha256,
            inventory_path=context.inventory_path,
            inventory_sha256=context.inventory_sha256,
            inventory_rows=context.inventory_rows,
            records_dir=context.records_dir,
            artifacts_path=context.artifacts_path,
            receipt_path=context.receipt_path,
            require_current_source_locations=True,
            source_root=context.source_checkout.root,
        )
        facade.recheck_inputs(context)
        publication_committed = True
    except Exception as exc:
        rollback_errors: list[str] = []

        def attempt_rollback(label: str, operation: Any) -> None:
            try:
                operation()
            except Exception as rollback_exc:  # pragma: no cover - fault injection
                rollback_errors.append(f"{label}: {rollback_exc}")

        if published_receipt:
            attempt_rollback(
                "remove new receipt",
                lambda: facade.remove_owned(context.receipt_path),
            )
        if published_index:
            attempt_rollback(
                "remove new artifact index",
                lambda: facade.remove_owned(context.artifacts_path),
            )
        if published_records:
            attempt_rollback(
                "remove new records directory",
                lambda: facade.remove_owned(context.records_dir),
            )
        if had_previous:
            if backed_up_records:
                attempt_rollback(
                    "restore prior records directory",
                    lambda: facade.os.replace(backup_records, context.records_dir),
                )
            if backed_up_index:
                attempt_rollback(
                    "restore prior artifact index",
                    lambda: facade.os.replace(backup_index, context.artifacts_path),
                )
            if backed_up_receipt and not rollback_errors:
                # Restore the old receipt last.
                attempt_rollback(
                    "restore prior receipt",
                    lambda: facade.os.replace(backup_receipt, context.receipt_path),
                )
            if not rollback_errors:
                validation_error_count = len(rollback_errors)
                attempt_rollback(
                    "validate restored prior transaction",
                    lambda: facade.validate_existing_transaction(
                        existing=facade.load_existing_receipt(
                            context.receipt_path,
                            context.artifacts_path,
                            context.records_dir,
                        )
                        or {},
                        run_id=context.run_id,
                        run_contract=context.run_contract,
                        records_dir=context.records_dir,
                        artifacts_path=context.artifacts_path,
                        receipt_path=context.receipt_path,
                        source_root=context.source_checkout.root,
                    ),
                )
                if len(rollback_errors) > validation_error_count and (
                    context.receipt_path.exists() or context.receipt_path.is_symlink()
                ):
                    # A receipt is a complete-transaction marker. Quarantine
                    # it again if the restored records/index do not validate.
                    attempt_rollback(
                        "quarantine invalid restored receipt",
                        lambda: facade.os.replace(
                            context.receipt_path,
                            backup_receipt,
                        ),
                    )
            if not rollback_errors:
                attempt_rollback(
                    "durability-sync restored transaction",
                    lambda: facade.fsync_directory(context.output_dir),
                )
        else:
            for label, path in (
                ("new receipt", context.receipt_path),
                ("new artifact index", context.artifacts_path),
                ("new records directory", context.records_dir),
            ):
                if path.exists() or path.is_symlink():
                    rollback_errors.append(
                        f"{label} remains after first-publication rollback: {path}"
                    )
            if not rollback_errors:
                attempt_rollback(
                    "durability-sync first-publication rollback",
                    lambda: facade.fsync_directory(context.output_dir),
                )
        if rollback_errors:
            rollback_failed = True
            with contextlib.suppress(OSError):
                recovery_path.write_text(
                    "Artifact-index rollback was incomplete.\n"
                    f"Original error: {exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n",
                    encoding="utf-8",
                )
            raise ArtifactIndexError(
                f"{exc}\nArtifact-index rollback was incomplete; preserve "
                f"the lock and recovery paths under {context.output_dir}"
            ) from exc
        raise ArtifactIndexError(str(exc)) from exc
    finally:
        cleanup_errors: list[str] = []
        if not rollback_failed:
            cleanup_paths = [temp_records, temp_index, temp_receipt]
            if publication_committed:
                cleanup_paths.extend([backup_records, backup_index, backup_receipt])
            for path in cleanup_paths:
                try:
                    facade.remove_owned(path)
                except OSError as cleanup_exc:
                    cleanup_errors.append(f"{path}: {cleanup_exc}")
            if not cleanup_errors:
                try:
                    facade.release_owned_lock(context.lock_path, lock_ownership)
                except ArtifactIndexError as cleanup_exc:
                    cleanup_errors.append(str(cleanup_exc))
        active_error = sys.exc_info()[1]
        try:
            facade.restore_signal_handlers(previous_signal_handlers)
        except (OSError, ValueError) as signal_exc:
            cleanup_errors.append(
                f"could not restore publication signal handlers: {signal_exc}"
            )
        if cleanup_errors:
            cleanup_state = (
                "publication is complete"
                if publication_committed
                else "rollback completed"
            )
            with contextlib.suppress(OSError):
                recovery_path.write_text(
                    f"Artifact-index {cleanup_state} but owned cleanup was "
                    "incomplete.\n"
                    f"Cleanup errors: {'; '.join(cleanup_errors)}\n",
                    encoding="utf-8",
                )
            prefix = f"{active_error}\n" if active_error is not None else ""
            raise ArtifactIndexError(
                prefix + "Artifact-index cleanup failed; preserve the lock and "
                f"recovery paths under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active_error
