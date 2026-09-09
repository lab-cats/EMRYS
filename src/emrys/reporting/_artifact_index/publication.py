"""Receipt-last publication workflow for the artifact-index builder."""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

from emrys.reporting._signals import install as _install_signal_handlers
from emrys.reporting._signals import restore as restore_signal_handlers

from .context import recheck_inputs, recheck_source_identity
from .models import ArtifactIndexError, BuildContext, LockOwnership
from .validation import validate_published_transaction


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
    return _install_signal_handlers(ArtifactIndexError, "Artifact-index", "publication")


def _admit_output_directory(context: BuildContext) -> None:
    """Create and re-admit output ancestry beneath the artifact source root."""

    root = context.artifact_source_root.root
    try:
        relative = context.output_dir.relative_to(root)
    except ValueError as exc:
        raise ArtifactIndexError(
            "Artifact-index output directory must be beneath its admitted source root"
        ) from exc
    if not relative.parts:
        raise ArtifactIndexError("Artifact-index output directory cannot be its root")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor = -1
    cursor = root
    try:
        descriptor = os.open(root, flags)
        for part in relative.parts:
            cursor /= part
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        opened = os.fstat(descriptor)
        current = context.output_dir.lstat()
        if context.output_dir.resolve(strict=True) != context.output_dir:
            raise ArtifactIndexError(
                "Artifact-index output boundary changed during admission"
            )
        if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
            raise ArtifactIndexError(
                "Artifact-index output boundary changed during admission"
            )
    except OSError as exc:
        raise ArtifactIndexError(
            f"Artifact-index output boundary is unsafe: {cursor}: {exc}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def publish_context(context: BuildContext) -> None:
    """Publish a new index without replacing any existing transaction output."""

    _admit_output_directory(context)
    directory = context.output_dir.stat()
    directory_identity = (directory.st_dev, directory.st_ino)
    records_identity: tuple[int, int] | None = None

    def assert_directory() -> None:
        current = context.output_dir.lstat()
        if (
            not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != directory_identity
            or context.output_dir.resolve(strict=True) != context.output_dir
        ):
            raise ArtifactIndexError("Artifact-index output directory changed identity")
        if records_identity is not None:
            current = context.records_dir.lstat()
            if (
                not stat.S_ISDIR(current.st_mode)
                or (current.st_dev, current.st_ino) != records_identity
            ):
                raise ArtifactIndexError("Artifact records directory changed identity")

    finals = (context.records_dir, context.artifacts_path, context.receipt_path)
    for path in finals:
        if os.path.lexists(path):
            raise ArtifactIndexError(
                f"Artifact-index output already exists; refusing: {path}"
            )
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_records = context.output_dir / f".artifact-index.{run_token}.tmp.records"
    temp_index = temp_records / context.artifacts_path.name
    temp_receipt = temp_records / context.receipt_path.name
    recovery_path = context.output_dir / f".artifact-index.{run_token}.RECOVERY.txt"
    scratch = (temp_records,)
    for path in (*scratch, recovery_path):
        if os.path.lexists(path):
            raise ArtifactIndexError(
                f"Run-token scratch path already exists; refusing: {path}"
            )
    ownership = acquire_lock(context.lock_path, context.run_id, run_token)
    try:
        previous_signal_handlers = install_publication_signal_handlers()
    except BaseException as exc:
        try:
            release_owned_lock(context.lock_path, ownership)
        except ArtifactIndexError as cleanup_exc:
            raise ArtifactIndexError(
                "Could not install publication signal handlers and could "
                f"not release the owned lock: {exc}; {cleanup_exc}"
            ) from exc
        raise ArtifactIndexError(
            f"Could not install publication signal handlers: {exc}"
        ) from exc

    attempted: dict[Path, tuple[Path, os.stat_result]] = {}
    scratch_identity: dict[Path, tuple[int, int]] = {}
    committed = rollback_failed = False
    try:
        assert_directory()
        for path in finals:
            if os.path.lexists(path):
                raise ArtifactIndexError(
                    f"Artifact-index output appeared after preflight: {path}"
                )
        temp_records.mkdir()
        current = temp_records.lstat()
        scratch_identity[temp_records] = (current.st_dev, current.st_ino)
        for record, payload in zip(context.records, context.record_bytes, strict=True):
            write_bytes_exclusive(
                temp_records / f"{record['artifact_id']}.json", payload
            )
        write_bytes_exclusive(temp_index, context.index_bytes)
        write_bytes_exclusive(temp_receipt, context.receipt_bytes)
        fsync_directory(temp_records)
        recheck_inputs(context)
        recheck_source_identity(context)
        assert_directory()
        # mkdir reserves the records directory exclusively; rename could replace
        # an empty directory created by another process after admission.
        context.records_dir.mkdir()
        current = context.records_dir.lstat()
        records_identity = (current.st_dev, current.st_ino)
        outputs = (
            *(
                (
                    temp_records / f"{record['artifact_id']}.json",
                    context.records_dir / f"{record['artifact_id']}.json",
                )
                for record in context.records
            ),
            (temp_index, context.artifacts_path),
            (temp_receipt, context.receipt_path),
        )
        for staged, final in outputs:
            assert_directory()
            if final == context.receipt_path:
                fsync_directory(context.records_dir)
                recheck_source_identity(context)
            # Keep the staged inode as proof even if a signal arrives after the
            # link succeeds but before control returns to this publisher.
            attempted[final] = (staged, staged.lstat())
            os.link(staged, final, follow_symlinks=False)
            expected, current = attempted[final][1], final.lstat()
            if (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino):
                raise ArtifactIndexError(
                    "Artifact output identity changed during publication"
                )
            assert_directory()
        fsync_directory(context.output_dir)
        validate_published_transaction(
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
            source_root=context.artifact_source_root.root,
        )
        recheck_inputs(context)
        recheck_source_identity(context)
        assert_directory()
        committed = True
    except BaseException as exc:
        rollback_errors: list[str] = []
        try:
            assert_directory()
            for final, (staged, expected) in reversed(tuple(attempted.items())):
                if not os.path.lexists(final):
                    continue
                try:
                    current, anchor = final.lstat(), staged.lstat()
                    identity = (
                        expected.st_dev,
                        expected.st_ino,
                        expected.st_size,
                        expected.st_mtime_ns,
                    )
                    if any(
                        not stat.S_ISREG(item.st_mode)
                        or (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
                        != identity
                        for item in (current, anchor)
                    ):
                        raise ArtifactIndexError(
                            f"Published output ownership changed; preserve: {final}"
                        )
                    assert_directory()
                    final.unlink()
                    assert_directory()
                except (OSError, ArtifactIndexError) as cleanup_exc:
                    rollback_errors.append(str(cleanup_exc))
            if records_identity is not None:
                assert_directory()
                context.records_dir.rmdir()
                records_identity = None
                assert_directory()
            remaining = [str(path) for path in finals if os.path.lexists(path)]
            if remaining:
                rollback_errors.append(
                    f"Outputs remain after rollback: {', '.join(remaining)}"
                )
            if not rollback_errors:
                fsync_directory(context.output_dir)
        except (OSError, ArtifactIndexError) as cleanup_exc:
            rollback_errors.append(str(cleanup_exc))
        if rollback_errors:
            rollback_failed = True
            with contextlib.suppress(OSError, ArtifactIndexError):
                assert_directory()
                write_bytes_exclusive(
                    recovery_path,
                    (
                        f"Artifact-index rollback was incomplete.\nOriginal error: {exc}\n"
                        f"Rollback errors: {'; '.join(rollback_errors)}\n"
                    ).encode("utf-8"),
                )
            raise ArtifactIndexError(
                f"{exc}\nArtifact-index rollback was incomplete; preserve "
                f"the lock and recovery paths under {context.output_dir}"
            ) from exc
        raise ArtifactIndexError(str(exc)) from exc
    finally:
        cleanup_errors: list[str] = []
        if not rollback_failed:
            try:
                assert_directory()
                for path in scratch:
                    if os.path.lexists(path):
                        current = path.lstat()
                        expected = scratch_identity.get(path)
                        if (
                            expected is None
                            or (current.st_dev, current.st_ino) != expected
                        ):
                            raise ArtifactIndexError(
                                f"Scratch ownership is unproved; preserve: {path}"
                            )
                        remove_owned(path)
                assert_directory()
                release_owned_lock(context.lock_path, ownership)
            except (OSError, ArtifactIndexError) as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        active = sys.exc_info()[1]
        try:
            restore_signal_handlers(previous_signal_handlers)
        except (OSError, ValueError) as signal_exc:
            cleanup_errors.append(
                f"could not restore publication signal handlers: {signal_exc}"
            )
        if cleanup_errors:
            state = "publication is complete" if committed else "rollback completed"
            with contextlib.suppress(OSError, ArtifactIndexError):
                assert_directory()
                write_bytes_exclusive(
                    recovery_path,
                    (
                        f"Artifact-index {state} but owned cleanup was incomplete.\n"
                        f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    ).encode("utf-8"),
                )
            prefix = f"{active}\n" if active is not None else ""
            raise ArtifactIndexError(
                prefix + "Artifact-index cleanup failed; preserve the lock and "
                f"recovery paths under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active
