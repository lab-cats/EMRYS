#!/usr/bin/env python3
"""Prove retained real-tool direct/Slurm parity on one synthetic EMRYS Run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import select
import signal
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUMMARY_SCHEMA = "emrys.ci-real-synthetic-e2e-summary.v6"
PROFILE_DATASETS = {"130": "smoke-v1", "100000": "production-like-v1"}
DISCOVERY_UTILITIES = ("basename", "dirname", "grep", "rm", "uname")
TERMINAL_STATES = frozenset(
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
RUN_ROOT = re.compile(r"^Location: (/.+/runs/run-[a-f0-9]{64})$", re.MULTILINE)
REQUEST_ROOT = re.compile(
    r"^Submission request: (/.+/logs/submission-[0-9a-f]{32})$", re.MULTILINE
)
JOB_ID = re.compile(r"^JOB_ID=([1-9][0-9]*)$", re.MULTILINE)
OUT = re.compile(r"^OUT=(/.+)$", re.MULTILINE)
ERR = re.compile(r"^ERR=(/.+)$", re.MULTILINE)
STATE = re.compile(r"(?:^| )JobState=([A-Z_]+)")
EXIT = re.compile(r"(?:^| )ExitCode=([0-9]+:[0-9]+)")
# Step09 is compared after removing placement-local locators and the digest of
# the Step08 receipt that contains those locators.
SCIENTIFIC_RESULT_SUFFIXES = (
    ".cmh_all_sites.tsv",
    ".cmh_significant_sites.tsv",
    ".mutation_spectrum.tsv",
    ".candidate_context.tsv",
    ".motif_hits.tsv",
    ".sequence_logo.tsv",
    ".motif_statistics.tsv",
)
STEP09_LOCAL_PATH_FIELDS = frozenset(
    {
        "sample_manifest_path",
        "partition_manifest_path",
        "step08_sites_path",
        "step08_inputs_path",
        "step08_inputs_sha256",
    }
)
TASK_ENTRY_EVIDENCE_FIELDS = (
    "task_attempt_records",
    "task_start_records",
    "verified_tasks",
)
APPLICATION_EVENTS = (
    "attempt_opened",
    "analysis_prepared",
    "analysis_started",
    "publication_ready",
    "attempt_receipt_observed",
    "reporting_started",
    "reporting_completed",
)
FAILURE_APPLICATION_EVENTS = APPLICATION_EVENTS[:-2]


class DriverError(RuntimeError):
    """One E2E stage failed; retained state remains untouched."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


@dataclass(frozen=True, slots=True)
class Paths:
    root: Path
    direct_workspace: Path
    slurm_workspace: Path
    scratch: Path
    execution_profile: Path
    adapters: Path
    transcripts: Path

    @property
    def native_gate(self) -> Path:
        return self.scratch / "native-stop-gate"


@dataclass(frozen=True, slots=True)
class Runtime:
    bash: Path
    star: Path
    samtools: Path
    gatk: Path
    bcftools: Path
    python: Path
    rseqc: Path
    gunzip: Path
    java: Path
    picard: Path
    rscript: Path
    renv: Path
    discovery_utilities: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class Job:
    job_id: str
    stdout: Path
    stderr: Path
    state: str = ""
    exit_code: str = ""


@dataclass(frozen=True, slots=True)
class NativeGate:
    pid: int
    descriptor: int
    attempt_id: str
    task: str


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
    matched = re.fullmatch(r"([1-9][0-9]*)([MG])", value)
    if matched is None:
        raise argparse.ArgumentTypeError("must be a positive size such as 6144M or 6G")
    amount = int(matched.group(1))
    return amount if matched.group(2) == "M" else amount * 1024


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=tuple(PROFILE_DATASETS))
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--operator-root", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--rscript", required=True, type=Path)
    parser.add_argument("--renv-library", required=True, type=Path)
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
    parser.add_argument("--execute", action="store_true")
    return parser


def _real(
    path: Path,
    label: str,
    *,
    directory: bool = False,
    executable: bool = False,
) -> Path:
    try:
        selected = Path(os.path.abspath(path)).resolve(strict=True)
    except OSError as exc:
        raise DriverError(
            "preflight", f"{label} is unavailable: {path}: {exc}"
        ) from exc
    if directory != selected.is_dir() or (not directory and not selected.is_file()):
        kind = "directory" if directory else "file"
        raise DriverError("preflight", f"{label} must be one real {kind}: {selected}")
    if executable and not os.access(selected, os.X_OK):
        raise DriverError("preflight", f"{label} is not executable: {selected}")
    return selected


def _command(path: Path | None, name: str) -> Path:
    selected = str(path) if path is not None else shutil.which(name)
    if not selected:
        raise DriverError("preflight", f"required command is unavailable: {name}")
    return _real(Path(selected), name, executable=True)


def _workflow_python(repo: Path) -> Path:
    """Keep the lexical virtualenv launcher so Python selects that environment."""

    selected = Path(os.path.abspath(repo / ".venv/bin/python"))
    if (
        not selected.exists()
        or not selected.is_file()
        or not os.access(selected, os.X_OK)
    ):
        raise DriverError("preflight", f"workflow Python is unavailable: {selected}")
    return selected


def require_operator_root(operator_root: Path, repo_root: Path) -> Paths:
    root = _real(operator_root, "operator root", directory=True)
    repo = _real(repo_root, "repository root", directory=True)
    if root == repo or root.is_relative_to(repo):
        raise DriverError(
            "preflight", "operator root must be outside the source checkout"
        )
    if any(root.iterdir()):
        raise DriverError(
            "preflight",
            "operator root must be empty; existing contents were preserved",
        )
    if not os.access(root, os.R_OK | os.W_OK | os.X_OK):
        raise DriverError("preflight", "operator root is not usable")
    return Paths(
        root,
        root / "direct",
        root / "slurm",
        root / "scratch",
        root / "slurm/runtime/profiles/ci.yaml",
        root / "runtime-adapters",
        root / "driver-transcripts",
    )


def _selected_workspaces(paths: Paths, profile: str) -> dict[str, Path]:
    if profile == "130":
        return {"direct": paths.direct_workspace, "slurm": paths.slurm_workspace}
    return {"slurm": paths.slurm_workspace}


def resolve_runtime(prefix: Path, rscript: Path, renv: Path) -> Runtime:
    root = _real(prefix, "runtime prefix", directory=True)
    jars = tuple(root.glob("share/picard-slim-3.1.1-*/picard.jar"))
    if len(jars) != 1:
        raise DriverError(
            "preflight", "runtime prefix must contain one Picard 3.1.1 jar"
        )

    def tool(relative: str, label: str) -> Path:
        return _real(root / relative, label, executable=True)

    python = Path(os.path.abspath(root / "bin/python"))
    if not python.exists() or not os.access(python, os.X_OK):
        raise DriverError("preflight", f"runtime Python is unavailable: {python}")
    return Runtime(
        _command(None, "bash"),
        tool("bin/STAR", "STAR"),
        tool("bin/samtools", "samtools"),
        tool("bin/gatk", "GATK"),
        tool("bin/bcftools", "bcftools"),
        python,
        tool("bin/infer_experiment.py", "RSeQC"),
        tool("bin/gunzip", "gunzip"),
        tool("bin/java", "Java"),
        _real(jars[0], "Picard jar"),
        _real(rscript, "Rscript", executable=True),
        _real(renv, "renv library", directory=True),
        tuple(tool(f"bin/{name}", name) for name in DISCOVERY_UTILITIES),
    )


def _safe_adapter(*paths: Path) -> tuple[str, ...]:
    values = tuple(str(path) for path in paths)
    if any(
        not path.is_absolute() or "\n" in value or "\r" in value
        for path, value in zip(paths, values, strict=True)
    ):
        raise DriverError("preflight", "adapter paths must be absolute and line-safe")
    return values


def rseqc_adapter_bytes(python: Path, delegate: Path) -> bytes:
    py, target = _safe_adapter(python, delegate)
    return (
        "#!/bin/sh\nset -eu\n"
        'if [ "$#" -eq 1 ] && [ "$1" = "--version" ]; then exec '
        f'{shlex.quote(py)} -I -B -c "from importlib.metadata import version; '
        "print('infer_experiment.py ' + version('RSeQC'))\"; fi\n"
        f'exec {shlex.quote(py)} -I -B {shlex.quote(target)} "$@"\n'
    ).encode()


def gatk_adapter_bytes(python: Path, delegate: Path, java: Path) -> bytes:
    py, target, _java = _safe_adapter(python, delegate, java)
    if java.name != "java" or java.parent.name != "bin":
        raise DriverError("preflight", "runtime Java must be <JAVA_HOME>/bin/java")
    java_home = java.parent.parent
    sealed_path = os.pathsep.join((str(java.parent), "/usr/bin", "/bin"))
    return (
        "#!/bin/sh\nset -eu\n"
        "unset CLASSPATH GATK_JAR GATK_LOCAL_JAR JAVA_OPTS JAVA_TOOL_OPTIONS "
        "JDK_JAVA_OPTIONS _JAVA_OPTIONS\n"
        f"export JAVA_HOME={shlex.quote(str(java_home))} "
        f"PATH={shlex.quote(sealed_path)}\n"
        f'exec {shlex.quote(py)} -I -B {shlex.quote(target)} "$@"\n'
    ).encode()


def gunzip_adapter_bytes(delegate: Path) -> bytes:
    (target,) = _safe_adapter(delegate)
    quoted = shlex.quote(target)
    return (
        "#!/bin/sh\nset -eu\n"
        'if [ "$#" -eq 1 ] && [ "$1" = "--version" ]; then exec '
        f'{quoted} --version; fi\nexec {quoted} -d "$@"\n'
    ).encode()


def samtools_gate_adapter_bytes(delegate: Path, gate: Path) -> bytes:
    """Pass through except for one armed Task invocation with a real native child."""

    target, armed, claimed, fifo, ready = _safe_adapter(
        delegate,
        gate.with_suffix(".armed"),
        gate.with_suffix(".claimed"),
        gate.with_suffix(".fifo"),
        gate.with_suffix(".ready"),
    )
    return (
        "#!/bin/bash\nset -euo pipefail\n"
        f'if [[ -n "${{EMRYS_TASK_WORK_DIR:-}}" && "${{1:-}}" == view ]] '
        f"&& [ -f {shlex.quote(armed)} ] "
        f"&& /bin/mkdir -- {shlex.quote(claimed)} 2>/dev/null; then\n"
        f"  /bin/rm -f -- {shlex.quote(armed)}\n"
        f"  /usr/bin/mkfifo -- {shlex.quote(fifo)}\n"
        '  args=("$@")\n'
        f"  args[${{#args[@]}}-1]={shlex.quote(fifo)}\n"
        f'  {shlex.quote(target)} "${{args[@]}}" &\n'
        "  native=$!\n"
        f'  printf \'%s\\0%s\\0\' "$native" "$EMRYS_TASK_WORK_DIR" > {shlex.quote(ready)}.tmp\n'
        f"  /bin/mv -- {shlex.quote(ready)}.tmp {shlex.quote(ready)}\n"
        '  wait "$native"\n'
        "  exit $?\n"
        "fi\n"
        f'exec {shlex.quote(target)} "$@"\n'
    ).encode()


def controlled_failure_module_init_bytes(profile: Path, marker: Path) -> bytes:
    missing, armed = _safe_adapter(profile, marker)
    return (
        "module() {\n"
        '  case "$1:$#" in\n'
        "    purge:1|load:2) return 0 ;;\n"
        "    *) return 2 ;;\n"
        "  esac\n"
        "}\n"
        f"if [ -e {shlex.quote(armed)} ]; then\n"
        f"  /bin/rm -f -- {shlex.quote(armed)}\n"
        f"  export SNAKEMAKE_PROFILE={shlex.quote(missing)}\n"
        "fi\n"
    ).encode()


def _write(path: Path, data: bytes, *, mode: int = 0o600) -> None:
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


def _artifact(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DriverError(
            "assert-results", f"required result is not a real file: {path}"
        )
    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def runtime_environment(paths: Paths, runtime: Runtime) -> dict[str, str]:
    for name, target in (
        ("bash", runtime.bash),
        ("STAR", runtime.star),
        ("bcftools", runtime.bcftools),
        ("java", runtime.java),
    ):
        (paths.adapters / name).symlink_to(target)
    _write(
        paths.adapters / "samtools",
        samtools_gate_adapter_bytes(runtime.samtools, paths.native_gate),
        mode=0o700,
    )
    for target in runtime.discovery_utilities:
        (paths.adapters / target.name).symlink_to(target)
    return {
        **os.environ,
        "PATH": str(paths.adapters),
        "JAVA_HOME": str(runtime.java.parent.parent),
        "EMRYS_PICARD_JAR": str(runtime.picard),
        "EMRYS_RSCRIPT": str(runtime.rscript),
        "EMRYS_RENV_LIBRARY": str(runtime.renv),
    }


def symbolic_resource_document() -> dict[str, Any]:
    """Explicit small budget for symbolic-admission tests and hosted E2E."""
    from emrys.orchestration.run_coordinator.resource_policy import (
        REPEATABLE_STAGE_IDS,
        STAGE_IDS,
    )

    return {
        "schema_version": "emrys.local-pilot-resources.v1",
        "workflow_cores": 4,
        "workflow_memory_mb": "allocation",
        "stage_concurrency": {step_id: 1 for step_id in REPEATABLE_STAGE_IDS},
        "step_threads": {
            "00a": 4,
            "00c": 1,
            "01": 4,
            "02": 1,
            "02b": 1,
            "04": 1,
            "05": 1,
            "06": 4,
            "08": 1,
            "09": 1,
            "10": 1,
        },
        "stage_memory_mb": {step_id: "workflow" for step_id in STAGE_IDS},
    }


def slurm_execution_profile_bytes(
    *,
    account: str | None,
    partition: str,
    qos: str | None,
    cpus_per_task: int,
    memory_mb: int,
    time_limit: str,
    nodelist: str | None,
    scratch_parent: Path,
    module_init: Path | None = None,
) -> bytes:
    from emrys.contracts.orchestration import api as contracts
    from emrys.orchestration.run_coordinator.execution_profile import SCHEMA_VERSION

    try:
        document = {
            "schema_version": SCHEMA_VERSION,
            "resources": symbolic_resource_document(),
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
                "modules": (
                    {"mode": "none", "init": "", "load": []}
                    if module_init is None
                    else {
                        "mode": "exact",
                        "init": str(module_init),
                        "load": ["emrys-ci-controlled-failure"],
                    }
                ),
            },
        }
        contracts.validate_record("execution-profile", document)
        return contracts.canonical_json_bytes(document) + b"\n"
    except Exception as exc:
        raise DriverError("prepare-execution-profile", str(exc)) from exc


class Transcripts:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records: list[dict[str, Any]] = []
        self.operator_root_admitted = False

    def run(
        self,
        stage: str,
        argv: list[str] | tuple[str, ...],
        *,
        cwd: Path,
        environment: dict[str, str] | None = None,
        expected_returncode: int | None = 0,
        timeout_seconds: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        selected = tuple(map(str, argv))
        print(f"E2E stage {stage}: {shlex.join(selected)}", flush=True)
        label = re.sub(r"[^a-z0-9-]+", "-", stage.lower())
        stem = f"{len(self.records) + 1:02d}-{label}"
        stdout = self.root / f"{stem}.stdout.log"
        stderr = self.root / f"{stem}.stderr.log"
        try:
            result = subprocess.run(
                selected,
                cwd=cwd,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            for path, partial in ((stdout, exc.stdout), (stderr, exc.stderr)):
                data = partial or b""
                _write(path, data.encode() if isinstance(data, str) else data)
            self.records.append(
                {
                    "stage": stage,
                    "argv": list(selected),
                    "returncode": None,
                    "timed_out": True,
                    "stdout": str(stdout),
                    "stderr": str(stderr),
                }
            )
            raise DriverError(
                stage,
                f"command timed out; partial streams retained: {stdout}, {stderr}",
            ) from exc
        except OSError as exc:
            raise DriverError(stage, f"could not execute command: {exc}") from exc
        _write(stdout, result.stdout.encode())
        _write(stderr, result.stderr.encode())
        self.records.append(
            {
                "stage": stage,
                "argv": list(selected),
                "returncode": result.returncode,
                "stdout": str(stdout),
                "stderr": str(stderr),
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
        if expected_returncode is not None and result.returncode != expected_returncode:
            raise DriverError(
                stage,
                f"command exited {result.returncode}, expected {expected_returncode}; "
                f"retained streams: {stdout}, {stderr}",
            )
        return result


def _one(pattern: re.Pattern[str], text: str, label: str, stage: str) -> str:
    values = pattern.findall(text)
    if len(values) != 1:
        raise DriverError(stage, f"expected one {label}; observed {len(values)}")
    return values[0]


def parse_run_plan(text: str, workspace: Path, *, no_write: bool) -> Path:
    run_root = Path(_one(RUN_ROOT, text, "run root", "plan-workflow"))
    if run_root.parent != workspace / "runs":
        raise DriverError("plan-workflow", "Run plan root differs")
    if "Reporting: automatic after scientific work" not in text or (
        no_write and "Dry-run complete; no workspace state was written." not in text
    ):
        raise DriverError(
            "plan-workflow",
            "Run plan omitted reporting or no-write assurance",
        )
    return run_root


def parse_submission(text: str, log_dir: Path) -> Job:
    job_id = _one(JOB_ID, text, "job ID", "submit-slurm")
    job = Job(
        job_id,
        Path(_one(OUT, text, "stdout", "submit-slurm")),
        Path(_one(ERR, text, "stderr", "submit-slurm")),
    )
    if (
        job.stdout.parent != log_dir
        or re.fullmatch(rf"emrys-[0-9a-f]{{32}}-{job_id}\.out", job.stdout.name) is None
        or job.stderr != job.stdout.with_suffix(".err")
    ):
        raise DriverError("submit-slurm", "submission stream paths differ")
    return job


def parse_submission_request(
    output: subprocess.CompletedProcess[str], workspace: Path
) -> Path:
    request = Path(
        _one(REQUEST_ROOT, output.stderr, "submission request", "submit-slurm")
    )
    if request.parent != workspace / "logs":
        raise DriverError(
            "submit-slurm", "submission request belongs to another Project"
        )
    return request


def parse_scontrol(text: str) -> tuple[str, str]:
    state, exit_code = STATE.search(text), EXIT.search(text)
    if state is None or exit_code is None:
        raise DriverError("wait-slurm", "scontrol omitted JobState or ExitCode")
    return state.group(1), exit_code.group(1)


def _stream(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise DriverError("wait-slurm", f"retained stream is unavailable: {path}")
    return path.read_text(encoding="utf-8")


def _scheduler(argv: tuple[str, ...], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv, cwd=cwd, text=True, capture_output=True, check=False, timeout=10
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            argv, 124, "", "scheduler observation timed out after 10 seconds"
        )


def cancel_job(
    job_id: str,
    *,
    scancel: Path,
    scontrol: Path,
    cwd: Path,
    poll_seconds: float,
    timeout_seconds: float = 30.0,
) -> str:
    result = _scheduler((str(scancel), "--signal=TERM", job_id), cwd)
    if result.returncode:
        raise DriverError("cancel-slurm", f"scancel failed: {result.stderr.strip()}")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        observed = _scheduler((str(scontrol), "show", "job", "-o", job_id), cwd)
        if observed.returncode:
            return "NO_LONGER_OBSERVABLE"
        state, _ = parse_scontrol(observed.stdout)
        if state in TERMINAL_STATES:
            return state
        time.sleep(min(poll_seconds, 1.0))
    raise DriverError(
        "cancel-slurm", f"job {job_id} did not become terminal after TERM"
    )


def _emergency_cancel(
    job_id: str,
    *,
    scancel: Path,
    scontrol: Path,
    cwd: Path,
    poll_seconds: float,
    original: BaseException,
) -> None:
    """Release only a known disposable job after a pre-stop driver failure."""

    try:
        cancel_job(
            job_id,
            scancel=scancel,
            scontrol=scontrol,
            cwd=cwd,
            poll_seconds=poll_seconds,
        )
    except DriverError as exc:
        raise DriverError(
            "native-stop", f"{original}; emergency cleanup uncertain: {exc}"
        ) from original


def wait_for_job(
    submission: str,
    *,
    log_dir: Path,
    scontrol: Path,
    scancel: Path,
    cwd: Path,
    timeout_seconds: int,
    poll_seconds: float,
    expected: tuple[str, str] | None = ("COMPLETED", "0:0"),
    cleanup_on_failure: bool = True,
) -> Job:
    # A single reported job ID is required before any cancellation is safe.
    job_id = _one(JOB_ID, submission, "job ID", "submit-slurm")
    deadline = time.monotonic() + timeout_seconds
    try:
        job = parse_submission(submission, log_dir)
        while True:
            if time.monotonic() >= deadline:
                raise DriverError("wait-slurm", "job timed out")
            result = _scheduler((str(scontrol), "show", "job", "-o", job.job_id), cwd)
            if result.returncode:
                raise DriverError(
                    "wait-slurm", f"scontrol failed: {result.stderr.strip()}"
                )
            state, exit_code = parse_scontrol(result.stdout)
            if state in TERMINAL_STATES:
                break
            time.sleep(poll_seconds)
    except (DriverError, KeyboardInterrupt) as exc:
        if not cleanup_on_failure:
            raise
        disposition = cancel_job(
            job_id,
            scancel=scancel,
            scontrol=scontrol,
            cwd=cwd,
            poll_seconds=poll_seconds,
        )
        reason = "interrupted" if isinstance(exc, KeyboardInterrupt) else str(exc)
        raise DriverError(
            "wait-slurm",
            f"{reason}; cancellation: {disposition}",
        ) from None
    stream_deadline = time.monotonic() + min(30.0, timeout_seconds)
    while (
        not job.stdout.exists() or not job.stderr.exists()
    ) and time.monotonic() < stream_deadline:
        time.sleep(min(poll_seconds, 1.0))
    stdout, stderr = _stream(job.stdout), _stream(job.stderr)
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
    completed = Job(job.job_id, job.stdout, job.stderr, state, exit_code)
    if expected is not None and (state, exit_code) != expected:
        raise DriverError(
            "wait-slurm",
            f"job ended {state} with {exit_code}, expected {expected}; streams retained",
        )
    return completed


def await_native_gate(
    gate: Path,
    run_root: Path,
    job: Job,
    *,
    samtools: Path,
    scontrol: Path,
    cwd: Path,
    poll_seconds: float,
    timeout_seconds: float = 300.0,
) -> NativeGate:
    from emrys.orchestration.run_coordinator import inspection

    ready = gate.with_suffix(".ready")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if ready.exists():
            if ready.is_symlink() or not ready.is_file():
                raise DriverError("native-stop", "native readiness is not a real file")
            fields = ready.read_bytes().split(b"\0")
            if (
                len(fields) != 3
                or fields[-1]
                or re.fullmatch(rb"[1-9][0-9]*", fields[0]) is None
            ):
                raise DriverError("native-stop", "native readiness is malformed")
            pid = int(fields[0])
            work_directory = Path(os.fsdecode(fields[1]))
            if not work_directory.is_relative_to(run_root.parent.parent):
                raise DriverError("native-stop", "native Task work root differs")
            try:
                executable = Path(os.readlink(f"/proc/{pid}/exe")).resolve()
                argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            except (OSError, ValueError):
                time.sleep(min(poll_seconds, 0.1))
                continue
            if executable != samtools or len(argv) < 2 or argv[1] != b"view":
                time.sleep(min(poll_seconds, 0.1))
                continue
            observed = inspection.inspect_run(run_root)
            attempt = observed.latest_attempt
            active = []
            if attempt is not None:
                for task in observed.tasks:
                    if task.start_reference is None or task.record is not None:
                        continue
                    if task.start_origin != attempt["workflow_attempt_id"]:
                        continue
                    planned = attempt["tasks"][task.expected.machine_key][
                        task.expected.scope_id
                    ]
                    working = Path(planned["outputs"][0]["working_path"]).parent
                    if work_directory == working.with_name(working.name + ".scratch"):
                        active.append(task)
            if observed.attempt_outcome == "running" and len(active) == 1:
                descriptor = os.pidfd_open(pid)
                return NativeGate(
                    pid,
                    descriptor,
                    str(attempt["workflow_attempt_id"]),
                    f"{active[0].expected.machine_key}/{active[0].expected.scope_id}",
                )
        status = _scheduler((str(scontrol), "show", "job", "-o", job.job_id), cwd)
        if status.returncode:
            raise DriverError("native-stop", "scheduler lost the selected job")
        state, _ = parse_scontrol(status.stdout)
        if state in TERMINAL_STATES:
            raise DriverError(
                "native-stop", f"job became {state} before native readiness"
            )
        time.sleep(min(poll_seconds, 0.2))
    raise DriverError("native-stop", "native Task readiness timed out")


def await_native_exit(gate: NativeGate, *, timeout_seconds: float = 120.0) -> None:
    exited, _, _ = select.select([gate.descriptor], [], [], timeout_seconds)
    if not exited:
        raise DriverError("native-stop", "native process survived controller stop")


def validate_step09_oracle(
    all_sites: Path,
    significant_sites: Path,
    fixture: dict[str, Any],
) -> dict[str, Any]:
    def table(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", strict=True)
            rows = list(reader)
        if not reader.fieldnames or not {
            "candidate_id",
            "call_status",
        } <= set(reader.fieldnames):
            raise DriverError("assert-results", f"Step09 columns differ: {path}")
        return rows

    all_rows, significant = table(all_sites), table(significant_sites)
    expected = fixture.get("expected_terminal_computational_result", {})
    candidate = (
        expected.get("significant_candidate_id") if isinstance(expected, dict) else None
    )
    all_ids = [row["candidate_id"] for row in all_rows]
    if (
        expected.get("all_sites_rows") != 3
        or expected.get("significant_sites_rows") != 1
        or len(all_rows) != 3
        or len(significant) != 1
        or len(set(all_ids)) != 3
        or significant[0]["candidate_id"] != candidate
        or candidate not in all_ids
        or significant[0]["call_status"] not in {"significant_up", "significant_down"}
    ):
        raise DriverError("assert-results", "independent Step09 3/1 oracle differs")
    return {
        "all_sites_rows": 3,
        "significant_sites_rows": 1,
        "significant_candidate_id": candidate,
        "all_sites": _artifact(all_sites),
        "significant_sites": _artifact(significant_sites),
    }


def assert_completed_run(
    run_root: Path,
    fixture: dict[str, Any],
    *,
    observed: Any | None = None,
) -> dict[str, Any]:
    from emrys.orchestration.run_coordinator import inspection

    observed = inspection.inspect_run(run_root) if observed is None else observed
    if (
        observed.integrity,
        observed.attempt_outcome,
        observed.results_status,
        observed.reporting_status,
        observed.recovery_available,
    ) != ("valid", "succeeded", "complete", "complete", False) or observed.blockers:
        raise DriverError("assert-results", "Run inspection is not complete")
    reports = dict(observed.verified_report_locations)
    if set(reports) != {"scientific-report-html", "evidence-report-html"}:
        raise DriverError("assert-results", "verified report locations differ")
    all_sites = tuple(run_root.glob("results/editing/*/*.cmh_all_sites.tsv"))
    significant = tuple(run_root.glob("results/editing/*/*.cmh_significant_sites.tsv"))
    if len(all_sites) != 1 or len(significant) != 1:
        raise DriverError("assert-results", "Step09 result locations are ambiguous")
    oracle = validate_step09_oracle(
        all_sites[0],
        significant[0],
        fixture,
    )
    return {
        "run_id": observed.run_id,
        "run_root": str(run_root),
        "step09_oracle": oracle,
        "reports": {name: _artifact(path) for name, path in reports.items()},
    }


def _scientific_result_hashes(run_root: Path) -> dict[str, dict[str, Any]]:
    results = run_root / "results"
    selected: dict[str, dict[str, Any]] = {}
    for suffix in SCIENTIFIC_RESULT_SUFFIXES:
        matches = tuple(results.rglob(f"*{suffix}"))
        if len(matches) != 1:
            raise DriverError(
                "assert-parity",
                f"expected one terminal scientific result ending {suffix}; "
                f"observed {len(matches)}",
            )
        artifact = _artifact(matches[0])
        selected[matches[0].relative_to(results).as_posix()] = {
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }
    summaries = tuple(results.rglob("*.cmh_summary.tsv"))
    if len(summaries) != 1:
        raise DriverError(
            "assert-parity",
            f"expected one Step09 summary; observed {len(summaries)}",
        )
    selected[summaries[0].relative_to(results).as_posix()] = {
        "semantic_fields": _step09_summary_projection(summaries[0])
    }
    return selected


def _step09_summary_projection(path: Path) -> dict[str, str]:
    from emrys.contracts.scientific_evidence.step09 import STEP09_SUMMARY_HEADER

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        rows = list(reader)
    if tuple(reader.fieldnames or ()) != STEP09_SUMMARY_HEADER or len(rows) != 1:
        raise DriverError("assert-parity", f"Step09 summary shape differs: {path}")
    return {
        field: rows[0][field]
        for field in STEP09_SUMMARY_HEADER
        if field not in STEP09_LOCAL_PATH_FIELDS
    }


def _tree_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    if root.is_symlink() or not root.is_dir():
        raise DriverError("assert-parity", f"retained evidence root differs: {root}")
    return {
        path.relative_to(root).as_posix(): _artifact(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() or path.is_symlink()
    }


def _execution_state(workspace: Path) -> dict[str, Any]:
    return {
        name: (
            tuple(sorted((workspace / name).rglob("*"))),
            _tree_artifacts(workspace / name),
        )
        for name in ("runs", "logs")
    }


def _predecessor_evidence(
    run_root: Path,
    attempt_id: str,
    job: Job | None,
    application_log: dict[str, Any],
) -> dict[str, Any]:
    return {
        "attempt_root": str(run_root / "attempts" / attempt_id),
        "attempt_artifacts": _tree_artifacts(run_root / "attempts" / attempt_id),
        "application_log": application_log,
        "scheduler_streams": {
            name: _artifact(path)
            for name, path in (
                () if job is None else (("stdout", job.stdout), ("stderr", job.stderr))
            )
        },
    }


def _assert_predecessor_preserved(snapshot: dict[str, Any]) -> None:
    attempt_root = Path(str(snapshot["attempt_root"]))
    streams = snapshot["scheduler_streams"]
    observed = {
        "attempt_root": str(attempt_root),
        "attempt_artifacts": _tree_artifacts(attempt_root),
        "application_log": _artifact(Path(str(snapshot["application_log"]["path"]))),
        "scheduler_streams": {
            name: _artifact(Path(str(artifact["path"])))
            for name, artifact in streams.items()
        },
    }
    if observed != snapshot:
        raise DriverError("assert-parity", "Resume changed predecessor evidence")


def _assert_no_task_entry(
    task_roster: list[dict[str, Any]],
    receipt: dict[str, Any],
) -> None:
    if {item["state"] for item in task_roster} != {"pending"}:
        raise DriverError(
            "assert-parity", "Controlled pre-entry failure entered a task"
        )
    if any(receipt.get(field) for field in TASK_ENTRY_EVIDENCE_FIELDS):
        raise DriverError(
            "assert-parity",
            "Controlled pre-entry failure retained task-entry evidence",
        )


def _resource_snapshot(
    attempt: dict[str, Any],
) -> dict[str, Any]:
    from emrys.orchestration.run_coordinator.resource_policy import (
        admit_resource_policy_record,
    )

    try:
        plan = admit_resource_policy_record(attempt["workflow"]["resource_policy"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DriverError(
            "assert-parity",
            f"Attempt resource policy is malformed: {exc}",
        ) from exc
    allocation = plan.allocation
    return {
        "symbolic": plan.policy.document(),
        "effective": plan.effective_document(),
        "allocation": {
            "cores": allocation.cores,
            "memory_mb": allocation.memory_mb,
            "source": allocation.source,
            "slurm_job_id": allocation.slurm_job_id,
        },
    }


def _application_log_snapshot(
    workspace: Path,
    *,
    run_id: str,
    attempt_id: str,
    scheduler_job_id: str | None,
    operation: str,
    expected_status: str,
) -> dict[str, Any]:
    resumed = operation == "resume"
    entrypoint = "emrys-resume" if resumed else "emrys-run"
    scope_id = run_id if resumed else "pending"
    required_events = (
        APPLICATION_EVENTS
        if expected_status == "succeeded"
        else FAILURE_APPLICATION_EVENTS
    )
    logs = tuple(sorted((workspace / "logs/application").rglob("*.jsonl")))
    matches: list[tuple[Path, list[dict[str, Any]]]] = []
    for path in logs:
        try:
            records = [json.loads(line) for line in path.read_text().splitlines()]
        except (OSError, json.JSONDecodeError) as exc:
            raise DriverError(
                "assert-parity", f"Application log is malformed: {path}: {exc}"
            ) from exc
        if any(
            record.get("event") == "analysis_prepared"
            and record.get("fields")
            == {"run_id": run_id, "workflow_attempt_id": attempt_id}
            for record in records
        ):
            matches.append((path, records))
    if len(matches) != 1:
        raise DriverError(
            "assert-parity",
            f"expected one application log for Attempt {attempt_id}; "
            f"observed {len(matches)}",
        )
    path, records = matches[0]
    artifact = _artifact(path)
    if not records or [record.get("sequence") for record in records] != list(
        range(1, len(records) + 1)
    ):
        raise DriverError("assert-parity", "Application-log sequence is not contiguous")
    expected_metadata = {
        "scope_kind": "run",
        "scope_id": scope_id,
        "entrypoint": entrypoint,
        "mode": operation,
    }
    if (
        any(
            any(record.get(name) != value for name, value in expected_metadata.items())
            for record in records
        )
        or len({record.get("execution_attempt_id") for record in records}) != 1
    ):
        raise DriverError("assert-parity", "Application log scope is inconsistent")
    events = [str(record.get("event")) for record in records]
    cursor = -1
    for event_name in required_events:
        try:
            cursor = events.index(event_name, cursor + 1)
        except ValueError as exc:
            raise DriverError(
                "assert-parity",
                f"Application log omitted ordered event {event_name}",
            ) from exc
    if expected_status != "succeeded" and any(
        event_name in events for event_name in APPLICATION_EVENTS[-2:]
    ):
        raise DriverError("assert-parity", "Application log contains a forbidden event")
    opened = records[events.index("attempt_opened")]
    opening_fields = opened.get("fields")
    if not isinstance(opening_fields, dict):
        raise DriverError(
            "assert-parity", "Application-log opening fields are malformed"
        )
    observed_job = opening_fields.get("slurm_job_id")
    if observed_job != scheduler_job_id:
        raise DriverError("assert-parity", "Application-log scheduler identity differs")
    terminal = records[events.index("attempt_receipt_observed")].get("fields")
    if not isinstance(terminal, dict) or terminal.get("status") != expected_status:
        raise DriverError("assert-parity", "Application-log receipt status differs")
    return {
        "path": artifact,
        "scheduler_job_id": observed_job,
    }


def _authority_snapshot(authority: Any) -> dict[str, Any]:
    records = (
        ("analysis", authority.analysis_revision, "analysis_revision_id"),
        ("execution_plan", authority.execution_plan, "execution_plan_id"),
        ("run", authority.run_binding, "run_id"),
    )
    return {
        name: {"id": getattr(record, identity), "sha256": record.record_sha256}
        for name, record, identity in records
    }


def _task_roster(observed: Any) -> list[dict[str, Any]]:
    return [
        {
            "machine_key": task.expected.machine_key,
            "step_id": task.expected.step_id,
            "scope_type": task.expected.scope_type,
            "scope_id": task.expected.scope_id,
            "state": task.state,
        }
        for task in observed.tasks
    ]


def _attempt_snapshot(
    run_root: Path,
    observed: Any,
    attempt: dict[str, Any],
    receipt: dict[str, Any],
    *,
    job: Job | None,
    expected_status: str,
    expected_exit_code: int,
    operation: str,
) -> dict[str, Any]:
    from emrys.orchestration.run_coordinator import inspection

    if (
        receipt.get("status") != expected_status
        or receipt.get("snakemake_exit_code") != expected_exit_code
        or receipt.get("termination_signal") is not None
        or receipt.get("blockers")
    ):
        raise DriverError("assert-parity", "Terminal Attempt receipt differs")
    if attempt.get("operation") != operation:
        raise DriverError("assert-parity", "Attempt operation differs")
    scheduler_job_id = None if job is None else job.job_id
    placement = attempt.get("placement")
    expected_kind = "direct" if job is None else "slurm"
    if (
        not isinstance(placement, dict)
        or placement.get("kind") != expected_kind
        or placement.get("scheduler_job_id") != scheduler_job_id
        or not isinstance(placement.get("request"), dict)
        or placement["request"].get("kind") != expected_kind
    ):
        raise DriverError("assert-parity", "Attempt placement provenance differs")
    resources = _resource_snapshot(attempt)
    if resources["allocation"]["slurm_job_id"] != scheduler_job_id:
        raise DriverError(
            "assert-parity", "Resource allocation scheduler identity differs"
        )
    attempt_id = str(attempt["workflow_attempt_id"])
    return {
        "id": attempt_id,
        "common_fields": {name: attempt[name] for name in inspection.attempt_fields()},
        "placement": placement,
        "receipt": _artifact(
            run_root / "attempts" / attempt_id / "attempt-receipt.json"
        ),
        "task_roster": _task_roster(observed),
        "resources": resources,
        "application_log": _application_log_snapshot(
            run_root.parent.parent,
            run_id=observed.run_id,
            attempt_id=attempt_id,
            scheduler_job_id=scheduler_job_id,
            operation=operation,
            expected_status=expected_status,
        ),
    }


def _assert_scheduler_streams(workspace: Path, jobs: tuple[Job, ...]) -> None:
    observed = set(workspace.glob("logs/emrys-[0-9a-f]*-*"))
    expected = {path for job in jobs for path in (job.stdout, job.stderr)}
    if observed != expected:
        raise DriverError("assert-parity", "Scheduler stream ownership differs")


def _admitted_failure(run_root: Path, *, job: Job | None) -> dict[str, Any]:
    from emrys.orchestration.run_coordinator import inspection

    observed = inspection.inspect_run(run_root)
    if (
        observed.integrity,
        observed.attempt_outcome,
        observed.results_status,
        observed.reporting_status,
        observed.recovery_available,
    ) != ("valid", "failed", "incomplete", "incomplete", True) or observed.blockers:
        raise DriverError("assert-parity", "Controlled failure is not safely resumable")
    authority = observed.authority
    attempt = observed.latest_attempt
    receipt = observed.latest_receipt
    if authority is None or attempt is None or receipt is None:
        raise DriverError("assert-parity", "Failed Run lacks successor authority")
    attempts, receipts, blockers = inspection.inspect_attempt_chain(
        run_root, authority=authority
    )
    attempt_id = str(attempt["workflow_attempt_id"])
    if blockers or len(attempts) != 1 or set(receipts) != {attempt_id}:
        raise DriverError("assert-parity", "Failed Run Attempt chain differs")
    task_roster = _task_roster(observed)
    _assert_no_task_entry(task_roster, receipt)
    expected_reporting = {"run_summary", "html_report"}
    if set(observed.reporting_completion_records) != expected_reporting or any(
        records["start"] is not None or records["verified"] is not None
        for records in observed.reporting_completion_records.values()
    ):
        raise DriverError("assert-parity", "Reporting began before scientific success")
    snapshot = _attempt_snapshot(
        run_root,
        observed,
        attempt,
        receipt,
        job=job,
        expected_status="failed",
        expected_exit_code=1,
        operation="execute",
    )
    return {
        "authority": _authority_snapshot(authority),
        "attempt": snapshot,
        "predecessor_evidence": _predecessor_evidence(
            run_root,
            attempt_id,
            job,
            snapshot["application_log"]["path"],
        ),
    }


def _admitted_interruption(
    run_root: Path,
    *,
    job: Job,
    gate: NativeGate,
    failed_attempt_id: str,
) -> dict[str, Any]:
    from emrys.orchestration.run_coordinator import inspection

    observed = inspection.inspect_run(run_root)
    if (
        observed.integrity,
        observed.attempt_outcome,
        observed.results_status,
        observed.reporting_status,
        observed.recovery_available,
    ) != (
        "valid",
        "interrupted",
        "incomplete",
        "incomplete",
        True,
    ) or observed.blockers:
        raise DriverError("native-stop", "stopped Run has no admitted resume boundary")
    attempt, receipt, authority = (
        observed.latest_attempt,
        observed.latest_receipt,
        observed.authority,
    )
    if attempt is None or receipt is None or authority is None:
        raise DriverError("native-stop", "stopped Attempt lacks admitted authority")
    attempt_id = str(attempt["workflow_attempt_id"])
    if (
        attempt_id != gate.attempt_id
        or attempt.get("operation") != "resume"
        or attempt.get("supersedes_workflow_attempt_id") != failed_attempt_id
        or receipt.get("status") != "interrupted"
        or receipt.get("termination_signal") != signal.SIGTERM
        or not receipt.get("task_start_records")
    ):
        raise DriverError("native-stop", "stopped Attempt identity or receipt differs")
    attempts, receipts, blockers = inspection.inspect_attempt_chain(
        run_root, authority=authority
    )
    if (
        blockers
        or len(attempts) != 2
        or set(receipts) != {failed_attempt_id, attempt_id}
    ):
        raise DriverError("native-stop", "stopped Attempt chain differs")
    selected = [
        task
        for task in observed.tasks
        if f"{task.expected.machine_key}/{task.expected.scope_id}" == gate.task
    ]
    if len(selected) != 1 or not selected[0].terminal_attempts:
        raise DriverError("native-stop", "active native Task has no terminal record")
    terminal = selected[0].terminal_attempts[-1].record
    if (
        terminal is None
        or terminal.get("status") != "failed"
        or terminal.get("abort_closure") != "linux-task-prepublication.v1"
    ):
        raise DriverError("native-stop", "native Task did not close safely")
    application = _application_log_snapshot(
        run_root.parent.parent,
        run_id=observed.run_id,
        attempt_id=attempt_id,
        scheduler_job_id=job.job_id,
        operation="resume",
        expected_status="interrupted",
    )
    return {
        "attempt_id": attempt_id,
        "task": gate.task,
        "receipt": _artifact(
            run_root / "attempts" / attempt_id / "attempt-receipt.json"
        ),
        "terminal_task_status": terminal["status"],
        "predecessor_evidence": _predecessor_evidence(
            run_root, attempt_id, job, application["path"]
        ),
    }


def _admitted_completion(
    run_root: Path,
    fixture: dict[str, Any],
    *,
    jobs: tuple[Job, ...],
    failure: dict[str, Any] | None = None,
    interruption: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from emrys.orchestration.run_coordinator import inspection

    observed = inspection.inspect_run(run_root)
    completion = assert_completed_run(run_root, fixture, observed=observed)
    authority = observed.authority
    attempt = observed.latest_attempt
    receipt = observed.latest_receipt
    if authority is None or attempt is None or receipt is None:
        raise DriverError("assert-parity", "Completed Run lacks successor authority")
    attempts, receipts, blockers = inspection.inspect_attempt_chain(
        run_root, authority=authority
    )
    expected_count = 1 + int(failure is not None) + int(interruption is not None)
    if blockers or len(attempts) != expected_count or len(receipts) != expected_count:
        raise DriverError("assert-parity", "Completed Run Attempt chain differs")
    expected_reporting = {"run_summary", "html_report"}
    if set(observed.reporting_completion_records) != expected_reporting or any(
        records["start"] is None or records["verified"] is None
        for records in observed.reporting_completion_records.values()
    ):
        raise DriverError(
            "assert-parity", "Completed reporting transaction roster differs"
        )
    latest_job = jobs[-1] if jobs else None
    attempt_snapshot = _attempt_snapshot(
        run_root,
        observed,
        attempt,
        receipt,
        job=latest_job,
        expected_status="succeeded",
        expected_exit_code=0,
        operation="resume" if failure is not None else "execute",
    )
    if (
        len(
            tuple((run_root.parent.parent / "logs/application").glob("run-*/*/*.jsonl"))
        )
        != expected_count
    ):
        raise DriverError(
            "assert-parity", "Application-log count differs from operations"
        )
    _assert_scheduler_streams(run_root.parent.parent, jobs)
    authority_summary = _authority_snapshot(authority)
    if failure is not None:
        failed_id = str(failure["attempt"]["id"])
        _assert_predecessor_preserved(failure["predecessor_evidence"])
        if (
            authority_summary != failure["authority"]
            or str(attempts[0]["workflow_attempt_id"]) != failed_id
            or attempts[1]["operation"] != "resume"
            or attempts[1]["supersedes_workflow_attempt_id"] != failed_id
        ):
            raise DriverError(
                "assert-parity", "Resume changed predecessor evidence or Run authority"
            )
    if interruption is not None:
        interrupted_id = str(interruption["attempt_id"])
        _assert_predecessor_preserved(interruption["predecessor_evidence"])
        if (
            failure is None
            or len(attempts) != 3
            or str(attempts[1]["workflow_attempt_id"]) != interrupted_id
            or attempts[2]["operation"] != "resume"
            or attempts[2]["supersedes_workflow_attempt_id"] != interrupted_id
            or len({job.job_id for job in jobs}) != 3
        ):
            raise DriverError("assert-parity", "Stopped Run resume chain differs")
    return {
        **completion,
        "authority": authority_summary,
        "attempt": attempt_snapshot,
        "scientific_results": _scientific_result_hashes(run_root),
        "failure": failure,
        "interruption": interruption,
    }


def _assert_direct_slurm_parity(
    direct: dict[str, Any],
    scheduled: dict[str, Any],
) -> dict[str, Any]:
    if direct["authority"] != scheduled["authority"]:
        raise DriverError(
            "assert-parity", "Immutable Run authority differs by placement"
        )
    if direct["attempt"]["id"] == scheduled["attempt"]["id"]:
        raise DriverError(
            "assert-parity", "Direct and Slurm Attempts share an identity"
        )
    direct_failure = direct.get("failure")
    scheduled_failure = scheduled.get("failure")
    if (direct_failure is None) != (scheduled_failure is None):
        raise DriverError("assert-parity", "Recovery journeys differ by placement")
    if direct_failure is not None and scheduled_failure is not None:
        if direct_failure["attempt"]["id"] == scheduled_failure["attempt"]["id"]:
            raise DriverError("assert-parity", "Failed Attempts share an identity")
        if (
            direct_failure["attempt"]["common_fields"]
            != scheduled_failure["attempt"]["common_fields"]
        ):
            raise DriverError(
                "assert-parity", "Failed Attempt authority differs by placement"
            )
    for key in ("common_fields", "task_roster"):
        if direct["attempt"][key] != scheduled["attempt"][key]:
            raise DriverError("assert-parity", f"Attempt {key} differs by placement")
    if direct["scientific_results"] != scheduled["scientific_results"]:
        raise DriverError(
            "assert-parity", "Terminal scientific Results differ by placement"
        )
    direct_resources = direct["attempt"]["resources"]
    scheduled_resources = scheduled["attempt"]["resources"]
    if direct_resources["symbolic"] != scheduled_resources["symbolic"]:
        raise DriverError("assert-parity", "Run-bound resource declaration differs")
    if direct_resources["effective"] == scheduled_resources["effective"]:
        raise DriverError(
            "assert-parity",
            "Hosted proof did not exercise allocation-sensitive resource resolution",
        )
    return {
        "immutable_authority": direct["authority"],
        "attempt_ids_distinct": True,
        "failed_attempt_ids_distinct": direct_failure is not None,
        "attempt_common_fields": direct["attempt"]["common_fields"],
        "task_roster": direct["attempt"]["task_roster"],
        "scientific_results": direct["scientific_results"],
        "symbolic_resources": direct_resources["symbolic"],
        "direct_effective_resources": direct_resources["effective"],
        "slurm_effective_resources": scheduled_resources["effective"],
        "report_kinds": sorted(direct["reports"]),
        "single_application_log_per_operation": True,
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


def run_driver(
    arguments: argparse.Namespace,
    transcripts: Transcripts,
) -> dict[str, Any]:
    repo = _real(arguments.repo_root, "repository root", directory=True)
    paths = require_operator_root(arguments.operator_root, repo)
    transcripts.operator_root_admitted = True
    if os.environ.get("SLURM_JOB_ID", "").strip():
        raise DriverError("preflight", "driver must start outside Slurm")
    python = _workflow_python(repo)
    runtime = resolve_runtime(
        arguments.runtime_prefix, arguments.rscript, arguments.renv_library
    )
    scontrol = _command(arguments.scontrol, "scontrol")
    scancel = _command(arguments.scancel, "scancel")
    for directory in (paths.scratch, paths.adapters, paths.transcripts):
        directory.mkdir(mode=0o700)

    profile = str(arguments.profile)
    dataset = PROFILE_DATASETS[profile]
    parity_journey = profile == "130"
    recovery_journey = parity_journey
    workspaces = _selected_workspaces(paths, profile)
    failure_profile = paths.scratch / "controlled-missing-snakemake-profile"
    failure_module_init = paths.scratch / "controlled-failure-module-init.sh"
    slurm_failure_marker = paths.scratch / "slurm-fail-once"
    adapters = {
        "gatk": gatk_adapter_bytes(runtime.python, runtime.gatk, runtime.java),
        "infer_experiment.py": rseqc_adapter_bytes(runtime.python, runtime.rseqc),
        "gunzip": gunzip_adapter_bytes(runtime.gunzip),
    }
    for name, data in adapters.items():
        _write(paths.adapters / name, data, mode=0o700)
    if recovery_journey:
        _write(
            failure_module_init,
            controlled_failure_module_init_bytes(
                failure_profile,
                slurm_failure_marker,
            ),
        )
        _write(slurm_failure_marker, b"fail once\n")

    environment = runtime_environment(paths, runtime)
    projects: dict[str, Path] = {}
    for label, workspace in workspaces.items():
        init = _emrys(
            python,
            "init",
            "synthetic",
            "--output-dir",
            str(workspace),
            "--dataset-profile",
            dataset,
        )
        transcripts.run(f"{label}-init-plan", init, cwd=repo)
        transcripts.run(f"{label}-init", [*init, "--execute"], cwd=repo)
        # Pin the disposable fixture budget before Doctor or any Run exists.
        (workspace / "runtime/profiles/default.yaml").write_bytes(
            json.dumps(
                {
                    "schema_version": "emrys.execution-profile.v1",
                    "resources": symbolic_resource_document(),
                    "placement": {"kind": "direct"},
                }
            ).encode()
            + b"\n",
        )
        projects[label] = workspace / "project.yaml"

    slurm_settings = dict(
        account=arguments.slurm_account,
        partition=arguments.slurm_partition,
        qos=arguments.slurm_qos,
        cpus_per_task=arguments.slurm_cpus,
        memory_mb=arguments.slurm_memory,
        time_limit=arguments.slurm_time,
        nodelist=arguments.slurm_nodelist,
        scratch_parent=paths.scratch,
    )
    _write(
        paths.execution_profile,
        slurm_execution_profile_bytes(
            **slurm_settings,
            module_init=failure_module_init if recovery_journey else None,
        ),
    )
    # This disposable Project selects its site before any Run exists. Doctor's
    # qualification must not consume the separate deliberate engine failure.
    (paths.slurm_workspace / "runtime/profiles/default.yaml").write_bytes(
        slurm_execution_profile_bytes(**slurm_settings)
    )
    from emrys.evidence.storage_inventory import qualification

    qualifications: dict[str, Any] = {}
    for label, workspace in workspaces.items():
        project = projects[label]
        runtime_profile = workspace / "runtime/runtime.tsv"
        discover = _emrys(python, "runtime", "discover", "--project", str(project))
        transcripts.run(
            f"{label}-runtime-plan",
            discover,
            cwd=repo,
            environment=environment,
        )
        if runtime_profile.exists():
            raise DriverError(
                f"{label}-runtime-plan",
                "runtime dry-run published a profile",
            )
        transcripts.run(
            f"{label}-runtime-admit",
            [*discover, "--execute"],
            cwd=repo,
            environment=environment,
        )
        transcripts.run(
            f"{label}-validate",
            _emrys(python, "validate", "--project", str(project)),
            cwd=repo,
        )

        fasta = workspace / "inputs/reference/reference.fa"
        transcripts.run(
            f"{label}-doctor-repair",
            _emrys(
                python, "doctor", "--project", str(project), "--repair", "--execute"
            ),
            cwd=repo,
        )
        admit_storage = (
            qualification.admit_direct_qualification
            if label == "direct"
            else qualification.admit_final_qualification
        )
        qualifications[label] = admit_storage(workspace, fasta)
        transcripts.run(
            f"{label}-doctor",
            _emrys(python, "doctor", "--project", str(project)),
            cwd=repo,
        )
        before_inspect = _execution_state(workspace)
        empty = transcripts.run(
            f"{label}-inspect-before-run",
            _emrys(python, "inspect", "--project", str(project)),
            cwd=repo,
        )
        if (
            "Runs: none found at inspection time." not in empty.stdout
            or before_inspect != _execution_state(workspace)
        ):
            raise DriverError(
                f"{label}-inspect-before-run", "pre-Run inspection wrote or found a Run"
            )

    direct: list[str] | None = None
    direct_run_root: Path | None = None
    if parity_journey:
        direct = _emrys(
            python,
            "run",
            "--project",
            str(projects["direct"]),
            "--verbose",
        )
        before_plan = _execution_state(paths.direct_workspace)
        planned = transcripts.run("run-plan", direct, cwd=repo)
        direct_run_root = parse_run_plan(
            planned.stderr,
            paths.direct_workspace,
            no_write=True,
        )
        if planned.stdout or before_plan != _execution_state(paths.direct_workspace):
            raise DriverError("run-plan", "direct dry-run wrote state")
    scheduled = _emrys(
        python,
        "run",
        "--project",
        str(projects["slurm"]),
        "--profile",
        "ci",
        "--verbose",
    )
    before_plan = _execution_state(paths.slurm_workspace)
    scheduler_plan = transcripts.run("slurm-plan", scheduled, cwd=repo)
    if (
        scheduler_plan.stdout
        or "Dry-run complete; no scheduler or workspace state was written."
        not in scheduler_plan.stderr
        or before_plan != _execution_state(paths.slurm_workspace)
    ):
        raise DriverError("slurm-plan", "scheduler dry-run wrote or submitted")

    failure_environment = None
    if recovery_journey:
        failure_environment = {**os.environ, "SNAKEMAKE_PROFILE": str(failure_profile)}
    failure_signature = "but no profile.yaml (or config.yaml) found"
    if direct is not None and direct_run_root is not None:
        direct_execution = transcripts.run(
            "direct-execute",
            [*direct, "--execute"],
            cwd=repo,
            environment=failure_environment,
            expected_returncode=1 if recovery_journey else 0,
        )
        if (
            parse_run_plan(
                direct_execution.stderr,
                paths.direct_workspace,
                no_write=False,
            )
            != direct_run_root
        ):
            raise DriverError(
                "direct-execute", "Direct execution selected a different Run"
            )
        if recovery_journey and failure_signature not in direct_execution.stderr:
            raise DriverError(
                "direct-execute", "controlled engine failure was not observed"
            )

    submission = transcripts.run(
        "slurm-submit",
        [*scheduled, "--execute"],
        cwd=repo,
    )
    initial_job = wait_for_job(
        submission.stdout,
        log_dir=paths.slurm_workspace / "logs",
        scontrol=scontrol,
        scancel=scancel,
        cwd=repo,
        timeout_seconds=arguments.slurm_timeout_seconds,
        poll_seconds=arguments.poll_seconds,
        expected=("FAILED", "1:0") if recovery_journey else ("COMPLETED", "0:0"),
    )
    execution_stderr = _stream(initial_job.stderr)
    if recovery_journey and (
        slurm_failure_marker.exists() or failure_signature not in execution_stderr
    ):
        raise DriverError("slurm-submit", "controlled engine failure was not observed")
    slurm_run_root = parse_run_plan(
        execution_stderr,
        paths.slurm_workspace,
        no_write=False,
    )
    if direct_run_root is not None and direct_run_root.name != slurm_run_root.name:
        raise DriverError("plan-parity", "Direct and Slurm selected different Runs")

    failures: dict[str, dict[str, Any] | None] = {label: None for label in workspaces}
    slurm_jobs = (initial_job,)
    interruption: dict[str, Any] | None = None
    stop_evidence: dict[str, Any] | None = None
    if recovery_journey:
        if direct_run_root is None:
            raise DriverError("internal", "recovery parity lacks a direct Run")
        for label, run_root, job in (
            ("direct", direct_run_root, None),
            ("slurm", slurm_run_root, initial_job),
        ):
            failures[label] = _admitted_failure(run_root, job=job)

        transcripts.run(
            "direct-resume",
            _emrys(
                python,
                "resume",
                direct_run_root.name,
                "--project",
                str(projects["direct"]),
                "--verbose",
                "--execute",
            ),
            cwd=repo,
        )
        _write(paths.native_gate.with_suffix(".armed"), b"stop one native Task\n")
        resume_submission = transcripts.run(
            "slurm-resume-submit",
            _emrys(
                python,
                "resume",
                slurm_run_root.name,
                "--project",
                str(projects["slurm"]),
                "--profile",
                "ci",
                "--verbose",
                "--execute",
            ),
            cwd=repo,
            timeout_seconds=120,
        )
        from emrys.orchestration.run_coordinator import slurm_submission

        try:
            active_job = parse_submission(
                resume_submission.stdout, paths.slurm_workspace / "logs"
            )
        except DriverError as exc:
            job_id = _one(JOB_ID, resume_submission.stdout, "job ID", "submit-slurm")
            _emergency_cancel(
                job_id,
                scancel=scancel,
                scontrol=scontrol,
                cwd=repo,
                poll_seconds=arguments.poll_seconds,
                original=exc,
            )
            raise
        try:
            request_root = parse_submission_request(
                resume_submission, paths.slurm_workspace
            )
            request = slurm_submission.select_submission_request(
                projects["slurm"], request_root.name
            )
            if (
                request.request_root != request_root
                or request.recorded_job_id != active_job.job_id
                or request.context is None
                or request.context["project"] != str(projects["slurm"])
                or request.context["requested_run"] != slurm_run_root.name
            ):
                raise DriverError(
                    "native-stop", "retained request does not bind this Run/job"
                )
            gate = await_native_gate(
                paths.native_gate,
                slurm_run_root,
                active_job,
                samtools=runtime.samtools,
                scontrol=scontrol,
                cwd=repo,
                poll_seconds=arguments.poll_seconds,
            )
        except BaseException as exc:
            _emergency_cancel(
                active_job.job_id,
                scancel=scancel,
                scontrol=scontrol,
                cwd=repo,
                poll_seconds=arguments.poll_seconds,
                original=exc,
            )
            raise
        stop_started = False
        try:
            selected = ("--project", str(projects["slurm"]))
            submission_inspect = transcripts.run(
                "slurm-inspect-active-submission",
                _emrys(
                    python,
                    "inspect",
                    *selected,
                    "--submission",
                    request_root.name,
                ),
                cwd=repo,
                timeout_seconds=60,
            )
            if (
                request_root.name not in submission_inspect.stdout
                or active_job.job_id not in submission_inspect.stdout
            ):
                raise DriverError("native-stop", "active submission inspection differs")
            active_inspect = transcripts.run(
                "slurm-inspect-active-run",
                _emrys(python, "inspect", slurm_run_root.name, *selected),
                cwd=repo,
                timeout_seconds=60,
            )
            if "Attempt outcome: running" not in active_inspect.stdout:
                raise DriverError("native-stop", "active Run inspection differs")
            active_watch = transcripts.run(
                "slurm-watch-active-submission",
                _emrys(
                    python,
                    "watch",
                    *selected,
                    "--submission",
                    request_root.name,
                    "--snapshot",
                ),
                cwd=repo,
                timeout_seconds=60,
            )
            if not all(
                value in active_watch.stdout
                for value in (
                    f"Request: {request_root.name}",
                    f"Recorded job: {active_job.job_id}",
                    "Scheduler: RUNNING",
                )
            ):
                raise DriverError("native-stop", "active watch snapshot differs")
            stop = _emrys(
                python,
                "stop",
                *selected,
                "--submission",
                request_root.name,
            )
            preview = transcripts.run(
                "slurm-stop-preview", stop, cwd=repo, timeout_seconds=60
            )
            if not all(
                value in preview.stdout
                for value in (
                    "Preview only",
                    "--ctld",
                    "--clusters=",
                    "--name=",
                    "--me",
                )
            ):
                raise DriverError(
                    "native-stop", "controller-filtered stop preview differs"
                )
            stop_started = True
            stopped = transcripts.run(
                "slurm-stop-execute",
                [*stop, "--execute"],
                cwd=repo,
                expected_returncode=None,
                timeout_seconds=60,
            )
            if (
                "scancel exit status: 0" not in stopped.stdout
                or f"Stop request: {request_root}" not in stopped.stdout
            ):
                raise DriverError(
                    "native-stop", "public stop did not confirm one request"
                )
            await_native_exit(gate)
        except BaseException as exc:
            if not stop_started:
                _emergency_cancel(
                    active_job.job_id,
                    scancel=scancel,
                    scontrol=scontrol,
                    cwd=repo,
                    poll_seconds=arguments.poll_seconds,
                    original=exc,
                )
            raise
        finally:
            os.close(gate.descriptor)
        stopped_job = wait_for_job(
            resume_submission.stdout,
            log_dir=paths.slurm_workspace / "logs",
            scontrol=scontrol,
            scancel=scancel,
            cwd=repo,
            timeout_seconds=arguments.slurm_timeout_seconds,
            poll_seconds=arguments.poll_seconds,
            expected=None,
            cleanup_on_failure=False,
        )
        if stopped_job.state != "CANCELLED" or stopped_job.job_id == initial_job.job_id:
            raise DriverError("native-stop", "controller stop did not cancel a new job")
        deadline = time.monotonic() + 30.0
        while True:
            try:
                interruption = _admitted_interruption(
                    slurm_run_root,
                    job=stopped_job,
                    gate=gate,
                    failed_attempt_id=str(failures["slurm"]["attempt"]["id"]),
                )
                break
            except DriverError as exc:
                if time.monotonic() >= deadline:
                    raise DriverError("native-stop", str(exc)) from exc
                time.sleep(min(arguments.poll_seconds, 1.0))
        resume = _emrys(
            python,
            "resume",
            slurm_run_root.name,
            "--project",
            str(projects["slurm"]),
            "--profile",
            "ci",
            "--verbose",
        )
        before_preview = _execution_state(paths.slurm_workspace)
        transcripts.run(
            "slurm-stopped-resume-preview", resume, cwd=repo, timeout_seconds=60
        )
        if before_preview != _execution_state(paths.slurm_workspace):
            raise DriverError("native-stop", "resume preview changed stopped Run")
        final_submission = transcripts.run(
            "slurm-stopped-resume-submit",
            [*resume, "--execute"],
            cwd=repo,
            timeout_seconds=120,
        )
        final_job = wait_for_job(
            final_submission.stdout,
            log_dir=paths.slurm_workspace / "logs",
            scontrol=scontrol,
            scancel=scancel,
            cwd=repo,
            timeout_seconds=arguments.slurm_timeout_seconds,
            poll_seconds=arguments.poll_seconds,
        )
        if final_job.job_id in {initial_job.job_id, stopped_job.job_id}:
            raise DriverError("native-stop", "final resume reused an earlier job")
        slurm_jobs = (initial_job, stopped_job, final_job)
        stop_evidence = {
            "request": str(request_root),
            "native_pid": gate.pid,
            "native_tool": str(runtime.samtools),
            "native_task": gate.task,
            "stopped_job": stopped_job.job_id,
            "stop_command_returncode": stopped.returncode,
            "interrupted_attempt": interruption["attempt_id"],
            "completed_job": final_job.job_id,
        }

    run_roots = {"slurm": slurm_run_root}
    if direct_run_root is not None:
        run_roots = {"direct": direct_run_root, **run_roots}
    for label, run_root in run_roots.items():
        inspected = transcripts.run(
            f"{label}-inspect",
            _emrys(
                python,
                "inspect",
                run_root.name,
                "--project",
                str(projects[label]),
            ),
            cwd=repo,
        )
        if any(
            value not in inspected.stdout
            for value in (
                "Attempt outcome: succeeded",
                "Scientific Results: complete",
                "Reporting admission: complete",
            )
        ):
            raise DriverError(
                f"{label}-inspect",
                "public Run inspection is incomplete",
            )

    fixtures = {
        label: json.loads((workspace / "fixture.json").read_text())
        for label, workspace in workspaces.items()
    }
    fixture_values = tuple(fixtures.values())
    if any(fixture != fixture_values[0] for fixture in fixture_values[1:]) or any(
        fixture.get("dataset_profile") != dataset
        or fixture.get("read_pairs_per_library") != int(profile)
        for fixture in fixture_values
    ):
        raise DriverError(
            "assert-results", "synthetic fixture identity or scale differs"
        )
    direct_completion = (
        _admitted_completion(
            direct_run_root,
            fixtures["direct"],
            jobs=(),
            failure=failures["direct"],
        )
        if direct_run_root is not None
        else None
    )
    slurm_completion = _admitted_completion(
        slurm_run_root,
        fixtures["slurm"],
        jobs=slurm_jobs,
        failure=failures["slurm"],
        interruption=interruption,
    )
    parity = (
        _assert_direct_slurm_parity(direct_completion, slurm_completion)
        if direct_completion is not None
        else None
    )
    return {
        "schema_version": SUMMARY_SCHEMA,
        "status": "passed",
        "profile": profile,
        "dataset_profile": dataset,
        "fixture_id": fixtures["slurm"].get("fixture_id"),
        "operator_root": str(paths.root),
        "runtime_profiles": {
            label: _artifact(workspace / "runtime/runtime.tsv")
            for label, workspace in workspaces.items()
        },
        "execution_profile": _artifact(paths.execution_profile),
        "runtime_adapters": {
            name: _artifact(paths.adapters / name) for name in (*adapters, "samtools")
        },
        "controlled_failure": (
            {
                "boundary": "snakemake profile admission before task entry",
                "missing_profile": str(failure_profile),
                "slurm_module_init": _artifact(failure_module_init),
            }
            if recovery_journey
            else None
        ),
        "controller_stop_resume": stop_evidence,
        "storage_qualifications": {
            label: {
                "qualification_id": qualified.qualification_id,
                "final_receipt": _artifact(qualified.receipt_path),
            }
            for label, qualified in qualifications.items()
        },
        "direct": (
            {
                "dry_run": {"submitted": False, "wrote_state": False},
                "completion": direct_completion,
            }
            if direct_completion is not None
            else {"selected": False}
        ),
        "slurm": {
            "partition": arguments.slurm_partition,
            "dry_run": {"submitted": False},
            "jobs": [
                {
                    "job_id": job.job_id,
                    "state": job.state,
                    "exit_code": job.exit_code,
                    "stdout": _artifact(job.stdout),
                    "stderr": _artifact(job.stderr),
                }
                for job in slurm_jobs
            ],
            "completion": slurm_completion,
        },
        "parity": parity,
        "commands": transcripts.records,
        "retention": "complete operator root retained; no post-run cleanup or repair",
        "evidence_boundary": (
            "real-tool hosted direct and disposable single-node Slurm parity "
            if parity_journey
            else "real-tool disposable single-node Slurm production-like exercise "
        )
        + ("only; no production, scientific-review, or biological claim"),
        "biological_interpretation_claimed": False,
    }


def _summary(
    arguments: argparse.Namespace,
    transcripts: Transcripts,
    error: BaseException,
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
        "retention": (
            "all partials, logs, streams, and receipts retained; "
            "no post-failure cleanup or repair performed"
        ),
        "evidence_boundary": (
            "failed synthetic E2E attempt; no completion or biological claim"
        ),
        "biological_interpretation_claimed": False,
    }


def _publish(path: Path, value: dict[str, Any]) -> None:
    _write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())
    print(f"Machine-readable E2E summary: {path}", flush=True)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
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
                    "evidence_boundary": (
                        "planned execution only; no runtime, workflow, "
                        "scientific, or biological evidence"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        print("Dry-run complete; no directories or files were created.")
        return 0
    root = Path(arguments.operator_root).absolute()
    transcripts = Transcripts(root / "driver-transcripts")
    try:
        result = run_driver(arguments, transcripts)
    except (Exception, KeyboardInterrupt) as exc:
        summary = root / "e2e-summary.json"
        if transcripts.operator_root_admitted and not summary.exists():
            try:
                _publish(summary, _summary(arguments, transcripts, exc))
            except OSError as summary_error:
                print(
                    f"ERROR: could not publish failure summary: {summary_error}",
                    file=sys.stderr,
                )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    _publish(root / "e2e-summary.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
