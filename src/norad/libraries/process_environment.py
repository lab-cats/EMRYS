"""Neutral controlled-subprocess environment selectors."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

BASH_STARTUP_VARIABLES = frozenset(
    {
        "BASH_ENV",
        "ENV",
        "SHELLOPTS",
        "BASHOPTS",
        "CDPATH",
        "GLOBIGNORE",
    }
)
GUARDED_RSCRIPT_STARTUP_ARGS = (
    "--no-environ",
    "--no-site-file",
    "--no-restore",
    "--no-save",
)
GATK_STARTUP_VARIABLES = frozenset(
    {
        "CLASSPATH",
        "GATK_JAR",
        "GATK_LOCAL_JAR",
        "JAVA_OPTS",
        "JAVA_TOOL_OPTIONS",
        "JDK_JAVA_OPTIONS",
        "_JAVA_OPTIONS",
    }
)
RENV_VERSION = "1.2.3"
R_SELECTOR_PREFIXES = ("R_LIBS", "R_PROFILE", "R_ENVIRON", "RENV_")
R_STARTUP_VARIABLES = frozenset({"R_DEFAULT_PACKAGES"})


class ProcessEnvironmentError(RuntimeError):
    """A selected child-process launcher or environment is inadmissible."""


@dataclass(frozen=True, slots=True)
class AdmittedJavaLauncher:
    """One canonical Java launcher and its derived Java home."""

    executable: Path
    java_home: Path


def sanitized_subprocess_environment(
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Copy an environment without inherited noninteractive-shell startup hooks."""

    environment = dict(os.environ if base_environment is None else base_environment)
    for name in tuple(environment):
        if name in BASH_STARTUP_VARIABLES or name.startswith("BASH_FUNC_"):
            del environment[name]
    return environment


def guarded_r_environment(
    source_root: Path,
    renv_library: Path,
    *,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Select one existing R library without permitting renv auto-bootstrap."""

    environment = sanitized_subprocess_environment(base_environment)
    for name in tuple(environment):
        if name.startswith(R_SELECTOR_PREFIXES) or name in R_STARTUP_VARIABLES:
            del environment[name]
    library = str(renv_library)
    environment.update(
        {
            "NORAD_LOCAL_PILOT_R": "1",
            "NORAD_USE_RENV": "1",
            "NORAD_RENV_LIBRARY": library,
            "NORAD_RENV_VERSION": RENV_VERSION,
            "RENV_PROJECT": str(source_root),
            "RENV_PATHS_LIBRARY": library,
            "RENV_CONFIG_AUTOLOADER_ENABLED": "FALSE",
            "RENV_AUTOLOADER_ENABLED": "FALSE",
            "RENV_ACTIVATE_PROJECT": "FALSE",
            "RENV_CONFIG_USER_PROFILE": "FALSE",
            "RENV_CONFIG_SANDBOX_ENABLED": "FALSE",
            "RENV_CONFIG_AUTO_SNAPSHOT": "FALSE",
            "R_LIBS": library,
            "R_LIBS_USER": library,
            "R_LIBS_SITE": library,
            "R_PROFILE_USER": str(source_root / ".Rprofile"),
            "R_PROFILE_SITE": os.devnull,
            "R_ENVIRON_USER": os.devnull,
            "R_ENVIRON_SITE": os.devnull,
            "R_DEFAULT_PACKAGES": "NULL",
        }
    )
    return environment


def guarded_rscript_argv(rscript: str, arguments: Sequence[str]) -> list[str]:
    """Build the one Rscript startup selector shared by probes and owners."""

    return [rscript, *GUARDED_RSCRIPT_STARTUP_ARGS, *arguments]


def admit_java_launcher(selected_java: str | Path) -> AdmittedJavaLauncher:
    """Admit one executable as the canonical ``<JAVA_HOME>/bin/java`` target."""

    requested = Path(selected_java)
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    try:
        executable = requested.resolve(strict=True)
    except OSError as exc:
        raise ProcessEnvironmentError(
            f"Selected Java launcher could not be resolved: {requested}: {exc}"
        ) from exc
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ProcessEnvironmentError(
            f"Selected Java launcher is not an executable file: {executable}"
        )
    if executable.name != "java" or executable.parent.name != "bin":
        raise ProcessEnvironmentError(
            "Selected Java launcher must resolve to canonical "
            f"<JAVA_HOME>/bin/java: {executable}"
        )
    java_home = executable.parent.parent
    expected = java_home / "bin" / "java"
    try:
        canonical_expected = expected.resolve(strict=True)
    except OSError as exc:  # pragma: no cover - executable resolution proved it
        raise ProcessEnvironmentError(
            f"Derived Java launcher could not be resolved: {expected}: {exc}"
        ) from exc
    if canonical_expected != executable:
        raise ProcessEnvironmentError(
            f"Derived JAVA_HOME does not select the admitted Java launcher: {java_home}"
        )
    return AdmittedJavaLauncher(executable=executable, java_home=java_home)


def gatk_subprocess_environment(
    selected_java: str | Path,
    *,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build and verify the controlled Java environment used for GATK."""

    launcher = admit_java_launcher(selected_java)
    environment = sanitized_subprocess_environment(base_environment)
    for name in GATK_STARTUP_VARIABLES:
        environment.pop(name, None)
    selected_bin = str(launcher.executable.parent)
    inherited_path = environment.get("PATH", "")
    path_parts = [
        part
        for part in inherited_path.split(os.pathsep)
        if part and part != selected_bin
    ]
    environment["JAVA_HOME"] = str(launcher.java_home)
    environment["PATH"] = os.pathsep.join((selected_bin, *path_parts))

    try:
        completed = subprocess.run(
            ("/bin/sh", "-c", "command -v java"),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProcessEnvironmentError(
            f"Could not verify selected Java on PATH: {exc}"
        ) from exc
    observed_lines = completed.stdout.splitlines()
    if completed.returncode != 0 or len(observed_lines) != 1:
        detail = " ".join((completed.stdout + " " + completed.stderr).split())
        raise ProcessEnvironmentError(
            "Could not resolve exactly one Java launcher through the controlled "
            f"PATH: {detail or f'exit {completed.returncode}'}"
        )
    observed = Path(observed_lines[0])
    try:
        canonical_observed = observed.resolve(strict=True)
    except OSError as exc:
        raise ProcessEnvironmentError(
            f"Java selected through controlled PATH could not be resolved: {observed}: {exc}"
        ) from exc
    if canonical_observed != launcher.executable:
        raise ProcessEnvironmentError(
            "Java selected through controlled PATH differs from the admitted launcher: "
            f"{canonical_observed} != {launcher.executable}"
        )
    return environment


def _execute_gatk_with_selected_java(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Execute GATK with one admitted Java launcher."
    )
    parser.add_argument("--java-bin", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    namespace = parser.parse_args(arguments)
    command = list(namespace.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        parser.error("a GATK command is required after --")
    try:
        environment = gatk_subprocess_environment(namespace.java_bin)
        os.execvpe(command[0], command, environment)
    except (OSError, ProcessEnvironmentError) as exc:
        print(
            f"ERROR: Could not execute GATK with selected Java: {exc}", file=sys.stderr
        )
        return 2
    raise AssertionError("os.execvpe returned unexpectedly")


if __name__ == "__main__":  # pragma: no cover - exercised by stage-owner tests
    raise SystemExit(_execute_gatk_with_selected_java(sys.argv[1:]))
