"""Shared STAR-specific parse/validation helpers."""

from __future__ import annotations

import re
from pathlib import Path

from norad.libraries import validation as report
from norad.libraries.references import contigs as reference_contigs

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
        if (
            not fields[0]
            or start < 1
            or end < start
            or any(value < 0 for value in numeric)
        ):
            return False, f"line {line_number} contains invalid coordinates/counts"
        count += 1
    return True, f"{count} splice-junction rows"


def parse_parameters(path: Path) -> tuple[dict[str, list[str]], report.Snapshot]:
    text, snapshot = report.stable_text(path, "STAR genomeParameters")
    parsed: dict[str, list[str]] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) < 2:
            raise ValueError(f"STAR genomeParameters line {number} has no value")
        if fields[0] in parsed:
            raise ValueError(f"STAR genomeParameters repeats {fields[0]!r}")
        parsed[fields[0]] = fields[1:]
    return parsed, snapshot


def parse_fasta(path: Path) -> tuple[list[tuple[str, int]], report.Snapshot]:
    text, snapshot = report.stable_text(path, "Reference FASTA")
    try:
        contigs = reference_contigs.parse_fasta_lines(text.splitlines())
    except reference_contigs.ReferenceContigError as exc:
        raise ValueError(str(exc))
    return contigs, snapshot


def parse_star_index_contigs(
    index_dir: Path,
) -> tuple[list[tuple[str, int]], tuple[report.Snapshot, report.Snapshot]]:
    names_text, names_snapshot = report.stable_text(
        index_dir / "chrName.txt", "STAR chrName"
    )
    lengths_text, lengths_snapshot = report.stable_text(
        index_dir / "chrLength.txt", "STAR chrLength"
    )
    names = names_text.splitlines()
    lengths = lengths_text.splitlines()
    if not names or len(names) != len(lengths) or len(names) != len(set(names)):
        raise ValueError(
            "STAR chrName/chrLength rows are empty, duplicate, or misaligned"
        )
    try:
        parsed = [
            (name, int(length)) for name, length in zip(names, lengths, strict=True)
        ]
    except ValueError as exc:
        raise ValueError(f"STAR chrLength contains a non-integer: {exc}") from exc
    if any(not name or length <= 0 for name, length in parsed):
        raise ValueError("STAR contig names and lengths must be nonempty and positive")
    return parsed, (names_snapshot, lengths_snapshot)
