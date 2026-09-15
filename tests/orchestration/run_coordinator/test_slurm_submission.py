"""Focused contracts for the private whole-Run Slurm transport."""

from __future__ import annotations

import json
import os
import shlex
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from emrys.orchestration.run_coordinator import slurm_submission


def _request_record(
    tmp_path: Path,
    token: str = "a",
    *,
    stdout: bytes = b"700123\n",
    stderr: bytes = b"",
) -> tuple[Path, Path, dict[str, object]]:
    project = tmp_path / "project.yaml"
    project.touch(exist_ok=True)
    root = tmp_path / "logs" / ("submission-" + token * 32)
    root.mkdir(parents=True)
    context = {
        "schema_version": "emrys.submission-request.v1",
        "created_at": "2026-09-15T12:00:00+00:00",
        "submitter_uid": os.getuid(),
        "command": "run",
        "project": str(project),
        "requested_run": None,
        "analysis": None,
        "application_log_root": str(tmp_path / "custom application logs"),
        "profile_binding_sha256": "f" * 64,
        "emrys_argv": [
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "emrys",
            "run",
            "--project",
            str(project),
        ],
        "scheduler_stdout_pattern": str(tmp_path / "logs" / "emrys-local-pilot-%j.out"),
        "scheduler_stderr_pattern": str(tmp_path / "logs" / "emrys-local-pilot-%j.err"),
    }
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(context)
    )
    (root / "sbatch.stdout").write_bytes(stdout)
    (root / "sbatch.stderr").write_bytes(stderr)
    return project, root, context


def test_submission_requests_keep_all_retained_responses_without_scheduler_or_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, first, context = _request_record(
        tmp_path, stdout=b"700123;other-cluster\n", stderr=b"reason:\xff\n"
    )
    _, second, _ = _request_record(tmp_path, "b")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    monkeypatch.setattr(
        slurm_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("discovery invoked a subprocess"),
    )
    observations = slurm_submission.submission_requests(project)
    assert [item.request_root for item in observations] == [first, second]
    assert [item.recorded_job_id for item in observations] == ["700123", "700123"]
    assert [item.recorded_cluster for item in observations] == ["other-cluster", None]
    assert all(item.record_status == "recorded-response" for item in observations)
    assert (
        observations[0].context["application_log_root"]
        == context["application_log_root"]
    )
    assert observations[0].stderr_excerpt == b"reason:\xff\n"
    assert isinstance(observations[0].context["emrys_argv"], tuple)
    assert {
        path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before


@pytest.mark.parametrize(
    "response",
    [
        b"",
        b"70012",
        b"0\n",
        b"0700123\n",
        b"700123\n700124\n",
        b"700123;\n",
        b"700123;bad;cluster\n",
        b"\xff\n",
        b"7" * 4097 + b"\n",
    ],
)
def test_submission_request_preserves_unconfirmed_response(
    tmp_path: Path,
    response: bytes,
) -> None:
    project, _, _ = _request_record(tmp_path, stdout=response)
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == "unconfirmed"
    assert observed.context is not None
    assert observed.recorded_job_id is None
    assert "unconfirmed" in " ".join(observed.diagnostics)


@pytest.mark.parametrize("missing", ["request.json", "sbatch.stdout", "sbatch.stderr"])
def test_submission_request_retains_partial_record_identity(
    tmp_path: Path,
    missing: str,
) -> None:
    project, root, _ = _request_record(tmp_path)
    (root / missing).unlink()
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.request_root == root
    assert observed.record_status == "partial"
    assert observed.recorded_job_id == (
        "700123" if missing == "sbatch.stderr" else None
    )
    assert observed.diagnostics


@pytest.mark.parametrize(
    "defect",
    [
        "extra-field",
        "uid",
        "project",
        "run",
        "version",
        "timestamp",
        "path",
        "argv",
        "duplicate-json",
        "noncanonical-json",
        "oversized",
    ],
)
def test_submission_request_rejects_malformed_context(
    tmp_path: Path,
    defect: str,
) -> None:
    project, root, context = _request_record(tmp_path)
    changes = {
        "extra-field": {"future": True},
        "uid": {"submitter_uid": os.getuid() + 1},
        "project": {"project": str(tmp_path / "other.yaml")},
        "run": {"requested_run": "run-" + "e" * 64},
        "version": {"schema_version": "v2"},
        "timestamp": {"created_at": "2026-09-15T12:00:00"},
        "path": {"scheduler_stdout_pattern": "/other/%j.out"},
        "argv": {"emrys_argv": []},
    }
    context.update(changes.get(defect, {}))
    data = slurm_submission.orchestration_contracts.canonical_json_bytes(context)
    if defect == "duplicate-json":
        data = b'{"command":"run",' + data[1:]
    elif defect == "noncanonical-json":
        data += b"\n"
    elif defect == "oversized":
        data += b" " * 65537
    (root / "request.json").write_bytes(data)
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == "malformed"
    assert observed.context is None and observed.recorded_job_id is None
    assert observed.diagnostics


@pytest.mark.parametrize(
    "defect",
    [
        "name",
        "directory-symlink",
        "directory-loop",
        "file-symlink",
        "unexpected-entry",
        "directory-owner",
        "file-owner",
    ],
)
def test_submission_request_rejects_unowned_or_noncanonical_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    project, root, _ = _request_record(tmp_path)
    if defect == "name":
        root.rename(root.with_name("submission-not-a-uuid"))
    elif defect in {"directory-symlink", "directory-loop"}:
        held = tmp_path / "held"
        root.rename(held)
        root.symlink_to(
            held if defect == "directory-symlink" else root.name,
            target_is_directory=True,
        )
    elif defect == "file-symlink":
        (root / "sbatch.stdout").unlink()
        (root / "sbatch.stdout").symlink_to(project)
    elif defect == "unexpected-entry":
        (root / "extra").touch()
    elif defect == "directory-owner":
        original = slurm_submission.directory_entries_with_identity

        def unowned_directory(path: Path, label: str):
            entries, identity = original(path, label)
            return entries, SimpleNamespace(
                st_uid=os.getuid() + 1
            ) if path == root else identity

        monkeypatch.setattr(
            slurm_submission, "directory_entries_with_identity", unowned_directory
        )
    else:
        original = slurm_submission.read_bytes_with_identity

        def unowned_file(*args, **kwargs):
            data, _ = original(*args, **kwargs)
            return data, SimpleNamespace(st_uid=os.getuid() + 1)

        monkeypatch.setattr(slurm_submission, "read_bytes_with_identity", unowned_file)
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == "malformed"
    assert observed.context is None and observed.recorded_job_id is None


def test_submission_request_bounds_stderr_and_refuses_roster_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, _, _ = _request_record(tmp_path, stderr=b"e" * 8192)
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == "recorded-response"
    assert observed.stderr_excerpt == b"e" * 4096
    original = slurm_submission.read_bytes_with_identity

    def replace_roster(*args, **kwargs):
        result = original(*args, **kwargs)
        (tmp_path / "logs" / "changed").touch()
        return result

    monkeypatch.setattr(slurm_submission, "read_bytes_with_identity", replace_roster)
    with pytest.raises(slurm_submission.SlurmSubmissionError, match="roster changed"):
        slurm_submission.submission_requests(project)


def test_submission_request_empty_roster_does_not_create_logs(tmp_path: Path) -> None:
    project = tmp_path / "project.yaml"
    project.touch()
    assert slurm_submission.submission_requests(project) == ()
    assert not (tmp_path / "logs").exists()


def test_request_context_preserves_empty_analysis(tmp_path: Path) -> None:
    project, root, context = _request_record(tmp_path)
    context["analysis"] = ""
    context["emrys_argv"].extend(("--analysis", ""))
    admitted = slurm_submission.validate_request_context(context, project)
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(admitted)
    )
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == "recorded-response"
    assert observed.context["analysis"] == ""
    assert observed.context["emrys_argv"][-2:] == ("--analysis", "")


@pytest.mark.parametrize("extra_bytes", [0, 1])
def test_request_context_writer_and_reader_share_serialized_byte_limit(
    tmp_path: Path, extra_bytes: int
) -> None:
    project, root, context = _request_record(tmp_path)
    context["emrys_argv"].append("é")
    size = len(slurm_submission.orchestration_contracts.canonical_json_bytes(context))
    context["emrys_argv"][-1] += "x" * (65536 - size + extra_bytes)
    data = slurm_submission.orchestration_contracts.canonical_json_bytes(context)
    assert len(data) == 65536 + extra_bytes
    if extra_bytes:
        with pytest.raises(slurm_submission.SlurmSubmissionError, match="64 KiB"):
            slurm_submission.validate_request_context(context, project)
    else:
        assert slurm_submission.validate_request_context(context, project) == context
    (root / "request.json").write_bytes(data)
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == (
        "malformed" if extra_bytes else "recorded-response"
    )
    if extra_bytes:
        assert observed.context is None
        assert "64 KiB" in " ".join(observed.diagnostics)
    else:
        assert observed.context["emrys_argv"] == tuple(context["emrys_argv"])


@pytest.mark.parametrize("command", ["resume", "report"])
def test_request_context_retains_exact_requested_run(
    tmp_path: Path,
    command: str,
) -> None:
    project, root, context = _request_record(tmp_path)
    run_id = "run-" + "e" * 64
    context.update(command=command, requested_run=run_id)
    context["emrys_argv"][6:7] = [command, run_id]
    admitted = slurm_submission.validate_request_context(context, project)
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(admitted)
    )
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.context["requested_run"] == run_id
    assert observed.context["command"] == command


@pytest.mark.parametrize("command", ["run", "resume", "report"])
@pytest.mark.parametrize("version", ["v2", "v3"])
def test_request_specific_streams_roundtrip_through_producer_and_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str, version: str
) -> None:
    project, root, context = _request_record(tmp_path)
    context.update(
        schema_version=f"emrys.submission-request.{version}",
        command=command,
        requested_run=None if command == "run" else "run-" + "e" * 64,
    )
    plan = slurm_submission.plan_submission(
        _profile(tmp_path),
        emrys_argv=context["emrys_argv"],
        log_dir=project.parent / "logs",
        request_token="a" * 32,
    )
    context.update(
        scheduler_stdout_pattern=str(plan.stdout_pattern),
        scheduler_stderr_pattern=str(plan.stderr_pattern),
    )
    if version == "v3":
        context["scheduler_job_name"] = plan.job_name
        assert f"--job-name={plan.job_name}" in plan.argv
    admitted = slurm_submission.validate_request_context(context, project, root)
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(admitted)
    )
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.record_status == "recorded-response"
    assert observed.context["scheduler_stdout_pattern"] == str(plan.stdout_pattern)
    assert observed.context["scheduler_stderr_pattern"] == str(plan.stderr_pattern)
    assert observed.context["requested_run"] == context["requested_run"]
    monkeypatch.setattr(
        slurm_submission.scheduler_observation,
        "command_bytes",
        lambda *_args, **_kwargs: (
            f"700123|{os.getuid()}|RUNNING|alpha|{plan.stdout_pattern}|{plan.stderr_pattern}|None"
            + (f"|{plan.job_name}" if version == "v3" else "")
            + "\n"
        ).encode(),
    )
    state = slurm_submission.observe_submission_request(observed)
    assert state["source"] == "squeue" and state["state"] == "RUNNING"
    assert state.get("job_name") == (plan.job_name if version == "v3" else None)


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "wrong-token",
        "legacy-name",
        "empty",
        "wrong-type",
        "extra",
        "v1",
        "v2",
    ],
)
def test_v3_request_name_is_closed_and_bound_to_its_request_token(
    tmp_path: Path, defect: str
) -> None:
    project, root, context = _request_record(tmp_path)
    plan = slurm_submission.plan_submission(
        _profile(tmp_path),
        emrys_argv=("emrys", "run"),
        log_dir=project.parent / "logs",
        request_token="a" * 32,
    )
    context.update(
        schema_version="emrys.submission-request.v3",
        scheduler_job_name=plan.job_name,
        scheduler_stdout_pattern=str(plan.stdout_pattern),
        scheduler_stderr_pattern=str(plan.stderr_pattern),
    )
    if defect == "missing":
        del context["scheduler_job_name"]
    elif defect == "extra":
        context["cancellable"] = True
    elif defect in ("v1", "v2"):
        context["schema_version"] = f"emrys.submission-request.{defect}"
    else:
        context["scheduler_job_name"] = {
            "wrong-token": plan.job_name.replace("a" * 32, "b" * 32),
            "legacy-name": "emrys-local-pilot",
            "empty": "",
            "wrong-type": [plan.job_name],
        }[defect]
    with pytest.raises(slurm_submission.SlurmSubmissionError):
        slurm_submission.validate_request_context(context, project, root)
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(context)
    )
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.context is None and observed.record_status == "malformed"


@pytest.mark.parametrize("record", ["legacy", "partial", "unconfirmed"])
def test_request_observation_requires_complete_unique_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: str
) -> None:
    project, root, _ = _request_record(tmp_path)
    if record == "partial":
        (root / "sbatch.stderr").unlink()
    elif record == "unconfirmed":
        (root / "sbatch.stdout").write_bytes(b"")
    (request,) = slurm_submission.submission_requests(project)
    monkeypatch.setattr(
        slurm_submission.scheduler_observation,
        "command_bytes",
        lambda *_args, **_kwargs: pytest.fail("unbound request queried the scheduler"),
    )
    observed = slurm_submission.observe_submission_request(request)
    assert observed["state"] == "UNKNOWN" and observed["diagnostic"]


@pytest.mark.parametrize(
    "defect", ["missing-root", "other-root", "legacy-paths", "mixed-token"]
)
def test_request_specific_streams_refuse_unbound_paths(
    tmp_path: Path, defect: str
) -> None:
    project, root, context = _request_record(tmp_path)
    context["schema_version"] = "emrys.submission-request.v2"
    for stream, suffix in (("stdout", "out"), ("stderr", "err")):
        context[f"scheduler_{stream}_pattern"] = str(
            project.parent / "logs" / f"emrys-local-pilot-{'a' * 32}-%j.{suffix}"
        )
    selected = root
    if defect == "missing-root":
        selected = None
    elif defect == "other-root":
        selected = root.with_name("submission-" + "b" * 32)
    elif defect == "legacy-paths":
        context["scheduler_stdout_pattern"] = str(
            root.parent / "emrys-local-pilot-%j.out"
        )
    else:
        context["scheduler_stderr_pattern"] = str(
            root.parent / f"emrys-local-pilot-{'b' * 32}-%j.err"
        )
    with pytest.raises(slurm_submission.SlurmSubmissionError):
        slurm_submission.validate_request_context(context, project, selected)


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

    def validate_reservation(self) -> None:
        """This transport fixture is already admitted; real profiles test fitting."""


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


@pytest.mark.parametrize("request_token", [None, "b" * 32])
def test_plan_is_no_write_and_builds_exact_sbatch_argv(
    tmp_path: Path, request_token: str | None
) -> None:
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
        request_token=request_token,
        sbatch="/opt/slurm/bin/sbatch",
        environment={
            "KEEP": "yes",
            "SBATCH_ACCOUNT": "ambient-account",
            "SBATCH_FAKE": "ambient-flag",
            slurm_submission.DELEGATE_MARKER_ENV: "ambient-marker",
            slurm_submission.PROFILE_SHA256_ENV: "b" * 64,
            slurm_submission.REQUEST_TOKEN_ENV: "ambient-token",
            "EMRYS_PRIVATE_SLURM_UNKNOWN": "ambient-private-value",
        },
        submitter_uid=1234,
    )

    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before
    stem = "emrys-local-pilot" + (f"-{request_token}" if request_token else "")
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
        f"--job-name={stem}",
        f"--output={log_dir}/{stem}-%j.out",
        f"--error={log_dir}/{stem}-%j.err",
        "--export="
        f"{slurm_submission.DELEGATE_MARKER_ENV}="
        f"{slurm_submission.DELEGATE_MARKER},"
        f"{slurm_submission.PROFILE_SHA256_ENV}={'a' * 64},"
        f"{slurm_submission.SUBMIT_UID_ENV}=1234,"
        + (
            f"{slurm_submission.REQUEST_TOKEN_ENV}={request_token},"
            if request_token is not None
            else ""
        )
        + "LOGNAME,USER,LNAME,USERNAME",
    )
    assert dict(plan.environment) == {"KEEP": "yes"}
    assert plan.stdout_pattern == log_dir / f"{stem}-%j.out"
    assert plan.stderr_pattern == log_dir / f"{stem}-%j.err"
    assert plan.job_name == stem
    assert plan.batch_script.startswith("#!/bin/bash\nset -euo pipefail\n")
    assert '/bin/rm -rf --one-file-system -- "$job_tmpdir"' in plan.batch_script
    assert "--wrap" not in plan.argv


@pytest.mark.parametrize(
    "context", ["direct", "legacy", "request", "orphan", "partial", "malformed", "uid"]
)
def test_optional_request_token_requires_admitted_private_delegate_context(
    monkeypatch: pytest.MonkeyPatch, context: str
) -> None:
    values = {
        slurm_submission.DELEGATE_MARKER_ENV: slurm_submission.DELEGATE_MARKER,
        slurm_submission.PROFILE_SHA256_ENV: "a" * 64,
        slurm_submission.SUBMIT_UID_ENV: str(os.getuid()),
        slurm_submission.REQUEST_TOKEN_ENV: "b" * 32,
    }
    for key in values:
        monkeypatch.delenv(key, raising=False)
    if context == "direct":
        values = {}
    elif context == "legacy":
        values.pop(slurm_submission.REQUEST_TOKEN_ENV)
    elif context == "orphan":
        values = {slurm_submission.REQUEST_TOKEN_ENV: "b" * 32}
    elif context == "partial":
        values.pop(slurm_submission.PROFILE_SHA256_ENV)
    elif context == "malformed":
        values[slurm_submission.REQUEST_TOKEN_ENV] = "B" * 32
    elif context == "uid":
        values[slurm_submission.SUBMIT_UID_ENV] = str(os.getuid() + 1)
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    if context in {"direct", "legacy", "request"}:
        assert slurm_submission.delegate_binding() == (
            None if context == "direct" else "a" * 64
        )
    else:
        with pytest.raises(slurm_submission.SlurmSubmissionError):
            slurm_submission.delegate_binding()


@pytest.mark.parametrize("token", ["", "a" * 31, "A" * 32, "../unsafe", True])
def test_submission_plan_refuses_noncanonical_request_token(
    tmp_path: Path, token: str
) -> None:
    with pytest.raises(slurm_submission.SlurmSubmissionError, match="request token"):
        slurm_submission.plan_submission(
            _profile(tmp_path),
            emrys_argv=("emrys", "run"),
            log_dir=tmp_path / "logs",
            request_token=token,
        )
    assert not (tmp_path / "logs").exists()


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


@pytest.mark.parametrize(
    "failure",
    (
        "invoke",
        "waited_invoke",
        "records",
        "recorded_invoke",
        "recorded_collision",
        "stderr_collision",
        "recorded_directory",
        "waited_directory",
    ),
)
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
    if failure in {"records", "recorded_collision"}:
        transcript.write_bytes(b"preserved submission\n")
    if failure == "stderr_collision":
        transcript.with_suffix(".stderr").write_bytes(b"preserved stderr\n")
    attempts = []
    real_popen = slurm_submission.subprocess.Popen

    def popen(*args, **kwargs):
        attempts.append(args)
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(slurm_submission.subprocess, "Popen", popen)
    if failure.endswith("directory"):

        def fail_sync(descriptor):
            assert stat.S_ISDIR(os.fstat(descriptor).st_mode)
            raise OSError("submission directory fsync failed")

        monkeypatch.setattr(slurm_submission.os, "fsync", fail_sync)
    operation = (
        "synchronize submission directory"
        if failure.endswith("directory")
        else "prepare submission records"
        if failure in {"records", "recorded_collision", "stderr_collision"}
        else "invoke sbatch"
    )
    with pytest.raises(
        slurm_submission.SlurmSubmissionError, match=f"Could not {operation}"
    ) as caught:
        slurm_submission.submit(
            plan,
            **{
                "record_path"
                if failure.startswith("recorded") or failure == "stderr_collision"
                else "wait_record": transcript
            },
        )
    assert "job ID unconfirmed" in str(caught.value)
    assert isinstance(caught.value.__cause__, OSError)
    assert ascii(str(caught.value.__cause__)) in str(caught.value)
    assert len(attempts) == (
        0
        if failure
        in {
            "records",
            "recorded_collision",
            "stderr_collision",
            "recorded_directory",
            "waited_directory",
        }
        else 1
    )
    if failure in {"records", "recorded_collision"}:
        assert transcript.read_bytes() == b"preserved submission\n"
    if failure == "stderr_collision":
        assert transcript.read_bytes() == b""
        assert transcript.with_suffix(".stderr").read_bytes() == b"preserved stderr\n"
    if failure.endswith("directory"):
        assert transcript.read_bytes() == b""
        assert transcript.with_suffix(".stderr").read_bytes() == b""


@pytest.mark.parametrize(
    "outcome",
    ("accepted", "failed", "rejected", "ambiguous", "invalid_bytes", "interrupted"),
)
def test_recorded_submission_retains_raw_responses_without_waiting_for_the_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    marker = tmp_path / "invocations"
    stdout = {
        "rejected": b"",
        "ambiguous": b"614999\n615000\n",
        "invalid_bytes": b"unparseable\xffpartial",
    }.get(outcome, b"614999;cluster\n")
    stderr = b"scheduler diagnostic\xff\n" + b"x" * 4096 + b"raw tail"
    scheduler = tmp_path / "sbatch"
    scheduler.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, sys, time\n"
        "assert '--wait' not in sys.argv\n"
        "assert sys.stdin.read().startswith('#!/bin/bash')\n"
        f"os.write(1, {stdout!r}); os.write(2, {stderr!r})\n"
        f"with pathlib.Path({str(marker)!r}).open('ab') as stream: stream.write(b'once\\n')\n"
        f"if {outcome == 'interrupted'}: time.sleep(10)\n"
        f"raise SystemExit({2 if outcome in {'failed', 'rejected'} else 0})\n"
    )
    scheduler.chmod(0o700)
    submission = slurm_submission.plan_submission(
        _profile(tmp_path),
        emrys_argv=("emrys", "run"),
        log_dir=tmp_path,
        sbatch=str(scheduler),
        environment={},
    )
    transcript = tmp_path / "sbatch.stdout"
    if outcome == "interrupted":
        real_wait = slurm_submission.subprocess.Popen.wait
        interrupted = False

        def interrupt_wait(process, *args, **kwargs):
            nonlocal interrupted
            if not interrupted:
                interrupted = True
                deadline = time.monotonic() + 3
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                assert marker.exists()
                raise KeyboardInterrupt
            return real_wait(process, *args, **kwargs)

        monkeypatch.setattr(slurm_submission.subprocess.Popen, "wait", interrupt_wait)
    if outcome == "accepted":
        assert slurm_submission.submit(submission, record_path=transcript) == "614999"
    else:
        error = (
            KeyboardInterrupt
            if outcome == "interrupted"
            else slurm_submission.SlurmSubmissionError
        )
        with pytest.raises(error) as caught:
            slurm_submission.submit(submission, record_path=transcript)
        if outcome != "interrupted":
            assert "raw tail" not in str(caught.value)
            assert "scheduler diagnostic" in str(caught.value)
            assert (
                "accepted job 614999" in str(caught.value)
                if outcome == "failed"
                else "unconfirmed" in str(caught.value)
            )
    assert marker.read_bytes() == b"once\n"
    assert transcript.read_bytes() == stdout
    assert transcript.with_suffix(".stderr").read_bytes() == stderr
    assert transcript.stat().st_mode & 0o777 == 0o600
    assert transcript.with_suffix(".stderr").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("accepted", (False, True))
@pytest.mark.parametrize("waited", (False, True))
def test_recorded_scheduler_early_stdin_close_preserves_rejection_and_job_identity(
    tmp_path: Path, accepted: bool, waited: bool
) -> None:
    scheduler = tmp_path / "sbatch"
    marker = tmp_path / "invocations"
    stdout = b"614999;fixture\n" if accepted else b""
    stderr = b"sbatch: invalid account\n"
    scheduler.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib\n"
        "os.close(0)\n"
        f"with pathlib.Path({str(marker)!r}).open('ab') as stream: stream.write(b'once\\n')\n"
        f"os.write(1, {stdout!r}); os.write(2, {stderr!r})\n"
        "raise SystemExit(23)\n"
    )
    scheduler.chmod(0o700)
    submission = replace(
        slurm_submission.plan_submission(
            _profile(tmp_path),
            emrys_argv=("emrys", "run"),
            log_dir=tmp_path,
            sbatch=str(scheduler),
            environment={},
        ),
        batch_script="#!/bin/bash\n" + "# padding\n" * 100_000,
    )
    transcript = tmp_path / "sbatch.stdout"
    received = []
    with pytest.raises(slurm_submission.SlurmSubmissionError) as caught:
        slurm_submission.submit(
            submission,
            **{"wait_record" if waited else "record_path": transcript},
            on_submitted=received.append,
        )
    assert "sbatch exited with 23" in str(caught.value)
    assert "invalid account" in str(caught.value)
    assert (
        "accepted job 614999" in str(caught.value)
        if accepted
        else "job ID unconfirmed" in str(caught.value)
    )
    assert received == (["614999"] if accepted else [])
    assert transcript.read_bytes() == stdout
    assert transcript.with_suffix(".stderr").read_bytes() == stderr
    assert marker.read_bytes() == b"once\n"


@pytest.mark.parametrize("username_variable", ("LOGNAME", "USER", "LNAME", "USERNAME"))
@pytest.mark.parametrize("request_token", [None, "b" * 32])
def test_batch_script_checks_identity_loads_modules_and_cleans_private_scratch(
    tmp_path: Path,
    username_variable: str,
    request_token: str | None,
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
        "'request_token': os.environ.get('EMRYS_PRIVATE_SLURM_REQUEST_TOKEN'), "
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
        request_token=request_token,
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
    assert observed["request_token"] == request_token
    assert observed["scratch"].startswith(str(profile.placement.scratch_parent) + "/")
    assert observed["scratch_mode"] == 0o700
    assert list(profile.placement.scratch_parent.iterdir()) == []


@pytest.mark.parametrize("observed_token", [None, "c" * 32, "module-mutation"])
def test_batch_rejects_missing_or_changed_request_before_modules_and_scratch(
    tmp_path: Path, observed_token: str | None
) -> None:
    capture = tmp_path / "must-not-run"
    module_capture = tmp_path / "must-not-load"
    module_init = tmp_path / "module-init.sh"
    module_init.write_text(
        (
            f"export {slurm_submission.REQUEST_TOKEN_ENV}={'c' * 32}\n"
            if observed_token == "module-mutation"
            else ""
        )
        + f"/usr/bin/touch {shlex.quote(str(module_capture))}\n"
    )
    profile = _profile(tmp_path, module_init=module_init)
    plan = slurm_submission.plan_submission(
        profile,
        emrys_argv=("/usr/bin/touch", str(capture)),
        log_dir=tmp_path / "logs",
        request_token="b" * 32,
    )
    environment = _batch_environment(plan)
    if observed_token is None:
        environment.pop(slurm_submission.REQUEST_TOKEN_ENV)
    elif observed_token != "module-mutation":
        environment[slurm_submission.REQUEST_TOKEN_ENV] = observed_token
    completed = subprocess.run(
        ("/bin/bash",),
        input=plan.batch_script,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert (
        "readonly variable"
        if observed_token == "module-mutation"
        else "submission request token differs from the frozen plan"
    ) in completed.stderr
    assert not capture.exists() and not module_capture.exists()
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
        "import os, pathlib, sys, time\n"
        "assert '--wait' in sys.argv\n"
        "assert sys.stdin.read().startswith('#!/bin/bash')\n"
        f"with pathlib.Path({str(submitted)!r}).open('ab') as handle: handle.write(b'submit\\n')\n"
        f"sys.stderr.buffer.write({detail!r}); sys.stderr.flush()\n"
        f"if {outcome == 'rejected'}: raise SystemExit(2)\n"
        "print('614999;fixture', flush=True)\n"
        f"while not pathlib.Path({str(release)!r}).exists(): time.sleep(0.01)\n"
        f"if {outcome in {'ambiguous', 'wait_failure'}}: print('extra output', flush=True)\n"
        f"if {outcome == 'success'}:\n"
        " os.close(1); time.sleep(0.05); os.write(2, b'late stderr after stdout closed')\n"
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
    synchronized_stderr_sizes = []
    real_fsync = slurm_submission.os.fsync

    def fsync(descriptor):
        state = os.fstat(descriptor)
        stderr_state = transcript.with_suffix(".stderr").stat()
        if (state.st_dev, state.st_ino) == (stderr_state.st_dev, stderr_state.st_ino):
            synchronized_stderr_sizes.append(state.st_size)
        real_fsync(descriptor)

    monkeypatch.setattr(slurm_submission.os, "fsync", fsync)
    if outcome == "record_failure":

        def fail_fsync(_descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(_descriptor).st_mode):
                real_fsync(_descriptor)
                return
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
    expected_stderr = detail + (
        b"late stderr after stdout closed" if outcome == "success" else b""
    )
    assert transcript.with_suffix(".stderr").read_bytes() == expected_stderr
    if outcome == "success":
        assert synchronized_stderr_sizes[-1] == len(expected_stderr)
    assert transcript.stat().st_mode & 0o777 == 0o600
    assert transcript.with_suffix(".stderr").stat().st_mode & 0o777 == 0o600
