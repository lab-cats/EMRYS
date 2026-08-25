from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest

from emrys.libraries.application_logging.helpers import (
    LogValueError,
    child_diagnostic_events,
    classify_invocation,
    field,
    render_failure_summary,
    slurm_correlation,
    split_fields,
)


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


def test_invocation_classification_reads_only_selected_values() -> None:
    classified = classify_invocation(
        ["tool", "--token", "secret", "input.bam"],
        secret_arguments={2},
        environment={"PATH": "/tools", "TOKEN": "secret", "UNSELECTED": "no"},
        selected_environment=("PATH", "TOKEN"),
        secret_environment=("TOKEN",),
    )
    assert classified == {
        "argv": ["tool", "--token", "<redacted>", "input.bam"],
        "environment": {"PATH": "/tools", "TOKEN": "<redacted>"},
    }
    with pytest.raises(LogValueError, match="indexes"):
        classify_invocation(["tool"], secret_arguments={1})
    with pytest.raises(LogValueError, match="explicitly selected"):
        classify_invocation(
            ["tool"], selected_environment=("PATH",), secret_environment=("TOKEN",)
        )


def test_binary_diagnostics_round_trip_exact_bytes_and_safe_notice() -> None:
    data = b"bad:\xff\x00\xfe" + bytes(range(256)) * 100
    durable_events, warning = child_diagnostic_events(
        data, stream="stderr", component="samtools"
    )
    fields = [split_fields(selected["fields"])[0] for selected in durable_events]
    decoded = [base64.b64decode(selected["base64"]) for selected in fields]
    assert b"".join(decoded) == data
    assert all(
        len(chunk) == selected["byte_count"]
        and hashlib.sha256(chunk).hexdigest() == selected["sha256"]
        for chunk, selected in zip(decoded, fields, strict=True)
    )
    assert [selected["chunk_index"] for selected in fields] == list(
        range(1, len(fields) + 1)
    )
    assert all(
        selected
        | {
            "stream": "stderr",
            "component": "samtools",
            "chunk_count": len(fields),
        }
        == selected
        for selected in fields
    )
    assert all(selected["detail"] == "durable_only" for selected in durable_events)
    assert "bad" not in warning["message"]
    with pytest.raises(LogValueError, match="nonempty bytes"):
        child_diagnostic_events(b"", stream="stderr", component="samtools")


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
