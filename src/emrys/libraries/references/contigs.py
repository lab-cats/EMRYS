"""Ordered FASTA, FAI, and DICT contig/length parsers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path


class ReferenceContigError(RuntimeError):
    """Raised when a reference contig source violates the parser contract."""


def _fail(message: str) -> None:
    raise ReferenceContigError(message)


def parse_fasta(path: Path) -> list[tuple[str, int]]:
    return parse_fasta_lines(path.read_text(encoding="utf-8").splitlines())


def parse_fasta_lines(lines: Iterable[str]) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    seen: set[str] = set()
    name: str | None = None
    length = 0
    for raw_line in lines:
        if raw_line.startswith(">"):
            if name is not None:
                result.append((name, length))
            name = raw_line[1:].split()[0]
            if not name or name in seen:
                _fail(f"FASTA has empty or duplicate contig: {name!r}")
            seen.add(name)
            length = 0
        else:
            if name is None:
                _fail("FASTA sequence appears before its header")
            sequence = raw_line.strip()
            if sequence and re.fullmatch(r"[A-Za-z*.-]+", sequence) is None:
                _fail(f"FASTA has invalid sequence characters for {name}")
            length += len(sequence)
    if name is not None:
        result.append((name, length))
    if not result or any(length <= 0 for _, length in result):
        _fail("FASTA must contain nonempty contigs")
    return result


def parse_fai(path: Path) -> list[tuple[str, int]]:
    result = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        fields = line.split("\t")
        if len(fields) < 2 or re.fullmatch(r"[0-9]+", fields[1]) is None:
            _fail(f"FAI row {number} is malformed")
        result.append((fields[0], int(fields[1])))
    return _unique_contigs(result, "FAI")


def parse_dict(path: Path) -> list[tuple[str, int]]:
    result = []
    for line in path.read_text().splitlines():
        if not line.startswith("@SQ\t"):
            continue
        values = dict(
            field.split(":", 1) for field in line.split("\t")[1:] if ":" in field
        )
        if "SN" not in values or not values.get("LN", "").isdigit():
            _fail("DICT has malformed @SQ row")
        result.append((values["SN"], int(values["LN"])))
    return _unique_contigs(result, "DICT")


def _unique_contigs(rows: list[tuple[str, int]], label: str) -> list[tuple[str, int]]:
    if not rows or len({name for name, _ in rows}) != len(rows):
        _fail(f"{label} contigs are empty or duplicated")
    return rows
