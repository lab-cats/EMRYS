"""Explicit input parsing, immutable snapshots, and file guards."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import stat
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .. import _files
from .models import FileSnapshot, RunSummaryError, adapter, contracts


def parse_arguments(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic run summary from one complete NORAD "
            "artifact-adapter receipt. Dry-run is the default."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--artifact-receipt",
        required=True,
        type=Path,
        help="Exact completed artifact-adapter receipt TSV.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Artifact output root containing <run_id>/.",
    )
    parser.add_argument(
        "--science-review-summary",
        type=Path,
        help=(
            "Optional exact committed Step 09c review-summary TSV. It is "
            "never discovered automatically."
        ),
    )
    parser.add_argument(
        "--report-table-approvals",
        type=Path,
        help=(
            "Optional exact report-table approvals TSV. It is never "
            "discovered automatically and must be bound to this run and its "
            "explicit Step 09c scientific-review artifacts."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the four-file transaction; otherwise only validate.",
    )
    return parser.parse_args(argv)


def _fail(message: str) -> None:
    raise RunSummaryError(message)


def _resolved_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(Path(value).expanduser())))


def _require_regular_file(label: str, value: str | Path) -> Path:
    path = _resolved_path(value)
    try:
        metadata = path.lstat()
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(metadata.st_mode):
        _fail(f"{label} must not be a symbolic link: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        _fail(f"{label} is not a regular file: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} cannot be resolved: {path}: {exc}")
    if not resolved.is_file():
        _fail(f"{label} does not resolve to a regular file: {path}")
    return resolved


def _capture_file_snapshot(
    label: str,
    path: Path,
) -> tuple[bytes, FileSnapshot]:
    if path.is_symlink():
        _fail(f"{label} became a symbolic link: {path}")
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
                _fail(f"{label} is not a regular file: {path}")
            payload = stream.read()
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except OSError as exc:
        _fail(f"Could not capture {label} {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    sha256 = adapter.sha256_bytes(payload)
    states = before, after, current
    message = f"{label} changed while its immutable snapshot was captured: {path}"
    snapshot = _files.stable_snapshot(
        path, sha256, states, _fail, message, len(payload)
    )
    return payload, snapshot


def _verify_file_snapshot(label: str, expected: FileSnapshot) -> None:
    _payload, observed = _capture_file_snapshot(label, expected.path)
    if observed != expected:
        _fail(
            f"{label} changed after its immutable snapshot was captured: "
            f"{expected.path}"
        )


def _read_exact_tsv_bytes(
    *,
    label: str,
    path: Path,
    payload: bytes,
    header: Sequence[str],
    exact_rows: int | None = None,
) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(
            io.StringIO(text, newline=""),
            delimiter="\t",
            strict=True,
        )
        if tuple(reader.fieldnames or ()) != tuple(header):
            _fail(f"{label} has an invalid TSV header: {path}")
        rows = list(reader)
    except RunSummaryError:
        raise
    except (UnicodeError, csv.Error) as exc:
        _fail(f"Could not parse {label} {path}: {exc}")
    if exact_rows is not None and len(rows) != exact_rows:
        _fail(f"{label} must contain {exact_rows} rows; observed {len(rows)}: {path}")
    return rows


def _load_json_bytes(
    *,
    label: str,
    path: Path,
    payload: bytes,
) -> dict[str, Any]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=contracts.reject_duplicate_json_keys,
            parse_constant=contracts.reject_nonstandard_json_constant,
        )
    except contracts.ContractValidationError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"Could not parse {label} {path}: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label} must contain a JSON object: {path}")
    return value


def _reject_symlink_components(path: Path, label: str) -> None:
    _files.reject_symlink_components(path, label, _fail)


def _require_explicit_regular_file(
    label: str,
    value: str | Path,
) -> Path:
    try:
        contracts.validate_resolved_path(str(value), label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    lexical = _resolved_path(value)
    _reject_symlink_components(lexical, label)
    resolved = _require_regular_file(label, lexical)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved


def _require_contract_regular_file(
    label: str,
    value: str,
    *,
    source_root: Path,
) -> Path:
    try:
        contracts.validate_resolved_path(value, label)
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    declared = Path(value)
    lexical = (
        declared if declared.is_absolute() else source_root / declared
    ).absolute()
    _reject_symlink_components(lexical, label)
    resolved = _require_regular_file(label, lexical)
    if resolved != lexical:
        _fail(f"{label} must not traverse a symbolic link: {value}")
    return resolved


def _capture_report_table_snapshot(
    label: str,
    path: Path,
) -> tuple[FileSnapshot, int]:
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
                _fail(f"{label} is not a regular file: {path}")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            stream.seek(0)
            wrapper = io.TextIOWrapper(
                stream,
                encoding="utf-8",
                newline="",
            )
            try:
                reader = csv.reader(wrapper, delimiter="\t", strict=True)
                try:
                    header = next(reader)
                except StopIteration:
                    _fail(f"{label} is empty: {path}")
                if not header or any(not column for column in header):
                    _fail(f"{label} has a blank TSV header column: {path}")
                if len(header) != len(set(header)):
                    _fail(f"{label} has duplicate TSV header columns: {path}")
                row_count = 0
                for row_number, row in enumerate(reader, start=2):
                    if len(row) != len(header):
                        _fail(
                            f"{label} row {row_number} has {len(row)} fields; "
                            f"expected {len(header)}: {path}"
                        )
                    row_count += 1
            finally:
                wrapper.detach()
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except RunSummaryError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not inspect {label} {path}: {exc}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    sha256 = digest.hexdigest()
    states = before, after, current
    message = f"{label} changed while it was inspected: {path}"
    snapshot = _files.stable_snapshot(path, sha256, states, _fail, message)
    return (
        snapshot,
        row_count,
    )


def _verify_report_table_snapshot(expected: FileSnapshot) -> None:
    observed, _row_count = _capture_report_table_snapshot(
        "Approved report table",
        expected.path,
    )
    if observed != expected:
        _fail(
            "Approved report table changed after its immutable snapshot was "
            f"captured: {expected.path}"
        )
