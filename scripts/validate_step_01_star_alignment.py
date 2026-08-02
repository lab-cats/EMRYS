#!/usr/bin/env python3
"""Validate explicit Step 01 STAR alignment outputs and mapping summary."""

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
    "output_files",
    "bam_structure",
    "final_log_structure",
    "mapping_summary",
    "splice_junction_structure",
}
PERCENT_KEYS = {
    "Uniquely mapped reads %",
    "% of reads mapped to multiple loci",
    "% of reads mapped to too many loci",
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


def parse_final_log(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if "|" not in raw:
            continue
        key, value = (part.strip() for part in raw.split("|", 1))
        if not key or not value or key in values:
            report.fail(f"Invalid STAR Log.final.out row at line {line_number}")
        values[key] = value
    if not values:
        report.fail("STAR Log.final.out contains no key/value rows")
    return values


def valid_mapping_summary(values: dict[str, str]) -> tuple[bool, str]:
    missing = sorted(PERCENT_KEYS - values.keys())
    if missing:
        return False, f"missing keys: {','.join(missing)}"
    parsed = []
    for key in sorted(PERCENT_KEYS):
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)%", values[key])
        if match is None:
            return False, f"invalid percentage for {key}"
        value = float(match.group(1))
        if not 0 <= value <= 100:
            return False, f"percentage outside 0..100 for {key}"
        parsed.append(f"{key}={value:g}%")
    return True, "; ".join(parsed)


def valid_sj(path: Path) -> tuple[bool, str]:
    count = 0
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw:
            continue
        fields = raw.split("\t")
        if len(fields) != 9:
            return False, f"line {line_number} has {len(fields)} columns"
        try:
            start, end = int(fields[1]), int(fields[2])
            numeric = [int(value) for value in fields[3:]]
        except ValueError:
            return False, f"line {line_number} contains noninteger fields"
        if not fields[0] or start < 1 or end < start or any(value < 0 for value in numeric):
            return False, f"line {line_number} contains invalid coordinates/counts"
        count += 1
    return True, f"{count} splice-junction rows"


def build(args: argparse.Namespace):
    paths = {
        "bam": args.bam.resolve(strict=False),
        "log_final": args.log_final.resolve(strict=False),
        "log_out": args.log_out.resolve(strict=False),
        "log_progress": args.log_progress.resolve(strict=False),
        "sj_out": args.sj_out.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 01 {role}")
        for role, path in paths.items()
    }
    nonempty = all(snapshot.size > 0 for snapshot in snapshots.values())
    bam_prefix = paths["bam"].read_bytes()[:4]
    bam_valid = bam_prefix == b"BAM\x01" or bam_prefix == b"\x1f\x8b\x08\x04"
    final_values: dict[str, str] = {}
    final_error = ""
    try:
        final_values = parse_final_log(paths["log_final"])
    except report.ValidationError as exc:
        final_error = report.clean(exc)
    mapping_ok, mapping_observed = valid_mapping_summary(final_values)
    sj_ok, sj_observed = valid_sj(paths["sj_out"])

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "01",
            args.scope_id,
            check_id,
            "pass" if passed else "fail",
            report.clean(observed),
            report.clean(expected),
            report.clean(detail),
        )

    rows = [
        item("output_files", nonempty, len(paths), "5 nonempty explicit outputs",
             "BAM, final/general/progress logs, and SJ table"),
        item("bam_structure", bam_valid, bam_prefix.hex(), "BAM or BGZF magic",
             "alignment output container"),
        item("final_log_structure", bool(final_values), len(final_values) if final_values else final_error,
             "nonempty unique key/value rows", "STAR Log.final.out structure"),
        item("mapping_summary", mapping_ok, mapping_observed,
             "three required percentages in 0..100", "STAR mapping summary"),
        item("splice_junction_structure", sj_ok, sj_observed,
             "zero or more valid 9-column rows", "STAR SJ.out.tab structure"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="01", check_ids=CHECK_IDS)
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
        report.publish(args.output, data, args.scope_id, step_id="01", check_ids=CHECK_IDS)
        print(f"Published Step 01 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
