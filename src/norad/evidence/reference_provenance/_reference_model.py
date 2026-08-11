"""Shared contracts for reference-provenance inventory and output handling."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from norad.libraries import validation as report

PROFILE_HEADER = (
    "reference_id",
    "artifact_id",
    "role",
    "path",
    "required",
    "expected_sha256",
    "provenance_source",
    "provenance_release",
    "notes",
)
ARTIFACT_HEADER = (
    "reference_id",
    "artifact_id",
    "role",
    "declared_path",
    "resolved_path",
    "required",
    "status",
    "observed_sha256",
    "expected_sha256",
    "size_bytes",
    "provenance_source",
    "provenance_release",
    "detail",
)
CONTIG_HEADER = (
    "reference_id",
    "source_role",
    "ordinal",
    "contig",
    "length",
    "status",
    "detail",
)
SUMMARY_HEADER = (
    "reference_id",
    "profile_sha256",
    "artifact_count",
    "required_missing_count",
    "hash_mismatch_count",
    "invalid_artifact_count",
    "fasta_contig_count",
    "fai_agreement",
    "dict_agreement",
    "gtf_contigs_within_fasta",
    "bed12_contigs_within_fasta",
    "star_agreement",
    "overall_status",
)
OUTPUT_SPECS = (
    ("artifacts", "reference_artifacts.tsv", ARTIFACT_HEADER, None),
    ("contigs", "reference_contigs.tsv", CONTIG_HEADER, None),
    ("summary", "reference_summary.tsv", SUMMARY_HEADER, 1),
)
CONTIG_ROLES = ("fasta", "fai", "dict", "gtf", "bed12", "star")
ROLES = {
    "fasta",
    "fai",
    "dict",
    "gtf",
    "bed12",
    "star_chr_name",
    "star_chr_length",
    "star_index_file",
}
SINGLETON_ROLES = {
    "fasta",
    "fai",
    "dict",
    "gtf",
    "bed12",
    "star_chr_name",
    "star_chr_length",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceError(report.ValidationError):
    pass


@dataclass(frozen=True)
class Item:
    reference_id: str
    artifact_id: str
    role: str
    declared_path: str
    path: Path
    required: bool
    expected_sha256: str
    provenance_source: str
    provenance_release: str
    notes: str


@dataclass
class Observation:
    item: Item
    status: str
    digest: str = "NA"
    size: str = "NA"
    detail: str = ""


def fail(message: str) -> None:
    raise ProvenanceError(message)
