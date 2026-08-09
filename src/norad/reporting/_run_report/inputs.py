"""Explicit input resolution and stable snapshots for run-report rendering."""

from __future__ import annotations

import csv
import hashlib
import os
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import validate_artifact_contracts as contracts
from norad.reporting import _files

from .models import (
    CANDIDATE_TERMINOLOGY,
    RUN_SUMMARY_SCHEMA_VERSION,
    SCIENCE_BANNERS,
    ApprovedTable,
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
    current = _snapshot_regular(
        snapshot.path,
        label,
        executable=(label == "Quarto executable"),
    )
    if current != snapshot:
        _fail(f"{label} changed during report rendering: {snapshot.path}")
def _load_run_summary(path: Path) -> dict[str, Any]:
    try:
        document = contracts.load_json_object(path, "run-summary document")
        errors = contracts.schema_errors("run-summary", document)
        if errors:
            detail = "\n".join(
                f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
                for error in errors
            )
            _fail(f"run-summary document failed validation: {path}\n{detail}")
        contracts.validate_run_summary_semantics(document)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    if document["schema_version"] != RUN_SUMMARY_SCHEMA_VERSION:
        _fail(f"Unsupported run-summary schema version: {document['schema_version']!r}")
    if document["candidate_terminology"] != CANDIDATE_TERMINOLOGY:
        _fail(
            "Run summary does not use the required candidate terminology: "
            f"{CANDIDATE_TERMINOLOGY}"
        )
    if document["science_status"] not in SCIENCE_BANNERS:
        _fail(
            "Run summary uses an unauthorized scientific state: "
            f"{document['science_status']!r}"
        )
    return document
def _resolve_contract_file(value: str, label: str) -> Path:
    try:
        contracts.validate_resolved_path(value, label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    declared = Path(value)
    lexical = (
        declared if declared.is_absolute() else contracts.REPO_ROOT / declared
    ).absolute()
    _reject_symlink_components(lexical, label)
    resolved = contracts.resolve_contract_path(value)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved
def _read_approved_table(record: Mapping[str, Any]) -> ApprovedTable:
    table_id = record["table_id"]
    path = _resolve_contract_file(
        record["path"],
        f"approved report table {table_id!r}",
    )
    snapshot = _snapshot_regular(
        path,
        f"approved report table {table_id!r}",
    )
    if snapshot.sha256 != record["sha256"]:
        _fail(
            f"Approved report table {table_id!r} SHA-256 mismatch: observed "
            f"{snapshot.sha256}; expected {record['sha256']}"
        )

    display_limit = record["display_row_limit"]
    header: tuple[str, ...] | None = None
    displayed: list[tuple[str, ...]] = []
    row_count = 0
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            try:
                raw_header = next(reader)
            except StopIteration:
                _fail(f"Approved report table {table_id!r} is empty: {path}")
            if not raw_header or any(not column for column in raw_header):
                _fail(f"Approved report table {table_id!r} has a blank header column")
            if len(raw_header) != len(set(raw_header)):
                _fail(
                    f"Approved report table {table_id!r} has duplicate header columns"
                )
            header = tuple(raw_header)
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    _fail(
                        f"Approved report table {table_id!r} row {row_number} "
                        f"has {len(row)} fields; expected {len(header)}"
                    )
                row_count += 1
                if display_limit is None or len(displayed) < display_limit:
                    displayed.append(tuple(row))
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not parse approved report table {table_id!r}: {exc}")

    if row_count != record["row_count"]:
        _fail(
            f"Approved report table {table_id!r} row-count mismatch: observed "
            f"{row_count}; expected {record['row_count']}"
        )
    _assert_snapshot(snapshot, f"approved report table {table_id!r}")
    assert header is not None
    return ApprovedTable(
        table_id=table_id,
        artifact_id=record["artifact_id"],
        role=record["role"],
        title=record["title"],
        path=path,
        sha256=snapshot.sha256,
        row_count=row_count,
        display_row_limit=display_limit,
        approval_policy_version=record["approval"]["policy_version"],
        approved_by=record["approval"]["approved_by"],
        approved_at=record["approval"]["approved_at"],
        header=header,
        display_rows=tuple(displayed),
        snapshot=snapshot,
    )
