import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from emrys.evidence.runtime_availability import inspector
from emrys.evidence.runtime_availability import _probes as runtime_probes
from emrys.evidence.runtime_availability._probes import (
    R_NAMESPACE_ROOT_OUTPUT_MARKER,
    run_checks,
)
from emrys.evidence.runtime_availability._profile_contract import load_profile
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

REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE_HEADER = (
    "check_id\tcheck_type\truntime_context\trequired\ttarget\tprobe_args\t"
    "expected\tdescription"
)


def write_profile(path: Path, rows: list[list[str]]) -> Path:
    lines = [PROFILE_HEADER]
    lines.extend("\t".join(row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def tool_row(
    check_id: str = "python",
    context: str = "any",
    required: str = "true",
    target: str = sys.executable,
) -> list[str]:
    return [
        check_id,
        "tool_version",
        context,
        required,
        target,
        json.dumps(["--version"]),
        r"^Python 3[.]",
        "Python runtime",
    ]


def test_context_mismatch_is_blocked_or_not_checked(tmp_path: Path) -> None:
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            tool_row("required_cluster", "cluster_batch", "true"),
            tool_row("optional_cluster", "cluster_batch", "false"),
        ],
    )
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, "local"
    )
    rows = {item.check.check_id: item for item in inspection.observations}
    assert rows["required_cluster"].status == "blocked"
    assert rows["optional_cluster"].status == "not_checked"


def test_missing_tool_and_version_mismatch_are_failures(tmp_path: Path) -> None:
    mismatch = tool_row("mismatch")
    mismatch[6] = "^definitely-not-python$"
    profile = write_profile(
        tmp_path / "profile.tsv",
        [tool_row("missing", target="emrys-tool-that-does-not-exist"), mismatch],
    )
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, "local"
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
                "any",
                "true",
                sys.executable,
                json.dumps(["python_hashlib"]),
                "sha256",
                "Python hashlib",
            ],
            [
                "visible",
                "path_visibility",
                "any",
                "true",
                str(visible),
                json.dumps(["directory_readable"]),
                "readable",
                "Visible directory",
            ],
            [
                "missing",
                "path_visibility",
                "any",
                "true",
                str(tmp_path / "missing"),
                json.dumps(["file_readable"]),
                "readable",
                "Missing file",
            ],
        ],
    )
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, "local"
    )
    rows = {item.check.check_id: item for item in inspection.observations}
    assert rows["sha256"].status == "pass"
    assert rows["visible"].status == "pass"
    assert rows["missing"].status == "fail"


def test_python_hash_probe_uses_the_controlled_python_prefix() -> None:
    check = RuntimeCheck(
        check_id="sha256_python",
        check_type="hash_utility",
        runtime_context="local",
        required=True,
        target=sys.executable,
        probe_args=("python_hashlib",),
        expected="sha256",
        description="controlled Python hashlib",
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
        "local",
        environment={"PATH": os.environ["PATH"]},
        command_runner=capture,
    )

    assert results[0].status == "pass"
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
        runtime_context="local",
        required=True,
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^GATK ",
        description="GATK runtime",
    )

    result = run_checks([gatk], "local")[0]

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
        runtime_context="local",
        required=True,
        target=str(rscript),
        probe_args=("--version",),
        expected=r"^Rscript [(]R[)] version 4[.]6[.]1(\s|$)",
        description="Rscript runtime",
    )

    result = run_checks(
        [check],
        "local",
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
        runtime_context="local",
        required=True,
        target=str(java_path),
        probe_args=("-version",),
        expected=r"^openjdk version",
        description="Java runtime",
    )
    gatk = RuntimeCheck(
        check_id="gatk",
        check_type="tool_version",
        runtime_context="local",
        required=True,
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^GATK ",
        description="GATK runtime",
    )

    results = run_checks(
        [java, gatk],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            "openjdk version 17",
            0.0,
            False,
        ),
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
    _, policy_checks = load_profile(
        REPO_ROOT / "src/emrys/resources/runtime/runtime_policy.tsv"
    )
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
        "local",
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
        runtime_context="local",
        required=True,
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^Python 3[.]",
        description="tool runtime",
    )

    def fail_launch(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected launch failure")

    monkeypatch.setattr(subprocess, "run", fail_launch)
    launch_failure = run_checks([check], "local")[0]
    assert launch_failure.status == "fail"
    assert launch_failure.observed == "injected launch failure"
    assert launch_failure.detail == "Version probe failed"

    mismatch = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            "unexpected",
            0.0,
            False,
        ),
    )[0]
    assert mismatch.status == "fail"
    assert mismatch.observed == "unexpected"
    assert mismatch.detail == "Version output did not match expected regex"


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
    executable = tmp_path / "runtime-tool"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    check = RuntimeCheck(
        check_id="bounded",
        check_type=check_type,
        runtime_context="local",
        required=True,
        target="FixturePackage" if check_type == "r_namespace" else str(executable),
        probe_args=(
            (str(executable),)
            if check_type == "r_namespace"
            else ("python_hashlib",)
            if check_type == "hash_utility"
            else ("--version",)
        ),
        expected=r"^1[.]2[.]3$",
        description="bounded probe",
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

    result = run_checks([check], "local")[0]

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
        runtime_context="local",
        required=True,
        target=str(java),
        probe_args=("-jar", str(jar), "MarkDuplicates", "--version"),
        expected=r"^Version:3[.]1[.]1$",
        description="Picard runtime",
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

    passed = run_checks(
        [picard],
        "local",
        command_runner=exact_picard_probe,
    )[0]

    assert passed.status == "pass"
    assert passed.observed == "Version:3.1.1"
    assert passed.detail == f"Resolved executable: {java}"
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
            "local",
            command_runner=lambda _argv, _stdin, _environment, _timeout, c=code: (
                c,
                "Version:3.1.1",
                0.0,
                False,
            ),
        )[0]
        assert rejected.status == "fail"
        assert rejected.detail == "Version probe failed"

    wrong_output = run_checks(
        [picard],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            1,
            "Version:3.1.1 extra",
            0.0,
            False,
        ),
    )[0]
    assert wrong_output.status == "fail"
    assert wrong_output.detail == "Version output did not match expected regex"


@pytest.mark.parametrize(
    ("check_type", "probe_args", "expected_detail"),
    [
        ("r_namespace", ("missing-rscript",), "Rscript executable was not found"),
        ("hash_utility", ("sha256sum",), "Hash executable was not found"),
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
        runtime_context="local",
        required=True,
        target="emrys-runtime-tool-that-does-not-exist",
        probe_args=probe_args,
        expected=r".*",
        description="missing runtime",
    )

    result = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: pytest.fail(
            "missing executable must stop before command execution"
        ),
    )[0]

    assert result.status == "fail"
    assert result.observed == "unavailable"
    assert result.detail == expected_detail


def test_hash_probe_binds_declared_adapter_and_reports_command_failure(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "sha256sum"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    check = RuntimeCheck(
        check_id="sha256",
        check_type="hash_utility",
        runtime_context="local",
        required=True,
        target=str(executable),
        probe_args=("sha256sum",),
        expected="sha256",
        description="SHA-256 utility",
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
        return 23, "", 0.5, False

    result = run_checks([check], "local", command_runner=fail)[0]

    assert calls == [([str(executable)], HASH_PAYLOAD)]
    assert result.status == "fail"
    assert result.observed == "exit 23"
    assert result.detail == "SHA-256 probe failed"

    mismatch = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            "not-a-digest",
            0.0,
            False,
        ),
    )[0]
    assert mismatch.status == "fail"
    assert mismatch.observed == "not-a-digest"
    assert mismatch.detail == "SHA-256 digest mismatch"


def test_executable_visibility_uses_absolute_target_and_matching_expectation(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "tool"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "executable",
                "path_visibility",
                "any",
                "true",
                str(executable),
                json.dumps(["executable"]),
                "executable",
                "Executable path",
            ]
        ],
    )
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, "local"
    )
    assert inspection.observations[0].status == "pass"

    relative = write_profile(
        tmp_path / "relative.tsv",
        [
            [
                "relative",
                "path_visibility",
                "any",
                "true",
                "relative/path",
                json.dumps(["file_readable"]),
                "readable",
                "Relative path",
            ]
        ],
    )
    with pytest.raises(inspector.RuntimeInspectionError, match="must be absolute"):
        inspector.load_runtime_profile_contract(relative)


def test_r_namespace_with_fake_rscript(tmp_path: Path) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'if [[ "${*: -1}" == "GoodPackage" ]]; then printf \'1.2.3\'; exit 0; fi\n'
        "exit 42\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    rows = []
    for check_id, package in (("good", "GoodPackage"), ("missing", "MissingPackage")):
        rows.append(
            [
                check_id,
                "r_namespace",
                "any",
                "true",
                package,
                json.dumps([str(fake)]),
                r"^[0-9]+[.][0-9]+[.][0-9]+$",
                "R namespace",
            ]
        )
    profile = write_profile(tmp_path / "profile.tsv", rows)
    inspection = inspector.inspect_runtime_profile_bytes(
        profile.read_bytes(), profile, "local"
    )
    observed = {item.check.check_id: item.status for item in inspection.observations}
    assert observed == {"good": "pass", "missing": "fail"}


def test_guarded_r_namespace_probe_binds_startup_and_selected_library(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    library = tmp_path / "library"
    library.mkdir()
    check = RuntimeCheck(
        check_id="r_guarded",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="GuardedPackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="guarded namespace",
    )
    calls: list[tuple[list[str], bytes | None, dict[str, str] | None, int]] = []
    environment = {
        "EMRYS_LOCAL_PILOT_R": "1",
        "EMRYS_RENV_LIBRARY": str(library),
    }
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
        "local",
        environment=environment,
        command_runner=capture,
    )[0]

    assert result.status == "pass"
    argv, stdin, observed_environment, timeout_seconds = calls[0]
    assert argv[:5] == [
        str(fake),
        "--no-environ",
        "--no-site-file",
        "--no-restore",
        "--no-save",
    ]
    assert argv[-2:] == ["GuardedPackage", str(library)]
    assert "find.package" in argv[6]
    assert (
        "tryCatch(suppressWarnings(loadNamespace(p, lib.loc=lib)), "
        "error=function(e) NULL)" in argv[6]
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
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    check = RuntimeCheck(
        check_id="r_guarded",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="GuardedPackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="guarded namespace",
    )

    result = run_checks(
        [check],
        "local",
        environment={
            "EMRYS_LOCAL_PILOT_R": "1",
            "EMRYS_RENV_LIBRARY": str(tmp_path / "library"),
        },
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
        "elapsed_seconds=0.500; "
        f"timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


def test_r_namespace_timeout_is_distinct_bounded_and_fail_closed(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    check = RuntimeCheck(
        check_id="r_timeout",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="SlowPackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="bounded namespace",
    )
    observed_timeouts: list[int] = []

    def time_out(
        _argv: list[str],
        _stdin: bytes | None,
        _environment: dict[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        observed_timeouts.append(timeout_seconds)
        return 124, "fixture timeout", 120.25, True

    result = run_checks([check], "local", command_runner=time_out)[0]

    assert observed_timeouts == [R_NAMESPACE_PROBE_TIMEOUT_SECONDS]
    assert R_NAMESPACE_PROBE_TIMEOUT_SECONDS > TOOL_PROBE_TIMEOUT_SECONDS
    assert result.status == "fail"
    assert result.observed == "fixture timeout"
    assert result.detail == (
        f"R namespace probe timed out; elapsed_seconds=120.250; timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


def test_r_namespace_real_exit_124_is_not_misclassified_as_timeout(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 124\n", encoding="utf-8")
    fake.chmod(0o755)
    check = RuntimeCheck(
        check_id="r_exit_124",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="FixturePackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="real exit 124",
    )

    result = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            124,
            "real child exit",
            0.25,
            False,
        ),
    )[0]

    assert result.status == "fail"
    assert result.observed == "real child exit"
    assert result.detail == (
        f"R namespace probe failed; elapsed_seconds=0.250; timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


def test_unguarded_r_namespace_probe_suppresses_only_load_warnings(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    check = RuntimeCheck(
        check_id="r_unguarded",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="FixturePackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="unguarded namespace",
    )
    calls: list[list[str]] = []

    def capture(
        argv: list[str],
        _stdin: bytes | None,
        _environment: dict[str, str] | None,
        timeout_seconds: int,
    ) -> tuple[int, str, float, bool]:
        calls.append(argv)
        assert timeout_seconds == R_NAMESPACE_PROBE_TIMEOUT_SECONDS
        return 0, "1.2.3", 0.75, False

    result = run_checks([check], "local", command_runner=capture)[0]

    assert result.status == "pass"
    assert calls[0][-1] == "FixturePackage"
    assert "suppressWarnings(requireNamespace(p, quietly=TRUE))" in calls[0][2]


def test_r_namespace_keeps_strict_version_output_matching(tmp_path: Path) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    check = RuntimeCheck(
        check_id="r_warning",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="FixturePackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="strict namespace",
    )
    contaminated = "Warning message: replacing previous import 1.2.3"

    result = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            0,
            contaminated,
            0.0,
            False,
        ),
    )[0]

    assert result.status == "fail"
    assert result.observed == contaminated
    assert result.detail == (
        "Namespace version did not match expected regex; "
        "elapsed_seconds=0.000; "
        f"timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


@pytest.mark.parametrize(
    ("guarded", "code", "expected_detail"),
    [
        (True, 42, "R namespace is unavailable in the selected library"),
        (True, 43, "R did not select the admitted library first"),
        (True, 44, "R namespace did not resolve to its exact selected package root"),
        (False, 42, "R namespace is unavailable"),
    ],
)
def test_r_namespace_failure_detail_distinguishes_guarded_selection(
    tmp_path: Path,
    guarded: bool,
    code: int,
    expected_detail: str,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")
    fake.chmod(0o755)
    check = RuntimeCheck(
        check_id="r_fixture",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="Fixture",
        probe_args=(str(fake),),
        expected=r"^1[.]0[.]0$",
        description="fixture namespace",
    )
    environment = (
        {
            "EMRYS_LOCAL_PILOT_R": "1",
            "EMRYS_RENV_LIBRARY": str(tmp_path / "library"),
        }
        if guarded
        else None
    )

    result = run_checks(
        [check],
        "local",
        environment=environment,
        command_runner=lambda _argv, _stdin, _environment, _timeout: (
            code,
            "",
            0.0,
            False,
        ),
    )[0]

    assert result.status == "fail"
    assert result.detail == (
        f"{expected_detail}; elapsed_seconds=0.000; "
        f"timeout_seconds={R_NAMESPACE_PROBE_TIMEOUT_SECONDS}"
    )


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
                "local",
                "true",
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
        "local",
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


def test_r_namespace_requires_package_name(tmp_path: Path) -> None:
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "bad_namespace",
                "r_namespace",
                "any",
                "true",
                "bad namespace",
                json.dumps(["Rscript"]),
                r"^[0-9]+[.]",
                "Invalid package name",
            ]
        ],
    )
    with pytest.raises(
        inspector.RuntimeInspectionError, match="must be an R package name"
    ):
        inspector.load_runtime_profile_contract(profile)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda _rows: [], "at least one check"),
        (lambda rows: [rows[0], rows[0]], "duplicate check_id"),
        (
            lambda rows: [[*rows[0][:-1], ""]],
            "description must be nonempty",
        ),
        (
            lambda rows: [[*rows[0][:5], "not-json", *rows[0][6:]]],
            "not valid JSON",
        ),
        (
            lambda rows: [
                [*rows[0][:1], "tool_version_exit_1", *rows[0][2:5], "[]", *rows[0][6:]]
            ],
            "tool_version_exit_1 needs probe_args",
        ),
        (
            lambda rows: [
                [
                    *rows[0][:1],
                    "tool_version_exit_1",
                    *rows[0][2:6],
                    "[",
                    *rows[0][7:],
                ]
            ],
            "expected regex is invalid",
        ),
    ],
)
def test_malformed_profiles_are_rejected(
    tmp_path: Path,
    mutator: Callable[[list[list[str]]], list[list[str]]],
    message: str,
) -> None:
    rows = mutator([tool_row()])
    profile = write_profile(tmp_path / "profile.tsv", rows)
    with pytest.raises(inspector.RuntimeInspectionError, match=message):
        inspector.load_runtime_profile_contract(profile)


def test_profile_symlink_is_rejected(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    link = tmp_path / "profile-link.tsv"
    link.symlink_to(profile)
    with pytest.raises(inspector.RuntimeInspectionError, match="symbolic link"):
        inspector.load_runtime_profile_contract(link)
