"""Private Slurm transport for one grouped EMRYS Run-control command."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from operator import attrgetter
from types import MappingProxyType
from typing import TYPE_CHECKING, BinaryIO, cast

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    directory_entries_with_identity,
    read_bytes_with_identity,
    require_executable,
    sha256_with_identity,
)
from emrys.orchestration.run_coordinator.resource_policy import (
    is_canonical_slurm_job_id,
)
from emrys.orchestration.run_coordinator import scheduler_observation

if TYPE_CHECKING:
    from emrys.orchestration.run_coordinator.execution_profile import (
        ExecutionProfile,
        SlurmPlacement,
    )


DELEGATE_MARKER_ENV = "EMRYS_PRIVATE_SLURM_DELEGATE"
PROFILE_SHA256_ENV = "EMRYS_PRIVATE_SLURM_PROFILE_SHA256"
SUBMIT_UID_ENV = "EMRYS_PRIVATE_SLURM_SUBMIT_UID"
REQUEST_TOKEN_ENV = "EMRYS_PRIVATE_SLURM_REQUEST_TOKEN"
DELEGATE_MARKER = "emrys-slurm-delegate-v1"

_DELEGATE_ENV_PREFIX = "EMRYS_PRIVATE_SLURM_"


class SlurmSubmissionError(RuntimeError):
    """One private Slurm submission could not be planned or completed."""


_REQUEST_CONTEXT_LIMIT = 64 * 1024


def _validate_request_token(request_token: object) -> None:
    if request_token is not None and (
        not isinstance(request_token, str)
        or not re.fullmatch(r"[0-9a-f]{32}", request_token)
    ):
        raise SlurmSubmissionError(
            "Submission request token must be 32 lowercase hex digits"
        )


def _scheduler_job_name(request_token: str | None) -> str:
    _validate_request_token(request_token)
    return "emrys-local-pilot" + (f"-{request_token}" if request_token else "")


def _scheduler_stream_patterns(
    log_dir: Path, request_token: str | None = None
) -> tuple[Path, Path]:
    if "%" in os.fspath(log_dir):
        raise SlurmSubmissionError("scheduler log directory must not contain '%'")
    stem = _scheduler_job_name(request_token)
    return log_dir / f"{stem}-%j.out", log_dir / f"{stem}-%j.err"


def validate_request_context(
    context: Mapping[str, object], project: Path, request_root: Path | None = None
) -> dict[str, object]:
    """Admit legacy diagnostics or request-specific paths through one boundary."""
    fields = {
        "schema_version",
        "created_at",
        "submitter_uid",
        "command",
        "project",
        "requested_run",
        "analysis",
        "application_log_root",
        "profile_binding_sha256",
        "emrys_argv",
        "scheduler_stdout_pattern",
        "scheduler_stderr_pattern",
    }
    if context.get("schema_version") == "emrys.submission-request.v3":
        fields.add("scheduler_job_name")
    if set(context) != fields:
        raise SlurmSubmissionError("Submission request context fields differ")
    if (
        context["schema_version"]
        not in (
            "emrys.submission-request.v1",
            "emrys.submission-request.v2",
            "emrys.submission-request.v3",
        )
        or type(context["submitter_uid"]) is not int
        or context["submitter_uid"] != os.getuid()
        or context["project"] != str(project)
        or context["command"] not in ("run", "resume", "report")
    ):
        raise SlurmSubmissionError(
            "Submission request version, UID, Project or command differs"
        )
    for name in ("project", "application_log_root"):
        value = context[name]
        if (
            not isinstance(value, str)
            or not value
            or "\0" in value
            or not Path(value).is_absolute()
            or os.path.abspath(value) != value
        ):
            raise SlurmSubmissionError(
                f"Submission {name} must be an absolute normalized path"
            )
    created = context["created_at"]
    try:
        if (
            not isinstance(created, str)
            or datetime.fromisoformat(created).tzinfo != UTC
        ):
            raise ValueError("UTC timestamp required")
    except ValueError as exc:
        raise SlurmSubmissionError(
            "Submission creation time is not a UTC timestamp"
        ) from exc
    digest = context["profile_binding_sha256"]
    requested = context["requested_run"]
    analysis = context["analysis"]
    argv = context["emrys_argv"]
    if (
        not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        or (context["command"] == "run" and requested is not None)
        or (
            context["command"] != "run"
            and (
                not isinstance(requested, str)
                or not re.fullmatch(r"run-[0-9a-f]{64}", requested)
            )
        )
        or (analysis is not None and not isinstance(analysis, str))
        or not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) or "\0" in item for item in argv)
    ):
        raise SlurmSubmissionError(
            "Submission Run, analysis, profile binding or argv is malformed"
        )
    token = None
    if context["schema_version"] != "emrys.submission-request.v1":
        if (
            request_root is None
            or request_root.parent != project.parent / "logs"
            or not re.fullmatch(r"submission-[0-9a-f]{32}", request_root.name)
        ):
            raise SlurmSubmissionError(
                "Submission request root differs from the Project"
            )
        token = request_root.name.removeprefix("submission-")
    if context["schema_version"] == "emrys.submission-request.v3" and context[
        "scheduler_job_name"
    ] != _scheduler_job_name(token):
        raise SlurmSubmissionError("Submission scheduler name differs from its token")
    for stream, expected in zip(
        ("stdout", "stderr"),
        _scheduler_stream_patterns(project.parent / "logs", token),
        strict=True,
    ):
        if context[f"scheduler_{stream}_pattern"] != str(expected):
            raise SlurmSubmissionError(
                "Submission scheduler paths differ from the Project"
            )
    admitted = dict(context)
    if (
        len(orchestration_contracts.canonical_json_bytes(admitted))
        > _REQUEST_CONTEXT_LIMIT
    ):
        raise SlurmSubmissionError(
            "Submission request.json exceeds the 64 KiB observation limit"
        )
    return admitted


@dataclass(frozen=True, slots=True)
class SubmissionRequestObservation:
    """Retained diagnostic evidence, never scheduler acceptance or current state."""

    request_root: Path
    record_status: str
    context: Mapping[str, object] | None = field(repr=False)
    recorded_job_id: str | None
    recorded_cluster: str | None
    diagnostics: tuple[str, ...]
    stderr_excerpt: bytes = field(repr=False, default=b"")


def observe_submission_request(
    request: SubmissionRequestObservation,
    *,
    include_resources: bool = False,
) -> dict[str, object]:
    """Bind retained request identity to metadata without Run or recovery claims."""
    context = request.context
    if (
        request.record_status != "recorded-response"
        or context is None
        or context["schema_version"]
        not in ("emrys.submission-request.v2", "emrys.submission-request.v3")
    ):
        return scheduler_observation.unknown_observation(
            "Complete request-specific stream identity is unavailable"
        )
    return scheduler_observation.observe_job(
        request.recorded_job_id,
        context["scheduler_stdout_pattern"],
        context["scheduler_stderr_pattern"],
        request.recorded_cluster,
        job_name=(
            context["scheduler_job_name"]
            if context["schema_version"] == "emrys.submission-request.v3"
            else None
        ),
        include_resources=include_resources,
    )


def select_submission_request(
    project: Path, selector: str
) -> SubmissionRequestObservation:
    """Select one exact retained request, never a job ID or newest entry."""
    selected = tuple(
        request
        for request in submission_requests(project)
        if selector in (request.request_root.name, str(request.request_root))
    )
    if len(selected) != 1:
        raise SlurmSubmissionError(
            "Submission selector must identify one exact retained request"
        )
    return selected[0]


@dataclass(frozen=True, slots=True)
class SlurmStopPlan:
    request: SubmissionRequestObservation
    observation: Mapping[str, object]
    argv: tuple[str, ...]
    environment: Mapping[str, str] = field(repr=False)
    client_version: str | None
    client_binding: tuple[object, ...] | None = field(repr=False)


@dataclass(frozen=True, slots=True)
class SlurmStopResult:
    """Transport and scheduler observations, never proof of stopped native work."""

    invocation_attempted: bool
    returncode: int | None
    observation: Mapping[str, object]
    diagnostic: str | None
    stdout_excerpt: bytes = field(repr=False, default=b"")
    stderr_excerpt: bytes = field(repr=False, default=b"")


def _stop_client_binding(path: Path) -> tuple[object, ...]:
    require_executable(path, "scancel client")
    digest, state = sha256_with_identity(path, "scancel client")
    return (digest,) + tuple(
        getattr(state, name)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
    )


def plan_stop(project: Path, selector: str) -> SlurmStopPlan:
    """Read an exact v3 request and positively admit controller-filter support."""
    request = select_submission_request(project, selector)
    if (
        request.record_status != "recorded-response"
        or request.context is None
        or request.context["schema_version"] != "emrys.submission-request.v3"
    ):
        raise SlurmSubmissionError("Stop requires one complete v3 submission request")
    observation = MappingProxyType(observe_submission_request(request))
    if observation["state"] == "UNKNOWN":
        raise SlurmSubmissionError(
            f"Stop identity is unconfirmed: {observation['diagnostic']}"
        )
    environment = MappingProxyType(
        {
            key: value
            for key, value in os.environ.items()
            if key != "SLURM_CLUSTERS" and not key.startswith("SCANCEL_")
        }
    )
    if observation["terminal"]:
        return SlurmStopPlan(request, observation, (), environment, None, None)
    if observation["source"] != "squeue":
        raise SlurmSubmissionError("Stop requires a current controller observation")
    try:
        selected = shutil.which("scancel")
        if selected is None:
            raise SlurmSubmissionError("scancel client is unavailable")
        try:
            client = Path(selected).resolve(strict=True)
        except RuntimeError as exc:
            raise SlurmSubmissionError(
                "scancel client path cannot be resolved"
            ) from exc
        binding = _stop_client_binding(client)
        completed = subprocess.run(
            (str(client), "--version"),
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=10,
            check=False,
        )
        version = re.fullmatch(
            rb"slurm ([0-9]{2})\.([0-9]{2})\.(0|[1-9][0-9]{0,3})\n?", completed.stdout
        )
        if (
            completed.returncode != 0
            or version is None
            or tuple(map(int, version.groups())) < (23, 11, 6)
        ):
            raise SlurmSubmissionError(
                "Stop requires a confirmed scancel release >=23.11.6"
            )
        if _stop_client_binding(client) != binding:
            raise SlurmSubmissionError(
                "scancel client changed during version admission"
            )
    except (OSError, ValidationError, subprocess.TimeoutExpired) as exc:
        raise SlurmSubmissionError(
            f"Could not admit scancel client: {str(exc)[:4096]!a}"
        ) from exc
    argv = (
        str(client),
        "--ctld",
        f"--clusters={observation['cluster']}",
        f"--name={request.context['scheduler_job_name']}",
        "--me",
        str(request.recorded_job_id),
    )
    return SlurmStopPlan(
        request, observation, argv, environment, version[0].decode().strip(), binding
    )


def _observe_stop(plan: SlurmStopPlan) -> dict[str, object]:
    context = plan.request.context
    assert context is not None
    return scheduler_observation.observe_job(
        plan.request.recorded_job_id,
        context["scheduler_stdout_pattern"],
        context["scheduler_stderr_pattern"],
        plan.observation["cluster"],
        job_name=context["scheduler_job_name"],
    )


def stop(
    plan: SlurmStopPlan, *, record_path: Path, record_intent: Callable[[], None]
) -> SlurmStopResult:
    """Issue at most one filtered controller request and observe again, without retry."""
    context = plan.request.context
    assert context is not None
    attempted = False
    returncode = None
    diagnostic = None
    stdout = stderr = b""
    try:
        if (
            select_submission_request(
                Path(str(context["project"])), str(plan.request.request_root)
            )
            != plan.request
        ):
            raise SlurmSubmissionError("Submission request changed after stop planning")
        observed = _observe_stop(plan)
        if observed["state"] == "UNKNOWN":
            raise SlurmSubmissionError(
                f"Stop identity is unconfirmed: {observed['diagnostic']}"
            )
        if observed["terminal"]:
            return SlurmStopResult(False, None, MappingProxyType(observed), None)
        if not plan.argv:
            raise SlurmSubmissionError(
                "Scheduler state changed after terminal observation; plan again"
            )
        with _recorded_streams(record_path) as (output, errors, verify):
            verify(True)
            record_intent()
            if _stop_client_binding(Path(plan.argv[0])) != plan.client_binding:
                raise SlurmSubmissionError("scancel client changed after stop planning")
            try:
                verify()
                attempted = True
                completed = subprocess.run(
                    plan.argv,
                    env=dict(plan.environment),
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=errors,
                    timeout=10,
                    check=False,
                )
                returncode = completed.returncode
            finally:
                # Preserve process-control exceptions; a partial record never authorizes retry.
                active_error = sys.exc_info()[0] is not None
                retention_error = None
                for stream in (output, errors):
                    try:
                        stream.flush()
                        os.fsync(stream.fileno())
                    except OSError as exc:
                        retention_error = retention_error or exc
                try:
                    output.seek(0)
                    errors.seek(0)
                    stdout, stderr = output.read(4096), errors.read(4096)
                except OSError as exc:
                    retention_error = retention_error or exc
                if retention_error is not None and not active_error:
                    raise retention_error
    except (OSError, ValidationError, subprocess.TimeoutExpired) as exc:
        if not attempted:
            raise SlurmSubmissionError(
                f"Could not prepare stop: {str(exc)[:4096]!a}"
            ) from exc
        diagnostic = (
            f"Stop invocation or record retention is unconfirmed: {str(exc)[:4096]!a}"
        )
    return SlurmStopResult(
        attempted,
        returncode,
        MappingProxyType(_observe_stop(plan)),
        diagnostic,
        stdout,
        stderr,
    )


def submission_requests(project: Path) -> tuple[SubmissionRequestObservation, ...]:
    """Read every scoped request without writes, scheduler calls or newest selection."""
    log_root = project.parent / "logs"

    def directory(path: Path) -> tuple[tuple[str, ...], os.stat_result]:
        if (
            not path.is_absolute()
            or path.is_symlink()
            or path.resolve(strict=True) != path
        ):
            raise SlurmSubmissionError(f"Submission directory is not canonical: {path}")
        entries, identity = directory_entries_with_identity(
            path, "Submission directory"
        )
        if identity.st_uid != os.getuid():
            raise SlurmSubmissionError(
                f"Submission directory is not owned by current UID: {path}"
            )
        return entries, identity

    def read(path: Path, limit: int) -> tuple[bytes, int]:
        data, identity = read_bytes_with_identity(
            path, "Submission record", nonempty=False, limit=limit
        )
        if identity.st_uid != os.getuid():
            raise SlurmSubmissionError(
                f"Submission record is not owned by current UID: {path}"
            )
        return data, identity.st_size

    def same_directory(before: os.stat_result, after: os.stat_result) -> bool:
        return all(
            getattr(before, name) == getattr(after, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_uid",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        )

    try:
        if project.resolve(strict=True) != project or not project.is_file():
            raise SlurmSubmissionError("Project definition must be one canonical file")
        directory(project.parent)
        try:
            log_root.lstat()
        except FileNotFoundError:
            return ()
        entries, root_identity = directory(log_root)
    except (OSError, ValidationError) as exc:
        raise SlurmSubmissionError(str(exc)) from exc
    observations = []
    for name in entries:
        if not name.startswith("submission-"):
            continue
        request_root = log_root / name
        context = None
        recorded_job_id = recorded_cluster = None
        stderr = b""
        diagnostics = []
        status = "malformed"
        try:
            if not re.fullmatch(r"submission-[0-9a-f]{32}", name):
                raise SlurmSubmissionError(
                    "Submission request directory name is not canonical"
                )
            children, identity = directory(request_root)
            expected = {"request.json", "sbatch.stdout", "sbatch.stderr"}
            if set(children) - expected:
                raise SlurmSubmissionError(
                    "Submission request directory contains unexpected entries"
                )
            status = "partial" if set(children) != expected else "unconfirmed"
            if "request.json" not in children:
                raise SlurmSubmissionError("Submission request.json is missing")
            data, size = read(request_root / "request.json", _REQUEST_CONTEXT_LIMIT + 1)
            if size > _REQUEST_CONTEXT_LIMIT:
                raise SlurmSubmissionError(
                    "Submission request.json exceeds the 64 KiB observation limit"
                )
            parsed = orchestration_contracts.load_json_object_bytes(
                data, "Submission request"
            )
            context = validate_request_context(parsed, project, request_root)
            if orchestration_contracts.canonical_json_bytes(context) != data:
                raise SlurmSubmissionError(
                    "Submission request.json is not canonical JSON"
                )
            context = MappingProxyType(
                {**context, "emrys_argv": tuple(context["emrys_argv"])}
            )
            if "sbatch.stderr" in children:
                stderr, size = read(request_root / "sbatch.stderr", 4096)
                if size > len(stderr):
                    diagnostics.append(
                        "Retained stderr excerpt is limited to 4096 bytes"
                    )
            if "sbatch.stdout" not in children:
                diagnostics.append("Submission response is missing; job ID unconfirmed")
            else:
                data, size = read(request_root / "sbatch.stdout", 4097)
                if size > 4096:
                    diagnostics.append(
                        "Submission response exceeds 4096 bytes; job ID unconfirmed"
                    )
                elif not data.endswith(b"\n"):
                    diagnostics.append(
                        "Submission response is empty or unterminated; job ID unconfirmed"
                    )
                else:
                    try:
                        response = data.decode("utf-8")
                        recorded_job_id, recorded_cluster = _submitted_response(
                            response
                        )
                        if status != "partial":
                            status = "recorded-response"
                    except (UnicodeError, SlurmSubmissionError):
                        diagnostics.append(
                            "Submission response is empty or malformed; job ID unconfirmed"
                        )
            _, after = directory(request_root)
            if not same_directory(identity, after):
                raise SlurmSubmissionError(
                    "Submission request directory changed while read"
                )
            if status == "partial":
                diagnostics.append("Submission request has missing record files")
        except (OSError, ValidationError, ValueError, SlurmSubmissionError) as exc:
            diagnostics.append(str(exc)[:4096])
            context = None
            stderr = b""
            recorded_job_id = recorded_cluster = None
            if status != "partial":
                status = "malformed"
        observations.append(
            SubmissionRequestObservation(
                request_root,
                status,
                context,
                recorded_job_id,
                recorded_cluster,
                tuple(diagnostics),
                stderr,
            )
        )
    try:
        _, after = directory(log_root)
        if not same_directory(root_identity, after):
            raise SlurmSubmissionError("Submission request roster changed while read")
    except (OSError, ValidationError) as exc:
        raise SlurmSubmissionError(str(exc)) from exc
    return tuple(observations)


def delegate_binding() -> str | None:
    """Admit the shared private delegate context before loading its profile."""

    values = tuple(
        os.environ.get(name)
        for name in (DELEGATE_MARKER_ENV, PROFILE_SHA256_ENV, SUBMIT_UID_ENV)
    )
    request_token = os.environ.get(REQUEST_TOKEN_ENV)
    _validate_request_token(request_token)
    if request_token is None and all(value is None for value in values):
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
    job_name: str


def _batch_script(
    *,
    command: tuple[str, ...],
    scratch_parent: Path,
    module_init: Path | None,
    modules: tuple[str, ...],
    profile_sha256: str,
    submitter_uid: int,
    request_token: str | None,
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
            *(
                (
                    f'[[ "${{{REQUEST_TOKEN_ENV}:-}}" == {request_token} ]] || '
                    'die "submission request token differs from the frozen plan"',
                    f"readonly {REQUEST_TOKEN_ENV}",
                )
                if request_token is not None
                else ()
            ),
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
            "child_pid= termination_requested=0 termination_forwarded=0",
            "forward_termination() {",
            "    termination_requested=1",
            '    if [[ -n "$child_pid" && "$termination_forwarded" -eq 0 ]]; then',
            "        termination_forwarded=1",
            '        /bin/kill -TERM "$child_pid" 2>/dev/null || true',
            "    fi",
            "}",
            "trap forward_termination TERM",
            f"{quoted_command} &",
            "child_pid=$!",
            '[[ "$termination_requested" -eq 0 ]] || forward_termination',
            'while /bin/kill -0 "$child_pid" 2>/dev/null; do',
            "    set +e",
            '    wait "$child_pid"',
            "    command_status=$?",
            "    set -e",
            "done",
            "set +e",
            'wait "$child_pid"',
            "command_status=$?",
            "set -e",
            "trap - TERM",
            'exit "$command_status"',
            "",
        )
    )


def plan_submission(
    profile: ExecutionProfile,
    *,
    emrys_argv: Sequence[str],
    log_dir: Path,
    request_token: str | None = None,
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
    profile.validate_reservation()
    slurm_placement = cast("SlurmPlacement", placement)

    stdout_pattern, stderr_pattern = _scheduler_stream_patterns(
        Path(log_dir), request_token
    )
    argv = [sbatch, "--parsable"]
    if slurm_placement.account is not None:
        argv.append(f"--account={slurm_placement.account}")
    if slurm_placement.partition is not None:
        argv.append(f"--partition={slurm_placement.partition}")
    if slurm_placement.qos is not None:
        argv.append(f"--qos={slurm_placement.qos}")
    argv.extend(("--nodes=1", "--ntasks=1"))
    if slurm_placement.cpus_per_task != "node":
        argv.append(f"--cpus-per-task={slurm_placement.cpus_per_task}")
    if slurm_placement.memory_mb is not None:
        argv.append(
            f"--mem={slurm_placement.memory_mb}"
            + ("M" if slurm_placement.memory_mb else "")
        )
    if slurm_placement.exclusive:
        argv.append("--exclusive")
    if slurm_placement.nodelist is not None:
        argv.append(f"--nodelist={slurm_placement.nodelist}")
    argv.extend(
        (
            f"--time={slurm_placement.time}",
            "--signal=B:TERM@300",
            f"--job-name={_scheduler_job_name(request_token)}",
            f"--output={stdout_pattern}",
            f"--error={stderr_pattern}",
            f"--export={DELEGATE_MARKER_ENV}={DELEGATE_MARKER},"
            f"{PROFILE_SHA256_ENV}={profile_sha256},"
            f"{SUBMIT_UID_ENV}={uid},"
            + (
                f"{REQUEST_TOKEN_ENV}={request_token},"
                if request_token is not None
                else ""
            )
            + "LOGNAME,USER,LNAME,USERNAME",
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
        request_token=request_token,
    )
    return SlurmSubmission(
        argv=tuple(argv),
        batch_script=script,
        environment=scrubbed_environment,
        stdout_pattern=stdout_pattern,
        stderr_pattern=stderr_pattern,
        job_name=_scheduler_job_name(request_token),
    )


@contextmanager
def _recorded_streams(
    record: Path,
) -> Iterator[tuple[BinaryIO, BinaryIO, Callable[..., None]]]:
    """Keep two exclusive transcript files bound to their admitted directory."""
    identity = attrgetter("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")
    directory = os.open(
        record.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    original_error: BaseException | None = None
    try:
        parent = identity(os.fstat(directory))

        def verify_parent() -> None:
            try:
                canonical = record.parent.resolve(strict=True)
            except RuntimeError as exc:
                raise OSError("Transcript parent cannot be resolved") from exc
            if (
                canonical != record.parent
                or parent[3] != os.getuid()
                or identity(os.fstat(directory)) != parent
                or identity(record.parent.lstat()) != parent
            ):
                raise OSError(
                    "Transcript parent changed or is not canonical and current-owned"
                )

        verify_parent()

        def private_opener(path: str, flags: int) -> int:
            return os.open(
                Path(path).name, flags | os.O_NOFOLLOW, 0o600, dir_fd=directory
            )

        with (
            open(record, "xb+", opener=private_opener) as output,
            open(record.with_suffix(".stderr"), "xb+", opener=private_opener) as errors,
        ):
            streams = (output, errors)
            paths = (record, record.with_suffix(".stderr"))
            admitted = tuple(identity(os.fstat(stream.fileno())) for stream in streams)

            def verify(synchronize: bool = False) -> None:
                verify_parent()
                for stream, path, expected in zip(
                    streams, paths, admitted, strict=True
                ):
                    if (
                        not stat.S_ISREG(expected[2])
                        or expected[3] != os.getuid()
                        or identity(os.fstat(stream.fileno())) != expected
                        or identity(path.lstat()) != expected
                    ):
                        raise OSError("Transcript file changed after admission")
                if synchronize:
                    os.fsync(directory)
                    verify()

            try:
                yield output, errors, verify
            except BaseException as exc:
                original_error = exc
                raise
            else:
                verify()
    except OSError:
        if original_error is not None:
            raise original_error
        raise
    finally:
        try:
            os.close(directory)
        except OSError:
            if original_error is None:
                raise


def submit(
    submission: SlurmSubmission,
    *,
    record_path: Path,
    wait: bool = False,
    on_submitted: Callable[[str, str | None], None] | None = None,
    show_details: bool = True,
) -> str:
    """Retain transcripts for one submission, optionally waiting for the job."""

    job_id, operation = None, "prepare submission records"
    try:
        with _recorded_streams(record_path) as (output, errors, verify):
            operation = "synchronize submission directory"
            verify(True)
            if show_details:
                print(
                    f"Slurm submission records: {record_path}, {record_path.with_suffix('.stderr')}",
                    file=sys.stderr,
                )
            operation = "invoke sbatch"
            verify()
            with subprocess.Popen(
                (
                    *submission.argv,
                    *(("--wait",) if wait else ()),
                ),
                env=dict(submission.environment),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE if wait else output,
                stderr=errors,
            ) as process:
                operation = "communicate with sbatch"
                try:
                    with suppress(BrokenPipeError):
                        process.stdin.write(submission.batch_script.encode())
                    with suppress(BrokenPipeError):
                        process.stdin.close()
                    if wait:
                        first = process.stdout.readline()
                    else:
                        operation = "wait for sbatch"
                        process.wait()
                        output.seek(0)
                        first = output.read()
                        errors.seek(0)
                        stderr = errors.read(4096).decode("utf-8", "replace")
                    try:
                        job_id, cluster = (
                            _submitted_response(
                                first.decode("utf-8", "replace"),
                                stderr=stderr if not wait else None,
                            )
                            if first
                            else (None, None)
                        )
                    finally:
                        operation = "retain submission records"
                        if wait:
                            output.write(first)
                        output.flush()
                        os.fsync(output.fileno())
                    if job_id:
                        if show_details:
                            print(
                                f"Slurm job {job_id}; logs: {str(submission.stdout_pattern).replace('%j', job_id)}, {str(submission.stderr_pattern).replace('%j', job_id)}",
                                file=sys.stderr,
                            )
                        if on_submitted is not None:
                            on_submitted(job_id, cluster)
                    operation = "wait for sbatch"
                    rest = process.stdout.read() if wait else b""
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
    return _submitted_response(stdout, job_id, stderr)[0]


def _submitted_response(
    stdout: str, confirmed: str | None = None, stderr: str | None = None
) -> tuple[str, str | None]:

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
    return fields[0], fields[1] if len(fields) == 2 else None


__all__ = (
    "DELEGATE_MARKER",
    "DELEGATE_MARKER_ENV",
    "PROFILE_SHA256_ENV",
    "SUBMIT_UID_ENV",
    "REQUEST_TOKEN_ENV",
    "SlurmSubmission",
    "SlurmSubmissionError",
    "SlurmStopPlan",
    "SlurmStopResult",
    "SubmissionRequestObservation",
    "observe_submission_request",
    "plan_submission",
    "plan_stop",
    "select_submission_request",
    "stop",
    "submission_requests",
    "submit",
    "validate_request_context",
)
