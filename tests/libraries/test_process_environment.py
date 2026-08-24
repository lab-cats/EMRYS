from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import pytest

from norad.libraries import process_environment
from norad.libraries.process_environment import (
    GATK_STARTUP_VARIABLES,
    ProcessEnvironmentError,
    admit_java_launcher,
    gatk_subprocess_environment,
    guarded_r_environment,
    guarded_rscript_argv,
)


def make_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def make_java_launcher(tmp_path: Path, name: str = "java-home") -> Path:
    launcher = tmp_path / name / "bin" / "java"
    make_executable(launcher)
    return launcher


def test_guarded_r_environment_replaces_all_ambient_selectors(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    library = tmp_path / "renv-library"
    environment = guarded_r_environment(
        source_root,
        library,
        base_environment={
            "PATH": "/controlled/bin",
            "KEEP": "preserved",
            "R_LIBS_CUSTOM": "/ambient/custom-library",
            "R_PROFILE_USER": "/ambient/profile",
            "R_ENVIRON_SITE": "/ambient/environ",
            "RENV_PATHS_CACHE": "/ambient/cache",
            "R_DEFAULT_PACKAGES": "hostilePackage",
        },
    )

    assert environment["KEEP"] == "preserved"
    assert environment["R_LIBS"] == str(library)
    assert environment["R_LIBS_USER"] == str(library)
    assert environment["R_PROFILE_USER"] == str(source_root / ".Rprofile")
    assert environment["R_ENVIRON_SITE"] == os.devnull
    assert environment["R_DEFAULT_PACKAGES"] == "NULL"
    assert environment["RENV_CONFIG_AUTOLOADER_ENABLED"] == "FALSE"
    assert "R_LIBS_CUSTOM" not in environment
    assert "RENV_PATHS_CACHE" not in environment
    assert guarded_rscript_argv("Rscript", ("-e", "cat('ready')")) == [
        "Rscript",
        "--no-environ",
        "--no-site-file",
        "--no-restore",
        "--no-save",
        "-e",
        "cat('ready')",
    ]


def test_java_admission_accepts_relative_canonical_launcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = make_java_launcher(tmp_path)
    monkeypatch.chdir(tmp_path)

    admitted = admit_java_launcher(Path("java-home/bin/java"))

    assert admitted.executable == launcher
    assert admitted.java_home == tmp_path / "java-home"


@pytest.mark.parametrize(
    ("fault", "expected_error"),
    [
        ("missing", "Selected Java launcher could not be resolved"),
        ("not-executable", "Selected Java launcher is not an executable file"),
        ("wrong-layout", "must resolve to canonical <JAVA_HOME>/bin/java"),
    ],
)
def test_java_admission_rejects_invalid_launcher(
    fault: str, expected_error: str, tmp_path: Path
) -> None:
    if fault == "missing":
        launcher = tmp_path / "missing" / "bin" / "java"
    elif fault == "not-executable":
        launcher = tmp_path / "java-home" / "bin" / "java"
        launcher.parent.mkdir(parents=True)
        launcher.write_text("not executable\n", encoding="utf-8")
    else:
        launcher = tmp_path / "wrong-parent" / "java"
        make_executable(launcher)

    with pytest.raises(ProcessEnvironmentError, match=expected_error):
        admit_java_launcher(launcher)


def test_java_admission_rejects_launcher_identity_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = make_java_launcher(tmp_path, "selected-java")
    replacement = make_java_launcher(tmp_path, "replacement-java")
    real_resolve = Path.resolve
    first_resolution = True

    def resolve_with_identity_change(path: Path, strict: bool = False) -> Path:
        nonlocal first_resolution
        if path == launcher:
            if first_resolution:
                first_resolution = False
                return launcher
            return replacement
        return real_resolve(path, strict=strict)

    with monkeypatch.context() as context:
        context.setattr(Path, "resolve", resolve_with_identity_change)
        with pytest.raises(
            ProcessEnvironmentError,
            match="Derived JAVA_HOME does not select the admitted Java launcher",
        ):
            admit_java_launcher(launcher)


def test_gatk_environment_selects_java_and_removes_ambient_selectors(
    tmp_path: Path,
) -> None:
    launcher = make_java_launcher(tmp_path)
    selected_bin = str(launcher.parent)
    other_bin = str(tmp_path / "other-bin")
    base_environment = {
        "PATH": os.pathsep.join((other_bin, "", selected_bin, selected_bin)),
        "BASH_ENV": "/hostile/bash-env",
        "BASH_FUNC_hostile%%": "() { false; }",
        **{name: f"ambient-{name}" for name in GATK_STARTUP_VARIABLES},
    }

    environment = gatk_subprocess_environment(
        launcher, base_environment=base_environment
    )

    assert environment["JAVA_HOME"] == str(tmp_path / "java-home")
    assert environment["PATH"].split(os.pathsep) == [selected_bin, other_bin]
    assert not GATK_STARTUP_VARIABLES.intersection(environment)
    assert "BASH_ENV" not in environment
    assert "BASH_FUNC_hostile%%" not in environment


@pytest.mark.parametrize(
    "launch_error",
    [
        OSError("launch denied"),
        subprocess.TimeoutExpired(("/bin/sh", "-c", "command -v java"), 5),
    ],
    ids=("launch-error", "timeout"),
)
def test_gatk_environment_rejects_verification_launch_failure(
    launch_error: OSError | subprocess.TimeoutExpired,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = make_java_launcher(tmp_path)

    def fail_verification(*args: object, **kwargs: object) -> NoReturn:
        raise launch_error

    monkeypatch.setattr(process_environment.subprocess, "run", fail_verification)

    with pytest.raises(
        ProcessEnvironmentError, match="Could not verify selected Java on PATH"
    ):
        gatk_subprocess_environment(launcher, base_environment={"PATH": ""})


def completed_lookup(
    *, returncode: int = 0, stdout: str = "", stderr: str = ""
) -> Callable[..., subprocess.CompletedProcess[str]]:
    def lookup(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=("/bin/sh", "-c", "command -v java"),
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    return lookup


@pytest.mark.parametrize(
    ("lookup", "expected_error"),
    [
        (
            completed_lookup(returncode=127, stderr="java: not found\n"),
            "Could not resolve exactly one Java launcher through the controlled PATH",
        ),
        (
            completed_lookup(stdout="/first/bin/java\n/second/bin/java\n"),
            "Could not resolve exactly one Java launcher through the controlled PATH",
        ),
        (
            completed_lookup(stdout="/missing/bin/java\n"),
            "Java selected through controlled PATH could not be resolved",
        ),
    ],
    ids=("lookup-failure", "multiple-results", "missing-result"),
)
def test_gatk_environment_rejects_inadmissible_path_lookup(
    lookup: Callable[..., subprocess.CompletedProcess[str]],
    expected_error: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = make_java_launcher(tmp_path)
    monkeypatch.setattr(process_environment.subprocess, "run", lookup)

    with pytest.raises(ProcessEnvironmentError, match=expected_error):
        gatk_subprocess_environment(launcher, base_environment={"PATH": ""})


def test_gatk_environment_rejects_path_launcher_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = make_java_launcher(tmp_path, "selected-java")
    other_launcher = make_java_launcher(tmp_path, "other-java")
    monkeypatch.setattr(
        process_environment.subprocess,
        "run",
        completed_lookup(stdout=f"{other_launcher}\n"),
    )

    with pytest.raises(
        ProcessEnvironmentError,
        match="differs from the admitted launcher",
    ):
        gatk_subprocess_environment(launcher, base_environment={"PATH": ""})


@pytest.mark.parametrize("separator", [(), ("--",)], ids=("absent", "present"))
def test_gatk_cli_requires_command_after_optional_separator(
    separator: tuple[str, ...],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = make_java_launcher(tmp_path)

    with pytest.raises(SystemExit) as termination:
        process_environment._execute_gatk_with_selected_java(
            ("--java-bin", str(launcher), *separator)
        )

    assert termination.value.code == 2
    assert "a GATK command is required after --" in capsys.readouterr().err


def test_gatk_cli_strips_separator_and_reports_exec_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = make_java_launcher(tmp_path)
    observed: dict[str, object] = {}

    def reject_exec(
        executable: str, arguments: list[str], environment: dict[str, str]
    ) -> NoReturn:
        observed.update(
            executable=executable,
            arguments=arguments,
            environment=environment,
        )
        raise OSError("exec denied")

    monkeypatch.setattr(process_environment.os, "execvpe", reject_exec)

    result = process_environment._execute_gatk_with_selected_java(
        ("--java-bin", str(launcher), "--", "gatk", "HaplotypeCaller")
    )

    assert result == 2
    assert observed["executable"] == "gatk"
    assert observed["arguments"] == ["gatk", "HaplotypeCaller"]
    environment = observed["environment"]
    assert isinstance(environment, dict)
    assert environment["JAVA_HOME"] == str(launcher.parent.parent)
    assert "Could not execute GATK with selected Java: exec denied" in (
        capsys.readouterr().err
    )


def test_gatk_cli_reports_java_admission_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = process_environment._execute_gatk_with_selected_java(
        ("--java-bin", str(tmp_path / "missing-java"), "gatk")
    )

    assert result == 2
    assert "Selected Java launcher could not be resolved" in capsys.readouterr().err


def test_gatk_cli_guards_against_exec_returning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = make_java_launcher(tmp_path)
    monkeypatch.setattr(process_environment.os, "execvpe", lambda *args: None)

    with pytest.raises(AssertionError, match="os.execvpe returned unexpectedly"):
        process_environment._execute_gatk_with_selected_java(
            ("--java-bin", str(launcher), "gatk")
        )
