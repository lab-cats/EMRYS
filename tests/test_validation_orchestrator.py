import configparser
import os
import signal
import subprocess
import sys
import threading
import time
import tomllib
from pathlib import Path

import pytest
from tests.tools import run_validation as TOOL

REPO_ROOT = Path(__file__).resolve().parents[1]


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
    assert "PYTHON_COVERAGE_WORKERS=1" in serial[0].command
    assert "PYTHON_COVERAGE_WORKERS=4" in parallel[0].command
    assert "python-coverage-check" in serial[0].command
    assert "validation-wheel-smoke" in serial[1].command
    assert "validation-shell-contracts" in serial[2].command
    assert "validation-guarded-r" in serial[3].command


def test_dependency_and_make_wiring_are_explicit() -> None:
    configuration = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert set(configuration["project"]["dependencies"]) == {
        "Jinja2==3.1.6",
        "logomaker==0.8.7",
        "matplotlib==3.11.1",
        "PyYAML==6.0.3",
        "jsonschema>=4.18.0",
        "referencing>=0.28.4",
    }
    assert set(configuration["dependency-groups"]["dev"]) == {
        "coverage==7.15.2",
        "pytest",
        "pytest-xdist",
        "ruff",
        "vulture",
    }
    assert configuration["dependency-groups"]["workflow"] == [
        "snakemake==9.25.1"
    ]
    assert configuration["tool"]["uv"]["default-groups"] == ["dev", "workflow"]
    assert configuration["build-system"]["requires"] == ["setuptools==83.0.0"]
    assert not (REPO_ROOT / "requirements.txt").exists()
    assert not (REPO_ROOT / "requirements-dev.txt").exists()

    config = configparser.ConfigParser()
    config.read(REPO_ROOT / ".coveragerc", encoding="utf-8")
    assert config.getboolean("run", "parallel")

    root_makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    quality_makefile = (REPO_ROOT / "scripts" / "make_quality.mk").read_text(
        encoding="utf-8"
    )
    for target in (
        "python-coverage-check:",
        "python-coverage-enforce:",
        "validation-shell-contracts:",
        "validation-wheel-smoke:",
        "validation-guarded-r:",
        "validation-static:",
        "report-test:",
        "all-checks:",
    ):
        assert target in quality_makefile
    assert "demo-report:" not in root_makefile + quality_makefile
    assert "tests/tools/run_validation.py" in quality_makefile
    assert "tests/tools/source_dependencies.py" in quality_makefile
    assert "PYTHON_COVERAGE_WORKERS" in root_makefile
    shard_tool = (
        REPO_ROOT / "tests" / "tools" / "python_test_shards.py"
    ).read_text(encoding="utf-8")
    assert '"tests/test_package_distribution.py"' in shard_tool
    assert "--dist=worksteal" in shard_tool
    assert "shell-test: validation-shell-contracts" in quality_makefile
    assert "validation-static: lint documentation-check" in quality_makefile
    assert 'version("ruff")' not in quality_makefile
    assert 'version("vulture")' not in quality_makefile
    assert '"$(RUFF_BIN)" check --no-cache' in quality_makefile
    assert '"$(VULTURE_BIN)"' in quality_makefile
    assert "--exit-zero" not in quality_makefile
    assert "skipping dead-code scan" not in quality_makefile


def test_selected_environment_lock_check_is_read_only_and_explicit() -> None:
    observed: dict[str, object] = {}

    def command_runner(
        command: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, "", "")

    python_bin = REPO_ROOT / ".venv" / "bin" / "python"
    TOOL.require_locked_environment(
        REPO_ROOT,
        python_bin,
        uv_bin="/explicit/uv",
        command_runner=command_runner,
    )

    assert observed["command"] == (
        "/explicit/uv",
        "sync",
        "--locked",
        "--check",
        "--active",
        "--group",
        "workflow",
        "--offline",
        "--no-python-downloads",
        "--project",
        str(REPO_ROOT),
        "--python",
        str(python_bin),
    )
    kwargs = observed["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["cwd"] == REPO_ROOT
    assert kwargs["check"] is False
    assert kwargs["env"]["VIRTUAL_ENV"] == str(python_bin.parent.parent)


def test_selected_environment_lock_check_reports_uv_failure() -> None:
    def command_runner(
        command: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 2, "", "controlled mismatch")

    with pytest.raises(
        TOOL.ValidationError,
        match=(
            "(?s)selected Python environment does not match uv.lock.*"
            "controlled mismatch"
        ),
    ):
        TOOL.require_locked_environment(
            REPO_ROOT,
            REPO_ROOT / ".venv" / "bin" / "python",
            uv_bin="/explicit/uv",
            command_runner=command_runner,
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
    assert not list(tmp_path.glob("*.log"))


def test_verbose_failure_streams_and_retains_log(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    outcome = TOOL.run_lanes(
        [python_lane("verbose-failure", "print('durable diagnostic'); raise SystemExit(7)")],
        REPO_ROOT,
        tmp_path,
        1,
        True,
    )

    try:
        result = outcome.results[0]
        assert outcome.status == 7
        assert result.retained_log is not None
        assert "durable diagnostic" in Path(result.retained_log).read_text(
            encoding="utf-8"
        )
        captured = capsys.readouterr()
        assert "durable diagnostic" in captured.out
        assert "FAIL verbose-failure status=7" in captured.err
        assert not list(tmp_path.glob("*.log"))
    finally:
        remove_retained_logs(outcome)


def test_verbose_peer_cancellation_streams_and_retains_both_logs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ready = tmp_path / "verbose-ready"
    slow_source = (
        "from pathlib import Path; import time; "
        "print('slow diagnostic', flush=True); "
        f"Path({str(ready)!r}).write_text('ready'); "
        "time.sleep(10)"
    )
    failure_source = (
        "from pathlib import Path; import sys, time; "
        f"p = Path({str(ready)!r}); "
        "deadline = time.monotonic() + 5; "
        "\nwhile not p.exists() and time.monotonic() < deadline: time.sleep(0.01)\n"
        "print('failing diagnostic', flush=True); sys.exit(9)"
    )
    outcome = TOOL.run_lanes(
        [
            python_lane("verbose-slow", slow_source),
            python_lane("verbose-controlled", failure_source),
        ],
        REPO_ROOT,
        tmp_path,
        2,
        True,
    )

    try:
        failure = next(
            result for result in outcome.results if result.name == "verbose-controlled"
        )
        cancelled = next(
            result for result in outcome.results if result.name == "verbose-slow"
        )
        assert outcome.status == 9
        assert failure.retained_log is not None
        assert cancelled.retained_log is not None
        assert "failing diagnostic" in Path(failure.retained_log).read_text(
            encoding="utf-8"
        )
        assert "slow diagnostic" in Path(cancelled.retained_log).read_text(
            encoding="utf-8"
        )
        captured = capsys.readouterr()
        assert "failing diagnostic" in captured.out
        assert "slow diagnostic" in captured.out
        assert "CANCELLED verbose-slow" in captured.err
        assert not list(tmp_path.glob("*.log"))
    finally:
        remove_retained_logs(outcome)


def test_first_failure_propagates_and_kills_child_process_group(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ready = tmp_path / "ready"
    survived = tmp_path / "grandchild-survived"
    slow_source = (
        "from pathlib import Path; import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', "
        f'"from pathlib import Path; import time; time.sleep(1.0); '
        f"Path({str(survived)!r}).write_text('survived')\"]); "
        f"Path({str(ready)!r}).write_text('ready'); "
        "time.sleep(10)"
    )
    failure_source = (
        "import sys, time; time.sleep(0.5); print('controlled failure'); sys.exit(7)"
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
        cancelled = next(result for result in outcome.results if result.name == "slow")
        assert failure.retained_log is not None
        assert cancelled.status == 128 + signal.SIGTERM
        assert cancelled.retained_log is not None
        assert "controlled failure" in Path(failure.retained_log).read_text(
            encoding="utf-8"
        )
        captured = capsys.readouterr()
        assert "FAIL controlled status=7" in captured.err
        assert "CANCELLED slow" in captured.err
        assert "controlled failure" in captured.err
        assert not list(tmp_path.glob("*.log"))
    finally:
        remove_retained_logs(outcome)


@pytest.mark.parametrize("verbose", [False, True])
def test_sigint_cleans_process_tree_and_restores_handler(
    tmp_path: Path,
    verbose: bool,
) -> None:
    ready = tmp_path / "interrupt-ready"
    survived = tmp_path / "interrupt-grandchild-survived"
    lane_source = (
        "from pathlib import Path; import subprocess, sys, time; "
        "print('interrupt diagnostic', flush=True); "
        "subprocess.Popen([sys.executable, '-c', "
        f'"from pathlib import Path; import time; time.sleep(1.0); '
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
        verbose,
    )
    interrupter.join(timeout=5)

    try:
        assert outcome.status == 130
        assert outcome.interrupted_by == signal.SIGINT
        assert signal.getsignal(signal.SIGINT) == prior_handler
        interrupted = outcome.results[0]
        assert interrupted.retained_log is not None
        assert "interrupt diagnostic" in Path(interrupted.retained_log).read_text(
            encoding="utf-8"
        )
        time.sleep(1.2)
        assert not survived.exists()
        assert not list(tmp_path.glob("*.log"))
    finally:
        remove_retained_logs(outcome)
