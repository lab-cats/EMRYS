"""Focused contracts for the private whole-Run Slurm transport."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from emrys.orchestration.run_coordinator import slurm_submission


@dataclass(frozen=True, slots=True)
class _Placement:
    kind: str
    account: str | None
    partition: str | None
    qos: str | None
    cpus_per_task: int
    memory_mb: int | None
    time: str
    exclusive: bool
    nodelist: str | None
    scratch_parent: Path
    module_init: Path | None
    modules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Profile:
    binding_sha256: str
    placement: _Placement


def _profile(
    tmp_path: Path,
    *,
    module_init: Path | None = None,
    modules: tuple[str, ...] = (),
    memory_mb: int | None = 16384,
) -> _Profile:
    scratch = tmp_path / "scratch parent"
    scratch.mkdir()
    return _Profile(
        binding_sha256="a" * 64,
        placement=_Placement(
            kind="slurm",
            account="research-account",
            partition="compute",
            qos="normal",
            cpus_per_task=8,
            memory_mb=memory_mb,
            time="02:30:00",
            exclusive=True,
            nodelist="node-[01-02]",
            scratch_parent=scratch,
            module_init=module_init,
            modules=modules,
        ),
    )


def _batch_environment(
    plan: slurm_submission.SlurmSubmission,
    *,
    job_id: str = "700123",
) -> dict[str, str]:
    return {
        "SLURM_JOB_ID": job_id,
        slurm_submission.DELEGATE_MARKER_ENV: slurm_submission.DELEGATE_MARKER,
        slurm_submission.PROFILE_SHA256_ENV: "a" * 64,
        slurm_submission.SUBMIT_UID_ENV: str(os.getuid()),
    }


def test_plan_is_no_write_and_builds_exact_sbatch_argv(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    log_dir = tmp_path / "log files"
    log_dir.mkdir()
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    plan = slurm_submission.plan_submission(
        profile,  # type: ignore[arg-type]
        emrys_argv=(
            "/opt/emrys/python",
            "-I",
            "-m",
            "emrys",
            "run",
            "--project",
            "/data/request with spaces.yaml",
        ),
        log_dir=log_dir,
        sbatch="/opt/slurm/bin/sbatch",
        environment={
            "KEEP": "yes",
            "SBATCH_ACCOUNT": "ambient-account",
            "SBATCH_FAKE": "ambient-flag",
            slurm_submission.DELEGATE_MARKER_ENV: "ambient-marker",
            slurm_submission.PROFILE_SHA256_ENV: "b" * 64,
            "EMRYS_PRIVATE_SLURM_UNKNOWN": "ambient-private-value",
        },
        submitter_uid=1234,
    )

    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before
    assert plan.argv == (
        "/opt/slurm/bin/sbatch",
        "--parsable",
        "--account=research-account",
        "--partition=compute",
        "--qos=normal",
        "--nodes=1",
        "--ntasks=1",
        "--cpus-per-task=8",
        "--mem=16384M",
        "--exclusive",
        "--nodelist=node-[01-02]",
        "--time=02:30:00",
        "--job-name=emrys-local-pilot",
        f"--output={log_dir}/emrys-local-pilot-%j.out",
        f"--error={log_dir}/emrys-local-pilot-%j.err",
        "--export="
        f"{slurm_submission.DELEGATE_MARKER_ENV}="
        f"{slurm_submission.DELEGATE_MARKER},"
        f"{slurm_submission.PROFILE_SHA256_ENV}={'a' * 64},"
        f"{slurm_submission.SUBMIT_UID_ENV}=1234",
    )
    assert dict(plan.environment) == {"KEEP": "yes"}
    assert plan.stdout_pattern == log_dir / "emrys-local-pilot-%j.out"
    assert plan.stderr_pattern == log_dir / "emrys-local-pilot-%j.err"
    assert plan.batch_script.startswith("#!/bin/bash\nset -euo pipefail\n")
    assert "--wrap" not in plan.argv


def test_optional_scheduler_flags_and_invalid_module_pairing(tmp_path: Path) -> None:
    profile = _profile(tmp_path, memory_mb=None)
    profile = replace(
        profile,
        placement=replace(
            profile.placement,
            account=None,
            partition=None,
            qos=None,
            exclusive=False,
            nodelist=None,
        ),
    )

    plan = slurm_submission.plan_submission(
        profile,  # type: ignore[arg-type]
        emrys_argv=("/opt/emrys/python", "-m", "emrys", "run"),
        log_dir=tmp_path / "logs",
    )

    assert not any(
        argument.startswith(("--account=", "--partition=", "--qos=", "--mem="))
        for argument in plan.argv
    )
    assert "--exclusive" not in plan.argv
    assert not any(argument.startswith("--nodelist=") for argument in plan.argv)

    invalid = replace(
        profile,
        placement=replace(profile.placement, modules=("STAR/2.7.11b",)),
    )
    with pytest.raises(
        slurm_submission.SlurmSubmissionError,
        match="modules require an explicit module init",
    ):
        slurm_submission.plan_submission(
            invalid,  # type: ignore[arg-type]
            emrys_argv=("emrys", "run"),
            log_dir=tmp_path / "logs",
        )

    direct = replace(profile, placement=replace(profile.placement, kind="direct"))
    with pytest.raises(
        slurm_submission.SlurmSubmissionError,
        match="requires Slurm placement",
    ):
        slurm_submission.plan_submission(
            direct,  # type: ignore[arg-type]
            emrys_argv=("emrys", "run"),
            log_dir=tmp_path / "logs",
        )


def test_scheduler_log_parent_rejects_sbatch_percent_tokens(tmp_path: Path) -> None:
    with pytest.raises(
        slurm_submission.SlurmSubmissionError,
        match="scheduler log directory must not contain",
    ):
        slurm_submission.plan_submission(
            _profile(tmp_path),  # type: ignore[arg-type]
            emrys_argv=("emrys", "run"),
            log_dir=tmp_path / "workspace%j" / "logs",
        )


def test_submit_uses_one_process_call_and_parses_one_job_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = slurm_submission.plan_submission(
        _profile(tmp_path),  # type: ignore[arg-type]
        emrys_argv=("/opt/emrys/python", "-m", "emrys", "run"),
        log_dir=tmp_path / "logs",
        environment={"KEEP": "yes", "SBATCH_FAKE": "discard"},
    )
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_run(
        argv: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "812345;cluster-a\n", "")

    monkeypatch.setattr(slurm_submission.subprocess, "run", fake_run)

    assert slurm_submission.submit(plan) == "812345"
    assert len(calls) == 1
    assert calls[0] == (
        plan.argv,
        {
            "input": plan.batch_script,
            "env": {"KEEP": "yes"},
            "text": True,
            "capture_output": True,
            "check": False,
        },
    )


@pytest.mark.parametrize(
    ("returncode", "stdout", "message"),
    (
        (1, "", "sbatch failed with exit 1"),
        (0, "", "one parsable job ID"),
        (0, "123\n456\n", "one parsable job ID"),
        (0, "123;cluster;extra\n", "invalid job ID"),
        (0, "not-a-job\n", "invalid job ID"),
        (0, "0\n", "invalid job ID"),
        (0, "00\n", "invalid job ID"),
        (0, "１２３\n", "invalid job ID"),
    ),
)
def test_submit_rejects_failed_or_ambiguous_scheduler_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    message: str,
) -> None:
    plan = slurm_submission.plan_submission(
        _profile(tmp_path),  # type: ignore[arg-type]
        emrys_argv=("emrys", "run"),
        log_dir=tmp_path / "logs",
    )
    call_count = 0

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal call_count
        call_count += 1
        return subprocess.CompletedProcess(args, returncode, stdout, "scheduler error")

    monkeypatch.setattr(slurm_submission.subprocess, "run", fake_run)

    with pytest.raises(slurm_submission.SlurmSubmissionError, match=message):
        slurm_submission.submit(plan)
    assert call_count == 1


def test_batch_script_checks_identity_loads_modules_and_cleans_private_scratch(
    tmp_path: Path,
) -> None:
    module_capture = tmp_path / "module calls.jsonl"
    module_init = tmp_path / "module init.sh"
    module_init.write_text(
        "module() { printf '%s\\n' \"$*\" >> "
        f"{shlex.quote(str(module_capture))}; }}\n",
        encoding="utf-8",
    )
    profile = _profile(
        tmp_path,
        module_init=module_init,
        modules=("Java/17", "STAR/2.7.11b"),
    )
    command_capture = tmp_path / "command.json"
    command_code = (
        "import json, os, pathlib, stat, sys; "
        "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
        "'arguments': sys.argv[2:], "
        "'delegate': os.environ['EMRYS_PRIVATE_SLURM_DELEGATE'], "
        "'profile': os.environ['EMRYS_PRIVATE_SLURM_PROFILE_SHA256'], "
        "'scratch': os.environ['TMPDIR'], "
        "'scratch_mode': stat.S_IMODE(os.stat(os.environ['TMPDIR']).st_mode)"
        "}), encoding='utf-8'); "
        "pathlib.Path(os.environ['TMPDIR'], 'temporary').write_text('work')"
    )
    plan = slurm_submission.plan_submission(
        profile,  # type: ignore[arg-type]
        emrys_argv=(
            sys.executable,
            "-c",
            command_code,
            str(command_capture),
            "argument with spaces",
            "$(must-not-expand)",
        ),
        log_dir=tmp_path / "logs",
    )

    completed = subprocess.run(
        ("/bin/bash",),
        input=plan.batch_script,
        env=_batch_environment(plan),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert module_capture.read_text(encoding="utf-8").splitlines() == [
        "purge",
        "load Java/17",
        "load STAR/2.7.11b",
    ]
    observed = json.loads(command_capture.read_text(encoding="utf-8"))
    assert observed["arguments"] == ["argument with spaces", "$(must-not-expand)"]
    assert observed["delegate"] == slurm_submission.DELEGATE_MARKER
    assert observed["profile"] == "a" * 64
    assert observed["scratch"].startswith(str(profile.placement.scratch_parent) + "/")
    assert observed["scratch_mode"] == 0o700
    assert list(profile.placement.scratch_parent.iterdir()) == []


def test_batch_script_rejects_submitter_uid_drift_before_running(
    tmp_path: Path,
) -> None:
    capture = tmp_path / "must-not-exist"
    profile = _profile(tmp_path)
    plan = slurm_submission.plan_submission(
        profile,  # type: ignore[arg-type]
        emrys_argv=("/usr/bin/touch", str(capture)),
        log_dir=tmp_path / "logs",
        submitter_uid=os.getuid() + 1,
    )
    environment = _batch_environment(plan)
    environment[slurm_submission.SUBMIT_UID_ENV] = str(os.getuid() + 1)

    completed = subprocess.run(
        ("/bin/bash",),
        input=plan.batch_script,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "batch UID does not match the submitter" in completed.stderr
    assert not capture.exists()
    assert list(profile.placement.scratch_parent.iterdir()) == []
