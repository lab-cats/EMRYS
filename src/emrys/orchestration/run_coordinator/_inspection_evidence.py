"""Admit task, Results, reporting, and cumulative Attempt evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.run_coordinator._inspection_admission import (
    ExpectedTask,
    InspectionError,
    SuccessorRunAuthority,
    admit_successor_run,
    _record_reference,
    expected_tasks,
    verified_tree_blockers,
)
from emrys.orchestration.run_coordinator._inspection_attempts import (
    TaskAttemptObservation,
    TaskHistoryEntry,
    inspect_attempt_task_trees,
)
from emrys.orchestration.run_coordinator.reporting_boundary import (
    SemanticTransaction as ValidatedReportingReceipt,
)
from emrys.orchestration.run_coordinator.reporting_boundary import (
    SemanticValidator as ReportingReceiptValidator,
    inspect_reporting_ledger,
)

TaskState = Literal["pending", "verified", "blocked"]


@dataclass(frozen=True, slots=True)
class TaskInspection:
    """Derived state for one required owner scope."""

    expected: ExpectedTask
    state: TaskState
    record: dict[str, Any] | None
    record_reference: dict[str, str] | None
    start_origin: str | None = None
    start_reference: dict[str, str] | None = None
    terminal_attempts: tuple[TaskAttemptObservation, ...] = ()
    retry_task_attempt_record: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class EvidenceInspection:
    """One canonical evidence snapshot shared by inspection and lifecycle."""

    tasks: tuple[TaskInspection, ...]
    task_attempt_records: tuple[dict[str, Any], ...]
    task_start_records: tuple[dict[str, Any], ...]
    verified_tasks: tuple[dict[str, Any], ...]
    missing_tasks: tuple[str, ...]
    reporting_completion_records: dict[str, dict[str, dict[str, str] | None]]
    verified_report_locations: tuple[tuple[str, Path], ...]
    integrity_blockers: tuple[str, ...]
    results_blockers: tuple[str, ...]
    reporting_blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskEvidenceInspection:
    """One task-history fold shared by lifecycle, public inspection and backend."""

    tasks: tuple[TaskInspection, ...]
    task_attempt_records: tuple[dict[str, Any], ...]
    task_start_records: tuple[dict[str, Any], ...]
    verified_tasks: tuple[dict[str, Any], ...]
    integrity_blockers: tuple[str, ...]
    results_blockers: tuple[str, ...]


def inspect_task_evidence(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    *,
    receipts: Mapping[str, Mapping[str, Any]],
    authority: SuccessorRunAuthority | None = None,
    allow_incomplete_origin: str | None = None,
    selected_task: tuple[str, str] | None = None,
) -> TaskEvidenceInspection:
    """Admit immutable history, then separately observe current retry readiness."""

    from emrys.orchestration.run_coordinator import task  # noqa: PLC0415

    authority = authority or admit_successor_run(root)
    expected = expected_tasks(authority, profile)
    if selected_task is not None:
        expected = tuple(
            item
            for item in expected
            if (item.machine_key, item.scope_id) == selected_task
        )
        if not expected:
            raise InspectionError("Selected Task is not an expected Run scope")
    entries, tree_blockers = inspect_attempt_task_trees(
        root,
        execution,
        profile,
        attempts,
        authority=authority,
        allow_incomplete_origin=allow_incomplete_origin,
        selected_task=selected_task,
    )
    by_scope: dict[tuple[str, str], dict[str, TaskHistoryEntry]] = {}
    for entry in entries:
        key = entry.expected.machine_key, entry.expected.scope_id
        by_scope.setdefault(key, {})[entry.workflow_attempt_id] = entry
    blockers = [
        *(verified_tree_blockers(root, expected) if selected_task is None else ()),
        *tree_blockers,
    ]
    inspected: list[TaskInspection] = []
    for item in expected:
        scoped = by_scope.get((item.machine_key, item.scope_id), {})
        errors: list[str] = []
        verified_path = (
            root / "state" / "verified" / item.machine_key / f"{item.scope_id}.json"
        )
        verified_present = verified_path.exists() or verified_path.is_symlink()
        verified_record = None
        verified_reference = None
        if verified_present:
            try:
                verified_reference = _record_reference(
                    verified_path, root, "verified task record"
                )
                verified_record = task.validate_verified_task(
                    verified_path,
                    run_root=root,
                    execution=execution,
                    profile=profile,
                    machine_key=item.machine_key,
                    scope=item.scope,
                )
                if (
                    _record_reference(verified_path, root, "verified task record")
                    != verified_reference
                ):
                    raise InspectionError(
                        "Verified task record changed during semantic admission"
                    )
            except (
                InspectionError,
                OSError,
                task.TaskBoundaryError,
                orchestration_contracts.ContractValidationError,
            ) as exc:
                errors.append(
                    f"Could not admit reusable verified task {verified_path}: {exc}"
                )
                verified_record = verified_reference = None

        latest: TaskHistoryEntry | None = None
        for attempt in attempts:
            identifier = str(attempt["workflow_attempt_id"])
            entry = scoped.get(identifier)
            try:
                definition = attempt["tasks"][item.machine_key][item.scope_id]
                if "workflow_attempt_record" in definition:
                    if (
                        latest is None
                        or latest.start_record is None
                        or latest.terminal is None
                        or latest.terminal.record != verified_record
                        or definition["workflow_attempt_record"]
                        != latest.start_record["workflow_attempt_record"]
                    ):
                        raise InspectionError(
                            "Retained task does not bind its admitted verified origin"
                        )
                else:
                    expected_retry = None
                    if latest is not None:
                        if (
                            latest.terminal is None
                            or latest.terminal.record["abort_closure"]
                            != "linux-task-prepublication.v1"
                        ):
                            raise InspectionError(
                                "Fresh task follows an entered scope without positive abort closure"
                            )
                        expected_retry = latest.terminal.record_reference
                    if definition["retry_task_attempt_record"] != expected_retry:
                        raise InspectionError(
                            "Task retry reference is not its latest closed abort"
                        )
                if entry is not None and entry.start_record is not None:
                    latest = entry
            except (KeyError, TypeError, InspectionError) as exc:
                errors.append(
                    f"Task history {identifier}/{item.machine_key}/{item.scope_id}: {exc}"
                )

        if verified_record is not None and (
            latest is None
            or latest.terminal is None
            or latest.terminal.record != verified_record
            or latest.start_reference != verified_record["task_start_record"]
        ):
            errors.append(
                f"Verified task has no exact terminal history: {verified_path}"
            )
            verified_record = verified_reference = None
        retry_reference = None
        if latest is not None and verified_record is None:
            if (
                latest.terminal is not None
                and latest.terminal.record["abort_closure"]
                == "linux-task-prepublication.v1"
            ):
                if not errors:
                    try:
                        task.recheck_aborted_task(
                            run_root=root,
                            execution=execution,
                            profile=profile,
                            machine_key=item.machine_key,
                            scope=item.scope,
                            record_reference=latest.terminal.record_reference,
                        )
                        retry_reference = dict(latest.terminal.record_reference)
                    except (
                        InspectionError,
                        OSError,
                        task.TaskBoundaryError,
                        orchestration_contracts.ContractValidationError,
                    ) as exc:
                        errors.append(
                            f"Aborted task is not ready for retry {item.machine_key}/{item.scope_id}: {exc}"
                        )
            elif latest.workflow_attempt_id != allow_incomplete_origin:
                errors.append(
                    f"Could not close task-start {latest.start_reference['path']}: "
                    "Producer entry has no positive abort closure or verified result"
                )
        state: TaskState = (
            "blocked"
            if errors
            else "verified"
            if verified_record is not None
            else "pending"
        )
        inspected.append(
            TaskInspection(
                item,
                state,
                verified_record,
                verified_reference,
                None if latest is None else latest.workflow_attempt_id,
                None if latest is None else latest.start_reference,
                tuple(
                    entry.terminal
                    for entry in scoped.values()
                    if entry.terminal is not None
                ),
                retry_reference,
            )
        )
        blockers.extend(errors)

    def projection(
        entry: TaskHistoryEntry, reference: dict[str, str]
    ) -> dict[str, Any]:
        return {
            "workflow_attempt_id": entry.workflow_attempt_id,
            "machine_key": entry.expected.machine_key,
            "scope": entry.expected.scope,
            "record": reference,
        }

    ordered_entries = sorted(
        entries,
        key=lambda entry: (
            entry.workflow_attempt_id,
            entry.expected.machine_key,
            entry.expected.scope_type,
            entry.expected.scope_id,
        ),
    )
    terminal_records = tuple(
        projection(entry, entry.terminal.record_reference)
        for entry in ordered_entries
        if entry.terminal is not None
    )
    start_records = tuple(
        projection(entry, entry.start_reference)
        for entry in ordered_entries
        if entry.start_reference is not None
    )
    verified_records = tuple(
        {
            "machine_key": item.expected.machine_key,
            "scope": item.expected.scope,
            "record": item.record_reference,
        }
        for item in inspected
        if item.record is not None
    )
    projections = (
        (
            "task_attempt_records",
            tuple((item["workflow_attempt_id"], item) for item in terminal_records),
            "Task attempts",
        ),
        (
            "task_start_records",
            tuple((item["workflow_attempt_id"], item) for item in start_records),
            "task starts",
        ),
        (
            "verified_tasks",
            tuple(
                (item.record["workflow_attempt_id"], record)
                for item, record in zip(
                    (item for item in inspected if item.record is not None),
                    verified_records,
                    strict=True,
                )
            ),
            "verified tasks",
        ),
    )
    receipt_integrity, receipt_results = _receipt_evidence_blockers(
        attempts, receipts, projections, inspected, selected_task=selected_task
    )
    return TaskEvidenceInspection(
        tasks=tuple(inspected),
        task_attempt_records=terminal_records,
        task_start_records=start_records,
        verified_tasks=verified_records,
        integrity_blockers=tuple(receipt_integrity),
        results_blockers=tuple((*blockers, *receipt_results)),
    )


def _receipt_evidence_blockers(
    attempts: Sequence[Mapping[str, Any]],
    receipts: Mapping[str, Mapping[str, Any]],
    projections: Sequence[tuple[str, Sequence[tuple[Any, dict[str, Any]]], str]],
    tasks: Sequence[TaskInspection],
    *,
    selected_task: tuple[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    """Require every receipt to bind the exact cumulative evidence at its time."""

    positions = {
        str(attempt["workflow_attempt_id"]): index
        for index, attempt in enumerate(attempts)
    }

    def admitted(origin: Any, position: int) -> bool:
        return str(origin) in positions and positions[str(origin)] <= position

    def selected(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            item
            for item in records
            if selected_task is None
            or (item["machine_key"], item["scope"]["scope_id"]) == selected_task
        ]

    integrity_blockers: list[str] = []
    results_blockers: list[str] = []
    for identifier, receipt in receipts.items():
        if identifier not in positions:
            integrity_blockers.append(
                f"Receipt has no workflow attempt in chain: {identifier}"
            )
            continue
        position = positions[identifier]
        for field, evidence, label in projections:
            expected = [
                record for origin, record in evidence if admitted(origin, position)
            ]
            if selected(receipt[field]) != expected:
                results_blockers.append(
                    f"Attempt receipt omits or adds cumulative {label}: {identifier}"
                )

        if receipt["status"] != "blocked":
            closed = {
                (
                    terminal.record["task_start_record"]["path"],
                    terminal.record["task_start_record"]["sha256"],
                )
                for item in tasks
                for terminal in item.terminal_attempts
                if terminal.record["task_start_record"] is not None
                and admitted(terminal.record["workflow_attempt_id"], position)
                and (
                    terminal.record["abort_closure"] == "linux-task-prepublication.v1"
                    or terminal.record == item.record
                )
            }
            starts = {
                (item["record"]["path"], item["record"]["sha256"])
                for item in selected(receipt["task_start_records"])
            }
            if starts != closed:
                results_blockers.append(
                    f"Nonblocked Attempt receipt has an unclosed task start: {identifier}"
                )

    return integrity_blockers, results_blockers


def inspect_evidence(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    receipts: Mapping[str, Mapping[str, Any]],
    validator: ReportingReceiptValidator,
    *,
    authority: SuccessorRunAuthority | None = None,
    allow_incomplete_origin: str | None = None,
) -> EvidenceInspection:
    """Admit canonical evidence once and compare every cumulative receipt."""

    task_evidence = inspect_task_evidence(
        root,
        execution,
        profile,
        attempts,
        receipts=receipts,
        authority=authority,
        allow_incomplete_origin=allow_incomplete_origin,
    )
    reporting, reporting_blockers, locations = inspect_reporting_ledger(
        root,
        execution,
        profile,
        validator,
        allow_incomplete_origin=allow_incomplete_origin,
    )
    return EvidenceInspection(
        tasks=task_evidence.tasks,
        task_attempt_records=task_evidence.task_attempt_records,
        task_start_records=task_evidence.task_start_records,
        verified_tasks=task_evidence.verified_tasks,
        missing_tasks=tuple(
            f"{item.expected.machine_key}/{item.expected.scope_id}"
            for item in task_evidence.tasks
            if item.state == "pending"
        ),
        reporting_completion_records=reporting,
        verified_report_locations=locations,
        integrity_blockers=task_evidence.integrity_blockers,
        results_blockers=task_evidence.results_blockers,
        reporting_blockers=tuple(reporting_blockers),
    )
