"""Shared Picard metrics parsing helpers."""

from __future__ import annotations

from collections.abc import Iterable
from math import isfinite


def duplication_metrics_row(lines: Iterable[str]) -> dict[str, str]:
    """Read the single first Picard table while consuming the complete input."""
    table: list[str] = []
    ended = False
    for line in lines:
        if not line or line.startswith("#"):
            ended = bool(table)
        elif not ended and len(table) < 3:
            table.append(line)

    if len(table) < 2:
        raise ValueError("missing metrics header/data row")
    header = table[0].split("\t")
    values = table[1].split("\t")
    if len(header) != len(set(header)):
        raise ValueError("duplicate Picard metric columns")
    required = {
        "LIBRARY",
        "READ_PAIRS_EXAMINED",
        "READ_PAIR_DUPLICATES",
        "PERCENT_DUPLICATION",
    }
    if not required <= set(header) or len(table) != 2 or len(values) != len(header):
        raise ValueError("expected one row with required Picard columns")
    return dict(zip(header, values, strict=True))


def parse_duplication_metrics(text: str) -> tuple[bool, str]:
    try:
        values = duplication_metrics_row(text.splitlines())
    except ValueError as exc:
        return False, str(exc)
    try:
        examined = int(values["READ_PAIRS_EXAMINED"])
        duplicates = int(values["READ_PAIR_DUPLICATES"])
        fraction = float(values["PERCENT_DUPLICATION"])
    except ValueError:
        return False, "non-numeric duplication metric"
    valid = (
        bool(values["LIBRARY"])
        and examined >= 0
        and 0 <= duplicates <= examined
        and isfinite(fraction)
        and 0 <= fraction <= 1
    )
    return valid, (
        f"library={values['LIBRARY']} pairs={examined} "
        f"duplicates={duplicates} fraction={fraction:.12g}"
    )
