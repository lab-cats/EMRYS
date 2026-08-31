"""Task, Results, reporting, and historical-receipt evidence admission."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.artifact_inventory import report_output_root
from emrys.orchestration.local_pilot._inspection_admission import (
    ExpectedTask,
    InspectionError,
    SuccessorRunAuthority,
    _record_reference,
    expected_tasks,
    task_start_tree_blockers,
    verified_tree_blockers,
)
from emrys.orchestration.local_pilot._inspection_attempts import (
    inspect_attempt_task_trees,
)
from emrys.orchestration.local_pilot.reporting_boundary import (
    SemanticTransaction as ValidatedReportingReceipt,
)
from emrys.orchestration.local_pilot.reporting_boundary import (
    SemanticValidator as ReportingReceiptValidator,
)

TaskState = Literal["pending", "verified", "blocked"]


def _receipt_binds_reporting(receipt: Mapping[str, Any]) -> bool:
    return receipt.get("schema_version") == "emrys.attempt-receipt.v1"


@dataclass(frozen=True, slots=True)
class TaskInspection:
    """Derived state for one required owner scope."""

    expected: ExpectedTask
    state: TaskState
    record: dict[str, Any] | None
    record_reference: dict[str, str] | None
    start_origin: str | None = None
    start_reference: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class EvidenceInspection:
    """One canonical evidence snapshot shared by inspection and lifecycle."""

    tasks: tuple[TaskInspection, ...]
    preentry_task_attempt_records: tuple[dict[str, Any], ...]
    task_start_records: tuple[dict[str, Any], ...]
    verified_tasks: tuple[dict[str, Any], ...]
    missing_tasks: tuple[str, ...]
    reporting_completion_records: dict[str, dict[str, dict[str, str] | None]]
    verified_report_locations: tuple[tuple[str, Path], ...]
    integrity_blockers: tuple[str, ...]
    results_blockers: tuple[str, ...]
    reporting_blockers: tuple[str, ...]


def _inspect_reporting_ledger_with_locations(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    validator: ReportingReceiptValidator,
    *,
    allow_incomplete_origin: str | None = None,
) -> tuple[
    dict[str, dict[str, dict[str, str] | None]],
    list[str],
    tuple[tuple[str, Path], ...],
    dict[str, str | None],
]:
    """Admit the reporting ledger and retain verified report output locations."""

    from emrys.orchestration.local_pilot import reporting_boundary  # noqa: PLC0415

    kinds = ("artifact_index", "run_summary", "html_report")
    state_root = root / "state" / "reporting"
    result = {kind: {"start": None, "verified": None} for kind in kinds}
    origins: dict[str, str | None] = dict.fromkeys(kinds)
    blockers: list[str] = []
    verified_report_locations: tuple[tuple[str, Path], ...] = ()
    if state_root.exists() or state_root.is_symlink():
        if state_root.is_symlink() or not state_root.is_dir():
            return (
                result,
                [f"Reporting ledger root is not a real directory: {state_root}"],
                (),
                origins,
            )
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

    run_id = str(execution["run_id"])
    for kind in kinds:
        kind_root = state_root / kind
        start_path = kind_root / "start.json"
        verified_path = kind_root / "verified.json"
        output_root = (
            report_output_root(root, profile)
            if kind == "html_report"
            else root / "products" / "artifact-summary"
        )
        suffix = {
            "artifact_index": "artifact_receipt.tsv",
            "run_summary": "run_summary_receipt.tsv",
            "html_report": "report_outputs.tsv",
        }[kind]
        semantic_path = output_root / run_id / f"{run_id}.{suffix}"
        start_exists = start_path.exists() or start_path.is_symlink()
        verified_exists = verified_path.exists() or verified_path.is_symlink()
        if not start_exists:
            if verified_exists:
                blockers.append(f"{kind} verified reporting exists without a start")
            if semantic_path.exists() or semantic_path.is_symlink():
                blockers.append(
                    f"{kind} semantic receipt exists without a start ledger"
                )
            continue
        try:
            admission = (
                reporting_boundary.validate_verified(
                    kind,
                    root,
                    execution,
                    profile,
                    semantic_validator=validator,
                )
                if verified_exists
                else reporting_boundary.validate_start(kind, root, execution, profile)
            )
            result[kind]["start"] = admission.start_reference
            origins[kind] = admission.origin_workflow_attempt_id
            if verified_exists:
                result[kind]["verified"] = admission.verified_reference
                if kind == "html_report":
                    verified_report_locations = admission.verified_report_locations
            elif admission.origin_workflow_attempt_id != allow_incomplete_origin:
                raise InspectionError(
                    f"{kind} reporting start has no verified completion"
                )
        except Exception as exc:
            blockers.append(f"Could not close {kind} reporting ledger: {exc}")
    return result, blockers, verified_report_locations, origins


def _inspect_task_evidence(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    authority: SuccessorRunAuthority | None = None,
    allow_incomplete_origin: str | None = None,
) -> tuple[
    tuple[TaskInspection, ...],
    list[str],
]:
    """Admit task markers and producer entries in one owner/scope pass."""

    from emrys.orchestration.local_pilot import task  # noqa: PLC0415

    expected = expected_tasks(authority or execution, profile)
    blockers = [
        *verified_tree_blockers(root, expected),
        *task_start_tree_blockers(root, expected),
    ]
    inspected: list[TaskInspection] = []
    for item in expected:
        start_path = (
            root / "state" / "task-starts" / item.machine_key / f"{item.scope_id}.json"
        )
        verified_path = (
            root / "state" / "verified" / item.machine_key / f"{item.scope_id}.json"
        )
        start_present = start_path.exists() or start_path.is_symlink()
        verified_present = verified_path.exists() or verified_path.is_symlink()
        verified_record: dict[str, Any] | None = None
        verified_reference: dict[str, str] | None = None
        start_origin: str | None = None
        start_reference: dict[str, str] | None = None

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
                blockers.append(
                    f"Could not admit reusable verified task {verified_path}: {exc}"
                )
                verified_record = None
                verified_reference = None

        if start_present:
            try:
                if verified_record is None:
                    start = task.validate_task_start(
                        start_path,
                        run_root=root,
                        execution=execution,
                        profile=profile,
                        machine_key=item.machine_key,
                        scope=item.scope,
                    )
                    start_reference = _record_reference(
                        start_path, root, "task-start record"
                    )
                    start_origin = str(start["workflow_attempt_id"])
                else:
                    start_reference = dict(verified_record["task_start_record"])
                    if (
                        _record_reference(start_path, root, "task-start record")
                        != start_reference
                    ):
                        raise InspectionError(
                            "Task-start changed after verified-task admission"
                        )
                    start_origin = str(verified_record["workflow_attempt_id"])
            except (
                InspectionError,
                OSError,
                task.TaskBoundaryError,
                orchestration_contracts.ContractValidationError,
            ) as exc:
                blockers.append(f"Could not close task-start {start_path}: {exc}")
                start_origin = None
                start_reference = None
            if (
                start_origin is not None
                and not verified_present
                and start_origin != allow_incomplete_origin
            ):
                blockers.append(
                    f"Could not close task-start {start_path}: "
                    "Producer entry has no succeeded task attempt and verified record"
                )

        state: TaskState = (
            "verified"
            if verified_record is not None
            else "blocked"
            if verified_present
            else "pending"
        )
        inspected.append(
            TaskInspection(
                item,
                state,
                verified_record,
                verified_reference,
                start_origin,
                start_reference,
            )
        )
    return tuple(inspected), blockers


def _historical_receipt_evidence_blockers(
    attempts: Sequence[Mapping[str, Any]],
    receipts: Mapping[str, Mapping[str, Any]],
    projections: Sequence[tuple[str, Sequence[tuple[Any, dict[str, Any]]], str]],
    reporting: Mapping[str, Mapping[str, dict[str, str] | None]],
    reporting_origins: Mapping[str, str | None],
) -> tuple[list[str], list[str], list[str]]:
    """Require every receipt to bind the exact cumulative evidence at its time."""

    positions = {
        str(attempt["workflow_attempt_id"]): index
        for index, attempt in enumerate(attempts)
    }

    def admitted(origin: Any, position: int) -> bool:
        return str(origin) in positions and positions[str(origin)] <= position

    integrity_blockers: list[str] = []
    results_blockers: list[str] = []
    reporting_blockers: list[str] = []
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
            if receipt[field] != expected:
                results_blockers.append(
                    f"Attempt receipt omits or adds cumulative {label}: {identifier}"
                )

        if _receipt_binds_reporting(receipt):
            expected_reporting: dict[str, dict[str, dict[str, str] | None]] = {}
            for kind, states in reporting.items():
                expected_reporting[kind] = {"start": None, "verified": None}
                for state_name in ("start", "verified"):
                    reference = states[state_name]
                    if reference is None:
                        continue
                    if admitted(reporting_origins[kind], position):
                        expected_reporting[kind][state_name] = reference
            if receipt["reporting_completion_records"] != expected_reporting:
                reporting_blockers.append(
                    "Attempt receipt omits or adds cumulative reporting evidence: "
                    f"{identifier}"
                )
    return integrity_blockers, results_blockers, reporting_blockers


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

    tasks, task_blockers = _inspect_task_evidence(
        root,
        execution,
        profile,
        authority=authority,
        allow_incomplete_origin=allow_incomplete_origin,
    )
    preentry_tasks, task_tree_blockers = inspect_attempt_task_trees(
        root,
        execution,
        profile,
        attempts,
        allow_incomplete_origin=allow_incomplete_origin,
        authority=authority,
    )
    reporting, reporting_blockers, locations, reporting_origins = (
        _inspect_reporting_ledger_with_locations(
            root,
            execution,
            profile,
            validator,
            allow_incomplete_origin=allow_incomplete_origin,
        )
    )
    ordered_starts = sorted(
        (item for item in tasks if item.start_reference is not None),
        key=lambda item: (
            item.expected.machine_key,
            item.expected.scope_type,
            item.expected.scope_id,
        ),
    )
    start_projection = tuple(
        (
            item.start_origin,
            {
                "machine_key": item.expected.machine_key,
                "scope": item.expected.scope,
                "record": item.start_reference,
            },
        )
        for item in ordered_starts
    )
    verified_projection = tuple(
        (
            item.record["workflow_attempt_id"],
            {
                "machine_key": item.expected.machine_key,
                "scope": item.expected.scope,
                "record": item.record_reference,
            },
        )
        for item in tasks
        if item.record is not None and item.record_reference is not None
    )
    projections = (
        (
            "preentry_task_attempt_records",
            tuple((item["workflow_attempt_id"], dict(item)) for item in preentry_tasks),
            "preentry evidence",
        ),
        (
            "task_start_records",
            start_projection,
            "task starts",
        ),
        (
            "verified_tasks",
            verified_projection,
            "verified tasks",
        ),
    )
    historical_integrity, historical_results, historical_reporting = (
        _historical_receipt_evidence_blockers(
            attempts,
            receipts,
            projections,
            reporting,
            reporting_origins,
        )
    )
    return EvidenceInspection(
        tasks=tasks,
        preentry_task_attempt_records=tuple(preentry_tasks),
        task_start_records=tuple(record for _, record in start_projection),
        verified_tasks=tuple(record for _, record in verified_projection),
        missing_tasks=tuple(
            f"{item.expected.machine_key}/{item.expected.scope_id}"
            for item in tasks
            if item.state == "pending"
        ),
        reporting_completion_records=reporting,
        verified_report_locations=locations,
        integrity_blockers=tuple(historical_integrity),
        results_blockers=tuple(
            (*task_blockers, *task_tree_blockers, *historical_results)
        ),
        reporting_blockers=tuple((*reporting_blockers, *historical_reporting)),
    )
