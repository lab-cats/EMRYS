#!/usr/bin/env python3
"""Validate explicit Step 04 marked-duplicate BAM/BAI and Picard metrics."""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path
from typing import Sequence


# Temporary exact-file bridge; the final owner is src/norad/libraries/validation_report.py.
_REPORT_MODULE_NAME = "_norad_validation_report"
_REPORT_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
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


_BAM_MODULE_NAME = "_norad_bam_validation"
_BAM_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
    / "libraries"
    / "bam_validation.py"
).resolve(strict=False)
_BAM_READY_ATTRIBUTE = "_NORAD_BAM_VALIDATION_READY"
_BAM_REQUIRED_CALLABLES = ("run_tool", "parse_header")


def _validated_bam_validation(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (AttributeError, OSError, TypeError) as exc:
        raise ImportError("cached BAM-validation owner has no valid file path") from exc
    if module_path != _BAM_MODULE_PATH:
        raise ImportError(
            f"cached BAM-validation owner resolves to {module_path}, "
            f"expected {_BAM_MODULE_PATH}"
        )
    if getattr(module, _BAM_READY_ATTRIBUTE, False) is not True:
        raise ImportError("cached BAM-validation owner is partially initialized")
    incomplete = [
        name
        for name in _BAM_REQUIRED_CALLABLES
        if not callable(getattr(module, name, None))
    ]
    if incomplete:
        raise ImportError(
            "cached BAM-validation owner has incomplete API: " + ", ".join(incomplete)
        )
    return module


def _load_bam_validation() -> object:
    cached = sys.modules.get(_BAM_MODULE_NAME)
    if cached is not None:
        return _validated_bam_validation(cached)
    spec = importlib.util.spec_from_file_location(_BAM_MODULE_NAME, _BAM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("unable to create an exact-file module specification")
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_BAM_MODULE_NAME, module)
    if existing is not module:
        return _validated_bam_validation(existing)
    try:
        spec.loader.exec_module(module)
        _validated_bam_validation(module)
    except BaseException:
        if sys.modules.get(_BAM_MODULE_NAME) is module:
            del sys.modules[_BAM_MODULE_NAME]
        raise
    return module


try:
    bam_report = _load_bam_validation()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load NORAD BAM-validation owner at "
        f"{_BAM_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


CHECK_IDS = {
    "bam_bai_structure",
    "samtools_quickcheck",
    "coordinate_sorting",
    "read_group_preservation",
    "duplication_metrics",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--bai", required=True, type=Path)
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--samtools-bin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def parse_metrics(path: Path) -> tuple[bool, str]:
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    if len(lines) < 2:
        return False, "missing metrics header/data row"
    header = lines[0].split("\t")
    rows = [line.split("\t") for line in lines[1:]]
    required = {"LIBRARY", "READ_PAIRS_EXAMINED", "READ_PAIR_DUPLICATES",
                "PERCENT_DUPLICATION"}
    if not required <= set(header) or len(rows) != 1 or len(rows[0]) != len(header):
        return False, "expected one row with required Picard columns"
    values = dict(zip(header, rows[0], strict=True))
    try:
        examined = int(values["READ_PAIRS_EXAMINED"])
        duplicates = int(values["READ_PAIR_DUPLICATES"])
        fraction = float(values["PERCENT_DUPLICATION"])
    except ValueError:
        return False, "non-numeric duplication metric"
    valid = (
        bool(values["LIBRARY"])
        and examined >= 0
        and 0 <= duplicates <= examined
        and math.isfinite(fraction)
        and 0 <= fraction <= 1
    )
    return valid, (
        f"library={values['LIBRARY']} pairs={examined} "
        f"duplicates={duplicates} fraction={fraction:.12g}"
    )


def build(args: argparse.Namespace):
    paths = {
        "bam": args.bam.resolve(strict=False),
        "bai": args.bai.resolve(strict=False),
        "metrics": args.metrics.resolve(strict=False),
        "samtools": args.samtools_bin.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 04 {role}")
        for role, path in paths.items()
    }
    if not paths["samtools"].stat().st_mode & 0o111:
        report.fail(f"samtools executable is not executable: {paths['samtools']}")
    bam_magic = paths["bam"].read_bytes()[:4]
    bai_magic = paths["bai"].read_bytes()[:4]
    structure = (
        bam_magic in {b"BAM\x01", b"\x1f\x8b\x08\x04"}
        and bai_magic in {b"BAI\x01", b"CSI\x01"}
    )
    quick = bam_report.run_tool(
        paths["samtools"], "quickcheck", "-v", str(paths["bam"])
    )
    header = bam_report.run_tool(
        paths["samtools"], "view", "-H", str(paths["bam"])
    )
    if header.returncode != 0:
        report.fail(f"samtools view -H failed: {report.clean(header.stderr)}")
    coordinate, matching_rg, header_detail = bam_report.parse_header(
        header.stdout, args.scope_id
    )
    metrics_ok, metrics_detail = parse_metrics(paths["metrics"])

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "04", args.scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("bam_bai_structure", structure,
             f"BAM={bam_magic.hex()} BAI={bai_magic.hex()}",
             "BAM/BGZF and BAI/CSI magic", "marked-duplicate pair containers"),
        item("samtools_quickcheck", quick.returncode == 0,
             report.clean(quick.stderr) or f"exit={quick.returncode}",
             "exit=0 with empty diagnostics", "samtools quickcheck -v"),
        item("coordinate_sorting", coordinate, header_detail,
             "one @HD with SO:coordinate", "marked BAM sort order"),
        item("read_group_preservation", matching_rg, header_detail,
             f"one @RG with ID:{args.scope_id} and SM:{args.scope_id}",
             "canonical sample read group is preserved"),
        item("duplication_metrics", metrics_ok, metrics_detail,
             "one valid Picard metrics row", "duplication metrics structure"),
    ]
    data = report.render(rows)
    report.validate_report(data, args.scope_id, step_id="04", check_ids=CHECK_IDS)
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
        report.publish(args.output, data, args.scope_id, step_id="04", check_ids=CHECK_IDS)
        print(f"Published Step 04 validation report: {args.output}")
        return 0
    except (OSError, UnicodeError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
