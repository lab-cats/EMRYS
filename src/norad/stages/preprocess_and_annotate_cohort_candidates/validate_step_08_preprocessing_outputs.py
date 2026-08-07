#!/usr/bin/env python3
"""Validate one explicit Step 08 three-TSV transaction without invoking R."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence


_SRC_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "src")
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from norad.libraries import validation as report
from norad.libraries.alignments import orientation as alignment_orientation

from norad.contracts.scientific_evidence import step08


CHECK_IDS = {
    "output_transaction",
    "manifest_annotation_identity",
    "input_receipt_reconciliation",
    "sites_order_uniqueness",
    "summary_count_reconciliation",
}
IS_LEGACY_ORIENTATION_POLICY = alignment_orientation.validate_legacy_orientation_policy


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


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": report.lexical_path(args.sample_manifest),
        "partition_manifest": report.lexical_path(args.partition_manifest),
        "annotation_gtf": report.lexical_path(args.annotation_gtf),
        "sites": report.lexical_path(args.sites),
        "inputs": report.lexical_path(args.inputs),
        "summary": report.lexical_path(args.summary),
    }
    snapshots = report.snapshots(paths, label="Step 08")
    sample_result, sample_detail = report.attempt(
        lambda: step08.validate_sample_manifest(paths["sample_manifest"]),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    partition_table, partition_detail = report.attempt(
        lambda: step08.validate_partition_manifest(paths["partition_manifest"]),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    sample_hash = step08.sha256_file(paths["sample_manifest"])
    partition_hash = step08.sha256_file(paths["partition_manifest"])
    annotation_hash = step08.sha256_file(paths["annotation_gtf"])
    annotation_path_text = str(paths["annotation_gtf"].resolve())

    expected_sites_header = None
    if sample_result is not None:
        expected_sites_header = (
            step08.STEP08_METADATA_HEADER
            + tuple(f"DP__{sample}" for sample in sample_result[1])
            + tuple(f"AD__{sample}" for sample in sample_result[1])
            + tuple(f"AF__{sample}" for sample in sample_result[1])
        )
    observed_headers, header_detail = report.attempt(
        lambda: (
            report.read_header(paths["sites"]),
            report.read_header(paths["inputs"]),
            report.read_header(paths["summary"]),
        ),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
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
        inputs_table, inputs_detail = report.attempt(
            lambda: step08.validate_step08_inputs(
                paths["inputs"],
                sample_result[1],
                partition_table.rows,
                sample_hash,
                partition_hash,
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
    identity_ok = False
    if inputs_table is not None:
        identity_ok = all(
            row["cohort_id"] == args.cohort_id
            and row["annotation_gtf"] == annotation_path_text
            and row["annotation_gtf_sha256"] == annotation_hash
            and IS_LEGACY_ORIENTATION_POLICY(row["orientation_policy"])[0]
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
        sites_table, sites_detail = report.attempt(
            lambda: step08.validate_step08_sites(
                paths["sites"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )

    summary_table = None
    summary_detail = "prerequisite sites validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
        and sites_table is not None
    ):
        summary_table, summary_detail = report.attempt(
            lambda: step08.validate_step08_summary(
                paths["summary"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
                sites_table.rows,
                sample_hash,
                partition_hash,
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
        if summary_table is not None:
            row = summary_table.rows[0]
            if (
                row["cohort_id"] != args.cohort_id
                or row["annotation_gtf"] != annotation_path_text
                or row["annotation_gtf_sha256"] != annotation_hash
                or not IS_LEGACY_ORIENTATION_POLICY(row["orientation_policy"])[0]
            ):
                summary_table = None
                summary_detail = "summary cohort, annotation identity, or policy mismatch"

    scope_id = args.cohort_id

    rows = [
        report.row(
            "08", scope_id, "output_transaction", transaction_ok,
            header_detail, "three exact Step 08 TSV headers",
            "sites, inputs, and summary",
        ),
        report.row(
            "08", scope_id, "manifest_annotation_identity", identity_ok,
            f"sample={sample_detail}; partition={partition_detail}",
            "cohort, manifest hashes, annotation path/hash, provisional policy",
            inputs_detail,
        ),
        report.row(
            "08", scope_id, "input_receipt_reconciliation", inputs_table is not None,
            inputs_detail, "complete partition x orientation receipt",
            "ordered inputs, types, hashes, and per-row arithmetic",
        ),
        report.row(
            "08", scope_id, "sites_order_uniqueness", sites_table is not None,
            sites_detail, "typed unique candidates and per-scope counts",
            "sites schema, sample columns, order, uniqueness, and AF arithmetic",
        ),
        report.row(
            "08", scope_id, "summary_count_reconciliation", summary_table is not None,
            summary_detail, "one exact aggregate row matching inputs and sites",
            "three-output transaction count reconciliation",
        ),
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
