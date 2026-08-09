"""Shared TSV validation helpers."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import TextIO, TypeVar

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
