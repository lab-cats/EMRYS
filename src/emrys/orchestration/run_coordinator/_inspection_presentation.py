"""Dated inspection presentation and explicit handoff to CLI-owned actions."""

from __future__ import annotations

import os
import select
import stat
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
from emrys.libraries.validation.inputs import read_suffix_with_identity
from . import _submission_inspection, slurm_submission

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


class PresentationError(RuntimeError):
    """An inspection cannot be projected into the supported public view."""


def task_observation(task: TaskInspection) -> str:
    if task.state == "verified":
        return "Verified complete"
    if task.state == "blocked":
        return "Verification not admitted"
    if task.start_reference is not None:
        return "Started; completion unverified"
    return "No admitted start"


def reporting_observation(records: Mapping[str, object]) -> str:
    if records["verified"] is not None:
        return "Verified complete"
    if records["start"] is not None:
        return "Started; completion unverified"
    return "No admitted start"


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


def safe_text(value: object) -> str:
    return "".join(
        character if character.isprintable() else ascii(character)[1:-1]
        for character in str(value)
    )


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


def _ancestors(source: StreamSource) -> dict[Path, tuple[int, ...]]:
    path, root = source.path, source.root
    if (
        not path.is_absolute()
        or not path.is_relative_to(root)
        or path.resolve() != path
    ):
        raise PresentationError(
            "Stream path is not canonical beneath its admitted root"
        )
    result = {}
    for parent in path.parents:
        state = parent.lstat()
        if not stat.S_ISDIR(state.st_mode) or (
            (parent == root or parent.is_relative_to(root))
            and state.st_uid != os.getuid()
        ):
            raise PresentationError("Stream ancestor is not a real owned directory")
        result[parent] = (state.st_dev, state.st_ino, state.st_mode, state.st_uid)
    return result


def read_tail(source: StreamSource, previous: StreamTail | None = None) -> StreamTail:
    """Read current diagnostic bytes; never inherit a prior content reference."""
    try:
        ancestors = _ancestors(source)
        before = source.path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid():
            raise PresentationError("Stream is not a regular owned file")
        data, state = read_suffix_with_identity(
            source.path, "Diagnostic stream", _TAIL_BYTES
        )
        if (before.st_dev, before.st_ino, before.st_uid) != (
            state.st_dev,
            state.st_ino,
            state.st_uid,
        ) or ancestors != _ancestors(source):
            raise PresentationError("Stream or ancestor changed while read")
        diagnostic = "Current diagnostic bytes; content not verified"
        if (
            previous is not None
            and previous.source == source
            and previous.state is not None
        ):
            old = previous.state
            if (old.st_dev, old.st_ino) != (state.st_dev, state.st_ino):
                diagnostic += "; replaced since previous observation"
            elif state.st_size < old.st_size:
                diagnostic += "; truncated since previous observation"
        lines = data.decode("utf-8", "replace").split("\n")
        text = "\n".join(safe_text(line) for line in lines[-_TAIL_LINES:])
        return StreamTail(source, text, state, diagnostic, datetime.now(UTC))
    except (OSError, ValueError, RuntimeError) as exc:
        return StreamTail(
            source,
            diagnostic="Unavailable: " + safe_text(str(exc)[:4096]),
            observed_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class WatchSnapshot:
    project: Path
    request: slurm_submission.SubmissionRequestObservation | None = None
    request_at: datetime | None = None
    run_root: Path | None = None
    application: _submission_inspection.SubmissionApplicationObservation | None = None
    application_at: datetime | None = None
    observed: RunInspection | None = None
    verified_at: datetime | None = None
    verification_error: str = ""
    next_action: str = "Press r to inspect the exact selection."
    scheduler: dict[str, object] | None = None
    scheduler_at: datetime | None = None
    streams: tuple[StreamSource, ...] = ()
    tail: StreamTail | None = None


def _stream_sources(snapshot: WatchSnapshot) -> tuple[StreamSource, ...]:
    sources = []
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
    observed = snapshot.observed
    if observed is not None:
        selected_attempt = (
            None if application is None else application.workflow_attempt_id
        )
        for task in observed.tasks:
            for terminal in task.terminal_attempts:
                record = terminal.record
                if (
                    selected_attempt is not None
                    and record["workflow_attempt_id"] != selected_attempt
                ):
                    continue
                label = f"Task {record['machine_key']}/{record['scope']['scope_id']} ({record['workflow_attempt_id']})"
                for kind in ("stderr", "stdout"):
                    sources.append(
                        StreamSource(
                            label + " " + kind,
                            observed.run_root / record[kind + "_log"]["path"],
                            observed.run_root,
                        )
                    )
    return tuple(sources)


def refresh_snapshot(
    snapshot: WatchSnapshot,
    *,
    verify: bool,
    stream_index: int,
    inspect_run: Callable[[Path], RunInspection],
    next_action: Callable[[RunInspection], str],
) -> WatchSnapshot:
    """Only this worker boundary reads observations; rendering uses its result."""
    if verify:
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
                if snapshot.request is not None
                else snapshot.application_at,
                verified_at=None,
                verification_error=safe_text(str(exc)[:4096]),
                next_action="Preserve retained evidence; inspect again when available.",
            )
    scheduler = (
        slurm_submission.scheduler_observation.unknown_observation(
            "No exact submission selected; recorded Run job IDs are not a current binding"
        )
        if snapshot.request is None
        else slurm_submission.observe_submission_request(snapshot.request)
    )
    scheduler_at = datetime.now(UTC)
    streams = _stream_sources(snapshot)
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
    lines = ["EMRYS inspection — read-only", f"Project: {snapshot.project}"]
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
    for name in ("cluster", "reason", "exit_code", "diagnostic"):
        if scheduler.get(name) is not None:
            lines.append(f"  {name}: {scheduler[name]}")
    application = snapshot.application
    if application is not None:
        lines.append(
            f"Application association as of {snapshot.application_at or 'unavailable'}: {application.status}; selected Attempt: {application.workflow_attempt_id or 'unavailable'}"
        )
        if application.recorded_event:
            lines.append(
                f"Recorded preparation: {application.recorded_event}; candidate Run: {application.recorded_run_id or 'none'}"
            )
        lines.extend(f"  {value}" for value in application.diagnostics[:2])
    observed = snapshot.observed
    lines.append(
        f"Run evidence as of: {snapshot.verified_at or 'unavailable'}; changes require r"
    )
    if snapshot.verification_error:
        lines.append("Verification unavailable: " + snapshot.verification_error)
    if observed is not None:
        latest = observed.latest_attempt
        lines.append(
            f"Run: {observed.run_id}; latest Attempt: {'none' if latest is None else latest['workflow_attempt_id']}"
        )
        lines.append(
            f"Admission: {observed.integrity}; lock: {observed.lock_observation}; outcome: {observed.attempt_outcome}"
        )
        lines.append(
            attempt_elapsed_line(observed, now=snapshot.verified_at or now)
            + " (latest Run Attempt; elapsed at dated verification)"
        )
        milestones = milestone_progress(
            observed.tasks,
            processing_source_state=None
            if observed.processing_source_run_id is None
            else "reused"
            if observed.processing_source is not None
            else "blocked",
        )
        lines.extend(
            f"  {label}: {state} ({verified}/{total} verified)"
            for label, state, verified, total in milestones
        )
        counts = Counter(task_observation(task) for task in observed.tasks)
        lines.append(
            "Tasks: "
            + "; ".join(f"{label}: {count}" for label, count in counts.items())
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
            lines.extend(
                f"  {kind}: {reporting_observation(records)}"
                for kind, records in observed.reporting_completion_records.items()
            )
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


def require_action_terminal() -> None:
    if not all(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr)) or (
        os.environ.get("TERM") == "dumb"
    ):
        raise PresentationError("Actions require an interactive Run-only watch")


def watch(
    project: Path,
    *,
    request: slurm_submission.SubmissionRequestObservation | None = None,
    run_root: Path | None = None,
    inspect_run: Callable[[Path], RunInspection],
    next_action: Callable[[RunInspection], str],
    review_resume: Callable[[], int] | None = None,
) -> int:
    from functools import partial

    refresh = partial(
        refresh_snapshot, inspect_run=inspect_run, next_action=next_action
    )
    initial = WatchSnapshot(project, request=request, run_root=run_root)
    interactive = (
        sys.stdin.isatty() and sys.stdout.isatty() and os.environ.get("TERM") != "dumb"
    )
    if review_resume is not None:
        require_action_terminal()
        if request is not None or run_root is None:
            raise PresentationError("Actions require an interactive Run-only watch")
    if not interactive:
        print(
            render_snapshot(
                refresh(initial, verify=True, stream_index=0),
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
    stream_index = 0
    scroll = 0
    deadline = time.monotonic() + _REFRESH_SECONDS
    worker.request(verify=True, stream_index=stream_index)
    try:
        tty.setcbreak(descriptor)
        with Live(
            console=console,
            screen=True,
            auto_refresh=False,
            redirect_stdout=False,
            redirect_stderr=False,
        ) as live:
            layout = Layout()
            layout.split_column(Layout(name="body"), Layout(name="controls", size=2))
            while True:
                now = time.monotonic()
                if now >= deadline:
                    worker.request(verify=False, stream_index=stream_index)
                    deadline = now + _REFRESH_SECONDS
                snapshot = worker.snapshot
                text = render_snapshot(snapshot, now=datetime.now(UTC))
                controls = "q quit | r verify/associate again | Tab stream | j/k scroll"
                if review_resume is not None:
                    controls += " | p leave view and review resume plan"
                if worker.busy or worker.pending is not None:
                    controls += (
                        "\nRefresh in progress; displayed observations are dated"
                    )
                rows = text.split("\n")
                scroll = min(scroll, max(0, len(rows) - 1))
                layout["body"].update(Text("\n".join(rows[scroll:])))
                layout["controls"].update(Text(controls))
                live.update(layout, refresh=True)
                if select.select([descriptor], [], [], 1)[0]:
                    key = os.read(descriptor, 1)
                    if key in (b"q", b"Q", b"\x04", b""):
                        return 0
                    if key in (b"p", b"P") and review_resume is not None:
                        break
                    if key in (b"r", b"R", b"\t"):
                        if key == b"\t":
                            stream_index += 1
                        worker.request(verify=key != b"\t", stream_index=stream_index)
                    if key in (b"j", b"k"):
                        scroll = max(0, scroll + (1 if key == b"j" else -1))
    except KeyboardInterrupt:
        return 0
    finally:
        worker.close()
        termios.tcsetattr(descriptor, termios.TCSADRAIN, original)
    # An active daemon read may finish, but no queued refresh or cached evidence
    # participates in the CLI operation. Its owner admits and confirms a new plan.
    assert review_resume is not None
    return review_resume()
