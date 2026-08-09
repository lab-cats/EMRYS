#!/usr/bin/env python3
"""Validate an explicit Step 02 canonical BAM/BAI and read-group contract."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.libraries import validation as report
from norad.libraries.alignments import bam as bam_report

CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_header",
    "alignment_rg_tags",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    report.add_output_arguments(parser)
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    bam = report.lexical_path(args.bam)
    bai = report.lexical_path(args.bai)
    tool = report.lexical_path(args.samtools_bin)
    snapshots = report.snapshots(
        {"bam": bam, "bai": bai, "samtools": tool}, label="Step 02"
    )
    report.require_executable(tool, "samtools executable")
    structure, bam_magic, bai_magic = bam_report.validate_bam_bai_pair(bam, bai)
    (
        quickcheck_ok,
        quickcheck_detail,
        coordinate,
        matching_rg,
        header_detail,
    ) = bam_report.validate_samtools_readiness(tool, bam, args.scope_id)
    total = report.integer_stdout(
        bam_report.run_tool(tool, "view", "-c", str(bam)), "alignment count"
    )
    tagged = report.integer_stdout(
        bam_report.run_tool(tool, "view", "-c", "-d", f"RG:{args.scope_id}", str(bam)),
        "read-group alignment count",
    )

    return report.build_report(
        "02",
        args.scope_id,
        snapshots,
        CHECK_IDS,
        {
            "bam_bai_structure": (
                structure,
                f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
                "BAM/BGZF and BAI/CSI magic",
                "canonical pair containers",
            ),
            "samtools_quickcheck": (
                quickcheck_ok,
                quickcheck_detail,
                "exit=0 with empty diagnostics",
                "samtools quickcheck -v",
            ),
            "coordinate_sorting": (
                coordinate,
                header_detail,
                "one @HD with SO:coordinate",
                "canonical BAM sort order",
            ),
            "read_group_header": (
                matching_rg,
                header_detail,
                f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
                "sample read-group header",
            ),
            "alignment_rg_tags": (
                tagged == total,
                f"tagged={tagged} total={total}",
                "tagged equals total",
                "all alignments carry the sample RG tag",
            ),
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(
        args,
        build,
        "02",
        CHECK_IDS,
        caught_errors=(OSError, report.ValidationError),
    )


if __name__ == "__main__":
    raise SystemExit(main())
