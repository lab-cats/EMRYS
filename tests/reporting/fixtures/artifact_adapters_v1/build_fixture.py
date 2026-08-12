#!/usr/bin/env python3
"""Build a complete, temporary artifact-adapters-v1 fixture.

The tracked artifact inventory is the fixture's source of truth.  This builder
rewrites its 81 explicit source paths into a caller-owned temporary directory
and creates the smallest source accepted by each registered adapter.  Generated
pipeline-like artifacts stay untracked.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import zlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from norad.contracts.scientific_evidence import review_package, step09
from norad.reporting._artifact_index.binary_readers import BGZF_EOF_BLOCK
from norad.reporting._artifact_index.registry import ADAPTER_REGISTRY

REPO_ROOT = Path(__file__).resolve().parents[4]
INVENTORY_TEMPLATE = REPO_ROOT / "configs" / "artifact_inventory.example.tsv"
INVENTORY_HEADER = (
    "artifact_id",
    "step_id",
    "scope_type",
    "scope_id",
    "adapter",
    "source_path",
    "required",
)
RUN_ID = "synthetic_run"
SAMPLE_MANIFEST_SHA256 = "1" * 64
REFERENCE_CONTRACT_SHA256 = "2" * 64
PARTITION_MANIFEST_SHA256 = "3" * 64
PRIMARY_ANALYSIS_ID = "synthetic_analysis"
PRIMARY_ANALYSIS_POLICY_SHA256 = "4" * 64
COHORT_ID = "synthetic_cohort"
REVIEW_ID = "synthetic_review"


@dataclass(frozen=True)
class FixturePaths:
    """Paths and inventory metadata for one generated fixture."""

    root: Path
    run_id: str
    run_contract: Path
    inventory: Path
    source_root: Path
    output_root: Path
    inventory_rows: tuple[dict[str, str], ...]
    source_paths: Mapping[str, Path]

    @property
    def output_dir(self) -> Path:
        return self.output_root / self.run_id

    @property
    def records_dir(self) -> Path:
        return self.output_dir / "records"

    @property
    def artifacts_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.artifacts.tsv"

    @property
    def receipt_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.artifact_receipt.tsv"

    @property
    def lock_path(self) -> Path:
        return self.output_dir / f".{self.run_id}.artifact-index.lock"

    def command_args(self, *, execute: bool = False) -> list[str]:
        arguments = [
            "--source-checkout",
            str(REPO_ROOT),
            "--run-id",
            self.run_id,
            "--run-contract",
            str(self.run_contract),
            "--inventory",
            str(self.inventory),
            "--output-root",
            str(self.output_root),
        ]
        if execute:
            arguments.append("--execute")
        return arguments

    def source_for(self, artifact_id: str) -> Path:
        return self.source_paths[artifact_id]


def canonical_run_contract_sha256(components: Mapping[str, str]) -> str:
    payload = json.dumps(
        components,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_run_contract() -> dict[str, str]:
    components = {
        "sample_manifest_sha256": SAMPLE_MANIFEST_SHA256,
        "reference_contract_sha256": REFERENCE_CONTRACT_SHA256,
        "partition_manifest_sha256": PARTITION_MANIFEST_SHA256,
        "primary_analysis_id": PRIMARY_ANALYSIS_ID,
        "primary_analysis_policy_sha256": PRIMARY_ANALYSIS_POLICY_SHA256,
    }
    return {
        "run_contract_sha256": canonical_run_contract_sha256(components),
        **components,
    }


def read_inventory_template() -> list[dict[str, str]]:
    with INVENTORY_TEMPLATE.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != INVENTORY_HEADER:
            raise RuntimeError("Tracked artifact inventory header changed")
        rows = list(reader)
    if len(rows) != 81:
        raise RuntimeError(
            f"Expected 81 artifact rows in tracked inventory; found {len(rows)}"
        )
    return rows


def write_tsv(
    path: Path,
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def row_value(column: str) -> str:
    values = {
        "sample_id": "SYNTH_A",
        "cohort_id": COHORT_ID,
        "partition_id": "p1",
        "selector_type": "region",
        "selector_value": "1:1-100",
        "orientation": "FWD_like",
        "sample_manifest_sha256": SAMPLE_MANIFEST_SHA256,
        "reference_contract_sha256": REFERENCE_CONTRACT_SHA256,
        "partition_manifest_sha256": PARTITION_MANIFEST_SHA256,
        "analysis_id": PRIMARY_ANALYSIS_ID,
        "primary_analysis_id": PRIMARY_ANALYSIS_ID,
        "review_id": REVIEW_ID,
        "overall_science_status": "evidence_incomplete",
        "orientation_status": "provisional",
        "orientation_policy": "legacy_provisional_v1",
        "transaction_state": "complete",
        "sample_count": "1",
        "vcf_record_count": "1",
        "implementation_status": "implemented",
        "local_test_status": "passed",
        "runtime_validation_status": "blocked",
        "cluster_dry_run_status": "not_run",
        "cluster_proof_status": "not_run",
        "sample_manifest_path": "/synthetic/sample_manifest.tsv",
        "sample_manifest_row_count": "1",
        "partition_manifest_path": "/synthetic/partition_manifest.tsv",
        "partition_manifest_row_count": "2",
        "evidence_manifest_path": "/synthetic/evidence_manifest.tsv",
        "evidence_manifest_sha256": "6" * 64,
        "evidence_manifest_row_count": str(len(review_package.CATEGORY_ORDER)),
        "evidence_source_count": "0",
        "superseded_analysis_ids": "NA",
        "sensitivity_analysis_ids": "NA",
        "review_completed_date": "NA",
        "background_decision": "pending",
        "matched_dna_decision": "pending",
        "orthogonal_evidence_decision": "pending",
        "annotation_decision": "pending",
        "thresholds_decision": "pending",
        "adjudication_decision": "pending",
        "orientation_decision": "pending",
    }
    if column in {f"{category}_status" for category in review_package.CATEGORY_ORDER}:
        return "missing"
    if column.startswith("DP__"):
        return "10"
    if column.startswith("AD__"):
        return "1"
    if column.startswith("AF__"):
        return "0.1"
    return values.get(column, "fixture")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bgzf_block(payload: bytes) -> bytes:
    compressor = zlib.compressobj(level=6, wbits=-15)
    compressed = compressor.compress(payload) + compressor.flush()
    block_size = 18 + len(compressed) + 8
    if block_size > 65536:
        raise RuntimeError("Synthetic BGZF block is too large")
    return (
        b"\x1f\x8b\x08\x04"
        + b"\x00\x00\x00\x00"
        + b"\x00\xff"
        + struct.pack("<H", 6)
        + b"BC"
        + struct.pack("<H", 2)
        + struct.pack("<H", block_size - 1)
        + compressed
        + struct.pack(
            "<II",
            zlib.crc32(payload) & 0xFFFFFFFF,
            len(payload),
        )
    )


def minimal_bam_bytes() -> bytes:
    header_text = b"@HD\tVN:1.6\tSO:coordinate\n"
    payload = (
        b"BAM\x01"
        + struct.pack("<i", len(header_text))
        + header_text
        + struct.pack("<i", 0)
    )
    return bgzf_block(payload) + BGZF_EOF_BLOCK


def minimal_bai_bytes() -> bytes:
    return b"BAI\x01" + struct.pack("<I", 0) + struct.pack("<Q", 0)


def minimal_pdf_bytes() -> bytes:
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 72 72] >>"),
    )
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, value in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(
            f"{object_number} 0 obj\n".encode("ascii") + value + b"\nendobj\n"
        )
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


def inventory_row(
    rows: Sequence[Mapping[str, str]],
    adapter: str,
    *,
    scope_id: str | None = None,
) -> Mapping[str, str]:
    matches = [
        row
        for row in rows
        if row["adapter"] == adapter
        and (scope_id is None or row["scope_id"] == scope_id)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one inventory row for {adapter}/{scope_id}; "
            f"observed {len(matches)}"
        )
    return matches[0]


def sample_block_header(prefix: Sequence[str]) -> tuple[str, ...]:
    return (
        *prefix,
        "DP__SYNTH_A",
        "AD__SYNTH_A",
        "AF__SYNTH_A",
    )


def candidate_values(index: int) -> dict[str, str]:
    orientation = "FWD_like" if index % 2 else "REV_like"
    return {
        "partition_id": f"p{1 if index <= 2 else 2}",
        "candidate_id": f"candidate_{index}",
        "orientation": orientation,
        "chromosome": "1",
        "position": str(index * 10),
        "alt_index": "1",
        "genomic_ref": "T" if orientation == "FWD_like" else "A",
        "genomic_alt": "C" if orientation == "FWD_like" else "G",
        "rna_ref": "A",
        "rna_alt": "G",
        "annotation_strand": "+" if orientation == "FWD_like" else "-",
        "gene_ids": "GENE1",
        "transcript_ids": f"TX{index}",
        "is_cds": "TRUE",
        "is_five_prime_utr": "FALSE",
        "is_three_prime_utr": "FALSE",
        "is_exon": "TRUE",
        "is_intron": "FALSE",
        "qual": "60",
        "filter": "PASS",
        "info_alt_depth": "5",
        "orientation_policy": "legacy_provisional_v1",
        "DP__SYNTH_A": "10",
        "AD__SYNTH_A": "1",
        "AF__SYNTH_A": "0.1",
    }


def tsv_rows_for(
    row: Mapping[str, str],
    header: Sequence[str],
    exact_rows: int | None,
    inventory_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    adapter = row["adapter"]
    count_overrides = {
        "step08_sites_v1": 4,
        "step08_inputs_v1": 4,
        "step09_cmh_all_sites_v1": 4,
        "step09_cmh_significant_sites_v1": 1,
        "step09_mutation_spectrum_tsv_v1": 12,
        "step09c_evidence_index_v1": len(review_package.CATEGORY_ORDER),
        "step09c_orientation_locus_audit_v1": 0,
        "step09c_annotation_audit_v1": 0,
        "step09c_qc_funnel_v1": 0,
        "step09c_replicate_effects_v1": 0,
        "step09c_sensitivity_matrix_v1": 0,
        "step09c_leave_one_pair_out_v1": 0,
        "step09c_candidate_selection_v1": 0,
        "step09c_candidate_adjudication_v1": 0,
        "step09c_decisions_v1": 0,
        "step09c_limitations_v1": 0,
    }
    count = count_overrides.get(
        adapter,
        exact_rows if exact_rows is not None else 1,
    )
    rows = [{column: row_value(column) for column in header} for _ in range(count)]
    if adapter == "step06_orientation_counts_v1":
        rows[0].update(
            {
                "sample_id": "SYNTH_A",
                "input_records": "10",
                "flag_99_records": "3",
                "flag_147_records": "2",
                "flag_83_records": "2",
                "flag_163_records": "1",
                "fwd_like_records": "5",
                "rev_like_records": "3",
                "assigned_records": "8",
                "unassigned_records": "2",
                "assigned_fraction": "0.8",
            }
        )
    elif adapter in {
        "step00a_validation_report_v1",
        "step00b_validation_report_v1",
        "step00c_validation_report_v1",
        "step01_validation_report_v1",
        "step02_validation_report_v1",
        "step02b_validation_report_v1",
        "step03_validation_report_v1",
        "step04_validation_report_v1",
        "step05_validation_report_v1",
        "step06_validation_report_v1",
        "step07_validation_report_v1",
        "step08_validation_report_v1",
        "step09_validation_report_v1",
    }:
        check_ids = (
            (
                "index_members",
                "fasta_identity",
                "gtf_identity",
                "contig_names_lengths",
                "sjdb_overhang",
            )
            if adapter == "step00a_validation_report_v1"
            else (
                "bed12_structure",
                "coordinate_sorting",
                "block_structure",
                "unique_transcript_names",
                "gtf_transcript_agreement",
            )
            if adapter == "step00b_validation_report_v1"
            else (
                "fasta_structure",
                "fai_structure",
                "dict_structure",
                "fai_contig_agreement",
                "dict_contig_agreement",
            )
            if adapter == "step00c_validation_report_v1"
            else (
                "output_files",
                "bam_structure",
                "final_log_structure",
                "mapping_summary",
                "splice_junction_structure",
            )
            if adapter == "step01_validation_report_v1"
            else (
                "bam_bai_structure",
                "samtools_quickcheck",
                "coordinate_sorting",
                "read_group_header",
                "alignment_rg_tags",
            )
            if adapter == "step02_validation_report_v1"
            else (
                "quickcheck_structure",
                "flagstat_structure",
                "total_records",
                "mapped_records",
                "count_consistency",
            )
            if adapter == "step02b_validation_report_v1"
            else (
                "report_structure",
                "failed_fraction",
                "paired_orientation_fraction_a",
                "paired_orientation_fraction_b",
                "fraction_sum",
            )
            if adapter == "step03_validation_report_v1"
            else (
                "bam_bai_structure",
                "samtools_quickcheck",
                "coordinate_sorting",
                "read_group_preservation",
                "duplication_metrics",
            )
            if adapter == "step04_validation_report_v1"
            else (
                "output_containers",
                "counts_structure",
                "fwd_count_arithmetic",
                "rev_count_arithmetic",
                "assigned_count_arithmetic",
            )
            if adapter == "step06_validation_report_v1"
            else (
                "receipt_structure",
                "vcf_structure",
                "selector_reconciliation",
                "manifest_identity_and_sample_order",
                "vcf_record_counts",
            )
            if adapter == "step07_validation_report_v1"
            else (
                "output_transaction",
                "manifest_annotation_identity",
                "input_receipt_reconciliation",
                "sites_order_uniqueness",
                "summary_count_reconciliation",
            )
            if adapter == "step08_validation_report_v1"
            else (
                "output_transaction",
                "upstream_identity_and_candidate_order",
                "status_semantics",
                "significant_subset",
                "summary_count_reconciliation",
                "mutation_spectrum_reconciliation",
                "pdf_structure",
            )
            if adapter == "step09_validation_report_v1"
            else (
                "bam_bai_structure",
                "samtools_quickcheck",
                "coordinate_sorting",
                "read_group_preservation",
                "reference_sidecars",
            )
        )
        for output_row, check_id in zip(rows, check_ids, strict=True):
            output_row.update(
                {
                    "step_id": row["step_id"],
                    "scope_id": row["scope_id"],
                    "check_id": check_id,
                    "status": "pass",
                    "observed": "fixture",
                    "expected": "fixture",
                    "detail": "synthetic passing validation",
                }
            )
    elif adapter == "step07_mpileup_receipt_v1":
        partition = row["scope_id"].split("__", 1)[-1]
        vcfs = [
            candidate
            for candidate in inventory_rows
            if candidate["scope_id"] == row["scope_id"]
            and candidate["adapter"] == "step07_mpileup_vcf_v1"
        ]
        for output_row, vcf in zip(rows, vcfs, strict=True):
            orientation = (
                "FWD_like" if ".FWD_like." in vcf["source_path"] else "REV_like"
            )
            output_row.update(
                {
                    "cohort_id": COHORT_ID,
                    "partition_id": partition,
                    "selector_type": "region",
                    "selector_value": f"{partition[-1]}:1-100",
                    "orientation": orientation,
                    "vcf_path": vcf["source_path"],
                    "sample_manifest_sha256": SAMPLE_MANIFEST_SHA256,
                    "partition_manifest_sha256": PARTITION_MANIFEST_SHA256,
                    "sample_count": "1",
                    "vcf_record_count": "1",
                }
            )
    elif adapter == "step08_sites_v1":
        for index, output_row in enumerate(rows, start=1):
            output_row.update(candidate_values(index))
    elif adapter == "step08_inputs_v1":
        vcfs = [
            candidate
            for candidate in inventory_rows
            if candidate["adapter"] == "step07_mpileup_vcf_v1"
        ]
        for output_row, vcf in zip(rows, vcfs, strict=True):
            partition = vcf["scope_id"].split("__", 1)[-1]
            receipt = inventory_row(
                inventory_rows,
                "step07_mpileup_receipt_v1",
                scope_id=vcf["scope_id"],
            )
            orientation = (
                "FWD_like" if ".FWD_like." in vcf["source_path"] else "REV_like"
            )
            output_row.update(
                {
                    "cohort_id": COHORT_ID,
                    "partition_id": partition,
                    "selector_type": "region",
                    "selector_value": f"{partition[-1]}:1-100",
                    "orientation": orientation,
                    "step07_receipt_path": receipt["source_path"],
                    "step07_receipt_sha256": sha256_file(receipt["source_path"]),
                    "vcf_path": vcf["source_path"],
                    "vcf_sha256": sha256_file(vcf["source_path"]),
                    "sample_manifest_sha256": SAMPLE_MANIFEST_SHA256,
                    "partition_manifest_sha256": PARTITION_MANIFEST_SHA256,
                    "annotation_gtf": "/synthetic/annotation.gtf",
                    "annotation_gtf_sha256": "5" * 64,
                    "sample_count": "1",
                    "declared_vcf_record_count": "1",
                    "observed_vcf_record_count": "1",
                    "observed_alt_allele_count": "1",
                    "supported_snv_count": "1",
                    "skipped_symbolic_count": "0",
                    "skipped_non_snv_count": "0",
                    "published_candidate_count": "1",
                    "orientation_policy": "legacy_provisional_v1",
                }
            )
    elif adapter == "step08_summary_v1":
        rows[0].update(
            {
                "cohort_id": COHORT_ID,
                "partition_count": "2",
                "step07_receipt_count": "2",
                "input_vcf_count": "4",
                "sample_count": "1",
                "observed_vcf_record_count": "4",
                "observed_alt_allele_count": "4",
                "supported_snv_count": "4",
                "skipped_symbolic_count": "0",
                "skipped_non_snv_count": "0",
                "published_candidate_count": "4",
                "sample_manifest_sha256": SAMPLE_MANIFEST_SHA256,
                "partition_manifest_sha256": PARTITION_MANIFEST_SHA256,
                "annotation_gtf": "/synthetic/annotation.gtf",
                "annotation_gtf_sha256": "5" * 64,
                "orientation_policy": "legacy_provisional_v1",
            }
        )
    elif adapter in {
        "step09_cmh_all_sites_v1",
        "step09_cmh_significant_sites_v1",
    }:
        for index, output_row in enumerate(rows, start=1):
            output_row.update(candidate_values(index))
            output_row.update(
                {
                    "analysis_id": PRIMARY_ANALYSIS_ID,
                    "test_status": "tested",
                    "call_status": (
                        "significant_up"
                        if adapter == "step09_cmh_significant_sites_v1" or index == 1
                        else "effect_not_met"
                    ),
                    "orientation_policy": "legacy_provisional_v1",
                }
            )
    elif adapter == "step09_cmh_summary_v1":
        sites = inventory_row(inventory_rows, "step08_sites_v1")
        inputs = inventory_row(inventory_rows, "step08_inputs_v1")
        numeric = {column: "0" for column in header if column.endswith("_count")}
        rows[0].update(numeric)
        rows[0].update(
            {
                "analysis_id": PRIMARY_ANALYSIS_ID,
                "cohort_id": COHORT_ID,
                "sample_count": "1",
                "candidate_count": "4",
                "target_candidate_count": "4",
                "successfully_tested_count": "4",
                "effect_not_met_count": "3",
                "significant_up_count": "1",
                "significant_down_count": "0",
                "sample_manifest_sha256": SAMPLE_MANIFEST_SHA256,
                "partition_manifest_sha256": PARTITION_MANIFEST_SHA256,
                "step08_sites_path": sites["source_path"],
                "step08_sites_sha256": sha256_file(sites["source_path"]),
                "step08_inputs_path": inputs["source_path"],
                "step08_inputs_sha256": sha256_file(inputs["source_path"]),
                "orientation_policy": "legacy_provisional_v1",
            }
        )
    elif adapter == "step09_mutation_spectrum_tsv_v1":
        for output_row, mutation_type in zip(
            rows,
            step09.CANONICAL_MUTATIONS,
            strict=True,
        ):
            ref, alt = mutation_type.split(">")
            is_target = mutation_type == "A>G"
            output_row.update(
                {
                    "analysis_id": PRIMARY_ANALYSIS_ID,
                    "rna_ref": ref,
                    "rna_alt": alt,
                    "mutation_type": mutation_type,
                    "candidate_count": "4" if is_target else "0",
                    "candidate_fraction": "1" if is_target else "0",
                    "successfully_tested_count": "4" if is_target else "0",
                    "significant_up_count": "1" if is_target else "0",
                    "significant_down_count": "0",
                }
            )
    elif adapter == "step09c_evidence_index_v1":
        for output_row, category in zip(
            rows,
            review_package.CATEGORY_ORDER,
            strict=True,
        ):
            output_row.update(
                {
                    "review_id": REVIEW_ID,
                    "evidence_id": f"evidence_{category}",
                    "evidence_category": category,
                    "analysis_id": PRIMARY_ANALYSIS_ID,
                    "source_path": "NA",
                    "declared_sha256": "NA",
                    "observed_sha256": "NA",
                    "declared_row_count": "NA",
                    "observed_row_count": "NA",
                    "evidence_status": "missing",
                    "not_applicable_reason": "NA",
                    "reviewer": "synthetic_reviewer",
                    "owner": "synthetic_owner",
                    "evidence_date": "NA",
                    "policy_version": "synthetic_policy_v1",
                }
            )
    elif adapter == "step09c_review_summary_v1":
        plan = inventory_row(inventory_rows, "step09c_review_plan_v1")
        rows[0].update(
            {
                "review_id": REVIEW_ID,
                "primary_analysis_id": PRIMARY_ANALYSIS_ID,
                "overall_science_status": "evidence_incomplete",
                "orientation_status": "provisional",
                "orientation_policy": "legacy_provisional_v1",
                "evidence_record_count": str(len(review_package.CATEGORY_ORDER)),
                "evidence_source_count": "0",
                "selected_candidate_count": "0",
                "adjudicated_candidate_count": "0",
                "limitation_count": "0",
                "published_output_count": "13",
                "transaction_state": "complete",
                "review_plan_path": plan["source_path"],
                "review_plan_sha256": sha256_file(plan["source_path"]),
                "review_plan_row_count": "1",
            }
        )
        upstream = {
            "step08_sites": "step08_sites_v1",
            "step08_inputs": "step08_inputs_v1",
            "step08_summary": "step08_summary_v1",
            "step09_all_sites": "step09_cmh_all_sites_v1",
            "step09_significant_sites": ("step09_cmh_significant_sites_v1"),
            "step09_summary": "step09_cmh_summary_v1",
            "step09_mutation_spectrum": ("step09_mutation_spectrum_tsv_v1"),
            "step09_mutation_spectrum_pdf": ("step09_mutation_spectrum_pdf_v1"),
            "step09_depth_delta_pdf": "step09_depth_delta_pdf_v1",
        }
        row_counts = {
            "step08_sites": "4",
            "step08_inputs": "4",
            "step08_summary": "1",
            "step09_all_sites": "4",
            "step09_significant_sites": "1",
            "step09_summary": "1",
            "step09_mutation_spectrum": "12",
            "step09_mutation_spectrum_pdf": "NA",
            "step09_depth_delta_pdf": "NA",
        }
        for prefix, adapter_id in upstream.items():
            upstream_row = inventory_row(inventory_rows, adapter_id)
            rows[0][f"{prefix}_path"] = upstream_row["source_path"]
            rows[0][f"{prefix}_sha256"] = sha256_file(upstream_row["source_path"])
            rows[0][f"{prefix}_row_count"] = row_counts[prefix]
    return rows


def write_adapter_source(
    path: Path,
    row: Mapping[str, str],
    inventory_rows: Sequence[Mapping[str, str]],
) -> None:
    spec = ADAPTER_REGISTRY[row["adapter"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    if spec.kind == "star_index":
        if path.name in {"Genome", "SA", "SAindex"}:
            path.write_bytes(b"\x00synthetic STAR index\n")
        elif path.name == "genomeParameters.txt":
            path.write_text("sjdbOverhang 99\n", encoding="utf-8")
        else:
            path.write_text("synthetic STAR index\n", encoding="utf-8")
    elif spec.kind == "bed12":
        path.write_text(
            "1\t0\t10\ttx1\t0\t+\t0\t10\t0\t1\t10,\t0,\n",
            encoding="utf-8",
        )
    elif spec.kind == "fasta":
        path.write_text(">1\nACGTACGTAA\n", encoding="utf-8")
    elif spec.kind == "fai":
        path.write_text("1\t10\t3\t10\t11\n", encoding="utf-8")
    elif spec.kind == "dict":
        path.write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:10\n", encoding="utf-8")
    elif spec.kind == "bam":
        path.write_bytes(minimal_bam_bytes())
    elif spec.kind == "bai":
        path.write_bytes(minimal_bai_bytes())
    elif spec.kind == "quickcheck":
        path.write_text(
            "PASS: samtools quickcheck completed with no errors.\n",
            encoding="utf-8",
        )
    elif spec.kind == "flagstat":
        path.write_text(
            "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
            "8 + 0 mapped (80.00% : N/A)\n",
            encoding="utf-8",
        )
    elif spec.kind == "rseqc":
        path.write_text(
            "Fraction of reads failed to determine: 0.01\n"
            'Fraction of reads explained by "1++,1--,2+-,2-+": 0.97\n'
            'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n',
            encoding="utf-8",
        )
    elif spec.kind == "star_log_final":
        path.write_text(
            "Number of input reads | 100\n"
            "Uniquely mapped reads % | 95.00%\n"
            "% of reads mapped to multiple loci | 4.00%\n"
            "% of reads mapped to too many loci | 1.00%\n",
            encoding="utf-8",
        )
    elif spec.kind == "star_sj":
        path.write_text(
            "1\t10\t20\t1\t1\t0\t1\t0\t1\n",
            encoding="utf-8",
        )
    elif spec.kind == "picard_metrics":
        path.write_text(
            "## METRICS CLASS synthetic\n"
            "LIBRARY\tREAD_PAIRS_EXAMINED\tREAD_PAIR_DUPLICATES\tPERCENT_DUPLICATION\n"
            "synthetic\t10\t2\t0.2\n",
            encoding="utf-8",
        )
    elif spec.kind == "text":
        path.write_text("synthetic text output\n", encoding="utf-8")
    elif spec.kind == "vcf":
        path.write_text(
            "##fileformat=VCFv4.2\n"
            '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">\n'
            '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            '##FORMAT=<ID=ADF,Number=R,Type=Integer,Description="Forward depth">\n'
            '##FORMAT=<ID=ADR,Number=R,Type=Integer,Description="Reverse depth">\n'
            '##FORMAT=<ID=SP,Number=1,Type=Integer,Description="Strand bias">\n'
            '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            '##INFO=<ID=ADF,Number=R,Type=Integer,Description="Forward depth">\n'
            '##INFO=<ID=ADR,Number=R,Type=Integer,Description="Reverse depth">\n'
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH_A\n"
            "1\t10\t.\tA\tG\t60\tPASS\tAD=5,5;ADF=3,3;ADR=2,2"
            "\tDP:AD:ADF:ADR:SP\t10:5,5:3,3:2,2:0\n",
            encoding="utf-8",
        )
    elif spec.kind in {"tsv", "sample_blocks_tsv", "validation_report"}:
        if spec.expected_header is None:
            raise RuntimeError(f"Fixture TSV adapter lacks a header: {spec}")
        header = (
            sample_block_header(spec.expected_header)
            if spec.kind == "sample_blocks_tsv"
            else spec.expected_header
        )
        write_tsv(
            path,
            header,
            tsv_rows_for(row, header, spec.exact_data_rows, inventory_rows),
        )
    elif spec.kind == "pdf":
        path.write_bytes(minimal_pdf_bytes())
    else:
        raise RuntimeError(f"No fixture source writer for adapter kind {spec.kind!r}")


def build_fixture(root: Path, *, run_id: str = RUN_ID) -> FixturePaths:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    source_root = root / "source"
    inventory_path = root / "artifact_inventory.tsv"
    run_contract_path = root / "run_contract.json"
    output_root = root / "artifacts"

    template_rows = read_inventory_template()
    rewritten_rows: list[dict[str, str]] = []
    source_paths: dict[str, Path] = {}
    source_marker = "tests/fixtures/artifact_schema_v1/source/"
    for template_row in template_rows:
        relative = template_row["source_path"]
        if not relative.startswith(source_marker):
            raise RuntimeError(f"Unexpected tracked fixture source path: {relative}")
        source_path = source_root / relative.removeprefix(source_marker)
        rewritten = {**template_row, "source_path": str(source_path)}
        rewritten_rows.append(rewritten)
        source_paths[rewritten["artifact_id"]] = source_path

    for row in rewritten_rows:
        write_adapter_source(source_paths[row["artifact_id"]], row, rewritten_rows)

    write_tsv(inventory_path, INVENTORY_HEADER, rewritten_rows)
    run_contract_path.write_text(
        json.dumps(build_run_contract(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return FixturePaths(
        root=root,
        run_id=run_id,
        run_contract=run_contract_path,
        inventory=inventory_path,
        source_root=source_root,
        output_root=output_root,
        inventory_rows=tuple(rewritten_rows),
        source_paths=source_paths,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a complete temporary artifact-adapter fixture."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--run-id", default=RUN_ID)
    arguments = parser.parse_args()
    fixture = build_fixture(arguments.root, run_id=arguments.run_id)
    print(f"Fixture inventory: {fixture.inventory}")
    print(f"Fixture run contract: {fixture.run_contract}")
    print(f"Fixture output root: {fixture.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
