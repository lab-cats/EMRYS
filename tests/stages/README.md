# Transformation-stage tests

This directory mirrors the ten computational stage owners.

- Reference building:
  [`construct_STAR_index/`](construct_STAR_index/README.md),
  [`convert_GTF_to_BED12/`](convert_GTF_to_BED12/README.md), and
  [`construct_FASTA_sidecars/`](construct_FASTA_sidecars/README.md).
- Sample processing:
  [`align_RNA_reads_with_STAR/`](align_RNA_reads_with_STAR/README.md),
  [`construct_canonical_BAM/`](construct_canonical_BAM/README.md),
  [`mark_BAM_duplicates_with_Picard/`](mark_BAM_duplicates_with_Picard/README.md),
  [`split_N_cigar_reads_with_GATK/`](split_N_cigar_reads_with_GATK/README.md),
  and
  [`partition_BAM_by_mechanical_read_orientation/`](partition_BAM_by_mechanical_read_orientation/README.md).
- Cohort processing:
  [`generate_partitioned_cohort_mpileup_VCFs/`](generate_partitioned_cohort_mpileup_VCFs/README.md)
  and
  [`preprocess_and_annotate_cohort_candidates/`](preprocess_and_annotate_cohort_candidates/README.md).

The [stage-owner router](../../src/norad/stages/README.md) owns exact identities,
commands, transactions, recovery, and cross-stage placement. Protection here
is predominantly local fixture or fake-tool evidence, with guarded real-R
evidence only where explicitly stated; it is not cluster or production proof.
