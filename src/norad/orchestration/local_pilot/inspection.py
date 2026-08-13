"""Read-only derivation of local-pilot run state from NORAD records.

Snakemake metadata is intentionally absent from this owner.  State comes from
the immutable execution/profile contracts, attempt chain, verified task
records, reporting transaction receipts, and the explicitly owned run lock.
"""

from __future__ import annotations

import hashlib
import os
import re
import socket
import stat
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from norad.contracts.orchestration import api as orchestration_contracts

RunState = Literal[
    "prepared",
    "running",
    "resume_available",
    "blocked",
    "local_pipeline_complete",
]
TaskState = Literal["pending", "verified", "blocked"]
_WORKFLOW_ATTEMPT_NAME_RE = re.compile(r"^workflow-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}$")
_ATTEMPT_CHILD_NAMES = frozenset(
    {
        "attempt.json",
        "attempt-receipt.json",
        "released-run-lock.json",
        "request.yaml",
        "tasks",
    }
)


class ValidatedReportingReceipt(Protocol):
    """Neutral result required from direct reporting transaction admission."""

    receipt_path: Path
    receipt_sha256: str


ReportingReceiptValidator = Callable[
    [
        str,
        Path,
        Path,
        Mapping[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ],
    ValidatedReportingReceipt,
]


class InspectionError(RuntimeError):
    """Raised when the immutable run identity itself cannot be admitted."""


@dataclass(frozen=True, slots=True)
class ExpectedTask:
    """One required profile owner scope selected by an execution contract."""

    machine_key: str
    scope_type: str
    scope_id: str

    @property
    def scope(self) -> dict[str, str]:
        return {"scope_type": self.scope_type, "scope_id": self.scope_id}


@dataclass(frozen=True, slots=True)
class TaskInspection:
    """Derived state for one required owner scope."""

    expected: ExpectedTask
    state: TaskState
    record_path: Path
    blocker: str | None
    record: dict[str, Any] | None
    record_reference: dict[str, str] | None


@dataclass(frozen=True, slots=True)
class TaskLedgerInspection:
    """One exact producer-entry record and its terminal reusable state."""

    expected: ExpectedTask
    start: dict[str, Any]
    start_reference: dict[str, str]
    verified: dict[str, Any] | None
    verified_reference: dict[str, str] | None


@dataclass(frozen=True, slots=True)
class InspectionOps:
    """Explicit host/process observations used by read-only inspection."""

    host_name: Callable[[], str]
    process_is_alive: Callable[[int], bool]
    validate_reporting_receipt: ReportingReceiptValidator


@dataclass(frozen=True, slots=True)
class RunInspection:
    """Complete derived state without a mutable status cache."""

    run_root: Path
    run_id: str
    state: RunState
    latest_workflow_attempt_id: str | None
    latest_attempt: dict[str, Any] | None
    latest_receipt: dict[str, Any] | None
    tasks: tuple[TaskInspection, ...]
    reporting_completion_records: dict[str, dict[str, dict[str, str] | None]]
    blockers: tuple[str, ...]
    resume_available: bool
    local_pipeline_complete: bool


def _default_process_is_alive(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def default_inspection_ops() -> InspectionOps:
    """Construct production-only process observations."""

    from norad.reporting import transaction_validation  # noqa: PLC0415

    return InspectionOps(
        host_name=socket.gethostname,
        process_is_alive=_default_process_is_alive,
        validate_reporting_receipt=transaction_validation.validate_receipt,
    )


def _canonical_root(path: Path) -> Path:
    if not path.is_absolute():
        raise InspectionError(f"run_root must be absolute: {path}")
    if not path.is_dir() or path.is_symlink():
        raise InspectionError(f"run_root must be a real directory: {path}")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise InspectionError(f"run_root must already be canonical: {path}")
    return path


def _within(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise InspectionError(f"{label} must be beneath run_root: {path}") from exc


def _read_bytes(path: Path, root: Path, label: str) -> bytes:
    _within(path, root, label)
    if not hasattr(os, "O_NOFOLLOW"):
        raise InspectionError("This platform lacks required O_NOFOLLOW admission")
    try:
        if path.resolve(strict=True) != path:
            raise InspectionError(f"{label} must be a canonical regular file: {path}")
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise InspectionError(f"Could not read {label}: {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise InspectionError(f"{label} is not a regular file: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        path_state = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise InspectionError(f"Could not restat {label}: {path}: {exc}") from exc

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
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
        raise InspectionError(f"{label} changed while it was read: {path}")
    return data


def _stable_directory_entries(path: Path, root: Path, label: str) -> tuple[str, ...]:
    """List one real directory through a stable descriptor-bound snapshot."""

    _within(path, root, label)
    if not hasattr(os, "O_NOFOLLOW"):
        raise InspectionError("This platform lacks required O_NOFOLLOW admission")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    try:
        if path.resolve(strict=True) != path:
            raise InspectionError(f"{label} must be a canonical real directory: {path}")
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise InspectionError(f"Could not inspect {label}: {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISDIR(before.st_mode):
            raise InspectionError(f"{label} is not a real directory: {path}")
        entries = tuple(sorted(os.listdir(descriptor)))
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        current = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise InspectionError(f"Could not restat {label}: {path}: {exc}") from exc

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after) or identity(after) != identity(current):
        raise InspectionError(f"{label} changed while it was inspected: {path}")
    return entries


def _load_canonical_record(
    path: Path,
    root: Path,
    name: str,
    *,
    profile: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], bytes]:
    data = _read_bytes(path, root, name)
    try:
        record = orchestration_contracts.load_json_object_bytes(data, f"{name} {path}")
        orchestration_contracts.validate_record(name, record, profile=profile)
    except orchestration_contracts.ContractValidationError as exc:
        raise InspectionError(f"Invalid {name} at {path}: {exc}") from exc
    if data != orchestration_contracts.canonical_json_bytes(record):
        raise InspectionError(f"{name} must use canonical JSON bytes: {path}")
    return record, data


def _scope_ids(
    owner: Mapping[str, Any], execution: Mapping[str, Any]
) -> tuple[str, ...]:
    selector = owner["scope_selector"]
    if selector == "reference":
        return (str(execution["reference"]["reference_id"]),)
    if selector == "samples":
        return tuple(str(row["sample_id"]) for row in execution["samples"]["rows"])
    if selector == "partitions":
        cohort = str(execution["analysis"]["cohort_id"])
        return tuple(
            f"{cohort}__{row['partition_id']}"
            for row in execution["partitions"]["rows"]
        )
    if selector == "cohort":
        return (str(execution["analysis"]["cohort_id"]),)
    if selector == "analysis":
        return (str(execution["analysis"]["primary_analysis_id"]),)
    raise InspectionError(f"Unsupported required scope selector: {selector}")


def expected_tasks(
    execution: Mapping[str, Any], profile: Mapping[str, Any]
) -> tuple[ExpectedTask, ...]:
    """Project the exact required owner/scope roster in profile order."""

    orchestration_contracts.validate_record("profile", profile)
    orchestration_contracts.validate_record("execution", execution, profile=profile)
    required = set(profile["required_owner_keys"])
    projected: list[ExpectedTask] = []
    for owner in profile["owner_tasks"]:
        machine_key = str(owner["machine_key"])
        if machine_key not in required:
            continue
        for scope_id in _scope_ids(owner, execution):
            projected.append(
                ExpectedTask(
                    machine_key=machine_key,
                    scope_type=str(owner["scope_type"]),
                    scope_id=scope_id,
                )
            )
    return tuple(projected)


def verified_tree_blockers(
    root: Path,
    expected: Sequence[ExpectedTask],
) -> tuple[str, ...]:
    """Require the verified-marker tree to be an exact closed real-file roster."""

    verified_root = root / "state" / "verified"
    if not verified_root.exists() and not verified_root.is_symlink():
        return ()
    if verified_root.is_symlink() or not verified_root.is_dir():
        return (f"Verified task root is not a real directory: {verified_root}",)
    expected_by_owner: dict[str, set[str]] = {}
    for item in expected:
        expected_by_owner.setdefault(item.machine_key, set()).add(
            f"{item.scope_id}.json"
        )
    blockers: list[str] = []
    for child in verified_root.iterdir():
        expected_names = expected_by_owner.get(child.name)
        if expected_names is None:
            blockers.append(f"Unexpected verified task owner state: {child}")
            continue
        if child.is_symlink() or not child.is_dir():
            blockers.append(
                f"Verified task owner state is not a real directory: {child}"
            )
            continue
        observed_names: set[str] = set()
        for marker in child.iterdir():
            observed_names.add(marker.name)
            if marker.name not in expected_names:
                blockers.append(f"Unexpected verified task state path: {marker}")
            elif marker.is_symlink() or not marker.is_file():
                blockers.append(f"Verified task marker is not a real file: {marker}")
        unexpected = observed_names - expected_names
        if unexpected:
            continue
    return tuple(blockers)


def _exact_scope_tree_blockers(
    root_path: Path,
    expected: Sequence[ExpectedTask],
    *,
    file_name: Callable[[ExpectedTask], str],
    label: str,
) -> tuple[str, ...]:
    """Close one optional owner/scope tree against the execution roster."""

    if not root_path.exists() and not root_path.is_symlink():
        return ()
    if root_path.is_symlink() or not root_path.is_dir():
        return (f"{label} root is not a real directory: {root_path}",)
    expected_by_owner: dict[str, dict[str, ExpectedTask]] = {}
    for item in expected:
        expected_by_owner.setdefault(item.machine_key, {})[file_name(item)] = item
    blockers: list[str] = []
    for owner_path in root_path.iterdir():
        expected_names = expected_by_owner.get(owner_path.name)
        if expected_names is None:
            blockers.append(f"Unexpected {label} owner state: {owner_path}")
            continue
        if owner_path.is_symlink() or not owner_path.is_dir():
            blockers.append(
                f"{label} owner state is not a real directory: {owner_path}"
            )
            continue
        for record_path in owner_path.iterdir():
            if record_path.name not in expected_names:
                blockers.append(f"Unexpected {label} state path: {record_path}")
            elif record_path.is_symlink() or not record_path.is_file():
                blockers.append(f"{label} record is not a real file: {record_path}")
    return tuple(blockers)


def task_start_tree_blockers(
    root: Path, expected: Sequence[ExpectedTask]
) -> tuple[str, ...]:
    """Require the aggregate producer-entry ledger to have an exact roster."""

    return _exact_scope_tree_blockers(
        root / "state" / "task-starts",
        expected,
        file_name=lambda item: f"{item.scope_id}.json",
        label="task-start",
    )


def state_tree_blockers(root: Path) -> tuple[str, ...]:
    """Close the aggregate NORAD state namespace before trusting its ledgers."""

    state_root = root / "state"
    try:
        entries = _stable_directory_entries(state_root, root, "aggregate state root")
    except InspectionError as exc:
        return (str(exc),)
    allowed = frozenset({"task-starts", "verified", "reporting"})
    blockers: list[str] = []
    for name in entries:
        path = state_root / name
        if name not in allowed:
            blockers.append(f"Unexpected aggregate state path: {path}")
        elif path.is_symlink() or not path.is_dir():
            label = {
                "reporting": "Reporting state root",
                "task-starts": "Task-start state root",
                "verified": "Verified state root",
            }[name]
            blockers.append(f"{label} must be a real directory: {path}")
    return tuple(blockers)


def lock_tree_blockers(
    root: Path,
    *,
    expected_run_lock: bool | None = None,
) -> tuple[str, ...]:
    """Close the aggregate lock namespace through a stable directory snapshot."""

    locks_root = root / "locks"
    try:
        entries = _stable_directory_entries(locks_root, root, "aggregate locks root")
    except InspectionError as exc:
        return (str(exc),)
    allowed = frozenset({"run.lock", "acquire.mutex"})
    blockers = [
        f"Unexpected retained aggregate lock state: {locks_root / name}"
        for name in entries
        if name not in allowed
    ]
    mutex_path = locks_root / "acquire.mutex"
    if "acquire.mutex" in entries:
        try:
            mutex_data = _read_bytes(
                mutex_path,
                root,
                "persistent lifecycle mutex",
            )
            if mutex_data:
                blockers.append(
                    f"Persistent lifecycle mutex must be zero bytes: {mutex_path}"
                )
        except InspectionError as exc:
            blockers.append(str(exc))
    has_run_lock = "run.lock" in entries
    lock_path = locks_root / "run.lock"
    if expected_run_lock is True and not has_run_lock:
        blockers.append(f"Aggregate run lock is absent: {lock_path}")
    elif expected_run_lock is False and has_run_lock:
        blockers.append(f"Unexpected aggregate run lock is present: {lock_path}")
    if has_run_lock and (lock_path.is_symlink() or not lock_path.is_file()):
        blockers.append(f"Aggregate run lock is not a real file: {lock_path}")
    return tuple(blockers)


def admit_attempt_run_lock(
    root: Path,
    attempt: Mapping[str, Any],
    *,
    require_active: bool,
) -> dict[str, str]:
    """Bind one attempt's active or terminalized outer-lock evidence.

    The returned reference always names the attempt-local retained evidence, so
    an irreversible start keeps the same content binding after atomic release.
    """

    identifier = str(attempt["workflow_attempt_id"])
    attempt_root = root / "attempts" / identifier
    attempt_path = attempt_root / "attempt.json"
    terminal_path = attempt_root / "attempt-receipt.json"
    released_path = attempt_root / "released-run-lock.json"
    terminal_exists = terminal_path.exists() or terminal_path.is_symlink()
    released_exists = released_path.exists() or released_path.is_symlink()

    if require_active and terminal_exists:
        raise InspectionError(
            "A terminal workflow attempt may not cross an irreversible entry boundary"
        )
    if require_active and released_exists:
        raise InspectionError(
            "An attempt with released run-lock evidence is not active"
        )

    expected_lock = {
        "run_id": attempt["run_id"],
        "workflow_attempt_id": identifier,
        "attempt_record_path": f"attempts/{identifier}/attempt.json",
        "owner_token": attempt["owner_token"],
        "process_id": attempt["process_id"],
        "host": attempt["host"],
        "created_at": attempt["created_at"],
    }
    if terminal_exists and not require_active:
        receipt, _ = _load_canonical_record(terminal_path, root, "attempt-receipt")
        released, released_data = _load_canonical_record(
            released_path, root, "run-lock"
        )
        released_reference = _reference_for_bytes(released_path, root, released_data)
        expected_attempt_reference = _record_reference(
            attempt_path, root, "workflow-attempt"
        )
        for field in (
            "run_id",
            "execution_contract_sha256",
            "profile_sha256",
            "workflow_attempt_id",
        ):
            if receipt[field] != attempt[field]:
                raise InspectionError(
                    f"Attempt receipt disagrees with run-lock origin on {field}"
                )
        if receipt["attempt_record"] != expected_attempt_reference:
            raise InspectionError(
                "Attempt receipt does not bind the run-lock origin attempt"
            )
        if receipt["released_run_lock"] != released_reference:
            raise InspectionError(
                "Attempt receipt does not bind exact released run-lock evidence"
            )
        lock_record = released
        reference = released_reference
    else:
        if terminal_exists or released_exists:
            raise InspectionError(
                "Nonterminal workflow attempt has terminal run-lock evidence"
            )
        namespace_blockers = lock_tree_blockers(root, expected_run_lock=True)
        if namespace_blockers:
            raise InspectionError("; ".join(namespace_blockers))
        active_path = root / "locks" / "run.lock"
        lock_record, lock_data = _load_canonical_record(active_path, root, "run-lock")
        reference = {
            "path": released_path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(lock_data).hexdigest(),
        }

    for field, expected in expected_lock.items():
        if lock_record[field] != expected:
            raise InspectionError(
                f"Run-lock evidence disagrees with workflow attempt on {field}"
            )
    return reference


def _record_reference(path: Path, root: Path, label: str) -> dict[str, str]:
    data = _read_bytes(path, root, label)
    return _reference_for_bytes(path, root, data)


def _reference_for_bytes(path: Path, root: Path, data: bytes) -> dict[str, str]:
    """Bind one already-admitted descriptor snapshot without reopening its path."""

    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _admit_reference(
    reference: Mapping[str, Any] | None,
    *,
    root: Path,
    label: str,
) -> str | None:
    if reference is None:
        return None
    raw_path = reference.get("path")
    if not isinstance(raw_path, str):
        return f"{label} has no relative record path"
    path = root / raw_path
    try:
        observed = _record_reference(path, root, label)
    except InspectionError as exc:
        return str(exc)
    if observed != dict(reference):
        return f"{label} content binding no longer matches: {path}"
    return None


def _fixed_reporting_receipt(root: Path, run_id: str, kind: str) -> Path:
    if kind == "artifact_index":
        return (
            root
            / "products"
            / "artifact-summary"
            / run_id
            / f"{run_id}.artifact_receipt.tsv"
        )
    if kind == "run_summary":
        return (
            root
            / "products"
            / "artifact-summary"
            / run_id
            / f"{run_id}.run_summary_receipt.tsv"
        )
    if kind == "html_report":
        return root / "products" / "report" / run_id / f"{run_id}.report_outputs.tsv"
    raise InspectionError(f"Unknown reporting transaction kind: {kind}")


def inspect_reporting_ledger(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    validator: ReportingReceiptValidator,
    *,
    allow_incomplete_origin: str | None = None,
) -> tuple[dict[str, dict[str, dict[str, str] | None]], list[str]]:
    """Close and semantically admit the fixed reporting-entry ledger."""

    from norad.orchestration.local_pilot import reporting_boundary  # noqa: PLC0415

    kinds = ("artifact_index", "run_summary", "html_report")
    state_root = root / "state" / "reporting"
    result = {kind: {"start": None, "verified": None} for kind in kinds}
    blockers: list[str] = []
    if state_root.exists() or state_root.is_symlink():
        if state_root.is_symlink() or not state_root.is_dir():
            return result, [
                f"Reporting ledger root is not a real directory: {state_root}"
            ]
        for kind_path in state_root.iterdir():
            if kind_path.name not in kinds:
                blockers.append(f"Unexpected reporting ledger kind: {kind_path}")
                continue
            if kind_path.is_symlink() or not kind_path.is_dir():
                blockers.append(
                    f"Reporting ledger kind is not a real directory: {kind_path}"
                )
                continue
            for child in kind_path.iterdir():
                if child.name not in {"start.json", "verified.json"}:
                    blockers.append(f"Unexpected reporting ledger state: {child}")
                elif child.is_symlink() or not child.is_file():
                    blockers.append(f"Reporting ledger record is not real: {child}")

    run_id = str(execution["run_id"])
    for kind in kinds:
        kind_root = state_root / kind
        start_path = kind_root / "start.json"
        verified_path = kind_root / "verified.json"
        semantic_path = _fixed_reporting_receipt(root, run_id, kind)
        start_exists = start_path.exists() or start_path.is_symlink()
        verified_exists = verified_path.exists() or verified_path.is_symlink()
        semantic_exists = semantic_path.exists() or semantic_path.is_symlink()
        if not start_exists:
            if verified_exists:
                blockers.append(f"{kind} verified reporting exists without a start")
            if semantic_exists:
                blockers.append(
                    f"{kind} semantic receipt exists without a start ledger"
                )
            continue
        try:
            start_outcome = reporting_boundary.validate_start(
                kind, root, execution, profile
            )
            start, start_data = _load_canonical_record(
                start_path, root, "reporting-start"
            )
            start_reference = _reference_for_bytes(start_path, root, start_data)
            origin = start_outcome.origin_workflow_attempt_id
            result[kind]["start"] = start_reference
            if not verified_exists:
                if origin == allow_incomplete_origin:
                    continue
                raise InspectionError(
                    f"{kind} reporting start has no verified completion"
                )
            verified_outcome = reporting_boundary.validate_verified(
                kind,
                root,
                execution,
                profile,
                semantic_validator=validator,
            )
            verified, verified_data = _load_canonical_record(
                verified_path, root, "verified-reporting"
            )
            verified_reference = _reference_for_bytes(
                verified_path, root, verified_data
            )
            if verified["reporting_start"] != start_reference:
                raise InspectionError(
                    f"{kind} verified reporting does not bind its exact start"
                )
            if verified_outcome.semantic_receipt_path != semantic_path:
                raise InspectionError(
                    f"{kind} reporting boundary selected a different semantic receipt"
                )
            result[kind]["verified"] = verified_reference
        except Exception as exc:
            blockers.append(f"Could not close {kind} reporting ledger: {exc}")
    return result, blockers


def inspect_attempt_tree(root: Path) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    """Inspect the exact aggregate attempt-directory roster without mutation."""

    attempts_root = root / "attempts"
    try:
        root_state = attempts_root.lstat()
    except OSError as exc:
        return (), (
            "Aggregate attempts root must be a pre-materialized real directory: "
            f"{attempts_root}: {exc}",
        )
    if attempts_root.is_symlink() or not stat.S_ISDIR(root_state.st_mode):
        return (), (
            f"Aggregate attempts root is not a real directory: {attempts_root}",
        )
    try:
        observed_entries = tuple(sorted(attempts_root.iterdir()))
    except OSError as exc:
        return (), (
            f"Could not inspect aggregate attempts root: {attempts_root}: {exc}",
        )

    entries: list[Path] = []
    blockers: list[str] = []
    for entry in observed_entries:
        if _WORKFLOW_ATTEMPT_NAME_RE.fullmatch(entry.name) is None:
            blockers.append(f"Unexpected aggregate attempt state path: {entry}")
            continue
        if entry.is_symlink() or not entry.is_dir():
            blockers.append(f"Workflow attempt state is not a real directory: {entry}")
            continue
        entries.append(entry)
        try:
            children = tuple(entry.iterdir())
        except OSError as exc:
            blockers.append(f"Could not inspect workflow attempt state: {entry}: {exc}")
            continue
        blockers.extend(
            f"Unexpected workflow-attempt state path: {child}"
            for child in children
            if child.name not in _ATTEMPT_CHILD_NAMES
        )
        attempt_path = entry / "attempt.json"
        request_path = entry / "request.yaml"
        if attempt_path.is_symlink() or not attempt_path.is_file():
            blockers.append(
                f"Workflow attempt directory has no immutable attempt record: {entry}"
            )
        if request_path.is_symlink() or not request_path.is_file():
            blockers.append(
                f"Workflow attempt directory has no immutable request snapshot: {entry}"
            )
        receipt_path = entry / "attempt-receipt.json"
        if (receipt_path.exists() or receipt_path.is_symlink()) and (
            receipt_path.is_symlink() or not receipt_path.is_file()
        ):
            blockers.append(
                f"Workflow attempt receipt is not a real file: {receipt_path}"
            )
        tasks_path = entry / "tasks"
        if (tasks_path.exists() or tasks_path.is_symlink()) and (
            tasks_path.is_symlink() or not tasks_path.is_dir()
        ):
            blockers.append(
                f"Workflow attempt tasks state is not a real directory: {tasks_path}"
            )
        released_lock_path = entry / "released-run-lock.json"
        if (released_lock_path.exists() or released_lock_path.is_symlink()) and (
            released_lock_path.is_symlink() or not released_lock_path.is_file()
        ):
            blockers.append(
                f"Released run-lock evidence is not a real file: {released_lock_path}"
            )
        if (released_lock_path.exists() or released_lock_path.is_symlink()) and (
            receipt_path.is_symlink() or not receipt_path.is_file()
        ):
            blockers.append(
                "Released run-lock evidence exists without a terminal receipt: "
                f"{released_lock_path}"
            )
    return tuple(entries), tuple(blockers)


def inspect_attempt_chain(
    root: Path,
) -> tuple[
    tuple[dict[str, Any], ...],
    dict[str, dict[str, Any]],
    list[str],
]:
    records: dict[str, dict[str, Any]] = {}
    attempt_references: dict[str, dict[str, str]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    attempt_entries, attempt_tree_blockers = inspect_attempt_tree(root)
    blockers = list(attempt_tree_blockers)
    for entry in attempt_entries:
        attempt_path = entry / "attempt.json"
        if attempt_path.is_symlink() or not attempt_path.is_file():
            continue
        try:
            attempt_data = _read_bytes(attempt_path, root, "workflow-attempt")
            record = _parse_attempt_path_bytes(attempt_data, attempt_path)
        except InspectionError as exc:
            blockers.append(str(exc))
            continue
        identifier = str(record["workflow_attempt_id"])
        if attempt_path.parent.name != identifier:
            blockers.append(
                f"Workflow attempt directory does not match record identity: {attempt_path}"
            )
            continue
        if identifier in records:
            blockers.append(f"Duplicate workflow attempt identity: {identifier}")
            continue
        records[identifier] = record
        attempt_references[identifier] = _reference_for_bytes(
            attempt_path, root, attempt_data
        )
        receipt_path = attempt_path.with_name("attempt-receipt.json")
        if receipt_path.exists() or receipt_path.is_symlink():
            try:
                receipt, _ = _load_canonical_record(
                    receipt_path, root, "attempt-receipt"
                )
            except InspectionError as exc:
                blockers.append(str(exc))
            else:
                receipts[identifier] = receipt

    if blockers:
        return tuple(records.values()), receipts, blockers
    if not records:
        return (), receipts, blockers
    roots = [
        item
        for item in records.values()
        if item["supersedes_workflow_attempt_id"] is None
    ]
    if len(roots) != 1 or roots[0]["operation"] != "execute":
        blockers.append("Workflow attempt chain must have one execute root")
        return tuple(records.values()), receipts, blockers
    ordered = [roots[0]]
    visited = {str(roots[0]["workflow_attempt_id"])}
    while len(visited) < len(records):
        previous = str(ordered[-1]["workflow_attempt_id"])
        children = [
            item
            for item in records.values()
            if item["supersedes_workflow_attempt_id"] == previous
            and str(item["workflow_attempt_id"]) not in visited
        ]
        if len(children) != 1 or children[0]["operation"] != "resume":
            blockers.append(
                "Workflow attempts do not form one linear supersession chain"
            )
            break
        ordered.append(children[0])
        visited.add(str(children[0]["workflow_attempt_id"]))
    for index, attempt in enumerate(ordered[:-1]):
        identifier = str(attempt["workflow_attempt_id"])
        if identifier not in receipts:
            blockers.append(
                f"Non-latest workflow attempt has no terminal receipt: {identifier}"
            )
            continue
        predecessor_receipt = receipts[identifier]
        if predecessor_receipt["status"] not in {"failed", "interrupted"}:
            blockers.append(
                "Superseded workflow attempt is not resumable: "
                f"{identifier}/{predecessor_receipt['status']}"
            )
        successor = ordered[index + 1]
        for field in (
            "run_id",
            "execution_contract_sha256",
            "profile_sha256",
            "source_checkout",
            "required_tools",
            "execution_mode",
            "executor",
        ):
            if successor[field] != attempt[field]:
                blockers.append(
                    f"Adjacent workflow attempts differ on {field}: {identifier}"
                )
        try:
            predecessor_created = datetime.fromisoformat(
                str(attempt["created_at"]).replace("Z", "+00:00")
            )
            predecessor_finished = datetime.fromisoformat(
                str(predecessor_receipt["finished_at"]).replace("Z", "+00:00")
            )
            successor_created = datetime.fromisoformat(
                str(successor["created_at"]).replace("Z", "+00:00")
            )
        except ValueError:
            blockers.append(
                f"Workflow attempt chain has invalid timestamps: {identifier}"
            )
        else:
            if predecessor_finished < predecessor_created:
                blockers.append(
                    f"Workflow attempt receipt predates its attempt: {identifier}"
                )
            if successor_created < predecessor_finished:
                blockers.append(
                    f"Resume attempt predates predecessor completion: {identifier}"
                )
    seen_config_paths: set[str] = set()
    attempt_positions = {
        str(item["workflow_attempt_id"]): index for index, item in enumerate(ordered)
    }
    for attempt in ordered:
        identifier = str(attempt["workflow_attempt_id"])
        receipt_position = attempt_positions[identifier]
        request_path = root / "attempts" / identifier / "request.yaml"
        try:
            request_data = _read_bytes(request_path, root, "attempt request snapshot")
        except InspectionError as exc:
            blockers.append(str(exc))
        else:
            expected_request = {
                "path": str(request_path),
                "size_bytes": len(request_data),
                "sha256": hashlib.sha256(request_data).hexdigest(),
            }
            if attempt["request"] != expected_request:
                blockers.append(
                    f"Workflow attempt request snapshot no longer matches: {identifier}"
                )
        config_reference = attempt["workflow_config"]
        raw_config_path = config_reference.get("path")
        if not isinstance(raw_config_path, str):
            blockers.append(
                f"Workflow attempt has invalid config reference: {identifier}"
            )
        else:
            expected_config_path = (
                Path("contract") / "workflow-configs" / f"{identifier}.json"
            ).as_posix()
            if raw_config_path != expected_config_path:
                blockers.append(
                    f"Workflow attempt config path is not attempt-specific: {identifier}"
                )
            if raw_config_path in seen_config_paths:
                blockers.append(
                    f"Workflow attempts reuse an immutable config path: {raw_config_path}"
                )
            seen_config_paths.add(raw_config_path)
            config_path = root / raw_config_path
            try:
                config_data = _read_bytes(config_path, root, "workflow config")
                observed_config = _reference_for_bytes(config_path, root, config_data)
                config_document = orchestration_contracts.load_json_object_bytes(
                    config_data, f"workflow config {config_path}"
                )
                if config_data != orchestration_contracts.canonical_json_bytes(
                    config_document
                ):
                    raise InspectionError(
                        f"Workflow config is not canonical JSON: {config_path}"
                    )
                expected_config_identity = {
                    "run_root": str(root),
                    "execution_path": str(root / "contract" / "normalized.json"),
                    "profile_path": str(root / "contract" / "profile.json"),
                    "workflow_attempt_id": identifier,
                    "python_executable": str(attempt["normalizer"]["path"]),
                }
                for field, value in expected_config_identity.items():
                    if config_document.get(field) != value:
                        raise InspectionError(
                            f"Workflow config does not bind {field}: {config_path}"
                        )
            except (
                InspectionError,
                orchestration_contracts.ContractValidationError,
            ) as exc:
                blockers.append(str(exc))
            else:
                if observed_config != config_reference:
                    blockers.append(
                        f"Workflow attempt config binding no longer matches: {identifier}"
                    )
        receipt = receipts.get(identifier)
        if receipt is None:
            continue
        try:
            created_at = datetime.fromisoformat(
                str(attempt["created_at"]).replace("Z", "+00:00")
            )
            finished_at = datetime.fromisoformat(
                str(receipt["finished_at"]).replace("Z", "+00:00")
            )
        except ValueError:
            blockers.append(
                f"Workflow attempt has invalid terminal timestamps: {identifier}"
            )
        else:
            if finished_at < created_at:
                blockers.append(
                    f"Workflow attempt receipt predates its attempt: {identifier}"
                )
        for field in (
            "run_id",
            "execution_contract_sha256",
            "profile_sha256",
            "workflow_attempt_id",
        ):
            if receipt[field] != attempt[field]:
                blockers.append(f"Attempt receipt disagrees on {field}: {identifier}")
        attempt_path = root / "attempts" / identifier / "attempt.json"
        expected_reference = attempt_references[identifier]
        if receipt["attempt_record"] != expected_reference:
            blockers.append(
                f"Attempt receipt does not bind its attempt record: {identifier}"
            )
        released_lock_path = attempt_path.with_name("released-run-lock.json")
        try:
            released_lock, released_lock_data = _load_canonical_record(
                released_lock_path, root, "run-lock"
            )
        except InspectionError as exc:
            blockers.append(str(exc))
        else:
            released_reference = _reference_for_bytes(
                released_lock_path, root, released_lock_data
            )
            if receipt["released_run_lock"] != released_reference:
                blockers.append(
                    f"Attempt receipt does not bind released run lock: {identifier}"
                )
            expected_lock = {
                "run_id": attempt["run_id"],
                "workflow_attempt_id": identifier,
                "attempt_record_path": f"attempts/{identifier}/attempt.json",
                "owner_token": attempt["owner_token"],
                "process_id": attempt["process_id"],
                "host": attempt["host"],
                "created_at": attempt["created_at"],
            }
            for field, value in expected_lock.items():
                if released_lock[field] != value:
                    blockers.append(
                        f"Released run lock disagrees on {field}: {identifier}"
                    )
        seen_receipt_paths: set[str] = set()
        seen_preentry_paths: set[str] = set()
        for index, preentry_reference in enumerate(
            receipt["preentry_task_attempt_records"]
        ):
            raw_path = preentry_reference["record"].get("path")
            if not isinstance(raw_path, str):
                blockers.append(
                    f"Attempt receipt has invalid preentry task path: {identifier}/{index}"
                )
                continue
            if raw_path in seen_preentry_paths:
                blockers.append(
                    f"Attempt receipt repeats preentry task path: {identifier}/{raw_path}"
                )
            seen_preentry_paths.add(raw_path)
            expected_path = (
                Path("attempts")
                / str(preentry_reference["workflow_attempt_id"])
                / "tasks"
                / str(preentry_reference["machine_key"])
                / str(preentry_reference["scope"]["scope_id"])
                / "task-attempt.json"
            ).as_posix()
            if raw_path != expected_path:
                blockers.append(
                    "Attempt receipt preentry task path is not canonical: "
                    f"{identifier}/{raw_path}"
                )
                continue
            record_path = root / raw_path
            try:
                preentry_record, preentry_data = _load_canonical_record(
                    record_path, root, "task-attempt"
                )
            except InspectionError as exc:
                blockers.append(str(exc))
                continue
            observed_reference = _reference_for_bytes(record_path, root, preentry_data)
            if observed_reference != preentry_reference["record"]:
                blockers.append(
                    "Historical preentry task content binding no longer matches: "
                    f"{record_path}"
                )
            if (
                preentry_record["task_start_record"] is not None
                or preentry_record["status"] != "failed"
            ):
                blockers.append(
                    f"Historical preentry task is not an unentered failure: {record_path}"
                )
            preentry_origin = str(preentry_record["workflow_attempt_id"])
            if (
                preentry_origin != preentry_reference["workflow_attempt_id"]
                or preentry_origin not in attempt_positions
                or attempt_positions[preentry_origin] > receipt_position
            ):
                blockers.append(
                    f"Attempt receipt pre-binds future preentry evidence: {identifier}/{raw_path}"
                )
            if (
                preentry_record["machine_key"] != preentry_reference["machine_key"]
                or preentry_record["scope"] != preentry_reference["scope"]
            ):
                blockers.append(
                    f"Historical preentry task disagrees with receipt scope: {raw_path}"
                )
        seen_start_paths: set[str] = set()
        for index, start_reference in enumerate(receipt["task_start_records"]):
            raw_path = start_reference["record"].get("path")
            if not isinstance(raw_path, str):
                blockers.append(
                    f"Attempt receipt has invalid task-start path: {identifier}/{index}"
                )
                continue
            if raw_path in seen_start_paths:
                blockers.append(
                    f"Attempt receipt repeats task-start path: {identifier}/{raw_path}"
                )
            seen_start_paths.add(raw_path)
            expected_path = (
                Path("state")
                / "task-starts"
                / str(start_reference["machine_key"])
                / f"{start_reference['scope']['scope_id']}.json"
            ).as_posix()
            if raw_path != expected_path:
                blockers.append(
                    "Attempt receipt task-start path is not canonical: "
                    f"{identifier}/{raw_path}"
                )
                continue
            record_path = root / raw_path
            try:
                start_record, start_data = _load_canonical_record(
                    record_path, root, "task-start"
                )
            except InspectionError as exc:
                blockers.append(str(exc))
                continue
            observed_reference = _reference_for_bytes(record_path, root, start_data)
            if observed_reference != start_reference["record"]:
                blockers.append(
                    "Historical task-start content binding no longer matches: "
                    f"{record_path}"
                )
            start_origin = str(start_record["workflow_attempt_id"])
            if (
                start_origin not in attempt_positions
                or attempt_positions[start_origin] > receipt_position
            ):
                blockers.append(
                    f"Attempt receipt pre-binds future task-start evidence: {identifier}/{raw_path}"
                )
            if (
                start_record["machine_key"] != start_reference["machine_key"]
                or start_record["scope"] != start_reference["scope"]
            ):
                blockers.append(
                    f"Historical task-start disagrees with receipt scope: {raw_path}"
                )
        for index, task_reference in enumerate(receipt["verified_tasks"]):
            raw_path = task_reference["record"].get("path")
            if not isinstance(raw_path, str):
                blockers.append(
                    f"Attempt receipt has invalid verified-task path: {identifier}/{index}"
                )
                continue
            if raw_path in seen_receipt_paths:
                blockers.append(
                    f"Attempt receipt repeats verified-task path: {identifier}/{raw_path}"
                )
            seen_receipt_paths.add(raw_path)
            expected_path = (
                Path("state")
                / "verified"
                / str(task_reference["machine_key"])
                / f"{task_reference['scope']['scope_id']}.json"
            ).as_posix()
            if raw_path != expected_path:
                blockers.append(
                    "Attempt receipt verified-task path is not canonical: "
                    f"{identifier}/{raw_path}"
                )
                continue
            record_path = root / raw_path
            try:
                verified_record, record_data = _load_canonical_record(
                    record_path, root, "verified-task"
                )
            except InspectionError as exc:
                blockers.append(str(exc))
                continue
            observed_reference = _reference_for_bytes(record_path, root, record_data)
            if observed_reference != task_reference["record"]:
                blockers.append(
                    "Historical verified task content binding no longer matches: "
                    f"{record_path}"
                )
            for field in (
                "run_id",
                "execution_contract_sha256",
                "profile_sha256",
            ):
                if verified_record[field] != receipt[field]:
                    blockers.append(
                        "Historical verified task disagrees with receipt on "
                        f"{field}: {identifier}/{index}"
                    )
            if (
                verified_record["machine_key"] != task_reference["machine_key"]
                or verified_record["scope"] != task_reference["scope"]
            ):
                blockers.append(
                    "Historical verified task disagrees with receipt owner scope: "
                    f"{identifier}/{index}"
                )
            verified_origin = str(verified_record["workflow_attempt_id"])
            if (
                verified_origin not in attempt_positions
                or attempt_positions[verified_origin] > receipt_position
            ):
                blockers.append(
                    f"Attempt receipt pre-binds future verified task: {identifier}/{raw_path}"
                )
        for kind, ledger_state in receipt["reporting_completion_records"].items():
            for state_name, schema_name in (
                ("start", "reporting-start"),
                ("verified", "verified-reporting"),
            ):
                reference = ledger_state[state_name]
                if reference is None:
                    continue
                expected_path = (
                    Path("state") / "reporting" / kind / f"{state_name}.json"
                ).as_posix()
                if reference["path"] != expected_path:
                    blockers.append(
                        "Attempt receipt reporting ledger path is not canonical: "
                        f"{identifier}/{reference['path']}"
                    )
                    continue
                ledger_path = root / expected_path
                try:
                    ledger_record, ledger_data = _load_canonical_record(
                        ledger_path, root, schema_name
                    )
                except InspectionError as exc:
                    blockers.append(str(exc))
                    continue
                if _reference_for_bytes(ledger_path, root, ledger_data) != reference:
                    blockers.append(
                        "Historical reporting ledger binding no longer matches: "
                        f"{ledger_path}"
                    )
                reporting_origin = str(ledger_record["origin_workflow_attempt_id"])
                if (
                    reporting_origin not in attempt_positions
                    or attempt_positions[reporting_origin] > receipt_position
                ):
                    blockers.append(
                        "Attempt receipt pre-binds future reporting evidence: "
                        f"{identifier}/{expected_path}"
                    )
                if ledger_record["kind"] != kind:
                    blockers.append(
                        f"Historical reporting ledger kind differs: {ledger_path}"
                    )
        try:
            attempt_reference_after = _record_reference(
                attempt_path, root, "workflow-attempt"
            )
        except InspectionError as exc:
            blockers.append(str(exc))
        else:
            if attempt_reference_after != expected_reference:
                blockers.append(
                    f"Workflow attempt changed during inspection: {identifier}"
                )
    return tuple(ordered), receipts, blockers


def _parse_attempt_path_bytes(
    data: bytes,
    path: Path,
) -> dict[str, Any]:
    """Testable seam proving path contents are never reopened after admission."""

    try:
        record = orchestration_contracts.load_json_object_bytes(
            data, f"workflow-attempt {path}"
        )
        orchestration_contracts.validate_record("workflow-attempt", record)
    except orchestration_contracts.ContractValidationError as exc:
        raise InspectionError(f"Invalid workflow-attempt at {path}: {exc}") from exc
    if data != orchestration_contracts.canonical_json_bytes(record):
        raise InspectionError(f"workflow-attempt must use canonical JSON bytes: {path}")
    return record


def _inspect_tasks(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[tuple[TaskInspection, ...], list[str]]:
    from norad.orchestration.local_pilot import task  # noqa: PLC0415

    expected = expected_tasks(execution, profile)
    inspected: list[TaskInspection] = []
    blockers: list[str] = []
    verified_root = root / "state" / "verified"
    for item in expected:
        record_path = verified_root / item.machine_key / f"{item.scope_id}.json"
        if not record_path.exists() and not record_path.is_symlink():
            inspected.append(
                TaskInspection(item, "pending", record_path, None, None, None)
            )
            continue
        try:
            reference_before = _record_reference(
                record_path, root, "verified task record"
            )
            record = task.validate_verified_task(
                record_path,
                run_root=root,
                execution=execution,
                profile=profile,
                machine_key=item.machine_key,
                scope=item.scope,
            )
            reference_after = _record_reference(
                record_path, root, "verified task record"
            )
            if reference_after != reference_before:
                raise InspectionError(
                    "Verified task record changed during semantic admission"
                )
        except (
            InspectionError,
            OSError,
            task.TaskBoundaryError,
            orchestration_contracts.ContractValidationError,
        ) as exc:
            message = f"Could not admit reusable verified task {record_path}: {exc}"
            blockers.append(message)
            inspected.append(
                TaskInspection(item, "blocked", record_path, message, None, None)
            )
        else:
            inspected.append(
                TaskInspection(
                    item,
                    "verified",
                    record_path,
                    None,
                    record,
                    reference_before,
                )
            )
    blockers.extend(verified_tree_blockers(root, expected))
    return tuple(inspected), blockers


def _inspect_task_ledger(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    allow_incomplete_origin: str | None = None,
) -> tuple[tuple[TaskLedgerInspection, ...], list[str]]:
    from norad.orchestration.local_pilot import task  # noqa: PLC0415

    """Admit every observed producer entry and require a successful closure."""

    expected = expected_tasks(execution, profile)
    blockers = list(task_start_tree_blockers(root, expected))
    admitted: list[TaskLedgerInspection] = []
    for item in expected:
        start_path = (
            root / "state" / "task-starts" / item.machine_key / f"{item.scope_id}.json"
        )
        if not start_path.exists() and not start_path.is_symlink():
            continue
        try:
            start_reference_before = _record_reference(
                start_path, root, "task-start record"
            )
            start = task.validate_task_start(
                start_path,
                run_root=root,
                execution=execution,
                profile=profile,
                machine_key=item.machine_key,
                scope=item.scope,
            )
            start_reference_after = _record_reference(
                start_path, root, "task-start record"
            )
            if start_reference_after != start_reference_before:
                raise InspectionError("Task-start changed during semantic admission")
            verified_path = (
                root / "state" / "verified" / item.machine_key / f"{item.scope_id}.json"
            )
            if not verified_path.exists() and not verified_path.is_symlink():
                if start["workflow_attempt_id"] == allow_incomplete_origin:
                    admitted.append(
                        TaskLedgerInspection(
                            item,
                            start,
                            start_reference_before,
                            None,
                            None,
                        )
                    )
                    continue
                raise InspectionError(
                    "Producer entry has no succeeded task attempt and verified record"
                )
            verified_reference_before = _record_reference(
                verified_path, root, "verified task record"
            )
            verified = task.validate_verified_task(
                verified_path,
                run_root=root,
                execution=execution,
                profile=profile,
                machine_key=item.machine_key,
                scope=item.scope,
            )
            verified_reference_after = _record_reference(
                verified_path, root, "verified task record"
            )
            if verified_reference_after != verified_reference_before:
                raise InspectionError(
                    "Verified task changed during ledger semantic admission"
                )
            if verified["task_start_record"] != start_reference_before:
                raise InspectionError(
                    "Verified task does not bind its exact producer-entry record"
                )
            if verified["workflow_attempt_id"] != start["workflow_attempt_id"]:
                raise InspectionError(
                    "Verified task and producer entry disagree on origin attempt"
                )
        except (
            InspectionError,
            OSError,
            task.TaskBoundaryError,
            orchestration_contracts.ContractValidationError,
        ) as exc:
            blockers.append(f"Could not close task-start {start_path}: {exc}")
            continue
        admitted.append(
            TaskLedgerInspection(
                item,
                start,
                start_reference_before,
                verified,
                verified_reference_before,
            )
        )
    return tuple(admitted), blockers


def inspect_attempt_task_trees(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    *,
    allow_incomplete_origin: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    from norad.orchestration.local_pilot import task  # noqa: PLC0415

    """Close all historical task trees and bind exact preentry diagnostics."""

    expected = {
        (item.machine_key, item.scope_id): item
        for item in expected_tasks(execution, profile)
    }
    attempt_order = {
        str(attempt["workflow_attempt_id"]): index
        for index, attempt in enumerate(attempts)
    }
    preentry: list[dict[str, Any]] = []
    blockers: list[str] = []
    for attempt in attempts:
        identifier = str(attempt["workflow_attempt_id"])
        tasks_root = root / "attempts" / identifier / "tasks"
        if not tasks_root.exists() and not tasks_root.is_symlink():
            continue
        if tasks_root.is_symlink() or not tasks_root.is_dir():
            blockers.append(f"Attempt task root is not a real directory: {tasks_root}")
            continue
        owner_paths = tuple(tasks_root.iterdir())
        if not owner_paths and identifier != allow_incomplete_origin:
            blockers.append(f"Attempt task root is unexpectedly empty: {tasks_root}")
        for owner_path in owner_paths:
            if owner_path.is_symlink() or not owner_path.is_dir():
                blockers.append(
                    f"Attempt task owner is not a real directory: {owner_path}"
                )
                continue
            scope_paths = tuple(owner_path.iterdir())
            if not scope_paths and identifier != allow_incomplete_origin:
                blockers.append(
                    f"Attempt task owner is unexpectedly empty: {owner_path}"
                )
            for scope_path in scope_paths:
                item = expected.get((owner_path.name, scope_path.name))
                if item is None:
                    blockers.append(f"Unexpected attempt task scope: {scope_path}")
                    continue
                if scope_path.is_symlink() or not scope_path.is_dir():
                    blockers.append(
                        f"Attempt task scope is not a real directory: {scope_path}"
                    )
                    continue
                children = {child.name: child for child in scope_path.iterdir()}
                exact = {"task-attempt.json", "stdout.log", "stderr.log"}
                if set(children) != exact:
                    if identifier == allow_incomplete_origin and set(children) <= exact:
                        continue
                    blockers.append(
                        f"Attempt task scope has incomplete or unexpected state: {scope_path}"
                    )
                    continue
                if any(
                    path.is_symlink() or not path.is_file()
                    for path in children.values()
                ):
                    blockers.append(
                        f"Attempt task state is not all real files: {scope_path}"
                    )
                    continue
                record_path = children["task-attempt.json"]
                try:
                    record, record_data = _load_canonical_record(
                        record_path, root, "task-attempt"
                    )
                    identity = {
                        "run_id": execution["run_id"],
                        "execution_contract_sha256": hashlib.sha256(
                            orchestration_contracts.canonical_json_bytes(execution)
                        ).hexdigest(),
                        "profile_sha256": orchestration_contracts.canonical_sha256(
                            profile
                        ),
                        "workflow_attempt_id": identifier,
                        "machine_key": item.machine_key,
                        "scope": item.scope,
                    }
                    for field, value in identity.items():
                        if record[field] != value:
                            raise InspectionError(
                                f"Attempt task state disagrees on {field}"
                            )
                    for field, child_name in (
                        ("stdout_log", "stdout.log"),
                        ("stderr_log", "stderr.log"),
                    ):
                        log_path = children[child_name]
                        log_data = _read_bytes(
                            log_path,
                            root,
                            field.replace("_", " "),
                        )
                        expected_reference = _reference_for_bytes(
                            log_path,
                            root,
                            log_data,
                        )
                        if record[field] != expected_reference:
                            raise InspectionError(
                                f"Attempt task state binds different {field}"
                            )
                    start_path = (
                        root
                        / "state"
                        / "task-starts"
                        / item.machine_key
                        / f"{item.scope_id}.json"
                    )
                    if record["task_start_record"] is None:
                        if record["status"] != "failed":
                            raise InspectionError(
                                "Preentry task attempt must be failed"
                            )
                        if start_path.exists() or start_path.is_symlink():
                            later_start = task.validate_task_start(
                                start_path,
                                run_root=root,
                                execution=execution,
                                profile=profile,
                                machine_key=item.machine_key,
                                scope=item.scope,
                            )
                            later_origin = str(later_start["workflow_attempt_id"])
                            if (
                                later_origin not in attempt_order
                                or attempt_order[later_origin]
                                <= attempt_order[identifier]
                            ):
                                raise InspectionError(
                                    "Preentry task attempt has a same-or-earlier task-start"
                                )
                        preentry.append(
                            {
                                "workflow_attempt_id": identifier,
                                "machine_key": item.machine_key,
                                "scope": item.scope,
                                "record": _reference_for_bytes(
                                    record_path, root, record_data
                                ),
                            }
                        )
                    else:
                        start_reference = _record_reference(
                            start_path, root, "task-start record"
                        )
                        if record["task_start_record"] != start_reference:
                            raise InspectionError(
                                "Task attempt does not bind its exact start"
                            )
                except Exception as exc:
                    blockers.append(
                        f"Could not close attempt task state {scope_path}: {exc}"
                    )
    preentry.sort(
        key=lambda item: (
            item["workflow_attempt_id"],
            item["machine_key"],
            item["scope"]["scope_type"],
            item["scope"]["scope_id"],
        )
    )
    return preentry, blockers


def _historical_receipt_evidence_blockers(
    root: Path,
    attempts: Sequence[Mapping[str, Any]],
    receipts: Mapping[str, Mapping[str, Any]],
    preentry_tasks: Sequence[Mapping[str, Any]],
    task_ledger: Sequence[TaskLedgerInspection],
    tasks: Sequence[TaskInspection],
    reporting: Mapping[str, Mapping[str, dict[str, str] | None]],
) -> list[str]:
    """Require every receipt to bind the exact cumulative evidence at its time."""

    positions = {
        str(attempt["workflow_attempt_id"]): index
        for index, attempt in enumerate(attempts)
    }

    def admitted(origin: Any, position: int) -> bool:
        return str(origin) in positions and positions[str(origin)] <= position

    ordered_starts = sorted(
        task_ledger,
        key=lambda value: (
            value.expected.machine_key,
            value.expected.scope_type,
            value.expected.scope_id,
        ),
    )
    blockers: list[str] = []
    for identifier, receipt in receipts.items():
        if identifier not in positions:
            blockers.append(f"Receipt has no workflow attempt in chain: {identifier}")
            continue
        position = positions[identifier]
        expected_preentry = [
            dict(item)
            for item in preentry_tasks
            if admitted(item["workflow_attempt_id"], position)
        ]
        if receipt["preentry_task_attempt_records"] != expected_preentry:
            blockers.append(
                f"Attempt receipt omits or adds cumulative preentry evidence: {identifier}"
            )

        expected_starts = [
            {
                "machine_key": item.expected.machine_key,
                "scope": item.expected.scope,
                "record": item.start_reference,
            }
            for item in ordered_starts
            if admitted(item.start["workflow_attempt_id"], position)
        ]
        if receipt["task_start_records"] != expected_starts:
            blockers.append(
                f"Attempt receipt omits or adds cumulative task starts: {identifier}"
            )

        expected_verified = [
            {
                "machine_key": item.expected.machine_key,
                "scope": item.expected.scope,
                "record": item.record_reference,
            }
            for item in tasks
            if item.record is not None
            and admitted(item.record["workflow_attempt_id"], position)
        ]
        if receipt["verified_tasks"] != expected_verified:
            blockers.append(
                f"Attempt receipt omits or adds cumulative verified tasks: {identifier}"
            )

        expected_reporting: dict[str, dict[str, dict[str, str] | None]] = {}
        for kind, states in reporting.items():
            expected_reporting[kind] = {"start": None, "verified": None}
            for state_name, schema_name in (
                ("start", "reporting-start"),
                ("verified", "verified-reporting"),
            ):
                reference = states[state_name]
                if reference is None:
                    continue
                try:
                    record, _ = _load_canonical_record(
                        root / reference["path"], root, schema_name
                    )
                except InspectionError:
                    continue
                if admitted(record["origin_workflow_attempt_id"], position):
                    expected_reporting[kind][state_name] = reference
        if receipt["reporting_completion_records"] != expected_reporting:
            blockers.append(
                f"Attempt receipt omits or adds cumulative reporting evidence: {identifier}"
            )
    return blockers


def _inspect_lock(
    root: Path,
    *,
    latest: Mapping[str, Any] | None,
    latest_terminal: bool,
    ops: InspectionOps,
    allowed_next_attempt: Mapping[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    locks_root = root / "locks"
    blockers = list(lock_tree_blockers(root))
    if any("aggregate locks root" in item.lower() for item in blockers):
        return False, blockers
    path = locks_root / "run.lock"
    if not path.exists() and not path.is_symlink():
        return False, blockers
    try:
        record, _ = _load_canonical_record(path, root, "run-lock")
    except InspectionError as exc:
        return False, [str(exc)]
    if latest is None:
        blockers.append("Run lock exists without a workflow attempt")
    else:
        identifier = str(latest["workflow_attempt_id"])
        expected_lock_attempt = latest
        if (
            allowed_next_attempt is not None
            and allowed_next_attempt.get("supersedes_workflow_attempt_id") == identifier
            and record["workflow_attempt_id"]
            == allowed_next_attempt.get("workflow_attempt_id")
        ):
            expected_lock_attempt = allowed_next_attempt
        elif record["workflow_attempt_id"] != identifier:
            blockers.append("Run lock does not bind the latest workflow attempt")
        if record["run_id"] != expected_lock_attempt["run_id"]:
            blockers.append("Run lock does not bind the normalized run")
        if record["owner_token"] != expected_lock_attempt["owner_token"]:
            blockers.append("Run lock owner token does not match the latest attempt")
        if record["process_id"] != expected_lock_attempt["process_id"]:
            blockers.append("Run lock process does not match the owned attempt")
        if record["host"] != expected_lock_attempt["host"]:
            blockers.append("Run lock host does not match the owned attempt")
        if record["created_at"] != expected_lock_attempt["created_at"]:
            blockers.append("Run lock creation time does not match the owned attempt")
        expected_path = (
            f"attempts/{expected_lock_attempt['workflow_attempt_id']}/attempt.json"
        )
        if record["attempt_record_path"] != expected_path:
            blockers.append("Run lock does not name the exact attempt record")
        if latest_terminal and expected_lock_attempt is latest:
            blockers.append("Terminal workflow attempt retained its run lock")
        if record["host"] != ops.host_name():
            blockers.append(
                "Run lock host is not this host; live ownership is unproved"
            )
        elif not ops.process_is_alive(int(record["process_id"])):
            blockers.append(
                "Run lock process is not live; automatic recovery is forbidden"
            )
    return (
        not blockers
        and latest is not None
        and (not latest_terminal or expected_lock_attempt is not latest),
        blockers,
    )


def inspect_run(
    run_root: Path,
    *,
    ops: InspectionOps | None = None,
    allowed_next_attempt: Mapping[str, Any] | None = None,
) -> RunInspection:
    """Derive one run state without reading or repairing ``.snakemake``."""

    root = _canonical_root(run_root)
    active_ops = default_inspection_ops() if ops is None else ops
    profile, profile_data = _load_canonical_record(
        root / "contract" / "profile.json", root, "profile"
    )
    execution, execution_data = _load_canonical_record(
        root / "contract" / "normalized.json",
        root,
        "execution",
        profile=profile,
    )
    blockers: list[str] = []
    blockers.extend(state_tree_blockers(root))
    if (
        execution["profile"]["profile_sha256"]
        != hashlib.sha256(profile_data).hexdigest()
    ):
        blockers.append("Execution contract no longer binds profile snapshot bytes")
    attempts, receipts, attempt_blockers = inspect_attempt_chain(root)
    blockers.extend(attempt_blockers)
    latest = attempts[-1] if attempts else None
    latest_id = None if latest is None else str(latest["workflow_attempt_id"])
    latest_receipt = None if latest_id is None else receipts.get(latest_id)
    if latest is not None:
        expected_execution_hash = hashlib.sha256(execution_data).hexdigest()
        expected_profile_hash = hashlib.sha256(profile_data).hexdigest()
        if latest["run_id"] != execution["run_id"]:
            blockers.append("Latest attempt does not bind normalized run_id")
        if latest["execution_contract_sha256"] != expected_execution_hash:
            blockers.append("Latest attempt does not bind normalized execution bytes")
        if latest["profile_sha256"] != expected_profile_hash:
            blockers.append("Latest attempt does not bind profile bytes")

    latest_terminal = latest_receipt is not None
    running, lock_blockers = _inspect_lock(
        root,
        latest=latest,
        latest_terminal=latest_terminal,
        ops=active_ops,
        allowed_next_attempt=allowed_next_attempt,
    )
    blockers.extend(lock_blockers)
    live_origin = (
        latest_id
        if running and latest_receipt is None and allowed_next_attempt is None
        else None
    )
    tasks, task_blockers = _inspect_tasks(root, execution, profile)
    blockers.extend(task_blockers)
    task_ledger, task_ledger_blockers = _inspect_task_ledger(
        root,
        execution,
        profile,
        allow_incomplete_origin=live_origin,
    )
    blockers.extend(task_ledger_blockers)
    preentry_tasks, task_tree_blockers = inspect_attempt_task_trees(
        root,
        execution,
        profile,
        attempts,
        allow_incomplete_origin=live_origin,
    )
    blockers.extend(task_tree_blockers)
    reporting, reporting_blockers = inspect_reporting_ledger(
        root,
        execution,
        profile,
        active_ops.validate_reporting_receipt,
        allow_incomplete_origin=live_origin,
    )
    blockers.extend(reporting_blockers)
    blockers.extend(
        _historical_receipt_evidence_blockers(
            root,
            attempts,
            receipts,
            preentry_tasks,
            task_ledger,
            tasks,
            reporting,
        )
    )
    if latest_receipt is not None:
        if latest_receipt["reporting_completion_records"] != reporting:
            blockers.append(
                "Latest attempt receipt does not bind exact reporting ledger"
            )
        receipt_tasks = latest_receipt["verified_tasks"]
        if latest_receipt["preentry_task_attempt_records"] != preentry_tasks:
            blockers.append(
                "Latest attempt receipt does not bind exact preentry task evidence"
            )
        receipt_starts = latest_receipt["task_start_records"]
        observed_starts = [
            {
                "machine_key": item.expected.machine_key,
                "scope": item.expected.scope,
                "record": item.start_reference,
            }
            for item in sorted(
                task_ledger,
                key=lambda value: (
                    value.expected.machine_key,
                    value.expected.scope_type,
                    value.expected.scope_id,
                ),
            )
        ]
        if receipt_starts != observed_starts:
            blockers.append(
                "Latest attempt receipt does not bind exact producer-entry ledger"
            )
        expected_references = []
        for inspected in tasks:
            if inspected.record is None:
                continue
            expected_references.append(
                {
                    "machine_key": inspected.expected.machine_key,
                    "scope": inspected.expected.scope,
                    "record": inspected.record_reference,
                }
            )
        if receipt_tasks != expected_references:
            blockers.append(
                "Latest attempt receipt does not bind exact verified task state"
            )
        if latest_receipt["status"] == "succeeded":
            if any(item.state != "verified" for item in tasks):
                blockers.append(
                    "Successful attempt receipt is missing required verified tasks"
                )
            if any(
                state["start"] is None or state["verified"] is None
                for state in reporting.values()
            ):
                blockers.append(
                    "Successful attempt receipt is missing reporting transactions"
                )
    if blockers:
        state: RunState = "blocked"
    elif latest is None:
        state = "prepared"
    elif running and allowed_next_attempt is None:
        state = "running"
    elif latest_receipt is None:
        state = "blocked"
        blockers.append(
            "Latest workflow attempt is nonterminal without a live owned lock"
        )
    elif latest_receipt["status"] in {"failed", "interrupted"}:
        state = "resume_available"
    elif latest_receipt["status"] == "succeeded":
        state = "local_pipeline_complete"
    else:
        state = "blocked"
        blockers.extend(str(value) for value in latest_receipt["blockers"])

    complete = state == "local_pipeline_complete"
    return RunInspection(
        run_root=root,
        run_id=str(execution["run_id"]),
        state=state,
        latest_workflow_attempt_id=latest_id,
        latest_attempt=latest,
        latest_receipt=latest_receipt,
        tasks=tasks,
        reporting_completion_records=reporting,
        blockers=tuple(dict.fromkeys(blockers)),
        resume_available=state == "resume_available",
        local_pipeline_complete=complete,
    )


__all__ = (
    "ExpectedTask",
    "InspectionError",
    "InspectionOps",
    "RunInspection",
    "ReportingReceiptValidator",
    "TaskInspection",
    "TaskLedgerInspection",
    "ValidatedReportingReceipt",
    "admit_attempt_run_lock",
    "default_inspection_ops",
    "expected_tasks",
    "inspect_attempt_tree",
    "inspect_attempt_chain",
    "inspect_attempt_task_trees",
    "inspect_reporting_ledger",
    "inspect_run",
    "lock_tree_blockers",
    "state_tree_blockers",
    "task_start_tree_blockers",
    "verified_tree_blockers",
)
