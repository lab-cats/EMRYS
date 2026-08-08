"""Shared parsing helpers for cohort mpileup-style contracts."""

from __future__ import annotations

from pathlib import Path

from norad.libraries import validation as report
from norad.libraries.references import contigs as reference_contigs


def read_sample_ids(path: Path) -> list[str]:
    header, rows = report.read_tsv(path)
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
    header, rows = report.read_tsv(path)
    required = {"partition_id", "selector_type", "selector_value"}
    if not required.issubset(header):
        raise report.ValidationError("Partition manifest lacks required columns")
    matches = [row for row in rows if row["partition_id"] == partition_id]
    if len(matches) != 1:
        raise report.ValidationError("Expected one declared partition row")
    selector_type = matches[0]["selector_type"]
    selector_value = matches[0]["selector_value"]
    if selector_type not in {"region", "regions_file"} or not selector_value:
        raise report.ValidationError("Partition selector is invalid")
    return selector_type, selector_value


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
            bounds = coordinates.rstrip("-").split("-", 1)
            if not all(value.isdigit() for value in bounds):
                return False
            start = int(bounds[0])
            end = int(bounds[-1]) if not coordinates.endswith("-") else contigs[contig]
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
            if fields[:9] != [
                "#CHROM",
                "POS",
                "ID",
                "REF",
                "ALT",
                "QUAL",
                "FILTER",
                "INFO",
                "FORMAT",
            ]:
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
