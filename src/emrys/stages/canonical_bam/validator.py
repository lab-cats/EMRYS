"""Validate an explicit Step 02 canonical BAM/BAI and read-group contract."""

from __future__ import annotations

import argparse
from pathlib import Path

from emrys.libraries.alignments.bam import (
    run_tool,
    validate_bam_bai_pair,
    validate_samtools_readiness,
)
from emrys.libraries.validation import (
    Snapshot,
    ValidationError,
    add_output_arguments,
    build_report,
    integer_stdout,
    lexical_path,
    require_executable,
    run_from_args,
    snapshots,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_header",
    "alignment_rg_tags",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the canonical-BAM validator owner's arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 02 report from a canonical BAM/BAI pair."""
    bam_path = lexical_path(arguments.bam)
    bai_path = lexical_path(arguments.bai)
    samtools_path = lexical_path(arguments.samtools_bin)
    input_snapshots = snapshots(
        {"bam": bam_path, "bai": bai_path, "samtools": samtools_path},
        label="Step 02",
    )
    require_executable(samtools_path, "samtools executable")
    pair_structure_valid, bam_magic, bai_magic = validate_bam_bai_pair(
        bam_path,
        bai_path,
    )
    (
        quickcheck_valid,
        quickcheck_detail,
        coordinate_sorting_valid,
        read_group_header_valid,
        header_detail,
    ) = validate_samtools_readiness(
        samtools_path,
        bam_path,
        arguments.scope_id,
    )
    total_alignments = integer_stdout(
        run_tool(samtools_path, "view", "-c", str(bam_path)),
        "alignment count",
    )
    tagged_alignments = integer_stdout(
        run_tool(
            samtools_path,
            "view",
            "-c",
            "-d",
            f"RG:{arguments.scope_id}",
            str(bam_path),
        ),
        "read-group alignment count",
    )

    return build_report(
        "02",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        {
            "bam_bai_structure": (
                pair_structure_valid,
                f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
                "BAM/BGZF and BAI/CSI magic",
                "canonical pair containers",
            ),
            "samtools_quickcheck": (
                quickcheck_valid,
                quickcheck_detail,
                "exit=0 with empty diagnostics",
                "samtools quickcheck -v",
            ),
            "coordinate_sorting": (
                coordinate_sorting_valid,
                header_detail,
                "one @HD with SO:coordinate",
                "canonical BAM sort order",
            ),
            "read_group_header": (
                read_group_header_valid,
                header_detail,
                (f"one @RG with ID:{arguments.scope_id} and SM:{arguments.scope_id}"),
                "sample read-group header",
            ),
            "alignment_rg_tags": (
                tagged_alignments == total_alignments,
                f"tagged={tagged_alignments} total={total_alignments}",
                "tagged equals total",
                "all alignments carry the sample RG tag",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 02 canonical-BAM request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "02",
        CHECK_IDS,
        caught_errors=(OSError, ValidationError),
    )
