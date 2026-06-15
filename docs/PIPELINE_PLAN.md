# NORAD Pipeline Plan

This is the high-level map for the local-first, SLURM-scaled NORAD / Novogene Remora RNA-seq workflow.

The project is rebuilding an uploaded/reference RNA-editing workflow into a cleaner, manifest-driven, testable pipeline. Legacy scripts are treated as protocol references, not as runnable source of truth.

Pipeline development follows a gated workflow:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> proceed
```

Future steps are scaffolding only until their scripts, wrappers, and tests are implemented.

## Current validated sample

The current development/validation sample is:

```text
ABE_EV_2
```

The full sample set is:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

## Pipeline table

| Step | Purpose                                                        | Expected inputs                                                | Expected outputs                                                                       | Status                                      | Main tool(s)                |
| ---- | -------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------- | --------------------------- |
| 00a  | Build the Novogene STAR index.                                 | Novogene reference FASTA/GTF under `refs/novogene_ref/`        | `refs/novogene_star_index/`                                                            | implemented / cluster-proven                | STAR                        |
| 00b  | Convert reference GTF to sorted BED12 for strandedness checks. | `refs/novogene_ref/genome.gtf`                                 | `refs/novogene_ref/genome.bed`                                                         | implemented / cluster-proven                | Python, bedtools            |
| 01   | Align paired-end FASTQs to the reference.                      | FASTQ R1/R2 files, STAR index                                  | STAR output under `results/star/<sample_id>/`                                          | implemented / cluster-proven for `ABE_EV_2` | STAR                        |
| 02   | Create canonical coordinate-sorted, read-group-tagged, indexed BAMs.  | STAR alignment BAM                                             | `results/bam/<sample_id>/<sample_id>.sorted.bam` and `.bai`                            | implemented / pending cluster revalidation after read-group hardening | samtools                    |
| 02b  | Run BAM integrity/QC checks.                                   | canonical sorted BAM                                           | `results/qc/bam/<sample_id>.quickcheck.txt`, `results/qc/bam/<sample_id>.flagstat.txt` | implemented / cluster-proven for `ABE_EV_2` | samtools                    |
| 03   | Infer strandedness and read orientation.                       | canonical sorted BAM, `refs/novogene_ref/genome.bed`           | `results/qc/strandedness/<sample_id>.infer_experiment.txt`                             | implemented / cluster-proven for `ABE_EV_2` | RSeQC `infer_experiment.py` |
| 04   | Mark PCR/optical duplicates.                                   | canonical sorted BAM                                           | `results/markdup/<sample_id>/<sample_id>.markdup.bam` and `.bai`, Picard metrics       | implemented / pending cluster validation    | Picard MarkDuplicates       |
| 05   | Run RNA-seq SplitNCigarReads.                                  | duplicate-marked BAM, reference FASTA                          | split-N-cigar BAM and index                                                            | pending / scaffold only                     | GATK SplitNCigarReads       |
| 06   | Split processed BAMs by read orientation.                      | split-N-cigar BAM                                              | orientation-specific BAMs and indexes                                                  | pending / scaffold only                     | samtools                    |
| 07   | Run mpileup by chromosome and orientation/strand.              | orientation-specific BAMs, chromosome regions, reference FASTA | per-chromosome/per-orientation VCF files                                               | pending / scaffold only                     | bcftools                    |
| 08   | Preprocess mpileup VCFs for editing-site statistics.           | Step 07 VCF files                                              | cleaned/annotated VCF-like TSV/table files                                             | pending / scaffold only                     | R                           |
| 09   | Call CMH editing sites and write summaries.                    | Step 08 preprocessed tables                                    | CMH/editing-site result tables and plots                                               | pending / scaffold only                     | R                           |

## Validated outputs so far

### Step 00a

```text
refs/novogene_star_index/
```

STAR index was built using `sjdbOverhang=149`, matching 150 bp reads.

### Step 00b

```text
refs/novogene_ref/genome.bed
```

The BED12 file contains 206,601 transcript records.

### Step 01 for ABE_EV_2

```text
results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam
results/star/ABE_EV_2/ABE_EV_2.Log.final.out
results/star/ABE_EV_2/ABE_EV_2.Log.out
results/star/ABE_EV_2/ABE_EV_2.Log.progress.out
results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab
```

STAR summary for `ABE_EV_2`:

```text
Input reads: 21,358,987
Unique mapped: 58.50%
Multi-mapped: 24.19%
Too many loci: 0.52%
Unmapped too short: 16.55%
Approximate total mapped: 83.21%
```

### Step 02 for ABE_EV_2

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Hardened Step `02` sorts the input alignment, adds the sample read group with
`samtools addreplacerg`, validates strict one-sample read-group metadata,
indexes the replacement BAM, and publishes the canonical BAM/BAI under a
per-sample lock with rollback protection.

The original Step 02 sort/index implementation was successfully exercised on
the cluster before read-group hardening. Those pre-hardening outputs lacked
required read-group metadata and are superseded by the hardened Step 02
contract.

Pre-hardening Step 02 execution used approximately 6.8G MaxRSS and completed
in about 3 minutes 46 seconds.

### Step 02b for ABE_EV_2

```text
results/qc/bam/ABE_EV_2.quickcheck.txt
results/qc/bam/ABE_EV_2.flagstat.txt
```

Step 02b execute completed successfully with no stderr noted.

### Step 03 for ABE_EV_2

```text
results/qc/strandedness/ABE_EV_2.infer_experiment.txt
```

Observed RSeQC output:

```text
This is PairEnd Data
Fraction of reads failed to determine: 0.0828
Fraction of reads explained by "1++,1--,2+-,2-+": 0.0432
Fraction of reads explained by "1+-,1-+,2++,2--": 0.8740
```

Interpretation:

```text
ABE_EV_2 appears strongly reverse-stranded / first-strand-style.
```

Common equivalent settings:

```text
featureCounts -s 2
HTSeq stranded=reverse
fr-firststrand
```

Caution: this result has only been confirmed for `ABE_EV_2`. Confirm strandedness across all six samples before relying on it as a global library-prep assumption.

## Reference workflow alignment

Steps 04-09 are based on the uploaded/reference RNA-editing workflow:

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

Because Step 03 indicates reverse-stranded / first-strand behavior for `ABE_EV_2`, future steps should document the difference between read orientation labels and biological transcript strand.

## Future artifact and reporting layer

This layer is planned, deferred, and non-runnable. It should not be treated as a new core pipeline step or as a runnable Step 10. The existing Steps 00a-09 remain the core computational pipeline.

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

Future sidecars should use a consistent, versioned JSON schema. The minimum shared fields are expected to include schema version, pipeline version or git commit, run ID, step ID/name, sample ID when applicable, status, timing, inputs, outputs, tool names and versions, resolved parameters, key metrics, warnings, and exit status.

The future aggregation phase should discover or receive expected sidecars, validate schema versions, combine sample-level and run-level information, record missing/failed/incomplete steps explicitly, and write:

```text
results/artifacts/run_summary.json
```

The future report layer should read only structured artifacts and final result tables. It must not require rerunning STAR, samtools, Picard, GATK, bcftools, or CMH computation. It should support multiple renderers from the same underlying data, initially targeting:

```text
results/reports/run_report.html
results/reports/run_report.pdf
results/reports/run_summary.tsv
```

Jinja2 may be a good fit for HTML rendering. Quarto or R Markdown may be useful for publication-quality biological figures and PDF output. The renderer layer should remain replaceable without modifying compute steps.

Step 09 CMH/editing-site results should eventually receive a richer, domain-specific artifact schema rather than being flattened into generic key/value metrics. That schema may include comparison definitions, editing type, filter thresholds, site counts, significant up/down site counts, effect-size summaries, coverage summaries, result-table paths, plot paths, annotation/reference metadata, and multiple-testing method.

## Current next decision

The next validation target is:

```text
Step 04: Picard MarkDuplicates cluster dry-run and execute validation
```

Expected Step 04 input:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Expected Step 04 outputs:

```text
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam
results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai
results/qc/markdup/ABE_EV_2.markdup.metrics.txt
```

Step 04 is implemented as a dry-run-first Picard MarkDuplicates wrapper. It marks duplicates, does not remove them, writes Picard metrics, runs `samtools quickcheck`, and indexes the duplicate-marked BAM.

Before implementing later biological interpretation steps, decide whether to:

1. Continue pipeline development on `ABE_EV_2` through Steps 04-06, or
2. Generalize/run Steps 01-03 across all six samples first.

For development speed, continuing on `ABE_EV_2` is reasonable. For final assumptions, all samples must eventually be checked.

## Local validation gate

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

## Cluster execution pattern

Run from the cluster repo:

```bash
cd ~/norad
git pull
git status --short
mkdir -p logs
```

Dry-run:

```bash
sbatch jobs/<step>.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Check job:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

If shell helpers are installed on the cluster:

```bash
sjcheck <JOBID>
sjtail <JOBID>
sqme
nlogs
```

## Known cluster notes

* `logs/` must exist before `sbatch`.
* Use `TMPDIR=/tmp`.
* The cluster may warn that `/local/tmp` is not writable and fall back to `/tmp`; this has not been fatal.
* `module list` writes to stderr, so scripts should use `module list 2>&1 || true`.
* Known useful modules:

  * `star/2.7.11b`
  * `samtools/1.19.2`
  * `bedtools/2.31.1`
  * `picard/3.1.1`
  * `python39`
  * `java/17.0.10`
* RSeQC is available through the project virtual environment:

  * `.venv/bin/infer_experiment.py`
* GATK availability still needs validation.
