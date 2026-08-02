#!/usr/bin/env python3
"""Validate explicit Step 06 orientation BAM/BAI outputs and count arithmetic."""

from __future__ import annotations

import argparse
import importlib.util
import csv
import math
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



COUNTS_HEADER = (
    "sample_id", "input_records", "flag_99_records", "flag_147_records",
    "flag_83_records", "flag_163_records", "fwd_like_records",
    "rev_like_records", "assigned_records", "unassigned_records",
    "assigned_fraction",
)
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


def read_counts(path: Path, scope_id: str) -> tuple[dict[str, int | float], str]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != COUNTS_HEADER:
                return {}, "header mismatch"
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return {}, report.clean(exc)
    if len(rows) != 1 or rows[0]["sample_id"] != scope_id:
        return {}, "expected one row for the declared sample"
    values: dict[str, int | float] = {}
    try:
        for key in COUNTS_HEADER[1:-1]:
            value = int(rows[0][key])
            if value < 0:
                raise ValueError
            values[key] = value
        fraction = float(rows[0]["assigned_fraction"])
        if not math.isfinite(fraction) or not 0 <= fraction <= 1:
            raise ValueError
        values["assigned_fraction"] = fraction
    except ValueError:
        return {}, "counts must be nonnegative integers and fraction in 0..1"
    return values, "one typed sample row"


def build(args: argparse.Namespace):
    paths = {
        "fwd_bam": args.fwd_bam.resolve(strict=False),
        "fwd_bai": args.fwd_bai.resolve(strict=False),
        "rev_bam": args.rev_bam.resolve(strict=False),
        "rev_bai": args.rev_bai.resolve(strict=False),
        "counts": args.counts.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 06 {role}")
        for role, path in paths.items()
    }
    magic = {role: path.read_bytes()[:4] for role, path in paths.items() if role != "counts"}
    containers_ok = (
        magic["fwd_bam"] in {b"BAM\x01", b"\x1f\x8b\x08\x04"}
        and magic["rev_bam"] in {b"BAM\x01", b"\x1f\x8b\x08\x04"}
        and magic["fwd_bai"] in {b"BAI\x01", b"CSI\x01"}
        and magic["rev_bai"] in {b"BAI\x01", b"CSI\x01"}
    )
    values, structure_detail = read_counts(paths["counts"], args.scope_id)
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

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "06", args.scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("output_containers", containers_ok,
             " ".join(f"{key}={value.hex()}" for key, value in magic.items()),
             "two BAM/BGZF and two BAI/CSI signatures",
             "orientation output containers"),
        item("counts_structure", structure_ok, structure_detail,
             "one exact typed sample row", "orientation counts table"),
        item("fwd_count_arithmetic", fwd_ok,
             f"{values.get('flag_99_records')}+{values.get('flag_147_records')}="
             f"{values.get('fwd_like_records')}",
             "flag99 + flag147 = FWD_like", "mechanical FWD_like counts"),
        item("rev_count_arithmetic", rev_ok,
             f"{values.get('flag_83_records')}+{values.get('flag_163_records')}="
             f"{values.get('rev_like_records')}",
             "flag83 + flag163 = REV_like", "mechanical REV_like counts"),
        item("assigned_count_arithmetic", assigned_ok,
             f"input={values.get('input_records')} assigned={values.get('assigned_records')} "
             f"unassigned={values.get('unassigned_records')} "
             f"fraction={values.get('assigned_fraction')}",
             "groups sum; assigned + unassigned = input; fraction reconciles",
             "complete orientation count arithmetic"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="06", check_ids=CHECK_IDS)
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
        report.publish(args.output, data, args.scope_id, step_id="06", check_ids=CHECK_IDS)
        print(f"Published Step 06 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
