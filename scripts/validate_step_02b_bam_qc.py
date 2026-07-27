#!/usr/bin/env python3
"""Validate explicit Step 02b quickcheck and flagstat evidence files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Sequence

import validate_step_00a_star_index as report


CHECK_IDS = {
    "quickcheck_structure",
    "flagstat_structure",
    "total_records",
    "mapped_records",
    "count_consistency",
}
COUNT_RE = re.compile(r"^([0-9]+) \+ ([0-9]+) (.+)$")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--quickcheck", required=True, type=Path)
    parser.add_argument("--flagstat", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def parse_flagstat(path: Path) -> tuple[dict[str, tuple[int, int]], list[str]]:
    values: dict[str, tuple[int, int]] = {}
    errors: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        match = COUNT_RE.match(raw)
        if match is None:
            errors.append(f"line {number} malformed")
            continue
        passed, failed, label = int(match.group(1)), int(match.group(2)), match.group(3)
        key = (
            "total"
            if label.startswith("in total ")
            else "mapped"
            if label.startswith("mapped ")
            else ""
        )
        if key:
            if key in values:
                errors.append(f"duplicate {key} row")
            values[key] = (passed, failed)
    return values, errors


def build(args: argparse.Namespace):
    quickcheck = args.quickcheck.resolve(strict=False)
    flagstat = args.flagstat.resolve(strict=False)
    snapshots = {
        path: report.regular_snapshot(path, label)
        for path, label in (
            (quickcheck, "Step 02b quickcheck report"),
            (flagstat, "Step 02b flagstat report"),
        )
    }
    quick_text = quickcheck.read_text(encoding="utf-8").strip()
    quick_ok = quick_text == "PASS: samtools quickcheck completed with no errors."
    values, errors = parse_flagstat(flagstat)
    total = sum(values.get("total", (-1, -1)))
    mapped = sum(values.get("mapped", (-1, -1)))
    flagstat_ok = not errors and {"total", "mapped"} <= values.keys()
    total_ok = flagstat_ok and total >= 0
    mapped_ok = flagstat_ok and mapped >= 0
    consistent = total_ok and mapped_ok and mapped <= total

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "02b", args.scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("quickcheck_structure", quick_ok, quick_text or "empty",
             "exact PASS marker", "captured samtools quickcheck result"),
        item("flagstat_structure", flagstat_ok,
             "; ".join(errors) if errors else ",".join(sorted(values)),
             "unique total and mapped rows", "flagstat report structure"),
        item("total_records", total_ok, total if total_ok else "invalid",
             "nonnegative integer", "QC-passed plus QC-failed total"),
        item("mapped_records", mapped_ok, mapped if mapped_ok else "invalid",
             "nonnegative integer", "QC-passed plus QC-failed mapped"),
        item("count_consistency", consistent, f"mapped={mapped} total={total}",
             "mapped <= total", "flagstat count reconciliation"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="02b", check_ids=CHECK_IDS)
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
        report.publish(args.output, data, args.scope_id, step_id="02b", check_ids=CHECK_IDS)
        print(f"Published Step 02b validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
