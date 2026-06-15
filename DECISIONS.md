# Decisions

This file records project decisions that should not be casually re-litigated unless new evidence appears.

## TSV Is The Canonical Manifest Format

Decision: the manifest is tab-separated.

Reason: TSV is simple, robust with file paths, easy to parse in Python/R/shell, and avoids CSV quoting issues.

Current manifest:

```text
samples.tsv
```

The manifest is the source of truth for sample IDs, conditions, and FASTQ paths.

## The Workflow Is Local-First And Cluster-Scaled

Decision: develop and test locally, then execute full data jobs on CSU SLURM.

Workflow:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs -> proceed
```

Reason: this keeps large cluster jobs reproducible, reviewable, and gated.

## SLURM Wrappers Are Dry-Run By Default

Decision: pipeline job wrappers default to dry-run mode.

Execute mode must be explicit:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Reason: this prevents accidental large jobs, makes command construction testable, and supports a one-step-at-a-time workflow.

## Script-Level Execution Uses `--execute`

Decision: scripts should print resolved context and commands by default, and only run tool commands when passed `--execute`.

Reason: this keeps behavior consistent between local tests and SLURM wrappers.

## Future Steps Remain Non-Runnable Until Implemented

Decision: scaffolded future steps must be clearly pending/non-runnable.

Pending steps should not look submit-ready. Placeholder jobs should not load modules, call tools, or define realistic resource use until implemented.

Reason: this prevents accidentally submitting placeholder jobs and mistaking scaffolding for working pipeline logic.

## Active Tests Live Under `tests/shell/`; Future Test Plans Live Under `tests/pending/`

Decision: implemented steps get active tests under `tests/shell/`.

Future steps may have comment-only test plans under `tests/pending/`, but pending tests must not be wired into `Makefile` or active test runners.

Reason: this prevents known-failing future tests from breaking current validation while still preserving implementation plans.

## Uploaded Legacy Workflow Is A Protocol Reference

Decision: uploaded old scripts are reference/protocol fossils, not code to run directly.

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

## Use The Novogene-Provided Reference

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

## STAR Index Uses `sjdbOverhang=149`

Decision: build the STAR index with:

```text
sjdbOverhang=149
```

Reason: reads are 150 bp, and STAR convention is read length minus 1.

## BED12 Is Generated From The GTF For RSeQC

Decision: use a generated BED12 annotation for RSeQC strandedness checks.

Output:

```text
refs/novogene_ref/genome.bed
```

Reason: RSeQC `infer_experiment.py` expects BED-style gene/transcript models, not raw GTF.

## GATK Reference Sidecars Are Step 00c

Decision: reference FASTA sidecars are a dedicated Step `00c`, not hidden per-sample Step `05` work.

Expected outputs:

```text
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Reason: `SplitNCigarReads` needs the FASTA index and sequence dictionary, and shared reference files should be prepared and validated once instead of silently created inside per-sample jobs.

Current evidence: an ad hoc cluster prep task generated both sidecars successfully with exit code `0:0`; FAI, DICT, and BAM header contig counts all matched at 194, and the reference/BAM SQ check passed. Step `00c` is implemented locally with a dry-run-first script, SLURM wrapper, reference-level lock, temp-file publication, and shell tests; the formal Step `00c` job is pending cluster validation.

## STAR Outputs Feed Canonical Step 02 BAMs

Decision: even though STAR can output coordinate-sorted BAM directly, Step `02` creates the canonical downstream BAM path.

STAR output example:

```text
results/star/<sample_id>/<sample_id>.Aligned.sortedByCoord.out.bam
```

Canonical Step `02` output:

```text
results/bam/<sample_id>/<sample_id>.sorted.bam
results/bam/<sample_id>/<sample_id>.sorted.bam.bai
```

Reason: downstream steps should depend on a stable canonical path, not STAR-specific output naming.

## Step 02 Enforces Canonical Read-Group Metadata

Decision: Step `02` is the boundary that creates canonical downstream BAMs. Those BAMs must be coordinate sorted, indexed, and carry exactly one read group for the current one-sample-per-BAM contract.

Read-group convention:

```text
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

`LB=<sample_id>` is provisional until true Novogene library, lane, or platform-unit metadata is recovered.

Reason: Picard and downstream tools require records to resolve to a valid `@RG`. Missing read groups caused Picard MarkDuplicates to fail, so Step `04` must not work around missing canonical metadata.

Implementation requirement: Step `02` validates the replacement BAM and index before publishing, uses a per-sample lock, and restores the previous canonical BAM/BAI pair if publication fails after backups begin.

## Step 02 Publication Is Validation-First And Rollback-Protected

Decision: stable canonical BAM and BAI paths are replaced only after temporary replacement files pass validation.

Reason: downstream jobs should never consume a half-published canonical BAM/BAI pair.

## All Six Libraries Are Reverse-Stranded / First-Strand-Style

Decision: all six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.

Confirmed dominant RSeQC orientation group:

```text
1+-,1-+,2++,2--
```

The dominant reverse-stranded orientation ranges from 0.8562 to 0.8740 across the cohort.

Tool-specific examples that commonly correspond to this orientation include:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

Do not present tool-specific options as universally interchangeable without naming the tool.

## Step 03 And Step 04 Are Parallel Consumers Of Canonical Step 02 BAMs

Decision: Step `03` and Step `04` both consume the canonical Step `02` BAM. Step `03` does not require the duplicate-marked BAM from Step `04`.

Reason: strandedness inference depends on the canonical alignment and annotation, not duplicate-marked output.

## Read Orientation Labels Must Be Separated From Biological Strand Interpretation

Decision: future orientation-splitting steps must document the distinction between read orientation labels and biological transcript strand.

Reason: the old workflow used FWD/REV-like read orientation splits, but the cohort is reverse-stranded / first-strand-style.

Old workflow used samtools flags similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Do not silently assume old `FWD` / `REV` labels equal biological sense / antisense.

## Picard Is Invoked Through `$PICARD`

Decision: invoke Picard through the jar path set by the CSU module:

```bash
module load picard/3.1.1
java -jar "$PICARD" <PicardCommand>
```

Reason: CSU exposes Picard as a jar path through the `picard/3.1.1` module rather than as a standalone `picard` executable.

## Step 04 Validates The Actual Java Runtime

Decision: Step `04` must select and validate Java before Picard starts.

Resolution order:

```text
1. JAVA_BIN_OVERRIDE, when explicitly provided
2. $JAVA_HOME/bin/java, only if the path exists and is executable
3. command -v java
```

The wrapper logs `JAVA_HOME`, the selected executable, and the actual `java -version`, then fails before Picard starts if the runtime is below Java 17.

Reason: the cluster has shown inconsistent Java availability across compute nodes, and `JAVA_HOME` or module name alone is not proof of the effective runtime.

## Step 04 Marks Duplicates, Not Removes Them

Decision: Step `04` uses Picard MarkDuplicates with:

```text
REMOVE_DUPLICATES=false
```

Reason: the legacy workflow appears to mark duplicates, and marking preserves reads for downstream inspection while still encoding duplicate status.

Expected Step `04` outputs:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
results/qc/markdup/<sample_id>.markdup.metrics.txt
```

## Node Pinning Is Temporary Mitigation

Decision: pinning Step `04` to `node003` is a temporary operational workaround, not a durable architecture choice.

Reason: `node002` has provided Java 17 and completed the GATK/bcftools probe, `node003` has provided working Java 17 for Step `04`, while `node007` exposed Java 11 and a missing advertised Java 17 `JAVA_HOME`. The durable fix is an HPC-supported cluster-wide Java 17 executable/path or administrator remediation.

Do not copy a JDK from another compute node or from the head node.

## RSeQC Is Run Through The Project Virtual Environment

Decision: Step `03` prefers the project-local RSeQC executable:

```text
.venv/bin/infer_experiment.py
```

Reason: RSeQC was available in the project `.venv`, and relying on it avoids needing a global RSeQC module.

## SLURM Jobs Export `TMPDIR=/tmp`

Decision: SLURM jobs should export/use:

```text
TMPDIR=/tmp
```

Reason: CSU default `/local/tmp` was observed to be non-writable on compute nodes. Jobs may emit a warning and fall back to `/tmp`; this has not been fatal when the job logs show `TMPDIR: /tmp`.

## `logs/` Must Exist Before `sbatch`

Decision: create `logs/` before submitting jobs.

```bash
mkdir -p logs
```

Reason: jobs use `#SBATCH --output=logs/%x-%j.out` and `#SBATCH --error=logs/%x-%j.err`; SLURM can fail if the directory does not exist.

## `module list` Output Should Be Captured With stderr

Decision: scripts should use:

```bash
module list 2>&1 || true
```

Reason: Environment Modules writes `module list` output to stderr, which can otherwise make logs confusing or interact badly with strict shell settings.

## Step 05 Uses The Confirmed GATK Path And Split-N-Cigar Layout

Decision: Step `05` uses the validated CSU GATK path in its SLURM wrapper and writes split-N-cigar outputs under `results/split_ncigar/<sample_id>/`.

Confirmed evidence:

```text
node: node002
Java: OpenJDK 17.0.14
GATK: 4.6.1.0
GATK path: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
tool probe exit code: 0:0
```

Expected outputs:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

Step `05` consumes validated `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` sidecars as prerequisites, fails clearly if they are missing, and must not create shared reference sidecars inside per-sample jobs. It remains pending cluster validation until a SLURM dry-run and execute job are inspected.

## bcftools Path Is Confirmed But Step 07 Is Not Implemented

Decision: use the validated CSU bcftools path when Step `07` is implemented, but keep Step `07` scaffolded / not implemented / not cluster-proven until real script/job behavior and tests exist.

Confirmed evidence:

```text
node: node002
bcftools: 1.21
bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
tool probe exit code: 0:0
```

## R/Rscript Availability Is Not Decided

Decision: do not assume final module names or invocation patterns for R/Rscript until validated on the cluster.

These are needed for Steps `08` and `09`.

## Future Refactors Must Preserve Proven Interfaces

Decision: future helper-library, orchestration, validation-reporting, and admin-utility refactors must preserve existing step command-line interfaces, output paths, dry-run/execute semantics, and proven cluster contracts unless a later task explicitly decides otherwise.

Reason: the current pipeline is intentionally gated and handoff-oriented. Deferred engineering improvements should reduce duplication and improve operability without changing the behavior that downstream steps and cluster runbooks already depend on.

Candidate helper names, config filenames, validator names, Makefile targets, and admin utilities remain roadmap ideas until separately implemented and tested.

## Reporting Is Decoupled From Computation Through Structured Artifacts

Decision: compute steps and report rendering should remain decoupled.

Future pipeline results should be exposed through versioned structured JSON artifacts. Per-step JSON sidecars are planned as a cross-cutting capability, and a future aggregation phase should combine them into:

```text
results/artifacts/run_summary.json
```

`run_summary.json` is intended to become the report layer's single structured input. HTML, PDF, TSV, or other renderers should consume that summary and final result tables without rerunning STAR, samtools, Picard, GATK, bcftools, or CMH computation.

This decision does not require immediate retrofitting of currently implemented steps. Artifact emission, aggregation, and rendering remain planned, deferred, and non-runnable until the core computational workflow is substantially proven.

## Documentation Files Have Different Purposes

Decision: keep documentation roles distinct.

```text
docs/HANDOFF.md        big context handoff / project state
docs/PIPELINE_PLAN.md  tactical step map and validation status
docs/QUESTIONS.md      answered/open project questions
docs/RUNBOOK.md        operational commands and cluster procedure
TROUBLESHOOTING.md     symptom -> cause -> fix
DECISIONS.md           decisions and reasons
TODO.md                tactical next work
README.md              entrypoint / overview
```

Reason: avoids turning one file into an everything-bucket.
