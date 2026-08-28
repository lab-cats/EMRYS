"""Create and validate explicit local-pilot onboarding inputs."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shlex
import stat
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.references.contigs import (
    ReferenceContigError,
    parse_fasta_lines,
)
from emrys.orchestration.local_pilot.normalization import (
    NormalizationBundle,
    normalize_request,
)
from emrys.orchestration.local_pilot.launcher_config import BATCH_MARKER
from emrys.stages.gtf_to_bed12 import converter as gtf_converter

DESCRIPTION = (
    "Validate one complete local-pilot request before probing the scientific "
    "runtime. This command reads declared inputs, checks reference compatibility, "
    "and writes nothing."
)
PROFILE_RELATIVE_PATH = Path("workflow/contracts/local_cmh_v2.json")
STARTER_MANIFEST = "starter-set.manifest.tsv"
SLURM_WRAPPER = "run-in-slurm.sh"
LAUNCHER_CONFIG = "emrys.launcher.yaml"
RUNTIME_HEADER = (
    "check_id",
    "check_type",
    "runtime_context",
    "required",
    "target",
    "probe_args",
    "expected",
    "description",
)
PATH_TOOL_COMMANDS = {
    "bash": "bash",
    "star": "STAR",
    "samtools": "samtools",
    "gatk": "gatk",
    "bcftools": "bcftools",
    "infer_experiment": "infer_experiment.py",
    "gunzip": "gunzip",
}


class OnboardingError(RuntimeError):
    """An onboarding input or publication boundary is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class RequestValidation:
    """Read-only normalized request and compatibility evidence."""

    normalized: NormalizationBundle
    fasta_contigs: tuple[tuple[str, int], ...]
    transcript_count: int
    sample_count: int
    pair_count: int
    partition_count: int
    gtf_warnings: tuple[str, ...]


def source_root() -> Path:
    """Return the checkout root owning the selected package."""

    return Path(__file__).resolve().parents[4]


def _absolute(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise OnboardingError(f"path must be absolute: {path}")
    return Path(os.path.abspath(path))


def _require_external_absent_output(value: str | Path, root: Path) -> Path:
    output = _absolute(value)
    if os.path.lexists(output):
        raise OnboardingError(f"output directory must be absent: {output}")
    if output == root or output in root.parents or root in output.parents:
        raise OnboardingError(
            f"output directory must not overlap the EMRYS checkout: {output}"
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
    expected_directories = {
        parent.as_posix()
        for name in expected
        for parent in Path(name).parents
        if parent != Path(".")
    }
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
        state = path.lstat()
        if stat.S_IMODE(state.st_mode) != expected_mode:
            raise OnboardingError(
                f"published member mode changed: {relative}: "
                f"{stat.S_IMODE(state.st_mode):04o}"
            )
        data = path.read_bytes()
        if data != expected_bytes or state.st_size != len(expected_bytes):
            raise OnboardingError(f"published member bytes changed: {relative}")


def publish_create_absent_tree(
    output: Path,
    members: Mapping[str, tuple[bytes, int]],
    *,
    completion_name: str,
    completion_bytes: bytes,
    before_completion: Callable[[Path], None] | None = None,
) -> None:
    """Publish one reserved tree with its completion member written last."""

    for name in (*members, completion_name):
        relative = Path(name)
        if (
            not name
            or any(character in name for character in ("\x00", "\r", "\n", "\\"))
            or relative.is_absolute()
            or name != relative.as_posix()
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise OnboardingError(f"unsafe publication member path: {name!r}")
    if completion_name in members:
        raise OnboardingError(f"completion member is duplicated: {completion_name}")
    all_names = (*members, completion_name)
    directories = sorted(
        {
            parent
            for name in all_names
            for parent in Path(name).parents
            if parent != Path(".")
        },
        key=lambda path: (len(path.parts), path.as_posix()),
    )
    if any(directory.as_posix() in all_names for directory in directories):
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
        )
    except BaseException as exc:
        raise OnboardingError(
            "publication did not complete; preserve and inspect the partial "
            "create-absent directory. The completion member may be absent or "
            "present-but-invalid; its presence alone is not completion proof: "
            f"{output}: {exc}"
        ) from exc


def _slurm_wrapper_bytes(source_checkout: Path, python_executable: Path) -> bytes:
    template = b"""#!/bin/bash
set -euo pipefail

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

require_export_value() {
    local name="$1"
    declare -p "$name" >/dev/null 2>&1 || \
        die "$name must be explicitly set"
    [[ "${!name}" != *$'\n'* && "${!name}" != *','* ]] || \
        die "$name contains a newline or comma"
}

require_value() {
    local name="$1"
    require_export_value "$name"
    [[ -n "${!name}" ]] || die "$name must be nonempty"
}

observe_live_identity() {
    [[ -x /usr/bin/id ]] || die "/usr/bin/id is unavailable"
    live_uid="$(/usr/bin/id -u)" || die "could not resolve the live numeric UID"
    live_user="$(/usr/bin/id -un)" || die "could not resolve the live user name"
    [[ "$live_uid" =~ ^[0-9]+$ ]] || die "live numeric UID is invalid"
    [[ "$live_user" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || \
        die "live user name is unsafe for Slurm export"
}

validate_module_settings() {
    case "$EMRYS_MODULE_MODE" in
        exact)
            require_value EMRYS_MODULE_INIT
            require_value EMRYS_MODULES
            ;;
        none)
            [[ -z "$EMRYS_MODULE_INIT" && -z "$EMRYS_MODULES" ]] || \
                die "EMRYS_MODULE_INIT and EMRYS_MODULES must be empty when EMRYS_MODULE_MODE=none"
            ;;
        *)
            die "EMRYS_MODULE_MODE must be exact or none"
            ;;
    esac
}

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
    [[ "${1:-}" != __EMRYS_BATCH_MARKER__ ]] || \
        die "internal batch marker requires a Slurm allocation"
    EMRYS_LAUNCHER_SOURCE_CHECKOUT=__EMRYS_LAUNCHER_SOURCE_CHECKOUT__
    EMRYS_LAUNCHER_PYTHON=__EMRYS_LAUNCHER_PYTHON__
    export EMRYS_LAUNCHER_SOURCE_CHECKOUT EMRYS_LAUNCHER_PYTHON
    exec __EMRYS_LAUNCHER_PYTHON__ -X pycache_prefix=/dev/null -I \
        -m emrys.orchestration.local_pilot.launcher_config "$0" "$@"
fi

[[ "$#" -eq 1 && "$1" == __EMRYS_BATCH_MARKER__ ]] || \
    die "batch mode requires the exact internal batch marker"
shift

for name in EMRYS_SUBMIT_UID EMRYS_SUBMIT_USER USER LOGNAME \
    EMRYS_SOURCE_CHECKOUT EMRYS_PYTHON EMRYS_REQUEST EMRYS_WORKSPACE \
    EMRYS_RUNTIME_PROFILE EMRYS_MODULE_MODE EMRYS_SCRATCH_PARENT \
    EMRYS_EXECUTE; do
    require_value "$name"
done
for name in EMRYS_MODULE_INIT EMRYS_MODULES; do
    require_export_value "$name"
done
[[ "$EMRYS_EXECUTE" == 0 || "$EMRYS_EXECUTE" == 1 ]] || die "EMRYS_EXECUTE must be 0 or 1"
[[ "$EMRYS_SUBMIT_UID" =~ ^[0-9]+$ ]] || die "EMRYS_SUBMIT_UID must be numeric"
[[ "$EMRYS_SUBMIT_USER" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || \
    die "EMRYS_SUBMIT_USER is invalid"
observe_live_identity
[[ "$EMRYS_SUBMIT_UID" == "$live_uid" && \
    "$EMRYS_SUBMIT_USER" == "$live_user" && \
    "$USER" == "$live_user" && "$LOGNAME" == "$live_user" ]] || \
    die "batch identity does not match the admitted submitter"
readonly live_uid live_user
validate_module_settings
if [[ "$EMRYS_MODULE_MODE" == exact ]]; then
    [[ -f "$EMRYS_MODULE_INIT" && ! -L "$EMRYS_MODULE_INIT" ]] || \
        die "EMRYS_MODULE_INIT must be an explicit real file"
    # shellcheck disable=SC1090
    source "$EMRYS_MODULE_INIT"
    command -v module >/dev/null 2>&1 || die "module command is unavailable after EMRYS_MODULE_INIT"
    IFS=: read -r -a requested_modules <<< "$EMRYS_MODULES"
    (( ${#requested_modules[@]} > 0 )) || die "EMRYS_MODULES is empty"
    for module_name in "${requested_modules[@]}"; do
        [[ "$module_name" =~ ^[A-Za-z0-9][A-Za-z0-9._+/-]*$ ]] || \
            die "unsafe module identifier: $module_name"
        module load "$module_name"
    done
fi
[[ -d "$EMRYS_SOURCE_CHECKOUT" && ! -L "$EMRYS_SOURCE_CHECKOUT" ]] || \
    die "EMRYS_SOURCE_CHECKOUT must be an existing real directory"
[[ -x "$EMRYS_PYTHON" ]] || die "EMRYS_PYTHON must be an explicit executable"
[[ -d "$EMRYS_SCRATCH_PARENT" && ! -L "$EMRYS_SCRATCH_PARENT" && \
    -w "$EMRYS_SCRATCH_PARENT" && -x "$EMRYS_SCRATCH_PARENT" ]] || \
    die "EMRYS_SCRATCH_PARENT must be an existing real writable directory"
command -v mktemp >/dev/null 2>&1 || die "mktemp is unavailable in the allocation"
command -v df >/dev/null 2>&1 || die "df is unavailable in the allocation"
scratch_parent="$(cd -P "$EMRYS_SCRATCH_PARENT" && pwd)"
job_tmpdir="$(mktemp -d "$scratch_parent/emrys-${SLURM_JOB_ID}.XXXXXX")" || \
    die "unable to create private compute scratch directory"
job_tmpdir_name="${job_tmpdir##*/}"
job_tmpdir_suffix="${job_tmpdir_name#"emrys-${SLURM_JOB_ID}."}"
canonical_job_tmpdir="$(cd -P "$job_tmpdir" && pwd)" || \
    die "unable to canonicalize private compute scratch directory"
[[ "${job_tmpdir%/*}" == "$scratch_parent" && \
    "$canonical_job_tmpdir" == "$job_tmpdir" && \
    "$job_tmpdir_name" == "emrys-${SLURM_JOB_ID}.$job_tmpdir_suffix" && \
    "$job_tmpdir_suffix" =~ ^[A-Za-z0-9]{6}$ ]] || \
    die "mktemp returned an unsafe compute scratch directory"
readonly scratch_parent job_tmpdir
cleanup_job_tmpdir() {
    if [[ "${OSTYPE:-}" == linux* ]]; then
        rm -rf --one-file-system -- "$job_tmpdir"
    else
        rm -rf -- "$job_tmpdir"
    fi
}
trap cleanup_job_tmpdir EXIT
chmod 700 "$job_tmpdir"
export TMPDIR="$job_tmpdir"
printf 'EMRYS_SCRATCH_PARENT=%s\n' "$scratch_parent"
printf 'TMPDIR=%s\n' "$TMPDIR"
printf 'TMPDIR filesystem and capacity:\n'
df -PT "$TMPDIR"
cd "$EMRYS_SOURCE_CHECKOUT"
"$EMRYS_PYTHON" -X pycache_prefix=/dev/null -I -m emrys validate \
    local-pilot-request --request "$EMRYS_REQUEST"
run_arguments=(
    --request "$EMRYS_REQUEST"
    --workspace "$EMRYS_WORKSPACE"
    --runtime-profile "$EMRYS_RUNTIME_PROFILE"
)
if [[ "$EMRYS_EXECUTE" == 1 ]]; then
    run_arguments+=(--execute)
fi
"$EMRYS_PYTHON" -X pycache_prefix=/dev/null -I -m emrys run "${run_arguments[@]}"
"""
    source_value = shlex.quote(str(source_checkout)).encode("utf-8")
    python_value = shlex.quote(str(python_executable)).encode("utf-8")
    marker_value = shlex.quote(BATCH_MARKER).encode("utf-8")
    return (
        template.replace(b"__EMRYS_LAUNCHER_SOURCE_CHECKOUT__", source_value)
        .replace(b"__EMRYS_LAUNCHER_PYTHON__", python_value)
        .replace(b"__EMRYS_BATCH_MARKER__", marker_value)
    )


def starter_members(
    *,
    root: Path | None = None,
    python_executable: Path | None = None,
) -> dict[str, tuple[bytes, int]]:
    """Render one matched starter set from the tracked policy templates."""

    requested_checkout = source_root() if root is None else root
    requested_python = (
        Path(sys.executable) if python_executable is None else python_executable
    )
    try:
        checkout = requested_checkout.resolve(strict=True)
    except OSError as exc:
        raise OnboardingError(
            f"source checkout must resolve to an existing directory: "
            f"{requested_checkout}: {exc}"
        ) from exc
    if not checkout.is_dir():
        raise OnboardingError(f"source checkout must be a directory: {checkout}")
    selected_python = _absolute(requested_python)
    if selected_python.parent == Path("/"):
        raise OnboardingError(
            "selected Python parent must not be the filesystem root"
        )
    if ":" in str(selected_python.parent):
        raise OnboardingError(
            "selected Python parent is unsafe for the sealed PATH"
        )
    try:
        parent_state = selected_python.parent.lstat()
        parent_resolved = selected_python.parent.resolve(strict=True)
        before = selected_python.lstat()
        link_before = (
            os.readlink(selected_python) if stat.S_ISLNK(before.st_mode) else ""
        )
        target = selected_python.resolve(strict=True)
        target_before = target.stat(follow_symlinks=False)
        after = selected_python.lstat()
        link_after = (
            os.readlink(selected_python) if stat.S_ISLNK(after.st_mode) else ""
        )
        confirmed_target = selected_python.resolve(strict=True)
        target_after = confirmed_target.stat(follow_symlinks=False)
    except OSError as exc:
        raise OnboardingError(
            f"selected Python must resolve to an executable file: "
            f"{selected_python}: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(parent_state.st_mode)
        or not stat.S_ISDIR(parent_state.st_mode)
        or parent_resolved != selected_python.parent
        or (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns)
        or link_before != link_after
        or confirmed_target != target
        or (target_before.st_dev, target_before.st_ino, target_before.st_mode)
        != (target_after.st_dev, target_after.st_ino, target_after.st_mode)
        or not stat.S_ISREG(target_after.st_mode)
        or not os.access(selected_python, os.X_OK)
    ):
        raise OnboardingError(
            "selected Python launcher identity is invalid or changed: "
            f"{selected_python}"
        )
    for label, path in (
        ("source checkout", checkout),
        ("selected Python", selected_python),
    ):
        if any(character in str(path) for character in ("\n", "\r", ",")):
            raise OnboardingError(f"{label} path contains an unsafe character")
    request = (checkout / "configs/local_pilot_request.example.yaml").read_text(
        encoding="utf-8"
    )
    request = request.replace(
        "sample_manifest: local_pilot_samples.example.tsv",
        "sample_manifest: samples.tsv",
    ).replace(
        "partition_manifest: local_pilot_partitions.example.tsv",
        "partition_manifest: partitions.tsv",
    )
    resource_config = (
        checkout / "configs/local_pilot_resources.example.yaml"
    ).read_bytes()
    launcher_config = (
        checkout / "configs/local_pilot_launcher.example.yaml"
    ).read_bytes()
    runtime = (checkout / "configs/local_pilot_runtime.example.tsv").read_text(
        encoding="utf-8"
    )
    runtime = runtime.replace(
        "/absolute/path/to/emrys/.venv/bin/python", str(selected_python)
    ).replace("/absolute/path/to/emrys", str(checkout))
    return {
        "request.yaml": (request.encode("utf-8"), 0o644),
        LAUNCHER_CONFIG: (launcher_config, 0o644),
        "emrys.resources.yaml": (resource_config, 0o644),
        "samples.tsv": (
            (checkout / "configs/local_pilot_samples.example.tsv").read_bytes(),
            0o644,
        ),
        "partitions.tsv": (
            (checkout / "configs/local_pilot_partitions.example.tsv").read_bytes(),
            0o644,
        ),
        "runtime.tsv": (runtime.encode("utf-8"), 0o644),
        SLURM_WRAPPER: (
            _slurm_wrapper_bytes(checkout, selected_python),
            0o755,
        ),
    }


def _manifest_bytes(members: Mapping[str, tuple[bytes, int]]) -> bytes:
    lines = ["path\tmode\tsize_bytes\tsha256"]
    for name, (data, mode) in sorted(members.items()):
        lines.append(
            f"{name}\t{mode:04o}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def configure_init_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Absolute absent directory to receive the matched starter set.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create the starter set. Default is a no-write plan.",
    )
    parser.set_defaults(_command_parser=parser)


def init_from_args(arguments: argparse.Namespace) -> int:
    """Plan or create one matched, create-absent local-pilot starter set."""

    try:
        root = source_root()
        output = _require_external_absent_output(arguments.output_dir, root)
        members = starter_members(root=root)
        print(f"Output directory: {output}")
        print("Members: " + ", ".join((*sorted(members), STARTER_MANIFEST)))
        print("Publication policy: create-absent; no file will be replaced or adopted.")
        if not arguments.execute:
            print("Dry-run complete; no files were written.")
            return 0
        publish_create_absent_tree(
            output,
            members,
            completion_name=STARTER_MANIFEST,
            completion_bytes=_manifest_bytes(members),
        )
        print(f"Published matched local-pilot starter set: {output}")
        return 0
    except (OSError, OnboardingError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _sha256_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _require_snapshot(snapshot: Mapping[str, object], label: str) -> Path:
    path = Path(str(snapshot["path"]))
    try:
        state = path.lstat()
    except OSError as exc:
        raise OnboardingError(f"could not re-admit {label}: {path}: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode):
        raise OnboardingError(f"{label} must remain a real regular file: {path}")
    digest, size = _sha256_and_size(path)
    if digest != snapshot["sha256"] or size != snapshot["size_bytes"]:
        raise OnboardingError(f"{label} changed after request normalization: {path}")
    return path


def _region_parts(value: str) -> Sequence[str]:
    regions = value.split(",")
    if any(not region for region in regions):
        raise OnboardingError(f"region selector contains an empty region: {value}")
    return regions


def _validate_region_selector(value: str, lengths: Mapping[str, int]) -> None:
    for region in _region_parts(value):
        contig, separator, coordinates = region.partition(":")
        if contig not in lengths:
            raise OnboardingError(
                f"partition region contig is absent from the reference FASTA: {contig}"
            )
        if not separator:
            continue
        match = re.fullmatch(r"([0-9]+)(?:-([0-9]*))?", coordinates)
        if match is None:
            raise OnboardingError(f"partition region has invalid coordinates: {region}")
        start = int(match.group(1))
        end_text = match.group(2)
        end = (
            start
            if end_text is None
            else lengths[contig]
            if end_text == ""
            else int(end_text)
        )
        if start < 1 or end < start or end > lengths[contig]:
            raise OnboardingError(
                f"partition region is outside FASTA bounds: {region} "
                f"(length {lengths[contig]})"
            )


def _regions_lines(path: Path) -> Iterator[str]:
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
                yield from handle
        else:
            with path.open(encoding="utf-8", newline="") as handle:
                yield from handle
    except (OSError, UnicodeError) as exc:
        raise OnboardingError(
            f"regions file is not valid UTF-8 text: {path}: {exc}"
        ) from exc


def _validate_regions_file(path: Path, lengths: Mapping[str, int]) -> None:
    uncompressed_name = path.name.removesuffix(".gz")
    mode = (
        "bed"
        if uncompressed_name.endswith(".bed")
        else "vcf"
        if uncompressed_name.endswith(".vcf")
        else "tab"
    )
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


def validate_local_pilot_request(
    request: str | Path,
    *,
    root: Path | None = None,
) -> RequestValidation:
    """Normalize and compatibility-check one request without runtime probes."""

    checkout = source_root() if root is None else root
    normalized = normalize_request(request, checkout / PROFILE_RELATIVE_PATH)
    source = normalized.projection_source
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
        transcripts = gtf_converter.normalize_gtf(
            gtf,
            "exon",
            "transcript_id",
            "gene_id",
            warnings.append,
        )
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
    for partition in source["partitions"]["rows"]:
        if partition["selector_type"] == "region":
            _validate_region_selector(str(partition["selector_value"]), lengths)
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
    _require_snapshot(fasta_snapshot, "reference FASTA")
    _require_snapshot(gtf_snapshot, "reference GTF")
    samples = source["samples"]["rows"]
    control = source["analysis"]["policy"]["control_condition"]
    pair_count = len(
        {row["replicate"] for row in samples if row["condition"] == control}
    )
    return RequestValidation(
        normalized=normalized,
        fasta_contigs=fasta_contigs,
        transcript_count=len(transcripts),
        sample_count=len(samples),
        pair_count=pair_count,
        partition_count=len(source["partitions"]["rows"]),
        gtf_warnings=tuple(warnings),
    )


def configure_validation_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--request", required=True, type=Path)
    parser.set_defaults(_command_parser=parser)


def validate_from_args(arguments: argparse.Namespace) -> int:
    try:
        result = validate_local_pilot_request(arguments.request)
    except (
        OSError,
        OnboardingError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    normalized = result.normalized
    reference = normalized.projection_source["reference"]
    print("Local-pilot request validation: PASS")
    print(f"  Request: {normalized.request_path}")
    print(f"  Request SHA-256: {normalized.request_sha256}")
    print(f"  Analysis revision: {normalized.analysis_revision.analysis_revision_id}")
    print(f"  Samples / paired strata: {result.sample_count} / {result.pair_count}")
    print(f"  Partitions: {result.partition_count}")
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


def _admit_explicit_file(
    value: str | Path,
    label: str,
    *,
    executable: bool = False,
) -> Path:
    path = _absolute(value)
    try:
        path.lstat()
        resolved = path.resolve(strict=True)
        state = resolved.stat()
    except OSError as exc:
        raise OnboardingError(f"could not inspect {label}: {path}: {exc}") from exc
    if not stat.S_ISREG(state.st_mode):
        raise OnboardingError(f"{label} must resolve to a real file: {path}")
    if state.st_size == 0 or not os.access(path, os.R_OK):
        raise OnboardingError(f"{label} must be nonempty and readable: {path}")
    if executable and not os.access(path, os.X_OK):
        raise OnboardingError(f"{label} must be executable: {path}")
    return resolved


def _admit_explicit_directory(value: str | Path, label: str) -> Path:
    path = _absolute(value)
    try:
        path.lstat()
        resolved = path.resolve(strict=True)
        state = resolved.stat()
    except OSError as exc:
        raise OnboardingError(f"could not inspect {label}: {path}: {exc}") from exc
    if not stat.S_ISDIR(state.st_mode):
        raise OnboardingError(f"{label} must resolve to a real directory: {path}")
    if not os.access(path, os.R_OK | os.X_OK):
        raise OnboardingError(f"{label} must be readable and searchable: {path}")
    return resolved


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
    explicit: Path | None,
    environment: Mapping[str, str],
) -> Path:
    if explicit is not None:
        return _admit_explicit_file(explicit, check_id, executable=True)
    command = PATH_TOOL_COMMANDS[check_id]
    candidates = _path_candidates(command, environment)
    if not candidates:
        raise OnboardingError(
            f"{check_id}: {command} is absent from PATH; supply --{check_id.replace('_', '-')}"
        )
    if len(candidates) != 1:
        raise OnboardingError(
            f"{check_id}: PATH resolves {command} to multiple executables: "
            + ", ".join(str(path) for path in candidates)
            + f"; supply --{check_id.replace('_', '-')}"
        )
    return candidates[0]


def render_runtime_profile(
    *,
    java: Path,
    picard_jar: Path,
    rscript: Path,
    renv_library: Path,
    explicit_tools: Mapping[str, Path | None],
    environment: Mapping[str, str] | None = None,
    root: Path | None = None,
    python_executable: Path | None = None,
) -> bytes:
    """Render a fixed-policy profile without probing or writing tools."""

    checkout = source_root() if root is None else root
    selected_environment = os.environ if environment is None else environment
    selected_python = (
        Path(sys.executable) if python_executable is None else python_executable
    )
    if not selected_python.is_absolute():
        raise OnboardingError(f"workflow Python must be absolute: {selected_python}")
    java_path = _admit_explicit_file(java, "Java launcher", executable=True)
    jar_path = _admit_explicit_file(picard_jar, "Picard jar")
    rscript_path = _admit_explicit_file(rscript, "Rscript", executable=True)
    library_path = _admit_explicit_directory(renv_library, "renv library")
    selected = {
        check_id: _selected_tool(
            check_id,
            explicit_tools.get(check_id),
            selected_environment,
        )
        for check_id in PATH_TOOL_COMMANDS
    }
    template = checkout / "configs/local_pilot_runtime.example.tsv"
    with template.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if tuple(reader.fieldnames or ()) != RUNTIME_HEADER:
            raise OnboardingError(
                f"tracked runtime template header is invalid: {template}"
            )
        rows = list(reader)
    if {row["check_id"] for row in rows} != {
        *PATH_TOOL_COMMANDS,
        "python",
        "snakemake",
        "sha256_python",
        "java",
        "picard",
        "picard_jar",
        "rscript",
        "renv_project",
        "renv_library",
        "r_variant_annotation",
        "r_genomic_ranges",
        "r_iranges",
        "r_biostrings",
        "r_rsamtools",
        "r_s4vectors",
        "r_summarized_experiment",
        "r_genome_info_db",
        "r_bioc_generics",
        "r_rtracklayer",
    }:
        raise OnboardingError("tracked runtime template roster is unexpected")
    for row in rows:
        check_id = row["check_id"]
        if check_id in selected:
            row["target"] = str(selected[check_id])
        elif check_id in {"python", "snakemake", "sha256_python"}:
            row["target"] = str(selected_python)
        elif check_id == "java":
            row["target"] = str(java_path)
        elif check_id == "picard":
            row["target"] = str(java_path)
            row["probe_args"] = json.dumps(
                ["-jar", str(jar_path), "MarkDuplicates", "--version"],
                separators=(",", ":"),
            )
        elif check_id == "picard_jar":
            row["target"] = str(jar_path)
        elif check_id == "rscript":
            row["target"] = str(rscript_path)
        elif check_id == "renv_project":
            row["target"] = str(checkout)
        elif check_id == "renv_library":
            row["target"] = str(library_path)
        elif check_id.startswith("r_"):
            row["probe_args"] = json.dumps([str(rscript_path)], separators=(",", ":"))
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=RUNTIME_HEADER,
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def configure_runtime_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--java", required=True, type=Path)
    parser.add_argument("--picard-jar", required=True, type=Path)
    parser.add_argument("--rscript", required=True, type=Path)
    parser.add_argument("--renv-library", required=True, type=Path)
    for check_id, command in PATH_TOOL_COMMANDS.items():
        parser.add_argument(
            f"--{check_id.replace('_', '-')}",
            type=Path,
            help=f"Explicit {command} path; omit only for unambiguous PATH resolution.",
        )
    parser.set_defaults(_command_parser=parser)


def prepare_runtime_from_args(arguments: argparse.Namespace) -> int:
    """Print one complete runtime profile to stdout without writing or probing."""

    try:
        explicit = {
            check_id: getattr(arguments, check_id) for check_id in PATH_TOOL_COMMANDS
        }
        payload = render_runtime_profile(
            java=arguments.java,
            picard_jar=arguments.picard_jar,
            rscript=arguments.rscript,
            renv_library=arguments.renv_library,
            explicit_tools=explicit,
        )
    except (OSError, csv.Error, OnboardingError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(payload.decode("utf-8"))
    return 0


__all__ = (
    "DESCRIPTION",
    "OnboardingError",
    "RequestValidation",
    "configure_init_parser",
    "configure_runtime_parser",
    "configure_validation_parser",
    "init_from_args",
    "prepare_runtime_from_args",
    "publish_create_absent_tree",
    "render_runtime_profile",
    "starter_members",
    "validate_from_args",
    "validate_local_pilot_request",
)
