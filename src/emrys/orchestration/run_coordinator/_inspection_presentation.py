"""Dated inspection presentation and explicit handoff to CLI-owned actions."""

from __future__ import annotations

import os
import re
import select
import sys
import termios
import threading
import time
import tty
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from emrys.contracts.orchestration.application_model import PROCESSING_STEP_IDS
from . import (
    _submission_inspection,
    dashboard,
    scheduler_observation,
    slurm_submission,
)
from .task import task_attempt_root

if TYPE_CHECKING:
    from .inspection import RunInspection, TaskInspection


_MILESTONE_STEPS = (
    ("Preparation", ("00a", "00b", "00c")),
    ("Alignment and sample processing", ("01", "02", "04", "05", "06")),
    ("QC evidence", ("02b", "03")),
    ("Candidate evidence", ("07", "08")),
    ("Statistical/context processing", ("09", "10")),
)
_TAIL_BYTES = 64 * 1024
_TAIL_LINES = 256
_REFRESH_SECONDS = 30
_MOUSE_TRACKING_ON = "\x1b[?1000h\x1b[?1006h"
_MOUSE_TRACKING_OFF = "\x1b[?1000l\x1b[?1006l"
_VIEW_KEYS = {
    **dict.fromkeys((b"1", b"o", b"O"), "overview"),
    **dict.fromkeys((b"2", b"d", b"D"), "details"),
    **dict.fromkeys((b"3", b"v", b"V"), "evidence"),
}
_SCROLL_DELTAS = {
    b"j": 1,
    b"J": 1,
    b"\x1b[B": 1,
    b"k": -1,
    b"K": -1,
    b"\x1b[A": -1,
    b"\x1b[5~": -6,
    b"\x1b[6~": 6,
}
_TOP_KEYS = (b"g", b"\x1b[H", b"\x1bOH", b"\x1b[1~", b"\x1b[7~")
_BOTTOM_KEYS = (b"G", b"\x1b[F", b"\x1bOF", b"\x1b[4~", b"\x1b[8~")
_ACTION_KEYS = {bytes((value,)) for value in b"odrqvgjk123\t[]"}


class PresentationError(RuntimeError):
    """An inspection cannot be projected into the supported public view."""


@dataclass(frozen=True)
class Navigation:
    view: str = "overview"
    stream_index: int = 0
    scroll: int = 0
    follow: bool = True
    count: str = ""
    search_input: str | None = None
    search_query: str = ""
    search_error: str = ""
    match_line: int | None = None


def fit_navigation(
    state: Navigation, max_scroll: int, matches: tuple[int, ...]
) -> Navigation:
    """Clamp repaint-derived positions without reading or changing selection."""
    return replace(
        state,
        scroll=max_scroll if state.follow else min(state.scroll, max_scroll),
        match_line=state.match_line if state.match_line in matches else None,
    )


def reduce_navigation(
    state: Navigation,
    key: bytes,
    *,
    max_scroll: int,
    matches: tuple[int, ...],
    more_input: bool = False,
    search_result: tuple[tuple[int, ...], str] | None = None,
) -> tuple[Navigation, str | tuple[bool, int] | None]:
    """Apply one key to immutable watch navigation and return any refresh command."""
    if state.search_input is not None:
        if key in (b"\r", b"\n"):
            found, error = search_result or ((), "Search result unavailable")
            candidate = state.search_input or state.search_query
            match = next(
                (line for line in found if line > state.scroll),
                found[0] if found else None,
            )
            return (
                replace(
                    state,
                    search_input=None,
                    search_error=error,
                    search_query=candidate
                    if candidate and not error
                    else state.search_query,
                    match_line=match if not error else None,
                    scroll=min(match, max_scroll)
                    if match is not None
                    else state.scroll,
                    follow=False if match is not None else state.follow,
                ),
                None,
            )
        if key in (b"\x1b", b"\x03"):
            return replace(state, search_input=None), None
        if key in (b"\x7f", b"\b"):
            return replace(state, search_input=state.search_input[:-1]), None
        if len(key) == 1 and 32 <= key[0] <= 126:
            return replace(
                state, search_input=state.search_input + key.decode("ascii")
            ), None
        return state, None
    if key in (b"q", b"Q", b"\x04", b""):
        return state, "quit"
    if key == b"/" and state.view == "evidence":
        return replace(state, search_input="", search_error=""), None
    if (
        state.view == "evidence"
        and len(key) == 1
        and key.isdigit()
        and (state.count or key not in (b"1", b"2", b"3") or more_input)
    ):
        return replace(state, count=state.count + key.decode("ascii")), None
    if state.view == "evidence" and key in (b"n", b"N") and matches:
        anchor = state.scroll if state.match_line is None else state.match_line
        candidates = (
            tuple(line for line in matches if line < anchor)[::-1]
            if key == b"N"
            else tuple(line for line in matches if line > anchor)
        )
        match = (
            candidates[0]
            if candidates
            else (matches[-1] if key == b"N" else matches[0])
        )
        return replace(
            state,
            match_line=match,
            scroll=min(match, max_scroll),
            follow=False,
            count="",
        ), None
    if key in _VIEW_KEYS or key == b"\t":
        view = (
            ("details" if state.view == "overview" else "overview")
            if key == b"\t"
            else _VIEW_KEYS[key]
        )
        return replace(
            state, view=view, scroll=0, follow=view == "evidence", count=""
        ), None
    if key in (b"r", b"R", b"[", b"]"):
        if key in (b"[", b"]"):
            state = replace(
                state,
                stream_index=state.stream_index + (1 if key == b"]" else -1),
                view="evidence",
                scroll=0,
                follow=True,
                search_query="",
                search_error="",
                match_line=None,
            )
        return state, (key in (b"r", b"R"), state.stream_index)
    if key in _SCROLL_DELTAS:
        delta = _SCROLL_DELTAS[key]
        if state.count:
            delta = (1 if delta > 0 else -1) * int(state.count)
        scroll = max(0, state.scroll + delta)
        return replace(
            state, scroll=scroll, follow=scroll >= max_scroll, count=""
        ), None
    if key in _TOP_KEYS:
        return replace(state, scroll=0, follow=max_scroll == 0, count=""), None
    if key in _BOTTOM_KEYS:
        return replace(state, scroll=max_scroll, follow=True, count=""), None
    return state, None


def task_observation(task: TaskInspection) -> str:
    if task.state == "verified":
        return "Verified complete"
    if task.state == "blocked":
        return "Verification not admitted"
    if task.retry_task_attempt_record is not None:
        return "Aborted before publication; retry available"
    if task.start_reference is not None:
        return "Started; completion unverified"
    return "No admitted start"


def reporting_observation(records: Mapping[str, object]) -> str:
    if records["verified"] is not None:
        return "Verified complete"
    if records["start"] is not None:
        return "Started; completion unverified"
    return "No admitted start"


def completion_line(observed: RunInspection) -> str | None:
    """State verified completion without promoting scheduler or log observations."""

    if observed.attempt_outcome != "succeeded" or observed.results_status != "complete":
        return None
    if observed.reporting_status == "complete":
        return "Run complete: scientific Results and reporting are verified."
    if observed.reporting_status == "not applicable":
        return "Run complete: requested scientific work is verified."
    return f"Scientific work complete; reporting is {observed.reporting_status}."


def milestone_progress(
    tasks: tuple[TaskInspection, ...],
    *,
    processing_source_state: str | None = None,
) -> tuple[tuple[str, str, int, int], ...]:
    known_steps = {step for _label, steps in _MILESTONE_STEPS for step in steps}
    unknown = sorted({task.expected.step_id for task in tasks} - known_steps)
    if unknown:
        raise PresentationError(
            "Inspected task Steps have no public milestone: " + ", ".join(unknown)
        )
    result = []
    for label, steps in _MILESTONE_STEPS:
        members = tuple(task for task in tasks if task.expected.step_id in steps)
        if (
            processing_source_state is not None
            and not members
            and set(steps).issubset(PROCESSING_STEP_IDS)
        ):
            state = processing_source_state
        elif not members:
            state = "not applicable"
        elif any(task.state == "blocked" for task in members):
            state = "blocked"
        elif all(task.state == "verified" for task in members):
            state = "complete"
        else:
            state = "incomplete"
        result.append(
            (
                label,
                state,
                sum(task.state == "verified" for task in members),
                len(members),
            )
        )
    return tuple(result)


def attempt_elapsed_line(
    observed: RunInspection, *, now: datetime | None = None
) -> str:
    attempt = observed.latest_attempt
    if attempt is None:
        return "Attempt elapsed: unavailable — no Attempt"
    label = "Current" if observed.attempt_outcome == "running" else "Latest"
    try:
        started = datetime.fromisoformat(
            str(attempt["created_at"]).replace("Z", "+00:00")
        )
        if observed.attempt_outcome == "running":
            finished = datetime.now(UTC) if now is None else now
        elif observed.latest_receipt is not None:
            finished = datetime.fromisoformat(
                str(observed.latest_receipt["finished_at"]).replace("Z", "+00:00")
            )
        else:
            return f"{label} Attempt elapsed: unavailable — no terminal receipt"
        if finished < started:
            raise ValueError("negative Attempt duration")
        seconds = int((finished - started).total_seconds())
    except (KeyError, TypeError, ValueError):
        return f"{label} Attempt elapsed: unavailable — invalid timestamp boundary"
    if started.tzinfo is None or finished.tzinfo is None:
        return f"{label} Attempt elapsed: unavailable — invalid timestamp boundary"
    return f"{label} Attempt elapsed: {timedelta(seconds=seconds)}"


@dataclass(frozen=True)
class RunProjection:
    completion: str | None
    elapsed: str
    milestones: tuple[tuple[str, str, int, int], ...]
    task_counts: tuple[tuple[str, int], ...]
    reporting: tuple[tuple[str, str], ...]


def project_run(
    observed: RunInspection, *, now: datetime | None = None
) -> RunProjection:
    """Derive display semantics only from one already-admitted Run inspection."""
    source_state = (
        None
        if observed.processing_source_run_id is None
        else "reused"
        if observed.processing_source is not None
        else "blocked"
    )
    return RunProjection(
        completion=completion_line(observed),
        elapsed=attempt_elapsed_line(observed, now=now),
        milestones=milestone_progress(
            observed.tasks, processing_source_state=source_state
        ),
        task_counts=tuple(
            Counter(task_observation(task) for task in observed.tasks).items()
        ),
        reporting=tuple(
            (kind, reporting_observation(records))
            for kind, records in (
                observed.reporting_completion_records.items()
                if observed.reporting_status != "not applicable"
                else ()
            )
        ),
    )


def safe_text(value: object) -> str:
    return "".join(
        character if character.isprintable() else ascii(character)[1:-1]
        for character in str(value)
    )


def _safe_log_text(value: str) -> str:
    return "\n".join(safe_text(line) for line in value.split("\n"))


@dataclass(frozen=True)
class StreamSource:
    label: str
    path: Path
    root: Path


@dataclass(frozen=True)
class StreamTail:
    source: StreamSource
    text: str = ""
    state: os.stat_result | None = None
    diagnostic: str = ""
    observed_at: datetime | None = None
    generation_changed: bool = False


def read_tail(source: StreamSource, previous: StreamTail | None = None) -> StreamTail:
    """Project the shared stream owner as one bounded selected tail."""
    state = (
        previous.state if previous is not None and previous.source == source else None
    )
    cache = dashboard.StreamCache(
        source.path,
        root=source.root,
        tail=(_TAIL_BYTES, _TAIL_LINES, _safe_log_text),
        previous_state=state,
    )
    cache.sync()
    cache.close()
    return StreamTail(
        source,
        cache.text(),
        cache.state,
        cache.diagnostic,
        datetime.fromtimestamp(cache.observed_at, UTC)
        if cache.observed_at is not None
        else datetime.now(UTC),
        cache.generation_changed,
    )


@dataclass(frozen=True)
class WatchSnapshot:
    project: Path | None
    raw_job: Mapping[str, object] | None = None
    request: slurm_submission.SubmissionRequestObservation | None = None
    request_at: datetime | None = None
    run_root: Path | None = None
    application: _submission_inspection.SubmissionApplicationObservation | None = None
    run_applications: _submission_inspection.RunApplicationObservation | None = None
    application_at: datetime | None = None
    observed: RunInspection | None = None
    verified_at: datetime | None = None
    verification_error: str = ""
    next_action: str = "Press r to inspect the exact selection."
    scheduler: dict[str, object] | None = None
    scheduler_at: datetime | None = None
    streams: tuple[StreamSource, ...] = ()
    tail: StreamTail | None = None
    workflow: Mapping[str, object] | None = None
    control_identity: Mapping[str, object] | None = None
    trace_at: datetime | None = None
    trace_diagnostics: tuple[str, ...] = ()


def application_outcome_lines(
    observation: _submission_inspection.SubmissionApplicationObservation,
) -> tuple[str, ...]:
    """Describe recorded diagnostics without projecting Run or scheduler outcome."""
    if observation.recorded_outcome is None:
        return ()
    return (
        f"Recorded application outcome: {observation.recorded_outcome}; phase: {observation.recorded_outcome_phase or 'unavailable'}",
    )


def run_application_lines(
    observation: _submission_inspection.RunApplicationObservation,
    *,
    detail: str = "normal",
    include_watch_paths: bool = False,
) -> tuple[str, ...]:
    """Render diagnostic associations without deriving application ownership."""
    lines = [
        f"Run diagnostic logs: {len(observation.logs)} association(s); scan {observation.status}."
    ]
    if detail != "normal" or include_watch_paths:
        lines.append(f"Application log search root: {observation.log_root}")
    for item in observation.logs:
        outcome = application_outcome_lines(item)
        if detail != "normal" or (include_watch_paths and outcome):
            lines.append(f"  {item.application_log}")
        if detail != "normal":
            lines.append(
                f"    {item.status}; recorded {item.recorded_event}; Attempt: {item.workflow_attempt_id or 'none (Run only)'}"
            )
        lines.extend(f"    {line}" for line in outcome)
    lines.extend(f"  {value}" for value in observation.diagnostics[:2])
    return tuple(lines)


def task_stream_sources(
    observed: RunInspection, *, selected_attempt: str | None = None
) -> tuple[StreamSource, ...]:
    """Project admitted terminal references and expected started-Task paths only."""
    sources = {}
    for task in observed.tasks:
        for terminal in task.terminal_attempts:
            record = terminal.record
            if (
                selected_attempt is not None
                and record["workflow_attempt_id"] != selected_attempt
            ):
                continue
            label = f"Task {record['machine_key']}/{record['scope']['scope_id']} ({record['workflow_attempt_id']}; recorded {record['status']})"
            for kind in ("stderr", "stdout"):
                path = observed.run_root / record[kind + "_log"]["path"]
                sources.setdefault(
                    path, StreamSource(label + " " + kind, path, observed.run_root)
                )
        if (
            task.start_origin is None
            or task.start_reference is None
            or (selected_attempt is not None and task.start_origin != selected_attempt)
        ):
            continue
        root = task_attempt_root(
            observed.run_root,
            task.start_origin,
            task.expected.machine_key,
            task.expected.scope_id,
        )
        label = f"Task {task.expected.machine_key}/{task.expected.scope_id} ({task.start_origin}; expected diagnostic from admitted start)"
        for kind in ("stderr", "stdout"):
            path = root / (kind + ".log")
            sources.setdefault(
                path, StreamSource(label + " " + kind, path, observed.run_root)
            )
    return tuple(sources.values())


def _stream_sources(snapshot: WatchSnapshot) -> tuple[StreamSource, ...]:
    sources = []
    if snapshot.raw_job is not None:
        for kind, key in (("stderr", "err"), ("stdout", "out")):
            path = Path(str(snapshot.raw_job[key]))
            sources.append(StreamSource("Scheduler " + kind, path, path.parent))
    request = snapshot.request
    if request is not None and request.context is not None and request.recorded_job_id:
        for kind in ("stderr", "stdout"):
            path = Path(
                str(request.context[f"scheduler_{kind}_pattern"]).replace(
                    "%j", request.recorded_job_id
                )
            )
            sources.append(StreamSource("Scheduler " + kind, path, path.parent))
    application = snapshot.application
    if application is not None and application.application_log is not None:
        sources.append(
            StreamSource(
                "Application",
                application.application_log,
                Path(str(request.context["application_log_root"])),
            )
        )
    if snapshot.run_applications is not None:
        sources.extend(
            StreamSource(
                f"Application {item.application_log.parent.name} ({item.workflow_attempt_id or 'Run only'})",
                item.application_log,
                snapshot.run_applications.log_root,
            )
            for item in snapshot.run_applications.logs
        )
    observed = snapshot.observed
    if observed is not None:
        selected_attempt = (
            None if application is None else application.workflow_attempt_id
        )
        sources.extend(task_stream_sources(observed, selected_attempt=selected_attempt))
    return tuple(sources)


def refresh_snapshot(
    snapshot: WatchSnapshot,
    *,
    verify: bool,
    stream_index: int,
    inspect_run: Callable[[Path], RunInspection],
    next_action: Callable[[RunInspection], str],
    stream_caches: dict[str, dashboard.StreamCache] | None = None,
    offline: bool = False,
    trace_closed: threading.Event | None = None,
) -> WatchSnapshot:
    """Only this worker boundary reads observations; rendering uses its result."""
    if verify and snapshot.raw_job is None:
        try:
            if snapshot.request is not None:
                previous = snapshot.request
                request = slurm_submission.select_submission_request(
                    snapshot.project, str(previous.request_root)
                )
                if (
                    previous.context is not None and request.context != previous.context
                ) or (
                    previous.recorded_job_id is not None
                    and (request.recorded_job_id, request.recorded_cluster)
                    != (previous.recorded_job_id, previous.recorded_cluster)
                ):
                    raise PresentationError(
                        "Selected request context or confirmed response changed; preserve the records and select explicitly again"
                    )
                snapshot = replace(
                    snapshot, request=request, request_at=datetime.now(UTC)
                )
                application = _submission_inspection.inspect_submission_application(
                    snapshot.request
                )
                snapshot = replace(
                    snapshot,
                    application=application,
                    application_at=datetime.now(UTC),
                    run_root=application.run_root,
                )
            elif snapshot.run_applications is not None:
                snapshot = replace(
                    snapshot,
                    run_applications=_submission_inspection.inspect_run_applications(
                        snapshot.project,
                        snapshot.run_root,
                        snapshot.run_applications.log_root,
                    ),
                    application_at=datetime.now(UTC),
                )
            observed = (
                None if snapshot.run_root is None else inspect_run(snapshot.run_root)
            )
            snapshot = replace(
                snapshot,
                observed=observed,
                verified_at=datetime.now(UTC),
                verification_error="",
                next_action=(
                    "Press r to check this request for recorded preparation and Run association."
                    if observed is None
                    else next_action(observed)
                ),
            )
        except Exception as exc:
            snapshot = replace(
                snapshot,
                observed=None,
                application=None
                if snapshot.request is not None
                else snapshot.application,
                application_at=None
                if snapshot.request is not None or snapshot.run_applications is not None
                else snapshot.application_at,
                run_applications=None
                if snapshot.run_applications is None
                else replace(
                    snapshot.run_applications,
                    logs=(),
                    status="unknown",
                    diagnostics=(str(exc)[:4096],),
                ),
                verified_at=None,
                verification_error=safe_text(str(exc)[:4096]),
                next_action="Preserve retained evidence; inspect again when available.",
            )
    retained_terminal = not verify and bool(
        snapshot.scheduler and snapshot.scheduler.get("terminal")
    )
    scheduler = (
        snapshot.scheduler
        if retained_terminal
        else (
            {
                "state": "UNKNOWN",
                "terminal": False,
                "reason": "Offline; scheduler not queried",
            }
            if offline
            else scheduler_observation.observe_job(
                snapshot.raw_job["job_id"],
                snapshot.raw_job["out"],
                snapshot.raw_job["err"],
                include_resources=True,
            )
            if snapshot.raw_job is not None
            else scheduler_observation.unknown_observation(
                "No exact submission selected; recorded Run job IDs are not a current binding"
            )
            if snapshot.request is None
            else slurm_submission.observe_submission_request(
                snapshot.request,
                include_resources=True,
            )
        )
    )
    scheduler_at = (
        snapshot.scheduler_at
        if retained_terminal
        else (
            datetime.fromisoformat(str(scheduler["observed_at"]))
            if scheduler.get("observed_at")
            else datetime.now(UTC)
        )
    )
    streams = _stream_sources(snapshot)
    if stream_caches is not None:
        traces = {}
        diagnostics = []
        dates = []
        for source in streams:
            if trace_closed is not None and trace_closed.is_set():
                break
            if source.label not in ("Scheduler stdout", "Scheduler stderr"):
                continue
            cache = stream_caches.setdefault(
                str(source.path), dashboard.StreamCache(str(source.path))
            )
            if trace_closed is not None and trace_closed.is_set():
                cache.close()
                break
            cache.sync()
            traces[source.label] = cache.text()
            diagnostics.append(f"{source.label}: {cache.diagnostic}")
            if cache.observed_at is not None:
                dates.append(datetime.fromtimestamp(cache.observed_at, UTC))
        snapshot = replace(
            snapshot,
            workflow=dashboard.parse_workflow(traces.get("Scheduler stderr", "")),
            control_identity=dashboard.parse_identity(
                traces.get("Scheduler stdout", "")
            ),
            trace_at=min(dates) if len(dates) == 2 else None,
            trace_diagnostics=tuple(diagnostics),
        )
    tail = (
        None
        if not streams
        else read_tail(streams[stream_index % len(streams)], snapshot.tail)
    )
    return replace(
        snapshot,
        scheduler=scheduler,
        streams=streams,
        tail=tail,
        scheduler_at=scheduler_at,
    )


class RefreshWorker:
    """One daemon reader and one coalesced pending refresh; close never joins I/O."""

    def __init__(self, snapshot: WatchSnapshot, refresh: Callable[..., WatchSnapshot]):
        self.snapshot = snapshot
        self.refresh = refresh
        self.condition = threading.Condition()
        self.pending: tuple[bool, int] | None = None
        self.closed = False
        self.busy = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def request(self, *, verify: bool, stream_index: int) -> None:
        with self.condition:
            if not self.closed:
                self.pending = (
                    verify or bool(self.pending and self.pending[0]),
                    stream_index,
                )
                self.condition.notify()

    def _run(self) -> None:
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.pending is not None)
                if self.closed:
                    return
                verify, stream_index = self.pending
                self.pending = None
                self.busy = True
            try:
                result = self.refresh(
                    self.snapshot, verify=verify, stream_index=stream_index
                )
            except Exception as exc:
                result = replace(
                    self.snapshot,
                    scheduler=slurm_submission.scheduler_observation.unknown_observation(
                        safe_text(str(exc)[:4096])
                    ),
                    tail=None,
                    scheduler_at=datetime.now(UTC),
                )
            with self.condition:
                self.snapshot = result
                self.busy = False

    def close(self) -> None:
        with self.condition:
            self.closed = True
            self.pending = None
            self.condition.notify()


def render_snapshot(
    snapshot: WatchSnapshot, *, now: datetime, tail_lines: int = _TAIL_LINES
) -> str:
    """Literal display only: no filesystem, scheduler, association or hash reads."""
    lines = ["EMRYS inspection — read-only"]
    if snapshot.project is not None:
        lines.append(f"Project: {snapshot.project}")
    if snapshot.raw_job is not None:
        lines.append(
            f"Scheduler job: {snapshot.raw_job['job_id']}; diagnostic selection only"
        )
    if snapshot.request is not None:
        lines.extend(
            (
                f"Request: {snapshot.request.request_root.name}",
                f"Recorded job: {snapshot.request.recorded_job_id or 'unconfirmed'}; request admission as of {snapshot.request_at or 'unavailable'}",
            )
        )
    scheduler = snapshot.scheduler or {"state": "QUERYING"}
    lines.append(
        f"Scheduler: {scheduler['state']} ({scheduler.get('source', 'unavailable')}); observed {snapshot.scheduler_at or 'not yet'}"
    )
    for name in (
        "cluster",
        "reason",
        "exit_code",
        "diagnostic",
        "elapsed",
        "left",
        "time_limit",
        "cpus",
        "partition",
        "node",
        "max_rss",
        "disk_read",
        "disk_write",
        "ave_cpu",
        "usage_observed_at",
        "usage_diagnostic",
    ):
        if scheduler.get(name) is not None:
            lines.append(f"  {name}: {scheduler[name]}")
    lines.extend(snapshot.trace_diagnostics)
    if snapshot.workflow is not None:
        lines.append(
            f"Diagnostic trace as of {snapshot.trace_at or 'unavailable'}; parsed log progress is unverified"
        )
    application = snapshot.application
    if application is not None:
        lines.append(
            f"Application association as of {snapshot.application_at or 'unavailable'}: {application.status}; selected Attempt: {application.workflow_attempt_id or 'unavailable'}"
        )
        if application.recorded_event:
            lines.append(
                f"Recorded preparation: {application.recorded_event}; candidate Run: {application.recorded_run_id or 'none'}"
            )
        lines.extend(application_outcome_lines(application))
        lines.extend(f"  {value}" for value in application.diagnostics[:2])
    if snapshot.run_applications is not None:
        lines.append(
            f"Run log associations as of: {snapshot.application_at or 'unavailable'}"
        )
        lines.extend(
            run_application_lines(snapshot.run_applications, include_watch_paths=True)
        )
    observed = snapshot.observed
    lines.append(
        f"Run evidence as of: {snapshot.verified_at or 'unavailable'}; changes require r"
    )
    if snapshot.verification_error:
        lines.append("Verification unavailable: " + snapshot.verification_error)
    if observed is not None:
        latest = observed.latest_attempt
        projection = project_run(observed, now=snapshot.verified_at or now)
        lines.append(
            f"Run: {observed.run_id}; latest Attempt: {'none' if latest is None else latest['workflow_attempt_id']}"
        )
        lines.append(
            f"Admission: {observed.integrity}; lock: {observed.lock_observation}; outcome: {observed.attempt_outcome}"
        )
        lines.append(
            projection.elapsed + " (latest Run Attempt; elapsed at dated verification)"
        )
        if completion := projection.completion:
            lines.append(completion)
        lines.extend(
            f"  {label}: {state} ({verified}/{total} verified)"
            for label, state, verified, total in projection.milestones
        )
        lines.append(
            "Tasks: "
            + "; ".join(f"{label}: {count}" for label, count in projection.task_counts)
        )
        outcomes = Counter(
            item.record["status"]
            for task in observed.tasks
            for item in task.terminal_attempts
        )
        lines.append(
            f"Recorded Task outcomes: {dict(outcomes)}; not verified completion"
        )
        lines.append(
            f"Results: {observed.results_status}; reporting: {observed.reporting_status}"
        )
        if observed.reporting_status != "not applicable":
            lines.extend(f"  {kind}: {state}" for kind, state in projection.reporting)
    lines.append("Next supported action at last verification: " + snapshot.next_action)
    if snapshot.tail is not None:
        lines.extend(
            (
                f"Stream: {snapshot.tail.source.label}: {snapshot.tail.source.path}",
                f"Tail observed {snapshot.tail.observed_at or 'unavailable'}: {snapshot.tail.diagnostic}",
            )
        )
        # The suffix was already escaped line by line; retain only its line separators.
        return (
            "\n".join(safe_text(line) for line in lines)
            + "\n"
            + "\n".join(snapshot.tail.text.split("\n")[-tail_lines:])
        )
    return "\n".join(safe_text(line) for line in lines)


def render_dashboard(
    snapshot, *, height, width, view, scroll, refresh_seconds=_REFRESH_SECONDS
):
    """Render the shared overview/detail projection without reading any source."""
    job = snapshot.raw_job
    job_id = (
        job["job_id"]
        if job is not None
        else (
            snapshot.request.recorded_job_id
            if snapshot.request is not None
            else "unbound"
        )
    )
    workflow = snapshot.workflow or dashboard.parse_workflow("")
    identity = dict(snapshot.control_identity or {})
    if snapshot.observed is not None:
        if completion := completion_line(snapshot.observed):
            identity["verified_status"] = completion
        if snapshot.observed.results_status == "complete":
            workflow = {
                **workflow,
                "active": {},
                "done": dict(workflow["done"]),
                "expected": dict(workflow["expected"]),
            }
            counts = Counter(task.expected.step_id for task in snapshot.observed.tasks)
            for key in dashboard.STAGE_BY_KEY:
                if key not in {"REPORT", "FINAL"}:
                    workflow["expected"][key] = counts.get(key, 0)
                    workflow["done"][key] = counts.get(key, 0)
            if snapshot.observed.reporting_status in {"complete", "not applicable"}:
                workflow["expected"]["REPORT"] = int(
                    snapshot.observed.reporting_status == "complete"
                )
                workflow["done"]["REPORT"] = workflow["expected"]["REPORT"]
                workflow["expected"]["FINAL"] = 1
                workflow["done"]["FINAL"] = 1
    model = dashboard.dashboard_view(
        job_id,
        snapshot.scheduler or {"state": "QUERYING"},
        identity,
        workflow,
        height=height,
        width=width,
        view=view,
        work_scroll=scroll,
        footer=(
            "NFS-light %ss (%s)"
            % (
                refresh_seconds,
                "unavailable"
                if snapshot.trace_at is None
                else "%ss ago"
                % max(
                    0,
                    int((datetime.now(UTC) - snapshot.trace_at).total_seconds()),
                ),
            ),
            "dim",
        ),
    )
    from itertools import groupby
    from rich.text import Text

    styles = {
        "normal": "",
        "dim": "dim",
        "border": "dim cyan",
        "label": "bold cyan",
        "value": "bold",
        "title": "bold cyan",
        "panel_title": "bold magenta",
        "green": "green",
        "green_bold": "bold green",
        "cyan_bold": "bold cyan",
        "yellow": "yellow",
        "yellow_bold": "bold yellow",
        "red": "red",
        "cyan": "cyan",
    }
    result = Text()
    for row in dashboard.render_view(model):
        for style, cells in groupby(row, key=lambda cell: cell[1]):
            result.append(
                "".join(character for character, _ in cells),
                style=styles.get(style) or None,
            )
        result.append("\n")
    return result


def render_watch_text(snapshot, *, now):
    """Color dated evidence and log severity without interpreting or hiding text."""
    from rich.text import Text

    result = Text(render_snapshot(snapshot, now=now))
    result.highlight_regex(r"(?m)^EMRYS inspection — read-only$", "bold cyan")
    result.highlight_regex(
        r"(?m)^(?:  )?(?:Project|Scheduler job|Request|Recorded job|Scheduler|"
        r"Diagnostic trace as of|Application association as of|Recorded preparation|"
        r"Run evidence as of|Attempt|Scientific Results|Reporting|Recovery available|"
        r"Verified reports|Tasks|Recorded Task outcomes|Results|"
        r"Next supported action at last verification|Stream|Tail observed|cluster|"
        r"reason|exit_code|diagnostic|elapsed|left|time_limit|cpus|partition|node|"
        r"max_rss|disk_read|disk_write|ave_cpu|usage_observed_at|usage_diagnostic):",
        "bold cyan",
    )
    for pattern, style in (
        (
            r"(?m)^\s*\[(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+|"
            r"20\d\d-\d\d-\d\d)[^\]\n]{0,70}\]",
            "dim",
        ),
        (r"(?im)^\s*(?:\[[^\]\n]{1,80}\]\s*)?20\d\d-\d\d-\d\d(?:T|\s)\S+", "dim"),
        (
            r"(?im)\b(?:ERROR|FATAL|WorkflowError|Traceback|Exception)(?=\b|:)",
            "bold red",
        ),
        (r"(?im)\b(?:Error in rule|Exiting because a job execution failed)\b", "red"),
        (r"(?im)\b(?:WARNING|WARN)(?=\b|:)", "bold yellow"),
        (r"(?im)\b(?:INFO|DEBUG)(?=\b|:)", "cyan"),
        (r"(?im)\b(?:rule|localrule|checkpoint)\s+[A-Za-z0-9_.-]+:", "cyan"),
        (r"(?im)\bFinished jobid:\s*\d+", "green"),
        (r"(?im)\b\d+ of \d+ steps \(100%\) done\b", "bold green"),
        (r"(?im)\b\d+ of \d+ steps \((?!100%)\d+%\) done\b", "cyan"),
        (r"(?i)\"(?:level|severity)\"\s*:", "bold cyan"),
        (r"(?i)\"(?:error|fatal)\"(?=\s*[,}])", "bold red"),
        (r"(?i)\"(?:warning|warn)\"(?=\s*[,}])", "bold yellow"),
        (r"(?i)\"(?:info|debug)\"(?=\s*[,}])", "cyan"),
    ):
        result.highlight_regex(pattern, style)
    return result


def _render_log_rows(snapshot, *, now, query=""):
    """Number and search only the sanitized, bounded stream tail."""
    from rich.text import Text

    rows = render_watch_text(snapshot, now=now).split("\n", allow_blank=True)
    if snapshot.tail is None:
        return rows, (), ""
    tail_rows = snapshot.tail.text.split("\n")
    first = max(0, len(rows) - len(tail_rows))
    pattern = None
    if query:
        try:
            pattern = re.compile(query)
        except re.error as exc:
            return rows, (), f"Invalid search pattern: {safe_text(exc)}"
    matches = []
    width = max(3, len(str(len(tail_rows))))
    for tail_index, row_index in enumerate(range(first, len(rows)), start=1):
        row = rows[row_index]
        if pattern is not None and pattern.search(row.plain):
            matches.append(row_index)
            row.highlight_regex(pattern, "bold black on yellow")
        rows[row_index] = Text(f"{tail_index:>{width}} ", style="dim") + row
    return rows, tuple(matches), ""


def _read_watch_key(descriptor: int) -> bytes | None:
    """Read one navigation key and consume SGR mouse reports without acting."""
    key = os.read(descriptor, 1)
    if key != b"\x1b":
        return key
    while len(key) < 64 and select.select([descriptor], [], [], 0.01)[0]:
        key += os.read(descriptor, 1)
        if key.startswith(b"\x1b[<"):
            if key[-1:] in b"Mm":
                return None
        elif key[-1:] in b"ABCDHF~":
            break
    return key


def require_action_terminal() -> None:
    if not all(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr)) or (
        os.environ.get("TERM") == "dumb"
    ):
        raise PresentationError("Actions require an interactive watch")


def watch(
    project: Path | None,
    *,
    request: slurm_submission.SubmissionRequestObservation | None = None,
    run_root: Path | None = None,
    application_log_root: Path | None = None,
    inspect_run: Callable[[Path], RunInspection],
    next_action: Callable[[RunInspection], str],
    review_actions: tuple[tuple[bytes, str, Callable[[], int]], ...] = (),
    raw_job: Mapping[str, object] | None = None,
    offline: bool = False,
    refresh_seconds: int = _REFRESH_SECONDS,
    snapshot_only: bool = False,
) -> int:
    from functools import partial

    if refresh_seconds < 5:
        raise PresentationError("--refresh must be at least 5 seconds")
    if raw_job is not None and (
        project is not None
        or request is not None
        or run_root is not None
        or review_actions
    ):
        raise PresentationError(
            "A scheduler diagnostic selection has no Project, Run or action authority"
        )
    stream_caches = {}
    trace_closed = threading.Event()
    refresh = partial(
        refresh_snapshot,
        inspect_run=inspect_run,
        next_action=next_action,
        stream_caches=stream_caches,
        offline=offline,
        trace_closed=trace_closed,
    )
    if application_log_root is not None and (request is not None or run_root is None):
        raise PresentationError("A log search root requires an explicit Run selection")
    initial = WatchSnapshot(
        project,
        raw_job=raw_job,
        request=request,
        run_root=run_root,
        run_applications=None
        if application_log_root is None
        else _submission_inspection.RunApplicationObservation(application_log_root),
    )
    interactive = (
        not snapshot_only
        and sys.stdin.isatty()
        and sys.stdout.isatty()
        and os.environ.get("TERM") != "dumb"
    )
    if review_actions:
        require_action_terminal()
        if snapshot_only:
            raise PresentationError("Actions require an interactive watch")
        if any(key.lower() in _ACTION_KEYS for key, _, _ in review_actions):
            raise PresentationError("Actions cannot replace dashboard navigation keys")
        if (request is None) == (run_root is None):
            raise PresentationError("Actions require one exact Run or submission")
    if not interactive:
        try:
            observed = refresh(initial, verify=True, stream_index=0)
        finally:
            trace_closed.set()
            for cache in tuple(stream_caches.values()):
                cache.close()
        from rich.console import Console

        if observed.workflow is not None:
            Console(no_color=True, force_terminal=False, width=100).print(
                render_dashboard(
                    observed, height=56, width=100, view="details", scroll=0
                )
            )
        print(
            render_snapshot(
                observed,
                now=datetime.now(UTC),
                tail_lines=8,
            )
        )
        return 0
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text

    console = Console(markup=False, highlight=False, no_color="NO_COLOR" in os.environ)
    descriptor = sys.stdin.fileno()
    original = termios.tcgetattr(descriptor)
    worker = RefreshWorker(initial, refresh)
    max_scroll = 0
    matches = ()
    navigation = Navigation(
        view="evidence" if run_root is not None and request is None else "overview"
    )
    selected_review = None
    observed_tail_generation = None
    reviews = {key: callback for key, _label, callback in review_actions}
    deadline = time.monotonic() + refresh_seconds
    worker.request(verify=True, stream_index=navigation.stream_index)
    mouse_tracking = False
    try:
        tty.setcbreak(descriptor)
        sys.stdout.write(_MOUSE_TRACKING_ON)
        sys.stdout.flush()
        mouse_tracking = True
        with Live(
            console=console,
            screen=True,
            auto_refresh=False,
            redirect_stdout=False,
            redirect_stderr=False,
        ) as live:
            layout = Layout()
            layout.split_column(
                Layout(name="body"), Layout(name="controls", size=5 if reviews else 4)
            )
            while True:
                now = time.monotonic()
                if now >= deadline:
                    worker.request(verify=False, stream_index=navigation.stream_index)
                    deadline = now + refresh_seconds
                snapshot = worker.snapshot
                tail = snapshot.tail
                if (
                    tail is not None
                    and tail.generation_changed
                    and tail.state is not None
                ):
                    generation = (
                        str(tail.source.path),
                        tail.state.st_dev,
                        tail.state.st_ino,
                        tail.state.st_size,
                        tail.state.st_mtime_ns,
                        tail.state.st_ctime_ns,
                    )
                    if generation != observed_tail_generation:
                        navigation = replace(
                            navigation,
                            scroll=0,
                            follow=True,
                            count="",
                            search_input=None,
                            search_query="",
                            search_error="",
                            match_line=None,
                        )
                        observed_tail_generation = generation
                controls = "Views: [1] Overview | [2] Details | [3] Logs | Tab switch | [/] stream | Scroll: arrows/j/k PgUp/PgDn Home/g | r recheck selection/evidence (read-only) | q quit"
                controls += f"\nDiagnostic trace: {snapshot.trace_at or 'unavailable'} (unverified log identity/progress) | Scheduler: {snapshot.scheduler_at or 'unavailable'}"
                if navigation.view == "evidence":
                    state = "FOLLOWING" if navigation.follow else "PAUSED"
                    search = (
                        f"/{navigation.search_input}"
                        if navigation.search_input is not None
                        else f"/{navigation.search_query}"
                        if navigation.search_query
                        else "none"
                    )
                    stream_count = len(snapshot.streams)
                    stream_number = (
                        navigation.stream_index % stream_count + 1
                        if stream_count
                        else 0
                    )
                    stream_label = (
                        tail.source.label if tail is not None else "unavailable"
                    )
                    controls += (
                        f"\nLog stream: {stream_number}/{stream_count} {stream_label} | "
                        f"State: {state} | Lines: tail-relative | Search: {search} | "
                        "Keys: count+j/k, G bottom, / search, n/N matches"
                    )
                    if navigation.count:
                        controls += f" | Count: {navigation.count}"
                    if navigation.search_error:
                        controls += f" | {navigation.search_error}"
                if reviews:
                    controls += "\nLeave view: " + " | ".join(
                        f"{key.decode('ascii')} {label}"
                        for key, label, _ in review_actions
                    )
                if worker.busy or worker.pending is not None:
                    controls += (
                        "\nRefresh in progress; displayed observations are dated"
                    )
                controls_text = Text(controls, style="dim")
                controls_text.highlight_regex(
                    r"(?m)^(?:Views|Diagnostic trace|Log stream|Leave view):",
                    "bold cyan",
                )
                controls_text.highlight_regex(
                    r"(?<=\| )(?:Scheduler|State|Lines|Search|Keys|Count):",
                    "bold cyan",
                )
                controls_text.highlight_regex(r"\[(?:1|2|3|/)\]", "bold cyan")
                selected_view = navigation.view.replace("evidence", "logs").title()
                controls_text.highlight_regex(
                    rf"(?<=\] ){selected_view}\b", "bold white"
                )
                controls_text.highlight_regex(r"\bFOLLOWING\b", "bold green")
                controls_text.highlight_regex(r"\bPAUSED\b", "bold yellow")
                layout["controls"].size = min(
                    console.size.height - 1,
                    max(
                        1,
                        sum(
                            max(
                                1,
                                (len(line) + console.size.width - 1)
                                // console.size.width,
                            )
                            for line in controls.splitlines()
                        ),
                    ),
                )
                if navigation.view == "evidence":
                    rows, matches, render_error = _render_log_rows(
                        snapshot, now=datetime.now(UTC), query=navigation.search_query
                    )
                    if render_error:
                        navigation = replace(navigation, search_error=render_error)
                    body_height = max(1, console.size.height - layout["controls"].size)
                    max_scroll = max(0, len(rows) - body_height)
                    navigation = fit_navigation(navigation, max_scroll, matches)
                    layout["body"].update(Text("\n").join(rows[navigation.scroll :]))
                else:
                    layout["body"].update(
                        render_dashboard(
                            snapshot,
                            height=max(
                                1, console.size.height - layout["controls"].size
                            ),
                            width=console.size.width,
                            view=navigation.view,
                            scroll=navigation.scroll,
                            refresh_seconds=refresh_seconds,
                        )
                    )
                layout["controls"].update(controls_text)
                live.update(layout, refresh=True)
                if select.select([descriptor], [], [], 1)[0]:
                    key = _read_watch_key(descriptor)
                    if key is None:
                        continue
                    selected_review = (
                        None
                        if navigation.search_input is not None
                        else reviews.get(key.lower())
                    )
                    if selected_review is not None:
                        break
                    search_result = None
                    if navigation.search_input is not None and key in (b"\r", b"\n"):
                        candidate = navigation.search_input or navigation.search_query
                        _rows, found, error = _render_log_rows(
                            snapshot, now=datetime.now(UTC), query=candidate
                        )
                        search_result = found, error
                    more_input = bool(
                        navigation.search_input is None
                        and navigation.view == "evidence"
                        and len(key) == 1
                        and key.isdigit()
                        and select.select([descriptor], [], [], 0.15)[0]
                    )
                    navigation, command = reduce_navigation(
                        navigation,
                        key,
                        max_scroll=max_scroll,
                        matches=matches,
                        more_input=more_input,
                        search_result=search_result,
                    )
                    if command == "quit":
                        return 0
                    if isinstance(command, tuple):
                        verify, stream_index = command
                        worker.request(verify=verify, stream_index=stream_index)
    except KeyboardInterrupt:
        return 0
    finally:
        if mouse_tracking:
            sys.stdout.write(_MOUSE_TRACKING_OFF)
            sys.stdout.flush()
        trace_closed.set()
        worker.close()
        for cache in tuple(stream_caches.values()):
            cache.close()
        termios.tcflush(descriptor, termios.TCIFLUSH)
        termios.tcsetattr(descriptor, termios.TCSADRAIN, original)
    # An active daemon read may finish, but no queued refresh or cached evidence
    # participates in the CLI operation. Its owner admits a fresh review.
    assert selected_review is not None
    return selected_review()
