"""Stable definitions for the neutral Step 08 scientific-evidence contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from norad.libraries.alignments import orientation as alignment_orientation


class ContractError(RuntimeError):
    """Raised when an explicit scientific-review contract is invalid."""


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NA_VALUE = "NA"
ORIENTATIONS = alignment_orientation.ORIENTATIONS
STEP08_METADATA_HEADER = (
    "partition_id",
    "candidate_id",
    "orientation",
    "chromosome",
    "position",
    "alt_index",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "annotation_strand",
    "gene_ids",
    "transcript_ids",
    "is_cds",
    "is_five_prime_utr",
    "is_three_prime_utr",
    "is_exon",
    "is_intron",
    "qual",
    "filter",
    "info_alt_depth",
    "orientation_policy",
)

STEP08_INPUTS_HEADER = (
    "cohort_id",
    "partition_id",
    "selector_type",
    "selector_value",
    "orientation",
    "step07_receipt_path",
    "step07_receipt_sha256",
    "vcf_path",
    "vcf_sha256",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "annotation_gtf",
    "annotation_gtf_sha256",
    "sample_count",
    "declared_vcf_record_count",
    "observed_vcf_record_count",
    "observed_alt_allele_count",
    "supported_snv_count",
    "skipped_symbolic_count",
    "skipped_non_snv_count",
    "published_candidate_count",
    "orientation_policy",
)

STEP08_SUMMARY_HEADER = (
    "cohort_id",
    "partition_count",
    "step07_receipt_count",
    "input_vcf_count",
    "sample_count",
    "observed_vcf_record_count",
    "observed_alt_allele_count",
    "supported_snv_count",
    "skipped_symbolic_count",
    "skipped_non_snv_count",
    "published_candidate_count",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "annotation_gtf",
    "annotation_gtf_sha256",
    "orientation_policy",
)
STEP08_AGGREGATE_COUNT_FIELDS = STEP08_SUMMARY_HEADER[5:10]
STEP08_PARTITION_COUNT_FIELDS = STEP08_SUMMARY_HEADER[5:11]

SAMPLE_MANIFEST_REQUIRED = (
    "sample_id",
    "r1_fastq",
    "r2_fastq",
    "strandedness",
    "condition",
    "replicate",
)
SAMPLE_MANIFEST_ALLOWED = SAMPLE_MANIFEST_REQUIRED + ("notes",)
PARTITION_MANIFEST_HEADER = (
    "partition_id",
    "selector_type",
    "selector_value",
)


@dataclass
class Table:
    header: tuple[str, ...]
    rows: list[dict[str, str]]
    path: Path
