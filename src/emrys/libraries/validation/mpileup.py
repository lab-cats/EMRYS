"""Shared parsing helpers for cohort mpileup-style contracts."""

from __future__ import annotations

import re
from pathlib import Path

from emrys.libraries import validation as report
from emrys.libraries.references import contigs as reference_contigs
from emrys.libraries.validation.tsv import read_strict_tsv

VCF_FIXED_COLUMNS = (
    "#CHROM",
    "POS",
    "ID",
    "REF",
    "ALT",
    "QUAL",
    "FILTER",
    "INFO",
    "FORMAT",
)
RECEIPT_HEADER = (
    "cohort_id",
    "partition_id",
    "selector_type",
    "selector_value",
    "orientation",
    "vcf_path",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "sample_count",
    "vcf_record_count",
)
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def read_sample_ids(path: Path) -> list[str]:
    header, rows = read_strict_tsv("sample manifest", path, None, _invalid)
    if "sample_id" not in header:
        raise report.ValidationError("Sample manifest lacks sample_id")
    values = [row["sample_id"] for row in rows]
    if (
        not values
        or any(not value for value in values)
        or len(values) != len(set(values))
    ):
        raise report.ValidationError("Sample manifest IDs must be nonempty and unique")
    return values


def read_partition(path: Path, partition_id: str) -> tuple[str, str]:
    header, rows = read_strict_tsv("partition manifest", path, None, _invalid)
    required = {"partition_id", "selector_type", "selector_value"}
    if not required.issubset(header):
        raise report.ValidationError("Partition manifest lacks required columns")
    seen: set[str] = set()
    for row in rows:
        values = tuple(row[column] for column in required)
        if not all(values):
            raise report.ValidationError("Partition manifest has an empty value")
        declared = row["partition_id"]
        if not SAFE_ID.fullmatch(declared):
            raise report.ValidationError(f"Invalid partition ID: {declared}")
        if declared in seen:
            raise report.ValidationError(f"Duplicate partition ID: {declared}")
        seen.add(declared)
        if row["selector_type"] not in {"region", "regions_file"}:
            raise report.ValidationError(f"Invalid selector type for {declared}")
    matches = [row for row in rows if row["partition_id"] == partition_id]
    if len(matches) != 1:
        raise report.ValidationError("Expected one declared partition row")
    return matches[0]["selector_type"], matches[0]["selector_value"]


def _invalid(message: str) -> None:
    raise report.ValidationError(message)


def read_fai(path: Path) -> dict[str, int]:
    try:
        return {name: length for name, length in reference_contigs.parse_fai(path)}
    except reference_contigs.ReferenceContigError as exc:
        raise report.ValidationError(str(exc))


def selector_ok(
    selector_type: str,
    selector_value: str,
    partition_manifest: Path,
    contigs: dict[str, int],
) -> bool:
    if selector_type == "region":
        for region in selector_value.split(","):
            if not region:
                return False
            contig, separator, coordinates = region.partition(":")
            if contig not in contigs:
                return False
            if not separator:
                continue
            match = re.fullmatch(r"([0-9]+)(?:-([0-9]*))?", coordinates)
            if match is None:
                return False
            start = int(match.group(1))
            end_text = match.group(2)
            end = (
                start
                if end_text is None
                else contigs[contig]
                if end_text == ""
                else int(end_text)
            )
            if start < 1 or end < start or end > contigs[contig]:
                return False
        return True
    selector_path = report.resolve_from_base(partition_manifest.parent, selector_value)
    try:
        rows = [
            line.split("\t")
            for line in report.stable_text(selector_path, "Partition selector file")[
                0
            ].splitlines()
            if line.strip() and not line.startswith("#")
        ]
    except (OSError, UnicodeError, report.ValidationError):
        return False
    return bool(rows) and all(row and row[0] in contigs for row in rows)


def read_vcf(path: Path) -> tuple[list[str], int]:
    samples: list[str] | None = None
    count = 0
    for line in report.stable_text(path, "VCF")[0].splitlines():
        if line.startswith("##"):
            continue
        if line.startswith("#CHROM\t"):
            fields = line.split("\t")
            if tuple(fields[:9]) != VCF_FIXED_COLUMNS:
                raise report.ValidationError(f"Invalid VCF header: {path}")
            samples = fields[9:]
            continue
        if line.startswith("#"):
            continue
        if samples is None:
            raise report.ValidationError(f"VCF data precedes header: {path}")
        fields = line.split("\t")
        if len(fields) != 9 + len(samples) or not fields[1].isdigit():
            raise report.ValidationError(f"Invalid VCF data row: {path}")
        count += 1
    if samples is None:
        raise report.ValidationError(f"VCF lacks #CHROM header: {path}")
    return samples, count
