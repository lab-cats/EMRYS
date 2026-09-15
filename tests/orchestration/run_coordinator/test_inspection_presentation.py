"""Read-only watch cadence, exact selection, diagnostic tails and dated evidence."""

from __future__ import annotations

import fcntl
import importlib.util
import os
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from emrys.orchestration.run_coordinator import _inspection_presentation as view
from emrys.orchestration.run_coordinator import _submission_inspection as association
from emrys.orchestration.run_coordinator import slurm_submission


NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


def _run(root):
    task = SimpleNamespace(
        expected=SimpleNamespace(
            step_id="00a", machine_key="fixture.owner", scope_id="reference"
        ),
        state="pending",
        start_origin="workflow-later",
        start_reference={"path": "start.json"},
        terminal_attempts=(),
    )
    return SimpleNamespace(
        run_root=root,
        run_id=root.name,
        tasks=(task,),
        latest_attempt={
            "workflow_attempt_id": "workflow-later",
            "created_at": "2026-09-15T11:59:00Z",
        },
        latest_receipt=None,
        attempt_outcome="running",
        integrity="admitted",
        lock_observation="remote ownership unverified",
        results_status="incomplete",
        reporting_status="not applicable",
        processing_source_run_id=None,
        processing_source=None,
    )


def _request(root):
    return slurm_submission.SubmissionRequestObservation(
        root / "request-a",
        "recorded-response",
        {
            "scheduler_stderr_pattern": str(root / "request-a-%j.err"),
            "scheduler_stdout_pattern": str(root / "request-a-%j.out"),
            "application_log_root": str(root),
        },
        "42",
        None,
        (),
    )


@pytest.mark.parametrize("missing", ("origin", "reference", "both"))
def test_task_streams_require_both_admitted_start_fields(
    tmp_path, monkeypatch, missing
):
    observed = _run(tmp_path / "run")
    started = observed.tasks[0]
    if missing in {"origin", "both"}:
        started.start_origin = None
    if missing in {"reference", "both"}:
        started.start_reference = None

    def forbidden(*args, **kwargs):
        pytest.fail("Stream projection must not read or infer start evidence")

    for name in ("stat", "lstat", "open", "resolve"):
        monkeypatch.setattr(Path, name, forbidden)
    assert view.task_stream_sources(observed) == ()


@pytest.mark.parametrize(
    "selection", (None, "workflow-earlier", "workflow-later", "absent")
)
def test_task_streams_preserve_preentry_history_and_exact_start_origin_without_reads(
    tmp_path, monkeypatch, selection
):
    observed = _run(tmp_path / "run")
    started = observed.tasks[0]
    old_root = Path("attempts/workflow-earlier/tasks/fixture.owner/reference")
    started.terminal_attempts = (
        SimpleNamespace(
            record={
                "workflow_attempt_id": "workflow-earlier",
                "machine_key": "fixture.owner",
                "scope": {"scope_id": "reference"},
                "status": "failed",
                "task_start_record": None,
                "stderr_log": {"path": str(old_root / "stderr.log")},
                "stdout_log": {"path": str(old_root / "stdout.log")},
            }
        ),
    )
    expected = []
    for origin in ("workflow-earlier", "workflow-later"):
        if selection is None or selection == origin:
            expected.extend(
                observed.run_root
                / "attempts"
                / origin
                / "tasks"
                / "fixture.owner"
                / "reference"
                / name
                for name in ("stderr.log", "stdout.log")
            )

    def forbidden(*args, **kwargs):
        pytest.fail("Projection must not read logs, current Attempt, or dispatch")

    for name in ("stat", "lstat", "open", "resolve"):
        monkeypatch.setattr(Path, name, forbidden)
    sources = view.task_stream_sources(observed, selected_attempt=selection)
    assert [source.path for source in sources] == expected
    assert all(source.root == observed.run_root for source in sources)
    for source in sources:
        assert (
            "recorded failed"
            if "workflow-earlier" in str(source.path)
            else "expected diagnostic from admitted start"
        ) in source.label
    snapshot = view.WatchSnapshot(
        tmp_path / "project.yaml",
        observed=observed,
        application=None
        if selection is None
        else association.SubmissionApplicationObservation(
            status="run-and-attempt-associated", workflow_attempt_id=selection
        ),
    )
    assert view._stream_sources(snapshot) == sources


def test_task_streams_deduplicate_started_paths_against_terminal_references(tmp_path):
    observed = _run(tmp_path / "run")
    started = observed.tasks[0]
    root = "attempts/workflow-later/tasks/fixture.owner/reference"
    started.terminal_attempts = (
        SimpleNamespace(
            record={
                "workflow_attempt_id": "workflow-later",
                "machine_key": "fixture.owner",
                "scope": {"scope_id": "reference"},
                "status": "failed",
                "task_start_record": started.start_reference,
                "stderr_log": {"path": root + "/stderr.log"},
                "stdout_log": {"path": root + "/stdout.log"},
            }
        ),
    )
    sources = view.task_stream_sources(observed)
    assert len(sources) == 2
    assert all("recorded failed" in source.label for source in sources)


def test_started_task_streams_remain_expected_and_use_current_unverified_tail(tmp_path):
    observed = _run(tmp_path / "run")
    source = view.task_stream_sources(observed)[0]
    assert "expected diagnostic from admitted start" in source.label
    missing = view.read_tail(source)
    assert missing.text == "" and missing.diagnostic.startswith("Unavailable:")
    source.path.parent.mkdir(parents=True)
    source.path.write_bytes(b"producer diagnostic\\x00\n")
    tail = view.read_tail(source, missing)
    assert "content not verified" in tail.diagnostic
    assert "producer diagnostic" in tail.text
    assert observed.tasks[0].state == "pending"


def test_refresh_keeps_selected_request_and_only_reverifies_when_explicit(
    tmp_path, monkeypatch
):
    request = _request(tmp_path)
    selected_run = tmp_path / "run-exact"
    calls = []

    def associate(selected):
        calls.append(("associate", selected))
        return association.SubmissionApplicationObservation(
            status="run-and-attempt-associated",
            run_root=selected_run,
            workflow_attempt_id="workflow-earlier",
            recorded_event="analysis_prepared",
        )

    def inspect(root):
        calls.append(("inspect", root))
        return _run(root)

    def action(observed):
        calls.append(("action", observed.run_root))
        return "Review this exact Run."

    def scheduler(selected):
        calls.append(("scheduler", selected))
        return {"state": "PENDING", "reason": "Resources", "source": "squeue"}

    monkeypatch.setattr(association, "inspect_submission_application", associate)

    def select_request(project, selector):
        calls.append(("select", selector))
        assert project == tmp_path / "project.yaml"
        assert selector == str(request.request_root)
        return request

    monkeypatch.setattr(slurm_submission, "select_submission_request", select_request)
    monkeypatch.setattr(slurm_submission, "observe_submission_request", scheduler)
    initial = view.WatchSnapshot(tmp_path / "project.yaml", request=request)
    observed = view.refresh_snapshot(
        initial, verify=True, stream_index=0, inspect_run=inspect, next_action=action
    )
    for _ in range(3):
        observed = view.refresh_snapshot(
            observed,
            verify=False,
            stream_index=0,
            inspect_run=inspect,
            next_action=action,
        )

    assert [name for name, _ in calls].count("inspect") == 1
    assert [name for name, _ in calls].count("associate") == 1
    assert [name for name, _ in calls].count("action") == 1
    assert [name for name, _ in calls].count("select") == 1
    assert [value for name, value in calls if name == "scheduler"] == [request] * 4
    assert initial.observed is None
    text = view.render_snapshot(observed, now=NOW)
    assert "selected Attempt: workflow-earlier" in text
    assert "latest Attempt: workflow-later" in text
    assert "Started; completion unverified" in text
    assert "Run evidence as of:" in text and "changes require r" in text
    assert "not verified completion" in text

    refreshed = view.refresh_snapshot(
        observed, verify=True, stream_index=0, inspect_run=inspect, next_action=action
    )
    assert [name for name, _ in calls].count("inspect") == 2
    assert refreshed.request is request


def test_request_without_run_does_not_infer_or_scan_again_on_timer(
    tmp_path, monkeypatch
):
    request = _request(tmp_path)
    calls = []

    def associate(selected):
        calls.append(selected)
        return association.SubmissionApplicationObservation(
            status="application-log-bound", recorded_event="submission_context_bound"
        )

    monkeypatch.setattr(association, "inspect_submission_application", associate)
    monkeypatch.setattr(
        slurm_submission, "select_submission_request", lambda project, selector: request
    )
    monkeypatch.setattr(
        slurm_submission,
        "observe_submission_request",
        lambda selected: {"state": "RUNNING"},
    )

    def forbidden(*args):
        raise AssertionError("No associated Run is available")

    snapshot = view.WatchSnapshot(tmp_path / "project.yaml", request=request)
    for verify in (True, False, False):
        snapshot = view.refresh_snapshot(
            snapshot,
            verify=verify,
            stream_index=0,
            inspect_run=forbidden,
            next_action=forbidden,
        )
    assert calls == [request]
    assert snapshot.run_root is None and snapshot.observed is None
    assert "Press r to check this request" in view.render_snapshot(snapshot, now=NOW)


def test_run_only_never_queries_scheduler_and_failed_reverify_clears_old_evidence(
    tmp_path, monkeypatch
):
    def forbidden(*args):
        raise AssertionError("Run job ID does not establish a scheduler binding")

    monkeypatch.setattr(slurm_submission, "observe_submission_request", forbidden)
    snapshot = view.WatchSnapshot(tmp_path / "project.yaml", run_root=tmp_path / "run")
    snapshot = view.refresh_snapshot(
        snapshot,
        verify=True,
        stream_index=0,
        inspect_run=_run,
        next_action=lambda _: "Review",
    )
    assert snapshot.scheduler["state"] == "UNKNOWN"

    def failed(root):
        raise OSError("read unavailable\x1b[31m")

    snapshot = view.refresh_snapshot(
        snapshot, verify=True, stream_index=0, inspect_run=failed, next_action=forbidden
    )
    assert snapshot.observed is None and snapshot.verified_at is None
    assert "Verification unavailable" in view.render_snapshot(snapshot, now=NOW)
    assert "\x1b" not in snapshot.verification_error


def test_repainting_is_read_free_and_retains_dated_observation(tmp_path, monkeypatch):
    snapshot = view.WatchSnapshot(
        tmp_path / "project.yaml",
        observed=_run(tmp_path / "run"),
        verified_at=NOW,
        scheduler={"state": "UNKNOWN", "diagnostic": "bad\x1b]8;;url\x07"},
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Painting attempted an observation")

    monkeypatch.setattr(view, "refresh_snapshot", forbidden)
    monkeypatch.setattr(view, "read_tail", forbidden)
    monkeypatch.setattr(Path, "stat", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    for _ in range(20):
        output = view.render_snapshot(snapshot, now=NOW)
        assert "\x1b" not in output and "\x07" not in output
        assert NOW.isoformat(sep=" ") in output
    assert "Current Attempt elapsed: 0:01:00" in output
    later = view.render_snapshot(snapshot, now=NOW + timedelta(hours=1))
    assert "Current Attempt elapsed: 0:01:00" in later


@pytest.mark.parametrize("changed", ("context", "job", "cluster"))
def test_explicit_refresh_refuses_changed_admitted_request_identity(
    tmp_path, monkeypatch, changed
):
    original = _request(tmp_path)
    current = (
        replace(
            original,
            **{
                "context": {
                    **original.context,
                    "application_log_root": str(tmp_path / "other"),
                }
            },
        )
        if changed == "context"
        else replace(
            original,
            **{"recorded_job_id" if changed == "job" else "recorded_cluster": "other"},
        )
    )
    monkeypatch.setattr(
        slurm_submission, "select_submission_request", lambda project, selector: current
    )
    monkeypatch.setattr(
        slurm_submission,
        "observe_submission_request",
        lambda request: {"state": "UNKNOWN"},
    )

    def forbidden(*args):
        raise AssertionError("Changed selection cannot acquire Run authority")

    monkeypatch.setattr(association, "inspect_submission_application", forbidden)
    snapshot = view.WatchSnapshot(
        tmp_path / "project.yaml",
        request=original,
        request_at=NOW,
        application=association.SubmissionApplicationObservation(
            status="run-associated"
        ),
        application_at=NOW,
    )
    result = view.refresh_snapshot(
        snapshot,
        verify=True,
        stream_index=0,
        inspect_run=forbidden,
        next_action=forbidden,
    )
    assert result.request is original and result.request_at == NOW
    assert result.application is None and result.application_at is None
    assert "confirmed response changed" in result.verification_error


def test_slow_tail_does_not_make_scheduler_reply_appear_fresh(tmp_path, monkeypatch):
    current = [NOW]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return current[0]

    monkeypatch.setattr(view, "datetime", Clock)
    monkeypatch.setattr(
        slurm_submission, "observe_submission_request", lambda _: {"state": "RUNNING"}
    )

    def delayed_tail(source, previous):
        current[0] += timedelta(minutes=5)
        return view.StreamTail(source, observed_at=current[0])

    monkeypatch.setattr(view, "read_tail", delayed_tail)
    snapshot = view.WatchSnapshot(tmp_path / "project.yaml", request=_request(tmp_path))
    result = view.refresh_snapshot(
        snapshot,
        verify=False,
        stream_index=0,
        inspect_run=_run,
        next_action=lambda _: "unused",
    )
    assert result.scheduler_at == NOW
    assert result.tail.observed_at == NOW + timedelta(minutes=5)


@pytest.mark.parametrize(
    "records, expected",
    (
        ({"verified": None, "start": None}, "No admitted start"),
        (
            {"verified": None, "start": {"path": "start"}},
            "Started; completion unverified",
        ),
        (
            {"verified": {"path": "receipt"}, "start": {"path": "start"}},
            "Verified complete",
        ),
    ),
)
def test_reporting_transaction_projection_matches_watch(records, expected, tmp_path):
    observed = _run(tmp_path / "run")
    observed.reporting_status = "incomplete"
    observed.reporting_completion_records = {"scientific": records}
    snapshot = view.WatchSnapshot(tmp_path, observed=observed, verified_at=NOW)
    assert view.reporting_observation(records) == expected
    assert f"scientific: {expected}" in view.render_snapshot(snapshot, now=NOW)


@pytest.mark.parametrize("change", ("replace", "truncate", "grow"))
def test_tail_handles_stream_generations_without_carrying_old_bytes(tmp_path, change):
    path = tmp_path / "stream"
    path.write_bytes(b"old-generation")
    source = view.StreamSource("Task log", path, tmp_path)
    previous = view.read_tail(source)
    if change == "replace":
        path.rename(tmp_path / "old")
        path.write_bytes(b"new-generation")
    elif change == "truncate":
        path.write_bytes(b"new")
    else:
        path.write_bytes(b"old-generation appended")
    current = view.read_tail(source, previous)
    assert current.text == path.read_text()
    assert "content not verified" in current.diagnostic
    assert (
        "replaced" in current.diagnostic
        if change == "replace"
        else "replaced" not in current.diagnostic
    )
    assert (
        "truncated" in current.diagnostic
        if change == "truncate"
        else "truncated" not in current.diagnostic
    )


@pytest.mark.parametrize(
    "defect",
    (
        "missing",
        "symlink",
        "parent-symlink",
        "fifo",
        "foreign-uid",
        "ancestor-replaced",
    ),
)
def test_tail_refuses_unowned_or_unstable_paths(tmp_path, monkeypatch, defect):
    root = tmp_path / "logs"
    root.mkdir()
    path = root / "stream"
    path.write_bytes(b"private-bytes")
    if defect == "missing":
        path.unlink()
    elif defect == "symlink":
        path.rename(root / "real")
        path.symlink_to(root / "real")
    elif defect == "parent-symlink":
        root.rename(tmp_path / "real")
        root.symlink_to(tmp_path / "real", target_is_directory=True)
    elif defect == "fifo":
        path.unlink()
        os.mkfifo(path)
    elif defect == "foreign-uid":
        monkeypatch.setattr(view.os, "getuid", lambda: path.stat().st_uid + 1)
    else:
        original = view.read_suffix_with_identity

        def read(*args, **kwargs):
            result = original(*args, **kwargs)
            root.rename(tmp_path / "old")
            root.mkdir()
            (root / "stream").write_bytes(b"replacement")
            return result

        monkeypatch.setattr(view, "read_suffix_with_identity", read)
    observed = view.read_tail(view.StreamSource("Stream", path, root))
    assert observed.text == "" and observed.state is None
    assert observed.diagnostic.startswith("Unavailable:")


def test_tail_bounds_bytes_lines_and_escapes_control_sequences(tmp_path):
    path = tmp_path / "stream"
    data = (
        b"ignored-prefix" * 10000
        + b"\n" * 300
        + b"\x1b]8;;file:///secret\x07[red]raw[/red]\xff\r\t"
    )
    path.write_bytes(data)
    result = view.read_tail(view.StreamSource("Stream", path, tmp_path))
    assert "ignored-prefix" not in result.text
    assert len(result.text.split("\n")) <= 256
    assert all(
        character.isprintable() or character == "\n" for character in result.text
    )
    assert "[red]raw[/red]" in result.text
    assert "\\x1b" in result.text and "\\x07" in result.text
    assert "\\r" in result.text and "\\t" in result.text


def test_watch_scroll_rows_include_older_lines_from_the_complete_retained_tail(
    tmp_path,
):
    path = tmp_path / "stream"
    path.write_text("\n".join(f"retained-line-{index:03}" for index in range(300)))
    tail = view.read_tail(view.StreamSource("Stream", path, tmp_path))
    snapshot = view.WatchSnapshot(tmp_path, tail=tail)

    # Interactive watch scrolls these complete rows; terminal height clips only
    # the visible layout, not the retained history available to j/k.
    rows = view.render_snapshot(snapshot, now=NOW).split("\n")
    older_offset = rows.index("retained-line-044")
    assert rows[older_offset : older_offset + 3] == [
        "retained-line-044",
        "retained-line-045",
        "retained-line-046",
    ]
    assert rows[-1] == "retained-line-299"
    assert "retained-line-043" not in rows
    assert sum(row.startswith("retained-line-") for row in rows) == 256

    plain_rows = view.render_snapshot(snapshot, now=NOW, tail_lines=8).split("\n")
    assert "retained-line-044" not in plain_rows
    assert plain_rows[-8] == "retained-line-292"


def test_worker_coalesces_verification_and_close_does_not_wait_for_reader(tmp_path):
    entered = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    calls = []

    def refresh(snapshot, *, verify, stream_index):
        calls.append((verify, stream_index))
        entered.set()
        assert release.wait(3)
        if len(calls) == 2:
            finished.set()
        return replace(snapshot, next_action=str(stream_index))

    worker = view.RefreshWorker(view.WatchSnapshot(tmp_path), refresh)
    try:
        worker.request(verify=False, stream_index=0)
        assert entered.wait(1)
        for index in range(1, 20):
            worker.request(verify=index == 3, stream_index=index)
        assert worker.pending == (True, 19)
        assert worker.thread.daemon
        release.set()
        assert finished.wait(1)
        assert calls == [(False, 0), (True, 19)]
    finally:
        worker.close()
        release.set()
        worker.thread.join(1)
    assert not worker.thread.is_alive()


def test_worker_close_returns_while_observation_is_stalled(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def blocked(snapshot, **kwargs):
        entered.set()
        release.wait(3)
        return snapshot

    worker = view.RefreshWorker(view.WatchSnapshot(tmp_path), blocked)
    try:
        worker.request(verify=True, stream_index=0)
        assert entered.wait(1)
        worker.close()
        assert worker.thread.is_alive() and worker.closed
    finally:
        release.set()
        worker.thread.join(1)


def test_nonterminal_watch_is_one_plain_snapshot_with_no_worker(
    tmp_path, monkeypatch, capsys
):
    calls = []
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    def inspect(root):
        calls.append(root)
        return _run(root)

    def forbidden(*args, **kwargs):
        raise AssertionError("Nonterminal snapshot must not start a worker")

    monkeypatch.setattr(view, "RefreshWorker", forbidden)
    assert (
        view.watch(
            tmp_path / "project.yaml",
            run_root=tmp_path / "run",
            inspect_run=inspect,
            next_action=lambda _: "Review",
        )
        == 0
    )
    assert calls == [tmp_path / "run"]
    output = capsys.readouterr().out
    assert output.count("EMRYS inspection") == 1 and "\x1b" not in output
    assert "No exact submission selected" in output


@pytest.mark.parametrize(
    "defect", ("stdin", "stdout", "stderr", "dumb", "both-selections", "no-run")
)
def test_action_watch_refuses_unsupported_modes_before_observation(
    tmp_path, monkeypatch, defect
):
    for name in ("stdin", "stdout", "stderr"):
        monkeypatch.setattr(getattr(sys, name), "isatty", lambda: True)
    monkeypatch.setenv("TERM", "xterm")
    if defect in {"stdin", "stdout", "stderr"}:
        monkeypatch.setattr(getattr(sys, defect), "isatty", lambda: False)
    elif defect == "dumb":
        monkeypatch.setenv("TERM", "dumb")

    def forbidden(*args, **kwargs):
        pytest.fail("Unsupported action mode must not observe or invoke an action")

    monkeypatch.setattr(view, "RefreshWorker", forbidden)
    monkeypatch.setattr(view, "refresh_snapshot", forbidden)
    message = (
        "one exact Run or submission"
        if defect in {"both-selections", "no-run"}
        else "interactive watch"
    )
    with pytest.raises(view.PresentationError, match=message):
        view.watch(
            tmp_path / "project.yaml",
            request=_request(tmp_path) if defect == "both-selections" else None,
            run_root=None if defect == "no-run" else tmp_path / "run",
            inspect_run=forbidden,
            next_action=forbidden,
            review_actions=((b"p", "resume plan/confirm", forbidden),),
        )


@pytest.mark.skipif(
    importlib.util.find_spec("rich") is None,
    reason="Interactive rendering requires the existing Rich dependency",
)
@pytest.mark.parametrize(
    "mode", ("readonly", "quit-enabled", "resume", "report", "stop", "restore-failure")
)
def test_interactive_quit_restores_terminal_without_waiting_for_stalled_worker(
    tmp_path,
    mode,
):
    marker = tmp_path / "entered"
    code = """
import sys, termios, threading
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from emrys.orchestration.run_coordinator import _inspection_presentation as view
root = Path(sys.argv[1])
mode = sys.argv[2]
original_terminal = termios.tcgetattr(0)
workers = []
original_worker = view.RefreshWorker
def worker(*args, **kwargs):
    current = original_worker(*args, **kwargs)
    workers.append(current)
    return current
view.RefreshWorker = worker
def blocked(*args, **kwargs):
    workers[0].request(verify=True, stream_index=0)
    (root / 'entered').touch()
    threading.Event().wait(60)
view.refresh_snapshot = blocked
def review(command):
    assert threading.current_thread() is threading.main_thread()
    assert termios.tcgetattr(0) == original_terminal
    assert len(workers) == 1 and workers[0].closed
    assert workers[0].pending is None and workers[0].thread.is_alive()
    print('REVIEW CALLED', command)
    return 7
if mode == 'restore-failure':
    original_restore = termios.tcsetattr
    def fail_restore(fd, when, attrs):
        if when == termios.TCSADRAIN:
            raise OSError('terminal restoration failed')
        return original_restore(fd, when, attrs)
    termios.tcsetattr = fail_restore
actions = () if mode == 'readonly' else (
    ((b's', 'stop preview', partial(review, 'stop')),) if mode == 'stop' else (
        (b'p', 'resume plan/confirm', partial(review, 'resume')),
        (b'o', 'report preview', partial(review, 'report')),
    )
)
request = SimpleNamespace(request_root=root / 'submission', recorded_job_id=None)
result = view.watch(root / 'project.yaml',
                    run_root=None if mode == 'stop' else root / 'run',
                    request=request if mode == 'stop' else None,
                    inspect_run=blocked, next_action=lambda _: '', review_actions=actions)
print('WATCH EXITED', result)
raise SystemExit(result)
"""
    master, slave = pty.openpty()
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 80, 0, 0))
    original_terminal = termios.tcgetattr(master)
    environment = dict(
        os.environ,
        TERM="xterm",
        COLUMNS="80",
        LINES="40",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(Path(__file__).resolve().parents[3] / "src"),
    )
    process = subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(tmp_path), mode],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=environment,
    )
    os.close(slave)
    output = b""

    def rendered_text():
        return b" ".join(re.sub(rb"\x1b\[[0-?]*[ -/]*[@-~]", b"", output).split())

    try:
        deadline = time.monotonic() + 5
        caption = (
            b"q quit"
            if mode == "readonly"
            else (
                b"s stop preview"
                if mode == "stop"
                else b"p resume plan/confirm | o report preview"
            )
        )
        while (
            (not marker.exists() or caption not in rendered_text())
            and process.poll() is None
            and time.monotonic() < deadline
        ):
            if select.select([master], [], [], 0.05)[0]:
                output += os.read(master, 65536)
        assert marker.exists(), output
        assert caption in rendered_text(), output
        assert (b"resume plan/confirm" in rendered_text()) is (
            mode not in {"readonly", "stop"}
        )
        assert (b"stop preview" in rendered_text()) is (mode == "stop")
        assert b"Refresh in progress" in rendered_text()
        selected_key = {"report": b"o", "stop": b"s"}.get(mode, b"p")
        os.write(
            master,
            b"posq"
            if mode == "readonly"
            else b"q"
            if mode == "quit-enabled"
            else selected_key * 2,
        )
        while process.poll() is None and time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    output += os.read(master, 65536)
                except OSError:
                    break
        reviewed = mode in {"resume", "report", "stop"}
        expected = 7 if reviewed else 1 if mode == "restore-failure" else 0
        assert process.wait(timeout=1) == expected, output
        while select.select([master], [], [], 0)[0]:
            try:
                output += os.read(master, 65536)
            except OSError:
                break
        assert b"\x1b[?1049l" in output
        assert output.count(b"REVIEW CALLED") == reviewed
        if mode == "restore-failure":
            assert b"terminal restoration failed" in output
            assert b"WATCH EXITED" not in output
        else:
            assert b"WATCH EXITED" in output
            assert termios.tcgetattr(master) == original_terminal
        if reviewed:
            assert (b"REVIEW CALLED " + mode.encode()) in output
            assert output.index(b"\x1b[?1049l") < output.index(b"REVIEW CALLED")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
