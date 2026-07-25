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
stage branch
-> local implementation and validation
-> implementation commit
-> repository-wide docpatch and documentation-only commit
-> clean status/history and push
-> next descendant local stage
-> upstream-first cluster dry-run and execute promotion
-> inspected evidence and validation docpatch
```

Reason: this keeps large cluster jobs reproducible, reviewable, and gated.

## Major Stages Use Descendant Branches And Documentation Gates

Decision: each major implementation or validation stage must use a dedicated
branch created from the latest clean, docpatched parent branch.

The completion gate is:

```text
implement only the stage and its required contracts
-> run focused tests and the complete repository validation gate
-> commit implementation and tests
-> reread the nine required project documents
-> perform a repository-wide documentation consistency pass
-> commit documentation separately as "step NN docpatch"
-> rerun diff/status/history checks and require a clean worktree
-> push the completed stage branch
-> create the next descendant branch
```

If implementation changes after a docpatch, the gate reopens: retest, commit
the fix, and add another separate documentation-only commit before branching.
Any inserted work package follows the same pattern on a sequentially named
descendant branch.

Documentation must distinguish:

```text
implemented locally
locally tested
runtime validation blocked
cluster dry-run validated
cluster-proven
```

Only inspected cluster evidence can support a `cluster-proven` claim.

Reason: linear stage ancestry plus a documentation-only gate makes the state,
interfaces, evidence, and remaining validation requirements reviewable at every
handoff boundary.

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

Current application: Steps `08` and `09` remain pending and non-runnable.
Step `07` is implemented locally and locally tested, but is not yet
cluster-proven.

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

Current evidence: an ad hoc cluster prep task generated both sidecars successfully with exit code `0:0`; FAI, DICT, and BAM header contig counts all matched at 194, and the reference/BAM SQ check passed. Step `00c` is implemented with a dry-run-first script, SLURM wrapper, reference-level lock, temp-file publication, and shell tests; the formal Step `00c` job is cluster-proven.

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

Decision: future orientation-splitting steps must document the distinction between read-orientation labels, mechanical flag groups, and biological interpretation.

Reason: the old workflow used FWD/REV-like read orientation splits, but the rebuilt pipeline should preserve them as `FWD_like` / `REV_like` mechanical flag groups because the cohort is reverse-stranded / first-strand-style.

Old workflow used samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

`samtools view -f FLAG` means a read has all bits in `FLAG`, not exact flag equality. Do not silently assume `FWD_like` / `REV_like` labels equal biological sense / antisense, transcript strand, or biological strand.

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

## Step 05 GATK Temp Files Use Project Storage

Decision: Step `05` must route GATK `SplitNCigarReads` Java/HTSJDK temp files to a per-run project-storage temp directory, not node-local `/tmp`.

Required mechanism:

```text
--java-options -Djava.io.tmpdir=<project temp dir>
--tmp-dir <project temp dir>
TMPDIR=<project temp dir> for the GATK process
```

Reason: GATK/HTSJDK `SortingCollection` spill files can exceed safe node-local `/tmp` capacity during `SplitNCigarReads`. Project-storage temp space keeps large temporary spill files with the pipeline run instead of relying on node-local scratch capacity.

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

Step `05` consumes validated `refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict` sidecars as prerequisites, fails clearly if they are missing, and must not create shared reference sidecars inside per-sample jobs. It is cluster-proven across all six samples after final BAM/BAI output inspection.

## Step 07 Is A Cohort-Wide, Manifest-Partitioned mpileup

Decision: Step `07` runs every sample in manifest order together for one
declared partition and publishes both neutral mechanical orientations:

```text
FWD_like
REV_like
```

The analysis partition manifest is the declared correction universe and has the
schema:

```text
partition_id    selector_type    selector_value
```

`region` maps to bcftools `-r`; `regions_file` maps to `-R`. Pilots use a
separate one-row manifest rather than changing the approved full-analysis
manifest.

Step `07` preserves these legacy mpileup/filter defaults:

```text
maximum depth: 10000000
skip indels
FORMAT annotations: DP, AD, ADF, ADR, SP
INFO annotations: AD, ADF, ADR
filter: INFO/AD[1-]>2 & MAX(FORMAT/DP)>20
plain VCF output
no bcftools call stage
```

Reason: cohort-wide multi-BAM mpileup preserves the manifest-defined sample
universe and order for downstream paired analysis, while explicit partition
manifests prevent accidental glob-based changes to the multiple-testing
universe. Neutral orientation names avoid claiming biological strand meaning.

## Step 07 Publishes VCFs Atomically With A Receipt Commit Marker

Decision: one Step `07` transaction owns the cohort/partition output scope,
validates both orientation VCFs, and publishes the receipt last.

Expected paths:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

The receipt records the cohort, partition selector, orientation, VCF path,
manifest hashes, manifest sample count, and VCF record count. Its presence is
the transaction commit marker. Header-only VCFs are valid when their structure
and exact manifest-ordered sample columns pass validation.

Reason: publishing the receipt last prevents downstream steps from accepting a
partial pair of VCFs as a complete partition. Owned locks, run-token scratch
paths, validation-before-publication, rollback, and cleanup preserve the
reliability contract established by Steps `05` and `06`.

## The Confirmed bcftools Path Is The Step 07 Cluster Default

Decision: use the validated CSU bcftools path as the Step `07` SLURM-wrapper
default:

Confirmed evidence:

```text
node: node002
bcftools: 1.21
bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
tool probe exit code: 0:0
```

Current status: Step `07` is implemented locally and locally tested with mocked
bcftools. It has not run against real bcftools on this workstation, has not
completed a cluster dry-run or execute job, has no inspected cluster output,
and is not cluster-proven. The tracked primary-contig manifest includes `MT`;
its exact presence/spelling in the Novogene FASTA index must be confirmed
during cluster dry-run validation.

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
docs/operations/       handoff, runbook, and troubleshooting
docs/design/           pipeline plan, questions, and decisions
docs/demo/             PI demo walkthrough and report
docs/architecture/     visual pipeline/dataflow architecture and diagrams
TODO.md                tactical next work
README.md              entrypoint / overview
```

Reason: avoids turning one file into an everything-bucket.
