"""Validate one explicit Step 00b BED12 against its source GTF."""

from __future__ import annotations

import argparse
from pathlib import Path

from norad.libraries.alignments.bed import inspect_bed12_rows, parse_bed12
from norad.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    fail,
    lexical_path,
    run_from_args,
    stable_text,
)
from norad.stages.gtf_to_bed12 import converter

DESCRIPTION = __doc__
CHECK_IDS = {
    "bed12_structure",
    "coordinate_sorting",
    "block_structure",
    "unique_transcript_names",
    "gtf_transcript_agreement",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the BED12 validator owner's arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bed12", required=True, type=Path)
    parser.add_argument("--source-gtf", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    if not arguments.scope_id or any(
        character.isspace() for character in arguments.scope_id
    ):
        fail("scope-id must be nonempty and contain no whitespace")

    bed_path = lexical_path(arguments.bed12)
    gtf_path = lexical_path(arguments.source_gtf)
    rows, bed_snapshot = parse_bed12(bed_path)
    _, gtf_snapshot = stable_text(gtf_path, "Source GTF")
    structural, sorted_rows, blocks_valid, unique_names = inspect_bed12_rows(rows)
    try:
        expected_records = converter.normalize_gtf(
            gtf_path,
            "exon",
            "transcript_id",
            "gene_id",
        )
    except (OSError, ValueError) as exc:
        fail(f"Source GTF cannot be normalized: {exc}")

    expected_lines = [record.to_line() for record in expected_records]
    observed_lines = ["\t".join(values) for values in rows]
    agreement = observed_lines == expected_lines
    return build_report(
        "00b",
        arguments.scope_id,
        {bed_path: bed_snapshot, gtf_path: gtf_snapshot},
        CHECK_IDS,
        {
            "bed12_structure": (
                structural,
                len(rows),
                "valid BED12 rows",
                "12 columns and legal coordinates/fields",
            ),
            "coordinate_sorting": (
                sorted_rows,
                "sorted" if sorted_rows else "unsorted",
                "chrom,start,end,name",
                "deterministic BED order",
            ),
            "block_structure": (
                blocks_valid,
                "valid" if blocks_valid else "invalid",
                "blockCount/sizes/starts reconcile",
                "BED blocks remain within transcript span",
            ),
            "unique_transcript_names": (
                unique_names,
                len({item[3] for item in rows}),
                len(rows),
                "one row per transcript name",
            ),
            "gtf_transcript_agreement": (
                agreement,
                len(rows),
                len(expected_lines),
                "BED12 bytes equal deterministic normalization of explicit GTF",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 00b BED12 request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "00b",
        CHECK_IDS,
    )
