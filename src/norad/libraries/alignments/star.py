"""Shared STAR-specific parse/validation helpers."""

from __future__ import annotations

import re


PERCENT_KEYS = {
    "Uniquely mapped reads %",
    "% of reads mapped to multiple loci",
    "% of reads mapped to too many loci",
}


def parse_final_log(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(text.splitlines(), start=1):
        if "|" not in raw:
            continue
        key, value = (part.strip() for part in raw.split("|", 1))
        if not key or not value or key in values:
            raise ValueError(f"Invalid STAR Log.final.out row at line {line_number}")
        values[key] = value
    if not values:
        raise ValueError("STAR Log.final.out contains no key/value rows")
    return values


def valid_mapping_summary(values: dict[str, str]) -> tuple[bool, str]:
    missing = sorted(PERCENT_KEYS - values.keys())
    if missing:
        return False, f"missing keys: {','.join(missing)}"
    parsed = []
    for key in sorted(PERCENT_KEYS):
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)%", values[key])
        if match is None:
            return False, f"invalid percentage for {key}"
        value = float(match.group(1))
        if not 0 <= value <= 100:
            return False, f"percentage outside 0..100 for {key}"
        parsed.append(f"{key}={value:g}%")
    return True, "; ".join(parsed)


def valid_splice_junction_table(text: str) -> tuple[bool, str]:
    count = 0
    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw:
            continue
        fields = raw.split("\t")
        if len(fields) != 9:
            return False, f"line {line_number} has {len(fields)} columns"
        try:
            start, end = int(fields[1]), int(fields[2])
            numeric = [int(value) for value in fields[3:]]
        except ValueError:
            return False, f"line {line_number} contains noninteger fields"
        if not fields[0] or start < 1 or end < start or any(value < 0 for value in numeric):
            return False, f"line {line_number} contains invalid coordinates/counts"
        count += 1
    return True, f"{count} splice-junction rows"
