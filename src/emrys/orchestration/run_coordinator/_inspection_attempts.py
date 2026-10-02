"""Immutable Attempt-chain and per-Attempt task-tree inspection."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import validate_successor_run
from emrys.orchestration.run_coordinator._inspection_admission import (
    ExpectedTask,
    InspectionError,
    PreparedFinalizationCandidate,
    SuccessorRunAuthority,
    _read_bytes,
    _record_reference,
    _reference_for_bytes,
    _stable_directory_entries,
    admit_attempt_run_lock,
    admit_canonical_record,
    admit_prepared_finalization,
    admit_successor_run,
    expected_tasks,
)

_WORKFLOW_ATTEMPT_NAME_RE = re.compile(r"^workflow-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}$")
_ATTEMPT_CHILD_NAMES = frozenset(
    {
        "attempt.json",
        "attempt-receipt.json",
        "prepared-attempt-receipt.json",
        "released-run-lock.json",
        "request.yaml",
        "tasks",
    }
)


@dataclass(frozen=True, slots=True)
class TaskAttemptObservation:
    """One admitted terminal record and its exact reference, without Results authority."""

    record: dict[str, Any]
    record_reference: dict[str, str]


@dataclass(frozen=True, slots=True)
class TaskHistoryEntry:
    """One admitted per-Attempt scope, including an active incomplete entry."""

    expected: ExpectedTask
    workflow_attempt_id: str
    start_record: dict[str, Any] | None
    start_reference: dict[str, str] | None
    terminal: TaskAttemptObservation | None


def inspect_attempt_tree(root: Path) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    """Inspect the exact aggregate attempt-directory roster without mutation."""

    attempts_root = root / "attempts"
    try:
        observed_entries = tuple(
            attempts_root / name
            for name in _stable_directory_entries(
                attempts_root, root, "aggregate attempts root"
            )
        )
    except InspectionError as exc:
        return (), (str(exc),)

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
        child_names = {child.name for child in children}
        blockers.extend(
            f"Unexpected workflow-attempt state path: {child}"
            for child in children
            if child.name not in _ATTEMPT_CHILD_NAMES
        )
        if "released-run-lock.json" in child_names and not child_names.intersection(
            {"attempt-receipt.json", "prepared-attempt-receipt.json"}
        ):
            blockers.append(
                "Released run-lock evidence exists without a prepared or final "
                "terminal receipt: "
                f"{entry / 'released-run-lock.json'}"
            )
    return tuple(entries), tuple(blockers)


def attempt_fields() -> tuple[str, ...]:
    """Return the fields that remain equal across Attempts of one Run."""

    return (
        "run_id",
        "execution_contract_sha256",
        "profile_sha256",
        "execution_mode",
        "executor",
    )


def inspect_attempt_chain(
    root: Path,
    *,
    authority: SuccessorRunAuthority | None = None,
    profile: Mapping[str, Any] | None = None,
    prospective_receipt: PreparedFinalizationCandidate | None = None,
) -> tuple[
    tuple[dict[str, Any], ...],
    dict[str, dict[str, Any]],
    list[str],
]:
    if authority is None:
        authority = admit_successor_run(root)
    records: dict[str, dict[str, Any]] = {}
    attempt_references: dict[str, dict[str, str]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    attempt_entries, attempt_tree_blockers = inspect_attempt_tree(root)
    blockers = list(attempt_tree_blockers)
    for entry in attempt_entries:
        attempt_path = entry / "attempt.json"
        try:
            record, attempt_data = admit_canonical_record(
                attempt_path, root, "workflow-attempt"
            )
        except InspectionError as exc:
            blockers.append(str(exc))
            continue
        identifier = str(record["workflow_attempt_id"])
        if (
            attempt_path.parent.name != identifier
            or root != Path(record["workspace"]) / "runs" / record["run_id"]
        ):
            blockers.append(
                f"Workflow attempt directory does not match record identity: {attempt_path}"
            )
            continue
        records[identifier] = record
        attempt_references[identifier] = _reference_for_bytes(
            attempt_path, root, attempt_data
        )
        receipt_path = attempt_path.with_name("attempt-receipt.json")
        if receipt_path.exists() or receipt_path.is_symlink():
            try:
                receipt, _ = admit_canonical_record(
                    receipt_path, root, "attempt-receipt"
                )
            except InspectionError as exc:
                blockers.append(str(exc))
            else:
                receipts[identifier] = receipt

    if blockers:
        return (
            tuple(records.values()),
            receipts,
            blockers,
        )
    if not records:
        return (), receipts, blockers
    roots = [
        item
        for item in records.values()
        if item["supersedes_workflow_attempt_id"] is None
    ]
    if len(roots) != 1 or roots[0]["operation"] != "execute":
        blockers.append("Workflow attempt chain must have one execute root")
        return (
            tuple(records.values()),
            receipts,
            blockers,
        )
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
        next_attempt = ordered[index + 1]
        for field in attempt_fields():
            if next_attempt[field] != attempt[field]:
                blockers.append(
                    f"Adjacent workflow attempts differ on {field}: {identifier}"
                )
        try:
            predecessor_finished = datetime.fromisoformat(
                str(predecessor_receipt["finished_at"]).replace("Z", "+00:00")
            )
            successor_created = datetime.fromisoformat(
                str(next_attempt["created_at"]).replace("Z", "+00:00")
            )
        except ValueError:
            blockers.append(
                f"Workflow attempt chain has invalid timestamps: {identifier}"
            )
        else:
            if successor_created < predecessor_finished:
                blockers.append(
                    f"Resume attempt predates predecessor completion: {identifier}"
                )
    latest_id = str(ordered[-1]["workflow_attempt_id"])
    for attempt in ordered[:-1]:
        identifier = str(attempt["workflow_attempt_id"])
        prepared_path = root / "attempts" / identifier / "prepared-attempt-receipt.json"
        if prepared_path.exists() or prepared_path.is_symlink():
            blockers.append(
                f"Non-latest workflow attempt retains prepared finalization: {identifier}"
            )
    if prospective_receipt is not None:
        candidate_id = str(prospective_receipt.record["workflow_attempt_id"])
        if candidate_id != latest_id:
            blockers.append("Prepared finalization does not bind the latest Attempt")
        else:
            try:
                current = admit_prepared_finalization(root, ordered[-1])
            except InspectionError as exc:
                blockers.append(str(exc))
            else:
                if current != prospective_receipt:
                    blockers.append("Prepared finalization changed during inspection")
                receipts[latest_id] = prospective_receipt.record
    for attempt in ordered:
        identifier = str(attempt["workflow_attempt_id"])
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
        if profile is not None:
            try:
                validate_successor_run(
                    analysis=authority.analysis_revision,
                    plan=authority.execution_plan,
                    run=authority.run_binding,
                    profile=profile,
                    attempt=attempt,
                    resource_policy=attempt["workflow"]["resource_policy"],
                )
            except (
                KeyError,
                orchestration_contracts.ContractValidationError,
            ) as exc:
                blockers.append(
                    f"Workflow Attempt differs from immutable Run: {identifier}: {exc}"
                )
        receipt = receipts.get(identifier)
        if receipt is not None:
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
            try:
                if prospective_receipt is None or identifier != str(
                    prospective_receipt.record["workflow_attempt_id"]
                ):
                    admit_attempt_run_lock(root, attempt, require_active=False)
            except InspectionError as exc:
                blockers.append(str(exc))
        attempt_path = root / "attempts" / identifier / "attempt.json"
        expected_reference = attempt_references[identifier]
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
    return (
        tuple(ordered),
        receipts,
        blockers,
    )


def inspect_attempt_task_trees(
    root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    *,
    allow_incomplete_origin: str | None = None,
    authority: SuccessorRunAuthority | None = None,
    selected_task: tuple[str, str] | None = None,
) -> tuple[tuple[TaskHistoryEntry, ...], tuple[str, ...]]:
    """Admit each exact per-Attempt task tree once, without retry freshness checks."""

    from emrys.orchestration.run_coordinator import task  # noqa: PLC0415

    expected = {
        (item.machine_key, item.scope_id): item
        for item in expected_tasks(authority or admit_successor_run(root), profile)
    }
    entries: list[TaskHistoryEntry] = []
    blockers: list[str] = []
    for attempt in attempts:
        identifier = str(attempt["workflow_attempt_id"])
        tasks_root = root / "attempts" / identifier / "tasks"
        if not tasks_root.exists() and not tasks_root.is_symlink():
            continue
        if tasks_root.is_symlink() or not tasks_root.is_dir():
            blockers.append(f"Attempt task root is not a real directory: {tasks_root}")
            continue
        for owner_path in tasks_root.iterdir():
            if selected_task is not None and owner_path.name != selected_task[0]:
                continue
            if owner_path.is_symlink() or not owner_path.is_dir():
                blockers.append(
                    f"Attempt task owner is not a real directory: {owner_path}"
                )
                continue
            for scope_path in owner_path.iterdir():
                if selected_task is not None and scope_path.name != selected_task[1]:
                    continue
                item = expected.get((owner_path.name, scope_path.name))
                if item is None:
                    blockers.append(f"Unexpected attempt task scope: {scope_path}")
                    continue
                if scope_path.is_symlink() or not scope_path.is_dir():
                    blockers.append(
                        f"Attempt task scope is not a real directory: {scope_path}"
                    )
                    continue
                start_record = None
                start_reference = None
                terminal = None
                try:
                    definition = attempt["tasks"][item.machine_key][item.scope_id]
                    if "workflow_attempt_record" in definition:
                        raise InspectionError(
                            "Retained task owns a new attempt task tree"
                        )
                    children = {child.name for child in scope_path.iterdir()}
                    allowed = {
                        "task-start.json",
                        "task-attempt.json",
                        "stdout.log",
                        "stderr.log",
                    }
                    start_path = scope_path / "task-start.json"
                    if "task-start.json" in children:
                        admitted_start = task.validate_task_start(
                            start_path,
                            run_root=root,
                            execution=execution,
                            profile=profile,
                            machine_key=item.machine_key,
                            scope=item.scope,
                        )
                        admitted_reference = _record_reference(
                            start_path, root, "task start"
                        )
                        if admitted_reference[
                            "sha256"
                        ] != orchestration_contracts.canonical_sha256(admitted_start):
                            raise InspectionError("Task start changed during admission")
                        if admitted_start["workflow_attempt_id"] != identifier:
                            raise InspectionError(
                                "Task start belongs to another Attempt"
                            )
                        start_record = admitted_start
                        start_reference = admitted_reference
                    if not children <= allowed:
                        raise InspectionError("Task scope contains unexpected state")
                    if any(
                        (scope_path / name).is_symlink()
                        or not (scope_path / name).is_file()
                        for name in children
                    ):
                        raise InspectionError("Task state is not a regular file")
                    if "task-attempt.json" in children:
                        record, reference = task._admit_task_attempt(
                            run_root=root,
                            execution=execution,
                            profile=profile,
                            workflow_attempt_id=identifier,
                            machine_key=item.machine_key,
                            scope=item.scope,
                        )
                        exact = {"task-attempt.json", "stdout.log", "stderr.log"}
                        if record["task_start_record"] is not None:
                            exact.add("task-start.json")
                        if (
                            children != exact
                            or record["task_start_record"] != start_reference
                        ):
                            raise InspectionError(
                                "Task terminal does not close its exact entry tree"
                            )
                        terminal = TaskAttemptObservation(record, reference)
                    elif identifier != allow_incomplete_origin:
                        blockers.append(
                            f"Could not close attempt task state {scope_path}: "
                            "Task scope has no terminal result"
                        )
                except Exception as exc:
                    blockers.append(
                        f"Could not close attempt task state {scope_path}: {exc}"
                    )
                    if start_reference is None:
                        continue
                entries.append(
                    TaskHistoryEntry(
                        item, identifier, start_record, start_reference, terminal
                    )
                )
    return tuple(entries), tuple(blockers)
