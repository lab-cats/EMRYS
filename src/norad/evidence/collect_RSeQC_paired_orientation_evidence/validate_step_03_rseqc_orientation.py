#!/usr/bin/env python3
"""Validate an explicit Step 03 RSeQC infer_experiment report."""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]

from norad.libraries import validation as report
from norad.libraries.evidence import qc as qc_report

LABELS = (
    "Fraction of reads failed to determine",
    'Fraction of reads explained by "1++,1--,2+-,2-+"',
    'Fraction of reads explained by "1+-,1-+,2++,2--"',
)
CHECK_IDS = {
    "report_structure",
    "failed_fraction",
    "paired_orientation_fraction_a",
    "paired_orientation_fraction_b",
    "fraction_sum",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--infer-report", required=True, type=Path)
    parser.add_argument("--sum-tolerance", type=float, default=0.001)
    report.add_output_arguments(parser)
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    if not math.isfinite(args.sum_tolerance) or not 0 <= args.sum_tolerance <= 0.1:
        report.fail("--sum-tolerance must be finite and between 0 and 0.1")
    source = report.lexical_path(args.infer_report)
    snapshots = report.snapshots({"report": source}, label="Step 03 RSeQC")
    values, errors = qc_report.parse_fraction_report(
        report.stable_text(source, "RSeQC inference report")[0], LABELS
    )
    fractions = [values.get(label) for label in LABELS]
    valid = [value is not None and 0 <= value <= 1 for value in fractions]
    observed_sum = sum(value for value in fractions if value is not None)
    sum_ok = all(valid) and abs(observed_sum - 1.0) <= args.sum_tolerance

    return report.build_report(
        "03",
        args.scope_id,
        snapshots,
        CHECK_IDS,
        {
            "report_structure": (
                not errors,
                "; ".join(errors) if errors else "3 unique required labels",
                "exactly one value per required label",
                "RSeQC report structure",
            ),
            "failed_fraction": (
                valid[0],
                fractions[0],
                "finite 0..1",
                "reads not assigned to an orientation",
            ),
            "paired_orientation_fraction_a": (
                valid[1],
                fractions[1],
                "finite 0..1",
                LABELS[1],
            ),
            "paired_orientation_fraction_b": (
                valid[2],
                fractions[2],
                "finite 0..1",
                LABELS[2],
            ),
            "fraction_sum": (
                sum_ok,
                f"{observed_sum:.12g}",
                f"1 within {args.sum_tolerance:.12g}",
                "three fractions reconcile",
            ),
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run_from_args(args, build, "03", CHECK_IDS)


if __name__ == "__main__":
    raise SystemExit(main())
