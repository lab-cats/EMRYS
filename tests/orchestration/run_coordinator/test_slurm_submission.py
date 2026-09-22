"""Focused contracts for the private whole-Run Slurm transport."""

from __future__ import annotations

import json
import os
import shlex
import signal
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from emrys.orchestration.run_coordinator import slurm_submission


def _scheduler_replies(monkeypatch, scheduler, *replies):
    """Keep RPC inputs observable and responses independent of requested fields."""
    command = Mock(side_effect=replies)

    def reply(argv, timeout=10, environment=None):
        return command(argv, timeout=timeout, environment=environment)

    monkeypatch.setattr(scheduler, "command_bytes", reply)
    return command


def _root_row(**changes):
    fields = dict(
        JobIDRaw="700123",
        UID=str(os.getuid()),
        State="COMPLETED",
        Cluster="alpha",
        StdOut="/tmp/a%j.out",
        StdErr="/tmp/a%j.err",
        ExitCode="0:0",
    )
    fields.update(changes)
    return ("|".join(fields.values()) + "\n").encode()


def _observe_scheduler(monkeypatch, *replies, job="700123", cluster=None, **options):
    scheduler = slurm_submission.scheduler_observation
    command = _scheduler_replies(monkeypatch, scheduler, *replies)
    return scheduler.observe_job(
        job, "/tmp/a%j.out", "/tmp/a%j.err", cluster, **options
    ), command


def _file_snapshot(root: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _request_record(
    tmp_path: Path,
    token: str = "a",
    *,
    stdout: bytes = b"700123\n",
    stderr: bytes = b"",
    version: str = "v1",
    **context_overrides: object,
) -> tuple[Path, Path, dict[str, object]]:
    project = tmp_path / "project.yaml"
    project.touch(exist_ok=True)
    root = tmp_path / "logs" / ("submission-" + token * 32)
    root.mkdir(parents=True)
    name = (
        "emrys-" + token * 32
        if version == "v4"
        else "emrys-local-pilot" + ("-" + token * 32 if version != "v1" else "")
    )
    context = {
        "schema_version": f"emrys.submission-request.{version}",
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
        "scheduler_stdout_pattern": str(root.parent / f"{name}-%j.out"),
        "scheduler_stderr_pattern": str(root.parent / f"{name}-%j.err"),
    }
    if version in ("v3", "v4"):
        context["scheduler_job_name"] = name
    context.update(context_overrides)
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(context)
    )
    (root / "sbatch.stdout").write_bytes(stdout)
    (root / "sbatch.stderr").write_bytes(stderr)
    return project, root, context


def _stop_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    version: bytes = b"slurm 23.11.6\n",
    version_status: int = 0,
    stop_status: int = 0,
) -> SimpleNamespace:
    project, root, context = _request_record(
        tmp_path, stdout=b"700123;alpha\n", version="v3"
    )
    name = "emrys-local-pilot-" + "a" * 32
    client = tmp_path / "scancel"
    marker = tmp_path / "mutations"
    stdout, stderr = (
        b"reply\xff\n",
        b"controller diagnostic\xfe\n" + b"x" * 4096 + b"tail",
    )
    client.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        f" sys.stdout.buffer.write({version!r}); raise SystemExit({version_status})\n"
        f"with pathlib.Path({str(marker)!r}).open('ab') as stream:\n"
        " stream.write(json.dumps({'argv': sys.argv, 'env': dict(os.environ)}).encode()+b'\\n')\n"
        f"os.write(1, {stdout!r}); os.write(2, {stderr!r})\n"
        f"raise SystemExit({stop_status})\n"
    )
    client.chmod(0o700)
    monkeypatch.setattr(slurm_submission.shutil, "which", lambda _name: str(client))
    replies: list[str | None] = ["RUNNING", "RUNNING", "CANCELLED"]
    queries: list[tuple[str, ...]] = []

    def observe(argv: list[str], **_kwargs: object) -> bytes | None:
        queries.append(tuple(argv))
        state = replies.pop(0) if len(replies) > 1 else replies[0]
        if state is None:
            return None
        return (
            f"700123|{os.getuid()}|{state}|alpha|"
            f"{context['scheduler_stdout_pattern']}|{context['scheduler_stderr_pattern']}|None|{name}\n"
        ).encode()

    monkeypatch.setattr(
        slurm_submission.scheduler_observation, "command_bytes", observe
    )
    output = tmp_path / "stop-attempt" / "scancel.stdout"
    output.parent.mkdir()
    return SimpleNamespace(
        project=project,
        root=root,
        context=context,
        client=client,
        marker=marker,
        replies=replies,
        queries=queries,
        output=output,
        stdout=stdout,
        stderr=stderr,
    )


@pytest.mark.parametrize(
    "version,status,accepted",
    [
        (b"slurm 23.02.7\n", 0, False),
        (b"slurm 23.11.5\n", 0, False),
        (b"slurm 23.11.6\n", 0, True),
        (b"slurm 24.05.1\n", 0, True),
        (b"slurm-wlm 23.11.5\n", 0, False),
        (b"slurm-wlm 23.11.6\n", 0, True),
        (b"slurm-wlm 25.11.2\n", 0, True),
        (b"slurm 23.11.6\n", 1, False),
        (b"slurm 23.11.6-rc1\n", 0, False),
        (b"slurm 23.11.6\nextra\n", 0, False),
        (b"slurm 23.11\n", 0, False),
        (b"slurm-wlm 25.11.2-rc1\n", 0, False),
        (b"slurm-wlm 25.11.2\nextra\n", 0, False),
        (b"slurm-wlm-extra 25.11.2\n", 0, False),
        (b"\xff", 0, False),
    ],
)
def test_stop_preview_requires_supported_client_without_writing_or_mutating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: bytes,
    status: int,
    accepted: bool,
) -> None:
    fixture = _stop_fixture(
        tmp_path, monkeypatch, version=version, version_status=status
    )
    before = _file_snapshot(tmp_path)
    if accepted:
        plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
        assert plan.client_version == version.decode().strip()
        assert plan.argv == (
            str(fixture.client),
            "--ctld",
            "--clusters=alpha",
            f"--name={fixture.context['scheduler_job_name']}",
            "--me",
            "700123",
        )
    else:
        with pytest.raises(slurm_submission.SlurmSubmissionError, match=">=23.11.6"):
            slurm_submission.plan_stop(fixture.project, fixture.root.name)
    assert not fixture.marker.exists()
    assert _file_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "failure", ("missing", "permissions", "changed", "timeout", "symlink-loop")
)
def test_stop_client_admission_failure_never_invokes_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    if failure == "missing":
        monkeypatch.setattr(slurm_submission.shutil, "which", lambda _name: None)
    elif failure == "permissions":
        fixture.client.chmod(0o600)
    elif failure == "symlink-loop":
        fixture.client.unlink()
        fixture.client.symlink_to(fixture.client.name)
    else:
        run = slurm_submission.subprocess.run

        def version_probe(*args: object, **kwargs: object) -> object:
            assert args[0] == (str(fixture.client), "--version")
            if failure == "timeout":
                raise subprocess.TimeoutExpired(args[0], 10)
            result = run(*args, **kwargs)
            fixture.client.write_text(fixture.client.read_text() + "# replaced\n")
            return result

        monkeypatch.setattr(slurm_submission.subprocess, "run", version_probe)
    with pytest.raises(slurm_submission.SlurmSubmissionError):
        slurm_submission.plan_stop(fixture.project, fixture.root.name)
    assert not fixture.marker.exists() and not fixture.output.exists()


def test_already_terminal_stop_needs_no_client_and_retains_no_new_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    fixture.replies[:] = ["COMPLETED"]
    monkeypatch.setattr(
        slurm_submission.shutil,
        "which",
        lambda _name: pytest.fail("terminal stop looked up a client"),
    )
    monkeypatch.setattr(
        slurm_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("terminal stop invoked a client"),
    )
    plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
    assert plan.argv == () and plan.client_version is None
    result = slurm_submission.stop(
        plan, record_path=fixture.output, record_intent=lambda: None
    )
    assert not result.invocation_attempted and result.returncode is None
    assert result.observation["state"] == "COMPLETED"
    assert not fixture.output.exists() and not fixture.marker.exists()
    assert len(fixture.queries) == 2


@pytest.mark.parametrize(
    "defect",
    ("v1", "v2", "partial", "selector", "name", "uid", "cluster", "unavailable"),
)
def test_stop_refuses_unproven_request_identity_before_client_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    selector = fixture.root.name
    if defect == "partial":
        (fixture.root / "sbatch.stderr").unlink()
    elif defect == "selector":
        selector = "700123"
    elif defect in {"v1", "v2"}:
        fixture.context["schema_version"] = f"emrys.submission-request.{defect}"
        del fixture.context["scheduler_job_name"]
        if defect == "v1":
            for stream, extension in (("stdout", "out"), ("stderr", "err")):
                fixture.context[f"scheduler_{stream}_pattern"] = str(
                    tmp_path / "logs" / f"emrys-local-pilot-%j.{extension}"
                )
        (fixture.root / "request.json").write_bytes(
            slurm_submission.orchestration_contracts.canonical_json_bytes(
                fixture.context
            )
        )
    else:
        observed = slurm_submission.scheduler_observation.command_bytes

        def wrong_identity(*args: object, **kwargs: object) -> bytes | None:
            reply = observed(*args, **kwargs)
            if defect == "unavailable":
                return None
            assert reply is not None
            if defect == "name":
                return reply.replace(
                    fixture.context["scheduler_job_name"].encode(), b"other-job"
                )
            if defect == "uid":
                return reply.replace(
                    f"|{os.getuid()}|".encode(), f"|{os.getuid() + 1}|".encode()
                )
            return reply.replace(b"|alpha|", b"|other-cluster|")

        monkeypatch.setattr(
            slurm_submission.scheduler_observation, "command_bytes", wrong_identity
        )
    monkeypatch.setattr(
        slurm_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("inadmissible stop invoked client"),
    )
    with pytest.raises(slurm_submission.SlurmSubmissionError):
        slurm_submission.plan_stop(fixture.project, selector)
    assert not fixture.marker.exists() and not fixture.output.exists()


@pytest.mark.parametrize(
    "status,post_state", [(0, "CANCELLED"), (0, "RUNNING"), (0, None), (7, "RUNNING")]
)
def test_stop_retains_raw_diagnostics_and_observes_after_exact_single_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    post_state: str | None,
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch, stop_status=status)
    fixture.replies[:] = ["RUNNING", "RUNNING", post_state]
    monkeypatch.setenv("SCANCEL_SIGNAL", "KILL")
    monkeypatch.setenv("SCANCEL_USER", "another-user")
    monkeypatch.setenv("SLURM_CLUSTERS", "all")
    monkeypatch.setenv("USER", "not-the-owner")
    monkeypatch.setenv("SLURM_CONF", "/site/slurm.conf")
    plan = slurm_submission.plan_stop(fixture.project, str(fixture.root))
    result = slurm_submission.stop(
        plan, record_path=fixture.output, record_intent=lambda: None
    )
    assert result.invocation_attempted and result.returncode == status
    assert result.observation["state"] == (post_state or "UNKNOWN")
    assert result.observation["terminal"] == (post_state == "CANCELLED")
    assert result.diagnostic is None
    calls = fixture.marker.read_text().splitlines()
    assert len(calls) == 1
    call = json.loads(calls[0])
    assert call["argv"] == list(plan.argv)
    assert not any(
        key.startswith("SCANCEL_") or key == "SLURM_CLUSTERS" for key in call["env"]
    )
    assert call["env"]["SLURM_CONF"] == "/site/slurm.conf"
    assert len(fixture.queries) == 3
    assert all("--clusters=alpha" in query for query in fixture.queries)
    assert fixture.output.read_bytes() == fixture.stdout
    assert fixture.output.with_suffix(".stderr").read_bytes() == fixture.stderr
    assert (
        result.stdout_excerpt == fixture.stdout
        and result.stderr_excerpt == fixture.stderr[:4096]
    )
    assert stat.S_IMODE(fixture.output.stat().st_mode) == 0o600
    assert stat.S_IMODE(fixture.output.with_suffix(".stderr").stat().st_mode) == 0o600


@pytest.mark.parametrize("changed", ("request", "client", "scheduler", "terminal"))
def test_stop_readmission_prevents_changed_or_already_terminal_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed: str,
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
    if changed == "request":
        fixture.context["analysis"] = "different"
        (fixture.root / "request.json").write_bytes(
            slurm_submission.orchestration_contracts.canonical_json_bytes(
                fixture.context
            )
        )
    elif changed == "client":
        fixture.client.write_text(fixture.client.read_text() + "# changed\n")
    elif changed == "scheduler":
        fixture.replies[:] = [None]
    else:
        fixture.replies[:] = ["COMPLETED"]
    if changed == "terminal":
        result = slurm_submission.stop(
            plan, record_path=fixture.output, record_intent=lambda: None
        )
        assert not result.invocation_attempted and result.returncode is None
        assert result.observation["terminal"]
    else:
        with pytest.raises(slurm_submission.SlurmSubmissionError):
            slurm_submission.stop(
                plan, record_path=fixture.output, record_intent=lambda: None
            )
    assert not fixture.marker.exists()


@pytest.mark.parametrize(
    "failure", ("stdout", "stderr", "directory", "synchronize", "timeout", "interrupt")
)
def test_stop_record_and_transport_failure_preserves_evidence_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
    if failure in {"stdout", "stderr"}:
        path = (
            fixture.output
            if failure == "stdout"
            else fixture.output.with_suffix(".stderr")
        )
        path.write_bytes(b"preserve\n")
    elif failure in {"directory", "synchronize"}:
        synchronize = os.fsync

        def failed_sync(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode) == (failure == "directory"):
                raise OSError("record sync failed")
            synchronize(descriptor)

        monkeypatch.setattr(slurm_submission.os, "fsync", failed_sync)
    else:
        run = slurm_submission.subprocess.run

        def failed_run(*args: object, **kwargs: object) -> None:
            run(*args, **kwargs)
            if failure == "interrupt":
                raise KeyboardInterrupt("operator interrupted")
            raise subprocess.TimeoutExpired(plan.argv, 10)

        monkeypatch.setattr(slurm_submission.subprocess, "run", failed_run)
    if failure in {"stdout", "stderr", "directory", "interrupt"}:
        with pytest.raises(
            KeyboardInterrupt
            if failure == "interrupt"
            else slurm_submission.SlurmSubmissionError
        ):
            slurm_submission.stop(
                plan, record_path=fixture.output, record_intent=lambda: None
            )
    else:
        result = slurm_submission.stop(
            plan, record_path=fixture.output, record_intent=lambda: None
        )
        assert result.invocation_attempted and result.diagnostic
        assert result.observation["terminal"]
        assert result.returncode == (0 if failure == "synchronize" else None)
        assert result.stdout_excerpt == fixture.stdout
    attempted = failure in {"synchronize", "timeout", "interrupt"}
    assert fixture.marker.exists() == attempted
    assert len(fixture.queries) == (3 if failure in {"synchronize", "timeout"} else 2)
    if attempted:
        assert len(fixture.marker.read_text().splitlines()) == 1
        assert fixture.output.read_bytes() == fixture.stdout
        assert fixture.output.with_suffix(".stderr").read_bytes() == fixture.stderr
    if failure in {"stdout", "stderr"}:
        assert path.read_bytes() == b"preserve\n"


@pytest.mark.parametrize("transport", ("stop", "ordinary", "waited"))
@pytest.mark.parametrize("boundary", ("before-launch", "after-launch"))
def test_recorded_transport_pins_parent_across_real_directory_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, transport: str, boundary: str
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    retained = tmp_path / "retained-transcripts"
    replaced = False

    def replace_parent() -> None:
        nonlocal replaced
        if not replaced:
            replaced = True
            fixture.output.parent.rename(retained)
            fixture.output.parent.mkdir()

    if transport == "stop":
        plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
    else:
        fixture.client.write_text(
            f"#!{sys.executable}\n"
            "import os, pathlib, sys\n"
            "sys.stdin.read()\n"
            f"pathlib.Path({str(fixture.marker)!r}).write_text('once\\n')\n"
            "os.write(1, b'700123;alpha\\n'); os.write(2, b'retained stderr\\n')\n"
        )
        plan = slurm_submission.plan_submission(
            _profile(tmp_path),
            emrys_argv=("emrys", "doctor"),
            log_dir=tmp_path,
            sbatch=str(fixture.client),
        )
    if boundary == "before-launch":
        synchronize = os.fsync

        def sync_and_replace(descriptor: int) -> None:
            synchronize(descriptor)
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                replace_parent()

        monkeypatch.setattr(slurm_submission.os, "fsync", sync_and_replace)
    else:
        wait = slurm_submission.subprocess.Popen.wait

        def wait_and_replace(process: object, *args: object, **kwargs: object) -> int:
            status = wait(process, *args, **kwargs)
            replace_parent()
            return status

        monkeypatch.setattr(slurm_submission.subprocess.Popen, "wait", wait_and_replace)
    if transport == "stop" and boundary == "after-launch":
        result = slurm_submission.stop(
            plan, record_path=fixture.output, record_intent=lambda: None
        )
        assert result.invocation_attempted and result.diagnostic
    else:
        with pytest.raises(
            slurm_submission.SlurmSubmissionError, match="Transcript parent changed"
        ):
            if transport == "stop":
                slurm_submission.stop(
                    plan, record_path=fixture.output, record_intent=lambda: None
                )
            else:
                slurm_submission.submit(
                    plan,
                    record_path=fixture.output,
                    wait=transport == "waited",
                )
    assert replaced and not fixture.output.exists()
    assert fixture.marker.exists() == (boundary == "after-launch")
    assert (retained / fixture.output.name).read_bytes() == (
        b""
        if boundary == "before-launch"
        else fixture.stdout
        if transport == "stop"
        else b"700123;alpha\n"
    )


@pytest.mark.parametrize("change", ("intent-failure", "parent", "client"))
def test_stop_requires_intent_inside_pins_and_rechecks_before_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
    calls = []
    original = RuntimeError("required intent failed")

    def intent() -> None:
        calls.append("intent")
        assert (
            fixture.output.exists() and fixture.output.with_suffix(".stderr").exists()
        )
        if change == "intent-failure":
            raise original
        if change == "parent":
            fixture.output.parent.rename(tmp_path / "retained-attempt")
            fixture.output.parent.mkdir()
        else:
            fixture.client.write_text(
                fixture.client.read_text() + "# changed after intent\n"
            )

    with pytest.raises(RuntimeError) as caught:
        slurm_submission.stop(plan, record_path=fixture.output, record_intent=intent)
    if change == "intent-failure":
        assert caught.value is original
    else:
        assert isinstance(caught.value, slurm_submission.SlurmSubmissionError)
    assert calls == ["intent"] and len(fixture.queries) == 2
    assert not fixture.marker.exists()


def test_recorded_stop_refuses_replaced_file_before_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _stop_fixture(tmp_path, monkeypatch)
    plan = slurm_submission.plan_stop(fixture.project, fixture.root.name)
    synchronize = os.fsync

    def sync_and_replace(descriptor: int) -> None:
        synchronize(descriptor)
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            fixture.output.rename(fixture.output.with_suffix(".retained"))
            fixture.output.write_bytes(b"replacement\n")

    monkeypatch.setattr(slurm_submission.os, "fsync", sync_and_replace)
    with pytest.raises(
        slurm_submission.SlurmSubmissionError, match="Transcript file changed"
    ):
        slurm_submission.stop(
            plan, record_path=fixture.output, record_intent=lambda: None
        )
    assert not fixture.marker.exists()
    assert fixture.output.read_bytes() == b"replacement\n"
    assert fixture.output.with_suffix(".retained").read_bytes() == b""


def test_submission_requests_keep_all_retained_responses_without_scheduler_or_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, first, context = _request_record(
        tmp_path, stdout=b"700123;other-cluster\n", stderr=b"reason:\xff\n"
    )
    _, second, _ = _request_record(tmp_path, "b")
    before = _file_snapshot(tmp_path)
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
    assert _file_snapshot(tmp_path) == before


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
@pytest.mark.parametrize("version", ["v2", "v3", "v4"])
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
    if version != "v4":
        stem = "emrys-local-pilot-" + "a" * 32
        plan = replace(
            plan,
            stdout_pattern=project.parent / "logs" / f"{stem}-%j.out",
            stderr_pattern=project.parent / "logs" / f"{stem}-%j.err",
            job_name=stem,
        )
    context.update(
        scheduler_stdout_pattern=str(plan.stdout_pattern),
        scheduler_stderr_pattern=str(plan.stderr_pattern),
    )
    if version in ("v3", "v4"):
        context["scheduler_job_name"] = plan.job_name
        if version == "v4":
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
            + (f"|{plan.job_name}" if version in ("v3", "v4") else "")
            + "\n"
        ).encode(),
    )
    state = slurm_submission.observe_submission_request(observed)
    assert state["source"] == "squeue" and state["state"] == "RUNNING"
    assert state.get("job_name") == (plan.job_name if version in ("v3", "v4") else None)


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
@pytest.mark.parametrize("version", ("v3", "v4"))
def test_named_request_is_closed_and_bound_to_its_request_token(
    tmp_path: Path, defect: str, version: str
) -> None:
    project, root, context = _request_record(tmp_path, version=version)
    prefix = "emrys-local-pilot-" if version == "v3" else "emrys-"
    if defect == "missing":
        del context["scheduler_job_name"]
    elif defect == "extra":
        context["cancellable"] = True
    elif defect in ("v1", "v2"):
        context["schema_version"] = f"emrys.submission-request.{defect}"
    else:
        context["scheduler_job_name"] = {
            "wrong-token": prefix + "b" * 32,
            "legacy-name": "emrys-local-pilot"
            + ("-" + "a" * 32 if version == "v4" else ""),
            "empty": "",
            "wrong-type": [prefix + "a" * 32],
        }[defect]
    with pytest.raises(slurm_submission.SlurmSubmissionError):
        slurm_submission.validate_request_context(context, project, root)
    (root / "request.json").write_bytes(
        slurm_submission.orchestration_contracts.canonical_json_bytes(context)
    )
    (observed,) = slurm_submission.submission_requests(project)
    assert observed.context is None and observed.record_status == "malformed"


@pytest.mark.parametrize("include_resources", [False, True])
@pytest.mark.parametrize("record", ["legacy", "partial", "unconfirmed"])
def test_request_observation_requires_complete_unique_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record: str,
    include_resources: bool,
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
    observed = slurm_submission.observe_submission_request(
        request, include_resources=include_resources
    )
    assert observed["state"] == "UNKNOWN" and observed["diagnostic"]


@pytest.mark.parametrize(
    "defect", ["missing-root", "other-root", "legacy-paths", "mixed-token"]
)
def test_request_specific_streams_refuse_unbound_paths(
    tmp_path: Path, defect: str
) -> None:
    project, root, context = _request_record(tmp_path, version="v2")
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
    stem = f"emrys-{request_token}" if request_token else "emrys-doctor"
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
        "--signal=B:TERM@300",
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


@pytest.mark.parametrize(
    "failure",
    (
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
    transcript = tmp_path / "submission.stdout"
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
            record_path=transcript,
            wait=failure.startswith("waited") or failure == "records",
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
    "outcome,stdout,returncode",
    (
        ("accepted", b"614999;cluster\n", 0),
        ("failed", b"614999;cluster\n", 1),
        ("rejected", b"", 2),
        ("ambiguous", b"614999\n615000\n", 0),
        ("invalid_bytes", b"unparseable\xffpartial", 0),
        ("interrupted", b"614999;cluster\n", 0),
        ("empty_success", b"", 0),
        ("extra_fields", b"123;cluster;extra\n", 0),
        ("nonnumeric", b"not-a-job\n", 0),
        ("zero", b"0\n", 0),
        ("leading_zero", b"00\n", 0),
        ("unicode_digits", "１２３\n".encode(), 0),
        ("escaped_malformed", b"invalid\x1b[31m\n", 1),
    ),
)
def test_recorded_submission_retains_raw_responses_without_waiting_for_the_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
    stdout: bytes,
    returncode: int,
) -> None:
    marker = tmp_path / "invocations"
    stderr = b'scheduler diagnostic: "memory"\xff\n\x1b[31m' + b"x" * 4096 + b"raw tail"
    scheduler = tmp_path / "sbatch"
    submission = slurm_submission.plan_submission(
        _profile(tmp_path),
        emrys_argv=("emrys", "run"),
        log_dir=tmp_path,
        sbatch=str(scheduler),
        environment={"KEEP": "yes", "SBATCH_FAKE": "discard"},
    )
    scheduler.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, sys, time\n"
        "assert '--wait' not in sys.argv\n"
        f"assert sys.stdin.read() == {submission.batch_script!r}\n"
        f"os.write(1, {stdout!r}); os.write(2, {stderr!r})\n"
        f"with pathlib.Path({str(marker)!r}).open('ab') as stream: stream.write(b'once\\n')\n"
        f"if {outcome == 'interrupted'}: time.sleep(10)\n"
        f"raise SystemExit({returncode})\n"
    )
    scheduler.chmod(0o700)
    popen = slurm_submission.subprocess.Popen

    def checked_popen(argv, **kwargs):
        assert argv == submission.argv
        assert kwargs["env"] == {"KEEP": "yes"}
        return popen(argv, **kwargs)

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
    monkeypatch.setattr(slurm_submission.subprocess, "Popen", checked_popen)
    if outcome == "accepted":
        assert (
            slurm_submission.submit(
                submission, record_path=transcript, show_details=False
            )
            == "614999"
        )
        assert "Slurm submission records:" not in capsys.readouterr().err
    else:
        error = (
            KeyboardInterrupt
            if outcome == "interrupted"
            else slurm_submission.SlurmSubmissionError
        )
        with pytest.raises(error) as caught:
            slurm_submission.submit(submission, record_path=transcript)
        if outcome != "interrupted":
            diagnostic = str(caught.value)
            assert "\x1b" not in diagnostic and "\n" not in diagnostic
            assert "raw tail" not in diagnostic
            assert ascii(stderr[:4096].decode("utf-8", "replace")) in diagnostic
            assert (
                "accepted job 614999" in diagnostic
                if outcome == "failed"
                else "unconfirmed" in diagnostic
            )
            if outcome in {"failed", "rejected"}:
                assert f"sbatch exited with {returncode}" in diagnostic
                assert "cancelled" not in diagnostic
            else:
                assert "Invalid sbatch response" in diagnostic
            if outcome == "failed":
                for pattern in (submission.stdout_pattern, submission.stderr_pattern):
                    assert str(pattern).replace("%j", "614999") in diagnostic
    assert marker.read_bytes() == b"once\n"
    assert transcript.read_bytes() == stdout
    assert transcript.with_suffix(".stderr").read_bytes() == stderr
    assert transcript.stat().st_mode & 0o777 == 0o600
    assert transcript.with_suffix(".stderr").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("version", ["v2", "v3", "v4"])
@pytest.mark.parametrize(
    ("cluster", "local_cluster"),
    [(None, "alpha"), ("alpha", "alpha"), ("alpha", "beta")],
)
@pytest.mark.parametrize("state", ["PENDING", "RUNNING", "COMPLETED", "CANCELLED"])
def test_request_resources_respect_supported_cluster_scope(
    tmp_path, monkeypatch, version, cluster, local_cluster, state
):
    project, _root, context = _request_record(
        tmp_path,
        stdout=b"700123\n" if cluster is None else b"700123;alpha\n",
        version=version,
    )
    (request,) = slurm_submission.submission_requests(project)
    fields = dict(
        State=state,
        StdOut=context["scheduler_stdout_pattern"],
        StdErr=context["scheduler_stderr_pattern"],
        ExitCode="0:0" if state == "COMPLETED" else "Priority",
    )
    if version in ("v3", "v4"):
        fields["JobName"] = (
            "emrys-local-pilot-" if version == "v3" else "emrys-"
        ) + "a" * 32
    resources = dict(
        Elapsed="00:01:00",
        Timelimit="01:00:00",
        AllocCPUS="4",
        Partition="compute",
        NodeList="node[1-2]",
    )

    def reply(argv, timeout=10, environment=None):
        assert timeout == 10 and "SLURM_CLUSTERS" not in environment
        selected = next(
            (
                arg.removeprefix("--clusters=")
                for arg in argv
                if arg.startswith("--clusters=")
            ),
            local_cluster,
        )
        if argv[0] == "sstat":
            assert local_cluster == "alpha"
            return b"700123.batch|00:00:02|1024K|8M|0\n"
        if argv[0] == "squeue" and state == "COMPLETED":
            return b""
        if "700123.batch" in argv:
            return (
                f"700123.batch|{os.getuid()}|{selected}|00:00:02|1024K|8M|0\n"
            ).encode()
        detailed = "TimeUsed:0" in argv[-1] or ",Elapsed,Timelimit" in argv[-1]
        return _root_row(**fields, Cluster=selected, **(resources if detailed else {}))

    monkeypatch.setenv("SLURM_CLUSTERS", "other")
    command = Mock(side_effect=reply)
    monkeypatch.setattr(
        slurm_submission.scheduler_observation, "command_bytes", command
    )
    result = slurm_submission.observe_submission_request(
        request, include_resources=True
    )
    calls = [call.args[0] for call in command.call_args_list]
    source = "sacct" if state == "COMPLETED" else "squeue"
    initial = calls[1 if state == "COMPLETED" else 0]
    assert initial[1] == ("--local" if cluster is None else "--clusters=alpha")
    assert initial[-1].endswith(
        ",Elapsed,Timelimit,AllocCPUS,Partition,NodeList"
        if source == "sacct"
        else "|,TimeUsed:0|,TimeLeft:0|,NumCPUs:0|,Partition:0|,NodeList:0"
    )
    if source == "sacct":
        assert "--duplicates" in initial and "-X" in initial
    assert result["state"] == state
    assert result["terminal"] is (state in {"COMPLETED", "CANCELLED"})
    assert result["cluster"] == "alpha"
    assert [result[key] for key in ("elapsed", "cpus", "partition", "node")] == [
        "00:01:00",
        "4",
        "compute",
        "node[1-2]",
    ]
    assert result["time_limit" if state == "COMPLETED" else "left"] == "01:00:00"
    if state == "COMPLETED" or (state == "RUNNING" and local_cluster == "alpha"):
        expected = (
            ["squeue", "squeue", "sstat", "squeue"]
            if state == "RUNNING"
            else ["squeue", "sacct", "squeue", "sacct", "sacct", "squeue", "sacct"]
        )
        assert [call[0] for call in calls] == expected
        usage = calls[2 if state == "RUNNING" else 4]
        assert usage == (
            [
                "sstat",
                "-n",
                "-P",
                "-j",
                "700123.batch",
                "--format=JobID,AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite",
            ]
            if state == "RUNNING"
            else [
                "sacct",
                "--clusters=alpha",
                "--duplicates",
                "-n",
                "-P",
                "-j",
                "700123.batch",
                "--format=JobIDRaw,UID,Cluster,AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite",
            ]
        )
        assert result["usage_diagnostic"] is None and result[
            "usage_observed_at"
        ].endswith("+00:00")
        assert [
            result[key] for key in ("ave_cpu", "max_rss", "disk_read", "disk_write")
        ] == ["00:00:02", "1024K", "8M", "0"]
    else:
        assert [call[0] for call in calls] == (
            ["squeue", "squeue"] if state == "RUNNING" else ["squeue"]
        )
        assert "ave_cpu" not in result and result["usage_diagnostic"]
    if state == "COMPLETED":
        assert "left" not in result
        assert all("--clusters=alpha" in call for call in calls[2:])


@pytest.mark.parametrize("boundary", ["initial", "before-usage", "after-usage"])
@pytest.mark.parametrize("defect", ["id", "uid", "name", "stdout", "stderr", "cluster"])
def test_request_resource_usage_rejects_identity_drift_without_erasing_root(
    monkeypatch, boundary, defect
):
    name = "emrys-local-pilot-" + "a" * 32
    fields = dict(State="RUNNING", ExitCode="None", JobName=name)
    resources = dict(
        Elapsed="00:01",
        Timelimit="01:00",
        AllocCPUS="4",
        Partition="compute",
        NodeList="node",
    )
    rows = [_root_row(**fields, **resources), _root_row(**fields), _root_row(**fields)]
    selected = {"initial": 0, "before-usage": 1, "after-usage": 2}[boundary]
    changes = {
        "id": {"JobIDRaw": "700124"},
        "uid": {"UID": str(os.getuid() + 1)},
        "name": {"JobName": name + "x"},
        "stdout": {"StdOut": "/tmp/b%j.out"},
        "stderr": {"StdErr": "/tmp/b%j.err"},
        "cluster": {"Cluster": "beta"},
    }[defect]
    rows[selected] = _root_row(
        **(fields | changes | (resources if selected == 0 else {}))
    )
    initial, before, after = rows
    result, command = _observe_scheduler(
        monkeypatch,
        initial,
        before,
        b"700123.batch|00:00:02|1024K|8M|0\n",
        after,
        cluster="alpha",
        job_name=name,
        include_resources=True,
    )
    calls = [call.args[0][0] for call in command.call_args_list]
    if boundary == "initial":
        assert result["state"] == "UNKNOWN" and calls == ["squeue"]
        assert "elapsed" not in result
    else:
        assert result["state"] == "RUNNING" and result["elapsed"] == "00:01"
        assert result["usage_diagnostic"] and "usage_observed_at" not in result
        assert calls == (
            ["squeue", "squeue"]
            if boundary == "before-usage"
            else ["squeue", "squeue", "sstat", "squeue"]
        )
    assert "max_rss" not in result


@pytest.mark.parametrize(
    "reply",
    [
        None,
        b"",
        b"700124.batch|00:00|1K|0|0\n",
        b"700123.0|00:00|1K|0|0\n",
        b"700123.batch|00:00|1K|0\n",
        b"700123.batch|00:00|1K|0|0|\n",
        b"700123.batch|00:00|1K|0|0\n700123.batch|00:00|1K|0|0\n",
        b"x" * 65537,
        b"700123.batch|\xff|1K|0|0\n",
        b"700123.batch|00:00|\x1b[31m1K|0|0\n",
        b"700123.batch|00:00|1.2.3M|0|0\n",
        b"700123.batch|not-a-time|1K|0|0\n",
    ],
)
def test_request_resource_usage_faults_preserve_exact_root_observation(
    monkeypatch, reply
):
    root = f"700123|{os.getuid()}|RUNNING|alpha|/tmp/a%j.out|/tmp/a%j.err|None"
    result, command = _observe_scheduler(
        monkeypatch,
        (root + "|00:01|01:00|4|compute|node\n").encode(),
        (root + "\n").encode(),
        reply,
        include_resources=True,
    )
    assert result["state"] == "RUNNING" and result["cpus"] == "4"
    assert result["usage_diagnostic"] and "max_rss" not in result
    assert [call.args[0][0] for call in command.call_args_list] == [
        "squeue",
        "squeue",
        "sstat",
    ]


@pytest.mark.parametrize(
    ("defect", "batch"),
    [
        ("unavailable", None),
        ("duplicate", "{row}{row}"),
        ("id", "700124.batch|{uid}|alpha|00:00|1K|0|0\n"),
        ("uid", "700123.batch|{wrong_uid}|alpha|00:00|1K|0|0\n"),
        ("cluster", "700123.batch|{uid}|beta|00:00|1K|0|0\n"),
        ("incomplete", "700123.batch|{uid}|alpha|00:00|1K|0\n"),
        ("metric", "700123.batch|{uid}|alpha|bad|1K|0|0\n"),
    ],
)
def test_terminal_batch_usage_faults_preserve_exact_root(monkeypatch, defect, batch):
    root = _root_row(State="COMPLETED", ExitCode="0:0")
    detailed = _root_row(
        State="COMPLETED",
        ExitCode="0:0",
        Elapsed="00:01",
        Timelimit="01:00",
        AllocCPUS="4",
        Partition="compute",
        NodeList="node",
    )
    row = f"700123.batch|{os.getuid()}|alpha|00:00|1K|0|0\n"
    reply = (
        None
        if batch is None
        else batch.format(row=row, uid=os.getuid(), wrong_uid=os.getuid() + 1).encode()
    )
    result, command = _observe_scheduler(
        monkeypatch, b"", detailed, b"", root, reply, include_resources=True
    )
    assert defect and result["state"] == "COMPLETED" and result["cpus"] == "4"
    assert result["usage_diagnostic"] and "max_rss" not in result
    assert [call.args[0][0] for call in command.call_args_list] == [
        "squeue",
        "sacct",
        "squeue",
        "sacct",
        "sacct",
    ]


def test_request_resource_dates_precede_followup_identity_queries(monkeypatch) -> None:
    scheduler = slurm_submission.scheduler_observation
    events = []
    dates = []

    def now(_timezone):
        value = f"2026-09-15T12:00:0{len(dates)}+00:00"
        dates.append(value)
        events.append("date")
        return SimpleNamespace(isoformat=lambda: value)

    def command(argv, timeout=10, environment=None):
        events.append(argv[0])
        if argv[0] == "sstat":
            return b"700123.batch|00:00:02|1024K|8M|0\n"
        fields = f"700123|{os.getuid()}|RUNNING|alpha|/tmp/a%j.out|/tmp/a%j.err|None"
        if "TimeUsed:0" in argv[-1]:
            fields += "|00:01|01:00|4|compute|node"
        return (fields + "\n").encode()

    monkeypatch.setattr(scheduler, "command_bytes", command)
    monkeypatch.setattr(scheduler, "datetime", SimpleNamespace(now=now))
    result = scheduler.observe_job(
        "700123", "/tmp/a%j.out", "/tmp/a%j.err", "alpha", include_resources=True
    )
    assert events == ["squeue", "date", "squeue", "sstat", "date", "squeue"]
    assert result["observed_at"] == dates[0]
    assert result["usage_observed_at"] == dates[1]


def _timing_accounting_row(**changes):
    fields = dict(
        JobName="emrys-local-pilot",
        Submit="2026-09-15T12:00:00Z",
        Eligible="2026-09-15T12:01:00Z",
        Start="2026-09-15T12:03:00Z",
        End="2026-09-15T12:05:00Z",
        ElapsedRaw="120",
        Restarts="0",
        Suspended="00:00:00",
    )
    fields.update(changes)
    return _root_row(**fields)


@pytest.mark.parametrize("cluster", [None, "alpha"])
@pytest.mark.parametrize("resources", [False, True])
@pytest.mark.parametrize("state", ["COMPLETED", "FAILED", "CANCELLED by 123"])
def test_accounting_timing_is_one_exact_utc_observation(
    monkeypatch, cluster, resources, state
):
    monkeypatch.setenv("TZ", "America/New_York")
    monkeypatch.setenv("SLURM_TIME_FORMAT", "relative")
    monkeypatch.setenv("SLURM_CLUSTERS", "other")
    monkeypatch.setenv("SACCT_FORMAT", "JobID")
    reply = _timing_accounting_row(State=state)
    if resources:
        reply = reply.replace(
            b"|2026-09-15T12:00:00Z",
            b"|00:02:00|01:00:00|2|compute|node|2026-09-15T12:00:00Z",
        )
    result, command = _observe_scheduler(
        monkeypatch,
        reply,
        *([None] if resources else []),
        cluster=cluster,
        job_name="emrys-local-pilot",
        include_timing=True,
        include_resources=resources,
    )
    initial = command.call_args_list[0]
    argv, environment = initial.args[0], initial.kwargs["environment"]
    assert argv[:8] == [
        "sacct",
        "--local" if cluster is None else "--clusters=alpha",
        "--duplicates",
        "-X",
        "-n",
        "-P",
        "-j",
        "700123",
    ]
    assert initial.kwargs["timeout"] == 10
    assert (
        environment["TZ"] == "UTC0"
        and environment["SLURM_TIME_FORMAT"] == "%Y-%m-%dT%H:%M:%SZ"
    )
    assert "SLURM_CLUSTERS" not in environment and "SACCT_FORMAT" not in environment
    if resources:
        assert ",Elapsed,Timelimit,AllocCPUS,Partition,NodeList," in argv[-1]
    assert argv[-1].endswith(",Submit,Eligible,Start,End,ElapsedRaw,Restarts,Suspended")
    assert (
        command.call_count == 1 + resources
        and result["terminal"]
        and result["source"] == "sacct"
    )
    assert result["state"] == state.split(" by ")[0]
    assert result["timing_observed_at"].endswith("+00:00")
    assert result["timing"] == {
        "submit_utc": "2026-09-15T12:00:00Z",
        "eligible_utc": "2026-09-15T12:01:00Z",
        "start_utc": "2026-09-15T12:03:00Z",
        "end_utc": "2026-09-15T12:05:00Z",
        "elapsed_seconds": 120,
        "restarts": 0,
        "suspended_seconds": 0,
        "submission_to_start_seconds": 180,
        "eligible_to_start_seconds": 120,
        "allocation_wall_seconds": 120,
        "diagnostic": None,
    }
    assert os.environ["TZ"] == "America/New_York"
    assert os.environ["SLURM_TIME_FORMAT"] == "relative"


@pytest.mark.parametrize(
    "changes",
    [
        {"Submit": "Unknown"},
        {"Eligible": "None"},
        {"Start": ""},
        {"End": "Unknown"},
        {"Eligible": "2026-09-15T12:04:00Z"},
        {"Submit": "2026-09-15T12:02:00Z"},
        {"End": "2026-09-15T12:01:00Z"},
        {"Start": "2026-02-30T12:03:00Z"},
        {"Submit": "2026-09-15T12:00:00+02:00"},
        {"ElapsedRaw": "119"},
        {"ElapsedRaw": "-1"},
        {"ElapsedRaw": "9" * 100},
        {"Restarts": "Unknown"},
        {"Restarts": "1"},
        {"Suspended": "00:00:30", "ElapsedRaw": "90"},
        {"Suspended": "1-01:00:00"},
        {"Suspended": "Unknown"},
        {"Suspended": "24:00:00"},
        {"Suspended": "00:60:00"},
    ],
)
def test_uncertain_accounting_timing_preserves_root_and_raw_dates_not_intervals(
    monkeypatch, changes
):
    result, command = _observe_scheduler(
        monkeypatch,
        _timing_accounting_row(**changes),
        cluster="alpha",
        job_name="emrys-local-pilot",
        include_timing=True,
    )
    assert command.call_count == 1 and result["source"] == "sacct"
    assert result["state"] == changes.get("State", "COMPLETED")
    timing = result["timing"]
    assert timing["diagnostic"] and result["diagnostic"] is None
    assert "submission_to_start_seconds" not in timing
    assert "eligible_to_start_seconds" not in timing
    assert "allocation_wall_seconds" not in timing
    if "Submit" not in changes:
        assert timing["submit_utc"] == "2026-09-15T12:00:00Z"
    if changes.get("Suspended") == "00:00:30":
        assert timing["suspended_seconds"] == 30 and timing["elapsed_seconds"] == 90
    if changes.get("Restarts") == "1":
        assert timing["restarts"] == 1 and "Requeued" in timing["diagnostic"]


@pytest.mark.parametrize(
    "defect",
    [
        "id",
        "uid",
        "name",
        "stdout",
        "stderr",
        "cluster",
        "array",
        "step",
        "duplicate",
        "empty",
        "missing",
        "oversized",
        "truncated",
        "unicode",
        "running",
        "suspended",
        "requeued",
    ],
)
def test_accounting_timing_cannot_bypass_exact_root_identity(monkeypatch, defect):
    changes = {
        "id": {"JobIDRaw": "700124"},
        "uid": {"UID": str(os.getuid() + 1)},
        "name": {"JobName": "other"},
        "stdout": {"StdOut": "/tmp/other%j.out"},
        "stderr": {"StdErr": "/tmp/other%j.err"},
        "cluster": {"Cluster": "other"},
        "array": {"JobIDRaw": "700123_1"},
        "step": {"JobIDRaw": "700123.batch"},
        "running": {"State": "RUNNING"},
        "suspended": {"State": "SUSPENDED"},
        "requeued": {"State": "REQUEUED"},
    }
    reply = _timing_accounting_row(**changes.get(defect, {}))
    reply = {
        "duplicate": reply + reply,
        "empty": b"",
        "missing": None,
        "oversized": b"x" * 65537,
        "truncated": reply.rsplit(b"|", 1)[0],
        "unicode": b"\xff",
    }.get(defect, reply)
    result, command = _observe_scheduler(
        monkeypatch,
        reply,
        cluster="alpha",
        job_name="emrys-local-pilot",
        include_timing=True,
    )
    assert command.call_count == 1 and result["state"] == "UNKNOWN"
    assert "timing" not in result and result["diagnostic"]


@pytest.mark.parametrize(
    "job,cluster", [("0", None), ("700123", "all"), ("700123", "a,b")]
)
def test_accounting_timing_refuses_nonexact_request_without_rpc(
    monkeypatch, job, cluster
):
    result, command = _observe_scheduler(
        monkeypatch, job=job, cluster=cluster, include_timing=True
    )
    command.assert_not_called()
    assert result["state"] == "UNKNOWN" and "timing" not in result


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
            record_path=transcript,
            wait=waited,
            on_submitted=lambda job_id, cluster: received.append((job_id, cluster)),
        )
    assert "sbatch exited with 23" in str(caught.value)
    assert "invalid account" in str(caught.value)
    assert (
        "accepted job 614999" in str(caught.value)
        if accepted
        else "job ID unconfirmed" in str(caught.value)
    )
    assert received == ([("614999", "fixture")] if accepted else [])
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


def test_batch_walltime_warning_forwards_once_and_waits_for_owned_command(
    tmp_path: Path,
) -> None:
    ready = tmp_path / "ready"
    interrupted = tmp_path / "interrupted"
    child_code = (
        "import os,pathlib,signal,sys,time; "
        "ready=pathlib.Path(sys.argv[1]); interrupted=pathlib.Path(sys.argv[2]); "
        "signal.signal(signal.SIGTERM, lambda *_: "
        "(interrupted.write_text('TERM\\n'), sys.exit(23))); "
        "ready.write_text(str(os.getpid())); "
        "time.sleep(60)"
    )
    profile = _profile(tmp_path)
    plan = slurm_submission.plan_submission(
        profile,
        emrys_argv=(
            sys.executable,
            "-c",
            child_code,
            str(ready),
            str(interrupted),
        ),
        log_dir=tmp_path / "logs",
    )
    process = subprocess.Popen(
        ("/bin/bash",),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_batch_environment(plan),
    )
    assert process.stdin is not None
    process.stdin.write(plan.batch_script)
    process.stdin.close()
    deadline = time.monotonic() + 5
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready.exists()
    assert int(ready.read_text()) != process.pid
    os.kill(process.pid, signal.SIGTERM)
    assert process.wait(timeout=10) == 23
    assert interrupted.read_text() == "TERM\n"
    assert list(profile.placement.scratch_parent.iterdir()) == []


def _batch_startup_child(destination: str) -> None:
    """Observe simulated allocation metadata, then start the actual local backend."""
    from dataclasses import asdict

    from emrys.evidence.runtime_availability import _probes, inspector
    from emrys.libraries.source_authority import controlled_python_argv
    from emrys.orchestration.run_coordinator import capacity

    allocation = capacity.observe_allocation()
    check = replace(
        next(
            item
            for item in inspector.load_runtime_policy()
            if item.check_id == "snakemake"
        ),
        target=sys.executable,
        probe_args=tuple(
            controlled_python_argv(sys.executable, "-m", "snakemake", "--version")[1:]
        ),
    )
    commands = []
    scratch_paths = []

    def run(argv, stdin, environment, timeout):
        module_index = argv.index("-m")
        assert argv[module_index + 1] == "snakemake"
        if "--directory" in argv:
            scratch_paths.append(Path(argv[argv.index("--directory") + 1]))
        # Preserve the real probe's interpreter/options/environment; only NSS
        # lookup is unavailable, as in the separate runtime startup oracle.
        injected = [
            *argv[:module_index],
            "-c",
            "from unittest.mock import patch\n"
            "with patch('pwd.getpwuid', side_effect=KeyError('uid unavailable')):\n"
            " from snakemake.cli import main\n"
            " main()\n",
            *argv[module_index + 2 :],
        ]
        outcome = _probes._run_command(injected, stdin, environment, timeout)
        commands.append({"argv": argv, "code": outcome[0], "output": outcome[1]})
        return outcome

    observed = _probes.run_checks(
        [check], environment=dict(os.environ), command_runner=run
    )[0]
    Path(destination).write_text(
        json.dumps(
            {
                "allocation": asdict(allocation),
                "status": observed.status,
                "observed": observed.observed,
                "detail": observed.detail,
                "commands": commands,
                "username": os.environ.get("USER"),
                "memory_variables": {
                    key: value
                    for key, value in os.environ.items()
                    if key.startswith("SLURM_MEM_")
                },
                "scratch": os.environ["TMPDIR"],
                "startup_directories": [str(path) for path in scratch_paths],
                "startup_cleaned": all(not path.exists() for path in scratch_paths),
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("forward_username", [True, False])
def test_simulated_batch_environment_starts_real_snakemake_without_passwd_or_memory_vars(
    tmp_path: Path, forward_username: bool
) -> None:
    profile = _profile(tmp_path, memory_mb=None)
    capture = tmp_path / "startup.json"
    plan = slurm_submission.plan_submission(
        profile,  # type: ignore[arg-type]
        emrys_argv=(
            sys.executable,
            "-B",
            "-I",
            "-c",
            "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
            "runpy.run_path(sys.argv[2])['_batch_startup_child'](sys.argv[3])",
            str(Path(slurm_submission.__file__).resolve().parents[3]),
            str(Path(__file__).resolve()),
            str(capture),
        ),
        log_dir=tmp_path / "logs",
        environment={
            **({"USER": "emrys-batch-user"} if forward_username else {}),
            "SLURM_MEM_PER_NODE": "32768",
            "SLURM_MEM_PER_CPU": "4096",
        },
    )
    assert not any(item.startswith("--mem") for item in plan.argv)
    environment = {**_batch_environment(plan), "SLURM_CPUS_PER_TASK": "1"}
    assert not any(key.startswith("SLURM_MEM_") for key in environment)

    completed = subprocess.run(
        ("/bin/bash",),
        input=plan.batch_script,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )

    assert completed.returncode == 0, completed.stderr
    observed = json.loads(capture.read_text(encoding="utf-8"))
    allocation = observed["allocation"]
    assert allocation["slurm_job_id"] == "700123"
    assert allocation["cores"] == 1 and allocation["memory_mb"] > 0
    assert (
        "process-visible memory; Slurm memory limit unspecified" in allocation["source"]
    )
    assert observed["memory_variables"] == {}
    version, startup = observed["commands"]
    assert version["argv"][-1] == "--version" and version["code"] == 0
    assert version["output"] == "9.25.1"
    assert "--snakefile" in startup["argv"] and os.devnull in startup["argv"]
    assert startup["argv"][startup["argv"].index("--executor") + 1] == "local"
    assert observed["startup_cleaned"] and len(observed["startup_directories"]) == 1
    assert Path(observed["startup_directories"][0]).parent == Path(observed["scratch"])
    assert list(profile.placement.scratch_parent.iterdir()) == []
    assert not (tmp_path / "logs").exists()
    if forward_username:
        assert observed["username"] == "emrys-batch-user"
        assert observed["status"] == "pass" and startup["code"] == 0
        assert "Nothing to be done" in startup["output"]
        assert "user: emrys-batch-user" in startup["output"].lower()
        assert "minimal local Snakemake startup passed" in observed["detail"]
    else:
        assert observed["username"] is None
        assert observed["status"] == "fail" and startup["code"] == 1
        assert "No username set in the environment" in observed["observed"]
        assert "Snakemake startup failed; exit_status=1" in observed["detail"]


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
    received: list[tuple[str, str | None]] = []
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

    def announce(job_id: str, cluster: str | None) -> None:
        received.append((job_id, cluster))
        assert transcript.read_text() == "614999;fixture\n"
        assert "Slurm job 614999" in capsys.readouterr().err
        if outcome == "interrupted":
            raise KeyboardInterrupt
        release.touch()

    if outcome == "success":
        assert (
            slurm_submission.submit(
                submission, record_path=transcript, wait=True, on_submitted=announce
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
                submission, record_path=transcript, wait=True, on_submitted=announce
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
    assert received == (
        [] if outcome in {"rejected", "record_failure"} else [("614999", "fixture")]
    )
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
