"""Independent ordered expectations for live validation-report check rosters."""

from collections.abc import Mapping, Sequence


EXPECTED_CHECK_ROSTERS: dict[str, tuple[str, ...]] = {
    "00a": (
        "index_members",
        "fasta_identity",
        "gtf_identity",
        "contig_names_lengths",
        "sjdb_overhang",
    ),
    "00b": (
        "bed12_structure",
        "coordinate_sorting",
        "block_structure",
        "unique_transcript_names",
        "gtf_transcript_agreement",
    ),
    "00c": (
        "fasta_structure",
        "fai_structure",
        "dict_structure",
        "fai_contig_agreement",
        "dict_contig_agreement",
    ),
    "01": (
        "output_files",
        "bam_structure",
        "final_log_structure",
        "mapping_summary",
        "splice_junction_structure",
    ),
    "02": (
        "bam_bai_structure",
        "samtools_quickcheck",
        "coordinate_sorting",
        "read_group_header",
        "alignment_rg_tags",
    ),
    "02b": (
        "quickcheck_structure",
        "flagstat_structure",
        "total_records",
        "mapped_records",
        "count_consistency",
    ),
    "03": (
        "report_structure",
        "failed_fraction",
        "paired_orientation_fraction_a",
        "paired_orientation_fraction_b",
        "fraction_sum",
    ),
    "04": (
        "bam_bai_structure",
        "samtools_quickcheck",
        "coordinate_sorting",
        "read_group_preservation",
        "duplication_metrics",
    ),
    "05": (
        "bam_bai_structure",
        "samtools_quickcheck",
        "coordinate_sorting",
        "read_group_preservation",
        "reference_sidecars",
    ),
    "06": (
        "output_containers",
        "counts_structure",
        "fwd_count_arithmetic",
        "rev_count_arithmetic",
        "assigned_count_arithmetic",
    ),
    "07": (
        "receipt_structure",
        "vcf_structure",
        "selector_reconciliation",
        "manifest_identity_and_sample_order",
        "vcf_record_counts",
    ),
    "08": (
        "output_transaction",
        "manifest_annotation_identity",
        "input_receipt_reconciliation",
        "sites_order_uniqueness",
        "summary_count_reconciliation",
    ),
    "09": (
        "output_transaction",
        "upstream_identity_and_candidate_order",
        "status_semantics",
        "significant_subset",
        "summary_count_reconciliation",
        "mutation_spectrum_reconciliation",
        "pdf_structure",
    ),
}


def assert_exact_check_roster(
    rows: Sequence[Mapping[str, str]],
    step_id: str,
) -> None:
    """Assert literal check identity and order without producer constants."""

    expected = EXPECTED_CHECK_ROSTERS[step_id]
    actual = tuple(row["check_id"] for row in rows)
    assert actual == expected, (
        f"Step {step_id} validation check roster mismatch: "
        f"expected={expected!r}, actual={actual!r}"
    )
