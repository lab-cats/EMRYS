"""Read-only readiness doctor for the fixed local CMH pilot."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeInspectionError,
    inspect_runtime_availability,
    load_runtime_profile_contract,
)
from emrys.evidence.storage_inventory import qualification as storage_qualification
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_package_tree_identity,
)
from emrys.libraries.process_environment import (
    ProcessEnvironmentError,
    RENV_VERSION,
    gatk_subprocess_environment,
    guarded_r_environment,
    sanitized_subprocess_environment,
)
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    SourceCheckoutIdentity,
    controlled_python_argv,
    inspect_source_checkout,
)
from emrys.orchestration.local_pilot import onboarding
from emrys.orchestration.local_pilot.normalization import (
    NormalizationBundle,
    normalize_request,
)

DESCRIPTION = (
    "Check whether one explicit request, workspace, source checkout, runtime "
    "profile, and final storage qualification are ready for the fixed local "
    "pilot. This command is read-only and never installs, repairs, loads "
    "modules, or creates a workspace."
)
SNAKEMAKE_VERSION = "9.25.1"
PROFILE_RELATIVE_PATH = Path("workflow/contracts/local_cmh_v2.json")

LOCAL_PILOT_R_PACKAGES = (
    ("r_variant_annotation", "VariantAnnotation"),
    ("r_genomic_ranges", "GenomicRanges"),
    ("r_iranges", "IRanges"),
    ("r_biostrings", "Biostrings"),
    ("r_rsamtools", "Rsamtools"),
    ("r_s4vectors", "S4Vectors"),
    ("r_summarized_experiment", "SummarizedExperiment"),
    ("r_genome_info_db", "GenomeInfoDb"),
    ("r_bioc_generics", "BiocGenerics"),
    ("r_rtracklayer", "rtracklayer"),
)
LOCAL_PILOT_RUNTIME_CHECKS = (
    ("bash", "tool_version"),
    ("python", "tool_version"),
    ("snakemake", "tool_version"),
    ("sha256_python", "hash_utility"),
    ("star", "tool_version"),
    ("samtools", "tool_version"),
    ("java", "tool_version"),
    ("gatk", "tool_version"),
    ("picard", "tool_version_exit_1"),
    ("picard_jar", "path_visibility"),
    ("bcftools", "tool_version"),
    ("infer_experiment", "tool_version"),
    ("gunzip", "tool_version"),
    ("rscript", "tool_version"),
    ("renv_project", "path_visibility"),
    ("renv_library", "path_visibility"),
    *((check_id, "r_namespace") for check_id, _package in LOCAL_PILOT_R_PACKAGES),
)


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

    request_path: Path
    workspace: Path
    source_root: Path
    source_commit: str | None
    runtime_profile: Path
    runtime_profile_sha256: str
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


def runtime_environment(
    source_root: Path,
    renv_library: Path,
    *,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return the sanitized guarded R environment used by every runtime probe."""

    return guarded_r_environment(
        source_root,
        renv_library,
        base_environment=base_environment,
    )


def required_tool_identities(
    inspection: RuntimeInspection,
    *,
    bindings: tuple[RuntimeBinding, ...],
    python_executable: Path,
    snakemake_version: str = SNAKEMAKE_VERSION,
    runtime_profile_path: Path | None = None,
) -> tuple[dict[str, str | None], ...]:
    """Project exact attempt tool identities from one admitted runtime probe."""

    bound = {item.check_id: item for item in bindings}
    if len(bound) != len(bindings):
        raise DoctorInputError("Runtime file bindings must use unique check IDs")
    if "storage_qualification" not in bound:
        raise DoctorInputError(
            "Runtime file binding is absent: storage_qualification"
        )

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
        file_identity("snakemake", snakemake_version),
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
    normalize: Callable[
        [str | Path, Mapping[str, object] | str | Path], NormalizationBundle
    ]
    inspect_runtime: Callable[[Path, str, Mapping[str, str]], RuntimeInspection]
    observe_snakemake: Callable[[Path], str]
    load_runtime_profile: Callable[[Path], tuple[bytes, tuple[RuntimeCheck, ...]]]
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
    profile: Path,
    context: str,
    environment: Mapping[str, str],
) -> RuntimeInspection:
    return inspect_runtime_availability(profile, context, environment=environment)


def _default_snakemake_observer(python_executable: Path) -> str:
    try:
        completed = subprocess.run(
            controlled_python_argv(
                python_executable,
                "-m",
                "snakemake",
                "--version",
            ),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=sanitized_subprocess_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DoctorInputError(f"Could not inspect Snakemake: {exc}") from exc
    observed = " ".join((completed.stdout + " " + completed.stderr).split())
    if completed.returncode != 0:
        raise DoctorInputError(
            f"Could not inspect Snakemake through {python_executable}: "
            f"{observed or f'exit {completed.returncode}'}"
        )
    return observed


def _default_profile_loader(profile: Path) -> tuple[bytes, tuple[RuntimeCheck, ...]]:
    try:
        return load_runtime_profile_contract(profile)
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc


DEFAULT_DOCTOR_OPS = DoctorOps(
    inspect_source=_default_source_inspector,
    normalize=normalize_request,
    inspect_runtime=_default_runtime_inspector,
    observe_snakemake=_default_snakemake_observer,
    load_runtime_profile=_default_profile_loader,
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
    normalized: NormalizationBundle,
    *,
    path_access: Callable[[Path, int], bool],
) -> tuple[list[str], list[str]]:
    """Check the stationary FASTA parent needed for Step 00c sidecar publication."""

    fasta = Path(str(normalized.projection_source["reference"]["fasta"]["path"]))
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

    observed_shape = tuple((check.check_id, check.check_type) for check in checks)
    if observed_shape != LOCAL_PILOT_RUNTIME_CHECKS:
        expected = ", ".join(check_id for check_id, _kind in LOCAL_PILOT_RUNTIME_CHECKS)
        raise DoctorInputError(
            "Local-pilot runtime profile must contain the exact ordered check roster: "
            + expected
        )
    try:
        _policy_bytes, policy_checks = load_runtime_profile_contract(
            source_root / "configs/local_pilot_runtime.example.tsv"
        )
    except RuntimeInspectionError as exc:
        raise DoctorInputError(
            f"Could not load the tracked local-pilot runtime policy: {exc}"
        ) from exc
    if tuple((check.check_id, check.check_type) for check in policy_checks) != (
        LOCAL_PILOT_RUNTIME_CHECKS
    ):
        raise DoctorInputError(
            "Tracked local-pilot runtime policy differs from the fixed roster"
        )
    policy_by_name = {check.check_id: check for check in policy_checks}
    for check in checks:
        policy = policy_by_name[check.check_id]
        if (
            check.check_type != policy.check_type
            or check.runtime_context != policy.runtime_context
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
        if not check.required or check.runtime_context not in {"local", "any"}:
            raise DoctorInputError(
                f"Local-pilot runtime check must be required in local/any context: {check.check_id}"
            )
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


def validate_runtime_profile(inspection: RuntimeInspection, source_root: Path) -> None:
    """Re-admit observed checks against the tracked fixed runtime policy."""

    validate_runtime_profile_contract(
        tuple(observation.check for observation in inspection.observations),
        source_root,
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
    package_entry = library / "renv"
    try:
        entry_before = package_entry.lstat()
        package_root = package_entry.resolve(strict=True)
        package_state = package_root.lstat()
    except OSError as exc:
        raise DoctorInputError(
            f"Selected renv_library has no readable installed renv package: {exc}"
        ) from exc
    if not (
        stat.S_ISDIR(entry_before.st_mode) or stat.S_ISLNK(entry_before.st_mode)
    ):
        raise DoctorInputError(
            f"Installed renv package entry must be a directory or symlink: "
            f"{package_entry}"
        )
    if stat.S_ISLNK(package_state.st_mode) or not stat.S_ISDIR(package_state.st_mode):
        raise DoctorInputError(
            f"Installed renv package must resolve to a canonical real directory: "
            f"{package_entry}"
        )
    description = package_root / "DESCRIPTION"
    try:
        state = description.lstat()
        data = description.read_bytes()
        after = description.lstat()
        entry_after = package_entry.lstat()
        resolved_after = package_entry.resolve(strict=True)
        package_after = package_root.lstat()
    except OSError as exc:
        raise DoctorInputError(
            f"Selected renv_library has no readable installed renv package: {exc}"
        ) from exc
    if not stat.S_ISREG(state.st_mode) or stat.S_ISLNK(state.st_mode):
        raise DoctorInputError(
            f"Installed renv DESCRIPTION must be a regular non-symlink file: {description}"
        )
    if (
        (
            entry_before.st_dev,
            entry_before.st_ino,
            entry_before.st_mode,
            entry_before.st_size,
            entry_before.st_mtime_ns,
            entry_before.st_ctime_ns,
        )
        != (
            entry_after.st_dev,
            entry_after.st_ino,
            entry_after.st_mode,
            entry_after.st_size,
            entry_after.st_mtime_ns,
            entry_after.st_ctime_ns,
        )
        or resolved_after != package_root
    ):
        raise DoctorInputError("Installed renv package entry changed during admission")
    if (
        package_state.st_dev,
        package_state.st_ino,
        package_state.st_mode,
        package_state.st_size,
        package_state.st_mtime_ns,
        package_state.st_ctime_ns,
    ) != (
        package_after.st_dev,
        package_after.st_ino,
        package_after.st_mode,
        package_after.st_size,
        package_after.st_mtime_ns,
        package_after.st_ctime_ns,
    ):
        raise DoctorInputError("Installed renv package root changed during admission")
    if (
        state.st_dev,
        state.st_ino,
        state.st_size,
        state.st_mtime_ns,
        state.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise DoctorInputError("Installed renv DESCRIPTION changed during admission")
    try:
        text = data.decode("utf-8")
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
                entry_before = package_entry.lstat()
                path = package_entry.resolve(strict=True)
                target_before = path.lstat()
            except OSError as exc:
                raise DoctorInputError(
                    f"Could not resolve installed R package {check.check_id}: "
                    f"{package_entry}: {exc}"
                ) from exc
            if not (
                stat.S_ISDIR(entry_before.st_mode)
                or stat.S_ISLNK(entry_before.st_mode)
            ):
                raise DoctorInputError(
                    f"Installed R package entry must be a directory or symlink: "
                    f"{check.check_id}: {package_entry}"
                )
            if (
                stat.S_ISLNK(target_before.st_mode)
                or not stat.S_ISDIR(target_before.st_mode)
            ):
                raise DoctorInputError(
                    f"Installed R package must resolve to a canonical real directory: "
                    f"{check.check_id}: {package_entry}"
                )
            if observation.resolved_path is None:
                raise DoctorInputError(
                    f"Passing R namespace observation did not bind its loaded root: "
                    f"{check.check_id}"
                )
            if path != observation.resolved_path:
                raise DoctorInputError(
                    f"Loaded R namespace root changed before package binding: "
                    f"{check.check_id}: observed {observation.resolved_path}; "
                    f"bound {path}"
                )
            try:
                identity = installed_package_tree_identity(path)
            except InstalledPackageIdentityError as exc:
                raise DoctorInputError(
                    f"Could not bind installed R package {check.check_id}: {exc}"
                ) from exc
            if identity.root != observation.resolved_path:
                raise DoctorInputError(
                    f"Loaded R namespace root changed before package binding: "
                    f"{check.check_id}: observed {observation.resolved_path}; "
                    f"bound {identity.root}"
                )
            try:
                entry_after = package_entry.lstat()
                resolved_after = package_entry.resolve(strict=True)
                target_after = path.lstat()
            except OSError as exc:
                raise DoctorInputError(
                    f"Could not re-admit installed R package {check.check_id}: "
                    f"{package_entry}: {exc}"
                ) from exc
            if (
                (
                    entry_before.st_dev,
                    entry_before.st_ino,
                    entry_before.st_mode,
                    entry_before.st_size,
                    entry_before.st_mtime_ns,
                    entry_before.st_ctime_ns,
                )
                != (
                    entry_after.st_dev,
                    entry_after.st_ino,
                    entry_after.st_mode,
                    entry_after.st_size,
                    entry_after.st_mtime_ns,
                    entry_after.st_ctime_ns,
                )
                or resolved_after != path
                or (
                    target_before.st_dev,
                    target_before.st_ino,
                    target_before.st_mode,
                    target_before.st_size,
                    target_before.st_mtime_ns,
                    target_before.st_ctime_ns,
                )
                != (
                    target_after.st_dev,
                    target_after.st_ino,
                    target_after.st_mode,
                    target_after.st_size,
                    target_after.st_mtime_ns,
                    target_after.st_ctime_ns,
                )
            ):
                raise DoctorInputError(
                    f"Installed R package entry changed during admission: "
                    f"{check.check_id}: {package_entry}"
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
            before = resolved.stat()
            data = resolved.read_bytes()
        except OSError as exc:
            raise DoctorInputError(
                f"Could not bind runtime file {check.check_id}: {path}: {exc}"
            ) from exc
        try:
            after = resolved.stat()
        except OSError as exc:
            raise DoctorInputError(
                f"Could not recheck runtime file {check.check_id}: {resolved}: {exc}"
            ) from exc
        if not stat.S_ISREG(before.st_mode):
            raise DoctorInputError(
                f"Runtime binding must resolve to a regular file: {check.check_id}: {resolved}"
            )
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise DoctorInputError(
                f"Runtime file changed while it was being bound: {check.check_id}"
            )
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
    request_path: str | Path,
    workspace: str | Path,
    runtime_profile: str | Path,
    *,
    source_root: Path | None = None,
    ops: DoctorOps = DEFAULT_DOCTOR_OPS,
) -> DoctorResult:
    """Inspect one local-pilot request and runtime without writing anything."""

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
        normalized = ops.normalize(request_path, root / PROFILE_RELATIVE_PATH)
    except (orchestration_contracts.ContractValidationError, OSError) as exc:
        raise DoctorInputError(str(exc)) from exc
    try:
        onboarding.validate_normalized_request(normalized)
    except onboarding.OnboardingError as exc:
        raise DoctorInputError(str(exc)) from exc
    step00c_blockers, step00c_remediations = _step00c_external_parent_blockers(
        normalized,
        path_access=ops.path_access,
    )
    blockers.extend(step00c_blockers)
    remediations.extend(step00c_remediations)
    reference_fasta = Path(
        str(normalized.projection_source["reference"]["fasta"]["path"])
    )
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
    profile_bytes, declared_checks = ops.load_runtime_profile(profile_path)
    validate_runtime_profile_contract(declared_checks, root)
    renv_library = _declared_renv_library(declared_checks)
    environment = runtime_environment(
        root,
        renv_library,
        base_environment=os.environ,
    )
    java_targets = [
        check.target for check in declared_checks if check.check_id == "java"
    ]
    if len(java_targets) != 1:
        raise DoctorInputError("Runtime profile must declare exactly one Java launcher")
    try:
        environment = gatk_subprocess_environment(
            java_targets[0],
            base_environment=environment,
        )
    except ProcessEnvironmentError as exc:
        raise DoctorInputError(f"Could not admit Java for GATK: {exc}") from exc
    try:
        inspection = ops.inspect_runtime(profile_path, "local", environment)
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc
    if inspection.profile_bytes != profile_bytes:
        raise DoctorInputError("Runtime profile changed while it was being inspected")
    validate_runtime_profile(inspection, root)
    observed_renv_library = next(
        Path(item.check.target)
        for item in inspection.observations
        if item.check.check_id == "renv_library"
    )
    if _admit_runtime_directory(observed_renv_library, "renv_library") != renv_library:
        raise DoctorInputError("renv_library changed during runtime inspection")
    python_check = next(
        item for item in inspection.observations if item.check.check_id == "python"
    )
    if Path(python_check.check.target) != Path(sys.executable):
        blockers.append(
            f"runtime profile Python does not match this interpreter: {python_check.check.target}"
        )
        remediations.append(
            f"Run the doctor with and declare the workflow Python launcher: {sys.executable}"
        )
    try:
        snakemake_version = ops.observe_snakemake(Path(sys.executable))
    except DoctorInputError as exc:
        blockers.append(str(exc))
        remediations.append(
            "Run `uv sync --locked --group workflow` in the EMRYS checkout."
        )
    else:
        if snakemake_version != SNAKEMAKE_VERSION:
            blockers.append(
                f"Snakemake version is {snakemake_version!r}; expected {SNAKEMAKE_VERSION}"
            )
            remediations.append(
                "Restore the locked workflow environment with `uv sync --locked --group workflow`."
            )
    for observation in inspection.observations:
        if observation.check.required and observation.status != "pass":
            blockers.append(
                f"{observation.check.check_id}: {observation.status} ({observation.observed})"
            )
            remediations.append(
                f"Set {observation.check.check_id} to the exact local path/version required by "
                f"{profile_path}."
            )
    return DoctorResult(
        request_path=normalized.request_path,
        workspace=workspace_path,
        source_root=root,
        source_commit=source_commit,
        runtime_profile=profile_path,
        runtime_profile_sha256=inspection.profile_sha256,
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
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--runtime-profile", required=True, type=Path)


def doctor_from_args(
    arguments: argparse.Namespace,
    *,
    source_root: Path | None = None,
    ops: DoctorOps = DEFAULT_DOCTOR_OPS,
) -> int:
    try:
        result = inspect_local_pilot(
            arguments.request,
            arguments.workspace,
            arguments.runtime_profile,
            source_root=source_root,
            ops=ops,
        )
    except DoctorInputError as exc:
        print(f"emrys: error: {exc}", file=sys.stderr)
        return 2
    print(f"Request: {result.request_path}")
    print(f"Workspace: {result.workspace}")
    print(f"Source checkout: {result.source_root}")
    print(f"Source commit: {result.source_commit or 'not admitted'}")
    print(f"Runtime profile SHA-256: {result.runtime_profile_sha256}")
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
    "LOCAL_PILOT_R_PACKAGES",
    "LOCAL_PILOT_RUNTIME_CHECKS",
    "RuntimeBinding",
    "configure_parser",
    "doctor_from_args",
    "inspect_local_pilot",
    "required_tool_identities",
    "runtime_file_bindings",
    "runtime_environment",
    "storage_runtime_binding",
    "validate_runtime_profile",
)
