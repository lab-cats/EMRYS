"""Declarative artifact-adapter registry."""

from __future__ import annotations

from collections.abc import Sequence

from norad.libraries.alignments import orientation as alignment_orientation

from .contracts import review_package, step08, step09
from .models import (
    STEP00A_BASENAMES,
    STEP06_COUNTS_HEADER,
    STEP07_RECEIPT_HEADER,
    VALIDATION_REPORT_HEADER,
    AdapterSpec,
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


def add_validation_report(
    registry: dict[str, AdapterSpec],
    step_id: str,
    scope_type: str,
    *,
    exact_data_rows: int = 5,
) -> None:
    """Register the uniform validation-report contract for one pipeline step."""
    add_spec(
        registry,
        f"step{step_id}_validation_report_v1",
        step_id,
        scope_type,
        "validation_report",
        "text/tab-separated-values",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=exact_data_rows,
        allow_header_only=False,
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
    add_validation_report(registry, "00a", "reference")
    add_spec(
        registry,
        "step00b_bed12_v1",
        "00b",
        "reference",
        "bed12",
        "text/bed",
        suffixes=(".bed",),
    )
    add_validation_report(registry, "00b", "reference")
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
    add_validation_report(registry, "00c", "reference")
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
    add_validation_report(registry, "01", "sample")
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
    add_validation_report(registry, "02", "sample")
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
    add_validation_report(registry, "02b", "sample")
    add_spec(
        registry,
        "step03_rseqc_infer_v1",
        "03",
        "sample",
        "rseqc",
        "text/plain",
        suffixes=(".infer_experiment.txt",),
    )
    add_validation_report(registry, "03", "sample")
    add_spec(
        registry,
        "step04_markdup_metrics_v1",
        "04",
        "sample",
        "picard_metrics",
        "text/plain",
        suffixes=(".markdup.metrics.txt",),
    )
    add_validation_report(registry, "04", "sample")
    add_validation_report(registry, "05", "sample")
    add_validation_report(registry, "06", "sample")
    for orientation, adapter_prefix in zip(
        alignment_orientation.ORIENTATIONS,
        alignment_orientation.ORIENTATION_PREFIXES,
    ):
        add_spec(
            registry,
            f"step06_{adapter_prefix}_bam_v1",
            "06",
            "sample",
            "bam",
            "application/x-bam",
            suffixes=(f".{orientation}.bam",),
        )
        add_spec(
            registry,
            f"step06_{adapter_prefix}_bai_v1",
            "06",
            "sample",
            "bai",
            "application/octet-stream",
            suffixes=(f".{orientation}.bam.bai",),
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
    add_validation_report(registry, "07", "cohort_partition")
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
    add_validation_report(registry, "08", "cohort")
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
    add_validation_report(registry, "09", "analysis", exact_data_rows=7)
    for key, suffix in review_package.OUTPUT_SUFFIXES:
        exact_rows = 1 if key in review_package.SINGLE_ROW_OUTPUTS else None
        add_spec(
            registry,
            f"step09c_{key}_v1",
            "09c",
            "scientific_review",
            "tsv",
            "text/tab-separated-values",
            suffixes=(f".{suffix}",),
            expected_header=review_package.OUTPUT_HEADERS[key],
            exact_data_rows=exact_rows,
            allow_header_only=exact_rows is None,
        )
    return registry


ADAPTER_REGISTRY = build_adapter_registry()
