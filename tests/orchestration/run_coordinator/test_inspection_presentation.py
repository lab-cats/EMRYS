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
from functools import partial
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from emrys.orchestration.run_coordinator import _inspection_presentation as view
from emrys.orchestration.run_coordinator import _submission_inspection as association
from emrys.orchestration.run_coordinator import slurm_submission


NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
_DISCOVER_RUN_APPLICATIONS = association.inspect_run_applications


def _run(root):
    task = SimpleNamespace(
        expected=SimpleNamespace(
            step_id="00a", machine_key="fixture.owner", scope_id="reference"
        ),
        state="pending",
        start_origin="workflow-later",
        start_reference={"path": "start.json"},
        terminal_attempts=(),
        retry_task_attempt_record=None,
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


@pytest.fixture
def watcher(monkeypatch):
    """Record callbacks; unconfigured callbacks still execute their real owner."""
    calls = Mock()
    calls.inspect.side_effect = _run
    calls.action.return_value = "Review"
    for owner, name, alias in (
        (slurm_submission, "select_submission_request", "select"),
        (slurm_submission, "observe_submission_request", "scheduler"),
        (association, "inspect_submission_application", "associate"),
        (association, "inspect_run_applications", "discover"),
    ):
        callback = Mock(wraps=getattr(owner, name))
        calls.attach_mock(callback, alias)
        monkeypatch.setattr(owner, name, callback)
    return calls, partial(
        view.refresh_snapshot,
        stream_index=0,
        inspect_run=calls.inspect,
        next_action=calls.action,
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        ("pending", "Aborted before publication; retry available"),
        ("blocked", "Verification not admitted"),
        ("verified", "Verified complete"),
    ),
)
def test_task_observation_distinguishes_current_retry_readiness(
    tmp_path, state, expected
):
    task = _run(tmp_path).tasks[0]
    task.state = state
    task.retry_task_attempt_record = {"path": "retained-abort.json", "sha256": "a" * 64}
    assert view.task_observation(task) == expected


def test_verified_completion_is_clear_and_replaces_stale_log_progress(tmp_path):
    observed = _run(tmp_path / ("run-" + "a" * 64))
    observed.attempt_outcome = "succeeded"
    observed.results_status = "complete"
    observed.reporting_status = "complete"
    observed.tasks = tuple(
        SimpleNamespace(
            expected=SimpleNamespace(step_id=step),
            state="verified",
            retry_task_attempt_record=None,
        )
        for step in ("09", "10")
    )
    workflow = view.dashboard.parse_workflow("")
    workflow["done"]["09"] = 1
    snapshot = view.WatchSnapshot(
        None,
        raw_job={"job_id": 42},
        observed=observed,
        scheduler={"state": "COMPLETED"},
        workflow=workflow,
    )

    assert view.completion_line(observed) == (
        "Run complete: scientific Results and reporting are verified."
    )
    rendered = view.render_dashboard(
        snapshot, height=56, width=160, view="overview", scroll=0
    ).plain
    assert "Run complete: scientific Results and reporting are verified." in rendered
    assert "09      Paired CMH ranking" in rendered and "1/1" in rendered
    assert "10      Scientific context" in rendered and "1/1" in rendered


@pytest.mark.parametrize("outcome", [None, "attempt_failed", "attempt_interrupted"])
def test_recorded_application_outcomes_are_dated_escaped_diagnostics_in_all_views(
    tmp_path, monkeypatch, outcome
):
    application = association.SubmissionApplicationObservation(
        status="run-and-attempt-associated",
        application_log=tmp_path / "retained.jsonl",
        recorded_event="analysis_prepared",
        recorded_outcome=outcome,
        recorded_outcome_phase="preflight\nother\x1b[31m" if outcome else None,
        recorded_run_id="run-recorded",
        run_root=tmp_path / "run-recorded",
        workflow_attempt_id="workflow-earlier",
    )
    logs = association.RunApplicationObservation(tmp_path, (application,), "complete")

    def forbidden(*_args, **_kwargs):
        pytest.fail("Outcome rendering cannot read or re-admit evidence")

    for name in ("stat", "lstat", "open", "resolve"):
        monkeypatch.setattr(Path, name, forbidden)
    for selected in (
        {"application": application},
        {"run_applications": logs},
    ):
        text = view.render_snapshot(
            view.WatchSnapshot(
                tmp_path / "project.yaml", application_at=NOW, **selected
            ),
            now=NOW + timedelta(hours=1),
        )
        assert str(NOW) in text
        assert ("Recorded application outcome:" in text) is (outcome is not None)
        if outcome:
            assert f"Recorded application outcome: {outcome}" in text
            assert r"phase: preflight\nother\x1b[31m" in text and "\x1b" not in text
    for detail in ("normal", "verbose", "debug"):
        lines = view.run_application_lines(logs, detail=detail)
        assert any("Recorded application outcome:" in line for line in lines) is (
            outcome is not None
        )
        if outcome:
            assert (f"  {application.application_log}" in lines) is (detail != "normal")
    assert application.status == "run-and-attempt-associated"
    assert application.workflow_attempt_id == "workflow-earlier"


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
    tmp_path, watcher
):
    calls, refresh = watcher
    request, selected_run = _request(tmp_path), tmp_path / "run-exact"
    calls.select.return_value = request
    calls.associate.return_value = association.SubmissionApplicationObservation(
        status="run-and-attempt-associated",
        run_root=selected_run,
        workflow_attempt_id="workflow-earlier",
        recorded_event="analysis_prepared",
    )
    calls.action.return_value = "Review this exact Run."
    calls.scheduler.return_value = {
        "state": "PENDING",
        "reason": "Resources",
        "source": "squeue",
    }
    initial = view.WatchSnapshot(tmp_path / "project.yaml", request=request)
    observed = refresh(initial, verify=True)
    for _ in range(3):
        observed = refresh(observed, verify=False)
    calls.inspect.assert_called_once_with(selected_run)
    calls.associate.assert_called_once_with(request)
    calls.action.assert_called_once_with(observed.observed)
    calls.select.assert_called_once_with(
        tmp_path / "project.yaml", str(request.request_root)
    )
    assert [call.args for call in calls.scheduler.call_args_list] == [(request,)] * 4
    assert initial.observed is None
    text = view.render_snapshot(observed, now=NOW)
    for value in (
        "selected Attempt: workflow-earlier",
        "latest Attempt: workflow-later",
        "Started; completion unverified",
        "Run evidence as of:",
        "changes require r",
        "not verified completion",
    ):
        assert value in text
    refreshed = refresh(observed, verify=True)
    assert calls.inspect.call_count == 2 and refreshed.request is request


def test_request_without_run_does_not_infer_or_scan_again_on_timer(tmp_path, watcher):
    calls, refresh = watcher
    request = _request(tmp_path)
    calls.select.return_value = request
    calls.associate.return_value = association.SubmissionApplicationObservation(
        status="application-log-bound", recorded_event="submission_context_bound"
    )
    calls.scheduler.return_value = {"state": "RUNNING"}
    calls.inspect.side_effect = calls.action.side_effect = AssertionError(
        "No associated Run"
    )
    snapshot = view.WatchSnapshot(tmp_path / "project.yaml", request=request)
    for verify in (True, False, False):
        snapshot = refresh(snapshot, verify=verify)
    calls.associate.assert_called_once_with(request)
    assert snapshot.run_root is None and snapshot.observed is None
    assert "Press r to check this request" in view.render_snapshot(snapshot, now=NOW)


def test_run_only_never_queries_scheduler_and_failed_reverify_clears_old_evidence(
    tmp_path, watcher
):
    calls, refresh = watcher
    calls.scheduler.side_effect = AssertionError(
        "Run job ID does not establish a scheduler binding"
    )
    snapshot = refresh(
        view.WatchSnapshot(tmp_path / "project.yaml", run_root=tmp_path / "run"),
        verify=True,
    )
    assert snapshot.scheduler["state"] == "UNKNOWN"
    calls.inspect.side_effect = OSError("read unavailable\x1b[31m")
    calls.action.side_effect = AssertionError("Unverified Run cannot be replanned")
    snapshot = refresh(snapshot, verify=True)
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
    tmp_path, watcher, changed
):
    calls, refresh = watcher
    original = _request(tmp_path)
    changes = (
        {
            "context": {
                **original.context,
                "application_log_root": str(tmp_path / "other"),
            }
        }
        if changed == "context"
        else {"recorded_job_id" if changed == "job" else "recorded_cluster": "other"}
    )
    calls.select.return_value = replace(original, **changes)
    calls.scheduler.return_value = {"state": "UNKNOWN"}
    for actor in (calls.associate, calls.inspect, calls.action):
        actor.side_effect = AssertionError(
            "Changed selection cannot acquire Run authority"
        )
    snapshot = view.WatchSnapshot(
        tmp_path / "project.yaml",
        request=original,
        request_at=NOW,
        application=association.SubmissionApplicationObservation(
            status="run-associated"
        ),
        application_at=NOW,
    )
    result = refresh(snapshot, verify=True)
    assert result.request is original and result.request_at == NOW
    assert result.application is None and result.application_at is None
    assert "confirmed response changed" in result.verification_error


def test_slow_tail_does_not_make_scheduler_reply_appear_fresh(
    tmp_path, monkeypatch, watcher
):
    calls, refresh = watcher
    current = [NOW]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return current[0]

    monkeypatch.setattr(view, "datetime", Clock)
    calls.scheduler.return_value = {"state": "RUNNING"}

    def delayed_tail(source, previous):
        current[0] += timedelta(minutes=5)
        return view.StreamTail(source, observed_at=current[0])

    monkeypatch.setattr(view, "read_tail", delayed_tail)
    result = refresh(
        view.WatchSnapshot(tmp_path / "project.yaml", request=_request(tmp_path)),
        verify=False,
    )
    assert result.scheduler_at == NOW and result.tail.observed_at == NOW + timedelta(
        minutes=5
    )


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


def test_watch_log_styles_preserve_every_literal_line(tmp_path):
    source = view.StreamSource("fixture", tmp_path / "fixture.log", tmp_path)
    snapshot = view.WatchSnapshot(
        None,
        scheduler={"state": "RUNNING"},
        scheduler_at=NOW,
        tail=view.StreamTail(
            source,
            "INFO: preparing\n"
            "[2026-09-16 12:00:00] WARNING: delayed\n"
            "2026-09-16T12:00:01Z ERROR: failed\n"
            '{"timestamp":"2026-09-16T12:00:02Z","level":"INFO","message":"checking"}\n'
            "Finished job 7.\n"
            "unaltered text",
            diagnostic="Current diagnostic bytes; content not verified",
            observed_at=NOW,
        ),
    )
    styled = view.render_watch_text(snapshot, now=NOW)
    assert styled.plain == view.render_snapshot(snapshot, now=NOW)
    styled_fragments = {
        styled.plain[span.start : span.end]: str(span.style) for span in styled.spans
    }
    assert styled_fragments["INFO: preparing"] == "cyan"
    assert styled_fragments["[2026-09-16 12:00:00] WARNING: delayed"] == "yellow"
    assert styled_fragments["2026-09-16T12:00:01Z ERROR: failed"] == "red"
    assert (
        styled_fragments[
            '{"timestamp":"2026-09-16T12:00:02Z","level":"INFO","message":"checking"}'
        ]
        == "cyan"
    )
    assert styled_fragments["Finished job 7."] == "green"
    assert "unaltered text" not in styled_fragments


def test_watch_key_reader_discards_sgr_mouse_reports_and_preserves_arrows():
    reader, writer = os.pipe()
    try:
        os.write(writer, b"\x1b[<64;10;4M")
        assert view._read_watch_key(reader) is None
        os.write(writer, b"\x1b[B")
        assert view._read_watch_key(reader) == b"\x1b[B"
    finally:
        os.close(reader)
        os.close(writer)


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
import sys, termios, threading, select
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from emrys.orchestration.run_coordinator import _inspection_presentation as view
root = Path(sys.argv[1])
mode = sys.argv[2]
def terminal_settings():
    attrs = termios.tcgetattr(0)
    # Darwin sets this kernel retype-pending bit on canonical-mode restoration.
    if sys.platform == "darwin":
        attrs[3] &= ~termios.PENDIN
    return attrs
original_terminal = terminal_settings()
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
    assert terminal_settings() == original_terminal
    assert not select.select([0], [], [], 0)[0]
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
        (b'b', 'report preview', partial(review, 'report')),
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
                else b"p resume plan/confirm | b report preview"
            )
        )
        while (
            (
                not marker.exists()
                or caption not in rendered_text()
                or b"Refresh in progress" not in rendered_text()
            )
            and process.poll() is None
            and time.monotonic() < deadline
        ):
            if select.select([master], [], [], 0.05)[0]:
                chunk = os.read(master, 65536)
                if not chunk:
                    break
                output += chunk
        assert marker.exists(), output
        assert caption in rendered_text(), output
        assert b"recheck selection/evidence (read-only)" in rendered_text(), output
        assert (b"resume plan/confirm" in rendered_text()) is (
            mode not in {"readonly", "stop"}
        )
        assert (b"stop preview" in rendered_text()) is (mode == "stop")
        assert b"Refresh in progress" in rendered_text()
        selected_key = {"report": b"b", "stop": b"s"}.get(mode, b"p")
        os.write(
            master,
            b"pobsq"
            if mode == "readonly"
            else b"3\x1b[<64;10;4Mo2\t1\x1b[B\x1b[A\x1b[6~\x1b[5~gq"
            if mode == "quit-enabled"
            else selected_key * 2,
        )
        while process.poll() is None and time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    chunk = os.read(master, 65536)
                    if not chunk:
                        break
                    output += chunk
                except OSError:
                    break
        reviewed = mode in {"resume", "report", "stop"}
        expected = 7 if reviewed else 1 if mode == "restore-failure" else 0
        assert process.wait(timeout=1) == expected, output[-1800:]
        while select.select([master], [], [], 0)[0]:
            try:
                chunk = os.read(master, 65536)
                if not chunk:
                    break
                output += chunk
            except OSError:
                break
        assert b"\x1b[?1049l" in output
        assert view._MOUSE_TRACKING_ON.encode() in output
        assert view._MOUSE_TRACKING_OFF.encode() in output
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


@pytest.mark.parametrize(
    "refresh_result", ["unknown", "partial", "exception", "run-failure"]
)
def test_run_log_refresh_retains_all_matches_and_revokes_unadmitted_streams(
    tmp_path, monkeypatch, watcher, refresh_result
):
    calls, refresh = watcher
    project, root, logs = tmp_path / "project.yaml", tmp_path / "run", tmp_path / "logs"
    paths = (
        logs / "application-a/emrys-run.jsonl",
        logs / "application-b/emrys-report.jsonl",
    )
    for path in paths:
        path.parent.mkdir(parents=True)
        path.write_text("diagnostic only\n")
    matches = tuple(
        association.SubmissionApplicationObservation(
            status="run-associated",
            application_log=path,
            run_root=root,
            recorded_event="reporting_started" if index else "analysis_prepared",
            workflow_attempt_id=None if index else "workflow-earlier",
        )
        for index, path in enumerate(paths)
    )
    complete = association.RunApplicationObservation(logs, matches, "complete")
    calls.discover.return_value = complete
    calls.scheduler.side_effect = pytest.fail.Exception(
        "Run logs do not establish a scheduler binding"
    )
    selected = refresh(
        view.WatchSnapshot(
            project,
            run_root=root,
            run_applications=association.RunApplicationObservation(logs),
        ),
        verify=True,
    )
    assert [source.path for source in selected.streams[:2]] == list(paths)
    task_sources = selected.streams[2:]
    assert len(task_sources) == 2 and all(
        "workflow-later" in str(item.path) for item in task_sources
    )
    calls.inspect.side_effect = calls.action.side_effect = pytest.fail.Exception(
        "Timer reverified or replanned Run"
    )
    for _ in range(3):
        selected = refresh(selected, verify=False)
    calls.discover.assert_called_once_with(project, root, logs)
    text = view.render_snapshot(selected, now=NOW)
    for value in (
        "Run diagnostic logs: 2 association(s); scan complete.",
        "Run log associations as of:",
        "Application log search root:",
    ):
        assert value in text
    calls.inspect.side_effect = (
        OSError("Run authority unavailable")
        if refresh_result == "run-failure"
        else _run
    )
    calls.action.side_effect = None
    if refresh_result == "exception":
        monkeypatch.setattr(
            association,
            "_CandidateAdmission",
            Mock(side_effect=RuntimeError("new reader unavailable\x1b[31m")),
        )
        calls.discover.side_effect = _DISCOVER_RUN_APPLICATIONS
    elif refresh_result != "run-failure":
        calls.discover.return_value = association.RunApplicationObservation(
            logs,
            matches[1:] if refresh_result == "partial" else (),
            "unknown",
            ("scan changed\nretain evidence",),
        )
    selected = refresh(selected, verify=True)
    assert calls.discover.call_count == 2
    assert all(
        call.args == (project, root, logs) for call in calls.discover.call_args_list
    )
    assert paths[0] not in [source.path for source in selected.streams]
    assert (paths[1] in [source.path for source in selected.streams]) is (
        refresh_result == "partial"
    )
    if refresh_result == "run-failure":
        assert selected.streams == () and selected.observed is None
        assert selected.application_at is None
    else:
        assert selected.streams[-2:] == task_sources
        assert selected.application_at is not None and selected.observed is not None
    assert selected.run_applications.status == "unknown"
    assert "\x1b" not in view.render_snapshot(selected, now=NOW)


def test_run_log_rendering_uses_only_the_collection_and_escapes_public_output(
    tmp_path, monkeypatch
):
    item = association.SubmissionApplicationObservation(
        status="run-associated",
        application_log=tmp_path / "bad\x1b[31m.jsonl",
        recorded_event="reporting_started",
        run_root=tmp_path / "run",
    )
    collection = association.RunApplicationObservation(
        tmp_path, (item,), "unknown", ("issue\nnext",)
    )
    snapshot = view.WatchSnapshot(
        tmp_path, run_applications=collection, application_at=NOW
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Rendering performed a read or association scan")

    monkeypatch.setattr(association, "inspect_run_applications", forbidden)
    for name in ("stat", "lstat", "open", "resolve"):
        monkeypatch.setattr(Path, name, forbidden)
    normal = view.run_application_lines(collection)
    verbose = view.run_application_lines(collection, detail="verbose")
    assert str(item.application_log) not in "\n".join(normal)
    assert str(item.application_log) in "\n".join(verbose)
    assert "none (Run only)" in "\n".join(verbose)
    text = view.render_snapshot(snapshot, now=NOW)
    assert "\x1b" not in text and "issue\\nnext" in text


def _legacy_trace():
    return """Job stats:
job                            count
---------------------------  -------
align_RNA_reads_with_STAR           2
construct_canonical_BAM             2
total                              4

[Tue Sep 15 11:00:00 2026]
localrule align_RNA_reads_with_STAR:
    jobid: 1
    wildcards: sample_id=control1
[Tue Sep 15 11:02:00 2026]
Finished jobid: 1 (Rule: align_RNA_reads_with_STAR)
1 of 4 steps (25%) done
"""


def test_scheduler_snapshot_reconnects_complete_trace_without_project_or_rpc(
    tmp_path, monkeypatch, capsys
):
    import argparse
    from emrys.orchestration.run_coordinator import control

    stdout = tmp_path / "emrys-local-pilot-42.out"
    stderr = tmp_path / "emrys-local-pilot-42.err"
    stdout.write_text(
        "Run ID: unverified-from-stream\nRun root: /never/admit/from/log\n"
    )
    stderr.write_text(_legacy_trace() + "ordinary diagnostic\n" * 400)
    original = {p: p.read_bytes() for p in (stdout, stderr)}

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Offline diagnostic viewing cannot query Slurm, admit a Project/Run, or execute"
        )

    monkeypatch.setattr(view.dashboard._scheduler, "command_bytes", forbidden)
    monkeypatch.setattr(control, "_resolve_run_argument", forbidden)
    monkeypatch.setattr(control.inspection, "inspect_run", forbidden)
    monkeypatch.setattr(control, "open_attempt_log", forbidden)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    args = parser.parse_args(
        [
            "--snapshot",
            "--job-id",
            "42",
            "--offline",
            "--out",
            str(stdout),
            "--err",
            str(stderr),
        ]
    )
    assert control.inspect_from_args(args) == 0
    text = capsys.readouterr().out
    assert "1/4" in text and "STAR alignment" in text
    assert "unverified-from-stream" in text and "diagnostic selection only" in text
    assert "Scheduler: UNKNOWN" in text and "Offline; scheduler not queried" in text
    assert "Run evidence as of: unavailable" in text
    assert "Project:" not in text and "\x1b" not in text
    assert {p: p.read_bytes() for p in (stdout, stderr)} == original


@pytest.mark.parametrize("explicit", [False, True])
def test_scheduler_dashboard_uses_legacy_selector_precedence_and_freezes_selection(
    tmp_path, monkeypatch, explicit
):
    import argparse
    from emrys.orchestration.run_coordinator import control

    monkeypatch.setenv("EMRYS_DASHBOARD_JOB_ID", "41")
    monkeypatch.setenv("EMRYS_DASHBOARD_LOG_DIR", str(tmp_path))
    selected = {
        "job_id": 42 if explicit else 41,
        "out": str(tmp_path / "out"),
        "err": str(tmp_path / "err"),
    }
    calls = []

    def resolve(*args):
        calls.append(args)
        return selected

    def watch(project, **kwargs):
        assert project is None
        assert kwargs["raw_job"] is selected
        assert kwargs["refresh_seconds"] == 5
        assert kwargs["snapshot_only"] is False
        assert not kwargs.get("review_actions")
        return 0

    monkeypatch.setattr(view.dashboard, "resolve_selection", resolve)
    monkeypatch.setattr(view, "watch", watch)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    args = ["--watch", "--refresh", "5", "--job-id", *(["42"] if explicit else [])]
    assert control.inspect_from_args(parser.parse_args(args)) == 0
    assert calls == [("42" if explicit else "41", str(tmp_path), None, None, False)]


@pytest.mark.parametrize(
    "extra",
    [
        ["--actions"],
        ["--project", "/not-admitted"],
        ["some-run"],
        ["--submission", "request"],
        ["--refresh", "4"],
    ],
)
def test_raw_dashboard_refuses_ambiguous_or_action_selection_before_reads(
    monkeypatch, extra, capsys
):
    import argparse
    from emrys.orchestration.run_coordinator import control

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid raw selector must fail before discovery or action")

    monkeypatch.setattr(view.dashboard, "resolve_selection", forbidden)
    monkeypatch.setattr(view, "watch", forbidden)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    assert (
        control.inspect_from_args(
            parser.parse_args(["--watch", "--job-id", "42", *extra])
        )
        == 2
    )
    assert "error:" in capsys.readouterr().err


def test_parity_views_preserve_panels_styles_and_literal_log_text(
    tmp_path, monkeypatch
):
    snapshot = view.WatchSnapshot(
        None,
        raw_job={"job_id": 42},
        scheduler={
            "state": "RUNNING",
            "cpus": "12",
            "partition": "compute",
            "node": "node1",
            "max_rss": "4G",
        },
        control_identity={"run_id": "run-<literal>\x1b[31m", "workflow_cores": "12"},
        workflow=view.dashboard.parse_workflow(_legacy_trace()),
        trace_at=NOW,
    )

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Repainting shared projections must not read any filesystem or scheduler state"
        )

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(view.dashboard._scheduler, "command_bytes", forbidden)
    overview = view.render_dashboard(
        snapshot, height=56, width=160, view="overview", scroll=0
    )
    details = view.render_dashboard(
        snapshot, height=56, width=160, view="details", scroll=0
    )
    for title in (
        "RUN OVERVIEW",
        "PIPELINE",
        "CURRENT WORK",
        "SAMPLE LANES",
        "FLOW, RUN ID & ACTIVITY",
    ):
        assert title in overview.plain
    for title in (
        "JOB, RESOURCES & RUN IDENTITY",
        "CURRENT WORK DETAILS",
        "SAMPLE DETAILS",
    ):
        assert title in details.plain
    assert "control1" in details.plain and "12 CPUs" in details.plain
    assert "run-<literal>\\x1b[31m" in details.plain and "\x1b" not in details.plain
    assert any(span.style == "bold yellow" for span in overview.spans)
    undated = view.render_dashboard(
        replace(snapshot, trace_at=None),
        height=56,
        width=160,
        view="details",
        scroll=0,
    )
    assert "NFS-light 30s (unavailable)" in undated.plain
    for width, height in ((100, 30), (60, 10)):
        text = view.render_dashboard(
            snapshot, height=height, width=width, view="details", scroll=6
        )
        assert len(text.plain.splitlines()) == height
        assert all(len(line) <= width for line in text.plain.splitlines())


def test_dashboard_pipeline_separates_columns_from_semantic_state() -> None:
    model = view.dashboard.parse_workflow(_legacy_trace())
    rows = view.dashboard.pipeline_lines(model, NOW.timestamp(), 100, False)
    assert [style for _text, style in rows[0]] == ["label"] * 5
    row = next(
        item
        for item in rows[1:]
        if isinstance(item, list) and item[0][0].strip() == "00a"
    )
    assert "".join(text for text, _style in row).startswith("00a     STAR index")
    assert [style for _text, style in row] == [
        "cyan_bold",
        "normal",
        "value",
        "dim",
        "green",
    ]


def test_action_keys_cannot_override_legacy_navigation(tmp_path, monkeypatch):
    for name in ("stdin", "stdout", "stderr"):
        monkeypatch.setattr(getattr(sys, name), "isatty", lambda: True)
    monkeypatch.setenv("TERM", "xterm")
    with pytest.raises(view.PresentationError, match="navigation"):
        view.watch(
            tmp_path,
            run_root=tmp_path / "run",
            inspect_run=lambda _: None,
            next_action=lambda _: "",
            review_actions=((b"o", "unsafe action collision", lambda: 0),),
        )


def test_no_project_watch_uses_shared_scheduler_discovery(tmp_path, monkeypatch):
    import argparse
    from emrys.orchestration.run_coordinator import control

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EMRYS_DASHBOARD_JOB_ID", raising=False)
    monkeypatch.delenv("EMRYS_DASHBOARD_LOG_DIR", raising=False)
    calls = []
    selected = {
        "job_id": 42,
        "out": str(tmp_path / "out"),
        "err": str(tmp_path / "err"),
    }

    def select(*args):
        calls.append(args)
        return selected

    def watch(project, **kwargs):
        assert project is None and kwargs["raw_job"] is selected
        return 0

    monkeypatch.setattr(view.dashboard, "resolve_selection", select)
    monkeypatch.setattr(view, "watch", watch)
    parser = argparse.ArgumentParser()
    control.configure_inspect_parser(parser)
    assert control.inspect_from_args(parser.parse_args(["--watch"])) == 0
    assert calls == [(None, None, None, None, False)]
    (tmp_path / "project.yaml").symlink_to(tmp_path / "missing")
    assert control.inspect_from_args(parser.parse_args(["--watch"])) == 2
    assert len(calls) == 1


def test_terminal_dashboard_poll_retains_original_date_until_explicit_refresh(
    tmp_path, monkeypatch, watcher
):
    calls, refresh = watcher
    job = {"job_id": 42, "out": str(tmp_path / "out"), "err": str(tmp_path / "err")}
    initial = view.WatchSnapshot(
        None,
        raw_job=job,
        scheduler={"state": "COMPLETED", "terminal": True},
        scheduler_at=NOW,
    )
    query = Mock(return_value={"state": "UNKNOWN", "terminal": False})
    monkeypatch.setattr(view.dashboard._scheduler, "query_slurm", query)
    monkeypatch.setattr(view, "read_tail", lambda *args: None)
    calls.inspect.side_effect = calls.action.side_effect = pytest.fail.Exception(
        "A raw selection cannot admit a Run"
    )
    kept = refresh(initial, verify=False)
    query.assert_not_called()
    assert kept.scheduler_at == NOW and kept.scheduler == initial.scheduler
    fresh = refresh(kept, verify=True)
    assert fresh.scheduler["state"] == "UNKNOWN" and fresh.scheduler_at != NOW
    query.assert_called_once_with(42, job["out"], job["err"])
