"""Validate one explicit Step 07 partitioned-cohort mpileup transaction."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from norad.libraries.alignments.orientation import ORIENTATIONS
from norad.libraries.validation import (
    Snapshot,
    add_output_arguments,
    build_report,
    lexical_path,
    read_tsv,
    run_from_args,
    sha256_file,
    snapshots,
)
from norad.libraries.validation.mpileup import (
    RECEIPT_HEADER,
    read_fai,
    read_partition,
    read_sample_ids,
    read_vcf,
    selector_ok,
)

DESCRIPTION = __doc__
CHECK_IDS = {
    "receipt_structure",
    "vcf_structure",
    "selector_reconciliation",
    "manifest_identity_and_sample_order",
    "vcf_record_counts",
}


@dataclass(frozen=True, slots=True)
class _VcfEvidence:
    orientation: str
    path: Path
    sample_ids: list[str]
    record_count: int


@dataclass(frozen=True, slots=True)
class _ParsedEvidence:
    sample_ids: list[str]
    selector_type: str
    selector_value: str
    contigs: dict[str, int]
    vcf_readings: tuple[_VcfEvidence, ...]
    receipt_header: list[str]
    receipt_rows: list[dict[str, str]]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add partitioned-cohort mpileup validator arguments to a parser."""
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--partition-id", required=True)
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--partition-manifest", required=True, type=Path)
    parser.add_argument("--reference-fai", required=True, type=Path)
    parser.add_argument("--fwd-vcf", required=True, type=Path)
    parser.add_argument("--rev-vcf", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    add_output_arguments(parser)


def _read_vcf_evidence(input_paths: dict[str, Path]) -> tuple[_VcfEvidence, ...]:
    readings = []
    for orientation, vcf_key in zip(
        ORIENTATIONS,
        ("fwd_vcf", "rev_vcf"),
        strict=True,
    ):
        sample_ids, record_count = read_vcf(input_paths[vcf_key])
        readings.append(
            _VcfEvidence(
                orientation=orientation,
                path=input_paths[vcf_key],
                sample_ids=sample_ids,
                record_count=record_count,
            )
        )
    return tuple(readings)


def _read_evidence(
    arguments: argparse.Namespace,
    input_paths: dict[str, Path],
) -> _ParsedEvidence:
    sample_ids = read_sample_ids(input_paths["sample_manifest"])
    selector_type, selector_value = read_partition(
        input_paths["partition_manifest"], arguments.partition_id
    )
    contigs = read_fai(input_paths["reference_fai"])
    vcf_readings = _read_vcf_evidence(input_paths)
    receipt_header, receipt_rows = read_tsv(input_paths["receipt"])
    return _ParsedEvidence(
        sample_ids=sample_ids,
        selector_type=selector_type,
        selector_value=selector_value,
        contigs=contigs,
        vcf_readings=vcf_readings,
        receipt_header=receipt_header,
        receipt_rows=receipt_rows,
    )


def _same_physical_file(recorded_path: str, admitted_path: Path) -> bool:
    try:
        return Path(recorded_path).samefile(admitted_path)
    except OSError:
        return False


def _build_checks(
    arguments: argparse.Namespace,
    input_paths: dict[str, Path],
    evidence: _ParsedEvidence,
) -> dict[str, tuple[bool, str, str, str]]:
    receipt_structure_valid = (
        tuple(evidence.receipt_header) == RECEIPT_HEADER
        and len(evidence.receipt_rows) == 2
        and tuple(row["orientation"] for row in evidence.receipt_rows) == ORIENTATIONS
        and all(
            row["cohort_id"] == arguments.cohort_id
            and row["partition_id"] == arguments.partition_id
            for row in evidence.receipt_rows
        )
    )
    vcf_structure_valid = all(
        reading.sample_ids == evidence.sample_ids for reading in evidence.vcf_readings
    )
    selector_reconciliation_valid = (
        selector_ok(
            evidence.selector_type,
            evidence.selector_value,
            input_paths["partition_manifest"],
            evidence.contigs,
        )
        and receipt_structure_valid
        and all(
            row["selector_type"] == evidence.selector_type
            and row["selector_value"] == evidence.selector_value
            for row in evidence.receipt_rows
        )
    )
    manifest_identity_valid = receipt_structure_valid and all(
        row["sample_manifest_sha256"] == sha256_file(input_paths["sample_manifest"])
        and row["partition_manifest_sha256"]
        == sha256_file(input_paths["partition_manifest"])
        and row["sample_count"].isdigit()
        and int(row["sample_count"]) == len(evidence.sample_ids)
        for row in evidence.receipt_rows
    )
    record_counts_valid = receipt_structure_valid and all(
        row["orientation"] == reading.orientation
        and _same_physical_file(row["vcf_path"], reading.path)
        and row["vcf_record_count"].isdigit()
        and int(row["vcf_record_count"]) == reading.record_count
        for row, reading in zip(
            evidence.receipt_rows,
            evidence.vcf_readings,
            strict=True,
        )
    )
    return {
        "receipt_structure": (
            receipt_structure_valid,
            f"rows={len(evidence.receipt_rows)}",
            f"exact header; {', '.join(ORIENTATIONS)} rows",
            "receipt transaction",
        ),
        "vcf_structure": (
            vcf_structure_valid,
            " ".join(
                f"{reading.orientation}={len(reading.sample_ids)}"
                for reading in evidence.vcf_readings
            )
            + " samples",
            "valid VCFs with manifest sample order",
            "explicit VCF structure",
        ),
        "selector_reconciliation": (
            selector_reconciliation_valid,
            f"{evidence.selector_type}={evidence.selector_value}",
            "declared valid selector in both rows",
            "partition selector and FAI universe",
        ),
        "manifest_identity_and_sample_order": (
            manifest_identity_valid and vcf_structure_valid,
            f"samples={len(evidence.sample_ids)}",
            "manifest hashes, count, and VCF order reconcile",
            "immutable manifest identity",
        ),
        "vcf_record_counts": (
            record_counts_valid,
            " ".join(
                f"{reading.orientation}={reading.record_count}"
                for reading in evidence.vcf_readings
            ),
            "receipt paths and counts match exact VCFs",
            "transaction record counts",
        ),
    }


def build_validation_report(
    arguments: argparse.Namespace,
) -> tuple[bytes, dict[Path, Snapshot]]:
    """Build the five-row Step 07 transaction report."""
    input_paths = {
        "sample_manifest": lexical_path(arguments.sample_manifest),
        "partition_manifest": lexical_path(arguments.partition_manifest),
        "reference_fai": lexical_path(arguments.reference_fai),
        "fwd_vcf": lexical_path(arguments.fwd_vcf),
        "rev_vcf": lexical_path(arguments.rev_vcf),
        "receipt": lexical_path(arguments.receipt),
    }
    input_snapshots = snapshots(input_paths, label="Step 07")
    evidence = _read_evidence(arguments, input_paths)
    scope_id = f"{arguments.cohort_id}__{arguments.partition_id}"
    return build_report(
        "07",
        scope_id,
        input_snapshots,
        CHECK_IDS,
        _build_checks(arguments, input_paths, evidence),
    )


def validate_from_args(arguments: argparse.Namespace) -> int:
    """Validate and report one parsed Step 07 transaction request."""
    return run_from_args(
        arguments,
        build_validation_report,
        "07",
        CHECK_IDS,
        scope_id=f"{arguments.cohort_id}__{arguments.partition_id}",
    )
