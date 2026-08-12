"""Materialize one no-science fixture for the fixed Snakemake projection."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from norad.contracts.orchestration import api as orchestration_contracts
from norad.orchestration.local_pilot.normalization import normalize_request
from tests.orchestration.local_pilot.fixture import build as build_intake

REPO_ROOT = Path(__file__).resolve().parents[4]
PROFILE_PATH = REPO_ROOT / "workflow" / "contracts" / "local_cmh_v1.json"
SNAKEFILE = REPO_ROOT / "workflow" / "Snakefile"
TASK_DOUBLE = Path(__file__).with_name("task_double.py").resolve()


@dataclass(frozen=True, slots=True)
class WorkflowFixture:
    """Paths and identities for one isolated workflow test run."""

    root: Path
    run_root: Path
    config_path: Path
    execution: dict[str, Any]
    profile: dict[str, Any]
    dispatch_paths: dict[str, dict[str, str]]

    @property
    def verified_root(self) -> Path:
        return self.run_root / "state" / "verified"


def _scope_ids(task: dict[str, Any], execution: dict[str, Any]) -> tuple[str, ...]:
    selector = task["scope_selector"]
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
    raise AssertionError(f"Fixture cannot execute selector {selector!r}")


def _task_attempt_id(index: int) -> str:
    suffix = hashlib.sha256(f"fixture-task-{index}".encode()).hexdigest()[:32]
    return f"task-20260812T120100Z-{suffix}"


def _write_dispatch(
    *,
    path: Path,
    run_root: Path,
    execution_path: Path,
    task: dict[str, Any],
    scope_id: str,
    index: int,
    fixture_input: Path,
) -> dict[str, Any]:
    machine_key = str(task["machine_key"])
    step_id = str(task["step_id"])
    native_output = (
        run_root / "results" / "test-double" / machine_key / f"{scope_id}.txt"
    )
    validation_report = (
        run_root / "results" / "qc" / "validation" / step_id / f"{scope_id}.tsv"
    )
    attempt_root = run_root / "attempts" / "workflow-test" / machine_key
    task_attempt = attempt_root / f"{scope_id}.attempt.json"
    verified = run_root / "state" / "verified" / machine_key / f"{scope_id}.json"
    stdout = attempt_root / f"{scope_id}.stdout.log"
    stderr = attempt_root / f"{scope_id}.stderr.log"
    for parent in {
        path.parent,
        task_attempt.parent,
        verified.parent,
        stdout.parent,
        stderr.parent,
    }:
        parent.mkdir(parents=True, exist_ok=True)
    producer = [
        sys.executable,
        "-I",
        str(TASK_DOUBLE),
        "producer",
        "--output",
        f"native_output={native_output}",
    ]
    validator = [
        sys.executable,
        "-I",
        str(TASK_DOUBLE),
        "validator",
        "--report",
        str(validation_report),
        "--step-id",
        step_id,
        "--scope-id",
        scope_id,
    ]
    record = {
        "schema_version": "norad.local-task-dispatch.v1",
        "run_root": str(run_root),
        "execution_path": str(execution_path),
        "profile_path": str(run_root / "contract" / "profile.json"),
        "workflow_attempt_id": "workflow-20260812T120000Z-" + "a" * 32,
        "task_attempt_id": _task_attempt_id(index),
        "owner_run_token": f"test-owner-{index:03d}",
        "machine_key": machine_key,
        "scope": {
            "scope_type": str(task["scope_type"]),
            "scope_id": scope_id,
        },
        "producer_argv": producer,
        "validator_argv": validator,
        "inputs": [{"role": "fixture_input", "path": str(fixture_input)}],
        "outputs": [{"role": "native_output", "path": str(native_output)}],
        "validation_report_path": str(validation_report),
        "native_receipt_path": None,
        "task_attempt_path": str(task_attempt),
        "verified_task_path": str(verified),
        "stdout_path": str(stdout),
        "stderr_path": str(stderr),
    }
    path.write_bytes(orchestration_contracts.canonical_json_bytes(record))
    return record


def build(root: Path) -> WorkflowFixture:
    """Build an immutable normalized contract plus pre-materialized dispatches."""

    root.mkdir(parents=True, exist_ok=True)
    intake_root = root / "intake"
    intake_root.mkdir()
    request_path = build_intake(intake_root)
    profile = orchestration_contracts.load_json_object(PROFILE_PATH)
    normalized = normalize_request(request_path, profile)
    execution = normalized.execution_contract

    run_root = (root / "run").resolve()
    contract_root = run_root / "contract"
    contract_root.mkdir(parents=True)
    execution_path = contract_root / "normalized.json"
    execution_path.write_bytes(normalized.normalized_bytes)
    profile_snapshot = contract_root / "profile.json"
    profile_snapshot.write_bytes(orchestration_contracts.canonical_json_bytes(profile))
    fixture_input = run_root / "contract" / "fixture_input.txt"
    fixture_input.write_text("bounded no-science workflow fixture\n", encoding="utf-8")

    dispatch_paths: dict[str, dict[str, str]] = {}
    index = 0
    for task in profile["owner_tasks"]:
        machine_key = str(task["machine_key"])
        if machine_key not in profile["required_owner_keys"]:
            continue
        by_scope: dict[str, str] = {}
        for scope_id in _scope_ids(task, execution):
            index += 1
            dispatch_path = (
                run_root
                / "attempts"
                / "workflow-test"
                / "dispatch"
                / machine_key
                / f"{scope_id}.json"
            )
            _write_dispatch(
                path=dispatch_path,
                run_root=run_root,
                execution_path=execution_path,
                task=task,
                scope_id=scope_id,
                index=index,
                fixture_input=fixture_input,
            )
            by_scope[scope_id] = str(dispatch_path)
        dispatch_paths[machine_key] = by_scope

    config = {
        "run_root": str(run_root),
        "execution_path": str(execution_path),
        "profile_path": str(profile_snapshot),
        "dispatch_paths": dispatch_paths,
    }
    config_path = root / "workflow-config.json"
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return WorkflowFixture(
        root=root,
        run_root=run_root,
        config_path=config_path,
        execution=execution,
        profile=profile,
        dispatch_paths=dispatch_paths,
    )


__all__ = (
    "PROFILE_PATH",
    "REPO_ROOT",
    "SNAKEFILE",
    "TASK_DOUBLE",
    "WorkflowFixture",
    "build",
)
