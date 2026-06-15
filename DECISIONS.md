# Decisions

This file records project decisions that should not be casually re-litigated unless new evidence appears.

## TSV is the canonical manifest format

Reason: TSV is simple, robust with file paths, easy to parse in Python/R/shell, and avoids CSV quoting issues.

Current manifest:

```text
samples.tsv
```

The manifest is the source of truth for sample IDs, conditions, and FASTQ paths.

## The workflow is local-first and cluster-scaled

Decision: develop and test locally, then execute full data jobs on CSU SLURM.

Workflow:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> proceed
```

Reason: this keeps large cluster jobs reproducible, reviewable, and gated.

## SLURM wrappers are dry-run by default

Decision: pipeline job wrappers default to dry-run mode.

Execute mode must be explicit:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Reason: prevents accidental large jobs, makes command construction testable, and supports a one-step-at-a-time workflow.

## Script-level execution uses `--execute`

Decision: scripts should print resolved context and commands by default, and only run tool commands when passed `--execute`.

Reason: keeps behavior consistent between local tests and SLURM wrappers.

## Future steps remain non-runnable until implemented

Decision: scaffolded future steps must be clearly pending/non-runnable.

Pending steps should not look submit-ready. Placeholder jobs should not load modules, call tools, or define realistic resource use until implemented.

Reason: prevents accidentally submitting placeholder jobs and mistaking scaffolding for working pipeline logic.

## Reporting is decoupled from computation through structured artifacts

Decision: compute steps and report rendering should remain decoupled.

Future pipeline results should be exposed through versioned structured JSON artifacts. Per-step JSON sidecars are planned as a cross-cutting capability, and a future aggregation phase should combine them into:

```text
results/artifacts/run_summary.json
```

`run_summary.json` is intended to become the report layer's single structured input. HTML, PDF, TSV, or other renderers should consume that summary and final result tables without rerunning STAR, samtools, Picard, GATK, bcftools, or CMH computation.

Reason: reports should be reproducible and replaceable without changing or rerunning the computational pipeline.

This decision does not require immediate retrofitting of currently implemented steps. Artifact emission, aggregation, and rendering remain planned, deferred, and non-runnable until the core computational workflow is substantially proven.

## Active tests live under `tests/shell/`; future test plans live under `tests/pending/`

Decision: implemented steps get active tests under `tests/shell/`.

Future steps may have comment-only test plans under `tests/pending/`, but pending tests must not be wired into `Makefile` or active test runners.

Reason: prevents known-failing future tests from breaking current validation while still preserving implementation plans.

## Uploaded legacy workflow is a protocol reference, not production code

Decision: uploaded old scripts are treated as reference/protocol fossils, not code to run directly.

Reason: the old workflow is hardcoded and not manifest-driven. This repo is rebuilding the workflow into a cleaner SLURM/script/testable structure.

The reference workflow informs Steps `04` through `09`:

```text
MarkDuplicates
-> SplitNCigarReads
-> split BAM by read orientation
-> bcftools mpileup
-> VCF preprocessing
-> CMH editing-site calling
```

## Use the Novogene-provided reference for this rebuild

Decision: use the Novogene-provided reference FASTA/GTF as the reference basis for this pipeline unless there is a strong reason to change.

Prepared reference paths:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_star_index/
```

Reason: the data delivery and original workflow were built around this reference. Using it avoids coordinate/name mismatches.

Known reference behavior:

```text
chromosome names are numeric-style, e.g. 1, 2, 3
not chr1, chr2, chr3
```

## STAR index uses `sjdbOverhang=149`

Decision: build the STAR index with:

```text
sjdbOverhang=149
```

Reason: reads are 150 bp, and STAR convention is read length minus 1.

## BED12 is generated from the GTF for RSeQC

Decision: use a generated BED12 annotation for RSeQC strandedness checks.

Output:

```text
refs/novogene_ref/genome.bed
```

Reason: RSeQC `infer_experiment.py` expects BED-style gene/transcript models, not raw GTF.

## STAR writes coordinate-sorted BAMs, but Step 02 still creates canonical BAMs

Decision: even though STAR can output coordinate-sorted BAM directly, Step `02` still creates a canonical downstream BAM path.

STAR output example:

```text
results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam
```

Canonical Step 02 output:

```text
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam
results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai
```

Reason: downstream steps should depend on a stable canonical path, not STAR-specific output naming.

## `ABE_EV_2` is the current development/validation sample

Decision: develop and validate new steps on `ABE_EV_2` first.

Reason: one-sample validation keeps cluster iteration fast and makes failures easier to debug.

Caution: final workflow assumptions must eventually be validated across all six samples.


## Step 02 canonical BAMs must be coordinate-sorted, indexed, and carry calid read-group materials

provisional convention:

```
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

Picard requires records to resolve to an `@RG`, and step 02 is the enforcement boundary.

## Step 03 result indicates reverse-stranded / first-strand behavior for `ABE_EV_2`

Decision: record the Step `03` result as strong evidence that `ABE_EV_2` is reverse-stranded / first-strand-style.

Observed RSeQC output:

```text
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

Caution: do not treat this as a global library assumption until Step `03` has been run on all six samples.

## Read orientation labels must be separated from biological strand interpretation

Decision: future orientation-splitting steps must document the distinction between read orientation labels and biological transcript strand.

Reason: the old workflow used FWD/REV-like read orientation splits, but Step `03` indicates reverse-stranded / first-strand library behavior for `ABE_EV_2`.

Old workflow used samtools flags similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Do not silently assume old `FWD` / `REV` labels equal biological sense / antisense.

## Picard is invoked through `$PICARD`

Decision: invoke Picard through the jar path set by the CSU module:

```bash
module load picard/3.1.1
java -jar "$PICARD" <PicardCommand>
```

Reason: CSU exposes Picard as a jar path through the `picard/3.1.1` module rather than as a standalone `picard` executable.

Known module behavior:

```text
picard/3.1.1 loads java/17.0.10
PICARD=/cm/shared/apps/picard/picard/build/libs/picard.jar
```

## Step 04 should mark duplicates, not remove them

Decision: Step `04` should use Picard MarkDuplicates to mark duplicates, not remove them, unless a future reason is explicitly documented.

Reason: the legacy workflow appears to mark duplicates, and marking preserves reads for downstream inspection while still encoding duplicate status.

Expected Step `04` outputs:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
results/qc/markdup/<sample_id>.markdup.metrics.txt
```

## RSeQC is run through the project virtual environment

Decision: Step `03` prefers the project-local RSeQC executable:

```text
.venv/bin/infer_experiment.py
```

Reason: RSeQC was available in the project `.venv`, and relying on it avoids needing a global RSeQC module.

## SLURM jobs export `TMPDIR=/tmp`

Decision: SLURM jobs should export/use:

```text
TMPDIR=/tmp
```

Reason: CSU default `/local/tmp` was observed to be non-writable on compute nodes. Jobs may emit a warning and fall back to `/tmp`; this has not been fatal when the job logs show `TMPDIR: /tmp`.

Execute jobs should use:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

## `logs/` must exist before `sbatch`

Decision: create `logs/` before submitting jobs.

```bash
mkdir -p logs
```

Reason: jobs use `#SBATCH --output=logs/%x-%j.out` and `#SBATCH --error=logs/%x-%j.err`; SLURM can fail if the directory does not exist.

## `module list` output should be captured with stderr

Decision: scripts should use:

```bash
module list 2>&1 || true
```

Reason: Environment Modules writes `module list` output to stderr, which can otherwise make logs confusing or interact badly with strict shell settings.

## GATK availability is not decided

Decision: do not implement Step `05` until GATK availability is resolved.

Known issue:

```bash
module avail gatk
```

did not reveal a visible GATK module.

Possible future options:

```text
different module name
jar
conda/mamba environment
container
project-local install
```

## R/Rscript and bcftools availability are not decided

Decision: do not assume final module names or invocation patterns for R/Rscript or bcftools until validated on the cluster.

These are needed for Steps `07`, `08`, and `09`.

## Documentation files have different purposes

Decision: keep documentation roles distinct.

```text
docs/HANDOFF.md        big context handoff / project state
docs/PIPELINE_PLAN.md  tactical step map and validation status
docs/QUESTIONS.md      answered/open project questions
docs/RUNBOOK.md        operational commands and cluster procedure
DECISIONS.md           decisions and reasons
```

Reason: avoids turning one file into an everything-bucket.
