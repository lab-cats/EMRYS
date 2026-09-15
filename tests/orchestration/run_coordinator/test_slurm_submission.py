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
    environment = {"SLURM_JOB_ID": job_id}
    exports = next(arg for arg in plan.argv if arg.startswith("--export="))
    for entry in exports.removeprefix("--export=").split(","):
        name, separator, value = entry.partition("=")
        if separator:
            environment[name] = value
        elif name in plan.environment:
            environment[name] = plan.environment[name]
    return environment


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
        f"{slurm_submission.SUBMIT_UID_ENV}=1234,LOGNAME,USER,LNAME,USERNAME",
    )
    assert dict(plan.environment) == {"KEEP": "yes"}
    assert plan.stdout_pattern == log_dir / "emrys-local-pilot-%j.out"
    assert plan.stderr_pattern == log_dir / "emrys-local-pilot-%j.err"
    assert plan.batch_script.startswith("#!/bin/bash\nset -euo pipefail\n")
    assert '/bin/rm -rf --one-file-system -- "$job_tmpdir"' in plan.batch_script
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
            "errors": "replace",
            "capture_output": True,
            "check": False,
        },
    )


@pytest.mark.parametrize(
    ("returncode", "stdout", "message"),
    (
        (1, "", "job ID unconfirmed"),
        (1, "812345;cluster\n", "accepted job 812345"),
        (0, "", "Invalid sbatch response"),
        (0, "123\n456\n", "Invalid sbatch response"),
        (0, "123;cluster;extra\n", "Invalid sbatch response"),
        (0, "not-a-job\n", "Invalid sbatch response"),
        (0, "0\n", "Invalid sbatch response"),
        (0, "00\n", "Invalid sbatch response"),
        (0, "１２３\n", "Invalid sbatch response"),
        (1, "invalid\x1b[31m\n", "Invalid sbatch response"),
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
    detail = 'submission rejected: "memory"\n\x1b[31m' + "x" * 4096 + "hidden tail"

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal call_count
        call_count += 1
        return subprocess.CompletedProcess(args, returncode, stdout, detail)

    monkeypatch.setattr(slurm_submission.subprocess, "run", fake_run)

    with pytest.raises(slurm_submission.SlurmSubmissionError, match=message) as caught:
        slurm_submission.submit(plan)
    assert call_count == 1
    diagnostic = str(caught.value)
    assert "\x1b" not in diagnostic and "\n" not in diagnostic
    assert "hidden tail" not in diagnostic
    if returncode and stdout in {"", "812345;cluster\n"}:
        assert "sbatch exited with 1" in diagnostic
        assert "cancelled" not in diagnostic
    assert ascii(detail[:4096]) in diagnostic
    if stdout == "812345;cluster\n":
        assert str(plan.stdout_pattern).replace("%j", "812345") in diagnostic
        assert str(plan.stderr_pattern).replace("%j", "812345") in diagnostic


@pytest.mark.parametrize("failure", ("invoke", "waited_invoke", "records"))
def test_submission_io_failure_preserves_cause_and_does_not_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    plan = slurm_submission.plan_submission(
        _profile(tmp_path),
        emrys_argv=("emrys", "doctor"),
        log_dir=tmp_path,
        sbatch=str(tmp_path / "missing-sbatch"),
    )
    transcript = None if failure == "invoke" else tmp_path / "submission.stdout"
    if failure == "records":
        transcript.write_bytes(b"preserved submission\n")
    attempts = []
    real_popen = slurm_submission.subprocess.Popen

    def popen(*args, **kwargs):
        attempts.append(args)
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(slurm_submission.subprocess, "Popen", popen)
    operation = (
        "prepare submission records" if failure == "records" else "invoke sbatch"
    )
    with pytest.raises(
        slurm_submission.SlurmSubmissionError, match=f"Could not {operation}"
    ) as caught:
        slurm_submission.submit(plan, wait_record=transcript)
    assert "job ID unconfirmed" in str(caught.value)
    assert isinstance(caught.value.__cause__, OSError)
    assert ascii(str(caught.value.__cause__)) in str(caught.value)
    assert len(attempts) == (0 if failure == "records" else 1)
    if failure == "records":
        assert transcript.read_bytes() == b"preserved submission\n"


@pytest.mark.parametrize("username_variable", ("LOGNAME", "USER", "LNAME", "USERNAME"))
def test_batch_script_checks_identity_loads_modules_and_cleans_private_scratch(
    tmp_path: Path,
    username_variable: str,
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
        "import getpass, json, os, pathlib, stat, sys; "
        "from unittest.mock import patch; "
        "patch('pwd.getpwuid', side_effect=KeyError('uid not found')).start(); "
        "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
        "'arguments': sys.argv[2:], "
        "'username': getpass.getuser(), "
        "'ambient': os.environ.get('UNRELATED'), "
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
        environment={
            username_variable: "login,name=$(must-not-expand)",
            "UNRELATED": "no",
        },
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
    assert observed["username"] == "login,name=$(must-not-expand)"
    assert observed["ambient"] is None
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


@pytest.mark.parametrize(
    "outcome",
    (
        "success",
        "failed",
        "interrupted",
        "rejected",
        "ambiguous",
        "record_failure",
        "wait_failure",
    ),
)
def test_waited_submission_announces_job_before_wait_and_retains_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    release = tmp_path / "release"
    submitted = tmp_path / "submitted"
    scheduler = tmp_path / "sbatch"
    detail = (
        b'scheduler diagnostics: "reason"\n\x1b[31m\xff' + b"x" * 4096 + b"hidden tail"
    )
    scheduler.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, sys, time\n"
        "assert '--wait' in sys.argv\n"
        "assert sys.stdin.read().startswith('#!/bin/bash')\n"
        f"with pathlib.Path({str(submitted)!r}).open('ab') as handle: handle.write(b'submit\\n')\n"
        f"sys.stderr.buffer.write({detail!r}); sys.stderr.flush()\n"
        f"if {outcome == 'rejected'}: raise SystemExit(2)\n"
        "print('614999;fixture', flush=True)\n"
        f"while not pathlib.Path({str(release)!r}).exists(): time.sleep(0.01)\n"
        f"if {outcome in {'ambiguous', 'wait_failure'}}: print('extra output', flush=True)\n"
        f"raise SystemExit({1 if outcome == 'failed' else 0})\n",
    )
    scheduler.chmod(0o700)
    submission = slurm_submission.plan_submission(
        _profile(tmp_path),
        emrys_argv=("emrys", "doctor"),
        log_dir=tmp_path,
        sbatch=str(scheduler),
    )
    transcript = tmp_path / "submission.stdout"
    received: list[str] = []
    if outcome == "record_failure":

        def fail_fsync(_descriptor: int) -> None:
            raise OSError("fixture fsync failed")

        monkeypatch.setattr(slurm_submission.os, "fsync", fail_fsync)
    if outcome == "wait_failure":
        real_wait = slurm_submission.subprocess.Popen.wait
        failed_wait = False

        def fail_wait_once(process, *args, **kwargs):
            nonlocal failed_wait
            if not failed_wait:
                failed_wait = True
                raise OSError("fixture wait failed")
            return real_wait(process, *args, **kwargs)

        monkeypatch.setattr(slurm_submission.subprocess.Popen, "wait", fail_wait_once)

    def announce(job_id: str) -> None:
        received.append(job_id)
        assert transcript.read_text() == "614999;fixture\n"
        assert "Slurm job 614999" in capsys.readouterr().err
        if outcome == "interrupted":
            raise KeyboardInterrupt
        release.touch()

    if outcome == "success":
        assert (
            slurm_submission.submit(
                submission, wait_record=transcript, on_submitted=announce
            )
            == "614999"
        )
    else:
        error = (
            KeyboardInterrupt
            if outcome == "interrupted"
            else slurm_submission.SlurmSubmissionError
        )
        with pytest.raises(error) as caught:
            slurm_submission.submit(
                submission, wait_record=transcript, on_submitted=announce
            )
        if outcome != "interrupted":
            diagnostic = str(caught.value)
            identity = "unconfirmed" if outcome == "rejected" else "614999"
            assert identity in diagnostic
            assert "cancelled" not in diagnostic
            assert "\x1b" not in diagnostic and "\n" not in diagnostic
            assert "hidden tail" not in diagnostic
            if outcome == "record_failure":
                assert (
                    "Could not retain submission records; job ID 614999" in diagnostic
                )
                assert "fixture fsync failed" in diagnostic
            elif outcome == "wait_failure":
                assert "Could not wait for sbatch; job ID 614999" in diagnostic
                assert "fixture wait failed" in diagnostic
            else:
                assert r"\x1b" in diagnostic and r"\ufffd" in diagnostic
            if outcome == "failed":
                assert "accepted job 614999: sbatch exited with 1" in diagnostic
                assert (
                    str(submission.stderr_pattern).replace("%j", "614999") in diagnostic
                )
    assert submitted.read_bytes() == b"submit\n"
    assert received == ([] if outcome in {"rejected", "record_failure"} else ["614999"])
    expected_stdout = "" if outcome == "rejected" else "614999;fixture\n"
    assert transcript.read_text() == expected_stdout + (
        "extra output\n" if outcome in {"ambiguous", "wait_failure"} else ""
    )
    assert transcript.with_suffix(".stderr").read_bytes() == detail
    assert transcript.stat().st_mode & 0o777 == 0o600
    assert transcript.with_suffix(".stderr").stat().st_mode & 0o777 == 0o600
