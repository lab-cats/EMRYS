#!/usr/bin/env python3
"""Validate one explicit Step 00b BED12 against its source GTF."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import Sequence


_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from norad.libraries import validation as report

import gtf_to_bed12
from norad.libraries.alignments import bed as bed_report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--bed12", required=True, type=Path)
    parser.add_argument("--source-gtf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build_report(args: argparse.Namespace) -> tuple[bytes, dict[Path, report.Snapshot]]:
    if not args.scope_id or any(char.isspace() for char in args.scope_id):
        report.fail("scope-id must be nonempty and contain no whitespace")
    bed = report.lexical_path(args.bed12)
    gtf = report.lexical_path(args.source_gtf)
    rows, bed_snapshot = bed_report.parse_bed12(bed)
    _, gtf_snapshot = report.stable_text(gtf, "Source GTF")
    structural, sorted_rows, blocks_valid, unique_names = bed_report.inspect_bed12_rows(
        rows
    )
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
    output_rows = (
        report.row(
            "00b", args.scope_id, "bed12_structure", structural, len(rows),
            "valid BED12 rows", "12 columns and legal coordinates/fields",
        ),
        report.row(
            "00b", args.scope_id, "coordinate_sorting", sorted_rows,
            "sorted" if sorted_rows else "unsorted", "chrom,start,end,name",
            "deterministic BED order",
        ),
        report.row(
            "00b", args.scope_id, "block_structure", blocks_valid,
            "valid" if blocks_valid else "invalid", "blockCount/sizes/starts reconcile",
            "BED blocks remain within transcript span",
        ),
        report.row(
            "00b", args.scope_id, "unique_transcript_names", unique_names,
            len({item[3] for item in rows}), len(rows), "one row per transcript name",
        ),
        report.row(
            "00b", args.scope_id, "gtf_transcript_agreement", agreement, len(rows),
            len(expected_lines),
            "BED12 bytes equal deterministic normalization of explicit GTF",
        ),
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
        return report.finish(
            report.Runtime(
                step_id='00b',
                scope_id=args.scope_id,
                check_ids={
                    "bed12_structure",
                    "coordinate_sorting",
                    "block_structure",
                    "unique_transcript_names",
                    "gtf_transcript_agreement",
                },
                output=args.output,
                execute=args.execute,
                published_label='Step 00b',
            ),
            data,
            snapshots,
        )
    except report.ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
