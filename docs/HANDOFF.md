# Project Handoff Notes

## What This Project Does

This repository rebuilds a Novogene Remora RNA-seq / RNA-editing workflow into a cleaner, manifest-driven, testable pipeline for local development and CSU SLURM execution.

The biological context is NORAD / PUM1 / rABE-related RNA-seq data. The downstream workflow appears to be RNA-editing / variant-like site calling rather than simple gene-count differential expression. Uploaded legacy scripts are treated as protocol references, not as runnable source of truth.

The intended high-level workflow is:

1. Build STAR index from the Novogene reference.
2. Convert GTF annotation to BED12 for RSeQC.
3. Align paired-end RNA-seq reads with STAR.
4. Create canonical coordinate-sorted, read-group-tagged, indexed BAMs.
5. QC canonical BAMs.
6. Infer library strandedness/orientation with RSeQC.
7. Mark duplicates.
8. Run GATK SplitNCigarReads.
9. Split BAMs by read orientation.
10. Run bcftools mpileup by chromosome and orientation/strand.
11. Preprocess VCFs.
12. Run CMH/editing-site calling.

## Current Status

| Step | Status | Notes |
| ---- | ------ | ----- |
| `00a` STAR index | cluster-proven | Built Novogene STAR index at `refs/novogene_star_index`. |
| `00b` GTF to BED12 | cluster-proven | Wrote `refs/novogene_ref/genome.bed`; 206,601 BED12 transcript records. |
| `00c` GATK reference sidecars | planned / not implemented | Ad hoc cluster prep generated `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict`; no repo script/job exists yet. |
| `01` STAR alignment | complete and cluster-proven across all six samples | `ABE_EV_2` is a mapping outlier but not a pipeline blocker. |
| `02` canonical sort/read-group/index BAM | hardened and cluster-proven across all six samples | Final canonical BAMs have coordinate sort order, sample-specific RG metadata, BAI files, and `quickcheck` PASS. |
| `02b` BAM QC | implemented and refreshed across all six final hardened Step 02 BAMs | Initial cohort attempt exposed a samtools `PATH` inconsistency; rerun succeeded after prepending the known samtools bin path. |
| `03` RSeQC strandedness/orientation inference | cluster-proven across all six samples | All libraries are paired-end and reverse-stranded / first-strand-style. |
| `04` Picard MarkDuplicates | cluster-proven across all six samples | Duplicate-marked BAMs, indexes, Picard metrics, quickcheck, coordinate sort order, read groups, and metrics rows are confirmed. |
| `05` GATK SplitNCigarReads | scaffolded and intentionally non-runnable; not cluster-proven | Real scaffold files exist, intentionally exit with code `2`, and perform no analysis. |
| `06`-`09` downstream editing workflow | scaffolded / not implemented / not cluster-proven | Scripts and wrappers exit as not implemented. |

## Cohort

Known paired-end samples:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

Conditions:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Note that `ABE_EV4` lacks the underscore before `4`.

## Current Scientific And Workflow Conclusions

Step `03` confirmed all six libraries are paired-end and reverse-stranded / first-strand-style.

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| ------ | ------------------: | ----------------: | ----------------: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The `ABE_EV_2` Step `03` output was rerun after Step `02` hardening and matched the previous report exactly. Step `02` changed operational metadata and publication safety without changing the biological orientation inference.

## Main Entry Points

Implemented scripts:

```text
scripts/validate_manifest.py
scripts/gtf_to_bed12.py
scripts/step_01_star_align.sh
scripts/step_02_sort_index_bam.sh
scripts/step_02b_bam_qc.sh
scripts/step_03_infer_strandedness_and_orientation.sh
scripts/step_04_mark_duplicates.sh
```

Implemented SLURM jobs:

```text
jobs/step_00a_build_novogene_star_index.slurm
jobs/step_00b_gtf_to_bed12.slurm
jobs/step_01_star_align.slurm
jobs/step_02_sort_index_bam.slurm
jobs/step_02b_bam_qc.slurm
jobs/step_03_infer_strandedness_and_orientation.slurm
jobs/step_04_mark_duplicates.slurm
```

Scaffolded downstream files:

```text
jobs/step_05_split_n_cigar_reads.slurm
jobs/step_06_split_bam_by_read_orientation.slurm
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
jobs/step_08_vcf_preprocessing.slurm
jobs/step_09_cmh_editing_site_calling.slurm
scripts/step_05_split_n_cigar_reads.sh
scripts/step_06_split_bam_by_read_orientation.sh
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
scripts/step_08_vcf_preprocessing.sh
scripts/step_09_cmh_editing_site_calling.sh
```

These future steps are intentionally non-runnable and exit as not implemented.

## Operator Pointers

For operational commands, validation checklists, cluster setup, and per-step run examples, start with `docs/RUNBOOK.md`.

Useful optional cluster helper commands, when installed:

```text
norad
nlogs
sqme
sj <jobid>
sjtail <jobid>
sjcheck <jobid>
```

Expected output families:

```text
results/star/<sample>/
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
results/qc/bam/<sample>.quickcheck.txt
results/qc/bam/<sample>.flagstat.txt
results/qc/strandedness/<sample>.infer_experiment.txt
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt
```

Expected future output families, once implemented:

```text
results/split_ncigar/
results/orientation/
results/vcf/
results/editing/
results/artifacts/
results/reports/
```

Where to look:

```text
docs/PIPELINE_PLAN.md  current step status and validation detail
docs/RUNBOOK.md        how to run and validate jobs
DECISIONS.md           durable decisions and rationale
TROUBLESHOOTING.md     symptom -> cause -> fix
docs/QUESTIONS.md      unresolved and answered questions
TODO.md                tactical next work
README.md              concise entrypoint
```

### Operator Checklist

- **Dry-run by default:** SLURM job wrappers default to dry-run; submit a dry-run first to validate resolved inputs and printed commands.
- **Execute on cluster:** When ready to run, submit with `EXECUTE=1` exported to the job, for example:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

- **Script-level execution:** Workflow shell scripts print resolved context by default and only run tool commands when passed `--execute`; include all required step arguments when invoking a script directly.
- **Where to validate:** Use `docs/RUNBOOK.md` for per-step dry-run/execute checks, `DECISIONS.md` for the execution policy, and `docs/PIPELINE_PLAN.md` for step status.
- **Quick post-run checks:** Confirm expected outputs appear under `results/` (star, bam, qc, markdup) and inspect SLURM logs under `logs/`.

## Data Locations

Local development repo:

```text
/Users/elisteiger/dev/norad
```

Cluster repo:

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

Raw data symlink on cluster:

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs are under:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

Prepared references:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

The GATK reference sidecars were generated successfully as an ad hoc cluster prep task with exit code `0:0`. Reference/BAM compatibility passed with 194 FAI contigs, 194 DICT contigs, 194 BAM header contigs, and reference/BAM SQ check `PASS`. This prep should become Step `00c`; Step `05` should require these files rather than creating shared reference sidecars inside per-sample jobs.

## Step 02b Current State

Step `02b` is implemented and refreshed across all six final hardened Step `02` BAMs.

The first cohort attempt failed immediately because `samtools` was not found on `PATH` even though module output listed `samtools/1.19.2`. The successful rerun prepended the known samtools bin directory:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This is a cluster environment/PATH inconsistency, not a BAM/QC failure. The current Step `02b` script creates the requested output directory before dry-run exit, so do not describe that dry-run as side-effect-free.

## Step 04 Current State

Step `04` is cluster-proven across all six samples with:

* completed scheduler state and exit code `0:0`
* nonempty duplicate-marked BAM, BAI, and Picard metrics
* passing `samtools quickcheck`
* coordinate sorting retained
* sample-specific read group retained
* duplicates marked, not removed
* `REMOVE_DUPLICATES=false`

Confirmed final Step `04` outputs:

| Sample | Markdup BAM size | Metrics size |
| ------ | ---------------: | -----------: |
| `ABE_EV_2` | 3.1G | 16K |
| `ABE_EV_3` | 2.1G | 7.8K |
| `ABE_EV4` | 3.0G | 15K |
| `ABE_PUM1_2` | 2.3G | 12K |
| `ABE_PUM1_3` | 2.1G | 8.5K |
| `ABE_PUM1_4` | 2.5G | 13K |

Confirmed Step `04` runtime/resource observations:

| Sample | Runtime | MaxRSS |
| ------ | ------: | -----: |
| `ABE_EV_2` | 00:08:29 | 22,660,004K |
| `ABE_EV_3` | 00:06:06 | 23,912,380K |
| `ABE_EV4` | 00:08:52 | 23,287,592K |
| `ABE_PUM1_2` | 00:06:40 | 24,293,400K |
| `ABE_PUM1_3` | 00:06:33 | 24,341,032K |
| `ABE_PUM1_4` | 00:07:32 | 23,376,504K |

Confirmed MarkDuplicates metrics:

| Sample | Read pairs examined | Duplicate read pairs | Optical duplicate pairs | Percent duplication | Estimated library size |
| ------ | ------------------: | -------------------: | ----------------------: | ------------------: | ---------------------: |
| `ABE_EV_2` | 17,663,180 | 11,731,288 | 120,669 | 0.664166 | 6,327,403 |
| `ABE_EV_3` | 18,867,589 | 11,371,887 | 130,069 | 0.602721 | 8,397,468 |
| `ABE_EV4` | 23,240,508 | 19,860,628 | 177,257 | 0.854569 | 3,383,587 |
| `ABE_PUM1_2` | 19,087,654 | 13,522,128 | 128,791 | 0.708423 | 5,783,576 |
| `ABE_PUM1_3` | 21,657,503 | 14,809,440 | 150,924 | 0.683802 | 7,214,041 |
| `ABE_PUM1_4` | 19,424,683 | 16,348,986 | 132,657 | 0.841660 | 3,081,584 |

Duplicate reads were marked, not removed. Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size. The observed Step `04` memory range was about 22.7-24.3 GB MaxRSS; this is observed evidence, not a guaranteed resource requirement.

## Step 05 Current State

Step `05` has real scaffold files:

```text
jobs/step_05_split_n_cigar_reads.slurm
scripts/step_05_split_n_cigar_reads.sh
```

They intentionally exit with code `2`, print that Step `05` is not implemented, and perform no analysis. The scaffold contains stale future path examples:

```text
results/bam/<sample_id>/<sample_id>.sorted.md.bam
results/bam/<sample_id>/<sample_id>.sorted.md.splitncigar.bam
```

Those are stale scaffold examples, not current interfaces. Current real Step `04` outputs are:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
```

Step `05` implementation should explicitly decide and document the processed-BAM output layout before becoming runnable, likely under:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
```

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`. Step `05` still remains scaffolded and intentionally non-runnable; not cluster-proven.

## Current Next Work

1. Resolve supported cluster-wide Java 17 availability or a supported `JAVA_BIN_OVERRIDE` path.
2. Formalize Step `00c` so it creates/validates `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict`.
3. Decide the Step `05` processed-BAM output layout before implementation.
4. Inspect and implement or harden Step `05` using the confirmed GATK path and validated reference sidecars.
5. Continue Steps `06`-`09` after each upstream gate is proven.
6. Keep the reporting/artifact layer deferred until the core compute pipeline is substantially proven.

## Java And Picard Handoff

Step `04` resolves Java in the local checkout as:

1. `JAVA_BIN_OVERRIDE`, when provided.
2. `$JAVA_HOME/bin/java`, only if that path exists and is executable.
3. `command -v java`.

The wrapper then verifies the selected executable exists, logs the actual `java -version`, parses the runtime major version, and fails before Picard starts if the runtime is below Java 17.

Known cluster issue:

* `node002` provided Java 17, completed the GATK/bcftools tool probe successfully, and ran OpenJDK `17.0.14`.
* `node003` provided working Java 17 via `/usr/bin/java` and completed `ABE_EV_2` MarkDuplicates.
* `node007` reported Java 11 at `/usr/bin/java`; Picard classes require Java 17 class-file version 61.
* The Java 17 module's advertised `JAVA_HOME` path was missing on `node007`.

Do not infer the effective Java runtime from the module name or `JAVA_HOME` alone. Scripts should continue logging and validating the actual Java runtime. Node-specific success is evidence, not a durable architecture decision.

## Local Validation Gate

Run from the local repo root:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
git status --short
git diff --name-status
```

Local tests are lightweight and should not require real full-size BAM/FASTQ data.

## Development Rule

Do not jump ahead. The pipeline should continue to be developed as:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs -> proceed
```
