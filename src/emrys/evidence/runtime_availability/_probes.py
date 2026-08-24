"""Read-only availability probes for runtime-preflight evidence."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from emrys.libraries.process_environment import (
    ProcessEnvironmentError,
    gatk_subprocess_environment,
    guarded_rscript_argv,
)
from emrys.libraries.source_authority import controlled_python_argv

from ._runtime_model import (
    HASH_EXPECTED,
    HASH_PAYLOAD,
    R_NAMESPACE_PROBE_TIMEOUT_SECONDS,
    RESULT_STATUSES,
    TOOL_PROBE_TIMEOUT_SECONDS,
    VERSION_TEXT_LIMIT,
    Check,
    Result,
    _fail,
    _single_line,
)

CommandRunner = Callable[
    [list[str], bytes | None, Mapping[str, str] | None, int],
    tuple[int, str, float, bool],
]
R_NAMESPACE_ROOT_OUTPUT_MARKER = "::emrys-root-utf8-hex::"


def _timing_detail(elapsed_seconds: float, timeout_seconds: int) -> str:
    return (
        f"elapsed_seconds={elapsed_seconds:.3f}; "
        f"timeout_seconds={timeout_seconds}"
    )


def _guarded_namespace_output(output: str) -> tuple[str, Path] | None:
    if output.count(R_NAMESPACE_ROOT_OUTPUT_MARKER) != 1:
        return None
    version, encoded_root = output.split(R_NAMESPACE_ROOT_OUTPUT_MARKER, 1)
    if (
        not encoded_root
        or len(encoded_root) % 2 != 0
        or re.fullmatch(r"[0-9a-f]+", encoded_root) is None
    ):
        return None
    try:
        decoded_root = bytes.fromhex(encoded_root).decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return None
    root = Path(decoded_root)
    if "\x00" in decoded_root or not root.is_absolute():
        return None
    return version, root


def _resolve_executable(target: str) -> str | None:
    if "/" in target:
        path = Path(target)
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(target)


def _run_command(
    command: list[str],
    stdin: bytes | None = None,
    environment: Mapping[str, str] | None = None,
    timeout_seconds: int = TOOL_PROBE_TIMEOUT_SECONDS,
) -> tuple[int, str, float, bool]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            check=False,
            env=None if environment is None else dict(environment),
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        return (
            124,
            _single_line(str(exc)),
            elapsed,
            True,
        )
    except OSError as exc:
        return 127, _single_line(str(exc)), time.monotonic() - started, False
    output = completed.stdout[:VERSION_TEXT_LIMIT].decode("utf-8", errors="replace")
    return (
        completed.returncode,
        _single_line(output),
        time.monotonic() - started,
        False,
    )


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
        and (environment.get("EMRYS_LOCAL_PILOT_R") == "1")
        # Rscript's standalone information mode rejects startup guards as a
        # missing script; executable R code remains guarded below.
        and check.probe_args != ("--version",)
    ):
        command = guarded_rscript_argv(executable, check.probe_args)
    code, output, elapsed, timed_out = run_command(
        command,
        None,
        environment,
        TOOL_PROBE_TIMEOUT_SECONDS,
    )
    expected_code = 1 if check.check_type == "tool_version_exit_1" else 0
    if timed_out:
        return Result(
            check,
            "fail",
            output or f"timeout after {TOOL_PROBE_TIMEOUT_SECONDS} seconds",
            "Version probe timed out; "
            f"{_timing_detail(elapsed, TOOL_PROBE_TIMEOUT_SECONDS)}",
        )
    if code != expected_code:
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
    guarded = environment is not None and environment.get("EMRYS_LOCAL_PILOT_R") == "1"
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
            "pkg <- normalizePath(pkg, winslash='/', mustWork=TRUE); "
            "if (!identical(pkg, expected)) quit(status=44); "
            "ns <- tryCatch(suppressWarnings(loadNamespace(p, lib.loc=lib)), "
            "error=function(e) NULL); "
            "if (is.null(ns)) quit(status=42); "
            "where <- normalizePath(getNamespaceInfo(ns, 'path'), winslash='/', "
            "mustWork=TRUE); "
            "if (!identical(where, expected)) quit(status=44); "
            "root_hex <- paste(sprintf('%02x', as.integer(charToRaw(enc2utf8(where)))), "
            "collapse=''); "
            f"cat(as.character(utils::packageVersion(p, lib.loc=lib)), "
            f"'{R_NAMESPACE_ROOT_OUTPUT_MARKER}', root_hex, sep='')"
        )
        arguments = guarded_rscript_argv(
            rscript,
            ("-e", expression, check.target, environment["EMRYS_RENV_LIBRARY"]),
        )
    else:
        expression = (
            "p <- commandArgs(TRUE)[1]; "
            "if (!suppressWarnings(requireNamespace(p, quietly=TRUE))) "
            "quit(status=42); "
            "cat(as.character(utils::packageVersion(p)))"
        )
        arguments = [rscript, "-e", expression, check.target]
    code, output, elapsed, timed_out = run_command(
        arguments,
        None,
        environment,
        R_NAMESPACE_PROBE_TIMEOUT_SECONDS,
    )
    elapsed_detail = _timing_detail(elapsed, R_NAMESPACE_PROBE_TIMEOUT_SECONDS)
    if timed_out:
        return Result(
            check,
            "fail",
            output or f"timeout after {R_NAMESPACE_PROBE_TIMEOUT_SECONDS} seconds",
            f"R namespace probe timed out; {elapsed_detail}",
        )
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
        detail = f"{details.get(code, 'R namespace probe failed')}; {elapsed_detail}"
        return Result(check, "fail", output or f"exit {code}", detail)
    version_output = output
    resolved_root: Path | None = None
    if guarded:
        parsed = _guarded_namespace_output(output)
        if parsed is None:
            return Result(
                check,
                "fail",
                output,
                "R namespace probe did not report its exact canonical root; "
                + elapsed_detail,
            )
        version_output, resolved_root = parsed
    if re.fullmatch(check.expected, version_output) is None:
        return Result(
            check,
            "fail",
            version_output,
            "Namespace version did not match expected regex; " + elapsed_detail,
        )
    detail = (
        "Resolved R package root: "
        f"{resolved_root}; "
        f"{elapsed_detail}"
        if guarded and environment is not None
        else (
            f"Resolved Rscript: {rscript}; {elapsed_detail}"
        )
    )
    return Result(
        check,
        "pass",
        version_output,
        detail,
        None if resolved_root is None else str(resolved_root),
    )


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
    code, output, elapsed, timed_out = run_command(
        command,
        HASH_PAYLOAD,
        environment,
        TOOL_PROBE_TIMEOUT_SECONDS,
    )
    observed = output.split()[0].lower() if output else ""
    if timed_out:
        return Result(
            check,
            "fail",
            output or f"timeout after {TOOL_PROBE_TIMEOUT_SECONDS} seconds",
            "SHA-256 probe timed out; "
            f"{_timing_detail(elapsed, TOOL_PROBE_TIMEOUT_SECONDS)}",
        )
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
    "tool_version_exit_1": _probe_tool,
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
