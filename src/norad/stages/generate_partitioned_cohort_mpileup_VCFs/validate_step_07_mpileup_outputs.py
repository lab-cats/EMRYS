#!/usr/bin/env python3
"""Validate one explicit Step 07 VCF/VCF/receipt transaction without bcftools."""

from __future__ import annotations

import argparse
import csv
import sys
from collections.abc import Sequence
from pathlib import Path

_SRC_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if parent.name == "src"
)
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from norad.libraries import validation as report
from norad.libraries.alignments import orientation as alignment_orientation
from norad.libraries.validation import mpileup as mpileup_report

RECEIPT_HEADER = (
    "cohort_id",
    "partition_id",
    "selector_type",
    "selector_value",
    "orientation",
    "vcf_path",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "sample_count",
    "vcf_record_count",
)
CHECK_IDS = {
    "receipt_structure",
    "vcf_structure",
    "selector_reconciliation",
    "manifest_identity_and_sample_order",
    "vcf_record_counts",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--partition-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--fwd-vcf", required=True, type=Path)
    parser.add_argument("--rev-vcf", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": report.lexical_path(args.sample_manifest),
        "partition_manifest": report.lexical_path(args.partition_manifest),
        "reference_fai": report.lexical_path(args.reference_fai),
        "fwd_vcf": report.lexical_path(args.fwd_vcf),
        "rev_vcf": report.lexical_path(args.rev_vcf),
        "receipt": report.lexical_path(args.receipt),
    }
    snapshots = report.snapshots(paths, label="Step 07")
    sample_ids = mpileup_report.read_sample_ids(paths["sample_manifest"])
    selector_type, selector_value = mpileup_report.read_partition(
        paths["partition_manifest"], args.partition_id
    )
    contigs = mpileup_report.read_fai(paths["reference_fai"])
    vcf_readings = []
    for orientation, vcf_key in (
        (alignment_orientation.ORIENTATIONS[0], "fwd_vcf"),
        (alignment_orientation.ORIENTATIONS[1], "rev_vcf"),
    ):
        samples, count = mpileup_report.read_vcf(paths[vcf_key])
        vcf_readings.append((orientation, paths[vcf_key], samples, count))
    receipt_header, receipt_rows = report.read_tsv(paths["receipt"])
    receipt_structure = (
        tuple(receipt_header) == RECEIPT_HEADER
        and len(receipt_rows) == 2
        and tuple(row["orientation"] for row in receipt_rows)
        == alignment_orientation.ORIENTATIONS
        and all(
            row["cohort_id"] == args.cohort_id
            and row["partition_id"] == args.partition_id
            for row in receipt_rows
        )
    )
    vcf_structure = all(samples == sample_ids for _, _, samples, _ in vcf_readings)
    selector_reconciliation = (
        mpileup_report.selector_ok(
            selector_type, selector_value, paths["partition_manifest"], contigs
        )
        and receipt_structure
        and all(
            row["selector_type"] == selector_type
            and row["selector_value"] == selector_value
            for row in receipt_rows
        )
    )
    manifest_identity = receipt_structure and all(
        row["sample_manifest_sha256"] == report.sha256_file(paths["sample_manifest"])
        and row["partition_manifest_sha256"]
        == report.sha256_file(paths["partition_manifest"])
        and row["sample_count"].isdigit()
        and int(row["sample_count"]) == len(sample_ids)
        for row in receipt_rows
    )
    counts_ok = receipt_structure and all(
        row["orientation"] == orientation
        and row["vcf_path"] == str(vcf_path)
        and row["vcf_record_count"].isdigit()
        and int(row["vcf_record_count"]) == count
        for row, (orientation, vcf_path, _, count) in zip(receipt_rows, vcf_readings)
    )

    scope_id = f"{args.cohort_id}__{args.partition_id}"

    rows = [
        report.row(
            "07",
            scope_id,
            "receipt_structure",
            receipt_structure,
            f"rows={len(receipt_rows)}",
            f"exact header; {', '.join(alignment_orientation.ORIENTATIONS)} rows",
            "receipt transaction",
        ),
        report.row(
            "07",
            scope_id,
            "vcf_structure",
            vcf_structure,
            " ".join(
                f"{orientation}={len(samples)}"
                for orientation, _, samples, _ in vcf_readings
            )
            + " samples",
            "valid VCFs with manifest sample order",
            "explicit VCF structure",
        ),
        report.row(
            "07",
            scope_id,
            "selector_reconciliation",
            selector_reconciliation,
            f"{selector_type}={selector_value}",
            "declared valid selector in both rows",
            "partition selector and FAI universe",
        ),
        report.row(
            "07",
            scope_id,
            "manifest_identity_and_sample_order",
            manifest_identity and vcf_structure,
            f"samples={len(sample_ids)}",
            "manifest hashes, count, and VCF order reconcile",
            "immutable manifest identity",
        ),
        report.row(
            "07",
            scope_id,
            "vcf_record_counts",
            counts_ok,
            " ".join(
                f"{orientation}={count}" for orientation, _, _, count in vcf_readings
            ),
            "receipt paths and counts match exact VCFs",
            "transaction record counts",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, scope_id, step_id="07", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id="07",
                scope_id=f"{args.cohort_id}__{args.partition_id}",
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label="Step 07",
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, csv.Error, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
