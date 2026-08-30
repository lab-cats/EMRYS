#!/usr/bin/env python3
"""Run one retained real-tool synthetic EMRYS E2E through single-node Slurm."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUMMARY_SCHEMA = "emrys.ci-real-synthetic-e2e-summary.v2"
PROFILE_DATASETS = {"130": "smoke-v1", "100000": "production-like-v1"}
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
RUN_ROOT = re.compile(r"^Run root: (/.+/runs/run-[a-f0-9]{64})$", re.MULTILINE)
JOB_ID = re.compile(r"^JOB_ID=([0-9]+)$", re.MULTILINE)
OUT = re.compile(r"^OUT=(/.+)$", re.MULTILINE)
ERR = re.compile(r"^ERR=(/.+)$", re.MULTILINE)
STATE = re.compile(r"(?:^| )JobState=([A-Z_]+)")
EXIT = re.compile(r"(?:^| )ExitCode=([0-9]+:[0-9]+)")


class DriverError(RuntimeError):
    """One E2E stage failed; retained state remains untouched."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


@dataclass(frozen=True, slots=True)
class Paths:
    root: Path
    workspace: Path
    scratch: Path
    execution_profile: Path
    runtime_profile: Path
    adapters: Path
    transcripts: Path


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


@dataclass(frozen=True, slots=True)
class Job:
    job_id: str
    stdout: Path
    stderr: Path
    state: str = ""
    exit_code: str = ""


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
        raise DriverError("preflight", f"{label} is unavailable: {path}: {exc}") from exc
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
    if not selected.exists() or not selected.is_file() or not os.access(selected, os.X_OK):
        raise DriverError("preflight", f"workflow Python is unavailable: {selected}")
    return selected


def require_operator_root(operator_root: Path, repo_root: Path) -> Paths:
    root = _real(operator_root, "operator root", directory=True)
    repo = _real(repo_root, "repository root", directory=True)
    if root == repo or root.is_relative_to(repo):
        raise DriverError("preflight", "operator root must be outside the source checkout")
    if any(root.iterdir()):
        raise DriverError(
            "preflight",
            "operator root must be empty; existing contents were preserved",
        )
    if not os.access(root, os.R_OK | os.W_OK | os.X_OK):
        raise DriverError("preflight", "operator root is not usable")
    workspace = root / "synthetic-inputs"
    return Paths(
        root,
        workspace,
        root / "scratch",
        root / "emrys.execution.slurm.json",
        workspace / "runtime/runtime.tsv",
        root / "runtime-adapters",
        root / "driver-transcripts",
    )


def resolve_runtime(prefix: Path, rscript: Path, renv: Path) -> Runtime:
    root = _real(prefix, "runtime prefix", directory=True)
    jars = tuple(root.glob("share/picard-slim-3.1.1-*/picard.jar"))
    if len(jars) != 1:
        raise DriverError("preflight", "runtime prefix must contain one Picard 3.1.1 jar")

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
        f"{shlex.quote(py)} -I -B -c \"from importlib.metadata import version; "
        "print('infer_experiment.py ' + version('RSeQC'))\"; fi\n"
        f"exec {shlex.quote(py)} -I -B {shlex.quote(target)} \"$@\"\n"
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
        f"exec {shlex.quote(py)} -I -B {shlex.quote(target)} \"$@\"\n"
    ).encode()


def gunzip_adapter_bytes(delegate: Path) -> bytes:
    (target,) = _safe_adapter(delegate)
    quoted = shlex.quote(target)
    return (
        "#!/bin/sh\nset -eu\n"
        'if [ "$#" -eq 1 ] && [ "$1" = "--version" ]; then exec '
        f'{quoted} --version; fi\nexec {quoted} -d "$@"\n'
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
        raise DriverError("assert-results", f"required result is not a real file: {path}")
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
        ("samtools", runtime.samtools),
        ("bcftools", runtime.bcftools),
        ("java", runtime.java),
    ):
        (paths.adapters / name).symlink_to(target)
    return {
        **os.environ,
        "PATH": str(paths.adapters),
        "JAVA_HOME": str(runtime.java.parent.parent),
        "EMRYS_PICARD_JAR": str(runtime.picard),
        "EMRYS_RSCRIPT": str(runtime.rscript),
        "EMRYS_RENV_LIBRARY": str(runtime.renv),
    }


def parse_launcher(value: str) -> tuple[str, ...]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise DriverError("preflight", f"invalid storage launcher JSON: {exc}") from exc
    if (
        not isinstance(parsed, list)
        or not parsed
        or any(not isinstance(item, str) or not item for item in parsed)
    ):
        raise DriverError("preflight", "storage launcher must be a nonempty string array")
    return (
        str(_real(Path(parsed[0]), "storage launcher", executable=True)),
        *parsed[1:],
    )


def slurm_execution_profile_bytes(
    request: Path,
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
    from emrys.contracts.orchestration import api as contracts
    from emrys.orchestration.local_pilot.execution_profile import (
        SCHEMA_VERSION,
        load_execution_profile,
    )

    try:
        source = load_execution_profile(request)
        document = {
            "schema_version": SCHEMA_VERSION,
            "resources": source.resource_policy.document(),
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
    ) -> subprocess.CompletedProcess[str]:
        selected = tuple(map(str, argv))
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
        label = re.sub(r"[^a-z0-9-]+", "-", stage.lower())
        stem = f"{len(self.records) + 1:02d}-{label}"
        stdout = self.root / f"{stem}.stdout.log"
        stderr = self.root / f"{stem}.stderr.log"
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
        if result.returncode:
            raise DriverError(
                stage,
                f"command exited {result.returncode}; retained streams: {stdout}, {stderr}",
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
        job.stdout != log_dir / f"emrys-local-pilot-{job_id}.out"
        or job.stderr != log_dir / f"emrys-local-pilot-{job_id}.err"
    ):
        raise DriverError("submit-slurm", "submission stream paths differ")
    return job


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
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, check=False
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
        observed = _scheduler(
            (str(scontrol), "show", "job", "-o", job_id), cwd
        )
        if observed.returncode:
            return "NO_LONGER_OBSERVABLE"
        state, _ = parse_scontrol(observed.stdout)
        if state in TERMINAL_STATES:
            return state
        time.sleep(min(poll_seconds, 1.0))
    raise DriverError("cancel-slurm", f"job {job_id} did not become terminal after TERM")


def wait_for_job(
    job: Job,
    *,
    scontrol: Path,
    scancel: Path,
    cwd: Path,
    timeout_seconds: int,
    poll_seconds: float,
) -> Job:
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            if time.monotonic() >= deadline:
                raise DriverError("wait-slurm", "job timed out")
            result = _scheduler(
                (str(scontrol), "show", "job", "-o", job.job_id), cwd
            )
            if result.returncode:
                raise DriverError("wait-slurm", f"scontrol failed: {result.stderr.strip()}")
            state, exit_code = parse_scontrol(result.stdout)
            if state in TERMINAL_STATES:
                break
            time.sleep(poll_seconds)
    except (DriverError, KeyboardInterrupt) as exc:
        disposition = cancel_job(
            job.job_id,
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
    if (state, exit_code) != ("COMPLETED", "0:0"):
        raise DriverError(
            "wait-slurm",
            f"job ended {state} with {exit_code}; streams retained",
        )
    return completed


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
    candidate = expected.get("significant_candidate_id") if isinstance(expected, dict) else None
    all_ids = [row["candidate_id"] for row in all_rows]
    if (
        expected.get("all_sites_rows") != 3
        or expected.get("significant_sites_rows") != 1
        or len(all_rows) != 3
        or len(significant) != 1
        or len(set(all_ids)) != 3
        or significant[0]["candidate_id"] != candidate
        or candidate not in all_ids
        or not significant[0]["call_status"].startswith("significant_")
    ):
        raise DriverError("assert-results", "independent Step09 3/1 oracle differs")
    return {
        "all_sites_rows": 3,
        "significant_sites_rows": 1,
        "significant_candidate_id": candidate,
        "all_sites": _artifact(all_sites),
        "significant_sites": _artifact(significant_sites),
    }


def assert_completed_run(run_root: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    from emrys.orchestration.local_pilot import inspection

    observed = inspection.inspect_run(run_root)
    if (
        (
            observed.integrity,
            observed.attempt_outcome,
            observed.results_status,
            observed.reporting_status,
        )
        != ("valid", "succeeded", "complete", "complete")
        or observed.blockers
    ):
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
    runtime = resolve_runtime(arguments.runtime_prefix, arguments.rscript, arguments.renv_library)
    launcher = parse_launcher(arguments.storage_compute_launcher_json)
    scontrol = _command(arguments.scontrol, "scontrol")
    scancel = _command(arguments.scancel, "scancel")
    for directory in (paths.scratch, paths.adapters, paths.transcripts):
        directory.mkdir(mode=0o700)

    adapters = {
        "gatk": gatk_adapter_bytes(runtime.python, runtime.gatk, runtime.java),
        "infer_experiment.py": rseqc_adapter_bytes(runtime.python, runtime.rseqc),
        "gunzip": gunzip_adapter_bytes(runtime.gunzip),
    }
    for name, data in adapters.items():
        _write(paths.adapters / name, data, mode=0o700)

    profile = str(arguments.profile)
    dataset = PROFILE_DATASETS[profile]
    init = _emrys(python, "init", "synthetic", "--output-dir", str(paths.workspace), "--dataset-profile", dataset)
    transcripts.run("init-plan", init, cwd=repo)
    transcripts.run("init", [*init, "--execute"], cwd=repo)
    project = paths.workspace / "project.yaml"
    _write(
        paths.execution_profile,
        slurm_execution_profile_bytes(
            project,
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
    discover = _emrys(python, "runtime", "discover", "--project", str(project))
    environment = runtime_environment(paths, runtime)
    transcripts.run("runtime-plan", discover, cwd=repo, environment=environment)
    if paths.runtime_profile.exists():
        raise DriverError("runtime-plan", "runtime dry-run published a profile")
    transcripts.run(
        "runtime-admit",
        [*discover, "--execute"],
        cwd=repo,
        environment=environment,
    )
    transcripts.run(
        "validate",
        _emrys(python, "validate", "project", "--project", str(project)),
        cwd=repo,
    )

    fasta = paths.workspace / "inputs/reference/reference.fa"
    storage = _emrys(python, "inspect", "storage-qualification", "--workspace", str(paths.workspace), "--reference-fasta", str(fasta))
    for phase in ("compute", "finalize"):
        command = [*storage, "--phase", phase]
        transcripts.run(f"storage-{phase}-plan", command, cwd=repo)
        prefix = launcher if phase == "compute" else ()
        transcripts.run(f"storage-{phase}", [*prefix, *command, "--execute"], cwd=repo)
    from emrys.evidence.storage_inventory import qualification

    qualified = qualification.admit_final_qualification(paths.workspace, fasta)
    transcripts.run("doctor", _emrys(python, "doctor", "--project", str(project)), cwd=repo)

    direct = _emrys(python, "run", "--project", str(project), "--log-level", "verbose")
    planned = transcripts.run("run-plan", direct, cwd=repo)
    run_root = parse_run_plan(planned.stderr, paths.workspace, no_write=True)
    if planned.stdout or any(any((paths.workspace / name).iterdir()) for name in ("runs", "logs")):
        raise DriverError("run-plan", "direct dry-run wrote state")
    scheduled = _emrys(python, "run", "--project", str(project), "--execution-profile", str(paths.execution_profile), "--log-level", "verbose")
    scheduler_plan = transcripts.run("slurm-plan", scheduled, cwd=repo)
    if (
        scheduler_plan.stdout
        or "Dry-run complete; no scheduler or workspace state was written."
        not in scheduler_plan.stderr
        or any(any((paths.workspace / name).iterdir()) for name in ("runs", "logs"))
    ):
        raise DriverError("slurm-plan", "scheduler dry-run wrote or submitted")
    submission = transcripts.run(
        "slurm-submit",
        [*scheduled, "--execute"],
        cwd=repo,
    )
    job = wait_for_job(
        parse_submission(submission.stdout, paths.workspace / "logs"),
        scontrol=scontrol,
        scancel=scancel,
        cwd=repo,
        timeout_seconds=arguments.slurm_timeout_seconds,
        poll_seconds=arguments.poll_seconds,
    )
    execution_stderr = _stream(job.stderr)
    if parse_run_plan(execution_stderr, paths.workspace, no_write=False) != run_root:
        raise DriverError("slurm-execute", "compute selected a different Run")

    inspected = transcripts.run("inspect", _emrys(python, "inspect", "run", "--run-root", str(run_root)), cwd=repo)
    if any(
        value not in inspected.stdout
        for value in (
            "Attempt outcome: succeeded",
            "Scientific Results: complete",
            "Reporting: complete",
        )
    ):
        raise DriverError("inspect", "public Run inspection is incomplete")
    fixture = json.loads((paths.workspace / "fixture.json").read_text())
    if (
        fixture.get("dataset_profile") != dataset
        or fixture.get("read_pairs_per_library") != int(profile)
    ):
        raise DriverError("assert-results", "fixture scale differs")
    completion = assert_completed_run(run_root, fixture)
    return {
        "schema_version": SUMMARY_SCHEMA,
        "status": "passed",
        "profile": profile,
        "dataset_profile": dataset,
        "fixture_id": fixture.get("fixture_id"),
        "operator_root": str(paths.root),
        "runtime_profile": _artifact(paths.runtime_profile),
        "execution_profile": _artifact(paths.execution_profile),
        "runtime_adapters": {
            name: _artifact(paths.adapters / name) for name in adapters
        },
        "storage_compute_launcher": list(launcher),
        "storage_qualification": {
            "qualification_id": qualified.qualification_id,
            "final_receipt": _artifact(qualified.receipt_path),
        },
        "slurm": {
            "partition": arguments.slurm_partition,
            "dry_run": {"submitted": False},
            "job": {
                "job_id": job.job_id,
                "state": job.state,
                "exit_code": job.exit_code,
                "stdout": _artifact(job.stdout),
                "stderr": _artifact(job.stderr),
            },
        },
        "completion": completion,
        "commands": transcripts.records,
        "retention": "complete operator root retained; no cleanup or repair performed",
        "evidence_boundary": (
            "real-tool single-node Slurm synthetic evidence only; no production, "
            "scientific-review, or biological claim"
        ),
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
            "no cleanup or repair performed"
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
