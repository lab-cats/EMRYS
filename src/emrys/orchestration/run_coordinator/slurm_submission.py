"""Private Slurm transport for one grouped EMRYS Run-control command."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from emrys.orchestration.run_coordinator.resource_policy import (
    is_canonical_slurm_job_id,
)

if TYPE_CHECKING:
    from emrys.orchestration.run_coordinator.execution_profile import (
        ExecutionProfile,
        SlurmPlacement,
    )


DELEGATE_MARKER_ENV = "EMRYS_PRIVATE_SLURM_DELEGATE"
PROFILE_SHA256_ENV = "EMRYS_PRIVATE_SLURM_PROFILE_SHA256"
SUBMIT_UID_ENV = "EMRYS_PRIVATE_SLURM_SUBMIT_UID"
DELEGATE_MARKER = "emrys-slurm-delegate-v1"

_DELEGATE_ENV_PREFIX = "EMRYS_PRIVATE_SLURM_"


class SlurmSubmissionError(RuntimeError):
    """One private Slurm submission could not be planned or completed."""


def delegate_binding() -> str | None:
    """Admit the shared private delegate context before loading its profile."""

    values = tuple(
        os.environ.get(name)
        for name in (DELEGATE_MARKER_ENV, PROFILE_SHA256_ENV, SUBMIT_UID_ENV)
    )
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise SlurmSubmissionError("Private Slurm delegate context is incomplete")
    if values[0] != DELEGATE_MARKER:
        raise SlurmSubmissionError("Private Slurm delegate marker is invalid")
    if values[2] != str(os.getuid()):
        raise SlurmSubmissionError(
            "Private Slurm delegate UID differs from the current process"
        )
    return values[1]


def delegate_job_id(profile: ExecutionProfile) -> str | None:
    """Re-admit the profile and allocation shared by every delegated command."""

    expected = delegate_binding()
    if expected is None:
        return None
    if profile.binding_sha256 != expected:
        raise SlurmSubmissionError("Execution-profile binding SHA-256 differs")
    if profile.placement.kind != "slurm":
        raise SlurmSubmissionError("A private Slurm delegate requires Slurm placement")
    job_id = os.environ.get("SLURM_JOB_ID")
    try:
        profile.attempt_placement(job_id)
    except ValueError as exc:
        raise SlurmSubmissionError(str(exc)) from exc
    return job_id


@dataclass(frozen=True, slots=True)
class SlurmSubmission:
    """Immutable transport plan for one scheduler submission."""

    argv: tuple[str, ...]
    batch_script: str = field(repr=False)
    environment: Mapping[str, str] = field(repr=False, compare=False)
    stdout_pattern: Path
    stderr_pattern: Path


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
            '    if [[ "$(/usr/bin/uname -s)" == Darwin ]]; then',
            '        /bin/rm -rfx -- "$job_tmpdir"',
            "    else",
            '        /bin/rm -rf --one-file-system -- "$job_tmpdir"',
            "    fi",
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

    profile_sha256 = profile.binding_sha256
    placement = profile.placement
    if getattr(placement, "kind", None) != "slurm":
        raise SlurmSubmissionError("scheduler submission requires Slurm placement")
    slurm_placement = cast("SlurmPlacement", placement)

    scheduler_log_dir = Path(log_dir)
    if "%" in os.fspath(scheduler_log_dir):
        raise SlurmSubmissionError("scheduler log directory must not contain '%'")
    stdout_pattern = scheduler_log_dir / "emrys-local-pilot-%j.out"
    stderr_pattern = scheduler_log_dir / "emrys-local-pilot-%j.err"
    argv = [sbatch, "--parsable"]
    if slurm_placement.account is not None:
        argv.append(f"--account={slurm_placement.account}")
    if slurm_placement.partition is not None:
        argv.append(f"--partition={slurm_placement.partition}")
    if slurm_placement.qos is not None:
        argv.append(f"--qos={slurm_placement.qos}")
    argv.extend(
        (
            "--nodes=1",
            "--ntasks=1",
            f"--cpus-per-task={slurm_placement.cpus_per_task}",
        )
    )
    if slurm_placement.memory_mb is not None:
        argv.append(f"--mem={slurm_placement.memory_mb}M")
    if slurm_placement.exclusive:
        argv.append("--exclusive")
    if slurm_placement.nodelist is not None:
        argv.append(f"--nodelist={slurm_placement.nodelist}")
    argv.extend(
        (
            f"--time={slurm_placement.time}",
            "--job-name=emrys-local-pilot",
            f"--output={stdout_pattern}",
            f"--error={stderr_pattern}",
            f"--export={DELEGATE_MARKER_ENV}={DELEGATE_MARKER},"
            f"{PROFILE_SHA256_ENV}={profile_sha256},"
            f"{SUBMIT_UID_ENV}={uid},LOGNAME,USER,LNAME,USERNAME",
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
        scratch_parent=Path(slurm_placement.scratch_parent),
        module_init=(
            None
            if slurm_placement.module_init is None
            else Path(slurm_placement.module_init)
        ),
        modules=tuple(slurm_placement.modules),
        profile_sha256=profile_sha256,
        submitter_uid=uid,
    )
    return SlurmSubmission(
        argv=tuple(argv),
        batch_script=script,
        environment=scrubbed_environment,
        stdout_pattern=stdout_pattern,
        stderr_pattern=stderr_pattern,
    )


def submit(
    submission: SlurmSubmission,
    *,
    wait_record: Path | None = None,
    record_path: Path | None = None,
    on_submitted: Callable[[str], None] | None = None,
) -> str:
    """Submit one planned script in one subprocess call and return its job ID."""

    if wait_record is not None and record_path is not None:
        raise SlurmSubmissionError("Select one submission record path")
    record = wait_record if wait_record is not None else record_path
    job_id = None
    operation = "invoke sbatch" if record is None else "prepare submission records"
    try:
        if record is None:
            completed = subprocess.run(
                submission.argv,
                input=submission.batch_script,
                env=dict(submission.environment),
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
            )
            stdout, stderr = completed.stdout, completed.stderr
            job_id = _submitted_job_id(stdout, stderr=stderr) if stdout else None
        else:
            error_record = record.with_suffix(".stderr")

            def private_opener(path: str, flags: int) -> int:
                return os.open(path, flags, 0o600)

            with (
                open(record, "xb+", opener=private_opener) as output,
                open(error_record, "xb+", opener=private_opener) as errors,
            ):
                operation = "synchronize submission directory"
                directory = os.open(
                    record.parent,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                )
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
                print(
                    f"Slurm submission records: {record}, {error_record}",
                    file=sys.stderr,
                )
                operation = "invoke sbatch"
                with subprocess.Popen(
                    (
                        *submission.argv,
                        *(("--wait",) if wait_record is not None else ()),
                    ),
                    env=dict(submission.environment),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE if wait_record is not None else output,
                    stderr=errors,
                ) as process:
                    operation = "communicate with sbatch"
                    try:
                        with suppress(BrokenPipeError):
                            process.stdin.write(submission.batch_script.encode())
                        with suppress(BrokenPipeError):
                            process.stdin.close()
                        if wait_record is not None:
                            first = process.stdout.readline()
                        else:
                            operation = "wait for sbatch"
                            process.wait()
                            output.seek(0)
                            first = output.read()
                            errors.seek(0)
                            stderr = errors.read(4096).decode("utf-8", "replace")
                        try:
                            job_id = (
                                _submitted_job_id(
                                    first.decode("utf-8", "replace"),
                                    stderr=stderr if wait_record is None else None,
                                )
                                if first
                                else None
                            )
                        finally:
                            operation = "retain submission records"
                            if wait_record is not None:
                                output.write(first)
                            output.flush()
                            os.fsync(output.fileno())
                        if job_id:
                            print(
                                f"Slurm job {job_id}; logs: {str(submission.stdout_pattern).replace('%j', job_id)}, {str(submission.stderr_pattern).replace('%j', job_id)}",
                                file=sys.stderr,
                                flush=True,
                            )
                            if on_submitted is not None:
                                on_submitted(job_id)
                        operation = "wait for sbatch"
                        rest = process.stdout.read() if wait_record is not None else b""
                        operation = "retain submission records"
                        output.write(rest)
                        output.flush()
                        os.fsync(output.fileno())
                        stdout = (first + rest).decode("utf-8", "replace")
                        completed = process
                        operation = "wait for sbatch"
                        process.wait()
                        operation = "retain submission records"
                        os.fsync(errors.fileno())
                        operation = "read submission records"
                        errors.seek(0)
                        stderr = errors.read(4096).decode("utf-8", "replace")
                    except BaseException:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        raise
    except OSError as exc:
        raise SlurmSubmissionError(
            f"Could not {operation}; job ID {job_id or 'unconfirmed'}: {str(exc)[:4096]!a}"
        ) from exc
    if completed.returncode != 0:
        subject = (
            f"accepted job {job_id}" if job_id else "submission (job ID unconfirmed)"
        )
        logs = tuple(
            str(path).replace("%j", job_id or "%j")
            for path in (submission.stdout_pattern, submission.stderr_pattern)
        )
        raise SlurmSubmissionError(
            f"Slurm {subject}: sbatch exited with {completed.returncode}; "
            f"logs={logs!a}; stderr excerpt={stderr[:4096]!a}"
        )
    return _submitted_job_id(stdout, job_id, stderr)


def _submitted_job_id(
    stdout: str, confirmed: str | None = None, stderr: str | None = None
) -> str:

    lines = stdout.splitlines()
    fields = lines[0].split(";") if len(lines) == 1 else ()
    if (
        len(fields) not in {1, 2}
        or not is_canonical_slurm_job_id(fields[0])
        or (len(fields) == 2 and not fields[1])
    ):
        detail = f"; stderr excerpt={stderr[:4096]!a}" if stderr is not None else ""
        raise SlurmSubmissionError(
            f"Invalid sbatch response; job ID {confirmed or 'unconfirmed'}; "
            f"stdout excerpt={stdout[:4096]!a}{detail}"
        )
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
