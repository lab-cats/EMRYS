#!/usr/bin/env python3
"""Validate explicit Step 01 STAR alignment outputs and mapping summary."""

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
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
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
    bam_prefix = bam_report.read_bam_prefix(paths["bam"])
    bam_valid = bam_report.bam_magic_ok(bam_prefix)
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
            "01", args.scope_id, "output_files", nonempty,
            len(paths), "5 nonempty explicit outputs",
            "BAM, final/general/progress logs, and SJ table",
        ),
        report.row(
            "01", args.scope_id, "bam_structure", bam_valid,
            bam_prefix.hex(), "BAM or BGZF magic",
            "alignment output container",
        ),
        report.row(
            "01", args.scope_id, "final_log_structure", bool(final_values),
            len(final_values) if final_values else final_error,
            "nonempty unique key/value rows", "STAR Log.final.out structure",
        ),
        report.row(
            "01", args.scope_id, "mapping_summary", mapping_ok,
            mapping_observed, "three required percentages in 0..100",
            "STAR mapping summary",
        ),
        report.row(
            "01", args.scope_id, "splice_junction_structure", sj_ok,
            sj_observed, "zero or more valid 9-column rows",
            "STAR SJ.out.tab structure",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="01", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id='01',
                scope_id=args.scope_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label='Step 01',
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
