# NORAD Pipeline Plan

This is the detailed map for the local-first, SLURM-scaled NORAD / Novogene Remora RNA-seq workflow.

The project rebuilds an uploaded/reference RNA-editing workflow into a cleaner, manifest-driven, testable pipeline. Legacy scripts are protocol references, not runnable source of truth.

Pipeline development follows a gated workflow:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs -> proceed
```

## Cohort

Samples:

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

## Pipeline Table

| Step | Purpose | Expected inputs | Expected outputs | Status | Main tool(s) |
| ---- | ------- | --------------- | ---------------- | ------ | ------------ |
| `00a` | Build the Novogene STAR index. | Novogene reference FASTA/GTF under `refs/novogene_ref/` | `refs/novogene_star_index/` | cluster-proven | STAR |
| `00b` | Convert reference GTF to sorted BED12 for strandedness checks. | `refs/novogene_ref/genome.gtf` | `refs/novogene_ref/genome.bed` | cluster-proven | Python, bedtools |
| `00c` | Create/validate GATK reference sidecars. | `refs/novogene_ref/genome.fa` | `refs/novogene_ref/genome.fa.fai`, `refs/novogene_ref/genome.dict` | cluster-proven | samtools, GATK |
| `01` | Align paired-end FASTQs to the reference. | FASTQ R1/R2 files, STAR index | `results/star/<sample_id>/` | complete and cluster-proven across all six samples | STAR |
| `02` | Create canonical coordinate-sorted, read-group-tagged, indexed BAMs. | STAR alignment BAM | `results/bam/<sample_id>/<sample_id>.sorted.bam` and `.bai` | hardened and cluster-proven across all six samples | samtools |
| `02b` | Run BAM integrity/QC checks. | canonical sorted BAM | `results/qc/bam/<sample_id>.quickcheck.txt`, `results/qc/bam/<sample_id>.flagstat.txt` | implemented and refreshed across all six final hardened Step 02 BAMs | samtools |
| `03` | Infer strandedness and read orientation. | canonical sorted BAM, `refs/novogene_ref/genome.bed` | `results/qc/strandedness/<sample_id>.infer_experiment.txt` | cluster-proven across all six samples | RSeQC `infer_experiment.py` |
| `04` | Mark PCR/optical duplicates. | canonical sorted BAM | `results/markdup/<sample_id>/<sample_id>.markdup.bam` and `.bai`, Picard metrics | cluster-proven across all six samples | Picard MarkDuplicates |
| `05` | Run RNA-seq SplitNCigarReads. | duplicate-marked BAM, Step `00c` reference FASTA/FAI/DICT | `results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam` and `.bai` | implemented and locally tested; cluster revalidation submitted/running; final outputs not yet inspected | GATK SplitNCigarReads |
| `06` | Split processed BAMs by read-orientation group. | `results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam` and `.bai` | `results/orientation/<sample_id>/<sample_id>.FWD_like.bam` and `.bai`; `results/orientation/<sample_id>/<sample_id>.REV_like.bam` and `.bai`; `results/qc/orientation/<sample_id>.orientation_counts.tsv` | next implementation target / not cluster-proven | samtools |
| `07` | Run mpileup by chromosome and read-orientation group. | orientation-specific BAMs, chromosome regions, reference FASTA | per-chromosome/per-orientation VCF files | scaffolded / not implemented / not cluster-proven | bcftools |
| `08` | Preprocess mpileup VCFs for editing-site statistics. | Step `07` VCF files | cleaned/annotated VCF-like TSV/table files | scaffolded / not implemented / not cluster-proven | R |
| `09` | Call CMH editing sites and write summaries. | Step `08` preprocessed tables | CMH/editing-site result tables and plots | scaffolded / not implemented / not cluster-proven | R |

## Validated Outputs And Results

### Step 00a

```text
refs/novogene_star_index/
```

The STAR index was built using `sjdbOverhang=149`, matching 150 bp reads.

### Step 00b

```text
refs/novogene_ref/genome.bed
```

The BED12 file contains 206,601 transcript records.

### Step 00c

Purpose:

```text
GATK reference sidecars / reference FASTA index and sequence dictionary
```

Expected outputs:

```text
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Implemented entry points:

```text
scripts/step_00c_prepare_gatk_reference.sh
jobs/step_00c_prepare_gatk_reference.slurm
tests/shell/test_step_00c_prepare_gatk_reference.sh
```

The Step `00c` implementation is dry-run by default, creates only missing sidecars in execute mode, uses a reference-level lock, publishes run-token temp files only after validation, and fails rather than overwriting invalid existing sidecars.

The sidecars were also generated successfully before this implementation as an ad hoc cluster prep task; formal Step `00c` cluster validation is now complete.

Reference/BAM compatibility check:

```text
FAI contigs: 194
DICT contigs: 194
BAM header contigs: 194
Reference/BAM SQ check: PASS
```

Status:

```text
cluster-proven
```

### Step 01

All six samples completed STAR alignment.

| Sample | Approximate input reads | Unique mapping rate |
| ------ | ----------------------: | ------------------: |
| `ABE_EV_2` | 21.36 million | 58.50% |
| `ABE_EV_3` | 20.5 million | 82.95% |
| `ABE_EV4` | 26.6 million | 71.06% |
| `ABE_PUM1_2` | 21.1 million | 77.51% |
| `ABE_PUM1_3` | 23.2 million | 85.38% |
| `ABE_PUM1_4` | 22.5 million | 70.96% |

For `ABE_EV_2`, uniquely mapped reads were 58.50%, reads mapped to multiple loci were 24.19%, and reads unmapped because they were too short were 16.55%. `ABE_EV_2` is a cross-sample mapping outlier, especially in unique mapping, but this is an observed sample-level property rather than a pipeline blocker.

### Step 02

Canonical outputs:

```text
results/bam/<sample_id>/<sample_id>.sorted.bam
results/bam/<sample_id>/<sample_id>.sorted.bam.bai
```

The hardened Step `02` implementation guarantees:

* coordinate sorting
* one sample-specific read group per BAM
* read-group fields `ID=<sample_id>`, `SM=<sample_id>`, provisional `LB=<sample_id>`, and `PL=ILLUMINA`
* every alignment record has the expected `RG` tag
* `@HD` reports `SO:coordinate`
* validation before publication
* `samtools quickcheck`
* BAM indexing
* per-sample lock directory
* fresh job/process-specific temporary and backup paths
* rollback-protected publication
* stable canonical BAM/BAI paths are replaced only after validation succeeds
* dry-run mode creates no directories or files

The hardening was required because the original canonical `ABE_EV_2` BAM lacked read groups, causing Picard to fail with:

```text
SAMRecord.getReadGroup() is null
```

All six final Step `02` BAMs have been manually confirmed to have a nonempty BAM, matching BAI, `samtools quickcheck: PASS`, `SO:coordinate`, and the correct sample-specific `@RG`.

Confirmed final canonical BAM sizes were approximately:

| Sample | BAM size |
| ------ | -------: |
| `ABE_EV_2` | 3.0 GB |
| `ABE_EV_3` | 2.0 GB |
| `ABE_EV4` | 2.9 GB |
| `ABE_PUM1_2` | 2.2 GB |
| `ABE_PUM1_3` | 2.1 GB |
| `ABE_PUM1_4` | 2.5 GB |

Transient backup and lock paths are not stable interfaces.

Step `02` cleanup/trap handling was hardened after local validation-failure tests found an owned-lock cleanup regression. This did not change the canonical Step `02` BAM/BAI output contract.

### Step 02b

Outputs:

```text
results/qc/bam/<sample_id>.quickcheck.txt
results/qc/bam/<sample_id>.flagstat.txt
```

Step `02b` is implemented and refreshed across all six final hardened Step `02` BAMs.

The first Step `02b` cohort attempt failed immediately because `samtools` was not found on `PATH`, despite module output listing `samtools/1.19.2`. The successful rerun prepended the known samtools bin directory:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This is a cluster environment/PATH inconsistency, not a BAM/QC failure.

The current script creates the requested output directory before dry-run exit; do not describe Step `02b` dry-run mode as side-effect-free.

### Step 03

All six libraries are paired-end and consistently reverse-stranded / first-strand-style.

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| ------ | ------------------: | ----------------: | ----------------: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The dominant reverse-stranded orientation ranges from 0.8562 to 0.8740 across the cohort. The opposing orientation ranges from 0.0374 to 0.0433, and the failed-to-determine fraction ranges from 0.0828 to 0.1063.

There is no flipped-orientation sample and no obvious condition-specific strandedness inconsistency. The `ABE_EV_2` Step `03` report was preserved, rerun after Step `02` hardening, and compared with the previous report with an empty diff, confirming the Step `02` metadata hardening did not change the biological orientation inference.

Durable scientific conclusion:

```text
All six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.
```

Tool-specific examples that commonly correspond to this orientation include:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

### Step 04

Step `04` is cluster-proven across all six samples.

All six samples have:

* duplicate-marked BAM present
* BAM index present
* Picard metrics present
* `samtools quickcheck: PASS`
* `@HD` retained with `SO:coordinate`
* sample-specific `@RG` retained
* populated Picard metrics row
* duplicate records marked, not removed
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

Duplicate reads were marked, not removed. Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size.

The observed Step `04` memory range was about 22.7-24.3 GB MaxRSS. This is an observed resource range, not a guaranteed requirement.

### Step 05

Step `05` is implemented and locally tested. Six-sample cluster revalidation has been submitted/running, but final outputs have not yet been inspected in this interim status patch. Do not describe Step `05` as cluster-proven or cohort-proven yet.

Implemented entry points:

```text
jobs/step_05_split_n_cigar_reads.slurm
scripts/step_05_split_n_cigar_reads.sh
tests/shell/test_step_05_split_n_cigar_reads.sh
```

Inputs:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Outputs:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`.

Step `05` treats `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` as prerequisites, fails clearly if they are missing, and must not silently create shared reference sidecars inside per-sample jobs.

The implementation is dry-run by default, side-effect-free in dry-run mode, validates the selected Java runtime is at least Java 17 in execute mode, writes GATK output to a run-token temp BAM, indexes and validates the temp pair with samtools, checks coordinate sort order and sample read-group preservation, and publishes final BAM/BAI only after validation succeeds.

The first `ABE_EV_2` cluster execute attempt provided useful partial evidence: GATK completed traversal pass 1, entered traversal pass 2, and then failed during HTSJDK temporary spill/write/close behavior because `SortingCollection` temp files were written to node-local `/tmp` and hit `No space left on device`.

Step `05` was hardened to use a per-run project-storage GATK temp directory via `--java-options -Djava.io.tmpdir=...`, `--tmp-dir ...`, and `TMPDIR` for the GATK process. Cleanup now removes owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks on failure.

Step `06` should consume the Step `05` output contract:

```text
results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai
```

### Step 06

Step `06` is the next implementation target. It is not implemented and not cluster-proven.

Input contract:

```text
results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai
```

Expected output contract:

```text
results/orientation/<sample>/<sample>.FWD_like.bam
results/orientation/<sample>/<sample>.FWD_like.bam.bai
results/orientation/<sample>/<sample>.REV_like.bam
results/orientation/<sample>/<sample>.REV_like.bam.bai
results/qc/orientation/<sample>.orientation_counts.tsv
```

Legacy read-orientation groups to preserve:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

These are mechanical flag groups. `samtools view -f FLAG` means a read has all bits in `FLAG`; it is not exact flag equality. Do not describe `FWD_like` or `REV_like` as biological sense, antisense, transcript-strand, or biological-strand calls.

## Reference Workflow Alignment

Steps `04`-`09` are based on the uploaded/reference RNA-editing workflow:

```text
MarkDuplicates
-> SplitNCigarReads
-> split BAM by read orientation
-> bcftools mpileup
-> VCF preprocessing
-> CMH editing-site calling
```

This repository is rebuilding that workflow in a cleaner SLURM/script/testable structure rather than using the hardcoded original scripts directly.

The old workflow split read orientation using samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

Because Step `03` confirms reverse-stranded / first-strand behavior across the cohort, future steps must treat `FWD_like` and `REV_like` as read-orientation/mechanical flag groups and avoid unsupported biological strand claims.

## Future Artifact And Reporting Layer

This layer is planned, deferred, and non-runnable. It is not a new core pipeline step and is not a runnable Step `10`. The existing Steps `00a`-`09` remain the core computational pipeline.

The intended future separation is:

```text
core computation: Steps 00a-09
    -> future per-step JSON sidecars
    -> future aggregation into results/artifacts/run_summary.json
    -> future report rendering from structured artifacts
```

Per-step JSON sidecars are a future cross-cutting pipeline capability. They should eventually describe each completed or attempted step without changing the core output paths. A future layout may look like:

```text
results/
  bam/ABE_EV_2/ABE_EV_2.sorted.bam
  bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai

  artifacts/
    ABE_EV_2/
      01_star_align.json
      02_sort_index.json
      02b_bam_qc.json
      03_strandedness.json
      04_mark_duplicates.json
      ...
    run_summary.json

  reports/
    run_report.html
    run_report.pdf
    run_summary.tsv
```

Future sidecars should use a consistent, versioned JSON schema. The minimum shared fields are expected to include:

```text
schema version
pipeline version or git commit
run ID
step ID/name
sample ID when applicable
status
timing
inputs
outputs
tool names and versions
resolved parameters
key metrics
warnings
exit status
```

The future aggregation phase should discover or receive expected sidecars, validate schema versions, combine sample-level and run-level information, record missing/failed/incomplete steps explicitly, and write:

```text
results/artifacts/run_summary.json
```

The future report layer should read only structured artifacts and final result tables. It must not require rerunning STAR, samtools, Picard, GATK, bcftools, or CMH computation.

Compute outputs and rendering outputs should stay separate: core steps write BAMs, indexes, metrics, VCF-like tables, and CMH result tables; the reporting layer consumes those outputs plus structured artifacts to produce human-readable summaries.

Initial report targets:

```text
results/reports/run_report.html
results/reports/run_report.pdf
results/reports/run_summary.tsv
```

Jinja2 may be a good fit for HTML rendering. Quarto or R Markdown may be useful for publication-quality biological figures and PDF output. The renderer layer should remain replaceable without modifying compute steps.

Step `09` CMH/editing-site results should eventually receive a richer, domain-specific artifact schema rather than being flattened into generic key/value metrics. That schema may include:

```text
comparison definitions
editing type
filter thresholds
site counts
significant up/down site counts
effect-size summaries
coverage summaries
result-table paths
plot paths
annotation/reference metadata
multiple-testing method
```

## Future Cross-Cutting Engineering Roadmap

Deferred engineering improvements are tracked canonically in `TODO.md`. They are roadmap ideas, not current blockers for Step `05` or the remaining compute pipeline.

Future cross-cutting capabilities may include:

* manifest-driven submission and validation helpers, followed later by SLURM job arrays after single-sample behavior is stable
* environment/tool probes, reference provenance and checksums, output retention policy, standardized validation reports, cohort QC summaries, and demo/reporting artifacts
* shared shell/SLURM helper libraries after behavior is covered by tests and output contracts are stable
* conservative handoff/admin utilities such as tool-path config, troubleshooting taxonomy, and stale-lock inspection or cleanup helpers

Candidate helper names and interfaces are not decided unless a later implementation task explicitly promotes them. Future refactors must preserve existing step CLIs, output paths, dry-run/execute semantics, and proven cluster contracts.

## Current Next Work

1. Inspect the submitted/running Step `05` six-sample cluster revalidation outputs and logs.
2. Confirm each final split-N-cigar BAM/BAI before declaring Step `05` cluster-proven or cohort-proven.
3. Implement Step `06` against the Step `05` output contract.
4. Continue Steps `07`-`09` one gate at a time.

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

## Known Cluster Notes

* `logs/` must exist before `sbatch`.
* Use `TMPDIR=/tmp` for the general SLURM wrapper convention.
* Step `05` GATK work must route Java/HTSJDK/GATK temp files to project storage, not node-local `/tmp`.
* The cluster may warn that `/local/tmp` is not writable and fall back to `/tmp`; this has not been fatal.
* `module list` writes to stderr, so scripts should use `module list 2>&1 || true`.
* Known useful modules include `star/2.7.11b`, `samtools/1.19.2`, `bedtools/2.31.1`, `picard/3.1.1`, `python39`, and `java/17.0.10`.
* Step `04` validates the selected Java executable and actual runtime version; loading a module or reading `JAVA_HOME` alone is not enough.
* RSeQC is available through `.venv/bin/infer_experiment.py`.
* GATK is available at `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the confirmed version is `4.6.1.0`.
* bcftools is available at `/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools`; the confirmed version is `1.21`.
* The GATK/bcftools tool probe succeeded on `node002` with exit code `0:0`; `node002` used OpenJDK `17.0.14`.
* The Java inconsistency remains relevant: `node002` and `node003` have provided Java 17, while `node007` previously exposed Java 11 / a missing Java 17 path.
