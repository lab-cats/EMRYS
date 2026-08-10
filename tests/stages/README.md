# Transformation-stage tests

This directory mirrors the ten computational stage owners.

- Reference building:
  [`star_index/`](star_index/README.md),
  [`gtf_to_bed12/`](gtf_to_bed12/README.md), and
  [`fasta_sidecars/`](fasta_sidecars/README.md).
- Sample processing:
  [`star_alignment/`](star_alignment/README.md),
  [`canonical_bam/`](canonical_bam/README.md),
  [`duplicate_marking/`](duplicate_marking/README.md),
  [`split_n_cigar/`](split_n_cigar/README.md),
  and
  [`mechanical_orientation/`](mechanical_orientation/README.md).
- Cohort processing:
  [`partitioned_cohort_mpileup/`](partitioned_cohort_mpileup/README.md)
  and
  [`cohort_candidate_preprocessing/`](cohort_candidate_preprocessing/README.md).

The [stage-owner router](../../src/norad/stages/README.md) owns exact identities,
commands, transactions, recovery, and cross-stage placement. Protection here
is predominantly local fixture or fake-tool evidence, with guarded real-R
evidence only where explicitly stated; it is not cluster or production proof.
