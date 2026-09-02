"""Project-aware readiness diagnosis and explicit managed-runtime repair."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from emrys import analyses as analysis_modules
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import AnalysisRevision
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeInspectionError,
    inspect_runtime_profile_bytes,
    load_runtime_profile_contract,
    runtime_profile_bytes,
)
from emrys.evidence.storage_inventory import qualification as storage_qualification
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
    resolve_log_controls,
)
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_package_tree_identity,
)
from emrys.libraries.exclusive_publication import publish_exclusive
from emrys.libraries.process_environment import (
    guarded_r_environment,
    guarded_rscript_argv,
    sanitized_subprocess_environment,
)
from emrys.libraries.source_authority import (
    SourceCheckout,
    SourceCheckoutError,
    controlled_python_argv,
    inspect_source_checkout,
)
from emrys.orchestration.local_pilot import onboarding
from emrys.orchestration.local_pilot.execution_profile import (
    ExecutionProfileError,
    load_execution_profile,
    project_execution_profile_path,
)
from emrys.orchestration.local_pilot.normalization import (
    AnalysisAdmission,
    ProjectAdmission,
)

DESCRIPTION = (
    "Diagnose one Project across inputs, storage, runtime, and execution. "
    "Diagnosis and repair preview are read-only; an explicitly confirmed "
    "repair may qualify direct storage and restore only EMRYS-owned runtime "
    "state through uv, Pixi, and renv."
)

StorageRequirement = Literal["direct", "slurm"]


class DoctorInputError(RuntimeError):
    """The doctor invocation contains malformed or unsafe input."""


class DoctorRepairError(RuntimeError):
    """The managed-runtime repair cannot proceed or did not complete."""


@dataclass(frozen=True, slots=True)
class RuntimeBinding:
    """One exact path-and-content binding admitted from the runtime inventory."""

    check_id: str
    path: Path
    resolved_path: Path
    sha256: str
    observed: str
    identity_kind: Literal["file", "package_tree"] | None = None


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Immutable readiness result consumed by Run planning."""

    project: ProjectAdmission
    analysis: AnalysisAdmission
    source_root: Path
    source_commit: str | None
    inspection: RuntimeInspection | None
    bindings: tuple[RuntimeBinding, ...]
    blockers: tuple[str, ...]
    remediations: tuple[str, ...]
    storage_ready: bool = True
    runtime_ready: bool = True
    execution_ready: bool = True

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
    profile = inspection.profile_path if runtime_profile_path is None else runtime_profile_path
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
    identities.append(identity("storage_qualification", bound["storage_qualification"].observed))
    return tuple(sorted(identities, key=lambda item: item["name"]))


_PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _absolute_path(value: str | Path) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else Path.cwd() / path
    return Path(os.path.abspath(path))


def workspace_location_blockers(workspace: Path, source_root: Path) -> tuple[list[str], list[str]]:
    """Admit the already-created Project root without legacy absent-workspace logic."""

    if workspace == source_root or workspace in source_root.parents or source_root in workspace.parents:
        return [f"workspace overlaps the EMRYS source checkout: {workspace}"], [
            "Choose a Project outside and not containing the EMRYS source checkout."
        ]
    try:
        state = workspace.lstat()
        resolved = workspace.resolve(strict=True)
    except OSError as exc:
        raise DoctorInputError(f"Project root is unavailable: {workspace}: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode) or resolved != workspace:
        raise DoctorInputError(f"Project root must be a canonical real directory: {workspace}")
    if not os.access(workspace, os.R_OK | os.W_OK | os.X_OK):
        return [f"Project root is not readable, writable, and searchable: {workspace}"], [
            f"Grant user access to the Project root: {workspace}"
        ]
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
            check_type, target, expected = "path_visibility", declaration.target, "readable"
            probe_args = (("directory_readable",) if declaration.kind == "package_tree" else ("file_readable",))
            if declaration.kind == "package_tree":
                package_trees.add(check_id)
            else:
                files.add(check_id)
        additions.append(
            RuntimeCheck(
                check_id, check_type, "local", True, target, probe_args,
                expected, declaration.description,
            )
        )
    return (
        tuple(additions),
        frozenset(package_trees),
        frozenset(files),
    )


def validate_runtime_profile_contract(
    checks: tuple[RuntimeCheck, ...],
    source_root: Path,
    *,
    expected_additions: tuple[RuntimeCheck, ...] = (),
    allow_derived_dependencies: bool = False,
) -> None:
    """Bind editable runtime paths plus one selected module to fixed policy."""

    try:
        _bytes, policy = load_runtime_profile_contract(onboarding.runtime_policy_path())
    except RuntimeInspectionError as exc:
        raise DoctorInputError(f"Could not load fixed runtime policy: {exc}") from exc
    fixed_count = len(policy)
    selected_fixed = checks[:fixed_count]
    shape = lambda values: tuple(  # noqa: E731 - compact immutable projection
        (item.check_id, item.check_type) for item in values
    )
    if shape(selected_fixed) != shape(policy):
        raise DoctorInputError("Runtime inventory must begin with the exact ordered fixed-policy roster")
    selected = {item.check_id: item for item in selected_fixed}
    fixed = {item.check_id: item for item in policy}
    rscript = selected["rscript"].target
    immutable = lambda item: (  # noqa: E731 - compact fixed-policy projection
        item.runtime_context,
        item.required,
        item.expected,
        item.description,
    )
    for check in selected_fixed:
        expected = fixed[check.check_id]
        dynamic = check.check_id in {"snakemake", "sha256_python", "picard"}
        wanted_args = (rscript,) if check.check_type == "r_namespace" else expected.probe_args
        target_valid = (
            check.target == expected.target if check.check_type == "r_namespace" else Path(check.target).is_absolute()
        )
        if (
            immutable(check) != immutable(expected)
            or not target_valid
            or (not dynamic and check.probe_args != wanted_args)
        ):
            raise DoctorInputError(f"Runtime check changes fixed policy: {check.check_id}")
    renv_library = Path(selected["renv_library"].target)
    try:
        state = renv_library.lstat()
        canonical_library = renv_library.resolve(strict=True)
    except OSError as exc:
        raise DoctorInputError(f"renv library is unavailable: {renv_library}: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode) or canonical_library != renv_library:
        raise DoctorInputError(f"renv library must be a canonical real directory: {renv_library}")
    python = selected["python"].target
    relations = (
        selected["snakemake"].target == python
        and selected["snakemake"].probe_args == controlled_python_argv(python, "-m", "snakemake", "--version")[1:]
        and selected["sha256_python"].target == python
        and selected["sha256_python"].probe_args == ("python_hashlib",)
        and selected["picard"].target == selected["java"].target
        and selected["picard"].probe_args == ("-jar", selected["picard_jar"].target, "MarkDuplicates", "--version")
        and Path(selected["renv_project"].target) == source_root
    )
    if not relations:
        raise DoctorInputError("Runtime inventory changes a fixed cross-check binding")
    additions = checks[fixed_count:]
    if not allow_derived_dependencies and additions != expected_additions:
        raise DoctorInputError("Runtime inventory differs from the selected analysis-module dependencies")
    for check in additions:
        valid = check.required and check.runtime_context == "local" and (
            check.check_type == "tool_version" and Path(check.target).is_absolute() and bool(check.probe_args)
            or check.check_type == "r_namespace" and check.probe_args == (rscript,)
            or check.check_type == "path_visibility" and Path(check.target).is_absolute()
            and check.probe_args in {("file_readable",), ("directory_readable",)}
        )
        if not valid:
            raise DoctorInputError(f"Runtime check is not a supported analysis dependency: {check.check_id}")


def runtime_file_bindings(
    inspection: RuntimeInspection,
    *,
    package_tree_ids: frozenset[str] = frozenset(),
    explicit_file_ids: frozenset[str] = frozenset(),
) -> tuple[RuntimeBinding, ...]:
    """Bind executable/jar bytes and exact installed R package trees."""

    bindings: list[RuntimeBinding] = []
    renv_library = next(
        Path(item.check.target) for item in inspection.observations if item.check.check_id == "renv_library"
    )
    for observation in inspection.observations:
        check = observation.check
        if observation.status != "pass" or check.check_id in {
            "renv_project",
            "renv_library",
        }:
            continue
        if check.check_type == "r_namespace" or check.check_id in package_tree_ids:
            try:
                root = renv_library / check.target if check.check_type == "r_namespace" else Path(check.target)
                identity = installed_package_tree_identity(root.resolve(strict=True))
            except (OSError, InstalledPackageIdentityError) as exc:
                raise DoctorInputError(
                    f"Could not bind runtime package tree {check.check_id}: {exc}"
                ) from exc
            expected_root = observation.resolved_path if check.check_type == "r_namespace" else Path(check.target)
            if expected_root is None or identity.root != expected_root:
                raise DoctorInputError(f"Runtime package-tree root changed: {check.check_id}")
            bindings.append(
                RuntimeBinding(
                    check.check_id,
                    identity.root,
                    identity.root,
                    identity.sha256,
                    observation.observed,
                    (
                        "package_tree"
                        if check.check_id in package_tree_ids
                        else None
                    ),
                )
            )
            continue
        path = Path(check.target)
        try:
            resolved = path.resolve(strict=True)
            state = path.lstat()
        except OSError as exc:
            raise DoctorInputError(f"Could not bind runtime file {check.check_id}: {exc}") from exc
        if check.check_id in explicit_file_ids and (
            stat.S_ISLNK(state.st_mode)
            or not stat.S_ISREG(state.st_mode)
            or resolved != path
        ):
            raise DoctorInputError(
                f"Analysis dependency must be a canonical real file: {check.check_id}"
            )
        try:
            data = resolved.read_bytes()
        except OSError as exc:
            raise DoctorInputError(f"Could not bind runtime file {check.check_id}: {exc}") from exc
        bindings.append(
            RuntimeBinding(
                check.check_id,
                path,
                resolved,
                hashlib.sha256(data).hexdigest(),
                observation.observed,
                "file" if check.check_id in explicit_file_ids else None,
            )
        )
    return tuple(bindings)


def diagnose_project(
    project_path: str | Path,
    workspace: str | Path | None = None,
    runtime_inventory: str | Path | None = None,
    *,
    storage_requirement: StorageRequirement | None = None,
    analysis_name: str | None = None,
    expected_analysis_revision: AnalysisRevision | None = None,
    allow_legacy: bool = False,
    require_reporter: bool = True,
) -> DoctorResult:
    """Diagnose Project execution, storage, and runtime readiness without writes."""

    project = _absolute_path(project_path)
    execution_error: str | None = None
    if storage_requirement is None:
        execution_path = project_execution_profile_path(project, None)
        try:
            execution = load_execution_profile(config_path=execution_path)
            storage_requirement = execution.placement.kind
        except ExecutionProfileError as exc:
            execution_error = str(exc)
            storage_requirement = "direct"
    root = _absolute_path(onboarding.source_root())
    workspace_path = _absolute_path(project.parent if workspace is None else workspace)
    blockers, remediations = workspace_location_blockers(workspace_path, root)
    try:
        source_commit = inspect_source_checkout(
            root=root,
            package_root=_PACKAGE_ROOT,
            require_clean=True,
        ).commit
    except SourceCheckoutError as exc:
        source_commit = None
        blockers.append(f"source checkout is not ready: {exc}")
        remediations.append("Use the clean reviewed EMRYS checkout and workflow environment.")
    try:
        admitted_project = onboarding.validate_project(
            project,
            root=root,
            allow_legacy=allow_legacy,
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
        storage_remediation = "Run `emrys doctor --repair` in the intended direct execution context."
    elif storage_requirement == "slurm":
        admit_storage = storage_qualification.admit_final_qualification
        storage_label = "storage is not site-qualified"
        storage_remediation = (
            f"Run `emrys debug storage-qualification` for Project {workspace_path} "
            f"and reference FASTA {fasta}."
        )
    else:
        raise DoctorInputError(f"unsupported storage requirement: {storage_requirement}")
    try:
        bindings = (storage_runtime_binding(admit_storage(workspace_path, fasta)),)
    except storage_qualification.StorageQualificationError as exc:
        bindings = ()
        blockers.append(f"{storage_label}: {exc}")
        remediations.append(storage_remediation)
    foundations = DoctorResult(
        project=admitted_project,
        analysis=analysis,
        source_root=root,
        source_commit=source_commit,
        inspection=None,
        bindings=bindings,
        blockers=tuple(blockers),
        remediations=tuple(remediations),
        storage_ready=bool(bindings),
        runtime_ready=False,
    )
    profile_path = (
        onboarding.runtime_profile_path(project)
        if runtime_inventory is None
        else _absolute_path(runtime_inventory)
    )
    if runtime_inventory is None and not os.path.lexists(profile_path):
        result = replace(
            foundations,
            blockers=(
                *foundations.blockers,
                f"runtime inventory is not admitted: {profile_path}",
            ),
            remediations=tuple(
                dict.fromkeys(
                    (
                        *foundations.remediations,
                        "Run `emrys doctor --repair`, or admit a complete site runtime "
                        "with `emrys runtime discover --execute`.",
                    )
                )
            ),
        )
    else:
        try:
            profile_bytes, declared_checks = load_runtime_profile_contract(profile_path)
            _policy_bytes, fixed_policy = load_runtime_profile_contract(
                onboarding.runtime_policy_path()
            )
        except RuntimeInspectionError as exc:
            raise DoctorInputError(str(exc)) from exc
        fixed_checks = declared_checks[: len(fixed_policy)]
        additions, package_tree_ids, explicit_file_ids = _module_dependency_checks(
            foundations.analysis.module.descriptor,
            fixed_checks,
        )
        selected_checks = (
            (*fixed_checks, *additions)
            if len(declared_checks) == len(fixed_policy)
            else declared_checks
        )
        validate_runtime_profile_contract(
            selected_checks,
            foundations.source_root,
            expected_additions=additions,
        )
        if selected_checks != declared_checks:
            profile_bytes = runtime_profile_bytes(selected_checks)
        renv_library = next(
            Path(check.target)
            for check in fixed_checks
            if check.check_id == "renv_library"
        )
        try:
            inspection = inspect_runtime_profile_bytes(
                profile_bytes,
                profile_path,
                "local",
                environment=guarded_r_environment(
                    foundations.source_root,
                    renv_library,
                ),
            )
        except RuntimeInspectionError as exc:
            raise DoctorInputError(str(exc)) from exc
        blockers = list(foundations.blockers)
        remediations = list(foundations.remediations)
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
            item
            for item in inspection.observations
            if item.check.required and item.status != "pass"
        )
        blockers.extend(
            f"{item.check.check_id}: {item.status} ({item.observed})"
            for item in failed
        )
        fixed_ids = {check.check_id for check in fixed_checks}
        custom_ids = {
            dependency.dependency_id
            for dependency in foundations.analysis.module.descriptor.dependencies
            if isinstance(dependency, analysis_modules.AnalysisDependencyV1)
        }
        if any(item.check.check_id in fixed_ids for item in failed):
            remediations.append(
                "Run `emrys doctor --repair` for an EMRYS-managed runtime, or repair "
                "and re-admit the selected site environment without editing runtime.tsv."
            )
        if any(item.check.check_id in custom_ids for item in failed):
            remediations.append(
                "Install the selected analysis module and its declared dependencies "
                "with their package manager, then rerun Doctor; managed repair "
                "restores only the fixed EMRYS runtime."
            )
        result = replace(
            foundations,
            inspection=inspection,
            bindings=(
                *runtime_file_bindings(
                    inspection,
                    package_tree_ids=package_tree_ids,
                    explicit_file_ids=explicit_file_ids,
                ),
                *foundations.bindings,
            ),
            blockers=tuple(blockers),
            remediations=tuple(dict.fromkeys(remediations)),
            runtime_ready=python_ready and not failed,
        )
    if execution_error is None:
        return result
    return replace(
        result,
        blockers=(
            *result.blockers,
            f"default execution profile is not admitted: {execution_error}",
        ),
        remediations=tuple(
            dict.fromkeys(
                (
                    *result.remediations,
                    "Restore a valid Project-owned runtime/profiles/default.yaml; "
                    "Doctor preserves operator execution policy.",
                )
            )
        ),
        execution_ready=False,
    )


@dataclass(frozen=True, slots=True)
class _ManagedRuntimePlan:
    source_root: Path
    managed_root: Path
    profile: Path
    uv: Path
    pixi: Path
    uv_sha256: str
    pixi_sha256: str
    profile_bytes: bytes | None
    manifest_bytes: bytes
    lock_bytes: bytes


@dataclass(frozen=True, slots=True)
class _RepairPlan:
    project: ProjectAdmission
    analysis_name: str
    source_root: Path
    source_commit: str
    storage: storage_qualification.DirectQualificationPlan | None
    runtime: _ManagedRuntimePlan | None


def _profile_is_managed(
    checks: tuple[RuntimeCheck, ...],
    plan: _ManagedRuntimePlan,
) -> bool:
    def owned(target: Path) -> bool:
        try:
            return target.is_relative_to(plan.managed_root) and (
                not os.path.lexists(plan.managed_root) or target.resolve(strict=False).is_relative_to(plan.managed_root)
            )
        except (OSError, RuntimeError):
            return False

    for check in checks:
        if check.check_type == "r_namespace":
            continue
        target = _absolute_path(check.target)
        if check.check_id in {"python", "snakemake", "sha256_python"}:
            allowed = target == Path(sys.executable)
        elif check.check_id == "renv_project":
            allowed = target == plan.source_root
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
        raise DoctorRepairError(f"could not bind package manager {path}: {exc}") from exc


def _build_repair_plan(result: DoctorResult) -> _RepairPlan:
    if result.source_commit is None:
        raise DoctorRepairError("repair requires a clean reviewed EMRYS checkout")
    if not result.execution_ready:
        raise DoctorRepairError(
            "repair preserves execution profiles; restore runtime/profiles/default.yaml"
        )
    project = result.project
    fasta = Path(str(result.analysis.workflow_inputs["reference"]["fasta"]["path"]))
    try:
        storage = (
            None
            if result.storage_ready
            else storage_qualification.plan_direct_qualification(
                project.source_path.parent,
                fasta,
            )
        )
    except storage_qualification.StorageQualificationError as exc:
        raise DoctorRepairError(str(exc)) from exc
    if result.runtime_ready:
        return _RepairPlan(
            project=project,
            analysis_name=result.analysis.name,
            source_root=result.source_root,
            source_commit=result.source_commit,
            storage=storage,
            runtime=None,
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
    venv = result.source_root / ".venv"
    if _absolute_path(sys.prefix) != venv:
        raise DoctorRepairError(f"Python repair is restricted to the active checkout-owned .venv; found {sys.prefix}")
    try:
        state = venv.lstat()
        owned_venv = stat.S_ISDIR(state.st_mode) and not stat.S_ISLNK(state.st_mode)
        owned_venv = owned_venv and venv.resolve(strict=True) == venv
    except OSError as exc:
        raise DoctorRepairError(f"checkout-owned .venv is unavailable: {exc}") from exc
    if not owned_venv or not os.access(venv, os.R_OK | os.W_OK | os.X_OK):
        raise DoctorRepairError(f"checkout-owned .venv is not canonical and writable: {venv}")
    try:
        runtime = onboarding.project_runtime_directory(project)
        resources = _PACKAGE_ROOT / "resources/runtime"
        manifest_bytes = (resources / "pixi.toml").read_bytes()
        lock_bytes = (resources / "pixi.lock").read_bytes()
    except (OSError, onboarding.OnboardingError) as exc:
        raise DoctorRepairError(str(exc)) from exc
    managed = runtime / "managed"
    profile = runtime / "runtime.tsv"
    profile_bytes: bytes | None = None
    profile_checks: tuple[RuntimeCheck, ...] = ()
    if result.inspection is not None:
        if _absolute_path(result.inspection.profile_path) != profile:
            raise DoctorRepairError(
                "the admitted runtime inventory is site- or user-owned and was preserved"
            )
        try:
            profile_bytes, profile_checks = load_runtime_profile_contract(profile)
        except RuntimeInspectionError as exc:
            raise DoctorRepairError(f"could not re-admit the managed runtime inventory: {exc}") from exc
    uv, pixi = _manager("uv"), _manager("pixi")
    managed_plan = _ManagedRuntimePlan(
        source_root=result.source_root,
        managed_root=managed,
        profile=profile,
        uv=uv,
        pixi=pixi,
        uv_sha256=_file_sha256(uv),
        pixi_sha256=_file_sha256(pixi),
        profile_bytes=profile_bytes,
        manifest_bytes=manifest_bytes,
        lock_bytes=lock_bytes,
    )
    if result.inspection is not None:
        if not _profile_is_managed(profile_checks, managed_plan):
            raise DoctorRepairError(
                "the admitted runtime inventory is site- or user-owned and was "
                "preserved; repair that environment or explicitly admit a replacement"
            )
    return _RepairPlan(
        project=project,
        analysis_name=result.analysis.name,
        source_root=result.source_root,
        source_commit=result.source_commit,
        storage=storage,
        runtime=managed_plan,
    )


def _readmit_repair_plan(
    plan: _RepairPlan,
    *,
    before_storage: bool,
) -> None:
    try:
        source = inspect_source_checkout(root=plan.source_root, package_root=_PACKAGE_ROOT, require_clean=True)
        project = onboarding.validate_project(plan.project.source_path, root=plan.source_root).project
        runtime_root = onboarding.project_runtime_directory(project)
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
    ) as exc:
        raise DoctorRepairError(f"repair plan changed before execution: {exc}") from exc
    if (
        source.commit != plan.source_commit
        or project != plan.project
        or (plan.storage is not None and observed_storage != plan.storage)
        or (plan.runtime is not None and runtime_root != plan.runtime.managed_root.parent)
    ):
        raise DoctorRepairError("repair plan changed before execution")
    runtime = plan.runtime
    if runtime is None:
        return
    if _file_sha256(runtime.uv) != runtime.uv_sha256 or _file_sha256(runtime.pixi) != runtime.pixi_sha256:
        raise DoctorRepairError("admitted package manager changed before execution")
    if runtime.profile_bytes is None:
        if os.path.lexists(runtime.profile):
            raise DoctorRepairError("runtime inventory appeared after repair confirmation")
        return
    try:
        state = runtime.profile.lstat()
        data = runtime.profile.read_bytes()
    except OSError as exc:
        raise DoctorRepairError(f"runtime inventory changed before execution: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode) or data != runtime.profile_bytes:
        raise DoctorRepairError("runtime inventory changed before execution")


def _admit_managed_root(plan: _ManagedRuntimePlan) -> None:
    root = plan.managed_root
    try:
        if not os.path.lexists(root):
            root.mkdir(mode=0o700)
        state = root.lstat()
        safe = stat.S_ISDIR(state.st_mode) and not stat.S_ISLNK(state.st_mode)
        safe = safe and root.resolve(strict=True) == root
        if not safe or not os.access(root, os.R_OK | os.W_OK | os.X_OK):
            raise DoctorRepairError(f"managed runtime must be canonical and writable: {root}")
        allowed = {".pixi", "cache", "pixi.lock", "pixi.toml", "renv"}
        unexpected = {path.name for path in root.iterdir()} - allowed
        if unexpected:
            raise DoctorRepairError("foreign managed-runtime entries: " + ", ".join(sorted(unexpected)))
        if os.path.lexists(root / ".pixi/config.toml"):
            raise DoctorRepairError("Project-local Pixi configuration is not permitted during repair")
        for relative in (".pixi", ".pixi/envs", ".pixi/envs/native", ".pixi/envs/r"):
            directory = root / relative
            if os.path.lexists(directory) and (
                directory.is_symlink() or not directory.is_dir() or root not in directory.resolve(strict=True).parents
            ):
                raise DoctorRepairError(f"managed Pixi state is not owned: {directory}")
        for name, data in (
            ("pixi.toml", plan.manifest_bytes),
            ("pixi.lock", plan.lock_bytes),
        ):
            destination = root / name
            if os.path.lexists(destination):
                state = destination.lstat()
                observed = destination.read_bytes()
                if not stat.S_ISREG(state.st_mode) or observed != data:
                    raise DoctorRepairError(f"managed {name} differs from packaged bytes")
            else:
                publish_exclusive(destination, data, DoctorRepairError)
        for relative in (
            "cache",
            "cache/uv",
            "cache/pixi",
            "renv",
            "renv/cache",
            "renv/library",
        ):
            directory = root / relative
            directory.mkdir(mode=0o700, exist_ok=True)
            if directory.is_symlink() or not directory.is_dir():
                raise DoctorRepairError(f"managed directory is not owned state: {directory}")
    except OSError as exc:
        raise DoctorRepairError(f"managed runtime is unavailable: {root}: {exc}") from exc


def _repair_actions(
    plan: _RepairPlan,
) -> tuple[tuple[tuple[str, ...], dict[str, str]], ...]:
    runtime = plan.runtime
    if runtime is None:
        return ()
    base = sanitized_subprocess_environment()
    uv = dict(base)
    uv.update(
        {
            "UV_CACHE_DIR": str(runtime.managed_root / "cache/uv"),
            "UV_PROJECT_ENVIRONMENT": sys.prefix,
        }
    )
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
        if name.startswith(("R_LIBS", "R_PROFILE", "R_ENVIRON", "RENV_")) or name == "R_DEFAULT_PACKAGES":
            del restore[name]
    restore.update(
        {
            "EMRYS_USE_RENV": "1",
            "EMRYS_LOCAL_PILOT_R": "0",
            "RENV_PROJECT": str(plan.source_root),
            "RENV_PATHS_LIBRARY": str(runtime.managed_root / "renv/library"),
            "RENV_PATHS_CACHE": str(runtime.managed_root / "renv/cache"),
            "RENV_CONFIG_SANDBOX_ENABLED": "FALSE",
            "RENV_CONFIG_AUTO_SNAPSHOT": "FALSE",
            "R_PROFILE_USER": str(plan.source_root / ".Rprofile"),
        }
    )
    manifest = str(runtime.managed_root / "pixi.toml")
    restore_argv = guarded_rscript_argv(
        str(runtime.managed_root / ".pixi/envs/r/bin/Rscript"),
        (str(plan.source_root / "scripts/restore_r_environment.R"),),
    )
    return (
        (
            (
                str(runtime.uv),
                "sync",
                "--locked",
                "--no-default-groups",
                "--group",
                "workflow",
                "--python",
                sys.executable,
                "--project",
                str(plan.source_root),
            ),
            uv,
        ),
        (
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
        raise DoctorRepairError("managed renv restore must produce one qualified library")
    library = libraries[0]
    try:
        if library.is_symlink() or not library.is_dir() or library.resolve(strict=True) != library:
            raise DoctorRepairError(f"managed renv library is not owned: {library}")
    except OSError as exc:
        raise DoctorRepairError(f"managed renv library is unavailable: {exc}") from exc
    environment = sanitized_subprocess_environment()
    environment.pop("JAVA_HOME", None)
    environment.update(
        {
            "PATH": str(runtime.managed_root / ".pixi/envs/native/bin"),
            "EMRYS_RSCRIPT": str(
                runtime.managed_root / ".pixi/envs/r/bin/Rscript"
            ),
            "EMRYS_PICARD_JAR": str(jars[0]),
            "EMRYS_RENV_LIBRARY": str(library),
        }
    )
    return environment


def _stderr(message: str) -> None:
    print(message, file=sys.stderr)


def _print_result(result: DoctorResult, detail: LogLevel) -> None:
    _stderr("EMRYS Doctor")
    _stderr(f"  Project    PASS  {result.project.source_path.parent}")
    _stderr(f"  Analysis   PASS  {result.analysis.name}")
    _stderr("  Inputs     PASS")
    for label, ready in (
        ("Storage", result.storage_ready),
        ("Runtime", result.runtime_ready),
        ("Execution", result.execution_ready),
    ):
        _stderr(f"  {label:<10} {'PASS' if ready else 'FAIL'}")
    if detail in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        _stderr(f"Source checkout: {result.source_root}")
        _stderr(f"Source commit: {result.source_commit or 'not admitted'}")
        if result.inspection is not None:
            _stderr(f"Runtime inventory: {result.inspection.profile_path}")
            _stderr(f"Runtime inventory SHA-256: {result.inspection.profile_sha256}")
            for observation in result.inspection.observations:
                _stderr(f"  {observation.check.check_id}: {observation.status} ({observation.observed})")
    if detail is LogLevel.DEBUG:
        for binding in result.bindings:
            _stderr(f"Binding {binding.check_id}: {binding.path} -> {binding.resolved_path} sha256:{binding.sha256}")
    _stderr("EMRYS is ready." if result.ready else "EMRYS is not ready.")
    for blocker in result.blockers:
        _stderr(f"BLOCKER: {blocker}")
    for remediation in result.remediations:
        _stderr(f"REMEDIATION: {remediation}")


def _print_repair_plan(plan: _RepairPlan) -> None:
    _stderr("EMRYS Doctor repair plan")
    _stderr(f"  Project: {plan.project.source_path}")
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
        _stderr(f"  uv: {runtime.uv}")
        _stderr(f"  Pixi: {runtime.pixi}")
        actions.extend(
            (
                "uv sync",
                "Pixi native/R install",
                "renv restore",
                "runtime qualification",
            )
        )
    _stderr("  Actions: " + "; ".join(actions))
    _stderr("Declared input files and site/user environments will not be modified.")


def _confirm_repair() -> bool:
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        return False
    print("Apply this repair? [y/N] ", end="", file=sys.stderr, flush=True)
    return sys.stdin.readline().strip().casefold() in {"y", "yes"}


def _execute_repair(plan: _RepairPlan, *, controls: LogControls) -> DoctorResult:
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
        raise DoctorRepairError(f"could not open repair log before mutation: {exc}") from exc
    logger = attempt.logger(component="maintenance", phase="repair")
    degraded = False

    def record(operation: Callable[[], object]) -> None:
        nonlocal degraded
        if not degraded:
            try:
                degraded = operation() is False
            except Exception:
                degraded = True
            if degraded:
                print(
                    "WARNING: repair logging degraded; requalification remains controlling.",
                    file=sys.stderr,
                )

    def emit(name: str, message: str, **values: object) -> None:
        record(
            lambda: logger.info(
                message,
                extra=event(name, fields={key: field(value) for key, value in values.items()}),
            )
        )

    started: dict[str, object] = {"project": plan.project.source_path}
    if plan.storage is not None:
        started["storage_receipt"] = plan.storage.receipt_path
    if plan.runtime is not None:
        runtime = plan.runtime
        started.update(
            {
                "managed_root": runtime.managed_root,
                "uv": runtime.uv,
                "pixi": runtime.pixi,
                "uv_sha256": runtime.uv_sha256,
                "pixi_sha256": runtime.pixi_sha256,
                "pixi_manifest_sha256": hashlib.sha256(runtime.manifest_bytes).hexdigest(),
                "pixi_lock_sha256": hashlib.sha256(runtime.lock_bytes).hexdigest(),
            }
        )
    emit("repair_started", "Project repair started.", **started)
    try:
        _readmit_repair_plan(plan, before_storage=True)
        if plan.storage is not None:
            emit(
                "storage_qualification_started",
                "Single-host storage qualification started.",
                receipt=plan.storage.receipt_path,
            )
            qualified = storage_qualification.execute_direct_qualification(plan.storage)
            emit(
                "storage_qualification_admitted",
                "Single-host storage qualification admitted.",
                receipt=qualified.receipt_path,
                sha256=qualified.receipt_sha256,
            )
        runtime = plan.runtime
        if runtime is not None:
            _admit_managed_root(runtime)
            for argv, environment in _repair_actions(plan):
                manager = Path(argv[0]).name
                if manager == "pixi" and os.path.lexists(runtime.managed_root / ".pixi/config.toml"):
                    raise DoctorRepairError("Project-local Pixi configuration appeared during repair")
                emit(
                    "package_manager_started",
                    "Package-manager action started.",
                    manager=manager,
                    argv=argv,
                )
                try:
                    completed = subprocess.run(
                        argv,
                        cwd=plan.source_root,
                        env=environment,
                        stdout=sys.stderr,
                        stderr=sys.stderr,
                        check=False,
                    )
                except OSError as exc:
                    raise DoctorRepairError(f"could not start {manager}: {exc}") from exc
                emit(
                    "package_manager_completed",
                    "Package-manager action completed.",
                    manager=manager,
                    exit_status=completed.returncode,
                )
                if completed.returncode != 0:
                    raise DoctorRepairError(f"{manager} exited with status {completed.returncode}")
            _readmit_repair_plan(plan, before_storage=False)
            candidate = onboarding.discover_runtime_profile(
                project=plan.project.source_path,
                environment=_managed_discovery_environment(plan),
                root=plan.source_root,
                python_executable=Path(sys.executable),
            )
            if not candidate.required_ready:
                raise DoctorRepairError("repaired runtime did not pass qualification")
            if runtime.profile_bytes is None:
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
                    raise DoctorRepairError(f"could not read runtime inventory: {exc}") from exc
                if (
                    stat.S_ISLNK(state.st_mode)
                    or not stat.S_ISREG(state.st_mode)
                    or existing != runtime.profile_bytes
                    or existing != candidate.profile_bytes
                ):
                    raise DoctorRepairError("existing managed profile differs and was preserved")
        final = diagnose_project(
            plan.project.source_path,
            analysis_name=plan.analysis_name,
        )
        if not final.ready:
            raise DoctorRepairError("Project remained not ready after repair requalification")
        record(
            lambda: attempt.terminal(
                event_name="repair_requalified",
                message="Project repair completed and was requalified.",
                fields={
                    "ready": field(final.ready, console=True),
                    "storage_ready": field(final.storage_ready),
                    "runtime_ready": field(final.runtime_ready),
                },
            )
        )
        return final
    except KeyboardInterrupt:
        record(lambda: attempt.interrupt_best_effort(message="Project repair interrupted."))
        raise
    except (
        DoctorInputError,
        DoctorRepairError,
        RuntimeInspectionError,
        storage_qualification.StorageQualificationError,
        onboarding.OnboardingError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        error = str(exc)
        record(
            lambda: attempt.fail(
                phase="repair",
                message="Project repair failed.",
                fields={"error": field(error)},
            )
        )
        raise DoctorRepairError(str(exc)) from exc
    finally:
        with suppress(Exception):
            attempt.close()


def configure_parser(parser: argparse.ArgumentParser) -> None:
    onboarding.add_project_argument(parser)
    parser.add_argument(
        "--analysis",
        help="Named Analysis; required only when the Project defines more than one.",
    )
    add_log_arguments(parser)
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Preview supported EMRYS-owned readiness repair and confirm on a terminal.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply --repair noninteractively; invalid without --repair.",
    )
    parser.set_defaults(_command_parser=parser)


def doctor_from_args(arguments: argparse.Namespace) -> int:
    if arguments.execute and not arguments.repair:
        print("emrys: error: --execute requires --repair", file=sys.stderr)
        return 2
    try:
        result = diagnose_project(
            onboarding.project_definition_path(arguments.project),
            analysis_name=arguments.analysis,
        )
        controls = resolve_log_controls(
            source_checkout=SourceCheckout(result.source_root),
            cli_level=arguments.log_level,
            cli_root=arguments.log_root,
            default_root=result.project.source_path.parent / "logs/application",
        )
    except (DoctorInputError, LogControlError, onboarding.OnboardingError) as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return 2
    detail = controls.level
    _print_result(result, detail)
    if not arguments.repair or result.ready:
        return 0 if result.ready else 1
    try:
        plan = _build_repair_plan(result)
    except DoctorRepairError as exc:
        print(f"REPAIR BLOCKED: {exc}", file=sys.stderr)
        return 1
    _print_repair_plan(plan)
    if not arguments.execute:
        try:
            confirmed = _confirm_repair()
        except KeyboardInterrupt:
            confirmed = False
        if not confirmed:
            print("Repair preview complete; no files were written.", file=sys.stderr)
            return 1
    try:
        final = _execute_repair(plan, controls=controls)
    except KeyboardInterrupt:
        print("Repair interrupted; partial repair state was preserved.", file=sys.stderr)
        return 130
    except DoctorRepairError as exc:
        print(f"REPAIR FAILED: {exc}", file=sys.stderr)
        return 1
    _print_result(final, detail)
    return 0 if final.ready else 1


__all__ = (
    "DESCRIPTION",
    "DoctorInputError",
    "DoctorRepairError",
    "DoctorResult",
    "RuntimeBinding",
    "configure_parser",
    "diagnose_project",
    "doctor_from_args",
    "required_tool_identities",
    "runtime_file_bindings",
    "storage_runtime_binding",
)
