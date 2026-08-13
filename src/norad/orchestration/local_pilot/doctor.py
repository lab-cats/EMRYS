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

from norad.contracts.orchestration import api as orchestration_contracts
from norad.evidence.runtime_availability.inspector import (
    RuntimeInspection,
    RuntimeInspectionError,
    inspect_runtime_availability,
)
from norad.libraries.source_authority import (
    SourceCheckoutError,
    SourceCheckoutIdentity,
    controlled_python_argv,
    inspect_source_checkout,
)
from norad.orchestration.local_pilot.normalization import (
    NormalizationBundle,
    normalize_request,
)

DESCRIPTION = (
    "Check whether one explicit request, workspace, source checkout, and "
    "runtime profile are ready for the fixed local pilot. This command is "
    "read-only and never installs, repairs, loads modules, or creates a workspace."
)
SNAKEMAKE_VERSION = "9.25.1"
PROFILE_RELATIVE_PATH = Path("workflow/contracts/local_cmh_v1.json")

LOCAL_PILOT_R_PACKAGES = (
    ("r_variant_annotation", "VariantAnnotation"),
    ("r_genomic_ranges", "GenomicRanges"),
    ("r_iranges", "IRanges"),
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
    ("star", "tool_version"),
    ("samtools", "tool_version"),
    ("java", "tool_version"),
    ("gatk", "tool_version"),
    ("picard", "tool_version"),
    ("picard_jar", "path_visibility"),
    ("bcftools", "tool_version"),
    ("infer_experiment", "tool_version"),
    ("rscript", "tool_version"),
    ("renv_project", "path_visibility"),
    *((check_id, "r_namespace") for check_id, _package in LOCAL_PILOT_R_PACKAGES),
)


class DoctorInputError(RuntimeError):
    """The doctor invocation contains malformed or unsafe input."""


@dataclass(frozen=True, slots=True)
class RuntimeBinding:
    """One exact file binding admitted from the local runtime profile."""

    check_id: str
    path: Path
    resolved_path: Path
    sha256: str
    observed: str


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Immutable read-only local-pilot readiness result."""

    request_path: Path
    run_id: str
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


def runtime_environment(source_root: Path) -> dict[str, str]:
    """Return the fixed guarded R environment used by doctor and workflow."""

    return {
        "NORAD_USE_RENV": "1",
        "RENV_PROJECT": str(source_root),
        "R_PROFILE_USER": str(source_root / ".Rprofile"),
        "RENV_CONFIG_SANDBOX_ENABLED": "FALSE",
        "RENV_CONFIG_AUTO_SNAPSHOT": "FALSE",
    }


def required_tool_identities(
    inspection: RuntimeInspection,
    *,
    python_executable: Path,
    snakemake_version: str = SNAKEMAKE_VERSION,
    runtime_profile_path: Path | None = None,
) -> tuple[dict[str, str], ...]:
    """Project exact attempt tool identities from one admitted runtime probe."""

    observations = {item.check.check_id: item for item in inspection.observations}
    rscript = observations["rscript"].check.target
    identities: list[dict[str, str]] = [
        {
            "name": "python",
            "version": platform.python_version(),
            "path": str(python_executable),
        },
        {
            "name": "runtime_profile",
            "version": f"sha256:{inspection.profile_sha256}",
            "path": str(
                inspection.profile_path
                if runtime_profile_path is None
                else runtime_profile_path
            ),
        },
        {
            "name": "snakemake",
            "version": snakemake_version,
            "path": str(python_executable),
        },
    ]
    for observation in inspection.observations:
        check = observation.check
        if check.check_id in {"python", "snakemake"}:
            continue
        path = rscript if check.check_type == "r_namespace" else check.target
        identities.append(
            {
                "name": check.check_id,
                "version": observation.observed,
                "path": path,
            }
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


DEFAULT_DOCTOR_OPS = DoctorOps(
    inspect_source=_default_source_inspector,
    normalize=normalize_request,
    inspect_runtime=_default_runtime_inspector,
    observe_snakemake=_default_snakemake_observer,
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


def _workspace_blockers(
    workspace: Path, source_root: Path
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    remediations: list[str] = []
    if (
        workspace == source_root
        or workspace in source_root.parents
        or source_root in workspace.parents
    ):
        blockers.append(f"workspace overlaps the NORAD source checkout: {workspace}")
        remediations.append(
            "Choose a workspace outside and not containing the NORAD source checkout."
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
    ancestor = workspace.parent
    while not os.path.lexists(ancestor):
        if ancestor == ancestor.parent:
            raise DoctorInputError(f"Workspace has no existing parent: {workspace}")
        ancestor = ancestor.parent
    if (
        ancestor.is_symlink()
        or not ancestor.is_dir()
        or ancestor.resolve(strict=True) != ancestor
    ):
        raise DoctorInputError(
            f"Nearest existing workspace parent must be a canonical real directory: {ancestor}"
        )
    if not os.access(ancestor, os.W_OK | os.X_OK):
        blockers.append(f"workspace parent is not writable and searchable: {ancestor}")
        remediations.append(
            f"Choose a writable workspace parent instead of: {ancestor}"
        )
    return blockers, remediations


def validate_runtime_profile(inspection: RuntimeInspection, source_root: Path) -> None:
    observed_shape = tuple(
        (observation.check.check_id, observation.check.check_type)
        for observation in inspection.observations
    )
    if observed_shape != LOCAL_PILOT_RUNTIME_CHECKS:
        expected = ", ".join(check_id for check_id, _kind in LOCAL_PILOT_RUNTIME_CHECKS)
        raise DoctorInputError(
            "Local-pilot runtime profile must contain the exact ordered check roster: "
            + expected
        )
    rscript_target = next(
        observation.check.target
        for observation in inspection.observations
        if observation.check.check_id == "rscript"
    )
    for observation in inspection.observations:
        check = observation.check
        if not check.required or check.runtime_context not in {"local", "any"}:
            raise DoctorInputError(
                f"Local-pilot runtime check must be required in local/any context: {check.check_id}"
            )
        if check.check_id.startswith("r_") and check.probe_args != (rscript_target,):
            raise DoctorInputError(
                f"R namespace check must use the declared Rscript target: {check.check_id}"
            )
    checks = {
        observation.check.check_id: observation.check
        for observation in inspection.observations
    }
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
    renv = next(
        observation.check.target
        for observation in inspection.observations
        if observation.check.check_id == "renv_project"
    )
    if Path(renv) != source_root:
        raise DoctorInputError(
            f"renv_project must be the NORAD source checkout: expected {source_root}"
        )


def _bind_files(inspection: RuntimeInspection) -> tuple[RuntimeBinding, ...]:
    bindings: list[RuntimeBinding] = []
    for observation in inspection.observations:
        if observation.check.check_type not in {"tool_version", "path_visibility"}:
            continue
        if observation.check.check_id == "renv_project":
            continue
        path = Path(observation.check.target)
        if not path.is_absolute():
            raise DoctorInputError(
                f"Local-pilot runtime target must be absolute: {observation.check.check_id}"
            )
        try:
            resolved = path.resolve(strict=True)
            state = resolved.stat()
            data = resolved.read_bytes()
        except OSError as exc:
            continue
        if not stat.S_ISREG(state.st_mode):
            continue
        bindings.append(
            RuntimeBinding(
                check_id=observation.check.check_id,
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
    blockers, remediations = _workspace_blockers(workspace_path, root)
    source_commit: str | None = None
    try:
        identity = ops.inspect_source(root, _package_root())
        source_commit = identity.commit
    except SourceCheckoutError as exc:
        blockers.append(f"source checkout is not ready: {exc}")
        remediations.append(
            "Use the clean reviewed NORAD checkout and selected workflow environment."
        )
    try:
        normalized = ops.normalize(request_path, root / PROFILE_RELATIVE_PATH)
    except (orchestration_contracts.ContractValidationError, OSError) as exc:
        raise DoctorInputError(str(exc)) from exc
    environment = dict(os.environ)
    environment.update(runtime_environment(root))
    try:
        inspection = ops.inspect_runtime(profile_path, "local", environment)
    except RuntimeInspectionError as exc:
        raise DoctorInputError(str(exc)) from exc
    validate_runtime_profile(inspection, root)
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
            "Run `uv sync --locked --group workflow` in the NORAD checkout."
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
        run_id=normalized.run_id,
        workspace=workspace_path,
        source_root=root,
        source_commit=source_commit,
        runtime_profile=profile_path,
        runtime_profile_sha256=inspection.profile_sha256,
        inspection=inspection,
        bindings=_bind_files(inspection),
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
        print(f"norad: error: {exc}", file=sys.stderr)
        return 2
    print(f"Request: {result.request_path}")
    print(f"Run ID: {result.run_id}")
    print(f"Workspace: {result.workspace}")
    print(f"Source checkout: {result.source_root}")
    print(f"Source commit: {result.source_commit or 'not admitted'}")
    print(f"Runtime profile SHA-256: {result.runtime_profile_sha256}")
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
    "runtime_environment",
    "validate_runtime_profile",
)
