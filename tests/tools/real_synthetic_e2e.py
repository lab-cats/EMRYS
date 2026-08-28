#!/usr/bin/env python3
"""Run one retained real-tool synthetic EMRYS E2E through single-node Slurm."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUMMARY_SCHEMA = "emrys.ci-real-synthetic-e2e-summary.v1"
PROFILE_DATASETS = {
    "130": "smoke-v1",
    "100000": "production-like-v1",
}
EXPECTED_OWNER_JOBS = 35
EXPECTED_REPORTING_KINDS = ("artifact_index", "run_summary", "html_report")
STEP10_OWNER = "emrys.analysis.project_candidate_scientific_context.v1"
TERMINAL_SLURM_STATES = frozenset(
    {
        "BOOT_FAIL",
        "CANCELLED",
        "COMPLETED",
        "DEADLINE",
        "FAILED",
        "NODE_FAIL",
        "OUT_OF_MEMORY",
        "PREEMPTED",
        "REVOKED",
        "SPECIAL_EXIT",
        "TIMEOUT",
    }
)
_RUN_ROOT_RE = re.compile(r"^Run root: (/.+/runs/run-[a-f0-9]{64})$", re.MULTILINE)
_PENDING_WORK_RE = re.compile(r"^Pending work items: ([0-9]+)$", re.MULTILINE)
_JOB_ID_RE = re.compile(r"^JOB_ID=([0-9]+)$", re.MULTILINE)
_OUT_RE = re.compile(r"^OUT=(/.+)$", re.MULTILINE)
_ERR_RE = re.compile(r"^ERR=(/.+)$", re.MULTILINE)
_SCHEDULER_PROFILE_RE = re.compile(r"^Execution profile: (/.+)$", re.MULTILINE)
_SCHEDULER_OUT_RE = re.compile(r"^Scheduler stdout: (/.+)$", re.MULTILINE)
_SCHEDULER_ERR_RE = re.compile(r"^Scheduler stderr: (/.+)$", re.MULTILINE)
_EVIDENCE_RE = re.compile(r"^Evidence: (/.+/attempt-receipt[.]json)$", re.MULTILINE)
_STATE_RE = re.compile(r"(?:^| )JobState=([A-Z_]+)")
_EXIT_RE = re.compile(r"(?:^| )ExitCode=([0-9]+:[0-9]+)")
_SLURM_MEMORY_RE = re.compile(r"^([1-9][0-9]*)([MG])$")


class DriverError(RuntimeError):
    """One explicit E2E stage failed without authorizing cleanup."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


@dataclass(frozen=True, slots=True)
class DriverPaths:
    """All driver-owned mutable paths under one supplied operator root."""

    operator_root: Path
    inputs: Path
    workspace: Path
    scratch: Path
    execution_profile: Path
    runtime_profile: Path
    runtime_adapters: Path
    transcripts: Path
    summary: Path


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Exact runtime identities selected outside workflow execution."""

    bash: Path
    star: Path
    samtools: Path
    gatk_delegate: Path
    bcftools: Path
    python: Path
    infer_experiment: Path
    gunzip_delegate: Path
    java: Path
    picard_jar: Path
    rscript: Path
    renv_library: Path


@dataclass(frozen=True, slots=True)
class SubmittedJob:
    """One grouped Run submission and its retained streams."""

    job_id: str
    stdout_path: Path
    stderr_path: Path


@dataclass(frozen=True, slots=True)
class CompletedJob:
    """Terminal Slurm observation for one submitted Run job."""

    job_id: str
    state: str
    exit_code: str
    stdout_path: Path
    stderr_path: Path
    stdout_sha256: str
    stderr_sha256: str


def _positive_int(value: str) -> int:
    try:
        selected = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if selected < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return selected


def _positive_float(value: str) -> float:
    try:
        selected = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be positive") from exc
    if selected <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return selected


def _memory_mb(value: str) -> int:
    """Parse one positive Slurm M/G size into profile-native MiB."""

    matched = _SLURM_MEMORY_RE.fullmatch(value)
    if matched is None:
        raise argparse.ArgumentTypeError("must be a positive size such as 6144M or 6G")
    amount = int(matched.group(1))
    return amount if matched.group(2) == "M" else amount * 1024


def build_parser() -> argparse.ArgumentParser:
    """Build the closed, explicit CI-driver argument surface."""

    parser = argparse.ArgumentParser(
        description=(
            "Run one real-tool synthetic EMRYS E2E through a retained "
            "single-node Slurm workflow. This driver installs and cleans nothing."
        )
    )
    parser.add_argument("--profile", required=True, choices=tuple(PROFILE_DATASETS))
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--operator-root", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--rscript", required=True, type=Path)
    parser.add_argument("--renv-library", required=True, type=Path)
    parser.add_argument("--storage-compute-launcher-json", required=True)
    parser.add_argument("--slurm-partition", required=True)
    parser.add_argument("--slurm-account")
    parser.add_argument("--slurm-qos")
    parser.add_argument("--slurm-cpus", type=_positive_int, default=4)
    parser.add_argument("--slurm-memory", type=_memory_mb, default="8G")
    parser.add_argument("--slurm-time", default="06:00:00")
    parser.add_argument("--slurm-nodelist")
    parser.add_argument("--scontrol", type=Path)
    parser.add_argument("--scancel", type=Path)
    parser.add_argument("--slurm-timeout-seconds", type=_positive_int, default=21_600)
    parser.add_argument("--poll-seconds", type=_positive_float, default=2.0)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the retained E2E. Without this flag, print a no-write plan.",
    )
    return parser


def _canonical_directory(path: Path, label: str) -> Path:
    authored = Path(os.path.abspath(path))
    try:
        state = authored.lstat()
        resolved = authored.resolve(strict=True)
    except OSError as exc:
        raise DriverError(
            "preflight", f"{label} is unavailable: {authored}: {exc}"
        ) from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
        raise DriverError(
            "preflight", f"{label} must be one real directory: {authored}"
        )
    if resolved != authored:
        raise DriverError("preflight", f"{label} must be canonical: {authored}")
    return authored


def _canonical_file(path: Path, label: str, *, executable: bool = False) -> Path:
    authored = Path(os.path.abspath(path))
    try:
        state = authored.lstat()
        resolved = authored.resolve(strict=True)
        resolved_state = resolved.stat()
    except OSError as exc:
        raise DriverError(
            "preflight", f"{label} is unavailable: {authored}: {exc}"
        ) from exc
    if stat.S_ISLNK(state.st_mode):
        authored = resolved
    if not stat.S_ISREG(resolved_state.st_mode):
        raise DriverError("preflight", f"{label} must resolve to one real file: {path}")
    if executable and not os.access(resolved, os.X_OK):
        raise DriverError("preflight", f"{label} is not executable: {resolved}")
    return resolved


def _resolve_command(value: Path | None, name: str) -> Path:
    selected = str(value) if value is not None else shutil.which(name)
    if not selected:
        raise DriverError("preflight", f"required command is unavailable: {name}")
    return _canonical_file(Path(selected), name, executable=True)


def _lexical_executable(path: Path, label: str) -> Path:
    """Admit an executable target while preserving its lexical launcher path."""

    authored = Path(os.path.abspath(path))
    try:
        parent_state = authored.parent.lstat()
        parent_resolved = authored.parent.resolve(strict=True)
        before = authored.lstat()
        link_before = os.readlink(authored) if stat.S_ISLNK(before.st_mode) else ""
        target = authored.resolve(strict=True)
        target_before = target.stat(follow_symlinks=False)
        after = authored.lstat()
        link_after = os.readlink(authored) if stat.S_ISLNK(after.st_mode) else ""
        confirmed_target = authored.resolve(strict=True)
        target_after = confirmed_target.stat(follow_symlinks=False)
    except OSError as exc:
        raise DriverError(
            "preflight", f"{label} launcher is unavailable: {authored}: {exc}"
        ) from exc
    if (
        stat.S_ISLNK(parent_state.st_mode)
        or not stat.S_ISDIR(parent_state.st_mode)
        or parent_resolved != authored.parent
        or (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns)
        or link_before != link_after
        or confirmed_target != target
        or (target_before.st_dev, target_before.st_ino, target_before.st_mode)
        != (target_after.st_dev, target_after.st_ino, target_after.st_mode)
        or not stat.S_ISREG(target_after.st_mode)
        or not os.access(authored, os.X_OK)
    ):
        raise DriverError(
            "preflight", f"{label} launcher identity is invalid or changed: {authored}"
        )
    return authored


def require_operator_root(operator_root: Path, repo_root: Path) -> DriverPaths:
    """Admit one empty external root without deleting or adopting prior state."""

    root = _canonical_directory(operator_root, "operator root")
    try:
        root.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise DriverError(
            "preflight", "operator root must be outside the source checkout"
        )
    try:
        children = tuple(root.iterdir())
    except OSError as exc:
        raise DriverError("preflight", f"cannot inspect operator root: {exc}") from exc
    if children:
        raise DriverError(
            "preflight",
            "operator root must be empty; preserve existing contents and select a new root",
        )
    if not os.access(root, os.R_OK | os.W_OK | os.X_OK):
        raise DriverError(
            "preflight", "operator root must be readable, writable, and searchable"
        )
    return DriverPaths(
        operator_root=root,
        inputs=root / "synthetic-inputs",
        workspace=root / "workspace",
        scratch=root / "scratch",
        execution_profile=root / "emrys.execution.slurm.json",
        runtime_profile=root / "runtime.selected.tsv",
        runtime_adapters=root / "runtime-adapters",
        transcripts=root / "driver-transcripts",
        summary=root / "e2e-summary.json",
    )


def _runtime_member(prefix: Path, relative: str, label: str) -> Path:
    return _canonical_file(prefix / relative, label, executable=True)


def resolve_runtime_paths(
    runtime_prefix: Path,
    rscript: Path,
    renv_library: Path,
) -> RuntimePaths:
    """Resolve the exact pre-provisioned runtime without installing anything."""

    prefix = _canonical_directory(runtime_prefix, "runtime prefix")
    library = _canonical_directory(renv_library, "renv library")
    picard_candidates = tuple(
        path
        for path in sorted(prefix.glob("share/picard-slim-3.1.1-*/picard.jar"))
        if path.is_file()
    )
    if len(picard_candidates) != 1:
        raise DriverError(
            "preflight",
            "runtime prefix must contain exactly one "
            "share/picard-slim-3.1.1-*/picard.jar",
        )
    return RuntimePaths(
        bash=_resolve_command(None, "bash"),
        star=_runtime_member(prefix, "bin/STAR", "STAR"),
        samtools=_runtime_member(prefix, "bin/samtools", "samtools"),
        gatk_delegate=_runtime_member(prefix, "bin/gatk", "GATK delegate"),
        bcftools=_runtime_member(prefix, "bin/bcftools", "bcftools"),
        python=_lexical_executable(prefix / "bin/python", "runtime Python"),
        infer_experiment=_runtime_member(
            prefix, "bin/infer_experiment.py", "infer_experiment.py"
        ),
        gunzip_delegate=_canonical_file(
            prefix / "bin/gunzip", "gunzip delegate", executable=True
        ),
        java=_runtime_member(prefix, "bin/java", "Java"),
        picard_jar=_canonical_file(picard_candidates[0], "Picard jar"),
        rscript=_canonical_file(rscript, "Rscript", executable=True),
        renv_library=library,
    )


def rseqc_adapter_bytes(runtime_python: Path, delegate: Path) -> bytes:
    """Render a closed version adapter that delegates every real invocation."""

    for label, path in (
        ("runtime Python", runtime_python),
        ("RSeQC delegate", delegate),
    ):
        if not path.is_absolute() or any(
            character in str(path) for character in ("\n", "\r")
        ):
            raise DriverError("preflight", f"{label} path is unsafe for the adapter")
    return (
        "#!/bin/sh\n"
        "set -eu\n"
        'if [ "$#" -eq 1 ] && [ "$1" = "--version" ]; then\n'
        "    printf '%s\\n' 'infer_experiment.py 5.0.4'\n"
        "    exit 0\n"
        "fi\n"
        f'exec {shlex.quote(str(runtime_python))} -I -B {shlex.quote(str(delegate))} "$@"\n'
    ).encode("utf-8")


def gatk_adapter_bytes(
    runtime_python: Path,
    delegate: Path,
    runtime_java: Path,
) -> bytes:
    """Render a retained GATK launcher with exact Python and Java selectors."""

    for label, path in (
        ("runtime Python", runtime_python),
        ("GATK delegate", delegate),
        ("runtime Java", runtime_java),
    ):
        if not path.is_absolute() or any(
            character in str(path) for character in ("\n", "\r")
        ):
            raise DriverError("preflight", f"{label} path is unsafe for the adapter")
    if runtime_java.name != "java" or runtime_java.parent.name != "bin":
        raise DriverError(
            "preflight",
            "runtime Java must be canonical <JAVA_HOME>/bin/java for the adapter",
        )
    java_bin = runtime_java.parent
    if os.pathsep in str(java_bin):
        raise DriverError("preflight", "runtime Java bin path is unsafe for PATH")
    java_home = java_bin.parent
    sealed_path = os.pathsep.join((str(java_bin), "/usr/bin", "/bin"))
    return (
        "#!/bin/sh\n"
        "set -eu\n"
        "unset CLASSPATH GATK_GCS_STAGING GATK_JAR GATK_LOCAL_JAR "
        "GATK_SPARK_JAR GCLOUD_HOME JAVA_OPTS JAVA_TOOL_OPTIONS "
        "JDK_JAVA_OPTIONS SPARK_HOME _JAVA_OPTIONS\n"
        f"JAVA_HOME={shlex.quote(str(java_home))}\n"
        f"PATH={shlex.quote(sealed_path)}\n"
        "export JAVA_HOME PATH\n"
        f'exec {shlex.quote(str(runtime_python))} -I -B {shlex.quote(str(delegate))} "$@"\n'
    ).encode("utf-8")


def gunzip_adapter_bytes(delegate: Path) -> bytes:
    """Render a retained decompressor independent of delegate ``argv[0]``."""

    if not delegate.is_absolute() or any(
        character in str(delegate) for character in ("\n", "\r")
    ):
        raise DriverError("preflight", "gunzip delegate path is unsafe for the adapter")
    quoted_delegate = shlex.quote(str(delegate))
    return (
        "#!/bin/sh\n"
        "set -eu\n"
        'if [ "$#" -eq 1 ] && [ "$1" = "--version" ]; then\n'
        f"exec {quoted_delegate} --version\n"
        "fi\n"
        f'exec {quoted_delegate} -d "$@"\n'
    ).encode("utf-8")


def parse_launcher_prefix(value: str) -> tuple[str, ...]:
    """Admit one explicit no-shell argv prefix used for compute qualification."""

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise DriverError(
            "preflight", f"storage launcher JSON is invalid: {exc}"
        ) from exc
    if (
        not isinstance(parsed, list)
        or not parsed
        or any(not isinstance(item, str) or not item for item in parsed)
    ):
        raise DriverError(
            "preflight", "storage launcher JSON must be a nonempty string array"
        )
    if any("\x00" in item or "\n" in item or "\r" in item for item in parsed):
        raise DriverError(
            "preflight", "storage launcher argv contains a control character"
        )
    executable = _canonical_file(
        Path(parsed[0]), "storage compute launcher", executable=True
    )
    return (str(executable), *parsed[1:])


def slurm_execution_profile_bytes(
    request_path: Path,
    source_profile_path: Path,
    *,
    account: str | None,
    partition: str,
    qos: str | None,
    cpus_per_task: int,
    memory_mb: int,
    time_limit: str,
    nodelist: str | None,
    scratch_parent: Path,
) -> bytes:
    """Project admitted fixture resources into one explicit Slurm profile."""

    from emrys.contracts.orchestration import api as orchestration_contracts
    from emrys.orchestration.local_pilot.execution_profile import (
        SCHEMA_VERSION,
        ExecutionProfileError,
        load_execution_profile,
    )

    try:
        source = load_execution_profile(
            request_path,
            config_path=source_profile_path,
        )
        document = {
            "schema_version": SCHEMA_VERSION,
            "resources": source.resources.document(),
            "placement": {
                "kind": "slurm",
                "account": account,
                "partition": partition,
                "qos": qos,
                "cpus_per_task": cpus_per_task,
                "memory_mb": memory_mb,
                "time": time_limit,
                "exclusive": False,
                "nodelist": nodelist,
                "scratch_parent": str(scratch_parent),
                "modules": {"mode": "none", "init": "", "load": []},
            },
        }
        orchestration_contracts.validate_record("execution-profile", document)
        return orchestration_contracts.canonical_json_bytes(document) + b"\n"
    except (
        ExecutionProfileError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        raise DriverError(
            "prepare-execution-profile",
            f"could not project the admitted synthetic execution profile: {exc}",
        ) from exc


def _write_exclusive(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, mode)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError(f"short write: {path}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sha256_file(path: Path) -> str:
    """Hash one stable real file without following a symbolic-link leaf."""

    if path.is_symlink() or not path.is_file():
        raise DriverError(
            "assert-results", f"required result is not a real file: {path}"
        )
    before = path.stat(follow_symlinks=False)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    after = path.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise DriverError("assert-results", f"result changed while hashing: {path}")
    return digest.hexdigest()


class Transcripts:
    """Run argv-only subprocesses and retain every captured stream under the root."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.records: list[dict[str, Any]] = []
        self.operator_root_admitted = False
        self._counter = 0

    def run(
        self,
        stage: str,
        command: list[str] | tuple[str, ...],
        *,
        cwd: Path,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self._counter += 1
        label = re.sub(r"[^a-z0-9-]+", "-", stage.lower()).strip("-")
        stem = f"{self._counter:02d}-{label}"
        stdout_path = self.root / f"{stem}.stdout.log"
        stderr_path = self.root / f"{stem}.stderr.log"
        selected = tuple(str(value) for value in command)
        print(f"E2E stage {stage}: {shlex.join(selected)}", flush=True)
        try:
            result = subprocess.run(
                selected,
                cwd=cwd,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise DriverError(stage, f"could not execute command: {exc}") from exc
        _write_exclusive(stdout_path, result.stdout.encode("utf-8"))
        _write_exclusive(stderr_path, result.stderr.encode("utf-8"))
        self.records.append(
            {
                "stage": stage,
                "argv": list(selected),
                "returncode": result.returncode,
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
            }
        )
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(
                result.stderr,
                end="" if result.stderr.endswith("\n") else "\n",
                file=sys.stderr,
            )
        if result.returncode != 0:
            raise DriverError(
                stage,
                f"command exited {result.returncode}; retained streams: {stdout_path}, {stderr_path}",
            )
        return result


def _one_match(pattern: re.Pattern[str], text: str, label: str, stage: str) -> str:
    observed = pattern.findall(text)
    if len(observed) != 1:
        raise DriverError(stage, f"expected one {label}; observed {len(observed)}")
    return observed[0]


def parse_run_plan(text: str, workspace: Path, *, no_write: bool) -> Path:
    """Require the current grouped Run plan and automatic-report contract."""

    stage = "plan-workflow"
    run_root = Path(_one_match(_RUN_ROOT_RE, text, "run root", stage))
    pending = int(_one_match(_PENDING_WORK_RE, text, "pending-work count", stage))
    if pending != EXPECTED_OWNER_JOBS:
        raise DriverError(
            stage,
            f"expected {EXPECTED_OWNER_JOBS} pending work items; observed {pending}",
        )
    if "Reporting: automatic after scientific work" not in text:
        raise DriverError(stage, "public Run plan did not declare automatic reporting")
    expected_parent = workspace / "runs"
    if run_root.parent != expected_parent:
        raise DriverError(
            stage, f"planned run root escapes selected workspace: {run_root}"
        )
    if no_write and "Dry-run complete; no workspace state was written." not in text:
        raise DriverError(
            stage, "public run plan did not confirm its no-write boundary"
        )
    return run_root


def parse_scheduler_plan(
    text: str,
    execution_profile: Path,
    workspace: Path,
) -> tuple[Path, Path]:
    """Require one scheduler dry-run without interpreting it as a submission."""

    stage = "submit-slurm-plan"
    profile = Path(_one_match(_SCHEDULER_PROFILE_RE, text, "profile path", stage))
    stdout_pattern = Path(
        _one_match(_SCHEDULER_OUT_RE, text, "scheduler stdout pattern", stage)
    )
    stderr_pattern = Path(
        _one_match(_SCHEDULER_ERR_RE, text, "scheduler stderr pattern", stage)
    )
    log_dir = workspace / "logs"
    if profile != execution_profile:
        raise DriverError(stage, "scheduler plan selected a different profile")
    if stdout_pattern != log_dir / "emrys-local-pilot-%j.out":
        raise DriverError(stage, "scheduler plan selected an unexpected stdout path")
    if stderr_pattern != log_dir / "emrys-local-pilot-%j.err":
        raise DriverError(stage, "scheduler plan selected an unexpected stderr path")
    if "Execution placement: Slurm" not in text:
        raise DriverError(stage, "scheduler plan omitted Slurm placement")
    if "Dry-run complete; no scheduler or workspace state was written." not in text:
        raise DriverError(stage, "scheduler plan omitted its no-write boundary")
    return stdout_pattern, stderr_pattern


def parse_submission(text: str, expected_log_dir: Path) -> SubmittedJob:
    """Admit the grouped Run command's exact submission receipt lines."""

    stage = "submit-slurm"
    job_id = _one_match(_JOB_ID_RE, text, "Slurm job ID", stage)
    stdout_path = Path(_one_match(_OUT_RE, text, "Slurm stdout path", stage))
    stderr_path = Path(_one_match(_ERR_RE, text, "Slurm stderr path", stage))
    if stdout_path != expected_log_dir / f"emrys-local-pilot-{job_id}.out":
        raise DriverError(stage, "grouped Run returned an unexpected stdout path")
    if stderr_path != expected_log_dir / f"emrys-local-pilot-{job_id}.err":
        raise DriverError(stage, "grouped Run returned an unexpected stderr path")
    return SubmittedJob(job_id, stdout_path, stderr_path)


def parse_execution_evidence(text: str, run_root: Path) -> Path:
    """Admit the compute-side receipt location reported on retained stderr."""

    stage = "slurm-execute"
    receipt = Path(_one_match(_EVIDENCE_RE, text, "attempt receipt", stage))
    try:
        relative = receipt.relative_to(run_root)
    except ValueError as exc:
        raise DriverError(stage, "attempt receipt escapes the selected Run") from exc
    if (
        len(relative.parts) != 3
        or relative.parts[0] != "attempts"
        or relative.parts[2] != "attempt-receipt.json"
    ):
        raise DriverError(stage, "attempt receipt uses an unexpected Run location")
    return receipt


def parse_scontrol_job(text: str) -> tuple[str, str]:
    """Parse the terminal-relevant fields from one-line ``scontrol show job``."""

    state_match = _STATE_RE.search(text)
    exit_match = _EXIT_RE.search(text)
    if state_match is None or exit_match is None:
        raise DriverError("wait-slurm", "scontrol output omits JobState or ExitCode")
    return state_match.group(1), exit_match.group(1)


def _read_retained_stream(path: Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise DriverError("wait-slurm", f"{label} is absent or not a real file: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DriverError(
            "wait-slurm", f"could not read {label}: {path}: {exc}"
        ) from exc


def cancel_job(
    job_id: str,
    *,
    scancel: Path,
    scontrol: Path,
    cwd: Path,
    poll_seconds: float,
    timeout_seconds: float = 30.0,
) -> str:
    """Request TERM once and boundedly confirm terminal scheduler disposition."""

    result = subprocess.run(
        (str(scancel), "--signal=TERM", job_id),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise DriverError(
            "cancel-slurm",
            f"scancel failed for job {job_id}: {result.stderr.strip()}",
        )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        observed = subprocess.run(
            (str(scontrol), "show", "job", "-o", job_id),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        if observed.returncode != 0:
            print(f"Slurm job {job_id}: no longer observable after scancel", flush=True)
            return "NO_LONGER_OBSERVABLE"
        state, _exit_code = parse_scontrol_job(observed.stdout)
        if state in TERMINAL_SLURM_STATES:
            print(f"Slurm job {job_id}: terminal after scancel ({state})", flush=True)
            return state
        time.sleep(min(poll_seconds, 1.0))
    raise DriverError(
        "cancel-slurm",
        f"job {job_id} did not reach a terminal state within {timeout_seconds:g} seconds of scancel",
    )


def wait_for_job(
    job: SubmittedJob,
    *,
    scontrol: Path,
    scancel: Path,
    cwd: Path,
    timeout_seconds: int,
    poll_seconds: float,
) -> CompletedJob:
    """Wait boundedly for terminal Slurm state without inferring EMRYS success."""

    started = time.monotonic()
    last_state: str | None = None
    last_heartbeat = started
    state = "UNKNOWN"
    exit_code = "0:0"
    try:
        while True:
            now = time.monotonic()
            if now - started > timeout_seconds:
                cancelled_state = cancel_job(
                    job.job_id,
                    scancel=scancel,
                    scontrol=scontrol,
                    cwd=cwd,
                    poll_seconds=poll_seconds,
                )
                raise DriverError(
                    "wait-slurm",
                    f"job {job.job_id} exceeded the {timeout_seconds}-second wait; scancel disposition: {cancelled_state}",
                )
            result = subprocess.run(
                (str(scontrol), "show", "job", "-o", job.job_id),
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise DriverError(
                    "wait-slurm",
                    f"scontrol could not observe retained job {job.job_id}: {result.stderr.strip()}",
                )
            state, exit_code = parse_scontrol_job(result.stdout)
            if state != last_state or now - last_heartbeat >= 60:
                print(f"Slurm job {job.job_id}: {state} {exit_code}", flush=True)
                last_state = state
                last_heartbeat = now
            if state in TERMINAL_SLURM_STATES:
                break
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        cancelled_state = cancel_job(
            job.job_id,
            scancel=scancel,
            scontrol=scontrol,
            cwd=cwd,
            poll_seconds=poll_seconds,
        )
        raise DriverError(
            "wait-slurm",
            f"interrupted while waiting for job {job.job_id}; scancel disposition: {cancelled_state}",
        ) from None

    stream_deadline = time.monotonic() + min(30.0, float(timeout_seconds))
    while (
        not job.stdout_path.exists() or not job.stderr_path.exists()
    ) and time.monotonic() < stream_deadline:
        time.sleep(min(poll_seconds, 1.0))
    stdout = _read_retained_stream(job.stdout_path, "Slurm stdout")
    stderr = _read_retained_stream(job.stderr_path, "Slurm stderr")
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
    completed = CompletedJob(
        job_id=job.job_id,
        state=state,
        exit_code=exit_code,
        stdout_path=job.stdout_path,
        stderr_path=job.stderr_path,
        stdout_sha256=sha256_file(job.stdout_path),
        stderr_sha256=sha256_file(job.stderr_path),
    )
    if state != "COMPLETED" or exit_code != "0:0":
        raise DriverError(
            "wait-slurm",
            f"job {job.job_id} ended {state} with exit {exit_code}; retained streams remain in {job.stdout_path.parent}",
        )
    return completed


def validate_step09_oracle(
    all_sites: Path,
    significant_sites: Path,
    fixture_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Independently require the fixture's direct 3/1 candidate-table oracle."""

    def rows(path: Path) -> list[dict[str, str]]:
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t", strict=True)
                selected = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise DriverError(
                "assert-results", f"cannot read Step 09 table {path}: {exc}"
            ) from exc
        if not reader.fieldnames or not {"candidate_id", "call_status"}.issubset(
            reader.fieldnames
        ):
            raise DriverError(
                "assert-results",
                f"Step 09 table omits candidate_id or call_status: {path}",
            )
        return selected

    all_rows = rows(all_sites)
    significant_rows = rows(significant_sites)
    expected = fixture_metadata.get("expected_terminal_computational_result")
    if not isinstance(expected, dict):
        raise DriverError(
            "assert-results", "fixture metadata omits the terminal oracle"
        )
    expected_all = expected.get("all_sites_rows")
    expected_significant = expected.get("significant_sites_rows")
    expected_candidate = expected.get("significant_candidate_id")
    if (expected_all, expected_significant) != (3, 1):
        raise DriverError(
            "assert-results", "fixture metadata no longer declares the 3/1 oracle"
        )
    if len(all_rows) != 3 or len(significant_rows) != 1:
        raise DriverError(
            "assert-results",
            f"Step 09 oracle expected 3/1 rows; observed {len(all_rows)}/{len(significant_rows)}",
        )
    all_ids = [row["candidate_id"] for row in all_rows]
    significant_ids = [row["candidate_id"] for row in significant_rows]
    if len(set(all_ids)) != 3 or significant_ids != [expected_candidate]:
        raise DriverError(
            "assert-results",
            "Step 09 candidate identity differs from the fixture oracle",
        )
    if expected_candidate not in all_ids:
        raise DriverError(
            "assert-results", "significant candidate is absent from all-sites"
        )
    if significant_rows[0]["call_status"] not in {"significant_up", "significant_down"}:
        raise DriverError(
            "assert-results", "significant table contains a non-significant call"
        )
    return {
        "all_sites_rows": len(all_rows),
        "significant_sites_rows": len(significant_rows),
        "significant_candidate_id": expected_candidate,
        "all_sites_sha256": sha256_file(all_sites),
        "significant_sites_sha256": sha256_file(significant_sites),
    }


def _artifact(path: Path) -> dict[str, Any]:
    digest = sha256_file(path)
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest}


def assert_completed_run(
    run_root: Path,
    fixture_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Re-admit completion, then assert direct owner/report/artifact oracles."""

    from emrys.orchestration.local_pilot import inspection

    observed = inspection.inspect_run(run_root)
    if (
        observed.integrity != "valid"
        or observed.attempt_outcome != "succeeded"
        or observed.results_status != "complete"
        or observed.reporting_status != "complete"
    ):
        raise DriverError("assert-results", "inspection is not fully complete")
    if observed.blockers:
        raise DriverError("assert-results", "completed inspection retained blockers")
    if len(observed.tasks) != EXPECTED_OWNER_JOBS:
        raise DriverError(
            "assert-results",
            f"expected {EXPECTED_OWNER_JOBS} inspected owners; observed {len(observed.tasks)}",
        )
    if any(task.state != "verified" for task in observed.tasks):
        raise DriverError(
            "assert-results", "one or more required owner jobs is not verified"
        )
    verified_records = [
        {
            "machine_key": task.expected.machine_key,
            "scope_type": task.expected.scope_type,
            "scope_id": task.expected.scope_id,
            **_artifact(task.record_path),
        }
        for task in observed.tasks
    ]
    if len({record["path"] for record in verified_records}) != EXPECTED_OWNER_JOBS:
        raise DriverError(
            "assert-results", "verified owner records are not path-disjoint"
        )
    step10 = [
        task for task in observed.tasks if task.expected.machine_key == STEP10_OWNER
    ]
    if len(step10) != 1 or step10[0].state != "verified":
        raise DriverError("assert-results", "the current Step 10 owner is not verified")
    reporting = observed.reporting_completion_records
    if tuple(reporting) != EXPECTED_REPORTING_KINDS:
        raise DriverError("assert-results", "reporting transaction roster differs")
    if any(
        value["start"] is None or value["verified"] is None
        for value in reporting.values()
    ):
        raise DriverError(
            "assert-results", "one or more reporting transaction is incomplete"
        )
    reporting_records = {
        kind: {
            state: _artifact(run_root / "state" / "reporting" / kind / f"{state}.json")
            for state in ("start", "verified")
        }
        for kind in EXPECTED_REPORTING_KINDS
    }
    if (
        observed.latest_receipt is None
        or observed.latest_receipt.get("status") != "succeeded"
    ):
        raise DriverError(
            "assert-results", "latest workflow attempt receipt is not succeeded"
        )

    run_id = observed.run_id
    summary_dir = run_root / "products" / "artifact-summary" / run_id
    report_dir = run_root / "products" / "report" / run_id
    artifacts = {
        "artifact_index": summary_dir / f"{run_id}.artifacts.tsv",
        "artifact_receipt": summary_dir / f"{run_id}.artifact_receipt.tsv",
        "run_summary_json": summary_dir / f"{run_id}.run_summary.json",
        "run_summary_tsv": summary_dir / f"{run_id}.run_summary.tsv",
        "qc_summary_tsv": summary_dir / f"{run_id}.qc_summary.tsv",
        "run_summary_receipt": summary_dir / f"{run_id}.run_summary_receipt.tsv",
        "scientific_html": report_dir / f"{run_id}.scientific_report.html",
        "evidence_html": report_dir / f"{run_id}.evidence_report.html",
        "report_summary_tsv": report_dir / f"{run_id}.run_summary.tsv",
        "report_receipt": report_dir / f"{run_id}.report_outputs.tsv",
        "attempt_receipt": run_root
        / "attempts"
        / str(observed.latest_workflow_attempt_id)
        / "attempt-receipt.json",
    }
    admitted_artifacts = {name: _artifact(path) for name, path in artifacts.items()}
    try:
        summary = json.loads(artifacts["run_summary_json"].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DriverError(
            "assert-results", f"run summary JSON is unreadable: {exc}"
        ) from exc
    if (
        not isinstance(summary, dict)
        or summary.get("run_id") != run_id
        or summary.get("summary_state") != "complete"
        or summary.get("candidate_terminology") != "CMH-ranked candidates"
        or summary.get("interpretation_boundary")
        != "computational_candidates_only_biological_validation_outside_emrys"
        or summary.get("errors") != []
    ):
        raise DriverError(
            "assert-results", "canonical run summary completion boundary differs"
        )

    run_contract = summary.get("run_contract", {})
    analysis_id = (
        run_contract.get("primary_analysis_id")
        if isinstance(run_contract, dict)
        else None
    )
    if not isinstance(analysis_id, str) or not analysis_id:
        raise DriverError("assert-results", "run summary omits the primary analysis ID")
    editing = run_root / "results" / "editing" / analysis_id
    oracle = validate_step09_oracle(
        editing / f"{analysis_id}.cmh_all_sites.tsv",
        editing / f"{analysis_id}.cmh_significant_sites.tsv",
        fixture_metadata,
    )
    step10_receipt = (
        run_root
        / "results"
        / "scientific_context"
        / analysis_id
        / f"{analysis_id}.context_receipt.tsv"
    )
    admitted_artifacts["step10_context_receipt"] = _artifact(step10_receipt)
    return {
        "run_id": run_id,
        "run_root": str(run_root),
        "state": "local_pipeline_complete",
        "verified_owner_jobs": len(observed.tasks),
        "verified_owner_records": verified_records,
        "step10_verified": True,
        "reporting_transactions": list(reporting),
        "reporting_records": reporting_records,
        "step09_oracle": oracle,
        "artifacts": admitted_artifacts,
    }


def _emrys(python: Path, *arguments: str) -> list[str]:
    return [
        str(python),
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "emrys",
        *arguments,
    ]


def _job_summary(job: CompletedJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "state": job.state,
        "exit_code": job.exit_code,
        "stdout": str(job.stdout_path),
        "stdout_sha256": job.stdout_sha256,
        "stderr": str(job.stderr_path),
        "stderr_sha256": job.stderr_sha256,
    }


def run_driver(
    arguments: argparse.Namespace, transcripts: Transcripts
) -> dict[str, Any]:
    """Execute the approved retained E2E sequence; never install or clean."""

    repo_root = _canonical_directory(arguments.repo_root, "repository root")
    paths = require_operator_root(arguments.operator_root, repo_root)
    transcripts.operator_root_admitted = True
    if os.environ.get("SLURM_JOB_ID", "").strip():
        raise DriverError(
            "preflight",
            "driver must start outside Slurm so storage finalization occurs in the control context",
        )
    workflow_python = _lexical_executable(
        repo_root / ".venv/bin/python", "workflow Python"
    )
    runtime = resolve_runtime_paths(
        arguments.runtime_prefix, arguments.rscript, arguments.renv_library
    )
    storage_launcher = parse_launcher_prefix(arguments.storage_compute_launcher_json)
    scontrol = _resolve_command(arguments.scontrol, "scontrol")
    scancel = _resolve_command(arguments.scancel, "scancel")
    paths.scratch.mkdir(mode=0o700)
    paths.runtime_adapters.mkdir(mode=0o700)
    paths.transcripts.mkdir(mode=0o700)

    gatk_adapter = paths.runtime_adapters / "gatk"
    _write_exclusive(
        gatk_adapter,
        gatk_adapter_bytes(
            runtime.python,
            runtime.gatk_delegate,
            runtime.java,
        ),
        mode=0o700,
    )
    gatk_adapter = _canonical_file(
        gatk_adapter, "retained GATK adapter", executable=True
    )
    gatk_probe = transcripts.run(
        "probe-gatk-adapter",
        [str(gatk_adapter), "--version"],
        cwd=repo_root,
    )
    gatk_version_text = (gatk_probe.stdout + gatk_probe.stderr).strip()
    gatk_version_match = re.search(
        r"(?:^|\s)The Genome Analysis Toolkit [(]GATK[)] "
        r"v?4[.]6[.]1[.]0(?:\s|$)",
        gatk_version_text,
    )
    if gatk_version_match is None:
        raise DriverError(
            "probe-gatk-adapter",
            "retained GATK adapter did not report exact GATK 4.6.1.0",
        )
    gatk_attestation = {
        "runtime_python_launcher": str(runtime.python),
        "runtime_python": _artifact(runtime.python.resolve(strict=True)),
        "runtime_java": _artifact(runtime.java),
        "java_home": str(runtime.java.parent.parent),
        "delegate": _artifact(runtime.gatk_delegate),
        "adapter": _artifact(gatk_adapter),
        "version_output": " ".join(gatk_version_match.group(0).split()),
    }

    rseqc_attestation_result = transcripts.run(
        "attest-rseqc-package",
        [
            str(runtime.python),
            "-B",
            "-I",
            "-c",
            "from importlib.metadata import version; print(version('RSeQC'))",
        ],
        cwd=repo_root,
    )
    if rseqc_attestation_result.stdout != "5.0.4\n":
        raise DriverError(
            "attest-rseqc-package",
            "importlib.metadata did not attest exact RSeQC package version 5.0.4",
        )
    rseqc_adapter = paths.runtime_adapters / "infer_experiment.py"
    _write_exclusive(
        rseqc_adapter,
        rseqc_adapter_bytes(runtime.python, runtime.infer_experiment),
        mode=0o700,
    )
    rseqc_adapter = _canonical_file(
        rseqc_adapter, "retained RSeQC version adapter", executable=True
    )
    rseqc_probe = transcripts.run(
        "probe-rseqc-adapter", [str(rseqc_adapter), "--version"], cwd=repo_root
    )
    if rseqc_probe.stdout != "infer_experiment.py 5.0.4\n":
        raise DriverError(
            "probe-rseqc-adapter", "retained RSeQC adapter version output differs"
        )
    rseqc_attestation = {
        "distribution": "RSeQC",
        "distribution_version": "5.0.4",
        "runtime_python": _artifact(runtime.python.resolve(strict=True)),
        "delegate": _artifact(runtime.infer_experiment),
        "adapter": _artifact(rseqc_adapter),
        "version_output": "infer_experiment.py 5.0.4",
    }

    gunzip_adapter = paths.runtime_adapters / "gunzip"
    _write_exclusive(
        gunzip_adapter,
        gunzip_adapter_bytes(runtime.gunzip_delegate),
        mode=0o700,
    )
    gunzip_adapter = _canonical_file(
        gunzip_adapter, "retained gunzip adapter", executable=True
    )
    gunzip_version_probe = transcripts.run(
        "probe-gunzip-adapter-version",
        [str(gunzip_adapter), "--version"],
        cwd=repo_root,
    )
    gunzip_version_text = (
        gunzip_version_probe.stdout + gunzip_version_probe.stderr
    ).strip()
    if (
        not gunzip_version_text
        or re.match(r"^(?:gzip|gunzip|Apple gzip).*", gunzip_version_text) is None
    ):
        raise DriverError(
            "probe-gunzip-adapter-version",
            "retained gunzip adapter version output differs from the runtime contract",
        )
    gunzip_probe_payload = b"emrys-gunzip-adapter-probe\n"
    gunzip_probe_archive = paths.runtime_adapters / "gunzip-probe.txt.gz"
    _write_exclusive(
        gunzip_probe_archive,
        gzip.compress(gunzip_probe_payload, mtime=0),
    )
    gunzip_decompression_probe = transcripts.run(
        "probe-gunzip-adapter-decompression",
        [str(gunzip_adapter), "-c", str(gunzip_probe_archive)],
        cwd=repo_root,
    )
    if gunzip_decompression_probe.stdout.encode("utf-8") != gunzip_probe_payload:
        raise DriverError(
            "probe-gunzip-adapter-decompression",
            "retained gunzip adapter did not reproduce the fixed probe payload",
        )
    gunzip_attestation = {
        "delegate": _artifact(runtime.gunzip_delegate),
        "adapter": _artifact(gunzip_adapter),
        "version_output": gunzip_version_text.splitlines()[0],
        "decompression_probe_sha256": hashlib.sha256(gunzip_probe_payload).hexdigest(),
    }

    profile = str(arguments.profile)
    dataset_profile = PROFILE_DATASETS[profile]
    fixture_plan = _emrys(
        workflow_python,
        "init",
        "synthetic-local-pilot",
        "--output-dir",
        str(paths.inputs),
        "--dataset-profile",
        dataset_profile,
    )
    transcripts.run("fixture-plan", fixture_plan, cwd=repo_root)
    transcripts.run("fixture-publish", [*fixture_plan, "--execute"], cwd=repo_root)

    request = paths.inputs / "request.yaml"
    direct_execution_profile = paths.inputs / "emrys.execution.yaml"
    _write_exclusive(
        paths.execution_profile,
        slurm_execution_profile_bytes(
            request,
            direct_execution_profile,
            account=arguments.slurm_account,
            partition=arguments.slurm_partition,
            qos=arguments.slurm_qos,
            cpus_per_task=arguments.slurm_cpus,
            memory_mb=arguments.slurm_memory,
            time_limit=arguments.slurm_time,
            nodelist=arguments.slurm_nodelist,
            scratch_parent=paths.scratch,
        ),
    )

    runtime_command = _emrys(
        workflow_python,
        "prepare",
        "local-pilot-runtime",
        "--bash",
        str(runtime.bash),
        "--star",
        str(runtime.star),
        "--samtools",
        str(runtime.samtools),
        "--gatk",
        str(gatk_adapter),
        "--bcftools",
        str(runtime.bcftools),
        "--infer-experiment",
        str(rseqc_adapter),
        "--gunzip",
        str(gunzip_adapter),
        "--java",
        str(runtime.java),
        "--picard-jar",
        str(runtime.picard_jar),
        "--rscript",
        str(runtime.rscript),
        "--renv-library",
        str(runtime.renv_library),
    )
    runtime_result = transcripts.run("prepare-runtime", runtime_command, cwd=repo_root)
    _write_exclusive(paths.runtime_profile, runtime_result.stdout.encode("utf-8"))

    reference_fasta = paths.inputs / "inputs/reference/reference.fa"
    transcripts.run(
        "validate-request",
        _emrys(
            workflow_python,
            "validate",
            "local-pilot-request",
            "--request",
            str(request),
        ),
        cwd=repo_root,
    )
    compute = _emrys(
        workflow_python,
        "inspect",
        "storage-qualification",
        "--workspace",
        str(paths.workspace),
        "--reference-fasta",
        str(reference_fasta),
        "--phase",
        "compute",
    )
    transcripts.run("storage-compute-plan", compute, cwd=repo_root)
    transcripts.run(
        "storage-compute",
        [*storage_launcher, *compute, "--execute"],
        cwd=repo_root,
    )
    finalize = _emrys(
        workflow_python,
        "inspect",
        "storage-qualification",
        "--workspace",
        str(paths.workspace),
        "--reference-fasta",
        str(reference_fasta),
        "--phase",
        "finalize",
    )
    transcripts.run("storage-finalize-plan", finalize, cwd=repo_root)
    transcripts.run("storage-finalize", [*finalize, "--execute"], cwd=repo_root)
    from emrys.evidence.storage_inventory import qualification

    qualified_storage = qualification.admit_final_qualification(
        paths.workspace, reference_fasta
    )
    storage_qualification = {
        "qualification_id": qualified_storage.qualification_id,
        "final_receipt": _artifact(qualified_storage.receipt_path),
    }

    transcripts.run(
        "doctor",
        _emrys(
            workflow_python,
            "doctor",
            "local-pilot",
            "--request",
            str(request),
            "--workspace",
            str(paths.workspace),
            "--runtime-profile",
            str(paths.runtime_profile),
        ),
        cwd=repo_root,
    )
    plan_result = transcripts.run(
        "plan-workflow",
        _emrys(
            workflow_python,
            "run",
            "--request",
            str(request),
            "--workspace",
            str(paths.workspace),
            "--runtime-profile",
            str(paths.runtime_profile),
            "--execution-profile",
            str(direct_execution_profile),
        ),
        cwd=repo_root,
    )
    if plan_result.stdout:
        raise DriverError("plan-workflow", "direct Run plan wrote machine stdout")
    run_root = parse_run_plan(plan_result.stderr, paths.workspace, no_write=True)
    if paths.workspace.exists():
        raise DriverError("plan-workflow", "no-write plan created the workspace")

    scheduled_run = _emrys(
        workflow_python,
        "run",
        "--request",
        str(request),
        "--workspace",
        str(paths.workspace),
        "--runtime-profile",
        str(paths.runtime_profile),
        "--execution-profile",
        str(paths.execution_profile),
    )
    dry_submission_result = transcripts.run(
        "submit-slurm-plan", scheduled_run, cwd=repo_root
    )
    if dry_submission_result.stdout:
        raise DriverError("submit-slurm-plan", "scheduler dry-run submitted a job")
    dry_stdout_pattern, dry_stderr_pattern = parse_scheduler_plan(
        dry_submission_result.stderr,
        paths.execution_profile,
        paths.workspace,
    )
    if paths.workspace.exists():
        raise DriverError("slurm-plan", "Slurm no-write plan created the workspace")

    execute_result = transcripts.run(
        "submit-slurm-execute", [*scheduled_run, "--execute"], cwd=repo_root
    )
    execute_submission = parse_submission(
        execute_result.stdout,
        paths.workspace / "logs",
    )
    execute_job = wait_for_job(
        execute_submission,
        scontrol=scontrol,
        scancel=scancel,
        cwd=repo_root,
        timeout_seconds=arguments.slurm_timeout_seconds,
        poll_seconds=arguments.poll_seconds,
    )
    execute_stderr = _read_retained_stream(
        execute_job.stderr_path, "Slurm execution stderr"
    )
    if parse_run_plan(execute_stderr, paths.workspace, no_write=False) != run_root:
        raise DriverError(
            "slurm-execute", "Slurm execution selected a different Run root"
        )
    execute_receipt = parse_execution_evidence(execute_stderr, run_root)

    inspect_result = transcripts.run(
        "inspect-run",
        _emrys(
            workflow_python,
            "inspect",
            "local-pilot-run",
            "--run-root",
            str(run_root),
        ),
        cwd=repo_root,
    )
    if (
        "Attempt outcome: succeeded" not in inspect_result.stdout
        or "Scientific Results: complete" not in inspect_result.stdout
        or "Reporting: complete" not in inspect_result.stdout
    ):
        raise DriverError("inspect-run", "public inspection did not report completion")

    try:
        fixture_metadata = json.loads(
            (paths.inputs / "fixture.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DriverError(
            "assert-results", f"fixture metadata is unreadable: {exc}"
        ) from exc
    if not isinstance(fixture_metadata, dict):
        raise DriverError("assert-results", "fixture metadata must be a JSON object")
    if fixture_metadata.get("dataset_profile") != dataset_profile:
        raise DriverError(
            "assert-results", "fixture metadata selected a different dataset profile"
        )
    if fixture_metadata.get("read_pairs_per_library") != int(profile):
        raise DriverError(
            "assert-results",
            "fixture read-pair scale differs from the selected profile",
        )
    fixture_id = fixture_metadata.get("fixture_id")
    expected_workflow = fixture_metadata.get("expected_terminal_workflow")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise DriverError(
            "assert-results", "fixture metadata omits its fixture identity"
        )
    if (
        not isinstance(expected_workflow, dict)
        or expected_workflow.get("last_scientific_step") != "10"
        or expected_workflow.get("local_pipeline_complete") is not True
    ):
        raise DriverError(
            "assert-results",
            "fixture metadata omits the current Step 10 completion oracle",
        )
    completion = assert_completed_run(run_root, fixture_metadata)
    return {
        "schema_version": SUMMARY_SCHEMA,
        "status": "passed",
        "profile": profile,
        "dataset_profile": dataset_profile,
        "fixture_id": fixture_id,
        "read_pairs_per_library": fixture_metadata.get("read_pairs_per_library"),
        "operator_root": str(paths.operator_root),
        "runtime_profile": _artifact(paths.runtime_profile),
        "execution_profile": _artifact(paths.execution_profile),
        "gatk_attestation": gatk_attestation,
        "rseqc_attestation": rseqc_attestation,
        "gunzip_attestation": gunzip_attestation,
        "storage_compute_launcher": list(storage_launcher),
        "storage_qualification": storage_qualification,
        "slurm": {
            "partition": arguments.slurm_partition,
            "account": arguments.slurm_account,
            "qos": arguments.slurm_qos,
            "cpus": arguments.slurm_cpus,
            "memory_mb": arguments.slurm_memory,
            "dry_run": {
                "submitted": False,
                "stdout_pattern": str(dry_stdout_pattern),
                "stderr_pattern": str(dry_stderr_pattern),
            },
            "execute_job": _job_summary(execute_job),
            "attempt_receipt": _artifact(execute_receipt),
        },
        "completion": completion,
        "commands": transcripts.records,
        "retention": "complete operator root retained; no cleanup or repair performed",
        "evidence_boundary": (
            "real-tool single-node Slurm synthetic workflow evidence only; not "
            "production-data, scientific-review, biological-validation, or biological-interpretation evidence"
        ),
        "biological_interpretation_claimed": False,
    }


def _failure_summary(
    arguments: argparse.Namespace,
    transcripts: Transcripts,
    error: Exception,
) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA,
        "status": "failed",
        "profile": str(arguments.profile),
        "dataset_profile": PROFILE_DATASETS.get(str(arguments.profile)),
        "operator_root": str(Path(arguments.operator_root).absolute()),
        "failed_stage": error.stage if isinstance(error, DriverError) else "internal",
        "error": str(error),
        "commands": transcripts.records,
        "retention": "all created roots, partials, logs, and receipts retained; no cleanup or repair performed",
        "evidence_boundary": "failed synthetic E2E attempt; no completion or biological claim",
        "biological_interpretation_claimed": False,
    }


def _publish_summary(path: Path, summary: dict[str, Any]) -> None:
    data = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_exclusive(path, data)
    print(f"Machine-readable E2E summary: {path}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if not arguments.execute:
        print(
            json.dumps(
                {
                    "schema_version": SUMMARY_SCHEMA,
                    "operation": "plan",
                    "profile": arguments.profile,
                    "dataset_profile": PROFILE_DATASETS[arguments.profile],
                    "repo_root": str(Path(arguments.repo_root).absolute()),
                    "operator_root": str(Path(arguments.operator_root).absolute()),
                    "slurm_partition": arguments.slurm_partition,
                    "stages": [
                        "initialize fixture",
                        "prepare exact runtime profile",
                        "validate request",
                        "two-phase storage qualification",
                        "doctor",
                        "no-write workflow plan",
                        "single-node Slurm plan",
                        "single-node Slurm execution",
                        "read-only inspection and direct result assertions",
                    ],
                    "evidence_boundary": (
                        "planned synthetic execution only; no runtime, workflow, "
                        "production, scientific-review, or biological evidence"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        print("Dry-run complete; no directories or files were created.")
        return 0
    transcript_root = Path(arguments.operator_root).absolute() / "driver-transcripts"
    transcripts = Transcripts(transcript_root)
    summary_path = Path(arguments.operator_root).absolute() / "e2e-summary.json"
    try:
        summary = run_driver(arguments, transcripts)
    except Exception as exc:
        summary = _failure_summary(arguments, transcripts, exc)
        try:
            if transcripts.operator_root_admitted and not summary_path.exists():
                _publish_summary(summary_path, summary)
        except OSError as summary_error:
            print(
                f"ERROR: could not publish failure summary: {summary_error}",
                file=sys.stderr,
            )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    _publish_summary(summary_path, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
