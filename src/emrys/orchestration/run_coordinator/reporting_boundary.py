"""Immutable start/completion boundary for fixed reporting transactions."""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.artifact_inventory import report_output_root
from emrys.contracts.orchestration.application_model import (
    RUN_BINDING_SCHEMA_VERSION,
    AnalysisRevision,
)
from emrys.contracts.orchestration.projection import (
    CONTRACT_PATHS,
    build_reporting_bundle,
)
from emrys.libraries.exclusive_publication import publish_exclusive
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    attest_source_checkout,
)
from emrys.libraries.validation.errors import ValidationError
from emrys.libraries.validation.inputs import (
    directory_entries_with_identity,
    read_bytes_with_identity,
)
from emrys.orchestration.run_coordinator._inspection_admission import (
    InspectionError,
    admit_attempt_run_lock,
    admit_canonical_record,
    admit_execution_path,
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
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
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
    if tuple(output_id for output_id, _path in admitted) != expected_ids or any(
        not isinstance(path, Path) or not path.is_absolute() for _, path in admitted
    ):
        raise ReportingBoundaryError(
            "Validated HTML report transaction lacks both exact verified result locations"
        )
    return admitted


SemanticValidator = Callable[..., SemanticTransaction]


@dataclass(frozen=True, slots=True)
class ReportingLedgerPaths:
    """The only state paths owned by one reporting kind."""

    root: Path
    start: Path
    verified: Path


@dataclass(frozen=True, slots=True)
class ReportingLedgerAdmission:
    """Already-admitted reporting records and semantic result locations."""

    origin_workflow_attempt_id: str
    start_reference: dict[str, str]
    verified_reference: dict[str, str] | None = None
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
    config: dict[str, Any]
    execution_sha256: str
    profile_sha256: str
    attempt_reference: dict[str, str]
    config_reference: dict[str, str]
    run_lock_reference: dict[str, str]


def _validate_semantic_receipt(
    kind: str,
    receipt_path: Path,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    attempt: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    read: bool = False,
    validated_predecessor: SemanticTransaction | None = None,
) -> SemanticTransaction:
    from emrys.reporting.transaction_validation import validate_receipt  # noqa: PLC0415

    return validate_receipt(
        kind,
        receipt_path,
        run_root,
        execution,
        profile,
        attempt,
        config,
        historical_read=(
            read
            and report_output_root(run_root, profile)
            == run_root / "products" / "report"
        ),
        validated_predecessor=validated_predecessor,
    )


_semantic_validator = partial(_validate_semantic_receipt, read=False)
validate_read_semantic_receipt = partial(_validate_semantic_receipt, read=True)


def semantic_validator_session(*, read: bool) -> SemanticValidator:
    """Reuse only the immediately preceding transaction in one fixed sequence."""

    predecessor: SemanticTransaction | None = None

    def validate(*args: Any) -> SemanticTransaction:
        nonlocal predecessor
        predecessor = _validate_semantic_receipt(
            *args, read=read, validated_predecessor=predecessor
        )
        return predecessor

    return validate


def _publish_exclusive(path: Path, data: bytes) -> None:
    publish_exclusive(
        path,
        data,
        ReportingBoundaryError,
        existing=f"Refusing to replace reporting ledger state: {path}",
    )


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
    try:
        if path.resolve(strict=True) != path:
            raise ReportingBoundaryError(
                f"{label} must be a canonical regular file: {path}"
            )
        return read_bytes_with_identity(
            path,
            label,
            nonempty=False,
        )[0]
    except (OSError, ValidationError) as exc:
        raise ReportingBoundaryError(f"Could not admit {label}: {path}: {exc}") from exc


_admit_record = partial(
    admit_canonical_record,
    read_bytes=_read_bound,
    error_type=ReportingBoundaryError,
)
_admit_execution = partial(
    admit_execution_path,
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


def _reporting_relative(relative: str, attempt_id: object | None) -> str:
    if attempt_id is None:
        return relative
    return f"contract/reporting-inputs/{attempt_id}/{Path(relative).name}"


def _admit_reporting_projection(
    *,
    root: Path,
    execution: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    successor = execution.get("schema_version") == RUN_BINDING_SCHEMA_VERSION
    projection = None if successor else execution["reporting_projection"]
    if projection is not None and set(projection) != set(CONTRACT_PATHS):
        raise ReportingBoundaryError(
            "Execution reporting projection does not use the fixed complete roster"
        )
    for name, relative in CONTRACT_PATHS.items():
        expected_relative = _reporting_relative(
            relative,
            config.get("workflow_attempt_id") if successor else None,
        )
        reference = config.get(f"{name}_path") if successor else projection[name]
        if successor and (
            not isinstance(reference, Mapping)
            or set(reference) != {"path", "sha256"}
            or not all(isinstance(value, str) for value in reference.values())
        ):
            raise ReportingBoundaryError(
                f"Workflow config does not bind exact reporting projection {name}"
            )
        assert isinstance(reference, Mapping)
        if reference["path"] != expected_relative:
            raise ReportingBoundaryError(
                f"Reporting projection {name} does not use its fixed path"
            )
        path = root / expected_relative
        if not successor and config.get(f"{name}_path") != str(path):
            raise ReportingBoundaryError(
                f"Workflow config does not bind reporting projection {name}"
            )
        data = _read_bound(path, root, f"reporting projection {name}")
        if hashlib.sha256(data).hexdigest() != reference["sha256"]:
            raise ReportingBoundaryError(
                f"Reporting projection {name} bytes differ from "
                f"{'workflow config' if successor else 'execution'} identity"
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


def _attempt_reporting_materialization(
    source: Mapping[str, Any],
    profile: Mapping[str, Any],
    run_root: Path,
    *,
    analysis: AnalysisRevision | None = None,
    attempt_id: str | None = None,
    processing_source_root: Path | None = None,
) -> tuple[
    tuple[tuple[Path, bytes], ...],
    dict[str, Any],
    tuple[Path, ...],
]:
    """Project identity-neutral reporting inputs for one Attempt adapter."""

    reporting = build_reporting_bundle(
        source,
        profile,
        analysis,
        processing_source_root,
    )
    projection_data = {
        "reference_contract": reporting.reference_contract_bytes,
        "primary_analysis_policy": reporting.primary_analysis_policy_bytes,
        "reporting_run_contract": reporting.reporting_run_contract_bytes,
        "artifact_inventory": reporting.artifact_inventory_bytes,
    }
    files: list[tuple[Path, bytes]] = []
    config: dict[str, Any] = {}
    successor = analysis is not None
    references = (
        reporting.projection_references if successor else source["reporting_projection"]
    )
    for name in CONTRACT_PATHS:
        reference = dict(references[name])
        if successor:
            reference["path"] = _reporting_relative(reference["path"], attempt_id)
        path = run_root / str(reference["path"])
        files.append((path, projection_data[name]))
        config[f"{name}_path"] = reference if successor else str(path)
    directories = (
        run_root / "products" / "artifact-summary",
        report_output_root(run_root, profile),
    )
    return tuple(files), config, directories


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

    try:
        entries = set(
            directory_entries_with_identity(
                paths.root,
                "Reporting ledger directory",
            )[0]
        )
    except ValidationError as exc:
        raise ReportingBoundaryError(
            f"Could not admit reporting ledger directory: {paths.root}: {exc}"
        ) from exc
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
    require_publishable_attempt: bool,
    attest_source: Callable[..., Any] = attest_source_checkout,
) -> _AdmittedIdentity:
    root = _canonical_root(run_root)
    expected_profile = root / "contract" / "profile.json"
    allowed = {root / "contract" / name for name in ("normalized.json", "run.json")}
    if profile_path != expected_profile or execution_path not in allowed:
        raise ReportingBoundaryError(
            "Reporting identity must use the fixed execution/profile contract paths"
        )
    profile, profile_data = _admit_record(profile_path, root, "profile")
    execution, execution_data, _authority = _admit_execution(
        execution_path,
        root,
        profile,
    )
    name = (
        "run.json"
        if execution["schema_version"] == RUN_BINDING_SCHEMA_VERSION
        else "normalized.json"
    )
    expected_execution = root / "contract" / name
    if execution_path != expected_execution:
        raise ReportingBoundaryError(
            "Reporting execution schema does not use its fixed contract path"
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
    if require_publishable_attempt:
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
        require_active=False,
    )
    if require_publishable_attempt:
        receipt_path = workflow_attempt_path.with_name("attempt-receipt.json")
        receipt, _receipt_data = _admit_record(
            receipt_path,
            root,
            "attempt-receipt",
        )
        if (
            receipt.get("schema_version") != "emrys.attempt-receipt.v2"
            or receipt.get("status") != "succeeded"
        ):
            raise ReportingBoundaryError(
                "New reporting publication requires a successful terminal v2 Attempt"
            )
    return _AdmittedIdentity(
        root=root,
        execution=execution,
        profile=profile,
        attempt=attempt,
        config=config,
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
) -> None:
    """Publish the immutable marker immediately before one reporting producer."""

    admitted_kind = _kind(kind)
    identity = _admit_identity(
        run_root=run_root,
        execution_path=execution_path,
        profile_path=profile_path,
        workflow_attempt_path=workflow_attempt_path,
        workflow_config_path=workflow_config_path,
        require_publishable_attempt=True,
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
        require_publishable_attempt=True,
        attest_source=ops.attest_source_checkout,
    )
    if confirmed != identity:
        raise ReportingBoundaryError(
            "Reporting orchestration identity changed before start publication"
        )
    ops.publish_bytes(paths.start, orchestration_contracts.canonical_json_bytes(record))


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
    before_publication: Callable[[], None] | None = None,
) -> tuple[tuple[str, Path], ...]:
    """Semantically validate a completed transaction and publish proof last."""

    admitted_kind = _kind(kind)
    identity = _admit_identity(
        run_root=run_root,
        execution_path=execution_path,
        profile_path=profile_path,
        workflow_attempt_path=workflow_attempt_path,
        workflow_config_path=workflow_config_path,
        require_publishable_attempt=True,
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
            identity.config,
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
        require_publishable_attempt=True,
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
            require_active=False,
        )
        != identity.run_lock_reference
    ):
        raise ReportingBoundaryError(
            "Reporting run-lock identity changed before completion publication"
        )
    if before_publication is not None:
        before_publication()
    ops.publish_bytes(
        paths.verified, orchestration_contracts.canonical_json_bytes(record)
    )
    return verified_report_locations


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
    name = (
        "run.json" if (root / "contract" / "run.json").exists() else "normalized.json"
    )
    identity = _admit_identity(
        run_root=root,
        execution_path=root / "contract" / name,
        profile_path=root / "contract" / "profile.json",
        workflow_attempt_path=attempt_path,
        workflow_config_path=config_path,
        require_publishable_attempt=False,
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
) -> ReportingLedgerAdmission:
    """Admit an entered reporting scope and retain its immutable reference."""

    admitted_kind = _kind(kind)
    identity, _start, start_reference = _identity_from_origin(
        admitted_kind,
        run_root,
        execution,
        profile,
    )
    return ReportingLedgerAdmission(
        str(identity.attempt["workflow_attempt_id"]), start_reference
    )


def validate_verified(
    kind: str,
    run_root: Path,
    execution: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    semantic_validator: SemanticValidator = validate_read_semantic_receipt,
) -> ReportingLedgerAdmission:
    """Admit a verified ledger and retain its immutable references."""

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
            identity.config,
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
    return ReportingLedgerAdmission(
        str(identity.attempt["workflow_attempt_id"]),
        start_reference,
        _reference(paths.verified, identity.root, verified_data),
        verified_report_locations,
    )


__all__ = (
    "DEFAULT_REPORTING_BOUNDARY_OPS",
    "REPORTING_KINDS",
    "ReportingBoundaryError",
    "ReportingBoundaryOps",
    "ReportingKind",
    "ReportingLedgerAdmission",
    "ReportingLedgerPaths",
    "SemanticTransaction",
    "SemanticValidator",
    "ledger_paths",
    "publish_start",
    "publish_verified",
    "validate_read_semantic_receipt",
    "validate_start",
    "validate_verified",
)
