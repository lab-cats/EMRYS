"""VCF, reference, BED12, STAR, and Picard artifact readers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from norad.libraries.validation.mpileup import VCF_FIXED_COLUMNS

from ._text_common import iter_text_lines
from .models import ArtifactIndexError


def inspect_vcf(path: Path) -> tuple[int, dict[str, Any]]:
    fields: list[str] | None = None
    samples: list[str] = []
    format_ids: set[str] = set()
    info_ids: set[str] = set()
    count = 0
    observed_lines = 0
    for line_number, line in iter_text_lines(path):
        observed_lines += 1
        if line_number == 1 and not line.startswith("##fileformat=VCF"):
            raise ArtifactIndexError(
                "VCF is missing the leading ##fileformat declaration"
            )
        format_match = re.match(r"^##FORMAT=<ID=([^,>]+)", line)
        if format_match:
            format_ids.add(format_match.group(1))
            continue
        info_match = re.match(r"^##INFO=<ID=([^,>]+)", line)
        if info_match:
            info_ids.add(info_match.group(1))
            continue
        if line.startswith("##"):
            continue
        if line.startswith("#CHROM\t"):
            if fields is not None:
                raise ArtifactIndexError("VCF must contain exactly one #CHROM header")
            fields = line.split("\t")
            if tuple(fields[:9]) != VCF_FIXED_COLUMNS:
                raise ArtifactIndexError("VCF fixed columns are invalid")
            samples = fields[9:]
            if not samples or any(not sample for sample in samples):
                raise ArtifactIndexError("VCF must declare at least one sample")
            if len(samples) != len(set(samples)):
                raise ArtifactIndexError("VCF sample columns are not unique")
            continue
        if line.startswith("#"):
            raise ArtifactIndexError(
                f"VCF line {line_number} has an unexpected header record"
            )
        if fields is None:
            raise ArtifactIndexError(f"VCF record line {line_number} precedes #CHROM")
        values = line.split("\t")
        if len(values) != len(fields):
            raise ArtifactIndexError(
                f"VCF record line {line_number} has {len(values)} fields; "
                f"expected {len(fields)}"
            )
        try:
            if int(values[1]) <= 0:
                raise ValueError
        except ValueError as exc:
            raise ArtifactIndexError(
                f"VCF record line {line_number} has invalid POS"
            ) from exc
        count += 1
    if observed_lines == 0 or fields is None:
        raise ArtifactIndexError("VCF must contain exactly one #CHROM header")
    return count, {
        "sample_count": len(samples),
        "samples": samples,
        "format_ids": sorted(format_ids),
        "info_ids": sorted(info_ids),
    }


def inspect_fasta(path: Path) -> tuple[int, dict[str, Any]]:
    sequence_ids: set[str] = set()
    sequence_lengths: dict[str, int] = {}
    current: str | None = None
    total_bases = 0
    sequence_has_bases = False
    for line_number, line in iter_text_lines(path):
        if line.startswith(">"):
            if current is not None and not sequence_has_bases:
                raise ArtifactIndexError(f"FASTA sequence {current!r} has no bases")
            current = line[1:].split()[0] if line[1:].split() else ""
            if not current or current in sequence_ids:
                raise ArtifactIndexError(
                    f"FASTA line {line_number} has an empty or duplicate ID"
                )
            sequence_ids.add(current)
            sequence_lengths[current] = 0
            sequence_has_bases = False
            continue
        if current is None:
            raise ArtifactIndexError("FASTA sequence appears before a header")
        sequence = line.strip()
        if not sequence or not re.fullmatch(r"[A-Za-z*.-]+", sequence):
            raise ArtifactIndexError(
                f"FASTA line {line_number} contains invalid sequence text"
            )
        total_bases += len(sequence)
        sequence_lengths[current] += len(sequence)
        sequence_has_bases = True
    if current is None or not sequence_has_bases:
        raise ArtifactIndexError("FASTA has no complete sequence")
    return len(sequence_ids), {
        "total_bases": total_bases,
        "contigs": sequence_lengths,
    }


def inspect_fai(path: Path) -> tuple[int, dict[str, Any]]:
    seen: set[str] = set()
    contigs: dict[str, int] = {}
    total_bases = 0
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) < 5 or not values[0] or values[0] in seen:
            raise ArtifactIndexError(f"FAI line {line_number} is invalid")
        try:
            length, offset, line_bases, line_width = map(int, values[1:5])
        except ValueError as exc:
            raise ArtifactIndexError(
                f"FAI line {line_number} has non-integer fields"
            ) from exc
        if length <= 0 or offset < 0 or line_bases <= 0 or line_width <= 0:
            raise ArtifactIndexError(
                f"FAI line {line_number} has invalid numeric fields"
            )
        seen.add(values[0])
        contigs[values[0]] = length
        total_bases += length
        count += 1
    if count == 0:
        raise ArtifactIndexError("FAI has no sequence records")
    return count, {"total_bases": total_bases, "contigs": contigs}


def inspect_dict(path: Path) -> tuple[int, dict[str, Any]]:
    seen: set[str] = set()
    contigs: dict[str, int] = {}
    total_bases = 0
    count = 0
    for line_number, line in iter_text_lines(path):
        if not line.startswith("@SQ\t"):
            continue
        fields = {
            token.split(":", 1)[0]: token.split(":", 1)[1]
            for token in line.split("\t")[1:]
            if ":" in token
        }
        name = fields.get("SN", "")
        try:
            length = int(fields.get("LN", ""))
        except ValueError as exc:
            raise ArtifactIndexError(
                f"Dictionary line {line_number} has an invalid LN"
            ) from exc
        if not name or name in seen or length <= 0:
            raise ArtifactIndexError(f"Dictionary line {line_number} has invalid SN/LN")
        seen.add(name)
        contigs[name] = length
        total_bases += length
        count += 1
    if count == 0:
        raise ArtifactIndexError("Dictionary has no @SQ records")
    return count, {"total_bases": total_bases, "contigs": contigs}


def inspect_bed12(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) != 12:
            raise ArtifactIndexError(f"BED line {line_number} does not have 12 fields")
        try:
            start = int(values[1])
            end = int(values[2])
            block_count = int(values[9])
            sizes = [int(value) for value in values[10].rstrip(",").split(",")]
            starts = [int(value) for value in values[11].rstrip(",").split(",")]
        except ValueError as exc:
            raise ArtifactIndexError(
                f"BED line {line_number} has invalid numeric fields"
            ) from exc
        if (
            not values[0]
            or not values[3]
            or start < 0
            or end <= start
            or values[5] not in {"+", "-"}
            or block_count <= 0
            or len(sizes) != block_count
            or len(starts) != block_count
            or any(size <= 0 for size in sizes)
            or any(offset < 0 for offset in starts)
        ):
            raise ArtifactIndexError(f"BED line {line_number} is invalid")
        count += 1
    if count == 0:
        raise ArtifactIndexError("BED12 file has no records")
    return count, {}


def inspect_star_sj(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) != 9:
            raise ArtifactIndexError(
                f"STAR SJ line {line_number} does not have 9 fields"
            )
        try:
            numbers = [int(value) for value in values[1:]]
        except ValueError as exc:
            raise ArtifactIndexError(
                f"STAR SJ line {line_number} has non-integer fields"
            ) from exc
        if not values[0] or numbers[0] <= 0 or numbers[1] < numbers[0]:
            raise ArtifactIndexError(f"STAR SJ line {line_number} is invalid")
        count += 1
    return count, {}


def inspect_picard_metrics(path: Path) -> tuple[int, dict[str, Any]]:
    header: list[str] | None = None
    metric_row: dict[str, str] | None = None
    for _line_number, line in iter_text_lines(path):
        if line.startswith("LIBRARY\t"):
            header = line.split("\t")
            continue
        if header is not None and line and not line.startswith("#"):
            values = line.split("\t")
            if len(header) != len(values):
                raise ArtifactIndexError("Picard metrics row width is invalid")
            metric_row = dict(zip(header, values, strict=True))
            break
    if header is None or metric_row is None:
        raise ArtifactIndexError("Picard metrics table is missing")
    native: dict[str, Any] = {}
    for key, value in metric_row.items():
        if key == "LIBRARY" or value == "":
            continue
        try:
            native[key.lower()] = (
                float(value)
                if any(token in value for token in (".", "e", "E"))
                else int(value)
            )
        except ValueError:
            continue
    return 1, native
