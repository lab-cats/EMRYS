#!/usr/bin/env python3
"""Validate explicit Step 06 orientation BAM/BAI outputs and count arithmetic."""

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
from norad.libraries.alignments import orientation

CHECK_IDS = {
    "output_containers",
    "counts_structure",
    "fwd_count_arithmetic",
    "rev_count_arithmetic",
    "assigned_count_arithmetic",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--fwd-bam", required=True, type=Path)
    parser.add_argument("--fwd-bai", required=True, type=Path)
    parser.add_argument("--rev-bam", required=True, type=Path)
    parser.add_argument("--rev-bai", required=True, type=Path)
    parser.add_argument("--counts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)
def build(args: argparse.Namespace):
    paths = {
        "fwd_bam": report.lexical_path(args.fwd_bam),
        "fwd_bai": report.lexical_path(args.fwd_bai),
        "rev_bam": report.lexical_path(args.rev_bam),
        "rev_bai": report.lexical_path(args.rev_bai),
        "counts": report.lexical_path(args.counts),
    }
    snapshots = report.snapshots(paths, label="Step 06")
    magic = {
        "fwd_bam": bam_report.read_bam_prefix(paths["fwd_bam"]),
        "fwd_bai": bam_report.read_bai_prefix(paths["fwd_bai"]),
        "rev_bam": bam_report.read_bam_prefix(paths["rev_bam"]),
        "rev_bai": bam_report.read_bai_prefix(paths["rev_bai"]),
    }
    containers_ok = (
        bam_report.bam_magic_ok(magic["fwd_bam"])
        and bam_report.bam_magic_ok(magic["rev_bam"])
        and bam_report.bai_magic_ok(magic["fwd_bai"])
        and bam_report.bai_magic_ok(magic["rev_bai"])
    )
    values, structure_detail = orientation.read_orientation_counts(
        paths["counts"], args.scope_id
    )
    structure_ok = bool(values)
    fwd_ok = structure_ok and (
        values["flag_99_records"] + values["flag_147_records"]
        == values["fwd_like_records"]
    )
    rev_ok = structure_ok and (
        values["flag_83_records"] + values["flag_163_records"]
        == values["rev_like_records"]
    )
    assigned_ok = structure_ok and (
        values["fwd_like_records"] + values["rev_like_records"]
        == values["assigned_records"]
        and values["assigned_records"] + values["unassigned_records"]
        == values["input_records"]
        and values["input_records"] > 0
        and abs(
            values["assigned_fraction"]
            - values["assigned_records"] / values["input_records"]
        ) <= 0.0000005
    )

    rows = [
        report.row(
            "06", args.scope_id, "output_containers", containers_ok,
            " ".join(f"{key}={value.hex()}" for key, value in magic.items()),
            "two BAM/BGZF and two BAI/CSI signatures",
            "orientation output containers",
        ),
        report.row(
            "06", args.scope_id, "counts_structure", structure_ok,
            structure_detail,
            "one exact typed sample row", "orientation counts table",
        ),
        report.row(
            "06", args.scope_id, "fwd_count_arithmetic", fwd_ok,
            f"{values.get('flag_99_records')}+{values.get('flag_147_records')}="
            f"{values.get('fwd_like_records')}",
            "flag99 + flag147 = FWD_like", "mechanical FWD_like counts",
        ),
        report.row(
            "06", args.scope_id, "rev_count_arithmetic", rev_ok,
            f"{values.get('flag_83_records')}+{values.get('flag_163_records')}="
            f"{values.get('rev_like_records')}",
            "flag83 + flag163 = REV_like", "mechanical REV_like counts",
        ),
        report.row(
            "06", args.scope_id, "assigned_count_arithmetic", assigned_ok,
            f"input={values.get('input_records')} assigned={values.get('assigned_records')} "
            f"unassigned={values.get('unassigned_records')} "
            f"fraction={values.get('assigned_fraction')}",
            "groups sum; assigned + unassigned = input; fraction reconciles",
            "complete orientation count arithmetic",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="06", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id='06',
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label='Step 06',
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
