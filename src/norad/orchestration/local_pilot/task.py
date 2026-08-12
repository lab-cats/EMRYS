"""Execute one closed local-pilot functional-owner task.

This module is the job boundary used by the fixed Snakemake workflow.  It is
deliberately not registered as a top-level ``norad`` command: the lifecycle
adapter remains a later campaign phase.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from norad.contracts.orchestration import api as orchestration_contracts

DISPATCH_SCHEMA_VERSION = "norad.local-task-dispatch.v1"
_DISPATCH_FIELDS = frozenset(
    {
        "schema_version",
        "run_root",
        "execution_path",
        "profile_path",
        "workflow_attempt_id",
        "task_attempt_id",
        "owner_run_token",
        "machine_key",
        "scope",
        "producer_argv",
        "validator_argv",
        "inputs",
        "outputs",
        "validation_report_path",
        "native_receipt_path",
        "task_attempt_path",
        "verified_task_path",
        "stdout_path",
        "stderr_path",
    }
)
_DECLARATION_FIELDS = frozenset({"role", "path"})
_SCOPE_FIELDS = frozenset({"scope_type", "scope_id"})
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class TaskBoundaryError(RuntimeError):
    """Raised when a task cannot prove one verified owner result."""


@dataclass(frozen=True, slots=True)
class FileDeclaration:
    """One role-bearing file path admitted from the dispatch."""

    role: str
    path: Path


@dataclass(frozen=True, slots=True)
class TaskBackend:
    """Exact public producer and validator commands for one owner invocation."""

    producer_argv: tuple[str, ...]
    validator_argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskDispatch:
    """Closed materialized job description consumed by one task invocation."""

    path: Path
    run_root: Path
    execution_path: Path
    profile_path: Path
    workflow_attempt_id: str
    task_attempt_id: str
    owner_run_token: str
    machine_key: str
    scope: dict[str, str]
    backend: TaskBackend
    inputs: tuple[FileDeclaration, ...]
    outputs: tuple[FileDeclaration, ...]
    validation_report_path: Path
    native_receipt_path: Path | None
    task_attempt_path: Path
    verified_task_path: Path
    stdout_path: Path
    stderr_path: Path


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Complete captured result for one delegated public command."""

    argv: tuple[str, ...]
    exit_code: int
    stdout: bytes
    stderr: bytes

    @property
    def record(self) -> dict[str, Any]:
        return {"argv": list(self.argv), "exit_code": self.exit_code}


CommandRunner = Callable[[tuple[str, ...], Path], CommandResult]
BytesPublisher = Callable[[Path, bytes], None]
Clock = Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class TaskOps:
    """Explicit effect boundary used by task execution and fault tests."""

    run_command: CommandRunner
    run_semantic_all_pass: CommandRunner
    publish_bytes: BytesPublisher
    now: Clock


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    """Paths and immutable records published by one successful task."""

    task_attempt_path: Path
    verified_task_path: Path
    task_attempt: dict[str, Any]
    verified_task: dict[str, Any]


def _closed_object(
    value: Any,
    *,
    fields: frozenset[str],
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TaskBoundaryError(f"{label} must be one object")
    observed = set(value)
    missing = fields - observed
    unknown = observed - fields
    if missing or unknown:
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if unknown:
            details.append("unknown " + ", ".join(sorted(unknown)))
        raise TaskBoundaryError(f"{label} is not closed: {'; '.join(details)}")
    return value


def _safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TaskBoundaryError(f"{label} must be a nonempty safe ID")
    if _SAFE_ID_RE.fullmatch(value) is None:
        raise TaskBoundaryError(f"{label} is not a safe ID: {value!r}")
    return value


def _absolute_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise TaskBoundaryError(f"{label} must be a nonempty absolute path")
    path = Path(value)
    if not path.is_absolute() or str(path) != value:
        raise TaskBoundaryError(f"{label} must be a lexical absolute path: {value!r}")
    if any(part in {"", ".", ".."} for part in path.parts[1:]):
        raise TaskBoundaryError(f"{label} contains a forbidden path component")
    return path


def _command(value: Any, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(part, str) or not part.strip() for part in value)
    ):
        raise TaskBoundaryError(f"{label} must be a nonempty string argv array")
    return tuple(value)


def _declarations(value: Any, label: str) -> tuple[FileDeclaration, ...]:
    if not isinstance(value, list) or not value:
        raise TaskBoundaryError(f"{label} must be a nonempty declaration array")
    declarations: list[FileDeclaration] = []
    roles: set[str] = set()
    paths: set[Path] = set()
    for index, raw in enumerate(value):
        item = _closed_object(
            raw,
            fields=_DECLARATION_FIELDS,
            label=f"{label}[{index}]",
        )
        role = _safe_id(item["role"], f"{label}[{index}].role")
        path = _absolute_path(item["path"], f"{label}[{index}].path")
        if role in roles:
            raise TaskBoundaryError(f"{label} repeats role: {role}")
        if path in paths:
            raise TaskBoundaryError(f"{label} repeats path: {path}")
        roles.add(role)
        paths.add(path)
        declarations.append(FileDeclaration(role=role, path=path))
    return tuple(declarations)


def _within(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise TaskBoundaryError(f"{label} must be beneath run_root: {path}") from exc


def _safe_in_run_destination(path: Path, root: Path, label: str) -> None:
    """Reject lexical escape and every existing symlink ancestor."""

    _within(path, root, label)
    relative = path.relative_to(root)
    cursor = root
    for part in relative.parts[:-1]:
        cursor = cursor / part
        try:
            state = cursor.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            raise TaskBoundaryError(
                f"Could not inspect {label}: {cursor}: {exc}"
            ) from exc
        if stat.S_ISLNK(state.st_mode):
            raise TaskBoundaryError(f"{label} has a symlink ancestor: {cursor}")
        if not stat.S_ISDIR(state.st_mode):
            raise TaskBoundaryError(f"{label} parent is not a directory: {cursor}")


def load_dispatch(path: Path) -> TaskDispatch:
    """Load one strict, closed dispatch without performing task mutations."""

    dispatch_path = _absolute_path(str(path), "dispatch path")
    raw = orchestration_contracts.load_json_object(dispatch_path)
    record = _closed_object(raw, fields=_DISPATCH_FIELDS, label="task dispatch")
    if record["schema_version"] != DISPATCH_SCHEMA_VERSION:
        raise TaskBoundaryError(
            f"task dispatch schema_version must be {DISPATCH_SCHEMA_VERSION}"
        )

    run_root = _absolute_path(record["run_root"], "run_root")
    if not run_root.is_dir() or run_root.is_symlink():
        raise TaskBoundaryError(f"run_root must be a real directory: {run_root}")
    canonical_root = run_root.resolve(strict=True)
    if canonical_root != run_root:
        raise TaskBoundaryError(f"run_root must already be canonical: {run_root}")

    scope_record = _closed_object(record["scope"], fields=_SCOPE_FIELDS, label="scope")
    scope = {
        "scope_type": _safe_id(scope_record["scope_type"], "scope.scope_type"),
        "scope_id": _safe_id(scope_record["scope_id"], "scope.scope_id"),
    }
    native_value = record["native_receipt_path"]
    native_receipt = (
        None
        if native_value is None
        else _absolute_path(native_value, "native_receipt_path")
    )
    result = TaskDispatch(
        path=dispatch_path,
        run_root=run_root,
        execution_path=_absolute_path(record["execution_path"], "execution_path"),
        profile_path=_absolute_path(record["profile_path"], "profile_path"),
        workflow_attempt_id=_safe_id(
            record["workflow_attempt_id"], "workflow_attempt_id"
        ),
        task_attempt_id=_safe_id(record["task_attempt_id"], "task_attempt_id"),
        owner_run_token=_safe_id(record["owner_run_token"], "owner_run_token"),
        machine_key=_safe_id(record["machine_key"], "machine_key"),
        scope=scope,
        backend=TaskBackend(
            producer_argv=_command(record["producer_argv"], "producer_argv"),
            validator_argv=_command(record["validator_argv"], "validator_argv"),
        ),
        inputs=_declarations(record["inputs"], "inputs"),
        outputs=_declarations(record["outputs"], "outputs"),
        validation_report_path=_absolute_path(
            record["validation_report_path"], "validation_report_path"
        ),
        native_receipt_path=native_receipt,
        task_attempt_path=_absolute_path(
            record["task_attempt_path"], "task_attempt_path"
        ),
        verified_task_path=_absolute_path(
            record["verified_task_path"], "verified_task_path"
        ),
        stdout_path=_absolute_path(record["stdout_path"], "stdout_path"),
        stderr_path=_absolute_path(record["stderr_path"], "stderr_path"),
    )

    mutable_paths = {
        *(item.path for item in result.outputs),
        result.validation_report_path,
        result.task_attempt_path,
        result.verified_task_path,
        result.stdout_path,
        result.stderr_path,
    }
    if result.native_receipt_path is not None:
        mutable_paths.add(result.native_receipt_path)
    expected_mutable_count = (
        len(result.outputs) + 5 + (result.native_receipt_path is not None)
    )
    if len(mutable_paths) != expected_mutable_count:
        raise TaskBoundaryError("task dispatch aliases mutable destination paths")
    admitted_inputs = {
        result.path,
        result.execution_path,
        result.profile_path,
        *(item.path for item in result.inputs),
    }
    if admitted_inputs & mutable_paths:
        raise TaskBoundaryError(
            "task dispatch aliases an input and mutable destination"
        )
    in_run_paths = mutable_paths - {item.path for item in result.outputs}
    for mutable in in_run_paths:
        _safe_in_run_destination(mutable, result.run_root, "mutable task path")
    _safe_in_run_destination(result.path, result.run_root, "dispatch path")
    _safe_in_run_destination(
        result.execution_path, result.run_root, "execution contract path"
    )
    _safe_in_run_destination(
        result.profile_path, result.run_root, "workflow profile path"
    )
    return result


def _read_bound_file(path: Path, label: str) -> tuple[bytes, os.stat_result]:
    if not hasattr(os, "O_NOFOLLOW"):
        raise TaskBoundaryError("This platform lacks required O_NOFOLLOW admission")
    try:
        if path.resolve(strict=True) != path:
            raise TaskBoundaryError(f"{label} path is not canonical: {path}")
    except OSError as exc:
        raise TaskBoundaryError(f"Could not resolve {label}: {path}: {exc}") from exc
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= os.O_NOFOLLOW
    flags |= getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise TaskBoundaryError(f"Could not admit {label}: {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise TaskBoundaryError(f"{label} is not a regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        path_state = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise TaskBoundaryError(f"Could not restat {label}: {path}: {exc}") from exc
    identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    if identity != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise TaskBoundaryError(f"{label} changed while it was read: {path}")
    if identity != (
        path_state.st_dev,
        path_state.st_ino,
        path_state.st_size,
        path_state.st_mtime_ns,
        path_state.st_ctime_ns,
    ):
        raise TaskBoundaryError(f"{label} path changed while it was read: {path}")
    return b"".join(chunks), after


def _snapshot(declaration: FileDeclaration) -> dict[str, Any]:
    data, state = _read_bound_file(declaration.path, declaration.role)
    return {
        "role": declaration.role,
        "path": str(declaration.path),
        "size_bytes": state.st_size,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _record_reference(path: Path, run_root: Path) -> dict[str, str]:
    data, _ = _read_bound_file(path, "record reference")
    return {
        "path": path.relative_to(run_root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _load_bound_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    data, _ = _read_bound_file(path, label)
    try:
        value = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TaskBoundaryError(f"Could not parse {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TaskBoundaryError(f"{label} must contain one JSON object: {path}")
    if orchestration_contracts.canonical_json_bytes(value) != data:
        raise TaskBoundaryError(f"{label} must use canonical JSON bytes: {path}")
    return value, data


def _default_run_command(argv: tuple[str, ...], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        message = f"Could not execute {argv[0]}: {exc}\n".encode(
            "utf-8", errors="backslashreplace"
        )
        exit_code = 127 if exc.errno == errno.ENOENT else 126
        return CommandResult(argv, exit_code, b"", message)
    exit_code = completed.returncode if 0 <= completed.returncode <= 255 else 128
    return CommandResult(argv, exit_code, completed.stdout, completed.stderr)


def _publish_bytes(path: Path, data: bytes) -> None:
    """Durably publish bytes at an absent final path without replacement."""

    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        raise TaskBoundaryError(
            f"Publication parent must be a real directory: {parent}"
        )
    staging = parent / f".{path.name}.{uuid.uuid4().hex}.norad-stage"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(staging, flags, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(staging, path, follow_symlinks=False)
        staged = staging.stat(follow_symlinks=False)
        final = path.stat(follow_symlinks=False)
        if (staged.st_dev, staged.st_ino) != (final.st_dev, final.st_ino):
            raise TaskBoundaryError(
                f"Create-exclusive publication lost staged inode: {path}"
            )
        staging.unlink()
        directory = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileExistsError as exc:
        raise TaskBoundaryError(f"Refusing to replace existing file: {path}") from exc
    except OSError as exc:
        raise TaskBoundaryError(f"Could not publish {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


def default_task_ops() -> TaskOps:
    """Construct the production effect boundary without a mutable global facade."""

    return TaskOps(
        run_command=_default_run_command,
        run_semantic_all_pass=_default_run_command,
        publish_bytes=_publish_bytes,
        now=lambda: datetime.now(UTC),
    )


def _timestamp_from_task_id(identifier: str) -> str:
    try:
        compact = identifier.split("-", 2)[1]
        parsed = datetime.strptime(compact, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except (IndexError, ValueError) as exc:
        raise TaskBoundaryError(f"Invalid task_attempt_id: {identifier}") from exc
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise TaskBoundaryError("Task clock must return a timezone-aware datetime")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _require_absent(path: Path, label: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise TaskBoundaryError(f"Could not inspect {label}: {path}: {exc}") from exc
    raise TaskBoundaryError(f"Refusing pre-existing {label}: {path}")


def _expected_scope_ids(
    task: Mapping[str, Any], execution: Mapping[str, Any]
) -> set[str]:
    selector = task["scope_selector"]
    if selector == "reference":
        return {str(execution["reference"]["reference_id"])}
    if selector == "samples":
        return {str(row["sample_id"]) for row in execution["samples"]["rows"]}
    if selector == "partitions":
        cohort = str(execution["analysis"]["cohort_id"])
        return {
            f"{cohort}__{row['partition_id']}"
            for row in execution["partitions"]["rows"]
        }
    if selector == "cohort":
        return {str(execution["analysis"]["cohort_id"])}
    if selector == "analysis":
        return {str(execution["analysis"]["primary_analysis_id"])}
    if selector == "scientific_review":
        analysis = str(execution["analysis"]["primary_analysis_id"])
        return {f"{analysis}.review"}
    raise TaskBoundaryError(f"Unsupported task scope selector: {selector}")


def _admit_output_locations(
    dispatch: TaskDispatch,
    execution: Mapping[str, Any],
) -> None:
    """Admit run-local outputs plus the exact stationary Step 00c sidecars."""

    outside: set[Path] = set()
    for output in dispatch.outputs:
        try:
            _safe_in_run_destination(
                output.path, dispatch.run_root, "native output path"
            )
        except TaskBoundaryError as exc:
            try:
                output.path.relative_to(dispatch.run_root)
            except ValueError:
                outside.add(output.path)
            else:
                raise exc
    if not outside:
        return
    sidecar_owner = "norad.stage.construct_FASTA_sidecars.v1"
    fasta = Path(str(execution["reference"]["fasta"]["path"]))
    try:
        if fasta.resolve(strict=True) != fasta:
            raise TaskBoundaryError(
                f"Step 00c stationary FASTA must be canonical: {fasta}"
            )
    except OSError as exc:
        raise TaskBoundaryError(
            f"Step 00c stationary FASTA is unavailable: {fasta}: {exc}"
        ) from exc
    expected = {
        Path(f"{fasta}.fai"),
        fasta.with_name(f"{fasta.stem}.dict"),
    }
    declared = {item.path for item in dispatch.outputs}
    if dispatch.machine_key != sidecar_owner or declared != expected:
        raise TaskBoundaryError(
            "Only the exact Step 00c FAI/DICT pair may be published outside run_root"
        )
    for path in expected:
        if path.parent.resolve(strict=True) != path.parent:
            raise TaskBoundaryError(
                f"Step 00c sidecar parent must be canonical: {path.parent}"
            )
        if path.parent != fasta.parent:
            raise TaskBoundaryError(
                f"Step 00c sidecar parent does not match stationary FASTA: {path}"
            )


def _admit_identity(
    dispatch: TaskDispatch,
) -> tuple[dict[str, Any], dict[str, Any], str, str, str]:
    profile = orchestration_contracts.load_record(dispatch.profile_path, "profile")
    execution = orchestration_contracts.load_record(
        dispatch.execution_path,
        "execution",
        profile=profile,
    )
    profile_sha256 = orchestration_contracts.canonical_sha256(profile)
    profile_data, _ = _read_bound_file(dispatch.profile_path, "workflow profile")
    if profile_data != orchestration_contracts.canonical_json_bytes(profile):
        raise TaskBoundaryError("Workflow profile must use canonical JSON bytes")
    if execution["profile"]["profile_sha256"] != profile_sha256:
        raise TaskBoundaryError("Execution does not bind the admitted profile")
    tasks = [
        task
        for task in profile["owner_tasks"]
        if task["machine_key"] == dispatch.machine_key
    ]
    if len(tasks) != 1:
        raise TaskBoundaryError(
            f"Dispatch machine_key is not one exact profile owner: {dispatch.machine_key}"
        )
    task = tasks[0]
    if dispatch.machine_key not in profile["required_owner_keys"]:
        raise TaskBoundaryError(
            f"Dispatch owner is excluded from automatic execution: {dispatch.machine_key}"
        )
    if task["scope_type"] != dispatch.scope["scope_type"]:
        raise TaskBoundaryError("Dispatch scope_type does not match its profile owner")
    if dispatch.scope["scope_id"] not in _expected_scope_ids(task, execution):
        raise TaskBoundaryError("Dispatch scope_id is not selected by the execution")
    _admit_output_locations(dispatch, execution)

    execution_data, _ = _read_bound_file(dispatch.execution_path, "execution contract")
    canonical_execution = orchestration_contracts.canonical_json_bytes(execution)
    if execution_data != canonical_execution:
        raise TaskBoundaryError("Execution contract must use canonical JSON bytes")
    return (
        profile,
        execution,
        hashlib.sha256(execution_data).hexdigest(),
        profile_sha256,
        str(task["step_id"]),
    )


def _semantic_argv(dispatch: TaskDispatch, step_id: str) -> tuple[str, ...]:
    return (
        sys.executable,
        "-I",
        "-m",
        "norad",
        "validate",
        "all-pass",
        "--report",
        str(dispatch.validation_report_path),
        "--step-id",
        step_id,
        "--scope-id",
        dispatch.scope["scope_id"],
    )


def _bound_file_matches(record: Mapping[str, Any], label: str) -> None:
    declaration = FileDeclaration(
        role=_safe_id(record.get("role"), f"{label}.role"),
        path=_absolute_path(record.get("path"), f"{label}.path"),
    )
    observed = _snapshot(declaration)
    if observed != dict(record):
        raise TaskBoundaryError(f"{label} content binding no longer matches")


def _referenced_record(
    reference: Mapping[str, Any],
    *,
    run_root: Path,
    label: str,
) -> tuple[Path, dict[str, Any]]:
    raw_path = reference.get("path")
    if not isinstance(raw_path, str):
        raise TaskBoundaryError(f"{label}.path must be a relative contract path")
    path = run_root / raw_path
    _safe_in_run_destination(path, run_root, label)
    record, data = _load_bound_json(path, label)
    if hashlib.sha256(data).hexdigest() != reference.get("sha256"):
        raise TaskBoundaryError(f"{label} SHA-256 no longer matches")
    return path, record


def _verify_reference(
    reference: Mapping[str, Any],
    *,
    run_root: Path,
    label: str,
) -> Path:
    raw_path = reference.get("path")
    if not isinstance(raw_path, str):
        raise TaskBoundaryError(f"{label}.path must be a relative contract path")
    path = run_root / raw_path
    _safe_in_run_destination(path, run_root, label)
    data, _ = _read_bound_file(path, label)
    if hashlib.sha256(data).hexdigest() != reference.get("sha256"):
        raise TaskBoundaryError(f"{label} SHA-256 no longer matches")
    return path


def validate_verified_task(
    path: Path,
    *,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    machine_key: str,
    scope: Mapping[str, str],
) -> dict[str, Any]:
    """Fail closed unless an existing verified task remains exactly reusable.

    This read-only check is intended for workflow graph admission.  It trusts
    neither Snakemake metadata nor mere marker presence.
    """

    canonical_root = _absolute_path(str(run_root), "run_root")
    if canonical_root.resolve(strict=True) != canonical_root:
        raise TaskBoundaryError("run_root must already be canonical")
    verified_path = _absolute_path(str(path), "verified task path")
    _safe_in_run_destination(verified_path, canonical_root, "verified task path")
    orchestration_contracts.validate_record("profile", profile)
    orchestration_contracts.validate_record("execution", execution, profile=profile)
    record, _ = _load_bound_json(verified_path, "verified task record")
    orchestration_contracts.validate_record("verified-task", record)

    expected_scope = {
        "scope_type": _safe_id(scope.get("scope_type"), "scope.scope_type"),
        "scope_id": _safe_id(scope.get("scope_id"), "scope.scope_id"),
    }
    profile_tasks = [
        item for item in profile["owner_tasks"] if item["machine_key"] == machine_key
    ]
    if len(profile_tasks) != 1 or machine_key not in profile["required_owner_keys"]:
        raise TaskBoundaryError("Verified task owner is not one required profile owner")
    owner = profile_tasks[0]
    if owner["scope_type"] != expected_scope["scope_type"]:
        raise TaskBoundaryError("Verified task scope_type does not match profile owner")
    if expected_scope["scope_id"] not in _expected_scope_ids(owner, execution):
        raise TaskBoundaryError("Verified task scope_id is not selected by execution")

    execution_sha256 = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(execution)
    ).hexdigest()
    identity = {
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": orchestration_contracts.canonical_sha256(profile),
        "machine_key": machine_key,
        "scope": expected_scope,
    }
    for field, expected in identity.items():
        if record[field] != expected:
            raise TaskBoundaryError(f"Verified task {field} does not match")

    roles: set[str] = set()
    paths: set[str] = set()
    for group in ("inputs", "outputs"):
        for index, bound in enumerate(record[group]):
            role = str(bound["role"])
            file_path = str(bound["path"])
            if role in roles or file_path in paths:
                raise TaskBoundaryError(
                    f"Verified task repeats a bound role or path in {group}"
                )
            roles.add(role)
            paths.add(file_path)
            _bound_file_matches(bound, f"verified {group}[{index}]")

    attempt_path, attempt = _referenced_record(
        record["task_attempt_record"],
        run_root=canonical_root,
        label="task-attempt record",
    )
    orchestration_contracts.validate_record("task-attempt", attempt)
    for field in (
        "run_id",
        "execution_contract_sha256",
        "profile_sha256",
        "workflow_attempt_id",
        "task_attempt_id",
        "machine_key",
        "scope",
        "owner_run_token",
    ):
        if attempt[field] != record[field]:
            raise TaskBoundaryError(
                f"Task attempt and verified task disagree on {field}"
            )
    if attempt["status"] != "succeeded" or attempt["failure_message"] is not None:
        raise TaskBoundaryError("Referenced task attempt is not successful")
    if attempt["producer"] != record["commands"]["producer"]:
        raise TaskBoundaryError("Producer command differs from task attempt")
    if attempt["validator"] != record["commands"]["validator"]:
        raise TaskBoundaryError("Validator command differs from task attempt")
    if attempt["semantic_all_pass"] != record["commands"]["semantic_all_pass"]:
        raise TaskBoundaryError("Semantic command differs from task attempt")

    report_reference = record["validation_report"]
    report_path = canonical_root / str(report_reference["path"])
    _safe_in_run_destination(report_path, canonical_root, "validation report")
    report_data, _ = _read_bound_file(report_path, "validation report")
    if hashlib.sha256(report_data).hexdigest() != report_reference["sha256"]:
        raise TaskBoundaryError("Verified validation report SHA-256 no longer matches")
    if attempt["validation_report"] != {
        "path": report_reference["path"],
        "sha256": report_reference["sha256"],
    }:
        raise TaskBoundaryError("Task attempt and verified validation report disagree")
    from norad.orchestration.local_pilot.all_pass import (  # noqa: PLC0415
        require_all_pass,
    )

    evidence = require_all_pass(
        report_path,
        step_id=str(owner["step_id"]),
        scope_id=expected_scope["scope_id"],
    )
    if evidence.report_sha256 != report_reference["sha256"]:
        raise TaskBoundaryError("Semantic all-pass observed a different report")

    native = record["native_receipt"]
    if native is not None:
        _verify_reference(
            native,
            run_root=canonical_root,
            label="native receipt",
        )
    if not attempt_path.is_file():
        raise TaskBoundaryError("Referenced task attempt disappeared")
    return record


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _publish_attempt(
    dispatch: TaskDispatch,
    *,
    ops: TaskOps,
    execution: Mapping[str, Any],
    execution_sha256: str,
    profile_sha256: str,
    started_at: str,
    producer: CommandResult | None,
    validator: CommandResult | None,
    semantic: CommandResult | None,
    stable_inputs_rechecked: bool,
    failure_message: str | None,
    stdout: bytes,
    stderr: bytes,
) -> tuple[dict[str, Any], bytes]:
    ops.publish_bytes(dispatch.stdout_path, stdout)
    ops.publish_bytes(dispatch.stderr_path, stderr)
    report_reference = None
    try:
        report_reference = _record_reference(
            dispatch.validation_report_path, dispatch.run_root
        )
    except TaskBoundaryError:
        if failure_message is None:
            raise
    status = "succeeded" if failure_message is None else "failed"
    attempt = {
        "schema_version": "norad.task-attempt.v1",
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
        "workflow_attempt_id": dispatch.workflow_attempt_id,
        "task_attempt_id": dispatch.task_attempt_id,
        "machine_key": dispatch.machine_key,
        "scope": dict(dispatch.scope),
        "owner_run_token": dispatch.owner_run_token,
        "status": status,
        "started_at": started_at,
        "finished_at": _utc_timestamp(ops.now()),
        "producer": None if producer is None else producer.record,
        "validator": None if validator is None else validator.record,
        "semantic_all_pass": None if semantic is None else semantic.record,
        "stable_inputs_rechecked": stable_inputs_rechecked,
        "validation_report": report_reference,
        "stdout_path": _relative(dispatch.stdout_path, dispatch.run_root),
        "stderr_path": _relative(dispatch.stderr_path, dispatch.run_root),
        "failure_message": failure_message,
    }
    orchestration_contracts.validate_record("task-attempt", attempt)
    attempt_bytes = orchestration_contracts.canonical_json_bytes(attempt)
    ops.publish_bytes(dispatch.task_attempt_path, attempt_bytes)
    return attempt, attempt_bytes


def run_task(
    dispatch: TaskDispatch,
    *,
    backend: TaskBackend,
    ops: TaskOps,
) -> TaskOutcome:
    """Execute and prove one admitted owner scope using explicit dependencies."""

    if backend != dispatch.backend:
        raise TaskBoundaryError("Task backend does not match the admitted dispatch")
    started_at = _timestamp_from_task_id(dispatch.task_attempt_id)
    profile: dict[str, Any] = {}
    execution: dict[str, Any] = {}
    execution_sha256 = "0" * 64
    profile_sha256 = "0" * 64
    step_id = "unknown"
    producer: CommandResult | None = None
    validator: CommandResult | None = None
    semantic: CommandResult | None = None
    stable_inputs_rechecked = False
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    failure: TaskBoundaryError | None = None

    protected = (
        dispatch.task_attempt_path,
        dispatch.verified_task_path,
        dispatch.stdout_path,
        dispatch.stderr_path,
    )
    for path, label in zip(
        protected,
        ("task-attempt record", "verified-task record", "stdout log", "stderr log"),
        strict=True,
    ):
        _require_absent(path, label)

    try:
        profile, execution, execution_sha256, profile_sha256, step_id = _admit_identity(
            dispatch
        )
        initial_inputs = tuple(
            _snapshot(item)
            for item in (
                FileDeclaration("task_dispatch", dispatch.path),
                FileDeclaration("execution_contract", dispatch.execution_path),
                FileDeclaration("workflow_profile", dispatch.profile_path),
                *dispatch.inputs,
            )
        )
        if len({item["role"] for item in initial_inputs}) != len(initial_inputs):
            raise TaskBoundaryError("Input roles collide with reserved contract roles")

        native_destinations = [item.path for item in dispatch.outputs]
        native_destinations.append(dispatch.validation_report_path)
        if dispatch.native_receipt_path is not None:
            native_destinations.append(dispatch.native_receipt_path)
        for path in native_destinations:
            _require_absent(path, "native task destination")

        producer = ops.run_command(backend.producer_argv, dispatch.run_root)
        stdout_parts.append(producer.stdout)
        stderr_parts.append(producer.stderr)
        if producer.exit_code != 0:
            raise TaskBoundaryError(
                f"Producer command exited with status {producer.exit_code}"
            )
        producer_outputs = tuple(_snapshot(output) for output in dispatch.outputs)
        producer_native_receipt = (
            None
            if dispatch.native_receipt_path is None
            else _record_reference(dispatch.native_receipt_path, dispatch.run_root)
        )

        validator = ops.run_command(backend.validator_argv, dispatch.run_root)
        stdout_parts.append(validator.stdout)
        stderr_parts.append(validator.stderr)
        if validator.exit_code != 0:
            raise TaskBoundaryError(
                f"Validator command exited with status {validator.exit_code}"
            )

        validation_before_all_pass = _record_reference(
            dispatch.validation_report_path, dispatch.run_root
        )
        semantic = ops.run_semantic_all_pass(
            _semantic_argv(dispatch, step_id), dispatch.run_root
        )
        stdout_parts.append(semantic.stdout)
        stderr_parts.append(semantic.stderr)
        if semantic.exit_code != 0:
            raise TaskBoundaryError(
                f"Semantic all-pass command exited with status {semantic.exit_code}"
            )

        final_inputs = tuple(
            _snapshot(item)
            for item in (
                FileDeclaration("task_dispatch", dispatch.path),
                FileDeclaration("execution_contract", dispatch.execution_path),
                FileDeclaration("workflow_profile", dispatch.profile_path),
                *dispatch.inputs,
            )
        )
        if final_inputs != initial_inputs:
            raise TaskBoundaryError("A stable task input changed during execution")
        stable_inputs_rechecked = True
        outputs = tuple(_snapshot(item) for item in dispatch.outputs)
        if outputs != producer_outputs:
            raise TaskBoundaryError(
                "A producer output changed during validation or semantic gating"
            )
        native_receipt = (
            None
            if dispatch.native_receipt_path is None
            else _record_reference(dispatch.native_receipt_path, dispatch.run_root)
        )
        if native_receipt != producer_native_receipt:
            raise TaskBoundaryError(
                "The native receipt changed during validation or semantic gating"
            )
        validation_reference = _record_reference(
            dispatch.validation_report_path, dispatch.run_root
        )
        if validation_reference != validation_before_all_pass:
            raise TaskBoundaryError(
                "The validation report changed during semantic all-pass gating"
            )
    except TaskBoundaryError as exc:
        failure = exc

    if failure is not None:
        message = str(failure).strip() or type(failure).__name__
        if not execution:
            raise TaskBoundaryError(message) from failure
        _publish_attempt(
            dispatch,
            ops=ops,
            execution=execution,
            execution_sha256=execution_sha256,
            profile_sha256=profile_sha256,
            started_at=started_at,
            producer=producer,
            validator=validator,
            semantic=semantic,
            stable_inputs_rechecked=stable_inputs_rechecked,
            failure_message=message,
            stdout=b"".join(stdout_parts),
            stderr=b"".join(stderr_parts),
        )
        raise TaskBoundaryError(message) from failure

    attempt, attempt_bytes = _publish_attempt(
        dispatch,
        ops=ops,
        execution=execution,
        execution_sha256=execution_sha256,
        profile_sha256=profile_sha256,
        started_at=started_at,
        producer=producer,
        validator=validator,
        semantic=semantic,
        stable_inputs_rechecked=True,
        failure_message=None,
        stdout=b"".join(stdout_parts),
        stderr=b"".join(stderr_parts),
    )
    assert producer is not None and validator is not None and semantic is not None
    task_attempt_reference = {
        "path": _relative(dispatch.task_attempt_path, dispatch.run_root),
        "sha256": hashlib.sha256(attempt_bytes).hexdigest(),
    }
    verified = {
        "schema_version": "norad.verified-task.v1",
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
        "workflow_attempt_id": dispatch.workflow_attempt_id,
        "task_attempt_id": dispatch.task_attempt_id,
        "task_attempt_record": task_attempt_reference,
        "machine_key": dispatch.machine_key,
        "scope": dict(dispatch.scope),
        "owner_run_token": dispatch.owner_run_token,
        "commands": {
            "producer": producer.record,
            "validator": validator.record,
            "semantic_all_pass": semantic.record,
        },
        "inputs": list(final_inputs),
        "outputs": list(outputs),
        "native_receipt": native_receipt,
        "validation_report": {**validation_reference, "all_pass": True},
        "stable_inputs_rechecked": True,
        "all_pass": True,
        "created_at": attempt["finished_at"],
    }
    orchestration_contracts.validate_record("verified-task", verified)
    ops.publish_bytes(
        dispatch.verified_task_path,
        orchestration_contracts.canonical_json_bytes(verified),
    )
    return TaskOutcome(
        task_attempt_path=dispatch.task_attempt_path,
        verified_task_path=dispatch.verified_task_path,
        task_attempt=attempt,
        verified_task=verified,
    )


def execute_dispatch(path: Path, *, ops: TaskOps | None = None) -> TaskOutcome:
    """Load and execute one dispatch through its exact admitted backend."""

    dispatch = load_dispatch(path)
    selected_ops = default_task_ops() if ops is None else ops
    return run_task(dispatch, backend=dispatch.backend, ops=selected_ops)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Execute one closed NORAD local-pilot owner dispatch and publish a "
        "verified-task record only after producer, validator, and semantic "
        "all-pass success. This is an internal workflow boundary, not a public "
        "run/resume/inspect interface."
    )
    parser.add_argument(
        "--dispatch",
        required=True,
        type=Path,
        help="Absolute path to one materialized norad.local-task-dispatch.v1 JSON file.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    arguments = parser.parse_args(argv)
    try:
        outcome = execute_dispatch(arguments.dispatch)
    except (
        OSError,
        orchestration_contracts.ContractValidationError,
        TaskBoundaryError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Task attempt: {outcome.task_attempt_path}")
    print(f"Verified task: {outcome.verified_task_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = (
    "DISPATCH_SCHEMA_VERSION",
    "CommandResult",
    "FileDeclaration",
    "TaskBackend",
    "TaskBoundaryError",
    "TaskDispatch",
    "TaskOps",
    "TaskOutcome",
    "configure_parser",
    "default_task_ops",
    "execute_dispatch",
    "load_dispatch",
    "main",
    "run_task",
    "validate_verified_task",
)
