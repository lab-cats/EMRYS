#!/usr/bin/env python3
"""Run the de-duplicated NORAD local validation lanes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
XDIST_VERSION = "3.8.0"
EXECNET_VERSION = "2.1.2"
LANE_NAMES = (
    "python-coverage",
    "shell-contracts",
    "guarded-r",
    "report-runtime",
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


def package_version(python_bin: Path, package: str) -> str:
    """Read one installed distribution version from the selected interpreter."""
    script = (
        "import importlib.metadata, sys; "
        "name=sys.argv[1]; "
        "print(importlib.metadata.version(name))"
    )
    result = subprocess.run(
        [str(python_bin), "-c", script, package],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(
            f"{package} is unavailable in {python_bin}; "
            "synchronize the tracked requirements explicitly"
        )
    return result.stdout.strip()


def require_parallel_dependencies(python_bin: Path) -> None:
    """Require the characterized xdist dependency identities."""
    observed = {
        "pytest-xdist": package_version(python_bin, "pytest-xdist"),
        "execnet": package_version(python_bin, "execnet"),
    }
    expected = {
        "pytest-xdist": XDIST_VERSION,
        "execnet": EXECNET_VERSION,
    }
    if observed != expected:
        raise ValidationError(
            "Parallel dependency version mismatch: "
            f"expected {expected}, observed {observed}"
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
    python_junit = run_root / "python.junit.xml"
    report_junit = run_root / "report.junit.xml"
    pytest_args = [
        "-q",
        "--tb=short",
        f"--junitxml={python_junit}",
    ]
    if python_workers > 1:
        pytest_args.extend(["-n", str(python_workers), "--dist=loadfile"])
    coverage_pytest_args = " ".join(shlex.quote(value) for value in pytest_args)

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
                make_assignment("PYTHON_COVERAGE_PYTEST_ARGS", coverage_pytest_args),
            ),
        ),
        Lane(
            "shell-contracts",
            (
                "make",
                "-s",
                "validation-shell-contracts",
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
        Lane(
            "report-runtime",
            (
                "make",
                "-s",
                "validation-report-runtime",
                *common,
                make_assignment("REPORT_TEST_RESULT", report_junit),
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


def start_lane(
    lane: Lane,
    repo_root: Path,
    run_root: Path,
    verbose: bool,
) -> RunningLane:
    """Start one lane in its own process group."""
    log_path: Path | None = None
    log_handle: Any | None = None
    stdout: Any | None = None
    if not verbose:
        log_path = run_root / f"{lane.name}.log"
        log_handle = log_path.open("w", encoding="utf-8")
        stdout = log_handle
    else:
        print(f"START {lane.name}: {command_text(lane.command)}", flush=True)

    environment = os.environ.copy()
    environment["PYTEST_ADDOPTS"] = ""
    try:
        process = subprocess.Popen(
            lane.command,
            cwd=repo_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except Exception:
        if log_handle is not None:
            log_handle.close()
        raise
    return RunningLane(
        lane=lane,
        process=process,
        started=time.monotonic(),
        log_path=log_path,
        log_handle=log_handle,
    )


def close_running_lane(running: RunningLane) -> None:
    """Close one lane's owned log handle."""
    if running.log_handle is not None and not running.log_handle.closed:
        running.log_handle.close()


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
                    if item.log_path is not None:
                        item.log_path.unlink(missing_ok=True)
                return RunOutcome(first_failure.status, tuple(results))

        return RunOutcome(0, tuple(results))
    finally:
        for signum, handler in original_handlers.items():
            signal.signal(signum, handler)
        for item in running:
            close_running_lane(item)


def junit_summary(path: Path) -> dict[str, int]:
    """Read aggregate pytest counts from a JUnit XML result."""
    if not path.is_file() or path.is_symlink():
        raise ValidationError(f"Expected a real JUnit XML result: {path}")
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValidationError(f"Could not parse JUnit XML {path}: {exc}") from exc

    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    if not suites:
        raise ValidationError(f"JUnit XML contains no test suites: {path}")
    totals = {
        name: sum(int(suite.attrib.get(name, "0")) for suite in suites)
        for name in ("tests", "failures", "errors", "skipped")
    }
    totals["passed"] = (
        totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    )
    return totals


def coverage_summary(path: Path) -> dict[str, Any]:
    """Read and identify one deterministic coverage snapshot."""
    if not path.is_file() or path.is_symlink():
        raise ValidationError(f"Expected a real coverage snapshot: {path}")
    payload_bytes = path.read_bytes()
    try:
        document = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"Could not parse coverage snapshot {path}: {exc}"
        ) from exc
    files = document.get("files")
    totals = document.get("totals")
    if not isinstance(files, list) or not isinstance(totals, dict):
        raise ValidationError(f"Coverage snapshot has an invalid shape: {path}")
    return {
        "sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "file_count": len(files),
        "totals": totals,
        "files": files,
    }


def captured_results(run_root: Path) -> dict[str, Any]:
    """Collect machine-readable Python and report results before cleanup."""
    return {
        "python": {
            "pytest": junit_summary(run_root / "python.junit.xml"),
            "coverage": coverage_summary(
                run_root / "coverage" / "python_coverage.current.json"
            ),
        },
        "report_runtime": {
            "pytest": junit_summary(run_root / "report.junit.xml"),
        },
    }


def outcome_document(
    outcome: RunOutcome,
    *,
    mode: str,
    jobs: int,
    python_workers: int,
    elapsed_seconds: float,
    results: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a machine-readable validation result."""
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "jobs": jobs,
        "python_workers": python_workers,
        "status": outcome.status,
        "interrupted_by": outcome.interrupted_by,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "lanes": [
            {
                "name": item.name,
                "status": item.status,
                "elapsed_seconds": round(item.elapsed_seconds, 6),
                "retained_log": item.retained_log,
            }
            for item in outcome.results
        ],
        "results": results,
    }


def write_result(path: Path, document: dict[str, Any]) -> None:
    """Write one canonical result JSON without following symlinks."""
    parent = require_real_directory(path.parent, "result JSON parent")
    destination = parent / path.name
    if destination.exists() and (not destination.is_file() or destination.is_symlink()):
        raise ValidationError(f"Refusing unsafe result JSON path: {destination}")
    payload = json.dumps(document, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


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
    parser.add_argument("--result-json", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the complete de-duplicated validation gate."""
    try:
        arguments = parse_args(argv)
        repo_root = require_real_directory(arguments.repo_root, "repository root")
        python_bin = require_executable(arguments.python_bin, "Python interpreter")
        jobs = 1 if arguments.serial else require_concurrency(arguments.jobs, "jobs")
        python_workers = (
            1
            if arguments.serial
            else require_concurrency(arguments.python_workers, "python workers")
        )
        if python_workers > 1:
            require_parallel_dependencies(python_bin)

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
                captured: dict[str, Any] | None = None
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
                captured = (
                    captured_results(run_root) if lane_outcome.status == 0 else None
                )
            elapsed = time.monotonic() - overall_started
            mode = "serial" if jobs == 1 and python_workers == 1 else "parallel"
            document = outcome_document(
                outcome,
                mode=mode,
                jobs=jobs,
                python_workers=python_workers,
                elapsed_seconds=elapsed,
                results=captured,
            )

        print(
            f"SUMMARY status={outcome.status} mode={document['mode']} "
            f"jobs={jobs} python_workers={python_workers} "
            f"elapsed={elapsed:.3f}s",
            flush=True,
        )
        if arguments.result_json is not None:
            write_result(arguments.result_json, document)
            print(f"RESULT {arguments.result_json.resolve()}", flush=True)
        return outcome.status
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
