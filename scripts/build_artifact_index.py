#!/usr/bin/env python3
"""Build a read-only, explicit artifact index for one immutable NORAD run.

The command never discovers pipeline inputs, invokes analysis software, or
changes native Step 00a-09c outputs.  Every source comes from one validated
inventory row.  Dry-run is the default; execute mode publishes one JSON record
per row, an inventory-ordered TSV index, and a receipt last as a
rollback-protected transaction.
"""

from __future__ import annotations

import argparse
import csv
import errno
import hashlib
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import uuid
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

import step_09c_scientific_validation as step09c
import validate_artifact_contracts as contracts


PRODUCER = "build_artifact_index"
PRODUCER_VERSION = "1.0.0"
ARTIFACT_SCHEMA_VERSION = "1.0.0"
ARTIFACT_INDEX_SCHEMA_VERSION = "1.0.0"
ARTIFACT_RECEIPT_SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RUN_CONTRACT_FIELDS = (
    "run_contract_sha256",
    "sample_manifest_sha256",
    "reference_contract_sha256",
    "partition_manifest_sha256",
    "primary_analysis_id",
    "primary_analysis_policy_sha256",
)
ANCHOR_HASH_FIELDS = (
    "sample_manifest_sha256",
    "partition_manifest_sha256",
)
STEP09C_CATEGORY_ADAPTERS = {
    category: f"step09c_{category}_v1"
    for category in step09c.CATEGORY_ORDER
}

ARTIFACT_INDEX_HEADER = (
    "run_id",
    "run_contract_sha256",
    "artifact_id",
    "step_id",
    "scope_type",
    "scope_id",
    "adapter",
    "source_path",
    "required",
    "availability_status",
    "completion_status",
    "attempt_provenance_status",
    "selected_attempt_id",
    "implementation_status",
    "local_test_status",
    "runtime_validation_status",
    "cluster_dry_run_status",
    "cluster_proof_status",
    "science_status",
    "orientation_status",
    "orientation_policy",
    "review_id",
    "source_sha256",
    "source_size_bytes",
    "source_row_count",
    "source_media_type",
    "warning_count",
    "error_count",
    "record_path",
    "record_sha256",
    "record_schema_version",
)

ARTIFACT_RECEIPT_HEADER = (
    "run_id",
    "run_contract_sha256",
    "run_contract_path",
    "run_contract_file_sha256",
    "sample_manifest_sha256",
    "reference_contract_sha256",
    "partition_manifest_sha256",
    "primary_analysis_id",
    "primary_analysis_policy_sha256",
    "inventory_path",
    "inventory_sha256",
    "inventory_row_count",
    "artifact_schema_version",
    "artifact_index_schema_version",
    "artifact_receipt_schema_version",
    "artifacts_index_path",
    "artifacts_index_sha256",
    "artifact_record_count",
    "record_set_sha256",
    "required_artifact_count",
    "required_missing_artifact_count",
    "present_artifact_count",
    "missing_artifact_count",
    "externally_unavailable_artifact_count",
    "unknown_artifact_count",
    "complete_artifact_count",
    "not_attempted_artifact_count",
    "in_progress_artifact_count",
    "incomplete_artifact_count",
    "failed_artifact_count",
    "warning_count",
    "error_count",
    "published_output_count",
    "adapter_attempt_id",
    "supersedes_adapter_attempt_id",
    "adapter_attempt_history",
    "producer",
    "producer_version",
    "git_commit",
    "started_at",
    "finished_at",
    "transaction_state",
)

STEP07_RECEIPT_HEADER = (
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

STEP06_COUNTS_HEADER = (
    "sample_id",
    "input_records",
    "flag_99_records",
    "flag_147_records",
    "flag_83_records",
    "flag_163_records",
    "fwd_like_records",
    "rev_like_records",
    "assigned_records",
    "unassigned_records",
    "assigned_fraction",
)

STEP00A_BASENAMES = (
    "genomeParameters.txt",
    "Genome",
    "SA",
    "SAindex",
    "chrLength.txt",
    "chrName.txt",
    "chrNameLength.txt",
    "chrStart.txt",
    "exonGeTrInfo.tab",
    "exonInfo.tab",
    "geneInfo.tab",
    "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab",
    "sjdbList.out.tab",
    "transcriptInfo.tab",
)
VALIDATION_REPORT_HEADER = (
    "step_id",
    "scope_id",
    "check_id",
    "status",
    "observed",
    "expected",
    "detail",
)


class ArtifactIndexError(RuntimeError):
    """Raised when the explicit adapter/index contract cannot be honored."""


@dataclass(frozen=True)
class AdapterSpec:
    adapter_id: str
    step_id: str
    scope_type: str
    kind: str
    media_type: str
    suffixes: tuple[str, ...] = ()
    basenames: tuple[str, ...] = ()
    expected_header: tuple[str, ...] | None = None
    exact_data_rows: int | None = None
    allow_header_only: bool = True


@dataclass(frozen=True)
class SourceSnapshot:
    status: str
    sha256: str | None
    size_bytes: int | None
    file_type: str
    link_target: str | None = None
    device: int | None = None
    inode: int | None = None
    mtime_ns: int | None = None
    ctime_ns: int | None = None


@dataclass(frozen=True)
class LockOwnership:
    device: int
    inode: int
    run_token: str


@dataclass
class Inspection:
    row: dict[str, str]
    spec: AdapterSpec
    resolved_path: Path
    availability_status: str
    completion_status: str
    state_reason: str | None
    attempt_provenance_status: str
    source: dict[str, Any] | None
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    native: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    first_row: dict[str, str] | None = None
    snapshot: SourceSnapshot | None = None


@dataclass
class BuildContext:
    run_id: str
    run_contract_path: Path
    run_contract: dict[str, Any]
    run_contract_file_sha256: str
    inventory_path: Path
    inventory_sha256: str
    inventory_rows: list[dict[str, str]]
    output_root: Path
    output_dir: Path
    records_dir: Path
    artifacts_path: Path
    receipt_path: Path
    lock_path: Path
    git_commit: str
    producer_evidence: dict[str, dict[str, Any]]
    inspections: list[Inspection]
    records: list[dict[str, Any]]
    record_bytes: list[bytes]
    index_rows: list[dict[str, str]]
    index_bytes: bytes
    receipt_row: dict[str, str]
    receipt_bytes: bytes
    started_at: str
    attempt_id: str
    previous_attempt_id: str | None
    attempt_history: list[str]
    previous_receipt: dict[str, str] | None


def add_spec(
    registry: dict[str, AdapterSpec],
    adapter_id: str,
    step_id: str,
    scope_type: str,
    kind: str,
    media_type: str,
    *,
    suffixes: Sequence[str] = (),
    basenames: Sequence[str] = (),
    expected_header: Sequence[str] | None = None,
    exact_data_rows: int | None = None,
    allow_header_only: bool = True,
) -> None:
    registry[adapter_id] = AdapterSpec(
        adapter_id=adapter_id,
        step_id=step_id,
        scope_type=scope_type,
        kind=kind,
        media_type=media_type,
        suffixes=tuple(suffixes),
        basenames=tuple(basenames),
        expected_header=(
            tuple(expected_header) if expected_header is not None else None
        ),
        exact_data_rows=exact_data_rows,
        allow_header_only=allow_header_only,
    )


def build_adapter_registry() -> dict[str, AdapterSpec]:
    registry: dict[str, AdapterSpec] = {}
    add_spec(
        registry,
        "step00a_star_index_v1",
        "00a",
        "reference",
        "star_index",
        "application/octet-stream",
        basenames=STEP00A_BASENAMES,
    )
    add_spec(
        registry,
        "step00a_validation_report_v1",
        "00a",
        "reference",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step00b_bed12_v1",
        "00b",
        "reference",
        "bed12",
        "text/bed",
        suffixes=(".bed",),
    )
    add_spec(
        registry,
        "step00b_validation_report_v1",
        "00b",
        "reference",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step00c_reference_fasta_v1",
        "00c",
        "reference",
        "fasta",
        "text/x-fasta",
        suffixes=(".fa", ".fasta"),
    )
    add_spec(
        registry,
        "step00c_reference_fai_v1",
        "00c",
        "reference",
        "fai",
        "text/tab-separated-values",
        suffixes=(".fai",),
    )
    add_spec(
        registry,
        "step00c_reference_dict_v1",
        "00c",
        "reference",
        "dict",
        "text/vnd.sam",
        suffixes=(".dict",),
    )
    add_spec(
        registry,
        "step00c_validation_report_v1",
        "00c",
        "reference",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step01_star_bam_v1",
        "01",
        "sample",
        "bam",
        "application/x-bam",
        suffixes=(".bam",),
    )
    for adapter_id, suffix, kind in (
        ("step01_star_log_final_v1", ".Log.final.out", "star_log_final"),
        ("step01_star_log_v1", ".Log.out", "text"),
        ("step01_star_log_progress_v1", ".Log.progress.out", "text"),
        ("step01_star_sj_v1", ".SJ.out.tab", "star_sj"),
    ):
        add_spec(
            registry,
            adapter_id,
            "01",
            "sample",
            kind,
            "text/plain",
            suffixes=(suffix,),
        )
    add_spec(
        registry,
        "step01_validation_report_v1",
        "01",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    for step_id, bam_adapter, bai_adapter, bam_suffix in (
        ("02", "step02_canonical_bam_v1", "step02_canonical_bai_v1", ".sorted.bam"),
        ("04", "step04_markdup_bam_v1", "step04_markdup_bai_v1", ".markdup.bam"),
        ("05", "step05_split_bam_v1", "step05_split_bai_v1", ".split_ncigar.bam"),
    ):
        add_spec(
            registry,
            bam_adapter,
            step_id,
            "sample",
            "bam",
            "application/x-bam",
            suffixes=(bam_suffix,),
        )
        add_spec(
            registry,
            bai_adapter,
            step_id,
            "sample",
            "bai",
            "application/octet-stream",
            suffixes=(f"{bam_suffix}.bai",),
        )
    add_spec(
        registry,
        "step02_validation_report_v1",
        "02",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step02b_quickcheck_v1",
        "02b",
        "sample",
        "quickcheck",
        "text/plain",
        suffixes=(".quickcheck.txt",),
    )
    add_spec(
        registry,
        "step02b_flagstat_v1",
        "02b",
        "sample",
        "flagstat",
        "text/plain",
        suffixes=(".flagstat.txt",),
    )
    add_spec(
        registry,
        "step02b_validation_report_v1",
        "02b",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step03_rseqc_infer_v1",
        "03",
        "sample",
        "rseqc",
        "text/plain",
        suffixes=(".infer_experiment.txt",),
    )
    add_spec(
        registry,
        "step03_validation_report_v1",
        "03",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step04_markdup_metrics_v1",
        "04",
        "sample",
        "picard_metrics",
        "text/plain",
        suffixes=(".markdup.metrics.txt",),
    )
    add_spec(
        registry,
        "step04_validation_report_v1",
        "04",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step05_validation_report_v1",
        "05",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step06_validation_report_v1",
        "06",
        "sample",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    for adapter_id, suffix in (
        ("step06_fwd_bam_v1", ".FWD_like.bam"),
        ("step06_rev_bam_v1", ".REV_like.bam"),
    ):
        add_spec(
            registry,
            adapter_id,
            "06",
            "sample",
            "bam",
            "application/x-bam",
            suffixes=(suffix,),
        )
    for adapter_id, suffix in (
        ("step06_fwd_bai_v1", ".FWD_like.bam.bai"),
        ("step06_rev_bai_v1", ".REV_like.bam.bai"),
    ):
        add_spec(
            registry,
            adapter_id,
            "06",
            "sample",
            "bai",
            "application/octet-stream",
            suffixes=(suffix,),
        )
    add_spec(
        registry,
        "step06_orientation_counts_v1",
        "06",
        "sample",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".orientation_counts.tsv",),
        expected_header=STEP06_COUNTS_HEADER,
        exact_data_rows=1,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step07_mpileup_vcf_v1",
        "07",
        "cohort_partition",
        "vcf",
        "text/vcf",
        suffixes=(".mpileup.vcf",),
    )
    add_spec(
        registry,
        "step07_mpileup_receipt_v1",
        "07",
        "cohort_partition",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".step07_outputs.tsv",),
        expected_header=STEP07_RECEIPT_HEADER,
        exact_data_rows=2,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step07_validation_report_v1",
        "07",
        "cohort_partition",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step08_sites_v1",
        "08",
        "cohort",
        "sample_blocks_tsv",
        "text/tab-separated-values",
        suffixes=(".step08_sites.tsv",),
        expected_header=step09c.STEP08_METADATA_HEADER,
    )
    add_spec(
        registry,
        "step08_inputs_v1",
        "08",
        "cohort",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".step08_inputs.tsv",),
        expected_header=step09c.STEP08_INPUTS_HEADER,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step08_summary_v1",
        "08",
        "cohort",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".step08_summary.tsv",),
        expected_header=step09c.STEP08_SUMMARY_HEADER,
        exact_data_rows=1,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step08_validation_report_v1",
        "08",
        "cohort",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=5,
        allow_header_only=False,
    )
    for adapter_id, suffix in (
        ("step09_cmh_all_sites_v1", ".cmh_all_sites.tsv"),
        ("step09_cmh_significant_sites_v1", ".cmh_significant_sites.tsv"),
    ):
        add_spec(
            registry,
            adapter_id,
            "09",
            "analysis",
            "sample_blocks_tsv",
            "text/tab-separated-values",
            suffixes=(suffix,),
            expected_header=step09c.STEP09_RESULT_HEADER,
        )
    add_spec(
        registry,
        "step09_cmh_summary_v1",
        "09",
        "analysis",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".cmh_summary.tsv",),
        expected_header=step09c.STEP09_SUMMARY_HEADER,
        exact_data_rows=1,
        allow_header_only=False,
    )
    add_spec(
        registry,
        "step09_mutation_spectrum_tsv_v1",
        "09",
        "analysis",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".mutation_spectrum.tsv",),
        expected_header=step09c.STEP09_MUTATION_HEADER,
    )
    for adapter_id, suffix in (
        ("step09_mutation_spectrum_pdf_v1", ".mutation_spectrum.pdf"),
        ("step09_depth_delta_pdf_v1", ".depth_delta.pdf"),
    ):
        add_spec(
            registry,
            adapter_id,
            "09",
            "analysis",
            "pdf",
            "application/pdf",
            suffixes=(suffix,),
        )
    add_spec(
        registry,
        "step09_validation_report_v1",
        "09",
        "analysis",
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=7,
        allow_header_only=False,
    )
    step09c_specs = (
        (
            "step09c_review_plan_v1",
            ".step09c_review_plan.tsv",
            step09c.REVIEW_PLAN_HEADER,
            1,
        ),
        (
            "step09c_evidence_index_v1",
            ".step09c_evidence_index.tsv",
            step09c.EVIDENCE_INDEX_HEADER,
            None,
        ),
        (
            "step09c_orientation_locus_audit_v1",
            ".step09c_orientation_locus_audit.tsv",
            step09c.ORIENTATION_HEADER,
            None,
        ),
        (
            "step09c_annotation_audit_v1",
            ".step09c_annotation_audit.tsv",
            step09c.ANNOTATION_HEADER,
            None,
        ),
        (
            "step09c_qc_funnel_v1",
            ".step09c_qc_funnel.tsv",
            step09c.QC_FUNNEL_HEADER,
            None,
        ),
        (
            "step09c_replicate_effects_v1",
            ".step09c_replicate_effects.tsv",
            step09c.REPLICATE_EFFECTS_HEADER,
            None,
        ),
        (
            "step09c_sensitivity_matrix_v1",
            ".step09c_sensitivity_matrix.tsv",
            step09c.SENSITIVITY_HEADER,
            None,
        ),
        (
            "step09c_leave_one_pair_out_v1",
            ".step09c_leave_one_pair_out.tsv",
            step09c.LEAVE_ONE_OUT_HEADER,
            None,
        ),
        (
            "step09c_candidate_selection_v1",
            ".step09c_candidate_selection.tsv",
            step09c.CANDIDATE_SELECTION_HEADER,
            None,
        ),
        (
            "step09c_candidate_adjudication_v1",
            ".step09c_candidate_adjudication.tsv",
            step09c.CANDIDATE_ADJUDICATION_HEADER,
            None,
        ),
        (
            "step09c_decisions_v1",
            ".step09c_decisions.tsv",
            step09c.DECISIONS_HEADER,
            None,
        ),
        (
            "step09c_limitations_v1",
            ".step09c_limitations.tsv",
            step09c.LIMITATIONS_HEADER,
            None,
        ),
        (
            "step09c_review_summary_v1",
            ".step09c_review_summary.tsv",
            step09c.REVIEW_SUMMARY_HEADER,
            1,
        ),
    )
    for adapter_id, suffix, header, exact_rows in step09c_specs:
        add_spec(
            registry,
            adapter_id,
            "09c",
            "scientific_review",
            "tsv",
            "text/tab-separated-values",
            suffixes=(suffix,),
            expected_header=header,
            exact_data_rows=exact_rows,
            allow_header_only=exact_rows is None,
        )
    return registry


ADAPTER_REGISTRY = build_adapter_registry()

SCOPE_ADAPTER_ROSTERS: dict[str, Counter[str]] = {
    "00a": Counter(
        {
            "step00a_star_index_v1": 15,
            "step00a_validation_report_v1": 1,
        }
    ),
    "00b": Counter(
        {"step00b_bed12_v1": 1, "step00b_validation_report_v1": 1}
    ),
    "00c": Counter({
        "step00c_reference_fasta_v1": 1,
        "step00c_reference_fai_v1": 1,
        "step00c_reference_dict_v1": 1,
        "step00c_validation_report_v1": 1,
    }),
    "01": Counter(
        {
            "step01_star_bam_v1": 1,
            "step01_star_log_final_v1": 1,
            "step01_star_log_v1": 1,
            "step01_star_log_progress_v1": 1,
            "step01_star_sj_v1": 1,
            "step01_validation_report_v1": 1,
        }
    ),
    "02": Counter({
        "step02_canonical_bam_v1": 1,
        "step02_canonical_bai_v1": 1,
        "step02_validation_report_v1": 1,
    }),
    "02b": Counter({
        "step02b_quickcheck_v1": 1,
        "step02b_flagstat_v1": 1,
        "step02b_validation_report_v1": 1,
    }),
    "03": Counter({
        "step03_rseqc_infer_v1": 1,
        "step03_validation_report_v1": 1,
    }),
    "04": Counter(
        {
            "step04_markdup_bam_v1": 1,
            "step04_markdup_bai_v1": 1,
            "step04_markdup_metrics_v1": 1,
            "step04_validation_report_v1": 1,
        }
    ),
    "05": Counter(
        {
            "step05_split_bam_v1": 1,
            "step05_split_bai_v1": 1,
            "step05_validation_report_v1": 1,
        }
    ),
    "06": Counter(
        {
            "step06_fwd_bam_v1": 1,
            "step06_fwd_bai_v1": 1,
            "step06_rev_bam_v1": 1,
            "step06_rev_bai_v1": 1,
            "step06_orientation_counts_v1": 1,
            "step06_validation_report_v1": 1,
        }
    ),
    "07": Counter(
        {
            "step07_mpileup_vcf_v1": 2,
            "step07_mpileup_receipt_v1": 1,
            "step07_validation_report_v1": 1,
        }
    ),
    "08": Counter(
        {
            "step08_sites_v1": 1,
            "step08_inputs_v1": 1,
            "step08_summary_v1": 1,
            "step08_validation_report_v1": 1,
        }
    ),
    "09": Counter(
        {
            "step09_cmh_all_sites_v1": 1,
            "step09_cmh_significant_sites_v1": 1,
            "step09_cmh_summary_v1": 1,
            "step09_mutation_spectrum_tsv_v1": 1,
            "step09_mutation_spectrum_pdf_v1": 1,
            "step09_depth_delta_pdf_v1": 1,
            "step09_validation_report_v1": 1,
        }
    ),
    "09c": Counter(
        {
            "step09c_review_plan_v1": 1,
            "step09c_evidence_index_v1": 1,
            "step09c_orientation_locus_audit_v1": 1,
            "step09c_annotation_audit_v1": 1,
            "step09c_qc_funnel_v1": 1,
            "step09c_replicate_effects_v1": 1,
            "step09c_sensitivity_matrix_v1": 1,
            "step09c_leave_one_pair_out_v1": 1,
            "step09c_candidate_selection_v1": 1,
            "step09c_candidate_adjudication_v1": 1,
            "step09c_decisions_v1": 1,
            "step09c_limitations_v1": 1,
            "step09c_review_summary_v1": 1,
        }
    ),
}

STEP_PRODUCERS = {
    "00a": (
        "src/norad/stages/construct_STAR_index/"
        "step_00a_build_novogene_star_index.slurm"
    ),
    "00b": "src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py",
    "00c": (
        "src/norad/stages/construct_FASTA_sidecars/"
        "step_00c_prepare_gatk_reference.sh"
    ),
    "01": (
        "src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh"
    ),
    "02": (
        "src/norad/stages/construct_canonical_BAM/"
        "step_02_sort_index_bam.sh"
    ),
    "02b": (
        "src/norad/evidence/collect_canonical_BAM_QC_evidence/"
        "step_02b_bam_qc.sh"
    ),
    "03": (
        "src/norad/evidence/collect_RSeQC_paired_orientation_evidence/"
        "step_03_infer_strandedness_and_orientation.sh"
    ),
    "04": "scripts/step_04_mark_duplicates.sh",
    "05": "scripts/step_05_split_n_cigar_reads.sh",
    "06": "scripts/step_06_split_bam_by_read_orientation.sh",
    "07": "scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh",
    "08": "scripts/step_08_vcf_preprocessing.sh",
    "09": "scripts/step_09_cmh_editing_site_calling.sh",
    "09c": "scripts/step_09c_scientific_validation.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an explicit read-only NORAD artifact index. Dry-run is "
            "the default; add --execute to publish the receipt-last "
            "transaction."
        )
    )
    parser.add_argument("--run-id", required=True, help="Immutable run ID.")
    parser.add_argument(
        "--run-contract",
        required=True,
        type=Path,
        help=(
            "Strict JSON file containing exactly the six-field canonical "
            "run contract."
        ),
    )
    parser.add_argument(
        "--inventory",
        required=True,
        type=Path,
        help="Explicit expected-artifact inventory TSV.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish records, index, and receipt. Default is dry-run.",
    )
    return parser.parse_args()


def safe_tsv(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return " ".join(text.replace("\t", " ").splitlines()).strip()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is not None:
        try:
            timestamp = int(source_date_epoch)
        except ValueError as exc:
            raise ArtifactIndexError(
                "SOURCE_DATE_EPOCH must be an integer when set"
            ) from exc
        value = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    else:
        value = datetime.now(tz=timezone.utc)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_attempt_id(timestamp: str) -> str:
    compact = re.sub(r"[^0-9]", "", timestamp)[:14]
    return f"artifact-index-{compact}-{uuid.uuid4().hex[:12]}"


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=contracts.REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ArtifactIndexError(
            f"Could not resolve the current Git commit: {exc}"
        ) from exc
    value = result.stdout.strip()
    if not contracts.SAFE_ID_RE.fullmatch(value):
        raise ArtifactIndexError(f"Resolved Git commit is invalid: {value!r}")
    return value


def load_run_contract(path: Path) -> tuple[dict[str, Any], str]:
    resolved = path.expanduser().resolve()
    document = contracts.load_json_object(resolved, "run contract")
    if len(document) != len(RUN_CONTRACT_FIELDS) or set(document) != set(
        RUN_CONTRACT_FIELDS
    ):
        raise ArtifactIndexError(
            "Run contract must contain exactly these fields: "
            + ", ".join(RUN_CONTRACT_FIELDS)
        )
    _schemas, registry = contracts.load_schema_registry()
    wrapper_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "urn:norad:schema:artifacts:common:v1#/$defs/run_contract",
    }
    validator = Draft202012Validator(
        wrapper_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: "
            f"{error.message}"
            for error in errors
        )
        raise ArtifactIndexError(f"Run contract failed validation:\n{detail}")
    try:
        contracts.validate_run_contract(document, "artifact index")
    except contracts.ContractValidationError as exc:
        raise ArtifactIndexError(str(exc)) from exc
    return document, contracts.sha256_file(resolved)


def validate_inventory_registry(rows: Sequence[dict[str, str]]) -> None:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        adapter_id = row["adapter"]
        spec = ADAPTER_REGISTRY.get(adapter_id)
        if spec is None:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: unsupported adapter "
                f"{adapter_id!r}"
            )
        if row["step_id"] != spec.step_id:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} belongs "
                f"to step {spec.step_id}, not {row['step_id']}"
            )
        if row["scope_type"] != spec.scope_type:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} requires "
                f"scope_type {spec.scope_type}, not {row['scope_type']}"
            )
        source_name = Path(row["source_path"]).name
        if spec.basenames and source_name not in spec.basenames:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} does not "
                f"accept basename {source_name!r}"
            )
        if spec.suffixes and not source_name.endswith(spec.suffixes):
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} does not "
                f"accept source filename {source_name!r}"
            )
        key = (row["step_id"], row["scope_type"], row["scope_id"])
        grouped[key].append(row)

    for scope, scope_rows in grouped.items():
        step_id = scope[0]
        expected = SCOPE_ADAPTER_ROSTERS.get(step_id)
        if expected is None:
            raise ArtifactIndexError(
                f"No logical transaction roster exists for step {step_id!r}"
            )
        observed = Counter(row["adapter"] for row in scope_rows)
        if observed != expected:
            raise ArtifactIndexError(
                f"Inventory scope {scope!r} adapter roster is invalid; "
                f"observed {dict(observed)}, expected {dict(expected)}"
            )
        if step_id == "00a":
            names = {
                Path(row["source_path"]).name
                for row in scope_rows
                if row["adapter"] == "step00a_star_index_v1"
            }
            if names != set(STEP00A_BASENAMES):
                raise ArtifactIndexError(
                    f"Inventory scope {scope!r} must declare the exact 15 "
                    "STAR index basenames"
                )
        if step_id == "07":
            vcf_names = [
                Path(row["source_path"]).name
                for row in scope_rows
                if row["adapter"] == "step07_mpileup_vcf_v1"
            ]
            if sum(".FWD_like." in name for name in vcf_names) != 1 or sum(
                ".REV_like." in name for name in vcf_names
            ) != 1:
                raise ArtifactIndexError(
                    f"Inventory scope {scope!r} must declare one FWD_like "
                    "and one REV_like Step 07 VCF"
                )


def issue(code: str, message: str, artifact_id: str) -> dict[str, Any]:
    return {
        "code": code,
        "message": safe_tsv(message),
        "related_artifact_ids": [artifact_id],
        "evidence": [],
    }


def declared_contract_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = contracts.REPO_ROOT / path
    return Path(os.path.abspath(os.fspath(path)))


def stat_source(
    path: Path,
    *,
    hash_content: bool = True,
) -> SourceSnapshot:
    try:
        lstat_result = path.lstat()
    except FileNotFoundError:
        return SourceSnapshot("missing", None, None, "absent")
    except OSError as exc:
        status = (
            "externally_unavailable"
            if exc.errno
            in {
                errno.EACCES,
                errno.EPERM,
                errno.ESTALE,
                errno.EIO,
                errno.ENXIO,
                errno.ETIMEDOUT,
            }
            else "unknown"
        )
        return SourceSnapshot(status, None, None, f"os_error:{exc.errno}")

    link_target: str | None = None
    if path.is_symlink():
        try:
            link_target = os.readlink(path)
        except OSError as exc:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                None,
                f"symlink_read_error:{exc.errno}",
            )
        try:
            stat_result = path.stat()
        except FileNotFoundError:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                None,
                "dangling_symlink",
                link_target,
            )
        except OSError as exc:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                None,
                f"symlink_target_error:{exc.errno}",
                link_target,
            )
    else:
        stat_result = lstat_result

    if not path.is_file():
        return SourceSnapshot("unknown", None, None, "not_regular_file")
    digest: str | None = None
    if hash_content:
        try:
            digest = contracts.sha256_file(path)
        except contracts.ContractValidationError:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                stat_result.st_size,
                "hash_read_error",
                link_target,
                stat_result.st_dev,
                stat_result.st_ino,
                stat_result.st_mtime_ns,
                stat_result.st_ctime_ns,
            )
        try:
            post_hash_stat = path.stat()
            post_hash_link = os.readlink(path) if link_target is not None else None
        except OSError:
            return SourceSnapshot(
                "unknown",
                None,
                None,
                "changed_during_hash",
                link_target,
            )
        before_identity = (
            stat_result.st_dev,
            stat_result.st_ino,
            stat_result.st_size,
            stat_result.st_mtime_ns,
            stat_result.st_ctime_ns,
            link_target,
        )
        after_identity = (
            post_hash_stat.st_dev,
            post_hash_stat.st_ino,
            post_hash_stat.st_size,
            post_hash_stat.st_mtime_ns,
            post_hash_stat.st_ctime_ns,
            post_hash_link,
        )
        if before_identity != after_identity:
            return SourceSnapshot(
                "unknown",
                None,
                post_hash_stat.st_size,
                "changed_during_hash",
                post_hash_link,
                post_hash_stat.st_dev,
                post_hash_stat.st_ino,
                post_hash_stat.st_mtime_ns,
                post_hash_stat.st_ctime_ns,
            )
    file_type = "symlink_to_regular_file" if link_target is not None else "regular_file"
    return SourceSnapshot(
        "present",
        digest,
        stat_result.st_size,
        file_type,
        link_target,
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
    )


def iter_text_lines(path: Path) -> Iterable[tuple[int, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if "\x00" in raw_line:
                    raise ArtifactIndexError(
                        f"Text line {line_number} contains a NUL byte"
                    )
                if "\r" in raw_line:
                    raise ArtifactIndexError(
                        f"Text line {line_number} contains a carriage return"
                    )
                line = (
                    raw_line[:-1]
                    if raw_line.endswith("\n")
                    else raw_line
                )
                yield line_number, line
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError) as exc:
        raise ArtifactIndexError(f"Could not read UTF-8 text: {exc}") from exc


def inspect_nonempty_text(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    has_content = False
    for _line_number, line in iter_text_lines(path):
        count += 1
        has_content = has_content or bool(line.strip())
    if not has_content:
        raise ArtifactIndexError("Text file is empty")
    return count, {}


def inspect_tsv(
    path: Path,
    spec: AdapterSpec,
) -> tuple[int, dict[str, str] | None, dict[str, Any], dict[str, Any]]:
    captured_rows: list[dict[str, str]] = []
    anchor_values: dict[str, set[str]] = defaultdict(set)
    value_counts: dict[str, Counter[str]] = defaultdict(Counter)
    capture_rows = (
        spec.exact_data_rows is not None
        or spec.adapter_id in set(STEP09C_CATEGORY_ADAPTERS.values())
        or spec.adapter_id
        in {
        "step07_mpileup_receipt_v1",
        "step08_inputs_v1",
        "step09_mutation_spectrum_tsv_v1",
        "step09c_evidence_index_v1",
        }
    )
    mutation_pair_counts: dict[str, Counter[str]] = defaultdict(Counter)
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t")
            try:
                header = tuple(next(reader))
            except StopIteration as exc:
                raise ArtifactIndexError("TSV is empty") from exc
            if not header or any(not value for value in header):
                raise ArtifactIndexError("TSV header contains an empty field")
            if len(header) != len(set(header)):
                raise ArtifactIndexError("TSV header contains duplicate fields")
            if spec.kind == "sample_blocks_tsv":
                validate_sample_block_header(header, spec.expected_header or ())
            elif spec.expected_header is not None and header != spec.expected_header:
                raise ArtifactIndexError(
                    "TSV header mismatch; expected "
                    + " | ".join(spec.expected_header)
                    + "; observed "
                    + " | ".join(header)
                )
            count = 0
            first_row: dict[str, str] | None = None
            for row_number, values in enumerate(reader, start=2):
                if not values or all(value == "" for value in values):
                    raise ArtifactIndexError(
                        f"TSV row {row_number} is blank"
                    )
                if len(values) != len(header):
                    raise ArtifactIndexError(
                        f"TSV row {row_number} has {len(values)} fields; "
                        f"expected {len(header)}"
                    )
                row = dict(zip(header, values, strict=True))
                validate_native_run_anchors(row, {})
                for field_name in (
                    "sample_manifest_sha256",
                    "partition_manifest_sha256",
                    "analysis_id",
                    "primary_analysis_id",
                    "review_id",
                    "cohort_id",
                    "orientation_policy",
                ):
                    if field_name in row:
                        anchor_values[field_name].add(row[field_name])
                if spec.adapter_id in {
                    "step09_cmh_all_sites_v1",
                    "step09_cmh_significant_sites_v1",
                }:
                    for field_name in (
                        "test_status",
                        "call_status",
                        "rna_ref",
                        "rna_alt",
                    ):
                        value_counts[field_name][row[field_name]] += 1
                    mutation_type = f"{row['rna_ref']}>{row['rna_alt']}"
                    mutation_pair_counts[mutation_type]["candidate_count"] += 1
                    if row["test_status"] == "tested":
                        mutation_pair_counts[mutation_type][
                            "successfully_tested_count"
                        ] += 1
                    if row["call_status"] == "significant_up":
                        mutation_pair_counts[mutation_type][
                            "significant_up_count"
                        ] += 1
                    if row["call_status"] == "significant_down":
                        mutation_pair_counts[mutation_type][
                            "significant_down_count"
                        ] += 1
                if spec.kind == "validation_report":
                    value_counts["status"][row["status"]] += 1
                if capture_rows:
                    captured_rows.append(row)
                if first_row is None:
                    first_row = row
                count += 1
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ArtifactIndexError(f"Could not parse TSV: {exc}") from exc
    if spec.exact_data_rows is not None and count != spec.exact_data_rows:
        raise ArtifactIndexError(
            f"TSV must contain exactly {spec.exact_data_rows} data rows; "
            f"observed {count}"
        )
    if not spec.allow_header_only and count == 0:
        raise ArtifactIndexError("TSV must contain at least one data row")
    parameters = extract_parameters(first_row)
    native: dict[str, Any] = {
        "header": list(header),
        "anchor_values": {
            key: sorted(values)
            for key, values in sorted(anchor_values.items())
        },
    }
    if spec.kind == "sample_blocks_tsv":
        remainder = header[len(spec.expected_header or ()) :]
        sample_count = len(remainder) // 3
        native["samples"] = [
            value.removeprefix("DP__")
            for value in remainder[:sample_count]
        ]
        native["sample_count"] = sample_count
    if capture_rows:
        native["rows"] = captured_rows
    if value_counts:
        native["value_counts"] = {
            field_name: dict(sorted(counts.items()))
            for field_name, counts in sorted(value_counts.items())
        }
    if mutation_pair_counts:
        native["mutation_pair_counts"] = {
            mutation_type: dict(sorted(counts.items()))
            for mutation_type, counts in sorted(mutation_pair_counts.items())
        }
    return count, first_row, parameters, native


def validate_sample_block_header(
    header: Sequence[str],
    fixed_prefix: Sequence[str],
) -> None:
    if tuple(header[: len(fixed_prefix)]) != tuple(fixed_prefix):
        raise ArtifactIndexError(
            "Sample-block TSV fixed metadata header is invalid"
        )
    remainder = tuple(header[len(fixed_prefix) :])
    if not remainder:
        raise ArtifactIndexError(
            "Sample-block TSV must declare at least one sample"
        )
    if len(remainder) % 3 != 0:
        raise ArtifactIndexError(
            "Sample-block TSV must have equal DP__, AD__, and AF__ blocks"
        )
    sample_count = len(remainder) // 3
    dp = remainder[:sample_count]
    ad = remainder[sample_count : sample_count * 2]
    af = remainder[sample_count * 2 :]
    samples = tuple(value.removeprefix("DP__") for value in dp)
    if any(
        not value.startswith("DP__") or not sample
        for value, sample in zip(dp, samples, strict=True)
    ):
        raise ArtifactIndexError("Sample-block TSV has an invalid DP__ block")
    if len(samples) != len(set(samples)):
        raise ArtifactIndexError("Sample-block TSV has duplicate samples")
    if ad != tuple(f"AD__{sample}" for sample in samples):
        raise ArtifactIndexError("Sample-block TSV AD__ order is invalid")
    if af != tuple(f"AF__{sample}" for sample in samples):
        raise ArtifactIndexError("Sample-block TSV AF__ order is invalid")


def extract_parameters(row: Mapping[str, str] | None) -> dict[str, Any]:
    if row is None:
        return {}
    fields = (
        "sample_id",
        "cohort_id",
        "partition_id",
        "selector_type",
        "selector_value",
        "orientation",
        "analysis_id",
        "review_id",
        "primary_analysis_id",
        "orientation_policy",
        "overall_science_status",
        "orientation_status",
        "transaction_state",
    )
    return {field: row[field] for field in fields if field in row}


def inspect_vcf(path: Path) -> tuple[int, dict[str, Any]]:
    fields: list[str] | None = None
    samples: list[str] = []
    format_ids: set[str] = set()
    info_ids: set[str] = set()
    count = 0
    observed_lines = 0
    for line_number, line in iter_text_lines(path):
        observed_lines += 1
        if line_number == 1 and not line.startswith("##fileformat=VCF"):
            raise ArtifactIndexError(
                "VCF is missing the leading ##fileformat declaration"
            )
        format_match = re.match(r"^##FORMAT=<ID=([^,>]+)", line)
        if format_match:
            format_ids.add(format_match.group(1))
            continue
        info_match = re.match(r"^##INFO=<ID=([^,>]+)", line)
        if info_match:
            info_ids.add(info_match.group(1))
            continue
        if line.startswith("##"):
            continue
        if line.startswith("#CHROM\t"):
            if fields is not None:
                raise ArtifactIndexError(
                    "VCF must contain exactly one #CHROM header"
                )
            fields = line.split("\t")
            if fields[:9] != [
                "#CHROM",
                "POS",
                "ID",
                "REF",
                "ALT",
                "QUAL",
                "FILTER",
                "INFO",
                "FORMAT",
            ]:
                raise ArtifactIndexError("VCF fixed columns are invalid")
            samples = fields[9:]
            if not samples or any(not sample for sample in samples):
                raise ArtifactIndexError("VCF must declare at least one sample")
            if len(samples) != len(set(samples)):
                raise ArtifactIndexError("VCF sample columns are not unique")
            continue
        if line.startswith("#"):
            raise ArtifactIndexError(
                f"VCF line {line_number} has an unexpected header record"
            )
        if fields is None:
            raise ArtifactIndexError(
                f"VCF record line {line_number} precedes #CHROM"
            )
        values = line.split("\t")
        if len(values) != len(fields):
            raise ArtifactIndexError(
                f"VCF record line {line_number} has {len(values)} fields; "
                f"expected {len(fields)}"
            )
        try:
            if int(values[1]) <= 0:
                raise ValueError
        except ValueError as exc:
            raise ArtifactIndexError(
                f"VCF record line {line_number} has invalid POS"
            ) from exc
        count += 1
    if observed_lines == 0 or fields is None:
        raise ArtifactIndexError(
            "VCF must contain exactly one #CHROM header"
        )
    return count, {
        "sample_count": len(samples),
        "samples": samples,
        "format_ids": sorted(format_ids),
        "info_ids": sorted(info_ids),
    }


def inspect_fasta(path: Path) -> tuple[int, dict[str, Any]]:
    sequence_ids: set[str] = set()
    sequence_lengths: dict[str, int] = {}
    current: str | None = None
    total_bases = 0
    sequence_has_bases = False
    for line_number, line in iter_text_lines(path):
        if line.startswith(">"):
            if current is not None and not sequence_has_bases:
                raise ArtifactIndexError(
                    f"FASTA sequence {current!r} has no bases"
                )
            current = line[1:].split()[0] if line[1:].split() else ""
            if not current or current in sequence_ids:
                raise ArtifactIndexError(
                    f"FASTA line {line_number} has an empty or duplicate ID"
                )
            sequence_ids.add(current)
            sequence_lengths[current] = 0
            sequence_has_bases = False
            continue
        if current is None:
            raise ArtifactIndexError("FASTA sequence appears before a header")
        sequence = line.strip()
        if not sequence or not re.fullmatch(r"[A-Za-z*.-]+", sequence):
            raise ArtifactIndexError(
                f"FASTA line {line_number} contains invalid sequence text"
            )
        total_bases += len(sequence)
        sequence_lengths[current] += len(sequence)
        sequence_has_bases = True
    if current is None or not sequence_has_bases:
        raise ArtifactIndexError("FASTA has no complete sequence")
    return len(sequence_ids), {
        "total_bases": total_bases,
        "contigs": sequence_lengths,
    }


def inspect_fai(path: Path) -> tuple[int, dict[str, Any]]:
    seen: set[str] = set()
    contigs: dict[str, int] = {}
    total_bases = 0
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) < 5 or not values[0] or values[0] in seen:
            raise ArtifactIndexError(f"FAI line {line_number} is invalid")
        try:
            length, offset, line_bases, line_width = map(int, values[1:5])
        except ValueError as exc:
            raise ArtifactIndexError(
                f"FAI line {line_number} has non-integer fields"
            ) from exc
        if length <= 0 or offset < 0 or line_bases <= 0 or line_width <= 0:
            raise ArtifactIndexError(
                f"FAI line {line_number} has invalid numeric fields"
            )
        seen.add(values[0])
        contigs[values[0]] = length
        total_bases += length
        count += 1
    if count == 0:
        raise ArtifactIndexError("FAI has no sequence records")
    return count, {"total_bases": total_bases, "contigs": contigs}


def inspect_dict(path: Path) -> tuple[int, dict[str, Any]]:
    seen: set[str] = set()
    contigs: dict[str, int] = {}
    total_bases = 0
    count = 0
    for line_number, line in iter_text_lines(path):
        if not line.startswith("@SQ\t"):
            continue
        fields = {
            token.split(":", 1)[0]: token.split(":", 1)[1]
            for token in line.split("\t")[1:]
            if ":" in token
        }
        name = fields.get("SN", "")
        try:
            length = int(fields.get("LN", ""))
        except ValueError as exc:
            raise ArtifactIndexError(
                f"Dictionary line {line_number} has an invalid LN"
            ) from exc
        if not name or name in seen or length <= 0:
            raise ArtifactIndexError(
                f"Dictionary line {line_number} has invalid SN/LN"
            )
        seen.add(name)
        contigs[name] = length
        total_bases += length
        count += 1
    if count == 0:
        raise ArtifactIndexError("Dictionary has no @SQ records")
    return count, {"total_bases": total_bases, "contigs": contigs}


def inspect_bed12(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) != 12:
            raise ArtifactIndexError(
                f"BED line {line_number} does not have 12 fields"
            )
        try:
            start = int(values[1])
            end = int(values[2])
            block_count = int(values[9])
            sizes = [int(value) for value in values[10].rstrip(",").split(",")]
            starts = [int(value) for value in values[11].rstrip(",").split(",")]
        except ValueError as exc:
            raise ArtifactIndexError(
                f"BED line {line_number} has invalid numeric fields"
            ) from exc
        if (
            not values[0]
            or not values[3]
            or start < 0
            or end <= start
            or values[5] not in {"+", "-"}
            or block_count <= 0
            or len(sizes) != block_count
            or len(starts) != block_count
            or any(size <= 0 for size in sizes)
            or any(offset < 0 for offset in starts)
        ):
            raise ArtifactIndexError(f"BED line {line_number} is invalid")
        count += 1
    if count == 0:
        raise ArtifactIndexError("BED12 file has no records")
    return count, {}


def inspect_star_sj(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    for line_number, line in iter_text_lines(path):
        values = line.split("\t")
        if len(values) != 9:
            raise ArtifactIndexError(
                f"STAR SJ line {line_number} does not have 9 fields"
            )
        try:
            numbers = [int(value) for value in values[1:]]
        except ValueError as exc:
            raise ArtifactIndexError(
                f"STAR SJ line {line_number} has non-integer fields"
            ) from exc
        if not values[0] or numbers[0] <= 0 or numbers[1] < numbers[0]:
            raise ArtifactIndexError(f"STAR SJ line {line_number} is invalid")
        count += 1
    return count, {}


def inspect_picard_metrics(path: Path) -> tuple[int, dict[str, Any]]:
    header: list[str] | None = None
    metric_row: dict[str, str] | None = None
    for _line_number, line in iter_text_lines(path):
        if line.startswith("LIBRARY\t"):
            header = line.split("\t")
            continue
        if header is not None and line and not line.startswith("#"):
            values = line.split("\t")
            if len(header) != len(values):
                raise ArtifactIndexError("Picard metrics row width is invalid")
            metric_row = dict(zip(header, values, strict=True))
            break
    if header is None or metric_row is None:
        raise ArtifactIndexError("Picard metrics table is missing")
    native: dict[str, Any] = {}
    for key, value in metric_row.items():
        if key == "LIBRARY" or value == "":
            continue
        try:
            native[key.lower()] = (
                float(value) if any(token in value for token in (".", "e", "E"))
                else int(value)
            )
        except ValueError:
            continue
    return 1, native


def inspect_source(
    row: dict[str, str],
    spec: AdapterSpec,
) -> Inspection:
    resolved = declared_contract_path(row["source_path"])
    snapshot = stat_source(resolved)
    required = row["required"] == "true"
    artifact_id = row["artifact_id"]
    if snapshot.status == "missing":
        if required:
            return Inspection(
                row=row,
                spec=spec,
                resolved_path=resolved,
                availability_status="missing",
                completion_status="incomplete",
                state_reason="Required source is absent.",
                attempt_provenance_status="unavailable",
                source=None,
                warnings=[
                    issue(
                        "required_source_missing",
                        f"Required source is absent: {row['source_path']}",
                        artifact_id,
                    )
                ],
                snapshot=snapshot,
            )
        return Inspection(
            row=row,
            spec=spec,
            resolved_path=resolved,
            availability_status="missing",
            completion_status="not_attempted",
            state_reason="Optional source is absent.",
            attempt_provenance_status="not_attempted",
            source=None,
            snapshot=snapshot,
        )
    if snapshot.status == "externally_unavailable":
        return Inspection(
            row=row,
            spec=spec,
            resolved_path=resolved,
            availability_status="externally_unavailable",
            completion_status="incomplete",
            state_reason="Declared source cannot be accessed.",
            attempt_provenance_status="unavailable",
            source=None,
            warnings=[
                issue(
                    "source_externally_unavailable",
                    f"Declared source cannot be accessed "
                    f"({snapshot.file_type}): {row['source_path']}",
                    artifact_id,
                )
            ],
            snapshot=snapshot,
        )
    if snapshot.status == "unknown":
        return Inspection(
            row=row,
            spec=spec,
            resolved_path=resolved,
            availability_status="unknown",
            completion_status="failed",
            state_reason="Declared source is not a readable regular file.",
            attempt_provenance_status="unavailable",
            source=None,
            errors=[
                issue(
                    "source_state_unknown",
                    f"Declared source is not a readable regular file "
                    f"({snapshot.file_type}): {row['source_path']}",
                    artifact_id,
                )
            ],
            snapshot=snapshot,
        )

    source = {
        "path": row["source_path"],
        "sha256": snapshot.sha256,
        "size_bytes": snapshot.size_bytes,
        "row_count": None,
        "media_type": (
            "text/plain"
            if spec.kind == "star_index"
            and resolved.name not in {"Genome", "SA", "SAindex"}
            else spec.media_type
        ),
    }
    try:
        row_count, first_row, parameters, native_metrics = inspect_present(
            resolved, spec
        )
        source["row_count"] = row_count
        if spec.kind == "validation_report":
            validation_rows = native_metrics.get("rows", [])
            if any(
                item["step_id"] != spec.step_id
                or item["scope_id"] != row["scope_id"]
                or item["status"] not in {"pass", "fail"}
                or not contracts.SAFE_ID_RE.fullmatch(item["check_id"])
                for item in validation_rows
            ):
                raise ArtifactIndexError(
                    "Validation report step, scope, check ID, or status is invalid"
                )
            check_ids = [item["check_id"] for item in validation_rows]
            if len(check_ids) != len(set(check_ids)):
                raise ArtifactIndexError(
                    "Validation report contains duplicate check IDs"
                )
        validate_native_run_anchors(first_row, row)
        metrics = build_metrics(row, row_count, native_metrics)
        if (
            spec.kind == "validation_report"
            and native_metrics.get("value_counts", {})
            .get("status", {})
            .get("fail", 0)
        ):
            return Inspection(
                row=row,
                spec=spec,
                resolved_path=resolved,
                availability_status="present",
                completion_status="failed",
                state_reason="Validation report contains failed checks.",
                attempt_provenance_status="unavailable",
                source=source,
                parameters=parameters,
                metrics=metrics,
                native=native_metrics,
                first_row=first_row,
                errors=[
                    issue(
                        "validation_checks_failed",
                        "One or more explicit validation checks failed.",
                        artifact_id,
                    )
                ],
                snapshot=snapshot,
            )
        return Inspection(
            row=row,
            spec=spec,
            resolved_path=resolved,
            availability_status="present",
            completion_status="complete",
            state_reason=None,
            attempt_provenance_status="unavailable",
            source=source,
            parameters=parameters,
            metrics=metrics,
            native=native_metrics,
            first_row=first_row,
            snapshot=snapshot,
        )
    except ArtifactIndexError as exc:
        return Inspection(
            row=row,
            spec=spec,
            resolved_path=resolved,
            availability_status="present",
            completion_status="failed",
            state_reason="Present source failed its registered adapter.",
            attempt_provenance_status="unavailable",
            source=source,
            errors=[
                issue(
                    "adapter_validation_failed",
                    f"{spec.adapter_id}: {exc}",
                    artifact_id,
                )
            ],
            snapshot=snapshot,
        )

BGZF_EOF_BLOCK = bytes.fromhex(
    "1f8b08040000000000ff0600424302001b00030000000000000000"
)
MAX_BAM_HEADER_BYTES = 64 * 1024 * 1024


def read_exact_binary(stream: Any, size: int, label: str) -> bytes:
    value = stream.read(size)
    if len(value) != size:
        raise ArtifactIndexError(f"{label} is truncated")
    return value


def read_bgzf_block(stream: Any) -> bytes:
    header = read_exact_binary(stream, 12, "BGZF header")
    if (
        header[:3] != b"\x1f\x8b\x08"
        or header[3] != 4
        or struct.unpack("<H", header[10:12])[0] < 6
    ):
        raise ArtifactIndexError("BAM does not contain a valid BGZF header")
    extra_length = struct.unpack("<H", header[10:12])[0]
    extra = read_exact_binary(stream, extra_length, "BGZF extra field")
    block_size: int | None = None
    cursor = 0
    while cursor < len(extra):
        if cursor + 4 > len(extra):
            raise ArtifactIndexError("BGZF extra field is malformed")
        subfield_id = extra[cursor : cursor + 2]
        subfield_length = struct.unpack("<H", extra[cursor + 2 : cursor + 4])[0]
        cursor += 4
        if cursor + subfield_length > len(extra):
            raise ArtifactIndexError("BGZF subfield is truncated")
        if subfield_id == b"BC":
            if subfield_length != 2 or block_size is not None:
                raise ArtifactIndexError("BGZF BC subfield is invalid")
            block_size = struct.unpack(
                "<H",
                extra[cursor : cursor + subfield_length],
            )[0] + 1
        cursor += subfield_length
    if block_size is None:
        raise ArtifactIndexError("BGZF block lacks the required BC subfield")
    consumed = 12 + extra_length
    remaining = block_size - consumed
    if remaining < 8 or block_size > 65536:
        raise ArtifactIndexError("BGZF block size is invalid")
    body = read_exact_binary(stream, remaining, "BGZF block")
    compressed = body[:-8]
    expected_crc, expected_size = struct.unpack("<II", body[-8:])
    try:
        uncompressed = zlib.decompress(compressed, wbits=-15)
    except zlib.error as exc:
        raise ArtifactIndexError(f"BGZF deflate payload is invalid: {exc}") from exc
    if (
        len(uncompressed) != expected_size
        or zlib.crc32(uncompressed) & 0xFFFFFFFF != expected_crc
    ):
        raise ArtifactIndexError("BGZF CRC or uncompressed size is invalid")
    return uncompressed


def parse_bam_header_buffer(
    value: bytes,
) -> tuple[int, int, int] | None:
    if len(value) < 8:
        return None
    if value[:4] != b"BAM\x01":
        raise ArtifactIndexError("Decompressed BAM magic is invalid")
    header_text_bytes = struct.unpack("<i", value[4:8])[0]
    if not 0 <= header_text_bytes <= 16 * 1024 * 1024:
        raise ArtifactIndexError("BAM header text length is invalid")
    cursor = 8 + header_text_bytes
    if len(value) < cursor + 4:
        return None
    reference_count = struct.unpack("<i", value[cursor : cursor + 4])[0]
    cursor += 4
    if not 0 <= reference_count <= 1_000_000:
        raise ArtifactIndexError("BAM reference count is invalid")
    for _reference_index in range(reference_count):
        if len(value) < cursor + 4:
            return None
        name_length = struct.unpack("<i", value[cursor : cursor + 4])[0]
        cursor += 4
        if not 2 <= name_length <= 1_048_576:
            raise ArtifactIndexError("BAM reference-name length is invalid")
        if len(value) < cursor + name_length + 4:
            return None
        name = value[cursor : cursor + name_length]
        if name[-1:] != b"\x00" or b"\x00" in name[:-1]:
            raise ArtifactIndexError("BAM reference name is invalid")
        cursor += name_length
        reference_length = struct.unpack("<i", value[cursor : cursor + 4])[0]
        cursor += 4
        if reference_length <= 0:
            raise ArtifactIndexError("BAM reference length is invalid")
    return cursor, header_text_bytes, reference_count


def inspect_bgzf_bam(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size <= len(BGZF_EOF_BLOCK):
            raise ArtifactIndexError("BAM is too small to contain data and EOF")
        with path.open("rb") as stream:
            stream.seek(size - len(BGZF_EOF_BLOCK))
            if stream.read(len(BGZF_EOF_BLOCK)) != BGZF_EOF_BLOCK:
                raise ArtifactIndexError(
                    "BAM lacks the canonical terminal BGZF EOF block"
                )
            stream.seek(0)
            header_buffer = bytearray()
            parsed: tuple[int, int, int] | None = None
            while parsed is None:
                header_buffer.extend(read_bgzf_block(stream))
                if len(header_buffer) > MAX_BAM_HEADER_BYTES:
                    raise ArtifactIndexError(
                        "BAM header exceeds the bounded adapter limit"
                    )
                parsed = parse_bam_header_buffer(bytes(header_buffer))
    except ArtifactIndexError:
        raise
    except OSError as exc:
        raise ArtifactIndexError(f"Could not inspect BAM: {exc}") from exc
    _header_end, header_text_bytes, reference_count = parsed
    return {
        "bgzf_eof_present": True,
        "bam_header_text_bytes": header_text_bytes,
        "reference_count": reference_count,
    }


def read_bai_uint32(stream: Any, label: str) -> int:
    return struct.unpack("<I", read_exact_binary(stream, 4, label))[0]


def inspect_bai_structure(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            if read_exact_binary(stream, 4, "BAI magic") != b"BAI\x01":
                raise ArtifactIndexError("BAI signature is invalid")
            reference_count = read_bai_uint32(stream, "BAI reference count")
            if (
                reference_count > 1_000_000
                or reference_count > max(0, (size - 8) // 8)
            ):
                raise ArtifactIndexError("BAI reference count is invalid")
            bin_count = 0
            chunk_count = 0
            interval_count = 0
            for _reference_index in range(reference_count):
                reference_bin_count = read_bai_uint32(
                    stream,
                    "BAI bin count",
                )
                if reference_bin_count > (size - stream.tell()) // 8:
                    raise ArtifactIndexError("BAI bin count exceeds file size")
                seen_bins: set[int] = set()
                for _bin_index in range(reference_bin_count):
                    bin_id = read_bai_uint32(stream, "BAI bin ID")
                    if bin_id in seen_bins or bin_id > 37450:
                        raise ArtifactIndexError("BAI bin ID is invalid")
                    seen_bins.add(bin_id)
                    reference_chunk_count = read_bai_uint32(
                        stream,
                        "BAI chunk count",
                    )
                    if reference_chunk_count > (size - stream.tell()) // 16:
                        raise ArtifactIndexError(
                            "BAI chunk count exceeds file size"
                        )
                    for _chunk_index in range(reference_chunk_count):
                        chunk_start, chunk_end = struct.unpack(
                            "<QQ",
                            read_exact_binary(stream, 16, "BAI chunk"),
                        )
                        if bin_id != 37450 and chunk_end < chunk_start:
                            raise ArtifactIndexError(
                                "BAI chunk virtual offsets are reversed"
                            )
                    chunk_count += reference_chunk_count
                bin_count += reference_bin_count
                reference_interval_count = read_bai_uint32(
                    stream,
                    "BAI interval count",
                )
                if reference_interval_count > (size - stream.tell()) // 8:
                    raise ArtifactIndexError(
                        "BAI interval count exceeds file size"
                    )
                read_exact_binary(
                    stream,
                    reference_interval_count * 8,
                    "BAI intervals",
                )
                interval_count += reference_interval_count
            remainder = stream.read()
            if len(remainder) not in {0, 8}:
                raise ArtifactIndexError("BAI contains trailing malformed bytes")
    except ArtifactIndexError:
        raise
    except OSError as exc:
        raise ArtifactIndexError(f"Could not inspect BAI: {exc}") from exc
    return {
        "reference_count": reference_count,
        "bin_count": bin_count,
        "chunk_count": chunk_count,
        "interval_count": interval_count,
    }


def inspect_pdf_structure(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size < 64:
            raise ArtifactIndexError("PDF is too small to contain its structure")
        with path.open("rb") as stream:
            prefix = stream.read(16)
            if re.match(rb"^%PDF-(?:1\.[0-9]|2\.0)(?:\r?\n)", prefix) is None:
                raise ArtifactIndexError("PDF version header is invalid")
            stream.seek(max(0, size - 65536))
            tail = stream.read()
            match = re.search(
                rb"startxref\s+([0-9]+)\s+%%EOF\s*$",
                tail,
            )
            if match is None:
                raise ArtifactIndexError(
                    "PDF lacks a terminal startxref/EOF structure"
                )
            startxref = int(match.group(1))
            if not 0 < startxref < size:
                raise ArtifactIndexError("PDF startxref offset is invalid")
            stream.seek(startxref)
            xref = stream.read(min(65536, size - startxref))
    except ArtifactIndexError:
        raise
    except OSError as exc:
        raise ArtifactIndexError(f"Could not inspect PDF: {exc}") from exc
    if xref.startswith(b"xref"):
        if (
            re.match(rb"xref\s+[0-9]+\s+[1-9][0-9]*", xref) is None
            or b"trailer" not in xref
            or re.search(rb"/Root\s+[0-9]+\s+[0-9]+\s+R", xref) is None
        ):
            raise ArtifactIndexError("PDF cross-reference table is invalid")
        xref_kind = "table"
    elif (
        re.match(rb"[0-9]+\s+[0-9]+\s+obj\b", xref) is not None
        and re.search(rb"/Type\s*/XRef\b", xref) is not None
        and re.search(rb"/Root\s+[0-9]+\s+[0-9]+\s+R", xref) is not None
    ):
        xref_kind = "stream"
    else:
        raise ArtifactIndexError(
            "PDF startxref does not point to a valid cross-reference object"
        )
    return {"pdf_startxref": startxref, "pdf_xref_kind": xref_kind}


def inspect_present(
    path: Path,
    spec: AdapterSpec,
) -> tuple[int | None, dict[str, str] | None, dict[str, Any], dict[str, Any]]:
    if spec.kind in {"tsv", "sample_blocks_tsv", "validation_report"}:
        return inspect_tsv(path, spec)
    if spec.kind == "vcf":
        row_count, native = inspect_vcf(path)
        return row_count, None, native, native
    if spec.kind == "fasta":
        row_count, native = inspect_fasta(path)
        return row_count, None, native, native
    if spec.kind == "fai":
        row_count, native = inspect_fai(path)
        return row_count, None, native, native
    if spec.kind == "dict":
        row_count, native = inspect_dict(path)
        return row_count, None, native, native
    if spec.kind == "bed12":
        row_count, native = inspect_bed12(path)
        return row_count, None, native, native
    if spec.kind == "star_sj":
        row_count, native = inspect_star_sj(path)
        return row_count, None, native, native
    if spec.kind == "picard_metrics":
        row_count, native = inspect_picard_metrics(path)
        return row_count, None, {}, native
    if spec.kind == "pdf":
        native = inspect_pdf_structure(path)
        return None, None, {}, native
    if spec.kind == "bam":
        native = inspect_bgzf_bam(path)
        return None, None, {}, native
    if spec.kind == "bai":
        native = inspect_bai_structure(path)
        return None, None, {}, native
    if spec.kind == "quickcheck":
        expected = "PASS: samtools quickcheck completed with no errors."
        observed = [
            line
            for _line_number, line in iter_text_lines(path)
            if line
        ]
        if observed != [expected]:
            raise ArtifactIndexError("quickcheck output does not declare PASS")
        return 1, None, {}, {"quickcheck_pass": True}
    if spec.kind == "flagstat":
        count = 0
        native: dict[str, Any] = {}
        for line_number, line in iter_text_lines(path):
            count += 1
            match = re.match(r"^([0-9]+) \+ ([0-9]+) (.+)$", line)
            if match is None:
                raise ArtifactIndexError(
                    f"flagstat line {line_number} is malformed"
                )
            passed = int(match.group(1))
            failed = int(match.group(2))
            label = match.group(3)
            if label.startswith("in total "):
                native["total_reads"] = passed + failed
            elif label.startswith("mapped "):
                native["mapped_reads"] = passed + failed
        if "total_reads" not in native or "mapped_reads" not in native:
            raise ArtifactIndexError(
                "flagstat output must contain total and mapped rows"
            )
        return count, None, {}, native
    if spec.kind == "rseqc":
        count = 0
        native: dict[str, Any] = {}
        for _line_number, line in iter_text_lines(path):
            count += 1
            match = re.match(r"^Fraction of reads (.+): ([0-9]*\.?[0-9]+)$", line)
            if match is None:
                continue
            key = re.sub(
                r"[^A-Za-z0-9._-]",
                "_",
                match.group(1).strip().lower(),
            ).strip("_")
            native[f"fraction_{key}"] = float(match.group(2))
        if not native:
            raise ArtifactIndexError("RSeQC fraction output is missing")
        return count, None, {}, native
    if spec.kind == "star_log_final":
        count = 0
        native: dict[str, Any] = {}
        key_value_count = 0
        for _line_number, line in iter_text_lines(path):
            count += 1
            if "|" not in line:
                continue
            key_text, value_text = (
                value.strip() for value in line.split("|", 1)
            )
            if not key_text or not value_text:
                continue
            key_value_count += 1
            metric_key = re.sub(
                r"[^A-Za-z0-9._-]",
                "_",
                key_text.strip().lower(),
            ).strip("_")
            numeric = value_text.removesuffix("%").replace(",", "")
            try:
                native[metric_key] = float(numeric)
            except ValueError:
                continue
        if key_value_count == 0:
            raise ArtifactIndexError("STAR final log has no key/value rows")
        return count, None, {}, native
    if spec.kind == "star_index":
        if path.stat().st_size == 0:
            raise ArtifactIndexError("STAR index member is empty")
        if path.name in {"Genome", "SA", "SAindex"}:
            return None, None, {}, {}
        count, _native = inspect_nonempty_text(path)
        native: dict[str, Any] = {}
        if path.name == "genomeParameters.txt":
            for _line_number, line in iter_text_lines(path):
                fields = line.split()
                if len(fields) >= 2 and fields[0] == "sjdbOverhang":
                    try:
                        native["sjdbOverhang"] = int(fields[1])
                    except ValueError as exc:
                        raise ArtifactIndexError(
                            "STAR genomeParameters sjdbOverhang is invalid"
                        ) from exc
                    break
            if "sjdbOverhang" not in native:
                raise ArtifactIndexError(
                    "STAR genomeParameters is missing sjdbOverhang"
                )
        return count, None, {}, native
    if spec.kind == "text":
        count, native = inspect_nonempty_text(path)
        return count, None, {}, native
    raise ArtifactIndexError(f"Adapter kind is not implemented: {spec.kind}")


def validate_native_run_anchors(
    row: Mapping[str, str] | None,
    inventory_row: Mapping[str, str],
) -> None:
    # The explicit run contract is checked later because it belongs to the
    # build context. This function only validates lexical anchor fields.
    if row is None:
        return
    for field_name in ANCHOR_HASH_FIELDS:
        if field_name in row and not SHA256_RE.fullmatch(row[field_name]):
            raise ArtifactIndexError(
                f"Native field {field_name} is not a lowercase SHA-256"
            )
    if (
        "analysis_id" in row
        and inventory_row.get("scope_type") == "analysis"
    ):
        if row["analysis_id"] != inventory_row["scope_id"]:
            raise ArtifactIndexError(
                "Native analysis_id does not match the explicit inventory scope"
            )
    if (
        "review_id" in row
        and inventory_row.get("scope_type") == "scientific_review"
    ):
        if row["review_id"] != inventory_row["scope_id"]:
            raise ArtifactIndexError(
                "Native review_id does not match the explicit inventory scope"
            )


def build_metrics(
    row: Mapping[str, str],
    row_count: int | None,
    native: Mapping[str, Any],
) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    if row_count is not None:
        metrics.append(
            {
                "metric_id": "source_row_count",
                "name": "Source row count",
                "value": row_count,
                "unit": "rows",
                "status": "not_assessed",
                "source_artifact_id": row["artifact_id"],
            }
        )
    for key in sorted(native):
        value = native[key]
        if value is None or isinstance(value, (dict, list, tuple)):
            continue
        metric_id = re.sub(r"[^A-Za-z0-9._-]", "_", key)
        if metric_id == "source_row_count":
            continue
        metrics.append(
            {
                "metric_id": metric_id,
                "name": key.replace("_", " ").title(),
                "value": value,
                "unit": None,
                "status": (
                    "pass"
                    if key.endswith("_pass") and value is True
                    else "not_assessed"
                ),
                "source_artifact_id": row["artifact_id"],
            }
        )
    return metrics


def apply_run_contract_checks(
    inspections: Sequence[Inspection],
    run_contract: Mapping[str, Any],
) -> None:
    for inspection in inspections:
        if inspection.completion_status != "complete":
            continue
        mismatches: list[str] = []
        anchor_values = inspection.native.get("anchor_values", {})
        for field_name in ANCHOR_HASH_FIELDS:
            values = anchor_values.get(field_name, [])
            if any(value != run_contract[field_name] for value in values):
                mismatches.append(field_name)
        if inspection.row["scope_type"] == "analysis":
            analysis_ids = anchor_values.get("analysis_id", [])
            if any(
                value != run_contract["primary_analysis_id"]
                for value in analysis_ids
            ):
                mismatches.append("primary_analysis_id")
        primary_analysis_ids = anchor_values.get("primary_analysis_id", [])
        if any(
            value != run_contract["primary_analysis_id"]
            for value in primary_analysis_ids
        ):
            mismatches.append("primary_analysis_id")
        review_ids = anchor_values.get("review_id", [])
        if inspection.row["scope_type"] == "scientific_review" and any(
            value != inspection.row["scope_id"] for value in review_ids
        ):
            mismatches.append("review_id")
        cohort_ids = anchor_values.get("cohort_id", [])
        if inspection.row["scope_type"] == "cohort" and any(
            value != inspection.row["scope_id"] for value in cohort_ids
        ):
            mismatches.append("cohort_id")
        if mismatches:
            inspection.completion_status = "failed"
            inspection.state_reason = (
                "Present source conflicts with the explicit run contract."
            )
            inspection.errors.append(
                issue(
                    "run_contract_mismatch",
                    "Native source conflicts with run contract fields: "
                    + ", ".join(sorted(set(mismatches))),
                    inspection.row["artifact_id"],
                )
            )


def native_int(row: Mapping[str, str], field_name: str) -> int:
    value = row.get(field_name, "")
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ArtifactIndexError(
            f"Native field {field_name} is not a non-negative integer: {value!r}"
        )
    return int(value)


def mark_native_transaction_failed(
    members: Sequence[Inspection],
    marker_adapter: str,
    message: str,
) -> None:
    marker = next(
        (
            member
            for member in members
            if member.row["adapter"] == marker_adapter
            and member.completion_status == "complete"
        ),
        None,
    )
    if marker is None:
        marker = next(
            (
                member
                for member in members
                if member.completion_status == "complete"
            ),
            None,
        )
    if marker is None:
        return
    marker.completion_status = "failed"
    marker.state_reason = "Native logical transaction is inconsistent."
    marker.errors.append(
        issue(
            "native_transaction_inconsistent",
            message,
            marker.row["artifact_id"],
        )
    )


def require_referenced_source(
    *,
    row: Mapping[str, str],
    path_field: str,
    hash_field: str,
    row_count_field: str | None,
    source_lookup: Mapping[Path, Inspection],
) -> Inspection:
    path_value = row.get(path_field, "")
    if not path_value:
        raise ArtifactIndexError(
            f"Native reference field {path_field} is empty"
        )
    target = source_lookup.get(declared_contract_path(path_value))
    if target is None:
        raise ArtifactIndexError(
            f"Native reference {path_field} is not declared by the inventory: "
            f"{path_value}"
        )
    if target.completion_status != "complete" or target.snapshot is None:
        raise ArtifactIndexError(
            f"Native reference {path_field} is not complete: {path_value}"
        )
    if row.get(hash_field, "") != target.snapshot.sha256:
        raise ArtifactIndexError(
            f"Native reference hash {hash_field} disagrees with {path_field}"
        )
    if row_count_field is not None:
        expected_count = target.source["row_count"] if target.source else None
        observed_count = row.get(row_count_field, "")
        if expected_count is None:
            if observed_count != step09c.NA_VALUE:
                raise ArtifactIndexError(
                    f"Native binary reference {row_count_field} must be "
                    f"{step09c.NA_VALUE}"
                )
        elif native_int(row, row_count_field) != expected_count:
            raise ArtifactIndexError(
                f"Native reference row count {row_count_field} disagrees "
                f"with {path_field}"
            )
    return target


def reconcile_step00c(members: Sequence[Inspection]) -> None:
    contig_sets = [
        member.native.get("contigs")
        for member in members
        if member.row["adapter"]
        in {
            "step00c_reference_fasta_v1",
            "step00c_reference_fai_v1",
            "step00c_reference_dict_v1",
        }
    ]
    if len(contig_sets) != 3 or any(value is None for value in contig_sets):
        raise ArtifactIndexError(
            "Step 00c FASTA/FAI/DICT contig projections are incomplete"
        )
    if not all(value == contig_sets[0] for value in contig_sets[1:]):
        raise ArtifactIndexError(
            "Step 00c FASTA/FAI/DICT contig names or lengths disagree"
        )


def reconcile_step06(members: Sequence[Inspection]) -> None:
    counts = next(
        member
        for member in members
        if member.row["adapter"] == "step06_orientation_counts_v1"
    )
    row = counts.first_row or {}
    values = {
        field_name: native_int(row, field_name)
        for field_name in STEP06_COUNTS_HEADER[1:-1]
    }
    if row.get("sample_id") != counts.row["scope_id"]:
        raise ArtifactIndexError(
            "Step 06 count sample_id disagrees with inventory scope"
        )
    if values["fwd_like_records"] != (
        values["flag_99_records"] + values["flag_147_records"]
    ):
        raise ArtifactIndexError("Step 06 FWD_like count arithmetic is invalid")
    if values["rev_like_records"] != (
        values["flag_83_records"] + values["flag_163_records"]
    ):
        raise ArtifactIndexError("Step 06 REV_like count arithmetic is invalid")
    if values["assigned_records"] != (
        values["fwd_like_records"] + values["rev_like_records"]
    ):
        raise ArtifactIndexError("Step 06 assigned count arithmetic is invalid")
    if values["input_records"] != (
        values["assigned_records"] + values["unassigned_records"]
    ):
        raise ArtifactIndexError("Step 06 input count arithmetic is invalid")
    try:
        assigned_fraction = float(row.get("assigned_fraction", ""))
    except ValueError as exc:
        raise ArtifactIndexError(
            "Step 06 assigned_fraction is not numeric"
        ) from exc
    if not 0.0 <= assigned_fraction <= 1.0:
        raise ArtifactIndexError(
            "Step 06 assigned_fraction is outside [0, 1]"
        )
    expected_fraction = (
        values["assigned_records"] / values["input_records"]
        if values["input_records"]
        else 0.0
    )
    # The Step 06 producer writes this value with printf "%.6f".
    if abs(assigned_fraction - expected_fraction) > 5.000001e-7:
        raise ArtifactIndexError(
            "Step 06 assigned_fraction disagrees with count arithmetic"
        )


def reconcile_step07(members: Sequence[Inspection]) -> None:
    vcfs = [
        member
        for member in members
        if member.row["adapter"] == "step07_mpileup_vcf_v1"
    ]
    receipt = next(
        member
        for member in members
        if member.row["adapter"] == "step07_mpileup_receipt_v1"
    )
    receipt_rows = receipt.native.get("rows", [])
    if len(vcfs) != 2 or len(receipt_rows) != 2:
        raise ArtifactIndexError(
            "Step 07 transaction must contain two VCFs and two receipt rows"
        )
    sample_orders = [vcf.native.get("samples") for vcf in vcfs]
    if (
        any(not samples for samples in sample_orders)
        or sample_orders[0] != sample_orders[1]
    ):
        raise ArtifactIndexError(
            "Step 07 VCF sample columns disagree across orientations"
        )
    required_format_ids = {"DP", "AD", "ADF", "ADR", "SP"}
    required_info_ids = {"AD", "ADF", "ADR"}
    for vcf in vcfs:
        missing_format = required_format_ids - set(
            vcf.native.get("format_ids", [])
        )
        missing_info = required_info_ids - set(vcf.native.get("info_ids", []))
        if missing_format or missing_info:
            raise ArtifactIndexError(
                "Step 07 VCF lacks required header definitions; missing "
                f"FORMAT={sorted(missing_format)}, INFO={sorted(missing_info)}"
            )
    cohort_ids = {row["cohort_id"] for row in receipt_rows}
    partition_ids = {row["partition_id"] for row in receipt_rows}
    if len(cohort_ids) != 1 or len(partition_ids) != 1:
        raise ArtifactIndexError(
            "Step 07 receipt rows disagree on cohort or partition identity"
        )
    cohort_id = next(iter(cohort_ids))
    partition_id = next(iter(partition_ids))
    receipt_by_path: dict[Path, Mapping[str, str]] = {}
    for row in receipt_rows:
        path = declared_contract_path(row["vcf_path"])
        if path in receipt_by_path:
            raise ArtifactIndexError("Step 07 receipt repeats a VCF path")
        receipt_by_path[path] = row
    observed_orientations: set[str] = set()
    for vcf in vcfs:
        row = receipt_by_path.get(vcf.resolved_path)
        if row is None:
            raise ArtifactIndexError(
                "Step 07 receipt does not declare every inventory VCF path"
            )
        orientation = (
            "FWD_like"
            if ".FWD_like." in vcf.resolved_path.name
            else "REV_like"
        )
        observed_orientations.add(orientation)
        if (
            row["cohort_id"] != cohort_id
            or row["partition_id"] != partition_id
            or row["orientation"] != orientation
        ):
            raise ArtifactIndexError(
                "Step 07 receipt cohort, partition, or orientation disagrees "
                "with the inventory VCF"
            )
        if native_int(row, "sample_count") != len(sample_orders[0]):
            raise ArtifactIndexError(
                "Step 07 receipt sample_count disagrees with VCF columns"
            )
        if native_int(row, "vcf_record_count") != (
            vcf.source["row_count"] if vcf.source else None
        ):
            raise ArtifactIndexError(
                "Step 07 receipt record count disagrees with its VCF"
            )
    if observed_orientations != {"FWD_like", "REV_like"}:
        raise ArtifactIndexError(
            "Step 07 transaction lacks one neutral orientation"
        )


def reconcile_step08(
    members: Sequence[Inspection],
    source_lookup: Mapping[Path, Inspection],
) -> None:
    sites = next(
        member for member in members if member.row["adapter"] == "step08_sites_v1"
    )
    inputs = next(
        member for member in members if member.row["adapter"] == "step08_inputs_v1"
    )
    summary = next(
        member for member in members if member.row["adapter"] == "step08_summary_v1"
    )
    input_rows = inputs.native.get("rows", [])
    summary_row = summary.first_row or {}
    samples = sites.native.get("samples", [])
    if not input_rows or not samples:
        raise ArtifactIndexError(
            "Step 08 inputs and sample-block sites must be non-empty"
        )
    partitions: dict[str, set[str]] = defaultdict(set)
    sum_fields = (
        "observed_vcf_record_count",
        "observed_alt_allele_count",
        "supported_snv_count",
        "skipped_symbolic_count",
        "skipped_non_snv_count",
        "published_candidate_count",
    )
    observed_sums = Counter()
    receipt_paths: set[Path] = set()
    input_keys: set[tuple[str, str]] = set()
    input_vcf_paths: set[Path] = set()
    for row in input_rows:
        if row["cohort_id"] != sites.row["scope_id"]:
            raise ArtifactIndexError(
                "Step 08 input cohort disagrees with inventory scope"
            )
        input_key = (row["partition_id"], row["orientation"])
        if input_key in input_keys:
            raise ArtifactIndexError(
                "Step 08 inputs repeat a partition/orientation key"
            )
        input_keys.add(input_key)
        partitions[row["partition_id"]].add(row["orientation"])
        if native_int(row, "sample_count") != len(samples):
            raise ArtifactIndexError(
                "Step 08 input sample_count disagrees with sites columns"
            )
        if native_int(row, "declared_vcf_record_count") != native_int(
            row, "observed_vcf_record_count"
        ):
            raise ArtifactIndexError(
                "Step 08 declared and observed VCF counts disagree"
            )
        if native_int(row, "observed_alt_allele_count") != (
            native_int(row, "supported_snv_count")
            + native_int(row, "skipped_symbolic_count")
            + native_int(row, "skipped_non_snv_count")
        ):
            raise ArtifactIndexError(
                "Step 08 alternate-allele counts do not reconcile"
            )
        if native_int(row, "published_candidate_count") != native_int(
            row, "supported_snv_count"
        ):
            raise ArtifactIndexError(
                "Step 08 supported and published candidate counts disagree"
            )
        vcf = require_referenced_source(
            row=row,
            path_field="vcf_path",
            hash_field="vcf_sha256",
            row_count_field=None,
            source_lookup=source_lookup,
        )
        expected_orientation = (
            "FWD_like"
            if ".FWD_like." in vcf.resolved_path.name
            else "REV_like"
        )
        if (
            row["orientation"] != expected_orientation
            or vcf.native.get("samples") != samples
        ):
            raise ArtifactIndexError(
                "Step 08 input partition, orientation, or sample order "
                "disagrees with its Step 07 VCF"
            )
        if vcf.resolved_path in input_vcf_paths:
            raise ArtifactIndexError("Step 08 inputs repeat a VCF path")
        input_vcf_paths.add(vcf.resolved_path)
        if native_int(row, "observed_vcf_record_count") != (
            vcf.source["row_count"] if vcf.source else None
        ):
            raise ArtifactIndexError(
                "Step 08 input observed count disagrees with source VCF"
            )
        receipt = require_referenced_source(
            row=row,
            path_field="step07_receipt_path",
            hash_field="step07_receipt_sha256",
            row_count_field=None,
            source_lookup=source_lookup,
        )
        if receipt.row["scope_id"] != vcf.row["scope_id"]:
            raise ArtifactIndexError(
                "Step 08 input receipt belongs to the wrong Step 07 scope"
            )
        receipt_rows = receipt.native.get("rows", [])
        matching_receipt_rows = [
            receipt_row
            for receipt_row in receipt_rows
            if declared_contract_path(receipt_row["vcf_path"])
            == vcf.resolved_path
        ]
        if len(matching_receipt_rows) != 1:
            raise ArtifactIndexError(
                "Step 08 input VCF lacks one matching Step 07 receipt row"
            )
        receipt_row = matching_receipt_rows[0]
        for field_name in (
            "cohort_id",
            "partition_id",
            "selector_type",
            "selector_value",
            "orientation",
        ):
            if row[field_name] != receipt_row[field_name]:
                raise ArtifactIndexError(
                    f"Step 08 input {field_name} disagrees with Step 07 receipt"
                )
        if native_int(row, "declared_vcf_record_count") != native_int(
            receipt_row, "vcf_record_count"
        ):
            raise ArtifactIndexError(
                "Step 08 declared VCF count disagrees with Step 07 receipt"
            )
        receipt_paths.add(receipt.resolved_path)
        for field_name in sum_fields:
            observed_sums[field_name] += native_int(row, field_name)
    if any(
        orientations != {"FWD_like", "REV_like"}
        for orientations in partitions.values()
    ) or len(input_rows) != 2 * len(partitions):
        raise ArtifactIndexError(
            "Step 08 inputs do not contain both orientations per partition"
        )
    expected_scalars = {
        "partition_count": len(partitions),
        "step07_receipt_count": len(receipt_paths),
        "input_vcf_count": len(input_rows),
        "sample_count": len(samples),
        "published_candidate_count": (
            sites.source["row_count"] if sites.source else None
        ),
    }
    for field_name, expected in expected_scalars.items():
        if native_int(summary_row, field_name) != expected:
            raise ArtifactIndexError(
                f"Step 08 summary {field_name} is inconsistent"
            )
    for field_name in sum_fields:
        if native_int(summary_row, field_name) != observed_sums[field_name]:
            raise ArtifactIndexError(
                f"Step 08 summary {field_name} does not reconcile inputs"
            )
    for field_name in (
        "annotation_gtf",
        "annotation_gtf_sha256",
        "orientation_policy",
    ):
        values = {row[field_name] for row in input_rows}
        if values != {summary_row[field_name]}:
            raise ArtifactIndexError(
                f"Step 08 {field_name} differs across inputs and summary"
            )


def validate_significant_exact_subset(
    all_sites_path: Path,
    significant_path: Path,
) -> None:
    try:
        all_stream = all_sites_path.open(encoding="utf-8", newline="")
        significant_stream = significant_path.open(encoding="utf-8", newline="")
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not open Step 09 result tables: {exc}"
        ) from exc
    try:
        with all_stream, significant_stream:
            all_reader = csv.DictReader(all_stream, delimiter="\t")
            significant_reader = csv.DictReader(
                significant_stream,
                delimiter="\t",
            )
            if tuple(all_reader.fieldnames or ()) != tuple(
                significant_reader.fieldnames or ()
            ):
                raise ArtifactIndexError(
                    "Step 09 significant and all-sites headers disagree"
                )
            current = next(significant_reader, None)
            for all_row in all_reader:
                if all_row["call_status"] not in {
                    "significant_up",
                    "significant_down",
                }:
                    continue
                if current != all_row:
                    raise ArtifactIndexError(
                        "Step 09 significant-sites table is not the exact "
                        "ordered significant subset of all-sites"
                    )
                current = next(significant_reader, None)
            if current is not None:
                raise ArtifactIndexError(
                    "Step 09 significant-sites table contains an extra row"
                )
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError, csv.Error, KeyError) as exc:
        raise ArtifactIndexError(
            f"Could not compare Step 09 result tables: {exc}"
        ) from exc


def validate_step09_statuses(
    all_value_counts: Mapping[str, Mapping[str, int]],
) -> None:
    allowed_test_statuses = {
        "not_target_change",
        "missing_counts",
        "low_coverage",
        "degenerate_table",
        "tested",
    }
    allowed_call_statuses = {
        "not_tested",
        "below_mean_dp",
        "background_not_passed",
        "fdr_not_met",
        "effect_not_met",
        "significant_up",
        "significant_down",
    }
    unknown_test = set(all_value_counts.get("test_status", {})) - (
        allowed_test_statuses
    )
    unknown_call = set(all_value_counts.get("call_status", {})) - (
        allowed_call_statuses
    )
    if unknown_test or unknown_call:
        raise ArtifactIndexError(
            "Step 09 all-sites contains unknown statuses; "
            f"test_status={sorted(unknown_test)}, "
            f"call_status={sorted(unknown_call)}"
        )


def validate_step09_mutation_spectrum(
    mutation_rows: Sequence[Mapping[str, str]],
    all_sites: Inspection,
    analysis_id: str,
) -> None:
    if [row["mutation_type"] for row in mutation_rows] != list(
        step09c.CANONICAL_MUTATIONS
    ):
        raise ArtifactIndexError(
            "Step 09 mutation spectrum must contain the canonical ordered "
            "12 directed substitutions"
        )
    pair_counts = all_sites.native.get("mutation_pair_counts", {})
    total = all_sites.source["row_count"] if all_sites.source else 0
    for row in mutation_rows:
        mutation_type = row["mutation_type"]
        reference, alternate = mutation_type.split(">")
        if (
            row["analysis_id"] != analysis_id
            or row["rna_ref"] != reference
            or row["rna_alt"] != alternate
        ):
            raise ArtifactIndexError(
                "Step 09 mutation spectrum identity columns do not reconcile"
            )
        expected_counts = pair_counts.get(mutation_type, {})
        for field_name in (
            "candidate_count",
            "successfully_tested_count",
            "significant_up_count",
            "significant_down_count",
        ):
            if native_int(row, field_name) != expected_counts.get(field_name, 0):
                raise ArtifactIndexError(
                    f"Step 09 mutation spectrum {field_name} does not "
                    f"reconcile for {mutation_type}"
                )
        try:
            observed_fraction = float(row["candidate_fraction"])
        except ValueError as exc:
            raise ArtifactIndexError(
                "Step 09 mutation spectrum candidate_fraction is not numeric"
            ) from exc
        expected_fraction = (
            0.0
            if total == 0
            else expected_counts.get("candidate_count", 0) / total
        )
        if (
            not 0.0 <= observed_fraction <= 1.0
            or not step09c.values_close(observed_fraction, expected_fraction)
        ):
            raise ArtifactIndexError(
                "Step 09 mutation spectrum candidate_fraction does not "
                f"reconcile for {mutation_type}"
            )


def reconcile_step09(
    members: Sequence[Inspection],
    source_lookup: Mapping[Path, Inspection],
) -> None:
    all_sites = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_all_sites_v1"
    )
    significant = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_significant_sites_v1"
    )
    summary = next(
        member
        for member in members
        if member.row["adapter"] == "step09_cmh_summary_v1"
    )
    mutation = next(
        member
        for member in members
        if member.row["adapter"] == "step09_mutation_spectrum_tsv_v1"
    )
    summary_row = summary.first_row or {}
    all_samples = all_sites.native.get("samples", [])
    if not all_samples or all_samples != significant.native.get("samples", []):
        raise ArtifactIndexError(
            "Step 09 result sample blocks disagree"
        )
    if native_int(summary_row, "sample_count") != len(all_samples):
        raise ArtifactIndexError(
            "Step 09 summary sample_count disagrees with result columns"
        )
    if native_int(summary_row, "candidate_count") != (
        all_sites.source["row_count"] if all_sites.source else None
    ):
        raise ArtifactIndexError(
            "Step 09 summary candidate_count disagrees with all-sites rows"
        )
    significant_count = (
        significant.source["row_count"] if significant.source else None
    )
    if significant_count != (
        native_int(summary_row, "significant_up_count")
        + native_int(summary_row, "significant_down_count")
    ):
        raise ArtifactIndexError(
            "Step 09 significant table count disagrees with summary"
        )
    validate_significant_exact_subset(
        all_sites.resolved_path,
        significant.resolved_path,
    )
    all_value_counts = all_sites.native.get("value_counts", {})
    significant_value_counts = significant.native.get("value_counts", {})
    validate_step09_statuses(all_value_counts)
    test_bindings = {
        "successfully_tested_count": "tested",
        "not_target_change_count": "not_target_change",
        "missing_counts_count": "missing_counts",
        "low_coverage_count": "low_coverage",
        "degenerate_table_count": "degenerate_table",
    }
    for summary_field, status in test_bindings.items():
        if native_int(summary_row, summary_field) != (
            all_value_counts.get("test_status", {}).get(status, 0)
        ):
            raise ArtifactIndexError(
                f"Step 09 summary {summary_field} disagrees with all-sites"
            )
    call_bindings = {
        "below_mean_dp_count": "below_mean_dp",
        "background_not_passed_count": "background_not_passed",
        "fdr_not_met_count": "fdr_not_met",
        "effect_not_met_count": "effect_not_met",
        "significant_up_count": "significant_up",
        "significant_down_count": "significant_down",
    }
    for summary_field, status in call_bindings.items():
        if native_int(summary_row, summary_field) != (
            all_value_counts.get("call_status", {}).get(status, 0)
        ):
            raise ArtifactIndexError(
                f"Step 09 summary {summary_field} disagrees with all-sites"
            )
    significant_statuses = significant_value_counts.get("call_status", {})
    if set(significant_statuses) - {"significant_up", "significant_down"}:
        raise ArtifactIndexError(
            "Step 09 significant table contains a non-significant call status"
        )
    for summary_field, status in (
        ("significant_up_count", "significant_up"),
        ("significant_down_count", "significant_down"),
    ):
        if significant_statuses.get(status, 0) != native_int(
            summary_row, summary_field
        ):
            raise ArtifactIndexError(
                f"Step 09 significant {status} rows disagree with summary"
            )
    mutation_rows = mutation.native.get("rows", [])
    validate_step09_mutation_spectrum(
        mutation_rows,
        all_sites,
        summary_row.get("analysis_id", ""),
    )
    for field_name, summary_field in (
        ("candidate_count", "candidate_count"),
        ("successfully_tested_count", "successfully_tested_count"),
        ("significant_up_count", "significant_up_count"),
        ("significant_down_count", "significant_down_count"),
    ):
        observed = sum(native_int(row, field_name) for row in mutation_rows)
        if observed != native_int(summary_row, summary_field):
            raise ArtifactIndexError(
                f"Step 09 mutation spectrum {field_name} does not reconcile"
            )
    for path_field, hash_field, adapter_id in (
        ("step08_sites_path", "step08_sites_sha256", "step08_sites_v1"),
        ("step08_inputs_path", "step08_inputs_sha256", "step08_inputs_v1"),
    ):
        target = require_referenced_source(
            row=summary_row,
            path_field=path_field,
            hash_field=hash_field,
            row_count_field=None,
            source_lookup=source_lookup,
        )
        if target.row["adapter"] != adapter_id:
            raise ArtifactIndexError(
                f"Step 09 {path_field} points to the wrong adapter"
            )
        if (
            adapter_id == "step08_sites_v1"
            and target.native.get("samples") != all_samples
        ):
            raise ArtifactIndexError(
                "Step 09 result sample order disagrees with Step 08 sites"
            )


def split_native_safe_ids(value: str, field_name: str) -> list[str]:
    if value == step09c.NA_VALUE:
        return []
    values = value.split(",")
    if (
        any(not item or item.strip() != item for item in values)
        or len(values) != len(set(values))
        or any(not contracts.SAFE_ID_RE.fullmatch(item) for item in values)
    ):
        raise ArtifactIndexError(
            f"Step 09c {field_name} is not a unique comma-separated safe-ID list"
        )
    return values


def validate_step09c_evidence_index(
    evidence_rows: Sequence[Mapping[str, str]],
    plan_row: Mapping[str, str],
    summary_row: Mapping[str, str],
) -> dict[str, str]:
    if not evidence_rows:
        raise ArtifactIndexError("Step 09c evidence index is empty")
    allowed_analyses = {
        plan_row["primary_analysis_id"],
        *split_native_safe_ids(
            plan_row["superseded_analysis_ids"],
            "superseded_analysis_ids",
        ),
        *split_native_safe_ids(
            plan_row["sensitivity_analysis_ids"],
            "sensitivity_analysis_ids",
        ),
    }
    seen_evidence_ids: set[str] = set()
    category_order = {
        category: index
        for index, category in enumerate(step09c.ALLOWED_EVIDENCE_CATEGORIES)
    }
    observed_order: list[tuple[int, str]] = []
    for row in evidence_rows:
        evidence_id = row["evidence_id"]
        category = row["evidence_category"]
        status = row["evidence_status"]
        if (
            not contracts.SAFE_ID_RE.fullmatch(evidence_id)
            or evidence_id in seen_evidence_ids
        ):
            raise ArtifactIndexError(
                "Step 09c evidence IDs must be unique safe IDs"
            )
        seen_evidence_ids.add(evidence_id)
        if category not in step09c.ALLOWED_EVIDENCE_CATEGORIES:
            raise ArtifactIndexError(
                f"Step 09c evidence category is invalid: {category!r}"
            )
        if status not in step09c.EVIDENCE_STATUSES:
            raise ArtifactIndexError(
                f"Step 09c evidence status is invalid: {status!r}"
            )
        if (
            row["review_id"] != summary_row["review_id"]
            or row["analysis_id"] not in allowed_analyses
        ):
            raise ArtifactIndexError(
                "Step 09c evidence identity is outside the declared review"
            )
        observed_order.append((category_order[category], evidence_id))
        if status in {"missing", "not_applicable"}:
            if any(
                row[field_name] != step09c.NA_VALUE
                for field_name in (
                    "source_path",
                    "declared_sha256",
                    "observed_sha256",
                    "declared_row_count",
                    "observed_row_count",
                )
            ):
                raise ArtifactIndexError(
                    "Step 09c missing/not-applicable evidence must use NA "
                    "for source path, hashes, and row counts"
                )
            if (
                status == "missing"
                and row["not_applicable_reason"] != step09c.NA_VALUE
            ) or (
                status == "not_applicable"
                and row["not_applicable_reason"] in {"", step09c.NA_VALUE}
            ):
                raise ArtifactIndexError(
                    "Step 09c evidence not-applicable reason is inconsistent"
                )
        else:
            if (
                row["source_path"] == step09c.NA_VALUE
                or row["not_applicable_reason"] != step09c.NA_VALUE
                or not SHA256_RE.fullmatch(row["declared_sha256"])
                or row["declared_sha256"] != row["observed_sha256"]
                or native_int(row, "declared_row_count")
                != native_int(row, "observed_row_count")
            ):
                raise ArtifactIndexError(
                    "Step 09c complete/incomplete evidence source metadata "
                    "does not reconcile"
                )
            if (
                status == "complete"
                and native_int(row, "observed_row_count") == 0
            ):
                raise ArtifactIndexError(
                    "Step 09c complete evidence must contain at least one row; "
                    "use not_applicable for a justified empty category"
                )
    if observed_order != sorted(observed_order):
        raise ArtifactIndexError(
            "Step 09c evidence index is not in canonical category/ID order"
        )
    missing_categories = [
        category
        for category in step09c.CATEGORY_ORDER
        if not any(
            row["evidence_category"] == category for row in evidence_rows
        )
    ]
    if missing_categories:
        raise ArtifactIndexError(
            "Step 09c evidence index omits required explicit categories: "
            + ", ".join(missing_categories)
        )
    for category in step09c.CATEGORY_ORDER:
        status = step09c.aggregate_evidence_status(evidence_rows, category)
        if summary_row[f"{category}_status"] != status:
            raise ArtifactIndexError(
                f"Step 09c summary {category}_status disagrees with evidence"
            )
    expected_source_count = sum(
        row["evidence_status"] in {"complete", "incomplete"}
        for row in evidence_rows
    )
    if native_int(summary_row, "evidence_source_count") != expected_source_count:
        raise ArtifactIndexError(
            "Step 09c summary evidence_source_count disagrees with evidence"
        )
    return {
        category: step09c.aggregate_evidence_status(evidence_rows, category)
        for category in step09c.ALLOWED_EVIDENCE_CATEGORIES
    }


def validate_step09c_payloads(
    *,
    by_adapter: Mapping[str, Inspection],
    evidence_rows: Sequence[Mapping[str, str]],
    plan_row: Mapping[str, str],
    summary_row: Mapping[str, str],
) -> None:
    allowed_analysis_ids = {
        plan_row["primary_analysis_id"],
        *split_native_safe_ids(
            plan_row["superseded_analysis_ids"],
            "superseded_analysis_ids",
        ),
        *split_native_safe_ids(
            plan_row["sensitivity_analysis_ids"],
            "sensitivity_analysis_ids",
        ),
    }
    evidence_by_category: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_category[row["evidence_category"]].append(row)
    for category, adapter_id in STEP09C_CATEGORY_ADAPTERS.items():
        member = by_adapter[adapter_id]
        payload_rows = member.native.get("rows", [])
        indexed_rows = evidence_by_category[category]
        indexed_by_id = {row["evidence_id"]: row for row in indexed_rows}
        expected_counts = {
            row["evidence_id"]: (
                native_int(row, "observed_row_count")
                if row["evidence_status"] in {"complete", "incomplete"}
                else 0
            )
            for row in indexed_rows
        }
        payload_counts = Counter(row["evidence_id"] for row in payload_rows)
        if payload_counts != Counter(expected_counts):
            raise ArtifactIndexError(
                f"Step 09c {category} payload row counts disagree with "
                "the evidence index"
            )
        expected_total = sum(expected_counts.values())
        observed_total = member.source["row_count"] if member.source else None
        if observed_total != expected_total:
            raise ArtifactIndexError(
                f"Step 09c {category} published row count disagrees with "
                "the evidence index"
            )
        for row in payload_rows:
            evidence = indexed_by_id.get(row["evidence_id"])
            if (
                evidence is None
                or row["review_id"] != summary_row["review_id"]
                or row.get("analysis_id") not in allowed_analysis_ids
            ):
                raise ArtifactIndexError(
                    f"Step 09c {category} payload identity is not declared "
                    "by the review/evidence index"
                )
            if (
                "primary_analysis_id" in row
                and row["primary_analysis_id"] != plan_row["primary_analysis_id"]
            ):
                raise ArtifactIndexError(
                    f"Step 09c {category} payload primary analysis is invalid"
                )


def validate_step09c_decisions(
    decision_rows: Sequence[Mapping[str, str]],
    summary_row: Mapping[str, str],
    *,
    require_complete: bool,
) -> dict[str, str]:
    seen: set[str] = set()
    decisions: dict[str, str] = {}
    for row in decision_rows:
        dimension = row["decision_dimension"]
        if (
            row["review_id"] != summary_row["review_id"]
            or dimension not in step09c.DECISION_DIMENSIONS
            or dimension in seen
            or row["evidence_status"] not in step09c.EVIDENCE_STATUSES
            or row["decision_status"] not in step09c.DECISION_STATUSES
        ):
            raise ArtifactIndexError(
                "Step 09c decision identity/status contract is invalid"
            )
        seen.add(dimension)
        if row["decision_status"] == "recorded":
            if (
                row["decision_value"] in {"", step09c.NA_VALUE}
                or row["decision_date"] in {"", step09c.NA_VALUE}
            ):
                raise ArtifactIndexError(
                    "Step 09c recorded decision lacks a value or date"
                )
            decisions[dimension] = row["decision_value"]
        else:
            if (
                row["decision_value"] != step09c.NA_VALUE
                or row["decision_date"] != step09c.NA_VALUE
            ):
                raise ArtifactIndexError(
                    "Step 09c pending decision must use NA value/date"
                )
            decisions[dimension] = "pending"
    if require_complete and (
        seen != set(step09c.DECISION_DIMENSIONS)
        or any(value == "pending" for value in decisions.values())
    ):
        raise ArtifactIndexError(
            "Step 09c completed science state lacks complete decisions"
        )
    summary_fields = {
        "background": "background_decision",
        "matched_dna": "matched_dna_decision",
        "orthogonal_evidence": "orthogonal_evidence_decision",
        "annotation": "annotation_decision",
        "thresholds": "thresholds_decision",
        "adjudication": "adjudication_decision",
        "orientation": "orientation_decision",
    }
    for dimension, field_name in summary_fields.items():
        if summary_row[field_name] != decisions.get(dimension, "pending"):
            raise ArtifactIndexError(
                f"Step 09c summary {field_name} disagrees with decisions"
            )
    return decisions


def step09c_candidate_keys(
    rows: Sequence[Mapping[str, str]],
    label: str,
) -> set[tuple[str, str]]:
    keys = {(row["analysis_id"], row["candidate_id"]) for row in rows}
    if len(keys) != len(rows):
        raise ArtifactIndexError(
            f"Step 09c {label} contains duplicate candidate identities"
        )
    return keys


def reconcile_step09c(
    members: Sequence[Inspection],
    source_lookup: Mapping[Path, Inspection],
) -> None:
    by_adapter = {member.row["adapter"]: member for member in members}
    plan = by_adapter["step09c_review_plan_v1"]
    summary = by_adapter["step09c_review_summary_v1"]
    plan_row = plan.first_row or {}
    summary_row = summary.first_row or {}
    for field_name in step09c.REVIEW_PLAN_HEADER:
        if summary_row.get(field_name) != plan_row.get(field_name):
            raise ArtifactIndexError(
                f"Step 09c summary disagrees with review plan: {field_name}"
            )
    if native_int(summary_row, "published_output_count") != len(
        step09c.OUTPUT_SUFFIXES
    ):
        raise ArtifactIndexError(
            "Step 09c published_output_count is inconsistent"
        )
    if summary_row.get("transaction_state") != "complete":
        raise ArtifactIndexError(
            "Step 09c summary transaction_state is not complete"
        )
    status_contracts = {
        "implementation_status": step09c.IMPLEMENTATION_STATUSES,
        "local_test_status": step09c.LOCAL_TEST_STATUSES,
        "runtime_validation_status": step09c.RUNTIME_VALIDATION_STATUSES,
        "cluster_dry_run_status": step09c.CLUSTER_DRY_RUN_STATUSES,
        "cluster_proof_status": step09c.CLUSTER_PROOF_STATUSES,
        "orientation_status": step09c.ORIENTATION_STATUSES,
    }
    for field_name, allowed in status_contracts.items():
        if summary_row.get(field_name) not in allowed:
            raise ArtifactIndexError(
                f"Step 09c summary {field_name} is invalid"
            )
    for category in step09c.CATEGORY_ORDER:
        field_name = f"{category}_status"
        if summary_row.get(field_name) not in step09c.EVIDENCE_STATUSES:
            raise ArtifactIndexError(
                f"Step 09c summary {field_name} is invalid"
            )
    for prefix in (
        "sample_manifest",
        "partition_manifest",
        "evidence_manifest",
    ):
        if not summary_row.get(f"{prefix}_path"):
            raise ArtifactIndexError(
                f"Step 09c summary {prefix}_path is empty"
            )
        if not SHA256_RE.fullmatch(summary_row.get(f"{prefix}_sha256", "")):
            raise ArtifactIndexError(
                f"Step 09c summary {prefix}_sha256 is invalid"
            )
        native_int(summary_row, f"{prefix}_row_count")
    if native_int(summary_row, "evidence_source_count") > native_int(
        summary_row, "evidence_record_count"
    ):
        raise ArtifactIndexError(
            "Step 09c evidence source count exceeds evidence record count"
        )
    count_bindings = (
        (
            "step09c_evidence_index_v1",
            "evidence_record_count",
        ),
        (
            "step09c_candidate_selection_v1",
            "selected_candidate_count",
        ),
        (
            "step09c_candidate_adjudication_v1",
            "adjudicated_candidate_count",
        ),
        (
            "step09c_limitations_v1",
            "limitation_count",
        ),
    )
    for adapter_id, field_name in count_bindings:
        member = by_adapter[adapter_id]
        if native_int(summary_row, field_name) != (
            member.source["row_count"] if member.source else None
        ):
            raise ArtifactIndexError(
                f"Step 09c summary {field_name} is inconsistent"
            )
    evidence_rows = by_adapter["step09c_evidence_index_v1"].native.get(
        "rows",
        [],
    )
    if native_int(summary_row, "evidence_manifest_row_count") != len(
        evidence_rows
    ):
        raise ArtifactIndexError(
            "Step 09c evidence manifest and evidence index row counts disagree"
        )
    category_statuses = validate_step09c_evidence_index(
        evidence_rows,
        plan_row,
        summary_row,
    )
    validate_step09c_payloads(
        by_adapter=by_adapter,
        evidence_rows=evidence_rows,
        plan_row=plan_row,
        summary_row=summary_row,
    )
    overall_status = summary_row.get("overall_science_status", "")
    exploratory_complete = (
        overall_status == "science_review_complete_exploratory"
    )
    decisions = validate_step09c_decisions(
        by_adapter["step09c_decisions_v1"].native.get("rows", []),
        summary_row,
        require_complete=exploratory_complete,
    )
    selected = step09c_candidate_keys(
        by_adapter["step09c_candidate_selection_v1"].native.get("rows", []),
        "candidate selection",
    )
    adjudicated = step09c_candidate_keys(
        by_adapter["step09c_candidate_adjudication_v1"].native.get("rows", []),
        "candidate adjudication",
    )
    if exploratory_complete:
        incomplete_categories = {
            category: category_statuses[category]
            for category in step09c.CATEGORY_ORDER
            if category_statuses[category] not in {"complete", "not_applicable"}
        }
        if incomplete_categories:
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state has incomplete evidence "
                f"categories: {incomplete_categories}"
            )
        if category_statuses["decisions"] != "complete":
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state lacks completed decisions"
            )
        if selected != adjudicated:
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state lacks complete "
                "candidate adjudication coverage"
            )
        if summary_row.get("review_completed_date") == step09c.NA_VALUE:
            raise ArtifactIndexError(
                "Step 09c exploratory-complete state lacks a completion date"
            )
    elif summary_row.get("review_completed_date") != step09c.NA_VALUE:
        raise ArtifactIndexError(
            "Step 09c evidence-incomplete state must not claim a completion date"
        )
    orientation_status = summary_row.get("orientation_status")
    if orientation_status != "provisional" and (
        category_statuses["orientation_locus_audit"] != "complete"
        or category_statuses["decisions"] != "complete"
        or decisions.get("orientation") != orientation_status
    ):
        raise ArtifactIndexError(
            "Step 09c non-provisional orientation status lacks complete "
            "orientation evidence and a matching recorded decision"
        )
    if (
        summary_row.get("cluster_proof_status") == "proven"
        and category_statuses["computational_validation"] != "complete"
    ):
        raise ArtifactIndexError(
            "Step 09c cluster proof lacks complete computational evidence"
        )
    input_bindings = (
        ("step08_sites", "step08_sites_v1"),
        ("step08_inputs", "step08_inputs_v1"),
        ("step08_summary", "step08_summary_v1"),
        ("step09_all_sites", "step09_cmh_all_sites_v1"),
        (
            "step09_significant_sites",
            "step09_cmh_significant_sites_v1",
        ),
        ("step09_summary", "step09_cmh_summary_v1"),
        (
            "step09_mutation_spectrum",
            "step09_mutation_spectrum_tsv_v1",
        ),
        (
            "step09_mutation_spectrum_pdf",
            "step09_mutation_spectrum_pdf_v1",
        ),
        ("step09_depth_delta_pdf", "step09_depth_delta_pdf_v1"),
        ("review_plan", "step09c_review_plan_v1"),
    )
    for prefix, adapter_id in input_bindings:
        target = require_referenced_source(
            row=summary_row,
            path_field=f"{prefix}_path",
            hash_field=f"{prefix}_sha256",
            row_count_field=f"{prefix}_row_count",
            source_lookup=source_lookup,
        )
        if target.row["adapter"] != adapter_id:
            raise ArtifactIndexError(
                f"Step 09c {prefix}_path points to the wrong adapter"
            )


def reconcile_native_transactions(
    inspections: Sequence[Inspection],
) -> None:
    source_lookup = {
        inspection.resolved_path: inspection for inspection in inspections
    }
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        row = inspection.row
        grouped[(row["step_id"], row["scope_type"], row["scope_id"])].append(
            inspection
        )
    marker_adapters = {
        "00c": "step00c_reference_dict_v1",
        "06": "step06_orientation_counts_v1",
        "07": "step07_mpileup_receipt_v1",
        "08": "step08_summary_v1",
        "09": "step09_cmh_summary_v1",
        "09c": "step09c_review_summary_v1",
    }
    validators = {
        "00c": lambda members: reconcile_step00c(members),
        "06": lambda members: reconcile_step06(members),
        "07": lambda members: reconcile_step07(members),
        "08": lambda members: reconcile_step08(members, source_lookup),
        "09": lambda members: reconcile_step09(members, source_lookup),
        "09c": lambda members: reconcile_step09c(members, source_lookup),
    }
    dependency_order = {
        "00c": 0,
        "06": 1,
        "07": 2,
        "08": 3,
        "09": 4,
        "09c": 5,
    }
    ordered_scopes = sorted(
        grouped,
        key=lambda scope: (
            dependency_order.get(scope[0], len(dependency_order)),
            scope,
        ),
    )
    for scope in ordered_scopes:
        members = grouped[scope]
        step_id = scope[0]
        validator = validators.get(step_id)
        if validator is None or any(
            member.row["required"] == "true"
            and member.completion_status != "complete"
            for member in members
        ):
            continue
        try:
            validator(members)
        except ArtifactIndexError as exc:
            mark_native_transaction_failed(
                members,
                marker_adapters[step_id],
                f"Scope {scope!r}: {exc}",
            )
            # Propagate this scope failure before validating downstream
            # transactions that explicitly reference one of its members.
            reconcile_scope_transactions(members)


def reconcile_scope_transactions(inspections: Sequence[Inspection]) -> None:
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        row = inspection.row
        grouped[(row["step_id"], row["scope_type"], row["scope_id"])].append(
            inspection
        )
    for scope, members in grouped.items():
        blocking = [
            member
            for member in members
            if member.row["required"] == "true"
            and member.completion_status != "complete"
        ]
        if not blocking:
            continue
        blocking_ids = ", ".join(member.row["artifact_id"] for member in blocking)
        for member in members:
            if member.completion_status != "complete":
                continue
            member.completion_status = "incomplete"
            member.state_reason = (
                "Logical scope transaction is incomplete or invalid."
            )
            member.warnings.append(
                issue(
                    "scope_transaction_incomplete",
                    f"Scope {scope!r} has incomplete/invalid required "
                    f"artifacts: {blocking_ids}",
                    member.row["artifact_id"],
                )
            )


def resolve_scientific_states(
    inspections: Sequence[Inspection],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Inspection]] = defaultdict(list)
    for inspection in inspections:
        row = inspection.row
        grouped[(row["step_id"], row["scope_type"], row["scope_id"])].append(
            inspection
        )
    resolved: dict[tuple[str, str, str], dict[str, Any]] = {}
    for scope, members in grouped.items():
        if scope[0] != "09c" or any(
            member.completion_status != "complete"
            for member in members
            if member.row["required"] == "true"
        ):
            continue
        summary = next(
            (
                member
                for member in members
                if member.row["adapter"] == "step09c_review_summary_v1"
            ),
            None,
        )
        if summary is None or summary.first_row is None:
            continue
        row = summary.first_row
        science_status = row.get("overall_science_status", "")
        if science_status not in {
            "evidence_incomplete",
            "science_review_complete_exploratory",
        }:
            summary.completion_status = "failed"
            summary.state_reason = "Review summary science status is invalid."
            summary.errors.append(
                issue(
                    "science_status_invalid",
                    "Step 09c cannot emit the reserved or unknown science "
                    f"status {science_status!r}",
                    summary.row["artifact_id"],
                )
            )
            reconcile_scope_transactions(members)
            continue
        orientation_status = row.get("orientation_status", "")
        if orientation_status not in {
            "provisional",
            "validated",
            "replacement_required",
        }:
            summary.completion_status = "failed"
            summary.state_reason = "Review summary orientation status is invalid."
            summary.errors.append(
                issue(
                    "orientation_status_invalid",
                    "Step 09c review summary has an unknown orientation "
                    f"status {orientation_status!r}",
                    summary.row["artifact_id"],
                )
            )
            reconcile_scope_transactions(members)
            continue
        orientation_policy = row.get("orientation_policy", "")
        if not contracts.SAFE_ID_RE.fullmatch(orientation_policy):
            summary.completion_status = "failed"
            summary.state_reason = "Review summary orientation policy is invalid."
            summary.errors.append(
                issue(
                    "orientation_policy_invalid",
                    "Step 09c review summary orientation policy must be a "
                    f"safe non-empty ID, observed {orientation_policy!r}",
                    summary.row["artifact_id"],
                )
            )
            reconcile_scope_transactions(members)
            continue
        resolved[scope] = {
            "overall_status": science_status,
            "orientation_status": orientation_status,
            "orientation_policy": orientation_policy,
            "review_id": scope[2],
        }
    return resolved


def producer_evidence(git_commit: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for step_id, relative_path in STEP_PRODUCERS.items():
        path = contracts.REPO_ROOT / relative_path
        if not path.is_file():
            raise ArtifactIndexError(
                f"Registered producer path is missing: {relative_path}"
            )
        result[step_id] = {
            "status": "implemented",
            "git_commit": git_commit,
            "evidence": [
                {
                    "evidence_id": f"implementation_{step_id}",
                    "role": "implementation",
                    "path": relative_path,
                    "sha256": contracts.sha256_file(path),
                }
            ],
        }
    return result


def build_artifact_record(
    *,
    run_id: str,
    run_contract: dict[str, Any],
    inspection: Inspection,
    implementation: dict[str, Any],
    scientific_state: dict[str, Any] | None,
    git_commit: str,
    created_at: str,
) -> dict[str, Any]:
    return {
        "schema_name": "norad.artifact_record",
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "record_type": "artifact_record",
        "run_id": run_id,
        "run_contract": run_contract,
        "artifact_id": inspection.row["artifact_id"],
        "scope": {
            "step_id": inspection.row["step_id"],
            "scope_type": inspection.row["scope_type"],
            "scope_id": inspection.row["scope_id"],
        },
        "adapter": inspection.row["adapter"],
        "expectation": {
            "required": inspection.row["required"] == "true",
            "source_path": inspection.row["source_path"],
        },
        "availability_status": inspection.availability_status,
        "completion_status": inspection.completion_status,
        "state_reason": inspection.state_reason,
        "attempt_provenance_status": inspection.attempt_provenance_status,
        "attempts": [],
        "selected_attempt_id": None,
        "implementation": implementation,
        "local_testing": {"status": "not_run", "evidence": []},
        "runtime_validation": {
            "status": "not_run",
            "detail": None,
            "evidence": [],
        },
        "cluster_validation": {
            "dry_run_status": "not_run",
            "proof_status": "not_run",
            "evidence": [],
        },
        "source": inspection.source,
        "members": [],
        "tools": [],
        "parameters": inspection.parameters,
        "metrics": inspection.metrics,
        "scientific_state": scientific_state,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
        "provenance": {
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "git_commit": git_commit,
            "created_at": created_at,
        },
    }


def validate_record_in_memory(
    record: dict[str, Any],
    inventory_row: dict[str, str],
    validator: Draft202012Validator,
) -> None:
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: "
            f"{error.message}"
            for error in errors
        )
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed schema:\n"
            f"{detail}"
        )
    try:
        contracts.validate_artifact_semantics(record)
        contracts.reconcile_artifact_inventory_row(record, inventory_row)
    except contracts.ContractValidationError as exc:
        raise ArtifactIndexError(
            f"Generated artifact {record['artifact_id']!r} failed semantic "
            f"validation: {exc}"
        ) from exc


def build_index_rows(
    *,
    records: Sequence[dict[str, Any]],
    record_bytes: Sequence[bytes],
    records_dir: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record, payload in zip(records, record_bytes, strict=True):
        source = record["source"] or {}
        science = record["scientific_state"] or {}
        rows.append(
            {
                "run_id": record["run_id"],
                "run_contract_sha256": record["run_contract"][
                    "run_contract_sha256"
                ],
                "artifact_id": record["artifact_id"],
                "step_id": record["scope"]["step_id"],
                "scope_type": record["scope"]["scope_type"],
                "scope_id": record["scope"]["scope_id"],
                "adapter": record["adapter"],
                "source_path": record["expectation"]["source_path"],
                "required": str(record["expectation"]["required"]).lower(),
                "availability_status": record["availability_status"],
                "completion_status": record["completion_status"],
                "attempt_provenance_status": record[
                    "attempt_provenance_status"
                ],
                "selected_attempt_id": safe_tsv(record["selected_attempt_id"]),
                "implementation_status": record["implementation"]["status"],
                "local_test_status": record["local_testing"]["status"],
                "runtime_validation_status": record["runtime_validation"][
                    "status"
                ],
                "cluster_dry_run_status": record["cluster_validation"][
                    "dry_run_status"
                ],
                "cluster_proof_status": record["cluster_validation"][
                    "proof_status"
                ],
                "science_status": safe_tsv(science.get("overall_status")),
                "orientation_status": safe_tsv(
                    science.get("orientation_status")
                ),
                "orientation_policy": safe_tsv(
                    science.get("orientation_policy")
                ),
                "review_id": safe_tsv(science.get("review_id")),
                "source_sha256": safe_tsv(source.get("sha256")),
                "source_size_bytes": safe_tsv(source.get("size_bytes")),
                "source_row_count": safe_tsv(source.get("row_count")),
                "source_media_type": safe_tsv(source.get("media_type")),
                "warning_count": str(len(record["warnings"])),
                "error_count": str(len(record["errors"])),
                "record_path": str(
                    records_dir / f"{record['artifact_id']}.json"
                ),
                "record_sha256": sha256_bytes(payload),
                "record_schema_version": record["schema_version"],
            }
        )
    return rows


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(header),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: safe_tsv(row[field]) for field in header})
    return stream.getvalue().encode("utf-8")


def load_existing_receipt(
    receipt_path: Path,
    artifacts_path: Path,
    records_dir: Path,
) -> dict[str, str] | None:
    owned = tuple(
        path.exists() or path.is_symlink()
        for path in (receipt_path, artifacts_path, records_dir)
    )
    if any(owned) and not all(owned):
        raise ArtifactIndexError(
            "Existing artifact-index output set is incomplete; preserve it "
            f"for recovery: {receipt_path.parent}"
        )
    if not any(owned):
        return None
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise ArtifactIndexError(
            f"Existing artifact receipt is not a regular owned file: {receipt_path}"
        )
    if artifacts_path.is_symlink() or not artifacts_path.is_file():
        raise ArtifactIndexError(
            f"Existing artifact index is not a regular owned file: {artifacts_path}"
        )
    if records_dir.is_symlink() or not records_dir.is_dir():
        raise ArtifactIndexError(
            f"Existing records path is not a regular owned directory: {records_dir}"
        )
    rows = read_exact_tsv(
        receipt_path,
        ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )
    return rows[0]


def read_exact_tsv(
    path: Path,
    header: Sequence[str],
    *,
    exact_rows: int | None = None,
) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != tuple(header):
                raise ArtifactIndexError(f"TSV header is invalid: {path}")
            rows = list(reader)
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ArtifactIndexError(f"Could not read TSV {path}: {exc}") from exc
    if exact_rows is not None and len(rows) != exact_rows:
        raise ArtifactIndexError(
            f"TSV {path} must contain {exact_rows} rows; observed {len(rows)}"
        )
    return rows


def validate_existing_identity(
    existing: Mapping[str, str] | None,
    run_contract: Mapping[str, Any],
) -> tuple[str | None, list[str]]:
    if existing is None:
        return None, []
    for field_name in RUN_CONTRACT_FIELDS:
        if existing[field_name] != str(run_contract[field_name]):
            raise ArtifactIndexError(
                "Existing run_id is bound to a different immutable run "
                f"contract field: {field_name}"
            )
    if existing["transaction_state"] != "complete":
        raise ArtifactIndexError("Existing artifact receipt is not complete")
    history = [
        value
        for value in existing["adapter_attempt_history"].split(",")
        if value
    ]
    if not history or history[-1] != existing["adapter_attempt_id"]:
        raise ArtifactIndexError(
            "Existing artifact receipt attempt history is inconsistent"
        )
    if len(history) != len(set(history)):
        raise ArtifactIndexError(
            "Existing artifact receipt attempt history contains duplicates"
        )
    return existing["adapter_attempt_id"], history


def inventory_rows_from_published_index(
    artifacts_path: Path,
) -> list[dict[str, str]]:
    index_rows = read_exact_tsv(artifacts_path, ARTIFACT_INDEX_HEADER)
    return [
        {
            field_name: row[field_name]
            for field_name in contracts.INVENTORY_HEADER
        }
        for row in index_rows
    ]


def validate_existing_transaction(
    *,
    existing: Mapping[str, str],
    run_id: str,
    run_contract: Mapping[str, Any],
    records_dir: Path,
    artifacts_path: Path,
    receipt_path: Path,
) -> None:
    previous_inventory_rows = inventory_rows_from_published_index(
        artifacts_path
    )
    validate_published_transaction(
        run_id=run_id,
        run_contract=run_contract,
        run_contract_path=Path(existing["run_contract_path"]),
        run_contract_file_sha256=existing["run_contract_file_sha256"],
        inventory_path=Path(existing["inventory_path"]),
        inventory_sha256=existing["inventory_sha256"],
        inventory_rows=previous_inventory_rows,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        require_current_source_locations=False,
    )


def build_receipt_row(
    *,
    run_id: str,
    run_contract: Mapping[str, Any],
    run_contract_path: Path,
    run_contract_file_sha256: str,
    inventory_path: Path,
    inventory_sha256: str,
    inventory_row_count: int,
    artifacts_path: Path,
    index_bytes: bytes,
    index_rows: Sequence[Mapping[str, str]],
    attempt_id: str,
    previous_attempt_id: str | None,
    attempt_history: Sequence[str],
    git_commit: str,
    started_at: str,
    finished_at: str,
) -> dict[str, str]:
    availability = Counter(row["availability_status"] for row in index_rows)
    completion = Counter(row["completion_status"] for row in index_rows)
    record_manifest = [
        {
            "artifact_id": row["artifact_id"],
            "record_path": row["record_path"],
            "record_sha256": row["record_sha256"],
        }
        for row in index_rows
    ]
    required_count = sum(row["required"] == "true" for row in index_rows)
    required_missing = sum(
        row["required"] == "true"
        and row["availability_status"] != "present"
        for row in index_rows
    )
    return {
        "run_id": run_id,
        "run_contract_sha256": str(run_contract["run_contract_sha256"]),
        "run_contract_path": str(run_contract_path),
        "run_contract_file_sha256": run_contract_file_sha256,
        "sample_manifest_sha256": str(run_contract["sample_manifest_sha256"]),
        "reference_contract_sha256": str(
            run_contract["reference_contract_sha256"]
        ),
        "partition_manifest_sha256": str(
            run_contract["partition_manifest_sha256"]
        ),
        "primary_analysis_id": str(run_contract["primary_analysis_id"]),
        "primary_analysis_policy_sha256": str(
            run_contract["primary_analysis_policy_sha256"]
        ),
        "inventory_path": str(inventory_path),
        "inventory_sha256": inventory_sha256,
        "inventory_row_count": str(inventory_row_count),
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_index_schema_version": ARTIFACT_INDEX_SCHEMA_VERSION,
        "artifact_receipt_schema_version": ARTIFACT_RECEIPT_SCHEMA_VERSION,
        "artifacts_index_path": str(artifacts_path),
        "artifacts_index_sha256": sha256_bytes(index_bytes),
        "artifact_record_count": str(len(index_rows)),
        "record_set_sha256": canonical_digest(record_manifest),
        "required_artifact_count": str(required_count),
        "required_missing_artifact_count": str(required_missing),
        "present_artifact_count": str(availability["present"]),
        "missing_artifact_count": str(availability["missing"]),
        "externally_unavailable_artifact_count": str(
            availability["externally_unavailable"]
        ),
        "unknown_artifact_count": str(availability["unknown"]),
        "complete_artifact_count": str(completion["complete"]),
        "not_attempted_artifact_count": str(completion["not_attempted"]),
        "in_progress_artifact_count": str(completion["in_progress"]),
        "incomplete_artifact_count": str(completion["incomplete"]),
        "failed_artifact_count": str(completion["failed"]),
        "warning_count": str(
            sum(int(row["warning_count"]) for row in index_rows)
        ),
        "error_count": str(sum(int(row["error_count"]) for row in index_rows)),
        "published_output_count": str(len(index_rows) + 2),
        "adapter_attempt_id": attempt_id,
        "supersedes_adapter_attempt_id": previous_attempt_id or "",
        "adapter_attempt_history": ",".join([*attempt_history, attempt_id]),
        "producer": PRODUCER,
        "producer_version": PRODUCER_VERSION,
        "git_commit": git_commit,
        "started_at": started_at,
        "finished_at": finished_at,
        "transaction_state": "complete",
    }


def prepare_context(arguments: argparse.Namespace) -> BuildContext:
    if not contracts.SAFE_ID_RE.fullmatch(arguments.run_id):
        raise ArtifactIndexError(
            "run_id must match [A-Za-z0-9][A-Za-z0-9._-]*"
        )
    run_contract_path = arguments.run_contract.expanduser().resolve()
    inventory_path = arguments.inventory.expanduser().resolve()
    output_root = arguments.output_root.expanduser().resolve()
    run_contract, run_contract_file_sha256 = load_run_contract(
        run_contract_path
    )
    inventory_rows = contracts.validate_inventory(inventory_path)
    validate_inventory_registry(inventory_rows)
    inventory_sha256 = contracts.sha256_file(inventory_path)
    output_dir = output_root / arguments.run_id
    records_dir = output_dir / "records"
    artifacts_path = output_dir / f"{arguments.run_id}.artifacts.tsv"
    receipt_path = output_dir / f"{arguments.run_id}.artifact_receipt.tsv"
    lock_path = output_dir / f".{arguments.run_id}.artifact-index.lock"
    if output_dir.is_symlink():
        raise ArtifactIndexError(
            f"Artifact-index output directory must not be a symlink: {output_dir}"
        )
    if lock_path.exists() or lock_path.is_symlink():
        raise ArtifactIndexError(
            f"Artifact-index output is locked; inspect owner metadata: {lock_path}"
        )
    for label, path in (
        ("run contract", run_contract_path),
        ("inventory", inventory_path),
    ):
        if path == output_dir or output_dir in path.parents:
            raise ArtifactIndexError(
                f"The {label} must not live inside its generated run directory"
            )
    for row in inventory_rows:
        source = contracts.resolve_contract_path(row["source_path"])
        if source == output_dir or output_dir in source.parents:
            raise ArtifactIndexError(
                "Inventory source paths must not point inside the generated "
                f"run directory: {row['source_path']}"
            )

    existing = load_existing_receipt(receipt_path, artifacts_path, records_dir)
    previous_attempt_id, attempt_history = validate_existing_identity(
        existing,
        run_contract,
    )
    if existing is not None:
        validate_existing_transaction(
            existing=existing,
            run_id=arguments.run_id,
            run_contract=run_contract,
            records_dir=records_dir,
            artifacts_path=artifacts_path,
            receipt_path=receipt_path,
        )

    started_at = utc_now()
    attempt_id = new_attempt_id(started_at)
    git_commit = get_git_commit()
    evidence = producer_evidence(git_commit)
    inspections = [
        inspect_source(row, ADAPTER_REGISTRY[row["adapter"]])
        for row in inventory_rows
    ]
    apply_run_contract_checks(inspections, run_contract)
    reconcile_native_transactions(inspections)
    reconcile_scope_transactions(inspections)
    scientific_states = resolve_scientific_states(inspections)

    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["artifact-record"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    records: list[dict[str, Any]] = []
    record_bytes: list[bytes] = []
    for inspection, inventory_row in zip(
        inspections, inventory_rows, strict=True
    ):
        scope = (
            inventory_row["step_id"],
            inventory_row["scope_type"],
            inventory_row["scope_id"],
        )
        record = build_artifact_record(
            run_id=arguments.run_id,
            run_contract=run_contract,
            inspection=inspection,
            implementation=evidence[inventory_row["step_id"]],
            scientific_state=scientific_states.get(scope),
            git_commit=git_commit,
            created_at=started_at,
        )
        validate_record_in_memory(record, inventory_row, validator)
        records.append(record)
        record_bytes.append(canonical_json_bytes(record))

    index_rows = build_index_rows(
        records=records,
        record_bytes=record_bytes,
        records_dir=records_dir,
    )
    index_bytes = tsv_bytes(ARTIFACT_INDEX_HEADER, index_rows)
    finished_at = utc_now()
    receipt_row = build_receipt_row(
        run_id=arguments.run_id,
        run_contract=run_contract,
        run_contract_path=run_contract_path,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_row_count=len(inventory_rows),
        artifacts_path=artifacts_path,
        index_bytes=index_bytes,
        index_rows=index_rows,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        git_commit=git_commit,
        started_at=started_at,
        finished_at=finished_at,
    )
    receipt_bytes = tsv_bytes(ARTIFACT_RECEIPT_HEADER, [receipt_row])
    context = BuildContext(
        run_id=arguments.run_id,
        run_contract_path=run_contract_path,
        run_contract=run_contract,
        run_contract_file_sha256=run_contract_file_sha256,
        inventory_path=inventory_path,
        inventory_sha256=inventory_sha256,
        inventory_rows=inventory_rows,
        output_root=output_root,
        output_dir=output_dir,
        records_dir=records_dir,
        artifacts_path=artifacts_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
        git_commit=git_commit,
        producer_evidence=evidence,
        inspections=inspections,
        records=records,
        record_bytes=record_bytes,
        index_rows=index_rows,
        index_bytes=index_bytes,
        receipt_row=receipt_row,
        receipt_bytes=receipt_bytes,
        started_at=started_at,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history,
        previous_receipt=existing,
    )
    validate_context_in_memory(context)
    return context


def validate_context_in_memory(context: BuildContext) -> None:
    if [row["artifact_id"] for row in context.index_rows] != [
        row["artifact_id"] for row in context.inventory_rows
    ]:
        raise ArtifactIndexError(
            "Generated artifact index order differs from inventory order"
        )
    if context.receipt_row["artifacts_index_sha256"] != sha256_bytes(
        context.index_bytes
    ):
        raise ArtifactIndexError("Generated artifact index hash is inconsistent")
    manifest = [
        {
            "artifact_id": row["artifact_id"],
            "record_path": row["record_path"],
            "record_sha256": row["record_sha256"],
        }
        for row in context.index_rows
    ]
    if context.receipt_row["record_set_sha256"] != canonical_digest(manifest):
        raise ArtifactIndexError("Generated record-set hash is inconsistent")
    if context.receipt_row["transaction_state"] != "complete":
        raise ArtifactIndexError("Generated receipt is not complete")


def source_snapshot_matches(
    expected: SourceSnapshot,
    observed: SourceSnapshot,
) -> bool:
    return (
        expected.status,
        expected.size_bytes,
        expected.file_type,
        expected.link_target,
        expected.device,
        expected.inode,
        expected.mtime_ns,
        expected.ctime_ns,
    ) == (
        observed.status,
        observed.size_bytes,
        observed.file_type,
        observed.link_target,
        observed.device,
        observed.inode,
        observed.mtime_ns,
        observed.ctime_ns,
    )


def recheck_inputs(context: BuildContext) -> None:
    if contracts.sha256_file(context.run_contract_path) != (
        context.run_contract_file_sha256
    ):
        raise ArtifactIndexError(
            "Run-contract file changed after initial validation"
        )
    if contracts.sha256_file(context.inventory_path) != context.inventory_sha256:
        raise ArtifactIndexError("Inventory changed after initial validation")
    for inspection in context.inspections:
        observed = stat_source(
            inspection.resolved_path,
            hash_content=(
                inspection.snapshot is not None
                and inspection.snapshot.file_type == "hash_read_error"
            ),
        )
        if inspection.snapshot is None or not source_snapshot_matches(
            inspection.snapshot, observed
        ):
            raise ArtifactIndexError(
                "Declared source changed after initial inspection: "
                f"{inspection.row['source_path']}"
            )


def write_bytes_exclusive(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not write temporary file {path}: {exc}"
        ) from exc


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not open directory for durability sync {path}: {exc}"
        ) from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not durability-sync directory {path}: {exc}"
        ) from exc
    finally:
        os.close(descriptor)


def acquire_lock(
    lock_path: Path,
    run_id: str,
    run_token: str,
) -> LockOwnership:
    payload = (
        f"run_id\t{run_id}\n"
        f"pid\t{os.getpid()}\n"
        f"run_token\t{run_token}\n"
    ).encode("utf-8")
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise ArtifactIndexError(
            f"Artifact-index output is locked; inspect owner metadata: {lock_path}"
        ) from exc
    except OSError as exc:
        raise ArtifactIndexError(f"Could not acquire lock {lock_path}: {exc}") from exc
    stat_result = os.fstat(descriptor)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        try:
            lock_path.unlink()
        except OSError as cleanup_exc:
            raise ArtifactIndexError(
                "Could not write lock metadata and could not remove the "
                f"incomplete owned lock {lock_path}: {exc}; {cleanup_exc}"
            ) from exc
        raise ArtifactIndexError(f"Could not write lock metadata: {exc}") from exc
    return LockOwnership(
        device=stat_result.st_dev,
        inode=stat_result.st_ino,
        run_token=run_token,
    )


def release_owned_lock(
    lock_path: Path,
    ownership: LockOwnership,
) -> None:
    try:
        if lock_path.is_symlink():
            raise ArtifactIndexError(
                f"Owned lock was replaced by a symlink: {lock_path}"
            )
        with lock_path.open(encoding="utf-8") as stream:
            stat_result = os.fstat(stream.fileno())
            payload = stream.read()
    except FileNotFoundError as exc:
        raise ArtifactIndexError(
            f"Owned lock disappeared before cleanup: {lock_path}"
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise ArtifactIndexError(
            f"Could not verify owned lock before cleanup: {lock_path}: {exc}"
        ) from exc
    if (
        stat_result.st_dev != ownership.device
        or stat_result.st_ino != ownership.inode
        or f"run_token\t{ownership.run_token}\n" not in payload
    ):
        raise ArtifactIndexError(
            f"Owned lock identity changed before cleanup: {lock_path}"
        )
    try:
        lock_path.unlink()
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not remove verified owned lock {lock_path}: {exc}"
        ) from exc


def remove_owned(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def install_publication_signal_handlers() -> dict[int, Any]:
    previous: dict[int, Any] = {}

    def interrupt(signum: int, _frame: Any) -> None:
        try:
            signal_name = signal.Signals(signum).name
        except ValueError:
            signal_name = str(signum)
        raise ArtifactIndexError(
            f"Artifact-index publication interrupted by signal {signal_name}"
        )

    try:
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, interrupt)
    except BaseException as exc:
        try:
            restore_signal_handlers(previous)
        except BaseException as restore_exc:
            raise ArtifactIndexError(
                "Could not restore partially installed publication signal "
                f"handlers: {restore_exc}"
            ) from exc
        raise
    return previous


def restore_signal_handlers(previous: Mapping[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)


def publish_context(context: BuildContext) -> None:
    if context.output_dir.is_symlink():
        raise ArtifactIndexError(
            "Artifact-index output directory became a symlink after initial "
            f"validation: {context.output_dir}"
        )
    if context.output_dir.exists() and not context.output_dir.is_dir():
        raise ArtifactIndexError(
            f"Artifact-index output path is not a directory: {context.output_dir}"
        )
    context.output_dir.mkdir(parents=True, exist_ok=True)
    if context.output_dir.is_symlink() or not context.output_dir.is_dir():
        raise ArtifactIndexError(
            f"Artifact-index output directory is unsafe: {context.output_dir}"
        )
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_records = context.output_dir / f".artifact-index.{run_token}.tmp.records"
    temp_index = context.output_dir / f".artifact-index.{run_token}.tmp.tsv"
    temp_receipt = context.output_dir / f".artifact-receipt.{run_token}.tmp.tsv"
    backup_records = (
        context.output_dir / f".artifact-index.{run_token}.previous.records"
    )
    backup_index = (
        context.output_dir / f".artifact-index.{run_token}.previous.tsv"
    )
    backup_receipt = (
        context.output_dir / f".artifact-receipt.{run_token}.previous.tsv"
    )
    recovery_path = (
        context.output_dir / f".artifact-index.{run_token}.RECOVERY.txt"
    )
    owned_scratch = (
        temp_records,
        temp_index,
        temp_receipt,
        backup_records,
        backup_index,
        backup_receipt,
        recovery_path,
    )
    for path in owned_scratch:
        if path.exists() or path.is_symlink():
            raise ArtifactIndexError(
                f"Run-token scratch path already exists; refusing: {path}"
            )
    lock_ownership = acquire_lock(context.lock_path, context.run_id, run_token)
    try:
        previous_signal_handlers = install_publication_signal_handlers()
    except BaseException as exc:
        try:
            release_owned_lock(context.lock_path, lock_ownership)
        except ArtifactIndexError as cleanup_exc:
            raise ArtifactIndexError(
                "Could not install publication signal handlers and could "
                f"not release the owned lock: {exc}; {cleanup_exc}"
            ) from exc
        if isinstance(exc, ArtifactIndexError):
            raise
        raise ArtifactIndexError(
            f"Could not install publication signal handlers: {exc}"
        ) from exc
    had_previous = False
    backed_up_records = False
    backed_up_index = False
    backed_up_receipt = False
    published_records = False
    published_index = False
    published_receipt = False
    publication_committed = False
    rollback_failed = False
    try:
        existing = load_existing_receipt(
            context.receipt_path,
            context.artifacts_path,
            context.records_dir,
        )
        had_previous = existing is not None
        locked_previous_attempt_id, locked_attempt_history = (
            validate_existing_identity(
                existing,
                context.run_contract,
            )
        )
        if (
            existing != context.previous_receipt
            or
            locked_previous_attempt_id != context.previous_attempt_id
            or locked_attempt_history != context.attempt_history
        ):
            raise ArtifactIndexError(
                "Artifact-index predecessor changed after initial inspection; "
                "retry from a fresh dry-run/context"
            )
        if existing is not None:
            validate_existing_transaction(
                existing=existing,
                run_id=context.run_id,
                run_contract=context.run_contract,
                records_dir=context.records_dir,
                artifacts_path=context.artifacts_path,
                receipt_path=context.receipt_path,
            )

        temp_records.mkdir()
        for record, payload in zip(
            context.records, context.record_bytes, strict=True
        ):
            write_bytes_exclusive(
                temp_records / f"{record['artifact_id']}.json",
                payload,
            )
        fsync_directory(temp_records)
        write_bytes_exclusive(temp_index, context.index_bytes)
        # Receipt is intentionally staged last.
        write_bytes_exclusive(temp_receipt, context.receipt_bytes)
        recheck_inputs(context)

        if had_previous:
            os.replace(context.receipt_path, backup_receipt)
            backed_up_receipt = True
            os.replace(context.artifacts_path, backup_index)
            backed_up_index = True
            os.replace(context.records_dir, backup_records)
            backed_up_records = True
        os.replace(temp_records, context.records_dir)
        published_records = True
        os.replace(temp_index, context.artifacts_path)
        published_index = True
        os.replace(temp_receipt, context.receipt_path)
        published_receipt = True
        fsync_directory(context.output_dir)

        validate_published_transaction(
            run_id=context.run_id,
            run_contract=context.run_contract,
            run_contract_path=context.run_contract_path,
            run_contract_file_sha256=context.run_contract_file_sha256,
            inventory_path=context.inventory_path,
            inventory_sha256=context.inventory_sha256,
            inventory_rows=context.inventory_rows,
            records_dir=context.records_dir,
            artifacts_path=context.artifacts_path,
            receipt_path=context.receipt_path,
            require_current_source_locations=True,
        )
        recheck_inputs(context)
        publication_committed = True
    except Exception as exc:
        rollback_errors: list[str] = []

        def attempt_rollback(label: str, operation: Any) -> None:
            try:
                operation()
            except Exception as rollback_exc:  # pragma: no cover - fault injection
                rollback_errors.append(f"{label}: {rollback_exc}")

        if published_receipt:
            attempt_rollback(
                "remove new receipt",
                lambda: remove_owned(context.receipt_path),
            )
        if published_index:
            attempt_rollback(
                "remove new artifact index",
                lambda: remove_owned(context.artifacts_path),
            )
        if published_records:
            attempt_rollback(
                "remove new records directory",
                lambda: remove_owned(context.records_dir),
            )
        if had_previous:
            if backed_up_records:
                attempt_rollback(
                    "restore prior records directory",
                    lambda: os.replace(backup_records, context.records_dir),
                )
            if backed_up_index:
                attempt_rollback(
                    "restore prior artifact index",
                    lambda: os.replace(backup_index, context.artifacts_path),
                )
            if backed_up_receipt and not rollback_errors:
                # Restore the old receipt last.
                attempt_rollback(
                    "restore prior receipt",
                    lambda: os.replace(backup_receipt, context.receipt_path),
                )
            if not rollback_errors:
                validation_error_count = len(rollback_errors)
                attempt_rollback(
                    "validate restored prior transaction",
                    lambda: validate_existing_transaction(
                        existing=load_existing_receipt(
                            context.receipt_path,
                            context.artifacts_path,
                            context.records_dir,
                        )
                        or {},
                        run_id=context.run_id,
                        run_contract=context.run_contract,
                        records_dir=context.records_dir,
                        artifacts_path=context.artifacts_path,
                        receipt_path=context.receipt_path,
                    ),
                )
                if (
                    len(rollback_errors) > validation_error_count
                    and (
                        context.receipt_path.exists()
                        or context.receipt_path.is_symlink()
                    )
                ):
                    # A receipt is a complete-transaction marker. Quarantine
                    # it again if the restored records/index do not validate.
                    attempt_rollback(
                        "quarantine invalid restored receipt",
                        lambda: os.replace(
                            context.receipt_path,
                            backup_receipt,
                        ),
                    )
            if not rollback_errors:
                attempt_rollback(
                    "durability-sync restored transaction",
                    lambda: fsync_directory(context.output_dir),
                )
        else:
            for label, path in (
                ("new receipt", context.receipt_path),
                ("new artifact index", context.artifacts_path),
                ("new records directory", context.records_dir),
            ):
                if path.exists() or path.is_symlink():
                    rollback_errors.append(
                        f"{label} remains after first-publication rollback: {path}"
                    )
            if not rollback_errors:
                attempt_rollback(
                    "durability-sync first-publication rollback",
                    lambda: fsync_directory(context.output_dir),
                )
        if rollback_errors:
            rollback_failed = True
            try:
                recovery_path.write_text(
                    "Artifact-index rollback was incomplete.\n"
                    f"Original error: {exc}\n"
                    f"Rollback errors: {'; '.join(rollback_errors)}\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            raise ArtifactIndexError(
                f"{exc}\nArtifact-index rollback was incomplete; preserve "
                f"the lock and recovery paths under {context.output_dir}"
            ) from exc
        raise ArtifactIndexError(str(exc)) from exc
    finally:
        cleanup_errors: list[str] = []
        if not rollback_failed:
            cleanup_paths = [temp_records, temp_index, temp_receipt]
            if publication_committed:
                cleanup_paths.extend(
                    [backup_records, backup_index, backup_receipt]
                )
            for path in cleanup_paths:
                try:
                    remove_owned(path)
                except OSError as cleanup_exc:
                    cleanup_errors.append(f"{path}: {cleanup_exc}")
            if not cleanup_errors:
                try:
                    release_owned_lock(context.lock_path, lock_ownership)
                except ArtifactIndexError as cleanup_exc:
                    cleanup_errors.append(
                        str(cleanup_exc)
                    )
        active_error = sys.exc_info()[1]
        try:
            restore_signal_handlers(previous_signal_handlers)
        except (OSError, ValueError) as signal_exc:
            cleanup_errors.append(
                f"could not restore publication signal handlers: {signal_exc}"
            )
        if cleanup_errors:
            cleanup_state = (
                "publication is complete"
                if publication_committed
                else "rollback completed"
            )
            try:
                recovery_path.write_text(
                    f"Artifact-index {cleanup_state} but owned cleanup was "
                    "incomplete.\n"
                    f"Cleanup errors: {'; '.join(cleanup_errors)}\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            prefix = f"{active_error}\n" if active_error is not None else ""
            raise ArtifactIndexError(
                prefix
                + "Artifact-index cleanup failed; preserve the lock and "
                f"recovery paths under {context.output_dir}: "
                + "; ".join(cleanup_errors)
            ) from active_error


def parse_nonnegative_receipt_int(value: str, field_name: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ArtifactIndexError(
            f"Published receipt field {field_name} is not a non-negative integer"
        )
    return int(value)


def validate_published_transaction(
    *,
    run_id: str,
    run_contract: Mapping[str, Any],
    run_contract_path: Path,
    run_contract_file_sha256: str,
    inventory_path: Path,
    inventory_sha256: str,
    inventory_rows: Sequence[dict[str, str]],
    records_dir: Path,
    artifacts_path: Path,
    receipt_path: Path,
    require_current_source_locations: bool,
) -> None:
    for label, path in (
        ("receipt", receipt_path),
        ("artifact index", artifacts_path),
    ):
        if path.is_symlink() or not path.is_file():
            raise ArtifactIndexError(
                f"Published {label} is not a regular owned file: {path}"
            )
    if records_dir.is_symlink() or not records_dir.is_dir():
        raise ArtifactIndexError(
            f"Published records path is not a regular owned directory: {records_dir}"
        )

    receipt_rows = read_exact_tsv(
        receipt_path,
        ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )
    receipt = receipt_rows[0]
    if receipt["run_id"] != run_id:
        raise ArtifactIndexError("Published receipt run_id is invalid")
    for field_name in RUN_CONTRACT_FIELDS:
        if receipt[field_name] != str(run_contract[field_name]):
            raise ArtifactIndexError(
                f"Published receipt run contract field is invalid: {field_name}"
            )
    for field_name in ("run_contract_path", "inventory_path"):
        if not receipt[field_name] or not Path(receipt[field_name]).is_absolute():
            raise ArtifactIndexError(
                f"Published receipt {field_name} must be an absolute path"
            )
    if not SHA256_RE.fullmatch(receipt["run_contract_file_sha256"]):
        raise ArtifactIndexError(
            "Published receipt run-contract file hash is invalid"
        )
    if require_current_source_locations:
        if receipt["run_contract_path"] != str(run_contract_path):
            raise ArtifactIndexError(
                "Published receipt run-contract path is invalid"
            )
        if receipt["run_contract_file_sha256"] != run_contract_file_sha256:
            raise ArtifactIndexError(
                "Published receipt run-contract file hash is invalid"
            )
        if receipt["inventory_path"] != str(inventory_path):
            raise ArtifactIndexError(
                "Published receipt inventory path is invalid"
            )
    if receipt["inventory_sha256"] != inventory_sha256:
        raise ArtifactIndexError("Published receipt inventory hash is invalid")
    for field_name, expected in (
        ("artifact_schema_version", ARTIFACT_SCHEMA_VERSION),
        ("artifact_index_schema_version", ARTIFACT_INDEX_SCHEMA_VERSION),
        ("artifact_receipt_schema_version", ARTIFACT_RECEIPT_SCHEMA_VERSION),
        ("producer", PRODUCER),
        ("producer_version", PRODUCER_VERSION),
    ):
        if receipt[field_name] != expected:
            raise ArtifactIndexError(
                f"Published receipt field is invalid: {field_name}"
            )
    if receipt["transaction_state"] != "complete":
        raise ArtifactIndexError("Published receipt transaction is not complete")
    if not contracts.SAFE_ID_RE.fullmatch(receipt["adapter_attempt_id"]):
        raise ArtifactIndexError(
            "Published receipt adapter attempt ID is invalid"
        )
    attempt_history = [
        value
        for value in receipt["adapter_attempt_history"].split(",")
        if value
    ]
    if (
        not attempt_history
        or len(attempt_history) != len(set(attempt_history))
        or attempt_history[-1] != receipt["adapter_attempt_id"]
        or any(
            not contracts.SAFE_ID_RE.fullmatch(value)
            for value in attempt_history
        )
    ):
        raise ArtifactIndexError(
            "Published receipt adapter attempt history is invalid"
        )
    expected_superseded = (
        attempt_history[-2] if len(attempt_history) > 1 else ""
    )
    if receipt["supersedes_adapter_attempt_id"] != expected_superseded:
        raise ArtifactIndexError(
            "Published receipt superseded adapter attempt is invalid"
        )
    if not re.fullmatch(r"[0-9a-f]{40,64}", receipt["git_commit"]):
        raise ArtifactIndexError("Published receipt Git commit is invalid")
    try:
        started_at = datetime.fromisoformat(
            receipt["started_at"].replace("Z", "+00:00")
        )
        finished_at = datetime.fromisoformat(
            receipt["finished_at"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ArtifactIndexError(
            "Published receipt timestamps are invalid"
        ) from exc
    if (
        started_at.tzinfo is None
        or finished_at.tzinfo is None
        or finished_at < started_at
    ):
        raise ArtifactIndexError(
            "Published receipt timestamp ordering is invalid"
        )
    if receipt["artifacts_index_path"] != str(artifacts_path):
        raise ArtifactIndexError("Published receipt index path is invalid")
    if receipt["artifacts_index_sha256"] != contracts.sha256_file(
        artifacts_path
    ):
        raise ArtifactIndexError("Published artifact-index hash is invalid")

    index_rows = read_exact_tsv(artifacts_path, ARTIFACT_INDEX_HEADER)
    if [row["artifact_id"] for row in index_rows] != [
        row["artifact_id"] for row in inventory_rows
    ]:
        raise ArtifactIndexError(
            "Published artifact index does not match inventory order"
        )
    expected_names = {
        f"{inventory_row['artifact_id']}.json"
        for inventory_row in inventory_rows
    }
    try:
        observed_entries = list(records_dir.iterdir())
    except OSError as exc:
        raise ArtifactIndexError(
            f"Could not inspect owned records directory: {exc}"
        ) from exc
    observed_names = {path.name for path in observed_entries}
    if observed_names != expected_names:
        raise ArtifactIndexError(
            "Published records directory has missing or unexpected files"
        )
    unsafe_entries = [
        path
        for path in observed_entries
        if path.is_symlink() or not path.is_file()
    ]
    if unsafe_entries:
        raise ArtifactIndexError(
            "Published records directory contains a non-regular owned entry: "
            + ", ".join(str(path) for path in unsafe_entries)
        )

    schemas, registry = contracts.load_schema_registry()
    validator = Draft202012Validator(
        schemas["artifact-record"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    record_manifest: list[dict[str, str]] = []
    validated_index_rows: list[dict[str, str]] = []
    for index_row, inventory_row in zip(
        index_rows, inventory_rows, strict=True
    ):
        expected_path = records_dir / f"{inventory_row['artifact_id']}.json"
        if index_row["record_path"] != str(expected_path):
            raise ArtifactIndexError(
                f"Published record path is invalid: {index_row['record_path']}"
            )
        observed_hash = contracts.sha256_file(expected_path)
        if index_row["record_sha256"] != observed_hash:
            raise ArtifactIndexError(
                f"Published record hash is invalid: {expected_path}"
            )
        try:
            payload = expected_path.read_bytes()
        except OSError as exc:
            raise ArtifactIndexError(
                f"Could not read published artifact record {expected_path}: {exc}"
            ) from exc
        record = contracts.load_json_object(
            expected_path,
            f"artifact record {inventory_row['artifact_id']}",
        )
        validate_record_in_memory(record, inventory_row, validator)
        if record["run_id"] != run_id or record["run_contract"] != run_contract:
            raise ArtifactIndexError(
                f"Published record has the wrong run identity: {expected_path}"
            )
        expected_index_row = build_index_rows(
            records=[record],
            record_bytes=[payload],
            records_dir=records_dir,
        )[0]
        if index_row != expected_index_row:
            raise ArtifactIndexError(
                "Published artifact-index row disagrees with its JSON record: "
                f"{inventory_row['artifact_id']}"
            )
        validated_index_rows.append(expected_index_row)
        record_manifest.append(
            {
                "artifact_id": inventory_row["artifact_id"],
                "record_path": str(expected_path),
                "record_sha256": observed_hash,
            }
        )
    if receipt["record_set_sha256"] != canonical_digest(record_manifest):
        raise ArtifactIndexError("Published record-set hash is invalid")

    availability = Counter(
        row["availability_status"] for row in validated_index_rows
    )
    completion = Counter(
        row["completion_status"] for row in validated_index_rows
    )
    required_count = sum(
        row["required"] == "true" for row in validated_index_rows
    )
    required_missing = sum(
        row["required"] == "true"
        and row["availability_status"] != "present"
        for row in validated_index_rows
    )
    expected_counts = {
        "inventory_row_count": len(inventory_rows),
        "artifact_record_count": len(validated_index_rows),
        "required_artifact_count": required_count,
        "required_missing_artifact_count": required_missing,
        "present_artifact_count": availability["present"],
        "missing_artifact_count": availability["missing"],
        "externally_unavailable_artifact_count": availability[
            "externally_unavailable"
        ],
        "unknown_artifact_count": availability["unknown"],
        "complete_artifact_count": completion["complete"],
        "not_attempted_artifact_count": completion["not_attempted"],
        "in_progress_artifact_count": completion["in_progress"],
        "incomplete_artifact_count": completion["incomplete"],
        "failed_artifact_count": completion["failed"],
        "warning_count": sum(
            int(row["warning_count"]) for row in validated_index_rows
        ),
        "error_count": sum(
            int(row["error_count"]) for row in validated_index_rows
        ),
        "published_output_count": len(validated_index_rows) + 2,
    }
    for field_name, expected in expected_counts.items():
        observed = parse_nonnegative_receipt_int(
            receipt[field_name],
            field_name,
        )
        if observed != expected:
            raise ArtifactIndexError(
                f"Published receipt rollup is invalid: {field_name}"
            )


def print_context(context: BuildContext, execute: bool) -> None:
    availability = Counter(
        inspection.availability_status for inspection in context.inspections
    )
    completion = Counter(
        inspection.completion_status for inspection in context.inspections
    )
    print("NORAD artifact-index context")
    print(f"  Mode: {'execute' if execute else 'dry-run'}")
    print(f"  Run ID: {context.run_id}")
    print(
        "  Run contract SHA-256: "
        f"{context.run_contract['run_contract_sha256']}"
    )
    print(f"  Run contract: {context.run_contract_path}")
    print(f"  Inventory: {context.inventory_path}")
    print(f"  Inventory artifacts: {len(context.inventory_rows)}")
    print(f"  Output directory: {context.output_dir}")
    print(f"  Records directory: {context.records_dir}")
    print(f"  Artifact index: {context.artifacts_path}")
    print(f"  Receipt (published last): {context.receipt_path}")
    print(f"  Adapter attempt ID: {context.attempt_id}")
    print(
        "  Availability: "
        + ", ".join(
            f"{status}={availability[status]}"
            for status in (
                "present",
                "missing",
                "externally_unavailable",
                "unknown",
            )
        )
    )
    print(
        "  Completion: "
        + ", ".join(
            f"{status}={completion[status]}"
            for status in (
                "complete",
                "not_attempted",
                "in_progress",
                "incomplete",
                "failed",
            )
        )
    )
    for inspection in context.inspections:
        print(
            "  Artifact: "
            f"{inspection.row['artifact_id']} "
            f"availability={inspection.availability_status} "
            f"completion={inspection.completion_status} "
            f"source={inspection.row['source_path']}"
        )
    if not execute:
        print(
            "Dry-run only. Add --execute to publish the artifact-index "
            "transaction."
        )


def main() -> int:
    arguments = parse_args()
    try:
        context = prepare_context(arguments)
        print_context(context, arguments.execute)
        if arguments.execute:
            publish_context(context)
            print(f"Published artifact index: {context.artifacts_path}")
            print(f"Published receipt last: {context.receipt_path}")
    except (
        ArtifactIndexError,
        contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
