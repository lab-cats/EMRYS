"""Shared BED12 validation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from emrys.libraries import validation as report


def parse_bed12(path: Path) -> tuple[list[tuple[str, ...]], report.Snapshot]:
    text, snapshot = report.stable_text(path, "BED12")
    rows: list[tuple[str, ...]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        fields = tuple(raw.split("\t"))
        if len(fields) != 12:
            report.fail(f"BED12 row {number} must contain exactly 12 columns")
        rows.append(fields)
    if not rows:
        report.fail("BED12 must contain at least one row")
    return rows, snapshot


def inspect_bed12_rows(
    rows: Sequence[tuple[str, ...]],
) -> tuple[bool, bool, bool, bool]:
    structural = True
    blocks_valid = True
    unique_names = True
    parsed_keys: list[tuple[str, int, int, str]] = []
    names: set[str] = set()
    for fields in rows:
        try:
            start = int(fields[1])
            end = int(fields[2])
            thick_start = int(fields[6])
            thick_end = int(fields[7])
            count = int(fields[9])
            sizes = tuple(int(value) for value in fields[10].rstrip(",").split(","))
            starts = tuple(int(value) for value in fields[11].rstrip(",").split(","))
        except ValueError:
            structural = False
            continue
        if (
            not fields[0]
            or not fields[3]
            or fields[4] != "0"
            or fields[5] not in {"+", "-", "."}
            or start < 0
            or end <= start
            or thick_start != start
            or thick_end != end
            or fields[8] != "0"
            or count <= 0
        ):
            structural = False
        if (
            len(sizes) != count
            or len(starts) != count
            or any(size <= 0 for size in sizes)
            or any(offset < 0 for offset in starts)
            or tuple(sorted(starts)) != starts
            or any(
                offset + size > end - start
                for offset, size in zip(starts, sizes, strict=False)
            )
            or starts[0] != 0
            or starts[-1] + sizes[-1] != end - start
        ):
            blocks_valid = False
        if fields[3] in names:
            unique_names = False
        names.add(fields[3])
        parsed_keys.append((fields[0], start, end, fields[3]))
    sorted_rows = structural and parsed_keys == sorted(parsed_keys)
    return structural, sorted_rows, blocks_valid, unique_names
