"""Validate one explicit Step 09 six-output transaction without invoking R."""

from __future__ import annotations

import argparse
from pathlib import Path

from norad.contracts.scientific_evidence import step08, step09
from norad.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY,
    validate_legacy_orientation_policy,
)
from norad.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    lexical_path,
    read_header,
    run_from_args,
    snapshots,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "output_transaction",
    "upstream_identity_and_candidate_order",
    "status_semantics",
    "significant_subset",
    "summary_count_reconciliation",
    "mutation_spectrum_reconciliation",
    "pdf_structure",
}

InputPaths = dict[str, Path]
InputSnapshots = dict[Path, Snapshot]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add paired-CMH candidate-ranking validator arguments to a parser."""
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
    add_output_arguments(parser)


def _prepare_transaction(
    arguments: argparse.Namespace,
) -> tuple[InputPaths, InputSnapshots, bool]:
    paths = {
        "sample_manifest": lexical_path(arguments.sample_manifest),
        "partition_manifest": lexical_path(arguments.partition_manifest),
        "step08_sites": lexical_path(arguments.step08_sites),
        "step08_inputs": lexical_path(arguments.step08_inputs),
        "all_sites": lexical_path(arguments.all_sites),
        "significant_sites": lexical_path(arguments.significant_sites),
        "summary": lexical_path(arguments.summary),
        "mutation_spectrum": lexical_path(arguments.mutation_spectrum),
        "mutation_spectrum_pdf": lexical_path(arguments.mutation_spectrum_pdf),
        "depth_delta_pdf": lexical_path(arguments.depth_delta_pdf),
    }
    input_snapshots = snapshots(paths, label="Step 09")
    suffixes = {
        "all_sites": ".cmh_all_sites.tsv",
        "significant_sites": ".cmh_significant_sites.tsv",
        "summary": ".cmh_summary.tsv",
        "mutation_spectrum": ".mutation_spectrum.tsv",
        "mutation_spectrum_pdf": ".mutation_spectrum.pdf",
        "depth_delta_pdf": ".depth_delta.pdf",
    }
    native_paths = [paths[key] for key in suffixes]
    native_snapshots = [input_snapshots[path] for path in native_paths]
    transaction_valid = (
        all(
            paths[key].name == f"{arguments.analysis_id}{suffix}"
            for key, suffix in suffixes.items()
        )
        and len({path.parent for path in native_paths}) == 1
        and len({(item.device, item.inode) for item in native_snapshots})
        == len(native_paths)
    )
    return paths, input_snapshots, transaction_valid


def _validate_pdfs(paths: InputPaths) -> tuple[bool, str, str]:
    _, mutation_detail = step08.attempt(
        lambda: step09.validate_pdf(
            "Step 09 mutation-spectrum PDF",
            paths["mutation_spectrum_pdf"],
        ),
    )
    _, depth_detail = step08.attempt(
        lambda: step09.validate_pdf(
            "Step 09 depth-delta PDF",
            paths["depth_delta_pdf"],
        ),
    )
    return mutation_detail == depth_detail == "validated", mutation_detail, depth_detail


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, InputSnapshots]:
    """Build one Step 09 validation report and its immutable input snapshots."""
    paths, input_snapshots, transaction_valid = _prepare_transaction(arguments)

    _, id_detail = step08.attempt(
        lambda: (
            step08.validate_safe_id("analysis_id", arguments.analysis_id),
            step08.validate_safe_id("cohort_id", arguments.cohort_id),
        ),
    )
    sample_result, sample_detail = step08.attempt(
        lambda: step08.validate_sample_manifest(paths["sample_manifest"]),
    )
    partition_table, partition_detail = step08.attempt(
        lambda: step08.validate_partition_manifest(paths["partition_manifest"]),
    )
    step08_inputs = None
    step08_input_detail = "manifest prerequisite failed"
    if sample_result is not None and partition_table is not None:
        step08_inputs, step08_input_detail = step08.attempt(
            lambda: step08.validate_step08_inputs(
                paths["step08_inputs"],
                sample_result[1],
                partition_table.rows,
                step08.sha256_file(paths["sample_manifest"]),
                step08.sha256_file(paths["partition_manifest"]),
            ),
        )
    cohort_policy_valid = step08_inputs is not None and all(
        row["cohort_id"] == arguments.cohort_id
        and validate_legacy_orientation_policy(row["orientation_policy"])[0]
        for row in step08_inputs.rows
    )
    if step08_inputs is not None and not cohort_policy_valid:
        step08_input_detail = (
            "explicit cohort identity or "
            f"{LEGACY_PROVISIONAL_ORIENTATION_POLICY} policy mismatch"
        )
    step08_sites = None
    step08_sites_detail = "Step 08 input prerequisite failed"
    if (
        sample_result is not None
        and partition_table is not None
        and step08_inputs is not None
    ):
        step08_sites, step08_sites_detail = step08.attempt(
            lambda: step08.validate_step08_sites(
                paths["step08_sites"],
                sample_result[1],
                partition_table.rows,
                step08_inputs.rows,
            ),
        )

    expected_result_header = (
        step08.sample_block_header(
            step09.STEP09_RESULT_HEADER,
            sample_result[1],
        )
        if sample_result is not None
        else None
    )
    observed_headers, header_detail = step08.attempt(
        lambda: (
            read_header(paths["all_sites"]),
            read_header(paths["significant_sites"]),
            read_header(paths["summary"]),
            read_header(paths["mutation_spectrum"]),
        ),
    )
    transaction_valid = (
        transaction_valid
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
        all_sites, all_detail = step08.attempt(
            lambda: step09.validate_step09_results(
                "Step 09 all-sites",
                paths["all_sites"],
                sample_result[1],
                arguments.analysis_id,
                step08_sites.rows,
            ),
        )
        significant_sites, significant_detail = step08.attempt(
            lambda: step09.validate_step09_results(
                "Step 09 significant-sites",
                paths["significant_sites"],
                sample_result[1],
                arguments.analysis_id,
                step08_sites.rows,
            ),
        )
        result_detail = f"all={all_detail}; significant={significant_detail}"
    candidate_order_valid = (
        all_sites is not None
        and step08_sites is not None
        and [row["candidate_id"] for row in all_sites.rows]
        == [row["candidate_id"] for row in step08_sites.rows]
    )
    if all_sites is not None and not candidate_order_valid:
        result_detail = "all-sites candidate order/universe differs from Step 08"

    summary = None
    summary_detail = "result or upstream prerequisite failed"
    if (
        sample_result is not None
        and step08_inputs is not None
        and all_sites is not None
    ):
        summary, summary_detail = step08.attempt(
            lambda: step09.validate_step09_summary(
                paths["summary"],
                arguments.analysis_id,
                arguments.cohort_id,
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
        )
    semantic_detail = "result or summary prerequisite failed"
    if summary is not None and all_sites is not None and sample_result is not None:
        _, semantic_detail = step08.attempt(
            lambda: step09.validate_step09_result_semantics(
                all_sites.rows,
                summary.rows[0],
                sample_result[2],
            ),
        )
    semantic_valid = semantic_detail == "validated"

    subset_detail = "result prerequisite failed"
    if all_sites is not None and significant_sites is not None:
        _, subset_detail = step08.attempt(
            lambda: step09.validate_significant_subset(
                all_sites.rows,
                significant_sites.rows,
            ),
        )
    subset_valid = subset_detail == "validated"

    mutation_spectrum = None
    mutation_detail = "all-sites prerequisite failed"
    if all_sites is not None:
        mutation_spectrum, mutation_detail = step08.attempt(
            lambda: step09.validate_mutation_spectrum(
                paths["mutation_spectrum"],
                arguments.analysis_id,
                all_sites.rows,
            ),
        )

    pdf_valid, mutation_pdf_detail, depth_pdf_detail = _validate_pdfs(paths)
    return build_report(
        "09",
        arguments.analysis_id,
        input_snapshots,
        CHECK_IDS,
        {
            "output_transaction": (
                transaction_valid,
                f"headers={header_detail}; six regular snapshots",
                "four exact TSV headers; analysis-bound basenames; one parent; "
                "six distinct physical files",
                "native Step 09 output transaction",
            ),
            "upstream_identity_and_candidate_order": (
                (
                    id_detail == "validated"
                    and cohort_policy_valid
                    and candidate_order_valid
                    and significant_sites is not None
                ),
                result_detail,
                "safe analysis/cohort; provisional policy; complete ordered "
                "Step 08 candidate universe",
                f"ids={id_detail}; sample={sample_detail}; "
                f"partition={partition_detail}; inputs={step08_input_detail}; "
                f"sites={step08_sites_detail}",
            ),
            "status_semantics": (
                semantic_valid,
                semantic_detail,
                "recomputed target/test/call, depth, AF, background, CMH, and BH",
                "native Step 09 statistical-state contract",
            ),
            "significant_subset": (
                subset_valid,
                subset_detail,
                "exact ordered significant subset",
                "all-sites versus significant-sites",
            ),
            "summary_count_reconciliation": (
                summary is not None,
                summary_detail,
                "one analysis/cohort-bound summary with exact counts and provenance",
                "paths, hashes, pairings, context, policy, and thresholds",
            ),
            "mutation_spectrum_reconciliation": (
                mutation_spectrum is not None,
                mutation_detail,
                "canonical 12-SNV spectrum matching all-sites",
                "mutation counts, fractions, and significant directions",
            ),
            "pdf_structure": (
                pdf_valid,
                f"mutation={mutation_pdf_detail}; depth={depth_pdf_detail}",
                "two structurally valid PDFs",
                "plot output containers",
            ),
        },
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed paired-CMH candidate-ranking request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "09",
        CHECK_IDS,
        scope_id=arguments.analysis_id,
    )
