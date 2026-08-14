import csv
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from norad import __main__ as norad_main
from norad.evidence.runtime_availability import inspector
from norad.evidence.runtime_availability._probes import run_checks
from norad.evidence.runtime_availability._profile_contract import load_profile
from norad.evidence.runtime_availability._result_contract import result_bytes
from norad.evidence.runtime_availability._runtime_model import (
    HASH_EXPECTED,
    HASH_PAYLOAD,
    Check,
    PreflightError,
    Result,
)
from norad.libraries.source_authority import controlled_python_argv

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMAND = (sys.executable, "-I", "-m", "norad", "inspect", "runtime-availability")
EXAMPLE_PROFILE = REPO_ROOT / "configs" / "runtime_preflight.example.tsv"
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


def run_cli(
    profile: Path,
    output: Path,
    *extra: str,
    context: str = "local",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            *COMMAND,
            "--profile",
            str(profile),
            "--output",
            str(output),
            "--runtime-context",
            context,
            *extra,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def publication_values(
    tmp_path: Path,
) -> tuple[str, list[Check], bytes]:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    profile_data, checks = load_profile(profile)
    digest = hashlib.sha256(profile_data).hexdigest()
    results = run_checks(checks, "local")
    return digest, checks, result_bytes(digest, "local", results)


def test_help_and_dry_run_are_side_effect_free(tmp_path: Path) -> None:
    help_result = subprocess.run(
        [*COMMAND, "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "--runtime-context" in help_result.stdout
    assert "--execute" in help_result.stdout

    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "missing-parent" / "preflight.tsv"
    result = run_cli(profile, output)
    assert result.returncode == 0
    assert "python: pass" in result.stdout
    assert "not runtime validation or cluster proof" in result.stdout
    assert "Dry-run complete" in result.stdout
    assert not output.parent.exists()


def test_dry_run_execute_and_repeat_are_cwd_independent(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output_parent = tmp_path / "output"
    output_parent.mkdir()
    output = output_parent / "preflight.tsv"
    invocation = tmp_path / "invocation"
    invocation.mkdir()
    command = [
        *COMMAND,
        "--profile",
        str(profile),
        "--output",
        str(output),
        "--runtime-context",
        "local",
    ]

    dry_run = subprocess.run(
        command,
        cwd=invocation,
        text=True,
        capture_output=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert "Dry-run complete" in dry_run.stdout
    assert not output.exists()

    first = subprocess.run(
        [*command, "--execute"],
        cwd=invocation,
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    report = output.read_bytes()
    repeated = subprocess.run(
        [*command, "--execute"],
        cwd=invocation,
        text=True,
        capture_output=True,
        check=False,
    )
    assert repeated.returncode == 0, repeated.stderr
    assert first.stdout == repeated.stdout
    assert first.stderr == repeated.stderr == ""
    assert output.read_bytes() == report
    assert not any(invocation.iterdir())
    assert sorted(path.name for path in output_parent.iterdir()) == ["preflight.tsv"]


def test_tracked_example_profile_is_valid_and_locally_honest() -> None:
    _, checks = load_profile(EXAMPLE_PROFILE)
    results = run_checks(checks, "local")
    statuses = {result.check.check_id: result.status for result in results}
    assert statuses["python_version"] == "pass"
    assert statuses["sha256_python"] == "pass"
    assert statuses["rscript_version"] == "blocked"
    assert statuses["variant_annotation"] == "blocked"
    assert statuses["results_visibility"] == "blocked"


def test_execute_publishes_deterministic_result_and_replaces_valid_prior(
    tmp_path: Path,
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "preflight.tsv"
    first = run_cli(profile, output, "--execute")
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    rows = read_rows(output)
    assert len(rows) == 1
    assert rows[0]["status"] == "pass"
    assert rows[0]["profile_sha256"] == hashlib.sha256(profile.read_bytes()).hexdigest()

    second = run_cli(profile, output, "--execute")
    assert second.returncode == 0, second.stderr
    assert output.read_bytes() == original
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.previous"))


def test_context_mismatch_is_blocked_or_not_checked(tmp_path: Path) -> None:
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            tool_row("required_cluster", "cluster_batch", "true"),
            tool_row("optional_cluster", "cluster_batch", "false"),
        ],
    )
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = {row["check_id"]: row for row in read_rows(output)}
    assert rows["required_cluster"]["status"] == "blocked"
    assert rows["optional_cluster"]["status"] == "not_checked"


def test_missing_tool_and_version_mismatch_are_failures(tmp_path: Path) -> None:
    mismatch = tool_row("mismatch")
    mismatch[6] = "^definitely-not-python$"
    profile = write_profile(
        tmp_path / "profile.tsv",
        [tool_row("missing", target="norad-tool-that-does-not-exist"), mismatch],
    )
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = {row["check_id"]: row for row in read_rows(output)}
    assert rows["missing"]["status"] == "fail"
    assert rows["mismatch"]["status"] == "fail"


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
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = {row["check_id"]: row for row in read_rows(output)}
    assert rows["sha256"]["status"] == "pass"
    assert rows["visible"]["status"] == "pass"
    assert rows["missing"]["status"] == "fail"


def test_python_hash_probe_uses_the_controlled_python_prefix() -> None:
    check = Check(
        check_id="sha256_python",
        check_type="hash_utility",
        runtime_context="local",
        required=True,
        target=sys.executable,
        probe_args=("python_hashlib",),
        expected="sha256",
        description="controlled Python hashlib",
    )
    calls: list[tuple[list[str], bytes | None, dict[str, str] | None]] = []

    def capture(
        argv: list[str],
        stdin: bytes | None,
        environment: dict[str, str] | None,
    ) -> tuple[int, str]:
        calls.append((argv, stdin, environment))
        return 0, HASH_EXPECTED

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
        )
    ]


def test_gatk_probe_requires_exactly_one_declared_java_launcher() -> None:
    gatk = Check(
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


def test_gatk_probe_reports_an_invalid_declared_java_environment(
    tmp_path: Path,
) -> None:
    java_path = tmp_path / "java"
    java_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    java_path.chmod(0o755)
    java = Check(
        check_id="java",
        check_type="tool_version",
        runtime_context="local",
        required=True,
        target=str(java_path),
        probe_args=("-version",),
        expected=r"^openjdk version",
        description="Java runtime",
    )
    gatk = Check(
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
        command_runner=lambda _argv, _stdin, _environment: (
            0,
            "openjdk version 17",
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
        "printf 'openjdk version \\\"17.0.1\\\"\\n' >&2\n",
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
        REPO_ROOT / "configs" / "local_pilot_runtime.example.tsv"
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
    check = Check(
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
        command_runner=lambda _argv, _stdin, _environment: (0, "unexpected"),
    )[0]
    assert mismatch.status == "fail"
    assert mismatch.observed == "unexpected"
    assert mismatch.detail == "Version output did not match expected regex"


def test_picard_version_probe_accepts_only_its_exact_exit_one_contract(
    tmp_path: Path,
) -> None:
    java = tmp_path / "java-home" / "bin" / "java"
    jar = tmp_path / "picard.jar"
    java.parent.mkdir(parents=True)
    java.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    java.chmod(0o755)
    jar.write_bytes(b"bound picard jar")
    picard = Check(
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
    ) -> tuple[int, str]:
        observed_argv.append(tuple(argv))
        return 1, "Version:3.1.1"

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
            command_runner=lambda _argv, _stdin, _environment, c=code: (
                c,
                "Version:3.1.1",
            ),
        )[0]
        assert rejected.status == "fail"
        assert rejected.detail == "Version probe failed"

    wrong_output = run_checks(
        [picard],
        "local",
        command_runner=lambda _argv, _stdin, _environment: (
            1,
            "Version:3.1.1 extra",
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
    check = Check(
        check_id="missing",
        check_type=check_type,
        runtime_context="local",
        required=True,
        target="norad-runtime-tool-that-does-not-exist",
        probe_args=probe_args,
        expected=r".*",
        description="missing runtime",
    )

    result = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment: pytest.fail(
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
    check = Check(
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
    ) -> tuple[int, str]:
        calls.append((argv, stdin))
        return 23, ""

    result = run_checks([check], "local", command_runner=fail)[0]

    assert calls == [([str(executable)], HASH_PAYLOAD)]
    assert result.status == "fail"
    assert result.observed == "exit 23"
    assert result.detail == "SHA-256 probe failed"

    mismatch = run_checks(
        [check],
        "local",
        command_runner=lambda _argv, _stdin, _environment: (0, "not-a-digest"),
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
    output = tmp_path / "preflight.tsv"
    assert run_cli(profile, output, "--execute").returncode == 0
    assert read_rows(output)[0]["status"] == "pass"

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
    rejected = run_cli(relative, tmp_path / "relative-output.tsv", "--execute")
    assert rejected.returncode == 2
    assert "must be absolute" in rejected.stderr


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
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    observed = {row["check_id"]: row["status"] for row in read_rows(output)}
    assert observed == {"good": "pass", "missing": "fail"}


def test_guarded_r_namespace_probe_binds_startup_and_selected_library(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    library = tmp_path / "library"
    library.mkdir()
    check = Check(
        check_id="r_guarded",
        check_type="r_namespace",
        runtime_context="local",
        required=True,
        target="GuardedPackage",
        probe_args=(str(fake),),
        expected=r"^1[.]2[.]3$",
        description="guarded namespace",
    )
    calls: list[tuple[list[str], bytes | None, dict[str, str] | None]] = []
    environment = {
        "NORAD_LOCAL_PILOT_R": "1",
        "NORAD_RENV_LIBRARY": str(library),
    }

    def capture(
        argv: list[str],
        stdin: bytes | None,
        observed_environment: dict[str, str] | None,
    ) -> tuple[int, str]:
        calls.append((argv, stdin, observed_environment))
        return 0, "1.2.3"

    result = run_checks(
        [check],
        "local",
        environment=environment,
        command_runner=capture,
    )[0]

    assert result.status == "pass"
    argv, stdin, observed_environment = calls[0]
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
    assert "identical(expected, declared)" in argv[6]
    assert "identical(pkg, expected)" in argv[6]
    assert "identical(where, expected)" in argv[6]
    assert stdin is None
    assert observed_environment == environment
    assert result.detail == f"Resolved R package root: {library / 'GuardedPackage'}"


def test_unguarded_r_namespace_probe_suppresses_only_load_warnings(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    check = Check(
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
    ) -> tuple[int, str]:
        calls.append(argv)
        return 0, "1.2.3"

    result = run_checks([check], "local", command_runner=capture)[0]

    assert result.status == "pass"
    assert calls[0][-1] == "FixturePackage"
    assert "suppressWarnings(requireNamespace(p, quietly=TRUE))" in calls[0][2]


def test_r_namespace_keeps_strict_version_output_matching(tmp_path: Path) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    check = Check(
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
        command_runner=lambda _argv, _stdin, _environment: (0, contaminated),
    )[0]

    assert result.status == "fail"
    assert result.observed == contaminated
    assert result.detail == "Namespace version did not match expected regex"


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
    check = Check(
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
            "NORAD_LOCAL_PILOT_R": "1",
            "NORAD_RENV_LIBRARY": str(tmp_path / "library"),
        }
        if guarded
        else None
    )

    result = run_checks(
        [check],
        "local",
        environment=environment,
        command_runner=lambda _argv, _stdin, _environment: (code, ""),
    )[0]

    assert result.status == "fail"
    assert result.detail == expected_detail


def test_direct_inspection_uses_explicit_probe_environment(tmp_path: Path) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        '[[ "${NORAD_DOCTOR_TEST:-}" == "guarded" ]] || exit 43\n'
        "printf '1.2.3'\n",
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

    inspection = inspector.inspect_runtime_availability(
        profile,
        "local",
        environment={"NORAD_DOCTOR_TEST": "guarded", "PATH": os.environ["PATH"]},
    )

    assert inspection.required_ready
    assert inspection.profile_bytes == profile.read_bytes()
    assert inspection.observations[0].status == "pass"
    assert inspection.observations[0].observed == "1.2.3"


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
    result = run_cli(profile, tmp_path / "preflight.tsv", "--execute")
    assert result.returncode == 2
    assert "must be an R package name" in result.stderr


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
def test_malformed_profiles_fail_without_output(
    tmp_path: Path,
    mutator: Callable[[list[list[str]]], list[list[str]]],
    message: str,
) -> None:
    rows = mutator([tool_row()])
    profile = write_profile(tmp_path / "profile.tsv", rows)
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 2
    assert message in result.stderr
    assert not output.exists()


def test_profile_symlink_and_changed_profile_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    link = tmp_path / "profile-link.tsv"
    link.symlink_to(profile)
    output = tmp_path / "preflight.tsv"
    linked = run_cli(link, output, "--execute")
    assert linked.returncode == 2
    assert "symbolic link" in linked.stderr

    original_run_checks = inspector.run_checks

    def mutate(checks: Sequence[Check], runtime_context: str) -> list[Result]:
        results = original_run_checks(checks, runtime_context)
        profile.write_text(profile.read_text() + "\n", encoding="utf-8")
        return results

    monkeypatch.setattr(inspector, "run_checks", mutate)
    assert (
        norad_main.main(
            [
                "inspect",
                "runtime-availability",
                "--profile",
                str(profile),
                "--output",
                str(output),
                "--runtime-context",
                "local",
                "--execute",
            ]
        )
        == 2
    )
    assert not output.exists()


def test_foreign_lock_and_invalid_prior_are_preserved(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "preflight.tsv"
    lock = tmp_path / ".preflight.tsv.lock"
    lock.write_text("foreign\n")
    locked = run_cli(profile, output, "--execute")
    assert locked.returncode == 2
    assert "lock already exists" in locked.stderr
    assert lock.read_text() == "foreign\n"
    lock.unlink()

    output.write_text("foreign\n")
    invalid = run_cli(profile, output, "--execute")
    assert invalid.returncode == 2
    assert "invalid header" in invalid.stderr
    assert output.read_text() == "foreign\n"


def test_prior_report_rows_must_reconcile_to_profile(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "preflight.tsv"
    assert run_cli(profile, output, "--execute").returncode == 0
    original = output.read_text(encoding="utf-8")
    output.write_text(
        original.replace("\tpython\ttool_version\t", "\ttampered\ttool_version\t")
    )

    result = run_cli(profile, output, "--execute")
    assert result.returncode == 2
    assert "check_id does not match the profile" in result.stderr
    assert "\ttampered\ttool_version\t" in output.read_text(encoding="utf-8")


def test_execute_requires_existing_real_parent_and_tsv_suffix(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    missing_parent = run_cli(
        profile,
        tmp_path / "missing" / "preflight.tsv",
        "--execute",
    )
    assert missing_parent.returncode == 2
    assert "Output parent must already exist" in missing_parent.stderr

    wrong_suffix = run_cli(profile, tmp_path / "preflight.txt", "--execute")
    assert wrong_suffix.returncode == 2
    assert "must use the .tsv suffix" in wrong_suffix.stderr

    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(tmp_path, target_is_directory=True)
    linked_parent = run_cli(
        profile,
        parent_link / "preflight.tsv",
        "--execute",
    )
    assert linked_parent.returncode == 2
    assert "real directory" in linked_parent.stderr


def test_publish_failure_rolls_back_valid_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    profile_data, checks = load_profile(profile)
    digest = hashlib.sha256(profile_data).hexdigest()
    results = run_checks(checks, "local")
    previous = result_bytes(digest, "local", results)
    output = tmp_path / "preflight.tsv"
    output.write_bytes(previous)

    real_validate = inspector.validate_result_bytes
    calls = 0

    def fail_after_publish(
        data: bytes,
        profile_sha256: str,
        runtime_context: str,
        expected_checks: Sequence[Check],
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise PreflightError("injected validation failure")
        real_validate(data, profile_sha256, runtime_context, expected_checks)

    monkeypatch.setattr(inspector, "validate_result_bytes", fail_after_publish)
    with pytest.raises(PreflightError, match="injected"):
        inspector.publish(output, previous, digest, "local", checks)
    assert output.read_bytes() == previous
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.previous"))


def test_stage_fsync_failure_cleans_preflight_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest, checks, data = publication_values(tmp_path)
    output = tmp_path / "preflight.tsv"
    real_fsync = inspector.os.fsync
    calls = 0

    def fail_second_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected staged preflight fsync failure")
        real_fsync(descriptor)

    # The first fsync commits lock ownership; the second belongs to the stage.
    monkeypatch.setattr(inspector.os, "fsync", fail_second_fsync)
    with pytest.raises(OSError, match="staged preflight fsync"):
        inspector.publish(output, data, digest, "local", checks)

    assert calls == 2
    assert not output.exists()
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob(".*.tmp"))


def test_characterizes_preflight_lock_fsync_failure_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest, checks, data = publication_values(tmp_path)
    output = tmp_path / "preflight.tsv"
    lock = tmp_path / ".preflight.tsv.lock"
    real_open = inspector.os.open
    real_close = inspector.os.close
    real_unlink = Path.unlink
    opened: list[int] = []

    def track_open(*args: object, **kwargs: object) -> int:
        descriptor = real_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def fail_lock_fsync(_descriptor: int) -> None:
        raise OSError("injected preflight lock fsync failure")

    monkeypatch.setattr(inspector.os, "open", track_open)
    monkeypatch.setattr(inspector.os, "fsync", fail_lock_fsync)
    with pytest.raises(OSError, match="lock fsync"):
        inspector.publish(output, data, digest, "local", checks)

    # Known TG-02 gap: failure occurs before publish owns a descriptor in its
    # try/finally, so the lock and descriptor are left behind.
    assert lock.is_file()
    assert not output.exists()
    for descriptor in opened:
        real_close(descriptor)
    real_unlink(lock)


def test_characterizes_preflight_incomplete_rollback_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest, checks, prior = publication_values(tmp_path)
    output = tmp_path / "preflight.tsv"
    output.write_bytes(prior)
    real_replace = inspector.os.replace
    publication_failed = False
    restoration_failed = False

    def fail_publication_and_restoration(source: Path, destination: Path) -> None:
        nonlocal publication_failed, restoration_failed
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not publication_failed
            and destination_path == output
            and source_path.name.endswith(".tmp")
        ):
            publication_failed = True
            raise OSError("injected preflight publication failure")
        if (
            publication_failed
            and not restoration_failed
            and destination_path == output
            and source_path.name.endswith(".previous")
        ):
            restoration_failed = True
            raise OSError("injected preflight restoration failure")
        real_replace(source, destination)

    monkeypatch.setattr(
        inspector.os,
        "replace",
        fail_publication_and_restoration,
    )
    with pytest.raises(OSError, match="preflight restoration"):
        inspector.publish(output, prior, digest, "local", checks)

    assert publication_failed and restoration_failed
    assert not output.exists()
    assert len(list(tmp_path.glob(".*.previous"))) == 1
    # Known TG-02 gap: the only predecessor bytes survive without the lock or
    # an explicit recovery marker.
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob("*.RECOVERY.txt"))


def test_characterizes_preflight_lock_cleanup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest, checks, data = publication_values(tmp_path)
    output = tmp_path / "preflight.tsv"
    lock = tmp_path / ".preflight.tsv.lock"
    real_unlink = Path.unlink

    def fail_lock_cleanup(
        path_value: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if path_value == lock:
            raise OSError("injected preflight lock cleanup failure")
        real_unlink(path_value, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_lock_cleanup)
    inspector.publish(output, data, digest, "local", checks)

    assert output.read_bytes() == data
    # Known TG-02 gap: lock cleanup errors are swallowed, so the caller sees
    # success while the owned lock continues to block future attempts.
    assert lock.is_file()
    real_unlink(lock)
