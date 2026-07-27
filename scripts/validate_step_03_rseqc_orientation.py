#!/usr/bin/env python3
"""Validate an explicit Step 03 RSeQC infer_experiment report."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Sequence

import validate_step_00a_star_index as report


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
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def parse_report(path: Path) -> tuple[dict[str, float], list[str]]:
    values: dict[str, float] = {}
    errors: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if ":" not in raw:
            continue
        label, lexeme = (part.strip() for part in raw.rsplit(":", 1))
        if label not in LABELS:
            continue
        if label in values:
            errors.append(f"duplicate label at line {number}")
            continue
        try:
            value = float(lexeme)
        except ValueError:
            errors.append(f"invalid fraction at line {number}")
            continue
        if not math.isfinite(value):
            errors.append(f"nonfinite fraction at line {number}")
            continue
        values[label] = value
    missing = [label for label in LABELS if label not in values]
    if missing:
        errors.append(f"missing {len(missing)} required labels")
    return values, errors


def build(args: argparse.Namespace):
    if not math.isfinite(args.sum_tolerance) or not 0 <= args.sum_tolerance <= 0.1:
        report.fail("--sum-tolerance must be finite and between 0 and 0.1")
    source = args.infer_report.resolve(strict=False)
    snapshots = {source: report.regular_snapshot(source, "Step 03 RSeQC report")}
    values, errors = parse_report(source)
    fractions = [values.get(label) for label in LABELS]
    valid = [value is not None and 0 <= value <= 1 for value in fractions]
    observed_sum = sum(value for value in fractions if value is not None)
    sum_ok = all(valid) and abs(observed_sum - 1.0) <= args.sum_tolerance

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "03", args.scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("report_structure", not errors,
             "; ".join(errors) if errors else "3 unique required labels",
             "exactly one value per required label", "RSeQC report structure"),
        item("failed_fraction", valid[0], fractions[0], "finite 0..1",
             "reads not assigned to an orientation"),
        item("paired_orientation_fraction_a", valid[1], fractions[1], "finite 0..1",
             LABELS[1]),
        item("paired_orientation_fraction_b", valid[2], fractions[2], "finite 0..1",
             LABELS[2]),
        item("fraction_sum", sum_ok, f"{observed_sum:.12g}",
             f"1 within {args.sum_tolerance:.12g}", "three fractions reconcile"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="03", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        print(data.decode(), end="")
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        for path, expected in snapshots.items():
            if report.regular_snapshot(path, f"Input {path.name}") != expected:
                report.fail(f"Input changed after validation: {path}")
        report.publish(args.output, data, args.scope_id, step_id="03", check_ids=CHECK_IDS)
        print(f"Published Step 03 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
