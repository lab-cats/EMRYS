"""Exact adapter rosters and producer ownership."""

from __future__ import annotations

from collections import Counter

from emrys.libraries.alignments import orientation as alignment_orientation


def roster(*entries: str | tuple[str, int]) -> Counter[str]:
    """Keep this independent oracle explicit while omitting Counter scaffolding."""
    return Counter(
        dict(entry if isinstance(entry, tuple) else (entry, 1) for entry in entries)
    )


SCOPE_ADAPTER_ROSTERS: dict[str, Counter[str]] = {
    "00a": roster(
        ("step00a_star_index_v1", 15),
        "step00a_validation_report_v1",
    ),
    "00b": roster("step00b_bed12_v1", "step00b_validation_report_v1"),
    "00c": roster(
        "step00c_reference_fasta_v1",
        "step00c_reference_fai_v1",
        "step00c_reference_dict_v1",
        "step00c_validation_report_v1",
    ),
    "01": roster(
        "step01_star_bam_v1",
        "step01_star_log_final_v1",
        "step01_star_log_v1",
        "step01_star_log_progress_v1",
        "step01_star_sj_v1",
        "step01_validation_report_v1",
    ),
    "02": roster(
        "step02_canonical_bam_v1",
        "step02_canonical_bai_v1",
        "step02_validation_report_v1",
    ),
    "02b": roster(
        "step02b_quickcheck_v1",
        "step02b_flagstat_v1",
        "step02b_validation_report_v1",
    ),
    "03": roster("step03_rseqc_infer_v1", "step03_validation_report_v1"),
    "04": roster(
        "step04_markdup_bam_v1",
        "step04_markdup_bai_v1",
        "step04_markdup_metrics_v1",
        "step04_validation_report_v1",
    ),
    "05": roster(
        "step05_split_bam_v1",
        "step05_split_bai_v1",
        "step05_validation_report_v1",
    ),
    "06": roster(
        "step06_orientation_counts_v1",
        "step06_validation_report_v1",
        *(
            f"step06_{prefix}_bam_v1"
            for prefix in alignment_orientation.ORIENTATION_PREFIXES
        ),
        *(
            f"step06_{prefix}_bai_v1"
            for prefix in alignment_orientation.ORIENTATION_PREFIXES
        ),
    ),
    "07": roster(
        ("step07_mpileup_vcf_v1", 2),
        "step07_mpileup_receipt_v1",
        "step07_validation_report_v1",
    ),
    "08": roster(
        "step08_sites_v1",
        "step08_inputs_v1",
        "step08_summary_v1",
        "step08_validation_report_v1",
    ),
    "09": roster(
        "step09_cmh_all_sites_v1",
        "step09_cmh_significant_sites_v1",
        "step09_cmh_summary_v1",
        "step09_mutation_spectrum_tsv_v1",
        "step09_mutation_spectrum_pdf_v1",
        "step09_depth_delta_pdf_v1",
        "step09_validation_report_v1",
    ),
    "10": roster(
        "step10_candidate_context_v1",
        "step10_motif_hits_v1",
        "step10_sequence_logo_v1",
        "step10_motif_statistics_v1",
        "step10_context_receipt_v1",
        "step10_validation_report_v1",
    ),
}

STEP_PRODUCERS = {
    "00a": "src/emrys/stages/star_index/step_00a_build_star_index.sh",
    "00b": "src/emrys/stages/gtf_to_bed12/converter.py",
    "00c": ("src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh"),
    "01": ("src/emrys/stages/star_alignment/step_01_star_align.sh"),
    "02": ("src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"),
    "02b": "src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh",
    "03": (
        "src/emrys/evidence/rseqc_orientation/"
        "step_03_infer_strandedness_and_orientation.sh"
    ),
    "04": "src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh",
    "05": ("src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"),
    "06": (
        "src/emrys/stages/mechanical_orientation/"
        "step_06_split_bam_by_read_orientation.sh"
    ),
    "07": (
        "src/emrys/stages/partitioned_cohort_mpileup/"
        "producer.py"
    ),
    "08": (
        "src/emrys/stages/cohort_candidate_preprocessing/producer.py"
    ),
    "09": ("src/emrys/analyses/paired_cmh_candidate_ranking/producer.py"),
    "10": (
        "src/emrys/analyses/scientific_context_projection/"
        "scientific_context_projection.sh"
    ),
}
