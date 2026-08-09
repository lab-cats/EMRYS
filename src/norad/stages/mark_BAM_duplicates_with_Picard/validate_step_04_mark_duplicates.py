#!/usr/bin/env python3
"""Validate explicit Step 04 marked-duplicate BAM/BAI and Picard metrics."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
if sys.path[:1] != [src_root]:
    if src_root in sys.path:
        sys.path.remove(src_root)
    sys.path.insert(0, src_root)

from norad.libraries import validation as report
from norad.libraries.alignments import bam as bam_report
from norad.libraries.quality import parse_duplication_metrics

CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_preservation",
    "duplication_metrics",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "bam": report.lexical_path(args.bam),
        "bai": report.lexical_path(args.bai),
        "metrics": report.lexical_path(args.metrics),
        "samtools": report.lexical_path(args.samtools_bin),
    }
    snapshots = report.snapshots(paths, label="Step 04")
    report.require_executable(paths["samtools"], "samtools executable")
    structure, bam_magic, bai_magic = bam_report.validate_bam_bai_pair(
        paths["bam"], paths["bai"]
    )
    (
        quickcheck_ok,
        quickcheck_detail,
        coordinate,
        matching_rg,
        header_detail,
    ) = bam_report.validate_samtools_readiness(
        paths["samtools"], paths["bam"], args.scope_id
    )
    metrics_ok, metrics_detail = parse_duplication_metrics(
        report.stable_text(paths["metrics"], "Picard metrics")[0]
    )

    rows = [
        report.row(
            "04",
            args.scope_id,
            "bam_bai_structure",
            structure,
            f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
            "BAM/BGZF and BAI/CSI magic",
            "marked-duplicate pair containers",
        ),
        report.row(
            "04",
            args.scope_id,
            "samtools_quickcheck",
            quickcheck_ok,
            quickcheck_detail,
            "exit=0 with empty diagnostics",
            "samtools quickcheck -v",
        ),
        report.row(
            "04",
            args.scope_id,
            "coordinate_sorting",
            coordinate,
            header_detail,
            "one @HD with SO:coordinate",
            "marked BAM sort order",
        ),
        report.row(
            "04",
            args.scope_id,
            "read_group_preservation",
            matching_rg,
            header_detail,
            f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
            "canonical sample read group is preserved",
        ),
        report.row(
            "04",
            args.scope_id,
            "duplication_metrics",
            metrics_ok,
            metrics_detail,
            "one valid Picard metrics row",
            "duplication metrics structure",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="04", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(args, build, "04", CHECK_IDS)


if __name__ == "__main__":
    raise SystemExit(main())
