"""Read-only availability probes for runtime-preflight evidence."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from norad.libraries.process_environment import (
    ProcessEnvironmentError,
    gatk_subprocess_environment,
    guarded_rscript_argv,
)
from norad.libraries.source_authority import controlled_python_argv

from ._runtime_model import (
    HASH_EXPECTED,
    HASH_PAYLOAD,
    PROBE_TIMEOUT_SECONDS,
    RESULT_STATUSES,
    VERSION_TEXT_LIMIT,
    Check,
    Result,
    _fail,
    _single_line,
)

CommandRunner = Callable[
    [list[str], bytes | None, Mapping[str, str] | None], tuple[int, str]
]


def _resolve_executable(target: str) -> str | None:
    if "/" in target:
        path = Path(target)
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(target)


def _run_command(
    command: list[str],
    stdin: bytes | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
            env=None if environment is None else dict(environment),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, _single_line(str(exc))
    output = completed.stdout[:VERSION_TEXT_LIMIT].decode("utf-8", errors="replace")
    return completed.returncode, _single_line(output)


def _probe_tool(
    check: Check,
    environment: Mapping[str, str] | None,
    run_command: CommandRunner,
) -> Result:
    executable = _resolve_executable(check.target)
    if executable is None:
        return Result(check, "fail", "unavailable", "Executable was not found")
    command = [executable, *check.probe_args]
    if (
        check.check_id == "rscript"
        and environment is not None
        and (environment.get("NORAD_LOCAL_PILOT_R") == "1")
    ):
        command = guarded_rscript_argv(executable, check.probe_args)
    code, output = run_command(command, None, environment)
    if code != 0:
        return Result(check, "fail", output or f"exit {code}", "Version probe failed")
    if re.search(check.expected, output) is None:
        return Result(
            check, "fail", output, "Version output did not match expected regex"
        )
    return Result(check, "pass", output, f"Resolved executable: {executable}")


def _probe_r_namespace(
    check: Check,
    environment: Mapping[str, str] | None,
    run_command: CommandRunner,
) -> Result:
    rscript = _resolve_executable(check.probe_args[0])
    if rscript is None:
        return Result(check, "fail", "unavailable", "Rscript executable was not found")
    guarded = environment is not None and environment.get("NORAD_LOCAL_PILOT_R") == "1"
    if guarded:
        expression = (
            "a <- commandArgs(TRUE); p <- a[1]; lib <- normalizePath(a[2], "
            "winslash='/', mustWork=TRUE); "
            "libs <- normalizePath(.libPaths(), winslash='/', mustWork=TRUE); "
            "if (length(libs) < 1L || !identical(libs[[1L]], lib)) quit(status=43); "
            "pkg <- tryCatch(find.package(p, lib.loc=lib, quiet=TRUE), "
            "error=function(e) ''); if (!nzchar(pkg)) quit(status=42); "
            "declared <- file.path(lib, p); "
            "expected <- normalizePath(declared, winslash='/', "
            "mustWork=TRUE); "
            "if (!identical(expected, declared)) quit(status=44); "
            "pkg <- normalizePath(pkg, winslash='/', mustWork=TRUE); "
            "if (!identical(pkg, expected)) quit(status=44); "
            "ns <- tryCatch(loadNamespace(p, lib.loc=lib), error=function(e) NULL); "
            "if (is.null(ns)) quit(status=42); "
            "where <- normalizePath(getNamespaceInfo(ns, 'path'), winslash='/', "
            "mustWork=TRUE); "
            "if (!identical(where, expected)) quit(status=44); "
            "cat(as.character(utils::packageVersion(p, lib.loc=lib)))"
        )
        arguments = guarded_rscript_argv(
            rscript,
            ("-e", expression, check.target, environment["NORAD_RENV_LIBRARY"]),
        )
    else:
        expression = (
            "p <- commandArgs(TRUE)[1]; "
            "if (!requireNamespace(p, quietly=TRUE)) quit(status=42); "
            "cat(as.character(utils::packageVersion(p)))"
        )
        arguments = [rscript, "-e", expression, check.target]
    code, output = run_command(arguments, None, environment)
    if code != 0:
        details = (
            {
                42: "R namespace is unavailable in the selected library",
                43: "R did not select the admitted library first",
                44: "R namespace did not resolve to its exact selected package root",
            }
            if guarded
            else {42: "R namespace is unavailable"}
        )
        detail = details.get(code, "R namespace probe failed")
        return Result(check, "fail", output or f"exit {code}", detail)
    if re.fullmatch(check.expected, output) is None:
        return Result(
            check,
            "fail",
            output,
            "Namespace version did not match expected regex",
        )
    detail = (
        f"Resolved R package root: {Path(environment['NORAD_RENV_LIBRARY']) / check.target}"
        if guarded and environment is not None
        else f"Resolved Rscript: {rscript}"
    )
    return Result(check, "pass", output, detail)


def _probe_hash_utility(
    check: Check,
    environment: Mapping[str, str] | None,
    run_command: CommandRunner,
) -> Result:
    executable = _resolve_executable(check.target)
    if executable is None:
        return Result(check, "fail", "unavailable", "Hash executable was not found")
    adapter = check.probe_args[0]
    if adapter == "python_hashlib":
        command = list(
            controlled_python_argv(
                executable,
                "-c",
                "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())",
            )
        )
    elif adapter == "sha256sum":
        command = [executable]
    else:
        command = [executable, "-a", "256"]
    code, output = run_command(command, HASH_PAYLOAD, environment)
    observed = output.split()[0].lower() if output else ""
    if code != 0:
        return Result(check, "fail", output or f"exit {code}", "SHA-256 probe failed")
    if observed != HASH_EXPECTED:
        return Result(check, "fail", observed or "empty", "SHA-256 digest mismatch")
    return Result(check, "pass", observed, f"Resolved executable: {executable}")


def _probe_path_visibility(
    check: Check,
    _environment: Mapping[str, str] | None,
    _run_command: CommandRunner,
) -> Result:
    path = Path(check.target)
    mode = check.probe_args[0]
    try:
        metadata = path.stat()
    except OSError as exc:
        return Result(check, "fail", "unavailable", _single_line(str(exc)))
    if mode == "file_readable":
        passed = stat.S_ISREG(metadata.st_mode) and os.access(path, os.R_OK)
    elif mode == "directory_readable":
        passed = stat.S_ISDIR(metadata.st_mode) and os.access(path, os.R_OK | os.X_OK)
    else:
        passed = stat.S_ISREG(metadata.st_mode) and os.access(path, os.X_OK)
    observed = f"{mode}:{'yes' if passed else 'no'}"
    detail = f"Resolved path: {path.resolve(strict=False)}"
    return Result(check, "pass" if passed else "fail", observed, detail)


PROBES: dict[
    str,
    Callable[[Check, Mapping[str, str] | None, CommandRunner], Result],
] = {
    "tool_version": _probe_tool,
    "r_namespace": _probe_r_namespace,
    "hash_utility": _probe_hash_utility,
    "path_visibility": _probe_path_visibility,
}


def run_checks(
    checks: Sequence[Check],
    runtime_context: str,
    *,
    environment: Mapping[str, str] | None = None,
    command_runner: CommandRunner = _run_command,
) -> list[Result]:
    results: list[Result] = []
    for check in checks:
        if check.runtime_context not in {"any", runtime_context}:
            status = "blocked" if check.required else "not_checked"
            results.append(
                Result(
                    check,
                    status,
                    f"current_context={runtime_context}",
                    f"Check requires runtime_context={check.runtime_context}",
                )
            )
            continue
        check_environment = environment
        if check.check_id == "gatk":
            java_targets = [item.target for item in checks if item.check_id == "java"]
            if len(java_targets) != 1:
                result = Result(
                    check,
                    "fail",
                    "unavailable",
                    "GATK probing requires exactly one declared Java launcher",
                )
                results.append(result)
                continue
            try:
                check_environment = gatk_subprocess_environment(
                    java_targets[0],
                    base_environment=environment,
                )
            except ProcessEnvironmentError as exc:
                result = Result(check, "fail", "unavailable", _single_line(str(exc)))
                results.append(result)
                continue
        result = PROBES[check.check_type](
            check,
            check_environment,
            command_runner,
        )
        if result.status not in RESULT_STATUSES:
            _fail(f"Internal error: invalid result status {result.status}")
        results.append(result)
    return results
