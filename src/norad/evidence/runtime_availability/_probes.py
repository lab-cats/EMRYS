"""Read-only availability probes for runtime-preflight evidence."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

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


def _resolve_executable(target: str) -> str | None:
    if "/" in target:
        path = Path(target)
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(target)


def _run_command(command: list[str], stdin: bytes | None = None) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, _single_line(str(exc))
    output = completed.stdout[:VERSION_TEXT_LIMIT].decode("utf-8", errors="replace")
    return completed.returncode, _single_line(output)


def _probe_tool(check: Check) -> Result:
    executable = _resolve_executable(check.target)
    if executable is None:
        return Result(check, "fail", "unavailable", "Executable was not found")
    code, output = _run_command([executable, *check.probe_args])
    if code != 0:
        return Result(check, "fail", output or f"exit {code}", "Version probe failed")
    if re.search(check.expected, output) is None:
        return Result(
            check, "fail", output, "Version output did not match expected regex"
        )
    return Result(check, "pass", output, f"Resolved executable: {executable}")


def _probe_r_namespace(check: Check) -> Result:
    rscript = _resolve_executable(check.probe_args[0])
    if rscript is None:
        return Result(check, "fail", "unavailable", "Rscript executable was not found")
    expression = (
        "p <- commandArgs(TRUE)[1]; "
        "if (!requireNamespace(p, quietly=TRUE)) quit(status=42); "
        "cat(as.character(utils::packageVersion(p)))"
    )
    code, output = _run_command([rscript, "-e", expression, "--args", check.target])
    if code != 0:
        detail = (
            "R namespace is unavailable" if code == 42 else "R namespace probe failed"
        )
        return Result(check, "fail", output or f"exit {code}", detail)
    if re.fullmatch(check.expected, output) is None:
        return Result(
            check,
            "fail",
            output,
            "Namespace version did not match expected regex",
        )
    return Result(check, "pass", output, f"Resolved Rscript: {rscript}")


def _probe_hash_utility(check: Check) -> Result:
    executable = _resolve_executable(check.target)
    if executable is None:
        return Result(check, "fail", "unavailable", "Hash executable was not found")
    adapter = check.probe_args[0]
    if adapter == "python_hashlib":
        command = [
            executable,
            "-c",
            "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())",
        ]
    elif adapter == "sha256sum":
        command = [executable]
    else:
        command = [executable, "-a", "256"]
    code, output = _run_command(command, HASH_PAYLOAD)
    observed = output.split()[0].lower() if output else ""
    if code != 0:
        return Result(check, "fail", output or f"exit {code}", "SHA-256 probe failed")
    if observed != HASH_EXPECTED:
        return Result(check, "fail", observed or "empty", "SHA-256 digest mismatch")
    return Result(check, "pass", observed, f"Resolved executable: {executable}")


def _probe_path_visibility(check: Check) -> Result:
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


PROBES: dict[str, Callable[[Check], Result]] = {
    "tool_version": _probe_tool,
    "r_namespace": _probe_r_namespace,
    "hash_utility": _probe_hash_utility,
    "path_visibility": _probe_path_visibility,
}


def run_checks(checks: Sequence[Check], runtime_context: str) -> list[Result]:
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
        result = PROBES[check.check_type](check)
        if result.status not in RESULT_STATUSES:
            _fail(f"Internal error: invalid result status {result.status}")
        results.append(result)
    return results
