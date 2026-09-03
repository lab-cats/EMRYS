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
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, TextIO

from simple_term_menu import TerminalMenu

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    PROCESSING_STEP_IDS,
    execution_plan_boundary,
)
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
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes
from emrys.orchestration.run_coordinator import (
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
    HistoricalRun,
    MaterializationError,
    admit_run,
    build_attempt_plan,
    build_run_candidate,
    processing_stopping_owner_keys,
    publish_attempt,
    validate_run_destination,
)
from emrys.orchestration.run_coordinator.normalization import _historical_execution_v1
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
    "Derive one Run state from immutable EMRYS records without reading or repairing Snakemake metadata."
)
REPORT_DESCRIPTION = (
    "Plan, generate, or reuse the fixed reports for one completed immutable Run. "
    "Dry-run is the default and reporting never creates a scientific Attempt."
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


class _RunSelectionCancelled(ControlError):
    """The operator left the read-only Run picker without selecting a Run."""


_CONTROL_ERRORS = (
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
        raise ControlError(f"Project has no Runs: {project_path.parent}")
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
            "Multiple Runs exist; select one explicitly:\n" + "\n".join(choices)
        )
    try:
        selected = TerminalMenu(choices, title="Select a Run:").show()
    except (EOFError, KeyboardInterrupt) as exc:
        raise _RunSelectionCancelled("Run selection canceled; nothing was changed.") from exc
    if selected is None:
        raise _RunSelectionCancelled("Run selection canceled; nothing was changed.")
    return run_roots[selected]


def _resolve_run_argument(
    arguments: argparse.Namespace,
) -> tuple[Path, Path]:
    project_path = onboarding.project_definition_path(getattr(arguments, "project", None))
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


def _load_config_reference(
    run_root: Path,
    attempt: Mapping[str, Any],
) -> dict[str, Any]:
    reference = attempt["workflow_config"]
    path = run_root / str(reference["path"])
    try:
        data = read_bytes(path, "prior workflow config")
    except ValidationError as exc:
        raise ControlError(f"Prior workflow config is unavailable: {path}") from exc

    if hashlib.sha256(data).hexdigest() != reference["sha256"]:
        raise ControlError("Prior workflow config differs from its attempt reference")
    try:
        value = orchestration_contracts.load_json_object_bytes(data, path)
    except orchestration_contracts.ContractValidationError as exc:
        raise ControlError(str(exc)) from exc
    if orchestration_contracts.canonical_json_bytes(value) != data:
        raise ControlError("Prior workflow config does not use canonical JSON bytes")
    return value


def _admit_resume_predecessor(
    run_root: Path,
) -> tuple[inspection.RunInspection, dict[str, Any], dict[str, Any]]:
    """Admit the one recoverable predecessor and its bound workflow config."""

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
    return observed, previous, _load_config_reference(root, previous)


def _resume_predecessor_policy(
    observed: inspection.RunInspection,
    predecessor_config: Mapping[str, Any],
    overrides: ResourceOverrides,
    reporting_overlay=(),
) -> ResourcePolicy:
    """Re-admit the predecessor policy without observing an allocation."""

    prior = predecessor_config.get("resource_policy")
    if not isinstance(prior, dict):
        raise ControlError("Prior workflow config has no resource policy")
    try:
        has_symbolic_policy = (
            "symbolic" in prior or "symbolic_sha256" in prior
        )
        predecessor: ResourcePolicy | Mapping[str, Any] = (
            admit_resource_policy_record(prior, require_symbolic=True).policy
            if observed.authority is not None or has_symbolic_policy
            else prior
        )
        return resume_resource_policy(
            predecessor, reporting_overlay=reporting_overlay, overrides=overrides
        )
    except ResourceConfigError as exc:
        raise ControlError(str(exc)) from exc


def _retained_dispatches(
    observed: inspection.RunInspection,
    config: Mapping[str, Any],
) -> tuple[dict[tuple[str, str], dict[str, str]], bytes | None]:
    dispatches = config.get("dispatch_paths")
    if not isinstance(dispatches, dict):
        raise ControlError("Prior workflow config has no closed dispatch map")
    retained: dict[tuple[str, str], dict[str, str]] = {}
    selected_manifest: bytes | None = None
    selected_projection: bool | None = None
    for inspected in observed.tasks:
        if inspected.state != "verified":
            continue
        try:
            reference = dispatches[inspected.expected.machine_key][
                inspected.expected.scope_id
            ]
        except (KeyError, TypeError) as exc:
            raise ControlError(
                "Prior workflow config omits a reusable verified dispatch: "
                f"{inspected.expected.machine_key}/{inspected.expected.scope_id}"
            ) from exc
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ControlError("Prior reusable dispatch reference is malformed")
        path = Path(str(reference["path"]))
        try:
            dispatch = task_boundary.load_dispatch(
                path,
                expected_sha256=str(reference["sha256"]),
            )
        except task_boundary.TaskBoundaryError as exc:
            raise ControlError(f"Reusable dispatch is unavailable: {path}: {exc}") from exc
        retained[(inspected.expected.machine_key, inspected.expected.scope_id)] = dict(
            reference
        )
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
            raise ControlError("Reusable Step 07 dispatches disagree on sample projection")
        selected_projection = projected
        if not projected:
            continue
        if declaration.expected_binding is None:
            raise ControlError("Reusable Step 07 sample projection is not content-bound")
        try:
            data = read_bytes(manifest_path, "reusable Step 07 sample projection")
        except ValidationError as exc:
            raise ControlError(
                f"Reusable Step 07 sample projection is unavailable: {manifest_path}"
            ) from exc
        binding = (len(data), hashlib.sha256(data).hexdigest())
        if binding != declaration.expected_binding:
            raise ControlError("Reusable Step 07 sample projection differs from its binding")
        if selected_manifest is not None and data != selected_manifest:
            raise ControlError("Reusable Step 07 dispatches disagree on sample projection")
        selected_manifest = data
    return retained, selected_manifest


def _retained_runtime_profile_path(
    predecessor: Mapping[str, Any],
) -> Path:
    """Re-admit the predecessor's one exact retained runtime profile binding."""

    retained = tuple(identity for identity in predecessor["required_tools"] if identity["name"] == "runtime_profile")
    if len(retained) != 1:
        raise ControlError("Predecessor attempt does not bind one retained runtime profile")
    identity = retained[0]
    path = Path(str(identity["path"]))
    resolved = Path(str(identity["resolved_path"]))
    try:
        data = read_bytes(path, "retained runtime profile")
        observed = path.resolve(strict=True)
    except (OSError, ValidationError) as exc:
        raise ControlError(f"Retained runtime profile is unavailable: {path}: {exc}") from exc
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
    retained: Path | None,
) -> Path:
    """Prefer a historical Attempt's retained runtime over Project state."""

    if retained is not None:
        return retained
    candidate = onboarding.runtime_profile_path(project_path)
    return (
        candidate
        if os.path.lexists(candidate)
        else _retained_runtime_profile_path(predecessor)
    )


def _predecessor_source_schema(
    root: Path,
    predecessor: Mapping[str, Any],
) -> str:
    identifier = str(predecessor["workflow_attempt_id"])
    path = root / "attempts" / identifier / "request.yaml"
    try:
        data = read_bytes(path, "predecessor Project snapshot")
        reference = predecessor["request"]
        identity = (len(data), hashlib.sha256(data).hexdigest())
        if identity != (reference["size_bytes"], reference["sha256"]):
            raise ControlError("Predecessor Project snapshot differs from its binding")
        schema = orchestration_contracts.load_yaml_object_bytes(data)["schema_version"]
    except (
        KeyError,
        TypeError,
        ValidationError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        raise ControlError(f"Could not admit predecessor Project snapshot: {exc}") from exc
    if schema not in ("emrys.project.v1", "emrys.request.v3"):
        raise ControlError(f"Unsupported predecessor Project schema: {schema!r}")
    return schema


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
    observed, previous, predecessor_config = _admit_resume_predecessor(root)
    predecessor_schema = _predecessor_source_schema(root, previous)
    legacy_source = predecessor_schema == "emrys.request.v3"
    project_path = Path(str(previous["authored_paths"]["request"]))
    workspace = Path(str(previous["workspace"]))
    retained_runtime_profile = _retained_runtime_profile_path(previous) if observed.authority is None else None
    runtime_profile = _resume_runtime_profile_path(
        project_path,
        previous,
        retained_runtime_profile,
    )
    try:
        readiness = doctor.diagnose_project(
            project_path,
            workspace,
            runtime_profile,
            storage_requirement=execution_profile.placement.kind,
            analysis_name=None if legacy_source else previous.get("request_label"),
            expected_analysis_revision=(
                None
                if observed.authority is None
                else observed.authority.analysis_revision
            ),
            allow_legacy=legacy_source,
            require_reporter=report_enabled
            and (
                observed.authority is None
                or execution_plan_boundary(
                    observed.authority.execution_plan
                )
                == "analysis"
            ),
        )
        _require_ready(readiness)
        analysis = readiness.analysis
        retained_dispatches, retained_sample_manifest = _retained_dispatches(
            observed,
            predecessor_config,
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
                observed,
                predecessor_config,
                resource_overrides,
                execution_profile.selected_reporting_memory,
            )
            execution_profile = replace(
                execution_profile,
                resource_policy=policy,
            )
        processing_source = observed.processing_source
        if observed.authority is not None:
            candidate = build_run_candidate(
                analysis,
                readiness,
                policy.declaration,
                scientific_stopping_owner_keys=observed.authority.execution_plan.record[
                    "identity"
                ]["scientific_stopping_owner_keys"],
                processing_source=(
                    None if processing_source is None else processing_source.binding
                ),
            )
            if candidate.run_binding.canonical_bytes != observed.authority.run_binding.canonical_bytes:
                raise ControlError("Current inputs resolve to a different Run")
            run = candidate
        else:
            legacy_execution, legacy_bytes = _historical_execution_v1(analysis)
            fixed_execution = root / "contract/normalized.json"
            if legacy_execution["run_id"] != observed.run_id:
                raise ControlError("Current Project resolves to a different Run")
            if (
                fixed_execution.is_symlink()
                or not fixed_execution.is_file()
                or fixed_execution.read_bytes() != legacy_bytes
            ):
                raise ControlError("Current Project differs from immutable Run bytes")
            run = HistoricalRun(
                analysis=analysis,
                run_id=observed.run_id,
                execution_projection_bytes=legacy_bytes,
            )
        resources = resolve_resource_policy(policy, capacity.observe_allocation())
        plan = build_attempt_plan(
            run,
            readiness,
            workspace,
            resources=resources,
            operation="resume",
            supersedes_workflow_attempt_id=str(previous["workflow_attempt_id"]),
            retained_dispatches=retained_dispatches,
            retained_runtime_profile_path=retained_runtime_profile,
            placement=execution_profile.attempt_placement(scheduler_job_id),
            processing_source=processing_source,
        )
    except _PLANNING_ERRORS as exc:
        raise ControlError(str(exc)) from exc
    if plan.run_root != root:
        raise ControlError("Resume workspace resolves to a different run root")
    for field in inspection.attempt_fields(observed.authority is not None):
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
        *(f"  {label}: {path}" for label, (_, path) in zip(labels, locations, strict=True)),
    )


def _run_followup(command: str, run_root: Path, run_id: str, *options: str) -> str:
    """Render one human-name Run command that remains complete outside its Project."""

    project_path = run_root.parent.parent / "project.yaml"
    argv = ["emrys", command, inspection.human_run_name(run_id)]
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
    if observed.results_status == "complete":
        if observed.reporting_status == "not applicable":
            return "Inspect this Run's verified scientific artifacts with --detail debug."
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

    values = {
        name: os.environ.get(name)
        for name in (
            slurm_submission.DELEGATE_MARKER_ENV,
            slurm_submission.PROFILE_SHA256_ENV,
            slurm_submission.SUBMIT_UID_ENV,
        )
    }
    delegated = any(value is not None for value in values.values())
    if delegated:
        if any(value is None for value in values.values()):
            raise ControlError("Private Slurm delegate context is incomplete")
        if values[slurm_submission.DELEGATE_MARKER_ENV] != slurm_submission.DELEGATE_MARKER:
            raise ControlError("Private Slurm delegate marker is invalid")
        if values[slurm_submission.SUBMIT_UID_ENV] != str(os.getuid()):
            raise ControlError("Private Slurm delegate UID differs from the current process")
    expected_sha256 = values[slurm_submission.PROFILE_SHA256_ENV] if delegated else None
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
        observed, _previous, predecessor_config = _admit_resume_predecessor(
            resume_run_root
        )
        profile = replace(
            profile,
            resource_policy=_resume_predecessor_policy(
                observed,
                predecessor_config,
                overrides,
                profile.selected_reporting_memory,
            ),
        )
    if (
        resume_run_root is not None
        and expected_sha256 is not None
        and profile.binding_sha256 != expected_sha256
    ):
        raise ExecutionProfileError("Execution-profile binding SHA-256 differs")
    if not delegated:
        return profile, None
    if not isinstance(profile.placement, SlurmPlacement):
        raise ControlError("A private Slurm delegate requires Slurm placement")
    job_id = os.environ.get("SLURM_JOB_ID")
    try:
        profile.attempt_placement(job_id)
    except ExecutionProfileError as exc:
        raise ControlError(str(exc)) from exc
    return profile, job_id


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


def _admit_workspace_location(workspace: Path) -> None:
    source_root = _absolute(Path(__file__).resolve().parents[4])
    try:
        blockers, remediations = doctor.workspace_location_blockers(_absolute(workspace), source_root)
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
        raise ControlError("Scheduler log directory creation requires symbolic-link protection")
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
        raise ControlError(f"Could not securely create scheduler log directory: {log_dir}") from exc
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
        plan.run_root / "attempts" / plan.workflow_attempt_id / "released-run-lock.json",
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
    print("Execute this plan? [y/N] ", end="", file=sys.stderr, flush=True)
    return sys.stdin.readline().strip().casefold() in {"y", "yes"}


def _print_no_write(subject: str) -> None:
    print(f"Dry-run complete; no {subject} state was written.", file=sys.stderr)


def _schedule(
    command: str,
    arguments: argparse.Namespace,
    profile: ExecutionProfile,
    effective_workflow_cores: int,
    controls: LogControls,
    overrides: ResourceOverrides,
    workspace: Path,
) -> int:
    placement = profile.placement
    if (
        isinstance(placement, SlurmPlacement)
        and placement.cpus_per_task < effective_workflow_cores
    ):
        raise ControlError(
            "Slurm CPUs per task cannot be lower than workflow cores: "
            f"{placement.cpus_per_task} < {effective_workflow_cores}"
        )
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
    if controls.level in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        print(f"Execution profile: {profile.source_path}", file=sys.stderr)
        print(f"Scheduler stdout: {submission.stdout_pattern}", file=sys.stderr)
        print(f"Scheduler stderr: {submission.stderr_pattern}", file=sys.stderr)
    if controls.level is LogLevel.DEBUG:
        print("Scheduler command: " + shlex.join(submission.argv), file=sys.stderr)
    if not arguments.execute and not _confirm_execution():
        _print_no_write("scheduler or workspace")
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
        print(
            render_failure_summary(
                entrypoint=entrypoint,
                phase="logging",
                status="failed",
                scope=f"run:{scope_id}",
                execution_attempt_id=execution_attempt_id,
                log_path=None,
                next_action=("Correct the application-log path or permissions, then retry."),
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
        print(
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
            file=sys.stderr,
        )

    try:
        plan = plan_source() if callable(plan_source) else plan_source
    except KeyboardInterrupt:
        log_best_effort(lambda: attempt.interrupt_best_effort(message="Analysis preflight interrupted."))
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
        print(f"emrys: error: {exc}", file=sys.stderr)
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
            log_best_effort(lambda: logger.info("Running analysis.", extra=event("analysis_started")))
        elif event_name == "publication_ready":
            receipt_ready = log_best_effort(
                lambda: attempt.publication_ready(message="Analysis finished; finalizing evidence.")
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
            initial_runtime_inspection=plan.readiness.inspection if build_at_execution else None,
        )
    except (
        MaterializationError,
        lifecycle.LifecycleError,
        OSError,
    ) as exc:
        if receipt_ready:
            log_best_effort(lambda: attempt.receipt_failed(message="Attempt receipt publication failed."))
            log_best_effort(
                lambda: attempt.terminal(
                    event_name="execution_incomplete",
                    message="Analysis execution did not complete.",
                )
            )
        else:
            log_best_effort(lambda: attempt.fail(phase="execute", message="Analysis execution failed."))
        print(f"emrys: error: {exc}", file=sys.stderr)
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
    elif not logging_degraded:
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
        print(f"Evidence: {outcome.receipt_path}", file=sys.stderr)
        if not _reporting_applicable(plan):
            observe_reporting(
                "reporting_not_applicable",
                "Reporting is not applicable to this partial scientific Run.",
            )
            close_log_best_effort()
            print("Reporting: not applicable (partial scientific Run)", file=sys.stderr)
            return 0
        if not report_enabled:
            observe_reporting("reporting_skipped", "Reporting was disabled for this execution.")
            close_log_best_effort()
            print("Reporting: skipped (--no-report)", file=sys.stderr)
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
            print(
                f"emrys: error: Reporting failed after scientific Results completed: {exc}",
                file=sys.stderr,
            )
            print_failure(
                phase="reporting",
                status="failed",
                run_scope=plan.run.run_id,
                next_action=(
                    "Scientific Results remain complete. Inspect the Run, then "
                    f"use {_run_followup('report', plan.run_root, plan.run.run_id, '--execute')}."
                ),
            )
            return 1
        observe_reporting(
            "reporting_completed",
            "Downstream reports are verified.",
            {"reporting_status": field(reported.status)},
        )
        close_log_best_effort()
        result_lines = _verified_report_location_lines(reported.verified_report_locations)
        for line in result_lines:
            print(line, file=sys.stderr)
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
    return isinstance(plan.run, HistoricalRun) or (
        execution_plan_boundary(plan.run.execution_plan) == "analysis"
    )


def _print_plan(plan: AttemptPlan, *, level: LogLevel, report_enabled: bool = True) -> None:
    new_dispatches = plan.new_dispatch_files
    reused = plan.dispatch_count - len(new_dispatches)
    resources = plan.resources
    project_label = plan.run.analysis.source_path.parent.name
    print(f"Project: {project_label!a}", file=sys.stderr)
    print(f"Analysis: {plan.run.analysis.name!a}", file=sys.stderr)
    print(f"Run: {inspection.human_run_name(plan.run.run_id)}", file=sys.stderr)
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
    print(f"Scientific boundary: {boundary}", file=sys.stderr)
    if (
        not isinstance(plan.run, HistoricalRun)
        and (
            processing_source := plan.run.execution_plan.record["identity"].get(
                "processing_source"
            )
        )
        is not None
    ):
        print(
            f"Processing source: {inspection.human_run_name(processing_source['source_run_id'])}",
            file=sys.stderr,
        )
    print(f"Work: {len(new_dispatches)} pending, {reused} reusable", file=sys.stderr)
    print(f"Reporting: {reporting}", file=sys.stderr)
    if level in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        print(f"Run ID: {plan.run.run_id}", file=sys.stderr)
        if not isinstance(plan.run, HistoricalRun) and processing_source is not None:
            print(
                f"Processing source Run ID: {processing_source['source_run_id']}",
                file=sys.stderr,
            )
        print(
            f"Analysis revision: {plan.run.analysis.revision.analysis_revision_id}",
            file=sys.stderr,
        )
        if not isinstance(plan.run, HistoricalRun):
            print(
                f"Execution Plan ID: {plan.run.execution_plan.execution_plan_id}",
                file=sys.stderr,
            )
        print(f"Run root: {plan.run_root}", file=sys.stderr)
        print(
            f"Resources: {resources.workflow_cores} cores, {resources.workflow_memory_mb} MiB",
            file=sys.stderr,
        )
        print("Step thread allocations:", file=sys.stderr)
        for step_id, threads in resources.step_threads:
            print(f"  Step {step_id}: {threads}", file=sys.stderr)
        print("Stage concurrency:", file=sys.stderr)
        for step_id, concurrency in resources.stage_concurrency:
            print(f"  Step {step_id}: {concurrency}", file=sys.stderr)
    if level is LogLevel.DEBUG:
        print(
            "Snakemake command: " + shlex.join(plan.attempt_record["snakemake_argv"]),
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
    effective_workflow_cores: int,
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
            effective_workflow_cores,
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


def _add_execution_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        metavar="NAME_OR_ABSOLUTE_PATH",
        help="Project-local profile name or exact absolute profile path.",
    )
    add_resource_override_arguments(parser)
    add_log_arguments(parser)
    parser.add_argument("--no-report", action="store_true", help="Skip reporting after Results.")
    parser.add_argument("--execute", action="store_true", help="Execute noninteractively.")


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
    add_log_arguments(parser)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Generate reports when absent. Without this flag, write nothing.",
    )


def configure_inspect_parser(parser: argparse.ArgumentParser) -> None:
    _add_run_selector(parser)
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
    *,
    processing_source_state: str | None = None,
) -> tuple[tuple[str, str, int, int], ...]:
    known_steps = {step for _label, steps in _MILESTONE_STEPS for step in steps}
    unknown = sorted({task.expected.step_id for task in tasks} - known_steps)
    if unknown:
        raise ControlError("Inspected task Steps have no public milestone: " + ", ".join(unknown))
    result = []
    for label, steps in _MILESTONE_STEPS:
        members = tuple(task for task in tasks if task.expected.step_id in steps)
        state = (
            processing_source_state
            if processing_source_state is not None
            and not members
            and set(steps).issubset(PROCESSING_STEP_IDS)
            else _progress_state(members)
        )
        result.append(
            (
                label,
                state,
                sum(task.state == "verified" for task in members),
                len(members),
            )
        )
    return tuple(result)


def _attempt_elapsed_line(
    observed: inspection.RunInspection,
) -> str:
    attempt = observed.latest_attempt
    if attempt is None:
        return "Attempt elapsed: unavailable — no Attempt"
    label = "Current" if observed.attempt_outcome == "running" else "Latest"
    try:
        started = datetime.fromisoformat(str(attempt["created_at"]).replace("Z", "+00:00"))
        if observed.attempt_outcome == "running":
            finished = datetime.now(UTC)
        elif observed.latest_receipt is not None:
            finished = datetime.fromisoformat(str(observed.latest_receipt["finished_at"]).replace("Z", "+00:00"))
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


def _print_safe(value: object, *, file: TextIO | None = None) -> None:
    rendered = "".join(
        character if character.isprintable() else ascii(character)[1:-1]
        for character in str(value)
    )
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
        effective_workflow_cores = profile.resource_policy.declaration.workflow_cores
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
            effective_workflow_cores=effective_workflow_cores,
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
    print(f"Reporting: {outcome.status}", file=sys.stderr)
    for line in _verified_report_location_lines(outcome.verified_report_locations):
        print(line, file=sys.stderr)


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
        except (reporting_operation.ReportingOperationError, OSError) as exc:
            print(f"emrys: error: {exc}", file=sys.stderr)
            return 2
        _print_reporting_outcome(planned)
        if planned.status == "planned":
            print("Dry-run complete; no reporting state was written.", file=sys.stderr)
        return 0

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
            attempt.logger(component="reporting", phase="execute").info(
                "Generating downstream reports.",
                extra=event("reporting_started", fields={"run_root": field(root)}),
            )
        except Exception as exc:
            close_log_best_effort()
            attempt = None
            print(
                "WARNING: Application logging unavailable for reporting; "
                f"publication remains controlled by reporting receipts: {exc}",
                file=sys.stderr,
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
        print(f"emrys: error: {exc}", file=sys.stderr)
        print(
            "Scientific Results remain complete; reporting state was preserved for inspection.",
            file=sys.stderr,
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
            print(
                "WARNING: Reporting completed, but application logging degraded.",
                file=sys.stderr,
            )
    close_log_best_effort()
    _print_reporting_outcome(completed)
    return 0


def inspect_from_args(
    arguments: argparse.Namespace,
) -> int:
    try:
        _project_path, run_root = _resolve_run_argument(arguments)
        observed = inspection.inspect_run(run_root)
        detail = getattr(arguments, "detail", "normal")
        milestones = _milestone_progress(
            observed.tasks,
            processing_source_state=(
                None
                if observed.processing_source_run_id is None
                else "reused"
                if observed.processing_source is not None
                else "blocked"
            ),
        )
        elapsed = _attempt_elapsed_line(observed)
        result_lines = _verified_report_location_lines(observed.verified_report_locations)
    except (
        OSError,
        inspection.InspectionError,
        onboarding.OnboardingError,
        ControlError,
    ) as exc:
        return _control_failure(exc)
    print(f"Run: {inspection.human_run_name(run_root.name)}")
    print(f"Run integrity: {observed.integrity}")
    print(f"Attempt outcome: {observed.attempt_outcome}")
    print(elapsed)
    if observed.processing_source_run_id is not None:
        source_state = "admitted" if observed.processing_source is not None else "blocked"
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
    print(f"Scientific Results: {observed.results_status}")
    print(f"Reporting: {observed.reporting_status}")
    latest = observed.latest_attempt
    receipt = observed.latest_receipt
    if detail != "normal":
        print(f"Run ID: {observed.run_id}")
        if observed.processing_source_run_id is not None:
            print(f"Processing source Run ID: {observed.processing_source_run_id}")
        authority = observed.authority
        if authority is None:
            print("Identity model: historical execution.v1")
        else:
            print(f"Analysis ID: {authority.analysis_revision.analysis_revision_id}")
            print(f"Execution Plan ID: {authority.execution_plan.execution_plan_id}")
        _print_safe(f"Run root: {observed.run_root}")
        attempt_id = "none" if latest is None else latest["workflow_attempt_id"]
        print(f"Attempt ID: {attempt_id}")
        if latest is not None:
            placement = latest.get("placement")
            placement_kind = "legacy/unrecorded" if placement is None else placement["kind"]
            scheduler_job_id = "none" if placement is None else placement["scheduler_job_id"] or "none"
            _print_safe(
                f"Execution: {latest['executor']}/{latest['execution_mode']} "
                f"placement={placement_kind} scheduler_job_id={scheduler_job_id}"
            )
        if observed.reporting_status != "not applicable":
            print("Reporting transactions:")
            for kind, records in observed.reporting_completion_records.items():
                state = (
                    "complete"
                    if records["verified"] is not None
                    else "incomplete"
                    if records["start"] is not None
                    else "pending"
                )
                print(f"  {kind}: {state}")
    if detail == "debug":
        authority = observed.authority
        if authority is None:
            _print_safe(f"Historical authority record: {observed.run_root / 'contract/normalized.json'}")
        else:
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
            receipt_path = "none" if receipt is None else attempt_root / "attempt-receipt.json"
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
            task_detail = f"  TASK {identity}: {task.state}"
            if task.record_reference is not None:
                task_detail += f"; verified={observed.run_root / task.record_reference['path']}"
            if task.record is not None:
                attempt_reference = task.record["task_attempt_record"]
                attempt_path = observed.run_root / attempt_reference["path"]
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
    "configure_inspect_parser",
    "configure_report_parser",
    "configure_resume_parser",
    "configure_run_parser",
    "inspect_from_args",
    "report_from_args",
    "resume_from_args",
    "run_from_args",
)
