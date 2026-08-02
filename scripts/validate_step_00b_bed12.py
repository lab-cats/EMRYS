#!/usr/bin/env python3
"""Validate one explicit Step 00b BED12 against its source GTF."""

from __future__ import annotations

import argparse
import importlib.util
import io
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

import gtf_to_bed12


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bed12", required=True, type=Path)
    parser.add_argument("--source-gtf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def parse_bed(path: Path) -> tuple[list[tuple[str, ...]], report.Snapshot]:
    text, snapshot = report.stable_text(path, "BED12")
    rows: list[tuple[str, ...]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        fields = tuple(raw.split("\t"))
        if len(fields) != 12:
            report.fail(f"BED12 row {number} must contain exactly 12 columns")
        rows.append(fields)
    if not rows:
        report.fail("BED12 must contain at least one row")
    return rows, snapshot


def inspect_rows(rows: Sequence[tuple[str, ...]]) -> tuple[bool, bool, bool, bool]:
    structural = True
    blocks_valid = True
    unique_names = True
    parsed_keys: list[tuple[str, int, int, str]] = []
    names: set[str] = set()
    for fields in rows:
        try:
            start = int(fields[1])
            end = int(fields[2])
            thick_start = int(fields[6])
            thick_end = int(fields[7])
            count = int(fields[9])
            sizes = tuple(int(value) for value in fields[10].rstrip(",").split(","))
            starts = tuple(int(value) for value in fields[11].rstrip(",").split(","))
        except ValueError:
            structural = False
            continue
        if (
            not fields[0] or not fields[3] or fields[4] != "0"
            or fields[5] not in gtf_to_bed12.VALID_STRANDS
            or start < 0 or end <= start or thick_start != start
            or thick_end != end or fields[8] != "0" or count <= 0
        ):
            structural = False
        if (
            len(sizes) != count or len(starts) != count
            or any(size <= 0 for size in sizes)
            or any(offset < 0 for offset in starts)
            or tuple(sorted(starts)) != starts
            or any(offset + size > end - start for offset, size in zip(starts, sizes, strict=False))
            or starts[0] != 0
            or starts[-1] + sizes[-1] != end - start
        ):
            blocks_valid = False
        if fields[3] in names:
            unique_names = False
        names.add(fields[3])
        parsed_keys.append((fields[0], start, end, fields[3]))
    sorted_rows = structural and parsed_keys == sorted(parsed_keys)
    return structural, sorted_rows, blocks_valid, unique_names


def build_report(args: argparse.Namespace) -> tuple[bytes, dict[Path, report.Snapshot]]:
    if not args.scope_id or any(char.isspace() for char in args.scope_id):
        report.fail("scope-id must be nonempty and contain no whitespace")
    bed = args.bed12.resolve(strict=False)
    gtf = args.source_gtf.resolve(strict=False)
    rows, bed_snapshot = parse_bed(bed)
    _, gtf_snapshot = report.stable_text(gtf, "Source GTF")
    structural, sorted_rows, blocks_valid, unique_names = inspect_rows(rows)
    warnings = io.StringIO()
    try:
        transcripts = gtf_to_bed12.parse_gtf(
            gtf, "exon", "transcript_id", "gene_id", warnings
        )
        expected_records = gtf_to_bed12.build_bed_records(transcripts, warnings)
    except (OSError, ValueError) as exc:
        report.fail(f"Source GTF cannot be normalized: {exc}")
    expected_lines = [record.to_line() for record in expected_records]
    observed_lines = ["\t".join(values) for values in rows]
    agreement = observed_lines == expected_lines
    def evidence(check_id: str, passed: bool, observed: object, expected: object, detail: str) -> tuple[str, ...]:
        return ("00b", args.scope_id, check_id, "pass" if passed else "fail", report.clean(observed), report.clean(expected), report.clean(detail))

    output_rows = (
        evidence("bed12_structure", structural, len(rows), "valid BED12 rows", "12 columns and legal coordinates/fields"),
        evidence("coordinate_sorting", sorted_rows, "sorted" if sorted_rows else "unsorted", "chrom,start,end,name", "deterministic BED order"),
        evidence("block_structure", blocks_valid, "valid" if blocks_valid else "invalid", "blockCount/sizes/starts reconcile", "BED blocks remain within transcript span"),
        evidence("unique_transcript_names", unique_names, len({item[3] for item in rows}), len(rows), "one row per transcript name"),
        evidence("gtf_transcript_agreement", agreement, len(rows), len(expected_lines), "BED12 bytes equal deterministic normalization of explicit GTF"),
    )
    data = report.render(output_rows)
    report.validate_report(
        data,
        args.scope_id,
        step_id="00b",
        check_ids={
            "bed12_structure",
            "coordinate_sorting",
            "block_structure",
            "unique_transcript_names",
            "gtf_transcript_agreement",
        },
    )
    return data, {bed: bed_snapshot, gtf: gtf_snapshot}


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build_report(args)
        print("Step: 00b")
        print(f"Scope: {args.scope_id}")
        print(f"BED12: {args.bed12}")
        print(f"Source GTF: {args.source_gtf}")
        print(f"Output: {args.output}")
        print(data.decode(), end="")
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        for path, expected in snapshots.items():
            if report.regular_snapshot(path, f"Input {path.name}") != expected:
                report.fail(f"Input changed after validation: {path}")
        report.publish(
            args.output,
            data,
            args.scope_id,
            step_id="00b",
            check_ids={
                "bed12_structure",
                "coordinate_sorting",
                "block_structure",
                "unique_transcript_names",
                "gtf_transcript_agreement",
            },
        )
        print(f"Published Step 00b validation report: {args.output}")
        return 0
    except report.ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
