# Transformation-stage owners

These stages prepare references and reads for downstream analysis. Each guide
explains what its stage consumes and produces; its adjacent contract defines
exact validation, publication, and recovery behavior.

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

Step numbers are historical identifiers, not instructions to run every stage
in numeric order. Explicit inputs determine readiness; for example, STAR index,
BED12, and FASTA-sidecar construction can branch from the same existing
references. The [stage map](../contracts/STAGE_MAP.md) owns those identities and
dependencies. Evidence operations `02b` and `03` live under
[`evidence/`](../evidence/README.md); downstream methods live under
[`analyses/`](../analyses/README.md).

## Running a stage

For normal processing, use `emrys run` and the supported `resume` route in the
[Runbook](../../../docs/operations/RUNBOOK.md#project-and-run-operations).
The Run coordinator prepares the declared inputs, runtime, and task commands.
It also owns Slurm submission and recovery; stages do not need separate
scheduler wrappers.

Scientific producers are internal workers. The Run supplies their working
paths and runtime; Bash and Python worker tool arguments require absolute paths.
Grouped validators remain available for specialist inspection, with their
arguments and evidence limits documented beside each owner. A native output
or passing structural check does not create an admissible Run.
