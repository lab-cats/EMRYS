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

ORIENTATIONS = ("FWD_like", "REV_like")
ORIENTATION_PREFIXES = tuple(
    orientation.split("_")[0].lower() for orientation in ORIENTATIONS
)
MECHANICAL_ORIENTATION_FLAG_GROUPS = {
    ORIENTATIONS[0]: ("99", "147"),
    ORIENTATIONS[1]: ("83", "163"),
}
REQUIRED_ORIENTATIONS = frozenset(ORIENTATIONS)
LEGACY_PROVISIONAL_ORIENTATION_POLICY = "legacy_provisional_v1"


def infer_orientation_from_path(path: Path | str) -> str | None:
    filename = Path(path).name
    for orientation in ORIENTATIONS:
        if f".{orientation}." in filename:
            return orientation
    return None


def validate_legacy_orientation_policy(value: str) -> tuple[bool, str]:
    if value == LEGACY_PROVISIONAL_ORIENTATION_POLICY:
        return True, "orientation_policy=legacy_provisional_v1"
    return False, f"unsupported orientation_policy={value!r}; expected legacy_provisional_v1"


def mechanical_like_count_detail(
    values: dict[str, int | float], orientation: str
) -> tuple[bool, str]:
    if orientation not in ORIENTATIONS:
        return False, f"unsupported orientation={orientation!r}"
    like_field = f"{orientation.lower()}_records"
    left_field = (
        f"flag_{MECHANICAL_ORIENTATION_FLAG_GROUPS[orientation][0]}_records"
    )
    right_field = (
        f"flag_{MECHANICAL_ORIENTATION_FLAG_GROUPS[orientation][1]}_records"
    )
    left_value = values.get(left_field)
    right_value = values.get(right_field)
    like_value = values.get(like_field)
    return (
        left_value is not None and right_value is not None and like_value is not None
        and left_value + right_value == like_value,
        f"{left_value}+{right_value}={like_value}",
    )


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
