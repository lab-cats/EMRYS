"""Canonical local-pilot authority and namespace admission primitives.

This private layer contains the stable path, immutable record, owner-roster,
state-tree, and run-lock admission shared beneath public run inspection and
its task and reporting callers.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    LEGACY_EXECUTION_SCHEMA_VERSION,
    RUN_BINDING_SCHEMA_VERSION,
    AnalysisRevision,
    ExecutionPlan,
    RunBinding,
    bind_run,
    execution_owner_keys,
    read_application_record,
    validate_execution_view,
    validate_successor_run,
)
from emrys.libraries.validation import inputs as validation_inputs
from emrys.libraries.validation.errors import ValidationError


class InspectionError(RuntimeError):
    """Raised when the immutable run identity itself cannot be admitted."""


@dataclass(frozen=True, slots=True)
class ExpectedTask:
    """One required profile owner scope selected by an execution contract."""

    machine_key: str
    step_id: str
    scope_type: str
    scope_id: str

    @property
    def scope(self) -> dict[str, str]:
        return {"scope_type": self.scope_type, "scope_id": self.scope_id}


@dataclass(frozen=True, slots=True)
class SuccessorRunAuthority:
    """One fully admitted successor authority triple."""

    analysis_revision: AnalysisRevision
    execution_plan: ExecutionPlan
    run_binding: RunBinding


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


def _require_stable_file_path(path: Path, root: Path, label: str) -> None:
    """Require one canonical in-Run path before shared descriptor admission."""

    _within(path, root, label)
    try:
        if path.resolve(strict=True) != path:
            raise InspectionError(f"{label} must be a canonical regular file: {path}")
    except OSError as exc:
        raise InspectionError(f"Could not read {label}: {path}: {exc}") from exc


def _read_bytes(path: Path, root: Path, label: str) -> bytes:
    _require_stable_file_path(path, root, label)
    try:
        data, _identity = validation_inputs.read_bytes_with_identity(
            path,
            label,
            nonempty=False,
        )
    except ValidationError as exc:
        raise InspectionError(str(exc)) from exc
    return data


def _stable_directory_entries(path: Path, root: Path, label: str) -> tuple[str, ...]:
    """List one real directory through a stable descriptor-bound snapshot."""

    _within(path, root, label)
    try:
        if path.resolve(strict=True) != path:
            raise InspectionError(f"{label} must be a canonical real directory: {path}")
    except OSError as exc:
        raise InspectionError(f"Could not inspect {label}: {path}: {exc}") from exc
    try:
        return validation_inputs.directory_entries_with_identity(path, label)[0]
    except ValidationError as exc:
        raise InspectionError(str(exc)) from exc


def admit_canonical_record(
    path: Path,
    root: Path,
    name: str,
    *,
    profile: Mapping[str, Any] | None = None,
    read_bytes: Callable[[Path, Path, str], bytes] = _read_bytes,
    error_type: type[RuntimeError] = InspectionError,
) -> tuple[dict[str, Any], bytes]:
    """Admit one stable schema-named record and its exact canonical bytes."""

    data = read_bytes(path, root, name)
    try:
        record = orchestration_contracts.load_json_object_bytes(data, f"{name} {path}")
        orchestration_contracts.validate_record(name, record, profile=profile)
    except orchestration_contracts.ContractValidationError as exc:
        raise error_type(f"Invalid {name} at {path}: {exc}") from exc
    if data != orchestration_contracts.canonical_json_bytes(record):
        raise error_type(f"{name} must use canonical JSON bytes: {path}")
    return record, data


def admit_successor_run(root: Path) -> SuccessorRunAuthority | None:
    """Admit a complete successor triple, or return None for a legacy namespace."""

    paths = {
        "analysis": root / "contract" / "analysis.json",
        "execution_plan": root / "contract" / "execution-plan.json",
        "run": root / "contract" / "run.json",
    }
    present = {
        name for name, path in paths.items() if path.exists() or path.is_symlink()
    }
    if not present:
        return None
    if present != set(paths):
        missing = ", ".join(sorted(set(paths) - present))
        raise InspectionError(f"Incomplete successor Run authority; missing: {missing}")
    values: dict[str, Any] = {}
    for name, path in paths.items():
        data = _read_bytes(path, root, f"successor {name} authority")
        try:
            values[name] = read_application_record(data)
        except orchestration_contracts.ContractValidationError as exc:
            raise InspectionError(f"Invalid successor {name} authority: {exc}") from exc
    analysis = values["analysis"]
    plan = values["execution_plan"]
    run = values["run"]
    if not isinstance(analysis, AnalysisRevision):
        raise InspectionError("analysis.json is not an Analysis revision")
    if not isinstance(plan, ExecutionPlan):
        raise InspectionError("execution-plan.json is not an Execution Plan")
    if not isinstance(run, RunBinding):
        raise InspectionError("run.json is not a Run binding")
    if run.canonical_bytes != bind_run(analysis, plan).canonical_bytes:
        raise InspectionError(
            "Run binding does not bind its Analysis and Execution Plan"
        )
    if root.name != run.run_id:
        raise InspectionError("Run root name does not match successor Run ID")
    return SuccessorRunAuthority(analysis, plan, run)


def admit_execution_path(
    path: Path,
    root: Path,
    profile: Mapping[str, Any],
    *,
    read_bytes: Callable[[Path, Path, str], bytes] = _read_bytes,
    error_type: type[RuntimeError] = InspectionError,
) -> tuple[dict[str, Any], bytes, SuccessorRunAuthority | None]:
    """Admit exact historical execution or successor Run bytes from one path."""

    data = read_bytes(path, root, "execution authority")
    try:
        record = orchestration_contracts.load_json_object_bytes(
            data, f"execution {path}"
        )
        canonical = orchestration_contracts.canonical_json_bytes(record)
        version = record.get("schema_version")
        authority = None
        if version == LEGACY_EXECUTION_SCHEMA_VERSION:
            validate_execution_view(record, profile=profile)
        elif version == RUN_BINDING_SCHEMA_VERSION:
            authority = admit_successor_run(root)
            if authority is None or authority.run_binding.canonical_bytes != canonical:
                raise InspectionError(
                    "Execution bytes differ from successor Run authority"
                )
            validate_successor_run(
                analysis=authority.analysis_revision,
                plan=authority.execution_plan,
                run=authority.run_binding,
                profile=profile,
            )
        else:
            raise InspectionError(f"Unsupported execution authority: {version!r}")
    except (orchestration_contracts.ContractValidationError, InspectionError) as exc:
        raise error_type(f"Invalid execution at {path}: {exc}") from exc
    if data != canonical:
        raise error_type(f"execution must use canonical JSON bytes: {path}")
    return record, data, authority


def _successor_expected_tasks(
    authority: SuccessorRunAuthority,
) -> tuple[ExpectedTask, ...]:
    plan_identity = authority.execution_plan.record["identity"]
    functional = plan_identity["functional_specification"]
    required = set(execution_owner_keys(authority.execution_plan))
    analysis = authority.analysis_revision
    identity = analysis.record["identity"]
    scope_ids = {
        "reference": (analysis.scope_id("reference"),),
        "sample": tuple(row["sample_id"] for row in identity["samples"]),
        "cohort_partition": tuple(
            analysis.scope_id("cohort_partition", row["partition_id"])
            for row in identity["partitions"]
        ),
        "cohort": (analysis.scope_id("cohort"),),
        "analysis": (analysis.scope_id("analysis"),),
    }
    return tuple(
        ExpectedTask(
            machine_key=str(owner["machine_key"]),
            step_id=str(owner["step_id"]),
            scope_type=str(owner["scope_type"]),
            scope_id=str(scope_id),
        )
        for owner in functional["owner_tasks"]
        if owner["machine_key"] in required
        for scope_id in scope_ids[str(owner["scope_type"])]
    )


def expected_tasks(
    execution: Mapping[str, Any] | SuccessorRunAuthority,
    profile: Mapping[str, Any],
) -> tuple[ExpectedTask, ...]:
    """Project the exact required owner/scope roster from its authority."""

    if isinstance(execution, SuccessorRunAuthority):
        return _successor_expected_tasks(execution)

    orchestration_contracts.validate_record("profile", profile)
    validate_execution_view(execution, profile=profile)
    required = set(profile["required_owner_keys"])
    cohort_id = str(execution["analysis"]["cohort_id"])
    scopes = {
        "reference": (str(execution["reference"]["reference_id"]),),
        "samples": tuple(str(row["sample_id"]) for row in execution["samples"]["rows"]),
        "partitions": tuple(
            f"{cohort_id}__{row['partition_id']}"
            for row in execution["partitions"]["rows"]
        ),
        "cohort": (cohort_id,),
        "analysis": (str(execution["analysis"]["primary_analysis_id"]),),
    }
    projected: list[ExpectedTask] = []
    for owner in profile["owner_tasks"]:
        machine_key = str(owner["machine_key"])
        if machine_key not in required:
            continue
        for scope_id in scopes[str(owner["scope_selector"])]:
            projected.append(
                ExpectedTask(
                    machine_key=machine_key,
                    step_id=str(owner["step_id"]),
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

    return _exact_scope_tree_blockers(
        root / "state" / "verified",
        expected,
        file_name=lambda item: f"{item.scope_id}.json",
        label="verified task",
        sentence_label="Verified task",
        record_label="Verified task marker",
    )


def _exact_scope_tree_blockers(
    root_path: Path,
    expected: Sequence[ExpectedTask],
    *,
    file_name: Callable[[ExpectedTask], str],
    label: str,
    sentence_label: str | None = None,
    record_label: str | None = None,
) -> tuple[str, ...]:
    """Close one optional owner/scope tree against the execution roster."""

    sentence_label = sentence_label or label
    record_label = record_label or f"{label} record"
    if not root_path.exists() and not root_path.is_symlink():
        return ()
    if root_path.is_symlink() or not root_path.is_dir():
        return (f"{sentence_label} root is not a real directory: {root_path}",)
    expected_by_owner: dict[str, set[str]] = {}
    for item in expected:
        expected_by_owner.setdefault(item.machine_key, set()).add(file_name(item))
    blockers: list[str] = []
    for owner_path in root_path.iterdir():
        expected_names = expected_by_owner.get(owner_path.name)
        if expected_names is None:
            blockers.append(f"Unexpected {label} owner state: {owner_path}")
            continue
        if owner_path.is_symlink() or not owner_path.is_dir():
            blockers.append(
                f"{sentence_label} owner state is not a real directory: {owner_path}"
            )
            continue
        for record_path in owner_path.iterdir():
            if record_path.name not in expected_names:
                blockers.append(f"Unexpected {label} state path: {record_path}")
            elif record_path.is_symlink() or not record_path.is_file():
                blockers.append(f"{record_label} is not a real file: {record_path}")
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


def _state_tree_blockers_by_domain(
    root: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Close the state namespace without collapsing science and reporting."""

    state_root = root / "state"
    try:
        entries = _stable_directory_entries(state_root, root, "aggregate state root")
    except InspectionError as exc:
        return (str(exc),), (), ()
    allowed = frozenset({"task-starts", "verified", "reporting"})
    integrity_blockers: list[str] = []
    results_blockers: list[str] = []
    reporting_blockers: list[str] = []
    for name in entries:
        path = state_root / name
        if name not in allowed:
            integrity_blockers.append(f"Unexpected aggregate state path: {path}")
        elif path.is_symlink() or not path.is_dir():
            label = {
                "reporting": "Reporting state root",
                "task-starts": "Task-start state root",
                "verified": "Verified state root",
            }[name]
            target = reporting_blockers if name == "reporting" else results_blockers
            target.append(f"{label} must be a real directory: {path}")
    return (
        tuple(integrity_blockers),
        tuple(results_blockers),
        tuple(reporting_blockers),
    )


def state_tree_blockers(root: Path) -> tuple[str, ...]:
    """Close Attempt-owned aggregate state without gating on reporting."""

    integrity, results, _reporting = _state_tree_blockers_by_domain(root)
    return (*integrity, *results)


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

    expected_lock = orchestration_contracts.run_lock_record(attempt)
    if terminal_exists and not require_active:
        receipt, _ = admit_canonical_record(terminal_path, root, "attempt-receipt")
        released, released_data = admit_canonical_record(
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
        lock_record, lock_data = admit_canonical_record(active_path, root, "run-lock")
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
