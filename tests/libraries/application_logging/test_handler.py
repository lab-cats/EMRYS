from __future__ import annotations

import io
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from emrys.libraries.application_logging.controls import LogControls, LogLevel
from emrys.libraries.application_logging.handler import (
    APPLICATION_LOG_SCHEMA_VERSION,
    ApplicationLogError,
    AttemptIdentity,
    event,
    open_attempt_log,
)
from emrys.libraries.application_logging.helpers import LogValueError, field
from emrys.libraries.application_logging import handler as logging_handler
from emrys.libraries.application_logging.storage import (
    ApplicationLogFile,
    ApplicationLogStorageError,
)


REQUIRED_KEYS = set(
    "schema_version timestamp_utc monotonic_seconds sequence severity console_detail "
    "entrypoint component scope_kind scope_id execution_attempt_id mode phase event "
    "message fields".split()
)


def identity(suffix: str = "1") -> AttemptIdentity:
    return AttemptIdentity("run", "run-7", f"attempt-{suffix}", "emrys-run")


def read_records(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def fixed_clock() -> datetime:
    return datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


def open_log(
    tmp_path: Path,
    *,
    suffix: str = "1",
    level: LogLevel = LogLevel.NORMAL,
    stderr: object | None = None,
    root: Path | None = None,
    **kwargs: object,
):
    return open_attempt_log(
        controls=LogControls(
            level,
            root or tmp_path / f"logs-{suffix}",
            "command_line",
            "command_line",
        ),
        identity=identity(suffix),
        mode="execute",
        component="run",
        stderr=stderr if stderr is not None else io.StringIO(),
        **kwargs,
    )


def test_attempt_writes_exact_schema_to_protected_path_before_stderr(
    tmp_path: Path,
) -> None:
    stderr = io.StringIO()
    ticks = iter((1.0, 2.0))
    attempt = open_log(
        tmp_path,
        stderr=stderr,
        root=tmp_path / "logs",
        _utc_now=fixed_clock,
        _monotonic=lambda: next(ticks),
    )
    path = attempt.path
    assert path == tmp_path / "logs/run-run-7/attempt-1/emrys-run.jsonl"
    assert "Application logging attempt opened" in stderr.getvalue()
    assert all(
        identity in stderr.getvalue()
        for identity in ("run:run-7", "attempt-1", "emrys-run")
    )

    attempt.logger(component="alignment", phase="execute").info(
        "Alignment completed.",
        extra=event(
            "alignment_completed",
            fields={"samples": field(2, console=True)},
        ),
    )
    attempt.close()

    records = read_records(path)
    assert all(set(record) == REQUIRED_KEYS for record in records)
    assert [record["sequence"] for record in records] == [1, 2]
    assert records[0]["schema_version"] == APPLICATION_LOG_SCHEMA_VERSION
    assert records[0]["timestamp_utc"] == "2026-08-25T12:00:00.000000Z"
    assert records[1]["event"] == "alignment_completed"
    assert records[1]["fields"] == {"samples": 2}


def test_console_levels_are_nested_while_durable_semantics_are_invariant(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline: list[dict[str, object]] | None = None
    for level, visible in (
        (LogLevel.NORMAL, ("normal",)),
        (LogLevel.VERBOSE, ("normal", "verbose")),
        (LogLevel.DEBUG, ("normal", "verbose", "debug")),
    ):
        stderr = io.StringIO()
        ticks = iter((1.0, 2.0, 3.0, 4.0, 5.0))
        attempt = open_log(
            tmp_path,
            suffix=level.value,
            level=level,
            stderr=stderr,
            _utc_now=fixed_clock,
            _monotonic=lambda: next(ticks),
        )
        logger = attempt.logger(component="qc", phase="execute")
        for detail in ("normal", "verbose", "debug", "durable_only"):
            logger.info(f"{detail} event", extra=event(detail, detail=detail))
        path = attempt.path
        attempt.close()

        records = read_records(path)
        for record in records:
            record.pop("execution_attempt_id")
        for field_name in ("execution_attempt_id", "log_level", "log_path"):
            records[0]["fields"].pop(field_name)
        if baseline is None:
            baseline = records
        else:
            assert records == baseline
        projection = stderr.getvalue()
        for detail in visible:
            assert f"{detail} event" in projection
        for detail in {"normal", "verbose", "debug", "durable_only"} - set(visible):
            assert f"{detail} event" not in projection
    assert capsys.readouterr().out == ""


def test_fields_are_classified_and_secrets_are_discarded(tmp_path: Path) -> None:
    class ExplosiveSecret:
        def __repr__(self) -> str:
            raise AssertionError("secret was inspected")

    stderr = io.StringIO()
    attempt = open_log(tmp_path, stderr=stderr)
    attempt.logger(component="tool", phase="execute").warning(
        "Tool warning.",
        extra=event(
            "tool_warning",
            fields={
                "token": field(ExplosiveSecret(), console=True, secret=True),
                "path": field(Path("/safe/path")),
            },
        ),
    )
    path = attempt.path
    attempt.close()
    record = read_records(path)[-1]
    assert record["fields"] == {"token": "<redacted>", "path": "/safe/path"}
    assert 'token="<redacted>"' in stderr.getvalue()
    assert "/safe/path" not in stderr.getvalue()


def test_global_disable_does_not_suppress_attempt_and_closed_adapter_rejects(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    attempt = open_log(tmp_path)
    logger = attempt.logger(component="work", phase="execute")
    logging.disable(logging.CRITICAL)
    try:
        logger.info("Still durable.")
    finally:
        logging.disable(logging.NOTSET)
    path = attempt.path
    attempt.close()
    assert read_records(path)[-1]["message"] == "Still durable."
    with pytest.raises(ApplicationLogError, match="closed"):
        logger.error("Must not escape to lastResort.")
    assert capsys.readouterr().err == ""


def test_public_extra_cannot_forge_lifecycle(tmp_path: Path) -> None:
    attempt = open_log(tmp_path)
    logger = attempt.logger(component="publication", phase="publish")
    for reserved in ("publication_ready", "attempt_failed", "attempt_interrupted"):
        with pytest.raises(ApplicationLogError, match="lifecycle method"):
            logger.info("Forged.", extra=event(reserved))
    with pytest.raises(ApplicationLogError, match="dedicated lifecycle method"):
        attempt.terminal(event_name="publication_ready", message="Forged.")
    path = attempt.path
    attempt.close()
    assert [record["event"] for record in read_records(path)] == ["attempt_opened"]


def test_invalid_scheduler_identity_has_no_storage_side_effect(tmp_path: Path) -> None:
    root = tmp_path / "logs"
    with pytest.raises(LogValueError):
        open_log(
            tmp_path,
            root=root,
            scheduler_environment={"SLURM_JOB_ID": "not-an-id"},
        )
    assert not root.exists()


def test_publication_boundary_is_atomic_with_ordinary_emission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempt = open_log(tmp_path)
    logger = attempt.logger(component="work", phase="execute")
    synchronizing = threading.Event()
    release_sync = threading.Event()
    original = ApplicationLogFile.synchronize

    def blocked_sync(file: ApplicationLogFile) -> None:
        synchronizing.set()
        assert release_sync.wait(timeout=5)
        original(file)

    monkeypatch.setattr(ApplicationLogFile, "synchronize", blocked_sync)
    publication = threading.Thread(target=attempt.publication_ready)
    publication.start()
    assert synchronizing.wait(timeout=5)

    rejected: list[Exception] = []

    def emit() -> None:
        try:
            logger.info("Too late.")
        except Exception as exc:  # captured from the worker for assertion below
            rejected.append(exc)

    ordinary = threading.Thread(target=emit)
    ordinary.start()
    ordinary.join(timeout=0.1)
    assert ordinary.is_alive()
    release_sync.set()
    publication.join(timeout=5)
    ordinary.join(timeout=5)

    assert len(rejected) == 1
    assert isinstance(rejected[0], ApplicationLogError)
    assert [record["event"] for record in read_records(attempt.path)][-1] == (
        "publication_ready"
    )
    attempt.close()


def test_receipt_lifecycle_orders_and_synchronizes_owner_events(tmp_path: Path) -> None:
    attempt = open_log(tmp_path)
    logger = attempt.logger(component="work", phase="execute")
    logger.info("Work complete.", extra=event("work_complete"))
    attempt.publication_ready()
    with pytest.raises(ApplicationLogError, match="ready"):
        logger.info("Too late.")
    attempt.receipt_committed()
    assert attempt.observe_post_receipt(
        event_name="receipt_observed", message="Receipt observed."
    )
    path = attempt.path
    attempt.close()
    assert [record["event"] for record in read_records(path)] == [
        "attempt_opened",
        "work_complete",
        "publication_ready",
        "receipt_observed",
    ]


def test_post_receipt_close_failure_is_best_effort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempt = open_log(tmp_path)
    attempt.publication_ready()
    attempt.receipt_committed()
    original = ApplicationLogFile.close

    def fail_after_close(file: ApplicationLogFile) -> None:
        original(file)
        raise ApplicationLogStorageError("injected")

    monkeypatch.setattr(ApplicationLogFile, "close", fail_after_close)
    assert not attempt.close()
    assert not attempt.observe_post_receipt(
        event_name="late_observation", message="Too late."
    )


def test_receipt_failure_reopens_only_recovery_then_terminal_closes(
    tmp_path: Path,
) -> None:
    attempt = open_log(tmp_path)
    attempt.publication_ready()
    attempt.receipt_failed(message="Receipt write failed.")
    attempt.logger(component="recovery", phase="rollback").info(
        "Rollback complete.", extra=event("rollback_complete")
    )
    path = attempt.path
    attempt.terminal(event_name="recovery_complete", message="Recovery complete.")
    assert [record["event"] for record in read_records(path)][-3:] == [
        "receipt_publication_failed",
        "rollback_complete",
        "recovery_complete",
    ]


def test_declared_boundaries_synchronize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synchronized: list[Path] = []
    original = ApplicationLogFile.synchronize

    def record_sync(file: ApplicationLogFile) -> None:
        synchronized.append(file.path)
        original(file)

    monkeypatch.setattr(ApplicationLogFile, "synchronize", record_sync)
    phase = open_log(tmp_path, suffix="phase")
    phase.synchronize("phase")
    phase.terminal(event_name="complete", message="Complete.")
    failure = open_log(tmp_path, suffix="failure-sync")
    failure.fail(phase="execute", message="Failed.")
    interrupted = open_log(tmp_path, suffix="interrupt-sync")
    interrupted.interrupt_best_effort(message="Interrupted.")
    recovery = open_log(tmp_path, suffix="recovery-sync")
    recovery.publication_ready()
    recovery.receipt_failed(message="Receipt failed.")
    recovery.synchronize("recovery")
    recovery.terminal(event_name="recovered", message="Recovered.")

    assert [path.parent.name for path in synchronized] == [
        "attempt-phase",
        "attempt-phase",
        "attempt-failure-sync",
        "attempt-interrupt-sync",
        "attempt-recovery-sync",
        "attempt-recovery-sync",
        "attempt-recovery-sync",
        "attempt-recovery-sync",
    ]


def test_console_failure_cannot_strand_a_durable_terminal_event(tmp_path: Path) -> None:
    class BrokenConsole:
        def write(self, value: str) -> None:
            raise OSError("stderr unavailable")

        def flush(self) -> None:
            raise OSError("stderr unavailable")

    attempt = open_log(tmp_path, stderr=BrokenConsole())
    path = attempt.path
    attempt.terminal(event_name="complete", message="Complete.")
    assert read_records(path)[-1]["event"] == "complete"


def test_slurm_context_changes_only_opening_correlation_fields(tmp_path: Path) -> None:
    def run(suffix: str, environment: dict[str, str]) -> list[dict[str, object]]:
        ticks = iter((1.0, 2.0))
        attempt = open_log(
            tmp_path,
            suffix=suffix,
            scheduler_environment=environment,
            _utc_now=fixed_clock,
            _monotonic=lambda: next(ticks),
        )
        attempt.logger(component="work", phase="execute").info(
            "Same work.", extra=event("same_work")
        )
        path = attempt.path
        attempt.close()
        return read_records(path)

    local = run("local", {})
    slurm = run("slurm", {"SLURM_JOB_ID": "42"})
    for records in (local, slurm):
        for record in records:
            record.pop("execution_attempt_id")
        records[0]["fields"].pop("execution_attempt_id")
    local[0]["fields"].pop("log_path")
    slurm[0]["fields"].pop("log_path")
    assert slurm[0]["fields"].pop("slurm_job_id") == "42"
    assert local == slurm


def test_failure_and_interrupt_boundaries_are_terminal(tmp_path: Path) -> None:
    attempt = open_log(tmp_path, suffix="failure")
    logger = attempt.logger(component="work", phase="execute")
    logger.debug("Debug detail.")
    logger.info("Hidden bytes.", extra=event("hidden", detail="durable_only"))
    assert attempt.durable_only_count == 1
    assert attempt.recent_console_events
    path = attempt.path
    attempt.fail(phase="execute", message="Operation failed.")
    assert read_records(path)[-1]["event"] == "attempt_failed"
    with pytest.raises(ApplicationLogError, match="closed"):
        logger.info("Too late.")
    assert not attempt.interrupt_best_effort(message="Late signal.")

    interrupted = open_log(tmp_path, suffix="interrupt")
    interrupted_path = interrupted.path
    assert interrupted.interrupt_best_effort(message="Caught signal.")
    assert read_records(interrupted_path)[-1]["event"] == "attempt_interrupted"


def test_initialization_write_and_sync_failures_remain_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def storage_failure(*args: object, **kwargs: object) -> None:
        raise ApplicationLogStorageError("injected")

    closed_after_interrupt: list[Path] = []
    original_close = ApplicationLogFile.close

    def close_after_interrupt(file: ApplicationLogFile) -> None:
        original_close(file)
        closed_after_interrupt.append(file.path)

    def interrupt_opening(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    with monkeypatch.context() as selected:
        selected.setattr(
            logging_handler._AttemptLogger,
            "addHandler",
            interrupt_opening,
        )
        selected.setattr(ApplicationLogFile, "close", close_after_interrupt)
        with pytest.raises(KeyboardInterrupt):
            open_log(tmp_path, suffix="initialization-interrupt")
    assert closed_after_interrupt

    with monkeypatch.context() as selected:
        selected.setattr(
            logging_handler, "create_application_log_file", storage_failure
        )
        with pytest.raises(ApplicationLogError) as raised:
            open_log(tmp_path, suffix="init")
        assert (raised.value.stage, raised.value.path) == ("initialization", None)

    for operation in ("write", "sync"):
        attempt = open_log(tmp_path, suffix=operation)
        target = "write_bytes" if operation == "write" else "synchronize"
        with monkeypatch.context() as selected:
            selected.setattr(ApplicationLogFile, target, storage_failure)
            with pytest.raises(ApplicationLogError) as raised:
                if operation == "write":
                    attempt.logger(component="work", phase="execute").info("Event.")
                else:
                    attempt.synchronize("phase")
        assert raised.value.path == attempt.path
        assert attempt.path.exists()

    post_receipt = open_log(tmp_path, suffix="post-failure")
    post_receipt.publication_ready()
    post_receipt.receipt_committed()
    with monkeypatch.context() as selected:
        selected.setattr(ApplicationLogFile, "write_bytes", storage_failure)
        assert not post_receipt.observe_post_receipt(
            event_name="observation", message="Best effort."
        )
    interrupted = open_log(tmp_path, suffix="interrupt-failure")
    with monkeypatch.context() as selected:
        selected.setattr(ApplicationLogFile, "synchronize", storage_failure)
        assert not interrupted.interrupt_best_effort(message="Caught signal.")


def test_admission_rejects_invalid_identity_extra_detail_fields_and_clocks(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        AttemptIdentity("unknown", "scope", "attempt", "emrys-run")
    with pytest.raises(ValueError):
        AttemptIdentity("run", "../escape", "attempt", "emrys-run")
    attempt = open_log(tmp_path, suffix="admission")
    logger = attempt.logger(component="work", phase="execute")
    with pytest.raises(TypeError):
        logger.info("Bad extra.", extra=[])  # type: ignore[arg-type]
    for extra in (
        event("bad_detail", detail="quiet"),
        event("bad_fields", fields={"raw": 1}),
    ):
        with pytest.raises(ApplicationLogError):
            logger.info("Rejected.", extra=extra)
    attempt.close()

    ticks = iter((2.0, 1.0))
    regressed = open_log(tmp_path, suffix="clock", _monotonic=lambda: next(ticks))
    with pytest.raises(ApplicationLogError, match="regressed"):
        regressed.logger(component="work", phase="execute").info("Event.")
    regressed.close()
