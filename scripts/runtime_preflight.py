#!/usr/bin/env python3
"""Run explicit, read-only runtime availability checks.

This command never installs software, loads modules, searches for inputs, or
executes analysis. A passing report records only the probes performed in the
declared runtime context; it is not runtime validation or cluster proof.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


PROFILE_HEADER = (
    "check_id",
    "check_type",
    "runtime_context",
    "required",
    "target",
    "probe_args",
    "expected",
    "description",
)
RESULT_HEADER = (
    "profile_sha256",
    "runtime_context",
    "check_id",
    "check_type",
    "target",
    "required",
    "status",
    "observed",
    "expected",
    "detail",
)
CHECK_TYPES = {
    "tool_version",
    "r_namespace",
    "hash_utility",
    "path_visibility",
}
RUNTIME_CONTEXTS = {"local", "cluster_batch", "any"}
RESULT_STATUSES = {"pass", "fail", "blocked", "not_checked"}
VISIBILITY_PROBES = {
    "file_readable",
    "directory_readable",
    "executable",
}
HASH_PROBES = {"python_hashlib", "sha256sum", "shasum"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VERSION_TEXT_LIMIT = 4096
PROBE_TIMEOUT_SECONDS = 30
HASH_PAYLOAD = b"norad-runtime-preflight\n"
HASH_EXPECTED = hashlib.sha256(HASH_PAYLOAD).hexdigest()


class PreflightError(RuntimeError):
    """Raised for invalid inputs or unsafe publication state."""


@dataclass(frozen=True)
class Check:
    check_id: str
    check_type: str
    runtime_context: str
    required: bool
    target: str
    probe_args: tuple[str, ...]
    expected: str
    description: str


@dataclass(frozen=True)
class Result:
    check: Check
    status: str
    observed: str
    detail: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run explicit, read-only runtime checks and optionally publish "
            "one deterministic TSV report."
        )
    )
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--runtime-context",
        required=True,
        choices=("local", "cluster_batch"),
        help="Context in which probes are actually running.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Atomically publish the validated TSV; dry-run is the default.",
    )
    return parser.parse_args(argv)


def _fail(message: str) -> None:
    raise PreflightError(message)


def _single_line(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())


def _read_regular_file(path: Path, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(before.st_mode):
        _fail(f"{label} must not be a symbolic link: {path}")
    if not stat.S_ISREG(before.st_mode):
        _fail(f"{label} must be a regular file: {path}")
    try:
        data = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        _fail(f"Could not read {label}: {path}: {exc}")
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        _fail(f"{label} changed while it was read: {path}")
    return data


def _parse_probe_args(raw: str, row_number: int) -> tuple[str, ...]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"Profile row {row_number} probe_args is not valid JSON: {exc}")
    if not isinstance(value, list) or not all(
        isinstance(item, str) and "\x00" not in item for item in value
    ):
        _fail(
            f"Profile row {row_number} probe_args must be a JSON array of strings"
        )
    return tuple(value)


def load_profile(path: Path) -> tuple[bytes, list[Check]]:
    data = _read_regular_file(path, "Runtime profile")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(f"Runtime profile is not UTF-8: {path}: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if reader.fieldnames is None:
        _fail("Runtime profile is empty")
    if tuple(reader.fieldnames) != PROFILE_HEADER:
        _fail(
            "Runtime profile header must be exactly: " + "\t".join(PROFILE_HEADER)
        )
    checks: list[Check] = []
    seen: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            _fail(f"Runtime profile row {row_number} has extra columns")
        values = {key: value if value is not None else "" for key, value in row.items()}
        if any("\x00" in value or "\n" in value or "\r" in value for value in values.values()):
            _fail(f"Runtime profile row {row_number} contains an unsafe character")
        check_id = values["check_id"]
        if not SAFE_ID.fullmatch(check_id):
            _fail(f"Runtime profile row {row_number} has invalid check_id: {check_id!r}")
        if check_id in seen:
            _fail(f"Runtime profile has duplicate check_id: {check_id}")
        seen.add(check_id)
        check_type = values["check_type"]
        if check_type not in CHECK_TYPES:
            _fail(f"Runtime profile row {row_number} has invalid check_type: {check_type}")
        runtime_context = values["runtime_context"]
        if runtime_context not in RUNTIME_CONTEXTS:
            _fail(
                f"Runtime profile row {row_number} has invalid runtime_context: "
                f"{runtime_context}"
            )
        required_raw = values["required"]
        if required_raw not in {"true", "false"}:
            _fail(f"Runtime profile row {row_number} required must be true or false")
        target = values["target"]
        expected = values["expected"]
        description = values["description"]
        if not target or not expected or not description:
            _fail(
                f"Runtime profile row {row_number} target, expected, and "
                "description must be nonempty"
            )
        probe_args = _parse_probe_args(values["probe_args"], row_number)
        check = Check(
            check_id=check_id,
            check_type=check_type,
            runtime_context=runtime_context,
            required=required_raw == "true",
            target=target,
            probe_args=probe_args,
            expected=expected,
            description=description,
        )
        _validate_check_contract(check, row_number)
        checks.append(check)
    if not checks:
        _fail("Runtime profile must contain at least one check")
    return data, checks


def _validate_regex(pattern: str, row_number: int) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:
        _fail(f"Runtime profile row {row_number} expected regex is invalid: {exc}")


def _validate_check_contract(check: Check, row_number: int) -> None:
    if check.check_type == "tool_version":
        if not check.probe_args:
            _fail(f"Runtime profile row {row_number} tool_version needs probe_args")
        _validate_regex(check.expected, row_number)
    elif check.check_type == "r_namespace":
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9.]*", check.target) is None:
            _fail(
                f"Runtime profile row {row_number} r_namespace target "
                "must be an R package name"
            )
        if len(check.probe_args) != 1 or not check.probe_args[0]:
            _fail(
                f"Runtime profile row {row_number} r_namespace probe_args must "
                "contain exactly one Rscript executable"
            )
        _validate_regex(check.expected, row_number)
    elif check.check_type == "hash_utility":
        if len(check.probe_args) != 1 or check.probe_args[0] not in HASH_PROBES:
            _fail(
                f"Runtime profile row {row_number} hash_utility probe_args must "
                f"contain one of: {', '.join(sorted(HASH_PROBES))}"
            )
        if check.expected != "sha256":
            _fail(
                f"Runtime profile row {row_number} hash_utility expected must be sha256"
            )
    elif check.check_type == "path_visibility":
        if not Path(check.target).is_absolute():
            _fail(
                f"Runtime profile row {row_number} path_visibility target "
                "must be absolute"
            )
        if len(check.probe_args) != 1 or check.probe_args[0] not in VISIBILITY_PROBES:
            _fail(
                f"Runtime profile row {row_number} path_visibility probe_args "
                f"must contain one of: {', '.join(sorted(VISIBILITY_PROBES))}"
            )
        expected = (
            "executable"
            if check.probe_args and check.probe_args[0] == "executable"
            else "readable"
        )
        if check.expected != expected:
            _fail(
                f"Runtime profile row {row_number} path_visibility expected "
                f"must be {expected}"
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
        return Result(check, "fail", output, "Version output did not match expected regex")
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
        detail = "R namespace is unavailable" if code == 42 else "R namespace probe failed"
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


def result_bytes(
    profile_sha256: str,
    runtime_context: str,
    results: Sequence[Result],
) -> bytes:
    rows = ["\t".join(RESULT_HEADER)]
    for result in results:
        values = (
            profile_sha256,
            runtime_context,
            result.check.check_id,
            result.check.check_type,
            result.check.target,
            "true" if result.check.required else "false",
            result.status,
            result.observed,
            result.check.expected,
            result.detail,
        )
        rows.append("\t".join(_single_line(value) for value in values))
    return ("\n".join(rows) + "\n").encode("utf-8")


def validate_result_bytes(
    data: bytes,
    profile_sha256: str,
    runtime_context: str,
    checks: Sequence[Check],
) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(f"Runtime preflight output is not UTF-8: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != RESULT_HEADER:
        _fail("Runtime preflight output has an invalid header")
    rows = list(reader)
    if len(rows) != len(checks):
        _fail("Runtime preflight output row count does not match the profile")
    seen: set[str] = set()
    for row, check in zip(rows, checks, strict=True):
        if None in row or any(value is None for value in row.values()):
            _fail("Runtime preflight output has an invalid row shape")
        if row["profile_sha256"] != profile_sha256:
            _fail("Runtime preflight output profile hash does not match")
        if row["runtime_context"] != runtime_context:
            _fail("Runtime preflight output context does not match")
        if row["status"] not in RESULT_STATUSES:
            _fail("Runtime preflight output has an invalid status")
        if row["check_id"] in seen:
            _fail("Runtime preflight output has duplicate check IDs")
        seen.add(row["check_id"])
        expected_fields = {
            "check_id": check.check_id,
            "check_type": check.check_type,
            "target": check.target,
            "required": "true" if check.required else "false",
            "expected": check.expected,
        }
        for field, expected_value in expected_fields.items():
            if row[field] != expected_value:
                _fail(
                    f"Runtime preflight output {field} does not match the "
                    f"profile for check {check.check_id}"
                )


def _ensure_output_parent(output: Path) -> None:
    parent = output.parent
    try:
        metadata = parent.lstat()
    except OSError as exc:
        _fail(f"Output parent must already exist: {parent}: {exc}")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail(f"Output parent must be a real directory: {parent}")
    if output.name in {"", ".", ".."}:
        _fail("Output must name one TSV file")
    if output.suffix != ".tsv":
        _fail(f"Output must use the .tsv suffix: {output}")


def _acquire_lock(lock_path: Path) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except FileExistsError:
        _fail(f"Runtime preflight lock already exists: {lock_path}")
    except OSError as exc:
        _fail(f"Could not acquire runtime preflight lock: {lock_path}: {exc}")
    os.write(descriptor, f"pid={os.getpid()}\n".encode())
    os.fsync(descriptor)
    return descriptor


def publish(
    output: Path,
    data: bytes,
    profile_sha256: str,
    runtime_context: str,
    checks: Sequence[Check],
) -> None:
    _ensure_output_parent(output)
    lock = output.with_name(f".{output.name}.lock")
    token = uuid.uuid4().hex
    staged = output.with_name(f".{output.name}.{token}.tmp")
    backup = output.with_name(f".{output.name}.{token}.previous")
    descriptor = _acquire_lock(lock)
    had_previous = output.exists()
    try:
        if output.is_symlink():
            _fail(f"Output must not be a symbolic link: {output}")
        if had_previous:
            previous = _read_regular_file(output, "Existing runtime preflight output")
            validate_result_bytes(
                previous, profile_sha256, runtime_context, checks
            )
        with staged.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        validate_result_bytes(
            _read_regular_file(staged, "Staged runtime preflight output"),
            profile_sha256,
            runtime_context,
            checks,
        )
        if had_previous:
            os.replace(output, backup)
        try:
            os.replace(staged, output)
            validate_result_bytes(
                _read_regular_file(output, "Published runtime preflight output"),
                profile_sha256,
                runtime_context,
                checks,
            )
        except BaseException:
            if output.exists() and not output.is_symlink():
                output.unlink()
            if had_previous and backup.exists():
                os.replace(backup, output)
            raise
        if backup.exists():
            backup.unlink()
    finally:
        if staged.exists() and not staged.is_symlink():
            staged.unlink()
        os.close(descriptor)
        try:
            lock.unlink()
        except OSError:
            pass


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        profile_data, checks = load_profile(args.profile)
        profile_sha256 = hashlib.sha256(profile_data).hexdigest()
        results = run_checks(checks, args.runtime_context)
        rendered = result_bytes(profile_sha256, args.runtime_context, results)
        validate_result_bytes(rendered, profile_sha256, args.runtime_context, checks)

        print(f"Runtime profile: {args.profile}")
        print(f"Profile SHA-256: {profile_sha256}")
        print(f"Runtime context: {args.runtime_context}")
        print(f"Output: {args.output}")
        for result in results:
            print(
                f"{result.check.check_id}: {result.status} "
                f"({result.observed})"
            )
        print(
            "Evidence boundary: availability checks only; this is not runtime "
            "validation or cluster proof."
        )
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0

        current_profile = _read_regular_file(args.profile, "Runtime profile")
        if hashlib.sha256(current_profile).hexdigest() != profile_sha256:
            _fail("Runtime profile changed after checks")
        publish(
            args.output,
            rendered,
            profile_sha256,
            args.runtime_context,
            checks,
        )
        print(f"Published runtime preflight report: {args.output}")
        return 0
    except PreflightError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
