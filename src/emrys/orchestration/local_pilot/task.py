"""Execute one closed local-pilot functional-owner task.

This module is the job boundary used by the fixed Snakemake workflow.  It is
deliberately not registered as a top-level ``emrys`` command: the lifecycle
adapter remains a later campaign phase.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import os
import re
import selectors
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from operator import attrgetter
from pathlib import Path
from typing import Any

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    RUN_BINDING_SCHEMA_VERSION,
)
from emrys.libraries.exclusive_publication import publish_exclusive
from emrys.libraries.process_environment import sanitized_subprocess_environment
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    attest_source_checkout as _attest_source_checkout,
    controlled_python_argv,
    is_controlled_python_argv,
    require_controlled_python_runtime,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    read_bytes_with_identity,
    sha256_with_identity,
)
from emrys.orchestration.local_pilot._inspection_admission import (
    InspectionError,
    SuccessorRunAuthority,
    admit_attempt_run_lock,
    admit_canonical_record,
    admit_execution_path,
    expected_tasks,
)

DISPATCH_SCHEMA_VERSION = "emrys.local-task-dispatch.v1"
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
        "task_start_path",
        "task_attempt_path",
        "verified_task_path",
        "stdout_path",
        "stderr_path",
    }
)
_DECLARATION_FIELDS = frozenset({"role", "path"})
_BOUND_DECLARATION_FIELDS = frozenset({"role", "path", "size_bytes", "sha256"})
_SCOPE_FIELDS = frozenset({"scope_type", "scope_id"})
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_STREAM_CHUNK_BYTES = 1024 * 1024
_STEP07_INPUT_IDENTITY_ENV = "EMRYS_STEP07_INPUT_IDENTITY_SHA256"
_STEP07_MACHINE_KEY = "emrys.stage.generate_partitioned_cohort_mpileup_VCFs.v1"


class TaskBoundaryError(RuntimeError):
    """Raised when a task cannot prove one verified owner result."""


@dataclass(frozen=True, slots=True)
class FileDeclaration:
    """One role-bearing file path admitted from the dispatch."""

    role: str
    path: Path
    expected_binding: tuple[int, str] | None = None


_FileIdentity = tuple[int, int, int, int, int]
_file_identity = attrgetter("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")


@dataclass(frozen=True, slots=True)
class _BoundFileSnapshot:
    """One content record plus the exact regular-file identity that supplied it."""

    record: dict[str, Any]
    identity: _FileIdentity


@dataclass(frozen=True, slots=True)
class TaskBackend:
    """Exact public producer and validator commands for one owner invocation."""

    producer_argv: tuple[str, ...]
    validator_argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskDispatch:
    """Closed materialized job description consumed by one task invocation."""

    path: Path
    dispatch_sha256: str
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
    task_start_path: Path
    task_attempt_path: Path
    verified_task_path: Path
    stdout_path: Path
    stderr_path: Path


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Exit evidence for one delegated public command."""

    argv: tuple[str, ...]
    exit_code: int

    @property
    def record(self) -> dict[str, Any]:
        return {"argv": list(self.argv), "exit_code": self.exit_code}


CommandRunner = Callable[
    [tuple[str, ...], Path, Mapping[str, str], int, int],
    CommandResult,
]
BytesPublisher = Callable[[Path, bytes], None]
Clock = Callable[[], datetime]
SourceCheckoutAttester = Callable[..., Any]
PathAccess = Callable[[Path, int], bool]


@dataclass(frozen=True, slots=True)
class TaskOps:
    """Explicit effect boundary used by task execution and fault tests."""

    run_command: CommandRunner
    run_semantic_all_pass: CommandRunner
    publish_bytes: BytesPublisher
    now: Clock
    attest_source_checkout: SourceCheckoutAttester = _attest_source_checkout
    path_access: PathAccess = os.access


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
    command = tuple(value)
    if command[0] == sys.executable and not is_controlled_python_argv(
        command,
        python_executable=sys.executable,
    ):
        raise TaskBoundaryError(f"{label} must use the controlled Python launch prefix")
    return command


def _declarations(
    value: Any,
    label: str,
    *,
    allow_binding: bool = False,
) -> tuple[FileDeclaration, ...]:
    if not isinstance(value, list) or not value:
        raise TaskBoundaryError(f"{label} must be a nonempty declaration array")
    declarations: list[FileDeclaration] = []
    roles: set[str] = set()
    paths: set[Path] = set()
    for index, raw in enumerate(value):
        observed = frozenset(raw) if isinstance(raw, Mapping) else frozenset()
        bound = allow_binding and observed == _BOUND_DECLARATION_FIELDS
        fields = _BOUND_DECLARATION_FIELDS if bound else _DECLARATION_FIELDS
        item = _closed_object(
            raw,
            fields=fields,
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
        expected_size = item.get("size_bytes")
        expected_sha256 = item.get("sha256")
        if bound and (
            isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size < 0
        ):
            raise TaskBoundaryError(
                f"{label}[{index}].size_bytes must be a nonnegative integer"
            )
        if bound and (
            not isinstance(expected_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
        ):
            raise TaskBoundaryError(f"{label}[{index}].sha256 must be 64 lowercase hex")
        declarations.append(
            FileDeclaration(
                role=role,
                path=path,
                expected_binding=(expected_size, expected_sha256) if bound else None,
            )
        )
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


def load_dispatch(path: Path, *, expected_sha256: str) -> TaskDispatch:
    """Load one strict, closed dispatch without performing task mutations."""

    dispatch_path = _absolute_path(str(path), "dispatch path")
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise TaskBoundaryError("expected dispatch SHA-256 must be 64 lowercase hex")
    dispatch_data, _dispatch_state = _read_bound_file(dispatch_path, "task dispatch")
    observed_sha256 = hashlib.sha256(dispatch_data).hexdigest()
    if observed_sha256 != expected_sha256:
        raise TaskBoundaryError("Task dispatch SHA-256 differs from workflow plan")
    try:
        raw = orchestration_contracts.load_json_object_bytes(
            dispatch_data, f"task dispatch {dispatch_path}"
        )
    except orchestration_contracts.ContractValidationError as exc:
        raise TaskBoundaryError(str(exc)) from exc
    if orchestration_contracts.canonical_json_bytes(raw) != dispatch_data:
        raise TaskBoundaryError(
            f"task dispatch must use canonical JSON bytes: {dispatch_path}"
        )
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
        dispatch_sha256=expected_sha256,
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
        inputs=_declarations(record["inputs"], "inputs", allow_binding=True),
        outputs=_declarations(record["outputs"], "outputs"),
        validation_report_path=_absolute_path(
            record["validation_report_path"], "validation_report_path"
        ),
        native_receipt_path=native_receipt,
        task_start_path=_absolute_path(record["task_start_path"], "task_start_path"),
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
        result.task_start_path,
        result.task_attempt_path,
        result.verified_task_path,
        result.stdout_path,
        result.stderr_path,
    }
    if result.native_receipt_path is not None:
        mutable_paths.add(result.native_receipt_path)
    expected_mutable_count = (
        len(result.outputs) + 6 + (result.native_receipt_path is not None)
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
    expected_task_start = (
        result.run_root
        / "state"
        / "task-starts"
        / result.machine_key
        / f"{result.scope['scope_id']}.json"
    )
    if result.task_start_path != expected_task_start:
        raise TaskBoundaryError(
            "task_start_path does not match the exact owner/scope ledger path"
        )
    expected_task_root = (
        result.run_root
        / "attempts"
        / result.workflow_attempt_id
        / "tasks"
        / result.machine_key
        / result.scope["scope_id"]
    )
    expected_task_paths = {
        "task_attempt_path": expected_task_root / "task-attempt.json",
        "stdout_path": expected_task_root / "stdout.log",
        "stderr_path": expected_task_root / "stderr.log",
    }
    for field, expected in expected_task_paths.items():
        if getattr(result, field) != expected:
            raise TaskBoundaryError(
                f"{field} does not match the exact workflow-attempt task path"
            )
    return result


def _require_canonical_bound_path(path: Path, label: str) -> None:
    if not hasattr(os, "O_NOFOLLOW"):
        raise TaskBoundaryError("This platform lacks required O_NOFOLLOW admission")
    try:
        if path.resolve(strict=True) != path:
            raise TaskBoundaryError(f"{label} path is not canonical: {path}")
    except OSError as exc:
        raise TaskBoundaryError(f"Could not resolve {label}: {path}: {exc}") from exc


def _read_bound_file(path: Path, label: str) -> tuple[bytes, os.stat_result]:
    _require_canonical_bound_path(path, label)
    try:
        return read_bytes_with_identity(path, label, nonempty=False)
    except ValidationError as exc:
        raise TaskBoundaryError(str(exc)) from exc


def _read_bound_record(path: Path, root: Path, label: str) -> bytes:
    _safe_in_run_destination(path, root, label)
    return _read_bound_file(path, label)[0]


_admit_record = partial(
    admit_canonical_record,
    read_bytes=_read_bound_record,
    error_type=TaskBoundaryError,
)
_admit_execution = partial(
    admit_execution_path,
    read_bytes=_read_bound_record,
    error_type=TaskBoundaryError,
)


def _hash_bound_file(path: Path, label: str) -> tuple[str, os.stat_result]:
    _require_canonical_bound_path(path, label)
    try:
        return sha256_with_identity(path, label, nonempty=False)
    except ValidationError as exc:
        raise TaskBoundaryError(str(exc)) from exc


def _bound_snapshot(declaration: FileDeclaration) -> _BoundFileSnapshot:
    digest, state = _hash_bound_file(declaration.path, declaration.role)
    record = {
        "role": declaration.role,
        "path": str(declaration.path),
        "size_bytes": state.st_size,
        "sha256": digest,
    }
    if declaration.expected_binding not in (None, (state.st_size, digest)):
        raise TaskBoundaryError(
            f"Task input differs from its processing-source binding: {declaration.path}"
        )
    return _BoundFileSnapshot(
        record=record,
        identity=_file_identity(state),
    )


def _snapshot(declaration: FileDeclaration) -> dict[str, Any]:
    return _bound_snapshot(declaration).record


def _record_reference(
    path: Path,
    run_root: Path,
    *,
    expected_identity: _FileIdentity | None = None,
    label: str = "record reference",
) -> dict[str, str]:
    digest, state = _hash_bound_file(path, label)
    if expected_identity is not None and _file_identity(state) != expected_identity:
        raise TaskBoundaryError(
            f"{label} path no longer matches its synchronized descriptor"
        )
    return {
        "path": path.relative_to(run_root).as_posix(),
        "sha256": digest,
    }


def _write_descriptor(descriptor: int, data: bytes, label: str) -> None:
    view = memoryview(data)
    try:
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError(f"short write returned {written}")
            view = view[written:]
    except OSError as exc:
        raise TaskBoundaryError(f"Could not write {label}: {exc}") from exc


def _open_task_log(path: Path, label: str) -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        raise TaskBoundaryError("This platform lacks required O_NOFOLLOW publication")
    parent = path.parent
    try:
        parent_state = parent.lstat()
    except OSError as exc:
        raise TaskBoundaryError(
            f"Could not inspect {label} parent: {parent}: {exc}"
        ) from exc
    if stat.S_ISLNK(parent_state.st_mode) or not stat.S_ISDIR(parent_state.st_mode):
        raise TaskBoundaryError(f"{label} parent must be a real directory: {parent}")
    try:
        if parent.resolve(strict=True) != parent:
            raise TaskBoundaryError(f"{label} parent must be canonical: {parent}")
    except OSError as exc:
        raise TaskBoundaryError(
            f"Could not resolve {label} parent: {parent}: {exc}"
        ) from exc

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise TaskBoundaryError(
            f"Refusing to replace existing {label}: {path}"
        ) from exc
    except OSError as exc:
        raise TaskBoundaryError(f"Could not create {label}: {path}: {exc}") from exc
    try:
        descriptor_state = os.fstat(descriptor)
        path_state = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(descriptor_state.st_mode) or not stat.S_ISREG(
            path_state.st_mode
        ):
            raise TaskBoundaryError(f"{label} is not a regular file: {path}")
        if (descriptor_state.st_dev, descriptor_state.st_ino) != (
            path_state.st_dev,
            path_state.st_ino,
        ):
            raise TaskBoundaryError(f"{label} path changed during creation: {path}")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _sync_task_log_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            state = os.fstat(descriptor)
            if not stat.S_ISDIR(state.st_mode):
                raise TaskBoundaryError(f"Task log parent is not a directory: {path}")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except TaskBoundaryError:
        raise
    except OSError as exc:
        raise TaskBoundaryError(
            f"Could not synchronize task log directory: {path}: {exc}"
        ) from exc


@dataclass(slots=True)
class _TaskStreamCapture:
    """One protected pair of task-owned opaque command streams."""

    stdout_path: Path
    stderr_path: Path
    run_root: Path
    _stdout_descriptor: int = -1
    _stderr_descriptor: int = -1
    _opened: bool = False
    _closed: bool = False
    _open_failure: TaskBoundaryError | None = None
    _final_identities: tuple[_FileIdentity, _FileIdentity] | None = None
    _references: tuple[dict[str, str], dict[str, str]] | None = None

    def open(self) -> tuple[int, int]:
        if self._opened:
            if self._closed:
                raise TaskBoundaryError("Task command streams are already closed")
            return self._stdout_descriptor, self._stderr_descriptor
        self._opened = True
        try:
            for field, path, label in (
                ("_stdout_descriptor", self.stdout_path, "task stdout log"),
                ("_stderr_descriptor", self.stderr_path, "task stderr log"),
            ):
                setattr(self, field, _open_task_log(path, label))
                _sync_task_log_directory(path.parent)
        except BaseException as exc:
            if isinstance(exc, TaskBoundaryError):
                self._open_failure = exc
            self.preserve_incomplete()
            raise
        return self._stdout_descriptor, self._stderr_descriptor

    def _synchronize_and_close(
        self, *, best_effort: bool
    ) -> tuple[_FileIdentity, _FileIdentity] | None:
        if not self._opened or self._closed:
            return self._final_identities
        failures: list[str] = []
        identities: dict[str, _FileIdentity] = {}
        for label, descriptor in (
            ("stdout", self._stdout_descriptor),
            ("stderr", self._stderr_descriptor),
        ):
            if descriptor < 0:
                continue
            try:
                os.fsync(descriptor)
                identities[label] = _file_identity(os.fstat(descriptor))
            except OSError as exc:
                failures.append(f"{label} fsync/fstat: {exc}")
        for label, field in (
            ("stdout", "_stdout_descriptor"),
            ("stderr", "_stderr_descriptor"),
        ):
            descriptor = getattr(self, field)
            if descriptor < 0:
                continue
            try:
                os.close(descriptor)
            except OSError as exc:
                failures.append(f"{label} close: {exc}")
            finally:
                setattr(self, field, -1)
        self._closed = True
        if "stdout" in identities and "stderr" in identities:
            self._final_identities = (identities["stdout"], identities["stderr"])
        if failures and not best_effort:
            raise TaskBoundaryError(
                "Could not synchronize and close task command streams: "
                + "; ".join(failures)
            )
        return self._final_identities

    def preserve_incomplete(self) -> None:
        """Best-effort durability for an unexpected interruption or capture fault."""

        self._synchronize_and_close(best_effort=True)

    def finalize(self) -> tuple[dict[str, str], dict[str, str]]:
        if self._open_failure is not None:
            raise TaskBoundaryError(str(self._open_failure)) from self._open_failure
        if self._references is not None:
            return self._references
        if not self._opened:
            self.open()
        identities = self._synchronize_and_close(best_effort=False)
        if identities is None:
            raise TaskBoundaryError("Task command streams have no final identity")
        stdout_reference = _record_reference(
            self.stdout_path,
            self.run_root,
            expected_identity=identities[0],
            label="task stdout log",
        )
        stderr_reference = _record_reference(
            self.stderr_path,
            self.run_root,
            expected_identity=identities[1],
            label="task stderr log",
        )
        self._references = (stdout_reference, stderr_reference)
        return self._references

    def revalidate_after_attempt_publication(self) -> None:
        if self._references is None or self._final_identities is None:
            raise TaskBoundaryError("Task command streams were not finalized")
        for label, path, reference, identity in zip(
            ("stdout", "stderr"),
            (self.stdout_path, self.stderr_path),
            self._references,
            self._final_identities,
            strict=True,
        ):
            try:
                current = _record_reference(
                    path,
                    self.run_root,
                    expected_identity=identity,
                    label=f"task {label} log",
                )
            except TaskBoundaryError as exc:
                raise TaskBoundaryError(
                    f"Task {label} changed during attempt publication"
                ) from exc
            if current != reference:
                raise TaskBoundaryError(
                    f"Task {label} changed during attempt publication"
                )


def _default_run_command(
    argv: tuple[str, ...],
    cwd: Path,
    environment: Mapping[str, str] | None = None,
    stdout_descriptor: int = -1,
    stderr_descriptor: int = -1,
) -> CommandResult:
    if stdout_descriptor < 0 or stderr_descriptor < 0:
        raise TaskBoundaryError(
            "Task command execution requires both stream descriptors"
        )
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=sanitized_subprocess_environment(environment),
        )
    except OSError as exc:
        message = f"Could not execute {argv[0]}: {exc}\n".encode(
            "utf-8", errors="backslashreplace"
        )
        exit_code = 127 if exc.errno == errno.ENOENT else 126
        _write_descriptor(stderr_descriptor, message, "task stderr log")
        return CommandResult(argv, exit_code)
    selector: selectors.BaseSelector | None = None
    try:
        if process.stdout is None or process.stderr is None:
            raise TaskBoundaryError("Task command did not expose both captured streams")
        selector = selectors.DefaultSelector()
        selector.register(
            process.stdout,
            selectors.EVENT_READ,
            (stdout_descriptor, "task stdout log"),
        )
        selector.register(
            process.stderr,
            selectors.EVENT_READ,
            (stderr_descriptor, "task stderr log"),
        )
        while selector.get_map():
            try:
                ready = selector.select()
            except OSError as exc:
                raise TaskBoundaryError(
                    f"Could not wait for task command streams: {exc}"
                ) from exc
            for key, _events in ready:
                destination, label = key.data
                try:
                    chunk = os.read(key.fd, _STREAM_CHUNK_BYTES)
                except OSError as exc:
                    raise TaskBoundaryError(f"Could not read {label}: {exc}") from exc
                if chunk:
                    _write_descriptor(destination, chunk, label)
                else:
                    selector.unregister(key.fileobj)
        return_code = process.wait()
    except BaseException:
        try:
            process.kill()
        finally:
            process.wait()
        raise
    finally:
        try:
            if selector is not None:
                selector.close()
        finally:
            try:
                if process.stdout is not None:
                    process.stdout.close()
            finally:
                if process.stderr is not None:
                    process.stderr.close()
    exit_code = return_code if 0 <= return_code <= 255 else 128
    return CommandResult(argv, exit_code)


def _publish_bytes(path: Path, data: bytes) -> None:
    """Durably publish bytes at an absent final path without replacement."""
    publish_exclusive(path, data, TaskBoundaryError)


def default_task_ops() -> TaskOps:
    """Construct the production effect boundary without a mutable global facade."""

    return TaskOps(
        run_command=_default_run_command,
        run_semantic_all_pass=_default_run_command,
        publish_bytes=_publish_bytes,
        now=lambda: datetime.now(UTC),
        attest_source_checkout=_attest_source_checkout,
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


def _require_real_directory(path: Path, label: str) -> None:
    try:
        state = path.lstat()
    except OSError as exc:
        raise TaskBoundaryError(f"Could not inspect {label}: {path}: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
        raise TaskBoundaryError(f"{label} is not a real directory: {path}")
    try:
        if path.resolve(strict=True) != path:
            raise TaskBoundaryError(f"{label} is not canonical: {path}")
    except OSError as exc:
        raise TaskBoundaryError(f"Could not resolve {label}: {path}: {exc}") from exc


def _sync_directory(path: Path, label: str) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise TaskBoundaryError(
            f"Could not synchronize {label}: {path}: {exc}"
        ) from exc


def _materialize_task_scope(dispatch: TaskDispatch) -> None:
    """Create only this attempt's exact task evidence directory."""

    attempt_root = dispatch.run_root / "attempts" / dispatch.workflow_attempt_id
    _require_real_directory(attempt_root, "workflow-attempt directory")
    parents = (
        (attempt_root / "tasks", "workflow-attempt tasks directory"),
        (
            attempt_root / "tasks" / dispatch.machine_key,
            "workflow-attempt owner directory",
        ),
    )
    for path, label in parents:
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            _require_real_directory(path, label)
        except OSError as exc:
            raise TaskBoundaryError(f"Could not create {label}: {path}: {exc}") from exc
        else:
            _sync_directory(path, label)
            _sync_directory(path.parent, f"{label} parent")

    scope_root = parents[-1][0] / dispatch.scope["scope_id"]
    try:
        scope_root.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise TaskBoundaryError(
            f"Refusing pre-existing workflow-attempt task scope: {scope_root}"
        ) from exc
    except OSError as exc:
        raise TaskBoundaryError(
            f"Could not create workflow-attempt task scope: {scope_root}: {exc}"
        ) from exc
    _sync_directory(scope_root, "workflow-attempt task scope")
    _sync_directory(scope_root.parent, "workflow-attempt owner directory")


def _expected_scope_ids(
    task: Mapping[str, Any],
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    authority: SuccessorRunAuthority | None,
) -> set[str]:
    return {
        item.scope_id
        for item in expected_tasks(authority or execution, profile)
        if item.machine_key == task["machine_key"]
    }


def _step00c_fasta(
    dispatch: TaskDispatch,
    execution: Mapping[str, Any],
) -> Path:
    if execution.get("schema_version") != RUN_BINDING_SCHEMA_VERSION:
        return Path(str(execution["reference"]["fasta"]["path"]))
    if len(dispatch.inputs) != 1:
        raise TaskBoundaryError("Step 00c dispatch must bind exactly one FASTA input")
    return dispatch.inputs[0].path


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
    sidecar_owner = "emrys.stage.construct_FASTA_sidecars.v1"
    fasta = _step00c_fasta(dispatch, execution)
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


def _admit_step00c_external_parent_access(
    dispatch: TaskDispatch,
    execution: Mapping[str, Any],
    *,
    path_access: PathAccess,
) -> None:
    """Require current-user Step 00c publication access before task entry."""

    if dispatch.machine_key != "emrys.stage.construct_FASTA_sidecars.v1":
        return
    fasta = _step00c_fasta(dispatch, execution)
    if not path_access(fasta, os.R_OK):
        raise TaskBoundaryError(
            f"Step 00c stationary FASTA is not readable before task entry: {fasta}"
        )
    if not path_access(fasta.parent, os.R_OK | os.W_OK | os.X_OK):
        raise TaskBoundaryError(
            "Step 00c stationary FASTA parent is not readable, writable, and "
            f"searchable before task entry: {fasta.parent}"
        )


def _step00c_external_outputs(
    dispatch: TaskDispatch,
    execution: Mapping[str, Any],
) -> tuple[FileDeclaration, ...]:
    """Return the exact stationary Step 00c pair, or no reusable outputs."""

    if dispatch.machine_key != "emrys.stage.construct_FASTA_sidecars.v1":
        return ()
    fasta = _step00c_fasta(dispatch, execution)
    expected_paths = {
        Path(f"{fasta}.fai"),
        fasta.with_name(f"{fasta.stem}.dict"),
    }
    for path in expected_paths:
        try:
            path.relative_to(dispatch.run_root)
        except ValueError:
            continue
        raise TaskBoundaryError(
            "Step 00c reusable sidecars must be stationary external outputs"
        )
    outputs = tuple(
        output for output in dispatch.outputs if output.path in expected_paths
    )
    if len(outputs) != 2 or {output.path for output in outputs} != expected_paths:
        raise TaskBoundaryError(
            "Step 00c dispatch must bind the exact stationary FAI/DICT pair"
        )
    return outputs


def _admit_native_destinations(
    dispatch: TaskDispatch,
    execution: Mapping[str, Any],
) -> dict[FileDeclaration, _BoundFileSnapshot]:
    """Require create-absent outputs except an already-complete Step 00c pair."""

    reusable = _step00c_external_outputs(dispatch, execution)
    reusable_paths = {output.path for output in reusable}
    observed_present: set[Path] = set()
    for output in reusable:
        try:
            output.path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise TaskBoundaryError(
                f"Could not inspect stationary Step 00c output: {output.path}: {exc}"
            ) from exc
        observed_present.add(output.path)
    if observed_present and observed_present != reusable_paths:
        raise TaskBoundaryError("Refusing partial pre-existing Step 00c FAI/DICT pair")

    reused = (
        {output: _bound_snapshot(output) for output in reusable}
        if observed_present
        else {}
    )
    for output in dispatch.outputs:
        if output.path not in reusable_paths:
            _require_absent(output.path, "native task destination")
    _require_absent(dispatch.validation_report_path, "native task destination")
    if dispatch.native_receipt_path is not None:
        _require_absent(dispatch.native_receipt_path, "native task destination")
    return reused


def _recheck_reused_outputs(
    reused: Mapping[FileDeclaration, _BoundFileSnapshot],
    *,
    phase: str,
) -> None:
    """Reject byte mutation or path replacement of an admitted Step 00c pair."""

    for declaration, expected in reused.items():
        observed = _bound_snapshot(declaration)
        if observed != expected:
            raise TaskBoundaryError(
                f"A reused Step 00c sidecar changed or was replaced {phase}: "
                f"{declaration.path}"
            )


def _admit_identity(
    dispatch: TaskDispatch,
) -> tuple[dict[str, Any], dict[str, Any], str, str, str]:
    profile, profile_data = _admit_record(
        dispatch.profile_path, dispatch.run_root, "profile"
    )
    execution, execution_data, authority = _admit_execution(
        dispatch.execution_path,
        dispatch.run_root,
        profile,
    )
    profile_sha256 = hashlib.sha256(profile_data).hexdigest()
    if (
        "profile" in execution
        and execution["profile"]["profile_sha256"] != profile_sha256
    ):
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
    if dispatch.scope["scope_id"] not in _expected_scope_ids(
        task, execution, profile, authority
    ):
        raise TaskBoundaryError("Dispatch scope_id is not selected by Run authority")
    _admit_output_locations(dispatch, execution)

    return (
        profile,
        execution,
        hashlib.sha256(execution_data).hexdigest(),
        profile_sha256,
        str(task["step_id"]),
    )


def _semantic_argv(dispatch: TaskDispatch, step_id: str) -> tuple[str, ...]:
    return controlled_python_argv(
        sys.executable,
        "-m",
        "emrys",
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
    data, _ = _read_bound_file(path, label)
    if hashlib.sha256(data).hexdigest() != reference.get("sha256"):
        raise TaskBoundaryError(f"{label} SHA-256 no longer matches")
    try:
        record = orchestration_contracts.load_json_object_bytes(data, label)
    except orchestration_contracts.ContractValidationError as exc:
        raise TaskBoundaryError(str(exc)) from exc
    if orchestration_contracts.canonical_json_bytes(record) != data:
        raise TaskBoundaryError(f"{label} must use canonical JSON bytes")
    return path, record


def _dispatch_reference(dispatch: TaskDispatch) -> dict[str, str]:
    return {
        "path": _relative(dispatch.path, dispatch.run_root),
        "sha256": dispatch.dispatch_sha256,
    }


def _admit_start_origins(
    dispatch: TaskDispatch,
    *,
    execution: Mapping[str, Any],
    execution_sha256: str,
    profile_sha256: str,
    require_active_attempt: bool,
    attest_source: SourceCheckoutAttester = _attest_source_checkout,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Admit the immutable workflow attempt and its bound dispatch plan."""

    attempt_path = (
        dispatch.run_root / "attempts" / dispatch.workflow_attempt_id / "attempt.json"
    )
    attempt, attempt_data = _admit_record(
        attempt_path, dispatch.run_root, "workflow-attempt"
    )
    expected_identity = {
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
        "workflow_attempt_id": dispatch.workflow_attempt_id,
    }
    for field, expected in expected_identity.items():
        if attempt[field] != expected:
            raise TaskBoundaryError(f"Workflow attempt does not bind task {field}")

    config_path, config = _referenced_record(
        attempt["workflow_config"],
        run_root=dispatch.run_root,
        label="workflow config",
    )
    by_owner = config.get("dispatch_paths")
    if not isinstance(by_owner, Mapping):
        raise TaskBoundaryError("Workflow config has no dispatch_paths object")
    by_scope = by_owner.get(dispatch.machine_key)
    if not isinstance(by_scope, Mapping):
        raise TaskBoundaryError("Workflow config has no dispatch owner scope map")
    configured = by_scope.get(dispatch.scope["scope_id"])
    if configured != {
        "path": str(dispatch.path),
        "sha256": dispatch.dispatch_sha256,
    }:
        raise TaskBoundaryError("Workflow config does not bind the exact task dispatch")
    source_checkout = attempt["source_checkout"]
    source_root = Path(str(source_checkout["path"]))
    if config.get("source_checkout") != str(source_root):
        raise TaskBoundaryError(
            "Workflow config does not bind the attempt source checkout"
        )
    if require_active_attempt:
        try:
            attest_source(
                root=source_root,
                package_root=Path(__file__).resolve().parents[2],
                expected_commit=str(source_checkout["commit"]),
            )
        except SourceCheckoutError as exc:
            raise TaskBoundaryError(
                f"Could not attest task child source checkout: {exc}"
            ) from exc
    config_after = _record_reference(config_path, dispatch.run_root)
    if config_after != attempt["workflow_config"]:
        raise TaskBoundaryError("Workflow config changed during task admission")
    attempt_after = _record_reference(attempt_path, dispatch.run_root)
    expected_attempt = {
        "path": _relative(attempt_path, dispatch.run_root),
        "sha256": hashlib.sha256(attempt_data).hexdigest(),
    }
    if attempt_after != expected_attempt:
        raise TaskBoundaryError("Workflow attempt changed during task admission")
    try:
        run_lock_reference = admit_attempt_run_lock(
            dispatch.run_root,
            attempt,
            require_active=require_active_attempt,
        )
    except InspectionError as exc:
        raise TaskBoundaryError(f"Could not admit workflow run lock: {exc}") from exc
    return expected_attempt, dict(attempt["workflow_config"]), run_lock_reference


def _build_task_start(
    dispatch: TaskDispatch,
    *,
    execution: Mapping[str, Any],
    execution_sha256: str,
    profile_sha256: str,
    created_at: str,
    attest_source: SourceCheckoutAttester,
) -> tuple[dict[str, Any], bytes]:
    attempt_reference, config_reference, run_lock_reference = _admit_start_origins(
        dispatch,
        execution=execution,
        execution_sha256=execution_sha256,
        profile_sha256=profile_sha256,
        require_active_attempt=True,
        attest_source=attest_source,
    )
    record = {
        "schema_version": "emrys.task-start.v1",
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
        "workflow_attempt_id": dispatch.workflow_attempt_id,
        "task_attempt_id": dispatch.task_attempt_id,
        "machine_key": dispatch.machine_key,
        "scope": dict(dispatch.scope),
        "owner_run_token": dispatch.owner_run_token,
        "workflow_attempt_record": attempt_reference,
        "workflow_config": config_reference,
        "run_lock": run_lock_reference,
        "task_dispatch_record": _dispatch_reference(dispatch),
        "created_at": created_at,
    }
    orchestration_contracts.validate_record("task-start", record)
    return record, orchestration_contracts.canonical_json_bytes(record)


def _task_admission_context(
    run_root: Path,
    machine_key: str,
    scope: Mapping[str, str],
) -> tuple[Path, str, dict[str, str]]:
    canonical_root = _absolute_path(str(run_root), "run_root")
    if canonical_root.resolve(strict=True) != canonical_root:
        raise TaskBoundaryError("run_root must already be canonical")
    return (
        canonical_root,
        _safe_id(machine_key, "machine_key"),
        {
            field: _safe_id(scope.get(field), f"scope.{field}")
            for field in ("scope_type", "scope_id")
        },
    )


def _task_identity(
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    machine_key: str,
    scope: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "run_id": execution["run_id"],
        "execution_contract_sha256": orchestration_contracts.canonical_sha256(
            execution
        ),
        "profile_sha256": orchestration_contracts.canonical_sha256(profile),
        "machine_key": machine_key,
        "scope": dict(scope),
    }


def validate_task_start(
    path: Path,
    *,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    machine_key: str,
    scope: Mapping[str, str],
) -> dict[str, Any]:
    """Fail closed unless one producer-entry record remains content-bound."""

    canonical_root, owner_key, expected_scope = _task_admission_context(
        run_root, machine_key, scope
    )
    start_path = _absolute_path(str(path), "task-start path")
    expected_path = (
        canonical_root
        / "state"
        / "task-starts"
        / owner_key
        / f"{expected_scope['scope_id']}.json"
    )
    if start_path != expected_path:
        raise TaskBoundaryError("Task-start record is not at its exact ledger path")
    _safe_in_run_destination(start_path, canonical_root, "task-start path")
    orchestration_contracts.validate_record("profile", profile)
    record, start_data = _admit_record(start_path, canonical_root, "task-start")
    identity = _task_identity(execution, profile, owner_key, expected_scope)
    for field, expected in identity.items():
        if record[field] != expected:
            raise TaskBoundaryError(f"Task-start {field} does not match")

    dispatch_path, dispatch_record = _referenced_record(
        record["task_dispatch_record"],
        run_root=canonical_root,
        label="task dispatch record",
    )
    dispatch = load_dispatch(
        dispatch_path,
        expected_sha256=record["task_dispatch_record"]["sha256"],
    )
    loaded_profile, loaded_execution, execution_sha256, profile_sha256, _ = (
        _admit_identity(dispatch)
    )
    if loaded_profile != dict(profile) or loaded_execution != dict(execution):
        raise TaskBoundaryError("Task-start dispatch binds different run contracts")
    for field in (
        "workflow_attempt_id",
        "task_attempt_id",
        "machine_key",
        "scope",
        "owner_run_token",
    ):
        observed = getattr(dispatch, field)
        if record[field] != observed:
            raise TaskBoundaryError(f"Task-start and dispatch disagree on {field}")
    if dispatch.task_start_path != start_path:
        raise TaskBoundaryError("Task-start dispatch binds a different ledger path")
    attempt_reference, config_reference, run_lock_reference = _admit_start_origins(
        dispatch,
        execution=loaded_execution,
        execution_sha256=execution_sha256,
        profile_sha256=profile_sha256,
        require_active_attempt=False,
    )
    if record["workflow_attempt_record"] != attempt_reference:
        raise TaskBoundaryError("Task-start workflow attempt reference differs")
    if record["workflow_config"] != config_reference:
        raise TaskBoundaryError("Task-start workflow config reference differs")
    if record["run_lock"] != run_lock_reference:
        raise TaskBoundaryError("Task-start run-lock reference differs")
    if dispatch_record.get("task_start_path") != str(start_path):
        raise TaskBoundaryError("Task dispatch content binds a different start path")
    if (
        _record_reference(dispatch_path, canonical_root)
        != record["task_dispatch_record"]
    ):
        raise TaskBoundaryError("Task dispatch changed during start admission")
    expected_start_reference = {
        "path": _relative(start_path, canonical_root),
        "sha256": hashlib.sha256(start_data).hexdigest(),
    }
    if _record_reference(start_path, canonical_root) != expected_start_reference:
        raise TaskBoundaryError("Task-start record changed during admission")
    return record


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
    digest, _ = _hash_bound_file(path, label)
    if digest != reference.get("sha256"):
        raise TaskBoundaryError(f"{label} SHA-256 no longer matches")
    return path


def _admit_task_attempt(
    *,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    workflow_attempt_id: str,
    machine_key: str,
    scope: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Admit one terminal owner attempt at its exact task-tree boundary."""

    canonical_root, owner_key, expected_scope = _task_admission_context(
        run_root, machine_key, scope
    )
    identifier = _safe_id(workflow_attempt_id, "workflow_attempt_id")
    attempt_path = (
        canonical_root
        / "attempts"
        / identifier
        / "tasks"
        / owner_key
        / expected_scope["scope_id"]
        / "task-attempt.json"
    )
    record, data = _admit_record(attempt_path, canonical_root, "task-attempt")
    reference = {
        "path": _relative(attempt_path, canonical_root),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    identity = _task_identity(execution, profile, owner_key, expected_scope)
    identity["workflow_attempt_id"] = identifier
    for field, expected in identity.items():
        if record[field] != expected:
            raise TaskBoundaryError(f"Task attempt {field} does not match")
    for field, file_name in (
        ("stdout_log", "stdout.log"),
        ("stderr_log", "stderr.log"),
    ):
        if _verify_reference(
            record[field],
            run_root=canonical_root,
            label=field.replace("_", " "),
        ) != attempt_path.with_name(file_name):
            raise TaskBoundaryError(f"Task attempt binds a different {field}")
    start_reference = record["task_start_record"]
    if start_reference is None:
        if record["status"] != "failed":
            raise TaskBoundaryError("Preentry task attempt must be failed")
    else:
        start_path = (
            canonical_root
            / "state"
            / "task-starts"
            / owner_key
            / f"{expected_scope['scope_id']}.json"
        )
        if (
            _verify_reference(
                start_reference,
                run_root=canonical_root,
                label="task-start record",
            )
            != start_path
        ):
            raise TaskBoundaryError("Task attempt does not bind its exact start")
    return record, reference


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

    canonical_root, owner_key, expected_scope = _task_admission_context(
        run_root, machine_key, scope
    )
    verified_path = _absolute_path(str(path), "verified task path")
    _safe_in_run_destination(verified_path, canonical_root, "verified task path")
    orchestration_contracts.validate_record("profile", profile)
    record, _ = _admit_record(verified_path, canonical_root, "verified-task")
    profile_tasks = [
        item for item in profile["owner_tasks"] if item["machine_key"] == owner_key
    ]
    if len(profile_tasks) != 1 or owner_key not in profile["required_owner_keys"]:
        raise TaskBoundaryError("Verified task owner is not one required profile owner")
    owner = profile_tasks[0]
    if owner["scope_type"] != expected_scope["scope_type"]:
        raise TaskBoundaryError("Verified task scope_type does not match profile owner")
    identity = _task_identity(execution, profile, owner_key, expected_scope)
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

    attempt_reference = record["task_attempt_record"]
    attempt, admitted_attempt_reference = _admit_task_attempt(
        run_root=canonical_root,
        execution=execution,
        profile=profile,
        workflow_attempt_id=str(record["workflow_attempt_id"]),
        machine_key=owner_key,
        scope=expected_scope,
    )
    if admitted_attempt_reference != attempt_reference:
        raise TaskBoundaryError("Task-attempt record reference no longer matches")
    for field in (
        "task_attempt_id",
        "owner_run_token",
    ):
        if attempt[field] != record[field]:
            raise TaskBoundaryError(
                f"Task attempt and verified task disagree on {field}"
            )
    if attempt["status"] != "succeeded" or attempt["failure_message"] is not None:
        raise TaskBoundaryError("Referenced task attempt is not successful")
    if attempt["task_start_record"] != record["task_start_record"]:
        raise TaskBoundaryError("Task attempt and verified task disagree on task start")
    start_path = (
        canonical_root
        / "state"
        / "task-starts"
        / owner_key
        / f"{expected_scope['scope_id']}.json"
    )
    start = validate_task_start(
        start_path,
        run_root=canonical_root,
        execution=execution,
        profile=profile,
        machine_key=owner_key,
        scope=expected_scope,
    )
    for field in (
        "workflow_attempt_id",
        "task_attempt_id",
        "machine_key",
        "scope",
        "owner_run_token",
    ):
        if start[field] != record[field]:
            raise TaskBoundaryError(f"Task start and verified task disagree on {field}")
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
    from emrys.orchestration.local_pilot.all_pass import (  # noqa: PLC0415
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
    task_start_reference: Mapping[str, str] | None,
    failure_message: str | None,
    streams: _TaskStreamCapture,
) -> tuple[dict[str, Any], bytes]:
    stdout_reference, stderr_reference = streams.finalize()
    report_reference = None
    if task_start_reference is not None:
        try:
            report_reference = _record_reference(
                dispatch.validation_report_path, dispatch.run_root
            )
        except TaskBoundaryError:
            if failure_message is None:
                raise
    status = "succeeded" if failure_message is None else "failed"
    attempt = {
        "schema_version": "emrys.task-attempt.v1",
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
        "workflow_attempt_id": dispatch.workflow_attempt_id,
        "task_attempt_id": dispatch.task_attempt_id,
        "machine_key": dispatch.machine_key,
        "scope": dict(dispatch.scope),
        "owner_run_token": dispatch.owner_run_token,
        "task_start_record": (
            None if task_start_reference is None else dict(task_start_reference)
        ),
        "status": status,
        "started_at": started_at,
        "finished_at": _utc_timestamp(ops.now()),
        "producer": None if producer is None else producer.record,
        "validator": None if validator is None else validator.record,
        "semantic_all_pass": None if semantic is None else semantic.record,
        "stable_inputs_rechecked": stable_inputs_rechecked,
        "validation_report": report_reference,
        "stdout_log": stdout_reference,
        "stderr_log": stderr_reference,
        "failure_message": failure_message,
    }
    orchestration_contracts.validate_record("task-attempt", attempt)
    attempt_bytes = orchestration_contracts.canonical_json_bytes(attempt)
    ops.publish_bytes(dispatch.task_attempt_path, attempt_bytes)
    streams.revalidate_after_attempt_publication()
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
    task_start_reference: dict[str, str] | None = None
    task_scope_materialized = False
    reused_outputs: dict[FileDeclaration, _BoundFileSnapshot] = {}
    streams = _TaskStreamCapture(
        dispatch.stdout_path,
        dispatch.stderr_path,
        dispatch.run_root,
    )
    failure: TaskBoundaryError | None = None

    protected = (
        dispatch.task_start_path,
        dispatch.task_attempt_path,
        dispatch.verified_task_path,
        dispatch.stdout_path,
        dispatch.stderr_path,
    )
    for path, label in zip(
        protected,
        (
            "task-start record",
            "task-attempt record",
            "verified-task record",
            "stdout log",
            "stderr log",
        ),
        strict=True,
    ):
        _require_absent(path, label)

    try:
        profile, execution, execution_sha256, profile_sha256, step_id = _admit_identity(
            dispatch
        )
        _admit_step00c_external_parent_access(
            dispatch,
            execution,
            path_access=ops.path_access,
        )
        _admit_start_origins(
            dispatch,
            execution=execution,
            execution_sha256=execution_sha256,
            profile_sha256=profile_sha256,
            require_active_attempt=True,
            attest_source=ops.attest_source_checkout,
        )
        _materialize_task_scope(dispatch)
        task_scope_materialized = True
        initial_inputs = tuple(
            _snapshot(item)
            for item in (
                FileDeclaration("task_dispatch", dispatch.path),
                FileDeclaration("execution_contract", dispatch.execution_path),
                FileDeclaration("workflow_profile", dispatch.profile_path),
                *dispatch.inputs,
            )
        )
        if initial_inputs[0]["sha256"] != dispatch.dispatch_sha256:
            raise TaskBoundaryError("Task dispatch changed before producer execution")
        if len({item["role"] for item in initial_inputs}) != len(initial_inputs):
            raise TaskBoundaryError("Input roles collide with reserved contract roles")

        reused_outputs = _admit_native_destinations(dispatch, execution)

        entry_inputs = tuple(
            _snapshot(item)
            for item in (
                FileDeclaration("task_dispatch", dispatch.path),
                FileDeclaration("execution_contract", dispatch.execution_path),
                FileDeclaration("workflow_profile", dispatch.profile_path),
                *dispatch.inputs,
            )
        )
        if entry_inputs != initial_inputs:
            raise TaskBoundaryError("A stable task input changed before producer entry")
        _recheck_reused_outputs(reused_outputs, phase="before producer entry")
        _admit_step00c_external_parent_access(
            dispatch,
            execution,
            path_access=ops.path_access,
        )

        _task_start, task_start_bytes = _build_task_start(
            dispatch,
            execution=execution,
            execution_sha256=execution_sha256,
            profile_sha256=profile_sha256,
            created_at=_utc_timestamp(ops.now()),
            attest_source=ops.attest_source_checkout,
        )
        _attempt_ref, _config_ref, lock_reference_at_entry = _admit_start_origins(
            dispatch,
            execution=execution,
            execution_sha256=execution_sha256,
            profile_sha256=profile_sha256,
            require_active_attempt=True,
            attest_source=ops.attest_source_checkout,
        )
        if lock_reference_at_entry != _task_start["run_lock"]:
            raise TaskBoundaryError("Workflow run lock changed before producer entry")
        ops.publish_bytes(dispatch.task_start_path, task_start_bytes)
        task_start_reference = _record_reference(
            dispatch.task_start_path, dispatch.run_root
        )
        if task_start_reference != {
            "path": _relative(dispatch.task_start_path, dispatch.run_root),
            "sha256": hashlib.sha256(task_start_bytes).hexdigest(),
        }:
            raise TaskBoundaryError(
                "Published task-start bytes changed before producer"
            )
        _attempt_ref, _config_ref, lock_reference_before_producer = (
            _admit_start_origins(
                dispatch,
                execution=execution,
                execution_sha256=execution_sha256,
                profile_sha256=profile_sha256,
                require_active_attempt=True,
                attest_source=ops.attest_source_checkout,
            )
        )
        if lock_reference_before_producer != _task_start["run_lock"]:
            raise TaskBoundaryError("Workflow run lock changed before producer entry")
        _recheck_reused_outputs(reused_outputs, phase="before producer entry")
        command_environment = sanitized_subprocess_environment()
        command_environment.pop(_STEP07_INPUT_IDENTITY_ENV, None)
        producer_environment = dict(command_environment)
        if dispatch.machine_key == _STEP07_MACHINE_KEY:
            identity = hashlib.sha256(b"emrys.step07-input-identity.v1\0")
            for item in entry_inputs[3:]:
                identity.update(os.fsencode(f"{item['path']}\0{item['sha256']}\0"))
            producer_environment[_STEP07_INPUT_IDENTITY_ENV] = identity.hexdigest()
        stream_descriptors = streams.open()
        command_arguments = (
            dispatch.run_root,
            command_environment,
            *stream_descriptors,
        )
        producer = ops.run_command(
            backend.producer_argv,
            dispatch.run_root,
            producer_environment,
            *stream_descriptors,
        )
        if producer.exit_code != 0:
            raise TaskBoundaryError(
                f"Producer command exited with status {producer.exit_code}"
            )
        _recheck_reused_outputs(reused_outputs, phase="during producer execution")
        producer_outputs = tuple(_snapshot(output) for output in dispatch.outputs)
        producer_native_receipt = (
            None
            if dispatch.native_receipt_path is None
            else _record_reference(dispatch.native_receipt_path, dispatch.run_root)
        )

        validator = ops.run_command(backend.validator_argv, *command_arguments)
        if validator.exit_code != 0:
            raise TaskBoundaryError(
                f"Validator command exited with status {validator.exit_code}"
            )

        validation_before_all_pass = _record_reference(
            dispatch.validation_report_path, dispatch.run_root
        )
        semantic = ops.run_semantic_all_pass(
            _semantic_argv(dispatch, step_id), *command_arguments
        )
        if semantic.exit_code != 0:
            raise TaskBoundaryError(
                f"Semantic all-pass command exited with status {semantic.exit_code}"
            )
        _recheck_reused_outputs(
            reused_outputs,
            phase="during validation or semantic gating",
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
    except BaseException:
        streams.preserve_incomplete()
        raise

    if failure is not None:
        message = str(failure).strip() or type(failure).__name__
        if not execution or not task_scope_materialized:
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
            task_start_reference=task_start_reference,
            failure_message=message,
            streams=streams,
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
        task_start_reference=task_start_reference,
        failure_message=None,
        streams=streams,
    )
    assert producer is not None and validator is not None and semantic is not None
    assert task_start_reference is not None
    task_attempt_reference = {
        "path": _relative(dispatch.task_attempt_path, dispatch.run_root),
        "sha256": hashlib.sha256(attempt_bytes).hexdigest(),
    }
    verified = {
        "schema_version": "emrys.verified-task.v1",
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
        "workflow_attempt_id": dispatch.workflow_attempt_id,
        "task_attempt_id": dispatch.task_attempt_id,
        "task_attempt_record": task_attempt_reference,
        "task_start_record": task_start_reference,
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
    _recheck_reused_outputs(reused_outputs, phase="before verified publication")
    if tuple(_snapshot(item) for item in dispatch.outputs) != outputs:
        raise TaskBoundaryError("A producer output changed before verified publication")
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


def execute_dispatch(
    path: Path,
    *,
    expected_sha256: str,
    ops: TaskOps | None = None,
) -> TaskOutcome:
    """Load and execute one dispatch through its exact admitted backend."""

    dispatch = load_dispatch(path, expected_sha256=expected_sha256)
    selected_ops = default_task_ops() if ops is None else ops
    return run_task(dispatch, backend=dispatch.backend, ops=selected_ops)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Execute one closed EMRYS local-pilot owner dispatch and publish a "
        "verified-task record only after producer, validator, and semantic "
        "all-pass success. This is an internal workflow boundary, not a public "
        "run/resume/inspect interface."
    )
    parser.add_argument(
        "--dispatch",
        required=True,
        type=Path,
        help="Absolute path to one materialized emrys.local-task-dispatch.v1 JSON file.",
    )
    parser.add_argument(
        "--dispatch-sha256",
        required=True,
        help="Expected lowercase SHA-256 bound by the immutable workflow config.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    arguments = parser.parse_args(argv)
    try:
        require_controlled_python_runtime()
        outcome = execute_dispatch(
            arguments.dispatch,
            expected_sha256=arguments.dispatch_sha256,
        )
    except (
        OSError,
        SourceCheckoutError,
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
    "validate_task_start",
    "validate_verified_task",
)
