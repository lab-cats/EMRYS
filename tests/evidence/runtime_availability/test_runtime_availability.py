import csv
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from emrys.evidence.runtime_availability import inspector
from emrys.evidence.runtime_availability import _probes as runtime_probes
from emrys.evidence.runtime_availability._probes import (
    R_NAMESPACE_ROOT_OUTPUT_MARKER,
    run_checks,
)
from emrys.evidence.runtime_availability._profile_contract import CHOICE_IDS
from emrys.evidence.runtime_availability._runtime_model import (
    HASH_EXPECTED,
    HASH_PAYLOAD,
    R_NAMESPACE_PROBE_TIMEOUT_SECONDS,
    TOOL_PROBE_TIMEOUT_SECONDS,
)
from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeObservation,
)
from emrys.libraries.source_authority import controlled_python_argv

PROFILE_HEADER = "check_id\tcheck_type\ttarget\tprobe_args\texpected\tdescription"


def write_profile(path: Path, rows: list[list[str]]) -> Path:
    lines = [PROFILE_HEADER]
    lines.extend("\t".join(row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def fixture_checks(profile: Path) -> tuple[RuntimeCheck, ...]:
    return tuple(
        RuntimeCheck(
            row["check_id"],
            row["check_type"],
            row["target"],
            tuple(json.loads(row["probe_args"])),
            row["expected"],
        )
        for row in csv.DictReader(profile.read_text().splitlines(), delimiter="\t")
    )


def tool_row(
    check_id: str = "python",
    target: str = sys.executable,
) -> list[str]:
    return [
        check_id,
        "tool_version",
        target,
        json.dumps(["--version"]),
        r"^Python 3[.]",
        "Python runtime",
    ]


def executable(
    tmp_path: Path, name: str = "runtime-tool", body: str = "exit 0"
) -> Path:
    path = tmp_path / name
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def r_namespace_scenario(
    tmp_path: Path,
    check_id: str,
    target: str,
    expected: str = r"^1[.]2[.]3$",
) -> tuple[RuntimeCheck, dict[str, str]]:
    rscript = executable(tmp_path, "Rscript")
    return (
        RuntimeCheck(check_id, "r_namespace", target, (str(rscript),), expected),
        {
            "EMRYS_LOCAL_PILOT_R": "1",
            "EMRYS_RENV_LIBRARY": str(tmp_path / "library"),
        },
    )


def snakemake_check() -> RuntimeCheck:
    return replace(
        next(
            check
            for check in inspector.load_runtime_policy()
            if check.check_id == "snakemake"
        ),
        target=sys.executable,
        probe_args=tuple(
            controlled_python_argv(sys.executable, "-m", "snakemake", "--version")[1:]
        ),
    )


@pytest.mark.parametrize(
    ("code", "output", "timed_out"),
    [(7, "9.25.1", False), (0, "wrong version", False), (124, "", True)],
)
def test_snakemake_version_failure_prevents_startup(
    tmp_path: Path, code: int, output: str, timed_out: bool
) -> None:
    calls = []

    def run(argv, _stdin, _environment, _timeout):
        calls.append(argv)
        return code, output, 0.5, timed_out

    check = snakemake_check()
    result = run_checks(
        [check], environment={"TMPDIR": str(tmp_path)}, command_runner=run
    )[0]

    assert result.status == "fail"
    assert result.detail.startswith("Version")
    assert calls == [[sys.executable, *check.probe_args]]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    ("code", "timed_out"), [(0, False), (7, False), (124, False), (124, True)]
)
def test_snakemake_startup_is_isolated_and_reports_failure(
    tmp_path: Path, code: int, timed_out: bool
) -> None:
    environment = {
        "TMPDIR": str(tmp_path),
        "HOME": str(tmp_path / "operator-home"),
        "XDG_CACHE_HOME": str(tmp_path / "operator-cache"),
        "USER": "operator",
        "SNAKEMAKE_PROFILE": "operator-profile",
    }
    original = dict(environment)
    scratch_paths = []

    def run(argv, stdin, selected_environment, timeout):
        assert stdin is None
        assert timeout == TOOL_PROBE_TIMEOUT_SECONDS
        if "--version" in argv:
            assert selected_environment == original
            return 0, "9.25.1", 0.25, False
        scratch = Path(selected_environment["TMPDIR"])
        scratch_paths.append(scratch)
        assert scratch.parent == tmp_path
        assert scratch.is_dir()
        assert selected_environment == {
            **original,
            "HOME": str(scratch),
            "TMPDIR": str(scratch),
            "XDG_CACHE_HOME": str(scratch / "cache"),
        }
        assert argv == [
            *controlled_python_argv(sys.executable, "-m", "snakemake"),
            "--snakefile",
            os.devnull,
            "--profile",
            "none",
            "--workflow-profile",
            "none",
            "--directory",
            str(scratch),
            "--executor",
            "local",
            "--scheduler",
            "greedy",
            "--cores",
            "1",
            "--runtime-source-cache-path",
            str(scratch / "source-cache"),
            "--nocolor",
        ]
        (scratch / "cache").mkdir()
        (scratch / "cache" / "startup-marker").write_text("temporary")
        return code, "startup diagnostic", 0.5, timed_out

    check = snakemake_check()
    result = run_checks([check], environment=environment, command_runner=run)[0]

    assert result.check == check
    assert environment == original
    assert len(scratch_paths) == 1
    assert not scratch_paths[0].exists()
    assert not list(tmp_path.iterdir())
    assert "elapsed_seconds=0.500" in result.detail
    assert f"timeout_seconds={TOOL_PROBE_TIMEOUT_SECONDS}" in result.detail
    if code == 0:
        assert result.status == "pass"
        assert result.observed == "9.25.1"
        assert "minimal local Snakemake startup passed" in result.detail
        assert "version probe: elapsed_seconds=0.250;" in result.detail
        assert "startup passed: elapsed_seconds=0.500;" in result.detail
    else:
        assert result.status == "fail"
        assert result.observed == "startup diagnostic"
        assert "expected_exit_status=0" in result.detail
        if timed_out:
            assert "Snakemake startup timed out" in result.detail
            assert "; exit_status=" not in result.detail
        else:
            assert f"Snakemake startup failed; exit_status={code}" in result.detail


def test_snakemake_startup_temporary_state_failure_is_an_observation(
    tmp_path: Path,
) -> None:
    calls = []

    def run(argv, _stdin, _environment, _timeout):
        calls.append(argv)
        return 0, "9.25.1", 0.25, False

    check = snakemake_check()
    result = run_checks(
        [check],
        environment={"TMPDIR": str(tmp_path / "missing")},
        command_runner=run,
    )[0]

    assert result.status == "fail"
    assert result.observed == "unavailable"
    assert "Snakemake startup temporary state failed:" in result.detail
    assert calls == [[sys.executable, *check.probe_args]]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "login_variable", ["normal", None, "LOGNAME", "USER", "LNAME", "USERNAME"]
)
def test_real_snakemake_startup_exercises_login_identity(
    tmp_path: Path, login_variable: str | None
) -> None:
    environment = {
        "PATH": os.defpath,
        "HOME": str(tmp_path / "operator-home"),
        "TMPDIR": str(tmp_path),
        "XDG_CACHE_HOME": str(tmp_path / "operator-cache"),
        "SNAKEMAKE_PROFILE": str(tmp_path / "nonexistent-profile"),
    }
    if login_variable:
        environment["USER" if login_variable == "normal" else login_variable] = (
            "emrys-test"
        )
    results = []
    startup_directories = []

    def run(argv, stdin, selected_environment, timeout):
        if "--directory" in argv:
            startup_directories.append(Path(argv[argv.index("--directory") + 1]))
        if login_variable != "normal":
            module_index = argv.index("-m")
            assert argv[module_index + 1] == "snakemake"
            argv = [
                *argv[:module_index],
                "-c",
                "from unittest.mock import patch\n"
                "with patch('pwd.getpwuid', side_effect=KeyError('uid unavailable')):\n"
                " from snakemake.cli import main\n"
                " main()\n",
                *argv[module_index + 2 :],
            ]
        outcome = runtime_probes._run_command(
            argv, stdin, selected_environment, timeout
        )
        results.append(outcome)
        return outcome

    result = run_checks(
        [snakemake_check()], environment=environment, command_runner=run
    )[0]

    assert len(results) == 2
    assert results[0][0] == 0
    assert results[0][1] == "9.25.1"
    assert len(startup_directories) == 1
    assert not startup_directories[0].exists()
    assert not list(tmp_path.iterdir())
    if login_variable is None:
        assert result.status == "fail"
        assert "No username set in the environment" in result.observed
        assert "Snakemake startup failed; exit_status=1" in result.detail
    else:
        assert result.status == "pass"
        assert result.observed == "9.25.1"
        assert "Nothing to be done" in results[1][1]
        assert "user: emrys-test" in results[1][1].lower()
        assert "minimal local Snakemake startup passed" in result.detail


def test_missing_tool_and_version_mismatch_are_failures(tmp_path: Path) -> None:
    mismatch = tool_row("mismatch")
    mismatch[4] = "^definitely-not-python$"
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            tool_row(
                "missing", target=str(tmp_path / "emrys-tool-that-does-not-exist")
            ),
            mismatch,
        ],
    )
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, checks=fixture_checks(profile), environment={}
    )
    rows = {item.check.check_id: item for item in inspection.observations}
    assert rows["missing"].status == "fail"
    assert rows["mismatch"].status == "fail"


def test_hash_utility_and_path_visibility(tmp_path: Path) -> None:
    visible = tmp_path / "visible"
    visible.mkdir()
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "sha256",
                "hash_utility",
                sys.executable,
                json.dumps(["python_hashlib"]),
                "sha256",
                "Python hashlib",
            ],
            [
                "visible",
                "path_visibility",
                str(visible),
                json.dumps(["directory_readable"]),
                "readable",
                "Visible directory",
            ],
            [
                "missing",
                "path_visibility",
                str(tmp_path / "missing"),
                json.dumps(["file_readable"]),
                "readable",
                "Missing file",
            ],
        ],
    )
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, checks=fixture_checks(profile), environment={}
    )
    rows = {item.check.check_id: item for item in inspection.observations}
    assert rows["sha256"].status == "pass"
    assert rows["visible"].status == "pass"
    assert rows["missing"].status == "fail"


def test_python_hash_probe_uses_the_controlled_python_prefix() -> None:
    check = RuntimeCheck(
        check_id="sha256_python",
        check_type="hash_utility",
        target=sys.executable,
        probe_args=("python_hashlib",),
        expected="sha256",
    )
    calls: list[tuple[list[str], bytes | None, dict[str, str] | None, int]] = []

    def capture(
        argv: list[str],
        stdin: bytes | None,
        environment: dict[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        calls.append((argv, stdin, environment, timeout_seconds))
        return 0, HASH_EXPECTED, 0.125, False

    results = run_checks(
        [check],
        environment={"PATH": os.environ["PATH"]},
        command_runner=capture,
    )

    assert results[0].status == "pass"
    assert results[0].observed == HASH_EXPECTED
    assert (
        "SHA-256 tiny known-payload utility probe (not runtime-file hashing)"
        in results[0].detail
    )
    assert "elapsed_seconds=0.125; timeout_seconds=30" in results[0].detail
    assert calls == [
        (
            [
                *controlled_python_argv(sys.executable),
                "-c",
                "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())",
            ],
            HASH_PAYLOAD,
            {"PATH": os.environ["PATH"]},
            TOOL_PROBE_TIMEOUT_SECONDS,
        )
    ]


def test_gatk_probe_requires_exactly_one_declared_java_launcher() -> None:
    gatk = RuntimeCheck(
        check_id="gatk",
        check_type="tool_version",
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^GATK ",
    )

    result = run_checks([gatk], environment={})[0]

    assert result.status == "fail"
    assert result.observed == "unavailable"
    assert result.detail == "GATK probing requires exactly one declared Java launcher"


def test_guarded_rscript_version_probe_uses_its_standalone_information_mode(
    tmp_path: Path,
) -> None:
    rscript = tmp_path / "Rscript"
    rscript.write_text(
        "#!/bin/sh\n"
        'if [ "$#" -ne 1 ] || [ "$1" != --version ]; then\n'
        "    printf 'file name is missing\\n' >&2\n"
        "    exit 1\n"
        "fi\n"
        "printf 'Rscript (R) version 4.6.1 (2026-06-24)\\n'\n",
        encoding="utf-8",
    )
    rscript.chmod(0o755)
    check = RuntimeCheck(
        check_id="rscript",
        check_type="tool_version",
        target=str(rscript),
        probe_args=("--version",),
        expected=r"^Rscript [(]R[)] version 4[.]6[.]1(\s|$)",
    )

    result = run_checks(
        [check],
        environment={"EMRYS_LOCAL_PILOT_R": "1"},
    )[0]

    assert result.status == "pass"
    assert result.observed == "Rscript (R) version 4.6.1 (2026-06-24)"


def test_gatk_probe_reports_an_invalid_declared_java_environment(
    tmp_path: Path,
) -> None:
    java_path = tmp_path / "java"
    java_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    java_path.chmod(0o755)
    java = RuntimeCheck(
        check_id="java",
        check_type="tool_version",
        target=str(java_path),
        probe_args=("-version",),
        expected=r"^openjdk version",
    )
    gatk = RuntimeCheck(
        check_id="gatk",
        check_type="tool_version",
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^GATK ",
    )

    results = run_checks(
        [java, gatk],
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            "openjdk version 17",
            0.0,
            False,
        ),
        environment={},
    )

    assert results[0].status == "pass"
    assert results[1].status == "fail"
    assert results[1].observed == "unavailable"
    assert "canonical <JAVA_HOME>/bin/java" in results[1].detail


@pytest.mark.parametrize(
    ("version", "exit_code", "expected_status"),
    [
        ("4.6.1.0", 0, "pass"),
        ("4.6.1.1", 0, "fail"),
        ("4.6.1.0", 2, "fail"),
    ],
)
def test_tracked_gatk_policy_handles_official_launcher_prelude(
    tmp_path: Path,
    version: str,
    exit_code: int,
    expected_status: str,
) -> None:
    java = tmp_path / "java-home" / "bin" / "java"
    java.parent.mkdir(parents=True)
    java.write_text(
        "#!/bin/sh\n"
        '[ "$#" -eq 1 ] && [ "$1" = -version ] || exit 2\n'
        "printf '%s\\n' 'openjdk version \"17.0.1\"' >&2\n",
        encoding="utf-8",
    )
    java.chmod(0o755)
    gatk = tmp_path / "gatk"
    gatk.write_text(
        "#!/bin/sh\n"
        '[ "$#" -eq 1 ] && [ "$1" = --version ] || exit 96\n'
        f"[ \"${{JAVA_HOME:-}}\" = '{java.parent.parent}' ] || exit 91\n"
        f"[ \"$(command -v java)\" = '{java}' ] || exit 92\n"
        "printf 'Using GATK jar fixture.jar\\nRunning:\\n' >&2\n"
        "printf 'java -jar fixture.jar --version\\n' >&2\n"
        f"printf 'The Genome Analysis Toolkit (GATK) v{version}\\n'\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    gatk.chmod(0o755)
    policy_checks = inspector.load_runtime_policy()
    selected = {
        check.check_id: check
        for check in policy_checks
        if check.check_id in {"java", "gatk"}
    }
    checks = [
        replace(selected["java"], target=str(java)),
        replace(selected["gatk"], target=str(gatk)),
    ]

    results = run_checks(
        checks,
        environment={"PATH": "/usr/bin:/bin"},
    )

    assert results[0].status == "pass"
    assert results[1].status == expected_status
    assert "Using GATK jar fixture.jar Running:" in results[1].observed
    assert f"The Genome Analysis Toolkit (GATK) v{version}" in results[1].observed


def test_tool_probe_normalizes_launch_and_version_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    check = RuntimeCheck(
        check_id="tool",
        check_type="tool_version",
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^Python 3[.]",
    )

    def fail_launch(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected launch failure")

    monkeypatch.setattr(subprocess, "run", fail_launch)
    launch_failure = run_checks([check], environment={})[0]
    assert launch_failure.status == "fail"
    assert launch_failure.observed == "injected launch failure"
    assert launch_failure.detail == (
        "Version probe failed; exit_status=127; expected_exit_status=0"
    )

    mismatch = run_checks(
        [check],
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            "unexpected",
            0.0,
            False,
        ),
        environment={},
    )[0]
    assert mismatch.status == "fail"
    assert mismatch.observed == "unexpected"
    assert mismatch.detail == (
        "Version output did not match expected regex; exit_status=0; expected_exit_status=0"
    )


@pytest.mark.parametrize(
    ("check_type", "expected_timeout", "detail_prefix"),
    [
        (
            "tool_version",
            TOOL_PROBE_TIMEOUT_SECONDS,
            "Version probe timed out",
        ),
        (
            "r_namespace",
            R_NAMESPACE_PROBE_TIMEOUT_SECONDS,
            "R namespace probe timed out",
        ),
        (
            "hash_utility",
            TOOL_PROBE_TIMEOUT_SECONDS,
            "SHA-256 probe timed out",
        ),
    ],
)
def test_default_runner_forwards_distinct_timeout_and_records_elapsed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_type: str,
    expected_timeout: int,
    detail_prefix: str,
) -> None:
    runtime_tool = executable(tmp_path)
    check = RuntimeCheck(
        check_id="bounded",
        check_type=check_type,
        target="FixturePackage" if check_type == "r_namespace" else str(runtime_tool),
        probe_args=(
            (str(runtime_tool),)
            if check_type == "r_namespace"
            else ("python_hashlib",)
            if check_type == "hash_utility"
            else ("--version",)
        ),
        expected=r"^1[.]2[.]3$",
    )
    observed_timeouts: list[int] = []
    clock = iter((10.0, 10.0 + expected_timeout + 0.5))

    def expire(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[bytes]:
        timeout = kwargs["timeout"]
        assert isinstance(timeout, int)
        observed_timeouts.append(timeout)
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(runtime_probes.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(runtime_probes.subprocess, "run", expire)

    result = run_checks(
        [check],
        environment={
            "EMRYS_LOCAL_PILOT_R": "1",
            "EMRYS_RENV_LIBRARY": str(tmp_path / "library"),
        },
    )[0]

    assert observed_timeouts == [expected_timeout]
    assert result.status == "fail"
    assert result.detail == (
        f"{detail_prefix}; elapsed_seconds={expected_timeout + 0.5:.3f}; "
        f"timeout_seconds={expected_timeout}"
    )


def test_picard_version_probe_accepts_only_its_exact_exit_one_contract(
    tmp_path: Path,
) -> None:
    java = tmp_path / "java-home" / "bin" / "java"
    jar = tmp_path / "picard.jar"
    java.parent.mkdir(parents=True)
    java.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    java.chmod(0o755)
    jar.write_bytes(b"bound picard jar")
    picard = RuntimeCheck(
        check_id="picard",
        check_type="tool_version_exit_1",
        target=str(java),
        probe_args=("-jar", str(jar), "MarkDuplicates", "--version"),
        expected=r"^Version:3[.]1[.]1$",
    )

    observed_argv: list[tuple[str, ...]] = []

    def exact_picard_probe(
        argv: Sequence[str],
        _stdin: str | None,
        _environment: Mapping[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        observed_argv.append(tuple(argv))
        assert timeout_seconds == TOOL_PROBE_TIMEOUT_SECONDS
        return 1, "Version:3.1.1", 0.25, False

    passed = run_checks([picard], command_runner=exact_picard_probe, environment={})[0]

    assert passed.status == "pass"
    assert passed.observed == "Version:3.1.1"
    assert passed.detail == (
        f"Resolved executable: {java}; version probe: "
        "elapsed_seconds=0.250; timeout_seconds=30"
    )
    assert observed_argv == [
        (str(java), "-jar", str(jar), "MarkDuplicates", "--version")
    ]

    for changed, code in (
        (replace(picard, check_type="tool_version"), 1),
        (picard, 0),
        (picard, 2),
    ):
        rejected = run_checks(
            [changed],
            command_runner=lambda _argv, _stdin, _environment, _timeout, c=code: (
                c,
                "Version:3.1.1",
                0.0,
                False,
            ),
            environment={},
        )[0]
        assert rejected.status == "fail"
        assert rejected.observed == "Version:3.1.1"
        expected_code = 1 if changed.check_type == "tool_version_exit_1" else 0
        assert rejected.detail == (
            f"Version probe failed; exit_status={code}; expected_exit_status={expected_code}"
        )

    wrong_output = run_checks(
        [picard],
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            1,
            "Version:3.1.1 extra",
            0.0,
            False,
        ),
        environment={},
    )[0]
    assert wrong_output.status == "fail"
    assert wrong_output.detail == (
        "Version output did not match expected regex; exit_status=1; expected_exit_status=1"
    )


@pytest.mark.parametrize(
    ("check_type", "probe_args", "expected_detail"),
    [
        ("r_namespace", ("/missing/Rscript",), "Rscript executable was not found"),
        ("hash_utility", ("python_hashlib",), "Hash executable was not found"),
    ],
)
def test_namespace_and_hash_probes_reject_missing_executables_without_running(
    check_type: str,
    probe_args: tuple[str, ...],
    expected_detail: str,
) -> None:
    check = RuntimeCheck(
        check_id="missing",
        check_type=check_type,
        target="/missing/emrys-runtime-tool-that-does-not-exist",
        probe_args=probe_args,
        expected=r".*",
    )

    result = run_checks(
        [check],
        command_runner=lambda _argv, _stdin, _environment, _timeout: pytest.fail(
            "missing executable must stop before command execution"
        ),
        environment={},
    )[0]

    assert result.status == "fail"
    assert result.observed == "unavailable"
    assert result.detail == expected_detail


@pytest.mark.parametrize("output", ["", "hash backend failed"])
def test_python_hash_probe_reports_command_and_digest_failures(
    tmp_path: Path,
    output: str,
) -> None:
    python = executable(tmp_path, "python")
    check = RuntimeCheck(
        check_id="sha256",
        check_type="hash_utility",
        target=str(python),
        probe_args=("python_hashlib",),
        expected="sha256",
    )
    calls: list[tuple[list[str], bytes | None]] = []

    def fail(
        argv: list[str],
        stdin: bytes | None,
        _environment: dict[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        calls.append((argv, stdin))
        assert timeout_seconds == TOOL_PROBE_TIMEOUT_SECONDS
        return 23, output, 0.5, False

    result = run_checks([check], command_runner=fail, environment={})[0]

    assert calls[0][1] == HASH_PAYLOAD
    assert result.status == "fail"
    assert result.observed == (output or "exit 23")
    assert result.detail == (
        "SHA-256 probe failed; exit_status=23; expected_exit_status=0"
    )

    mismatch = run_checks(
        [check],
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            "not-a-digest",
            0.0,
            False,
        ),
        environment={},
    )[0]
    assert mismatch.status == "fail"
    assert mismatch.observed == "not-a-digest"
    assert mismatch.detail == (
        "SHA-256 digest mismatch; exit_status=0; expected_exit_status=0"
    )


def test_guarded_r_namespace_probe_binds_startup_and_selected_library(
    tmp_path: Path,
) -> None:
    check, environment = r_namespace_scenario(tmp_path, "r_guarded", "GuardedPackage")
    library = Path(environment["EMRYS_RENV_LIBRARY"])
    library.mkdir()
    calls: list[tuple[list[str], bytes | None, dict[str, str] | None, int]] = []
    resolved_package = (tmp_path / "renv-cache" / "GuardedPackage").resolve()

    def capture(
        argv: list[str],
        stdin: bytes | None,
        observed_environment: dict[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        calls.append((argv, stdin, observed_environment, timeout_seconds))
        encoded_root = str(resolved_package).encode("utf-8").hex()
        return (
            0,
            f"1.2.3{R_NAMESPACE_ROOT_OUTPUT_MARKER}{encoded_root}",
            12.5,
            False,
        )

    result = run_checks(
        [check],
        environment=environment,
        command_runner=capture,
    )[0]

    assert result.status == "pass"
    argv, stdin, observed_environment, timeout_seconds = calls[0]
    assert argv[:5] == [
        check.probe_args[0],
        "--no-environ",
        "--no-site-file",
        "--no-restore",
        "--no-save",
    ]
    assert argv[-2:] == ["GuardedPackage", str(library)]
    assert "find.package" in argv[6]
    assert (
        "tryCatch(suppressWarnings(loadNamespace(p, lib.loc=lib)), "
        "error=function(e) {message(conditionMessage(e)); NULL})" in argv[6]
    )
    assert "identical(expected, declared)" not in argv[6]
    assert "identical(pkg, expected)" in argv[6]
    assert "identical(where, expected)" in argv[6]
    assert R_NAMESPACE_ROOT_OUTPUT_MARKER in argv[6]
    assert stdin is None
    assert observed_environment == environment
    assert timeout_seconds == R_NAMESPACE_PROBE_TIMEOUT_SECONDS
    assert result.observed == "1.2.3"
    assert result.resolved_path == resolved_package
    assert result.detail == (
        f"Resolved R package root: {resolved_package}; "
        "elapsed_seconds=12.500; "
        f"timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


@pytest.mark.parametrize(
    "output",
    [
        "1.2.3",
        f"1.2.3{R_NAMESPACE_ROOT_OUTPUT_MARKER}",
        f"1.2.3{R_NAMESPACE_ROOT_OUTPUT_MARKER}not-hex",
        f"1.2.3{R_NAMESPACE_ROOT_OUTPUT_MARKER}2f{R_NAMESPACE_ROOT_OUTPUT_MARKER}2f",
    ],
)
def test_guarded_r_namespace_rejects_missing_or_malformed_root_identity(
    tmp_path: Path,
    output: str,
) -> None:
    check, environment = r_namespace_scenario(tmp_path, "r_guarded", "GuardedPackage")

    result = run_checks(
        [check],
        environment=environment,
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            output,
            0.5,
            False,
        ),
    )[0]

    assert result.status == "fail"
    assert result.resolved_path is None
    assert result.detail == (
        "R namespace probe did not report its exact canonical root; "
        "exit_status=0; expected_exit_status=0; "
        "elapsed_seconds=0.500; "
        f"timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


def test_r_namespace_timeout_is_distinct_bounded_and_fail_closed(
    tmp_path: Path,
) -> None:
    check, environment = r_namespace_scenario(tmp_path, "r_timeout", "SlowPackage")
    observed_timeouts: list[int] = []

    def time_out(
        _argv: list[str],
        _stdin: bytes | None,
        _environment: dict[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        observed_timeouts.append(timeout_seconds)
        return 124, "fixture timeout", 120.25, True

    result = run_checks(
        [check],
        command_runner=time_out,
        environment=environment,
    )[0]

    assert observed_timeouts == [R_NAMESPACE_PROBE_TIMEOUT_SECONDS]
    assert R_NAMESPACE_PROBE_TIMEOUT_SECONDS > TOOL_PROBE_TIMEOUT_SECONDS
    assert result.status == "fail"
    assert result.observed == "fixture timeout"
    assert result.detail == (
        f"R namespace probe timed out; elapsed_seconds=120.250; timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


@pytest.mark.parametrize(
    ("code", "output", "detail_prefix", "include_root", "elapsed"),
    [
        pytest.param(
            124,
            "real child exit",
            "R namespace probe failed",
            False,
            0.25,
            id="real-exit-124-is-not-timeout",
        ),
        pytest.param(
            0,
            "Warning message: replacing previous import 1.2.3",
            "Namespace version did not match expected regex",
            True,
            0.0,
            id="strict-version-output",
        ),
        *(
            pytest.param(code, output, detail, False, 0.0, id=f"exit-{code}-{kind}")
            for code, detail in (
                (42, "R namespace is unavailable in the selected library"),
                (43, "R did not select the admitted library first"),
                (44, "R namespace did not resolve to its exact selected package root"),
            )
            for kind, output in (
                ("empty", ""),
                ("diagnostic", "namespace dependency unavailable"),
            )
        ),
    ],
)
def test_r_namespace_failures_retain_distinct_probe_outcomes(
    tmp_path: Path,
    code: int,
    output: str,
    detail_prefix: str,
    include_root: bool,
    elapsed: float,
) -> None:
    check, environment = r_namespace_scenario(
        tmp_path,
        "r_fixture",
        "Fixture",
        r"^1[.]2[.]3$" if include_root else r"^1[.]0[.]0$",
    )
    command_output = output
    if include_root:
        command_output += (
            R_NAMESPACE_ROOT_OUTPUT_MARKER
            + str(tmp_path / "library/Fixture").encode().hex()
        )

    result = run_checks(
        [check],
        environment=environment,
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            code,
            command_output,
            elapsed,
            False,
        ),
    )[0]

    assert result.status == "fail"
    assert result.observed == (output or f"exit {code}")
    assert result.detail == (
        f"{detail_prefix}; exit_status={code}; expected_exit_status=0; "
        f"elapsed_seconds={elapsed:.3f}; "
        f"timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


def test_r_namespace_retains_real_loader_error_without_installing(
    tmp_path: Path,
) -> None:
    rscript = shutil.which("Rscript")
    if rscript is None:
        pytest.skip("Rscript is required for the real namespace loader fault")
    library = tmp_path / "library"
    package = library / "BrokenPackage"
    package.mkdir(parents=True)
    (package / "DESCRIPTION").write_text(
        "Package: BrokenPackage\nVersion: 1.0.0\n", encoding="utf-8"
    )
    (package / "NAMESPACE").write_text(
        "importFrom(utils, emrys_cv02_missing_export)\n", encoding="utf-8"
    )
    check = RuntimeCheck(
        "r_broken", "r_namespace", "BrokenPackage", (rscript,), r"^1[.]0[.]0$"
    )

    result = run_checks(
        [check],
        environment={
            "PATH": os.defpath,
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            "R_PROFILE_USER": os.devnull,
            "R_LIBS_USER": str(library),
            "R_LIBS_SITE": "",
            "EMRYS_RENV_LIBRARY": str(library),
        },
    )[0]

    assert result.status == "fail"
    assert "emrys_cv02_missing_export" in result.observed
    assert result.observed != "exit 42"
    assert "exit_status=42; expected_exit_status=0" in result.detail
    assert result.resolved_path is None


def test_direct_inspection_uses_explicit_probe_environment(tmp_path: Path) -> None:
    library = tmp_path / "library"
    package_root = library / "GuardedPackage"
    package_root.mkdir(parents=True)
    encoded_root = str(package_root.resolve(strict=True)).encode("utf-8").hex()
    fake = tmp_path / "Rscript"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        '[[ "${EMRYS_DOCTOR_TEST:-}" == "guarded" ]] || exit 43\n'
        f"printf '1.2.3{R_NAMESPACE_ROOT_OUTPUT_MARKER}{encoded_root}'\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "guarded_namespace",
                "r_namespace",
                "GuardedPackage",
                json.dumps([str(fake)]),
                r"^1[.]2[.]3$",
                "Guarded R namespace",
            ]
        ],
    )

    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(),
        profile,
        checks=fixture_checks(profile),
        environment={
            "EMRYS_DOCTOR_TEST": "guarded",
            "EMRYS_LOCAL_PILOT_R": "1",
            "EMRYS_RENV_LIBRARY": str(library),
            "PATH": os.environ["PATH"],
        },
    )

    assert inspection.required_ready
    assert inspection.profile_bytes == profile.read_bytes()
    observation = inspection.observations[0]
    assert type(observation) is RuntimeObservation
    assert type(observation.check) is RuntimeCheck
    assert observation.check.target == "GuardedPackage"
    assert observation.check.probe_args == (str(fake),)
    assert observation.status == "pass"
    assert observation.observed == "1.2.3"
    assert isinstance(observation.resolved_path, Path)
    assert observation.resolved_path == package_root.resolve(strict=True)
    with pytest.raises(FrozenInstanceError):
        observation.check.target = "ChangedPackage"
    with pytest.raises(FrozenInstanceError):
        observation.status = "fail"


@pytest.mark.parametrize(
    "data",
    [
        b"check_id\ttarget\n",  # missing mandatory choices
        b"check_id\ttarget\n" + b"bash\t/bin/bash\n" * 12,
        b"check_id\ttarget\n"
        + b"".join(f"{key}\trelative/path\n".encode() for key in CHOICE_IDS),
        b"check_id\tcheck_type\n",  # retired editable probe grammar
    ],
)
def test_malformed_runtime_choices_are_rejected(data: bytes, tmp_path: Path) -> None:
    with pytest.raises(inspector.RuntimeInspectionError):
        inspector.runtime_profile_checks(data, tmp_path)


def test_profile_symlink_is_rejected(tmp_path: Path) -> None:
    profile = tmp_path / "profile.tsv"
    profile.write_bytes(
        inspector.runtime_profile_bytes({key: tmp_path / key for key in CHOICE_IDS})
    )
    link = tmp_path / "profile-link.tsv"
    link.symlink_to(profile)
    with pytest.raises(inspector.RuntimeInspectionError, match="non-symlink"):
        inspector.load_runtime_profile_contract(link, tmp_path)


def _managed_seal_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runtime = tmp_path / "donor/runtime"
    managed = runtime / "managed"
    managed.mkdir(parents=True)
    choices = {key: managed / key for key in CHOICE_IDS}
    choices["python"] = Path(sys.executable)
    choices["renv_library"].mkdir()
    for key, path in choices.items():
        if key not in {"python", "renv_library"}:
            path.write_bytes(f"fixed {key}\n".encode())
            path.chmod(0o755)
    data = inspector.runtime_profile_bytes(choices)
    checks = inspector.runtime_profile_checks(data, tmp_path)
    for check in checks:
        if check.check_type == "r_namespace":
            package = choices["renv_library"] / check.target
            package.mkdir()
            (package / "DESCRIPTION").write_text(
                f"Package: {check.target}\nVersion: 1.0\n"
            )

    def observe(checks, *, environment):
        return tuple(
            RuntimeObservation(
                check,
                "pass",
                f"fixed {check.check_id}",
                "fresh probe",
                (
                    Path(
                        environment.get("RENV_LIBRARY")
                        or environment["EMRYS_RENV_LIBRARY"]
                    )
                    / check.target
                ).resolve()
                if check.check_type == "r_namespace"
                else None,
            )
            for check in checks
        )

    monkeypatch.setattr(inspector, "run_checks", observe)
    inspection = inspector.inspect_runtime_profile_bytes(
        data,
        runtime / "runtime.tsv",
        checks=checks,
        environment={"RENV_LIBRARY": str(choices["renv_library"])},
    )
    return runtime / "shared.json", inspection


def _borrowed_inspection(seal: Path, tmp_path: Path):
    data = inspector.shared_runtime_profile_bytes(
        seal, seal.read_bytes(), Path(sys.executable)
    )
    checks = inspector.runtime_profile_checks(data, tmp_path)
    library = next(check.target for check in checks if check.check_id == "renv_library")
    return inspector.inspect_runtime_profile_bytes(
        data,
        tmp_path / "borrower/runtime.tsv",
        checks=checks,
        environment={"RENV_LIBRARY": library},
    )


@pytest.mark.parametrize("defect", ("empty", "missing", "failed"))
def test_sealing_requires_complete_fresh_passing_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    observations = original.observations
    if defect == "empty":
        observations = ()
    elif defect == "missing":
        observations = observations[:-1]
    else:
        observations = (
            replace(observations[0], status="fail"),
            *observations[1:],
        )
    with pytest.raises(inspector.RuntimeInspectionError, match="every probe|roster"):
        inspector.runtime_seal_bytes(replace(original, observations=observations), seal)
    assert not seal.exists()


@pytest.mark.parametrize("external", (False, True))
def test_seal_requires_native_symlink_targets_inside_managed_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, external: bool
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    native = seal.parent / "managed/star"
    target = (tmp_path if external else native.parent) / "star-target"
    native.rename(target)
    native.symlink_to(target)
    if external:
        with pytest.raises(inspector.RuntimeInspectionError, match="escaped"):
            inspector.runtime_seal_bytes(original, seal)
    else:
        seal.write_bytes(inspector.runtime_seal_bytes(original, seal))
        assert inspector.runtime_file_bindings(_borrowed_inspection(seal, tmp_path))


@pytest.mark.parametrize("mode", ("borrowed", "donor"))
@pytest.mark.parametrize("changed", ("native", "r_package", "version"))
def test_seal_rejects_changed_content_even_when_version_probes_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    changed: str,
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    seal.write_bytes(inspector.runtime_seal_bytes(original, seal))
    selected = _borrowed_inspection(seal, tmp_path) if mode == "borrowed" else original
    options = {} if mode == "borrowed" else {"donor_seal": seal}
    assert inspector.runtime_file_bindings(selected, **options)
    target = next(
        item
        for item in selected.observations
        if item.check.check_id
        == ("star" if changed != "r_package" else "r_variant_annotation")
    )
    if changed == "version":
        selected = replace(
            selected,
            observations=tuple(
                replace(item, observed="changed version") if item is target else item
                for item in selected.observations
            ),
        )
    elif changed == "native":
        Path(target.check.target).write_bytes(
            b"different implementation, same version\n"
        )
    else:
        assert target.resolved_path is not None
        (target.resolved_path / "DESCRIPTION").write_text(
            "different package bytes, same version\n"
        )
    assert selected.required_ready
    with pytest.raises(
        inspector.RuntimeInspectionError, match="content or version changed"
    ):
        inspector.runtime_file_bindings(selected, **options)


def test_shared_selector_retains_exact_reference_and_borrower_python_and_r_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    seal.write_bytes(inspector.runtime_seal_bytes(original, seal))
    borrower_python = tmp_path / "borrower-python"
    borrower_python.write_bytes(b"separate borrower interpreter\n")
    data = inspector.shared_runtime_profile_bytes(
        seal, seal.read_bytes(), borrower_python
    )
    retained = tmp_path / "run/contract/runtime-profiles/attempt.tsv"
    retained.parent.mkdir(parents=True)
    retained.write_bytes(data)
    loaded, checks = inspector.load_runtime_profile_contract(
        retained, tmp_path / "borrower-package"
    )
    assert loaded == data
    by_id = {check.check_id: check for check in checks}
    assert all(
        by_id[key].target == str(borrower_python) for key in inspector.PYTHON_CHECK_IDS
    )
    assert by_id["renv_project"].target == str(tmp_path / "borrower-package")
    assert by_id["star"].target == str(seal.parent / "managed/star")
    seal.write_bytes(seal.read_bytes() + b"\n")
    with pytest.raises(inspector.RuntimeInspectionError, match="SHA-256"):
        inspector.load_runtime_profile_contract(retained, tmp_path)


def test_shared_selector_retains_probe_targets_when_sealed_content_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    data = inspector.runtime_seal_bytes(original, seal)
    seal.write_bytes(data)
    selection = inspector.shared_runtime_profile_bytes(seal, data, Path(sys.executable))
    missing = seal.parent / "managed/star"
    missing.unlink()

    checks = inspector.runtime_profile_checks(selection, tmp_path)

    assert next(check.target for check in checks if check.check_id == "star") == str(
        missing
    )
    with pytest.raises(inspector.RuntimeInspectionError):
        inspector.load_runtime_seal(seal)


@pytest.mark.parametrize(
    "defect",
    ("missing", "claim", "trailing_row", "extra_column", "bad_sha", "unknown_header"),
)
def test_shared_selector_fails_closed_without_a_complete_unclaimed_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    data = inspector.runtime_seal_bytes(original, seal)
    seal.write_bytes(data)
    selection = inspector.shared_runtime_profile_bytes(seal, data, Path(sys.executable))
    if defect == "missing":
        seal.unlink()
    elif defect == "claim":
        (seal.parent / "maintenance.lock").write_bytes(b"incomplete owner\n")
    elif defect == "trailing_row":
        selection += selection.splitlines(keepends=True)[1]
    elif defect == "extra_column":
        selection = selection.rstrip(b"\n") + b"\textra\n"
    elif defect == "bad_sha":
        selection = (
            selection.splitlines()[0]
            + b"\n"
            + str(seal).encode()
            + b"\tbad\t"
            + sys.executable.encode()
            + b"\n"
        )
    else:
        selection = selection.replace(b"seal_path", b"unknown")
    with pytest.raises(inspector.RuntimeInspectionError):
        inspector.runtime_profile_checks(selection, tmp_path)


@pytest.mark.parametrize(
    "defect",
    (
        "extra",
        "bool_version",
        "missing_binding",
        "kind",
        "duplicate_binding",
        "digest",
        "noncanonical",
        "oversize",
        "symlink",
    ),
)
def test_seal_closed_record_and_stable_file_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    from emrys.contracts.orchestration import api as contracts

    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    record = json.loads(inspector.runtime_seal_bytes(original, seal))
    if defect == "extra":
        record["status"] = "passed"
    elif defect == "bool_version":
        record["schema_version"] = True
    elif defect == "missing_binding":
        record["bindings"].pop()
    elif defect == "kind":
        record["bindings"][0]["identity_kind"] = "package_tree"
    elif defect == "duplicate_binding":
        record["bindings"][1] = record["bindings"][0]
    elif defect == "digest":
        record["bindings"][0]["sha256"] = "not-a-digest"
    data = contracts.canonical_json_bytes(record)
    if defect == "noncanonical":
        data += b"\n"
    if defect == "oversize":
        data += b" " * (64 * 1024)
    if defect == "symlink":
        target = tmp_path / "external-seal"
        target.write_bytes(data)
        seal.symlink_to(target)
    else:
        seal.write_bytes(data)
    with pytest.raises(inspector.RuntimeInspectionError):
        inspector.load_runtime_seal(seal)


@pytest.mark.parametrize("external", (False, True))
def test_seal_accepts_only_managed_contained_r_package_symlink_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    external: bool,
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    observed = next(
        item
        for item in original.observations
        if item.check.check_id == "r_variant_annotation"
    )
    package = observed.resolved_path
    assert package is not None
    target = (
        tmp_path / "external-package"
        if external
        else seal.parent / "managed/package-cache"
    )
    package.rename(target)
    package.symlink_to(target, target_is_directory=True)
    original = replace(
        original,
        observations=tuple(
            replace(item, resolved_path=target) if item is observed else item
            for item in original.observations
        ),
    )
    if external:
        with pytest.raises(inspector.RuntimeInspectionError, match="escaped"):
            inspector.runtime_seal_bytes(original, seal)
    else:
        seal.write_bytes(inspector.runtime_seal_bytes(original, seal))
        assert inspector.runtime_file_bindings(_borrowed_inspection(seal, tmp_path))


@pytest.mark.parametrize("inside", (False, True))
def test_extra_analysis_dependencies_are_freshly_bound_without_extending_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    inside: bool,
) -> None:
    seal, original = _managed_seal_fixture(tmp_path, monkeypatch)
    seal.write_bytes(inspector.runtime_seal_bytes(original, seal))
    borrowed = _borrowed_inspection(seal, tmp_path)
    resource = (seal.parent / "managed" if inside else tmp_path) / "extra-resource"
    resource.write_bytes(b"new module resource\n")
    check = RuntimeCheck(
        "extra_resource",
        "path_visibility",
        str(resource),
        ("file_readable",),
        "readable",
    )
    borrowed = replace(
        borrowed,
        observations=(
            *borrowed.observations,
            RuntimeObservation(check, "pass", "readable", "fresh"),
        ),
    )
    if inside:
        with pytest.raises(inspector.RuntimeInspectionError, match="not covered"):
            inspector.runtime_file_bindings(
                borrowed, explicit_file_ids=frozenset({check.check_id})
            )
    else:
        bindings = inspector.runtime_file_bindings(
            borrowed, explicit_file_ids=frozenset({check.check_id})
        )
        first = next(item for item in bindings if item.check_id == check.check_id)
        resource.write_bytes(b"changed independent resource\n")
        next_binding = next(
            item
            for item in inspector.runtime_file_bindings(
                borrowed, explicit_file_ids=frozenset({check.check_id})
            )
            if item.check_id == check.check_id
        )
        assert first.sha256 != next_binding.sha256
