#!/usr/bin/env python3
"""Validate one explicit Step 08 three-TSV transaction without invoking R."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Callable, Sequence, TypeVar


_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from norad.libraries import validation as report

from norad.contracts.scientific_evidence import step08


CHECK_IDS = {
    "output_transaction",
    "manifest_annotation_identity",
    "input_receipt_reconciliation",
    "sites_order_uniqueness",
    "summary_count_reconciliation",
}
T = TypeVar("T")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--annotation-gtf", required=True, type=Path)
    parser.add_argument("--sites", required=True, type=Path)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def attempt(function: Callable[[], T]) -> tuple[T | None, str]:
    try:
        return function(), "validated"
    except (OSError, UnicodeError, csv.Error, step08.ContractError) as exc:
        return None, report.clean(exc)


def header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(next(csv.reader(stream, delimiter="\t")))


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": args.sample_manifest.resolve(strict=False),
        "partition_manifest": args.partition_manifest.resolve(strict=False),
        "annotation_gtf": args.annotation_gtf.resolve(strict=False),
        "sites": args.sites.resolve(strict=False),
        "inputs": args.inputs.resolve(strict=False),
        "summary": args.summary.resolve(strict=False),
    }
    snapshots = {
        path: report.regular_snapshot(path, f"Step 08 {role}")
        for role, path in paths.items()
    }
    sample_result, sample_detail = attempt(
        lambda: step08.validate_sample_manifest(paths["sample_manifest"])
    )
    partition_table, partition_detail = attempt(
        lambda: step08.validate_partition_manifest(paths["partition_manifest"])
    )
    sample_hash = step08.sha256_file(paths["sample_manifest"])
    partition_hash = step08.sha256_file(paths["partition_manifest"])
    annotation_hash = step08.sha256_file(paths["annotation_gtf"])

    expected_sites_header = None
    if sample_result is not None:
        expected_sites_header = (
            step08.STEP08_METADATA_HEADER
            + tuple(f"DP__{sample}" for sample in sample_result[1])
            + tuple(f"AD__{sample}" for sample in sample_result[1])
            + tuple(f"AF__{sample}" for sample in sample_result[1])
        )
    observed_headers, header_detail = attempt(
        lambda: (
            header(paths["sites"]),
            header(paths["inputs"]),
            header(paths["summary"]),
        )
    )
    transaction_ok = (
        observed_headers is not None
        and expected_sites_header is not None
        and observed_headers
        == (
            expected_sites_header,
            step08.STEP08_INPUTS_HEADER,
            step08.STEP08_SUMMARY_HEADER,
        )
    )

    inputs_table = None
    inputs_detail = "prerequisite manifest validation failed"
    if sample_result is not None and partition_table is not None:
        inputs_table, inputs_detail = attempt(
            lambda: step08.validate_step08_inputs(
                paths["inputs"],
                sample_result[1],
                partition_table.rows,
                sample_hash,
                partition_hash,
            )
        )
    identity_ok = False
    if inputs_table is not None:
        identity_ok = all(
            row["cohort_id"] == args.cohort_id
            and row["annotation_gtf"] == str(paths["annotation_gtf"])
            and row["annotation_gtf_sha256"] == annotation_hash
            and row["orientation_policy"] == "legacy_provisional_v1"
            for row in inputs_table.rows
        )
        if not identity_ok:
            inputs_detail = "cohort, annotation identity, or policy mismatch"

    sites_table = None
    sites_detail = "prerequisite input receipt validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
    ):
        sites_table, sites_detail = attempt(
            lambda: step08.validate_step08_sites(
                paths["sites"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
            )
        )

    summary_table = None
    summary_detail = "prerequisite sites validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
        and sites_table is not None
    ):
        summary_table, summary_detail = attempt(
            lambda: step08.validate_step08_summary(
                paths["summary"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
                sites_table.rows,
                sample_hash,
                partition_hash,
            )
        )
        if summary_table is not None:
            row = summary_table.rows[0]
            if (
                row["cohort_id"] != args.cohort_id
                or row["annotation_gtf"] != str(paths["annotation_gtf"])
                or row["annotation_gtf_sha256"] != annotation_hash
                or row["orientation_policy"] != "legacy_provisional_v1"
            ):
                summary_table = None
                summary_detail = "summary cohort, annotation identity, or policy mismatch"

    scope_id = args.cohort_id

    def item(check_id: str, passed: bool, observed: object, expected: str, detail: str):
        return (
            "08", scope_id, check_id, "pass" if passed else "fail",
            report.clean(observed), report.clean(expected), report.clean(detail),
        )

    rows = [
        item("output_transaction", transaction_ok, header_detail,
             "three exact Step 08 TSV headers", "sites, inputs, and summary"),
        item("manifest_annotation_identity", identity_ok,
             f"sample={sample_detail}; partition={partition_detail}",
             "cohort, manifest hashes, annotation path/hash, provisional policy",
             inputs_detail),
        item("input_receipt_reconciliation", inputs_table is not None,
             inputs_detail, "complete partition x orientation receipt",
             "ordered inputs, types, hashes, and per-row arithmetic"),
        item("sites_order_uniqueness", sites_table is not None,
             sites_detail, "typed unique candidates and per-scope counts",
             "sites schema, sample columns, order, uniqueness, and AF arithmetic"),
        item("summary_count_reconciliation", summary_table is not None,
             summary_detail, "one exact aggregate row matching inputs and sites",
             "three-output transaction count reconciliation"),
    ]
    data = report.render(rows)
    report.validate_report(data, scope_id, step_id="08", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id='08',
                scope_id=args.cohort_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label='Step 08',
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, csv.Error, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
