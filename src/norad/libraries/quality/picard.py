"""Shared Picard metrics parsing helpers."""

from __future__ import annotations

from math import isfinite


def parse_duplication_metrics(text: str) -> tuple[bool, str]:
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    if len(lines) < 2:
        return False, "missing metrics header/data row"
    header = lines[0].split("\t")
    rows = [line.split("\t") for line in lines[1:]]
    required = {
        "LIBRARY",
        "READ_PAIRS_EXAMINED",
        "READ_PAIR_DUPLICATES",
        "PERCENT_DUPLICATION",
    }
    if not required <= set(header) or len(rows) != 1 or len(rows[0]) != len(header):
        return False, "expected one row with required Picard columns"
    values = dict(zip(header, rows[0], strict=True))
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
