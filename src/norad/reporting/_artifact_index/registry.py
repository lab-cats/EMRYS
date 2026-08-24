"""Declarative artifact-adapter registry."""

from __future__ import annotations

from collections.abc import Sequence
from functools import partial

from norad.contracts.scientific_evidence import scientific_context, step08, step09
from norad.libraries.alignments import orientation as alignment_orientation

from .models import (
    STEP00A_BASENAMES,
    STEP06_COUNTS_HEADER,
    STEP07_RECEIPT_HEADER,
    VALIDATION_REPORT_HEADER,
    AdapterSpec,
)

MEDIA_TYPE_BY_KIND = {
    "bai": "application/octet-stream",
    "bam": "application/x-bam",
    "bed12": "text/bed",
    "dict": "text/vnd.sam",
    "fai": "text/tab-separated-values",
    "fasta": "text/x-fasta",
    "flagstat": "text/plain",
    "pdf": "application/pdf",
    "picard_metrics": "text/plain",
    "quickcheck": "text/plain",
    "rseqc": "text/plain",
    "sample_blocks_tsv": "text/tab-separated-values",
    "star_index": "application/octet-stream",
    "star_log_final": "text/plain",
    "star_sj": "text/plain",
    "text": "text/plain",
    "tsv": "text/tab-separated-values",
    "validation_report": "text/tab-separated-values",
    "vcf": "text/vcf",
}


def add_spec(
    registry: dict[str, AdapterSpec],
    scope_type: str,
    adapter_id: str,
    step_id: str,
    kind: str,
    *,
    suffixes: Sequence[str] = (),
    basenames: Sequence[str] = (),
    expected_header: Sequence[str] | None = None,
    exact_data_rows: int | None = None,
    allow_header_only: bool = True,
) -> None:
    """Register one adapter, deriving its media type from inspection kind."""
    registry[adapter_id] = AdapterSpec(
        adapter_id=adapter_id,
        step_id=step_id,
        scope_type=scope_type,
        kind=kind,
        media_type=MEDIA_TYPE_BY_KIND[kind],
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
        scope_type,
        f"step{step_id}_validation_report_v1",
        step_id,
        "validation_report",
        suffixes=(".validation.tsv",),
        expected_header=VALIDATION_REPORT_HEADER,
        exact_data_rows=exact_data_rows,
        allow_header_only=False,
    )


def build_adapter_registry() -> dict[str, AdapterSpec]:
    registry: dict[str, AdapterSpec] = {}
    add_reference = partial(add_spec, registry, "reference")
    add_sample = partial(add_spec, registry, "sample")
    add_partition = partial(add_spec, registry, "cohort_partition")
    add_cohort = partial(add_spec, registry, "cohort")
    add_analysis = partial(add_spec, registry, "analysis")
    add_reference(
        "step00a_star_index_v1",
        "00a",
        "star_index",
        basenames=STEP00A_BASENAMES,
    )
    add_validation_report(registry, "00a", "reference", exact_data_rows=6)
    add_reference(
        "step00b_bed12_v1",
        "00b",
        "bed12",
        suffixes=(".bed",),
    )
    add_validation_report(registry, "00b", "reference")
    add_reference(
        "step00c_reference_fasta_v1",
        "00c",
        "fasta",
        suffixes=(".fa", ".fasta"),
    )
    add_reference(
        "step00c_reference_fai_v1",
        "00c",
        "fai",
        suffixes=(".fai",),
    )
    add_reference(
        "step00c_reference_dict_v1",
        "00c",
        "dict",
        suffixes=(".dict",),
    )
    add_validation_report(registry, "00c", "reference")
    add_sample(
        "step01_star_bam_v1",
        "01",
        "bam",
        suffixes=(".bam",),
    )
    for adapter_id, suffix, kind in (
        ("step01_star_log_final_v1", ".Log.final.out", "star_log_final"),
        ("step01_star_log_v1", ".Log.out", "text"),
        ("step01_star_log_progress_v1", ".Log.progress.out", "text"),
        ("step01_star_sj_v1", ".SJ.out.tab", "star_sj"),
    ):
        add_sample(
            adapter_id,
            "01",
            kind,
            suffixes=(suffix,),
        )
    add_validation_report(registry, "01", "sample")
    for step_id, bam_adapter, bai_adapter, bam_suffix in (
        ("02", "step02_canonical_bam_v1", "step02_canonical_bai_v1", ".sorted.bam"),
        ("04", "step04_markdup_bam_v1", "step04_markdup_bai_v1", ".markdup.bam"),
        ("05", "step05_split_bam_v1", "step05_split_bai_v1", ".split_ncigar.bam"),
    ):
        add_sample(
            bam_adapter,
            step_id,
            "bam",
            suffixes=(bam_suffix,),
        )
        add_sample(
            bai_adapter,
            step_id,
            "bai",
            suffixes=(f"{bam_suffix}.bai",),
        )
    add_validation_report(registry, "02", "sample")
    add_sample(
        "step02b_quickcheck_v1",
        "02b",
        "quickcheck",
        suffixes=(".quickcheck.txt",),
    )
    add_sample(
        "step02b_flagstat_v1",
        "02b",
        "flagstat",
        suffixes=(".flagstat.txt",),
    )
    add_validation_report(registry, "02b", "sample")
    add_sample(
        "step03_rseqc_infer_v1",
        "03",
        "rseqc",
        suffixes=(".infer_experiment.txt",),
    )
    add_validation_report(registry, "03", "sample")
    add_sample(
        "step04_markdup_metrics_v1",
        "04",
        "picard_metrics",
        suffixes=(".markdup.metrics.txt",),
    )
    add_validation_report(registry, "04", "sample")
    add_validation_report(registry, "05", "sample")
    add_validation_report(registry, "06", "sample")
    for orientation, adapter_prefix in zip(
        alignment_orientation.ORIENTATIONS,
        alignment_orientation.ORIENTATION_PREFIXES,
    ):
        add_sample(
            f"step06_{adapter_prefix}_bam_v1",
            "06",
            "bam",
            suffixes=(f".{orientation}.bam",),
        )
        add_sample(
            f"step06_{adapter_prefix}_bai_v1",
            "06",
            "bai",
            suffixes=(f".{orientation}.bam.bai",),
        )
    add_sample(
        "step06_orientation_counts_v1",
        "06",
        "tsv",
        suffixes=(".orientation_counts.tsv",),
        expected_header=STEP06_COUNTS_HEADER,
        exact_data_rows=1,
        allow_header_only=False,
    )
    add_partition(
        "step07_mpileup_vcf_v1",
        "07",
        "vcf",
        suffixes=(".mpileup.vcf",),
    )
    add_partition(
        "step07_mpileup_receipt_v1",
        "07",
        "tsv",
        suffixes=(".step07_outputs.tsv",),
        expected_header=STEP07_RECEIPT_HEADER,
        exact_data_rows=2,
        allow_header_only=False,
    )
    add_validation_report(registry, "07", "cohort_partition")
    add_cohort(
        "step08_sites_v1",
        "08",
        "sample_blocks_tsv",
        suffixes=(".step08_sites.tsv",),
        expected_header=step08.STEP08_METADATA_HEADER,
    )
    add_cohort(
        "step08_inputs_v1",
        "08",
        "tsv",
        suffixes=(".step08_inputs.tsv",),
        expected_header=step08.STEP08_INPUTS_HEADER,
        allow_header_only=False,
    )
    add_cohort(
        "step08_summary_v1",
        "08",
        "tsv",
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
        add_analysis(
            adapter_id,
            "09",
            "sample_blocks_tsv",
            suffixes=(suffix,),
            expected_header=step09.STEP09_RESULT_HEADER,
        )
    add_analysis(
        "step09_cmh_summary_v1",
        "09",
        "tsv",
        suffixes=(".cmh_summary.tsv",),
        expected_header=step09.STEP09_SUMMARY_HEADER,
        exact_data_rows=1,
        allow_header_only=False,
    )
    add_analysis(
        "step09_mutation_spectrum_tsv_v1",
        "09",
        "tsv",
        suffixes=(".mutation_spectrum.tsv",),
        expected_header=step09.STEP09_MUTATION_HEADER,
    )
    for adapter_id, suffix in (
        ("step09_mutation_spectrum_pdf_v1", ".mutation_spectrum.pdf"),
        ("step09_depth_delta_pdf_v1", ".depth_delta.pdf"),
    ):
        add_analysis(
            adapter_id,
            "09",
            "pdf",
            suffixes=(suffix,),
        )
    add_validation_report(registry, "09", "analysis", exact_data_rows=7)
    for adapter_id, suffix, header in (
        (
            "step10_candidate_context_v1",
            ".candidate_context.tsv",
            scientific_context.CANDIDATE_CONTEXT_HEADER,
        ),
        (
            "step10_motif_hits_v1",
            ".motif_hits.tsv",
            scientific_context.MOTIF_HITS_HEADER,
        ),
        (
            "step10_sequence_logo_v1",
            ".sequence_logo.tsv",
            scientific_context.SEQUENCE_LOGO_HEADER,
        ),
        (
            "step10_motif_statistics_v1",
            ".motif_statistics.tsv",
            scientific_context.MOTIF_STATISTICS_HEADER,
        ),
    ):
        add_analysis(
            adapter_id,
            "10",
            "tsv",
            suffixes=(suffix,),
            expected_header=header,
        )
    add_analysis(
        "step10_context_receipt_v1",
        "10",
        "tsv",
        suffixes=(".context_receipt.tsv",),
        expected_header=scientific_context.SCIENTIFIC_CONTEXT_RECEIPT_HEADER,
        exact_data_rows=1,
        allow_header_only=False,
    )
    add_validation_report(registry, "10", "analysis", exact_data_rows=1)
    return registry


ADAPTER_REGISTRY = build_adapter_registry()
