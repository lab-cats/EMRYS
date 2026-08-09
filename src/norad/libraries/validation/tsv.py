"""Shared TSV validation helpers."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import NoReturn, TextIO, TypeVar

from norad.libraries.validation.report import clean

T = TypeVar("T")


def write_rows(
    stream: TextIO,
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> None:
    """Write rows with the deterministic TSV dialect used by NORAD contracts."""
    writer = csv.DictWriter(
        stream,
        fieldnames=list(header),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    """Serialize deterministic UTF-8 TSV bytes without platform newlines."""
    stream = StringIO(newline="")
    write_rows(stream, header, rows)
    return stream.getvalue().encode("utf-8")


def read_header(path: Path) -> tuple[str, ...]:
    """Return the first row of a TSV file as a header tuple."""
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(next(csv.reader(stream, delimiter="\t")))


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a TSV into a header list and row dictionaries."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def read_strict_tsv(
    label: str,
    path: Path,
    expected_header: Sequence[str] | None,
    fail: Callable[[str], NoReturn],
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Parse a validated path with NORAD's strict tabular diagnostics."""
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            raw_rows = list(csv.reader(stream, delimiter="\t", strict=True))
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")
    if not raw_rows:
        fail(f"{label} is empty: {path}")
    header = tuple(raw_rows[0])
    if any(not column for column in header):
        fail(f"{label} contains an empty header field: {path}")
    if len(header) != len(set(header)):
        fail(f"{label} contains duplicate header fields: {path}")
    if expected_header is not None and header != tuple(expected_header):
        fail(
            f"{label} header is invalid: {path}\n"
            f"Expected: {' | '.join(expected_header)}\n"
            f"Observed: {' | '.join(header)}"
        )
    rows: list[dict[str, str]] = []
    for index, values in enumerate(raw_rows[1:], start=2):
        if len(values) != len(header):
            fail(
                f"{label} row {index} has {len(values)} fields; "
                f"expected {len(header)}: {path}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    return header, rows


def sha256_file(path: Path) -> str:
    """Compute a stable SHA-256 digest for the file contents."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def attempt(
    function: Callable[[], T],
    catches: tuple[type[BaseException], ...] = (OSError, UnicodeError, csv.Error),
) -> tuple[T | None, str]:
    try:
        return function(), "validated"
    except catches as exc:
        return None, clean(exc)
