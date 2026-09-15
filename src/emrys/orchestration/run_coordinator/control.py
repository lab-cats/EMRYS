"""Public dry-run-first control plane for Project Runs."""

from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import sys
import uuid
from collections import Counter
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, TextIO

from simple_term_menu import TerminalMenu

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.artifact_inventory import validate_processing_graph
from emrys.contracts.orchestration.application_model import (
    execution_plan_boundary,
)
from emrys.libraries.application_logging import (
    ApplicationLogError,
    AttemptIdentity,
    AttemptLog,
    LogControlError,
    LogControls,
    LogLevel,
    add_log_arguments,
    console_print,
    event,
    field,
    open_attempt_log,
    phase_progress,
    render_failure_summary,
    resolve_log_controls,
)
from emrys.libraries.application_logging.controls import (
    add_log_root_argument,
    resolve_log_root,
)
from emrys.libraries.source_authority import admit_installed_package
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes
from emrys.orchestration.run_coordinator import (
    _inspection_presentation,
    _submission_inspection,
    capacity,
    doctor,
    inspection,
    lifecycle,
    onboarding,
    reporting_operation,
    task as task_boundary,
)
from emrys.orchestration.run_coordinator.execution_profile import (
    ExecutionProfile,
    ExecutionProfileError,
    SlurmPlacement,
    load_execution_profile,
    project_execution_profile_path,
)
from emrys.orchestration.run_coordinator.materialization import (
    AttemptPlan,
    MaterializationError,
    admit_run,
    build_attempt_plan,
    build_run_candidate,
    processing_stopping_owner_keys,
    publish_attempt,
    validate_run_destination,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    ResourceConfigError,
    ResourceOverrides,
    ResourcePolicy,
    add_resource_override_arguments,
    admit_resource_policy_record,
    overrides_from_args,
    resource_override_argv,
    resolve_resource_policy,
    resume_resource_policy,
)
from emrys.orchestration.run_coordinator import slurm_submission

RUN_DESCRIPTION = "Plan an immutable Run; confirm or use --execute. Installs nothing."
RESUME_DESCRIPTION = "Plan a safe resume, then confirm or use --execute for automation."
INSPECT_DESCRIPTION = (
    "Show retained Project submissions and inspect one Run without changing state."
)
STOP_DESCRIPTION = (
    "Preview one exact submission stop; use --execute to request cancellation."
)
REPORT_DESCRIPTION = (
    "Plan, generate, or reuse the fixed reports for one completed immutable Run. "
    "Dry-run is the default and reporting never creates a scientific Attempt."
)


class ControlError(RuntimeError):
    """A public control-plane request is malformed or not currently admissible."""

    def __init__(self, message: str, *, reported: bool = False) -> None:
        super().__init__(message)
        self.reported = reported


class _RunSelectionCancelled(ControlError):
    """The operator left the read-only Run picker without selecting a Run."""


class _NoProjectRuns(ControlError):
    """The Project has no selectable Run at the time of inspection."""


_CONTROL_ERRORS = (
    slurm_submission.SlurmSubmissionError,
    ControlError,
    ExecutionProfileError,
    ResourceConfigError,
    inspection.InspectionError,
    onboarding.OnboardingError,
)
_PLANNING_ERRORS = (
    doctor.DoctorInputError,
    inspection.InspectionError,
    MaterializationError,
    ResourceConfigError,
    ExecutionProfileError,
    orchestration_contracts.ContractValidationError,
)


def _control_failure(exc: Exception) -> int:
    if not isinstance(exc, ControlError) or not exc.reported:
        _print_safe(f"emrys: error: {exc}", file=sys.stderr)
    return 0 if isinstance(exc, _RunSelectionCancelled) else 2


PlanBuilder = Callable[[], AttemptPlan]


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _select_project_run(
    project_path: Path,
    selector: str | None,
    *,
    interactive: bool,
) -> Path:
    run_roots = inspection.project_run_roots(project_path.parent)
    if selector is not None:
        return inspection.resolve_run_root(run_roots, selector)
    if not run_roots:
        raise _NoProjectRuns(f"Project has no Runs: {project_path.parent}")
    if len(run_roots) == 1:
        return run_roots[0]
    names = tuple(inspection.human_run_name(root.name) for root in run_roots)
    name_counts = Counter(names)
    choices = tuple(
        name if name_counts[name] == 1 else f"{name} ({root.name})"
        for name, root in zip(names, run_roots, strict=True)
    )
    if not interactive:
        raise ControlError(
            "Multiple Runs exist; select one explicitly: " + ", ".join(choices)
        )
    try:
        selected = TerminalMenu(choices, title="Select a Run:").show()
    except (EOFError, KeyboardInterrupt) as exc:
        raise _RunSelectionCancelled(
            "Run selection canceled; nothing was changed."
        ) from exc
    if selected is None:
        raise _RunSelectionCancelled("Run selection canceled; nothing was changed.")
    return run_roots[selected]


def _resolve_run_argument(
    arguments: argparse.Namespace,
) -> tuple[Path, Path]:
    project_path = onboarding.project_definition_path(
        getattr(arguments, "project", None)
    )
    run_root = _select_project_run(
        project_path,
        getattr(arguments, "run", None),
        interactive=sys.stdin.isatty() and sys.stderr.isatty(),
    )
    arguments.project = project_path
    arguments.run = run_root.name
    return project_path, run_root


def _require_ready(result: doctor.DoctorResult) -> None:
    if result.ready:
        return
    details = [*result.blockers]
    details.extend(f"REMEDIATION: {value}" for value in result.remediations)
    raise ControlError("Project readiness blockers: " + "; ".join(details))


def _plan_run(
    project_path: Path,
    *,
    execution_profile: ExecutionProfile,
    analysis_name: str | None = None,
    through: str = "analysis",
    processing_source_run_id: str | None = None,
    scheduler_job_id: str | None = None,
    report_enabled: bool = True,
) -> AttemptPlan:
    """Plan a new run without writing any workspace state."""

    workspace = _absolute(project_path).parent
    try:
        readiness = doctor.diagnose_project(
            project_path,
            storage_requirement=execution_profile.placement.kind,
            analysis_name=analysis_name,
            require_reporter=report_enabled and through == "analysis",
        )
        _require_ready(readiness)
        validate_processing_graph(
            readiness.analysis.profile, readiness.installed_package.root
        )
        policy = execution_profile.resource_policy
        processing_source = None
        if processing_source_run_id is not None:
            if through != "analysis":
                raise ControlError(
                    "--from-processing-run cannot be combined with --through processing"
                )
            processing_source = inspection.admit_processing_source(
                workspace / "runs" / processing_source_run_id
            )
        run = build_run_candidate(
            readiness.analysis,
            readiness,
            policy.declaration,
            scientific_stopping_owner_keys=(
                None
                if through == "analysis"
                else processing_stopping_owner_keys(readiness.analysis.profile)
            ),
            processing_source=(
                None if processing_source is None else processing_source.binding
            ),
        )
        if processing_source is not None:
            inspection.validate_processing_source(
                processing_source,
                target_analysis=readiness.analysis.revision,
                target_plan=run.execution_plan,
            )
        resources = resolve_resource_policy(policy, capacity.observe_allocation())
        plan = build_attempt_plan(
            run,
            readiness,
            _absolute(workspace),
            resources=resources,
            operation="execute",
            placement=execution_profile.attempt_placement(scheduler_job_id),
            processing_source=processing_source,
        )
        validate_run_destination(plan.run_root, candidate=plan.run)
    except _PLANNING_ERRORS as exc:
        raise ControlError(str(exc)) from exc
    return plan


def _admit_resume_predecessor(
    run_root: Path,
) -> tuple[inspection.RunInspection, dict[str, Any]]:
    """Admit the one recoverable predecessor and its immutable Attempt manifest."""

    root = _absolute(run_root)
    try:
        observed = inspection.inspect_run(root)
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
    return observed, previous


def _resume_predecessor_policy(
    predecessor_config: Mapping[str, Any],
    overrides: ResourceOverrides,
) -> ResourcePolicy:
    """Re-admit the predecessor policy without observing an allocation."""

    prior = predecessor_config.get("resource_policy")
    if not isinstance(prior, dict):
        raise ControlError("Prior Attempt has no resource policy")
    try:
        predecessor = admit_resource_policy_record(prior).policy
        return resume_resource_policy(predecessor, overrides=overrides)
    except ResourceConfigError as exc:
        raise ControlError(str(exc)) from exc


def _retained_tasks(
    observed: inspection.RunInspection,
    attempt: Mapping[str, Any],
) -> tuple[dict[tuple[str, str], dict[str, Any]], bytes | None]:
    tasks = attempt["tasks"]
    retained: dict[tuple[str, str], dict[str, Any]] = {}
    attempt_reference = {
        "path": f"attempts/{attempt['workflow_attempt_id']}/attempt.json",
        "sha256": orchestration_contracts.canonical_sha256(attempt),
    }
    selected_manifest: bytes | None = None
    selected_projection: bool | None = None
    for inspected in observed.tasks:
        if inspected.state != "verified":
            continue
        try:
            definition = tasks[inspected.expected.machine_key][
                inspected.expected.scope_id
            ]
        except (KeyError, TypeError) as exc:
            raise ControlError(
                "Prior Attempt omits a reusable verified task: "
                f"{inspected.expected.machine_key}/{inspected.expected.scope_id}"
            ) from exc
        reference = definition.get("workflow_attempt_record", attempt_reference)
        path = observed.run_root / reference["path"]
        try:
            dispatch = task_boundary.load_task(
                path,
                expected_sha256=reference["sha256"],
                machine_key=inspected.expected.machine_key,
                scope_id=inspected.expected.scope_id,
            )
        except task_boundary.TaskBoundaryError as exc:
            raise ControlError(
                f"Reusable task plan is unavailable: {path}: {exc}"
            ) from exc
        retained[(inspected.expected.machine_key, inspected.expected.scope_id)] = {
            "workflow_attempt_record": dict(reference)
        }
        if inspected.expected.step_id != "07":
            continue
        manifest_path = (
            observed.run_root
            / "contract"
            / "workflow-inputs"
            / dispatch.workflow_attempt_id
            / "samples.tsv"
        )
        declaration = next(
            (item for item in dispatch.inputs if item.path == manifest_path),
            None,
        )
        projected = declaration is not None
        if selected_projection is not None and projected != selected_projection:
            raise ControlError("Reusable Step 07 tasks disagree on sample projection")
        selected_projection = projected
        if not projected:
            continue
        if declaration.expected_binding is None:
            raise ControlError(
                "Reusable Step 07 sample projection is not content-bound"
            )
        try:
            data = read_bytes(manifest_path, "reusable Step 07 sample projection")
        except ValidationError as exc:
            raise ControlError(
                f"Reusable Step 07 sample projection is unavailable: {manifest_path}"
            ) from exc
        binding = (len(data), hashlib.sha256(data).hexdigest())
        if binding != declaration.expected_binding:
            raise ControlError(
                "Reusable Step 07 sample projection differs from its binding"
            )
        if selected_manifest is not None and data != selected_manifest:
            raise ControlError("Reusable Step 07 tasks disagree on sample projection")
        selected_manifest = data
    return retained, selected_manifest


def _retained_runtime_profile_path(
    predecessor: Mapping[str, Any],
) -> Path:
    """Re-admit the predecessor's one exact retained runtime profile binding."""

    retained = tuple(
        identity
        for identity in predecessor["required_tools"]
        if identity["name"] == "runtime_profile"
    )
    if len(retained) != 1:
        raise ControlError(
            "Predecessor attempt does not bind one retained runtime profile"
        )
    identity = retained[0]
    path = Path(str(identity["path"]))
    resolved = Path(str(identity["resolved_path"]))
    try:
        data = read_bytes(path, "retained runtime profile")
        observed = path.resolve(strict=True)
    except (OSError, ValidationError) as exc:
        raise ControlError(
            f"Retained runtime profile is unavailable: {path}: {exc}"
        ) from exc
    digest = hashlib.sha256(data).hexdigest()
    if (
        not path.is_absolute()
        or path != resolved
        or observed != path
        or identity["sha256"] != digest
        or identity["version"] != f"sha256:{digest}"
    ):
        raise ControlError("Retained runtime profile differs from its binding")
    return path


def _resume_runtime_profile_path(
    project_path: Path,
    predecessor: Mapping[str, Any],
) -> Path:
    """Select current Project runtime or its exact predecessor binding."""

    candidate = onboarding.runtime_profile_path(project_path)
    return (
        candidate
        if os.path.lexists(candidate)
        else _retained_runtime_profile_path(predecessor)
    )


def _plan_resume(
    run_root: Path,
    *,
    execution_profile: ExecutionProfile,
    resource_overrides: ResourceOverrides = ResourceOverrides(),
    scheduler_job_id: str | None = None,
    report_enabled: bool = True,
) -> AttemptPlan:
    """Plan a safe between-task resume without writing run state."""

    root = _absolute(run_root)
    observed, previous = _admit_resume_predecessor(root)
    project_path = Path(str(previous["authored_paths"]["request"]))
    workspace = Path(str(previous["workspace"]))
    runtime_profile = _resume_runtime_profile_path(project_path, previous)
    authority = observed.authority
    if authority is None:
        raise ControlError("Resume requires current immutable Run authority")
    try:
        readiness = doctor.diagnose_project(
            project_path,
            workspace,
            runtime_profile,
            storage_requirement=execution_profile.placement.kind,
            analysis_name=previous.get("request_label"),
            expected_analysis_revision=authority.analysis_revision,
            require_reporter=report_enabled
            and execution_plan_boundary(authority.execution_plan) == "analysis",
        )
        _require_ready(readiness)
        analysis = readiness.analysis
        retained_tasks, retained_sample_manifest = _retained_tasks(
            observed,
            previous,
        )
        if retained_sample_manifest is not None:
            analysis = replace(
                analysis,
                selected_sample_manifest_bytes=retained_sample_manifest,
            )
            readiness = replace(readiness, analysis=analysis)
        policy = execution_profile.resource_policy
        if not execution_profile.computational_resources_explicit:
            policy = _resume_predecessor_policy(
                previous["workflow"],
                resource_overrides,
            )
            execution_profile = replace(
                execution_profile,
                resource_policy=policy,
            )
        processing_source = observed.processing_source
        candidate = build_run_candidate(
            analysis,
            readiness,
            policy.declaration,
            scientific_stopping_owner_keys=authority.execution_plan.record["identity"][
                "scientific_stopping_owner_keys"
            ],
            processing_source=(
                None if processing_source is None else processing_source.binding
            ),
        )
        if (
            candidate.run_binding.canonical_bytes
            != authority.run_binding.canonical_bytes
        ):
            raise ControlError("Current inputs resolve to a different Run")
        run = candidate
        resources = resolve_resource_policy(policy, capacity.observe_allocation())
        plan = build_attempt_plan(
            run,
            readiness,
            workspace,
            resources=resources,
            operation="resume",
            supersedes_workflow_attempt_id=str(previous["workflow_attempt_id"]),
            retained_tasks=retained_tasks,
            placement=execution_profile.attempt_placement(scheduler_job_id),
            processing_source=processing_source,
        )
    except _PLANNING_ERRORS as exc:
        raise ControlError(str(exc)) from exc
    if plan.run_root != root:
        raise ControlError("Resume workspace resolves to a different run root")
    for field in inspection.attempt_fields():
        if plan.attempt_record[field] != previous[field]:
            raise ControlError(f"Resume is incompatible with predecessor on {field}")
    return plan


def _verified_report_location_lines(
    locations: tuple[tuple[str, Path], ...],
) -> tuple[str, ...]:
    if not locations:
        return ()
    labels = ("Scientific report", "Evidence report")
    return (
        "Results:",
        *(
            f"  {label}: {path}"
            for label, (_, path) in zip(labels, locations, strict=True)
        ),
    )


def _run_followup(command: str, run_root: Path, run_id: str, *options: str) -> str:
    """Render one unambiguous Run command that works outside its Project."""

    project_path = run_root.parent.parent / "project.yaml"
    selector = inspection.human_run_name(run_id)
    try:
        run_roots = inspection.project_run_roots(project_path.parent)
        if run_roots and inspection.resolve_run_root(run_roots, selector) != run_root:
            selector = run_id
    except inspection.InspectionError:
        selector = run_id
    argv = ["emrys", command, selector]
    if _absolute(Path.cwd()) != project_path.parent:
        argv.extend(("--project", str(project_path)))
    return shlex.join((*argv, *options))


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
        return "Repeat the original emrys run invocation and confirm execution."
    if observed.attempt_outcome == "running":
        return "Wait for the active Attempt to finish, then inspect the Run again."
    if observed.recovery_available:
        return "Use emrys resume for this Run; review and confirm the plan."
    if (
        observed.latest_receipt is not None
        and observed.latest_receipt.get("status") != "succeeded"
    ):
        return "Preserve this Run; review the latest Attempt receipt. Do not generate reports."
    if observed.results_status == "complete":
        if observed.reporting_status == "not applicable":
            return (
                "Inspect this Run's verified scientific artifacts with --detail debug."
            )
        if observed.reporting_status == "complete":
            return "Review the verified Results and report paths."
        return f"Generate reports with {_run_followup('report', observed.run_root, observed.run_id, '--execute')}."
    return "Preserve this Run; review retained evidence. Do not resume."


def _resolve_execution_profile(
    arguments: argparse.Namespace,
    project_path: Path,
    overrides: ResourceOverrides,
    resume_run_root: Path | None = None,
) -> tuple[ExecutionProfile, str | None]:
    """Admit one selected profile and any private Slurm delegate binding."""

    expected_sha256 = slurm_submission.delegate_binding()
    profile = load_execution_profile(
        config_path=project_execution_profile_path(
            project_path,
            getattr(arguments, "profile", None),
        ),
        resource_overrides=overrides,
        expected_binding_sha256=(
            None if resume_run_root is not None else expected_sha256
        ),
    )
    if (
        resume_run_root is not None
        and isinstance(profile.placement, SlurmPlacement)
        and not profile.computational_resources_explicit
    ):
        _observed, previous = _admit_resume_predecessor(resume_run_root)
        profile = replace(
            profile,
            resource_policy=_resume_predecessor_policy(
                previous["workflow"],
                overrides,
            ),
        )
    if (
        resume_run_root is not None
        and expected_sha256 is not None
        and profile.binding_sha256 != expected_sha256
    ):
        raise ExecutionProfileError("Execution-profile binding SHA-256 differs")
    profile.validate_reservation()
    return profile, slurm_submission.delegate_job_id(profile)


def _resolve_controls(arguments: argparse.Namespace, workspace: Path) -> LogControls:
    root = _absolute(workspace)
    if root == Path("/"):
        raise ControlError("Workspace must not be the filesystem root")
    try:
        return resolve_log_controls(
            cli_level=getattr(arguments, "log_level", None),
            cli_root=getattr(arguments, "log_root", None),
            default_root=root / "logs" / "application",
        )
    except LogControlError as exc:
        raise ControlError(str(exc)) from exc


def _admit_workspace_location(workspace: Path) -> None:
    source_root = _absolute(Path(__file__).resolve().parents[2])
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
                "--project",
                str(_absolute(arguments.project)),
            )
        )
        if (analysis_name := getattr(arguments, "analysis", None)) is not None:
            argv.extend(("--analysis", analysis_name))
        if getattr(arguments, "through", "analysis") != "analysis":
            argv.extend(("--through", arguments.through))
        if (
            source_run_id := getattr(arguments, "from_processing_run", None)
        ) is not None:
            argv.extend(("--from-processing-run", source_run_id))
    else:
        argv.extend(
            (
                str(arguments.run),
                "--project",
                str(_absolute(arguments.project)),
            )
        )
    argv.extend(
        (
            "--profile",
            str(profile.source_path),
            "--log-level",
            controls.level.value,
            "--log-root",
            str(controls.root),
            *resource_override_argv(overrides),
            "--execute",
        )
    )
    if getattr(arguments, "no_report", False):
        argv.append("--no-report")
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
    expected_lock = orchestration_contracts.canonical_json_bytes(
        orchestration_contracts.run_lock_record(plan.attempt_record)
    )
    try:
        observed_lock = read_bytes(lock_path, "Run lock")
    except ValidationError:
        observed_lock = None
    if observed_lock == expected_lock:
        owned["lock"] = lock_path
    recovery_paths = (
        *((released_lock_path,) if released_lock_path is not None else ()),
        plan.run_root
        / "attempts"
        / plan.workflow_attempt_id
        / "released-run-lock.json",
        plan.run_root / "locks" / f"released-{plan.workflow_attempt_id}-run-lock.json",
    )
    for path in recovery_paths:
        if os.path.lexists(path):
            owned["recovery"] = path
            break
    return owned


def _confirm_execution() -> bool:
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        return False
    console_print("Execute this plan? [y/N] ", end="", style="bold")
    return sys.stdin.readline().strip().casefold() in {"y", "yes"}


def _print_no_write(subject: str) -> None:
    console_print(f"Dry-run complete; no {subject} state was written.")


def _schedule(
    command: str,
    arguments: argparse.Namespace,
    profile: ExecutionProfile,
    controls: LogControls,
    overrides: ResourceOverrides,
    workspace: Path,
) -> int:
    request_token = uuid.uuid4().hex
    request_root = _absolute(workspace) / "logs" / f"submission-{request_token}"
    delegate_argv = _delegate_argv(
        command,
        arguments,
        profile,
        controls,
        overrides,
    )
    submission = slurm_submission.plan_submission(
        profile,
        emrys_argv=delegate_argv,
        log_dir=_absolute(workspace) / "logs",
        request_token=request_token,
    )
    console_print(f"Project: {workspace.name!a}", style="bold")
    if command == "run":
        analysis = getattr(arguments, "analysis", None)
        console_print(
            f"Analysis: {analysis!a}"
            if analysis is not None
            else "Analysis: selected from the Project on the compute node"
        )
    else:
        console_print(f"Run: {inspection.human_run_name(arguments.run)}")
    for line in profile.submission_summary():
        console_print(line)
    if controls.level in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        console_print(f"Execution profile: {profile.source_path}")
        console_print(f"Scheduler stdout: {submission.stdout_pattern}")
        console_print(f"Scheduler stderr: {submission.stderr_pattern}")
    if controls.level is LogLevel.DEBUG:
        console_print("Scheduler command: " + shlex.join(submission.argv))
    if not arguments.execute and not _confirm_execution():
        _print_no_write("scheduler or workspace")
        return 0
    _admit_workspace_location(workspace)
    _prepare_scheduler_log_dir(workspace)
    try:
        request_root.mkdir(mode=0o700)
        context = {
            "schema_version": "emrys.submission-request.v3",
            "created_at": datetime.now(UTC).isoformat(),
            "submitter_uid": os.getuid(),
            "command": command,
            "project": str(_absolute(arguments.project)),
            "requested_run": None if command == "run" else arguments.run,
            "analysis": getattr(arguments, "analysis", None),
            "application_log_root": str(controls.root),
            "profile_binding_sha256": profile.binding_sha256,
            "emrys_argv": list(delegate_argv),
            "scheduler_stdout_pattern": str(submission.stdout_pattern),
            "scheduler_stderr_pattern": str(submission.stderr_pattern),
            "scheduler_job_name": submission.job_name,
        }
        context = slurm_submission.validate_request_context(
            context, _absolute(arguments.project), request_root
        )
        with open(
            request_root / "request.json",
            "xb",
            opener=lambda path, flags: os.open(path, flags, 0o600),
        ) as stream:
            stream.write(orchestration_contracts.canonical_json_bytes(context))
            stream.flush()
            os.fsync(stream.fileno())
        onboarding._fsync_directory(request_root)
        onboarding._fsync_directory(request_root.parent)
    except OSError as exc:
        raise ControlError(
            f"Could not prepare submission request {request_root}; sbatch was not invoked: {exc}"
        ) from exc
    console_print(f"Submission request: {request_root}")
    job_id = slurm_submission.submit(
        submission, record_path=request_root / "sbatch.stdout"
    )
    print(f"JOB_ID={job_id}")
    print(f"OUT={str(submission.stdout_pattern).replace('%j', job_id)}")
    print(f"ERR={str(submission.stderr_pattern).replace('%j', job_id)}")
    return 0


def _record_submission_context(attempt: AttemptLog, workspace: Path) -> None:
    binding = slurm_submission.delegate_binding()
    token = os.environ.get(slurm_submission.REQUEST_TOKEN_ENV)
    if token is not None:
        attempt.logger(component="orchestration", phase="initialization").info(
            "Submission request context recorded.",
            extra=event(
                "submission_context",
                detail="durable_only",
                fields={
                    "request_token": field(token),
                    "profile_binding_sha256": field(binding),
                    "project_root": field(workspace),
                },
            ),
        )


def _execute_plan(
    plan_source: AttemptPlan | PlanBuilder,
    *,
    controls: LogControls,
    workspace: Path,
    mode: str,
    scope_id: str,
    entrypoint: str,
    report_enabled: bool = True,
) -> int:
    """Build and execute one plan inside one non-authoritative application log."""

    _admit_workspace_location(workspace)
    build_at_execution = callable(plan_source)

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
        console_print(
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
        )
        raise ControlError(str(exc), reported=True) from exc

    logger = attempt.logger(component="orchestration", phase="execute")
    log_best_effort = partial(
        attempt.best_effort,
        warning="WARNING: Application logging degraded; the authoritative Attempt "
        "receipt and lifecycle outcome remain controlling.",
    )
    log_best_effort(lambda: _record_submission_context(attempt, workspace))

    def close_log_best_effort() -> None:
        with suppress(Exception):
            attempt.close()

    def print_failure(
        *,
        phase: str,
        status: str,
        next_action: str,
        owned_paths: Mapping[str, Path] | None = None,
        run_scope: str = scope_id,
    ) -> None:
        console_print(
            render_failure_summary(
                entrypoint=entrypoint,
                phase=phase,
                status=status,
                scope=f"run:{run_scope}",
                execution_attempt_id=execution_attempt_id,
                log_path=attempt.path,
                owned_paths=owned_paths,
                recent_events=attempt.recent_console_events,
                durable_only_count=attempt.durable_only_count,
                next_action=next_action,
            ),
            end="",
        )

    try:
        plan = plan_source() if callable(plan_source) else plan_source
    except KeyboardInterrupt:
        log_best_effort(
            lambda: attempt.interrupt_best_effort(
                message="Analysis preflight interrupted."
            )
        )
        print_failure(
            phase="preflight",
            status="interrupted",
            next_action="Retry when ready.",
        )
        raise
    except ControlError as exc:
        log_best_effort(
            lambda: attempt.fail(
                phase="preflight",
                message="Analysis preflight failed.",
            )
        )
        console_print(f"emrys: error: {exc}")
        print_failure(
            phase="preflight",
            status="failed",
            next_action="Correct the reported preflight error, then retry.",
        )
        raise ControlError(str(exc), reported=True) from exc

    log_best_effort(
        lambda: logger.info(
            "Preparing analysis.",
            extra=event(
                "analysis_prepared",
                fields={
                    "run_id": field(plan.run.run_id),
                    "workflow_attempt_id": field(plan.workflow_attempt_id),
                },
            ),
        )
    )
    if build_at_execution:
        _print_plan(plan, level=controls.level, report_enabled=report_enabled)
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
        ops = replace(
            lifecycle.default_lifecycle_ops(),
            observe_application_event=observe_application_event,
        )
        if plan.operation == "execute":
            admit_run(plan, ops=ops)
        outcome = lifecycle.run_materialized_attempt(
            plan.lifecycle_request,
            lambda: publish_attempt(plan, ops=ops),
            ops=ops,
            initial_runtime_inspection=plan.readiness.inspection
            if build_at_execution
            else None,
        )
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
        console_print(f"emrys: error: {exc}")
        print_failure(
            phase="execute",
            status="failed",
            owned_paths=_owned_failure_paths(plan),
            next_action=(
                f"Inspect the Run with "
                f"{_run_followup('inspect', plan.run_root, plan.run.run_id)}"
            ),
        )
        close_log_best_effort()
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
    elif not attempt.degraded:
        log_best_effort(
            lambda: attempt.terminal(
                event_name="execution_completed",
                message="Analysis execution completed without a receipt callback.",
                fields={"status": field(status)},
            )
        )

    def observe_reporting(
        event_name: str,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        if receipt_ready:
            log_best_effort(
                lambda: attempt.observe_post_receipt(
                    event_name=event_name,
                    message=message,
                    fields=fields,
                )
            )

    if status == "succeeded":
        console_print(f"Evidence: {outcome.receipt_path}")
        if not _reporting_applicable(plan):
            observe_reporting(
                "reporting_not_applicable",
                "Reporting is not applicable to this partial scientific Run.",
            )
            close_log_best_effort()
            console_print("Reporting: not applicable (partial scientific Run)")
            return 0
        if not report_enabled:
            observe_reporting(
                "reporting_skipped", "Reporting was disabled for this execution."
            )
            close_log_best_effort()
            console_print("Reporting: skipped (--no-report)")
            return 0
        observe_reporting("reporting_started", "Generating downstream reports.")
        try:
            reported = reporting_operation.run_reporting(plan.run_root, execute=True)
        except (reporting_operation.ReportingOperationError, OSError) as exc:
            observe_reporting(
                "reporting_failed",
                "Reporting failed after scientific Results completed.",
                {"error": field(str(exc))},
            )
            close_log_best_effort()
            console_print(
                f"emrys: error: Reporting failed after scientific Results completed: {exc}",
            )
            print_failure(
                phase="reporting",
                status="failed",
                run_scope=plan.run.run_id,
                next_action=(
                    "Scientific Results remain complete. Inspect the Run and follow "
                    "its admitted next action."
                ),
            )
            return 1
        observe_reporting(
            "reporting_completed",
            "Downstream reports are verified.",
            {"reporting_status": field(reported.status)},
        )
        close_log_best_effort()
        result_lines = _verified_report_location_lines(
            reported.verified_report_locations
        )
        for line in result_lines:
            console_print(line)
        return 0
    close_log_best_effort()
    print_failure(
        phase="terminal",
        status=status,
        owned_paths=_owned_failure_paths(
            plan,
            released_lock_path=outcome.released_lock_path,
        ),
        next_action=(
            f"Inspect the Run with "
            f"{_run_followup('inspect', plan.run_root, plan.run.run_id)}"
        ),
    )
    return 1


def _reporting_applicable(plan: AttemptPlan) -> bool:
    return execution_plan_boundary(plan.run.execution_plan) == "analysis"


def _print_plan(
    plan: AttemptPlan, *, level: LogLevel, report_enabled: bool = True
) -> None:
    reused = plan.task_count - plan.new_task_count
    resources = plan.resources
    project_label = plan.run.analysis.source_path.parent.name
    console_print(f"Project: {project_label!a}", style="bold")
    console_print(f"Analysis: {plan.run.analysis.name!a}", style="blue")
    console_print(f"Run: {inspection.human_run_name(plan.run.run_id)}")
    full_analysis = _reporting_applicable(plan)
    if full_analysis:
        boundary = "complete analysis"
    elif execution_plan_boundary(plan.run.execution_plan) == "processing":
        boundary = "sample processing (through Step 06)"
    else:
        boundary = "partial scientific plan"
    if not full_analysis:
        reporting = "not applicable to this partial scientific Run"
    elif report_enabled:
        reporting = "automatic after scientific work"
    else:
        reporting = "disabled for this execution"
    console_print(f"Scientific boundary: {boundary}")
    if (
        processing_source := plan.run.execution_plan.record["identity"].get(
            "processing_source"
        )
    ) is not None:
        console_print(
            f"Processing source: {inspection.human_run_name(processing_source['source_run_id'])}",
        )
    console_print(f"Work: {plan.new_task_count} pending, {reused} reusable")
    console_print(f"Reporting: {reporting}")
    if level in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        console_print(f"Run ID: {plan.run.run_id}")
        if processing_source is not None:
            console_print(
                f"Processing source Run ID: {processing_source['source_run_id']}",
            )
        console_print(
            f"Analysis revision: {plan.run.analysis.revision.analysis_revision_id}",
        )
        console_print(
            f"Execution Plan ID: {plan.run.execution_plan.execution_plan_id}",
        )
        console_print(f"Run root: {plan.run_root}")
        console_print(
            f"Resources: {resources.workflow_cores} cores, {resources.workflow_memory_mb} MiB",
        )
        console_print("Step thread allocations:")
        for step_id, threads in resources.step_threads:
            console_print(f"  Step {step_id}: {threads}")
        console_print("Stage concurrency:")
        for step_id, concurrency in resources.stage_concurrency:
            console_print(f"  Step {step_id}: {concurrency}")
    if level is LogLevel.DEBUG:
        console_print(
            "Snakemake command: " + shlex.join(plan.attempt_record["snakemake_argv"]),
        )
        for machine_key, by_scope in plan.attempt_record["tasks"].items():
            for scope_id, record in by_scope.items():
                if "workflow_attempt_record" in record:
                    continue
                for command in ("producer", "validator"):
                    console_print(
                        f"TASK {machine_key}/{scope_id} {command}: "
                        + shlex.join(record[f"{command}_argv"]),
                    )
    console_print(
        "Evidence boundary: this plan or execution proves only the admitted local "
        "workflow layer; it is not cluster, production, scientific-review, or "
        "biological proof.",
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
) -> int:
    report_enabled = not getattr(arguments, "no_report", False)
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
        plan = build_plan()
        _print_plan(
            plan,
            level=controls.level,
            report_enabled=report_enabled,
        )
        if not _confirm_execution():
            _print_no_write("workspace" if command == "run" else "resume")
            return 0
        plan_source: AttemptPlan | PlanBuilder = plan
    else:
        plan_source = build_plan
    return _execute_plan(
        plan_source,
        controls=controls,
        workspace=workspace,
        mode="execute" if command == "run" else "resume",
        scope_id="pending" if command == "run" else str(arguments.run),
        entrypoint=f"emrys-{command}",
        report_enabled=report_enabled,
    )


def _add_profile_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        metavar="NAME_OR_ABSOLUTE_PATH",
        help="Project-local profile name or exact absolute profile path.",
    )


def _add_execution_arguments(parser: argparse.ArgumentParser) -> None:
    _add_profile_argument(parser)
    add_resource_override_arguments(parser)
    add_log_arguments(parser)
    parser.add_argument(
        "--no-report", action="store_true", help="Skip reporting after Results."
    )
    parser.add_argument(
        "--execute", action="store_true", help="Execute noninteractively."
    )


def _add_run_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("run", nargs="?", metavar="RUN", help="Run name or ID prefix.")
    onboarding.add_project_argument(parser)


def configure_run_parser(parser: argparse.ArgumentParser) -> None:
    onboarding.add_project_argument(parser)
    parser.add_argument(
        "--analysis",
        help="Named Analysis; required only when the Project defines more than one.",
    )
    parser.add_argument(
        "--through",
        choices=("analysis", "processing"),
        default="analysis",
        help=(
            "Run a complete analysis (default) or stop after per-sample "
            "processing through Step 06."
        ),
    )
    parser.add_argument(
        "--from-processing-run",
        help=(
            "Reuse one successful processing Run name or ID from this Project and "
            "execute only the selected Analysis's downstream work."
        ),
    )
    _add_execution_arguments(parser)


def configure_resume_parser(parser: argparse.ArgumentParser) -> None:
    _add_run_selector(parser)
    _add_execution_arguments(parser)


def configure_report_parser(parser: argparse.ArgumentParser) -> None:
    _add_run_selector(parser)
    _add_profile_argument(parser)
    add_log_arguments(parser)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Generate reports when absent. Without this flag, write nothing.",
    )


def configure_inspect_parser(parser: argparse.ArgumentParser) -> None:
    _add_run_selector(parser)
    add_log_root_argument(parser)
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the exact selection; r refreshes Run verification. Read-only unless --actions is selected.",
    )
    parser.add_argument(
        "--actions",
        action="store_true",
        help="Enable interactive watch handoffs: p resume plan/confirm, b report preview for a Run; s stop preview for a submission. Run handoffs use the default profile.",
    )
    parser.add_argument(
        "--job-id",
        nargs="?",
        const="auto",
        metavar="JOB_ID",
        help="Watch a scheduler job without Project admission; omit JOB_ID to discover a current-user EMRYS job. Cannot authorize actions.",
    )
    parser.add_argument(
        "--log-dir",
        help="Absolute scheduler log directory for historical job selection.",
    )
    parser.add_argument("--out", help="Explicit scheduler stdout for --offline.")
    parser.add_argument("--err", help="Explicit scheduler stderr for --offline.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Read an explicit job and log pair without any scheduler queries.",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Dashboard diagnostic refresh interval, at least 5 seconds (default 30).",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Print one plain dashboard snapshot without entering the interactive terminal.",
    )
    parser.add_argument(
        "--submission",
        metavar="REQUEST",
        help="Inspect one exact request directory name or absolute path and query its scheduler state; excludes a Run selector.",
    )
    parser.add_argument(
        "--detail",
        choices=("normal", "verbose", "debug"),
        default="normal",
        help="Select static inspection detail; --watch has overview, details and evidence/log views.",
    )


def configure_stop_parser(parser: argparse.ArgumentParser) -> None:
    onboarding.add_project_argument(parser)
    parser.add_argument(
        "--submission",
        required=True,
        metavar="REQUEST",
        help="Exact retained request directory name or absolute path; no job-ID or Run aliases.",
    )
    add_log_arguments(parser)
    parser.add_argument(
        "--execute", action="store_true", help="Issue the previewed stop request."
    )


def _print_safe(value: object, *, file: TextIO | None = None) -> None:
    rendered = _inspection_presentation.safe_text(value)
    if file is sys.stderr:
        console_print(rendered, style="red")
    else:
        print(rendered, file=file)


def _run_or_resume_from_args(
    arguments: argparse.Namespace,
    command: str,
) -> int:
    """Admit the shared public control context, then build the selected plan."""

    try:
        overrides = overrides_from_args(arguments)
        if command == "resume":
            project_path, run_root = _resolve_run_argument(arguments)
        else:
            project_path = onboarding.project_definition_path(
                getattr(arguments, "project", None)
            )
            arguments.project = project_path
            run_root = None
        workspace = project_path.parent
        profile, scheduler_job_id = _resolve_execution_profile(
            arguments,
            project_path,
            overrides,
            resume_run_root=run_root,
        )
        report_enabled = not getattr(arguments, "no_report", False)
        if command == "run":
            source_run_id = None
            source_selector = getattr(arguments, "from_processing_run", None)
            if source_selector is not None:
                source_run_id = _select_project_run(
                    project_path,
                    source_selector,
                    interactive=False,
                ).name
                arguments.from_processing_run = source_run_id
            build_plan = partial(
                _plan_run,
                project_path,
                execution_profile=profile,
                analysis_name=getattr(arguments, "analysis", None),
                through=getattr(arguments, "through", "analysis"),
                processing_source_run_id=source_run_id,
                scheduler_job_id=scheduler_job_id,
                report_enabled=report_enabled,
            )
        else:
            build_plan = partial(
                _plan_resume,
                run_root,
                execution_profile=profile,
                resource_overrides=overrides,
                scheduler_job_id=scheduler_job_id,
                report_enabled=report_enabled,
            )
        return _finish_control(
            arguments,
            command=command,
            profile=profile,
            build_plan=build_plan,
            controls=_resolve_controls(arguments, workspace),
            overrides=overrides,
            scheduler_job_id=scheduler_job_id,
            workspace=workspace,
        )
    except _CONTROL_ERRORS as exc:
        return _control_failure(exc)


def run_from_args(arguments: argparse.Namespace) -> int:
    return _run_or_resume_from_args(arguments, "run")


def resume_from_args(arguments: argparse.Namespace) -> int:
    return _run_or_resume_from_args(arguments, "resume")


def _print_reporting_outcome(
    outcome: reporting_operation.ReportingOperationOutcome,
) -> None:
    console_print(
        f"Reporting: {outcome.status}",
        style="green" if outcome.status != "planned" else "blue",
    )
    for line in _verified_report_location_lines(outcome.verified_report_locations):
        console_print(line)


def report_from_args(
    arguments: argparse.Namespace,
) -> int:
    try:
        project_path, root = _resolve_run_argument(arguments)
        workspace = project_path.parent
    except (
        ControlError,
        inspection.InspectionError,
        onboarding.OnboardingError,
    ) as exc:
        return _control_failure(exc)
    if not arguments.execute:
        try:
            planned = reporting_operation.run_reporting(root, execute=False)
            if planned.status == "planned":
                profile, _job_id = _resolve_execution_profile(
                    arguments, project_path, ResourceOverrides()
                )
                for line in profile.submission_summary():
                    console_print(line)
        except (
            *_CONTROL_ERRORS,
            reporting_operation.ReportingOperationError,
            OSError,
        ) as exc:
            console_print(f"emrys: error: {exc}")
            return 2
        _print_reporting_outcome(planned)
        if planned.status == "planned":
            console_print("Dry-run complete; no reporting state was written.")
        return 0

    try:
        overrides = ResourceOverrides()
        profile, scheduler_job_id = _resolve_execution_profile(
            arguments, project_path, overrides
        )
        if isinstance(profile.placement, SlurmPlacement) and scheduler_job_id is None:
            return _schedule(
                "report",
                arguments,
                profile,
                _resolve_controls(arguments, workspace),
                overrides,
                workspace,
            )
    except _CONTROL_ERRORS as exc:
        return _control_failure(exc)

    execution_attempt_id = f"application-{uuid.uuid4().hex}"
    attempt = None

    def close_log_best_effort() -> None:
        if attempt is not None:
            with suppress(Exception):
                attempt.close()

    def observe_generation_start() -> None:
        nonlocal attempt
        try:
            controls = _resolve_controls(arguments, workspace)
            attempt = open_attempt_log(
                controls=controls,
                identity=AttemptIdentity(
                    "run",
                    root.name,
                    execution_attempt_id,
                    "emrys-report",
                ),
                mode="report",
                component="reporting",
                scheduler_environment=os.environ,
            )
            _record_submission_context(attempt, workspace)
            attempt.logger(component="reporting", phase="execute").info(
                "Generating downstream reports.",
                extra=event("reporting_started", fields={"run_root": field(root)}),
            )
        except Exception as exc:
            close_log_best_effort()
            attempt = None
            console_print(
                "WARNING: Application logging unavailable for reporting; "
                f"publication remains controlled by reporting receipts: {exc}",
            )

    try:
        completed = reporting_operation.run_reporting(
            root,
            execute=True,
            observe_generation_start=observe_generation_start,
        )
    except (reporting_operation.ReportingOperationError, OSError) as exc:
        if attempt is not None:
            with suppress(Exception):
                attempt.fail(
                    phase="reporting",
                    message="Downstream reporting failed.",
                    fields={"error": field(str(exc))},
                )
        close_log_best_effort()
        console_print(f"emrys: error: {exc}")
        console_print(
            "Scientific Results remain complete; reporting state was preserved for inspection.",
        )
        return 1
    if attempt is not None:
        try:
            attempt.terminal(
                event_name="reporting_completed",
                message="Downstream reports are verified.",
                fields={"reporting_status": field(completed.status)},
            )
        except Exception:
            console_print(
                "WARNING: Reporting completed, but application logging degraded.",
            )
    close_log_best_effort()
    _print_reporting_outcome(completed)
    return 0


def _print_submission_roster(project: Path, selector: str | None = None) -> None:
    requests = (
        (slurm_submission.select_submission_request(project, selector),)
        if selector is not None
        else slurm_submission.submission_requests(project)
    )
    print("Retained submissions:")
    if not requests:
        print("  None found; this does not establish that no job was submitted.")
        return
    for request in requests:
        _print_safe(f"  Request: {request.request_root}")
        print(f"    Records: {request.record_status.replace('-', ' ')}")
        if request.context is not None:
            context = request.context
            _print_safe(
                f"    Command: {context['command']}; recorded time: {context['created_at']}; "
                f"requested Run: {context['requested_run'] or 'new Run'}"
            )
            _print_safe(f"    Application logs: {context['application_log_root']}")
            if "scheduler_job_name" in context:
                _print_safe(
                    f"    Recorded scheduler name: {context['scheduler_job_name']}"
                )
            if selector is not None:
                for stream in ("stdout", "stderr"):
                    path = context[f"scheduler_{stream}_pattern"].replace(
                        "%j", request.recorded_job_id or "%j"
                    )
                    _print_safe(f"    Recorded scheduler {stream}: {path}")
        _print_safe(
            f"    Recorded response job ID: {request.recorded_job_id or 'unconfirmed'}; "
            f"cluster: {request.recorded_cluster or 'not recorded'}"
        )
        if request.stderr_excerpt:
            _print_safe(
                "    Scheduler stderr excerpt: "
                + request.stderr_excerpt.decode("utf-8", "replace")
            )
        for diagnostic in request.diagnostics:
            _print_safe(f"    Observation: {diagnostic}")
        if selector is not None:
            with phase_progress("Reading scheduler state for the selected request"):
                scheduler = slurm_submission.observe_submission_request(request)
            _print_safe(
                f"    Scheduler observation: {scheduler['state']}; "
                f"source: {scheduler['source'] or 'unavailable'}; "
                f"cluster: {scheduler['cluster'] or 'unconfirmed'}"
            )
            for key, label in (
                ("reason", "Queue reason"),
                ("exit_code", "Scheduler exit status"),
                ("diagnostic", "Observation"),
            ):
                if scheduler.get(key):
                    _print_safe(f"    {label}: {scheduler[key]}")
            with phase_progress(
                "Reading application evidence for the selected request"
            ):
                application = _submission_inspection.inspect_submission_application(
                    request
                )
            print(
                f"    Application association: {application.status.replace('-', ' ')}"
            )
            if application.application_log is not None:
                _print_safe(f"    Bound application log: {application.application_log}")
                print(f"    Log snapshot SHA-256: {application.application_log_sha256}")
            if application.recorded_event is not None:
                label = (
                    "Reporting start recorded"
                    if application.recorded_event == "reporting_started"
                    else "Preparation recorded"
                )
                _print_safe(
                    f"    {label}: Run={application.recorded_run_id}; "
                    f"Attempt={application.recorded_workflow_attempt_id or 'not applicable'}"
                )
            for line in _inspection_presentation.application_outcome_lines(application):
                _print_safe(f"    {line}")
            if application.run_root is not None:
                _print_safe(f"    Admitted Run: {application.run_root}")
                if application.workflow_attempt_id is not None:
                    _print_safe(
                        f"    Admitted Attempt record: {application.workflow_attempt_id}"
                    )
                _print_safe(
                    "    Inspect Run evidence: "
                    + shlex.join(
                        [
                            "emrys",
                            "inspect",
                            "--project",
                            str(project),
                            application.run_root.name,
                        ]
                    )
                )
            for diagnostic in application.diagnostics:
                _print_safe(f"    Application observation: {diagnostic}")
    if selector is None:
        print(
            "Current scheduler state and Run association are not established by these records."
        )
        print("Query one exact request with: emrys inspect --submission REQUEST")
    else:
        print(
            "Scheduler and application observations do not establish workflow entry, "
            "Run completion or recovery eligibility, or authorize cancellation."
        )


def stop_from_args(arguments: argparse.Namespace) -> int:
    attempt = None
    try:
        project = onboarding.project_definition_path(arguments.project)
        with phase_progress("Reading the selected stop target and client"):
            plan = slurm_submission.plan_stop(project, arguments.submission)
        context = plan.request.context
        assert context is not None
        controls = resolve_log_controls(
            cli_level=arguments.log_level,
            cli_root=arguments.log_root,
            default_root=Path(str(context["application_log_root"])),
        )
        _print_safe(f"Stop request: {plan.request.request_root}")
        _print_safe(f"Project: {project}")
        _print_safe(
            f"Target: job {plan.request.recorded_job_id}; UID {context['submitter_uid']}; "
            f"cluster {plan.observation['cluster']}; name {context['scheduler_job_name']}"
        )
        _print_safe(f"Scheduler observation: {plan.observation['state']}")
        _print_safe(
            "Inspect retained evidence: "
            + shlex.join(
                [
                    "emrys",
                    "inspect",
                    "--project",
                    str(project),
                    "--submission",
                    plan.request.request_root.name,
                ]
            )
        )
        print(
            "Scheduler state does not prove native-task quiescence or authorize resume."
        )
        if not plan.argv:
            print(
                "The exact scheduler record is already terminal; no stop request is needed."
            )
            return 0
        _print_safe(f"Client: {plan.client_version}; command: {shlex.join(plan.argv)}")
        if not arguments.execute:
            print(
                "Preview only; use --execute to issue this stop request. No files were written."
            )
            return 0
        attempt = open_attempt_log(
            controls=controls,
            identity=AttemptIdentity(
                "maintenance",
                plan.request.request_root.name,
                f"application-{uuid.uuid4().hex}",
                "emrys-stop",
            ),
            mode="stop",
            component="scheduler",
        )
        stdout = attempt.path.parent / "scancel.stdout"
        _print_safe(
            f"Stop diagnostics: {attempt.path}; {stdout}; {stdout.with_suffix('.stderr')}"
        )
        record_intent = partial(
            attempt.intent,
            event_name="slurm_stop_intent",
            message="Exact controller stop request admitted.",
            fields={
                name: field(value)
                for name, value in {
                    "request_root": plan.request.request_root,
                    "project": project,
                    "request_context_sha256": hashlib.sha256(
                        orchestration_contracts.canonical_json_bytes(dict(context))
                    ).hexdigest(),
                    "job_id": plan.request.recorded_job_id,
                    "submitter_uid": context["submitter_uid"],
                    "cluster": plan.observation["cluster"],
                    "scheduler_job_name": context["scheduler_job_name"],
                    "client_version": plan.client_version,
                    "client_file_binding": plan.client_binding,
                    "argv": plan.argv,
                    "stdout": stdout,
                    "stderr": stdout.with_suffix(".stderr"),
                }.items()
            },
        )
        with phase_progress(
            "Rechecking the target, requesting stop and observing the scheduler"
        ):
            result = slurm_submission.stop(
                plan, record_path=stdout, record_intent=record_intent
            )
        if result.invocation_attempted:
            _print_safe(
                f"scancel exit status: {result.returncode if result.returncode is not None else 'unconfirmed'}"
            )
            print(
                "A zero exit status means the controller request was processed; it does not prove the job was cancelled."
            )
        else:
            print(
                "No stop request was sent; the exact scheduler record became terminal."
            )
        _print_safe(
            f"Post-check scheduler observation: {result.observation['state']}; source: {result.observation['source'] or 'unavailable'}"
        )
        for label, value in (
            ("Stop diagnostic", result.diagnostic),
            ("Scheduler diagnostic", result.observation.get("diagnostic")),
            ("scancel stdout", result.stdout_excerpt.decode("utf-8", "replace")),
            ("scancel stderr", result.stderr_excerpt.decode("utf-8", "replace")),
        ):
            if value:
                _print_safe(f"{label}: {value}")
        recorded = attempt.best_effort(
            lambda: attempt.terminal(
                event_name="slurm_stop_observed",
                message="Stop transport and scheduler observations retained.",
                fields={
                    name: field(value)
                    for name, value in {
                        "invocation_attempted": result.invocation_attempted,
                        "returncode": result.returncode,
                        "scheduler": dict(result.observation),
                        "diagnostic": result.diagnostic,
                    }.items()
                },
            ),
            warning="WARNING: stop logging degraded; raw diagnostics are retained and the outcome remains unconfirmed.",
        )
        return (
            0
            if (
                recorded
                and result.observation["terminal"]
                and result.diagnostic is None
                and (not result.invocation_attempted or result.returncode == 0)
            )
            else 1
        )
    except KeyboardInterrupt:
        if attempt is not None:
            attempt.best_effort(
                lambda: attempt.interrupt_best_effort(
                    message="Stop invocation interrupted; submitted request outcome is unconfirmed."
                ),
                warning="WARNING: stop interruption logging degraded; retained diagnostics remain controlling.",
            )
        print(
            "Stop interrupted; any issued controller request may have been processed. Inspect retained evidence before another request.",
            file=sys.stderr,
        )
        return 130
    except (
        slurm_submission.SlurmSubmissionError,
        onboarding.OnboardingError,
        ApplicationLogError,
        LogControlError,
        ValueError,
        OSError,
    ) as exc:
        error = str(exc)
        if attempt is not None:
            attempt.best_effort(
                lambda: attempt.fail(
                    phase="stop",
                    message="Stop failed or was refused.",
                    fields={"error": field(error)},
                ),
                warning="WARNING: stop failure logging degraded; retained diagnostics were preserved.",
            )
        _print_safe(f"emrys: error: {exc}", file=sys.stderr)
        return 2
    finally:
        if attempt is not None:
            with suppress(Exception):
                attempt.close()


def _watch_review_actions(
    project: Path, selection: Path, *, submission: bool = False
) -> tuple[tuple[bytes, str, Callable[[], int]], ...]:
    """Capture exact selectors; leave fresh admission to each public CLI owner."""
    selected = ("--submission", str(selection)) if submission else (selection.name,)
    commands = (
        ((b"s", "stop preview", "stop", configure_stop_parser, stop_from_args),)
        if submission
        else (
            (
                b"p",
                "resume plan/confirm",
                "resume",
                configure_resume_parser,
                resume_from_args,
            ),
            (
                b"b",
                "report preview",
                "report",
                configure_report_parser,
                report_from_args,
            ),
        )
    )

    def review(command, configure, handler):
        parser = argparse.ArgumentParser(prog=f"emrys {command}")
        configure(parser)
        argv = ["--project", str(project), *selected]
        _print_safe("Reviewing: " + shlex.join(["emrys", command, *argv]))
        return handler(parser.parse_args(argv))

    return tuple(
        (key, label, partial(review, command, configure, handler))
        for key, label, command, configure, handler in commands
    )


def inspect_from_args(
    arguments: argparse.Namespace,
) -> int:
    try:
        submission_selector = getattr(arguments, "submission", None)
        explicit_run = getattr(arguments, "run", None) is not None
        cli_log_root = getattr(arguments, "log_root", None)
        if cli_log_root is not None and (
            submission_selector is not None or not explicit_run
        ):
            raise ControlError(
                "--log-root requires a Run selector and cannot override --submission evidence"
            )
        if (
            submission_selector is not None
            and getattr(arguments, "run", None) is not None
        ):
            raise ControlError("Select a submission or a Run, not both")
        snapshot_only = getattr(arguments, "snapshot", False)
        watching = getattr(arguments, "watch", False) or snapshot_only
        actions = getattr(arguments, "actions", False)
        refresh_seconds = getattr(arguments, "refresh", 30)
        if refresh_seconds < 5:
            raise ControlError("--refresh must be at least 5 seconds")
        raw_selector = getattr(arguments, "job_id", None)
        raw_mode = raw_selector is not None or any(
            getattr(arguments, key, None)
            for key in ("log_dir", "out", "err", "offline")
        )
        if (
            watching
            and not raw_mode
            and not actions
            and not explicit_run
            and submission_selector is None
            and getattr(arguments, "project", None) is None
        ):
            try:
                Path("project.yaml").lstat()
            except FileNotFoundError:
                raw_mode = True
        if raw_mode:
            if not watching:
                raise ControlError(
                    "Scheduler dashboard selection requires --watch or --snapshot"
                )
            if (
                actions
                or explicit_run
                or submission_selector is not None
                or getattr(arguments, "project", None) is not None
                or cli_log_root is not None
            ):
                raise ControlError(
                    "Scheduler diagnostic selection excludes Project, Run, submission, log-root and action selectors"
                )
            from . import dashboard

            selected = dashboard.resolve_selection(
                (os.environ.get("EMRYS_DASHBOARD_JOB_ID", "").strip() or None)
                if raw_selector in (None, "auto")
                else raw_selector,
                getattr(arguments, "log_dir", None)
                or os.environ.get("EMRYS_DASHBOARD_LOG_DIR", "").strip()
                or None,
                getattr(arguments, "out", None),
                getattr(arguments, "err", None),
                getattr(arguments, "offline", False),
            )
            return _inspection_presentation.watch(
                None,
                raw_job=selected,
                offline=getattr(arguments, "offline", False),
                refresh_seconds=refresh_seconds,
                snapshot_only=snapshot_only,
                inspect_run=inspection.inspect_run,
                next_action=_next_supported_action,
            )
        if actions and not watching:
            raise ControlError("--actions requires --watch")
        if actions and snapshot_only:
            raise ControlError("--actions cannot be used with --snapshot")
        if actions:
            _inspection_presentation.require_action_terminal()
        if getattr(arguments, "run", None) is None:
            project = onboarding.project_definition_path(
                getattr(arguments, "project", None)
            )
            if watching and submission_selector is not None:
                request = slurm_submission.select_submission_request(
                    project, submission_selector
                )
                return _inspection_presentation.watch(
                    project,
                    request=request,
                    inspect_run=inspection.inspect_run,
                    next_action=_next_supported_action,
                    refresh_seconds=refresh_seconds,
                    snapshot_only=snapshot_only,
                    review_actions=(
                        _watch_review_actions(
                            project, request.request_root, submission=True
                        )
                        if actions
                        else ()
                    ),
                )
            if not watching:
                _print_submission_roster(project, submission_selector)
            if submission_selector is not None:
                return 0
        try:
            _project_path, run_root = _resolve_run_argument(arguments)
        except _NoProjectRuns:
            print("Runs: none found at inspection time.")
            print(
                "Do not submit again solely because a Run is absent; retain the submission records."
            )
            return 0
        log_root = (
            None
            if not explicit_run
            else resolve_log_root(
                cli_root=cli_log_root,
                default_root=_project_path.parent / "logs" / "application",
            )[0]
        )
        if watching:
            return _inspection_presentation.watch(
                _project_path,
                run_root=run_root,
                application_log_root=log_root,
                inspect_run=inspection.inspect_run,
                next_action=_next_supported_action,
                refresh_seconds=refresh_seconds,
                snapshot_only=snapshot_only,
                review_actions=(
                    _watch_review_actions(_project_path, run_root) if actions else ()
                ),
            )
        observed = inspection.inspect_run(run_root)
        applications = (
            None
            if log_root is None
            else _submission_inspection.inspect_run_applications(
                _project_path, run_root, log_root
            )
        )
        detail = getattr(arguments, "detail", "normal")
        milestones = _inspection_presentation.milestone_progress(
            observed.tasks,
            processing_source_state=(
                None
                if observed.processing_source_run_id is None
                else "reused"
                if observed.processing_source is not None
                else "blocked"
            ),
        )
        elapsed = _inspection_presentation.attempt_elapsed_line(observed)
        result_lines = _verified_report_location_lines(
            observed.verified_report_locations
        )
    except (
        OSError,
        inspection.InspectionError,
        _inspection_presentation.PresentationError,
        slurm_submission.scheduler_observation.DiscoveryError,
        onboarding.OnboardingError,
        ControlError,
        LogControlError,
        slurm_submission.SlurmSubmissionError,
    ) as exc:
        return _control_failure(exc)
    print(f"Run: {inspection.human_run_name(run_root.name)}")
    if applications is not None:
        for line in _inspection_presentation.run_application_lines(
            applications, detail=detail
        ):
            _print_safe(line)
    print(f"Run admission: {observed.integrity}")
    print(f"Run lock: {observed.lock_observation}")
    latest = observed.latest_attempt
    if latest is not None and observed.lock_observation in {
        "local live owner",
        "remote ownership unverified",
        "local process not live",
    }:
        _print_safe(
            f"Recorded lock host: {latest['host']}; scheduler job: "
            f"{(latest.get('placement') or {}).get('scheduler_job_id') or 'none'}"
        )
    print(f"Attempt outcome: {observed.attempt_outcome}")
    print(elapsed)
    if observed.processing_source_run_id is not None:
        source_state = (
            "admitted" if observed.processing_source is not None else "blocked"
        )
        print(
            "Processing source: "
            f"{inspection.human_run_name(observed.processing_source_run_id)} "
            f"({source_state})"
        )
    print("Scientific milestones:")
    for label, state, verified, total in milestones:
        print(f"  {label}: {state}")
        if detail != "normal":
            if observed.processing_source_run_id is None or total:
                print(f"    Verified tasks: {verified}/{total}")
    if observed.tasks:
        print("Scientific task observations:")
        for label, count in Counter(
            _inspection_presentation.task_observation(task) for task in observed.tasks
        ).items():
            print(f"  {label}: {count}")
    terminal_attempts = tuple(
        terminal for task in observed.tasks for terminal in task.terminal_attempts
    )
    print(f"Recorded Task attempts: {len(terminal_attempts)}")
    if terminal_attempts:
        print("Recorded outcomes do not establish verified scientific completion.")
        if detail == "normal":
            print(
                "Use --detail verbose for recorded outcomes and content-bound log paths."
            )
    print(f"Scientific Results: {observed.results_status}")
    print(f"Reporting admission: {observed.reporting_status}")
    if observed.reporting_status != "not applicable":
        print("Reporting transactions:")
        for kind, records in observed.reporting_completion_records.items():
            state = _inspection_presentation.reporting_observation(records)
            print(f"  {kind}: {state}")
    receipt = observed.latest_receipt
    if detail != "normal":
        print(f"Run ID: {observed.run_id}")
        if observed.processing_source_run_id is not None:
            print(f"Processing source Run ID: {observed.processing_source_run_id}")
        authority = observed.authority
        if authority is not None:
            print(f"Analysis ID: {authority.analysis_revision.analysis_revision_id}")
            print(f"Execution Plan ID: {authority.execution_plan.execution_plan_id}")
        _print_safe(f"Run root: {observed.run_root}")
        attempt_id = "none" if latest is None else latest["workflow_attempt_id"]
        print(f"Attempt ID: {attempt_id}")
        if latest is not None:
            placement = latest.get("placement")
            placement_kind = "unrecorded" if placement is None else placement["kind"]
            scheduler_job_id = (
                "none" if placement is None else placement["scheduler_job_id"] or "none"
            )
            _print_safe(
                f"Execution: {latest['executor']}/{latest['execution_mode']} "
                f"placement={placement_kind} scheduler_job_id={scheduler_job_id}"
            )
    if detail != "normal" and terminal_attempts:
        print("Recorded Task outcomes and logs:")
        for terminal in terminal_attempts:
            record = terminal.record
            _print_safe(
                f"  TASK {record['machine_key']}/{record['scope']['scope_id']}: "
                f"recorded {record['status']}; Attempt {record['workflow_attempt_id']}"
            )
            _print_safe(
                f"    record: {observed.run_root / terminal.record_reference['path']}"
            )
            if record["failure_message"] is not None:
                _print_safe(f"    failure: {record['failure_message']}")
    if detail != "normal":
        streams = _inspection_presentation.task_stream_sources(observed)
        if streams:
            print(
                "Task diagnostic streams (paths do not establish existence or liveness):"
            )
            for source in streams:
                _print_safe(f"  {source.label}: {source.path}")
    if detail == "debug":
        authority = observed.authority
        print("Run authority records:")
        for label, name, record in (
            ("Analysis", "analysis.json", authority.analysis_revision),
            ("Execution Plan", "execution-plan.json", authority.execution_plan),
            ("Run", "run.json", authority.run_binding),
        ):
            path = observed.run_root / "contract" / name
            _print_safe(f"  {label}: path={path}; SHA-256={record.record_sha256}")
        plan_identity = authority.execution_plan.record["identity"]
        backend = plan_identity["backend"]
        resources = plan_identity["computational_resources"]
        _print_safe(
            "Effective plan: "
            f"backend={backend['backend']}; engine={backend['engine']}; "
            f"cores={resources['workflow_cores']}; "
            f"memory_mib={resources['workflow_memory_mb']}"
        )
        if latest is not None:
            attempt_id = str(latest["workflow_attempt_id"])
            attempt_root = observed.run_root / "attempts" / attempt_id
            receipt_path = (
                "none" if receipt is None else attempt_root / "attempt-receipt.json"
            )
            _print_safe(f"Attempt receipt: {receipt_path}")
            _print_safe(f"Engine command: {shlex.join(latest['snakemake_argv'])}")
            if receipt is not None:
                _print_safe(
                    "Attempt receipt result: "
                    f"exit={receipt['snakemake_exit_code']} "
                    f"signal={receipt['termination_signal']} "
                    f"message={receipt['message']}"
                )
        print("Task records:")
        for task in observed.tasks:
            identity = f"{task.expected.machine_key}/{task.expected.scope_id}"
            task_detail = (
                f"  TASK {identity}: {_inspection_presentation.task_observation(task)}"
            )
            if task.start_reference is not None:
                task_detail += (
                    f"; start={observed.run_root / task.start_reference['path']}"
                )
            if task.record_reference is not None:
                task_detail += (
                    f"; verified={observed.run_root / task.record_reference['path']}"
                )
            if task.record is not None:
                attempt_path = (
                    task_boundary.task_attempt_root(
                        observed.run_root,
                        task.record["workflow_attempt_id"],
                        task.expected.machine_key,
                        task.expected.scope_id,
                    )
                    / "task-attempt.json"
                )
                task_detail += (
                    f"; attempt={attempt_path}"
                    f"; stdout={attempt_path.with_name('stdout.log')}"
                    f"; stderr={attempt_path.with_name('stderr.log')}"
                )
            _print_safe(task_detail)
            for output in () if task.record is None else task.record["outputs"]:
                _print_safe(
                    f"    OUTPUT {output['role']}: path={output['path']}; "
                    f"size={output['size_bytes']}; SHA-256={output['sha256']}"
                )
    for blocker_label, blockers in (
        ("RUN BLOCKER", observed.integrity_blockers),
        ("RESULTS BLOCKER", observed.results_blockers),
        ("REPORTING BLOCKER", observed.reporting_blockers),
        ("ATTEMPT EVIDENCE BLOCKER", observed.receipt_blockers),
    ):
        for blocker in blockers:
            _print_safe(f"{blocker_label}: {blocker}")
    print(f"Recovery available: {'yes' if observed.recovery_available else 'no'}")
    _print_safe(f"Next supported action: {_next_supported_action(observed)}")
    for line in result_lines:
        _print_safe(line)
    return 0


__all__ = (
    "ControlError",
    "INSPECT_DESCRIPTION",
    "REPORT_DESCRIPTION",
    "RESUME_DESCRIPTION",
    "RUN_DESCRIPTION",
    "STOP_DESCRIPTION",
    "configure_inspect_parser",
    "configure_stop_parser",
    "configure_report_parser",
    "configure_resume_parser",
    "configure_run_parser",
    "inspect_from_args",
    "stop_from_args",
    "report_from_args",
    "resume_from_args",
    "run_from_args",
)
