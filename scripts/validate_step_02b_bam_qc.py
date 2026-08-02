#!/usr/bin/env python3
"""Validate explicit Step 02b quickcheck and flagstat evidence files."""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Sequence


# Temporary exact-file bridge; the final owner is src/norad/libraries/validation_report.py.
_REPORT_MODULE_NAME = "_norad_validation_report"
_REPORT_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "norad"
    / "libraries"
    / "validation_report.py"
).resolve(strict=False)
_REPORT_READY_ATTRIBUTE = "_NORAD_VALIDATION_REPORT_READY"


def _validated_validation_report(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError("cached validation-report owner has no valid file path") from exc
    if module_path != _REPORT_MODULE_PATH:
        raise ImportError(
            f"cached validation-report owner resolves to {module_path}, "
            f"expected {_REPORT_MODULE_PATH}"
        )
    if getattr(module, _REPORT_READY_ATTRIBUTE, False) is not True:
        raise ImportError("cached validation-report owner is partially initialized")
    return module


def _load_validation_report() -> object:
    cached = sys.modules.get(_REPORT_MODULE_NAME)
    if cached is not None:
        return _validated_validation_report(cached)
    spec = importlib.util.spec_from_file_location(
        _REPORT_MODULE_NAME, _REPORT_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError("unable to create an exact-file module specification")
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_REPORT_MODULE_NAME, module)
    if existing is not module:
        return _validated_validation_report(existing)
    try:
        spec.loader.exec_module(module)
        _validated_validation_report(module)
    except BaseException:
        if sys.modules.get(_REPORT_MODULE_NAME) is module:
            del sys.modules[_REPORT_MODULE_NAME]
        raise
    return module


try:
    report = _load_validation_report()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load NORAD validation-report owner at "
        f"{_REPORT_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None



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
