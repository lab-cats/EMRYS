#!/usr/bin/env python3
"""Validate explicit Step 04 marked-duplicate BAM/BAI and Picard metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

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
    quick = bam_report.run_tool(
        paths["samtools"], "quickcheck", "-v", str(paths["bam"])
    )
    header = bam_report.run_tool(
        paths["samtools"], "view", "-H", str(paths["bam"])
    )
    if header.returncode != 0:
        report.fail(f"samtools view -H failed: {report.clean(header.stderr)}")
    coordinate, matching_rg, header_detail = bam_report.parse_header(
        header.stdout, args.scope_id
    )
    metrics_ok, metrics_detail = parse_duplication_metrics(
        report.stable_text(paths["metrics"], "Picard metrics")[0]
    )

    rows = [
        report.row(
            "04", args.scope_id, "bam_bai_structure", structure,
            f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
            "BAM/BGZF and BAI/CSI magic", "marked-duplicate pair containers",
        ),
        report.row(
            "04", args.scope_id, "samtools_quickcheck", quick.returncode == 0,
            report.clean(quick.stderr) or f"exit={quick.returncode}",
            "exit=0 with empty diagnostics", "samtools quickcheck -v",
        ),
        report.row(
            "04", args.scope_id, "coordinate_sorting", coordinate,
            header_detail, "one @HD with SO:coordinate", "marked BAM sort order",
        ),
        report.row(
            "04", args.scope_id, "read_group_preservation", matching_rg,
            header_detail, f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
            "canonical sample read group is preserved",
        ),
        report.row(
            "04", args.scope_id, "duplication_metrics", metrics_ok,
            metrics_detail, "one valid Picard metrics row", "duplication metrics structure",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="04", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id='04',
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label='Step 04',
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
