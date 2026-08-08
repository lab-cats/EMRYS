#!/usr/bin/env python3
"""Validate one explicit Step 09 six-output transaction without invoking R."""

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

from norad.contracts.scientific_evidence import step08, step09
from norad.libraries import validation as report
from norad.libraries.alignments import orientation as alignment_orientation

if step09.step08 is not step08:
    raise ImportError(
        "Step 09 contract and validator resolved different Step 08 objects"
    )

IS_LEGACY_ORIENTATION_POLICY = alignment_orientation.validate_legacy_orientation_policy


CHECK_IDS = {
    "output_transaction",
    "upstream_identity_and_candidate_order",
    "status_semantics",
    "significant_subset",
    "summary_count_reconciliation",
    "mutation_spectrum_reconciliation",
    "pdf_structure",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--step08-sites", required=True, type=Path)
    parser.add_argument("--step08-inputs", required=True, type=Path)
    parser.add_argument("--all-sites", required=True, type=Path)
    parser.add_argument("--significant-sites", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--mutation-spectrum", required=True, type=Path)
    parser.add_argument("--mutation-spectrum-pdf", required=True, type=Path)
    parser.add_argument("--depth-delta-pdf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace):
    paths = {
        "sample_manifest": report.lexical_path(args.sample_manifest),
        "partition_manifest": report.lexical_path(args.partition_manifest),
        "step08_sites": report.lexical_path(args.step08_sites),
        "step08_inputs": report.lexical_path(args.step08_inputs),
        "all_sites": report.lexical_path(args.all_sites),
        "significant_sites": report.lexical_path(args.significant_sites),
        "summary": report.lexical_path(args.summary),
        "mutation_spectrum": report.lexical_path(args.mutation_spectrum),
        "mutation_spectrum_pdf": report.lexical_path(args.mutation_spectrum_pdf),
        "depth_delta_pdf": report.lexical_path(args.depth_delta_pdf),
    }
    snapshots = report.snapshots(paths, label="Step 09")
    suffixes = {
        "all_sites": ".cmh_all_sites.tsv",
        "significant_sites": ".cmh_significant_sites.tsv",
        "summary": ".cmh_summary.tsv",
        "mutation_spectrum": ".mutation_spectrum.tsv",
        "mutation_spectrum_pdf": ".mutation_spectrum.pdf",
        "depth_delta_pdf": ".depth_delta.pdf",
    }
    native_paths = [paths[key] for key in suffixes]
    native_snapshots = [snapshots[path] for path in native_paths]
    transaction_ok = (
        all(
            paths[key].name == f"{args.analysis_id}{suffix}"
            for key, suffix in suffixes.items()
        )
        and len({path.parent for path in native_paths}) == 1
        and len({(snapshot.device, snapshot.inode) for snapshot in native_snapshots})
        == len(native_paths)
    )

    _, id_detail = report.attempt(
        lambda: (
            step08.validate_safe_id("analysis_id", args.analysis_id),
            step08.validate_safe_id("cohort_id", args.cohort_id),
        ),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    sample_result, sample_detail = report.attempt(
        lambda: step08.validate_sample_manifest(paths["sample_manifest"]),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    partition_table, partition_detail = report.attempt(
        lambda: step08.validate_partition_manifest(paths["partition_manifest"]),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    step08_inputs = None
    step08_input_detail = "manifest prerequisite failed"
    if sample_result is not None and partition_table is not None:
        step08_inputs, step08_input_detail = report.attempt(
            lambda: step08.validate_step08_inputs(
                paths["step08_inputs"],
                sample_result[1],
                partition_table.rows,
                step08.sha256_file(paths["sample_manifest"]),
                step08.sha256_file(paths["partition_manifest"]),
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
    cohort_policy_ok = step08_inputs is not None and all(
        row["cohort_id"] == args.cohort_id
        and IS_LEGACY_ORIENTATION_POLICY(row["orientation_policy"])[0]
        for row in step08_inputs.rows
    )
    if step08_inputs is not None and not cohort_policy_ok:
        step08_input_detail = f"explicit cohort identity or {alignment_orientation.LEGACY_PROVISIONAL_ORIENTATION_POLICY} policy mismatch"
    step08_sites = None
    step08_sites_detail = "Step 08 input prerequisite failed"
    if (
        sample_result is not None
        and partition_table is not None
        and step08_inputs is not None
    ):
        step08_sites, step08_sites_detail = report.attempt(
            lambda: step08.validate_step08_sites(
                paths["step08_sites"],
                sample_result[1],
                partition_table.rows,
                step08_inputs.rows,
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )

    expected_result_header = None
    if sample_result is not None:
        expected_result_header = (
            step09.STEP09_RESULT_HEADER
            + tuple(f"DP__{sample}" for sample in sample_result[1])
            + tuple(f"AD__{sample}" for sample in sample_result[1])
            + tuple(f"AF__{sample}" for sample in sample_result[1])
        )
    observed_headers, header_detail = report.attempt(
        lambda: (
            report.read_header(paths["all_sites"]),
            report.read_header(paths["significant_sites"]),
            report.read_header(paths["summary"]),
            report.read_header(paths["mutation_spectrum"]),
        ),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    transaction_ok = (
        transaction_ok
        and expected_result_header is not None
        and observed_headers
        == (
            expected_result_header,
            expected_result_header,
            step09.STEP09_SUMMARY_HEADER,
            step09.STEP09_MUTATION_HEADER,
        )
    )

    all_sites = None
    significant_sites = None
    result_detail = "Step 08 prerequisite failed"
    if sample_result is not None and step08_sites is not None:
        all_sites, all_detail = report.attempt(
            lambda: step09.validate_step09_results(
                "Step 09 all-sites",
                paths["all_sites"],
                sample_result[1],
                args.analysis_id,
                step08_sites.rows,
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
        significant_sites, significant_detail = report.attempt(
            lambda: step09.validate_step09_results(
                "Step 09 significant-sites",
                paths["significant_sites"],
                sample_result[1],
                args.analysis_id,
                step08_sites.rows,
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
        result_detail = f"all={all_detail}; significant={significant_detail}"
    candidate_order_ok = (
        all_sites is not None
        and step08_sites is not None
        and [row["candidate_id"] for row in all_sites.rows]
        == [row["candidate_id"] for row in step08_sites.rows]
    )
    if all_sites is not None and not candidate_order_ok:
        result_detail = "all-sites candidate order/universe differs from Step 08"

    summary = None
    summary_detail = "result or upstream prerequisite failed"
    if (
        sample_result is not None
        and step08_inputs is not None
        and all_sites is not None
    ):
        summary, summary_detail = report.attempt(
            lambda: step09.validate_step09_summary(
                paths["summary"],
                args.analysis_id,
                args.cohort_id,
                sample_result[1],
                sample_result[2],
                all_sites.rows,
                paths["sample_manifest"],
                paths["partition_manifest"],
                paths["step08_sites"],
                paths["step08_inputs"],
                step08.sha256_file(paths["sample_manifest"]),
                step08.sha256_file(paths["partition_manifest"]),
                step08.sha256_file(paths["step08_sites"]),
                step08.sha256_file(paths["step08_inputs"]),
                step08_inputs.rows[0]["orientation_policy"],
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
    semantic_ok = False
    semantic_detail = "result or summary prerequisite failed"
    if summary is not None and all_sites is not None and sample_result is not None:
        _, semantic_detail = report.attempt(
            lambda: step09.validate_step09_result_semantics(
                all_sites.rows, summary.rows[0], sample_result[2]
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
        semantic_ok = semantic_detail == "validated"

    subset_ok = False
    subset_detail = "result prerequisite failed"
    if all_sites is not None and significant_sites is not None:
        subset_result, subset_detail = report.attempt(
            lambda: step09.validate_significant_subset(
                all_sites.rows, significant_sites.rows
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )
        subset_ok = subset_detail == "validated"

    mutation = None
    mutation_detail = "all-sites prerequisite failed"
    if all_sites is not None:
        mutation, mutation_detail = report.attempt(
            lambda: step09.validate_mutation_spectrum(
                paths["mutation_spectrum"], args.analysis_id, all_sites.rows
            ),
            catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
        )

    _, mutation_pdf_detail = report.attempt(
        lambda: step09.validate_pdf(
            "Step 09 mutation-spectrum PDF", paths["mutation_spectrum_pdf"]
        ),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    _, depth_pdf_detail = report.attempt(
        lambda: step09.validate_pdf(
            "Step 09 depth-delta PDF", paths["depth_delta_pdf"]
        ),
        catches=(OSError, UnicodeError, csv.Error, step08.ContractError),
    )
    pdf_ok = mutation_pdf_detail == depth_pdf_detail == "validated"
    scope_id = args.analysis_id

    rows = [
        report.row(
            "09",
            scope_id,
            "output_transaction",
            transaction_ok,
            f"headers={header_detail}; six regular snapshots",
            "four exact TSV headers; analysis-bound basenames; one parent; "
            "six distinct physical files",
            "native Step 09 output transaction",
        ),
        report.row(
            "09",
            scope_id,
            "upstream_identity_and_candidate_order",
            (
                id_detail == "validated"
                and cohort_policy_ok
                and candidate_order_ok
                and significant_sites is not None
            ),
            result_detail,
            "safe analysis/cohort; provisional policy; complete ordered "
            "Step 08 candidate universe",
            f"ids={id_detail}; sample={sample_detail}; "
            f"partition={partition_detail}; inputs={step08_input_detail}; "
            f"sites={step08_sites_detail}",
        ),
        report.row(
            "09",
            scope_id,
            "status_semantics",
            semantic_ok,
            semantic_detail,
            "recomputed target/test/call, depth, AF, background, CMH, and BH",
            "native Step 09 statistical-state contract",
        ),
        report.row(
            "09",
            scope_id,
            "significant_subset",
            subset_ok,
            subset_detail,
            "exact ordered significant subset",
            "all-sites versus significant-sites",
        ),
        report.row(
            "09",
            scope_id,
            "summary_count_reconciliation",
            summary is not None,
            summary_detail,
            "one analysis/cohort-bound summary with exact counts and provenance",
            "paths, hashes, pairings, context, policy, and thresholds",
        ),
        report.row(
            "09",
            scope_id,
            "mutation_spectrum_reconciliation",
            mutation is not None,
            mutation_detail,
            "canonical 12-SNV spectrum matching all-sites",
            "mutation counts, fractions, and significant directions",
        ),
        report.row(
            "09",
            scope_id,
            "pdf_structure",
            pdf_ok,
            f"mutation={mutation_pdf_detail}; depth={depth_pdf_detail}",
            "two structurally valid PDFs",
            "plot output containers",
        ),
    ]
    data = report.render(rows)
    report.validate_report(data, scope_id, step_id="09", check_ids=CHECK_IDS)
    return data, snapshots


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build(args)
        return report.finish(
            report.Runtime(
                step_id="09",
                scope_id=args.analysis_id,
                check_ids=CHECK_IDS,
                output=args.output,
                execute=args.execute,
                published_label="Step 09",
            ),
            data,
            snapshots,
        )
    except (OSError, UnicodeError, csv.Error, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
