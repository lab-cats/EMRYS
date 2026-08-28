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
import platform
import re
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, Any, Iterator, Literal

if TYPE_CHECKING:
    from emrys.evidence.storage_inventory.qualification import QualifiedStorage
    from emrys.orchestration.local_pilot.doctor import RuntimeBinding

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
from emrys.libraries.process_environment import (
    ProcessEnvironmentError,
    gatk_subprocess_environment,
    sanitized_subprocess_environment,
)
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.local_pilot import inspection, task
from emrys.orchestration.local_pilot.resource_policy import (
    REPEATABLE_STAGE_IDS,
    ResourceConfigError,
    ResourcePlan,
    admit_resource_policy_record,
    stage_slot_name,
)
from emrys.orchestration.local_pilot.run_implementation import (
    BACKEND_OPERATION_FLAGS,
    BACKEND_TARGET,
    SNAKEFILE_RELATIVE,
    WORKFLOW_PROFILE_RELATIVE,
    RunImplementationError,
    backend_semantics_identity,
    implementation_identity,
)

Operation = Literal["execute", "resume"]
_SAFE_RULE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_RESOURCE_LIMIT_NAMES = frozenset(
    {"mem_mb", *(stage_slot_name(step_id) for step_id in REPEATABLE_STAGE_IDS)}
)
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
    [Mapping[str, Any], "LifecycleRequest", "RuntimeBinding | None"],
    None,
]
DirectorySynchronizer = Callable[[Path, str], None]
PythonLauncherIdentity = tuple[str, str, int, int]
AttemptMaterializer = Callable[[], "LifecycleRequest"]
MutexObserver = Callable[[str, Path], None]
LifecyclePhaseObserver = Callable[[str], None]
SignalHandler = Callable[[int, FrameType | None], None]
SignalHandlerInstaller = Callable[
    [SignalHandler], tuple[Mapping[int, Any], set[signal.Signals]]
]
SignalHandlerRestorer = Callable[[Mapping[int, Any], set[signal.Signals]], None]
ProcessSpawner = Callable[[tuple[str, ...], Path, Mapping[str, str]], Any]
ProcessPoller = Callable[[Any], int | None]
ProcessGroupProbe = Callable[[int], bool]
ProcessGroupSignaler = Callable[[int, int], None]


def _ignore_mutex_event(_event: str, _path: Path) -> None:
    return None


def _ignore_lifecycle_phase(_phase: str) -> None:
    return None


def _install_transaction_signal_handlers(
    handler: SignalHandler,
) -> tuple[Mapping[int, Any], set[signal.Signals]]:
    if not hasattr(signal, "pthread_sigmask") or not hasattr(signal, "SIG_BLOCK"):
        raise LifecycleError(
            "This platform lacks required POSIX lifecycle signal masking"
        )
    watched = {signal.SIGINT, signal.SIGTERM}
    try:
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, watched)
    except (OSError, ValueError) as exc:
        raise LifecycleError(
            f"Could not block lifecycle signals during handler installation: {exc}"
        ) from exc
    if watched.intersection(previous_mask):
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        raise LifecycleError(
            "Lifecycle refuses an ambient mask that already blocks SIGINT or SIGTERM"
        )
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
            + (
                "; rollback failures: " + "; ".join(rollback_failures)
                if rollback_failures
                else ""
            )
        ) from exc
    try:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    except (OSError, ValueError) as exc:
        for signum, prior in previous.items():
            signal.signal(signum, prior)
        raise LifecycleError(
            f"Could not restore signal mask after handler installation: {exc}"
        ) from exc
    return previous, set(previous_mask)


def _restore_transaction_signal_handlers(
    previous: Mapping[int, Any],
    previous_mask: set[signal.Signals],
) -> None:
    watched = {signal.SIGINT, signal.SIGTERM}
    try:
        signal.pthread_sigmask(signal.SIG_BLOCK, watched)
    except (OSError, ValueError) as exc:
        raise LifecycleError(
            f"Could not block lifecycle signals during handler restoration: {exc}"
        ) from exc
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
        raise LifecycleError(
            "Could not restore lifecycle signal handlers: " + "; ".join(failures)
        )


def _spawn_process_group(
    argv: tuple[str, ...], cwd: Path, environment: Mapping[str, str]
) -> subprocess.Popen[bytes]:
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
        self._previous, self._previous_mask = self._signal_ops.install_handlers(
            self.record
        )
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: Any,
    ) -> None:
        previous = self._previous
        previous_mask = self._previous_mask
        if (
            self._receipt_commit_blocked
            and not self._receipt_committed
            and previous_mask is not None
        ):
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
            raise LifecycleError(
                "Lifecycle signal-handler state lost its prior signal mask"
            )

    def block_for_receipt_commit(self) -> None:
        """Linearize receipt publication before restoring ambient handlers."""

        if not hasattr(signal, "pthread_sigmask"):
            raise LifecycleError(
                "This platform lacks required POSIX receipt signal masking"
            )
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
        if (
            self.first_signal is None
            or self._process_group_id is None
            or self._forwarded
        ):
            return
        try:
            self._forwarded = True
            self._process_group_ops.signal_group(
                self._process_group_id, self.first_signal
            )
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
class AttemptPreparation:
    """Immutable attempt identity admitted before any attempt publication."""

    run_root: Path
    run_id: str
    workflow_attempt_id: str
    owner_token: str
    host: str
    process_id: int
    created_at: str
    operation: Operation
    attempt_record_bytes: bytes


@dataclass(frozen=True, slots=True)
class _OwnedRunLock:
    path: Path
    record: dict[str, Any]
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
    workflow_result: WorkflowResult | None
    verified_report_locations: tuple[tuple[str, Path], ...] = ()


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
        raise LifecycleError(
            f"Workflow profile must be an absolute canonical file: {workflow_profile}"
        )
    if operation not in {"execute", "resume"}:
        raise LifecycleError(f"Unsupported lifecycle operation: {operation}")
    if isinstance(cores, bool) or not isinstance(cores, int) or cores < 1:
        raise LifecycleError("Workflow cores must be a positive integer")
    limits = dict(resource_limits)
    if len(limits) != len(resource_limits) or set(limits) != _RESOURCE_LIMIT_NAMES:
        raise LifecycleError(
            "Snakemake resource limits must contain exactly: "
            + ", ".join(sorted(_RESOURCE_LIMIT_NAMES))
        )
    for name, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise LifecycleError(
                f"Snakemake resource limit {name} must be a positive integer"
            )
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
        raise LifecycleError(
            "Forbidden Snakemake recovery controls: " + ", ".join(sorted(observed))
        )
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
        raise LifecycleError(
            f"Workflow config resource policy is invalid: {exc}"
        ) from exc


def _publish_exclusive(path: Path, data: bytes) -> None:
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        raise LifecycleError(f"Publication parent must be a real directory: {parent}")
    if not hasattr(os, "O_NOFOLLOW"):
        raise LifecycleError("This platform lacks required O_NOFOLLOW publication")
    staging = parent / f".{path.name}.{uuid.uuid4().hex}.emrys-stage"
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
        or (descriptor_state.st_dev, descriptor_state.st_ino)
        != (path_state.st_dev, path_state.st_ino)
    ):
        raise LifecycleError(
            f"Lifecycle mutex must be one canonical zero-byte regular file: {path}"
        )


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
    if (
        locks_root.is_symlink()
        or not locks_root.is_dir()
        or locks_root.resolve(strict=True) != locks_root
    ):
        raise LifecycleError(
            f"Aggregate lock directory must be canonical and real: {locks_root}"
        )
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
                raise LifecycleError(
                    "Lifecycle interrupted while waiting for the acquisition mutex"
                )
            try:
                _fcntl.flock(descriptor, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise LifecycleError(
                        f"Could not acquire required lifecycle mutex: {path}: {exc}"
                    ) from exc
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
            raise LifecycleError(
                f"Could not synchronize lifecycle mutex: {path}: {exc}"
            ) from exc
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
        if publish_evidence is None:

            def evidence_publisher(source: Path, destination: Path) -> None:
                os.link(source, destination, follow_symlinks=False)
        else:
            evidence_publisher = publish_evidence
        try:
            evidence_publisher(path, evidence_path)
        except FileExistsError as exc:
            raise LifecycleError(
                f"Refusing to replace released-lock evidence: {evidence_path}"
            ) from exc
        evidence_state = evidence_path.stat(follow_symlinks=False)
        if (evidence_state.st_dev, evidence_state.st_ino) != expected_inode:
            raise LifecycleError(
                "Released run-lock evidence did not retain the owned inode: "
                f"{evidence_path}"
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
        os.fsync(descriptor)
        _sync_real_directory(evidence_path.parent, "released-lock evidence directory")
        public_state = path.stat(follow_symlinks=False)
        if (public_state.st_dev, public_state.st_ino) != expected_inode:
            raise LifecycleError(
                "Run lock pathname changed after evidence publication; "
                f"owned evidence retained at {evidence_path}"
            )
        path.unlink()
        if path.exists() or path.is_symlink():
            raise LifecycleError(
                f"Owned run lock remained after evidence publication: {path}"
            )
        evidence_after = evidence_path.stat(follow_symlinks=False)
        if (evidence_after.st_dev, evidence_after.st_ino) != expected_inode:
            raise LifecycleError(
                f"Released run-lock evidence changed after unlink: {evidence_path}"
            )
        _sync_real_directory(path.parent, "aggregate lock directory")
        if evidence_path.parent != path.parent:
            _sync_real_directory(
                evidence_path.parent, "released-lock evidence directory"
            )
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
        raise ProcessGroupAmbiguity(
            "Delegated workflow process-group quiescence proof failed"
        ) from exc
    raise ProcessGroupAmbiguity(
        "Delegated workflow process group could not be proved quiescent"
    )


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
                    raise ProcessGroupAmbiguity(
                        "Delegated workflow leader survived bounded signal escalation"
                    )
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
                "Delegated workflow process group could not be proved quiescent "
                "after an execution-boundary failure"
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
        raise LifecycleError(
            f"Required tool path is unavailable: {name}: {path}"
        ) from exc
    if (
        observed_resolved != resolved_path
        or resolved_path.resolve(strict=True) != resolved_path
    ):
        raise LifecycleError(
            f"Required tool canonical path differs from its binding: {name}"
        )
    digest = identity["sha256"]
    if digest is None:
        if (
            name not in {"renv_project", "renv_library"}
            or stat.S_ISLNK(resolved_state.st_mode)
            or not stat.S_ISDIR(resolved_state.st_mode)
            or not os.access(resolved_path, os.R_OK | os.X_OK)
        ):
            raise LifecycleError(
                f"Required runtime directory is not admissible: {name}: {resolved_path}"
            )
        return
    if name.startswith("r_"):
        if path != resolved_path:
            raise LifecycleError(
                f"Required R package root is not its exact canonical path: {name}"
            )
        try:
            package_identity = installed_package_tree_identity(resolved_path)
        except InstalledPackageIdentityError as exc:
            raise LifecycleError(
                f"Required R package tree is not admissible: {name}: {resolved_path}"
            ) from exc
        if package_identity.sha256 != digest:
            raise LifecycleError(f"Required R package tree digest differs: {name}")
        return
    if stat.S_ISLNK(resolved_state.st_mode) or not stat.S_ISREG(resolved_state.st_mode):
        raise LifecycleError(
            f"Required tool canonical target is not a real file: {name}: {resolved_path}"
        )
    try:
        data = resolved_path.read_bytes()
        after = resolved_path.stat()
    except OSError as exc:
        raise LifecycleError(
            f"Could not hash required tool canonical target: {name}: {resolved_path}"
        ) from exc
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


def _readmit_storage_runtime_binding(
    attempt: Mapping[str, Any],
    execution: Mapping[str, Any],
    *,
    inspect_storage: Callable[[Path, Path], "QualifiedStorage"],
) -> "RuntimeBinding | None":
    """Re-admit the qualified roots named by canonical workflow identity."""

    from emrys.evidence.storage_inventory import qualification  # noqa: PLC0415
    from emrys.orchestration.local_pilot import doctor  # noqa: PLC0415

    if attempt["execution_mode"] == "test-double":
        return None
    workspace = Path(str(attempt["workspace"]))
    reference_fasta = Path(
        str(
            attempt["authored_paths"]["reference_fasta"]
            if execution.get("schema_version") == RUN_BINDING_SCHEMA_VERSION
            else execution["reference"]["fasta"]["path"]
        )
    )
    try:
        qualified = inspect_storage(workspace, reference_fasta)
        return doctor.storage_runtime_binding(qualified)
    except (qualification.StorageQualificationError, OSError) as exc:
        raise LifecycleError(
            f"Could not re-admit storage qualification: {exc}"
        ) from exc


def _admit_runtime_context(
    attempt: Mapping[str, Any],
    request: LifecycleRequest,
    storage_binding: "RuntimeBinding | None",
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
        raise LifecycleError(
            "Workflow attempt must declare required Python and Snakemake identities"
        )
    if Path(str(python["path"])) != request.python_executable:
        raise LifecycleError("Required Python path differs from workflow runtime")
    if Path(str(attempt["normalizer"]["path"])) != request.python_executable:
        raise LifecycleError("Normalizer does not bind the workflow Python runtime")
    if (
        attempt["normalizer"]["resolved_path"] != python["resolved_path"]
        or attempt["normalizer"]["sha256"] != python["sha256"]
    ):
        raise LifecycleError("Normalizer does not bind the workflow Python bytes")
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
    if attempt["execution_mode"] == "test-double":
        if storage_binding is not None:
            raise LifecycleError(
                "Test-double attempt must not bind storage qualification"
            )
        # Common admission re-admits identities; doubles do not invoke science tools.
        return

    from emrys.evidence.runtime_availability.inspector import (  # noqa: PLC0415
        RuntimeInspectionError,
        inspect_runtime_availability,
    )
    from emrys.orchestration.local_pilot import doctor  # noqa: PLC0415

    runtime_profile = tools.get("runtime_profile")
    if runtime_profile is None:
        raise LifecycleError(
            "Local science attempt must bind its exact runtime profile"
        )
    profile_path = Path(str(runtime_profile["path"]))
    if profile_path != Path(str(runtime_profile["resolved_path"])):
        raise LifecycleError(
            f"Runtime profile must be an absolute canonical file: {profile_path}"
        )
    profile_sha256 = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    if (
        runtime_profile["sha256"] != profile_sha256
        or runtime_profile["version"] != f"sha256:{profile_sha256}"
    ):
        raise LifecycleError("Required runtime profile digest differs from its bytes")
    renv_project = tools.get("renv_project")
    renv_library = tools.get("renv_library")
    java = tools.get("java")
    if renv_project is None or renv_library is None or java is None:
        raise LifecycleError(
            "Local science attempt must bind its renv project, library, and Java launcher"
        )
    if Path(str(renv_project["resolved_path"])) != observed.root:
        raise LifecycleError("Required renv project differs from the source checkout")
    environment = _local_runtime_environment(
        observed.root,
        Path(str(renv_library["resolved_path"])),
        Path(str(java["resolved_path"])),
        base_environment=os.environ,
    )
    try:
        runtime_inspection = inspect_runtime_availability(
            profile_path,
            "local",
            environment=environment,
        )
        doctor.validate_runtime_profile(runtime_inspection, observed.root)
    except (RuntimeInspectionError, doctor.DoctorInputError) as exc:
        raise LifecycleError(
            f"Could not re-admit local runtime profile: {exc}"
        ) from exc
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
        raise LifecycleError(
            "Local science attempt must bind its storage qualification"
        )
    try:
        expected_tools = doctor.required_tool_identities(
            runtime_inspection,
            bindings=(
                *doctor.runtime_file_bindings(runtime_inspection),
                storage_binding,
            ),
            python_executable=request.python_executable,
            snakemake_version=observed_version,
            runtime_profile_path=profile_path,
        )
    except doctor.DoctorInputError as exc:
        raise LifecycleError(
            f"Could not project re-observed runtime identities: {exc}"
        ) from exc
    if tuple(attempt["required_tools"]) != expected_tools:
        raise LifecycleError(
            "Workflow attempt required tools differ from the re-observed runtime profile"
        )


def _local_runtime_environment(
    source_root: Path,
    renv_library: Path,
    selected_java: Path,
    *,
    base_environment: Mapping[str, str],
) -> dict[str, str]:
    """Construct the one guarded R and selected-Java runtime environment."""

    from emrys.orchestration.local_pilot import doctor  # noqa: PLC0415

    environment = doctor.runtime_environment(
        source_root,
        renv_library,
        base_environment=base_environment,
    )
    try:
        return gatk_subprocess_environment(
            selected_java,
            base_environment=environment,
        )
    except ProcessEnvironmentError as exc:
        raise LifecycleError(
            f"Could not admit Java for local GATK runtime: {exc}"
        ) from exc


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
        process_is_alive=_process_is_alive,
        validate_reporting_receipt=transaction_validation.validate_receipt,
        admit_storage_context=partial(
            _readmit_storage_runtime_binding,
            inspect_storage=qualification.admit_final_qualification,
        ),
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


_admit_record = partial(
    inspection.admit_canonical_record,
    read_bytes=_read_stable,
    error_type=LifecycleError,
)


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
    authority = inspection.admit_successor_run(root) or execution
    expected_tasks = inspection.expected_tasks(authority, profile)
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
    authority = inspection.admit_successor_run(root) or execution
    expected = inspection.expected_tasks(authority, profile)
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

    return inspection.inspect_attempt_task_trees(
        root,
        execution,
        profile,
        attempts,
        authority=inspection.admit_successor_run(root),
    )


def _admit_run_before_attempt(root: Path, expected_run_id: str) -> None:
    """Require one committed historical or successor Run before any mutex."""

    try:
        successor = inspection.admit_successor_run(root)
    except inspection.InspectionError as exc:
        raise LifecycleError(f"Could not admit successor Run: {exc}") from exc
    if successor is not None:
        if successor.run_id != expected_run_id:
            raise LifecycleError("Prepared Attempt does not bind admitted Run ID")
        return
    profile_path = _canonical_file(root / "contract" / "profile.json", "profile snapshot")
    execution_path = _canonical_file(
        root / "contract" / "normalized.json", "historical execution contract"
    )
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
    profile, profile_data = _admit_record(profile_path, root, "profile")
    execution, execution_data, successor = _admit_execution(
        execution_path,
        root,
        profile,
    )
    expected_execution_path = root / "contract" / (
        "run.json" if successor is not None else "normalized.json"
    )
    if execution_path != expected_execution_path:
        raise LifecycleError("Lifecycle execution path differs from Run authority")
    config_data = _read_stable(config_path, root, "workflow config")
    request_source_data = _read_external_stable(
        request_source_path, "authored request source"
    )
    try:
        config_document = orchestration_contracts.load_json_object_bytes(
            config_data, f"workflow config {config_path}"
        )
    except orchestration_contracts.ContractValidationError as exc:
        raise LifecycleError(f"Could not admit immutable run contracts: {exc}") from exc
    canonical_config = orchestration_contracts.canonical_json_bytes(config_document)
    if config_data != canonical_config:
        raise LifecycleError("Workflow config must use canonical JSON bytes")
    config_reference = {
        "path": config_path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(config_data).hexdigest(),
    }
    attempt = dict(request.attempt_record)
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    resources = _resource_plan_from_workflow_config(
        config_document,
        require_symbolic=successor is not None,
    )
    if resources.workflow_cores != attempt["cores"]:
        raise LifecycleError(
            "Workflow config resource cores differ from the attempt record"
        )
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
    storage_binding = ops.admit_storage_context(attempt, execution)
    ops.admit_runtime_context(attempt, request, storage_binding)
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
                    source_root
                ),
                observed_backend_semantics_sha256=backend_semantics_identity(
                    source_root
                ),
            )
        except (
            KeyError,
            RunImplementationError,
            orchestration_contracts.ContractValidationError,
        ) as exc:
            raise LifecycleError(
                f"Successor Attempt differs from immutable Run: {exc}"
            ) from exc
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
        raise LifecycleError(
            "Aggregate run namespace is not admissible: "
            + "; ".join(namespace_blockers)
        )
    attempt_entries, attempt_blockers = inspection.inspect_attempt_tree(root)
    if attempt_blockers:
        raise LifecycleError(
            "Aggregate attempt state is not admissible: " + "; ".join(attempt_blockers)
        )
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
    for field in inspection.attempt_compatibility_fields(observed.authority_format):
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
            "Resume lost its revalidated between-task boundary under lock: "
            + "; ".join(observed.blockers or (observed.state,))
        )
    if attempt["supersedes_workflow_attempt_id"] != observed.latest_attempt[
        "workflow_attempt_id"
    ] or observed.latest_receipt["status"] not in {"failed", "interrupted"}:
        raise LifecycleError("Resume lost its admissible terminal predecessor")
    for field in inspection.attempt_compatibility_fields(observed.authority_format):
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
        "schema_version": "emrys.attempt-receipt.v1",
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


def _observe_phase(
    ops: LifecycleOps,
    phase: str,
) -> None:
    ops.observe_phase(phase)


def _refuse_pre_attempt_signal(
    signals: TransactionSignalController,
    phase: str,
) -> None:
    if signals.first_signal is not None:
        raise LifecycleError(
            f"Lifecycle interrupted by signal {signals.first_signal} {phase}; "
            "no workflow attempt was published"
        )


def _run_attempt_locked(
    request: LifecycleRequest,
    *,
    active_ops: LifecycleOps,
    signals: TransactionSignalController,
    _owned_lock: _OwnedRunLock | None = None,
) -> LifecycleOutcome:
    """Execute one immutable local attempt while the fixed mutex is held."""
    (
        root,
        profile,
        execution,
        attempt,
        argv,
        config_reference,
        request_source_data,
    ) = _admit_request(request, active_ops)
    if _owned_lock is None:
        _operation_preflight(request.operation, root, attempt, active_ops)
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
        "schema_version": "emrys.run-lock.v1",
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
    if _owned_lock is None:
        _observe_phase(active_ops, "before_run_lock")
        _refuse_pre_attempt_signal(signals, "before run-lock publication")
        active_ops.publish_bytes(lock_path, lock_bytes)
        lock_state = lock_path.stat(follow_symlinks=False)
        lock_inode = (lock_state.st_dev, lock_state.st_ino)
    else:
        if (
            _owned_lock.path != lock_path
            or _owned_lock.record != lock_record
            or _owned_lock.data != lock_bytes
        ):
            raise LifecycleError(
                "Pre-materialization run lock does not bind the lifecycle request"
            )
        lock_state = lock_path.stat(follow_symlinks=False)
        lock_inode = (lock_state.st_dev, lock_state.st_ino)
        if lock_inode != _owned_lock.inode:
            raise LifecycleError(
                "Pre-materialization run lock identity changed before admission"
            )
    attempt_root_created = False
    try:
        _observe_phase(active_ops, "after_run_lock")
        _refuse_pre_attempt_signal(signals, "after run-lock publication")
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
        _observe_phase(active_ops, "before_attempt_directory")
        _refuse_pre_attempt_signal(signals, "before attempt publication")
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
        _observe_phase(active_ops, "after_attempt_publication")
    except Exception as exc:
        failure_evidence_path = (
            released_lock_path
            if attempt_path.exists() and not attempt_path.is_symlink()
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
    (
        reporting,
        reporting_blockers,
        verified_report_locations,
    ) = inspection._inspect_reporting_ledger_with_locations(
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
            _observe_phase(active_ops, "before_workflow")
            for identity in attempt["required_tools"]:
                _admit_required_tool_identity(identity)
            if signals.first_signal is not None:
                candidate = WorkflowResult(
                    None,
                    signals.first_signal,
                    "Lifecycle interrupted before delegated workflow start",
                )
            elif active_ops.run_workflow is None:
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
            storage_binding = active_ops.admit_storage_context(attempt, execution)
            active_ops.admit_runtime_context(attempt, request, storage_binding)
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
        (
            reporting,
            reporting_blockers,
            verified_report_locations,
        ) = inspection._inspect_reporting_ledger_with_locations(
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
            message = "Snakemake exited zero without complete EMRYS state"
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
    _observe_phase(active_ops, "before_receipt_publication")
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
        reporting=reporting,
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
                    reporting=reporting,
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
        workflow_result=result,
        verified_report_locations=(
            verified_report_locations if receipt["status"] == "succeeded" else ()
        ),
    )


def run_attempt(
    request: LifecycleRequest,
    *,
    ops: LifecycleOps | None = None,
) -> LifecycleOutcome:
    """Execute through the fixed signal authority and advisory mutex."""

    active_ops = default_lifecycle_ops() if ops is None else ops
    with TransactionSignalController(
        DEFAULT_SIGNAL_OPS,
        active_ops.process_group_ops,
    ) as signals:
        root = _canonical_root(request.run_root)
        try:
            prepared_run_id = str(request.attempt_record["run_id"])
        except KeyError as exc:
            raise LifecycleError("Lifecycle request has no Run ID") from exc
        _admit_run_before_attempt(root, prepared_run_id)
        _observe_phase(active_ops, "before_mutex")
        _refuse_pre_attempt_signal(signals, "before mutex acquisition")
        with _acquire_attempt_mutex(
            root,
            observe=active_ops.observe_mutex,
            interrupted=lambda: signals.first_signal is not None,
        ):
            _observe_phase(active_ops, "after_mutex")
            _refuse_pre_attempt_signal(signals, "at mutex acquisition")
            return _run_attempt_locked(
                request,
                active_ops=active_ops,
                signals=signals,
            )


def _admit_attempt_preparation(
    preparation: AttemptPreparation,
) -> dict[str, Any]:
    """Admit the exact no-write attempt record used at the mutex boundary."""

    if type(preparation.attempt_record_bytes) is not bytes:
        raise LifecycleError("Prepared workflow attempt must be exact immutable bytes")
    try:
        attempt = orchestration_contracts.load_json_object_bytes(
            preparation.attempt_record_bytes,
            "prepared workflow attempt",
        )
        orchestration_contracts.validate_record("workflow-attempt", attempt)
    except orchestration_contracts.ContractValidationError as exc:
        raise LifecycleError(f"Invalid prepared workflow attempt: {exc}") from exc
    if (
        orchestration_contracts.canonical_json_bytes(attempt)
        != preparation.attempt_record_bytes
    ):
        raise LifecycleError("Prepared workflow attempt must use canonical JSON bytes")
    if preparation.operation not in {"execute", "resume"}:
        raise LifecycleError(
            f"Unsupported prepared lifecycle operation: {preparation.operation}"
        )
    for field, expected in (
        ("run_id", preparation.run_id),
        ("workflow_attempt_id", preparation.workflow_attempt_id),
        ("owner_token", preparation.owner_token),
        ("host", preparation.host),
        ("process_id", preparation.process_id),
        ("created_at", preparation.created_at),
        ("operation", preparation.operation),
    ):
        if attempt.get(field) != expected:
            raise LifecycleError(
                f"Prepared workflow attempt does not bind prepared {field}"
            )
    return attempt


def run_materialized_attempt(
    preparation: AttemptPreparation,
    materialize: AttemptMaterializer,
    *,
    ops: LifecycleOps | None = None,
) -> LifecycleOutcome:
    """Serialize admission before publishing lock or attempt-specific inputs."""

    active_ops = default_lifecycle_ops() if ops is None else ops
    with TransactionSignalController(
        DEFAULT_SIGNAL_OPS,
        active_ops.process_group_ops,
    ) as signals:
        root = _canonical_root(preparation.run_root)
        locks_root = root / "locks"
        attempts_root = root / "attempts"
        for directory in (locks_root, attempts_root):
            if directory.is_symlink() or not directory.is_dir():
                raise LifecycleError(
                    f"Lifecycle parent must be pre-materialized and real: {directory}"
                )
        prepared_attempt = _admit_attempt_preparation(preparation)
        _admit_run_before_attempt(root, preparation.run_id)
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
                preparation.operation,
                root,
                prepared_attempt,
                active_ops,
            )
            _observe_phase(active_ops, "before_run_lock")
            _refuse_pre_attempt_signal(signals, "before run-lock publication")
            lock_path = locks_root / "run.lock"
            lock_record = {
                "schema_version": "emrys.run-lock.v1",
                "run_id": preparation.run_id,
                "workflow_attempt_id": preparation.workflow_attempt_id,
                "attempt_record_path": (
                    f"attempts/{preparation.workflow_attempt_id}/attempt.json"
                ),
                "owner_token": preparation.owner_token,
                "process_id": preparation.process_id,
                "host": preparation.host,
                "created_at": preparation.created_at,
            }
            orchestration_contracts.validate_record("run-lock", lock_record)
            lock_bytes = orchestration_contracts.canonical_json_bytes(lock_record)
            active_ops.publish_bytes(lock_path, lock_bytes)
            lock_state = lock_path.stat(follow_symlinks=False)
            owned = _OwnedRunLock(
                path=lock_path,
                record=lock_record,
                data=lock_bytes,
                inode=(lock_state.st_dev, lock_state.st_ino),
            )
            try:
                _observe_phase(active_ops, "after_run_lock")
                _refuse_pre_attempt_signal(signals, "after run-lock publication")
                _observe_phase(active_ops, "before_materialization")
                _refuse_pre_attempt_signal(signals, "before materialization")
                request = materialize()
                _observe_phase(active_ops, "after_materialization")
                _refuse_pre_attempt_signal(signals, "during materialization")
                if request.run_root != root:
                    raise LifecycleError(
                        "Materialized request changed the prepared run root"
                    )
                if request.operation != preparation.operation:
                    raise LifecycleError(
                        "Materialized request changed the prepared lifecycle operation"
                    )
                try:
                    materialized_attempt_bytes = (
                        orchestration_contracts.canonical_json_bytes(
                            dict(request.attempt_record)
                        )
                    )
                except (TypeError, ValueError) as exc:
                    raise LifecycleError(
                        "Materialized workflow attempt is not canonical JSON"
                    ) from exc
                if materialized_attempt_bytes != preparation.attempt_record_bytes:
                    raise LifecycleError(
                        "Materialized workflow attempt differs from prepared exact bytes"
                    )
                return _run_attempt_locked(
                    request,
                    active_ops=active_ops,
                    signals=signals,
                    _owned_lock=owned,
                )
            except Exception as exc:
                attempt_path = (
                    attempts_root / preparation.workflow_attempt_id / "attempt.json"
                )
                if not attempt_path.exists() and not attempt_path.is_symlink():
                    if lock_path.exists() and not lock_path.is_symlink():
                        evidence = locks_root / (
                            f"released-{preparation.workflow_attempt_id}-run-lock.json"
                        )
                        active_ops.release_lock(
                            lock_path,
                            evidence,
                            lock_bytes,
                            owned.inode,
                        )
                if isinstance(exc, LifecycleError):
                    raise
                raise LifecycleError(
                    f"Could not materialize immutable workflow attempt: {exc}"
                ) from exc


__all__ = (
    "AttemptPreparation",
    "LifecycleError",
    "LifecycleOps",
    "LifecycleOutcome",
    "LifecycleRequest",
    "RuntimeContextAdmission",
    "StorageContextAdmission",
    "WorkflowResult",
    "build_snakemake_argv",
    "default_lifecycle_ops",
    "run_attempt",
    "run_materialized_attempt",
)
