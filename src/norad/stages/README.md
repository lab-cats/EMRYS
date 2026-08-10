# Transformation-stage owners

This directory contains the ten final native owners for computational
transformation stages. It is a routing layer, not a shared implementation
package, generic dispatcher, or complete list of numbered pipeline activities.
Only explicitly migrated children enter the installed Python distribution and
grouped module interface.

| Historical alias | Native owner |
| --- | --- |
| `00a` | [`construct_STAR_index`](star_index/README.md) |
| `00b` | [`convert_GTF_to_BED12`](gtf_to_bed12/README.md) |
| `00c` | [`construct_FASTA_sidecars`](fasta_sidecars/README.md) |
| `01` | [`align_RNA_reads_with_STAR`](star_alignment/README.md) |
| `02` | [`construct_canonical_BAM`](canonical_bam/README.md) |
| `04` | [`mark_BAM_duplicates_with_Picard`](duplicate_marking/README.md) |
| `05` | [`split_N_cigar_reads_with_GATK`](split_n_cigar/README.md) |
| `06` | [`partition_BAM_by_mechanical_read_orientation`](mechanical_orientation/README.md) |
| `07` | [`generate_partitioned_cohort_mpileup_VCFs`](generate_partitioned_cohort_mpileup_VCFs/README.md) |
| `08` | [`preprocess_and_annotate_cohort_candidates`](preprocess_and_annotate_cohort_candidates/README.md) |

The canonical identities and dependency edges live in
[`STAGE_MAP.md`](../contracts/STAGE_MAP.md). Evidence operations `02b`, `03`,
and `09c` live under [`evidence/`](../evidence/README.md); analysis `09` lives
under [`analyses/`](../analyses/rank_cohort_candidates_with_paired_CMH/README.md).

## Owner convention

Each child directory owns its declared producer, scheduler wrapper when one
exists, validator, native outputs, publication/recovery behavior, and known
limitations. Its adjacent `CONTRACT.md` is the canonical interface and
evidence boundary; its `README.md` provides local operator orientation. Direct
tests mirror the owner under [`tests/stages/`](../../../tests/stages/), while
cross-owner contract tests retain their own neutral or repository-level
ownership.

For `00a`, the SLURM file embeds the producer rather than delegating to a
separate shell or Python producer, while its validator is exposed as
`python -I -m norad validate star-index`. Step `00b` exposes its migrated
producer and validator through the grouped module interface. Step `00c` keeps
its shell producer and scheduler as repository-path interfaces while exposing
its validator as `python -I -m norad validate fasta-sidecars`. Step `01`
likewise keeps its shell producer and scheduler as repository-path interfaces
while exposing its private validator as
`python -I -m norad validate star-alignment`. Step `02` keeps its shell
producer and scheduler as repository-path interfaces while exposing its
private validator as `python -I -m norad validate canonical-bam`. Step `04`
keeps its shell producer and scheduler as repository-path interfaces while
exposing its private validator as
`python -I -m norad validate duplicate-marking`. Step `05` likewise keeps its
shell producer and scheduler as repository-path interfaces while exposing its
private validator as `python -I -m norad validate split-n-cigar`. Step `06`
keeps its shell producer and scheduler as repository-path interfaces while
exposing its private validator as
`python -I -m norad validate mechanical-orientation`. For `08`, the shell
transaction owner delegates its scientific transform to the adjacent Rscript
implementation. The remaining stage interfaces are still repository paths,
not installed commands or import APIs.

Each owner declares and governs the outputs produced through its interfaces,
normally under ignored `results/` or declared reference storage. A file,
scheduler success, receipt, or validation row is not by itself proof of a
complete valid attempt. Current protection is predominantly local fixture/mock
evidence, with guarded local real-R evidence for Step `08`; it is not new
scheduler, cluster, production, scientific-review, editing-site, or
biological-readiness proof.

Use the [`RUNBOOK`](../../../docs/operations/RUNBOOK.md) for supported commands,
[`TROUBLESHOOTING`](../../../docs/operations/TROUBLESHOOTING.md) for recovery,
and each adjacent contract for exact behavior.
