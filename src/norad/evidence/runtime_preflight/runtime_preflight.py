#!/usr/bin/env python3
"""Run explicit, read-only runtime availability checks.

This command never installs software, loads modules, searches for inputs, or
executes analysis. A passing report records only the probes performed in the
declared runtime context; it is not runtime validation or cluster proof.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import stat
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
sys.path[:] = list(dict.fromkeys((src_root, *sys.path)))

from norad.evidence.runtime_preflight._probes import (
    PROBES,
    _probe_hash_utility,
    _probe_path_visibility,
    _probe_r_namespace,
    _probe_tool,
    _resolve_executable,
    _run_command,
    run_checks,
)
from norad.evidence.runtime_preflight._profile_contract import (
    _parse_probe_args,
    _read_regular_file,
    _validate_check_contract,
    _validate_regex,
    load_profile,
)
from norad.evidence.runtime_preflight._result_contract import (
    result_bytes,
    validate_result_bytes,
)
from norad.evidence.runtime_preflight._runtime_model import (
    CHECK_TYPES,
    HASH_EXPECTED,
    HASH_PAYLOAD,
    HASH_PROBES,
    PROBE_TIMEOUT_SECONDS,
    PROFILE_HEADER,
    RESULT_HEADER,
    RESULT_STATUSES,
    RUNTIME_CONTEXTS,
    SAFE_ID,
    VERSION_TEXT_LIMIT,
    VISIBILITY_PROBES,
    Check,
    PreflightError,
    Result,
    _fail,
    _single_line,
)

__all__ = [
    "CHECK_TYPES",
    "HASH_EXPECTED",
    "HASH_PAYLOAD",
    "HASH_PROBES",
    "PROBES",
    "PROBE_TIMEOUT_SECONDS",
    "PROFILE_HEADER",
    "RESULT_HEADER",
    "RESULT_STATUSES",
    "RUNTIME_CONTEXTS",
    "SAFE_ID",
    "VERSION_TEXT_LIMIT",
    "VISIBILITY_PROBES",
    "Check",
    "PreflightError",
    "Result",
    "_fail",
    "_parse_probe_args",
    "_probe_hash_utility",
    "_probe_path_visibility",
    "_probe_r_namespace",
    "_probe_tool",
    "_read_regular_file",
    "_resolve_executable",
    "_run_command",
    "_single_line",
    "_validate_check_contract",
    "_validate_regex",
    "load_profile",
    "main",
    "parse_args",
    "publish",
    "result_bytes",
    "run_checks",
    "validate_result_bytes",
]


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
            validate_result_bytes(previous, profile_sha256, runtime_context, checks)
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
        with contextlib.suppress(OSError):
            lock.unlink()


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
            print(f"{result.check.check_id}: {result.status} ({result.observed})")
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
