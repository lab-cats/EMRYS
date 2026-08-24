#!/usr/bin/env python3
"""Run the de-duplicated NORAD local validation lanes."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LANE_NAMES = (
    "python-coverage",
    "wheel-smoke",
    "shell-slurm",
    "guarded-r",
)
MAX_CONCURRENCY = 4
TERMINATION_GRACE_SECONDS = 5.0


class ValidationError(RuntimeError):
    """Raised when the validation runner cannot establish a safe run."""


@dataclass(frozen=True)
class Lane:
    """One independently runnable validation lane."""

    name: str
    command: tuple[str, ...]


@dataclass
class RunningLane:
    """A running lane and its owned resources."""

    lane: Lane
    process: subprocess.Popen[str]
    started: float
    log_path: Path | None
    log_handle: Any | None
    stream_stop: threading.Event | None = None
    stream_thread: threading.Thread | None = None


@dataclass(frozen=True)
class LaneResult:
    """One completed lane result."""

    name: str
    status: int
    elapsed_seconds: float
    retained_log: str | None = None


@dataclass(frozen=True)
class RunOutcome:
    """The result of running a set of lanes."""

    status: int
    results: tuple[LaneResult, ...]
    interrupted_by: int | None = None


def require_concurrency(value: int, label: str) -> int:
    """Require a bounded positive concurrency value."""
    if value < 1 or value > MAX_CONCURRENCY:
        raise ValidationError(
            f"{label} must be between 1 and {MAX_CONCURRENCY}; observed {value}"
        )
    return value


def require_real_directory(path: Path, label: str) -> Path:
    """Resolve an existing, non-symlink directory."""
    if not path.is_dir() or path.is_symlink():
        raise ValidationError(f"{label} must be a real directory: {path}")
    return path.resolve()


def require_executable(path: Path, label: str) -> Path:
    """Resolve an existing executable regular file."""
    candidate = path if path.is_absolute() else Path.cwd() / path
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise ValidationError(f"{label} must be an executable regular file: {path}")
    resolved = candidate.resolve()
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise ValidationError(f"{label} does not resolve to an executable: {path}")
    return candidate.absolute()


def require_locked_environment(
    repo_root: Path,
    python_bin: Path,
    *,
    uv_bin: str | None = None,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """Require the selected environment to match the reviewed uv lock."""
    selected_uv = uv_bin or shutil.which("uv")
    if selected_uv is None:
        raise ValidationError(
            "uv is unavailable; provision it explicitly, then run uv sync --locked"
        )
    environment = os.environ.copy()
    environment["VIRTUAL_ENV"] = str(python_bin.parent.parent)
    command = (
        selected_uv,
        "sync",
        "--locked",
        "--check",
        "--active",
        "--group",
        "workflow",
        "--offline",
        "--no-python-downloads",
        "--project",
        str(repo_root),
        "--python",
        str(python_bin),
    )
    result = command_runner(
        command,
        cwd=repo_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ValidationError(
            f"selected Python environment does not match uv.lock: {python_bin}"
            + (f"\n{detail}" if detail else "")
            + "\nRun uv sync --locked explicitly before validation."
        )


def make_assignment(name: str, value: str | Path | int) -> str:
    """Build one make command-line variable assignment."""
    return f"{name}={value}"


def build_preflight(repo_root: Path, python_bin: Path) -> Lane:
    """Build the serial static preflight."""
    return Lane(
        "static-preflight",
        (
            "make",
            "-s",
            "validation-static",
            make_assignment("REPORT_PYTHON_BIN", python_bin),
        ),
    )


def build_lanes(
    repo_root: Path,
    run_root: Path,
    python_bin: Path,
    rscript_bin: str,
    python_workers: int,
) -> tuple[Lane, ...]:
    """Build the four non-overlapping validation lanes."""
    coverage_root = run_root / "coverage"
    common = (make_assignment("REPORT_PYTHON_BIN", python_bin),)
    return (
        Lane(
            "python-coverage",
            (
                "make",
                "-s",
                "python-coverage-check",
                *common,
                make_assignment("PYTHON_COVERAGE_ROOT", coverage_root),
                make_assignment("PYTHON_COVERAGE_WORKERS", python_workers),
            ),
        ),
        Lane(
            "wheel-smoke",
            (
                "make",
                "-s",
                "validation-wheel-smoke",
                *common,
            ),
        ),
        Lane(
            "shell-slurm",
            (
                "make",
                "-s",
                "validation-shell-slurm",
                *common,
            ),
        ),
        Lane(
            "guarded-r",
            (
                "make",
                "-s",
                "validation-guarded-r",
                make_assignment("RSCRIPT_BIN", rscript_bin),
            ),
        ),
    )


def command_text(command: Sequence[str]) -> str:
    """Render a command for diagnostic output only."""
    return " ".join(shlex.quote(value) for value in command)


def retained_log_path(lane_name: str) -> Path:
    """Allocate a durable failed-lane log outside the ephemeral run root."""
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f"norad-validation-{lane_name}-",
        suffix=".log",
    )
    os.close(descriptor)
    return Path(raw_path)


def retain_log(log_path: Path | None, lane_name: str) -> str | None:
    """Retain one failed or interrupted log and return its path."""
    if log_path is None or not log_path.is_file():
        return None
    destination = retained_log_path(lane_name)
    shutil.copyfile(log_path, destination)
    return str(destination)


def print_log(log_path: Path | None) -> None:
    """Print a captured log without failing on non-text bytes."""
    if log_path is None or not log_path.is_file():
        return
    sys.stderr.write(log_path.read_text(encoding="utf-8", errors="replace"))
    if log_path.stat().st_size and not log_path.read_bytes().endswith(b"\n"):
        sys.stderr.write("\n")


def stream_log(log_path: Path, stop: threading.Event) -> None:
    """Mirror an active lane log to stdout until stopped, then drain it."""
    with log_path.open("r", encoding="utf-8", errors="replace") as reader:
        while True:
            chunk = reader.read()
            if chunk:
                sys.stdout.write(chunk)
                sys.stdout.flush()
                continue
            if stop.wait(0.02):
                remainder = reader.read()
                if remainder:
                    sys.stdout.write(remainder)
                    sys.stdout.flush()
                return


def start_lane(
    lane: Lane,
    repo_root: Path,
    run_root: Path,
    verbose: bool,
) -> RunningLane:
    """Start one lane in its own process group."""
    log_path = run_root / f"{lane.name}.log"
    log_handle = log_path.open("w", encoding="utf-8")
    if verbose:
        print(f"START {lane.name}: {command_text(lane.command)}", flush=True)

    environment = os.environ.copy()
    environment["PYTEST_ADDOPTS"] = ""
    try:
        process = subprocess.Popen(
            lane.command,
            cwd=repo_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except Exception:
        if log_handle is not None:
            log_handle.close()
        raise
    running = RunningLane(
        lane=lane,
        process=process,
        started=time.monotonic(),
        log_path=log_path,
        log_handle=log_handle,
    )
    if verbose:
        running.stream_stop = threading.Event()
        running.stream_thread = threading.Thread(
            target=stream_log,
            args=(log_path, running.stream_stop),
            name=f"norad-validation-{lane.name}-stream",
            daemon=True,
        )
        running.stream_thread.start()
    return running


def close_running_lane(running: RunningLane) -> None:
    """Close one lane's log and finish any verbose stream."""
    if running.log_handle is not None and not running.log_handle.closed:
        running.log_handle.close()
    if running.stream_stop is not None:
        running.stream_stop.set()
    if running.stream_thread is not None:
        running.stream_thread.join()


def normalized_status(returncode: int) -> int:
    """Convert a negative signal return code to a shell-style status."""
    if returncode < 0:
        return 128 + abs(returncode)
    return returncode


def terminate_running(
    running: Sequence[RunningLane],
    first_signal: int,
) -> None:
    """Terminate, escalate, and reap every running process group."""
    active = [item for item in running if item.process.poll() is None]
    for item in active:
        try:
            os.killpg(item.process.pid, first_signal)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + TERMINATION_GRACE_SECONDS
    while active and time.monotonic() < deadline:
        active = [item for item in active if item.process.poll() is None]
        if active:
            time.sleep(0.05)

    for item in active:
        try:
            os.killpg(item.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for item in running:
        try:
            item.process.wait(timeout=TERMINATION_GRACE_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise ValidationError(
                f"Could not reap validation lane {item.lane.name}"
            ) from exc


def run_lanes(
    lanes: Sequence[Lane],
    repo_root: Path,
    run_root: Path,
    jobs: int,
    verbose: bool,
) -> RunOutcome:
    """Run lanes with bounded concurrency and first-failure cancellation."""
    require_concurrency(jobs, "jobs")
    pending = list(lanes)
    running: list[RunningLane] = []
    results: list[LaneResult] = []
    interrupted_by: int | None = None
    original_handlers: dict[int, Any] = {}

    def handle_signal(signum: int, _frame: Any) -> None:
        nonlocal interrupted_by
        if interrupted_by is None:
            interrupted_by = signum

    for signum in (signal.SIGINT, signal.SIGTERM):
        original_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, handle_signal)

    try:
        while pending or running:
            while pending and len(running) < jobs and interrupted_by is None:
                running.append(start_lane(pending.pop(0), repo_root, run_root, verbose))

            if interrupted_by is not None:
                terminate_running(running, signal.SIGTERM)
                for item in running:
                    close_running_lane(item)
                    elapsed = time.monotonic() - item.started
                    retained = retain_log(item.log_path, item.lane.name)
                    if item.log_path is not None:
                        item.log_path.unlink(missing_ok=True)
                    print(
                        f"INTERRUPTED {item.lane.name} "
                        f"elapsed={elapsed:.3f}s"
                        + (f" retained_log={retained}" if retained else ""),
                        file=sys.stderr,
                    )
                    results.append(
                        LaneResult(
                            item.lane.name,
                            128 + interrupted_by,
                            elapsed,
                            retained,
                        )
                    )
                return RunOutcome(
                    128 + interrupted_by,
                    tuple(results),
                    interrupted_by,
                )

            completed = [item for item in running if item.process.poll() is not None]
            if not completed:
                time.sleep(0.05)
                continue

            first_failure: LaneResult | None = None
            for item in completed:
                running.remove(item)
                returncode = item.process.returncode
                assert returncode is not None
                status = normalized_status(returncode)
                elapsed = time.monotonic() - item.started
                close_running_lane(item)
                retained: str | None = None
                if status == 0:
                    print(
                        f"PASS {item.lane.name} elapsed={elapsed:.3f}s",
                        flush=True,
                    )
                    if item.log_path is not None:
                        item.log_path.unlink(missing_ok=True)
                else:
                    retained = retain_log(item.log_path, item.lane.name)
                    print(
                        f"FAIL {item.lane.name} status={status} "
                        f"elapsed={elapsed:.3f}s"
                        + (f" retained_log={retained}" if retained else ""),
                        file=sys.stderr,
                    )
                    if not verbose:
                        print_log(item.log_path)
                    if item.log_path is not None:
                        item.log_path.unlink(missing_ok=True)
                result = LaneResult(
                    item.lane.name,
                    status,
                    elapsed,
                    retained,
                )
                results.append(result)
                if status != 0 and first_failure is None:
                    first_failure = result

            if first_failure is not None:
                terminate_running(running, signal.SIGTERM)
                for item in running:
                    close_running_lane(item)
                    elapsed = time.monotonic() - item.started
                    retained = retain_log(item.log_path, item.lane.name)
                    if item.log_path is not None:
                        item.log_path.unlink(missing_ok=True)
                    print(
                        f"CANCELLED {item.lane.name} elapsed={elapsed:.3f}s"
                        + (f" retained_log={retained}" if retained else ""),
                        file=sys.stderr,
                    )
                    results.append(
                        LaneResult(
                            item.lane.name,
                            128 + signal.SIGTERM,
                            elapsed,
                            retained,
                        )
                    )
                return RunOutcome(first_failure.status, tuple(results))

        return RunOutcome(0, tuple(results))
    finally:
        for signum, handler in original_handlers.items():
            signal.signal(signum, handler)
        for item in running:
            close_running_lane(item)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the developer validation interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--python-bin", required=True, type=Path)
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--python-workers", type=int, default=1)
    parser.add_argument(
        "--serial",
        action="store_true",
        help="Force one top-level lane and one Python worker.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Stream complete lane output instead of capturing successful logs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the complete de-duplicated validation gate."""
    try:
        arguments = parse_args(argv)
        repo_root = require_real_directory(arguments.repo_root, "repository root")
        python_bin = require_executable(arguments.python_bin, "Python interpreter")
        require_locked_environment(repo_root, python_bin)
        jobs = 1 if arguments.serial else require_concurrency(arguments.jobs, "jobs")
        python_workers = (
            1
            if arguments.serial
            else require_concurrency(arguments.python_workers, "python workers")
        )
        overall_started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="norad-validation-") as temporary_root:
            run_root = Path(temporary_root)
            preflight = run_lanes(
                [build_preflight(repo_root, python_bin)],
                repo_root,
                run_root,
                1,
                arguments.verbose,
            )
            if preflight.status != 0:
                outcome = preflight
            else:
                lanes = build_lanes(
                    repo_root,
                    run_root,
                    python_bin,
                    arguments.rscript_bin,
                    python_workers,
                )
                lane_outcome = run_lanes(
                    lanes,
                    repo_root,
                    run_root,
                    jobs,
                    arguments.verbose,
                )
                outcome = RunOutcome(
                    lane_outcome.status,
                    preflight.results + lane_outcome.results,
                    lane_outcome.interrupted_by,
                )
            elapsed = time.monotonic() - overall_started
            mode = "serial" if jobs == 1 and python_workers == 1 else "parallel"

        print(
            f"SUMMARY status={outcome.status} mode={mode} "
            f"jobs={jobs} python_workers={python_workers} "
            f"elapsed={elapsed:.3f}s",
            flush=True,
        )
        return outcome.status
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
