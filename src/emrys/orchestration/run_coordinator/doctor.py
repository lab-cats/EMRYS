"""Project-aware readiness diagnosis and explicit managed-runtime repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from functools import partial
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from emrys import analyses as analysis_modules
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import AnalysisRevision
from emrys.evidence.runtime_availability.inspector import (
    PYTHON_CHECK_IDS,
    RuntimeBinding,
    RuntimeCheck,
    RuntimeInspection,
    RuntimeContentMismatchError,
    RuntimeInspectionError,
    RuntimeObservation,
    inspect_runtime_profile_bytes,
    admit_runtime_seal_bytes,
    load_runtime_profile_contract,
    runtime_root_for_seal,
    shared_runtime_profile_bytes,
    shared_runtime_selection,
    runtime_seal_bytes,
    runtime_file_bindings,
    runtime_profile_checks,
)
from emrys.evidence.storage_inventory import qualification as storage_qualification
from emrys.libraries.application_logging import (
    ApplicationLogError,
    AttemptLog,
    AttemptIdentity,
    LogControlError,
    LogControls,
    add_log_arguments,
    console_print,
    event,
    field,
    open_attempt_log,
    phase_progress,
    resolve_log_controls,
)
from emrys.libraries.exclusive_publication import (
    acquire_lock,
    publish_exclusive,
    release_lock,
)
from emrys.libraries.process_environment import (
    guarded_r_environment,
    guarded_rscript_argv,
    sanitized_subprocess_environment,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import read_bytes_with_identity
from emrys.libraries.source_authority import (
    InstalledPackage,
    InstalledPackageError,
    admit_installed_package,
)
from emrys.orchestration.run_coordinator import (
    onboarding,
    scheduler_observation,
    slurm_submission,
)
from emrys.orchestration.run_coordinator.capacity import observe_allocation
from emrys.orchestration.run_coordinator.execution_profile import (
    ExecutionProfileError,
    ExecutionProfile,
    SlurmPlacement,
    load_execution_profile,
    project_execution_profile_path,
)
from emrys.orchestration.run_coordinator.normalization import (
    AnalysisAdmission,
    ProjectAdmission,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    ResourceConfigError,
    is_canonical_slurm_job_id,
    resolve_resource_policy,
)

DESCRIPTION = (
    "Diagnose one Project across inputs, storage, runtime, and execution. "
    "Diagnosis and repair preview are read-only; an explicitly confirmed "
    "repair may qualify storage and restore only EMRYS-owned runtime "
    "native and R state through Pixi and renv."
)

StorageRequirement = Literal["direct", "slurm"]


class DoctorInputError(RuntimeError):
    """The doctor invocation contains malformed or unsafe input."""


class DoctorRepairError(RuntimeError):
    """The managed-runtime repair cannot proceed or did not complete."""


class _DoctorTiming:
    """Invocation-local observations; never an admission or execution authority."""

    def __init__(self) -> None:
        self.context = "head/local"
        self.detail = False
        self.phases: list[dict[str, object]] = []
        self.runtime_probes: list[tuple[str, dict[str, object]]] = []
        self.scheduler_timing: dict[str, object] | None = None
        self.flushed = False

    def observe(self, name: str, elapsed: float | None, outcome: str) -> None:
        values = {"phase_name": name, "elapsed_seconds": elapsed, "outcome": outcome}
        self.phases.append(values)

    def observe_runtime(
        self, inspection: RuntimeInspection | None, *, phase: str
    ) -> None:
        with suppress(Exception):
            if inspection is not None:
                self.runtime_probes.extend(
                    (phase, _runtime_observation_fields(inspection, item))
                    for item in inspection.observations
                    if item.status == "pass"
                )

    def flush(self, record: Callable[..., bool]) -> None:
        if self.flushed:
            return
        self.flushed = True
        with suppress(Exception):
            for values in self.phases:
                if not record(
                    "doctor_phase_timing",
                    "Doctor phase timing observed.",
                    execution_context=self.context,
                    **values,
                ):
                    return
            for phase, values in self.runtime_probes:
                if not record(
                    "runtime_check_passed",
                    "Runtime check passed at the recorded Doctor phase.",
                    phase=phase,
                    execution_context=self.context,
                    **values,
                ):
                    return
            if self.scheduler_timing is not None:
                record(
                    "doctor_scheduler_timing",
                    "Recorded Slurm accounting intervals observed.",
                    **self.scheduler_timing,
                )

    def observe_scheduler(
        self,
        submission: slurm_submission.SlurmSubmission,
        identity: tuple[str, str | None] | None,
    ) -> None:
        observed = scheduler_observation.unknown_observation(
            "No response-recorded job identity; accounting was not queried"
        )
        if identity is not None:
            try:
                with phase_progress(
                    "Reading recorded Slurm timing", on_complete=self.observe
                ):
                    observed = scheduler_observation.observe_job(
                        identity[0],
                        str(submission.stdout_pattern),
                        str(submission.stderr_pattern),
                        identity[1],
                        job_name=submission.job_name,
                        include_timing=True,
                    )
                    if not isinstance(observed, dict):
                        raise TypeError("Accounting observation was not a record")
            except Exception as exc:
                observed = scheduler_observation.unknown_observation(str(exc)[:4096])
        self.scheduler_timing = {
            "scheduler_job_id": identity[0] if identity is not None else None,
            **observed,
        }

    def finish(self, elapsed: float | None, status: int | None) -> None:
        if self.detail and self.scheduler_timing is not None:
            observed = self.scheduler_timing
            _stderr(
                f"Slurm accounting observation: {observed['state']}; "
                f"source: {observed.get('source') or 'unavailable'}; "
                f"scheduler exit status: {observed.get('exit_code') or 'unavailable'}"
            )
            timing = observed.get("timing", {})
            intervals = "; ".join(
                f"{label}: {timing[key]}s" if key in timing else f"{label}: unavailable"
                for key, label in (
                    ("submission_to_start_seconds", "submitted-to-start wait"),
                    ("eligible_to_start_seconds", "eligible queue wait"),
                    ("allocation_wall_seconds", "allocation wall time"),
                )
            )
            _stderr(
                f"Slurm accounting timing (job {observed['scheduler_job_id'] or 'unconfirmed'}; "
                f"cluster {observed.get('cluster') or 'unconfirmed'}; "
                f"observed {observed.get('timing_observed_at', 'unavailable')}): {intervals}"
            )
            diagnostic = timing.get("diagnostic") or observed.get("diagnostic")
            if diagnostic:
                _stderr(f"Slurm timing limitation: {str(diagnostic)!a}")
        if self.detail:
            for values in self.phases:
                seconds = values["elapsed_seconds"]
                duration = "unavailable" if seconds is None else f"{seconds:.6f}s"
                _stderr(
                    f"Doctor phase timing ({self.context}): {values['phase_name']}; "
                    f"{values['outcome']}; elapsed {duration}"
                )
            duration = "unavailable" if elapsed is None else f"{elapsed:.6f}s"
            outcome = (
                "interrupted or failed" if status is None else f"exit status {status}"
            )
            _stderr(
                f"Doctor invocation timing ({self.context}, including operator confirmation time): "
                f"elapsed {duration}; {outcome}"
            )


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Immutable readiness result consumed by Run planning."""

    project: ProjectAdmission
    analysis: AnalysisAdmission
    installed_package: InstalledPackage | None
    inspection: RuntimeInspection | None
    bindings: tuple[RuntimeBinding, ...]
    blockers: tuple[str, ...]
    remediations: tuple[str, ...]
    storage_ready: bool = True
    runtime_ready: bool = True
    execution_ready: bool = True
    execution_profile: ExecutionProfile | None = None

    @property
    def ready(self) -> bool:
        return not self.blockers


def storage_runtime_binding(
    qualified: storage_qualification.QualifiedStorage,
) -> RuntimeBinding:
    """Project one semantically admitted storage receipt into runtime identity."""

    return RuntimeBinding(
        "storage_qualification",
        qualified.receipt_path,
        qualified.receipt_path.resolve(strict=True),
        qualified.receipt_sha256,
        qualified.qualification_id,
    )


def required_tool_identities(
    inspection: RuntimeInspection,
    *,
    bindings: tuple[RuntimeBinding, ...],
    python_executable: Path,
    runtime_profile_path: Path | None = None,
) -> tuple[dict[str, str | None], ...]:
    """Project exact attempt tool identities from one admitted runtime probe."""

    bound = {item.check_id: item for item in bindings}

    def identity(name: str, version: str) -> dict[str, str | None]:
        try:
            binding = bound[name]
        except KeyError as exc:
            raise DoctorInputError(f"Runtime file binding is absent: {name}") from exc
        value = {
            "name": name,
            "version": version,
            "path": str(binding.path),
            "resolved_path": str(binding.resolved_path),
            "sha256": binding.sha256,
        }
        if binding.identity_kind is not None:
            value["identity_kind"] = binding.identity_kind
        return value

    python_binding = identity("python", platform.python_version())
    if Path(str(python_binding["path"])) != python_executable:
        raise DoctorInputError("Runtime Python binding differs from this interpreter")
    profile = (
        inspection.profile_path
        if runtime_profile_path is None
        else runtime_profile_path
    )
    identities: list[dict[str, str | None]] = [
        {
            "name": "runtime_profile",
            "version": f"sha256:{inspection.profile_sha256}",
            "path": str(profile),
            "resolved_path": str(profile),
            "sha256": inspection.profile_sha256,
        },
        python_binding,
    ]
    for observation in inspection.observations:
        check = observation.check
        if observation.status != "pass" or check.check_id == "python":
            continue
        if check.check_id in {"renv_project", "renv_library"}:
            path = Path(check.target)
            identities.append(
                {
                    "name": check.check_id,
                    "version": observation.observed,
                    "path": str(path),
                    "resolved_path": str(path.resolve(strict=True)),
                    "sha256": None,
                }
            )
            continue
        identities.append(identity(check.check_id, observation.observed))
    identities.append(
        identity("storage_qualification", bound["storage_qualification"].observed)
    )
    return tuple(sorted(identities, key=lambda item: item["name"]))


_PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _absolute_path(value: str | Path) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else Path.cwd() / path
    return Path(os.path.abspath(path))


def workspace_location_blockers(
    workspace: Path, source_root: Path
) -> tuple[list[str], list[str]]:
    """Admit the already-created Project root."""

    if (
        workspace == source_root
        or workspace in source_root.parents
        or source_root in workspace.parents
    ):
        return [f"workspace overlaps the installed EMRYS package: {workspace}"], [
            "Choose a Project outside and not containing the installed EMRYS package."
        ]
    try:
        state = workspace.lstat()
        resolved = workspace.resolve(strict=True)
    except OSError as exc:
        raise DoctorInputError(
            f"Project root is unavailable: {workspace}: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != workspace
    ):
        raise DoctorInputError(
            f"Project root must be a canonical real directory: {workspace}"
        )
    if not os.access(workspace, os.R_OK | os.W_OK | os.X_OK):
        return [
            f"Project root is not readable, writable, and searchable: {workspace}"
        ], [f"Grant user access to the Project root: {workspace}"]
    return [], []


def _module_dependency_checks(
    descriptor: analysis_modules.AnalysisModuleDescriptorV1,
    fixed_checks: tuple[RuntimeCheck, ...],
) -> tuple[
    tuple[RuntimeCheck, ...],
    frozenset[str],
    frozenset[str],
]:
    """Resolve one selected module onto the fixed runtime-check vocabulary."""

    fixed = {item.check_id: item for item in fixed_checks}
    additions: list[RuntimeCheck] = []
    package_trees: set[str] = set()
    files: set[str] = set()
    for declaration in sorted(
        descriptor.dependencies,
        key=lambda item: item if isinstance(item, str) else item.dependency_id,
    ):
        if isinstance(declaration, str):
            if declaration not in fixed:
                raise DoctorInputError(
                    f"Analysis module references an unknown runtime check: {declaration}"
                )
            continue
        check_id = declaration.dependency_id
        if check_id in fixed:
            raise DoctorInputError(
                f"Analysis module dependency collides with fixed runtime check: {check_id}"
            )
        if declaration.kind == "executable":
            check_type, target = "tool_version", declaration.target
            probe_args, expected = declaration.probe_args, declaration.expected
            files.add(check_id)
        elif declaration.kind == "r_namespace":
            check_type, target = "r_namespace", declaration.target
            probe_args, expected = (fixed["rscript"].target,), declaration.expected
            package_trees.add(check_id)
        else:
            check_type, target, expected = (
                "path_visibility",
                declaration.target,
                "readable",
            )
            probe_args = (
                ("directory_readable",)
                if declaration.kind == "package_tree"
                else ("file_readable",)
            )
            if declaration.kind == "package_tree":
                package_trees.add(check_id)
            else:
                files.add(check_id)
        additions.append(
            RuntimeCheck(
                check_id,
                check_type,
                target,
                probe_args,
                expected,
            )
        )
    return (
        tuple(additions),
        frozenset(package_trees),
        frozenset(files),
    )


def diagnose_project(
    project_path: str | Path,
    workspace: str | Path | None = None,
    runtime_inventory: str | Path | None = None,
    *,
    execution_profile: str | Path | None = None,
    storage_requirement: StorageRequirement | None = None,
    analysis_name: str | None = None,
    expected_analysis_revision: AnalysisRevision | None = None,
    require_reporter: bool = True,
) -> DoctorResult:
    """Diagnose Project execution, storage, and runtime readiness without writes."""

    project = _absolute_path(project_path)
    execution = None
    execution_error: str | None = None
    if storage_requirement is None:
        try:
            execution_path = project_execution_profile_path(project, execution_profile)
            execution = load_execution_profile(config_path=execution_path)
            storage_requirement = execution.placement.kind
        except ExecutionProfileError as exc:
            execution_error = str(exc)
            storage_requirement = "direct"
    root = _absolute_path(onboarding.source_root())
    workspace_path = _absolute_path(project.parent if workspace is None else workspace)
    blockers, remediations = workspace_location_blockers(workspace_path, root)
    try:
        installed_package = admit_installed_package(root=root)
    except InstalledPackageError as exc:
        installed_package = None
        blockers.append(f"installed EMRYS is not ready: {exc}")
        remediations.append(
            "Reinstall EMRYS with its package manager, then rerun Doctor."
        )
    try:
        admitted_project = onboarding.validate_project(
            project,
            root=root,
        ).project
        analysis = admitted_project.select_analysis(
            analysis_name,
            expected_revision=expected_analysis_revision,
        )
    except (
        onboarding.OnboardingError,
        orchestration_contracts.ContractValidationError,
        OSError,
    ) as exc:
        raise DoctorInputError(str(exc)) from exc
    if require_reporter:
        from emrys import reporting  # noqa: PLC0415

        try:
            reporting.admit_analysis_reporter(analysis.module.descriptor.module_id)
        except reporting.ReportProviderError as exc:
            blockers.append(f"analysis reporter is not ready: {exc}")
            remediations.append(
                "Install exactly one matching analysis reporter, or run with "
                "--no-report and generate reporting after it is installed."
            )
    fasta = Path(str(analysis.workflow_inputs["reference"]["fasta"]["path"]))
    if storage_requirement == "direct":
        admit_storage = storage_qualification.admit_direct_requirement
        storage_label = "single-host storage is not qualified"
        storage_remediation = (
            "Run `emrys doctor --repair` in the intended direct execution context."
        )
    elif storage_requirement == "slurm":
        admit_storage = storage_qualification.admit_final_qualification
        storage_label = "storage is not site-qualified"
        storage_remediation = "Run `emrys doctor --repair` on the head node."
    else:
        raise DoctorInputError(
            f"unsupported storage requirement: {storage_requirement}"
        )
    try:
        bindings = (storage_runtime_binding(admit_storage(workspace_path, fasta)),)
    except storage_qualification.StorageQualificationError as exc:
        bindings = ()
        blockers.append(f"{storage_label}: {exc}")
        remediations.append(storage_remediation)
    storage_ready = bool(bindings)
    inspection: RuntimeInspection | None = None
    runtime_ready = False
    profile_path = (
        onboarding.runtime_profile_path(project)
        if runtime_inventory is None
        else _absolute_path(runtime_inventory)
    )
    if runtime_inventory is None and not os.path.lexists(profile_path):
        blockers.append(f"runtime inventory is not admitted: {profile_path}")
        remediations.append(
            "Run `emrys doctor --repair`, or admit a complete site runtime "
            "with `emrys runtime discover --execute`."
        )
    else:
        try:
            profile_bytes, fixed_checks = load_runtime_profile_contract(
                profile_path, root
            )
            selected_shared = shared_runtime_selection(profile_bytes)
        except RuntimeInspectionError as exc:
            raise DoctorInputError(str(exc)) from exc
        additions, package_tree_ids, explicit_file_ids = _module_dependency_checks(
            analysis.module.descriptor,
            fixed_checks,
        )
        renv_library = next(
            Path(check.target)
            for check in fixed_checks
            if check.check_id == "renv_library"
        )
        try:
            with tempfile.TemporaryDirectory(prefix="emrys-doctor-") as temporary:
                inspection = inspect_runtime_profile_bytes(
                    profile_bytes,
                    profile_path,
                    checks=(*fixed_checks, *additions),
                    environment={
                        **guarded_r_environment(root, renv_library),
                        "TMPDIR": temporary,
                    },
                )
        except RuntimeInspectionError as exc:
            raise DoctorInputError(str(exc)) from exc
        python = next(
            item for item in inspection.observations if item.check.check_id == "python"
        )
        python_ready = Path(python.check.target) == Path(sys.executable)
        if not python_ready:
            blockers.append(
                f"runtime Python differs from this interpreter: {python.check.target}"
            )
            remediations.append(
                "Activate the Python environment admitted by the Project runtime, "
                "then rerun Doctor."
            )
        failed = tuple(
            item for item in inspection.observations if item.status != "pass"
        )
        blockers.extend(
            f"{item.check.check_id}: {item.status} ({item.observed})" for item in failed
        )
        fixed_ids = {check.check_id for check in fixed_checks}
        custom_ids = {
            dependency.dependency_id
            for dependency in analysis.module.descriptor.dependencies
            if isinstance(dependency, analysis_modules.AnalysisDependencyV1)
        }
        if any(item.check.check_id in PYTHON_CHECK_IDS for item in failed):
            remediations.append(
                "Reinstall EMRYS and its Python dependencies with the environment's "
                "package manager; Doctor repairs only native tools and R."
            )
        if any(item.check.check_id in fixed_ids - PYTHON_CHECK_IDS for item in failed):
            if (
                selected_shared is not None
                and runtime_root_for_seal(selected_shared.seal_path)
                != onboarding.runtime_profile_path(project).parent
            ):
                donor = (
                    runtime_root_for_seal(selected_shared.seal_path).parent
                    / "project.yaml"
                )
                remediations.append(
                    "The Project that owns these shared tools must prepare their "
                    "replacement. Then run `emrys runtime discover --from-project "
                    f"{donor} --replace --execute`."
                )
            else:
                remediations.append(
                    "Run `emrys doctor --repair` for an EMRYS-managed runtime, or "
                    "repair and re-admit the selected site environment without "
                    "editing runtime.tsv."
                )
        if any(item.check.check_id in custom_ids for item in failed):
            remediations.append(
                "Install the selected analysis module and its declared dependencies "
                "with their package manager, then rerun Doctor; managed repair "
                "restores only the fixed EMRYS runtime."
            )
        donor_seal = onboarding.runtime_profile_path(project).parent / "shared.json"
        content_matches = True
        try:
            runtime_bindings = runtime_file_bindings(
                inspection,
                package_tree_ids=package_tree_ids,
                explicit_file_ids=explicit_file_ids,
                donor_seal=donor_seal
                if profile_path == onboarding.runtime_profile_path(project)
                and os.path.lexists(donor_seal)
                and shared_runtime_selection(profile_bytes) is None
                else None,
            )
        except RuntimeContentMismatchError as exc:
            runtime_bindings = ()
            content_matches = False
            blockers.append(str(exc))
            owner = (
                None
                if selected_shared is None
                else runtime_root_for_seal(selected_shared.seal_path)
            )
            if (
                owner is None
                or owner == onboarding.runtime_profile_path(project).parent
            ):
                remediations.append(
                    "Run `emrys doctor --repair`; it will prepare a replacement "
                    "generation without changing the shared tools in place."
                )
            else:
                remediations.append(
                    "The Project that owns these shared tools must prepare their "
                    "replacement. Then run `emrys runtime discover --from-project "
                    f"{owner.parent / 'project.yaml'} --replace --execute`."
                )
        except RuntimeInspectionError as exc:
            raise DoctorInputError(str(exc)) from exc
        bindings = (*runtime_bindings, *bindings)
        runtime_ready = python_ready and not failed and content_matches
    if execution_error is not None:
        selection = "default" if execution_profile is None else "selected"
        blockers.append(
            f"{selection} execution profile is not admitted: {execution_error}"
        )
        remediations.append(
            "Restore a valid Project-owned runtime/profiles/default.yaml; "
            "Doctor preserves operator execution policy."
            if execution_profile is None
            else "Select a valid execution profile with --profile; Doctor preserves operator execution policy."
        )
    return DoctorResult(
        project=admitted_project,
        analysis=analysis,
        installed_package=installed_package,
        inspection=inspection,
        bindings=bindings,
        blockers=tuple(blockers),
        remediations=tuple(dict.fromkeys(remediations)),
        storage_ready=storage_ready,
        runtime_ready=runtime_ready,
        execution_ready=execution_error is None,
        execution_profile=execution,
    )


@dataclass(frozen=True, slots=True)
class _ManagedRuntimePlan:
    managed_root: Path
    profile: Path
    pixi: Path
    pixi_sha256: str
    profile_bytes: bytes | None
    manifest_bytes: bytes
    lock_bytes: bytes
    r_settings_bytes: bytes
    source_seal: Path | None = None
    source_seal_bytes: bytes | None = None
    replacement_seal: Path | None = None


@dataclass(frozen=True, slots=True)
class _RepairPlan:
    project: ProjectAdmission
    analysis_name: str
    installed_package: InstalledPackage
    storage: storage_qualification.DirectQualificationPlan | None
    runtime: _ManagedRuntimePlan | None
    execution: ExecutionProfile | None = None
    compute: bool = False
    qualification_binding: str | None = None

    @property
    def operation(self) -> str:
        return "repair and verification" if self.runtime else "verification"

    @property
    def runtime_work(self) -> str:
        if self.runtime is None:
            return "Selected runtime passed current checks; no package-manager work is needed."
        action = (
            "Prepare a managed runtime inventory; package managers check any retained tools and caches."
            if self.runtime.profile_bytes is None and self.runtime.source_seal is None
            else "Create and verify a replacement generation; other Projects keep their existing selection until explicitly replaced."
            if self.runtime.replacement_seal is not None
            else "Check/update tools selected by the retained managed runtime inventory."
        )
        return f"{action} Package-manager output records which packages are reused, installed, or changed."


def _profile_is_managed(
    checks: tuple[RuntimeCheck, ...],
    plan: _ManagedRuntimePlan,
) -> bool:
    def owned(target: Path) -> bool:
        try:
            return target.is_relative_to(plan.managed_root) and (
                not os.path.lexists(plan.managed_root)
                or target.resolve(strict=False).is_relative_to(plan.managed_root)
            )
        except (OSError, RuntimeError):
            return False

    for check in checks:
        if check.check_type == "r_namespace":
            continue
        target = _absolute_path(check.target)
        if check.check_id in PYTHON_CHECK_IDS:
            allowed = target == Path(sys.executable)
        elif check.check_id == "renv_project":
            allowed = target == _PACKAGE_ROOT
        else:
            allowed = owned(target)
        if not allowed:
            return False
    return True


def _manager(name: str) -> Path:
    selected = shutil.which(name)
    if selected:
        try:
            path = _absolute_path(selected).resolve(strict=True)
        except OSError as exc:
            raise DoctorRepairError(f"could not admit {name}: {exc}") from exc
        if path.is_file() and os.access(path, os.R_OK | os.X_OK):
            return path
    raise DoctorRepairError(f"{name} is required; install it through site policy")


def _file_sha256(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()
    except OSError as exc:
        raise DoctorRepairError(
            f"could not bind package manager {path}: {exc}"
        ) from exc


def _build_repair_plan(result: DoctorResult) -> _RepairPlan:
    if result.installed_package is None:
        raise DoctorRepairError("Doctor requires an admitted installed EMRYS package")
    if not result.execution_ready:
        raise DoctorRepairError(
            "Doctor preserves execution profiles; restore or select a valid profile with --profile"
        )
    if result.execution_profile is not None:
        result.execution_profile.validate_reservation()
    project = result.project
    fasta = Path(str(result.analysis.workflow_inputs["reference"]["fasta"]["path"]))
    try:
        storage = (
            None
            if result.storage_ready
            or (
                result.execution_profile is not None
                and result.execution_profile.placement.kind == "slurm"
            )
            else storage_qualification.plan_direct_qualification(
                project.source_path.parent,
                fasta,
            )
        )
    except storage_qualification.StorageQualificationError as exc:
        raise DoctorRepairError(str(exc)) from exc
    plan = _RepairPlan(
        project=project,
        analysis_name=result.analysis.name,
        installed_package=result.installed_package,
        storage=storage,
        runtime=None,
        execution=result.execution_profile,
    )
    if result.runtime_ready:
        return plan
    if result.inspection is not None and any(
        item.check.check_id in PYTHON_CHECK_IDS and item.status != "pass"
        for item in result.inspection.observations
    ):
        raise DoctorRepairError(
            "repair does not modify the Python environment; reinstall EMRYS and "
            "its Python dependencies with their package manager, then rerun Doctor"
        )
    custom_dependencies = {
        dependency.dependency_id
        for dependency in result.analysis.module.descriptor.dependencies
        if isinstance(dependency, analysis_modules.AnalysisDependencyV1)
    }
    unavailable_dependencies = (
        []
        if result.inspection is None
        else sorted(
            item.check.check_id
            for item in result.inspection.observations
            if item.check.check_id in custom_dependencies and item.status != "pass"
        )
    )
    if unavailable_dependencies:
        raise DoctorRepairError(
            "managed repair does not install selected analysis-module dependencies: "
            + ", ".join(unavailable_dependencies)
            + "; install them with their package manager and rerun Doctor"
        )
    machine = platform.machine().casefold()
    if platform.system() != "Linux" or machine not in {"amd64", "x86_64"}:
        raise DoctorRepairError(
            "managed repair currently supports x86-64 Linux; use site runtime discovery on this platform"
        )
    try:
        runtime = onboarding.project_runtime_directory(project)
        resources = _PACKAGE_ROOT / "resources/runtime"
        manifest_bytes = (resources / "pixi.toml").read_bytes()
        lock_bytes = (resources / "pixi.lock").read_bytes()
        r_settings_bytes = (_PACKAGE_ROOT / "renv/settings.json").read_bytes()
    except (OSError, onboarding.OnboardingError) as exc:
        raise DoctorRepairError(str(exc)) from exc
    managed = runtime / "managed"
    if os.path.lexists(runtime / "maintenance.lock"):
        raise DoctorRepairError(
            f"Runtime maintenance claim already exists: {runtime / 'maintenance.lock'}; "
            "preserved for explicit reconciliation"
        )
    profile = runtime / "runtime.tsv"
    profile_bytes: bytes | None = None
    profile_checks: tuple[RuntimeCheck, ...] = ()
    if result.inspection is not None:
        if _absolute_path(result.inspection.profile_path) != profile:
            raise DoctorRepairError(
                "the admitted runtime inventory is site- or user-owned and was preserved"
            )
        try:
            profile_bytes, profile_checks = load_runtime_profile_contract(
                profile, _PACKAGE_ROOT
            )
        except RuntimeInspectionError as exc:
            raise DoctorRepairError(
                f"could not re-admit the managed runtime inventory: {exc}"
            ) from exc
    source_seal: Path | None = None
    source_seal_bytes: bytes | None = None
    replacement_seal: Path | None = None
    try:
        selection = (
            None if profile_bytes is None else shared_runtime_selection(profile_bytes)
        )
        if selection is not None:
            source_seal = selection.seal_path
        elif os.path.lexists(runtime / "shared.json"):
            source_seal = runtime / "shared.json"
        if source_seal is not None:
            owner = runtime_root_for_seal(source_seal)
            if owner != runtime:
                donor = owner.parent / "project.yaml"
                raise DoctorRepairError(
                    "This Project uses tools shared by another Project. Doctor will "
                    "not change that installation. After its owner prepares a replacement, "
                    "run `emrys runtime discover --from-project "
                    f"{donor} --replace --execute`."
                )
            source_seal_bytes, _seal_state = read_bytes_with_identity(
                source_seal, "Shared runtime seal"
            )
            if (
                selection is not None
                and hashlib.sha256(source_seal_bytes).hexdigest()
                != selection.seal_sha256
            ):
                raise DoctorRepairError(
                    "shared runtime seal differs from the selected SHA-256"
                )
            admitted_seal = admit_runtime_seal_bytes(source_seal, source_seal_bytes)
            replacement_seal = (
                runtime / "generations" / uuid.uuid4().hex / "shared.json"
            )
            managed = replacement_seal.parent / "managed"
    except (RuntimeInspectionError, ValidationError) as exc:
        raise DoctorRepairError(
            f"could not re-admit the shared runtime seal: {exc}"
        ) from exc
    pixi = _manager("pixi")
    managed_plan = _ManagedRuntimePlan(
        managed_root=managed,
        profile=profile,
        pixi=pixi,
        pixi_sha256=_file_sha256(pixi),
        profile_bytes=profile_bytes,
        manifest_bytes=manifest_bytes,
        lock_bytes=lock_bytes,
        r_settings_bytes=r_settings_bytes,
        source_seal=source_seal,
        source_seal_bytes=source_seal_bytes,
        replacement_seal=replacement_seal,
    )
    if result.inspection is not None:
        admitted_plan = (
            replace(managed_plan, managed_root=admitted_seal.managed_root)
            if source_seal is not None
            else managed_plan
        )
        if not _profile_is_managed(profile_checks, admitted_plan):
            raise DoctorRepairError(
                "the admitted runtime inventory is site- or user-owned and was "
                "preserved; repair that environment or explicitly admit a replacement"
            )
    return replace(plan, runtime=managed_plan)


def _readmit_repair_plan(
    plan: _RepairPlan,
    *,
    before_storage: bool,
) -> None:
    runtime = plan.runtime
    if runtime is not None:
        _readmit_runtime_seal_plan(runtime)
    try:
        installed_package = admit_installed_package(root=plan.installed_package.root)
        project = onboarding.validate_project(
            plan.project.source_path, root=plan.installed_package.root
        ).project
        runtime_root = onboarding.project_runtime_directory(project)
        if plan.execution is not None:
            load_execution_profile(
                config_path=plan.execution.source_path,
                expected_binding_sha256=plan.execution.binding_sha256,
            )
        if before_storage and plan.storage is not None:
            observed_storage = storage_qualification.plan_direct_qualification(
                plan.storage.workspace,
                plan.storage.reference_fasta,
            )
        else:
            observed_storage = plan.storage
    except (
        OSError,
        RuntimeError,
        storage_qualification.StorageQualificationError,
        ExecutionProfileError,
    ) as exc:
        raise DoctorRepairError(f"Doctor plan changed before execution: {exc}") from exc
    if (
        installed_package != plan.installed_package
        or project != plan.project
        or (plan.storage is not None and observed_storage != plan.storage)
        or (plan.runtime is not None and runtime_root != plan.runtime.profile.parent)
    ):
        raise DoctorRepairError("Doctor plan changed before execution")
    if runtime is None:
        return
    if (
        before_storage
        and runtime.replacement_seal is not None
        and os.path.lexists(runtime.replacement_seal.parent)
    ):
        raise DoctorRepairError(
            "replacement runtime generation appeared before execution"
        )
    if _file_sha256(runtime.pixi) != runtime.pixi_sha256:
        raise DoctorRepairError("admitted package manager changed before execution")
    if not before_storage:
        settings = runtime.managed_root / "renv/settings.json"
        try:
            if (
                settings.is_symlink()
                or settings.read_bytes() != runtime.r_settings_bytes
            ):
                raise DoctorRepairError("managed R settings changed during repair")
        except OSError as exc:
            raise DoctorRepairError("managed R settings changed during repair") from exc
    if runtime.profile_bytes is None:
        if os.path.lexists(runtime.profile):
            raise DoctorRepairError(
                "runtime inventory appeared after repair confirmation"
            )
        return
    try:
        state = runtime.profile.lstat()
        data = runtime.profile.read_bytes()
    except OSError as exc:
        raise DoctorRepairError(
            f"runtime inventory changed before execution: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISREG(state.st_mode)
        or data != runtime.profile_bytes
    ):
        raise DoctorRepairError("runtime inventory changed before execution")


def _readmit_runtime_seal_plan(runtime: _ManagedRuntimePlan) -> None:
    """Require the exact shared-generation state admitted by the repair plan."""

    if runtime.source_seal is None:
        if os.path.lexists(runtime.profile.parent / "shared.json"):
            raise DoctorRepairError("shared runtime seal appeared before execution")
        return
    assert runtime.source_seal_bytes is not None
    try:
        source_data, _source_state = read_bytes_with_identity(
            runtime.source_seal, "Shared runtime seal"
        )
        if source_data != runtime.source_seal_bytes:
            raise DoctorRepairError("shared runtime seal changed before replacement")
        admitted = admit_runtime_seal_bytes(runtime.source_seal, source_data)
        if runtime_root_for_seal(admitted.path) != runtime.profile.parent:
            raise DoctorRepairError("shared runtime owner changed before replacement")
    except (RuntimeInspectionError, ValidationError) as exc:
        raise DoctorRepairError(
            f"shared runtime seal changed before replacement: {exc}"
        ) from exc


def _admit_managed_root(plan: _ManagedRuntimePlan) -> None:
    root = plan.managed_root
    try:
        if plan.replacement_seal is not None:
            generation = plan.replacement_seal.parent
            generations = generation.parent
            runtime = plan.profile.parent
            if (
                root != generation / "managed"
                or generations != runtime / "generations"
                or os.path.lexists(generation)
            ):
                raise DoctorRepairError(
                    "replacement runtime generation changed before creation"
                )
            if not os.path.lexists(generations):
                generations.mkdir(mode=0o700)
            state = generations.lstat()
            if (
                not stat.S_ISDIR(state.st_mode)
                or stat.S_ISLNK(state.st_mode)
                or generations.resolve(strict=True) != generations
                or state.st_uid != os.getuid()
            ):
                raise DoctorRepairError(
                    f"runtime generations directory is not owned: {generations}"
                )
            generation.mkdir(mode=0o700)
        if not os.path.lexists(root):
            root.mkdir(mode=0o700)
        state = root.lstat()
        safe = stat.S_ISDIR(state.st_mode) and not stat.S_ISLNK(state.st_mode)
        safe = safe and root.resolve(strict=True) == root
        if not safe or not os.access(root, os.R_OK | os.W_OK | os.X_OK):
            raise DoctorRepairError(
                f"managed runtime must be canonical and writable: {root}"
            )
        allowed = {".pixi", "cache", "pixi.lock", "pixi.toml", "renv"}
        unexpected = {path.name for path in root.iterdir()} - allowed
        if unexpected:
            raise DoctorRepairError(
                "foreign managed-runtime entries: " + ", ".join(sorted(unexpected))
            )
        if os.path.lexists(root / ".pixi/config.toml"):
            raise DoctorRepairError(
                "Project-local Pixi configuration is not permitted during repair"
            )
        for relative in (".pixi", ".pixi/envs", ".pixi/envs/native", ".pixi/envs/r"):
            directory = root / relative
            if os.path.lexists(directory) and (
                directory.is_symlink()
                or not directory.is_dir()
                or root not in directory.resolve(strict=True).parents
            ):
                raise DoctorRepairError(f"managed Pixi state is not owned: {directory}")
        for relative in (
            "cache",
            "cache/pixi",
            "renv",
            "renv/cache",
            "renv/library",
        ):
            directory = root / relative
            directory.mkdir(mode=0o700, exist_ok=True)
            if directory.is_symlink() or not directory.is_dir():
                raise DoctorRepairError(
                    f"managed directory is not owned state: {directory}"
                )
        for name, data in (
            ("pixi.toml", plan.manifest_bytes),
            ("pixi.lock", plan.lock_bytes),
            ("renv/settings.json", plan.r_settings_bytes),
        ):
            destination = root / name
            if os.path.lexists(destination):
                state = destination.lstat()
                observed = destination.read_bytes()
                if not stat.S_ISREG(state.st_mode) or observed != data:
                    raise DoctorRepairError(
                        f"managed {name} differs from packaged bytes"
                    )
            else:
                publish_exclusive(destination, data, DoctorRepairError)
    except OSError as exc:
        raise DoctorRepairError(
            f"managed runtime is unavailable: {root}: {exc}"
        ) from exc


def _repair_actions(
    plan: _RepairPlan,
) -> tuple[tuple[str, tuple[str, ...], dict[str, str]], ...]:
    runtime = plan.runtime
    if runtime is None:
        return ()
    base = sanitized_subprocess_environment()
    pixi = dict(base)
    for name in tuple(pixi):
        if name.startswith("PIXI_"):
            del pixi[name]
    pixi.update(
        {
            "PIXI_CACHE_DIR": str(runtime.managed_root / "cache/pixi"),
            "PIXI_DISABLE_NETFS_REDIRECT": "1",
            "PIXI_NO_CONFIG": "1",
        }
    )
    restore = dict(pixi)
    for name in tuple(restore):
        if (
            name.startswith(("R_LIBS", "R_PROFILE", "R_ENVIRON", "RENV_"))
            or name == "R_DEFAULT_PACKAGES"
        ):
            del restore[name]
    restore.update(
        {
            "EMRYS_USE_RENV": "1",
            "EMRYS_LOCAL_PILOT_R": "0",
            "RENV_PROJECT": str(runtime.managed_root),
            "RENV_PATHS_LIBRARY": str(runtime.managed_root / "renv/library"),
            "RENV_PATHS_CACHE": str(runtime.managed_root / "renv/cache"),
            "RENV_CONFIG_SANDBOX_ENABLED": "FALSE",
            "RENV_CONFIG_AUTO_SNAPSHOT": "FALSE",
            "R_PROFILE_USER": str(plan.installed_package.root / ".Rprofile"),
        }
    )
    manifest = str(runtime.managed_root / "pixi.toml")
    restore_argv = guarded_rscript_argv(
        str(runtime.managed_root / ".pixi/envs/r/bin/Rscript"),
        (
            str(
                plan.installed_package.root
                / "resources/runtime/restore_r_environment.R"
            ),
        ),
    )
    return (
        (
            "Checking/updating native tools and R",
            (
                str(runtime.pixi),
                "install",
                "--manifest-path",
                manifest,
                "--locked",
                "--all",
            ),
            pixi,
        ),
        (
            "Checking/restoring R packages",
            (
                str(runtime.pixi),
                "run",
                "--manifest-path",
                manifest,
                "--environment",
                "r",
                "--locked",
                "--executable",
                *restore_argv,
            ),
            restore,
        ),
    )


def _managed_discovery_environment(plan: _RepairPlan) -> dict[str, str]:
    runtime = plan.runtime
    if runtime is None:
        raise DoctorRepairError("managed runtime repair was not planned")
    jars = tuple(
        path
        for path in (runtime.managed_root / ".pixi/envs/native/share").glob(
            "picard-slim-3.1.1-*/picard.jar"
        )
        if path.is_file() and not path.is_symlink()
    )
    if len(jars) != 1:
        raise DoctorRepairError("locked runtime must contain one Picard 3.1.1 jar")
    libraries = tuple(
        description.parents[1]
        for description in (runtime.managed_root / "renv/library").rglob(
            "renv/DESCRIPTION"
        )
        if description.is_file()
    )
    if len(libraries) != 1:
        raise DoctorRepairError(
            "managed renv restore must produce one qualified library"
        )
    library = libraries[0]
    try:
        if (
            library.is_symlink()
            or not library.is_dir()
            or library.resolve(strict=True) != library
        ):
            raise DoctorRepairError(f"managed renv library is not owned: {library}")
    except OSError as exc:
        raise DoctorRepairError(f"managed renv library is unavailable: {exc}") from exc
    environment = sanitized_subprocess_environment()
    environment.pop("JAVA_HOME", None)
    environment.update(
        {
            "PATH": str(runtime.managed_root / ".pixi/envs/native/bin"),
            "EMRYS_RSCRIPT": str(runtime.managed_root / ".pixi/envs/r/bin/Rscript"),
            "EMRYS_PICARD_JAR": str(jars[0]),
            "EMRYS_RENV_LIBRARY": str(library),
        }
    )
    return environment


def _stderr(message: str, *, style: str | None = None) -> None:
    console_print(message, style=style)


def _runtime_observation_fields(
    inspection: RuntimeInspection, item: RuntimeObservation
) -> dict[str, object]:
    return {
        "check_id": item.check.check_id,
        "target": item.check.target,
        "status": item.status,
        "expected": item.check.expected,
        "observed": item.observed,
        "detail": item.detail,
        "host": platform.node(),
        "inventory": str(inspection.profile_path),
        "inventory_sha256": inspection.profile_sha256,
    }


def _record_runtime_failures(
    inspection: RuntimeInspection | None,
    *,
    phase: str,
    attempt: AttemptLog | None = None,
) -> None:
    """Retain failed observations in the existing maintenance or scheduler stream."""
    if inspection is None:
        return
    for item in inspection.observations:
        if item.status == "pass":
            continue
        values = _runtime_observation_fields(inspection, item)
        if attempt is None:
            _stderr(
                f"Runtime check failed ({phase}): {json.dumps(values, ensure_ascii=True)}"
            )
        else:
            attempt.best_effort(
                lambda: attempt.logger(component="maintenance", phase=phase).warning(
                    "Runtime check failed.",
                    extra=event(
                        "runtime_check_failed",
                        detail="durable_only",
                        fields={key: field(value) for key, value in values.items()},
                    ),
                ),
                warning="WARNING: runtime diagnostics could not be retained in the maintenance log.",
            )
            _stderr(
                f"Runtime check {item.check.check_id!r} failed ({phase}); diagnostics: {attempt.path}"
            )


def _print_result(result: DoctorResult, verbose: bool) -> None:
    _stderr("EMRYS Doctor", style="bold blue")
    _stderr(f"  Project    PASS  {result.project.source_path.parent}", style="green")
    _stderr(f"  Analysis   PASS  {result.analysis.name}", style="green")
    _stderr("  Inputs     PASS", style="green")
    for label, ready, requirement in (
        ("Storage", result.storage_ready, "NOT QUALIFIED"),
        (
            "Runtime",
            result.runtime_ready,
            "NOT PREPARED" if result.inspection is None else "CHECKS FAILED",
        ),
        ("Execution", result.execution_ready, "NOT ADMITTED"),
    ):
        _stderr(
            f"  {label:<10} {'PASS' if ready else requirement}",
            style="green" if ready else "red",
        )
    if verbose:
        package = result.installed_package
        if package is not None:
            _stderr(f"Installed EMRYS: {package.root}")
            _stderr(f"Package SHA-256: {package.content_sha256}")
            _stderr(f"Build commit: {package.git_commit or 'unrecorded'}")
        if result.inspection is not None:
            _stderr(f"Runtime inventory: {result.inspection.profile_path}")
            _stderr(f"Runtime inventory SHA-256: {result.inspection.profile_sha256}")
            for observation in result.inspection.observations:
                if observation.status == "pass":
                    _stderr(
                        f"  {observation.check.check_id!r}: pass; "
                        + json.dumps(
                            {
                                "observed": observation.observed,
                                "detail": observation.detail,
                            },
                            ensure_ascii=True,
                        )
                    )
            _record_runtime_failures(result.inspection, phase="diagnosis")
        for binding in result.bindings:
            _stderr(
                f"Binding {binding.check_id}: {binding.path} -> {binding.resolved_path} sha256:{binding.sha256}"
            )
    _stderr(
        "EMRYS is ready." if result.ready else "EMRYS is not ready.",
        style="green" if result.ready else "yellow",
    )
    for blocker in result.blockers:
        _stderr(f"EXECUTION REQUIREMENT: {blocker}", style="red")
    for remediation in result.remediations:
        _stderr(f"REMEDIATION: {remediation}", style="yellow")


def _print_repair_plan(plan: _RepairPlan, verbose: bool) -> None:
    _stderr(f"EMRYS Doctor {plan.operation} plan", style="bold blue")
    _stderr("First Doctor setup can take 5–25 minutes.", style="yellow")
    if not verbose:
        return
    _stderr(f"  Project: {plan.project.source_path}")
    _stderr(f"  Runtime work: {plan.runtime_work}")
    if plan.execution is not None:
        for line in plan.execution.submission_summary():
            _stderr(f"  {line}")
    actions = []
    if plan.storage is not None:
        _stderr(f"  Direct storage receipt: {plan.storage.receipt_path}")
        for role, root in zip(
            storage_qualification.ROLES,
            plan.storage.roots,
            strict=True,
        ):
            _stderr(f"  Storage probe ({role}): {root}")
        actions.append("single-host storage qualification")
    if plan.runtime is not None:
        runtime = plan.runtime
        _stderr(f"  Managed runtime: {runtime.managed_root}")
        _stderr(f"  Maintenance claim: {runtime.profile.parent / 'maintenance.lock'}")
        if runtime.replacement_seal is not None:
            _stderr(f"  Replacement seal: {runtime.replacement_seal}")
        _stderr(
            "  A retained claim blocks further repair; release errors require reconciliation."
        )
        _stderr(f"  Pixi: {runtime.pixi}")
        actions.extend(label for label, *_ in _repair_actions(plan))
    if plan.execution is not None and isinstance(
        plan.execution.placement, SlurmPlacement
    ):
        actions.append(
            "compute runtime/storage checks (head finalization follows)"
            if plan.compute
            else "Slurm runtime/storage checks, then head finalization"
        )
    actions.append("rechecking Project, package, runtime, and storage readiness")
    _stderr("  Actions: " + "; ".join(actions), style="blue")
    _stderr("Checks repeat because inputs, packages, and node visibility can change.")
    _stderr("Declared input files and site/user environments will not be modified.")


def _confirm_repair(plan: _RepairPlan) -> bool:
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        return False
    console_print(f"Apply this {plan.operation} plan? [y/N] ", end="")
    return sys.stdin.readline().strip().casefold() in {"y", "yes"}


def _qualification_binding(result: DoctorResult) -> str:
    if (
        not result.runtime_ready
        or not result.execution_ready
        or result.inspection is None
        or result.installed_package is None
    ):
        raise DoctorRepairError(
            "Runtime must pass inspection before compute qualification"
        )
    return orchestration_contracts.canonical_sha256(
        {
            "project": result.project.source_sha256,
            "analysis": result.analysis.revision.canonical_bytes.decode(),
            "package": result.installed_package.content_sha256,
            "inventory": result.inspection.profile_sha256,
            "runtime": [
                [item.check_id, str(item.path), str(item.resolved_path), item.sha256]
                for item in result.bindings
                if item.check_id != "storage_qualification"
            ],
        }
    )


def _qualify_slurm(
    plan: _RepairPlan,
    result: DoctorResult,
    attempt: AttemptLog | None,
    controls: LogControls,
    timing: _DoctorTiming | None = None,
) -> DoctorResult:
    progress = partial(phase_progress, on_complete=timing.observe if timing else None)
    execution = plan.execution
    assert execution is not None
    binding = _qualification_binding(result)
    workspace = plan.project.source_path.parent
    fasta = Path(str(result.analysis.workflow_inputs["reference"]["fasta"]["path"]))
    if plan.compute:
        execution.attempt_placement(os.environ.get("SLURM_JOB_ID"))
        if (
            plan.qualification_binding is not None
            and binding != plan.qualification_binding
        ):
            raise DoctorRepairError(
                "Project, package, or runtime changed before compute qualification"
            )
        resolve_resource_policy(execution.resource_policy, observe_allocation())
        with progress("Checking storage from the compute node"):
            receipt = storage_qualification.qualify_compute(workspace, fasta)
        _stderr(
            f"Compute checks passed; storage evidence: {receipt}. Head finalization is required."
        )
        return result
    assert attempt is not None
    submission = slurm_submission.plan_submission(
        execution,
        emrys_argv=(
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "emrys",
            "doctor",
            "--project",
            str(plan.project.source_path),
            "--analysis",
            plan.analysis_name,
            "--profile",
            str(execution.source_path),
            "--repair",
            "--execute",
            "--compute",
            "--qualification-binding",
            binding,
            *(("--verbose",) if controls.verbose else ()),
            "--log-root",
            str(controls.root),
        ),
        log_dir=attempt.path.parent,
    )
    submitted: tuple[str, str | None] | None = None

    def announce(job_id: str, cluster: str | None) -> None:
        nonlocal submitted
        submitted = job_id, cluster
        attempt.best_effort(
            lambda: attempt.logger(component="maintenance", phase="repair").info(
                "Compute qualification submitted.",
                extra=event(
                    "repair_compute_submitted",
                    fields={
                        "scheduler_job_id": field(job_id),
                        "scheduler_cluster": field(cluster),
                        "binding": field(binding),
                        "stdout": field(submission.stdout_pattern),
                        "stderr": field(submission.stderr_pattern),
                    },
                ),
            ),
            warning="WARNING: scheduler logging degraded; submission records are retained.",
        )

    try:
        with progress("Slurm submission-to-return wait"):
            job_id = slurm_submission.submit(
                submission,
                record_path=attempt.path.parent / "slurm-submit.stdout",
                wait=True,
                on_submitted=announce,
                show_details=controls.verbose,
            )
    except slurm_submission.SlurmSubmissionError:
        with suppress(Exception):
            if timing is not None:
                timing.observe_scheduler(submission, submitted)
        raise
    with suppress(Exception):
        if timing is not None:
            timing.observe_scheduler(submission, submitted)
    with progress("Verifying the checked runtime and Project"):
        _readmit_repair_plan(replace(plan, runtime=None), before_storage=False)
        observed = diagnose_project(
            plan.project.source_path,
            analysis_name=plan.analysis_name,
            execution_profile=execution.source_path,
        )
    if timing is not None:
        timing.observe_runtime(observed.inspection, phase="head_requalification")
    _record_runtime_failures(
        observed.inspection, phase="head_requalification", attempt=attempt
    )
    if _qualification_binding(observed) != binding:
        raise DoctorRepairError(
            "Project, package, or runtime changed during compute qualification"
        )
    with progress("Checking shared storage from the head node"):
        try:
            storage_qualification.qualify_head(workspace, fasta)
        except (storage_qualification.StorageQualificationError, OSError) as exc:
            raise DoctorRepairError(
                f"Head storage finalization failed after Slurm job {job_id}: {str(exc)!a}"
            ) from exc
    with progress("Verifying final Project readiness"):
        final = diagnose_project(
            plan.project.source_path,
            analysis_name=plan.analysis_name,
            execution_profile=execution.source_path,
        )
    if timing is not None:
        timing.observe_runtime(final.inspection, phase="head_final_readiness")
    if final.execution_profile != execution:
        raise DoctorRepairError(
            f"Execution profile changed during head finalization after Slurm job {job_id}"
        )
    if final.ready and _qualification_binding(final) != binding:
        raise DoctorRepairError(
            f"Project, package, or runtime changed during head finalization after Slurm job {job_id}"
        )
    return final


def _execute_repair(
    plan: _RepairPlan, *, controls: LogControls, timing: _DoctorTiming | None = None
) -> DoctorResult:
    progress = partial(phase_progress, on_complete=timing.observe if timing else None)
    try:
        attempt = open_attempt_log(
            controls=controls,
            identity=AttemptIdentity(
                "maintenance",
                plan.project.source_sha256[:16],
                f"repair-{uuid.uuid4().hex}",
                "emrys-doctor",
            ),
            mode="repair",
            component="maintenance",
        )
    except (ApplicationLogError, ValueError) as exc:
        raise DoctorRepairError(
            f"could not open Doctor log before mutation: {exc}"
        ) from exc
    record = partial(
        attempt.best_effort,
        warning="WARNING: Doctor logging degraded; requalification remains controlling.",
    )

    def emit(
        name: str, message: str, *, phase: str = "repair", **values: object
    ) -> bool:
        return record(
            lambda: attempt.logger(component="maintenance", phase=phase).info(
                message,
                extra=event(
                    name,
                    fields={key: field(value) for key, value in values.items()},
                    detail="durable_only",
                ),
            )
        )

    def flush_timing() -> None:
        if timing is not None:
            timing.flush(emit)

    started: dict[str, object] = {
        "project": plan.project.source_path,
        "runtime_work": plan.runtime_work,
    }
    if plan.storage is not None:
        started["storage_receipt"] = plan.storage.receipt_path
    if plan.runtime is not None:
        runtime = plan.runtime
        started.update(
            {
                "managed_root": runtime.managed_root,
                "package_output": attempt.path.parent / "package-output.log",
                "pixi": runtime.pixi,
                "pixi_sha256": runtime.pixi_sha256,
                "pixi_manifest_sha256": hashlib.sha256(
                    runtime.manifest_bytes
                ).hexdigest(),
                "pixi_lock_sha256": hashlib.sha256(runtime.lock_bytes).hexdigest(),
            }
        )
    emit("repair_started", f"Project {plan.operation} started.", **started)
    claim: tuple[Path, os.stat_result, bytes] | None = None
    try:
        if plan.runtime is not None:
            runtime_root = onboarding.project_runtime_directory(plan.project)
            if runtime_root != plan.runtime.profile.parent:
                raise DoctorRepairError(
                    "Doctor runtime parent changed before maintenance"
                )
            _readmit_runtime_seal_plan(plan.runtime)
            claim_path = runtime_root / "maintenance.lock"
            payload = f"emrys-doctor:{uuid.uuid4().hex}\n".encode("ascii")
            ownership = acquire_lock(
                claim_path, payload, DoctorRepairError, retain_on_failure=True
            )
            claim = claim_path, ownership, payload
        with progress("Verifying the approved plan inputs"):
            _readmit_repair_plan(plan, before_storage=True)
        if plan.storage is not None:
            emit(
                "storage_qualification_started",
                "Single-host storage qualification started.",
                receipt=plan.storage.receipt_path,
            )
            with progress("Qualifying single-host storage"):
                qualified = storage_qualification.execute_direct_qualification(
                    plan.storage
                )
            emit(
                "storage_qualification_admitted",
                "Single-host storage qualification admitted.",
                receipt=qualified.receipt_path,
                sha256=qualified.receipt_sha256,
            )
        runtime = plan.runtime
        if runtime is not None:
            _admit_managed_root(runtime)
            with (
                attempt.package_output() as output,
                tempfile.TemporaryDirectory(
                    prefix="repair-", dir=runtime.managed_root / "cache"
                ) as temporary,
            ):
                for label, argv, environment in _repair_actions(plan):
                    manager = Path(argv[0]).name
                    if manager == "pixi" and os.path.lexists(
                        runtime.managed_root / ".pixi/config.toml"
                    ):
                        raise DoctorRepairError(
                            "Project-local Pixi configuration appeared during repair"
                        )
                    emit(
                        "package_manager_started",
                        "Package-manager action started.",
                        manager=manager,
                        argv=argv,
                    )
                    with progress(label):
                        completed = subprocess.run(
                            argv,
                            cwd=plan.installed_package.root,
                            env={**environment, "TMPDIR": temporary, "NO_COLOR": "1"},
                            stdout=output,
                            stderr=subprocess.STDOUT,
                            check=False,
                        )
                        emit(
                            "package_manager_completed",
                            "Package-manager action completed.",
                            manager=manager,
                            exit_status=completed.returncode,
                        )
                        if completed.returncode != 0:
                            raise DoctorRepairError(
                                f"{manager} exited with status {completed.returncode}; see {attempt.path.parent / 'package-output.log'}"
                            )
            with (
                tempfile.TemporaryDirectory(prefix="emrys-doctor-") as temporary,
                progress("Discovering and verifying the installed runtime"),
            ):
                _readmit_repair_plan(plan, before_storage=False)
                candidate = onboarding.discover_runtime_profile(
                    project=plan.project.source_path,
                    environment={
                        **_managed_discovery_environment(plan),
                        "TMPDIR": temporary,
                    },
                    root=plan.installed_package.root,
                    python_executable=Path(sys.executable),
                )
            if timing is not None:
                timing.observe_runtime(candidate, phase="runtime_discovery")
            _record_runtime_failures(
                candidate, phase="runtime_discovery", attempt=attempt
            )
            if not _profile_is_managed(
                tuple(item.check for item in candidate.observations),
                runtime,
            ):
                raise DoctorRepairError(
                    "repaired runtime discovery escaped the Project-managed environment"
                )
            if not candidate.required_ready:
                raise DoctorRepairError("repaired runtime did not pass qualification")
            if runtime.replacement_seal is not None:
                seal_data = runtime_seal_bytes(candidate, runtime.replacement_seal)
                publish_exclusive(
                    runtime.replacement_seal,
                    seal_data,
                    DoctorRepairError,
                )
                reference = shared_runtime_profile_bytes(
                    runtime.replacement_seal,
                    seal_data,
                    Path(sys.executable),
                )
                replacement_checks = runtime_profile_checks(
                    reference, plan.installed_package.root
                )
                replacement_library = next(
                    Path(check.target)
                    for check in replacement_checks
                    if check.check_id == "renv_library"
                )
                with tempfile.TemporaryDirectory(prefix="emrys-doctor-") as temporary:
                    candidate = inspect_runtime_profile_bytes(
                        reference,
                        runtime.profile,
                        checks=replacement_checks,
                        environment={
                            **guarded_r_environment(
                                plan.installed_package.root,
                                replacement_library,
                            ),
                            "TMPDIR": temporary,
                        },
                    )
                runtime_file_bindings(candidate)
                if not candidate.required_ready:
                    raise DoctorRepairError(
                        "replacement runtime did not pass qualification"
                    )
                if runtime.profile_bytes is None:
                    onboarding.publish_runtime_profile(candidate)
                else:
                    publish_exclusive(
                        runtime.profile,
                        candidate.profile_bytes,
                        DoctorRepairError,
                        replace_expected=runtime.profile_bytes,
                    )
                emit(
                    "runtime_profile_admitted",
                    "Replacement runtime generation admitted.",
                    profile=runtime.profile,
                    sha256=candidate.profile_sha256,
                )
            elif runtime.profile_bytes is None:
                onboarding.publish_runtime_profile(candidate)
                emit(
                    "runtime_profile_admitted",
                    "Managed runtime inventory admitted.",
                    profile=runtime.profile,
                    sha256=candidate.profile_sha256,
                )
            else:
                try:
                    state = runtime.profile.lstat()
                    existing = runtime.profile.read_bytes()
                except OSError as exc:
                    raise DoctorRepairError(
                        f"could not read runtime inventory: {exc}"
                    ) from exc
                if (
                    stat.S_ISLNK(state.st_mode)
                    or not stat.S_ISREG(state.st_mode)
                    or existing != runtime.profile_bytes
                    or existing != candidate.profile_bytes
                ):
                    raise DoctorRepairError(
                        "existing managed profile differs and was preserved"
                    )
        with progress("Checking Project readiness"):
            final = diagnose_project(
                plan.project.source_path,
                analysis_name=plan.analysis_name,
                execution_profile=plan.execution.source_path
                if plan.execution
                else None,
            )
        if timing is not None:
            timing.observe_runtime(final.inspection, phase="project_readiness")
        _record_runtime_failures(
            final.inspection, phase="project_readiness", attempt=attempt
        )
        compute_checked = False
        if plan.execution is not None and isinstance(
            plan.execution.placement, SlurmPlacement
        ):
            final = _qualify_slurm(plan, final, attempt, controls, timing)
            _record_runtime_failures(
                final.inspection, phase="project_readiness", attempt=attempt
            )
            compute_checked = plan.compute
        if not compute_checked and not final.ready:
            raise DoctorRepairError("Project remained not ready after verification")
        if claim is not None:
            release_lock(*claim, DoctorRepairError)
            claim = None
        flush_timing()
        if compute_checked:
            record(
                lambda: attempt.terminal(
                    event_name="repair_compute_checked",
                    message="Compute runtime and storage checks passed; head finalization follows.",
                )
            )
        else:
            record(
                lambda: attempt.terminal(
                    event_name="repair_requalified",
                    message=f"Project {plan.operation} completed.",
                    fields={
                        "ready": field(final.ready, console=True),
                        "storage_ready": field(final.storage_ready),
                        "runtime_ready": field(final.runtime_ready),
                    },
                )
            )
        return final
    except KeyboardInterrupt:
        flush_timing()
        record(
            lambda: attempt.interrupt_best_effort(
                message=f"Project {plan.operation} interrupted."
            )
        )
        raise
    except (
        DoctorInputError,
        DoctorRepairError,
        RuntimeInspectionError,
        storage_qualification.StorageQualificationError,
        onboarding.OnboardingError,
        orchestration_contracts.ContractValidationError,
        slurm_submission.SlurmSubmissionError,
        ExecutionProfileError,
        ResourceConfigError,
        OSError,
        ApplicationLogError,
    ) as exc:
        error = str(exc)
        flush_timing()
        record(
            lambda: attempt.fail(
                phase="repair",
                message=f"Project {plan.operation} failed.",
                fields={"error": field(error)},
            )
        )
        raise DoctorRepairError(f"{exc}; diagnostics: {attempt.path}") from exc
    finally:
        with suppress(Exception):
            if claim is not None and os.path.lexists(claim[0]):
                _stderr(
                    f"Runtime maintenance claim remains for explicit reconciliation: {claim[0]}"
                )
        with suppress(Exception):
            attempt.close()


def configure_parser(parser: argparse.ArgumentParser) -> None:
    onboarding.add_project_argument(parser)
    parser.add_argument(
        "--profile",
        metavar="NAME_OR_ABSOLUTE_PATH",
        help="Project profile name or absolute path; defaults to runtime/profiles/default.yaml.",
    )
    parser.add_argument(
        "--analysis",
        help="Named Analysis; required only when the Project defines more than one.",
    )
    add_log_arguments(parser)
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Preview verification and any required EMRYS-owned runtime repair.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply --repair noninteractively; invalid without --repair.",
    )
    parser.add_argument(
        "--compute",
        action="store_true",
        help="Advanced: diagnose or repair inside an existing Slurm allocation; site finalization remains on the head node.",
    )
    parser.add_argument("--qualification-binding", help=argparse.SUPPRESS)
    parser.set_defaults(_command_parser=parser)


def doctor_from_args(arguments: argparse.Namespace) -> int:
    timing = _DoctorTiming()
    started = elapsed = status = None
    with suppress(Exception):
        started = time.monotonic()
    try:
        status = _doctor_from_args(arguments, timing)
        return status
    finally:
        with suppress(Exception):
            if started is not None:
                elapsed = time.monotonic() - started
        with suppress(Exception):
            timing.finish(elapsed, status)


def _doctor_from_args(arguments: argparse.Namespace, timing: _DoctorTiming) -> int:
    progress = partial(phase_progress, on_complete=timing.observe)
    timing.detail = arguments.verbose
    if arguments.execute and not arguments.repair:
        print("emrys: error: --execute requires --repair", file=sys.stderr)
        return 2
    try:
        compute = getattr(arguments, "compute", False)
        timing.context = "compute" if compute else "head/local"
        expected = getattr(arguments, "qualification_binding", None)
        job_id = os.environ.get("SLURM_JOB_ID", "").strip()
        if compute and not is_canonical_slurm_job_id(job_id):
            raise DoctorInputError("--compute requires an existing Slurm allocation")
        if job_id and not compute:
            raise DoctorInputError(
                "Run Doctor on the head node, or select the advanced --compute option"
            )
        with progress("Inspecting the Project and runtime"):
            result = diagnose_project(
                onboarding.project_definition_path(arguments.project),
                analysis_name=arguments.analysis,
                execution_profile=getattr(arguments, "profile", None),
            )
        timing.observe_runtime(
            result.inspection, phase="compute_runtime" if compute else "diagnosis"
        )
        delegated = slurm_submission.delegate_binding() is not None
        if delegated:
            _record_runtime_failures(result.inspection, phase="compute_runtime")
            if not compute or not expected or result.execution_profile is None:
                raise DoctorInputError(
                    "Private Doctor delegation requires compute input bindings"
                )
            slurm_submission.delegate_job_id(result.execution_profile)
            if _qualification_binding(result) != expected:
                raise DoctorInputError(
                    "Project, package, or runtime changed before compute qualification"
                )
            timing.context = "delegated compute"
        elif expected is not None:
            raise DoctorInputError(
                "Compute input bindings require private Slurm delegation"
            )
        if result.installed_package is None:
            _print_result(result, False)
            return 1
        controls = resolve_log_controls(
            verbose=arguments.verbose,
            cli_root=arguments.log_root,
            default_root=result.project.source_path.parent / "logs/application",
        )
    except (
        DoctorInputError,
        DoctorRepairError,
        LogControlError,
        onboarding.OnboardingError,
        slurm_submission.SlurmSubmissionError,
    ) as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return 2
    detail = controls.verbose
    _print_result(result, detail)
    slurm = result.execution_profile is not None and isinstance(
        result.execution_profile.placement, SlurmPlacement
    )
    if not arguments.repair or (result.ready and not slurm):
        return 0 if result.ready else 1
    try:
        plan = _build_repair_plan(result)
        plan = replace(plan, compute=compute, qualification_binding=expected)
        if delegated:
            if not arguments.execute:
                raise DoctorRepairError("Private Doctor delegation requires --execute")
            with progress("Verifying the approved plan inputs"):
                _readmit_repair_plan(plan, before_storage=True)
            _qualify_slurm(plan, result, None, controls, timing)
            return 0
    except (
        DoctorRepairError,
        ResourceConfigError,
        ExecutionProfileError,
        storage_qualification.StorageQualificationError,
    ) as exc:
        print(f"DOCTOR BLOCKED: {exc}", file=sys.stderr)
        return 1
    _print_repair_plan(plan, detail)
    if not arguments.execute:
        try:
            confirmed = _confirm_repair(plan)
        except KeyboardInterrupt:
            confirmed = False
        if not confirmed:
            _stderr(
                f"{plan.operation.capitalize()} preview complete; no files were written."
            )
            return 1
    try:
        final = _execute_repair(plan, controls=controls, timing=timing)
    except KeyboardInterrupt:
        print(
            f"{plan.operation.capitalize()} interrupted; partial state and submission records were preserved. A submitted Slurm job may still be running.",
            file=sys.stderr,
        )
        return 130
    except DoctorRepairError as exc:
        print(f"{plan.operation.upper()} FAILED: {exc}", file=sys.stderr)
        return 1
    if compute and slurm:
        return 0
    _print_result(final, detail)
    return 0 if final.ready else 1


__all__ = (
    "DESCRIPTION",
    "DoctorInputError",
    "DoctorRepairError",
    "DoctorResult",
    "configure_parser",
    "diagnose_project",
    "doctor_from_args",
    "required_tool_identities",
    "storage_runtime_binding",
)
