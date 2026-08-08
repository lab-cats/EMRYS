"""Shared TSV validation helpers."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from norad.libraries.validation.report import clean

T = TypeVar("T")


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
