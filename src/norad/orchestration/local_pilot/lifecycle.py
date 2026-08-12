"""Internal lifecycle owner for direct local Snakemake execution.

This module intentionally has no top-level ``norad run/resume/inspect`` route.
It is the direct API beneath that later adapter: it publishes immutable attempt
state, owns the aggregate run lock, and treats Snakemake as an executor rather
than as run-state authority.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import signal
import socket
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import Any, Literal

from norad.contracts.orchestration import api as orchestration_contracts
from norad.libraries.source_authority import controlled_python_argv
from norad.orchestration.local_pilot import inspection, task

Operation = Literal["execute", "resume"]
_SAFE_RULE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_FORBIDDEN_SNAKEMAKE_FLAGS = frozenset(
    {
        "--unlock",
        "--cleanup-metadata",
        "--forceall",
        "--rerun-incomplete",
        "--force",
    }
)


class LifecycleError(RuntimeError):
    """Raised when a workflow attempt cannot be safely started or finalized."""


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Terminal observation of the delegated Snakemake process group."""

    exit_code: int | None
    termination_signal: int | None
    message: str | None = None


WorkflowRunner = Callable[[tuple[str, ...], Path], WorkflowResult]
BytesPublisher = Callable[[Path, bytes], None]
LockReleaser = Callable[[Path, Path, bytes, tuple[int, int]], None]
RuntimeContextAdmission = Callable[[Mapping[str, Any], "LifecycleRequest"], None]
LockEvidencePublisher = Callable[[Path, Path], None]
DirectorySynchronizer = Callable[[Path, str], None]
PythonLauncherIdentity = tuple[str, str, int, int]


@dataclass(frozen=True, slots=True)
class LifecycleOps:
    """Explicit mutation/process boundary used by lifecycle and fault tests."""

    run_workflow: WorkflowRunner
    publish_bytes: BytesPublisher
    release_lock: LockReleaser
    now: Callable[[], datetime]
    host_name: Callable[[], str]
    process_id: Callable[[], int]
    process_is_alive: Callable[[int], bool]
    validate_reporting_receipt: inspection.ReportingReceiptValidator
    admit_runtime_context: RuntimeContextAdmission
    sync_directory: DirectorySynchronizer


@dataclass(frozen=True, slots=True)
class LifecycleRequest:
    """One already-materialized direct workflow invocation."""

    run_root: Path
    execution_path: Path
    profile_path: Path
    workflow_config_path: Path
    snakefile: Path
    python_executable: Path
    workflow_profile: Path
    target: str
    operation: Operation
    attempt_record: Mapping[str, Any]
    request_source_path: Path


@dataclass(frozen=True, slots=True)
class LifecycleOutcome:
    """Terminal immutable outcome of one workflow attempt."""

    attempt_path: Path
    receipt_path: Path
    lock_path: Path
    released_lock_path: Path
    receipt: dict[str, Any]
    workflow_result: WorkflowResult | None


def _canonical_file(path: Path, label: str) -> Path:
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise LifecycleError(f"{label} must be an absolute regular file: {path}")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise LifecycleError(f"{label} must already be canonical: {path}")
    return path


def _canonical_root(path: Path) -> Path:
    if not path.is_absolute() or not path.is_dir() or path.is_symlink():
        raise LifecycleError(f"run_root must be an absolute real directory: {path}")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise LifecycleError(f"run_root must already be canonical: {path}")
    return path


def _admit_python_launcher(path: Path) -> PythonLauncherIdentity:
    """Admit the lexical venv launcher and its stable executable target."""

    if not path.is_absolute() or str(path) != sys.executable:
        raise LifecycleError(
            "Workflow Python launcher must equal lexical sys.executable"
        )
    try:
        before = path.lstat()
        link_before = os.readlink(path) if stat.S_ISLNK(before.st_mode) else ""
        target = path.resolve(strict=True)
        target_before = target.stat(follow_symlinks=False)
        after = path.lstat()
        link_after = os.readlink(path) if stat.S_ISLNK(after.st_mode) else ""
        confirmed_target = path.resolve(strict=True)
        target_after = confirmed_target.stat(follow_symlinks=False)
    except OSError as exc:
        raise LifecycleError(
            f"Could not admit workflow Python launcher: {path}"
        ) from exc
    if (
        (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns)
        or link_before != link_after
        or confirmed_target != target
        or (target_before.st_dev, target_before.st_ino, target_before.st_mode)
        != (target_after.st_dev, target_after.st_ino, target_after.st_mode)
        or not stat.S_ISREG(target_after.st_mode)
        or not os.access(target, os.X_OK)
    ):
        raise LifecycleError(
            "Workflow Python launcher identity changed during admission"
        )
    return (
        str(target),
        link_before,
        target_after.st_dev,
        target_after.st_ino,
    )


def _within(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise LifecycleError(f"{label} must be beneath run_root: {path}") from exc


def _require_disjoint_roots(run_root: Path, source_checkout: Path) -> None:
    """Keep orchestration mutations wholly outside the reviewed source tree."""

    if (
        run_root == source_checkout
        or run_root in source_checkout.parents
        or source_checkout in run_root.parents
    ):
        raise LifecycleError(
            "run_root and source_checkout must be disjoint canonical directories"
        )


def build_snakemake_argv(
    *,
    python_executable: Path,
    snakefile: Path,
    workflow_profile: Path,
    configfile: Path,
    run_root: Path,
    target: str,
    operation: Operation,
) -> tuple[str, ...]:
    """Construct the fixed direct invocation and reject recovery bypasses."""

    if _SAFE_RULE_RE.fullmatch(target) is None:
        raise LifecycleError(f"Snakemake target is not one safe rule name: {target!r}")
    if (
        not workflow_profile.is_absolute()
        or workflow_profile.is_symlink()
        or not workflow_profile.is_file()
        or workflow_profile.resolve(strict=True) != workflow_profile
    ):
        raise LifecycleError(
            f"Workflow profile must be an absolute canonical file: {workflow_profile}"
        )
    if operation not in {"execute", "resume"}:
        raise LifecycleError(f"Unsupported lifecycle operation: {operation}")
    argv = [
        *controlled_python_argv(python_executable),
        "-m",
        "snakemake",
        "--snakefile",
        str(snakefile),
        "--workflow-profile",
        str(workflow_profile),
        "--configfile",
        str(configfile),
        "--directory",
        str(run_root),
        "--nocolor",
    ]
    if operation == "resume":
        argv.extend(("--rerun-triggers", "input", "--ignore-incomplete"))
    argv.extend(("--", target))
    observed = _FORBIDDEN_SNAKEMAKE_FLAGS.intersection(argv)
    if observed:
        raise LifecycleError(
            "Forbidden Snakemake recovery controls: " + ", ".join(sorted(observed))
        )
    return tuple(argv)


def _publish_exclusive(path: Path, data: bytes) -> None:
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        raise LifecycleError(f"Publication parent must be a real directory: {parent}")
    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW publication")
    staging = parent / f".{path.name}.{uuid.uuid4().hex}.norad-stage"
    descriptor = -1
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(staging, flags, 0o600)
        remaining = memoryview(data)
        while remaining:
            written = os.write(descriptor, remaining)
            remaining = remaining[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(staging, path, follow_symlinks=False)
        staged = staging.stat(follow_symlinks=False)
        final = path.stat(follow_symlinks=False)
        if (staged.st_dev, staged.st_ino) != (final.st_dev, final.st_ino):
            raise LifecycleError(f"Publication did not retain staged inode: {path}")
        staging.unlink()
        directory = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileExistsError as exc:
        raise LifecycleError(f"Refusing to replace existing file: {path}") from exc
    except OSError as exc:
        raise LifecycleError(f"Could not publish {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


def _sync_real_directory(path: Path, label: str) -> None:
    """Durably admit and synchronize one exact no-follow directory path."""

    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW directory sync")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    try:
        if path.resolve(strict=True) != path:
            raise LifecycleError(f"{label} must be a canonical real directory: {path}")
        descriptor = os.open(path, flags)
        try:
            state = os.fstat(descriptor)
            if not stat.S_ISDIR(state.st_mode):
                raise LifecycleError(f"{label} is not a real directory: {path}")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise LifecycleError(f"Could not synchronize {label}: {path}: {exc}") from exc


def _release_owned_lock(
    path: Path,
    evidence_path: Path,
    expected_bytes: bytes,
    expected_inode: tuple[int, int],
    *,
    publish_evidence: LockEvidencePublisher | None = None,
) -> None:
    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW lock release")
    descriptor = -1
    try:
        for directory, label in (
            (path.parent, "aggregate lock directory"),
            (evidence_path.parent, "released-lock evidence directory"),
        ):
            if (
                directory.is_symlink()
                or not directory.is_dir()
                or directory.resolve(strict=True) != directory
            ):
                raise LifecycleError(f"{label} must be a canonical real directory")
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or (
                before.st_dev,
                before.st_ino,
            )
            != expected_inode
        ):
            raise LifecycleError(f"Run lock ownership changed before release: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (after.st_dev, after.st_ino) != expected_inode:
            raise LifecycleError(f"Run lock ownership changed while read: {path}")
        if b"".join(chunks) != expected_bytes:
            raise LifecycleError(f"Run lock content changed before release: {path}")
        path_state = path.stat(follow_symlinks=False)
        if (path_state.st_dev, path_state.st_ino) != expected_inode:
            raise LifecycleError(f"Run lock pathname changed before release: {path}")
        if evidence_path.exists() or evidence_path.is_symlink():
            raise LifecycleError(
                f"Refusing to replace released-lock evidence: {evidence_path}"
            )
        evidence_publisher = os.rename if publish_evidence is None else publish_evidence
        evidence_publisher(path, evidence_path)
        evidence_state = evidence_path.stat(follow_symlinks=False)
        if (evidence_state.st_dev, evidence_state.st_ino) != expected_inode:
            raise LifecycleError(
                "Run lock ownership changed at atomic release boundary; "
                f"evidence retained at {evidence_path}"
            )
        os.lseek(descriptor, 0, os.SEEK_SET)
        retained_chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            retained_chunks.append(chunk)
        retained_state = os.fstat(descriptor)
        retained_identity = (
            retained_state.st_dev,
            retained_state.st_ino,
            retained_state.st_mode,
            retained_state.st_size,
        )
        evidence_identity = (
            evidence_state.st_dev,
            evidence_state.st_ino,
            evidence_state.st_mode,
            evidence_state.st_size,
        )
        if (
            retained_identity != evidence_identity
            or b"".join(retained_chunks) != expected_bytes
        ):
            raise LifecycleError(
                f"Released run-lock evidence changed at publication: {evidence_path}"
            )
        for parent in dict.fromkeys((path.parent, evidence_path.parent)):
            directory = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except OSError as exc:
        raise LifecycleError(f"Could not release owned run lock {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _run_process_group(argv: tuple[str, ...], cwd: Path) -> WorkflowResult:
    """Spawn a new process group and forward ordinary termination signals."""

    try:
        process = subprocess.Popen(argv, cwd=cwd, start_new_session=True)
    except OSError as exc:
        return WorkflowResult(127, None, f"Could not execute {argv[0]}: {exc}")
    forwarded: list[int] = []
    prior_handlers: dict[int, Any] = {}

    def forward(signum: int, _frame: FrameType | None) -> None:
        if not forwarded:
            forwarded.append(signum)
        try:
            os.killpg(process.pid, signum)
        except ProcessLookupError:
            pass

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            prior_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, forward)
        return_code = process.wait()
    finally:
        for signum, handler in prior_handlers.items():
            signal.signal(signum, handler)
    if forwarded:
        return WorkflowResult(None, forwarded[0], "Lifecycle signal forwarded")
    if return_code < 0:
        return WorkflowResult(None, -return_code, "Workflow process was signaled")
    return WorkflowResult(return_code, None, None)


def _process_is_alive(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _tool_version(argv: Sequence[str], label: str) -> str:
    try:
        completed = subprocess.run(
            [*argv, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise LifecycleError(f"Could not observe required tool: {label}") from exc
    version = completed.stdout.strip().splitlines()
    if not version or not version[0].strip():
        raise LifecycleError(f"Required tool reported no version: {label}")
    return version[0].strip()


def _admit_runtime_context(
    attempt: Mapping[str, Any],
    request: LifecycleRequest,
) -> None:
    """Observe clean source/package and exact required executor identity."""

    from norad.libraries import source_authority  # noqa: PLC0415

    declared = attempt["source_checkout"]
    _admit_python_launcher(request.python_executable)
    observed = source_authority.inspect_source_checkout(
        root=Path(str(declared["path"])),
        package_root=Path(__file__).resolve().parents[2],
        require_clean=True,
    )
    if (
        observed.root != Path(str(declared["path"]))
        or observed.commit != declared["commit"]
        or observed.clean is not True
    ):
        raise LifecycleError("Declared source checkout differs from observed identity")
    try:
        request.snakefile.relative_to(observed.root)
    except ValueError as exc:
        raise LifecycleError("Snakefile is outside declared source checkout") from exc
    tools = {str(item["name"]): item for item in attempt["required_tools"]}
    python = tools.get("python")
    snakemake = tools.get("snakemake")
    if python is None or snakemake is None:
        raise LifecycleError(
            "Workflow attempt must declare required Python and Snakemake identities"
        )
    if Path(str(python["path"])) != request.python_executable:
        raise LifecycleError("Required Python path differs from workflow runtime")
    if Path(str(attempt["normalizer"]["path"])) != request.python_executable:
        raise LifecycleError("Normalizer does not bind the workflow Python runtime")
    observed_python_version = _tool_version((str(request.python_executable),), "python")
    expected_python_version = platform.python_version()
    if observed_python_version.split()[-1] != expected_python_version:
        raise LifecycleError("Bound Python runtime version differs from this process")
    if python["version"] != expected_python_version:
        raise LifecycleError("Required Python version differs from the bound runtime")
    if Path(str(snakemake["path"])) != request.python_executable:
        raise LifecycleError("Snakemake module identity must bind the Python runtime")
    observed_version = _tool_version(
        controlled_python_argv(request.python_executable, "-m", "snakemake"),
        "snakemake module",
    )
    if observed_version != snakemake["version"]:
        raise LifecycleError(
            "Required Snakemake version differs: "
            f"declared {snakemake['version']!r}; observed {observed_version!r}"
        )
    for name, identity in tools.items():
        path = Path(str(identity["path"]))
        if name in {"python", "snakemake"}:
            continue
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise LifecycleError(
                f"Required tool path is not admissible: {name}: {path}"
            )
        observed = _tool_version((str(path),), name)
        if observed != identity["version"]:
            raise LifecycleError(
                f"Required {name} version differs: declared "
                f"{identity['version']!r}; observed {observed!r}"
            )


def default_lifecycle_ops() -> LifecycleOps:
    """Construct production effects without mutable facade globals."""

    from norad.reporting import transaction_validation  # noqa: PLC0415

    return LifecycleOps(
        run_workflow=_run_process_group,
        publish_bytes=_publish_exclusive,
        release_lock=_release_owned_lock,
        now=lambda: datetime.now(UTC),
        host_name=socket.gethostname,
        process_id=os.getpid,
        process_is_alive=_process_is_alive,
        validate_reporting_receipt=transaction_validation.validate_receipt,
        admit_runtime_context=_admit_runtime_context,
        sync_directory=_sync_real_directory,
    )


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise LifecycleError("Lifecycle clock must return timezone-aware values")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_stable_with_identity(
    path: Path, root: Path, label: str
) -> tuple[bytes, tuple[int, int]]:
    _within(path, root, label)
    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW admission")
    try:
        if path.resolve(strict=True) != path:
            raise LifecycleError(f"{label} path is not canonical: {path}")
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise LifecycleError(f"Could not admit {label}: {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise LifecycleError(f"{label} is not a regular file: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_state = path.stat(follow_symlinks=False)
    identity = lambda value: (  # noqa: E731
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    if identity(before) != identity(after) or identity(after) != identity(path_state):
        raise LifecycleError(f"{label} changed while it was read: {path}")
    data = b"".join(chunks)
    if len(data) != before.st_size:
        raise LifecycleError(f"{label} size changed while it was read: {path}")
    return data, (after.st_dev, after.st_ino)


def _read_stable(path: Path, root: Path, label: str) -> bytes:
    return _read_stable_with_identity(path, root, label)[0]


def _read_external_stable(path: Path, label: str) -> bytes:
    """Read one canonical external regular file through a no-follow descriptor."""

    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW admission")
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise LifecycleError(f"Could not admit {label}: {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise LifecycleError(f"{label} is not a regular file: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        path_state = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise LifecycleError(f"Could not restat {label}: {path}: {exc}") from exc
    identity = lambda value: (  # noqa: E731
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    data = b"".join(chunks)
    if (
        identity(before) != identity(after)
        or identity(after) != identity(path_state)
        or len(data) != before.st_size
    ):
        raise LifecycleError(f"{label} changed while it was admitted: {path}")
    return data


def _reference(path: Path, root: Path, label: str) -> dict[str, str]:
    data = _read_stable(path, root, label)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _verified_references(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    references: list[dict[str, Any]] = []
    blockers: list[str] = []
    missing: list[str] = []
    verified_root = root / "state" / "verified"
    expected_tasks = inspection.expected_tasks(execution, profile)
    for expected in expected_tasks:
        path = verified_root / expected.machine_key / f"{expected.scope_id}.json"
        if not path.exists() and not path.is_symlink():
            missing.append(f"{expected.machine_key}/{expected.scope_id}")
            continue
        try:
            reference_before = _reference(path, root, "verified task record")
            task.validate_verified_task(
                path,
                run_root=root,
                execution=execution,
                profile=profile,
                machine_key=expected.machine_key,
                scope=expected.scope,
            )
            reference_after = _reference(path, root, "verified task record")
            if reference_after != reference_before:
                raise LifecycleError(
                    "Verified task record changed during semantic admission"
                )
            reference = reference_before
        except (
            OSError,
            LifecycleError,
            task.TaskBoundaryError,
            orchestration_contracts.ContractValidationError,
        ) as exc:
            blockers.append(f"Could not admit reusable verified task {path}: {exc}")
            continue
        references.append(
            {
                "machine_key": expected.machine_key,
                "scope": expected.scope,
                "record": reference,
            }
        )
    blockers.extend(inspection.verified_tree_blockers(root, expected_tasks))
    return references, blockers, missing


def _task_start_references(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Admit the exact producer-entry ledger in normalized owner/scope order."""

    references: list[dict[str, Any]] = []
    blockers: list[str] = []
    expected = inspection.expected_tasks(execution, profile)
    for item in sorted(
        expected,
        key=lambda value: (value.machine_key, value.scope_type, value.scope_id),
    ):
        path = (
            root / "state" / "task-starts" / item.machine_key / f"{item.scope_id}.json"
        )
        if not path.exists() and not path.is_symlink():
            continue
        try:
            reference_before = _reference(path, root, "task-start record")
            task.validate_task_start(
                path,
                run_root=root,
                execution=execution,
                profile=profile,
                machine_key=item.machine_key,
                scope=item.scope,
            )
            reference_after = _reference(path, root, "task-start record")
            if reference_after != reference_before:
                raise LifecycleError(
                    "Task-start record changed during semantic admission"
                )
        except (
            OSError,
            LifecycleError,
            task.TaskBoundaryError,
            orchestration_contracts.ContractValidationError,
        ) as exc:
            blockers.append(f"Could not admit task-start record {path}: {exc}")
            continue
        references.append(
            {
                "machine_key": item.machine_key,
                "scope": item.scope,
                "record": reference_before,
            }
        )
    blockers.extend(inspection.task_start_tree_blockers(root, expected))
    return references, blockers


def _incomplete_task_start_blockers(
    task_starts: Sequence[Mapping[str, Any]],
    verified: Sequence[Mapping[str, Any]],
) -> list[str]:
    verified_identities = {
        (
            str(item["machine_key"]),
            str(item["scope"]["scope_type"]),
            str(item["scope"]["scope_id"]),
        )
        for item in verified
    }
    return [
        "Entered task scope has no succeeded task-attempt and verified record: "
        f"{item['machine_key']}/{item['scope']['scope_id']}"
        for item in task_starts
        if (
            str(item["machine_key"]),
            str(item["scope"]["scope_type"]),
            str(item["scope"]["scope_id"]),
        )
        not in verified_identities
    ]


def _preentry_task_attempt_references(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Use the inspection owner for the shared historical task-tree contract."""

    return inspection.inspect_attempt_task_trees(root, execution, profile, attempts)


def _admit_request(
    request: LifecycleRequest,
    ops: LifecycleOps,
) -> tuple[
    Path,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    tuple[str, ...],
    dict[str, str],
    bytes,
]:
    root = _canonical_root(request.run_root)
    _within(request.execution_path, root, "execution contract")
    _within(request.profile_path, root, "profile snapshot")
    execution_path = _canonical_file(request.execution_path, "execution contract")
    profile_path = _canonical_file(request.profile_path, "profile snapshot")
    config_path = _canonical_file(request.workflow_config_path, "workflow config")
    request_source_path = _canonical_file(
        request.request_source_path, "authored request source"
    )
    _within(config_path, root, "workflow config")
    snakefile = _canonical_file(request.snakefile, "Snakefile")
    workflow_profile = _canonical_file(request.workflow_profile, "workflow profile")
    python_executable = request.python_executable
    _admit_python_launcher(python_executable)
    profile_data = _read_stable(profile_path, root, "profile snapshot")
    execution_data = _read_stable(execution_path, root, "execution contract")
    config_data = _read_stable(config_path, root, "workflow config")
    request_source_data = _read_external_stable(
        request_source_path, "authored request source"
    )
    try:
        profile = orchestration_contracts.load_json_object_bytes(
            profile_data, f"profile snapshot {profile_path}"
        )
        orchestration_contracts.validate_record("profile", profile)
        execution = orchestration_contracts.load_json_object_bytes(
            execution_data, f"execution contract {execution_path}"
        )
        orchestration_contracts.validate_record("execution", execution, profile=profile)
        config_document = orchestration_contracts.load_json_object_bytes(
            config_data, f"workflow config {config_path}"
        )
    except orchestration_contracts.ContractValidationError as exc:
        raise LifecycleError(f"Could not admit immutable run contracts: {exc}") from exc
    if profile_data != orchestration_contracts.canonical_json_bytes(profile):
        raise LifecycleError("Profile snapshot must use canonical JSON bytes")
    if execution_data != orchestration_contracts.canonical_json_bytes(execution):
        raise LifecycleError("Execution contract must use canonical JSON bytes")
    canonical_config = orchestration_contracts.canonical_json_bytes(config_document)
    if config_data != canonical_config:
        raise LifecycleError("Workflow config must use canonical JSON bytes")
    config_reference = {
        "path": config_path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(config_data).hexdigest(),
    }
    argv = build_snakemake_argv(
        python_executable=python_executable,
        snakefile=snakefile,
        workflow_profile=request.workflow_profile,
        configfile=config_path,
        run_root=root,
        target=request.target,
        operation=request.operation,
    )
    attempt = dict(request.attempt_record)
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    identifier = str(attempt["workflow_attempt_id"])
    source_root = Path(str(attempt["source_checkout"]["path"]))
    _require_disjoint_roots(root, source_root)
    expected_snakefile = source_root / "workflow" / "Snakefile"
    expected_workflow_profile = (
        source_root / "workflow" / "profiles" / "local" / "profile.v9+.yaml"
    )
    if snakefile != expected_snakefile:
        raise LifecycleError("Lifecycle requires the reviewed workflow/Snakefile")
    if workflow_profile != expected_workflow_profile:
        raise LifecycleError("Lifecycle requires the reviewed local workflow profile")
    expected_config_relative = (
        Path("contract") / "workflow-configs" / f"{identifier}.json"
    ).as_posix()
    if config_reference["path"] != expected_config_relative:
        raise LifecycleError(
            "Workflow config must use its attempt-specific immutable path"
        )
    config_identity = {
        "run_root": str(root),
        "execution_path": str(execution_path),
        "profile_path": str(profile_path),
        "workflow_attempt_id": identifier,
        "python_executable": str(python_executable),
    }
    for field, value in config_identity.items():
        if config_document.get(field) != value:
            raise LifecycleError(f"Workflow config does not bind {field}")
    expected = {
        "run_id": execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(execution_data).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_data).hexdigest(),
        "operation": request.operation,
        "executor": "local",
        "snakemake_argv": list(argv),
        "workflow_config": config_reference,
        "host": ops.host_name(),
        "process_id": ops.process_id(),
    }
    for field, value in expected.items():
        if attempt[field] != value:
            raise LifecycleError(f"Workflow attempt does not bind {field}")
    if str(python_executable) != sys.executable:
        raise LifecycleError(
            "Workflow Python runtime must equal lexical sys.executable"
        )
    if Path(str(attempt["authored_paths"]["request"])) != request_source_path:
        raise LifecycleError(
            "Workflow attempt does not name its authored request source"
        )
    request_snapshot_path = root / "attempts" / identifier / "request.yaml"
    if attempt["request"] != {
        "path": str(request_snapshot_path),
        "size_bytes": len(request_source_data),
        "sha256": hashlib.sha256(request_source_data).hexdigest(),
    }:
        raise LifecycleError("Workflow attempt does not bind authored request source")
    ops.admit_runtime_context(attempt, request)
    workspace = Path(str(attempt["workspace"]))
    if not workspace.is_absolute():
        raise LifecycleError("Workflow attempt workspace must be absolute")
    try:
        root.relative_to(workspace)
    except ValueError as exc:
        raise LifecycleError(
            "Workflow attempt workspace does not contain run_root"
        ) from exc
    return (
        root,
        profile,
        execution,
        attempt,
        argv,
        config_reference,
        request_source_data,
    )


def _operation_preflight(
    request: LifecycleRequest,
    root: Path,
    attempt: Mapping[str, Any],
    ops: LifecycleOps,
) -> None:
    namespace_blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=False),
    ]
    if namespace_blockers:
        raise LifecycleError(
            "Aggregate run namespace is not admissible: "
            + "; ".join(namespace_blockers)
        )
    attempt_entries, attempt_blockers = inspection.inspect_attempt_tree(root)
    if attempt_blockers:
        raise LifecycleError(
            "Aggregate attempt state is not admissible: " + "; ".join(attempt_blockers)
        )
    if request.operation == "execute":
        if attempt_entries:
            raise LifecycleError("Initial execution refuses a run with prior attempts")
        if attempt["supersedes_workflow_attempt_id"] is not None:
            raise LifecycleError("Initial execution may not supersede an attempt")
        return
    observed = inspection.inspect_run(
        root,
        ops=inspection.InspectionOps(
            ops.host_name,
            ops.process_is_alive,
            ops.validate_reporting_receipt,
        ),
    )
    if observed.local_pipeline_complete:
        raise LifecycleError("Completed run refuses resume")
    if observed.state != "resume_available":
        raise LifecycleError(
            "Resume requires an independently revalidated between-task boundary: "
            + "; ".join(observed.blockers or (observed.state,))
        )
    latest = observed.latest_attempt
    receipt = observed.latest_receipt
    if latest is None or receipt is None:
        raise LifecycleError("Resume requires one terminal prior workflow attempt")
    if receipt["status"] not in {"failed", "interrupted"}:
        raise LifecycleError("Only a failed or interrupted attempt may be resumed")
    if attempt["supersedes_workflow_attempt_id"] != latest["workflow_attempt_id"]:
        raise LifecycleError("Resume must supersede the exact latest workflow attempt")
    for field in (
        "run_id",
        "execution_contract_sha256",
        "profile_sha256",
        "source_checkout",
        "required_tools",
        "execution_mode",
        "executor",
    ):
        if attempt[field] != latest[field]:
            raise LifecycleError(f"Resume attempt is incompatible on {field}")


def _under_lock_attempt_preflight(
    request: LifecycleRequest,
    root: Path,
    attempt: Mapping[str, Any],
    ops: LifecycleOps,
) -> None:
    """Repeat the attempt-chain predicate at the serialization boundary."""

    namespace_blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=True),
    ]
    if namespace_blockers:
        raise LifecycleError(
            "Aggregate run namespace changed at lock boundary: "
            + "; ".join(namespace_blockers)
        )

    attempt_entries, attempt_blockers = inspection.inspect_attempt_tree(root)
    if attempt_blockers:
        raise LifecycleError(
            "Aggregate attempt state changed before attempt publication: "
            + "; ".join(attempt_blockers)
        )
    if request.operation == "execute":
        if attempt_entries:
            raise LifecycleError("Initial execution lost attempt-chain race")
        return
    observed = inspection.inspect_run(
        root,
        ops=inspection.InspectionOps(
            ops.host_name,
            ops.process_is_alive,
            ops.validate_reporting_receipt,
        ),
        allowed_next_attempt=attempt,
    )
    if (
        observed.state != "resume_available"
        or observed.latest_attempt is None
        or observed.latest_receipt is None
    ):
        raise LifecycleError(
            "Resume lost its revalidated between-task boundary under lock"
        )
    if attempt["supersedes_workflow_attempt_id"] != observed.latest_attempt[
        "workflow_attempt_id"
    ] or observed.latest_receipt["status"] not in {"failed", "interrupted"}:
        raise LifecycleError("Resume lost its admissible terminal predecessor")
    for field in (
        "run_id",
        "execution_contract_sha256",
        "profile_sha256",
        "source_checkout",
        "required_tools",
        "execution_mode",
        "executor",
    ):
        if attempt[field] != observed.latest_attempt[field]:
            raise LifecycleError(f"Resume became incompatible on {field}")


def _terminal_receipt(
    *,
    root: Path,
    attempt: Mapping[str, Any],
    attempt_path: Path,
    released_lock_path: Path,
    lock_bytes: bytes,
    status: str,
    result: WorkflowResult | None,
    preentry_tasks: list[dict[str, Any]],
    task_starts: list[dict[str, Any]],
    verified: list[dict[str, Any]],
    reporting: Mapping[str, Mapping[str, dict[str, str] | None]],
    blockers: Sequence[str],
    message: str | None,
    now: datetime,
) -> dict[str, Any]:
    receipt = {
        "schema_version": "norad.attempt-receipt.v1",
        "run_id": attempt["run_id"],
        "execution_contract_sha256": attempt["execution_contract_sha256"],
        "profile_sha256": attempt["profile_sha256"],
        "workflow_attempt_id": attempt["workflow_attempt_id"],
        "attempt_record": _reference(attempt_path, root, "workflow-attempt"),
        "released_run_lock": {
            "path": released_lock_path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(lock_bytes).hexdigest(),
        },
        "status": status,
        "finished_at": _timestamp(now),
        "snakemake_exit_code": None if result is None else result.exit_code,
        "termination_signal": None if result is None else result.termination_signal,
        "preentry_task_attempt_records": preentry_tasks,
        "task_start_records": task_starts,
        "verified_tasks": verified,
        "reporting_completion_records": dict(reporting),
        "blockers": list(dict.fromkeys(blockers)),
        "message": message,
        "local_pipeline_complete": status == "succeeded",
    }
    orchestration_contracts.validate_record("attempt-receipt", receipt)
    return receipt


def run_attempt(
    request: LifecycleRequest,
    *,
    ops: LifecycleOps | None = None,
) -> LifecycleOutcome:
    """Execute one immutable local attempt and publish its receipt last."""

    active_ops = default_lifecycle_ops() if ops is None else ops
    (
        root,
        profile,
        execution,
        attempt,
        argv,
        config_reference,
        request_source_data,
    ) = _admit_request(request, active_ops)
    _operation_preflight(request, root, attempt, active_ops)
    identifier = str(attempt["workflow_attempt_id"])
    attempt_root = root / "attempts" / identifier
    locks_root = root / "locks"
    for directory in (root / "attempts", locks_root):
        if directory.is_symlink() or not directory.is_dir():
            raise LifecycleError(
                f"Lifecycle parent must be pre-materialized and real: {directory}"
            )
    attempt_path = attempt_root / "attempt.json"
    receipt_path = attempt_root / "attempt-receipt.json"
    lock_path = locks_root / "run.lock"
    released_lock_path = attempt_root / "released-run-lock.json"

    lock_record = {
        "schema_version": "norad.run-lock.v1",
        "run_id": attempt["run_id"],
        "workflow_attempt_id": identifier,
        "attempt_record_path": f"attempts/{identifier}/attempt.json",
        "owner_token": attempt["owner_token"],
        "process_id": attempt["process_id"],
        "host": attempt["host"],
        "created_at": attempt["created_at"],
    }
    orchestration_contracts.validate_record("run-lock", lock_record)
    lock_bytes = orchestration_contracts.canonical_json_bytes(lock_record)
    active_ops.publish_bytes(lock_path, lock_bytes)
    lock_state = lock_path.stat(follow_symlinks=False)
    lock_inode = (lock_state.st_dev, lock_state.st_ino)
    attempt_root_created = False
    try:
        _under_lock_attempt_preflight(request, root, attempt, active_ops)
        if (
            _reference(request.workflow_config_path, root, "workflow config")
            != config_reference
        ):
            raise LifecycleError("Workflow config changed before attempt publication")
        pre_spawn_bindings = (
            (
                request.execution_path,
                "execution contract",
                attempt["execution_contract_sha256"],
            ),
            (request.profile_path, "profile snapshot", attempt["profile_sha256"]),
        )
        for binding_path, label, expected_sha256 in pre_spawn_bindings:
            if _reference(binding_path, root, label)["sha256"] != expected_sha256:
                raise LifecycleError(f"{label} changed before attempt publication")
        request_source_after = _read_external_stable(
            request.request_source_path, "authored request source"
        )
        if request_source_after != request_source_data:
            raise LifecycleError("Authored request changed before attempt publication")
        _admit_python_launcher(request.python_executable)
        attempt_root.mkdir(mode=0o700)
        attempt_root_created = True
        if attempt_root.is_symlink() or not attempt_root.is_dir():
            raise LifecycleError(f"Attempt directory must be real: {attempt_root}")
        active_ops.sync_directory(attempt_root, "new workflow-attempt directory")
        active_ops.sync_directory(attempt_root.parent, "aggregate attempts directory")
        active_ops.publish_bytes(attempt_root / "request.yaml", request_source_data)
        active_ops.publish_bytes(
            attempt_path,
            orchestration_contracts.canonical_json_bytes(attempt),
        )
    except Exception as exc:
        failure_evidence_path = (
            released_lock_path
            if attempt_root_created
            else locks_root / f"released-{identifier}-run-lock.json"
        )
        active_ops.release_lock(
            lock_path, failure_evidence_path, lock_bytes, lock_inode
        )
        raise LifecycleError(
            f"Could not establish immutable workflow attempt: {exc}"
        ) from exc

    result: WorkflowResult | None = None
    verified, task_blockers, missing = _verified_references(root, execution, profile)
    task_starts, start_blockers = _task_start_references(root, execution, profile)
    preentry_tasks, task_tree_blockers = _preentry_task_attempt_references(
        root, execution, profile, (attempt,)
    )
    blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=True),
        *task_blockers,
        *start_blockers,
        *task_tree_blockers,
        *_incomplete_task_start_blockers(task_starts, verified),
    ]
    reporting, reporting_blockers = inspection.inspect_reporting_ledger(
        root,
        execution,
        profile,
        active_ops.validate_reporting_receipt,
    )
    blockers.extend(reporting_blockers)
    if blockers:
        status = "blocked"
        message = "Workflow preflight found ambiguous reusable state"
    else:
        _admit_python_launcher(request.python_executable)
        try:
            candidate = active_ops.run_workflow(argv, root)
        except Exception as exc:
            raise LifecycleError(
                "Workflow runner failed without a terminal child observation; "
                "the owned run lock is retained"
            ) from exc
        runtime_blockers: list[str] = []
        if not isinstance(candidate, WorkflowResult):
            runtime_blockers.append(
                "Workflow runner returned no typed terminal observation"
            )
        elif (
            (candidate.exit_code is None) == (candidate.termination_signal is None)
            or (
                candidate.exit_code is not None
                and (
                    type(candidate.exit_code) is not int
                    or not 0 <= candidate.exit_code <= 255
                )
            )
            or (
                candidate.termination_signal is not None
                and (
                    type(candidate.termination_signal) is not int
                    or candidate.termination_signal < 1
                )
            )
        ):
            runtime_blockers.append(
                "Workflow runner returned an invalid terminal observation"
            )
        else:
            result = candidate
        try:
            active_ops.admit_runtime_context(attempt, request)
        except Exception as exc:
            runtime_blockers.append(
                f"Runtime identity changed during workflow execution: {exc}"
            )
        try:
            config_after = _reference(
                request.workflow_config_path, root, "workflow config"
            )
            if config_after != config_reference:
                raise LifecycleError("Workflow config changed during execution")
        except Exception as exc:
            runtime_blockers.append(str(exc))
        for binding_path, label, expected_sha256 in (
            (
                request.execution_path,
                "execution contract",
                attempt["execution_contract_sha256"],
            ),
            (request.profile_path, "profile snapshot", attempt["profile_sha256"]),
        ):
            try:
                if _reference(binding_path, root, label)["sha256"] != expected_sha256:
                    raise LifecycleError(f"{label} changed during execution")
            except Exception as exc:
                runtime_blockers.append(str(exc))
        try:
            attempt_reference = _reference(attempt_path, root, "workflow-attempt")
            expected_attempt_reference = {
                "path": attempt_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(
                    orchestration_contracts.canonical_json_bytes(attempt)
                ).hexdigest(),
            }
            if attempt_reference != expected_attempt_reference:
                raise LifecycleError("Workflow attempt changed during execution")
        except Exception as exc:
            runtime_blockers.append(str(exc))
        try:
            request_snapshot = _read_stable(
                attempt_root / "request.yaml", root, "attempt request snapshot"
            )
            if request_snapshot != request_source_data:
                raise LifecycleError(
                    "Attempt request snapshot changed during execution"
                )
        except Exception as exc:
            runtime_blockers.append(str(exc))
        verified, task_blockers, missing = _verified_references(
            root, execution, profile
        )
        task_starts, start_blockers = _task_start_references(root, execution, profile)
        attempts, _receipts, _chain_blockers = inspection.inspect_attempt_chain(root)
        preentry_tasks, task_tree_blockers = _preentry_task_attempt_references(
            root, execution, profile, attempts
        )
        task_tree_blockers.extend(_chain_blockers)
        reporting, reporting_blockers = inspection.inspect_reporting_ledger(
            root,
            execution,
            profile,
            active_ops.validate_reporting_receipt,
        )
        blockers = [
            *runtime_blockers,
            *inspection.state_tree_blockers(root),
            *inspection.lock_tree_blockers(root, expected_run_lock=True),
            *task_blockers,
            *start_blockers,
            *task_tree_blockers,
            *_incomplete_task_start_blockers(task_starts, verified),
            *reporting_blockers,
        ]
        if blockers:
            status = "blocked"
            message = "Workflow termination left ambiguous owner state"
        elif result is None:
            raise AssertionError("invalid workflow observation lacked a blocker")
        elif result.termination_signal is not None:
            status = "interrupted"
            message = result.message or "Workflow execution was interrupted"
        elif result.exit_code != 0:
            status = "failed"
            message = result.message or f"Snakemake exited {result.exit_code}"
        elif (
            blockers
            or missing
            or any(
                state["start"] is None or state["verified"] is None
                for state in reporting.values()
            )
        ):
            status = "failed"
            absent = [*missing]
            absent.extend(
                name
                for name, state in reporting.items()
                if state["start"] is None or state["verified"] is None
            )
            message = "Snakemake exited zero without complete NORAD state"
            if absent:
                message += ": " + ", ".join(absent)
        else:
            status = "succeeded"
            message = None

    final_active_namespace_blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=True),
    ]
    if final_active_namespace_blockers:
        blockers.extend(final_active_namespace_blockers)
        status = "blocked"
        message = "Workflow termination left ambiguous aggregate state"

    active_ops.release_lock(lock_path, released_lock_path, lock_bytes, lock_inode)
    released_bytes, released_inode = _read_stable_with_identity(
        released_lock_path,
        root,
        "released run-lock evidence",
    )
    if released_bytes != lock_bytes or released_inode != lock_inode:
        raise LifecycleError(
            "Released run-lock evidence does not retain the owned descriptor identity"
        )
    released_namespace_blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=False),
    ]
    if released_namespace_blockers:
        blockers.extend(released_namespace_blockers)
        status = "blocked"
        message = "Workflow lock release left ambiguous aggregate state"
    receipt = _terminal_receipt(
        root=root,
        attempt=attempt,
        attempt_path=attempt_path,
        released_lock_path=released_lock_path,
        lock_bytes=lock_bytes,
        status=status,
        result=result,
        preentry_tasks=preentry_tasks,
        task_starts=task_starts,
        verified=verified,
        reporting=reporting,
        blockers=blockers,
        message=message,
        now=active_ops.now(),
    )
    active_ops.publish_bytes(
        receipt_path,
        orchestration_contracts.canonical_json_bytes(receipt),
    )
    return LifecycleOutcome(
        attempt_path=attempt_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
        released_lock_path=released_lock_path,
        receipt=receipt,
        workflow_result=result,
    )


__all__ = (
    "LifecycleError",
    "LifecycleOps",
    "LifecycleOutcome",
    "LifecycleRequest",
    "RuntimeContextAdmission",
    "WorkflowResult",
    "build_snakemake_argv",
    "default_lifecycle_ops",
    "run_attempt",
)
