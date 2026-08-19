"""Public dry-run-first control plane for the fixed local CMH pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from norad.contracts.orchestration import api as orchestration_contracts
from norad.orchestration.local_pilot import doctor, inspection, lifecycle
from norad.orchestration.local_pilot.materialization import (
    AttemptPlan,
    MaterializationError,
    build_attempt_plan,
    initialize_run,
    publish_attempt,
)
from norad.orchestration.local_pilot.normalization import (
    NormalizationBundle,
    normalize_request,
)

RUN_DESCRIPTION = (
    "Plan or execute one fixed source-checkout-bound local CMH pipeline. "
    "Dry-run is the default; this command never installs or repairs tools."
)
RESUME_DESCRIPTION = (
    "Plan or resume one failed/interrupted local pilot only from an independently "
    "verified between-task boundary. Dry-run is the default."
)
INSPECT_DESCRIPTION = (
    "Derive one local-pilot run state from immutable NORAD records without "
    "reading or repairing Snakemake metadata."
)


class ControlError(RuntimeError):
    """A public control-plane request is malformed or not currently admissible."""


ReadinessInspector = Callable[[Path, Path, Path], doctor.DoctorResult]
Normalizer = Callable[[Path, Mapping[str, Any] | Path], NormalizationBundle]
RunInspector = Callable[[Path], inspection.RunInspection]
PlanExecutor = Callable[[AttemptPlan], lifecycle.LifecycleOutcome]
PlanTransformer = Callable[[AttemptPlan], AttemptPlan]


@dataclass(frozen=True, slots=True)
class ControlOps:
    """Explicit collaborators for planning, execution, and public adapter tests."""

    inspect_readiness: ReadinessInspector
    normalize: Normalizer
    inspect_run: RunInspector
    execute_plan: PlanExecutor
    transform_plan: PlanTransformer
    now: Callable[[], datetime]
    token: Callable[[], str]


def _default_readiness(
    request: Path, workspace: Path, runtime_profile: Path
) -> doctor.DoctorResult:
    return doctor.inspect_local_pilot(request, workspace, runtime_profile)


def _default_execute(plan: AttemptPlan) -> lifecycle.LifecycleOutcome:
    ops = lifecycle.default_lifecycle_ops()
    if plan.operation == "execute":
        initialize_run(plan, ops=ops)
    return lifecycle.run_materialized_attempt(
        plan.preparation,
        lambda: publish_attempt(plan, ops=ops),
        ops=ops,
    )


DEFAULT_CONTROL_OPS = ControlOps(
    inspect_readiness=_default_readiness,
    normalize=normalize_request,
    inspect_run=inspection.inspect_run,
    execute_plan=_default_execute,
    transform_plan=lambda plan: plan,
    now=lambda: datetime.now(UTC),
    token=lambda: uuid.uuid4().hex,
)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _require_ready(result: doctor.DoctorResult) -> None:
    if result.ready:
        return
    raise ControlError("Local-pilot readiness blockers: " + "; ".join(result.blockers))


def _normalize_after_doctor(
    readiness: doctor.DoctorResult,
    ops: ControlOps,
) -> NormalizationBundle:
    try:
        normalized = ops.normalize(
            readiness.request_path,
            readiness.source_root / "workflow/contracts/local_cmh_v2.json",
        )
    except (OSError, orchestration_contracts.ContractValidationError) as exc:
        raise ControlError(str(exc)) from exc
    if normalized.run_id != readiness.run_id:
        raise ControlError(
            "Readiness and control normalization produced different runs"
        )
    return normalized


def plan_run(
    request: Path,
    workspace: Path,
    runtime_profile: Path,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> AttemptPlan:
    """Plan a new run without writing any workspace state."""

    try:
        readiness = ops.inspect_readiness(request, workspace, runtime_profile)
        _require_ready(readiness)
        normalized = _normalize_after_doctor(readiness, ops)
        plan = ops.transform_plan(
            build_attempt_plan(
                normalized,
                readiness,
                _absolute(workspace),
                operation="execute",
                now=ops.now(),
                token=ops.token(),
            )
        )
    except (doctor.DoctorInputError, MaterializationError) as exc:
        raise ControlError(str(exc)) from exc
    if os.path.lexists(plan.run_root):
        raise ControlError(
            f"Run root already exists; inspect or resume it instead: {plan.run_root}"
        )
    return plan


def _load_config_reference(
    run_root: Path,
    attempt: Mapping[str, Any],
) -> dict[str, Any]:
    reference = attempt["workflow_config"]
    path = run_root / str(reference["path"])
    if path.is_symlink() or not path.is_file():
        raise ControlError(f"Prior workflow config is unavailable: {path}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference["sha256"]:
        raise ControlError("Prior workflow config differs from its attempt reference")
    try:
        value = orchestration_contracts.load_json_object_bytes(data, path)
    except orchestration_contracts.ContractValidationError as exc:
        raise ControlError(str(exc)) from exc
    if orchestration_contracts.canonical_json_bytes(value) != data:
        raise ControlError("Prior workflow config does not use canonical JSON bytes")
    return value


def _retained_dispatches(
    observed: inspection.RunInspection,
) -> dict[tuple[str, str], dict[str, str]]:
    if observed.latest_attempt is None:
        raise ControlError("Resume has no predecessor workflow attempt")
    config = _load_config_reference(observed.run_root, observed.latest_attempt)
    dispatches = config.get("dispatch_paths")
    if not isinstance(dispatches, dict):
        raise ControlError("Prior workflow config has no closed dispatch map")
    retained: dict[tuple[str, str], dict[str, str]] = {}
    for task in observed.tasks:
        if task.state != "verified":
            continue
        try:
            reference = dispatches[task.expected.machine_key][task.expected.scope_id]
        except (KeyError, TypeError) as exc:
            raise ControlError(
                "Prior workflow config omits a reusable verified dispatch: "
                f"{task.expected.machine_key}/{task.expected.scope_id}"
            ) from exc
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ControlError("Prior reusable dispatch reference is malformed")
        path = Path(str(reference["path"]))
        if path.is_symlink() or not path.is_file():
            raise ControlError(f"Reusable dispatch is unavailable: {path}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
            raise ControlError(f"Reusable dispatch bytes changed: {path}")
        retained[(task.expected.machine_key, task.expected.scope_id)] = dict(reference)
    return retained


def plan_resume(
    run_root: Path,
    runtime_profile: Path,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> AttemptPlan:
    """Plan a safe between-task resume without writing run state."""

    root = _absolute(run_root)
    try:
        observed = ops.inspect_run(root)
    except (OSError, inspection.InspectionError) as exc:
        raise ControlError(str(exc)) from exc
    if observed.local_pipeline_complete:
        raise ControlError("Completed local-pilot run refuses resume")
    if not observed.resume_available or observed.latest_attempt is None:
        raise ControlError(
            "Run is not at an admissible between-task resume boundary: "
            + "; ".join(observed.blockers or (observed.state,))
        )
    previous = observed.latest_attempt
    request = Path(str(previous["authored_paths"]["request"]))
    workspace = Path(str(previous["workspace"]))
    try:
        readiness = ops.inspect_readiness(request, workspace, runtime_profile)
        _require_ready(readiness)
        normalized = _normalize_after_doctor(readiness, ops)
        if normalized.run_id != observed.run_id:
            raise ControlError("Current authored request resolves to a different run")
        fixed_execution = root / "contract/normalized.json"
        if (
            fixed_execution.is_symlink()
            or not fixed_execution.is_file()
            or fixed_execution.read_bytes() != normalized.normalized_bytes
        ):
            raise ControlError("Current normalization differs from immutable run bytes")
        plan = ops.transform_plan(
            build_attempt_plan(
                normalized,
                readiness,
                workspace,
                operation="resume",
                now=ops.now(),
                token=ops.token(),
                supersedes_workflow_attempt_id=str(previous["workflow_attempt_id"]),
                retained_dispatches=_retained_dispatches(observed),
            )
        )
    except (doctor.DoctorInputError, MaterializationError) as exc:
        raise ControlError(str(exc)) from exc
    if plan.run_root != root:
        raise ControlError("Resume workspace resolves to a different run root")
    for field in (
        "run_id",
        "execution_contract_sha256",
        "profile_sha256",
        "source_checkout",
        "required_tools",
        "execution_mode",
        "executor",
    ):
        if plan.attempt_record[field] != previous[field]:
            raise ControlError(f"Resume is incompatible with predecessor on {field}")
    return plan


def execute_plan(plan: AttemptPlan, *, ops: ControlOps = DEFAULT_CONTROL_OPS) -> int:
    """Execute one already-rendered plan through its explicit lifecycle adapter."""

    try:
        outcome = ops.execute_plan(plan)
    except (MaterializationError, lifecycle.LifecycleError, OSError) as exc:
        raise ControlError(str(exc)) from exc
    status = str(outcome.receipt["status"])
    print(f"Attempt receipt: {outcome.receipt_path}")
    print(f"Attempt status: {status}")
    if outcome.receipt["blockers"]:
        for blocker in outcome.receipt["blockers"]:
            print(f"BLOCKER: {blocker}")
    return 0 if status == "succeeded" else 1


def _print_plan(plan: AttemptPlan) -> None:
    new_dispatches = plan.new_dispatch_files
    reused = plan.dispatch_count - len(new_dispatches)
    print(f"Operation: {plan.operation}")
    print(f"Run ID: {plan.normalized.run_id}")
    print(f"Run root: {plan.run_root}")
    print(f"Workflow attempt: {plan.workflow_attempt_id}")
    print(f"Owner jobs: {plan.dispatch_count}")
    print("Step thread allocations:")
    for step_id, threads in plan.step_threads:
        print(f"  Step {step_id}: {threads}")
    print(f"Total workflow cores: {plan.workflow_cores}")
    print(f"Maximum concurrent sample tasks: {plan.sample_concurrency}")
    print("Reporting transactions: 3")
    print(f"Reusable completed owner jobs: {reused}")
    print(f"Pending owner jobs: {plan.dispatch_count - reused}")
    print("Snakemake command: " + shlex.join(plan.attempt_record["snakemake_argv"]))
    for item in new_dispatches:
        record = orchestration_contracts.load_json_object_bytes(item.data, item.path)
        print(
            f"TASK {record['machine_key']}/{record['scope']['scope_id']} producer: "
            + shlex.join(record["producer_argv"])
        )
        print(
            f"TASK {record['machine_key']}/{record['scope']['scope_id']} validator: "
            + shlex.join(record["validator_argv"])
        )
    print(
        "Evidence boundary: this plan or execution proves only the admitted local "
        "workflow layer; it is not cluster, production, scientific-review, or "
        "biological proof."
    )


def configure_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--runtime-profile", required=True, type=Path)
    parser.add_argument(
        "--allocated-cores",
        type=_positive_integer,
        help=(
            "Optional scheduler-allocation assertion; fails if the request's "
            "workflow_cores exceeds this value."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create and execute the planned run. Without this flag, write nothing.",
    )


def configure_resume_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--runtime-profile", required=True, type=Path)
    parser.add_argument(
        "--allocated-cores",
        type=_positive_integer,
        help=(
            "Optional scheduler-allocation assertion; fails if the request's "
            "workflow_cores exceeds this value."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the safe resume. Without this flag, write nothing.",
    )


def configure_inspect_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-root", required=True, type=Path)


def run_from_args(
    arguments: argparse.Namespace,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    try:
        plan = plan_run(
            arguments.request,
            arguments.workspace,
            arguments.runtime_profile,
            ops=ops,
        )
        allocated_cores = getattr(arguments, "allocated_cores", None)
        if allocated_cores is not None and plan.workflow_cores > allocated_cores:
            raise ControlError(
                "Request workflow_cores exceeds the declared scheduler allocation: "
                f"{plan.workflow_cores} > {allocated_cores}"
            )
        _print_plan(plan)
        if not arguments.execute:
            print("Dry-run complete; no workspace state was written.")
            return 0
        return execute_plan(plan, ops=ops)
    except ControlError as exc:
        print(f"norad: error: {exc}", file=sys.stderr)
        return 2


def resume_from_args(
    arguments: argparse.Namespace,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    try:
        plan = plan_resume(
            arguments.run_root,
            arguments.runtime_profile,
            ops=ops,
        )
        allocated_cores = getattr(arguments, "allocated_cores", None)
        if allocated_cores is not None and plan.workflow_cores > allocated_cores:
            raise ControlError(
                "Request workflow_cores exceeds the declared scheduler allocation: "
                f"{plan.workflow_cores} > {allocated_cores}"
            )
        _print_plan(plan)
        if not arguments.execute:
            print("Dry-run complete; no resume state was written.")
            return 0
        return execute_plan(plan, ops=ops)
    except ControlError as exc:
        print(f"norad: error: {exc}", file=sys.stderr)
        return 2


def inspect_from_args(
    arguments: argparse.Namespace,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    try:
        observed = ops.inspect_run(_absolute(arguments.run_root))
    except (OSError, inspection.InspectionError) as exc:
        print(f"norad: error: {exc}", file=sys.stderr)
        return 2
    print(f"Run ID: {observed.run_id}")
    print(f"Run root: {observed.run_root}")
    print(f"State: {observed.state}")
    print(f"Latest workflow attempt: {observed.latest_workflow_attempt_id or 'none'}")
    for task in observed.tasks:
        print(
            f"TASK {task.expected.machine_key}/{task.expected.scope_id}: {task.state}"
        )
        if task.blocker:
            print(f"  BLOCKER: {task.blocker}")
    for kind, records in observed.reporting_completion_records.items():
        state = "verified" if records["verified"] is not None else "pending"
        print(f"REPORTING {kind}: {state}")
    for blocker in observed.blockers:
        print(f"BLOCKER: {blocker}")
    print(f"Resume available: {'yes' if observed.resume_available else 'no'}")
    print(
        "Local pipeline complete: "
        + ("yes" if observed.local_pipeline_complete else "no")
    )
    return 0


__all__ = (
    "ControlError",
    "ControlOps",
    "DEFAULT_CONTROL_OPS",
    "INSPECT_DESCRIPTION",
    "RESUME_DESCRIPTION",
    "RUN_DESCRIPTION",
    "configure_inspect_parser",
    "configure_resume_parser",
    "configure_run_parser",
    "execute_plan",
    "inspect_from_args",
    "plan_resume",
    "plan_run",
    "resume_from_args",
    "run_from_args",
)
