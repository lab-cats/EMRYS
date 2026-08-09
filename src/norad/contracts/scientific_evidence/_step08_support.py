"""Shared parsing and file support for the Step 08 contract."""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TypeVar

from norad.contracts.scientific_evidence._step08_definitions import (
    NA_VALUE,
    SAFE_ID_RE,
    SHA256_RE,
    ContractError,
    Table,
)
from norad.libraries import validation as report
from norad.libraries.validation.tsv import read_strict_tsv

T = TypeVar("T")


def fail(message: str) -> None:
    raise ContractError(message)


def attempt(function: Callable[[], T]) -> tuple[T | None, str]:
    """Normalize the parser failures shared by Step 08 and Step 09 CLIs."""
    return report.attempt(
        function, catches=(OSError, UnicodeError, csv.Error, ContractError)
    )


def sample_block_header(
    base: Sequence[str], sample_ids: Sequence[str]
) -> tuple[str, ...]:
    """Append ordered DP, AD, and AF sample blocks to a fixed header."""
    return tuple(base) + tuple(
        f"{prefix}__{sample}" for prefix in ("DP", "AD", "AF") for sample in sample_ids
    )


def validate_safe_id(label: str, value: str) -> None:
    if not SAFE_ID_RE.fullmatch(value):
        fail(f"{label} must match [A-Za-z0-9][A-Za-z0-9._-]*; got: {value}")


def validate_enum(label: str, value: str, allowed: Sequence[str]) -> None:
    if value not in allowed:
        fail(f"{label} must be one of {', '.join(allowed)}; got: {value}")


def parse_nonnegative_int(label: str, value: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        fail(f"{label} must be a non-negative integer; got: {value}")
    return int(value)


def parse_number(
    label: str, value: str, *, allow_na: bool = False, nonnegative: bool = False
) -> float | None:
    if allow_na and value == NA_VALUE:
        return None
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label} must be numeric; got: {value}")
    if not math.isfinite(parsed):
        fail(f"{label} must be finite; got: {value}")
    if nonnegative and parsed < 0:
        fail(f"{label} must be non-negative; got: {value}")
    return parsed


def values_close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=1.5e-8, abs_tol=1.5e-8)


def sha256_file(path: Path) -> str:
    try:
        return report.sha256_file(path)
    except OSError as exc:
        fail(f"Could not hash {path}: {exc}")


def require_file(label: str, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        fail(f"{label} does not exist or is not a regular file: {path}")
    if path.stat().st_size == 0:
        fail(f"{label} is empty: {path}")
    return path.resolve()


def read_tsv(
    label: str,
    value: str | Path,
    expected_header: Sequence[str] | None = None,
) -> Table:
    path = require_file(label, value)
    header, rows = read_strict_tsv(label, path, expected_header, fail)
    return Table(header=header, rows=rows, path=path)


def ensure_unique(rows: Sequence[Mapping[str, str]], column: str, label: str) -> None:
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        value = row[column]
        if not value:
            fail(f"{label} row {row_number} has an empty {column}.")
        if value in seen:
            fail(f"{label} contains duplicate {column}: {value}")
        seen.add(value)


def require_text(label: str, value: str, *, allow_na: bool = False) -> None:
    if allow_na and value == NA_VALUE:
        return
    if not value or value.strip() != value:
        fail(f"{label} must be non-empty and have no surrounding whitespace.")


def validate_hash(label: str, value: str) -> None:
    if not SHA256_RE.fullmatch(value):
        fail(f"{label} must be a lowercase SHA-256 value; got: {value}")
