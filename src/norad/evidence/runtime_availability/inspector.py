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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ._probes import run_checks
from ._profile_contract import _read_regular_file, load_profile
from ._result_contract import (
    result_bytes,
    validate_result_bytes,
)
from ._runtime_model import Check, PreflightError, _fail

DESCRIPTION = (
    "Run explicit, read-only runtime checks and optionally publish "
    "one deterministic TSV report."
)


@dataclass(frozen=True, slots=True)
class RuntimeCheck:
    """One normalized check admitted from an explicit runtime profile."""

    check_id: str
    check_type: str
    runtime_context: str
    required: bool
    target: str
    probe_args: tuple[str, ...]
    expected: str
    description: str


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    """One completed availability observation without publication authority."""

    check: RuntimeCheck
    status: str
    observed: str
    detail: str


@dataclass(frozen=True, slots=True)
class RuntimeInspection:
    """Immutable read-only result for one explicit runtime profile."""

    profile_path: Path
    profile_sha256: str
    profile_bytes: bytes
    runtime_context: str
    observations: tuple[RuntimeObservation, ...]
    rendered_bytes: bytes

    @property
    def required_ready(self) -> bool:
        """Return whether every required check ran and passed."""

        return all(
            not observation.check.required or observation.status == "pass"
            for observation in self.observations
        )


class RuntimeInspectionError(RuntimeError):
    """The declared runtime profile could not be inspected safely."""


def _public_check(check: Check) -> RuntimeCheck:
    return RuntimeCheck(
        check_id=check.check_id,
        check_type=check.check_type,
        runtime_context=check.runtime_context,
        required=check.required,
        target=check.target,
        probe_args=check.probe_args,
        expected=check.expected,
        description=check.description,
    )


def inspect_runtime_availability(
    profile: Path,
    runtime_context: str,
    *,
    environment: Mapping[str, str] | None = None,
) -> RuntimeInspection:
    """Run one explicit profile without publishing or repairing anything."""

    try:
        if runtime_context not in {"local", "cluster_batch"}:
            _fail(f"Unsupported runtime context: {runtime_context}")
        profile_data, checks = load_profile(profile)
        profile_sha256 = hashlib.sha256(profile_data).hexdigest()
        if environment is None:
            results = run_checks(checks, runtime_context)
        else:
            results = run_checks(checks, runtime_context, environment=environment)
        rendered = result_bytes(profile_sha256, runtime_context, results)
        validate_result_bytes(rendered, profile_sha256, runtime_context, checks)
    except PreflightError as exc:
        raise RuntimeInspectionError(str(exc)) from exc
    observations = tuple(
        RuntimeObservation(
            check=_public_check(result.check),
            status=result.status,
            observed=result.observed,
            detail=result.detail,
        )
        for result in results
    )
    return RuntimeInspection(
        profile_path=profile,
        profile_sha256=profile_sha256,
        profile_bytes=profile_data,
        runtime_context=runtime_context,
        observations=observations,
        rendered_bytes=rendered,
    )


def load_runtime_profile_contract(
    profile: Path,
) -> tuple[bytes, tuple[RuntimeCheck, ...]]:
    """Read and validate one profile without running any declared probes."""

    try:
        data, checks = load_profile(profile)
    except PreflightError as exc:
        raise RuntimeInspectionError(str(exc)) from exc
    return data, tuple(_public_check(check) for check in checks)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add runtime-availability inspection arguments to ``parser``."""
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


def inspect_from_args(args: argparse.Namespace) -> int:
    """Inspect declared runtime availability and optionally publish evidence."""
    try:
        inspection = inspect_runtime_availability(
            args.profile,
            args.runtime_context,
        )
        profile_data, checks = load_profile(args.profile)
        if profile_data != inspection.profile_bytes:
            _fail("Runtime profile changed during inspection")

        print(f"Runtime profile: {args.profile}")
        print(f"Profile SHA-256: {inspection.profile_sha256}")
        print(f"Runtime context: {args.runtime_context}")
        print(f"Output: {args.output}")
        for observation in inspection.observations:
            print(
                f"{observation.check.check_id}: {observation.status} "
                f"({observation.observed})"
            )
        print(
            "Evidence boundary: availability checks only; this is not runtime "
            "validation or cluster proof."
        )
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0

        current_profile = _read_regular_file(args.profile, "Runtime profile")
        if current_profile != inspection.profile_bytes:
            _fail("Runtime profile changed after checks")
        publish(
            args.output,
            inspection.rendered_bytes,
            inspection.profile_sha256,
            args.runtime_context,
            checks,
        )
        print(f"Published runtime preflight report: {args.output}")
        return 0
    except (PreflightError, RuntimeInspectionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


__all__ = (
    "RuntimeCheck",
    "RuntimeInspection",
    "RuntimeInspectionError",
    "RuntimeObservation",
    "configure_parser",
    "inspect_from_args",
    "inspect_runtime_availability",
)
