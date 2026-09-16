from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

from emrys.libraries.application_logging import helpers
from emrys.libraries.application_logging.helpers import (
    LogValueError,
    console_print,
    field,
    phase_progress,
    render_failure_summary,
    slurm_correlation,
    split_fields,
)


def test_terminal_output_preserves_literal_text_and_plain_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    label = "PASS: sample[red] " + "x" * 100
    terminal = Terminal()
    console_print(label, style="bold green", file=terminal)
    assert "\x1b[" in terminal.getvalue()
    assert label in terminal.getvalue()
    plain = io.StringIO()
    console_print(label, style="bold green", file=plain)
    assert plain.getvalue() == label + "\n"
    monkeypatch.setenv("NO_COLOR", "")
    disabled = Terminal()
    console_print(label, style="bold green", file=disabled)
    assert disabled.getvalue() == plain.getvalue()


def test_phase_progress_reports_actual_completion_and_failure_without_percent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = io.StringIO()
    ticks = iter((10.0, 10.125, 11.0, 13.5))
    monkeypatch.setattr(helpers, "time", SimpleNamespace(monotonic=lambda: next(ticks)))
    observations: list[tuple[str, float | None, str]] = []

    def completed(name: str, elapsed: float | None, outcome: str) -> None:
        observations.append((name, elapsed, outcome))

    with phase_progress("Installing native tools", file=output, on_complete=completed):
        pass
    with pytest.raises(RuntimeError, match="package failure"):
        with phase_progress("Restoring R packages", file=output, on_complete=completed):
            raise RuntimeError("package failure")
    rendered = output.getvalue()
    assert "Installing native tools: complete (0m 00s)" in rendered
    assert "Restoring R packages: interrupted or failed (0m 02s)" in rendered
    assert "Restoring R packages: complete" not in rendered
    assert "\x1b" not in rendered and "%" not in rendered
    assert observations == [
        ("Installing native tools", 0.125, "complete"),
        ("Restoring R packages", 2.5, "interrupted or failed"),
    ]


@pytest.mark.parametrize("failed_clock_read", (None, 1, 2))
@pytest.mark.parametrize("callback_error", (RuntimeError, OSError))
@pytest.mark.parametrize("interrupted", (False, True))
def test_phase_observation_failures_preserve_the_body(
    monkeypatch: pytest.MonkeyPatch,
    failed_clock_read: int | None,
    callback_error: type[Exception],
    interrupted: bool,
) -> None:
    reads = 0
    observations: list[float | None] = []
    body: list[str] = []
    original = KeyboardInterrupt("body interrupted")

    def monotonic() -> float:
        nonlocal reads
        reads += 1
        if reads == failed_clock_read:
            raise OSError("clock unavailable")
        return reads + 0.25 * (reads - 1)

    def completed(_name: str, elapsed: float | None, _outcome: str) -> None:
        observations.append(elapsed)
        raise callback_error("observation unavailable")

    monkeypatch.setattr(helpers, "time", SimpleNamespace(monotonic=monotonic))

    def execute() -> None:
        with phase_progress("Checking", file=io.StringIO(), on_complete=completed):
            body.append("ran")
            if interrupted:
                raise original

    if interrupted:
        with pytest.raises(KeyboardInterrupt) as failure:
            execute()
        assert failure.value is original
    else:
        execute()
    assert body == ["ran"]
    assert observations == [1.25 if failed_clock_read is None else None]
    assert reads == (1 if failed_clock_read == 1 else 2)


@pytest.mark.parametrize("boundary", ("clock_before", "clock_after", "observer"))
@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_phase_timing_preserves_process_control_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    exception_type: type[BaseException],
) -> None:
    original = exception_type("stop requested")
    calls: list[str] = []

    def monotonic() -> float:
        selected = "clock_after" if "body" in calls else "clock_before"
        calls.append(selected)
        if boundary == selected:
            raise original
        return 1.0

    def completed(*_args: object) -> None:
        calls.append("observer")
        raise original

    monkeypatch.setattr(helpers, "time", SimpleNamespace(monotonic=monotonic))
    with pytest.raises(exception_type) as failure:
        with phase_progress("Checking", file=io.StringIO(), on_complete=completed):
            calls.append("body")
        calls.append("continued")
    assert failure.value is original
    assert (
        calls
        == {
            "clock_before": ["clock_before"],
            "clock_after": ["clock_before", "body", "clock_after"],
            "observer": ["clock_before", "body", "clock_after", "observer"],
        }[boundary]
    )


def test_real_sigint_during_phase_observation_stops_execution(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            dedent("""\
                import signal
                import sys
                sys.path.insert(0, sys.argv[1])
                from emrys.libraries.application_logging.helpers import phase_progress
                signal.signal(signal.SIGINT, signal.default_int_handler)
                def observe(*_args):
                    signal.raise_signal(signal.SIGINT)
                try:
                    with phase_progress("Checking", on_complete=observe):
                        print("body")
                    print("continued")
                except KeyboardInterrupt:
                    print("interrupted")
                """),
            str(Path(helpers.__file__).resolve().parents[3]),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "body\ninterrupted\n"


def test_unavailable_progress_display_preserves_interrupted_body() -> None:
    output = io.StringIO()
    interrupted = KeyboardInterrupt("setup interrupted")
    with pytest.raises(KeyboardInterrupt) as failure:
        with phase_progress("Restoring R packages", file=output):
            output.close()
            raise interrupted
    assert failure.value is interrupted
    with phase_progress("Checking retained setup", file=output):
        pass


def test_field_classification_redacts_before_inspection_and_bounds_metadata() -> None:
    class Secret:
        def __repr__(self) -> str:
            raise AssertionError("secret inspected")

    durable, console = split_fields(
        {
            "secret": field(Secret(), secret=True, console=True),
            "path": field(Path("/safe/path")),
        }
    )
    assert durable == {"secret": "<redacted>", "path": "/safe/path"}
    assert console == {"secret": "<redacted>"}
    with pytest.raises(LogValueError, match="bounded metadata"):
        field("x" * 20_000)
    with pytest.raises(LogValueError, match="finite JSON"):
        field(b"raw scientific bytes")
    with pytest.raises(LogValueError, match="console fields"):
        field([1, 2], console=True)


def test_slurm_correlation_is_explicit_canonical_and_relational() -> None:
    assert slurm_correlation(
        {
            "SLURM_JOB_ID": "42",
            "SLURM_ARRAY_JOB_ID": "40",
            "SLURM_ARRAY_TASK_ID": "0",
            "SECRET": "ignored",
        }
    ) == {
        "slurm_job_id": "42",
        "slurm_array_job_id": "40",
        "slurm_array_task_id": "0",
    }
    with pytest.raises(LogValueError, match="canonical"):
        slurm_correlation({"SLURM_JOB_ID": "042"})
    with pytest.raises(LogValueError, match="array correlation"):
        slurm_correlation({"SLURM_JOB_ID": "42", "SLURM_ARRAY_JOB_ID": "40"})


def test_failure_summary_is_complete_console_safe_and_bounded() -> None:
    events = [f"event-{index} " + "x" * 700 for index in range(30)]
    summary = render_failure_summary(
        entrypoint="emrys-run",
        phase="publication",
        status="failed",
        scope="run:run-7",
        execution_attempt_id="attempt-1",
        log_path=Path("/logs/run-run-7/attempt-1/emrys-run.jsonl"),
        owned_paths={
            "lock": Path("/work/run.lock"),
            "stage": Path("/work/stage"),
            "backup": Path("/work/backup"),
            "recovery": Path("/work/recovery"),
        },
        recent_events=events,
        durable_only_count=3,
        next_action="Run emrys inspect.",
    )
    assert len(summary.encode("utf-8")) <= 8192
    assert summary.count("Event:") <= 20
    assert "Console-safe events truncated:" in summary
    assert "Durable-only events omitted: 3" in summary
    assert "Next action: Run emrys inspect." in summary
    assert all(
        value in summary
        for value in ("Owned lock", "Owned stage", "Owned backup", "Owned recovery")
    )
    boundary = render_failure_summary(
        entrypoint="run",
        phase="work",
        status="failed",
        scope="run:1",
        execution_attempt_id="attempt-1",
        log_path=Path("/logs/run.jsonl"),
        recent_events=["x" * 417] * 20,
        next_action="Inspect the log.",
    )
    assert len(boundary.encode("utf-8")) <= 8192
    assert "Console-safe events truncated:" in boundary


def test_initialization_failure_summary_does_not_invent_log_path() -> None:
    summary = render_failure_summary(
        entrypoint="emrys-run",
        phase="initialization",
        status="failed",
        scope="run:run-7",
        execution_attempt_id="attempt-1",
        log_path=None,
        next_action="Correct the log root and retry.",
    )
    assert "no durable log exists" in summary
    assert "/logs/" not in summary


def test_failure_summary_bounds_multibyte_mandatory_fields() -> None:
    value = "🧬" * 3_000
    summary = render_failure_summary(
        entrypoint=value,
        phase=value,
        status=value,
        scope=value,
        execution_attempt_id=value,
        log_path=Path("/" + value),
        owned_paths={
            role: Path("/" + value)
            for role in (
                "lock",
                "stage",
                "backup",
                "recovery",
            )
        },
        next_action=value,
    )
    assert len(summary.encode("utf-8")) <= 8192
    assert "Next action:" in summary


@pytest.mark.parametrize("value", ["bad\nline", "bad\x1b[31m", "bad\u2028line"])
def test_console_bound_text_rejects_control_characters(value: str) -> None:
    with pytest.raises(LogValueError):
        field(value, console=True)
