"""Read-only readiness doctor for the fixed local CMH pilot."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import stat
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
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
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_package_tree_identity,
)
from emrys.libraries.process_environment import (
    RENV_VERSION,
    guarded_r_environment,
)
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    SourceCheckoutIdentity,
    controlled_python_argv,
    inspect_source_checkout,
)
from emrys.orchestration.local_pilot import onboarding
from emrys.orchestration.local_pilot.normalization import (
    ProjectAdmission,
    admit_project,
)

DESCRIPTION = (
    "Check whether one Project, its owned runtime, source checkout, and final "
    "storage qualification are ready for the fixed local "
    "pilot. This command is read-only and never installs, repairs, loads "
    "modules, or creates a workspace."
)
PROFILE_RELATIVE_PATH = Path("workflow/contracts/local_cmh_v2.json")


class DoctorInputError(RuntimeError):
    """The doctor invocation contains malformed or unsafe input."""


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
    """Immutable read-only local-pilot readiness result."""

    project_path: Path
    workspace: Path
    source_root: Path
    source_commit: str | None
    inspection: RuntimeInspection
    bindings: tuple[RuntimeBinding, ...]
    blockers: tuple[str, ...]
    remediations: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.blockers


def storage_runtime_binding(
    qualified: storage_qualification.QualifiedStorage,
) -> RuntimeBinding:
    """Project one semantically admitted storage receipt into runtime identity."""

    return RuntimeBinding(
        check_id="storage_qualification",
        path=qualified.receipt_path,
        resolved_path=qualified.receipt_path.resolve(strict=True),
        sha256=qualified.receipt_sha256,
        observed=qualified.qualification_id,
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
    if len(bound) != len(bindings):
        raise DoctorInputError("Runtime file bindings must use unique check IDs")
    if "storage_qualification" not in bound:
        raise DoctorInputError("Runtime file binding is absent: storage_qualification")

    def file_identity(name: str, version: str) -> dict[str, str | None]:
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

    python_binding = file_identity("python", platform.python_version())
    if Path(str(python_binding["path"])) != python_executable:
        raise DoctorInputError("Runtime Python binding differs from this interpreter")
    snakemake_observations = [
        item
        for item in inspection.observations
        if item.check.check_id == "snakemake" and item.status == "pass"
    ]
    if len(snakemake_observations) != 1:
        raise DoctorInputError("Runtime inspection has no unique passing Snakemake probe")
    identities: list[dict[str, str | None]] = [
        python_binding,
        {
            "name": "runtime_profile",
            "version": f"sha256:{inspection.profile_sha256}",
            "path": str(
                inspection.profile_path
                if runtime_profile_path is None
                else runtime_profile_path
            ),
            "resolved_path": str(
                inspection.profile_path
                if runtime_profile_path is None
                else runtime_profile_path
            ),
            "sha256": inspection.profile_sha256,
        },
        file_identity("snakemake", snakemake_observations[0].observed),
    ]
    for observation in inspection.observations:
        check = observation.check
        if observation.status != "pass":
            continue
        if check.check_id in {"python", "snakemake"}:
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
        identities.append(file_identity(check.check_id, observation.observed))
    identities.append(
        file_identity(
            "storage_qualification",
            bound["storage_qualification"].observed,
        )
    )
    return tuple(sorted(identities, key=lambda item: item["name"]))


@dataclass(frozen=True, slots=True)
class DoctorOps:
    """Explicit fault-injection dependencies for read-only admission."""

    inspect_source: Callable[[Path, Path], SourceCheckoutIdentity]
    admit_project: Callable[
        [str | Path, Mapping[str, object] | str | Path], ProjectAdmission
    ]
    inspect_runtime: Callable[
        [bytes, Path, str, Mapping[str, str]], RuntimeInspection
    ]
    path_access: Callable[[Path, int], bool]
    inspect_storage: Callable[
        [Path, Path],
        storage_qualification.QualifiedStorage,
    ] = storage_qualification.admit_final_qualification


def _default_source_inspector(root: Path, package_root: Path) -> SourceCheckoutIdentity:
    return inspect_source_checkout(
        root=root,
        package_root=package_root,
        require_clean=True,
    )


def _default_runtime_inspector(
    profile_bytes: bytes,
    profile: Path,
    context: str,
    environment: Mapping[str, str],
) -> RuntimeInspection:
    return inspect_runtime_profile_bytes(
        profile_bytes,
        profile,
        context,
        environment=environment,
    )


DEFAULT_DOCTOR_OPS = DoctorOps(
    inspect_source=_default_source_inspector,
    admit_project=admit_project,
    inspect_runtime=_default_runtime_inspector,
    path_access=os.access,
    inspect_storage=storage_qualification.admit_final_qualification,
)


def _source_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _absolute_path(value: str | Path, *, base: Path | None = None) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (Path.cwd() if base is None else base) / path
    return Path(os.path.abspath(path))


def workspace_location_blockers(
    workspace: Path, source_root: Path
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    remediations: list[str] = []
    if (
        workspace == source_root
        or workspace in source_root.parents
        or source_root in workspace.parents
    ):
        blockers.append(f"workspace overlaps the EMRYS source checkout: {workspace}")
        remediations.append(
            "Choose a workspace outside and not containing the EMRYS source checkout."
        )
        return blockers, remediations
    if os.path.lexists(workspace):
        try:
            state = workspace.lstat()
        except OSError as exc:
            raise DoctorInputError(
                f"Could not inspect workspace {workspace}: {exc}"
            ) from exc
        if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
            raise DoctorInputError(
                f"Workspace must be an existing real directory or an absent path: {workspace}"
            )
        if workspace.resolve(strict=True) != workspace:
            raise DoctorInputError(f"Workspace must be canonical: {workspace}")
        if not os.access(workspace, os.R_OK | os.W_OK | os.X_OK):
            blockers.append(
                f"workspace is not readable, writable, and searchable: {workspace}"
            )
            remediations.append(
                f"Grant user access to the existing workspace: {workspace}"
            )
        return blockers, remediations
    parent = workspace.parent
    if not os.path.lexists(parent):
        blockers.append(f"workspace immediate parent does not exist: {parent}")
        remediations.append(
            f"Create the immediate parent as a canonical real directory first: {parent}"
        )
        return blockers, remediations
    try:
        parent_state = parent.lstat()
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise DoctorInputError(
            f"Could not inspect workspace immediate parent {parent}: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(parent_state.st_mode)
        or not stat.S_ISDIR(parent_state.st_mode)
        or resolved_parent != parent
    ):
        raise DoctorInputError(
            f"Workspace immediate parent must be a canonical real directory: {parent}"
        )
    if not os.access(parent, os.W_OK | os.X_OK):
        blockers.append(f"workspace parent is not writable and searchable: {parent}")
        remediations.append(f"Choose a writable workspace parent instead of: {parent}")
    return blockers, remediations


def _step00c_external_parent_blockers(
    project: ProjectAdmission,
    *,
    path_access: Callable[[Path, int], bool],
) -> tuple[list[str], list[str]]:
    """Check the stationary FASTA parent needed for Step 00c sidecar publication."""

    fasta = Path(str(project.construction["reference"]["fasta"]["path"]))
    parent = fasta.parent
    try:
        fasta_state = fasta.lstat()
        parent_state = parent.lstat()
        canonical_fasta = fasta.resolve(strict=True)
        canonical_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise DoctorInputError(
            f"Could not admit Step 00c stationary FASTA and parent: {fasta}: {exc}"
        ) from exc
    blockers: list[str] = []
    if (
        stat.S_ISLNK(fasta_state.st_mode)
        or not stat.S_ISREG(fasta_state.st_mode)
        or canonical_fasta != fasta
    ):
        raise DoctorInputError(
            f"Step 00c stationary FASTA must be a canonical real file: {fasta}"
        )
    elif not path_access(fasta, os.R_OK):
        blockers.append(f"Step 00c stationary FASTA is not readable: {fasta}")
    if (
        stat.S_ISLNK(parent_state.st_mode)
        or not stat.S_ISDIR(parent_state.st_mode)
        or canonical_parent != parent
    ):
        raise DoctorInputError(
            f"Step 00c stationary FASTA parent must be a canonical real directory: {parent}"
        )
    elif not path_access(parent, os.R_OK | os.W_OK | os.X_OK):
        blockers.append(
            "Step 00c stationary FASTA parent is not readable, writable, and "
            f"searchable: {parent}"
        )
    remediations = (
        []
        if not blockers
        else [
            "Use a canonical readable FASTA in a readable, writable, searchable parent."
        ]
    )
    return blockers, remediations


def validate_runtime_profile_contract(
    checks: tuple[RuntimeCheck, ...], source_root: Path
) -> None:
    """Bind every editable runtime path to the tracked fixed probe policy."""

    try:
        _policy_bytes, policy_checks = load_runtime_profile_contract(
            onboarding.runtime_policy_path()
        )
    except RuntimeInspectionError as exc:
        raise DoctorInputError(
            f"Could not load the tracked local-pilot runtime policy: {exc}"
        ) from exc
    observed_shape = tuple((check.check_id, check.check_type) for check in checks)
    policy_shape = tuple(
        (check.check_id, check.check_type) for check in policy_checks
    )
    if observed_shape != policy_shape:
        raise DoctorInputError(
            "Local-pilot runtime profile must contain the exact ordered check roster: "
            + ", ".join(check_id for check_id, _kind in policy_shape)
        )
    policy_by_name = {check.check_id: check for check in policy_checks}
    for check in checks:
        policy = policy_by_name[check.check_id]
        if (
            check.runtime_context != policy.runtime_context
            or check.required != policy.required
            or check.expected != policy.expected
            or check.description != policy.description
        ):
            raise DoctorInputError(
                "Local-pilot runtime check changes fixed probe policy: "
                f"{check.check_id}"
            )
        if check.check_type != "r_namespace" and not Path(check.target).is_absolute():
            raise DoctorInputError(
                f"Local-pilot runtime path must be absolute: {check.check_id}"
            )
        if check.check_type == "r_namespace" and check.target != policy.target:
            raise DoctorInputError(
                f"R namespace target differs from fixed policy: {check.check_id}"
            )

    rscript_target = next(
        check.target for check in checks if check.check_id == "rscript"
    )
    dynamic_probe_args = {"snakemake", "sha256_python", "picard"}
    for check in checks:
        if check.check_id.startswith("r_") and check.probe_args != (rscript_target,):
            raise DoctorInputError(
                f"R namespace check must use the declared Rscript target: {check.check_id}"
            )
        if (
            not check.check_id.startswith("r_")
            and check.check_id not in dynamic_probe_args
            and check.probe_args != policy_by_name[check.check_id].probe_args
        ):
            raise DoctorInputError(
                "Local-pilot runtime check changes fixed probe policy arguments: "
                f"{check.check_id}"
            )
    checks = {check.check_id: check for check in checks}
    expected_snakemake_args = controlled_python_argv(
        checks["python"].target,
        "-m",
        "snakemake",
        "--version",
    )[1:]
    if (
        checks["snakemake"].target != checks["python"].target
        or checks["snakemake"].probe_args != expected_snakemake_args
    ):
        raise DoctorInputError(
            "Snakemake probing must use the declared controlled Python module invocation"
        )
    if checks["sha256_python"].target != checks["python"].target or checks[
        "sha256_python"
    ].probe_args != ("python_hashlib",):
        raise DoctorInputError(
            "SHA-256 probing must use the declared controlled Python runtime"
        )
    picard_args = checks["picard"].probe_args
    expected_picard_args = (
        "-jar",
        checks["picard_jar"].target,
        "MarkDuplicates",
        "--version",
    )
    if (
        checks["picard"].target != checks["java"].target
        or picard_args != expected_picard_args
    ):
        raise DoctorInputError(
            "Picard version probing must use the declared Java and Picard jar"
        )
    renv = checks["renv_project"].target
    if Path(renv) != source_root:
        raise DoctorInputError(
            f"renv_project must be the EMRYS source checkout: expected {source_root}"
        )


def _admit_runtime_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise DoctorInputError(f"{label} must be absolute: {path}")
    try:
        state = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise DoctorInputError(f"Could not inspect {label} {path}: {exc}") from exc
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != path
    ):
        raise DoctorInputError(f"{label} must be a canonical real directory: {path}")
    if not os.access(path, os.R_OK | os.X_OK):
        raise DoctorInputError(f"{label} must be readable and searchable: {path}")
    return resolved


def _declared_renv_library(checks: tuple[RuntimeCheck, ...]) -> Path:
    matches = [check for check in checks if check.check_id == "renv_library"]
    if len(matches) != 1:
        raise DoctorInputError(
            "Runtime profile must declare exactly one renv_library check"
        )
    check = matches[0]
    if check.check_type != "path_visibility" or check.probe_args != (
        "directory_readable",
    ):
        raise DoctorInputError(
            "renv_library must be one readable-directory visibility check"
        )
    library = _admit_runtime_directory(Path(check.target), "renv_library")
    try:
        description = (library / "renv").resolve(strict=True) / "DESCRIPTION"
        text = description.read_text(encoding="utf-8")
    except OSError as exc:
        raise DoctorInputError(
            f"Selected renv_library has no readable installed renv package: {exc}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise DoctorInputError("Installed renv DESCRIPTION is not UTF-8") from exc
    versions = [
        line.removeprefix("Version:").strip()
        for line in text.splitlines()
        if line.startswith("Version:")
    ]
    if versions != [RENV_VERSION]:
        raise DoctorInputError(
            f"Selected renv_library must contain installed renv {RENV_VERSION}"
        )
    return library


def runtime_file_bindings(
    inspection: RuntimeInspection,
) -> tuple[RuntimeBinding, ...]:
    """Bind executable/jar bytes and exact installed R package trees."""

    bindings: list[RuntimeBinding] = []
    renv_libraries = [
        Path(item.check.target)
        for item in inspection.observations
        if item.check.check_id == "renv_library"
    ]
    if len(renv_libraries) != 1:
        raise DoctorInputError(
            "Runtime inspection must contain exactly one renv_library binding"
        )
    renv_library = renv_libraries[0]
    for observation in inspection.observations:
        check = observation.check
        if observation.status != "pass":
            continue
        if check.check_id in {"renv_project", "renv_library"}:
            continue
        if check.check_type not in {
            "tool_version",
            "tool_version_exit_1",
            "path_visibility",
            "r_namespace",
            "hash_utility",
        }:
            continue
        if check.check_type == "r_namespace":
            package_entry = renv_library / check.target
            try:
                path = package_entry.resolve(strict=True)
                identity = installed_package_tree_identity(path)
            except (OSError, InstalledPackageIdentityError) as exc:
                raise DoctorInputError(
                    f"Could not bind installed R package {check.check_id}: {exc}"
                ) from exc
            if observation.resolved_path is None or identity.root != observation.resolved_path:
                raise DoctorInputError(
                    f"Loaded R namespace root differs from its package binding: "
                    f"{check.check_id}"
                )
            bindings.append(
                RuntimeBinding(
                    check_id=check.check_id,
                    path=identity.root,
                    resolved_path=identity.root,
                    sha256=identity.sha256,
                    observed=observation.observed,
                )
            )
            continue
        path = Path(check.target)
        if not path.is_absolute():
            raise DoctorInputError(
                f"Local-pilot runtime target must be absolute: {check.check_id}"
            )
        try:
            resolved = path.resolve(strict=True)
            data = resolved.read_bytes()
        except OSError as exc:
            raise DoctorInputError(
                f"Could not bind runtime file {check.check_id}: {path}: {exc}"
            ) from exc
        bindings.append(
            RuntimeBinding(
                check_id=check.check_id,
                path=path,
                resolved_path=resolved,
                sha256=hashlib.sha256(data).hexdigest(),
                observed=observation.observed,
            )
        )
    return tuple(bindings)


def inspect_local_pilot(
    project_path: str | Path,
    workspace: str | Path,
    runtime_profile: str | Path,
    *,
    source_root: Path | None = None,
    ops: DoctorOps = DEFAULT_DOCTOR_OPS,
) -> DoctorResult:
    """Inspect one Project and runtime without writing anything."""

    root = _absolute_path(_source_root() if source_root is None else source_root)
    profile_path = _absolute_path(runtime_profile)
    workspace_path = _absolute_path(workspace)
    blockers, remediations = workspace_location_blockers(workspace_path, root)
    source_commit: str | None = None
    try:
        identity = ops.inspect_source(root, _package_root())
        source_commit = identity.commit
    except SourceCheckoutError as exc:
        blockers.append(f"source checkout is not ready: {exc}")
        remediations.append(
            "Use the clean reviewed EMRYS checkout and selected workflow environment."
        )
    try:
        project = ops.admit_project(project_path, root / PROFILE_RELATIVE_PATH)
    except (orchestration_contracts.ContractValidationError, OSError) as exc:
        raise DoctorInputError(str(exc)) from exc
    try:
        onboarding.validate_project_admission(project)
    except onboarding.OnboardingError as exc:
        raise DoctorInputError(str(exc)) from exc
    step00c_blockers, step00c_remediations = _step00c_external_parent_blockers(
        project,
        path_access=ops.path_access,
    )
    blockers.extend(step00c_blockers)
    remediations.extend(step00c_remediations)
    reference_fasta = Path(str(project.construction["reference"]["fasta"]["path"]))
    qualification_binding: RuntimeBinding | None = None
    try:
        qualified_storage = ops.inspect_storage(workspace_path, reference_fasta)
    except storage_qualification.StorageQualificationError as exc:
        blockers.append(f"storage is not site-qualified: {exc}")
        remediations.append(
            "Run the compute and post-allocation finalize phases of "
            "`emrys inspect storage-qualification` for workspace "
            f"{workspace_path} and reference FASTA {reference_fasta}."
        )
    else:
        qualification_binding = storage_runtime_binding(qualified_storage)
    try:
        profile_bytes, declared_checks = load_runtime_profile_contract(profile_path)
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc
    validate_runtime_profile_contract(declared_checks, root)
    renv_library = _declared_renv_library(declared_checks)
    environment = guarded_r_environment(
        root,
        renv_library,
        base_environment=os.environ,
    )
    try:
        inspection = ops.inspect_runtime(
            profile_bytes,
            profile_path,
            "local",
            environment,
        )
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc
    python_check = next(
        item for item in inspection.observations if item.check.check_id == "python"
    )
    if Path(python_check.check.target) != Path(sys.executable):
        blockers.append(
            f"runtime profile Python does not match this interpreter: {python_check.check.target}"
        )
        remediations.append(
            "Activate the workflow environment admitted by the Project runtime "
            "profile, then rerun Doctor. Do not edit the admitted profile."
        )
    for observation in inspection.observations:
        if observation.check.required and observation.status != "pass":
            blockers.append(
                f"{observation.check.check_id}: {observation.status} ({observation.observed})"
            )
            remediations.append(
                f"Restore or activate {observation.check.check_id} as admitted by the "
                "Project runtime profile, preview the environment with `emrys runtime "
                "discover`, then rerun Doctor. Adopting a different environment requires "
                "explicit runtime migration or repair; do not edit the admitted profile."
            )
    return DoctorResult(
        project_path=project.source_path,
        workspace=workspace_path,
        source_root=root,
        source_commit=source_commit,
        inspection=inspection,
        bindings=(
            runtime_file_bindings(inspection)
            if qualification_binding is None
            else (*runtime_file_bindings(inspection), qualification_binding)
        ),
        blockers=tuple(blockers),
        remediations=tuple(dict.fromkeys(remediations)),
    )


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", default=Path("project.yaml"), type=Path)
    parser.set_defaults(_command_parser=parser)


def doctor_from_args(
    arguments: argparse.Namespace,
    *,
    source_root: Path | None = None,
    ops: DoctorOps = DEFAULT_DOCTOR_OPS,
) -> int:
    try:
        result = inspect_local_pilot(
            arguments.project,
            Path(os.path.abspath(arguments.project)).parent,
            onboarding.runtime_profile_path(arguments.project),
            source_root=source_root,
            ops=ops,
        )
    except DoctorInputError as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return 2
    print(f"Project: {result.project_path}")
    print(f"Workspace: {result.workspace}")
    print(f"Source checkout: {result.source_root}")
    print(f"Source commit: {result.source_commit or 'not admitted'}")
    print(f"Runtime profile SHA-256: {result.inspection.profile_sha256}")
    storage_binding = next(
        (
            binding
            for binding in result.bindings
            if binding.check_id == "storage_qualification"
        ),
        None,
    )
    if storage_binding is not None:
        print(f"Storage qualification: {storage_binding.path}")
        print(f"Storage qualification SHA-256: {storage_binding.sha256}")
    for observation in result.inspection.observations:
        print(
            f"{observation.check.check_id}: {observation.status} "
            f"({observation.observed})"
        )
    if result.ready:
        print("READY: local-pilot prerequisites passed.")
        return 0
    print("NOT READY: local-pilot prerequisites have blockers.")
    for blocker in result.blockers:
        print(f"BLOCKER: {blocker}")
    for remediation in result.remediations:
        print(f"REMEDIATION: {remediation}")
    return 1


__all__ = (
    "DEFAULT_DOCTOR_OPS",
    "DESCRIPTION",
    "DoctorInputError",
    "DoctorOps",
    "DoctorResult",
    "RuntimeBinding",
    "configure_parser",
    "doctor_from_args",
    "inspect_local_pilot",
    "required_tool_identities",
    "runtime_file_bindings",
    "storage_runtime_binding",
)
