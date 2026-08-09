#!/usr/bin/env python3
"""Validate explicit Step 06 orientation BAM/BAI outputs and count arithmetic."""

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
    magic = {}
    containers_ok = True
    for bam_key, bai_key in (("fwd_bam", "fwd_bai"), ("rev_bam", "rev_bai")):
        ok, bam_magic, bai_magic = bam_report.validate_bam_bai_pair(
            paths[bam_key], paths[bai_key]
        )
        containers_ok = containers_ok and ok
        magic[bam_key] = bam_magic
        magic[bai_key] = bai_magic
    values, structure_detail = orientation.read_orientation_counts(
        paths["counts"], args.scope_id
    )
    structure_ok = bool(values)
    rows = [
        report.row(
            "06",
            args.scope_id,
            "output_containers",
            containers_ok,
            " ".join(f"{key}={value.hex()}" for key, value in magic.items()),
            "two BAM/BGZF and two BAI/CSI signatures",
            "orientation output containers",
        ),
        report.row(
            "06",
            args.scope_id,
            "counts_structure",
            structure_ok,
            structure_detail,
            "one exact typed sample row",
            "orientation counts table",
        ),
    ]
    for check_id, orientation_key in zip(
        ("fwd_count_arithmetic", "rev_count_arithmetic"), orientation.ORIENTATIONS
    ):
        count_ok, count_detail = orientation.mechanical_like_count_detail(
            values, orientation_key
        )
        rows.append(
            report.row(
                "06",
                args.scope_id,
                check_id,
                structure_ok and count_ok,
                count_detail,
                f"mechanical {orientation_key} counts",
                f"mechanical {orientation_key} counts",
            )
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
        )
        <= 0.0000005
    )
    rows.extend(
        [
            report.row(
                "06",
                args.scope_id,
                "assigned_count_arithmetic",
                assigned_ok,
                f"input={values.get('input_records')} "
                f"assigned={values.get('assigned_records')} "
                f"unassigned={values.get('unassigned_records')} "
                f"fraction={values.get('assigned_fraction')}",
                "groups sum; assigned + unassigned = input; fraction reconciles",
                "complete orientation count arithmetic",
            ),
        ]
    )
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="06", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(args, build, "06", CHECK_IDS)


if __name__ == "__main__":
    raise SystemExit(main())
