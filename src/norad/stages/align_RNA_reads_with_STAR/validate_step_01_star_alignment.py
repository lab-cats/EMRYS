#!/usr/bin/env python3
"""Validate explicit Step 01 STAR alignment outputs and mapping summary."""

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
from norad.libraries.alignments import star as star_report

CHECK_IDS = {
    "output_files",
    "bam_structure",
    "final_log_structure",
    "mapping_summary",
    "splice_junction_structure",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--log-final", required=True, type=Path)
    parser.add_argument("--log-out", required=True, type=Path)
    parser.add_argument("--log-progress", required=True, type=Path)
    parser.add_argument("--sj-out", required=True, type=Path)
    report.add_output_arguments(parser)
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "bam": report.lexical_path(args.bam),
        "log_final": report.lexical_path(args.log_final),
        "log_out": report.lexical_path(args.log_out),
        "log_progress": report.lexical_path(args.log_progress),
        "sj_out": report.lexical_path(args.sj_out),
    }
    snapshots = report.snapshots(paths, label="Step 01")
    nonempty = all(snapshot.size > 0 for snapshot in snapshots.values())
    bam_valid, bam_prefix = bam_report.validate_bam_signature(paths["bam"])
    final_values: dict[str, str] = {}
    final_error = ""
    try:
        final_values = star_report.parse_final_log(
            report.stable_text(paths["log_final"], "STAR final log")[0]
        )
    except report.ValidationError as exc:
        final_error = report.clean(exc)
    except ValueError as exc:
        final_error = str(exc)
    mapping_ok, mapping_observed = star_report.valid_mapping_summary(final_values)
    sj_ok, sj_observed = star_report.valid_splice_junction_table(
        report.stable_text(paths["sj_out"], "STAR splice-junction table")[0]
    )

    rows = [
        report.row(
            "01",
            args.scope_id,
            "output_files",
            nonempty,
            len(paths),
            "5 nonempty explicit outputs",
            "BAM, final/general/progress logs, and SJ table",
        ),
        report.row(
            "01",
            args.scope_id,
            "bam_structure",
            bam_valid,
            bam_prefix.hex(),
            "BAM or BGZF magic",
            "alignment output container",
        ),
        report.row(
            "01",
            args.scope_id,
            "final_log_structure",
            bool(final_values),
            len(final_values) if final_values else final_error,
            "nonempty unique key/value rows",
            "STAR Log.final.out structure",
        ),
        report.row(
            "01",
            args.scope_id,
            "mapping_summary",
            mapping_ok,
            mapping_observed,
            "three required percentages in 0..100",
            "STAR mapping summary",
        ),
        report.row(
            "01",
            args.scope_id,
            "splice_junction_structure",
            sj_ok,
            sj_observed,
            "zero or more valid 9-column rows",
            "STAR SJ.out.tab structure",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="01", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(args, build, "01", CHECK_IDS)


if __name__ == "__main__":
    raise SystemExit(main())
