"""Publish table projections exclusively, then install the Run result manifest."""

from __future__ import annotations

import contextlib
import os
import stat
import sys
import uuid
from pathlib import Path

from emrys.reporting import _files, _signals

from .context import recheck_inputs, recheck_source_identity
from .models import ArtifactIndexError, BuildContext, EvidenceContext


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


def publish_context(evidence: EvidenceContext) -> None:
    """Publish the Run result manifest last under the shared reporting lock."""

    from emrys.reporting.transaction_validation import (
        ReportingTransactionError,
        _reject_reporting_control_residue,
    )

    context = evidence.index
    _admit_output_directory(context)
    directory = context.output_dir.stat()
    directory_identity = (directory.st_dev, directory.st_ino)

    def assert_directory() -> None:
        current = context.output_dir.lstat()
        if (
            not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != directory_identity
            or context.output_dir.resolve(strict=True) != context.output_dir
        ):
            raise ArtifactIndexError("Artifact-index output directory changed identity")

    projected = (
        (evidence.summary_paths.summary_tsv, evidence.summary_tsv_bytes),
        (evidence.summary_paths.qc_summary, evidence.qc_summary_bytes),
        (evidence.summary_paths.summary_json, evidence.summary_json_bytes),
    )
    finals = tuple(path for path, _payload in projected)

    def reject_residue() -> None:
        try:
            _reject_reporting_control_residue(
                kind="run_summary",
                output_dir=context.output_dir,
                run_id=context.run_id,
                output_names=(
                    path.name for path in evidence.summary_paths.ordered_outputs
                ),
            )
        except ReportingTransactionError as exc:
            raise ArtifactIndexError(str(exc)) from exc

    reject_residue()
    for path in finals:
        if os.path.lexists(path):
            raise ArtifactIndexError(
                f"Artifact-index output already exists; refusing: {path}"
            )
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_records = context.output_dir / f".artifact-index.{run_token}.tmp.records"
    recovery_path = context.output_dir / f".artifact-index.{run_token}.RECOVERY.txt"
    scratch = (temp_records,)
    for path in (*scratch, recovery_path):
        if os.path.lexists(path):
            raise ArtifactIndexError(
                f"Run-token scratch path already exists; refusing: {path}"
            )
    lock_payload = (
        f"run_id\t{context.run_id}\npid\t{os.getpid()}\nrun_token\t{run_token}\n"
    ).encode()
    ownership = _files.acquire_lock(context.lock_path, lock_payload, ArtifactIndexError)
    try:
        previous_signal_handlers = _signals.install(
            ArtifactIndexError, "Artifact-index", "publication"
        )
    except BaseException as exc:
        try:
            _files.release_lock(
                context.lock_path, ownership, lock_payload, ArtifactIndexError
            )
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
        for path, payload in projected:
            _files.write_bytes_exclusive(temp_records / path.name, payload, mode=0o666)
        _files.fsync_path(temp_records)
        recheck_inputs(context)
        recheck_source_identity(context)
        assert_directory()
        outputs = tuple(
            (temp_records / path.name, path) for path, _payload in projected
        )
        for staged, final in outputs:
            assert_directory()
            if final == evidence.summary_paths.summary_json:
                _files.fsync_path(context.output_dir)
                recheck_inputs(context)
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
        _files.fsync_path(context.output_dir)
        for path, expected in projected:
            if path.read_bytes() != expected:
                raise ArtifactIndexError(
                    f"Published evidence differs from prepared bytes: {path}"
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
            remaining = [str(path) for path in finals if os.path.lexists(path)]
            if remaining:
                rollback_errors.append(
                    f"Outputs remain after rollback: {', '.join(remaining)}"
                )
            if not rollback_errors:
                _files.fsync_path(context.output_dir)
        except (OSError, ArtifactIndexError) as cleanup_exc:
            rollback_errors.append(str(cleanup_exc))
        if rollback_errors:
            rollback_failed = True
            with contextlib.suppress(OSError, ArtifactIndexError):
                assert_directory()
                _files.write_bytes_exclusive(
                    recovery_path,
                    (
                        f"Artifact-index rollback was incomplete.\nOriginal error: {exc}\n"
                        f"Rollback errors: {'; '.join(rollback_errors)}\n"
                    ).encode("utf-8"),
                    mode=0o666,
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
                    _files.remove_owned_stage(
                        path, run_token, scratch_identity.get(path), ArtifactIndexError
                    )
                assert_directory()
                _files.release_lock(
                    context.lock_path, ownership, lock_payload, ArtifactIndexError
                )
            except (OSError, ArtifactIndexError) as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        active = sys.exc_info()[1]
        try:
            _signals.restore(previous_signal_handlers)
        except (OSError, ValueError) as signal_exc:
            cleanup_errors.append(
                f"could not restore publication signal handlers: {signal_exc}"
            )
        if cleanup_errors:
            state = "publication is complete" if committed else "rollback completed"
            with contextlib.suppress(OSError, ArtifactIndexError):
                assert_directory()
                _files.write_bytes_exclusive(
                    recovery_path,
                    (
                        f"Artifact-index {state} but owned cleanup was incomplete.\n"
                        f"Cleanup errors: {'; '.join(cleanup_errors)}\n"
                    ).encode("utf-8"),
                    mode=0o666,
                )
            prefix = f"{active}\n" if active is not None else ""
            raise ArtifactIndexError(
                prefix + "Artifact-index cleanup failed; preserve the lock and "
                f"recovery paths under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active
