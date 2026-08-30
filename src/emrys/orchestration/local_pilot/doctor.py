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

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeInspectionError,
    inspect_runtime_profile_bytes,
    load_runtime_profile_contract,
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
from emrys.orchestration.local_pilot.normalization import ProjectAdmission

DESCRIPTION = (
    "Diagnose one Project across inputs, storage, runtime, and execution. "
    "Diagnosis and repair preview are read-only; an explicitly confirmed "
    "repair may restore only EMRYS-owned runtime state through uv, Pixi, and renv."
)


class DoctorInputError(RuntimeError):
    """The doctor invocation contains malformed or unsafe input."""


class DoctorRepairError(RuntimeError):
    """The managed-runtime repair cannot proceed or did not complete."""


@dataclass(frozen=True, slots=True)
class RuntimeBinding:
    """One exact path-and-content binding admitted from the runtime profile."""

    check_id: str
    path: Path
    resolved_path: Path
    sha256: str
    observed: str


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Immutable readiness result consumed by Run planning."""

    project: ProjectAdmission
    source_root: Path
    source_commit: str | None
    inspection: RuntimeInspection | None
    bindings: tuple[RuntimeBinding, ...]
    blockers: tuple[str, ...]
    remediations: tuple[str, ...]
    storage_ready: bool = True
    runtime_ready: bool = True

    @property
    def ready(self) -> bool:
        return self.source_commit is not None and self.storage_ready and self.runtime_ready and not self.blockers


def storage_runtime_binding(
    qualified: storage_qualification.QualifiedStorage,
) -> RuntimeBinding:
    """Project one semantically admitted storage receipt into runtime identity."""

    return RuntimeBinding(
        "storage_qualification", qualified.receipt_path,
        qualified.receipt_path.resolve(strict=True), qualified.receipt_sha256,
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
        return {
            "name": name,
            "version": version,
            "path": str(binding.path),
            "resolved_path": str(binding.resolved_path),
            "sha256": binding.sha256,
        }

    python_binding = identity("python", platform.python_version())
    if Path(str(python_binding["path"])) != python_executable:
        raise DoctorInputError("Runtime Python binding differs from this interpreter")
    profile = inspection.profile_path if runtime_profile_path is None else runtime_profile_path
    identities: list[dict[str, str | None]] = [{
            "name": "runtime_profile",
            "version": f"sha256:{inspection.profile_sha256}",
            "path": str(profile),
            "resolved_path": str(profile),
            "sha256": inspection.profile_sha256,
        }, python_binding]
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


def workspace_location_blockers(
    workspace: Path, source_root: Path
) -> tuple[list[str], list[str]]:
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
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != workspace
    ):
        raise DoctorInputError(f"Project root must be a canonical real directory: {workspace}")
    if not os.access(workspace, os.R_OK | os.W_OK | os.X_OK):
        return [f"Project root is not readable, writable, and searchable: {workspace}"], [
            f"Grant user access to the Project root: {workspace}"
        ]
    return [], []


def validate_runtime_profile_contract(
    checks: tuple[RuntimeCheck, ...], source_root: Path
) -> None:
    """Bind every editable runtime path to the tracked fixed probe policy."""

    try:
        _bytes, policy = load_runtime_profile_contract(
            onboarding.runtime_policy_path()
        )
    except RuntimeInspectionError as exc:
        raise DoctorInputError(f"Could not load fixed runtime policy: {exc}") from exc
    shape = lambda values: tuple(  # noqa: E731 - compact immutable projection
        (item.check_id, item.check_type) for item in values
    )
    if shape(checks) != shape(policy):
        raise DoctorInputError(
            "Runtime profile must contain the exact ordered fixed-policy roster"
        )
    selected = {item.check_id: item for item in checks}
    fixed = {item.check_id: item for item in policy}
    rscript = selected["rscript"].target
    for check in checks:
        expected = fixed[check.check_id]
        dynamic = check.check_id in {"snakemake", "sha256_python", "picard"}
        wanted_args = (rscript,) if check.check_type == "r_namespace" else expected.probe_args
        fixed_fields = (check.runtime_context, check.required, check.expected, check.description)
        expected_fields = (expected.runtime_context, expected.required, expected.expected, expected.description)
        target_valid = (
            check.target == expected.target
            if check.check_type == "r_namespace"
            else Path(check.target).is_absolute()
        )
        if fixed_fields != expected_fields or not target_valid or (
            not dynamic and check.probe_args != wanted_args
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
        and selected["snakemake"].probe_args
        == controlled_python_argv(python, "-m", "snakemake", "--version")[1:]
        and selected["sha256_python"].target == python
        and selected["sha256_python"].probe_args == ("python_hashlib",)
        and selected["picard"].target == selected["java"].target
        and selected["picard"].probe_args
        == ("-jar", selected["picard_jar"].target, "MarkDuplicates", "--version")
        and Path(selected["renv_project"].target) == source_root
    )
    if not relations:
        raise DoctorInputError("Runtime profile changes a fixed cross-check binding")


def runtime_file_bindings(
    inspection: RuntimeInspection,
) -> tuple[RuntimeBinding, ...]:
    """Bind executable/jar bytes and exact installed R package trees."""

    bindings: list[RuntimeBinding] = []
    renv_library = next(
        Path(item.check.target)
        for item in inspection.observations
        if item.check.check_id == "renv_library"
    )
    for observation in inspection.observations:
        check = observation.check
        if observation.status != "pass" or check.check_id in {"renv_project", "renv_library"}:
            continue
        if check.check_type == "r_namespace":
            try:
                identity = installed_package_tree_identity(
                    (renv_library / check.target).resolve(strict=True)
                )
            except (OSError, InstalledPackageIdentityError) as exc:
                raise DoctorInputError(f"Could not bind R package {check.check_id}: {exc}") from exc
            if observation.resolved_path is None or identity.root != observation.resolved_path:
                raise DoctorInputError(f"Loaded R namespace root changed: {check.check_id}")
            bindings.append(RuntimeBinding(check.check_id, identity.root, identity.root, identity.sha256, observation.observed))
            continue
        path = Path(check.target)
        try:
            resolved = path.resolve(strict=True)
            data = resolved.read_bytes()
        except OSError as exc:
            raise DoctorInputError(f"Could not bind runtime file {check.check_id}: {exc}") from exc
        bindings.append(RuntimeBinding(check.check_id, path, resolved, hashlib.sha256(data).hexdigest(), observation.observed))
    return tuple(bindings)


def _inspect_foundations(
    project_path: str | Path,
    workspace: str | Path,
) -> DoctorResult:
    root = _absolute_path(onboarding.source_root())
    workspace_path = _absolute_path(workspace)
    blockers, remediations = workspace_location_blockers(workspace_path, root)
    try:
        source_commit = inspect_source_checkout(
            root=root, package_root=_PACKAGE_ROOT, require_clean=True
        ).commit
    except SourceCheckoutError as exc:
        source_commit = None
        blockers.append(f"source checkout is not ready: {exc}")
        remediations.append("Use the clean reviewed EMRYS checkout and workflow environment.")
    try:
        project = onboarding.validate_project(project_path, root=root).project
    except (
        onboarding.OnboardingError,
        orchestration_contracts.ContractValidationError,
        OSError,
    ) as exc:
        raise DoctorInputError(str(exc)) from exc
    fasta = Path(str(project.construction["reference"]["fasta"]["path"]))
    try:
        bindings = (storage_runtime_binding(
            storage_qualification.admit_final_qualification(workspace_path, fasta)
        ),)
    except storage_qualification.StorageQualificationError as exc:
        bindings = ()
        blockers.append(f"storage is not site-qualified: {exc}")
        remediations.append(
            "Run `emrys inspect storage-qualification` for Project "
            f"{workspace_path} and reference FASTA {fasta}."
        )
    return DoctorResult(
        project=project,
        source_root=root,
        source_commit=source_commit,
        inspection=None,
        bindings=bindings,
        blockers=tuple(blockers),
        remediations=tuple(remediations),
        storage_ready=bool(bindings),
        runtime_ready=False,
    )


def inspect_local_pilot(
    project_path: str | Path,
    workspace: str | Path,
    runtime_profile: str | Path,
) -> DoctorResult:
    """Inspect one Project and runtime without writing anything."""

    foundations = _inspect_foundations(project_path, workspace)
    profile_path = _absolute_path(runtime_profile)
    try:
        profile_bytes, declared_checks = load_runtime_profile_contract(profile_path)
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc
    validate_runtime_profile_contract(declared_checks, foundations.source_root)
    renv_library = next(
        Path(check.target) for check in declared_checks if check.check_id == "renv_library"
    )
    environment = guarded_r_environment(
        foundations.source_root, renv_library
    )
    try:
        inspection = inspect_runtime_profile_bytes(
            profile_bytes, profile_path, "local", environment=environment
        )
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc
    blockers = list(foundations.blockers)
    remediations = list(foundations.remediations)
    python = next(item for item in inspection.observations if item.check.check_id == "python")
    python_ready = Path(python.check.target) == Path(sys.executable)
    if not python_ready:
        blockers.append(f"runtime Python differs from this interpreter: {python.check.target}")
        remediations.append(
            "Activate the Python environment admitted by the Project runtime, then rerun Doctor."
        )
    failed = [item for item in inspection.observations if item.check.required and item.status != "pass"]
    blockers.extend(
        f"{item.check.check_id}: {item.status} ({item.observed})" for item in failed
    )
    if failed:
        remediations.append(
            "Run `emrys doctor --repair` for an EMRYS-managed runtime, or repair and "
            "re-admit the selected site environment without editing runtime.tsv."
        )
    bindings = (*runtime_file_bindings(inspection), *foundations.bindings)
    return DoctorResult(
        project=foundations.project,
        source_root=foundations.source_root,
        source_commit=foundations.source_commit,
        inspection=inspection,
        bindings=bindings,
        blockers=tuple(blockers),
        remediations=tuple(dict.fromkeys(remediations)),
        storage_ready=foundations.storage_ready,
        runtime_ready=python_ready and not failed,
    )


def diagnose_project(project_path: str | Path) -> DoctorResult:
    """Diagnose the canonical Project runtime, including an absent profile."""

    project = _absolute_path(project_path)
    profile = onboarding.runtime_profile_path(project)
    if os.path.lexists(profile):
        return inspect_local_pilot(project, project.parent, profile)
    foundations = _inspect_foundations(project, project.parent)
    remediation = (
        "Run `emrys doctor --repair`, or admit a complete site runtime with "
        "`emrys runtime discover --execute`."
    )
    return replace(
        foundations,
        blockers=(*foundations.blockers, f"runtime profile is not admitted: {profile}"),
        remediations=tuple(dict.fromkeys((*foundations.remediations, remediation))),
    )


@dataclass(frozen=True, slots=True)
class _RepairPlan:
    project: ProjectAdmission
    source_root: Path
    source_commit: str
    managed_root: Path
    native: Path
    r: Path
    renv: Path
    profile: Path
    uv: Path
    pixi: Path
    uv_sha256: str
    pixi_sha256: str
    profile_bytes: bytes | None
    manifest_bytes: bytes
    lock_bytes: bytes

def _profile_is_managed(checks: tuple[RuntimeCheck, ...], plan: _RepairPlan) -> bool:
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
    machine = platform.machine().casefold()
    if platform.system() != "Linux" or machine not in {"amd64", "x86_64"}:
        raise DoctorRepairError(
            "managed repair currently supports x86-64 Linux; use site runtime "
            "discovery on this platform"
        )
    venv = result.source_root / ".venv"
    if _absolute_path(sys.prefix) != venv:
        raise DoctorRepairError(
            "Python repair is restricted to the active checkout-owned .venv; "
            f"found {sys.prefix}"
        )
    try:
        state = venv.lstat()
        owned_venv = stat.S_ISDIR(state.st_mode) and not stat.S_ISLNK(state.st_mode)
        owned_venv = owned_venv and venv.resolve(strict=True) == venv
    except OSError as exc:
        raise DoctorRepairError(f"checkout-owned .venv is unavailable: {exc}") from exc
    if not owned_venv or not os.access(venv, os.R_OK | os.W_OK | os.X_OK):
        raise DoctorRepairError(f"checkout-owned .venv is not canonical and writable: {venv}")
    try:
        project = result.project
        runtime = onboarding.project_runtime_directory(project)
        resources = _PACKAGE_ROOT / "resources/runtime"
        manifest_bytes = (resources / "pixi.toml").read_bytes()
        lock_bytes = (resources / "pixi.lock").read_bytes()
    except (OSError, onboarding.OnboardingError) as exc:
        raise DoctorRepairError(str(exc)) from exc
    managed = runtime / "managed"
    uv, pixi = _manager("uv"), _manager("pixi")
    plan = _RepairPlan(
        project=project,
        source_root=result.source_root,
        source_commit=result.source_commit,
        managed_root=managed,
        native=managed / ".pixi/envs/native",
        r=managed / ".pixi/envs/r",
        renv=managed / "renv/library",
        profile=runtime / "runtime.tsv",
        uv=uv,
        pixi=pixi,
        uv_sha256=_file_sha256(uv),
        pixi_sha256=_file_sha256(pixi),
        profile_bytes=None if result.inspection is None else result.inspection.profile_bytes,
        manifest_bytes=manifest_bytes,
        lock_bytes=lock_bytes,
    )
    if result.inspection is not None:
        checks = tuple(item.check for item in result.inspection.observations)
        if not _profile_is_managed(checks, plan):
            raise DoctorRepairError(
                "the admitted runtime profile is site- or user-owned and was "
                "preserved; repair that environment or explicitly admit a replacement"
            )
    return plan


def _readmit_repair_plan(plan: _RepairPlan) -> None:
    try:
        source = inspect_source_checkout(
            root=plan.source_root, package_root=_PACKAGE_ROOT, require_clean=True
        )
        project = onboarding.validate_project(
            plan.project.source_path, root=plan.source_root
        ).project
    except (OSError, RuntimeError) as exc:
        raise DoctorRepairError(f"repair plan changed before execution: {exc}") from exc
    if source.commit != plan.source_commit or project != plan.project:
        raise DoctorRepairError("repair plan changed before execution")
    if _file_sha256(plan.uv) != plan.uv_sha256 or _file_sha256(plan.pixi) != plan.pixi_sha256:
        raise DoctorRepairError("admitted package manager changed before execution")
    if plan.profile_bytes is None:
        if os.path.lexists(plan.profile):
            raise DoctorRepairError("runtime profile appeared after repair confirmation")
        return
    try:
        state = plan.profile.lstat()
        data = plan.profile.read_bytes()
    except OSError as exc:
        raise DoctorRepairError(f"runtime profile changed before execution: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode) or data != plan.profile_bytes:
        raise DoctorRepairError("runtime profile changed before execution")


def _admit_managed_root(plan: _RepairPlan) -> None:
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
                directory.is_symlink()
                or not directory.is_dir()
                or root not in directory.resolve(strict=True).parents
            ):
                raise DoctorRepairError(f"managed Pixi state is not owned: {directory}")
        for name, data in (("pixi.toml", plan.manifest_bytes), ("pixi.lock", plan.lock_bytes)):
            destination = root / name
            if os.path.lexists(destination):
                state = destination.lstat()
                observed = destination.read_bytes()
                if not stat.S_ISREG(state.st_mode) or observed != data:
                    raise DoctorRepairError(f"managed {name} differs from packaged bytes")
            else:
                publish_exclusive(destination, data, DoctorRepairError)
        for relative in ("cache", "cache/uv", "cache/pixi", "renv", "renv/cache", "renv/library"):
            directory = root / relative
            directory.mkdir(mode=0o700, exist_ok=True)
            if directory.is_symlink() or not directory.is_dir():
                raise DoctorRepairError(f"managed directory is not owned state: {directory}")
    except OSError as exc:
        raise DoctorRepairError(f"managed runtime is unavailable: {root}: {exc}") from exc


def _repair_actions(plan: _RepairPlan) -> tuple[tuple[tuple[str, ...], dict[str, str]], ...]:
    base = sanitized_subprocess_environment()
    uv = dict(base)
    uv.update(
        {
            "UV_CACHE_DIR": str(plan.managed_root / "cache/uv"),
            "UV_PROJECT_ENVIRONMENT": sys.prefix,
        }
    )
    pixi = dict(base)
    for name in tuple(pixi):
        if name.startswith("PIXI_"):
            del pixi[name]
    pixi.update({
        "PIXI_CACHE_DIR": str(plan.managed_root / "cache/pixi"),
        "PIXI_DISABLE_NETFS_REDIRECT": "1",
        "PIXI_NO_CONFIG": "1",
    })
    restore = dict(pixi)
    for name in tuple(restore):
        if name.startswith(("R_LIBS", "R_PROFILE", "R_ENVIRON", "RENV_")) or name == "R_DEFAULT_PACKAGES":
            del restore[name]
    restore.update(
        {
            "EMRYS_USE_RENV": "1",
            "EMRYS_LOCAL_PILOT_R": "0",
            "RENV_PROJECT": str(plan.source_root),
            "RENV_PATHS_LIBRARY": str(plan.renv),
            "RENV_PATHS_CACHE": str(plan.managed_root / "renv/cache"),
            "RENV_CONFIG_SANDBOX_ENABLED": "FALSE",
            "RENV_CONFIG_AUTO_SNAPSHOT": "FALSE",
            "R_PROFILE_USER": str(plan.source_root / ".Rprofile"),
        }
    )
    manifest = str(plan.managed_root / "pixi.toml")
    restore_argv = guarded_rscript_argv(
        str(plan.r / "bin/Rscript"),
        (str(plan.source_root / "scripts/restore_r_environment.R"),),
    )
    return (
        ((str(plan.uv), "sync", "--locked", "--no-default-groups", "--group", "workflow", "--python", sys.executable, "--project", str(plan.source_root)), uv),
        ((str(plan.pixi), "install", "--manifest-path", manifest, "--locked", "--all"), pixi),
        (
            (
                str(plan.pixi), "run", "--manifest-path", manifest,
                "--environment", "r", "--locked", "--executable", *restore_argv,
            ),
            restore,
        ),
    )


def _managed_discovery_environment(plan: _RepairPlan) -> dict[str, str]:
    jars = tuple(
        path for path in (plan.native / "share").glob(
            "picard-slim-3.1.1-*/picard.jar"
        ) if path.is_file() and not path.is_symlink()
    )
    if len(jars) != 1:
        raise DoctorRepairError("locked runtime must contain one Picard 3.1.1 jar")
    libraries = tuple(
        description.parents[1]
        for description in plan.renv.rglob("renv/DESCRIPTION")
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
            "PATH": str(plan.native / "bin"),
            "EMRYS_RSCRIPT": str(plan.r / "bin/Rscript"),
            "EMRYS_PICARD_JAR": str(jars[0]),
            "EMRYS_RENV_LIBRARY": str(library),
        }
    )
    return environment


def _print_result(result: DoctorResult, detail: LogLevel) -> None:
    print("EMRYS Doctor")
    print(f"  Project    PASS  {result.project.source_path.parent}")
    print("  Inputs     PASS")
    for label, ready in (("Storage", result.storage_ready), ("Runtime", result.runtime_ready), ("Execution", result.ready)):
        print(f"  {label:<10} {'PASS' if ready else 'FAIL'}")
    if detail in {LogLevel.VERBOSE, LogLevel.DEBUG}:
        print(f"Source checkout: {result.source_root}")
        print(f"Source commit: {result.source_commit or 'not admitted'}")
        if result.inspection is not None:
            print(f"Runtime profile: {result.inspection.profile_path}")
            print(f"Runtime profile SHA-256: {result.inspection.profile_sha256}")
            for observation in result.inspection.observations:
                print(
                    f"  {observation.check.check_id}: {observation.status} "
                    f"({observation.observed})"
                )
    if detail is LogLevel.DEBUG:
        for binding in result.bindings:
            print(
                f"Binding {binding.check_id}: {binding.path} -> "
                f"{binding.resolved_path} sha256:{binding.sha256}"
            )
    print("EMRYS is ready." if result.ready else "EMRYS is not ready.")
    for blocker in result.blockers:
        print(f"BLOCKER: {blocker}")
    for remediation in result.remediations:
        print(f"REMEDIATION: {remediation}")


def _print_repair_plan(plan: _RepairPlan) -> None:
    print("EMRYS Doctor repair plan")
    print(f"  Project: {plan.project.source_path}")
    print(f"  Managed runtime: {plan.managed_root}")
    print(f"  uv: {plan.uv}")
    print(f"  Pixi: {plan.pixi}")
    print("  Actions: uv sync; Pixi native/R install; renv restore; runtime qualification")
    print("Declared inputs and site/user environments will not be modified.")


def _confirm_repair() -> bool:
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        return False
    print("Apply this repair? [y/N] ", end="", file=sys.stderr, flush=True)
    return sys.stdin.readline().strip().casefold() in {"y", "yes"}


def _execute_repair(plan: _RepairPlan, *, controls: LogControls) -> DoctorResult:
    try:
        attempt = open_attempt_log(
            controls=controls,
            identity=AttemptIdentity("maintenance", plan.project.source_sha256[:16], f"repair-{uuid.uuid4().hex}", "emrys-doctor"),
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
                print("WARNING: repair logging degraded; requalification remains controlling.", file=sys.stderr)

    def emit(name: str, message: str, **values: object) -> None:
        record(lambda: logger.info(message, extra=event(name, fields={key: field(value) for key, value in values.items()})))

    emit(
        "repair_started", "Managed runtime repair started.",
        project=plan.project.source_path, managed_root=plan.managed_root,
        uv=plan.uv, pixi=plan.pixi,
        uv_sha256=plan.uv_sha256, pixi_sha256=plan.pixi_sha256,
        pixi_manifest_sha256=hashlib.sha256(plan.manifest_bytes).hexdigest(),
        pixi_lock_sha256=hashlib.sha256(plan.lock_bytes).hexdigest(),
    )
    try:
        _readmit_repair_plan(plan)
        _admit_managed_root(plan)
        for argv, environment in _repair_actions(plan):
            manager = Path(argv[0]).name
            if manager == "pixi" and os.path.lexists(plan.managed_root / ".pixi/config.toml"):
                raise DoctorRepairError("Project-local Pixi configuration appeared during repair")
            emit("package_manager_started", "Package-manager action started.", manager=manager, argv=argv)
            try:
                completed = subprocess.run(
                    argv, cwd=plan.source_root, env=environment,
                    stdout=sys.stderr, stderr=sys.stderr, check=False,
                )
            except OSError as exc:
                raise DoctorRepairError(f"could not start {manager}: {exc}") from exc
            emit("package_manager_completed", "Package-manager action completed.", manager=manager, exit_status=completed.returncode)
            if completed.returncode != 0:
                raise DoctorRepairError(f"{manager} exited with status {completed.returncode}")
        _readmit_repair_plan(plan)
        candidate = onboarding.discover_runtime_profile(
            project=plan.project.source_path,
            environment=_managed_discovery_environment(plan),
            root=plan.source_root,
            python_executable=Path(sys.executable),
        )
        if not candidate.required_ready:
            raise DoctorRepairError("repaired runtime did not pass qualification")
        published = plan.profile_bytes is None
        if published:
            onboarding.publish_runtime_profile(candidate)
            emit("runtime_profile_admitted", "Managed runtime profile admitted.", profile=plan.profile, sha256=candidate.profile_sha256)
        else:
            try:
                state = plan.profile.lstat()
                existing = plan.profile.read_bytes()
            except OSError as exc:
                raise DoctorRepairError(f"could not read runtime profile: {exc}") from exc
            if (
                stat.S_ISLNK(state.st_mode)
                or not stat.S_ISREG(state.st_mode)
                or existing != plan.profile_bytes
                or existing != candidate.profile_bytes
            ):
                raise DoctorRepairError("existing managed profile differs and was preserved")
        final = diagnose_project(plan.project.source_path)
        record(
            lambda: attempt.terminal(
                event_name="repair_requalified",
                message="Managed runtime repair completed and Project was requalified.",
                fields={"ready": field(final.ready, console=True), "runtime_ready": field(final.runtime_ready)},
            )
        )
        return final
    except KeyboardInterrupt:
        record(lambda: attempt.interrupt_best_effort(message="Managed runtime repair interrupted."))
        raise
    except (
        DoctorInputError,
        DoctorRepairError,
        RuntimeInspectionError,
        onboarding.OnboardingError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        error = str(exc)
        record(lambda: attempt.fail(phase="repair", message="Managed runtime repair failed.", fields={"error": field(error)}))
        raise DoctorRepairError(str(exc)) from exc
    finally:
        with suppress(Exception):
            attempt.close()


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", default=Path("project.yaml"), type=Path)
    add_log_arguments(parser)
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Preview a supported EMRYS-owned runtime repair and confirm on a terminal.",
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
        result = diagnose_project(arguments.project)
        controls = resolve_log_controls(
            source_checkout=SourceCheckout(result.source_root),
            cli_level=arguments.log_level,
            cli_root=arguments.log_root,
            default_root=result.project.source_path.parent / "logs/application",
        )
    except (DoctorInputError, LogControlError) as exc:
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
        print("Repair interrupted; partial managed state was preserved.", file=sys.stderr)
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
    "inspect_local_pilot",
    "required_tool_identities",
    "runtime_file_bindings",
    "storage_runtime_binding",
)
