"""Create and validate explicit scientist-facing Project inputs."""

from __future__ import annotations

import argparse
import gzip
import os
import re
import shlex
import stat
import sys
import hashlib
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from emrys import __version__
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.scientific_evidence import step08
from emrys.evidence.runtime_availability.inspector import (
    RuntimeInspection,
    RuntimeInspectionError,
    inspect_runtime_profile_bytes,
    runtime_profile_checks,
    runtime_profile_bytes,
    load_runtime_profile_contract,
    load_runtime_seal,
    runtime_profile_choices,
    runtime_file_bindings,
    runtime_seal_bytes,
    shared_runtime_profile_bytes,
)
from emrys.libraries.application_logging import (
    add_verbose_argument,
    console_print,
    phase_progress,
)
from emrys.libraries.exclusive_publication import (
    acquire_lock,
    publish_exclusive,
    release_lock,
)
from emrys.libraries.process_environment import command_flags, guarded_r_environment
from emrys.libraries.source_authority import controlled_python_argv
from emrys.libraries.references.contigs import (
    ReferenceContigError,
    parse_fasta_lines,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.mpileup import (
    selector_file_semantics,
    validate_region_selector,
)
from emrys.libraries.validation.inputs import (
    read_bytes_with_identity,
    sha256_with_identity,
)
from emrys.libraries.validation.tsv import tsv_bytes
from emrys.orchestration.run_coordinator.normalization import (
    ProjectAdmission,
    _admit_project_data,
    admit_project,
    validate_authored_path,
)
from emrys.orchestration.run_coordinator.execution_profile import (
    ExecutionProfileError,
    PROJECT_PROFILE_DIRECTORY,
    add_site_argument,
    admit_execution_profile_bytes,
    load_execution_profile,
    project_default_profile_bytes,
    project_execution_profile_path,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    ResourceConfigError,
    add_resource_override_arguments,
    overrides_from_args,
    resume_resource_policy,
)
from emrys.stages.gtf_to_bed12 import converter as gtf_converter

DESCRIPTION = (
    "Validate one complete EMRYS Project before probing the scientific "
    "runtime. This command reads declared inputs, checks reference compatibility, "
    "and writes nothing."
)
PROFILE_RELATIVE_PATH = Path("workflow/contracts/local_cmh_v2.json")
PROJECT_DIRECTORIES = ("logs", "runs")
RUNTIME_PROFILE_RELATIVE_PATH = Path("runtime/runtime.tsv")
PATH_TOOL_COMMANDS = {
    "bash": "bash",
    "star": "STAR",
    "samtools": "samtools",
    "java": "java",
    "gatk": "gatk",
    "bcftools": "bcftools",
    "infer_experiment": "infer_experiment.py",
    "gunzip": "gunzip",
}
FASTQ_PAIR_NAME = re.compile(
    r"^(?P<sample>[A-Za-z0-9][A-Za-z0-9._-]*)_R?(?P<mate>[12])"
    r"\.(?:fastq|fq)(?:\.gz)?$"
)


class OnboardingError(RuntimeError):
    """An onboarding input or publication boundary is unsafe or invalid."""


class RuntimeDiscoveryError(OnboardingError):
    """The active environment does not identify one complete runtime."""


@dataclass(frozen=True, slots=True)
class ProjectValidation:
    """Read-only admitted Project and compatibility evidence."""

    project: ProjectAdmission
    fasta_contigs: tuple[tuple[str, int], ...]
    transcript_count: int
    sample_count: int
    gtf_warnings: tuple[str, ...]


def source_root() -> Path:
    """Return the executing installed package root."""

    return Path(__file__).resolve().parents[2]


def _absolute(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise OnboardingError(f"path must be absolute: {path}")
    return Path(os.path.abspath(path))


def project_definition_path(selection: str | Path | None = None) -> Path:
    """Resolve the exact current, named-directory, or explicit Project definition."""

    candidate = Path(
        os.path.abspath("project.yaml" if selection is None else selection)
    )
    if candidate.is_dir() or (not candidate.exists() and candidate.suffix != ".yaml"):
        candidate /= "project.yaml"
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise OnboardingError(
            f"Project definition is unavailable: {candidate}"
        ) from exc
    if resolved != candidate or not candidate.is_file():
        raise OnboardingError(f"Project definition is unavailable: {candidate}")
    return candidate


def add_project_argument(parser: argparse.ArgumentParser) -> None:
    """Add the one ordinary Project selector shared by public commands."""

    parser.add_argument(
        "--project",
        help="Named Project directory or exact project.yaml path; default: current Project.",
    )


_PLACEMENT_FIELDS = (
    "account",
    "partition",
    "qos",
    "cpus_per_task",
    "memory_mb",
    "time",
    "exclusive",
    "nodelist",
    "scratch_parent",
)


def configure_profile_create_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("name", help="Absent Project profile name, without .yaml.")
    add_project_argument(parser)
    placement = parser.add_mutually_exclusive_group(required=True)
    add_site_argument(placement)
    placement.add_argument("--placement", choices=("direct", "slurm"))
    for field in _PLACEMENT_FIELDS:
        if field == "exclusive":
            parser.add_argument("--exclusive", action=argparse.BooleanOptionalAction)
        else:
            parser.add_argument(
                "--" + field.replace("_", "-"),
                type=int if field in {"cpus_per_task", "memory_mb"} else str,
                help="Explicit Slurm placement value; omission retains the selected site setting.",
            )
    parser.add_argument(
        "--module-init", help="Absolute initialization file for exact modules."
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Exact module to load, in order; repeatable.",
    )
    add_resource_override_arguments(parser)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create the absent profile after displaying its settings.",
    )
    parser.set_defaults(_command_parser=parser)


def profile_create_from_args(arguments: argparse.Namespace) -> int:
    """Preview or create execution settings without reading scientific inputs."""

    try:
        project = project_definition_path(arguments.project)
        project_data, _ = read_bytes_with_identity(project, "Project definition")
        orchestration_contracts.validate_record(
            "project", orchestration_contracts.load_yaml_object_bytes(project_data)
        )
        if Path(arguments.name).is_absolute():
            raise OnboardingError(
                "Profile creation requires a Project profile name, not a path"
            )
        destination = project_execution_profile_path(project, arguments.name)
        if (
            destination.parent.resolve(strict=True) != destination.parent
            or not destination.parent.is_dir()
        ):
            raise OnboardingError(
                "Profile parent must be an existing canonical directory"
            )
        if os.path.lexists(destination):
            raise OnboardingError(f"Existing profile was preserved: {destination}")
        document = orchestration_contracts.load_yaml_object_bytes(
            project_default_profile_bytes(arguments.site)
        )
        if arguments.placement == "slurm":
            document["placement"] = {
                "kind": "slurm",
                **dict.fromkeys(_PLACEMENT_FIELDS),
                "exclusive": False,
                "modules": {"mode": "none", "init": "", "load": []},
            }
        placement = document["placement"]
        supplied = {
            field: getattr(arguments, field)
            for field in _PLACEMENT_FIELDS
            if getattr(arguments, field) is not None
        }
        if placement["kind"] == "direct" and (
            supplied or arguments.module_init is not None or arguments.module
        ):
            raise OnboardingError(
                "Slurm placement options require --site or --placement slurm"
            )
        placement.update(supplied)
        if placement["kind"] == "slurm":
            missing = [
                field
                for field in ("cpus_per_task", "time", "scratch_parent")
                if placement[field] is None
            ]
            if missing:
                raise OnboardingError(
                    "Custom Slurm placement requires: "
                    + ", ".join("--" + field.replace("_", "-") for field in missing)
                )
        if arguments.module_init is not None or arguments.module:
            if not arguments.module_init or not arguments.module:
                raise OnboardingError(
                    "Exact modules require both --module-init and --module"
                )
            placement["modules"] = {
                "mode": "exact",
                "init": arguments.module_init,
                "load": arguments.module,
            }
        defaults = load_execution_profile()
        overrides = overrides_from_args(arguments)
        if overrides.labels():
            document["resources"] = resume_resource_policy(
                defaults.resource_policy, overrides=overrides
            ).document()
        data = yaml.safe_dump(document, sort_keys=False).encode("utf-8")
        profile = admit_execution_profile_bytes(
            orchestration_contracts.canonical_json_bytes(defaults.document()),
            destination,
            data,
        )
        profile.validate_reservation()
        print(f"Execution profile: {str(destination)!r}")
        for line in profile.submission_summary():
            print(line)
        print(
            "Computational settings: complete reviewed policy will be saved in this profile."
            if profile.computational_resources_explicit
            else "Computational settings: packaged defaults; a resumed Run retains its existing policy."
        )
        print(
            "This preview does not verify runtime readiness or observed allocation capacity."
        )
        if not arguments.execute:
            print(
                "Dry-run complete; no files were written. Repeat with --execute to create this profile."
            )
            return 0
        publish_exclusive(destination, data, OnboardingError)
        load_execution_profile(
            destination, expected_binding_sha256=profile.binding_sha256
        )
        print(f"Profile created. Select it with --profile {arguments.name}.")
        return 0
    except (
        OSError,
        OnboardingError,
        ExecutionProfileError,
        ResourceConfigError,
        ValidationError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _require_external_absent_output(value: str | Path, root: Path) -> Path:
    output = _absolute(value)
    if os.path.lexists(output):
        raise OnboardingError(f"output directory must be absent: {output}")
    if output == root or output in root.parents or root in output.parents:
        raise OnboardingError(
            f"output directory must not overlap the installed EMRYS package: {output}"
        )
    parent = output.parent
    try:
        state = parent.lstat()
        resolved = parent.resolve(strict=True)
    except OSError as exc:
        raise OnboardingError(
            f"output parent must already exist as a canonical directory: {parent}: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != parent
    ):
        raise OnboardingError(
            f"output parent must be a canonical real directory: {parent}"
        )
    if not os.access(parent, os.W_OK | os.X_OK):
        raise OnboardingError(
            f"output parent must be writable and searchable: {parent}"
        )
    return output


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_member(path: Path, data: bytes, mode: int) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fchmod(handle.fileno(), mode)
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def _re_admit_published_tree(
    output: Path,
    expected_output_identity: tuple[int, int],
    members: Mapping[str, tuple[bytes, int]],
    completion_name: str,
    completion_bytes: bytes,
    expected_directories: set[str],
) -> None:
    try:
        output_state = output.lstat()
    except OSError as exc:
        raise OnboardingError(
            f"could not re-admit output directory {output}: {exc}"
        ) from exc
    if (
        not stat.S_ISDIR(output_state.st_mode)
        or (output_state.st_dev, output_state.st_ino) != expected_output_identity
    ):
        raise OnboardingError(f"published output directory identity changed: {output}")
    expected = {*members, completion_name}
    observed: set[str] = set()
    observed_directories: set[str] = set()
    for path in output.rglob("*"):
        state = path.lstat()
        if stat.S_ISLNK(state.st_mode):
            raise OnboardingError(f"published tree contains a symlink: {path}")
        if stat.S_ISDIR(state.st_mode):
            observed_directories.add(path.relative_to(output).as_posix())
            if stat.S_IMODE(state.st_mode) != 0o700:
                raise OnboardingError(f"published directory mode changed: {path}")
            continue
        if not stat.S_ISREG(state.st_mode):
            raise OnboardingError(f"published tree contains a non-file member: {path}")
        observed.add(path.relative_to(output).as_posix())
    if observed != expected:
        raise OnboardingError(
            "published tree membership differs from the prepared transaction: "
            f"expected {sorted(expected)}, observed {sorted(observed)}"
        )
    if observed_directories != expected_directories:
        raise OnboardingError(
            "published directory membership differs from the prepared transaction: "
            f"expected {sorted(expected_directories)}, "
            f"observed {sorted(observed_directories)}"
        )
    expected_members = dict(members)
    expected_members[completion_name] = (completion_bytes, 0o644)
    for relative, (expected_bytes, expected_mode) in expected_members.items():
        path = output / relative
        try:
            data, state = read_bytes_with_identity(
                path,
                f"published member {relative}",
                nonempty=False,
            )
        except ValidationError as exc:
            raise OnboardingError(str(exc)) from exc
        if stat.S_IMODE(state.st_mode) != expected_mode:
            raise OnboardingError(
                f"published member mode changed: {relative}: "
                f"{stat.S_IMODE(state.st_mode):04o}"
            )
        if data != expected_bytes or state.st_size != len(expected_bytes):
            raise OnboardingError(f"published member bytes changed: {relative}")


def publish_create_absent_tree(
    output: Path,
    members: Mapping[str, tuple[bytes, int]],
    *,
    completion_name: str,
    completion_bytes: bytes,
    directories: Sequence[str] = (),
    before_completion: Callable[[Path], None] | None = None,
) -> None:
    """Publish one reserved tree with its completion member written last."""

    file_names = (*members, completion_name)
    entry_names = (*file_names, *directories)
    if len(set(entry_names)) != len(entry_names):
        raise OnboardingError("publication member or directory is duplicated")
    for name in entry_names:
        relative = Path(name)
        if (
            not name
            or any(character in name for character in ("\x00", "\r", "\n", "\\"))
            or relative.is_absolute()
            or name != relative.as_posix()
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise OnboardingError(f"unsafe publication member path: {name!r}")
    explicit_directories = set(directories)
    directory_paths = {Path(name) for name in explicit_directories}
    directory_paths.update(
        parent
        for name in entry_names
        for parent in Path(name).parents
        if parent != Path(".")
    )
    directories = sorted(
        directory_paths,
        key=lambda path: (len(path.parts), path.as_posix()),
    )
    if any(directory.as_posix() in file_names for directory in directories):
        raise OnboardingError("publication member is also required as a directory")
    try:
        output.mkdir(mode=0o700, parents=False, exist_ok=False)
        reserved = output.lstat()
        output_identity = (reserved.st_dev, reserved.st_ino)
        _fsync_directory(output.parent)
    except OSError as exc:
        raise OnboardingError(
            f"could not reserve output directory {output}: {exc}"
        ) from exc
    try:
        for relative in directories:
            (output / relative).mkdir(mode=0o700, parents=False, exist_ok=False)
            _fsync_directory((output / relative).parent)
        for relative, (data, mode) in sorted(members.items()):
            _write_member(output / relative, data, mode)
        if before_completion is not None:
            before_completion(output)
        _write_member(output / completion_name, completion_bytes, 0o644)
        _re_admit_published_tree(
            output,
            output_identity,
            members,
            completion_name,
            completion_bytes,
            {path.as_posix() for path in directories},
        )
    except BaseException as exc:
        raise OnboardingError(
            "publication did not complete; preserve and inspect the partial "
            "create-absent directory. The completion member may be absent or "
            "present-but-invalid; its presence alone is not completion proof: "
            f"{output}: {exc}"
        ) from exc


_PROJECT_FIELDS = """sample_manifest partition_manifest
reference_fasta reference_gtf sjdb_overhang genome_sa_index_nbases
control_condition treatment_condition target_change min_sample_dp
mean_dp_threshold fdr_threshold common_or_threshold absolute_difference_threshold
background_max_fraction""".split()
_PROJECT_TYPES = {
    field: converter
    for fields, converter in (
        (
            "sample_manifest partition_manifest reference_fasta reference_gtf".split(),
            Path,
        ),
        ("sjdb_overhang genome_sa_index_nbases min_sample_dp".split(), int),
        (
            "mean_dp_threshold fdr_threshold common_or_threshold absolute_difference_threshold background_max_fraction".split(),
            float,
        ),
    )
    for field in fields
}
_PROJECT_SUGGESTIONS = dict(
    zip(
        "min_sample_dp mean_dp_threshold fdr_threshold common_or_threshold absolute_difference_threshold background_max_fraction".split(),
        (1, 50, 0.05, 1.2, 0.005, 0.01),
        strict=True,
    )
)


def configure_project_init_parser(parser: argparse.ArgumentParser) -> None:
    add_site_argument(parser)
    add_verbose_argument(parser)
    parser.add_argument(
        "project_name",
        metavar="PROJECT_NAME",
        type=_project_name,
        help="Safe name for the new child directory and Project root.",
    )
    for destination in _PROJECT_FIELDS:
        parser.add_argument(
            f"--{destination.replace('_', '-')}",
            type=_PROJECT_TYPES.get(destination, str),
            help=f"{destination.replace('_', ' ')}; prompted when omitted.",
        )
    parser.add_argument(
        "--background-condition",
        help="Optional background condition; omission means no background cohort.",
    )
    parser.add_argument(
        "--analysis-name",
        default="primary",
        help="Human name for the initial Analysis; default: primary.",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Create; omission is a no-write plan."
    )
    parser.set_defaults(_command_parser=parser)


def _project_name(value: str) -> str:
    if value in {"project", "manifests", "synthetic"}:
        raise argparse.ArgumentTypeError(f"reserved Project name: {value}")
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value) is None:
        raise argparse.ArgumentTypeError(
            "must begin with a letter or digit and contain only letters, digits, '.', '_', or '-'"
        )
    return value


def _collect_project_answers(arguments: argparse.Namespace) -> dict[str, object]:
    missing = [
        f"--{destination.replace('_', '-')}"
        for destination in _PROJECT_FIELDS
        if getattr(arguments, destination) is None
    ]
    interactive = sys.stdin.isatty() and sys.stderr.isatty()
    if missing and not interactive:
        raise OnboardingError(
            "missing Project setup answers: "
            + ", ".join(missing)
            + "; supply them explicitly or run this command in a terminal"
        )
    answers: dict[str, object] = {}
    for destination in _PROJECT_FIELDS:
        value = getattr(arguments, destination)
        if value is None:
            label = destination.replace("_", " ")
            suggestion = _PROJECT_SUGGESTIONS.get(destination)
            suffix = f" [{suggestion}]" if suggestion is not None else ""
            print(f"{label}{suffix}: ", end="", file=sys.stderr, flush=True)
            raw = sys.stdin.readline()
            if raw == "":
                raise OnboardingError(
                    f"Project setup ended before {label} was supplied"
                )
            raw = raw.strip() or ("" if suggestion is None else str(suggestion))
            if not raw:
                raise OnboardingError(f"{label} is required")
            try:
                value = _PROJECT_TYPES.get(destination, str)(raw)
            except (TypeError, ValueError) as exc:
                raise OnboardingError(f"invalid {label}: {raw!r}") from exc
        answers[destination] = value
    return answers


def _project_yaml(answers: Mapping[str, object]) -> bytes:
    target = str(answers["target_change"]).upper()
    match = re.fullmatch(r"([ACGT])>([ACGT])", target)
    if match is None or match[1] == match[2]:
        raise OnboardingError(
            "target RNA change must name two different bases, like A>G"
        )
    analysis = {
        "partitions": str(answers["partition_manifest"]),
        **{
            key: answers[key]
            for key in (
                "control_condition",
                "treatment_condition",
                "min_sample_dp",
                "mean_dp_threshold",
                "fdr_threshold",
                "common_or_threshold",
                "absolute_difference_threshold",
                "background_condition",
                "background_max_fraction",
            )
        },
        "target_change": target,
    }
    document = {
        "schema_version": "emrys.project.v1",
        "dataset": {"samples": str(answers["sample_manifest"])},
        "reference": {
            "fasta": str(answers["reference_fasta"]),
            "gtf": str(answers["reference_gtf"]),
            "star_index": {
                "sjdb_overhang": answers["sjdb_overhang"],
                "genome_sa_index_nbases": answers["genome_sa_index_nbases"],
            },
        },
        "analyses": {str(answers["analysis_name"]): analysis},
    }
    return yaml.safe_dump(document, sort_keys=False).encode("utf-8")


def _print_project_preview(
    project: ProjectAdmission,
    answers: Mapping[str, object],
    site: str | None,
    *,
    verbose: bool,
) -> None:
    """Review named init's admitted built-in Analysis and replay its answers."""

    def location(label: str, snapshot: Mapping[str, object]) -> None:
        print(f"  {label}: {snapshot['path']!r}; SHA-256: {snapshot['sha256']}")

    if verbose:
        source = project.select_analysis().workflow_inputs
        console_print("Detailed study review", style="bold blue", file=sys.stdout)
        for name in ("samples", "partitions"):
            location(f"{name} manifest", source[name]["manifest"])
        for name in ("fasta", "gtf"):
            location(f"reference {name}", source["reference"][name])
        print("Sample assignments (pairing groups are explicitly supplied):")
        for sample in source["samples"]["rows"]:
            print(
                f"  {sample['sample_id']}: condition={sample['condition']}; "
                f"pairing group={sample['replicate']}; strandedness={sample['strandedness']}"
            )
            for mate in ("r1_fastq", "r2_fastq"):
                location(mate, sample[mate])
        for partition in source["partitions"]["rows"]:
            print(
                f"  Partition {partition['partition_id']}: {partition['selector_type']} "
                f"{partition['selector_value']!r}"
            )
            if partition["selector_file"] is not None:
                print(
                    f"    format={partition['selector_format']}; "
                    f"compression={partition['selector_compression']}; "
                    f"SHA-256: {partition['selector_file']['sha256']}"
                )
        settings = {
            **source["reference"]["star_index"],
            **source["analysis"]["policy"]["configuration"],
        }
        print("Scientific settings:")
        print(f"  target change: {settings['rna_ref']}>{settings['rna_alt']}")
        for name, value in settings.items():
            if name not in {"rna_ref", "rna_alt"}:
                print(f"  {name.replace('_', ' ')}: {'none' if value is None else value}")
    flags = command_flags(
        *(
            (name.replace("_", "-"), value)
            for name, value in {**answers, "site": site}.items()
            if value is not None
        )
    )
    replay = controlled_python_argv(
        sys.executable,
        "-m",
        "emrys",
        "init",
        project.source_path.parent.name,
        *flags,
        "--execute",
    )
    print("Create this Project without repeating the questions:")
    parent = shlex.quote(str(project.source_path.parent.parent))
    print(f"cd {parent} && {shlex.join(replay)}")


def init_project_from_args(arguments: argparse.Namespace) -> int:
    """Plan or create one validated Project root around existing inputs."""

    try:
        answers = _collect_project_answers(arguments)
        execution_profile_bytes = project_default_profile_bytes(
            getattr(arguments, "site", None)
        )
        output = _require_external_absent_output(
            Path.cwd() / arguments.project_name, source_root()
        )
        for field in _PROJECT_FIELDS[:4]:
            answers[field] = _absolute(Path(answers[field])).resolve(strict=True)
        answers["analysis_name"] = arguments.analysis_name
        answers["background_condition"] = arguments.background_condition
        project_bytes = _project_yaml(answers)
        print(
            "Project preparation reads and hashes all declared inputs and checks "
            "reference compatibility. Large inputs may take several minutes.",
            file=sys.stderr,
        )
        with phase_progress("Reading and hashing Project inputs"):
            preview = _admit_project_data(
                output / "project.yaml",
                project_bytes,
                source_root() / PROFILE_RELATIVE_PATH,
            )
        with phase_progress("Checking reference and partition compatibility"):
            validate_project_admission(preview)
        analysis = preview.select_analysis()
        source = analysis.workflow_inputs
        samples = source["samples"]["rows"]
        console_print("Project preparation", style="bold blue", file=sys.stdout)
        print(f"  Output directory: {output}")
        print(f"  Libraries ({len(samples)}): {', '.join(str(row['sample_id']) for row in samples)}")
        print(f"  Analysis: {analysis.name}; site: {getattr(arguments, 'site', None) or 'direct'}")
        print(f"  Reference: {source['reference']['fasta']['path']}")
        print(f"  Partitions: {len(source['partitions']['rows'])}")
        print(f"  Comparison: {answers['control_condition']} -> {answers['treatment_condition']}; target {answers['target_change']}")
        if not arguments.execute:
            _print_project_preview(
                preview,
                answers,
                getattr(arguments, "site", None),
                verbose=getattr(arguments, "verbose", False),
            )
            console_print("Dry-run complete; no files were written.", style="yellow", file=sys.stdout)
            return 0
        publish_create_absent_tree(
            output,
            {
                (PROJECT_PROFILE_DIRECTORY / "default.yaml").as_posix(): (
                    execution_profile_bytes,
                    0o644,
                )
            },
            completion_name="project.yaml",
            completion_bytes=project_bytes,
            directories=PROJECT_DIRECTORIES,
        )
        with phase_progress("Verifying the published Project"):
            validate_project(output / "project.yaml")
        console_print(f"Project ready: {output / 'project.yaml'}", style="green", file=sys.stdout)
        return 0
    except (
        OSError,
        OnboardingError,
        orchestration_contracts.ContractValidationError,
        step08.ContractError,
    ) as exc:
        console_print(f"ERROR: {exc}", style="red", file=sys.stderr)
        return 2


def _admit_supplied_file(value: str | Path, label: str) -> Path:
    path = Path(value)
    admitted = _admit_existing_path(
        path if path.is_absolute() else Path.cwd() / path, label
    )
    emitted = str(admitted)
    if any(character in emitted for character in ('"', "\t", "\r", "\n")):
        raise OnboardingError(f"{label} cannot be represented in a raw TSV field")
    validate_authored_path(emitted, label)
    return admitted


def _indexed_values(
    rows: Sequence[Sequence[str]], label: str
) -> dict[str, tuple[str, ...]]:
    indexed: dict[str, tuple[str, ...]] = {}
    for key, *values in rows:
        if key in indexed:
            raise OnboardingError(f"duplicate {label}: {key}")
        indexed[key] = tuple(values)
    return indexed


def _draft_manifest_members(
    fastqs: Sequence[Path],
    samples: Sequence[Sequence[str]],
    regions_files: Sequence[Sequence[str]],
    regions: Sequence[Sequence[str]],
) -> dict[str, tuple[bytes, int]]:
    """Render validated manifest drafts from explicit paths and biology."""

    sample_rows: dict[str, dict[str, str]] = {}
    file_roles: dict[tuple[int, int], str] = {}
    for value in fastqs:
        admitted_path = _admit_supplied_file(value, "supplied FASTQ")
        match = FASTQ_PAIR_NAME.fullmatch(admitted_path.name)
        if match is None:
            raise OnboardingError(
                "FASTQ names must end in <sample>_R1/_R2 or <sample>_1/_2 followed by "
                f".fastq/.fq and optional .gz: {admitted_path}"
            )
        sample_id, mate = match["sample"], match["mate"]
        role = f"sample {sample_id} R{mate}"
        state = admitted_path.stat()
        identity = (state.st_dev, state.st_ino)
        if previous := file_roles.get(identity):
            raise OnboardingError(f"one FASTQ file is reused as {previous} and {role}")
        file_roles[identity] = role
        row = sample_rows.setdefault(sample_id, {"sample_id": sample_id})
        column = f"r{mate}_fastq"
        if column in row:
            raise OnboardingError(f"duplicate R{mate} FASTQ for sample {sample_id}")
        row[column] = str(admitted_path)

    for sample_id, row in sample_rows.items():
        if not {"r1_fastq", "r2_fastq"} <= row.keys():
            raise OnboardingError(f"unpaired FASTQ sample: {sample_id}")
        if row["r1_fastq"].endswith(".gz") != row["r2_fastq"].endswith(".gz"):
            raise OnboardingError(
                f"R1 and R2 FASTQs use different compression for sample {sample_id}"
            )

    assignments = _indexed_values(samples, "--sample assignment")
    unexpected = sorted(assignments.keys() - sample_rows.keys())
    if unexpected:
        raise OnboardingError(
            "--sample assignments have no supplied FASTQ pair: " + ", ".join(unexpected)
        )
    missing = sorted(sample_rows.keys() - assignments.keys())
    if missing:
        flags = "\n".join(
            f"  --sample {key} CONDITION REPLICATE STRANDEDNESS" for key in missing
        )
        raise OnboardingError(f"biological assignments are required:\n{flags}")
    for sample_id, (condition, replicate, strandedness) in assignments.items():
        step08.validate_safe_id(f"sample {sample_id} condition", condition)
        sample_rows[sample_id].update(
            condition=condition, replicate=replicate, strandedness=strandedness
        )
    sample_bytes = tsv_bytes(
        step08.SAMPLE_MANIFEST_REQUIRED,
        (sample_rows[key] for key in sorted(sample_rows)),
    )
    step08.validate_sample_manifest_bytes(sample_bytes, "samples.tsv")
    members = {"samples.tsv": (sample_bytes, 0o644)}
    rows = []
    for selector_type, selections in (
        ("regions_file", regions_files),
        ("region", regions),
    ):
        for partition_id, (value,) in sorted(
            _indexed_values(selections, f"--{selector_type.replace('_', '-')}").items()
        ):
            if selector_type == "regions_file":
                value = str(
                    _admit_supplied_file(
                        value, f"partition {partition_id} regions file"
                    )
                )
            rows.append(
                dict(
                    partition_id=partition_id,
                    selector_type=selector_type,
                    selector_value=value,
                )
            )
    if rows:
        rows.sort(key=lambda row: row["partition_id"])
        partition_bytes = tsv_bytes(step08.PARTITION_MANIFEST_HEADER, rows)
        step08.validate_partition_manifest_bytes(partition_bytes, "partitions.tsv")
        members["partitions.tsv"] = (partition_bytes, 0o644)
    return members


def configure_manifest_init_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Absolute absent draft directory.",
    )
    parser.add_argument(
        "--fastq",
        required=True,
        action="extend",
        nargs="+",
        type=Path,
        help="Existing FASTQs named <sample>_R1/_R2 or <sample>_1/_2 (.fastq/.fq, optional .gz).",
    )
    parser.add_argument(
        "--sample",
        action="append",
        nargs=4,
        default=[],
        metavar=("SAMPLE_ID", "CONDITION", "REPLICATE", "STRANDEDNESS"),
        help="Explicit biology for one inferred pair; repeat for every sample.",
    )
    for name, value in (("regions-file", "PATH"), ("region", "REGION")):
        parser.add_argument(
            f"--{name}",
            action="append",
            nargs=2,
            default=[],
            metavar=("PARTITION_ID", value),
            help=f"Optional {name.replace('-', ' ')}; repeat for additional partitions.",
        )
    parser.add_argument(
        "--execute", action="store_true", help="Publish; omission is a no-write plan."
    )
    parser.set_defaults(_command_parser=parser)


def init_manifests_from_args(arguments: argparse.Namespace) -> int:
    """Discover, validate, and optionally publish structural manifest drafts."""

    try:
        output = _require_external_absent_output(arguments.output_dir, source_root())
        members = _draft_manifest_members(
            arguments.fastq,
            arguments.sample,
            arguments.regions_file,
            arguments.region,
        )
        print(f"Output directory: {output}")
        print("Draft manifests: " + ", ".join(sorted(members)))
        print("Publication policy: create-absent; no file will be replaced or adopted.")
        if not arguments.execute:
            print("Dry-run complete; no files were written.")
            return 0
        sample_bytes, _ = members["samples.tsv"]
        publish_create_absent_tree(
            output,
            {name: member for name, member in members.items() if name != "samples.tsv"},
            completion_name="samples.tsv",
            completion_bytes=sample_bytes,
        )
        print(f"Published validated manifest drafts: {output}")
        return 0
    except (
        OSError,
        OnboardingError,
        orchestration_contracts.ContractValidationError,
        step08.ContractError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _require_snapshot(snapshot: Mapping[str, object], label: str) -> Path:
    path = Path(str(snapshot["path"]))
    try:
        digest, state = sha256_with_identity(path, label)
    except ValidationError as exc:
        raise OnboardingError(f"could not re-admit {label}: {path}: {exc}") from exc
    if digest != snapshot["sha256"] or state.st_size != snapshot["size_bytes"]:
        raise OnboardingError(f"{label} changed after Project admission: {path}")
    return path


def _regions_lines(path: Path) -> Iterator[str]:
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
                yield from handle
        else:
            with path.open(encoding="utf-8", newline="") as handle:
                yield from handle
    except (EOFError, OSError, UnicodeError) as exc:
        raise OnboardingError(
            f"regions file is not valid UTF-8 text: {path}: {exc}"
        ) from exc


def _validate_regions_file(path: Path, lengths: Mapping[str, int]) -> None:
    mode, _compression = selector_file_semantics(path)
    row_mode: int | None = None
    count = 0
    for row_number, raw in enumerate(_regions_lines(path), start=1):
        if not raw.strip() or raw.startswith("#"):
            continue
        fields = raw.rstrip("\r\n").split("\t")
        contig = fields[0]
        if contig not in lengths:
            raise OnboardingError(
                f"regions file row {row_number} contig is absent from FASTA: {contig}"
            )
        count += 1
        if mode == "bed":
            if len(fields) < 3 or not fields[1].isdigit() or not fields[2].isdigit():
                raise OnboardingError(
                    f"invalid BED interval on regions file row {row_number}"
                )
            start, end = int(fields[1]), int(fields[2])
            valid = start >= 0 and end > start and end <= lengths[contig]
        elif mode == "vcf":
            if len(fields) < 2 or not re.fullmatch(r"[1-9][0-9]*", fields[1]):
                raise OnboardingError(
                    f"invalid VCF position on regions file row {row_number}"
                )
            valid = int(fields[1]) <= lengths[contig]
        else:
            current_mode = 2 if len(fields) == 2 else 3
            if len(fields) < 2 or (row_mode is not None and current_mode != row_mode):
                raise OnboardingError(
                    f"regions file mixes position and interval rows at row {row_number}"
                )
            row_mode = current_mode
            if not re.fullmatch(r"[1-9][0-9]*", fields[1]):
                raise OnboardingError(
                    f"invalid regions file start/position on row {row_number}"
                )
            start = int(fields[1])
            valid = start <= lengths[contig]
            if current_mode == 3:
                valid = (
                    valid
                    and len(fields) >= 3
                    and re.fullmatch(r"[1-9][0-9]*", fields[2]) is not None
                    and start <= int(fields[2]) <= lengths[contig]
                )
        if not valid:
            raise OnboardingError(
                f"regions file row {row_number} is outside FASTA bounds"
            )
    if count == 0:
        raise OnboardingError(f"regions file contains no selector rows: {path}")


def validate_project(
    project: str | Path,
    *,
    root: Path | None = None,
) -> ProjectValidation:
    """Admit and compatibility-check one Project without runtime probes."""

    package_root = source_root() if root is None else root
    admission = admit_project(
        project,
        package_root / PROFILE_RELATIVE_PATH,
    )
    return validate_project_admission(admission)


def validate_project_admission(
    project: ProjectAdmission,
) -> ProjectValidation:
    """Compatibility-check one already admitted Project without re-admitting it."""

    source = project.analyses[0].workflow_inputs
    reference = source["reference"]
    fasta_snapshot = reference["fasta"]
    gtf_snapshot = reference["gtf"]
    fasta = _require_snapshot(fasta_snapshot, "reference FASTA")
    gtf = _require_snapshot(gtf_snapshot, "reference GTF")
    try:
        with fasta.open(encoding="utf-8") as handle:
            fasta_contigs = tuple(parse_fasta_lines(handle))
    except (OSError, UnicodeError, ReferenceContigError) as exc:
        raise OnboardingError(f"reference FASTA is invalid: {fasta}: {exc}") from exc
    warnings: list[str] = []
    try:
        transcripts = gtf_converter.normalize_gtf(gtf, warnings.append)
    except (OSError, UnicodeError, ValueError) as exc:
        raise OnboardingError(f"reference GTF is invalid: {gtf}: {exc}") from exc
    if not transcripts:
        raise OnboardingError("reference GTF contains no usable exon transcript models")
    lengths = dict(fasta_contigs)
    for transcript in transcripts:
        if transcript.chrom not in lengths:
            raise OnboardingError(
                "reference GTF transcript contig is absent from FASTA: "
                f"{transcript.name} ({transcript.chrom})"
            )
        if transcript.chrom_end > lengths[transcript.chrom]:
            raise OnboardingError(
                "reference GTF transcript exceeds FASTA bounds: "
                f"{transcript.name} ends at {transcript.chrom_end}; "
                f"{transcript.chrom} length is {lengths[transcript.chrom]}"
            )
    _require_snapshot(fasta_snapshot, "reference FASTA")
    _require_snapshot(gtf_snapshot, "reference GTF")
    for analysis in project.analyses:
        analysis_source = analysis.workflow_inputs
        for partition in analysis_source["partitions"]["rows"]:
            if partition["selector_type"] == "region":
                try:
                    validate_region_selector(str(partition["selector_value"]), lengths)
                except ValidationError as exc:
                    raise OnboardingError(str(exc)) from exc
            else:
                selector_snapshot = partition["selector_file"]
                if not isinstance(selector_snapshot, Mapping):
                    raise OnboardingError(
                        "regions_file partition has no admitted file snapshot"
                    )
                selector_path = _require_snapshot(
                    selector_snapshot, "partition regions file"
                )
                _validate_regions_file(selector_path, lengths)
                _require_snapshot(selector_snapshot, "partition regions file")
    return ProjectValidation(
        project=project,
        fasta_contigs=fasta_contigs,
        transcript_count=len(transcripts),
        sample_count=project.dataset_sample_count,
        gtf_warnings=tuple(warnings),
    )


def configure_validation_parser(parser: argparse.ArgumentParser) -> None:
    add_project_argument(parser)
    add_verbose_argument(parser)
    parser.set_defaults(_command_parser=parser)


def validate_from_args(arguments: argparse.Namespace) -> int:
    try:
        result = validate_project(project_definition_path(arguments.project))
    except (
        OSError,
        OnboardingError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        console_print(
            f"Project validation: FAIL — {exc}", style="red", file=sys.stderr
        )
        return 1
    project = result.project
    reference = project.analyses[0].workflow_inputs["reference"]
    verbose = getattr(arguments, "verbose", False)
    warning = f" — {len(result.gtf_warnings)} warning(s); use --verbose for details" if result.gtf_warnings and not verbose else ""
    console_print(f"Project validation: PASS{warning}", style="yellow" if warning else "green", file=sys.stdout)
    if not verbose:
        return 0
    print(f"  Project: {project.source_path}")
    print(f"  Project SHA-256: {project.source_sha256}")
    print(f"  Samples: {result.sample_count}")
    print(f"  Analyses: {len(project.analyses)}")
    for analysis in project.analyses:
        source = analysis.workflow_inputs
        print(
            f"    {analysis.name}: {len(source['samples']['rows'])} samples, "
            f"{len(source['partitions']['rows'])} partitions"
        )
    print(
        f"  FASTA contigs / GTF transcripts: {len(result.fasta_contigs)} / {result.transcript_count}"
    )
    print(f"  Reference FASTA: {reference['fasta']['path']}")
    if result.gtf_warnings:
        print(f"  GTF normalization warnings: {len(result.gtf_warnings)}")
        for warning in result.gtf_warnings:
            print(f"    - {warning}")
    print(
        "Evidence boundary: input/config compatibility only; no tools or analysis ran."
    )
    return 0


def _admit_existing_path(
    value: str | Path,
    label: str,
    *,
    directory: bool = False,
    executable: bool = False,
    writable: bool = False,
    canonical: bool = False,
    retain_path: bool = False,
) -> Path:
    path = _absolute(value)
    try:
        authored = path.lstat()
        resolved = path.resolve(strict=True)
        state = resolved.stat()
    except OSError as exc:
        raise OnboardingError(f"could not inspect {label}: {path}: {exc}") from exc
    kind, predicate = (
        ("directory", stat.S_ISDIR) if directory else ("file", stat.S_ISREG)
    )
    if not predicate(state.st_mode):
        raise OnboardingError(f"{label} must resolve to a real {kind}: {path}")
    if canonical and (stat.S_ISLNK(authored.st_mode) or resolved != path):
        raise OnboardingError(f"{label} must be canonical: {path}")
    required = os.R_OK | (os.X_OK if directory or executable else 0)
    required |= os.W_OK if writable else 0
    if (not directory and state.st_size == 0) or not os.access(path, required):
        access = (
            "readable, writable, and searchable"
            if writable
            else "readable and searchable"
            if directory
            else "nonempty and readable"
        )
        raise OnboardingError(f"{label} must be {access}: {path}")
    return path if retain_path else resolved


def runtime_profile_path(project: Path) -> Path:
    """Derive the one current runtime profile owned by a Project."""

    return Path(os.path.abspath(project)).parent / RUNTIME_PROFILE_RELATIVE_PATH


def _path_candidates(command: str, environment: Mapping[str, str]) -> tuple[Path, ...]:
    raw_path = environment.get("PATH", "")
    if not raw_path:
        raise OnboardingError(f"PATH is empty while resolving {command}")
    candidates: dict[Path, Path] = {}
    for entry in raw_path.split(os.pathsep):
        directory = Path(entry)
        if not entry or not directory.is_absolute():
            raise OnboardingError(
                f"PATH contains an empty or relative entry; refusing to resolve {command}"
            )
        candidate = directory / command
        try:
            if not candidate.is_file() or not os.access(candidate, os.X_OK):
                continue
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        candidates.setdefault(resolved, candidate)
    return tuple(sorted(candidates))


def _selected_tool(
    check_id: str,
    command: str,
    environment: Mapping[str, str],
    *,
    selector: str | None = None,
) -> Path:
    if selector and environment.get(selector):
        return _admit_existing_path(
            environment[selector],
            selector,
            executable=True,
        )
    candidates = _path_candidates(command, environment)
    if check_id == "java" and environment.get("JAVA_HOME"):
        java_home = Path(environment["JAVA_HOME"])
        if not java_home.is_absolute():
            raise RuntimeDiscoveryError("JAVA_HOME must be absolute")
        candidates = tuple(
            sorted(
                {
                    *candidates,
                    _admit_existing_path(
                        java_home / "bin/java",
                        "JAVA_HOME launcher",
                        executable=True,
                    ),
                }
            )
        )
    if not candidates:
        raise RuntimeDiscoveryError(
            f"{check_id}: {command} is absent from the active environment"
        )
    if len(candidates) != 1:
        raise RuntimeDiscoveryError(
            f"{check_id}: the active environment exposes multiple {command} installations: "
            + ", ".join(str(path) for path in candidates)
        )
    return candidates[0]


def _selected_environment_path(
    environment: Mapping[str, str],
    name: str,
    label: str,
    *,
    directory: bool = False,
) -> Path:
    value = environment.get(name)
    if not value:
        raise RuntimeDiscoveryError(
            f"{label} is not selected; set {name} in the active environment"
        )
    return _admit_existing_path(value, name, directory=directory)


def _runtime_profile_bytes(
    environment: Mapping[str, str],
    python_executable: Path,
) -> tuple[bytes, Path]:
    selected = {
        check_id: _selected_tool(check_id, command, environment)
        for check_id, command in PATH_TOOL_COMMANDS.items()
    }
    rscript = _selected_tool(
        "rscript",
        "Rscript",
        environment,
        selector="EMRYS_RSCRIPT",
    )
    picard = _selected_environment_path(
        environment,
        "EMRYS_PICARD_JAR",
        "Picard jar",
    )
    renv_library = _selected_environment_path(
        environment,
        "EMRYS_RENV_LIBRARY",
        "renv library",
        directory=True,
    )
    python = _admit_existing_path(
        python_executable,
        "workflow Python",
        executable=True,
        retain_path=True,
    )
    selected.update(
        python=python, rscript=rscript, picard_jar=picard, renv_library=renv_library
    )
    return runtime_profile_bytes(selected), renv_library


def project_runtime_directory(
    project: ProjectAdmission,
    *,
    writable: bool = True,
) -> Path:
    """Admit the canonical Project-owned runtime directory."""

    directory = project.source_path.parent / "runtime"
    try:
        return _admit_existing_path(
            directory,
            "Project runtime directory",
            directory=True,
            writable=writable,
            canonical=True,
        )
    except OnboardingError as exc:
        raise OnboardingError(
            f"Project runtime directory is unavailable; run `emrys init PROJECT_NAME`: {exc}"
        ) from exc


def discover_runtime_profile(
    *,
    project: Path,
    environment: Mapping[str, str] | None = None,
    root: Path | None = None,
    python_executable: Path | None = None,
) -> RuntimeInspection:
    """Discover and probe one candidate profile without publishing it."""

    package_root = _absolute(source_root() if root is None else root)
    admitted = validate_project(project, root=package_root).project
    destination = project_runtime_directory(admitted, writable=False) / "runtime.tsv"
    selected_environment = os.environ if environment is None else environment
    profile_bytes, renv_library = _runtime_profile_bytes(
        selected_environment,
        Path(sys.executable) if python_executable is None else python_executable,
    )
    inspection_environment = guarded_r_environment(
        package_root,
        renv_library,
        base_environment=selected_environment,
    )
    return inspect_runtime_profile_bytes(
        profile_bytes,
        destination,
        checks=runtime_profile_checks(profile_bytes, package_root),
        environment=inspection_environment,
    )


def publish_runtime_profile(inspection: RuntimeInspection) -> None:
    destination = inspection.profile_path
    publish_exclusive(
        destination,
        inspection.profile_bytes,
        OnboardingError,
        existing=f"runtime inventory already exists and was preserved: {destination}",
    )


def reuse_runtime_profile(
    *, project: Path, donor: Path, execute: bool
) -> RuntimeInspection:
    """Seal an owned donor once and freshly qualify one explicit borrower selection."""
    package_root = _absolute(source_root())
    borrower = validate_project(project, root=package_root).project
    source = validate_project(donor, root=package_root).project
    destination = project_runtime_directory(borrower, writable=execute) / "runtime.tsv"
    runtime = project_runtime_directory(source, writable=False)
    seal_path = runtime / "shared.json"
    if borrower.source_path == source.source_path:
        raise OnboardingError("Runtime reuse requires a distinct borrower Project")
    if os.path.lexists(destination):
        raise OnboardingError(
            f"runtime inventory already exists and was preserved: {destination}"
        )

    def inspect(data: bytes) -> RuntimeInspection:
        checks = runtime_profile_checks(data, package_root)
        library = next(
            Path(check.target) for check in checks if check.check_id == "renv_library"
        )
        result = inspect_runtime_profile_bytes(
            data,
            destination,
            checks=checks,
            environment=guarded_r_environment(package_root, library),
        )
        if not result.required_ready:
            raise RuntimeDiscoveryError(
                "Required runtime checks did not pass for reuse"
            )
        return result

    if os.path.lexists(seal_path):
        seal_data = load_runtime_seal(seal_path).data
    else:
        claim_path = runtime / "maintenance.lock"
        if os.path.lexists(claim_path):
            raise OnboardingError(
                f"Runtime maintenance claim is unresolved: {claim_path}"
            )
        ownership = None
        payload = f"emrys-runtime-seal:{uuid.uuid4().hex}\n".encode("ascii")
        if execute:
            project_runtime_directory(source)
            ownership = acquire_lock(
                claim_path, payload, OnboardingError, retain_on_failure=True
            )
        # Failed or interrupted preparation/publication deliberately retains the claim.
        data, _checks = load_runtime_profile_contract(
            runtime / "runtime.tsv", package_root
        )
        choices = runtime_profile_choices(data)
        choices["python"] = Path(sys.executable)
        candidate = inspect(runtime_profile_bytes(choices))
        seal_data = runtime_seal_bytes(candidate, seal_path)
        reference = shared_runtime_profile_bytes(
            seal_path, seal_data, Path(sys.executable)
        )
        if not execute:
            return replace(
                candidate,
                profile_bytes=reference,
                profile_sha256=hashlib.sha256(reference).hexdigest(),
            )
        publish_exclusive(seal_path, seal_data, OnboardingError)
        assert ownership is not None
        release_lock(claim_path, ownership, payload, OnboardingError)
    reference = shared_runtime_profile_bytes(seal_path, seal_data, Path(sys.executable))
    inspection = inspect(reference)
    runtime_file_bindings(inspection)
    if execute:
        project_runtime_directory(borrower)
        publish_runtime_profile(inspection)
    return inspection


def configure_runtime_discovery_parser(parser: argparse.ArgumentParser) -> None:
    add_project_argument(parser)
    parser.add_argument(
        "--from-project",
        metavar="DONOR",
        help="Reuse a managed donor runtime; --execute permanently seals its native/R content before selection.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the admitted inventory; omission is a no-write discovery.",
    )
    parser.set_defaults(_command_parser=parser)


def _print_runtime_inventory(inspection: RuntimeInspection) -> None:
    print("EMRYS runtime inventory")
    print(f"  emrys: PASS ({__version__})")
    for observation in inspection.observations:
        print(
            f"  {observation.check.check_id}: {observation.status.upper()} "
            f"({observation.observed})"
        )


def discover_runtime_from_args(arguments: argparse.Namespace) -> int:
    """Discover, probe, and optionally admit the active Project runtime."""

    try:
        donor = getattr(arguments, "from_project", None)
        if donor is None:
            inspection = discover_runtime_profile(
                project=project_definition_path(arguments.project)
            )
        else:
            inspection = reuse_runtime_profile(
                project=project_definition_path(arguments.project),
                donor=project_definition_path(donor),
                execute=arguments.execute,
            )
            print(
                f"Donor seal: {project_definition_path(donor).parent / 'runtime/shared.json'}"
            )
            print("A donor seal is permanent and disables its managed runtime repair.")
        _print_runtime_inventory(inspection)
        print(f"Inventory: {inspection.profile_path}")
        if not inspection.required_ready:
            print("NOT READY: required runtime checks did not pass.")
            return 1
        if not arguments.execute:
            print("Dry-run complete; no files were written.")
            return 0
        if donor is None:
            publish_runtime_profile(inspection)
        print("Runtime inventory admitted.")
        return 0
    except RuntimeDiscoveryError as exc:
        print(f"NOT READY: {exc}", file=sys.stderr)
        return 1
    except (
        OSError,
        OnboardingError,
        RuntimeInspectionError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


__all__ = (
    "DESCRIPTION",
    "OnboardingError",
    "ProjectValidation",
    "RuntimeDiscoveryError",
    "add_project_argument",
    "configure_profile_create_parser",
    "configure_runtime_discovery_parser",
    "configure_manifest_init_parser",
    "configure_project_init_parser",
    "configure_validation_parser",
    "discover_runtime_from_args",
    "discover_runtime_profile",
    "reuse_runtime_profile",
    "init_manifests_from_args",
    "init_project_from_args",
    "project_runtime_directory",
    "profile_create_from_args",
    "project_definition_path",
    "publish_create_absent_tree",
    "publish_runtime_profile",
    "runtime_profile_path",
    "validate_from_args",
    "validate_project",
    "validate_project_admission",
)
