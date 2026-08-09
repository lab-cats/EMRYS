"""Manifest validation for the neutral Step 08 contract."""

from __future__ import annotations

from pathlib import Path

from norad.contracts.scientific_evidence._step08_definitions import (
    PARTITION_MANIFEST_HEADER,
    SAMPLE_MANIFEST_ALLOWED,
    SAMPLE_MANIFEST_REQUIRED,
    Table,
)
from norad.contracts.scientific_evidence._step08_support import (
    ensure_unique,
    fail,
    read_tsv,
    require_text,
    validate_enum,
    validate_safe_id,
)


def validate_sample_manifest(
    value: str | Path,
) -> tuple[Table, list[str], list[dict[str, str]]]:
    table = read_tsv("Sample manifest", value)
    if table.header not in (SAMPLE_MANIFEST_REQUIRED, SAMPLE_MANIFEST_ALLOWED):
        fail(
            "Sample manifest must have the exact Step 09 schema, with optional "
            "notes as the final column."
        )
    if not table.rows:
        fail("Sample manifest contains no sample rows.")
    ensure_unique(table.rows, "sample_id", "Sample manifest")
    for row_number, row in enumerate(table.rows, start=2):
        for column in SAMPLE_MANIFEST_REQUIRED:
            require_text(f"Sample manifest row {row_number} {column}", row[column])
        validate_safe_id("sample_id", row["sample_id"])
        validate_safe_id("replicate", row["replicate"])
        if row["strandedness"] not in (
            "forward",
            "reverse",
            "unstranded",
            "unknown",
        ):
            fail(
                "Sample manifest row "
                f"{row_number} has invalid strandedness: {row['strandedness']}"
            )
    return table, [row["sample_id"] for row in table.rows], table.rows


def validate_partition_manifest(value: str | Path) -> Table:
    table = read_tsv("Partition manifest", value, PARTITION_MANIFEST_HEADER)
    if not table.rows:
        fail("Partition manifest contains no partition rows.")
    ensure_unique(table.rows, "partition_id", "Partition manifest")
    for row_number, row in enumerate(table.rows, start=2):
        for column in PARTITION_MANIFEST_HEADER:
            require_text(f"Partition manifest row {row_number} {column}", row[column])
        validate_safe_id("partition_id", row["partition_id"])
        validate_enum(
            f"Partition manifest row {row_number} selector_type",
            row["selector_type"],
            ("region", "regions_file"),
        )
    return table
