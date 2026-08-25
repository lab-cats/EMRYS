"""Immutable start/completion boundary for fixed reporting transactions."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.projection import CONTRACT_PATHS
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    attest_source_checkout,
    require_controlled_python_runtime,
)
from emrys.orchestration.local_pilot.inspection import (
    InspectionError,
    admit_attempt_run_lock,
    admit_canonical_record,
)

ReportingKind = Literal["artifact_index", "run_summary", "html_report"]
REPORTING_KINDS: tuple[ReportingKind, ...] = (
    "artifact_index",
    "run_summary",
    "html_report",
)


class ReportingBoundaryError(RuntimeError):
    """A reporting producer cannot enter or prove its immutable boundary."""


def _sync_directory(path: Path) -> None:
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
        raise ReportingBoundaryError(
            f"Could not synchronize reporting ledger directory: {path}: {exc}"
        ) from exc


class SemanticTransaction(Protocol):
    receipt_path: Path
    receipt_sha256: str


def _semantic_report_locations(
    kind: ReportingKind,
    semantic: SemanticTransaction,
) -> tuple[tuple[str, Path], ...]:
    if kind != "html_report":
        return ()
    locations = getattr(semantic, "verified_report_locations", ())
    expected_ids = ("scientific-report-html", "evidence-report-html")
    try:
        admitted = tuple((output_id, path) for output_id, path in locations)
    except (TypeError, ValueError) as exc:
        raise ReportingBoundaryError(
            "Validated HTML report transaction returned malformed result locations"
        ) from exc
    if (
        tuple(output_id for output_id, _path in admitted) != expected_ids
        or any(
            not isinstance(path, Path) or not path.is_absolute()
            for _, path in admitted
        )
    ):
        raise ReportingBoundaryError(
            "Validated HTML report transaction lacks both exact verified result locations"
        )
    return admitted


SemanticValidator = Callable[
    [
        str,
        Path,
        Path,
        Mapping[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ],
    SemanticTransaction,
]


@dataclass(frozen=True, slots=True)
class ReportingLedgerPaths:
    """The only state paths owned by one reporting kind."""

    root: Path
    start: Path
    verified: Path


@dataclass(frozen=True, slots=True)
class ReportingBoundaryOutcome:
    """One admitted reporting ledger plus its semantic receipt identity."""

    kind: ReportingKind
    start_path: Path
    verified_path: Path | None
    origin_workflow_attempt_id: str
    semantic_receipt_path: Path | None
    semantic_receipt_sha256: str | None
    verified_report_locations: tuple[tuple[str, Path], ...] = ()


BytesPublisher = Callable[[Path, bytes], None]


@dataclass(frozen=True, slots=True)
class ReportingBoundaryOps:
    """Explicit filesystem, clock, and semantic dependencies for fault tests."""

    publish_bytes: BytesPublisher
    now: Callable[[], datetime]
    validate_semantic_receipt: SemanticValidator
    sync_directory: Callable[[Path], None] = _sync_directory
    attest_source_checkout: Callable[..., Any] = attest_source_checkout


@dataclass(frozen=True, slots=True)
class _AdmittedIdentity:
    root: Path
    execution: dict[str, Any]
    profile: dict[str, Any]
    attempt: dict[str, Any]
    execution_sha256: str
    profile_sha256: str
    attempt_reference: dict[str, str]
    config_reference: dict[str, str]
    run_lock_reference: dict[str, str]


def _semantic_validator(
    kind: str,
    receipt_path: Path,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempt: Mapping[str, Any],
) -> SemanticTransaction:
    from emrys.reporting.transaction_validation import validate_receipt  # noqa: PLC0415

    return validate_receipt(kind, receipt_path, run_root, execution, profile, attempt)


def _publish_exclusive(path: Path, data: bytes) -> None:
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ReportingBoundaryError(
            f"Reporting ledger parent must be a real directory: {parent}"
        )
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportingBoundaryError(
            "This platform lacks required O_NOFOLLOW reporting publication"
        )
    stage = parent / f".{path.name}.{uuid.uuid4().hex}.emrys-stage"
    descriptor = -1
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(stage, flags, 0o600)
        remaining = memoryview(data)
        while remaining:
            written = os.write(descriptor, remaining)
            remaining = remaining[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(stage, path, follow_symlinks=False)
        staged = stage.stat(follow_symlinks=False)
        final = path.stat(follow_symlinks=False)
        if (staged.st_dev, staged.st_ino) != (final.st_dev, final.st_ino):
            raise ReportingBoundaryError(
                f"Reporting publication did not retain staged inode: {path}"
            )
        stage.unlink()
        _sync_directory(parent)
    except FileExistsError as exc:
        raise ReportingBoundaryError(
            f"Refusing to replace reporting ledger state: {path}"
        ) from exc
    except OSError as exc:
        raise ReportingBoundaryError(f"Could not publish {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            stage.unlink()
        except FileNotFoundError:
            pass


DEFAULT_REPORTING_BOUNDARY_OPS = ReportingBoundaryOps(
    publish_bytes=_publish_exclusive,
    now=lambda: datetime.now(UTC),
    validate_semantic_receipt=_semantic_validator,
)


def _kind(value: str) -> ReportingKind:
    if value not in REPORTING_KINDS:
        raise ReportingBoundaryError(f"Unknown reporting kind: {value}")
    return cast("ReportingKind", value)


def _canonical_root(path: Path) -> Path:
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ReportingBoundaryError(
            f"run_root must be an absolute real directory: {path}"
        )
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ReportingBoundaryError(f"run_root is unavailable: {path}") from exc
    if resolved != path:
        raise ReportingBoundaryError(f"run_root must already be canonical: {path}")
    return path


def _within(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ReportingBoundaryError(
            f"{label} must be beneath run_root: {path}"
        ) from exc


def _read_bound(path: Path, root: Path, label: str) -> bytes:
    if not path.is_absolute():
        raise ReportingBoundaryError(f"{label} must be absolute: {path}")
    _within(path, root, label)
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportingBoundaryError(
            "This platform lacks required O_NOFOLLOW reporting admission"
        )
    try:
        if path.resolve(strict=True) != path:
            raise ReportingBoundaryError(
                f"{label} must be a canonical regular file: {path}"
            )
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise ReportingBoundaryError(f"Could not admit {label}: {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReportingBoundaryError(f"{label} is not a regular file: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        current = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise ReportingBoundaryError(f"{label} changed while admitted: {path}") from exc

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after) or identity(after) != identity(current):
        raise ReportingBoundaryError(f"{label} changed while admitted: {path}")
    data = b"".join(chunks)
    if len(data) != before.st_size:
        raise ReportingBoundaryError(f"{label} size changed while admitted: {path}")
    return data


_admit_record = partial(
    admit_canonical_record,
    read_bytes=_read_bound,
    error_type=ReportingBoundaryError,
)


def _load_canonical_object(
    path: Path,
    root: Path,
    label: str,
) -> tuple[dict[str, Any], bytes]:
    data = _read_bound(path, root, label)
    try:
        record = orchestration_contracts.load_json_object_bytes(data, f"{label} {path}")
    except orchestration_contracts.ContractValidationError as exc:
        raise ReportingBoundaryError(f"Invalid {label} at {path}: {exc}") from exc
    if data != orchestration_contracts.canonical_json_bytes(record):
        raise ReportingBoundaryError(f"{label} must use canonical JSON bytes: {path}")
    return record, data


def _reference(path: Path, root: Path, data: bytes | None = None) -> dict[str, str]:
    admitted = _read_bound(path, root, "record reference") if data is None else data
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(admitted).hexdigest(),
    }


def _admit_reporting_projection(
    *,
    root: Path,
    execution: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    projection = execution["reporting_projection"]
    if set(projection) != set(CONTRACT_PATHS):
        raise ReportingBoundaryError(
            "Execution reporting projection does not use the fixed complete roster"
        )
    for name, relative in CONTRACT_PATHS.items():
        reference = projection[name]
        if reference["path"] != relative:
            raise ReportingBoundaryError(
                f"Reporting projection {name} does not use its fixed path"
            )
        path = root / relative
        if config.get(f"{name}_path") != str(path):
            raise ReportingBoundaryError(
                f"Workflow config does not bind reporting projection {name}"
            )
        data = _read_bound(path, root, f"reporting projection {name}")
        if hashlib.sha256(data).hexdigest() != reference["sha256"]:
            raise ReportingBoundaryError(
                f"Reporting projection {name} bytes differ from execution identity"
            )
        if path.suffix == ".json":
            try:
                document = orchestration_contracts.load_json_object_bytes(
                    data,
                    f"reporting projection {name} {path}",
                )
            except orchestration_contracts.ContractValidationError as exc:
                raise ReportingBoundaryError(
                    f"Reporting projection {name} is invalid: {path}: {exc}"
                ) from exc
            if data != orchestration_contracts.canonical_json_bytes(document):
                raise ReportingBoundaryError(
                    f"Reporting projection {name} must use canonical JSON bytes"
                )


def ledger_paths(run_root: Path, kind: str) -> ReportingLedgerPaths:
    """Return the only legal start/completion paths for one reporting kind."""

    root = _canonical_root(run_root)
    admitted_kind = _kind(kind)
    ledger_root = root / "state" / "reporting" / admitted_kind
    return ReportingLedgerPaths(
        root=ledger_root,
        start=ledger_root / "start.json",
        verified=ledger_root / "verified.json",
    )


def _ensure_ledger_root(
    paths: ReportingLedgerPaths,
    run_root: Path,
    ops: ReportingBoundaryOps,
) -> None:
    cursor = run_root
    for part in paths.root.relative_to(run_root).parts:
        cursor = cursor / part
        try:
            cursor.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise ReportingBoundaryError(
                f"Could not materialize reporting ledger directory: {cursor}: {exc}"
            ) from exc
        try:
            state = cursor.lstat()
        except OSError as exc:
            raise ReportingBoundaryError(
                f"Could not admit reporting ledger directory: {cursor}: {exc}"
            ) from exc
        if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
            raise ReportingBoundaryError(
                f"Reporting ledger path is not a real directory: {cursor}"
            )
        # Repeat the link-durability barrier for an existing empty hierarchy as
        # well: it may be the visible residue of an earlier failed sync/retry.
        ops.sync_directory(cursor)
        ops.sync_directory(cursor.parent)
    _admit_ledger_root(paths)


def _admit_ledger_root(paths: ReportingLedgerPaths) -> None:
    """Admit the stable, closed membership of one fixed ledger directory."""

    if not hasattr(os, "O_NOFOLLOW"):
        raise ReportingBoundaryError(
            "This platform lacks required O_NOFOLLOW reporting admission"
        )
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(paths.root, flags)
    except OSError as exc:
        raise ReportingBoundaryError(
            f"Could not admit reporting ledger directory: {paths.root}: {exc}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISDIR(before.st_mode):
            raise ReportingBoundaryError(
                f"Reporting ledger path is not a real directory: {paths.root}"
            )
        entries = set(os.listdir(descriptor))
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        current = paths.root.stat(follow_symlinks=False)
    except OSError as exc:
        raise ReportingBoundaryError(
            f"Reporting ledger directory changed during admission: {paths.root}"
        ) from exc

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after) or identity(after) != identity(current):
        raise ReportingBoundaryError(
            f"Reporting ledger directory changed during admission: {paths.root}"
        )
    unexpected = entries - {"start.json", "verified.json"}
    if unexpected:
        raise ReportingBoundaryError(
            "Reporting ledger contains unexpected state: "
            + ", ".join(sorted(unexpected))
        )


def _run_lock_reference(
    root: Path,
    attempt: Mapping[str, Any],
    *,
    require_active: bool,
) -> dict[str, str]:
    try:
        return admit_attempt_run_lock(
            root,
            attempt,
            require_active=require_active,
        )
    except InspectionError as exc:
        raise ReportingBoundaryError(
            f"Could not bind reporting to workflow run-lock evidence: {exc}"
        ) from exc


def _admit_identity(
    *,
    run_root: Path,
    execution_path: Path,
    profile_path: Path,
    workflow_attempt_path: Path,
    workflow_config_path: Path,
    require_active_attempt: bool,
    attest_source: Callable[..., Any] = attest_source_checkout,
) -> _AdmittedIdentity:
    root = _canonical_root(run_root)
    expected_execution = root / "contract" / "normalized.json"
    expected_profile = root / "contract" / "profile.json"
    if execution_path != expected_execution or profile_path != expected_profile:
        raise ReportingBoundaryError(
            "Reporting identity must use the fixed execution/profile contract paths"
        )
    profile, profile_data = _admit_record(profile_path, root, "profile")
    execution, execution_data = _admit_record(
        execution_path,
        root,
        "execution",
        profile=profile,
    )
    attempt, attempt_data = _admit_record(
        workflow_attempt_path,
        root,
        "workflow-attempt",
    )
    identifier = str(attempt["workflow_attempt_id"])
    expected_attempt = root / "attempts" / identifier / "attempt.json"
    if workflow_attempt_path != expected_attempt:
        raise ReportingBoundaryError(
            "Workflow attempt does not use its fixed immutable path"
        )
    expected_config = root / str(attempt["workflow_config"]["path"])
    if workflow_config_path != expected_config:
        raise ReportingBoundaryError(
            "Workflow config path differs from the attempt-bound reference"
        )
    config, config_data = _load_canonical_object(
        workflow_config_path,
        root,
        "workflow config",
    )
    config_reference = _reference(workflow_config_path, root, config_data)
    if config_reference != attempt["workflow_config"]:
        raise ReportingBoundaryError(
            "Workflow config bytes differ from the attempt-bound reference"
        )
    execution_sha256 = hashlib.sha256(execution_data).hexdigest()
    profile_sha256 = hashlib.sha256(profile_data).hexdigest()
    expected_identity = {
        "run_id": execution["run_id"],
        "execution_contract_sha256": execution_sha256,
        "profile_sha256": profile_sha256,
    }
    for field, expected in expected_identity.items():
        if attempt[field] != expected:
            raise ReportingBoundaryError(
                f"Workflow attempt does not bind reporting {field}"
            )
    config_identity = {
        "run_root": str(root),
        "execution_path": str(execution_path),
        "profile_path": str(profile_path),
        "workflow_attempt_id": identifier,
    }
    for field, expected in config_identity.items():
        if config.get(field) != expected:
            raise ReportingBoundaryError(f"Workflow config does not bind {field}")
    source_checkout = attempt["source_checkout"]
    source_checkout_root = Path(str(source_checkout["path"]))
    if config.get("source_checkout") != str(source_checkout_root):
        raise ReportingBoundaryError(
            "Workflow config does not bind the attempt source checkout"
        )
    if config.get("artifact_source_root") != str(root):
        raise ReportingBoundaryError(
            "Workflow config artifact_source_root must equal run_root"
        )
    if require_active_attempt:
        try:
            attest_source(
                root=source_checkout_root,
                package_root=Path(__file__).resolve().parents[2],
                expected_commit=str(source_checkout["commit"]),
            )
        except SourceCheckoutError as exc:
            raise ReportingBoundaryError(
                f"Could not attest reporting source checkout: {exc}"
            ) from exc
    _admit_reporting_projection(root=root, execution=execution, config=config)
    run_lock_reference = _run_lock_reference(
        root,
        attempt,
        require_active=require_active_attempt,
    )
    return _AdmittedIdentity(
        root=root,
        execution=execution,
        profile=profile,
        attempt=attempt,
        execution_sha256=execution_sha256,
        profile_sha256=profile_sha256,
        attempt_reference=_reference(workflow_attempt_path, root, attempt_data),
        config_reference=config_reference,
        run_lock_reference=run_lock_reference,
    )


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ReportingBoundaryError("Reporting clock must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _identity_record(
    identity: _AdmittedIdentity,
    kind: ReportingKind,
) -> dict[str, Any]:
    return {
        "run_id": identity.execution["run_id"],
        "execution_contract_sha256": identity.execution_sha256,
        "profile_sha256": identity.profile_sha256,
        "origin_workflow_attempt_id": identity.attempt["workflow_attempt_id"],
        "kind": kind,
    }


def _require_start_not_before_attempt(
    created_at: str,
    identity: _AdmittedIdentity,
) -> None:
    start_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    attempt_time = datetime.fromisoformat(
        str(identity.attempt["created_at"]).replace("Z", "+00:00")
    )
    if start_time < attempt_time:
        raise ReportingBoundaryError(
            "Reporting start timestamp precedes its workflow attempt"
        )


def publish_start(
    *,
    kind: str,
    run_root: Path,
    execution_path: Path,
    profile_path: Path,
    workflow_attempt_path: Path,
    workflow_config_path: Path,
    ops: ReportingBoundaryOps = DEFAULT_REPORTING_BOUNDARY_OPS,
) -> ReportingBoundaryOutcome:
    """Publish the immutable marker immediately before one reporting producer."""

    admitted_kind = _kind(kind)
    identity = _admit_identity(
        run_root=run_root,
        execution_path=execution_path,
        profile_path=profile_path,
        workflow_attempt_path=workflow_attempt_path,
        workflow_config_path=workflow_config_path,
        require_active_attempt=True,
        attest_source=ops.attest_source_checkout,
    )
    paths = ledger_paths(identity.root, admitted_kind)
    _ensure_ledger_root(paths, identity.root, ops)
    if paths.start.exists() or paths.start.is_symlink():
        raise ReportingBoundaryError(
            f"Reporting start marker already exists: {paths.start}"
        )
    if paths.verified.exists() or paths.verified.is_symlink():
        raise ReportingBoundaryError(
            f"Reporting completion exists without this start: {paths.verified}"
        )
    created_at = _timestamp(ops.now())
    _require_start_not_before_attempt(created_at, identity)
    record = {
        "schema_version": "emrys.reporting-start.v1",
        **_identity_record(identity, admitted_kind),
        "workflow_attempt": identity.attempt_reference,
        "workflow_config": identity.config_reference,
        "run_lock": identity.run_lock_reference,
        "created_at": created_at,
    }
    orchestration_contracts.validate_record("reporting-start", record)
    confirmed = _admit_identity(
        run_root=run_root,
        execution_path=execution_path,
        profile_path=profile_path,
        workflow_attempt_path=workflow_attempt_path,
        workflow_config_path=workflow_config_path,
        require_active_attempt=True,
        attest_source=ops.attest_source_checkout,
    )
    if confirmed != identity:
        raise ReportingBoundaryError(
            "Reporting orchestration identity changed before start publication"
        )
    ops.publish_bytes(paths.start, orchestration_contracts.canonical_json_bytes(record))
    return ReportingBoundaryOutcome(
        kind=admitted_kind,
        start_path=paths.start,
        verified_path=None,
        origin_workflow_attempt_id=str(identity.attempt["workflow_attempt_id"]),
        semantic_receipt_path=None,
        semantic_receipt_sha256=None,
    )


def _expected_start(
    identity: _AdmittedIdentity,
    kind: ReportingKind,
) -> tuple[dict[str, Any], dict[str, str]]:
    paths = ledger_paths(identity.root, kind)
    _admit_ledger_root(paths)
    record, data = _admit_record(paths.start, identity.root, "reporting-start")
    expected = {
        **_identity_record(identity, kind),
        "workflow_attempt": identity.attempt_reference,
        "workflow_config": identity.config_reference,
        "run_lock": identity.run_lock_reference,
    }
    for field, value in expected.items():
        if record[field] != value:
            raise ReportingBoundaryError(
                f"Reporting start does not bind current {field}"
            )
    _require_start_not_before_attempt(str(record["created_at"]), identity)
    return record, _reference(paths.start, identity.root, data)


def publish_verified(
    *,
    kind: str,
    receipt_path: Path,
    run_root: Path,
    execution_path: Path,
    profile_path: Path,
    workflow_attempt_path: Path,
    workflow_config_path: Path,
    ops: ReportingBoundaryOps = DEFAULT_REPORTING_BOUNDARY_OPS,
) -> ReportingBoundaryOutcome:
    """Semantically validate a completed transaction and publish proof last."""

    admitted_kind = _kind(kind)
    identity = _admit_identity(
        run_root=run_root,
        execution_path=execution_path,
        profile_path=profile_path,
        workflow_attempt_path=workflow_attempt_path,
        workflow_config_path=workflow_config_path,
        require_active_attempt=True,
        attest_source=ops.attest_source_checkout,
    )
    paths = ledger_paths(identity.root, admitted_kind)
    _ensure_ledger_root(paths, identity.root, ops)
    if paths.verified.exists() or paths.verified.is_symlink():
        raise ReportingBoundaryError(
            f"Reporting completion already exists: {paths.verified}"
        )
    start, start_reference = _expected_start(identity, admitted_kind)
    try:
        semantic = ops.validate_semantic_receipt(
            admitted_kind,
            receipt_path,
            identity.root,
            identity.execution,
            identity.profile,
            identity.attempt,
        )
    except Exception as exc:
        raise ReportingBoundaryError(
            f"Could not validate completed {admitted_kind} transaction: {exc}"
        ) from exc
    receipt_data = _read_bound(receipt_path, identity.root, "semantic receipt")
    receipt_reference = _reference(receipt_path, identity.root, receipt_data)
    if (
        semantic.receipt_path != receipt_path
        or semantic.receipt_sha256 != receipt_reference["sha256"]
    ):
        raise ReportingBoundaryError(
            "Semantic validator returned a different reporting receipt identity"
        )
    verified_report_locations = _semantic_report_locations(
        admitted_kind,
        semantic,
    )
    confirmed = _admit_identity(
        run_root=run_root,
        execution_path=execution_path,
        profile_path=profile_path,
        workflow_attempt_path=workflow_attempt_path,
        workflow_config_path=workflow_config_path,
        require_active_attempt=True,
        attest_source=ops.attest_source_checkout,
    )
    if confirmed != identity:
        raise ReportingBoundaryError(
            "Reporting orchestration identity changed during semantic validation"
        )
    _start_after, start_reference_after = _expected_start(confirmed, admitted_kind)
    if start_reference_after != start_reference:
        raise ReportingBoundaryError(
            "Reporting start marker changed during semantic validation"
        )
    created_at = _timestamp(ops.now())
    if datetime.fromisoformat(
        created_at.replace("Z", "+00:00")
    ) < datetime.fromisoformat(str(start["created_at"]).replace("Z", "+00:00")):
        raise ReportingBoundaryError(
            "Reporting completion timestamp precedes its start marker"
        )
    record = {
        "schema_version": "emrys.verified-reporting.v1",
        **_identity_record(identity, admitted_kind),
        "reporting_start": start_reference,
        "semantic_receipt": receipt_reference,
        "created_at": created_at,
    }
    orchestration_contracts.validate_record("verified-reporting", record)
    if (
        _run_lock_reference(
            identity.root,
            identity.attempt,
            require_active=True,
        )
        != identity.run_lock_reference
    ):
        raise ReportingBoundaryError(
            "Reporting run-lock identity changed before completion publication"
        )
    ops.publish_bytes(
        paths.verified, orchestration_contracts.canonical_json_bytes(record)
    )
    return ReportingBoundaryOutcome(
        kind=admitted_kind,
        start_path=paths.start,
        verified_path=paths.verified,
        origin_workflow_attempt_id=str(identity.attempt["workflow_attempt_id"]),
        semantic_receipt_path=receipt_path,
        semantic_receipt_sha256=receipt_reference["sha256"],
        verified_report_locations=verified_report_locations,
    )


def _identity_from_origin(
    kind: ReportingKind,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[_AdmittedIdentity, dict[str, Any], dict[str, str]]:
    root = _canonical_root(run_root)
    paths = ledger_paths(root, kind)
    _admit_ledger_root(paths)
    start, start_data = _admit_record(paths.start, root, "reporting-start")
    origin = str(start["origin_workflow_attempt_id"])
    attempt_path = root / "attempts" / origin / "attempt.json"
    attempt, _attempt_data = _admit_record(attempt_path, root, "workflow-attempt")
    config_path = root / str(attempt["workflow_config"]["path"])
    identity = _admit_identity(
        run_root=root,
        execution_path=root / "contract" / "normalized.json",
        profile_path=root / "contract" / "profile.json",
        workflow_attempt_path=attempt_path,
        workflow_config_path=config_path,
        require_active_attempt=False,
    )
    if identity.execution != dict(execution) or identity.profile != dict(profile):
        raise ReportingBoundaryError(
            "Reporting origin does not bind the current execution/profile"
        )
    expected_start, start_reference = _expected_start(identity, kind)
    if expected_start != start or start_reference != _reference(
        paths.start, root, start_data
    ):
        raise ReportingBoundaryError(
            "Reporting start identity changed during admission"
        )
    return identity, start, start_reference


def validate_start(
    kind: str,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> ReportingBoundaryOutcome:
    """Read-only validation of an entered reporting scope against its origin."""

    admitted_kind = _kind(kind)
    identity, _start, _reference_value = _identity_from_origin(
        admitted_kind,
        run_root,
        execution,
        profile,
    )
    paths = ledger_paths(identity.root, admitted_kind)
    return ReportingBoundaryOutcome(
        kind=admitted_kind,
        start_path=paths.start,
        verified_path=None,
        origin_workflow_attempt_id=str(identity.attempt["workflow_attempt_id"]),
        semantic_receipt_path=None,
        semantic_receipt_sha256=None,
    )


def validate_verified(
    kind: str,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    semantic_validator: SemanticValidator = _semantic_validator,
) -> ReportingBoundaryOutcome:
    """Read-only revalidation of a verified ledger and full semantic transaction."""

    admitted_kind = _kind(kind)
    identity, start, start_reference = _identity_from_origin(
        admitted_kind,
        run_root,
        execution,
        profile,
    )
    paths = ledger_paths(identity.root, admitted_kind)
    verified, verified_data = _admit_record(
        paths.verified,
        identity.root,
        "verified-reporting",
    )
    expected = {
        **_identity_record(identity, admitted_kind),
        "reporting_start": start_reference,
    }
    for field, value in expected.items():
        if verified[field] != value:
            raise ReportingBoundaryError(
                f"Verified reporting record does not bind {field}"
            )
    if datetime.fromisoformat(
        str(verified["created_at"]).replace("Z", "+00:00")
    ) < datetime.fromisoformat(str(start["created_at"]).replace("Z", "+00:00")):
        raise ReportingBoundaryError(
            "Verified reporting timestamp precedes its start marker"
        )
    receipt_path = identity.root / str(verified["semantic_receipt"]["path"])
    try:
        semantic = semantic_validator(
            admitted_kind,
            receipt_path,
            identity.root,
            identity.execution,
            identity.profile,
            identity.attempt,
        )
    except Exception as exc:
        raise ReportingBoundaryError(
            f"Could not revalidate {admitted_kind} semantic transaction: {exc}"
        ) from exc
    receipt_data = _read_bound(receipt_path, identity.root, "semantic receipt")
    receipt_reference = _reference(receipt_path, identity.root, receipt_data)
    if (
        semantic.receipt_path != receipt_path
        or semantic.receipt_sha256 != receipt_reference["sha256"]
        or verified["semantic_receipt"] != receipt_reference
    ):
        raise ReportingBoundaryError(
            "Verified reporting semantic receipt identity no longer matches"
        )
    verified_report_locations = _semantic_report_locations(
        admitted_kind,
        semantic,
    )
    confirmed, confirmed_start, confirmed_start_reference = _identity_from_origin(
        admitted_kind,
        identity.root,
        execution,
        profile,
    )
    if (
        confirmed != identity
        or confirmed_start != start
        or confirmed_start_reference != start_reference
    ):
        raise ReportingBoundaryError(
            "Reporting identity or start marker changed during semantic validation"
        )
    verified_after, verified_after_data = _admit_record(
        paths.verified,
        identity.root,
        "verified-reporting",
    )
    if verified_after != verified or verified_after_data != verified_data:
        raise ReportingBoundaryError(
            "Verified reporting record changed during semantic validation"
        )
    return ReportingBoundaryOutcome(
        kind=admitted_kind,
        start_path=paths.start,
        verified_path=paths.verified,
        origin_workflow_attempt_id=str(identity.attempt["workflow_attempt_id"]),
        semantic_receipt_path=receipt_path,
        semantic_receipt_sha256=receipt_reference["sha256"],
        verified_report_locations=verified_report_locations,
    )


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Publish fixed reporting start/completion ledger records around one "
        "receipt-last reporting producer."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("start", "complete"):
        selected = subparsers.add_parser(operation)
        selected.add_argument("--kind", required=True, choices=REPORTING_KINDS)
        selected.add_argument("--run-root", required=True, type=Path)
        selected.add_argument("--execution", required=True, type=Path)
        selected.add_argument("--profile", required=True, type=Path)
        selected.add_argument("--workflow-attempt", required=True, type=Path)
        selected.add_argument("--workflow-config", required=True, type=Path)
        if operation == "complete":
            selected.add_argument("--receipt", required=True, type=Path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    arguments = parser.parse_args(argv)
    common = {
        "kind": arguments.kind,
        "run_root": arguments.run_root,
        "execution_path": arguments.execution,
        "profile_path": arguments.profile,
        "workflow_attempt_path": arguments.workflow_attempt,
        "workflow_config_path": arguments.workflow_config,
    }
    try:
        require_controlled_python_runtime()
        if arguments.operation == "start":
            outcome = publish_start(**common)
            print(f"Reporting start: {outcome.start_path}")
        else:
            outcome = publish_verified(receipt_path=arguments.receipt, **common)
            print(f"Verified reporting: {outcome.verified_path}")
    except (
        OSError,
        ReportingBoundaryError,
        SourceCheckoutError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = (
    "DEFAULT_REPORTING_BOUNDARY_OPS",
    "REPORTING_KINDS",
    "ReportingBoundaryError",
    "ReportingBoundaryOps",
    "ReportingBoundaryOutcome",
    "ReportingKind",
    "ReportingLedgerPaths",
    "SemanticTransaction",
    "SemanticValidator",
    "configure_parser",
    "ledger_paths",
    "main",
    "publish_start",
    "publish_verified",
    "validate_start",
    "validate_verified",
)
