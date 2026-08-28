"""Public dry-run-first control plane for the fixed local CMH pilot."""

from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import sys
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.application_logging import (
    ApplicationLogError,
    AttemptIdentity,
    LogControlError,
    LogControls,
    LogLevel,
    add_log_arguments,
    event,
    field,
    open_attempt_log,
    render_failure_summary,
    resolve_log_controls,
)
from emrys.libraries.source_authority import SourceCheckout
from emrys.orchestration.local_pilot import capacity, doctor, inspection, lifecycle
from emrys.orchestration.local_pilot.execution_profile import (
    ExecutionProfile,
    ExecutionProfileError,
    SlurmPlacement,
    load_execution_profile,
)
from emrys.orchestration.local_pilot.materialization import (
    AttemptPlan,
    HistoricalRun,
    MaterializationError,
    admit_run,
    build_attempt_plan,
    build_run_candidate,
    publish_attempt,
    validate_run_destination,
)
from emrys.orchestration.local_pilot.normalization import (
    NormalizationBundle,
    normalize_request,
)
from emrys.orchestration.local_pilot.resource_policy import (
    AllocationCapacity,
    ResourceConfigError,
    ResourceOverrides,
    add_resource_override_arguments,
    admit_resource_policy_record,
    overrides_from_args,
    resource_override_argv,
    resolve_resource_policy,
    resume_resource_policy,
    resume_resource_plan,
)
from emrys.orchestration.local_pilot import slurm_submission

RUN_DESCRIPTION = (
    "Plan or execute one fixed source-checkout-bound local CMH pipeline. "
    "Dry-run is the default; this command never installs or repairs tools."
)
RESUME_DESCRIPTION = (
    "Plan or resume one failed/interrupted local pilot only from an independently "
    "verified between-task boundary. Dry-run is the default."
)
INSPECT_DESCRIPTION = (
    "Derive one local-pilot run state from immutable EMRYS records without "
    "reading or repairing Snakemake metadata."
)
_MILESTONE_STEPS = (
    ("Preparation", ("00a", "00b", "00c")),
    ("Alignment and sample processing", ("01", "02", "04", "05", "06")),
    ("QC evidence", ("02b", "03")),
    ("Candidate evidence", ("07", "08")),
    ("Statistical/context processing", ("09", "10")),
)


class ControlError(RuntimeError):
    """A public control-plane request is malformed or not currently admissible."""

    def __init__(self, message: str, *, reported: bool = False) -> None:
        super().__init__(message)
        self.reported = reported


ReadinessInspector = Callable[[Path, Path, Path], doctor.DoctorResult]
Normalizer = Callable[[Path, Mapping[str, Any] | Path], NormalizationBundle]
RunInspector = Callable[[Path], inspection.RunInspection]
ApplicationEventObserver = Callable[[str], None]
PlanExecutor = Callable[
    [AttemptPlan, ApplicationEventObserver], lifecycle.LifecycleOutcome
]
PlanBuilder = Callable[[], AttemptPlan]
PlanTransformer = Callable[[AttemptPlan], AttemptPlan]
AllocationObserver = Callable[[], AllocationCapacity]


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
    observe_allocation: AllocationObserver = capacity.observe_allocation


def _default_readiness(
    request: Path, workspace: Path, runtime_profile: Path
) -> doctor.DoctorResult:
    return doctor.inspect_local_pilot(request, workspace, runtime_profile)


def _default_execute(
    plan: AttemptPlan,
    observe_application_event: ApplicationEventObserver,
) -> lifecycle.LifecycleOutcome:
    ops = replace(
        lifecycle.default_lifecycle_ops(),
        observe_application_event=observe_application_event,
    )
    if plan.operation == "execute":
        admit_run(plan, ops=ops)
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


def _require_ready(result: doctor.DoctorResult) -> None:
    if result.ready:
        return
    details = [*result.blockers]
    details.extend(f"REMEDIATION: {value}" for value in result.remediations)
    raise ControlError("Local-pilot readiness blockers: " + "; ".join(details))


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
    return normalized


def _plan_run(
    request: Path,
    workspace: Path,
    runtime_profile: Path,
    *,
    execution_profile: ExecutionProfile,
    scheduler_job_id: str | None = None,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> AttemptPlan:
    """Plan a new run without writing any workspace state."""

    try:
        readiness = ops.inspect_readiness(request, workspace, runtime_profile)
        _require_ready(readiness)
        normalized = _normalize_after_doctor(readiness, ops)
        policy = execution_profile.resource_policy
        run = build_run_candidate(normalized, readiness, policy.declaration)
        resources = resolve_resource_policy(policy, ops.observe_allocation())
        plan = ops.transform_plan(
            build_attempt_plan(
                run,
                readiness,
                _absolute(workspace),
                resources=resources,
                operation="execute",
                now=ops.now(),
                token=ops.token(),
                placement=execution_profile.attempt_placement(scheduler_job_id),
            )
        )
    except (
        doctor.DoctorInputError,
        MaterializationError,
        ResourceConfigError,
        ExecutionProfileError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        raise ControlError(str(exc)) from exc
    try:
        validate_run_destination(
            plan.run_root,
            candidate=plan.run if not isinstance(plan.run, HistoricalRun) else None,
        )
    except MaterializationError as exc:
        raise ControlError(str(exc)) from exc
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


def _plan_resume(
    run_root: Path,
    runtime_profile: Path,
    *,
    execution_profile: ExecutionProfile,
    profile_resources_explicit: bool,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
    scheduler_job_id: str | None = None,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> AttemptPlan:
    """Plan a safe between-task resume without writing run state."""

    root = _absolute(run_root)
    try:
        observed = ops.inspect_run(root)
    except (OSError, inspection.InspectionError) as exc:
        raise ControlError(str(exc)) from exc
    if not observed.recovery_available or observed.latest_attempt is None:
        raise ControlError(
            "Run is not at an admissible between-task resume boundary: "
            + "; ".join(
                observed.blockers
                or (
                    f"Attempt outcome is {observed.attempt_outcome}",
                    f"Results are {observed.results_status}",
                )
            )
        )
    previous = observed.latest_attempt
    request = Path(str(previous["authored_paths"]["request"]))
    workspace = Path(str(previous["workspace"]))
    try:
        readiness = ops.inspect_readiness(request, workspace, runtime_profile)
        _require_ready(readiness)
        normalized = _normalize_after_doctor(readiness, ops)
        predecessor_config = _load_config_reference(root, previous)
        if observed.authority_format == "successor":
            if (
                observed.analysis_revision is None
                or observed.execution_plan is None
                or observed.run_binding is None
            ):
                raise ControlError("Successor inspection omitted immutable Run records")
            if profile_resources_explicit:
                policy = execution_profile.resource_policy
            else:
                prior = predecessor_config.get("resource_policy")
                if not isinstance(prior, dict):
                    raise ControlError("Prior workflow config has no resource policy")
                policy = resume_resource_policy(
                    admit_resource_policy_record(
                        prior,
                        require_symbolic=True,
                    ).policy,
                    overrides=resource_overrides,
                )
                execution_profile = replace(
                    execution_profile,
                    resource_policy=policy,
                )
            candidate = build_run_candidate(normalized, readiness, policy.declaration)
            if candidate.run_binding.canonical_bytes != observed.run_binding.canonical_bytes:
                raise ControlError("Current inputs resolve to a different Run")
            run = candidate
            resources = resolve_resource_policy(policy, ops.observe_allocation())
        else:
            legacy_execution, legacy_bytes = normalized.historical_execution_v1()
            fixed_execution = root / "contract/normalized.json"
            if legacy_execution["run_id"] != observed.run_id:
                raise ControlError("Current authored request resolves to a different run")
            if (
                fixed_execution.is_symlink()
                or not fixed_execution.is_file()
                or fixed_execution.read_bytes() != legacy_bytes
            ):
                raise ControlError("Current normalization differs from immutable run bytes")
            if profile_resources_explicit:
                resources = resolve_resource_policy(
                    execution_profile.resource_policy,
                    ops.observe_allocation(),
                )
            else:
                prior_record = predecessor_config.get("resource_policy")
                if not isinstance(prior_record, dict):
                    raise ControlError("Prior workflow config has no resource policy")
                resources = resume_resource_plan(
                    prior_record,
                    ops.observe_allocation(),
                    overrides=resource_overrides,
                )
                execution_profile = replace(
                    execution_profile,
                    resource_policy=resources.policy,
                )
            run = HistoricalRun(
                normalized=normalized,
                run_id=observed.run_id,
                execution_projection_bytes=legacy_bytes,
            )
        plan = ops.transform_plan(
            build_attempt_plan(
                run,
                readiness,
                workspace,
                resources=resources,
                operation="resume",
                now=ops.now(),
                token=ops.token(),
                supersedes_workflow_attempt_id=str(previous["workflow_attempt_id"]),
                retained_dispatches=_retained_dispatches(observed),
                placement=execution_profile.attempt_placement(scheduler_job_id),
            )
        )
    except (
        doctor.DoctorInputError,
        MaterializationError,
        ResourceConfigError,
        ExecutionProfileError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        raise ControlError(str(exc)) from exc
    if plan.run_root != root:
        raise ControlError("Resume workspace resolves to a different run root")
    for field in inspection.attempt_compatibility_fields(observed.authority_format):
        if plan.attempt_record[field] != previous[field]:
            raise ControlError(f"Resume is incompatible with predecessor on {field}")
    return plan


def _verified_report_location_lines(
    locations: tuple[tuple[str, Path], ...],
) -> tuple[str, ...]:
    expected = (
        ("scientific-report-html", "Scientific report"),
        ("evidence-report-html", "Evidence report"),
    )
    if not locations:
        return ()
    if len(locations) != len(expected):
        raise ControlError(
            "Completed run lacks both exact verified result locations"
        )
    lines = ["Results:"]
    for (output_id, path), (expected_id, label) in zip(
        locations, expected, strict=True
    ):
        if (
            output_id != expected_id
            or not isinstance(path, Path)
            or not path.is_absolute()
        ):
            raise ControlError("Completed run has malformed verified result locations")
        lines.append(f"  {label}: {path}")
    return tuple(lines)


def _next_supported_action(observed: inspection.RunInspection) -> str:
    if observed.integrity == "blocked":
        return "Preserve this Run; review Run integrity blockers. Do not resume."
    if observed.results_status == "blocked":
        return "Preserve this Run; review scientific Results blockers. Do not resume."
    if observed.reporting_status == "blocked":
        if observed.results_status == "complete":
            return "Preserve completed Results; do not rerun science. Review blockers."
        return "Preserve this Run; review reporting blockers. Do not resume."
    if observed.attempt_outcome == "blocked":
        return "Preserve this Run; review retained evidence. Do not resume."
    if observed.attempt_outcome == "not_started":
        return "Repeat the original emrys run invocation with --execute."
    if observed.attempt_outcome == "running":
        return "Wait for the active Attempt to finish, then inspect the Run again."
    if observed.recovery_available:
        return "Use emrys resume for this Run; dry-run remains the default."
    if observed.results_status == "complete":
        if observed.reporting_status == "complete":
            return "Review the verified Results and report paths."
        return "Preserve completed Results; report regeneration is not supported here."
    return "Preserve this Run; review retained evidence. Do not resume."


def _private_delegate_digest() -> str | None:
    values = {
        name: os.environ.get(name)
        for name in (
            slurm_submission.DELEGATE_MARKER_ENV,
            slurm_submission.PROFILE_SHA256_ENV,
            slurm_submission.SUBMIT_UID_ENV,
        )
    }
    if not any(value is not None for value in values.values()):
        return None
    if any(value is None for value in values.values()):
        raise ControlError("Private Slurm delegate context is incomplete")
    if values[slurm_submission.DELEGATE_MARKER_ENV] != slurm_submission.DELEGATE_MARKER:
        raise ControlError("Private Slurm delegate marker is invalid")
    if values[slurm_submission.SUBMIT_UID_ENV] != str(os.getuid()):
        raise ControlError("Private Slurm delegate UID differs from the current process")
    return values[slurm_submission.PROFILE_SHA256_ENV]


def _delegate_job_id(
    profile: ExecutionProfile,
    expected_profile_sha256: str | None,
) -> str | None:
    if expected_profile_sha256 is None:
        return None
    if not isinstance(profile.placement, SlurmPlacement):
        raise ControlError("A private Slurm delegate requires Slurm placement")
    job_id = os.environ.get("SLURM_JOB_ID")
    if (
        job_id is None
        or not job_id.isascii()
        or not job_id.isdecimal()
        or not job_id.strip("0")
    ):
        raise ControlError("A private Slurm delegate requires one positive job ID")
    return job_id


def _resolve_controls(arguments: argparse.Namespace, workspace: Path) -> LogControls:
    root = _absolute(workspace)
    if root == Path("/"):
        raise ControlError("Workspace must not be the filesystem root")
    try:
        return resolve_log_controls(
            source_checkout=SourceCheckout(Path(__file__).resolve().parents[4]),
            cli_level=getattr(arguments, "log_level", None),
            cli_root=getattr(arguments, "log_root", None),
            default_root=root / "logs" / "application",
        )
    except LogControlError as exc:
        raise ControlError(str(exc)) from exc


def _resume_workspace(run_root: Path) -> Path:
    root = _absolute(run_root)
    if root.parent.name != "runs" or root.parent.parent == Path("/"):
        raise ControlError("Run root must use the canonical <workspace>/runs/<run-id> layout")
    return root.parent.parent


def _admit_workspace_location(workspace: Path) -> None:
    source_root = _absolute(Path(__file__).resolve().parents[4])
    try:
        blockers, remediations = doctor.workspace_location_blockers(
            _absolute(workspace), source_root
        )
    except doctor.DoctorInputError as exc:
        raise ControlError(str(exc)) from exc
    if blockers:
        details = [*blockers, *(f"REMEDIATION: {value}" for value in remediations)]
        raise ControlError("Workspace admission blockers: " + "; ".join(details))


def _delegate_argv(
    command: str,
    arguments: argparse.Namespace,
    profile: ExecutionProfile,
    controls: LogControls,
    overrides: ResourceOverrides,
) -> tuple[str, ...]:
    argv = [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "emrys",
        command,
    ]
    if command == "run":
        argv.extend(
            (
                "--request",
                str(_absolute(arguments.request)),
                "--workspace",
                str(_absolute(arguments.workspace)),
            )
        )
    else:
        argv.extend(("--run-root", str(_absolute(arguments.run_root))))
    argv.extend(
        (
            "--runtime-profile",
            str(_absolute(arguments.runtime_profile)),
            "--execution-profile",
            str(profile.source_path),
            "--log-level",
            controls.level.value,
            "--log-root",
            str(controls.root),
            *resource_override_argv(overrides),
            "--execute",
        )
    )
    return tuple(argv)


def _prepare_scheduler_log_dir(workspace: Path) -> Path:
    root = _absolute(workspace)
    log_dir = root / "logs"
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ControlError(
            "Scheduler log directory creation requires symbolic-link protection"
        )
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= os.O_DIRECTORY
    descriptor: int | None = None
    try:
        descriptor = os.open(log_dir.anchor, flags)
        for component in log_dir.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                os.mkdir(component, mode=0o700, dir_fd=descriptor)
                child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    except OSError as exc:
        raise ControlError(
            f"Could not securely create scheduler log directory: {log_dir}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return log_dir


def _owned_failure_paths(
    plan: AttemptPlan,
    *,
    released_lock_path: Path | None = None,
) -> dict[str, Path]:
    """Return only lifecycle paths that this Attempt demonstrably owns."""

    owned: dict[str, Path] = {}
    lock_path = plan.run_root / "locks" / "run.lock"
    if os.path.lexists(lock_path):
        owned["lock"] = lock_path
    recovery_paths = (
        *((released_lock_path,) if released_lock_path is not None else ()),
        plan.run_root
        / "attempts"
        / plan.workflow_attempt_id
        / "released-run-lock.json",
        plan.run_root
        / "locks"
        / f"released-{plan.workflow_attempt_id}-run-lock.json",
    )
    for path in recovery_paths:
        if os.path.lexists(path):
            owned["recovery"] = path
            break
    return owned


def _schedule(
    command: str,
    arguments: argparse.Namespace,
    profile: ExecutionProfile,
    controls: LogControls,
    overrides: ResourceOverrides,
    workspace: Path,
) -> int:
    try:
        submission = slurm_submission.plan_submission(
            profile,
            emrys_argv=_delegate_argv(
                command,
                arguments,
                profile,
                controls,
                overrides,
            ),
            log_dir=_absolute(workspace) / "logs",
        )
    except slurm_submission.SlurmSubmissionError as exc:
        raise ControlError(str(exc)) from exc
    print("Execution placement: Slurm", file=sys.stderr)
    print(f"Execution profile: {profile.source_path}", file=sys.stderr)
    print(f"Scheduler stdout: {submission.stdout_pattern}", file=sys.stderr)
    print(f"Scheduler stderr: {submission.stderr_pattern}", file=sys.stderr)
    if controls.level is LogLevel.DEBUG:
        print("Scheduler command: " + shlex.join(submission.argv), file=sys.stderr)
    if not arguments.execute:
        print("Dry-run complete; no scheduler or workspace state was written.", file=sys.stderr)
        return 0
    _admit_workspace_location(workspace)
    _prepare_scheduler_log_dir(workspace)
    try:
        job_id = slurm_submission.submit(submission)
    except slurm_submission.SlurmSubmissionError as exc:
        raise ControlError(str(exc)) from exc
    print(f"JOB_ID={job_id}")
    print(f"OUT={str(submission.stdout_pattern).replace('%j', job_id)}")
    print(f"ERR={str(submission.stderr_pattern).replace('%j', job_id)}")
    return 0


def _execute_plan(
    build_plan: PlanBuilder,
    *,
    controls: LogControls,
    workspace: Path,
    mode: str,
    scope_id: str,
    entrypoint: str,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    """Build and execute one plan inside one non-authoritative application log."""

    _admit_workspace_location(workspace)

    execution_attempt_id = f"application-{uuid.uuid4().hex}"
    try:
        attempt = open_attempt_log(
            controls=controls,
            identity=AttemptIdentity(
                "run",
                scope_id,
                execution_attempt_id,
                entrypoint,
            ),
            mode=mode,
            component="orchestration",
            scheduler_environment=os.environ,
        )
    except (ApplicationLogError, ValueError) as exc:
        print(
            render_failure_summary(
                entrypoint=entrypoint,
                phase="logging",
                status="failed",
                scope=f"run:{scope_id}",
                execution_attempt_id=execution_attempt_id,
                log_path=None,
                next_action=(
                    "Correct the application-log path or permissions, then retry."
                ),
            ),
            end="",
            file=sys.stderr,
        )
        raise ControlError(str(exc), reported=True) from exc

    logger = attempt.logger(component="orchestration", phase="execute")
    logging_degraded = False

    def log_best_effort(operation: Callable[[], object]) -> bool:
        nonlocal logging_degraded
        if logging_degraded:
            return False
        try:
            result = operation()
        except Exception:
            result = False
        if result is not False:
            return True
        logging_degraded = True
        print(
            "WARNING: Application logging degraded; the authoritative Attempt "
            "receipt and lifecycle outcome remain controlling.",
            file=sys.stderr,
        )
        return False

    try:
        plan = build_plan()
    except KeyboardInterrupt:
        log_best_effort(
            lambda: attempt.interrupt_best_effort(
                message="Analysis preflight interrupted."
            )
        )
        print(
            render_failure_summary(
                entrypoint=entrypoint,
                phase="preflight",
                status="interrupted",
                scope=f"run:{scope_id}",
                execution_attempt_id=execution_attempt_id,
                log_path=attempt.path,
                recent_events=attempt.recent_console_events,
                durable_only_count=attempt.durable_only_count,
                next_action="Retry when ready.",
            ),
            end="",
            file=sys.stderr,
        )
        raise
    except ControlError as exc:
        log_best_effort(
            lambda: attempt.fail(
                phase="preflight",
                message="Analysis preflight failed.",
            )
        )
        print(f"emrys: error: {exc}", file=sys.stderr)
        print(
            render_failure_summary(
                entrypoint=entrypoint,
                phase="preflight",
                status="failed",
                scope=f"run:{scope_id}",
                execution_attempt_id=execution_attempt_id,
                log_path=attempt.path,
                recent_events=attempt.recent_console_events,
                durable_only_count=attempt.durable_only_count,
                next_action="Correct the reported preflight error, then retry.",
            ),
            end="",
            file=sys.stderr,
        )
        raise ControlError(str(exc), reported=True) from exc

    log_best_effort(
        lambda: logger.info(
            "Preparing analysis.",
            extra=event(
                "analysis_prepared",
                fields={
                    "run_id": field(plan.run.run_id, console=True),
                    "workflow_attempt_id": field(plan.workflow_attempt_id),
                },
            ),
        )
    )
    _print_plan(plan, level=controls.level)
    receipt_ready = False

    def observe_application_event(event_name: str) -> None:
        nonlocal receipt_ready
        if event_name == "analysis_started":
            log_best_effort(
                lambda: logger.info(
                    "Running analysis.", extra=event("analysis_started")
                )
            )
        elif event_name == "publication_ready":
            receipt_ready = log_best_effort(
                lambda: attempt.publication_ready(
                    message="Analysis finished; finalizing evidence."
                )
            )

    try:
        outcome = ops.execute_plan(plan, observe_application_event)
    except (
        MaterializationError,
        lifecycle.LifecycleError,
        OSError,
    ) as exc:
        if receipt_ready:
            log_best_effort(
                lambda: attempt.receipt_failed(
                    message="Attempt receipt publication failed."
                )
            )
            log_best_effort(
                lambda: attempt.terminal(
                    event_name="execution_incomplete",
                    message="Analysis execution did not complete.",
                )
            )
        else:
            log_best_effort(
                lambda: attempt.fail(
                    phase="execute", message="Analysis execution failed."
                )
            )
        print(f"emrys: error: {exc}", file=sys.stderr)
        print(
            render_failure_summary(
                entrypoint=entrypoint,
                phase="execute",
                status="failed",
                scope=f"run:{scope_id}",
                execution_attempt_id=execution_attempt_id,
                log_path=attempt.path,
                owned_paths=_owned_failure_paths(plan),
                recent_events=attempt.recent_console_events,
                durable_only_count=attempt.durable_only_count,
                next_action=(
                    "Inspect the Run with emrys inspect local-pilot-run --run-root "
                    f"{plan.run_root}"
                ),
            ),
            end="",
            file=sys.stderr,
        )
        raise ControlError(str(exc), reported=True) from exc

    status = str(outcome.receipt["status"])
    if receipt_ready:
        log_best_effort(attempt.receipt_committed)
        log_best_effort(
            lambda: attempt.observe_post_receipt(
                event_name="attempt_receipt_observed",
                message="Authoritative attempt receipt was observed.",
                fields={
                    "receipt_path": field(outcome.receipt_path),
                    "status": field(status),
                },
            )
        )
        log_best_effort(attempt.close)
    elif not logging_degraded:
        log_best_effort(
            lambda: attempt.terminal(
                event_name="execution_completed",
                message="Analysis execution completed without a receipt callback.",
                fields={"status": field(status)},
            )
        )

    result_lines = _verified_report_location_lines(outcome.verified_report_locations)
    if status == "succeeded":
        print(f"Evidence: {outcome.receipt_path}", file=sys.stderr)
        for line in result_lines:
            print(line, file=sys.stderr)
        return 0
    print(
        render_failure_summary(
            entrypoint=entrypoint,
            phase="terminal",
            status=status,
            scope=f"run:{scope_id}",
            execution_attempt_id=execution_attempt_id,
            log_path=attempt.path,
            owned_paths=_owned_failure_paths(
                plan,
                released_lock_path=outcome.released_lock_path,
            ),
            recent_events=attempt.recent_console_events,
            durable_only_count=attempt.durable_only_count,
            next_action=(
                "Inspect the Run with emrys inspect local-pilot-run --run-root "
                f"{plan.run_root}"
            ),
        ),
        end="",
        file=sys.stderr,
    )
    return 1


def _print_plan(plan: AttemptPlan, *, level: LogLevel) -> None:
    new_dispatches = plan.new_dispatch_files
    reused = plan.dispatch_count - len(new_dispatches)
    print(f"Operation: {plan.operation}", file=sys.stderr)
    resources = plan.resources
    print(f"Run ID: {plan.run.run_id}", file=sys.stderr)
    print(f"Run root: {plan.run_root}", file=sys.stderr)
    print(f"Pending work items: {plan.dispatch_count - reused}", file=sys.stderr)
    print(f"Reusable completed work items: {reused}", file=sys.stderr)
    print(
        f"Resources: {resources.workflow_cores} cores, "
        f"{resources.workflow_memory_mb} MiB",
        file=sys.stderr,
    )
    print("Reporting: automatic after scientific work", file=sys.stderr)
    if level in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        print("Step thread allocations:", file=sys.stderr)
        for step_id, threads in resources.step_threads:
            print(f"  Step {step_id}: {threads}", file=sys.stderr)
        print("Stage concurrency:", file=sys.stderr)
        for step_id, concurrency in resources.stage_concurrency:
            print(f"  Step {step_id}: {concurrency}", file=sys.stderr)
    if level is LogLevel.DEBUG:
        print(
            "Snakemake command: "
            + shlex.join(plan.attempt_record["snakemake_argv"]),
            file=sys.stderr,
        )
        for item in new_dispatches:
            record = orchestration_contracts.load_json_object_bytes(item.data, item.path)
            print(
                f"TASK {record['machine_key']}/{record['scope']['scope_id']} producer: "
                + shlex.join(record["producer_argv"]),
                file=sys.stderr,
            )
            print(
                f"TASK {record['machine_key']}/{record['scope']['scope_id']} validator: "
                + shlex.join(record["validator_argv"]),
                file=sys.stderr,
            )
    print(
        "Evidence boundary: this plan or execution proves only the admitted local "
        "workflow layer; it is not cluster, production, scientific-review, or "
        "biological proof.",
        file=sys.stderr,
    )


def _finish_control(
    arguments: argparse.Namespace,
    *,
    command: str,
    profile: ExecutionProfile,
    controls: LogControls,
    overrides: ResourceOverrides,
    scheduler_job_id: str | None,
    workspace: Path,
    build_plan: PlanBuilder,
    ops: ControlOps,
) -> int:
    if isinstance(profile.placement, SlurmPlacement) and scheduler_job_id is None:
        return _schedule(
            command,
            arguments,
            profile,
            controls,
            overrides,
            workspace,
        )
    if not arguments.execute:
        _print_plan(build_plan(), level=controls.level)
        print(
            "Dry-run complete; no "
            f"{'workspace' if command == 'run' else 'resume'} state was written.",
            file=sys.stderr,
        )
        return 0
    return _execute_plan(
        build_plan,
        controls=controls,
        workspace=workspace,
        mode="execute" if command == "run" else "resume",
        scope_id="pending" if command == "run" else _absolute(arguments.run_root).name,
        entrypoint=f"emrys-{command}",
        ops=ops,
    )


def configure_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--runtime-profile", required=True, type=Path)
    parser.add_argument(
        "--execution-profile",
        type=Path,
        help="Optional combined resource and placement profile; direct is the default.",
    )
    add_resource_override_arguments(parser)
    add_log_arguments(parser)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create and execute the planned run. Without this flag, write nothing.",
    )


def configure_resume_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--runtime-profile", required=True, type=Path)
    parser.add_argument(
        "--execution-profile",
        type=Path,
        help=(
            "Optional placement profile. Without one, reuse prior computational "
            "resources and execute directly."
        ),
    )
    add_resource_override_arguments(parser)
    add_log_arguments(parser)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the safe resume. Without this flag, write nothing.",
    )


def configure_inspect_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument(
        "--detail",
        choices=("normal", "verbose", "debug"),
        default="normal",
        help="Select concise, operational, or exact retained-record detail.",
    )


def _progress_state(tasks: tuple[inspection.TaskInspection, ...]) -> str:
    if not tasks:
        return "not applicable"
    if any(task.state == "blocked" for task in tasks):
        return "blocked"
    if all(task.state == "verified" for task in tasks):
        return "complete"
    return "incomplete"


def _milestone_progress(
    tasks: tuple[inspection.TaskInspection, ...],
) -> tuple[tuple[str, str, int, int], ...]:
    known_steps = {step for _label, steps in _MILESTONE_STEPS for step in steps}
    unknown = sorted({task.expected.step_id for task in tasks} - known_steps)
    if unknown:
        raise ControlError(
            "Inspected task Steps have no public milestone: " + ", ".join(unknown)
        )
    result = []
    for label, steps in _MILESTONE_STEPS:
        members = tuple(task for task in tasks if task.expected.step_id in steps)
        result.append(
            (
                label,
                _progress_state(members),
                sum(task.state == "verified" for task in members),
                len(members),
            )
        )
    return tuple(result)


def _attempt_elapsed_line(
    observed: inspection.RunInspection,
    clock: Callable[[], datetime],
) -> str:
    attempt = observed.latest_attempt
    if attempt is None:
        return "Attempt elapsed: unavailable — no Attempt"
    label = "Current" if observed.attempt_outcome == "running" else "Latest"
    try:
        started = datetime.fromisoformat(
            str(attempt["created_at"]).replace("Z", "+00:00")
        )
        if observed.attempt_outcome == "running":
            finished = clock()
        elif observed.latest_receipt is not None:
            finished = datetime.fromisoformat(
                str(observed.latest_receipt["finished_at"]).replace("Z", "+00:00")
            )
        else:
            return f"{label} Attempt elapsed: unavailable — no terminal receipt"
        if finished < started:
            raise ValueError("negative Attempt duration")
        seconds = int((finished - started).total_seconds())
    except (KeyError, TypeError, ValueError):
        return f"{label} Attempt elapsed: unavailable — invalid timestamp boundary"
    if started.tzinfo is None or finished.tzinfo is None:
        return f"{label} Attempt elapsed: unavailable — invalid timestamp boundary"
    return f"{label} Attempt elapsed: {timedelta(seconds=seconds)}"


def run_from_args(
    arguments: argparse.Namespace,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    try:
        overrides = overrides_from_args(arguments)
        expected_profile_sha256 = _private_delegate_digest()
        profile = load_execution_profile(
            arguments.request,
            config_path=getattr(arguments, "execution_profile", None),
            resource_overrides=overrides,
            expected_sha256=expected_profile_sha256,
        )
        scheduler_job_id = _delegate_job_id(profile, expected_profile_sha256)
        controls = _resolve_controls(arguments, arguments.workspace)
        build_plan = partial(
            _plan_run,
            arguments.request,
            arguments.workspace,
            arguments.runtime_profile,
            execution_profile=profile,
            scheduler_job_id=scheduler_job_id,
            ops=ops,
        )
        return _finish_control(
            arguments,
            command="run",
            profile=profile,
            build_plan=build_plan,
            controls=controls,
            overrides=overrides,
            scheduler_job_id=scheduler_job_id,
            workspace=arguments.workspace,
            ops=ops,
        )
    except (
        ControlError,
        ExecutionProfileError,
        ResourceConfigError,
    ) as exc:
        if not isinstance(exc, ControlError) or not exc.reported:
            print(f"emrys: error: {exc}", file=sys.stderr)
        return 2


def resume_from_args(
    arguments: argparse.Namespace,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    try:
        overrides = overrides_from_args(arguments)
        expected_profile_sha256 = _private_delegate_digest()
        selected_profile = getattr(arguments, "execution_profile", None)
        profile = load_execution_profile(
            arguments.run_root,
            config_path=selected_profile,
            resource_overrides=overrides,
            expected_sha256=expected_profile_sha256,
        )
        scheduler_job_id = _delegate_job_id(profile, expected_profile_sha256)
        workspace = _resume_workspace(arguments.run_root)
        controls = _resolve_controls(arguments, workspace)
        build_plan = partial(
            _plan_resume,
            arguments.run_root,
            arguments.runtime_profile,
            execution_profile=profile,
            profile_resources_explicit=(
                profile.resource_policy.config_path is not None
            ),
            resource_overrides=overrides,
            scheduler_job_id=scheduler_job_id,
            ops=ops,
        )
        return _finish_control(
            arguments,
            command="resume",
            profile=profile,
            build_plan=build_plan,
            controls=controls,
            overrides=overrides,
            scheduler_job_id=scheduler_job_id,
            workspace=workspace,
            ops=ops,
        )
    except (
        ControlError,
        ExecutionProfileError,
        ResourceConfigError,
    ) as exc:
        if not isinstance(exc, ControlError) or not exc.reported:
            print(f"emrys: error: {exc}", file=sys.stderr)
        return 2


def inspect_from_args(
    arguments: argparse.Namespace,
    *,
    ops: ControlOps = DEFAULT_CONTROL_OPS,
) -> int:
    try:
        observed = ops.inspect_run(_absolute(arguments.run_root))
        detail = getattr(arguments, "detail", "normal")
        milestones = _milestone_progress(observed.tasks)
        elapsed = _attempt_elapsed_line(observed, ops.now)
        result_lines = _verified_report_location_lines(
            observed.verified_report_locations
        )
    except (OSError, inspection.InspectionError, ControlError) as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return 2
    print(f"Run ID: {observed.run_id}")
    print(f"Run integrity: {observed.integrity}")
    print(f"Attempt outcome: {observed.attempt_outcome}")
    print(elapsed)
    print("Scientific milestones:")
    for label, state, verified, total in milestones:
        print(f"  {label}: {state}")
        if detail != "normal":
            print(f"    Verified tasks: {verified}/{total}")
    print(f"Scientific Results: {observed.results_status}")
    print(f"Reporting: {observed.reporting_status}")
    latest = observed.latest_attempt
    receipt = observed.latest_receipt
    if detail != "normal":
        print(f"Run root: {observed.run_root}")
        print("Attempt ID: " + ("none" if latest is None else str(latest["workflow_attempt_id"])))
        if latest is not None:
            placement = latest.get("placement")
            placement_kind = "legacy/unrecorded" if placement is None else placement["kind"]
            scheduler_job_id = "none" if placement is None else placement["scheduler_job_id"] or "none"
            print(
                f"Execution: {latest['executor']}/{latest['execution_mode']} "
                f"placement={placement_kind} scheduler_job_id={scheduler_job_id}"
            )
        print("Reporting transactions:")
        for kind, records in observed.reporting_completion_records.items():
            state = (
                "complete" if records["verified"] is not None
                else "incomplete" if records["start"] is not None
                else "pending"
            )
            print(f"  {kind}: {state}")
    if detail == "debug":
        if latest is not None:
            attempt_id = str(latest["workflow_attempt_id"])
            attempt_root = observed.run_root / "attempts" / attempt_id
            receipt_path = "none" if receipt is None else attempt_root / "attempt-receipt.json"
            print(f"Attempt receipt: {receipt_path}")
            print(f"Engine command: {shlex.join(latest['snakemake_argv'])}")
            if receipt is not None:
                print(
                    "Attempt receipt result: "
                    f"exit={receipt['snakemake_exit_code']} "
                    f"signal={receipt['termination_signal']} "
                    f"message={receipt['message']}"
                )
        print("Task records:")
        for task in observed.tasks:
            identity = f"{task.expected.machine_key}/{task.expected.scope_id}"
            task_detail = f"  TASK {identity}: {task.state}"
            if task.record_reference is not None:
                task_detail += (
                    f"; verified={observed.run_root / task.record_reference['path']}"
                )
            if task.record is not None:
                attempt_reference = task.record["task_attempt_record"]
                attempt_path = observed.run_root / attempt_reference["path"]
                task_detail += (
                    f"; attempt={attempt_path}"
                    f"; stdout={attempt_path.with_name('stdout.log')}"
                    f"; stderr={attempt_path.with_name('stderr.log')}"
                )
            print(task_detail)
    for blocker_label, blockers in (
        ("RUN BLOCKER", observed.integrity_blockers),
        ("RESULTS BLOCKER", observed.results_blockers),
        ("REPORTING BLOCKER", observed.reporting_blockers),
        ("ATTEMPT EVIDENCE BLOCKER", observed.receipt_blockers),
    ):
        for blocker in blockers:
            print(f"{blocker_label}: {blocker}")
    print(f"Recovery available: {'yes' if observed.recovery_available else 'no'}")
    print(f"Next supported action: {_next_supported_action(observed)}")
    for line in result_lines:
        print(line)
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
    "inspect_from_args",
    "resume_from_args",
    "run_from_args",
)
