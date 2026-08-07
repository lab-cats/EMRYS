"""Shared alignment-orientation validation helpers."""

from __future__ import annotations

import math
import csv
from pathlib import Path

from norad.libraries import validation as report

COUNTS_HEADER = (
    "sample_id", "input_records", "flag_99_records", "flag_147_records",
    "flag_83_records", "flag_163_records", "fwd_like_records",
    "rev_like_records", "assigned_records", "unassigned_records",
    "assigned_fraction",
)

LEGACY_PROVISIONAL_ORIENTATION_POLICY = "legacy_provisional_v1"


def validate_legacy_orientation_policy(value: str) -> tuple[bool, str]:
    if value == LEGACY_PROVISIONAL_ORIENTATION_POLICY:
        return True, "orientation_policy=legacy_provisional_v1"
    return False, f"unsupported orientation_policy={value!r}; expected legacy_provisional_v1"


def read_orientation_counts(
    path: Path, scope_id: str
) -> tuple[dict[str, int | float], str]:
    try:
        header, rows = report.read_tsv(path)
    except (OSError, UnicodeError, csv.Error) as exc:
        return {}, report.clean(exc)
    if tuple(header) != COUNTS_HEADER:
        return {}, "header mismatch"
    if len(rows) != 1 or rows[0]["sample_id"] != scope_id:
        return {}, "expected one row for the declared sample"
    values: dict[str, int | float] = {}
    try:
        for key in COUNTS_HEADER[1:-1]:
            value = int(rows[0][key])
            if value < 0:
                raise ValueError
            values[key] = value
        fraction = float(rows[0]["assigned_fraction"])
        if not math.isfinite(fraction) or not 0 <= fraction <= 1:
            raise ValueError
        values["assigned_fraction"] = fraction
    except ValueError:
        return {}, "counts must be nonnegative integers and fraction in 0..1"
    return values, "one typed sample row"
