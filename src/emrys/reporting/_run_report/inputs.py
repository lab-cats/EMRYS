"""Explicit input resolution and stable snapshots for run-report rendering."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

from emrys.contracts.artifacts import api as contracts
from emrys.reporting import _files

from .models import (
    CANDIDATE_TERMINOLOGY,
    INTERPRETATION_BOUNDARY,
    MODULE_RUN_SUMMARY_SCHEMA_VERSION,
    RUN_SUMMARY_SCHEMA_VERSION,
    FileSnapshot,
    ReportRenderError,
)


def _fail(message: str) -> None:
    raise ReportRenderError(message)


def _explicit_path(path: Path, label: str) -> Path:
    try:
        contracts.validate_resolved_path(str(path), label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    return path.absolute()


def _reject_symlink_components(path: Path, label: str) -> None:
    _files.reject_symlink_components(path, label, _fail)


def _snapshot_regular(
    path: Path,
    label: str,
    *,
    executable: bool = False,
) -> FileSnapshot:
    path = _explicit_path(path, label)
    _reject_symlink_components(path, label)
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                _fail(f"{label} must be a regular non-symlink file: {path}")
            if executable and not before.st_mode & stat.S_IXUSR:
                _fail(f"{label} is not executable: {path}")
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except ReportRenderError:
        raise
    except OSError as exc:
        _fail(f"Could not inspect and hash {label} {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    sha256 = digest.hexdigest()
    states = before, after, current
    message = f"{label} changed while its snapshot was captured: {path}"
    return _files.stable_snapshot(path, sha256, states, _fail, message)


def _assert_snapshot(snapshot: FileSnapshot, label: str) -> None:
    current = _snapshot_regular(snapshot.path, label)
    if current != snapshot:
        _fail(f"{label} changed during report rendering: {snapshot.path}")


def _assert_snapshot_identity(snapshot: FileSnapshot, label: str) -> None:
    """Recheck an already hash-bound large input without rereading its contents."""

    path = _explicit_path(snapshot.path, label)
    _reject_symlink_components(path, label)
    try:
        current = path.lstat()
    except OSError as exc:
        _fail(f"Could not recheck {label} {path}: {exc}")
    observed = (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_ctime_ns,
    )
    expected = (
        snapshot.device,
        snapshot.inode,
        snapshot.size_bytes,
        snapshot.mtime_ns,
        snapshot.ctime_ns,
    )
    if (
        stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
        or observed != expected
    ):
        _fail(f"{label} changed during report rendering: {path}")


def _assert_input_recheck(
    snapshot: FileSnapshot,
    label: str,
    rehash_content: bool,
) -> None:
    if rehash_content:
        _assert_snapshot(snapshot, label)
    else:
        _assert_snapshot_identity(snapshot, label)


def _load_run_summary(path: Path, *, source_root: Path) -> dict[str, Any]:
    try:
        document = contracts.load_json_object(path, "run-summary document")
        version = str(document.get("schema_version", ""))
        errors = sorted(
            contracts.schema_validator("run-summary", version).iter_errors(
                document
            ),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            detail = "\n".join(
                f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
                for error in errors
            )
            _fail(f"run-summary document failed validation: {path}\n{detail}")
        contracts.validate_run_summary_semantics(document, source_root=source_root)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    if document["schema_version"] not in {
        RUN_SUMMARY_SCHEMA_VERSION,
        MODULE_RUN_SUMMARY_SCHEMA_VERSION,
    }:
        _fail(f"Unsupported run-summary schema version: {document['schema_version']!r}")
    if (
        document["schema_version"] == RUN_SUMMARY_SCHEMA_VERSION
        and document["candidate_terminology"] != CANDIDATE_TERMINOLOGY
    ):
        _fail(
            "Run summary does not use the required candidate terminology: "
            f"{CANDIDATE_TERMINOLOGY}"
        )
    if (
        document["schema_version"] == RUN_SUMMARY_SCHEMA_VERSION
        and document["interpretation_boundary"] != INTERPRETATION_BOUNDARY
    ):
        _fail(
            "Run summary uses an unsupported interpretation boundary: "
            f"{document['interpretation_boundary']!r}"
        )
    return document


def _resolve_contract_file(value: str, label: str, *, source_root: Path) -> Path:
    try:
        contracts.validate_resolved_path(value, label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    declared = Path(value)
    lexical = (
        declared if declared.is_absolute() else source_root / declared
    ).absolute()
    _reject_symlink_components(lexical, label)
    resolved = contracts.resolve_contract_path(value, source_root=source_root)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved
