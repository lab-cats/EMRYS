# Transformation-stage tests

These tests mirror the ten computational stage owners:

- Reference preparation: [STAR index](star_index/README.md),
  [GTF to BED12](gtf_to_bed12/README.md), and [FASTA sidecars](fasta_sidecars/README.md).
- Sample processing: [STAR alignment](star_alignment/README.md),
  [canonical BAM](canonical_bam/README.md), [duplicate marking](duplicate_marking/README.md),
  [split N-cigar](split_n_cigar/README.md), and [mechanical orientation](mechanical_orientation/README.md).
- Cohort processing: [mpileup](partitioned_cohort_mpileup/README.md) and
  [candidate preprocessing](cohort_candidate_preprocessing/README.md).

The [stage index](../../src/emrys/stages/README.md) leads to each producer's
commands, contract, and recovery instructions. Most cases use local fixtures
or fake tools; real-R evidence is identified explicitly. The common
[test evidence limits](../README.md#evidence-limits) apply to every stage suite.
