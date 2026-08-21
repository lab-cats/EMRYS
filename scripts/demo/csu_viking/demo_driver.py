#!/usr/bin/env python3
"""Opt-in, presentation-only façade for the CSU Viking live demo."""

from __future__ import annotations

import csv
import hashlib
import io
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
from typing import NoReturn, Sequence


PASS_INIT_DRY = "DEMO_INIT_DRY_RUN=PASS"
PASS_INIT = "DEMO_INIT=PASS"
PASS_STORAGE_DRY = "DEMO_STORAGE_QUALIFICATION_DRY_RUN=PASS"
PASS_STORAGE = "DEMO_STORAGE_QUALIFICATION=PASS"
PASS_WORKFLOW_DRY = "DEMO_WORKFLOW_DRY_RUN=PASS"
PASS_SUBMISSION = "DEMO_WORKFLOW_SUBMISSION=PASS"

JOB_RE = re.compile(r"^[1-9][0-9]*$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SOURCE_OWNER_JOBS = 73
SOURCE_REPORTING_KINDS = frozenset(
    {"artifact_index", "run_summary", "html_report"}
)
INDEX_MEMBERS = (
    "Genome",
    "SA",
    "SAindex",
    "chrLength.txt",
    "chrName.txt",
    "chrNameLength.txt",
    "chrStart.txt",
    "exonGeTrInfo.tab",
    "exonInfo.tab",
    "geneInfo.tab",
    "genomeParameters.txt",
    "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab",
    "sjdbList.out.tab",
    "transcriptInfo.tab",
)
TERMINAL_STATES = {
    "BOOT_FAIL",
    "CANCELLED",
    "COMPLETED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "REVOKED",
    "TIMEOUT",
}


class DemoError(RuntimeError):
    """One demo-only orchestration boundary was not satisfied."""


def fail(message: str) -> NoReturn:
    raise DemoError(message)


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "")
    if not value or "\x00" in value or "\n" in value or "\r" in value:
        fail(f"source activate.sh first; {name} is unavailable")
    return value


def _absolute(raw: str, label: str) -> Path:
    path = Path(raw)
    if not path.is_absolute() or path == Path("/"):
        fail(f"{label} must be an absolute non-root path: {path}")
    return Path(os.path.abspath(path))


def _canonical_file(path: Path, label: str, *, executable: bool = False) -> Path:
    try:
        state = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISREG(state.st_mode)
        or resolved != path
        or (executable and not os.access(path, os.X_OK))
    ):
        fail(f"{label} must be a canonical real file: {path}")
    return path


def _selected_executable(path: Path, label: str) -> Path:
    """Admit one stable executable path, including a normal venv symlink."""

    try:
        parent_state = path.parent.lstat()
        parent_resolved = path.parent.resolve(strict=True)
        before = path.lstat()
        link_before = os.readlink(path) if stat.S_ISLNK(before.st_mode) else ""
        target = path.resolve(strict=True)
        target_before = target.stat(follow_symlinks=False)
        after = path.lstat()
        link_after = os.readlink(path) if stat.S_ISLNK(after.st_mode) else ""
        confirmed_target = path.resolve(strict=True)
        target_after = confirmed_target.stat(follow_symlinks=False)
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    if (
        stat.S_ISLNK(parent_state.st_mode)
        or not stat.S_ISDIR(parent_state.st_mode)
        or parent_resolved != path.parent
        or (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns)
        or link_before != link_after
        or confirmed_target != target
        or (target_before.st_dev, target_before.st_ino, target_before.st_mode)
        != (target_after.st_dev, target_after.st_ino, target_after.st_mode)
        or not stat.S_ISREG(target_after.st_mode)
        or not os.access(path, os.X_OK)
    ):
        fail(f"{label} executable identity is invalid or changed: {path}")
    return path


def _canonical_directory(path: Path, label: str) -> Path:
    try:
        state = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != path
    ):
        fail(f"{label} must be a canonical real directory: {path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class Config:
    repo: Path
    python: Path
    session: str
    seed_input: Path
    source_run: Path
    source_index: Path
    real_star: Path
    input_dir: Path
    workspace_parent: Path
    workspace: Path
    log_dir: Path
    state_file: Path
    job_env_file: Path
    account: str
    partition: str
    qos: str
    nodelist: str
    qualification_partition: str
    scratch_parent: Path

    @property
    def source_fasta(self) -> Path:
        return self.seed_input / "inputs/reference/genome.fa"

    @property
    def source_gtf(self) -> Path:
        return self.seed_input / "inputs/reference/annotation.gtf"

    @property
    def runtime_profile(self) -> Path:
        return self.input_dir / "runtime.selected.tsv"

    @property
    def wrapper(self) -> Path:
        return self.input_dir / "run-in-slurm.sh"


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def _validate_config(config: Config) -> Config:
    if not SAFE_ID_RE.fullmatch(config.session):
        fail("demo session contains unsafe characters")
    for value, label in (
        (config.account, "Slurm account"),
        (config.partition, "Slurm partition"),
        (config.qos, "Slurm QoS"),
        (config.nodelist, "Slurm node"),
        (config.qualification_partition, "qualification partition"),
    ):
        if not SAFE_ID_RE.fullmatch(value):
            fail(f"{label} contains unsafe characters")
    if config.workspace != config.workspace_parent / "workspace":
        fail("demo workspace must be the exact workspace-parent child")
    if config.python != config.repo / ".venv/bin/python":
        fail("demo Python must be this checkout's exact .venv launcher")
    if config.scratch_parent != Path("/tmp"):
        fail("the CSU demo scratch parent must be /tmp")

    mutable = (config.input_dir, config.workspace_parent, config.log_dir)
    for index, first in enumerate(mutable):
        for second in mutable[index + 1 :]:
            if _paths_overlap(first, second):
                fail("demo input, workspace-parent, and log roots must be disjoint")
    protected = (
        config.repo,
        config.seed_input,
        config.source_run,
        config.source_index,
    )
    home = _canonical_directory(Path.home(), "operator home")
    for destination in mutable:
        if any(_paths_overlap(destination, source) for source in protected):
            fail(f"mutable demo root overlaps retained/source state: {destination}")
        if destination.parent != home:
            fail(f"mutable demo root must be a direct operator-home child: {destination}")

    expected_state = config.log_dir / ".demo-state.json"
    expected_job_env = config.log_dir / ".demo-job.env"
    if config.state_file != expected_state or config.job_env_file != expected_job_env:
        fail("demo state paths must use the exact private log-directory names")
    return config


def load_config() -> Config:
    script_repo = Path(__file__).resolve().parents[3]
    repo = _absolute(_required_environment("NORAD_DEMO_REPO_ROOT"), "repo root")
    if repo != script_repo:
        fail("activation repository differs from the selected demo driver")
    config = Config(
        repo=_canonical_directory(repo, "repo root"),
        python=_selected_executable(
            _absolute(_required_environment("NORAD_DEMO_PYTHON"), "demo Python"),
            "demo Python",
        ),
        session=_required_environment("NORAD_DEMO_SESSION"),
        seed_input=_absolute(
            _required_environment("NORAD_DEMO_SEED_INPUT"), "seed input"
        ),
        source_run=_absolute(
            _required_environment("NORAD_DEMO_SOURCE_RUN"), "source run"
        ),
        source_index=_absolute(
            _required_environment("NORAD_DEMO_SOURCE_INDEX"), "source index"
        ),
        real_star=_absolute(
            _required_environment("NORAD_DEMO_REAL_STAR"), "real STAR"
        ),
        input_dir=_absolute(
            _required_environment("NORAD_DEMO_INPUT_DIR"), "demo input"
        ),
        workspace_parent=_absolute(
            _required_environment("NORAD_DEMO_WORKSPACE_PARENT"),
            "workspace parent",
        ),
        workspace=_absolute(
            _required_environment("NORAD_DEMO_WORKSPACE"), "workspace"
        ),
        log_dir=_absolute(
            _required_environment("NORAD_DEMO_LOG_DIR"), "log directory"
        ),
        state_file=_absolute(
            _required_environment("NORAD_DEMO_STATE_FILE"), "state file"
        ),
        job_env_file=_absolute(
            _required_environment("NORAD_DEMO_JOB_ENV_FILE"), "job environment file"
        ),
        account=_required_environment("NORAD_SLURM_ACCOUNT"),
        partition=_required_environment("NORAD_SLURM_PARTITION"),
        qos=_required_environment("NORAD_SLURM_QOS"),
        nodelist=_required_environment("NORAD_SLURM_NODELIST"),
        qualification_partition=_required_environment(
            "NORAD_DEMO_QUALIFICATION_PARTITION"
        ),
        scratch_parent=_absolute(
            _required_environment("NORAD_SCRATCH_PARENT"), "scratch parent"
        ),
    )
    return _validate_config(config)


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    try:
        live_user = subprocess.check_output(
            ("/usr/bin/id", "-un"), text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"could not resolve the live submitter: {exc}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", live_user):
        fail("live submitter name is unsafe")
    environment["USER"] = live_user
    environment["LOGNAME"] = live_user
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(
    command: Sequence[str],
    *,
    environment: dict[str, str] | None = None,
    print_output: bool = True,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            tuple(command),
            cwd=cwd,
            env=_child_environment() if environment is None else environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        fail(f"timed out executing {command[0]}")
    except OSError as exc:
        fail(f"could not execute {command[0]}: {exc}")
    if print_output:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
    return completed


def _real_cli(config: Config, *arguments: str) -> subprocess.CompletedProcess[str]:
    return _run(
        (
            str(config.python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "norad",
            *arguments,
        ),
        cwd=config.repo,
    )


def _require_success(
    completed: subprocess.CompletedProcess[str], marker: str, label: str
) -> None:
    if completed.returncode != 0 or marker not in completed.stdout:
        fail(f"{label} did not complete with its exact success marker")


def _atomic_write(path: Path, data: bytes, mode: int) -> None:
    temporary = path.with_name(f".{path.name}.demo-{os.getpid()}.tmp")
    if os.path.lexists(temporary):
        fail(f"retained demo staging file blocks publication: {temporary}")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fchmod(handle.fileno(), mode)
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def _state(config: Config) -> dict[str, object]:
    if not os.path.lexists(config.state_file):
        return {}
    try:
        state = config.state_file.lstat()
        if (
            stat.S_ISLNK(state.st_mode)
            or not stat.S_ISREG(state.st_mode)
            or state.st_uid != os.getuid()
            or stat.S_IMODE(state.st_mode) & 0o077
        ):
            fail("demo state must be a private real file owned by the current UID")
        value = json.loads(config.state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"demo state is unreadable: {config.state_file}: {exc}")
    if (
        not isinstance(value, dict)
        or value.get("session") != config.session
        or value.get("config") != _state_identity(config)
    ):
        fail("demo state has the wrong session identity")
    return value


def _state_identity(config: Config) -> dict[str, str]:
    return {
        "repo": str(config.repo),
        "python": str(config.python),
        "seed_input": str(config.seed_input),
        "source_run": str(config.source_run),
        "source_index": str(config.source_index),
        "real_star": str(config.real_star),
        "input_dir": str(config.input_dir),
        "workspace": str(config.workspace),
        "log_dir": str(config.log_dir),
        "account": config.account,
        "partition": config.partition,
        "qos": config.qos,
        "nodelist": config.nodelist,
        "qualification_partition": config.qualification_partition,
    }


def _write_state(config: Config, **updates: object) -> None:
    value = _state(config)
    value.update(updates)
    value["session"] = config.session
    value["config"] = _state_identity(config)
    _atomic_write(
        config.state_file,
        (json.dumps(value, sort_keys=True, indent=2) + "\n").encode(),
        0o600,
    )


def _source_completion_receipt(config: Config) -> Path:
    attempts = _canonical_directory(
        config.source_run / "attempts", "completed source attempts"
    )
    try:
        candidates = sorted(attempts.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        fail(f"could not enumerate completed source attempts: {exc}")
    if not candidates or len(candidates) > 100:
        fail("completed source run has an implausible attempt count")

    entries: list[Path] = []
    for candidate in candidates:
        if (
            not SAFE_ID_RE.fullmatch(candidate.name)
            or not candidate.name.startswith("workflow-")
        ):
            fail(
                f"completed source run has an unexpected attempt entry: "
                f"{candidate}"
            )
        entries.append(_canonical_directory(candidate, "completed source attempt"))
    latest = entries[-1]
    receipt = _canonical_file(
        latest / "attempt-receipt.json", "completed source attempt receipt"
    )
    try:
        record = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"completed source attempt receipt is unreadable: {exc}")
    if not isinstance(record, dict):
        fail("completed source attempt receipt is not an object")
    if (
        record.get("schema_version") != "norad.attempt-receipt.v1"
        or record.get("run_id") != config.source_run.name
        or record.get("workflow_attempt_id") != latest.name
        or record.get("status") != "succeeded"
        or record.get("local_pipeline_complete") is not True
        or record.get("snakemake_exit_code") != 0
        or record.get("termination_signal") is not None
        or record.get("blockers") != []
    ):
        fail("latest retained source attempt is not a successful complete pipeline")
    verified = record.get("verified_tasks")
    reporting = record.get("reporting_completion_records")
    if not isinstance(verified, list) or len(verified) != SOURCE_OWNER_JOBS:
        fail(f"retained source receipt does not bind {SOURCE_OWNER_JOBS} owner jobs")
    if not isinstance(reporting, dict) or set(reporting) != SOURCE_REPORTING_KINDS:
        fail("retained source receipt does not bind all reporting transactions")
    return receipt


def _repo_commit(config: Config) -> str:
    git = shutil.which("git")
    if git is None:
        fail("git is unavailable for the frozen demo checkout check")
    head = _run(
        (git, "rev-parse", "--verify", "HEAD"),
        print_output=False,
        cwd=config.repo,
        timeout=120,
    )
    status = _run(
        (git, "status", "--porcelain=v1", "--untracked-files=all"),
        print_output=False,
        cwd=config.repo,
        timeout=120,
    )
    commit = head.stdout.strip()
    if (
        head.returncode != 0
        or status.returncode != 0
        or not re.fullmatch(r"[0-9a-f]{40}", commit)
        or status.stdout
    ):
        fail("demo checkout must be a clean, committed Git worktree")
    return commit


def _index_identity(config: Config) -> str:
    rows: list[tuple[object, ...]] = []
    for name in INDEX_MEMBERS:
        member = _canonical_file(
            config.source_index / name, "retained STAR index member"
        )
        state = member.stat(follow_symlinks=False)
        rows.append(
            (
                name,
                state.st_dev,
                state.st_ino,
                state.st_size,
                state.st_mtime_ns,
                state.st_ctime_ns,
                state.st_nlink,
            )
        )
    encoded = json.dumps(rows, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _preflight_source(config: Config) -> None:
    _canonical_directory(config.seed_input, "seed input")
    _canonical_directory(config.source_run, "completed source run")
    _canonical_directory(config.source_index, "completed source STAR index")
    _canonical_file(config.source_fasta, "source reference FASTA")
    _canonical_file(config.source_gtf, "source reference GTF")
    _canonical_file(config.real_star, "real STAR", executable=True)
    for path in (
        config.seed_input / "request.yaml",
        config.seed_input / "samples.tsv",
        config.seed_input / "partitions.tsv",
        config.seed_input / "runtime.selected.tsv",
        config.source_fasta.with_suffix(config.source_fasta.suffix + ".fai"),
        config.source_fasta.with_suffix(".dict"),
        config.source_run / "contract/artifact_inventory.tsv",
    ):
        _canonical_file(path, "retained demo prerequisite")
        if path.stat().st_size < 1:
            fail(f"retained demo prerequisite is empty: {path}")
    _source_completion_receipt(config)
    for name in INDEX_MEMBERS:
        member = _canonical_file(
            config.source_index / name, "retained STAR index member"
        )
        if member.stat().st_size < 1:
            fail(f"retained STAR index member is empty: {member}")
    parameters: dict[str, tuple[str, ...]] = {}
    for number, raw in enumerate(
        (config.source_index / "genomeParameters.txt")
        .read_text(encoding="utf-8")
        .splitlines(),
        start=1,
    ):
        fields = raw.split()
        if not fields or fields[0] == "###":
            continue
        if len(fields) < 2 or fields[0] in parameters:
            fail(f"retained genomeParameters.txt is invalid at line {number}")
        parameters[fields[0]] = tuple(fields[1:])
    if parameters.get("genomeFastaFiles") != (str(config.source_fasta),):
        fail("retained STAR index does not bind the selected FASTA")
    if parameters.get("sjdbGTFfile") != (str(config.source_gtf),):
        fail("retained STAR index does not bind the selected GTF")
    if parameters.get("sjdbOverhang") != ("149",):
        fail("retained STAR index does not bind sjdbOverhang 149")
    if parameters.get("genomeSAindexNbases") != ("14",):
        fail("retained STAR index does not bind genomeSAindexNbases 14")
    run_id = config.source_run.name
    for suffix in ("scientific_report.html", "evidence_report.html"):
        report = config.source_run / f"products/report/{run_id}/{run_id}.{suffix}"
        _canonical_file(report, "completed source report")
        if report.stat().st_size < 1:
            fail(f"completed source report is empty: {report}")


def _replace_request_paths(config: Config, data: str) -> bytes:
    replacements = {
        r"(?m)^label:.*$": 'label: "CSU Viking live demo (DEMO ONLY)"',
        r"(?m)^  fasta:.*$": f"  fasta: {config.source_fasta}",
        r"(?m)^  gtf:.*$": f"  gtf: {config.source_gtf}",
    }
    for pattern, replacement in replacements.items():
        updated, count = re.subn(pattern, replacement, data, count=1)
        if count != 1:
            fail(f"seed request does not contain one expected row: {pattern}")
        data = updated
    return data.encode()


def _star_launcher(config: Config) -> bytes:
    proxy = config.repo / "scripts/demo/csu_viking/star_reuse.py"
    _canonical_file(proxy, "tracked demo STAR proxy")
    real_star = _canonical_file(config.real_star, "real STAR", executable=True)
    values = (
        "/usr/bin/python3",
        "-I",
        "-B",
        str(proxy),
        "--real-star",
        str(real_star),
        "--real-star-sha256",
        _sha256(real_star),
        "--source-index",
        str(config.source_index),
        "--source-fasta",
        str(config.source_fasta),
        "--source-gtf",
        str(config.source_gtf),
        "--workspace",
        str(config.workspace),
        "--expected-threads",
        "12",
        "--",
    )
    command = " ".join(shlex.quote(value) for value in values)
    return ("#!/usr/bin/env bash\nset -euo pipefail\nexec " + command + ' "$@"\n').encode()


def _runtime_profile(config: Config, star_launcher: Path) -> bytes:
    source = config.seed_input / "runtime.selected.tsv"
    try:
        rows = list(csv.reader(source.open(encoding="utf-8"), delimiter="\t"))
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"could not read seed runtime profile: {exc}")
    if not rows or rows[0] != [
        "check_id",
        "check_type",
        "runtime_context",
        "required",
        "target",
        "probe_args",
        "expected",
        "description",
    ]:
        fail("seed runtime profile has the wrong header")
    body = [row for row in rows[1:] if len(row) == 8]
    if len(body) != len(rows) - 1:
        fail("seed runtime profile contains a malformed row")
    star_rows = [row for row in body if row[0] == "star"]
    if len(star_rows) != 1:
        fail("seed runtime profile does not contain exactly one STAR row")
    star_rows[0][4] = str(star_launcher)
    for row in body:
        if row[0] in {"python", "snakemake", "sha256_python"}:
            row[4] = str(config.python)
        elif row[0] == "renv_project":
            row[4] = str(config.repo)
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue().encode()


def init_demo(config: Config, *, execute: bool) -> None:
    if not execute:
        completed = _real_cli(
            config,
            "init",
            "local-pilot",
            "--output-dir",
            str(config.input_dir),
        )
        _require_success(completed, "Dry-run complete; no files were written.", "init")
        if os.path.lexists(config.input_dir):
            fail("init dry-run unexpectedly created the demo input directory")
        print(PASS_INIT_DRY)
        return

    _preflight_source(config)
    completed = _real_cli(
        config,
        "init",
        "local-pilot",
        "--output-dir",
        str(config.input_dir),
        "--execute",
    )
    _require_success(
        completed,
        f"Published matched local-pilot starter set: {config.input_dir}",
        "init execute",
    )

    config.workspace_parent.mkdir(mode=0o700, parents=False, exist_ok=False)
    config.log_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    star_launcher = config.input_dir / "STAR.demo"
    _atomic_write(star_launcher, _star_launcher(config), 0o700)
    _atomic_write(
        config.input_dir / "request.yaml",
        _replace_request_paths(
            config,
            (config.seed_input / "request.yaml").read_text(encoding="utf-8"),
        ),
        0o644,
    )
    for name in ("samples.tsv", "partitions.tsv"):
        _atomic_write(
            config.input_dir / name,
            (config.seed_input / name).read_bytes(),
            0o644,
        )
    for source_name, destination_name in (
        (
            "configs/local_pilot_launcher.csu_viking_ev_pum1.yaml",
            "norad.launcher.yaml",
        ),
        (
            "configs/local_pilot_resources.csu_viking_ev_pum1.yaml",
            "norad.resources.yaml",
        ),
    ):
        _atomic_write(
            config.input_dir / destination_name,
            (config.repo / source_name).read_bytes(),
            0o644,
        )
    _atomic_write(
        config.runtime_profile,
        _runtime_profile(config, star_launcher),
        0o644,
    )
    _write_state(config, initialized=True)
    print("DEMO ONLY: retained manifests/configuration staged outside the checkout.")
    print(f"DEMO_INPUT_DIR={config.input_dir}")
    print(f"DEMO_WORKSPACE={config.workspace}")
    print(f"DEMO_LOG_DIR={config.log_dir}")
    print(PASS_INIT)


def _require_initialized(config: Config) -> None:
    if _state(config).get("initialized") is not True:
        fail("run both demo init commands first")
    for path, label in (
        (config.input_dir, "demo input"),
        (config.workspace_parent, "demo workspace parent"),
        (config.log_dir, "demo log directory"),
    ):
        _canonical_directory(path, label)
        state = path.stat(follow_symlinks=False)
        if state.st_uid != os.getuid() or stat.S_IMODE(state.st_mode) != 0o700:
            fail(f"{label} must be a current-UID mode-700 directory: {path}")
    _canonical_file(config.wrapper, "generated Slurm wrapper", executable=True)
    _canonical_file(config.runtime_profile, "demo runtime profile")


def _storage_cli(
    config: Config, phase: str, *, execute: bool
) -> subprocess.CompletedProcess[str]:
    arguments = [
        "inspect",
        "storage-qualification",
        "--workspace",
        str(config.workspace),
        "--reference-fasta",
        str(config.source_fasta),
        "--phase",
        phase,
    ]
    if execute:
        arguments.append("--execute")
    return _real_cli(config, *arguments)


def storage_demo(config: Config, *, execute: bool) -> None:
    _require_initialized(config)
    if not execute:
        for phase in ("compute", "finalize"):
            completed = _storage_cli(config, phase, execute=False)
            _require_success(
                completed,
                "Dry-run complete; no directories or files were created.",
                f"storage {phase} dry-run",
            )
        print(PASS_STORAGE_DRY)
        return

    if os.environ.get("SLURM_JOB_ID"):
        fail("combined demo storage execution must start on the head node")
    if _state(config).get("storage_qualified") is True:
        fail("demo storage qualification already completed for this session")
    sbatch = shutil.which("sbatch")
    if sbatch is None:
        fail("sbatch is unavailable")
    user = _child_environment()["USER"]
    script = config.log_dir / f"storage-compute-{config.session}.sh"
    command = (
        str(config.python),
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "norad",
        "inspect",
        "storage-qualification",
        "--workspace",
        str(config.workspace),
        "--reference-fasta",
        str(config.source_fasta),
        "--phase",
        "compute",
        "--execute",
    )
    quoted = " ".join(shlex.quote(value) for value in command)
    script_bytes = (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "umask 077\n"
        "unset TMPDIR TMP TEMP\n"
        "export TMPDIR=/tmp\n"
        "export PATH=/usr/bin:/bin\n"
        f"export USER={shlex.quote(user)} LOGNAME={shlex.quote(user)}\n"
        "export PYTHONDONTWRITEBYTECODE=1\n"
        "printf 'HOSTNAME=%s\\nSLURM_JOB_ID=%s\\nTMPDIR=%s\\n' "
        '"$(hostname)" "$SLURM_JOB_ID" "$TMPDIR"\n'
        f"cd {shlex.quote(str(config.repo))}\n"
        f"exec {quoted}\n"
    ).encode()
    _atomic_write(script, script_bytes, 0o700)
    submission = _run(
        (
            sbatch,
            "--parsable",
            "--wait",
            "--export=NONE",
            "--job-name=norad-demo-storage",
            f"--account={config.account}",
            f"--partition={config.qualification_partition}",
            f"--qos={config.qos}",
            "--nodes=1",
            "--ntasks=1",
            "--cpus-per-task=1",
            "--time=00:10:00",
            f"--nodelist={config.nodelist}",
            f"--chdir={config.repo}",
            f"--output={config.log_dir}/norad-demo-storage-%j.out",
            f"--error={config.log_dir}/norad-demo-storage-%j.err",
            str(script),
        ),
        print_output=False,
        cwd=config.repo,
        timeout=1800,
    )
    job_id = submission.stdout.strip().split(";", 1)[0]
    if submission.returncode != 0 or not JOB_RE.fullmatch(job_id):
        if submission.stderr:
            print(submission.stderr, file=sys.stderr, end="")
        fail("compute storage qualification Slurm job failed")
    stdout = config.log_dir / f"norad-demo-storage-{job_id}.out"
    stderr = config.log_dir / f"norad-demo-storage-{job_id}.err"
    out_text, err_text = _read_stream_pair(stdout, stderr, timeout=120)
    print(out_text, end="")
    if err_text:
        print(err_text, end="", file=sys.stderr)
    if "Published compute qualification receipt:" not in out_text:
        fail("compute storage qualification receipt was not published")

    finalized = _storage_cli(config, "finalize", execute=True)
    _require_success(
        finalized,
        "Published final storage qualification receipt:",
        "storage finalize",
    )
    _write_state(config, storage_qualified=True)
    print(f"DEMO_STORAGE_JOB_ID={job_id}")
    print(PASS_STORAGE)


def _wrapper_command(config: Config, *, execute: bool) -> tuple[str, ...]:
    command = [
        str(config.wrapper),
        "--launcher-config",
        str(config.input_dir / "norad.launcher.yaml"),
        "--log-dir",
        str(config.log_dir),
        "--request",
        str(config.input_dir / "request.yaml"),
        "--workspace",
        str(config.workspace),
        "--runtime-profile",
        str(config.runtime_profile),
        "--scratch-parent",
        str(config.scratch_parent),
    ]
    if execute:
        command.append("--execute")
    return tuple(command)


def _parse_submission(config: Config, text: str) -> tuple[str, Path, Path]:
    values: dict[str, str] = {}
    for key in ("JOB_ID", "OUT", "ERR"):
        matches = re.findall(rf"(?m)^{key}=(.+)$", text)
        if len(matches) != 1:
            fail(f"generated wrapper did not print exactly one {key}")
        values[key] = matches[0]
    job_id = values["JOB_ID"]
    if not JOB_RE.fullmatch(job_id):
        fail("generated wrapper printed an invalid job ID")
    stdout = _absolute(values["OUT"], "scheduler stdout")
    stderr = _absolute(values["ERR"], "scheduler stderr")
    if (
        stdout.parent != config.log_dir
        or stderr.parent != config.log_dir
        or stdout.name != f"norad-local-pilot-{job_id}.out"
        or stderr.name != f"norad-local-pilot-{job_id}.err"
    ):
        fail("generated wrapper printed unexpected scheduler stream paths")
    return job_id, stdout, stderr


def _slurm_state(job_id: str) -> tuple[str, str] | None:
    squeue = shutil.which("squeue")
    if squeue is not None:
        try:
            result = subprocess.run(
                (squeue, "-h", "-j", job_id, "-o", "%T"),
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            queue_state = result.stdout.splitlines()[0].strip().split("+", 1)[0]
            if queue_state not in TERMINAL_STATES:
                return queue_state, ""

    sacct = shutil.which("sacct")
    if sacct is None:
        fail("sacct is unavailable")
    try:
        result = subprocess.run(
            (
                sacct,
                "-X",
                "-n",
                "-P",
                "-j",
                job_id,
                "--format=JobIDRaw,State,ExitCode",
            ),
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    for raw in result.stdout.splitlines():
        fields = raw.split("|")
        if len(fields) >= 3 and fields[0] == job_id:
            state_fields = fields[1].strip().split()
            if not state_fields:
                continue
            state = state_fields[0].split("+", 1)[0]
            exit_code = fields[2].strip()
            if state in TERMINAL_STATES and not exit_code:
                return None
            return state, exit_code
    return None


def _wait_terminal(job_id: str, timeout: int) -> tuple[str, str]:
    started = time.monotonic()
    last_report = -30.0
    while time.monotonic() - started < timeout:
        observed = _slurm_state(job_id)
        elapsed = time.monotonic() - started
        if observed is not None:
            state, exit_code = observed
            if state in TERMINAL_STATES:
                return state, exit_code
        else:
            state = "ACCOUNTING_PENDING"
        if elapsed - last_report >= 30:
            print(f"DEMO_DRY_RUN_WAIT job={job_id} state={state} elapsed={int(elapsed)}s")
            last_report = elapsed
        time.sleep(5)
    fail(f"timed out waiting for Slurm job {job_id}")


def _read_stream_pair(
    stdout: Path, stderr: Path, *, timeout: int
) -> tuple[str, str]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stdout.exists() and stderr.exists():
            break
        time.sleep(2)
    for path, label in ((stdout, "stdout"), (stderr, "stderr")):
        _canonical_file(path, f"scheduler {label}")
        if path.stat().st_uid != os.getuid():
            fail(f"scheduler {label} is not owned by the current UID")
    return stdout.read_text(errors="replace"), stderr.read_text(errors="replace")


def _workflow_signature(config: Config) -> dict[str, str]:
    names = (
        "request.yaml",
        "samples.tsv",
        "partitions.tsv",
        "runtime.selected.tsv",
        "norad.launcher.yaml",
        "norad.resources.yaml",
        "run-in-slurm.sh",
        "STAR.demo",
    )
    signature = {name: _sha256(config.input_dir / name) for name in names}
    receipt = _source_completion_receipt(config)
    signature.update(
        {
            "repo_commit": _repo_commit(config),
            "demo_driver.py": _sha256(Path(__file__).resolve()),
            "star_reuse.py": _sha256(
                config.repo / "scripts/demo/csu_viking/star_reuse.py"
            ),
            "real_star": _sha256(config.real_star),
            "source_attempt_receipt": _sha256(receipt),
            "source_artifact_inventory": _sha256(
                config.source_run / "contract/artifact_inventory.tsv"
            ),
            "source_index_identity": _index_identity(config),
        }
    )
    return signature


def _one_anchored(text: str, label: str, pattern: str) -> str:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if len(matches) != 1:
        fail(f"workflow dry-run did not print exactly one {label}")
    return matches[0]


def _validate_dry_run_output(
    config: Config,
    out_text: str,
    err_text: str,
    signature: dict[str, str],
) -> dict[str, str]:
    marker = "Dry-run complete; no workspace state was written."
    nonempty = [line for line in out_text.splitlines() if line]
    if not nonempty or nonempty[-1] != marker or err_text:
        fail("workflow dry-run streams do not have the rehearsed clean ending")
    for required in (
        "Local-pilot request validation: PASS",
        "READY: local-pilot prerequisites passed.",
        "Operation: execute",
        "Owner jobs: 73",
    ):
        if required not in out_text:
            fail(f"workflow dry-run omitted required plan evidence: {required}")

    run_ids = set(re.findall(r"(?m)^Run ID: (run-[0-9a-f]{64})$", out_text))
    if len(run_ids) != 1:
        fail("workflow dry-run did not print one consistent run ID")
    run_id = next(iter(run_ids))
    run_root = _one_anchored(out_text, "run root", r"^Run root: (.+)$")
    workspace = _one_anchored(out_text, "workspace", r"^Workspace: (.+)$")
    source_commit = _one_anchored(
        out_text, "source commit", r"^Source commit: ([0-9a-f]{40})$"
    )
    runtime_sha = _one_anchored(
        out_text,
        "runtime-profile digest",
        r"^Runtime profile SHA-256: ([0-9a-f]{64})$",
    )
    expected_root = config.workspace / "runs" / run_id
    if (
        workspace != str(config.workspace)
        or run_root != str(expected_root)
        or source_commit != signature["repo_commit"]
        or runtime_sha != signature["runtime.selected.tsv"]
    ):
        fail("workflow dry-run plan identity differs from the frozen demo inputs")

    receipt_text = _one_anchored(
        out_text, "storage qualification", r"^Storage qualification: (.+)$"
    )
    receipt_sha = _one_anchored(
        out_text,
        "storage qualification digest",
        r"^Storage qualification SHA-256: ([0-9a-f]{64})$",
    )
    receipt = _canonical_file(
        _absolute(receipt_text, "storage qualification"),
        "storage qualification",
    )
    if not receipt.name.endswith(".qualified.json") or _sha256(receipt) != receipt_sha:
        fail("workflow dry-run storage qualification is not the exact final receipt")
    return {
        "run_id": run_id,
        "run_root": run_root,
        "storage_qualification": str(receipt),
        "storage_qualification_sha256": receipt_sha,
        "stdout_sha256": hashlib.sha256(out_text.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(err_text.encode()).hexdigest(),
    }


def _recheck_dry_run_streams(config: Config, state: dict[str, object]) -> None:
    evidence = state.get("dry_run_evidence")
    job_id = state.get("dry_run_job_id")
    if not isinstance(evidence, dict) or not isinstance(job_id, str):
        fail("workflow dry-run evidence is incomplete")
    stdout = config.log_dir / f"norad-local-pilot-{job_id}.out"
    stderr = config.log_dir / f"norad-local-pilot-{job_id}.err"
    out_text, err_text = _read_stream_pair(stdout, stderr, timeout=1)
    if (
        hashlib.sha256(out_text.encode()).hexdigest()
        != evidence.get("stdout_sha256")
        or hashlib.sha256(err_text.encode()).hexdigest()
        != evidence.get("stderr_sha256")
    ):
        fail("reviewed workflow dry-run streams changed before execution")
    receipt_value = evidence.get("storage_qualification")
    receipt_sha = evidence.get("storage_qualification_sha256")
    if not isinstance(receipt_value, str) or not isinstance(receipt_sha, str):
        fail("workflow dry-run storage evidence is incomplete")
    receipt = _canonical_file(
        _absolute(receipt_value, "storage qualification"),
        "storage qualification",
    )
    if _sha256(receipt) != receipt_sha:
        fail("storage qualification changed after the reviewed workflow dry-run")


def _write_job_environment(config: Config, job_id: str) -> None:
    _atomic_write(
        config.job_env_file,
        (
            f"SESSION={config.session}\n"
            f"JOB_ID={job_id}\n"
            f"LOG_DIR={config.log_dir}\n"
        ).encode(),
        0o600,
    )


def _reserve_execution(config: Config, signature: dict[str, str]) -> None:
    reservation = config.log_dir / ".demo-execution-reserved.json"
    try:
        with reservation.open("x", encoding="utf-8") as handle:
            json.dump(
                {
                    "session": config.session,
                    "signature": signature,
                },
                handle,
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fchmod(handle.fileno(), 0o600)
            os.fsync(handle.fileno())
    except FileExistsError:
        fail("demo execution is already reserved or was previously attempted")


def execute_demo(config: Config, *, execute: bool) -> None:
    _require_initialized(config)
    _preflight_source(config)
    state = _state(config)
    if state.get("storage_qualified") is not True:
        fail("run both demo storage-qualification commands first")
    if os.path.lexists(config.workspace):
        fail(f"demo workspace must remain absent before the initial run: {config.workspace}")

    signature = _workflow_signature(config)
    if execute:
        if state.get("workflow_dry_run") is not True:
            fail("run the demo workflow dry-run first")
        if state.get("execution_job_id") is not None:
            fail("the demo execution was already submitted for this session")
        if state.get("workflow_signature") != signature:
            fail("demo inputs changed after the reviewed workflow dry-run")
        _recheck_dry_run_streams(config, state)
        _reserve_execution(config, signature)

    submission = _run(_wrapper_command(config, execute=execute), cwd=config.repo)
    if submission.returncode != 0:
        fail("generated Slurm wrapper submission failed")
    job_id, stdout, stderr = _parse_submission(config, submission.stdout)
    if execute:
        deadline = time.monotonic() + 90
        observed = _slurm_state(job_id)
        while time.monotonic() < deadline and observed is None:
            time.sleep(2)
            observed = _slurm_state(job_id)
        if observed is None:
            fail("execution job was not visible in Slurm after submission")
        _write_job_environment(config, job_id)
        _write_state(config, execution_job_id=job_id)
        print(PASS_SUBMISSION)
        print("Next: make dashboard")
        return

    timeout = int(os.environ.get("NORAD_DEMO_DRY_RUN_TIMEOUT_SECONDS", "3600"))
    state_name, exit_code = _wait_terminal(job_id, timeout)
    out_text, err_text = _read_stream_pair(stdout, stderr, timeout=180)
    if state_name != "COMPLETED" or exit_code != "0:0":
        print(out_text[-8000:], file=sys.stderr)
        print(err_text[-8000:], file=sys.stderr)
        fail(f"workflow dry-run job ended {state_name} with exit {exit_code}")
    if os.path.lexists(config.workspace):
        print(out_text[-8000:], file=sys.stderr)
        print(err_text[-8000:], file=sys.stderr)
        fail("workflow dry-run did not preserve its no-write boundary")
    evidence = _validate_dry_run_output(
        config,
        out_text,
        err_text,
        signature,
    )
    if _workflow_signature(config) != signature:
        fail("demo inputs changed while the workflow dry-run was executing")
    marker = "Dry-run complete; no workspace state was written."
    print(f"JOB_ID={job_id}")
    print(f"OUT={stdout}")
    print(f"ERR={stderr}")
    print(marker)
    _write_state(
        config,
        workflow_dry_run=True,
        workflow_signature=signature,
        dry_run_job_id=job_id,
        dry_run_evidence=evidence,
    )
    print(PASS_WORKFLOW_DRY)


def usage() -> str:
    return """Demo-only command surface (source activate.sh first):
  norad init local-pilot
  norad init local-pilot --execute
  norad inspect storage-qualification
  norad inspect storage-qualification --execute
  norad execute
  norad execute --execute

All other commands are deliberately rejected in demo mode.
"""


def dispatch(config: Config, arguments: Sequence[str]) -> None:
    selected = tuple(arguments)
    if selected == ("init", "local-pilot"):
        init_demo(config, execute=False)
    elif selected == ("init", "local-pilot", "--execute"):
        init_demo(config, execute=True)
    elif selected == ("inspect", "storage-qualification"):
        storage_demo(config, execute=False)
    elif selected == ("inspect", "storage-qualification", "--execute"):
        storage_demo(config, execute=True)
    elif selected == ("execute",):
        execute_demo(config, execute=False)
    elif selected == ("execute", "--execute"):
        execute_demo(config, execute=True)
    elif selected in {("-h",), ("--help",)}:
        print(usage(), end="")
    else:
        fail("unsupported demo command\n" + usage())


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = load_config()
        dispatch(config, sys.argv[1:] if argv is None else argv)
        return 0
    except (DemoError, OSError, ValueError) as exc:
        print(f"DEMO ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
