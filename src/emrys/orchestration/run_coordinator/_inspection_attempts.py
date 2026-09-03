"""Immutable Attempt-chain and per-Attempt task-tree inspection."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import validate_successor_run
from emrys.orchestration.run_coordinator._inspection_admission import (
    InspectionError,
    SuccessorRunAuthority,
    _read_bytes,
    _record_reference,
    _reference_for_bytes,
    _stable_directory_entries,
    admit_attempt_run_lock,
    admit_canonical_record,
    admit_successor_run,
    expected_tasks,
)

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
        if (
            "released-run-lock.json" in child_names
            and "attempt-receipt.json" not in child_names
        ):
            blockers.append(
                "Released run-lock evidence exists without a terminal receipt: "
                f"{entry / 'released-run-lock.json'}"
            )
    return tuple(entries), tuple(blockers)


def attempt_fields(successor: bool) -> tuple[str, ...]:
    """Return fields that must remain equal across Attempts for one Run format."""

    common = ("run_id", "execution_contract_sha256", "profile_sha256")
    attempt_semantics = ("execution_mode", "executor")
    if successor:
        return (*common, *attempt_semantics)
    return (*common, "source_checkout", "required_tools", *attempt_semantics)


def inspect_attempt_chain(
    root: Path,
    *,
    authority: SuccessorRunAuthority | None = None,
    profile: Mapping[str, Any] | None = None,
) -> tuple[
    tuple[dict[str, Any], ...],
    dict[str, dict[str, Any]],
    list[str],
]:
    if authority is None:
        authority = admit_successor_run(root)
    successor_format = authority is not None
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
        if attempt_path.parent.name != identifier:
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
        for field in attempt_fields(successor_format):
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
        config_reference = attempt["workflow_config"]
        raw_config_path = config_reference["path"]
        expected_config_path = (
            Path("contract") / "workflow-configs" / f"{identifier}.json"
        ).as_posix()
        if raw_config_path != expected_config_path:
            blockers.append(
                f"Workflow attempt config path is not attempt-specific: {identifier}"
            )
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
                "execution_path": str(
                    root
                    / "contract"
                    / ("run.json" if successor_format else "normalized.json")
                ),
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
            if authority is not None and profile is not None:
                try:
                    validate_successor_run(
                        analysis=authority.analysis_revision,
                        plan=authority.execution_plan,
                        run=authority.run_binding,
                        profile=profile,
                        attempt=attempt,
                        resource_policy=config_document["resource_policy"],
                    )
                except (
                    KeyError,
                    orchestration_contracts.ContractValidationError,
                ) as exc:
                    blockers.append(
                        "Workflow Attempt differs from immutable Run: "
                        f"{identifier}: {exc}"
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
        attempt_path = root / "attempts" / identifier / "attempt.json"
        expected_reference = attempt_references[identifier]
        try:
            admit_attempt_run_lock(root, attempt, require_active=False)
        except InspectionError as exc:
            blockers.append(str(exc))
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
) -> tuple[list[dict[str, Any]], list[str]]:
    from emrys.orchestration.run_coordinator import task  # noqa: PLC0415

    """Close all historical task trees and bind exact preentry diagnostics."""

    expected = {
        (item.machine_key, item.scope_id): item
        for item in expected_tasks(authority or execution, profile)
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
        for owner_path in owner_paths:
            if owner_path.is_symlink() or not owner_path.is_dir():
                blockers.append(
                    f"Attempt task owner is not a real directory: {owner_path}"
                )
                continue
            scope_paths = tuple(owner_path.iterdir())
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
                try:
                    record, record_reference = task._admit_task_attempt(
                        run_root=root,
                        execution=execution,
                        profile=profile,
                        workflow_attempt_id=identifier,
                        machine_key=item.machine_key,
                        scope=item.scope,
                    )
                    start_path = (
                        root
                        / "state"
                        / "task-starts"
                        / item.machine_key
                        / f"{item.scope_id}.json"
                    )
                    if record["task_start_record"] is None:
                        if start_path.exists() or start_path.is_symlink():
                            start = task.validate_task_start(
                                start_path,
                                run_root=root,
                                execution=execution,
                                profile=profile,
                                machine_key=item.machine_key,
                                scope=item.scope,
                            )
                            later_origin = str(start["workflow_attempt_id"])
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
                                "record": record_reference,
                            }
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
