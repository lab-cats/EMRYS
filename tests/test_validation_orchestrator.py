import configparser
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tests" / "tools" / "run_validation.py"
SPEC = importlib.util.spec_from_file_location(
    "norad_validation_orchestrator",
    TOOL_PATH,
)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


def python_lane(name: str, source: str) -> object:
    return TOOL.Lane(name, (sys.executable, "-c", source))


def remove_retained_logs(outcome: object) -> None:
    for result in outcome.results:
        if result.retained_log:
            Path(result.retained_log).unlink(missing_ok=True)


def test_interface_bounds_and_lane_partition(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as help_exit:
        TOOL.parse_args(["--help"])
    assert help_exit.value.code == 0

    for value in (0, 5):
        with pytest.raises(TOOL.ValidationError, match="between 1 and 4"):
            TOOL.require_concurrency(value, "jobs")

    serial = TOOL.build_lanes(
        REPO_ROOT,
        tmp_path,
        Path(sys.executable),
        "/explicit/Rscript",
        1,
    )
    parallel = TOOL.build_lanes(
        REPO_ROOT,
        tmp_path,
        Path(sys.executable),
        "/explicit/Rscript",
        4,
    )
    assert tuple(lane.name for lane in serial) == TOOL.LANE_NAMES
    assert tuple(lane.name for lane in parallel) == TOOL.LANE_NAMES
    assert "-n" not in serial[0].command[-1]
    assert "-n 4 --dist=loadfile" in parallel[0].command[-1]
    assert "validation-shell-contracts" in serial[1].command
    assert "validation-guarded-r" in serial[2].command
    assert "validation-report-runtime" in serial[3].command


def test_dependency_and_make_wiring_are_explicit() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert f"pytest-xdist=={TOOL.XDIST_VERSION}" in requirements.splitlines()
    assert f"execnet=={TOOL.EXECNET_VERSION}" in requirements.splitlines()

    config = configparser.ConfigParser()
    config.read(REPO_ROOT / ".coveragerc", encoding="utf-8")
    assert config.getboolean("run", "parallel")

    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    for target in (
        "validation-python-coverage:",
        "validation-shell-contracts:",
        "validation-guarded-r:",
        "validation-report-runtime:",
        "validation-static:",
        "all-checks:",
        "demo-report:",
    ):
        assert target in makefile
    assert "tests/tools/run_validation.py" in makefile
    assert "PYTHON_COVERAGE_PYTEST_ARGS" in makefile


def test_selected_environment_has_exact_parallel_dependencies() -> None:
    TOOL.require_parallel_dependencies(Path(sys.executable))
    assert (
        TOOL.package_version(Path(sys.executable), "pytest-xdist")
        == TOOL.XDIST_VERSION
    )
    assert (
        TOOL.package_version(Path(sys.executable), "execnet")
        == TOOL.EXECNET_VERSION
    )


def test_executable_validation_preserves_virtualenv_symlink(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "python-target"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    virtualenv_link = tmp_path / "python"
    virtualenv_link.symlink_to(executable)

    assert TOOL.require_executable(virtualenv_link, "Python") == (
        virtualenv_link.absolute()
    )


def test_quiet_parallel_success_removes_logs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lanes = [
        python_lane("one", "print('one output')"),
        python_lane("two", "print('two output')"),
    ]
    outcome = TOOL.run_lanes(lanes, REPO_ROOT, tmp_path, 2, False)

    assert outcome.status == 0
    assert [result.status for result in outcome.results] == [0, 0]
    assert not list(tmp_path.glob("*.log"))
    captured = capsys.readouterr()
    assert "PASS one" in captured.out
    assert "PASS two" in captured.out
    assert "one output" not in captured.out
    assert "two output" not in captured.out


def test_verbose_mode_streams_child_output(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    outcome = TOOL.run_lanes(
        [python_lane("verbose", "print('visible child output')")],
        REPO_ROOT,
        tmp_path,
        1,
        True,
    )

    assert outcome.status == 0
    captured = capfd.readouterr()
    assert "START verbose:" in captured.out
    assert "visible child output" in captured.out
    assert "PASS verbose" in captured.out


def test_first_failure_propagates_and_kills_child_process_group(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ready = tmp_path / "ready"
    survived = tmp_path / "grandchild-survived"
    slow_source = (
        "from pathlib import Path; import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', "
        f"\"from pathlib import Path; import time; time.sleep(1.0); "
        f"Path({str(survived)!r}).write_text('survived')\"]); "
        f"Path({str(ready)!r}).write_text('ready'); "
        "time.sleep(10)"
    )
    failure_source = (
        "import sys, time; time.sleep(0.5); "
        "print('controlled failure'); sys.exit(7)"
    )
    outcome = TOOL.run_lanes(
        [
            python_lane("slow", slow_source),
            python_lane("controlled", failure_source),
        ],
        REPO_ROOT,
        tmp_path,
        2,
        False,
    )

    try:
        assert outcome.status == 7
        assert ready.is_file()
        time.sleep(1.2)
        assert not survived.exists()
        failure = next(
            result for result in outcome.results if result.name == "controlled"
        )
        assert failure.retained_log is not None
        assert "controlled failure" in Path(failure.retained_log).read_text(
            encoding="utf-8"
        )
        captured = capsys.readouterr()
        assert "FAIL controlled status=7" in captured.err
        assert "controlled failure" in captured.err
        assert not list(tmp_path.glob("*.log"))
    finally:
        remove_retained_logs(outcome)


def test_sigint_cleans_process_tree_and_restores_handler(
    tmp_path: Path,
) -> None:
    ready = tmp_path / "interrupt-ready"
    survived = tmp_path / "interrupt-grandchild-survived"
    lane_source = (
        "from pathlib import Path; import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', "
        f"\"from pathlib import Path; import time; time.sleep(1.0); "
        f"Path({str(survived)!r}).write_text('survived')\"]); "
        f"Path({str(ready)!r}).write_text('ready'); "
        "time.sleep(10)"
    )
    prior_handler = signal.getsignal(signal.SIGINT)

    def interrupt_when_ready() -> None:
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        os.kill(os.getpid(), signal.SIGINT)

    interrupter = threading.Thread(target=interrupt_when_ready)
    interrupter.start()
    outcome = TOOL.run_lanes(
        [python_lane("interrupt", lane_source)],
        REPO_ROOT,
        tmp_path,
        1,
        False,
    )
    interrupter.join(timeout=5)

    try:
        assert outcome.status == 130
        assert outcome.interrupted_by == signal.SIGINT
        assert signal.getsignal(signal.SIGINT) == prior_handler
        time.sleep(1.2)
        assert not survived.exists()
        assert not list(tmp_path.glob("*.log"))
    finally:
        remove_retained_logs(outcome)


def test_machine_readable_summaries_and_safe_result_write(
    tmp_path: Path,
) -> None:
    junit = tmp_path / "pytest.xml"
    junit.write_text(
        '<testsuites><testsuite tests="5" failures="1" errors="0" '
        'skipped="2"/></testsuites>',
        encoding="utf-8",
    )
    assert TOOL.junit_summary(junit) == {
        "tests": 5,
        "failures": 1,
        "errors": 0,
        "skipped": 2,
        "passed": 2,
    }

    snapshot = tmp_path / "coverage.json"
    snapshot.write_text(
        json.dumps(
            {
                "totals": {
                    "covered_lines": 9,
                    "num_statements": 10,
                    "covered_branches": 3,
                    "num_branches": 4,
                },
                "files": [{"path": "scripts/example.py"}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    summary = TOOL.coverage_summary(snapshot)
    assert summary["file_count"] == 1
    assert len(summary["sha256"]) == 64

    result = tmp_path / "result.json"
    TOOL.write_result(result, {"status": 0})
    assert json.loads(result.read_text(encoding="utf-8")) == {"status": 0}
    assert not list(tmp_path.glob("*.tmp"))
