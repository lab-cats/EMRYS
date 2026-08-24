"""Validate explicit Step 04 marked-duplicate BAM/BAI and Picard metrics."""

from __future__ import annotations

import argparse
from pathlib import Path

from emrys.libraries.alignments.bam import (
    validate_bam_bai_pair,
    validate_samtools_readiness,
)
from emrys.libraries.quality import parse_duplication_metrics
from emrys.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    lexical_path,
    require_executable,
    run_from_args,
    snapshots,
    stable_text,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_preservation",
    "duplication_metrics",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add duplicate-marking validator arguments to a command parser."""
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    add_output_arguments(parser)


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 04 report from marked-BAM evidence."""
    input_paths = {
        "bam": lexical_path(arguments.bam),
        "bai": lexical_path(arguments.bai),
        "metrics": lexical_path(arguments.metrics),
        "samtools": lexical_path(arguments.samtools_bin),
    }
    input_snapshots = snapshots(input_paths, label="Step 04")
    require_executable(input_paths["samtools"], "samtools executable")
    bam_bai_valid, bam_magic, bai_magic = validate_bam_bai_pair(
        input_paths["bam"], input_paths["bai"]
    )
    (
        quickcheck_valid,
        quickcheck_detail,
        coordinate_sorting_valid,
        read_group_valid,
        header_detail,
    ) = validate_samtools_readiness(
        input_paths["samtools"], input_paths["bam"], arguments.scope_id
    )
    metrics_valid, metrics_detail = parse_duplication_metrics(
        stable_text(input_paths["metrics"], "Picard metrics")[0]
    )

    return build_report(
        "04",
        arguments.scope_id,
        input_snapshots,
        CHECK_IDS,
        {
            "bam_bai_structure": (
                bam_bai_valid,
                f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
                "BAM/BGZF and BAI/CSI magic",
                "marked-duplicate pair containers",
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
                "marked BAM sort order",
            ),
            "read_group_preservation": (
                read_group_valid,
                header_detail,
                f"one @RG with ID:{arguments.scope_id} and SM:{arguments.scope_id}",
                "canonical sample read group is preserved",
            ),
            "duplication_metrics": (
                metrics_valid,
                metrics_detail,
                "one valid Picard metrics row",
                "duplication metrics structure",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 04 duplicate-marking request."""
    return run_from_args(arguments, build_validation_report, "04", CHECK_IDS)
