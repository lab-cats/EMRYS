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
| `01` STAR alignment | complete and cluster-proven across all six samples | `ABE_EV_2` is a mapping outlier but not a pipeline blocker. |
| `02` canonical sort/read-group/index BAM | hardened and cluster-proven across all six samples | Final canonical BAMs have coordinate sort order, sample-specific RG metadata, BAI files, and `quickcheck` PASS. |
| `02b` BAM QC | implemented and useful for cohort QC/provenance; clean refresh against final hardened BAMs pending | Do not assume older reports all correspond to final hardened BAMs. |
| `03` RSeQC strandedness/orientation inference | cluster-proven across all six samples | All libraries are paired-end and reverse-stranded / first-strand-style. |
| `04` Picard MarkDuplicates | implemented and cluster-proven for `ABE_EV_2`; cohort-wide validation pending | Remaining five samples must be validated before promotion. |
| `05`-`09` downstream editing workflow | scaffolded / not implemented / not cluster-proven | Scripts and wrappers exit as not implemented. |

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
results/splitncigar/
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
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_star_index/
```

## Step 04 Current State

Step `04` is proven for `ABE_EV_2` with:

* completed scheduler state and exit code `0:0`
* nonempty duplicate-marked BAM, BAI, and Picard metrics
* passing `samtools quickcheck`
* coordinate sorting retained
* sample-specific read group retained
* duplicates marked, not removed
* `REMOVE_DUPLICATES=false`

`ABE_EV_2` duplication metrics:

| Metric | Value |
| ------ | ----: |
| Read pairs examined | 17,663,180 |
| Duplicate read pairs | 11,731,288 |
| Individual records marked duplicate | 23,462,576 |
| Optical duplicate pairs | 120,669 |
| Percent duplication | 0.664166 |
| Estimated library size | 6,327,403 |

The duplication fraction is elevated and should be compared across the cohort before interpretation. It is not currently labeled a pipeline failure.

## Current Next Work

1. Validate Step `04` across the remaining five samples.
2. Collect and compare duplication metrics across all six samples, including whether `ABE_EV_2` is a duplication outlier.
3. Refresh Step `02b` quickcheck/flagstat reports against the final hardened Step `02` BAMs.
4. Resolve supported cluster-wide Java 17 availability or a supported `JAVA_BIN_OVERRIDE` path.
5. Inspect and implement or harden Step `05` after GATK availability is resolved.
6. Continue Steps `06`-`09` after each upstream gate is proven.
7. Keep the reporting/artifact layer deferred until the core compute pipeline is substantially proven.

## Java And Picard Handoff

Step `04` resolves Java in the local checkout as:

1. `JAVA_BIN_OVERRIDE`, when provided.
2. `$JAVA_HOME/bin/java`, only if that path exists and is executable.
3. `command -v java`.

The wrapper then verifies the selected executable exists, logs the actual `java -version`, parses the runtime major version, and fails before Picard starts if the runtime is below Java 17.

Known cluster issue:

* `node003` provided working Java 17 via `/usr/bin/java` and completed `ABE_EV_2` MarkDuplicates.
* `node007` reported Java 11 at `/usr/bin/java`; Picard classes require Java 17 class-file version 61.
* The Java 17 module's advertised `JAVA_HOME` path was missing on `node007`.

Do not infer the effective Java runtime from the module name or `JAVA_HOME` alone. `--nodelist=node003` is a temporary operational workaround, not a durable architecture decision.

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
