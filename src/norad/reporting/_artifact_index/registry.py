"""Declarative artifact-adapter registry."""

from __future__ import annotations

from typing import Sequence

from .contracts import review_package, step08, step09
from .models import (
    AdapterSpec,
    STEP00A_BASENAMES,
    STEP06_COUNTS_HEADER,
    STEP07_RECEIPT_HEADER,
    VALIDATION_REPORT_HEADER,
)

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
        expected_header=step08.STEP08_METADATA_HEADER,
    )
    add_spec(
        registry,
        "step08_inputs_v1",
        "08",
        "cohort",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".step08_inputs.tsv",),
        expected_header=step08.STEP08_INPUTS_HEADER,
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
        expected_header=step08.STEP08_SUMMARY_HEADER,
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
            expected_header=step09.STEP09_RESULT_HEADER,
        )
    add_spec(
        registry,
        "step09_cmh_summary_v1",
        "09",
        "analysis",
        "tsv",
        "text/tab-separated-values",
        suffixes=(".cmh_summary.tsv",),
        expected_header=step09.STEP09_SUMMARY_HEADER,
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
        expected_header=step09.STEP09_MUTATION_HEADER,
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
            review_package.REVIEW_PLAN_HEADER,
            1,
        ),
        (
            "step09c_evidence_index_v1",
            ".step09c_evidence_index.tsv",
            review_package.EVIDENCE_INDEX_HEADER,
            None,
        ),
        (
            "step09c_orientation_locus_audit_v1",
            ".step09c_orientation_locus_audit.tsv",
            review_package.ORIENTATION_HEADER,
            None,
        ),
        (
            "step09c_annotation_audit_v1",
            ".step09c_annotation_audit.tsv",
            review_package.ANNOTATION_HEADER,
            None,
        ),
        (
            "step09c_qc_funnel_v1",
            ".step09c_qc_funnel.tsv",
            review_package.QC_FUNNEL_HEADER,
            None,
        ),
        (
            "step09c_replicate_effects_v1",
            ".step09c_replicate_effects.tsv",
            review_package.REPLICATE_EFFECTS_HEADER,
            None,
        ),
        (
            "step09c_sensitivity_matrix_v1",
            ".step09c_sensitivity_matrix.tsv",
            review_package.SENSITIVITY_HEADER,
            None,
        ),
        (
            "step09c_leave_one_pair_out_v1",
            ".step09c_leave_one_pair_out.tsv",
            review_package.LEAVE_ONE_OUT_HEADER,
            None,
        ),
        (
            "step09c_candidate_selection_v1",
            ".step09c_candidate_selection.tsv",
            review_package.CANDIDATE_SELECTION_HEADER,
            None,
        ),
        (
            "step09c_candidate_adjudication_v1",
            ".step09c_candidate_adjudication.tsv",
            review_package.CANDIDATE_ADJUDICATION_HEADER,
            None,
        ),
        (
            "step09c_decisions_v1",
            ".step09c_decisions.tsv",
            review_package.DECISIONS_HEADER,
            None,
        ),
        (
            "step09c_limitations_v1",
            ".step09c_limitations.tsv",
            review_package.LIMITATIONS_HEADER,
            None,
        ),
        (
            "step09c_review_summary_v1",
            ".step09c_review_summary.tsv",
            review_package.REVIEW_SUMMARY_HEADER,
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
