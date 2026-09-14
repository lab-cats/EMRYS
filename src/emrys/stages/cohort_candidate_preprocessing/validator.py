"""Validate one explicit Step 08 three-TSV transaction without invoking R."""

from __future__ import annotations

import argparse
from pathlib import Path

from emrys.contracts.scientific_evidence import step08
from emrys.libraries.alignments.orientation import validate_legacy_orientation_policy
from emrys.libraries.alignments.orientation import ORIENTATIONS
from emrys.libraries.validation.mpileup import RECEIPT_HEADER
from emrys.libraries.validation import (
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
    "manifest_annotation_identity",
    "input_receipt_reconciliation",
    "sites_order_uniqueness",
    "summary_count_reconciliation",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add cohort candidate preprocessing validator arguments to a parser."""
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--annotation-gtf", required=True, type=Path)
    parser.add_argument("--step07-root", type=Path)
    parser.add_argument("--sites", required=True, type=Path)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    add_output_arguments(parser)


def _reconcile_step07(
    arguments: argparse.Namespace,
    inputs: step08.Table,
    sample_ids: tuple[str, ...],
    partitions: list[dict[str, str]],
    sample_hash: str,
    partition_hash: str,
) -> None:
    for partition in partitions:
        partition_id = partition["partition_id"]
        prefix = f"{arguments.cohort_id}.{partition_id}"
        root = arguments.step07_root / arguments.cohort_id / partition_id
        receipt_path = root / f"{prefix}.step07_outputs.tsv"
        receipt = step08.read_tsv("Step 07 receipt", receipt_path, RECEIPT_HEADER)
        receipt_hash = step08.sha256_file(receipt_path)
        if len(receipt.rows) != 2:
            step08.fail("Step 07 receipt must contain exactly two orientation rows.")
        for upstream, orientation in zip(receipt.rows, ORIENTATIONS, strict=True):
            vcf = root / f"{prefix}.{orientation}.mpileup.vcf"
            row = next(
                item
                for item in inputs.rows
                if item["partition_id"] == partition_id
                and item["orientation"] == orientation
            )
            expected = {
                "cohort_id": arguments.cohort_id,
                **partition,
                "orientation": orientation,
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "sample_count": str(len(sample_ids)),
            }
            if (
                any(upstream[key] != value for key, value in expected.items())
                or not Path(upstream["vcf_path"]).samefile(vcf)
                or row["step07_receipt_path"] != str(receipt_path)
                or row["step07_receipt_sha256"] != receipt_hash
                or row["vcf_path"] != str(vcf)
                or row["vcf_sha256"] != step08.sha256_file(vcf)
                or step08.parse_nonnegative_int(
                    "Step 07 record count", upstream["vcf_record_count"]
                )
                != int(row["declared_vcf_record_count"])
            ):
                step08.fail(
                    "Step 08 input receipt differs from its admitted Step 07 inputs."
                )


def _build_checks(
    arguments: argparse.Namespace,
    input_paths: dict[str, Path],
) -> dict[str, tuple[bool, str, str, str]]:
    sample_result, sample_detail = step08.attempt(
        lambda: step08.validate_sample_manifest(input_paths["sample_manifest"]),
    )
    partition_table, partition_detail = step08.attempt(
        lambda: step08.validate_partition_manifest(input_paths["partition_manifest"]),
    )
    sample_hash = step08.sha256_file(input_paths["sample_manifest"])
    partition_hash = step08.sha256_file(input_paths["partition_manifest"])
    annotation_hash = step08.sha256_file(input_paths["annotation_gtf"])
    annotation_path_text = str(input_paths["annotation_gtf"].resolve())

    expected_sites_header = None
    if sample_result is not None:
        expected_sites_header = step08.sample_block_header(
            step08.STEP08_METADATA_HEADER,
            sample_result[1],
        )
    observed_headers, header_detail = step08.attempt(
        lambda: (
            read_header(input_paths["sites"]),
            read_header(input_paths["inputs"]),
            read_header(input_paths["summary"]),
        ),
    )
    transaction_valid = (
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
        inputs_table, inputs_detail = step08.attempt(
            lambda: step08.validate_step08_inputs(
                input_paths["inputs"],
                sample_result[1],
                partition_table.rows,
                sample_hash,
                partition_hash,
            ),
        )

    if inputs_table is not None and getattr(arguments, "step07_root", None) is not None:
        _, inputs_detail = step08.attempt(
            lambda: _reconcile_step07(
                arguments,
                inputs_table,
                sample_result[1],
                partition_table.rows,
                sample_hash,
                partition_hash,
            )
        )
        if inputs_detail != "validated":
            inputs_table = None

    identity_valid = False
    if inputs_table is not None:
        identity_valid = all(
            row["cohort_id"] == arguments.cohort_id
            and row["annotation_gtf"] == annotation_path_text
            and row["annotation_gtf_sha256"] == annotation_hash
            and validate_legacy_orientation_policy(row["orientation_policy"])[0]
            for row in inputs_table.rows
        )
        if not identity_valid:
            inputs_detail = "cohort, annotation identity, or policy mismatch"

    sites_table = None
    sites_detail = "prerequisite input receipt validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
    ):
        sites_table, sites_detail = step08.attempt(
            lambda: step08.validate_step08_sites(
                input_paths["sites"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
            ),
        )

    if (
        sites_table is not None
        and getattr(arguments, "step07_root", None) is not None
        and any(int(row["position"]) < 1 for row in sites_table.rows)
    ):
        sites_table = None
        sites_detail = "Step 08 sites positions must be positive."

    summary_table = None
    summary_detail = "prerequisite sites validation failed"
    if (
        sample_result is not None
        and partition_table is not None
        and inputs_table is not None
        and sites_table is not None
    ):
        summary_table, summary_detail = step08.attempt(
            lambda: step08.validate_step08_summary(
                input_paths["summary"],
                sample_result[1],
                partition_table.rows,
                inputs_table.rows,
                sites_table.rows,
                sample_hash,
                partition_hash,
            ),
        )
        if summary_table is not None:
            summary_row = summary_table.rows[0]
            if (
                summary_row["cohort_id"] != arguments.cohort_id
                or summary_row["annotation_gtf"] != annotation_path_text
                or summary_row["annotation_gtf_sha256"] != annotation_hash
                or not validate_legacy_orientation_policy(
                    summary_row["orientation_policy"]
                )[0]
            ):
                summary_table = None
                summary_detail = (
                    "summary cohort, annotation identity, or policy mismatch"
                )

    return {
        "output_transaction": (
            transaction_valid,
            header_detail,
            "three exact Step 08 TSV headers",
            "sites, inputs, and summary",
        ),
        "manifest_annotation_identity": (
            identity_valid,
            f"sample={sample_detail}; partition={partition_detail}",
            "cohort, manifest hashes, annotation path/hash, provisional policy",
            inputs_detail,
        ),
        "input_receipt_reconciliation": (
            inputs_table is not None,
            inputs_detail,
            "complete partition x orientation receipt",
            "ordered inputs, types, hashes, and per-row arithmetic",
        ),
        "sites_order_uniqueness": (
            sites_table is not None,
            sites_detail,
            "typed unique candidates and per-scope counts",
            "sites schema, sample columns, order, uniqueness, and AF arithmetic",
        ),
        "summary_count_reconciliation": (
            summary_table is not None,
            summary_detail,
            "one exact aggregate row matching inputs and sites",
            "three-output transaction count reconciliation",
        ),
    }


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 08 transaction report."""
    input_paths = {
        "sample_manifest": lexical_path(arguments.sample_manifest),
        "partition_manifest": lexical_path(arguments.partition_manifest),
        "annotation_gtf": lexical_path(arguments.annotation_gtf),
        "sites": lexical_path(arguments.sites),
        "inputs": lexical_path(arguments.inputs),
        "summary": lexical_path(arguments.summary),
    }
    input_snapshots = snapshots(input_paths, label="Step 08")
    return build_report(
        "08",
        arguments.cohort_id,
        input_snapshots,
        CHECK_IDS,
        _build_checks(arguments, input_paths),
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 08 transaction request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "08",
        CHECK_IDS,
        scope_id=arguments.cohort_id,
    )
