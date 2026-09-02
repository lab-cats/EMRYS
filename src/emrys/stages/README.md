# Transformation-stage owners

| Step | Owner |
| --- | --- |
| `00a` | [`construct_STAR_index`](star_index/README.md) |
| `00b` | [`convert_GTF_to_BED12`](gtf_to_bed12/README.md) |
| `00c` | [`construct_FASTA_sidecars`](fasta_sidecars/README.md) |
| `01` | [`align_RNA_reads_with_STAR`](star_alignment/README.md) |
| `02` | [`construct_canonical_BAM`](canonical_bam/README.md) |
| `04` | [`mark_BAM_duplicates_with_Picard`](duplicate_marking/README.md) |
| `05` | [`split_N_cigar_reads_with_GATK`](split_n_cigar/README.md) |
| `06` | [`partition_BAM_by_mechanical_read_orientation`](mechanical_orientation/README.md) |
| `07` | [`generate_partitioned_cohort_mpileup_VCFs`](partitioned_cohort_mpileup/README.md) |
| `08` | [`preprocess_and_annotate_cohort_candidates`](cohort_candidate_preprocessing/README.md) |

[`STAGE_MAP.md`](../contracts/STAGE_MAP.md) owns semantic identities and edges;
adjacent `CONTRACT.md` files own exact behavior. Evidence operations `02b` and
`03` live under [`evidence/`](../evidence/README.md), and downstream analyses
under [`analyses/`](../analyses/README.md). Slurm placement and whole-Run
lifecycle belong to the run coordinator rather than owner-local wrappers.
