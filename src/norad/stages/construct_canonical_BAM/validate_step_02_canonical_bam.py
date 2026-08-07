#!/usr/bin/env python3
"""Validate an explicit Step 02 canonical BAM/BAI and read-group contract."""

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
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    bam = report.lexical_path(args.bam)
    bai = report.lexical_path(args.bai)
    tool = report.lexical_path(args.samtools_bin)
    snapshots = report.snapshots(
        {"bam": bam, "bai": bai, "samtools": tool}, label="Step 02"
    )
    if not tool.stat().st_mode & 0o111:
        report.fail(f"samtools executable is not executable: {tool}")
    bam_magic = bam.read_bytes()[:4]
    bai_magic = bai.read_bytes()[:4]
    structure = (
        bam_magic in {b"BAM\x01", b"\x1f\x8b\x08\x04"}
        and bai_magic in {b"BAI\x01", b"CSI\x01"}
    )
    quickcheck = bam_report.run_tool(tool, "quickcheck", "-v", str(bam))
    header = bam_report.run_tool(tool, "view", "-H", str(bam))
    if header.returncode != 0:
        report.fail(f"samtools view -H failed: {report.clean(header.stderr)}")
    coordinate, matching_rg, header_detail = bam_report.parse_header(
        header.stdout, args.scope_id
    )
    total = report.integer_stdout(
        bam_report.run_tool(tool, "view", "-c", str(bam)), "alignment count"
    )
    tagged = report.integer_stdout(
        bam_report.run_tool(
            tool, "view", "-c", "-d", f"RG:{args.scope_id}", str(bam)
        ),
        "read-group alignment count",
    )

    rows = [
        report.row("02", args.scope_id, "bam_bai_structure", structure,
             f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
             "BAM/BGZF and BAI/CSI magic", "canonical pair containers"),
        report.row("02", args.scope_id, "samtools_quickcheck", quickcheck.returncode == 0,
             report.clean(quickcheck.stderr) or f"exit={quickcheck.returncode}",
             "exit=0 with empty diagnostics", "samtools quickcheck -v"),
        report.row("02", args.scope_id, "coordinate_sorting", coordinate, header_detail,
             "one @HD with SO:coordinate", "canonical BAM sort order"),
        report.row("02", args.scope_id, "read_group_header", matching_rg, header_detail,
             f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
             "sample read-group header"),
        report.row("02", args.scope_id, "alignment_rg_tags", tagged == total, f"tagged={tagged} total={total}",
             "tagged equals total", "all alignments carry the sample RG tag"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="02", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id="02",
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label="Step 02",
            ),
            data,
            snapshots,
        )
    except (OSError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
