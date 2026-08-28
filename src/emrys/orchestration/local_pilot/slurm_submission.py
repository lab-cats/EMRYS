"""Private Slurm transport for one grouped EMRYS Run-control command."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from emrys.orchestration.local_pilot.execution_profile import ExecutionProfile


DELEGATE_MARKER_ENV = "EMRYS_PRIVATE_SLURM_DELEGATE"
PROFILE_SHA256_ENV = "EMRYS_PRIVATE_SLURM_PROFILE_SHA256"
SUBMIT_UID_ENV = "EMRYS_PRIVATE_SLURM_SUBMIT_UID"
DELEGATE_MARKER = "emrys-slurm-delegate-v1"

_DELEGATE_ENV_PREFIX = "EMRYS_PRIVATE_SLURM_"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SlurmSubmissionError(RuntimeError):
    """One private Slurm submission could not be planned or completed."""


@dataclass(frozen=True, slots=True)
class SlurmSubmission:
    """Immutable transport plan for one scheduler submission."""

    argv: tuple[str, ...]
    batch_script: str = field(repr=False)
    environment: Mapping[str, str] = field(repr=False, compare=False)
    stdout_pattern: Path
    stderr_pattern: Path
    execution_profile_path: Path
    execution_profile_sha256: str


def _batch_script(
    *,
    command: tuple[str, ...],
    scratch_parent: Path,
    module_init: Path | None,
    modules: tuple[str, ...],
    profile_sha256: str,
    submitter_uid: int,
) -> str:
    if modules and module_init is None:
        raise SlurmSubmissionError("modules require an explicit module init file")

    module_lines: list[str] = []
    if module_init is not None:
        quoted_init = shlex.quote(str(module_init))
        module_lines.extend(
            (
                f"module_init={quoted_init}",
                '[[ -f "$module_init" && ! -L "$module_init" ]] || '
                'die "module init must be one real file"',
                "# shellcheck disable=SC1090",
                'source "$module_init"',
                'type module >/dev/null 2>&1 || die "module command is unavailable"',
                "module purge",
                *(f"module load {shlex.quote(module)}" for module in modules),
            )
        )

    quoted_scratch = shlex.quote(str(scratch_parent))
    quoted_command = shlex.join(command)
    return "\n".join(
        (
            "#!/bin/bash",
            "set -euo pipefail",
            "",
            "die() {",
            "    printf 'ERROR: %s\\n' \"$*\" >&2",
            "    exit 2",
            "}",
            "",
            '[[ -n "${SLURM_JOB_ID:-}" ]] || die "Slurm allocation is required"',
            f'[[ "${{{DELEGATE_MARKER_ENV}:-}}" == {shlex.quote(DELEGATE_MARKER)} ]] || '
            'die "private delegate marker is invalid"',
            f'[[ "${{{PROFILE_SHA256_ENV}:-}}" == {shlex.quote(profile_sha256)} ]] || '
            'die "execution-profile digest is invalid"',
            f'[[ "${{{SUBMIT_UID_ENV}:-}}" == {submitter_uid} ]] || '
            'die "submitter UID is invalid"',
            f'[[ "$(/usr/bin/id -u)" == "${{{SUBMIT_UID_ENV}}}" ]] || '
            'die "batch UID does not match the submitter"',
            "export PATH=/usr/bin:/bin",
            "umask 077",
            *module_lines,
            f"scratch_parent_input={quoted_scratch}",
            '[[ -d "$scratch_parent_input" && ! -L "$scratch_parent_input" && '
            '-w "$scratch_parent_input" && -x "$scratch_parent_input" ]] || '
            'die "scratch parent must be one real writable directory"',
            'scratch_parent="$(cd -P -- "$scratch_parent_input" && pwd -P)"',
            '[[ -n "$scratch_parent" && "$scratch_parent" != / ]] || '
            'die "scratch parent must not be the filesystem root"',
            'job_tmpdir="$(/usr/bin/mktemp -d '
            '"$scratch_parent/emrys-${SLURM_JOB_ID}.XXXXXX")" || '
            'die "could not create private scratch"',
            'case "$job_tmpdir" in',
            '    "$scratch_parent"/emrys-"$SLURM_JOB_ID".??????) ;;',
            '    *) die "private scratch escaped its parent" ;;',
            "esac",
            '[[ -d "$job_tmpdir" && ! -L "$job_tmpdir" ]] || '
            'die "private scratch is invalid"',
            '/bin/chmod 700 "$job_tmpdir"',
            "cleanup() {",
            '    /bin/rm -rf -- "$job_tmpdir"',
            "}",
            "trap cleanup EXIT",
            'export TMPDIR="$job_tmpdir"',
            quoted_command,
            "",
        )
    )


def plan_submission(
    profile: ExecutionProfile,
    *,
    emrys_argv: Sequence[str],
    log_dir: Path,
    sbatch: str = "sbatch",
    environment: Mapping[str, str] | None = None,
    submitter_uid: int | None = None,
) -> SlurmSubmission:
    """Plan one Slurm submission without writing or invoking the scheduler."""

    command = tuple(emrys_argv)
    if not command or any(not isinstance(argument, str) for argument in command):
        raise SlurmSubmissionError("emrys_argv must be a nonempty string sequence")
    if not sbatch:
        raise SlurmSubmissionError("sbatch must be nonempty")
    uid = os.getuid() if submitter_uid is None else submitter_uid
    if isinstance(uid, bool) or not isinstance(uid, int) or uid < 0:
        raise SlurmSubmissionError("submitter_uid must be a nonnegative integer")

    profile_sha256 = profile.sha256
    if not isinstance(profile_sha256, str) or not _SHA256.fullmatch(profile_sha256):
        raise SlurmSubmissionError("execution-profile SHA-256 is invalid")
    profile_path = Path(profile.source_path)
    placement = profile.placement

    stdout_pattern = Path(log_dir) / "emrys-local-pilot-%j.out"
    stderr_pattern = Path(log_dir) / "emrys-local-pilot-%j.err"
    exports = (
        f"{DELEGATE_MARKER_ENV}={DELEGATE_MARKER}",
        f"{PROFILE_SHA256_ENV}={profile_sha256}",
        f"{SUBMIT_UID_ENV}={uid}",
    )
    argv = [sbatch, "--parsable"]
    if placement.account is not None:
        argv.append(f"--account={placement.account}")
    if placement.partition is not None:
        argv.append(f"--partition={placement.partition}")
    if placement.qos is not None:
        argv.append(f"--qos={placement.qos}")
    argv.extend(
        (
            "--nodes=1",
            "--ntasks=1",
            f"--cpus-per-task={placement.cpus_per_task}",
        )
    )
    if placement.request_memory:
        argv.append(f"--mem={placement.memory_mb}M")
    if placement.exclusive:
        argv.append("--exclusive")
    if placement.nodelist is not None:
        argv.append(f"--nodelist={placement.nodelist}")
    argv.extend(
        (
            f"--time={placement.time}",
            "--job-name=emrys-local-pilot",
            f"--output={stdout_pattern}",
            f"--error={stderr_pattern}",
            "--export=" + ",".join(exports),
        )
    )

    source_environment = os.environ if environment is None else environment
    scrubbed_environment = MappingProxyType(
        {
            name: value
            for name, value in source_environment.items()
            if not name.startswith("SBATCH_")
            and not name.startswith(_DELEGATE_ENV_PREFIX)
        }
    )
    script = _batch_script(
        command=command,
        scratch_parent=Path(placement.scratch_parent),
        module_init=(
            None if placement.module_init is None else Path(placement.module_init)
        ),
        modules=tuple(placement.modules),
        profile_sha256=profile_sha256,
        submitter_uid=uid,
    )
    return SlurmSubmission(
        argv=tuple(argv),
        batch_script=script,
        environment=scrubbed_environment,
        stdout_pattern=stdout_pattern,
        stderr_pattern=stderr_pattern,
        execution_profile_path=profile_path,
        execution_profile_sha256=profile_sha256,
    )


def submit(submission: SlurmSubmission) -> str:
    """Submit one planned script in one subprocess call and return its job ID."""

    try:
        completed = subprocess.run(
            submission.argv,
            input=submission.batch_script,
            env=dict(submission.environment),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise SlurmSubmissionError("could not execute sbatch") from exc
    if completed.returncode != 0:
        raise SlurmSubmissionError(f"sbatch failed with exit {completed.returncode}")

    lines = completed.stdout.splitlines()
    if len(lines) != 1:
        raise SlurmSubmissionError("sbatch did not return one parsable job ID")
    fields = lines[0].split(";")
    if (
        len(fields) not in {1, 2}
        or not fields[0].isdigit()
        or (len(fields) == 2 and not fields[1])
    ):
        raise SlurmSubmissionError("sbatch returned an invalid job ID")
    return fields[0]


__all__ = (
    "DELEGATE_MARKER",
    "DELEGATE_MARKER_ENV",
    "PROFILE_SHA256_ENV",
    "SUBMIT_UID_ENV",
    "SlurmSubmission",
    "SlurmSubmissionError",
    "plan_submission",
    "submit",
)
