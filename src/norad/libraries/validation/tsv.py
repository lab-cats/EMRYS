"""Shared TSV validation helpers."""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from norad.libraries.validation.report import clean


T = TypeVar("T")


def read_header(path: Path) -> tuple[str, ...]:
    """Return the first row of a TSV file as a header tuple."""
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(next(csv.reader(stream, delimiter="\t")))


def attempt(
    function: Callable[[], T],
    catches: tuple[type[BaseException], ...] = (OSError, UnicodeError, csv.Error),
) -> tuple[T | None, str]:
    try:
        return function(), "validated"
    except catches as exc:
        return None, clean(exc)
