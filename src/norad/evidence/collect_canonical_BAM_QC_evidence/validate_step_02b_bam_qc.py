#!/usr/bin/env python3
"""Validate explicit Step 02b quickcheck and flagstat evidence files."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

if (src_root := str(Path(__file__).resolve().parents[3])) not in sys.path:
    sys.path.insert(0, src_root)

from norad.libraries import validation as report
from norad.libraries.evidence import qc as qc_report

CHECK_IDS = {
    "quickcheck_structure",
    "flagstat_structure",
    "total_records",
    "mapped_records",
    "count_consistency",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--quickcheck", required=True, type=Path)
    parser.add_argument("--flagstat", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    quickcheck = report.lexical_path(args.quickcheck)
    flagstat = report.lexical_path(args.flagstat)
    snapshots = report.snapshots(
        {"quickcheck": quickcheck, "flagstat": flagstat},
        label="Step 02b",
    )
    quick_text = report.stable_text(quickcheck, "Quickcheck output")[0].strip()
    quick_ok = quick_text == "PASS: samtools quickcheck completed with no errors."
    values, errors = qc_report.parse_flagstat(
        report.stable_text(flagstat, "Flagstat output")[0]
    )
    total = sum(values.get("total", (-1, -1)))
    mapped = sum(values.get("mapped", (-1, -1)))
    flagstat_ok = not errors and {"total", "mapped"} <= values.keys()
    total_ok = flagstat_ok and total >= 0
    mapped_ok = flagstat_ok and mapped >= 0
    consistent = total_ok and mapped_ok and mapped <= total

    rows = [
        report.row(
            "02b",
            args.scope_id,
            "quickcheck_structure",
            quick_ok,
            quick_text or "empty",
            "exact PASS marker",
            "captured samtools quickcheck result",
        ),
        report.row(
            "02b",
            args.scope_id,
            "flagstat_structure",
            flagstat_ok,
            "; ".join(errors) if errors else ",".join(sorted(values)),
            "unique total and mapped rows",
            "flagstat report structure",
        ),
        report.row(
            "02b",
            args.scope_id,
            "total_records",
            total_ok,
            total if total_ok else "invalid",
            "nonnegative integer",
            "QC-passed plus QC-failed total",
        ),
        report.row(
            "02b",
            args.scope_id,
            "mapped_records",
            mapped_ok,
            mapped if mapped_ok else "invalid",
            "nonnegative integer",
            "QC-passed plus QC-failed mapped",
        ),
        report.row(
            "02b",
            args.scope_id,
            "count_consistency",
            consistent,
            f"mapped={mapped} total={total}",
            "mapped <= total",
            "flagstat count reconciliation",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="02b", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return report.run(
        lambda: build(args),
        step_id="02b",
        scope_id=args.scope_id,
        check_ids=CHECK_IDS,
        output=args.output,
        execute=args.execute,
        published_label="Step 02b",
    )


if __name__ == "__main__":
    raise SystemExit(main())
