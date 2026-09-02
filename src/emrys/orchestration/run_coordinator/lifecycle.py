"""Internal lifecycle owner for direct local Snakemake execution.

This module intentionally does not register the top-level
``emrys run/resume/inspect`` routes itself. It is the direct API beneath the
public control adapter: it publishes immutable attempt state, owns the
aggregate run lock, and treats Snakemake as an executor rather than as run-state
authority.
"""

from __future__ import annotations

import hashlib
import errno
import os
import re
import signal
import socket
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, Any, Iterator, Literal

if TYPE_CHECKING:
    from emrys.evidence.runtime_availability.inspector import RuntimeInspection
    from emrys.evidence.storage_inventory.qualification import QualifiedStorage
    from emrys.orchestration.run_coordinator.doctor import RuntimeBinding

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised only on unsupported platforms
    _fcntl = None  # type: ignore[assignment]

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    RUN_BINDING_SCHEMA_VERSION,
    validate_successor_run,
)
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_package_tree_identity,
)
from emrys.libraries.exclusive_publication import publish_exclusive
from emrys.libraries.process_environment import (
    guarded_r_environment,
    process_is_alive,
    sanitized_subprocess_environment,
)
from emrys.libraries.source_authority import controlled_python_argv
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes_with_identity
from emrys.orchestration.run_coordinator import inspection
from emrys.orchestration.run_coordinator.resource_policy import (
    REPEATABLE_STAGE_IDS,
    ResourceConfigError,
    ResourcePlan,
    admit_resource_policy_record,
    stage_slot_name,
)
from emrys.orchestration.run_coordinator.run_implementation import (
    BACKEND_OPERATION_FLAGS,
    BACKEND_TARGET,
    SNAKEFILE_RELATIVE,
    WORKFLOW_PROFILE_RELATIVE,
    RunImplementationError,
    backend_semantics_identity,
    execution_module_id,
    implementation_identity,
)

Operation = Literal["execute", "resume"]
_SAFE_RULE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_RESOURCE_LIMIT_NAMES = frozenset({"mem_mb", *(stage_slot_name(step_id) for step_id in REPEATABLE_STAGE_IDS)})
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


class ProcessGroupAmbiguity(LifecycleError):
    """Raised when the delegated process group cannot be proved quiescent."""


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Terminal observation of the delegated Snakemake process group."""

    exit_code: int | None
    termination_signal: int | None
    message: str | None = None


BytesPublisher = Callable[[Path, bytes], None]
LockReleaser = Callable[[Path, Path, bytes, tuple[int, int]], None]
LockEvidenceLinker = Callable[[Path, Path], None]
StorageContextAdmission = Callable[
    [Mapping[str, Any], Mapping[str, Any]],
    "RuntimeBinding | None",
]
RuntimeContextAdmission = Callable[
    [Mapping[str, Any], "LifecycleRequest", "RuntimeBinding | None", "RuntimeInspection | None"],
    None,
]
DirectorySynchronizer = Callable[[Path, str], None]
PythonLauncherIdentity = tuple[str, str, int, int]
AttemptMaterializer = Callable[[], None]
MutexObserver = Callable[[str, Path], None]
LifecyclePhaseObserver = Callable[[str], None]
ApplicationEventObserver = Callable[[str], None]
SignalHandler = Callable[[int, FrameType | None], None]
SignalHandlerInstaller = Callable[[SignalHandler], tuple[Mapping[int, Any], set[signal.Signals]]]
SignalHandlerRestorer = Callable[[Mapping[int, Any], set[signal.Signals]], None]
ProcessSpawner = Callable[[tuple[str, ...], Path, Mapping[str, str]], Any]
ProcessPoller = Callable[[Any], int | None]
ProcessGroupProbe = Callable[[int], bool]
ProcessGroupSignaler = Callable[[int, int], None]


def _ignore_mutex_event(_event: str, _path: Path) -> None:
    return None


def _ignore_lifecycle_phase(_phase: str) -> None:
    return None


def _ignore_application_event(_event: str) -> None:
    return None


def _install_transaction_signal_handlers(
    handler: SignalHandler,
) -> tuple[Mapping[int, Any], set[signal.Signals]]:
    if not hasattr(signal, "pthread_sigmask") or not hasattr(signal, "SIG_BLOCK"):
        raise LifecycleError("This platform lacks required POSIX lifecycle signal masking")
    watched = {signal.SIGINT, signal.SIGTERM}
    try:
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, watched)
    except (OSError, ValueError) as exc:
        raise LifecycleError(f"Could not block lifecycle signals during handler installation: {exc}") from exc
    if watched.intersection(previous_mask):
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        raise LifecycleError("Lifecycle refuses an ambient mask that already blocks SIGINT or SIGTERM")
    previous: dict[int, Any] = {}
    try:
        for signum in watched:
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handler)
    except (OSError, ValueError) as exc:
        rollback_failures: list[str] = []
        try:
            for signum, prior in previous.items():
                try:
                    signal.signal(signum, prior)
                except (OSError, ValueError) as rollback_exc:
                    rollback_failures.append(f"{signum}: {rollback_exc}")
        finally:
            try:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            except (OSError, ValueError) as mask_exc:
                rollback_failures.append(f"mask: {mask_exc}")
        raise LifecycleError(
            f"Could not install lifecycle signal handlers: {exc}"
            + ("; rollback failures: " + "; ".join(rollback_failures) if rollback_failures else "")
        ) from exc
    try:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    except (OSError, ValueError) as exc:
        for signum, prior in previous.items():
            signal.signal(signum, prior)
        raise LifecycleError(f"Could not restore signal mask after handler installation: {exc}") from exc
    return previous, set(previous_mask)


def _restore_transaction_signal_handlers(
    previous: Mapping[int, Any],
    previous_mask: set[signal.Signals],
) -> None:
    watched = {signal.SIGINT, signal.SIGTERM}
    try:
        signal.pthread_sigmask(signal.SIG_BLOCK, watched)
    except (OSError, ValueError) as exc:
        raise LifecycleError(f"Could not block lifecycle signals during handler restoration: {exc}") from exc
    failures: list[str] = []
    for signum, handler in previous.items():
        try:
            signal.signal(signum, handler)
        except (OSError, ValueError) as exc:
            failures.append(f"{signum}: {exc}")
    try:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    except (OSError, ValueError) as exc:
        failures.append(f"mask: {exc}")
    if failures:
        raise LifecycleError("Could not restore lifecycle signal handlers: " + "; ".join(failures))


def _spawn_process_group(argv: tuple[str, ...], cwd: Path, environment: Mapping[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        argv,
        cwd=cwd,
        env=dict(environment),
        start_new_session=True,
    )


def _poll_process(process: Any) -> int | None:
    return process.poll()


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_process_group(process_group_id: int, signum: int) -> None:
    try:
        os.killpg(process_group_id, signum)
    except ProcessLookupError:
        pass


@dataclass(frozen=True, slots=True)
class TransactionSignalOps:
    """Signal-handler effects admitted by one lifecycle transaction."""

    install_handlers: SignalHandlerInstaller = _install_transaction_signal_handlers
    restore_handlers: SignalHandlerRestorer = _restore_transaction_signal_handlers


@dataclass(frozen=True, slots=True)
class ProcessGroupOps:
    """Explicit process-group effects used by execution and fault tests."""

    spawn: ProcessSpawner = _spawn_process_group
    poll: ProcessPoller = _poll_process
    group_exists: ProcessGroupProbe = _process_group_exists
    signal_group: ProcessGroupSignaler = _signal_process_group
    monotonic: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    poll_interval_seconds: float = 0.02
    terminate_grace_seconds: float = 1.0
    kill_grace_seconds: float = 1.0


DEFAULT_SIGNAL_OPS = TransactionSignalOps()
DEFAULT_PROCESS_GROUP_OPS = ProcessGroupOps()


class TransactionSignalController:
    """Record one ordinary signal and forward it once to registered work."""

    def __init__(
        self,
        signal_ops: TransactionSignalOps,
        process_group_ops: ProcessGroupOps,
    ) -> None:
        self._signal_ops = signal_ops
        self._process_group_ops = process_group_ops
        self._previous: Mapping[int, Any] | None = None
        self._previous_mask: set[signal.Signals] | None = None
        self._process_group_id: int | None = None
        self._forwarded = False
        self._forwarding_error: BaseException | None = None
        self._receipt_commit_blocked = False
        self._receipt_committed = False
        self.first_signal: int | None = None

    def __enter__(self) -> "TransactionSignalController":
        self._previous, self._previous_mask = self._signal_ops.install_handlers(self.record)
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: Any,
    ) -> None:
        previous = self._previous
        previous_mask = self._previous_mask
        if self._receipt_commit_blocked and not self._receipt_committed and previous_mask is not None:
            # No receipt committed. After mutex cleanup, first deliver any
            # pending signal to this controller so publication failure remains
            # a controlled lifecycle error rather than ambient termination.
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            self._receipt_commit_blocked = False
        if previous is not None and previous_mask is not None:
            self._signal_ops.restore_handlers(previous, previous_mask)
            self._previous = None
            self._previous_mask = None
        elif previous_mask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            self._previous_mask = None
        elif previous is not None:
            raise LifecycleError("Lifecycle signal-handler state lost its prior signal mask")

    def block_for_receipt_commit(self) -> None:
        """Linearize receipt publication before restoring ambient handlers."""

        if not hasattr(signal, "pthread_sigmask"):
            raise LifecycleError("This platform lacks required POSIX receipt signal masking")
        signal.pthread_sigmask(
            signal.SIG_BLOCK,
            {signal.SIGINT, signal.SIGTERM},
        )
        self._receipt_commit_blocked = True

    def mark_receipt_committed(self) -> None:
        if not self._receipt_commit_blocked:
            raise LifecycleError("Receipt commit was not signal-masked")
        self._receipt_committed = True

    def record(self, signum: int, _frame: FrameType | None = None) -> None:
        """Record only the first signal and forward it at most once."""

        if signum not in {signal.SIGINT, signal.SIGTERM}:
            raise LifecycleError(f"Unsupported lifecycle signal: {signum}")
        if self.first_signal is None:
            self.first_signal = signum
        self._forward_if_possible()

    def raise_forwarding_error(self) -> None:
        if self._forwarding_error is not None:
            raise ProcessGroupAmbiguity(
                "Could not forward the lifecycle signal to the delegated process group"
            ) from self._forwarding_error

    def register_process_group(self, process_group_id: int) -> None:
        if self._process_group_id is not None:
            raise LifecycleError("A lifecycle process group is already registered")
        self._process_group_id = process_group_id
        self._forward_if_possible()

    def clear_process_group(self, process_group_id: int) -> None:
        if self._process_group_id != process_group_id:
            raise LifecycleError("Lifecycle process-group identity changed")
        self._process_group_id = None

    def _forward_if_possible(self) -> None:
        if self.first_signal is None or self._process_group_id is None or self._forwarded:
            return
        try:
            self._forwarded = True
            self._process_group_ops.signal_group(self._process_group_id, self.first_signal)
        except BaseException as exc:  # signal handlers must never unwind transactions
            self._forwarding_error = exc


WorkflowRunner = Callable[[tuple[str, ...], Path], WorkflowResult]


@dataclass(frozen=True, slots=True)
class LifecycleOps:
    """Explicit mutation/process boundary used by lifecycle and fault tests."""

    run_workflow: WorkflowRunner | None
    publish_bytes: BytesPublisher
    release_lock: LockReleaser
    now: Callable[[], datetime]
    host_name: Callable[[], str]
    process_id: Callable[[], int]
    process_is_alive: Callable[[int], bool]
    validate_reporting_receipt: inspection.ReportingReceiptValidator
    admit_storage_context: StorageContextAdmission
    admit_runtime_context: RuntimeContextAdmission
    sync_directory: DirectorySynchronizer
    process_group_ops: ProcessGroupOps = DEFAULT_PROCESS_GROUP_OPS
    observe_mutex: MutexObserver = _ignore_mutex_event
    observe_phase: LifecyclePhaseObserver = _ignore_lifecycle_phase
    observe_application_event: ApplicationEventObserver = _ignore_application_event


@dataclass(frozen=True, slots=True)
class LifecycleRequest:
    """One exact immutable workflow invocation crossing into lifecycle."""

    run_root: Path
    execution_path: Path
    profile_path: Path
    workflow_config_path: Path
    snakefile: Path
    python_executable: Path
    workflow_profile: Path
    target: str
    operation: Operation
    attempt_record_bytes: bytes
    request_source_path: Path


@dataclass(frozen=True, slots=True)
class _OwnedRunLock:
    path: Path
    data: bytes
    inode: tuple[int, int]


@dataclass(frozen=True, slots=True)
class LifecycleOutcome:
    """Terminal immutable outcome of one workflow attempt."""

    attempt_path: Path
    receipt_path: Path
    lock_path: Path
    released_lock_path: Path
    receipt: dict[str, Any]


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
        raise LifecycleError("Workflow Python launcher must equal lexical sys.executable")
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
        raise LifecycleError(f"Could not admit workflow Python launcher: {path}") from exc
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
        raise LifecycleError("Workflow Python launcher identity changed during admission")
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

    if run_root == source_checkout or run_root in source_checkout.parents or source_checkout in run_root.parents:
        raise LifecycleError("run_root and source_checkout must be disjoint canonical directories")


def build_snakemake_argv(
    *,
    python_executable: Path,
    snakefile: Path,
    workflow_profile: Path,
    configfile: Path,
    run_root: Path,
    target: str,
    operation: Operation,
    cores: int,
    resource_limits: Sequence[tuple[str, int]],
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
        raise LifecycleError(f"Workflow profile must be an absolute canonical file: {workflow_profile}")
    if operation not in {"execute", "resume"}:
        raise LifecycleError(f"Unsupported lifecycle operation: {operation}")
    if isinstance(cores, bool) or not isinstance(cores, int) or cores < 1:
        raise LifecycleError("Workflow cores must be a positive integer")
    limits = dict(resource_limits)
    if len(limits) != len(resource_limits) or set(limits) != _RESOURCE_LIMIT_NAMES:
        raise LifecycleError(
            "Snakemake resource limits must contain exactly: " + ", ".join(sorted(_RESOURCE_LIMIT_NAMES))
        )
    for name, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise LifecycleError(f"Snakemake resource limit {name} must be a positive integer")
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
        "--cores",
        str(cores),
        "--resources",
        *(f"{name}={limits[name]}" for name in sorted(limits)),
        "--nocolor",
    ]
    argv.extend(BACKEND_OPERATION_FLAGS[operation])
    argv.extend(("--", target))
    observed = _FORBIDDEN_SNAKEMAKE_FLAGS.intersection(argv)
    if observed:
        raise LifecycleError("Forbidden Snakemake recovery controls: " + ", ".join(sorted(observed)))
    return tuple(argv)


def _resource_plan_from_workflow_config(
    config_document: Mapping[str, Any],
    *,
    require_symbolic: bool = False,
) -> ResourcePlan:
    policy = config_document.get("resource_policy")
    if not isinstance(policy, dict):
        raise LifecycleError("Workflow config resource policy is malformed")
    try:
        return admit_resource_policy_record(
            policy,
            require_symbolic=require_symbolic,
        )
    except ResourceConfigError as exc:
        raise LifecycleError(f"Workflow config resource policy is invalid: {exc}") from exc


def _publish_exclusive(path: Path, data: bytes) -> None:
    publish_exclusive(path, data, LifecycleError)


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


def _admit_mutex_descriptor(path: Path, descriptor: int) -> None:
    """Bind the persistent mutex pathname to one empty regular-file descriptor."""

    try:
        descriptor_state = os.fstat(descriptor)
        path_state = path.stat(follow_symlinks=False)
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise LifecycleError(f"Could not admit lifecycle mutex: {path}: {exc}") from exc
    if (
        resolved != path
        or not stat.S_ISREG(descriptor_state.st_mode)
        or not stat.S_ISREG(path_state.st_mode)
        or descriptor_state.st_size != 0
        or path_state.st_size != 0
        or (descriptor_state.st_dev, descriptor_state.st_ino) != (path_state.st_dev, path_state.st_ino)
    ):
        raise LifecycleError(f"Lifecycle mutex must be one canonical zero-byte regular file: {path}")


@contextmanager
def _acquire_attempt_mutex(
    root: Path,
    *,
    observe: MutexObserver = _ignore_mutex_event,
    interrupted: Callable[[], bool] = lambda: False,
) -> Iterator[Path]:
    """Serialize lifecycle admission without publishing run-state evidence."""

    if (
        _fcntl is None
        or not hasattr(_fcntl, "flock")
        or not hasattr(_fcntl, "LOCK_EX")
        or not hasattr(_fcntl, "LOCK_NB")
        or not hasattr(_fcntl, "LOCK_UN")
    ):
        raise LifecycleError("This platform lacks required advisory file locking")
    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW mutex admission")
    locks_root = root / "locks"
    if locks_root.is_symlink() or not locks_root.is_dir() or locks_root.resolve(strict=True) != locks_root:
        raise LifecycleError(f"Aggregate lock directory must be canonical and real: {locks_root}")
    path = locks_root / "acquire.mutex"
    flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise LifecycleError(f"Could not open lifecycle mutex: {path}: {exc}") from exc
    acquired = False
    try:
        observe("before_wait", path)
        while True:
            if interrupted():
                raise LifecycleError("Lifecycle interrupted while waiting for the acquisition mutex")
            try:
                _fcntl.flock(descriptor, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise LifecycleError(f"Could not acquire required lifecycle mutex: {path}: {exc}") from exc
                time.sleep(0.02)
                continue
            break
        acquired = True
        _admit_mutex_descriptor(path, descriptor)
        observe("after_acquire", path)
        try:
            os.fsync(descriptor)
            _sync_real_directory(locks_root, "aggregate lock directory")
        except OSError as exc:
            raise LifecycleError(f"Could not synchronize lifecycle mutex: {path}: {exc}") from exc
        _admit_mutex_descriptor(path, descriptor)
        yield path
    finally:
        observer_error: BaseException | None = None
        if acquired:
            try:
                observe("before_release", path)
            except BaseException as exc:
                observer_error = exc
            finally:
                try:
                    _fcntl.flock(descriptor, _fcntl.LOCK_UN)
                except OSError:
                    # Closing the only descriptor still releases the advisory lock.
                    pass
        try:
            os.close(descriptor)
        except OSError as exc:
            if observer_error is None:
                observer_error = exc
        if acquired:
            try:
                observe("after_release", path)
            except BaseException as exc:
                if observer_error is None:
                    observer_error = exc
        if observer_error is not None:
            raise observer_error


def _release_owned_lock(
    path: Path,
    evidence_path: Path,
    expected_bytes: bytes,
    expected_inode: tuple[int, int],
    *,
    publish_evidence: LockEvidenceLinker | None = None,
) -> None:
    """Publish owned lock evidence without replacing any destination inode."""

    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW lock release")
    descriptor = -1
    try:
        for directory, label in (
            (path.parent, "aggregate lock directory"),
            (evidence_path.parent, "released-lock evidence directory"),
        ):
            if directory.is_symlink() or not directory.is_dir() or directory.resolve(strict=True) != directory:
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
        if publish_evidence is None:

            def evidence_publisher(source: Path, destination: Path) -> None:
                os.link(source, destination, follow_symlinks=False)
        else:
            evidence_publisher = publish_evidence
        try:
            evidence_publisher(path, evidence_path)
        except FileExistsError as exc:
            raise LifecycleError(f"Refusing to replace released-lock evidence: {evidence_path}") from exc
        evidence_state = evidence_path.stat(follow_symlinks=False)
        if (evidence_state.st_dev, evidence_state.st_ino) != expected_inode:
            raise LifecycleError(f"Released run-lock evidence did not retain the owned inode: {evidence_path}")
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
        if retained_identity != evidence_identity or b"".join(retained_chunks) != expected_bytes:
            raise LifecycleError(f"Released run-lock evidence changed at publication: {evidence_path}")
        os.fsync(descriptor)
        _sync_real_directory(evidence_path.parent, "released-lock evidence directory")
        public_state = path.stat(follow_symlinks=False)
        if (public_state.st_dev, public_state.st_ino) != expected_inode:
            raise LifecycleError(
                f"Run lock pathname changed after evidence publication; owned evidence retained at {evidence_path}"
            )
        path.unlink()
        if path.exists() or path.is_symlink():
            raise LifecycleError(f"Owned run lock remained after evidence publication: {path}")
        evidence_after = evidence_path.stat(follow_symlinks=False)
        if (evidence_after.st_dev, evidence_after.st_ino) != expected_inode:
            raise LifecycleError(f"Released run-lock evidence changed after unlink: {evidence_path}")
        _sync_real_directory(path.parent, "aggregate lock directory")
        if evidence_path.parent != path.parent:
            _sync_real_directory(evidence_path.parent, "released-lock evidence directory")
    except OSError as exc:
        raise LifecycleError(f"Could not release owned run lock {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _wait_for_group_absence(
    process_group_id: int,
    process: Any,
    deadline: float,
    ops: ProcessGroupOps,
) -> bool:
    while True:
        leader_returncode = ops.poll(process)
        group_present = ops.group_exists(process_group_id)
        if leader_returncode is not None and not group_present:
            return True
        if ops.monotonic() >= deadline:
            return False
        ops.sleep(ops.poll_interval_seconds)


def _quiesce_process_group(
    process_group_id: int,
    process: Any,
    ops: ProcessGroupOps,
) -> None:
    """Prove a group empty, escalating bounded TERM then KILL when necessary."""

    try:
        leader_returncode = ops.poll(process)
        group_present = ops.group_exists(process_group_id)
        if leader_returncode is not None and not group_present:
            return
        ops.signal_group(process_group_id, signal.SIGTERM)
        if _wait_for_group_absence(
            process_group_id,
            process,
            ops.monotonic() + ops.terminate_grace_seconds,
            ops,
        ):
            return
        ops.signal_group(process_group_id, signal.SIGKILL)
        if _wait_for_group_absence(
            process_group_id,
            process,
            ops.monotonic() + ops.kill_grace_seconds,
            ops,
        ):
            return
    except ProcessGroupAmbiguity:
        raise
    except BaseException as exc:
        raise ProcessGroupAmbiguity("Delegated workflow process-group quiescence proof failed") from exc
    raise ProcessGroupAmbiguity("Delegated workflow process group could not be proved quiescent")


def _run_process_group(
    argv: tuple[str, ...],
    cwd: Path,
    signals: TransactionSignalController,
    *,
    ops: ProcessGroupOps = DEFAULT_PROCESS_GROUP_OPS,
) -> WorkflowResult:
    """Spawn one sanitized process group and return only after quiescence proof."""

    try:
        process = ops.spawn(argv, cwd, sanitized_subprocess_environment())
    except OSError as exc:
        return WorkflowResult(127, None, f"Could not execute {argv[0]}: {exc}")
    process_group_id = int(process.pid)
    return_code: int | None = None
    kill_sent = False
    interrupt_deadline: float | None = None
    kill_deadline: float | None = None
    registered = False
    quiescence_attempted = False
    try:
        signals.register_process_group(process_group_id)
        registered = True
        signals.raise_forwarding_error()
        while return_code is None:
            return_code = ops.poll(process)
            if return_code is not None:
                break
            if signals.first_signal is not None:
                signals.raise_forwarding_error()
                now = ops.monotonic()
                if interrupt_deadline is None:
                    interrupt_deadline = now + ops.terminate_grace_seconds
                elif not kill_sent and now >= interrupt_deadline:
                    ops.signal_group(process_group_id, signal.SIGKILL)
                    kill_sent = True
                    kill_deadline = now + ops.kill_grace_seconds
                elif kill_sent and kill_deadline is not None and now >= kill_deadline:
                    raise ProcessGroupAmbiguity("Delegated workflow leader survived bounded signal escalation")
            ops.sleep(ops.poll_interval_seconds)
        quiescence_attempted = True
        _quiesce_process_group(process_group_id, process, ops)
        signals.raise_forwarding_error()
        signals.clear_process_group(process_group_id)
        registered = False
    except BaseException:
        if quiescence_attempted:
            raise
        try:
            _quiesce_process_group(process_group_id, process, ops)
        except BaseException as cleanup_error:
            raise ProcessGroupAmbiguity(
                "Delegated workflow process group could not be proved quiescent after an execution-boundary failure"
            ) from cleanup_error
        if registered:
            signals.clear_process_group(process_group_id)
        raise
    if signals.first_signal is not None:
        return WorkflowResult(
            None,
            signals.first_signal,
            "Lifecycle signal forwarded to delegated workflow process group",
        )
    if return_code < 0:
        return WorkflowResult(None, -return_code, "Workflow process was signaled")
    return WorkflowResult(return_code, None, None)


def _admit_required_tool_identity(identity: Mapping[str, Any]) -> None:
    """Re-admit one authored path against its canonical content digest."""

    name = str(identity["name"])
    path = Path(str(identity["path"]))
    resolved_path = Path(str(identity["resolved_path"]))
    if not path.is_absolute() or not resolved_path.is_absolute():
        raise LifecycleError(f"Required tool paths must be absolute: {name}")
    try:
        observed_resolved = path.resolve(strict=True)
        resolved_state = resolved_path.lstat()
    except OSError as exc:
        raise LifecycleError(f"Required tool path is unavailable: {name}: {path}") from exc
    if observed_resolved != resolved_path or resolved_path.resolve(strict=True) != resolved_path:
        raise LifecycleError(f"Required tool canonical path differs from its binding: {name}")
    digest = identity["sha256"]
    identity_kind = identity.get("identity_kind")
    if digest is None:
        if (
            name not in {"renv_project", "renv_library"}
            or stat.S_ISLNK(resolved_state.st_mode)
            or not stat.S_ISDIR(resolved_state.st_mode)
            or not os.access(resolved_path, os.R_OK | os.X_OK)
        ):
            raise LifecycleError(f"Required runtime directory is not admissible: {name}: {resolved_path}")
        return
    if identity_kind == "package_tree" or (
        identity_kind is None and name.startswith("r_")
    ):
        if path != resolved_path:
            raise LifecycleError(
                f"Required package-tree root is not its exact canonical path: {name}"
            )
        try:
            package_identity = installed_package_tree_identity(resolved_path)
        except InstalledPackageIdentityError as exc:
            raise LifecycleError(
                f"Required package tree is not admissible: {name}: {resolved_path}"
            ) from exc
        if package_identity.sha256 != digest:
            raise LifecycleError(f"Required package tree digest differs: {name}")
        return
    if stat.S_ISLNK(resolved_state.st_mode) or not stat.S_ISREG(resolved_state.st_mode):
        raise LifecycleError(f"Required tool canonical target is not a real file: {name}: {resolved_path}")
    try:
        data, after = _read_bound_file(
            resolved_path,
            f"required tool canonical target {name}",
        )
    except LifecycleError as exc:
        raise LifecycleError(f"Could not hash required tool canonical target: {name}: {resolved_path}") from exc
    if (
        resolved_state.st_dev,
        resolved_state.st_ino,
        resolved_state.st_size,
        resolved_state.st_mtime_ns,
        resolved_state.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise LifecycleError(f"Required tool changed while hashing: {name}")
    if hashlib.sha256(data).hexdigest() != digest:
        raise LifecycleError(f"Required tool byte digest differs: {name}")


def _admit_runtime_executable_permissions(inspection: "RuntimeInspection") -> None:
    """Recheck cached passing probes still name executable files."""

    for observation in inspection.observations:
        check = observation.check
        if (
            observation.status == "pass"
            and check.check_type in {"tool_version", "tool_version_exit_1"}
            and not os.access(check.target, os.X_OK)
        ):
            raise LifecycleError(
                f"Required runtime executable is no longer executable: {check.check_id}"
            )


def _readmit_storage_runtime_binding(
    attempt: Mapping[str, Any],
    execution: Mapping[str, Any],
    *,
    inspect_storage: Callable[[Path, Path], "QualifiedStorage"],
    inspect_direct_storage: Callable[[Path, Path], "QualifiedStorage"],
) -> "RuntimeBinding | None":
    """Re-admit the qualified roots named by canonical workflow identity."""

    from emrys.evidence.storage_inventory import qualification  # noqa: PLC0415
    from emrys.orchestration.run_coordinator import doctor  # noqa: PLC0415

    workspace = Path(str(attempt["workspace"]))
    if execution.get("schema_version") == RUN_BINDING_SCHEMA_VERSION:
        reference_fasta = Path(str(attempt["authored_paths"]["reference_fasta"]))
        if not reference_fasta.is_absolute():
            request_path = Path(str(attempt["authored_paths"]["request"]))
            reference_fasta = request_path.parent / reference_fasta
    else:
        reference_fasta = Path(str(execution["reference"]["fasta"]["path"]))
    placement = attempt.get("placement")
    if placement is None:
        inspector = inspect_storage
    elif not isinstance(placement, Mapping):
        raise LifecycleError("Workflow Attempt placement is malformed")
    elif placement.get("kind") == "slurm":
        inspector = inspect_storage
    elif placement.get("kind") == "direct":
        bound_storage = tuple(
            item
            for item in attempt.get("required_tools", ())
            if isinstance(item, Mapping) and item.get("name") == "storage_qualification"
        )
        if len(bound_storage) != 1:
            raise LifecycleError("Direct workflow Attempt must bind one storage qualification")
        bound_path = Path(str(bound_storage[0].get("path", "")))
        if bound_path.name.endswith(".direct-qualified.json"):
            inspector = inspect_direct_storage
        else:
            inspector = inspect_storage
    else:
        raise LifecycleError("Workflow Attempt placement kind is unsupported")
    try:
        qualified = inspector(workspace, reference_fasta)
        return doctor.storage_runtime_binding(qualified)
    except (qualification.StorageQualificationError, OSError) as exc:
        raise LifecycleError(f"Could not re-admit storage qualification: {exc}") from exc


def _admit_runtime_context(
    attempt: Mapping[str, Any],
    request: LifecycleRequest,
    storage_binding: "RuntimeBinding | None",
    initial_inspection: "RuntimeInspection | None",
) -> None:
    """Observe clean source/package and exact required executor identity."""

    from emrys.libraries import source_authority  # noqa: PLC0415

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
    for identity in tools.values():
        _admit_required_tool_identity(identity)
    _admit_required_tool_identity(attempt["normalizer"])
    python = tools.get("python")
    snakemake = tools.get("snakemake")
    if python is None or snakemake is None:
        raise LifecycleError("Workflow attempt must declare required Python and Snakemake identities")
    if Path(str(attempt["normalizer"]["path"])) != request.python_executable:
        raise LifecycleError("Normalizer does not bind the workflow Python runtime")
    if (
        attempt["normalizer"]["resolved_path"] != python["resolved_path"]
        or attempt["normalizer"]["sha256"] != python["sha256"]
    ):
        raise LifecycleError("Normalizer does not bind the workflow Python bytes")
    if Path(str(snakemake["path"])) != request.python_executable:
        raise LifecycleError("Snakemake module identity must bind the Python runtime")
    from emrys.evidence.runtime_availability.inspector import (  # noqa: PLC0415
        RuntimeInspectionError,
        inspect_runtime_profile_bytes,
    )
    from emrys.orchestration.run_coordinator import doctor  # noqa: PLC0415

    runtime_profile = tools.get("runtime_profile")
    if runtime_profile is None:
        raise LifecycleError("Local science attempt must bind its exact runtime profile")
    profile_path = Path(str(runtime_profile["path"]))
    profile_bytes, _profile_identity = _read_bound_file(
        profile_path,
        "runtime profile",
    )
    profile_sha256 = hashlib.sha256(profile_bytes).hexdigest()
    renv_library = tools.get("renv_library")
    if renv_library is None:
        raise LifecycleError("Local science attempt must bind its renv library")
    environment = guarded_r_environment(
        observed.root,
        Path(str(renv_library["resolved_path"])),
        base_environment=os.environ,
    )
    try:
        runtime_inspection = initial_inspection or inspect_runtime_profile_bytes(
            profile_bytes,
            profile_path,
            "local",
            environment=environment,
        )
        if (
            runtime_inspection.profile_bytes != profile_bytes
            or runtime_inspection.profile_sha256 != profile_sha256
            or runtime_inspection.runtime_context != "local"
        ):
            raise RuntimeInspectionError(
                "Planning runtime inspection differs from the immutable Attempt profile"
            )
        doctor.validate_runtime_profile_contract(
            tuple(item.check for item in runtime_inspection.observations),
            observed.root,
            allow_derived_dependencies=True,
        )
    except (RuntimeInspectionError, doctor.DoctorInputError) as exc:
        raise LifecycleError(f"Could not re-admit local runtime profile: {exc}") from exc
    _admit_runtime_executable_permissions(runtime_inspection)
    if not runtime_inspection.required_ready:
        failures = ", ".join(
            item.check.check_id
            for item in runtime_inspection.observations
            if item.check.required and item.status != "pass"
        )
        raise LifecycleError(f"Required local runtime probes failed: {failures}")
    if (
        tools.get("storage_qualification") is None
        or storage_binding is None
        or storage_binding.check_id != "storage_qualification"
    ):
        raise LifecycleError("Local science attempt must bind its storage qualification")
    try:
        package_tree_ids = frozenset(
            name
            for name, identity in tools.items()
            if identity.get("identity_kind") == "package_tree"
        )
        explicit_file_ids = frozenset(
            name
            for name, identity in tools.items()
            if identity.get("identity_kind") == "file"
        )
        expected_tools = doctor.required_tool_identities(
            runtime_inspection,
            bindings=(
                *doctor.runtime_file_bindings(
                    runtime_inspection,
                    package_tree_ids=package_tree_ids,
                    explicit_file_ids=explicit_file_ids,
                ),
                storage_binding,
            ),
            python_executable=request.python_executable,
            runtime_profile_path=profile_path,
        )
    except doctor.DoctorInputError as exc:
        raise LifecycleError(f"Could not project re-observed runtime identities: {exc}") from exc
    if tuple(attempt["required_tools"]) != expected_tools:
        raise LifecycleError("Workflow attempt required tools differ from the re-observed runtime profile")


def default_lifecycle_ops() -> LifecycleOps:
    """Construct production effects without mutable facade globals."""

    from emrys.evidence.storage_inventory import qualification  # noqa: PLC0415
    from emrys.reporting import transaction_validation  # noqa: PLC0415

    return LifecycleOps(
        run_workflow=None,
        publish_bytes=_publish_exclusive,
        release_lock=_release_owned_lock,
        now=lambda: datetime.now(UTC),
        host_name=socket.gethostname,
        process_id=os.getpid,
        process_is_alive=process_is_alive,
        validate_reporting_receipt=transaction_validation.validate_receipt,
        admit_storage_context=partial(
            _readmit_storage_runtime_binding,
            inspect_storage=qualification.admit_final_qualification,
            inspect_direct_storage=qualification.admit_direct_qualification,
        ),
        admit_runtime_context=_admit_runtime_context,
        sync_directory=_sync_real_directory,
    )


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise LifecycleError("Lifecycle clock must return timezone-aware values")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_bound_file(path: Path, label: str) -> tuple[bytes, os.stat_result]:
    try:
        return read_bytes_with_identity(path, label)
    except ValidationError as exc:
        raise LifecycleError(str(exc)) from exc


def _read_stable_with_identity(path: Path, root: Path, label: str) -> tuple[bytes, tuple[int, int]]:
    _within(path, root, label)
    try:
        if path.resolve(strict=True) != path:
            raise LifecycleError(f"{label} path is not canonical: {path}")
        data, identity = _read_bound_file(
            path,
            label,
        )
    except OSError as exc:
        raise LifecycleError(f"Could not admit {label}: {path}: {exc}") from exc
    return data, (identity.st_dev, identity.st_ino)


def _read_stable(path: Path, root: Path, label: str) -> bytes:
    return _read_stable_with_identity(path, root, label)[0]


_admit_record = partial(
    inspection.admit_canonical_record,
    read_bytes=_read_stable,
    error_type=LifecycleError,
)


def _read_external_stable(path: Path, label: str) -> bytes:
    """Read one canonical external regular file through a no-follow descriptor."""

    return _read_bound_file(path, label)[0]


def _reference(path: Path, root: Path, label: str) -> dict[str, str]:
    data = _read_stable(path, root, label)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _admit_run_before_attempt(root: Path, expected_run_id: str) -> None:
    """Require one committed historical or successor Run before any mutex."""

    try:
        successor = inspection.admit_successor_run(root)
    except inspection.InspectionError as exc:
        raise LifecycleError(f"Could not admit successor Run: {exc}") from exc
    if successor is not None:
        if successor.run_binding.run_id != expected_run_id:
            raise LifecycleError("Prepared Attempt does not bind admitted Run ID")
        return
    profile_path = _canonical_file(root / "contract" / "profile.json", "profile snapshot")
    execution_path = _canonical_file(root / "contract" / "normalized.json", "historical execution contract")
    profile, _profile_data = _admit_record(profile_path, root, "profile")
    execution, _execution_data = _admit_record(
        execution_path,
        root,
        "execution",
        profile=profile,
    )
    if execution["run_id"] != expected_run_id:
        raise LifecycleError("Prepared Attempt does not bind historical Run ID")


_admit_execution = partial(
    inspection.admit_execution_path,
    read_bytes=_read_stable,
    error_type=LifecycleError,
)


def _admit_request(
    request: LifecycleRequest,
    attempt: dict[str, Any],
    ops: LifecycleOps,
    initial_runtime_inspection: "RuntimeInspection | None" = None,
) -> tuple[
    Path,
    dict[str, Any],
    dict[str, Any],
    inspection.SuccessorRunAuthority | None,
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
    request_source_path = _canonical_file(request.request_source_path, "authored source")
    _within(config_path, root, "workflow config")
    snakefile = _canonical_file(request.snakefile, "Snakefile")
    workflow_profile = _canonical_file(request.workflow_profile, "workflow profile")
    python_executable = request.python_executable
    _admit_python_launcher(python_executable)
    profile, profile_data = _admit_record(profile_path, root, "profile")
    execution, execution_data, successor = _admit_execution(
        execution_path,
        root,
        profile,
    )
    expected_execution_path = root / "contract" / ("run.json" if successor is not None else "normalized.json")
    if execution_path != expected_execution_path:
        raise LifecycleError("Lifecycle execution path differs from Run authority")
    config_data = _read_stable(config_path, root, "workflow config")
    request_source_data = _read_external_stable(request_source_path, "authored source")
    try:
        config_document = orchestration_contracts.load_json_object_bytes(config_data, f"workflow config {config_path}")
    except orchestration_contracts.ContractValidationError as exc:
        raise LifecycleError(f"Could not admit immutable run contracts: {exc}") from exc
    canonical_config = orchestration_contracts.canonical_json_bytes(config_document)
    if config_data != canonical_config:
        raise LifecycleError("Workflow config must use canonical JSON bytes")
    config_reference = {
        "path": config_path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(config_data).hexdigest(),
    }
    resources = _resource_plan_from_workflow_config(
        config_document,
        require_symbolic=successor is not None,
    )
    if resources.workflow_cores != attempt["cores"]:
        raise LifecycleError("Workflow config resource cores differ from the attempt record")
    argv = build_snakemake_argv(
        python_executable=python_executable,
        snakefile=snakefile,
        workflow_profile=request.workflow_profile,
        configfile=config_path,
        run_root=root,
        target=request.target,
        operation=request.operation,
        cores=int(attempt["cores"]),
        resource_limits=resources.scheduler_limits(),
    )
    identifier = str(attempt["workflow_attempt_id"])
    source_root = Path(str(attempt["source_checkout"]["path"]))
    _require_disjoint_roots(root, source_root)
    expected_snakefile = source_root / SNAKEFILE_RELATIVE
    expected_workflow_profile = source_root / WORKFLOW_PROFILE_RELATIVE
    if snakefile != expected_snakefile:
        raise LifecycleError("Lifecycle requires the reviewed workflow/Snakefile")
    if workflow_profile != expected_workflow_profile:
        raise LifecycleError("Lifecycle requires the reviewed local workflow profile")
    if request.target != BACKEND_TARGET:
        raise LifecycleError("Lifecycle requires the Run-bound backend target")
    expected_config_relative = (Path("contract") / "workflow-configs" / f"{identifier}.json").as_posix()
    if config_reference["path"] != expected_config_relative:
        raise LifecycleError("Workflow config must use its attempt-specific immutable path")
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
    expected_executor = (
        "local" if successor is None else str(successor.execution_plan.record["identity"]["backend"]["backend"])
    )
    expected = {
        "run_id": execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(execution_data).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_data).hexdigest(),
        "operation": request.operation,
        "executor": expected_executor,
        "snakemake_argv": list(argv),
        "workflow_config": config_reference,
        "host": ops.host_name(),
        "process_id": ops.process_id(),
    }
    for field, value in expected.items():
        if attempt[field] != value:
            raise LifecycleError(f"Workflow attempt does not bind {field}")
    if str(python_executable) != sys.executable:
        raise LifecycleError("Workflow Python runtime must equal lexical sys.executable")
    if Path(str(attempt["authored_paths"]["request"])) != request_source_path:
        raise LifecycleError("Workflow attempt does not name its authored source")
    request_snapshot_path = root / "attempts" / identifier / "request.yaml"
    if attempt["request"] != {
        "path": str(request_snapshot_path),
        "size_bytes": len(request_source_data),
        "sha256": hashlib.sha256(request_source_data).hexdigest(),
    }:
        raise LifecycleError("Workflow attempt does not bind its authored source")
    storage_binding = ops.admit_storage_context(attempt, execution)
    ops.admit_runtime_context(attempt, request, storage_binding, initial_runtime_inspection)
    if successor is not None:
        try:
            validate_successor_run(
                analysis=successor.analysis_revision,
                plan=successor.execution_plan,
                run=successor.run_binding,
                profile=profile,
                attempt=attempt,
                resource_policy=config_document["resource_policy"],
                observed_implementation_content_sha256=implementation_identity(
                    source_root,
                    execution_module_id(
                        successor.analysis_revision,
                        successor.execution_plan,
                    ),
                ),
                observed_backend_semantics_sha256=backend_semantics_identity(source_root),
            )
            inspection.admit_bound_processing_source(root, successor)
        except (
            KeyError,
            inspection.InspectionError,
            RunImplementationError,
            orchestration_contracts.ContractValidationError,
        ) as exc:
            raise LifecycleError(f"Successor Attempt differs from immutable Run: {exc}") from exc
    workspace = Path(str(attempt["workspace"]))
    if not workspace.is_absolute():
        raise LifecycleError("Workflow attempt workspace must be absolute")
    try:
        root.relative_to(workspace)
    except ValueError as exc:
        raise LifecycleError("Workflow attempt workspace does not contain run_root") from exc
    return (
        root,
        profile,
        execution,
        successor,
        attempt,
        argv,
        config_reference,
        request_source_data,
    )


def _operation_preflight(
    operation: Operation,
    root: Path,
    attempt: Mapping[str, Any],
    ops: LifecycleOps,
) -> None:
    namespace_blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=False),
    ]
    if namespace_blockers:
        raise LifecycleError("Aggregate run namespace is not admissible: " + "; ".join(namespace_blockers))
    attempt_entries, attempt_blockers = inspection.inspect_attempt_tree(root)
    if attempt_blockers:
        raise LifecycleError("Aggregate attempt state is not admissible: " + "; ".join(attempt_blockers))
    if operation == "execute":
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
    if not observed.recovery_available:
        raise LifecycleError(
            "Resume requires an independently revalidated between-task boundary: "
            + "; ".join(
                observed.blockers
                or (
                    f"Attempt outcome is {observed.attempt_outcome}",
                    f"Results are {observed.results_status}",
                )
            )
        )
    latest = observed.latest_attempt
    receipt = observed.latest_receipt
    if latest is None or receipt is None:
        raise LifecycleError("Resume requires one terminal prior workflow attempt")
    if receipt["status"] not in {"failed", "interrupted"}:
        raise LifecycleError("Only a failed or interrupted attempt may be resumed")
    if attempt["supersedes_workflow_attempt_id"] != latest["workflow_attempt_id"]:
        raise LifecycleError("Resume must supersede the exact latest workflow attempt")
    for field in inspection.attempt_fields(observed.authority is not None):
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
        raise LifecycleError("Aggregate run namespace changed at lock boundary: " + "; ".join(namespace_blockers))

    attempt_entries, attempt_blockers = inspection.inspect_attempt_tree(root)
    if attempt_blockers:
        raise LifecycleError(
            "Aggregate attempt state changed before attempt publication: " + "; ".join(attempt_blockers)
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
    if not observed.recovery_available or observed.latest_attempt is None or observed.latest_receipt is None:
        raise LifecycleError(
            "Resume lost its revalidated between-task boundary under lock: "
            + "; ".join(
                observed.blockers
                or (
                    f"Attempt outcome is {observed.attempt_outcome}",
                    f"Results are {observed.results_status}",
                )
            )
        )
    if attempt["supersedes_workflow_attempt_id"] != observed.latest_attempt[
        "workflow_attempt_id"
    ] or observed.latest_receipt["status"] not in {"failed", "interrupted"}:
        raise LifecycleError("Resume lost its admissible terminal predecessor")
    for field in inspection.attempt_fields(observed.authority is not None):
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
    blockers: Sequence[str],
    message: str | None,
    now: datetime,
) -> dict[str, Any]:
    receipt = {
        "schema_version": "emrys.attempt-receipt.v2",
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
        "blockers": list(dict.fromkeys(blockers)),
        "message": message,
    }
    orchestration_contracts.validate_record("attempt-receipt", receipt)
    return receipt


def _observe_phase(
    ops: LifecycleOps,
    phase: str,
) -> None:
    ops.observe_phase(phase)


def _observe_application_event(ops: LifecycleOps, event_name: str) -> None:
    """Project diagnostics without allowing them to control lifecycle state."""

    try:
        ops.observe_application_event(event_name)
    except Exception:
        pass


def _refuse_pre_attempt_signal(
    signals: TransactionSignalController,
    phase: str,
) -> None:
    if signals.first_signal is not None:
        raise LifecycleError(
            f"Lifecycle interrupted by signal {signals.first_signal} {phase}; no workflow attempt was published"
        )


def _run_attempt_locked(
    request: LifecycleRequest,
    attempt: dict[str, Any],
    *,
    active_ops: LifecycleOps,
    signals: TransactionSignalController,
    owned_lock: _OwnedRunLock,
    initial_runtime_inspection: "RuntimeInspection | None" = None,
) -> LifecycleOutcome:
    """Execute one immutable local attempt while the fixed mutex is held."""
    (
        root,
        profile,
        execution,
        authority,
        attempt,
        argv,
        config_reference,
        request_source_data,
    ) = _admit_request(
        request,
        attempt,
        active_ops,
        initial_runtime_inspection,
    )
    identifier = str(attempt["workflow_attempt_id"])
    attempt_root = root / "attempts" / identifier
    locks_root = root / "locks"
    for directory in (root / "attempts", locks_root):
        if directory.is_symlink() or not directory.is_dir():
            raise LifecycleError(f"Lifecycle parent must be pre-materialized and real: {directory}")
    attempt_path = attempt_root / "attempt.json"
    receipt_path = attempt_root / "attempt-receipt.json"
    lock_path = locks_root / "run.lock"
    released_lock_path = attempt_root / "released-run-lock.json"

    lock_record = orchestration_contracts.run_lock_record(attempt)
    orchestration_contracts.validate_record("run-lock", lock_record)
    lock_bytes = orchestration_contracts.canonical_json_bytes(lock_record)
    if owned_lock.path != lock_path or owned_lock.data != lock_bytes:
        raise LifecycleError("Pre-materialization run lock does not bind the lifecycle request")
    lock_state = lock_path.stat(follow_symlinks=False)
    lock_inode = (lock_state.st_dev, lock_state.st_ino)
    if lock_inode != owned_lock.inode:
        raise LifecycleError("Pre-materialization run lock identity changed before admission")
    try:
        _observe_phase(active_ops, "after_run_lock")
        _refuse_pre_attempt_signal(signals, "after run-lock publication")
        _under_lock_attempt_preflight(request, root, attempt, active_ops)
        if _reference(request.workflow_config_path, root, "workflow config") != config_reference:
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
        request_source_after = _read_external_stable(request.request_source_path, "authored source")
        if request_source_after != request_source_data:
            raise LifecycleError("Authored source changed before attempt publication")
        _admit_python_launcher(request.python_executable)
        _observe_phase(active_ops, "before_attempt_directory")
        _refuse_pre_attempt_signal(signals, "before attempt publication")
        attempt_root.mkdir(mode=0o700)
        if attempt_root.is_symlink() or not attempt_root.is_dir():
            raise LifecycleError(f"Attempt directory must be real: {attempt_root}")
        active_ops.sync_directory(attempt_root, "new workflow-attempt directory")
        active_ops.sync_directory(attempt_root.parent, "aggregate attempts directory")
        active_ops.publish_bytes(attempt_root / "request.yaml", request_source_data)
        active_ops.publish_bytes(attempt_path, request.attempt_record_bytes)
        _observe_phase(active_ops, "after_attempt_publication")
    except Exception as exc:
        failure_evidence_path = (
            released_lock_path
            if attempt_path.exists() and not attempt_path.is_symlink()
            else locks_root / f"released-{identifier}-run-lock.json"
        )
        active_ops.release_lock(lock_path, failure_evidence_path, lock_bytes, lock_inode)
        raise LifecycleError(f"Could not establish immutable workflow attempt: {exc}") from exc

    result: WorkflowResult | None = None
    attempts, receipts, chain_blockers = inspection.inspect_attempt_chain(root)
    evidence = inspection.inspect_evidence(
        root,
        execution,
        profile,
        attempts,
        receipts,
        active_ops.validate_reporting_receipt,
        authority=authority,
    )
    verified = list(evidence.verified_tasks)
    task_starts = list(evidence.task_start_records)
    preentry_tasks = list(evidence.preentry_task_attempt_records)
    missing = list(evidence.missing_tasks)
    blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=True),
        *chain_blockers,
        *evidence.integrity_blockers,
        *evidence.results_blockers,
    ]
    if blockers:
        status = "blocked"
        message = "Workflow preflight found ambiguous reusable state"
    else:
        _admit_python_launcher(request.python_executable)
        try:
            _observe_phase(active_ops, "before_workflow")
            for identity in attempt["required_tools"]:
                _admit_required_tool_identity(identity)
            if signals.first_signal is not None:
                candidate = WorkflowResult(
                    None,
                    signals.first_signal,
                    "Lifecycle interrupted before delegated workflow start",
                )
            else:
                _observe_application_event(active_ops, "analysis_started")
                if active_ops.run_workflow is None:
                    candidate = _run_process_group(
                        argv,
                        root,
                        signals,
                        ops=active_ops.process_group_ops,
                    )
                else:
                    candidate = active_ops.run_workflow(argv, root)
            _observe_phase(active_ops, "after_workflow")
            if signals.first_signal is not None:
                candidate = WorkflowResult(
                    None,
                    signals.first_signal,
                    "Lifecycle signal recorded during workflow transaction",
                )
        except ProcessGroupAmbiguity:
            raise
        except Exception as exc:
            raise LifecycleError(
                "Workflow runner failed without a terminal child observation; the owned run lock is retained"
            ) from exc
        runtime_blockers: list[str] = []
        if not isinstance(candidate, WorkflowResult):
            runtime_blockers.append("Workflow runner returned no typed terminal observation")
        elif (
            (candidate.exit_code is None) == (candidate.termination_signal is None)
            or (
                candidate.exit_code is not None
                and (type(candidate.exit_code) is not int or not 0 <= candidate.exit_code <= 255)
            )
            or (
                candidate.termination_signal is not None
                and (type(candidate.termination_signal) is not int or candidate.termination_signal < 1)
            )
        ):
            runtime_blockers.append("Workflow runner returned an invalid terminal observation")
        else:
            result = candidate
        try:
            storage_binding = active_ops.admit_storage_context(attempt, execution)
            active_ops.admit_runtime_context(attempt, request, storage_binding, None)
        except Exception as exc:
            runtime_blockers.append(f"Runtime identity changed during workflow execution: {exc}")
        try:
            config_after = _reference(request.workflow_config_path, root, "workflow config")
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
                "sha256": hashlib.sha256(request.attempt_record_bytes).hexdigest(),
            }
            if attempt_reference != expected_attempt_reference:
                raise LifecycleError("Workflow attempt changed during execution")
        except Exception as exc:
            runtime_blockers.append(str(exc))
        try:
            request_snapshot = _read_stable(attempt_root / "request.yaml", root, "attempt request snapshot")
            if request_snapshot != request_source_data:
                raise LifecycleError("Attempt request snapshot changed during execution")
        except Exception as exc:
            runtime_blockers.append(str(exc))
        if authority is not None:
            try:
                inspection.admit_bound_processing_source(root, authority)
            except (OSError, inspection.InspectionError) as exc:
                runtime_blockers.append(
                    f"Processing source changed during workflow execution: {exc}"
                )
        attempts, receipts, chain_blockers = inspection.inspect_attempt_chain(root)
        evidence = inspection.inspect_evidence(
            root,
            execution,
            profile,
            attempts,
            receipts,
            active_ops.validate_reporting_receipt,
            authority=authority,
        )
        verified = list(evidence.verified_tasks)
        task_starts = list(evidence.task_start_records)
        preentry_tasks = list(evidence.preentry_task_attempt_records)
        missing = list(evidence.missing_tasks)
        blockers = [
            *runtime_blockers,
            *inspection.state_tree_blockers(root),
            *inspection.lock_tree_blockers(root, expected_run_lock=True),
            *chain_blockers,
            *evidence.integrity_blockers,
            *evidence.results_blockers,
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
        elif blockers or missing:
            status = "failed"
            message = "Snakemake exited zero without complete EMRYS state"
            if missing:
                message += ": " + ", ".join(missing)
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

    _observe_phase(active_ops, "before_lock_release")
    if signals.first_signal is not None:
        result = WorkflowResult(
            None,
            signals.first_signal,
            "Lifecycle signal recorded during workflow transaction",
        )
        if not blockers:
            status = "interrupted"
            message = result.message
    active_ops.release_lock(lock_path, released_lock_path, lock_bytes, lock_inode)
    released_bytes, released_inode = _read_stable_with_identity(
        released_lock_path,
        root,
        "released run-lock evidence",
    )
    if released_bytes != lock_bytes or released_inode != lock_inode:
        raise LifecycleError("Released run-lock evidence does not retain the owned descriptor identity")
    released_namespace_blockers = [
        *inspection.state_tree_blockers(root),
        *inspection.lock_tree_blockers(root, expected_run_lock=False),
    ]
    if released_namespace_blockers:
        blockers.extend(released_namespace_blockers)
        status = "blocked"
        message = "Workflow lock release left ambiguous aggregate state"
    _observe_phase(active_ops, "before_receipt_publication")
    _observe_application_event(active_ops, "publication_ready")
    if signals.first_signal is not None:
        result = WorkflowResult(
            None,
            signals.first_signal,
            "Lifecycle signal recorded during workflow transaction",
        )
        if not blockers and not released_namespace_blockers:
            status = "interrupted"
            message = result.message
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
        blockers=blockers,
        message=message,
        now=active_ops.now(),
    )
    signals.block_for_receipt_commit()
    try:
        if signals.first_signal is not None:
            result = WorkflowResult(
                None,
                signals.first_signal,
                "Lifecycle signal recorded during workflow transaction",
            )
            if not blockers and not released_namespace_blockers:
                receipt = _terminal_receipt(
                    root=root,
                    attempt=attempt,
                    attempt_path=attempt_path,
                    released_lock_path=released_lock_path,
                    lock_bytes=lock_bytes,
                    status="interrupted",
                    result=result,
                    preentry_tasks=preentry_tasks,
                    task_starts=task_starts,
                    verified=verified,
                    blockers=blockers,
                    message=result.message,
                    now=active_ops.now(),
                )
        active_ops.publish_bytes(
            receipt_path,
            orchestration_contracts.canonical_json_bytes(receipt),
        )
    except BaseException:
        raise
    signals.mark_receipt_committed()
    _observe_phase(active_ops, "after_receipt_publication")
    return LifecycleOutcome(
        attempt_path=attempt_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
        released_lock_path=released_lock_path,
        receipt=receipt,
    )


def _admit_lifecycle_request(request: LifecycleRequest) -> dict[str, Any]:
    """Admit the exact Attempt bytes before any lifecycle mutation."""

    if type(request.attempt_record_bytes) is not bytes:
        raise LifecycleError("Prepared workflow attempt must be exact immutable bytes")
    try:
        attempt = orchestration_contracts.load_json_object_bytes(
            request.attempt_record_bytes,
            "prepared workflow attempt",
        )
        orchestration_contracts.validate_record("workflow-attempt", attempt)
    except orchestration_contracts.ContractValidationError as exc:
        raise LifecycleError(f"Invalid prepared workflow attempt: {exc}") from exc
    if orchestration_contracts.canonical_json_bytes(attempt) != request.attempt_record_bytes:
        raise LifecycleError("Prepared workflow attempt must use canonical JSON bytes")
    if request.operation not in {"execute", "resume"}:
        raise LifecycleError(f"Unsupported prepared lifecycle operation: {request.operation}")
    if attempt["operation"] != request.operation:
        raise LifecycleError("Prepared workflow attempt does not bind lifecycle operation")
    return attempt


def run_materialized_attempt(
    request: LifecycleRequest,
    materialize: AttemptMaterializer,
    *,
    ops: LifecycleOps | None = None,
    initial_runtime_inspection: "RuntimeInspection | None" = None,
) -> LifecycleOutcome:
    """Serialize admission before publishing lock or attempt-specific inputs."""

    active_ops = default_lifecycle_ops() if ops is None else ops
    with TransactionSignalController(
        DEFAULT_SIGNAL_OPS,
        active_ops.process_group_ops,
    ) as signals:
        root = _canonical_root(request.run_root)
        locks_root = root / "locks"
        attempts_root = root / "attempts"
        for directory in (locks_root, attempts_root):
            if directory.is_symlink() or not directory.is_dir():
                raise LifecycleError(f"Lifecycle parent must be pre-materialized and real: {directory}")
        prepared_attempt = _admit_lifecycle_request(request)
        run_id = str(prepared_attempt["run_id"])
        identifier = str(prepared_attempt["workflow_attempt_id"])
        _admit_run_before_attempt(root, run_id)
        _observe_phase(active_ops, "before_mutex")
        _refuse_pre_attempt_signal(signals, "before mutex acquisition")
        with _acquire_attempt_mutex(
            root,
            observe=active_ops.observe_mutex,
            interrupted=lambda: signals.first_signal is not None,
        ):
            _observe_phase(active_ops, "after_mutex")
            _refuse_pre_attempt_signal(signals, "at mutex acquisition")
            _operation_preflight(
                request.operation,
                root,
                prepared_attempt,
                active_ops,
            )
            _observe_phase(active_ops, "before_run_lock")
            _refuse_pre_attempt_signal(signals, "before run-lock publication")
            lock_path = locks_root / "run.lock"
            lock_record = orchestration_contracts.run_lock_record(prepared_attempt)
            orchestration_contracts.validate_record("run-lock", lock_record)
            lock_bytes = orchestration_contracts.canonical_json_bytes(lock_record)
            active_ops.publish_bytes(lock_path, lock_bytes)
            lock_state = lock_path.stat(follow_symlinks=False)
            owned = _OwnedRunLock(
                path=lock_path,
                data=lock_bytes,
                inode=(lock_state.st_dev, lock_state.st_ino),
            )
            try:
                _observe_phase(active_ops, "after_run_lock")
                _refuse_pre_attempt_signal(signals, "after run-lock publication")
                _observe_phase(active_ops, "before_materialization")
                _refuse_pre_attempt_signal(signals, "before materialization")
                materialize()
                _observe_phase(active_ops, "after_materialization")
                _refuse_pre_attempt_signal(signals, "during materialization")
                return _run_attempt_locked(
                    request,
                    prepared_attempt,
                    active_ops=active_ops,
                    signals=signals,
                    owned_lock=owned,
                    initial_runtime_inspection=initial_runtime_inspection,
                )
            except Exception as exc:
                attempt_path = attempts_root / identifier / "attempt.json"
                if not attempt_path.exists() and not attempt_path.is_symlink():
                    if lock_path.exists() and not lock_path.is_symlink():
                        evidence = locks_root / f"released-{identifier}-run-lock.json"
                        active_ops.release_lock(
                            lock_path,
                            evidence,
                            lock_bytes,
                            owned.inode,
                        )
                if isinstance(exc, LifecycleError):
                    raise
                raise LifecycleError(f"Could not materialize immutable workflow attempt: {exc}") from exc


__all__ = (
    "LifecycleError",
    "LifecycleOps",
    "LifecycleOutcome",
    "LifecycleRequest",
    "RuntimeContextAdmission",
    "StorageContextAdmission",
    "WorkflowResult",
    "build_snakemake_argv",
    "default_lifecycle_ops",
    "run_materialized_attempt",
)
