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
| `01` | Align paired-end FASTQs to the reference. | FASTQ R1/R2 files, STAR index | `results/star/<sample_id>/` | complete and cluster-proven across all six samples | STAR |
| `02` | Create canonical coordinate-sorted, read-group-tagged, indexed BAMs. | STAR alignment BAM | `results/bam/<sample_id>/<sample_id>.sorted.bam` and `.bai` | hardened and cluster-proven across all six samples | samtools |
| `02b` | Run BAM integrity/QC checks. | canonical sorted BAM | `results/qc/bam/<sample_id>.quickcheck.txt`, `results/qc/bam/<sample_id>.flagstat.txt` | implemented and useful for cohort QC/provenance; clean refresh against final hardened BAMs pending | samtools |
| `03` | Infer strandedness and read orientation. | canonical sorted BAM, `refs/novogene_ref/genome.bed` | `results/qc/strandedness/<sample_id>.infer_experiment.txt` | cluster-proven across all six samples | RSeQC `infer_experiment.py` |
| `04` | Mark PCR/optical duplicates. | canonical sorted BAM | `results/markdup/<sample_id>/<sample_id>.markdup.bam` and `.bai`, Picard metrics | implemented and cluster-proven for `ABE_EV_2`; cohort-wide validation pending | Picard MarkDuplicates |
| `05` | Run RNA-seq SplitNCigarReads. | duplicate-marked BAM, reference FASTA | split-N-cigar BAM and index | scaffolded / not implemented / not cluster-proven | GATK SplitNCigarReads |
| `06` | Split processed BAMs by read orientation. | split-N-cigar BAM | orientation-specific BAMs and indexes | scaffolded / not implemented / not cluster-proven | samtools |
| `07` | Run mpileup by chromosome and orientation/strand. | orientation-specific BAMs, chromosome regions, reference FASTA | per-chromosome/per-orientation VCF files | scaffolded / not implemented / not cluster-proven | bcftools |
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

### Step 02b

Outputs:

```text
results/qc/bam/<sample_id>.quickcheck.txt
results/qc/bam/<sample_id>.flagstat.txt
```

Step `02b` is implemented and remains useful for cohort QC and provenance. A clean refresh against the final hardened Step `02` BAMs remains pending, so do not imply that all existing Step `02b` reports necessarily correspond to the final published BAMs.

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

Step `04` is implemented and cluster-proven for `ABE_EV_2`. Cohort-wide validation for the remaining five samples is pending confirmation.

For `ABE_EV_2`, Step `04` has been fully validated:

* SLURM state completed with exit code `0:0`
* elapsed time approximately 8 minutes 29 seconds
* observed MaxRSS approximately `22,660,004 K`
* output BAM approximately 3.1 GB
* BAM index created
* Picard metrics created
* `samtools quickcheck` passed
* coordinate order retained
* expected read-group metadata retained
* duplicate records marked, not removed
* `REMOVE_DUPLICATES=false`

Confirmed `ABE_EV_2` metrics:

| Metric | Value |
| ------ | ----: |
| Read pairs examined | 17,663,180 |
| Duplicate read pairs | 11,731,288 |
| Individual records marked duplicate | 23,462,576 |
| Optical duplicate pairs | 120,669 |
| Percent duplication | 0.664166 |
| Estimated library size | 6,327,403 |

The individual duplicate-record count is exactly twice the duplicate-pair count, which is internally consistent. The 66.42% duplication fraction is elevated and worth comparing across the cohort, but it is not by itself a pipeline failure. RNA-seq can show substantial coordinate duplication because highly expressed transcripts may generate many fragments with the same apparent endpoints; the optical duplicate count is much smaller than the total duplicate count.

Before Step `04` status can be updated for all six samples, the remaining five samples require confirmed scheduler completion, exit code `0:0`, nonempty BAM/BAI/metrics, passing `samtools quickcheck`, retained coordinate sorting, and retained sample-specific read groups.

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
FWD-like: 99 and 147
REV-like: 83 and 163
```

Because Step `03` confirms reverse-stranded / first-strand behavior across the cohort, future steps must document the difference between read orientation labels and biological transcript strand.

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

## Current Next Work

1. Validate Step `04` across the remaining five samples.
2. Collect and compare duplication metrics across all six samples.
3. Refresh Step `02b` quickcheck/flagstat reports against the final hardened BAMs.
4. Resolve supported cluster-wide Java 17 availability.
5. Inspect and implement or harden Step `05` after GATK availability is resolved.

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
* Use `TMPDIR=/tmp`.
* The cluster may warn that `/local/tmp` is not writable and fall back to `/tmp`; this has not been fatal.
* `module list` writes to stderr, so scripts should use `module list 2>&1 || true`.
* Known useful modules include `star/2.7.11b`, `samtools/1.19.2`, `bedtools/2.31.1`, `picard/3.1.1`, `python39`, and `java/17.0.10`.
* Step `04` validates the selected Java executable and actual runtime version; loading a module or reading `JAVA_HOME` alone is not enough.
* RSeQC is available through `.venv/bin/infer_experiment.py`.
* GATK availability still needs validation.
