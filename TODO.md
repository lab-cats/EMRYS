# TODO

Current tactical TODOs for the NORAD / Novogene Remora RNA-seq pipeline.

This file is for actionable next work. For broader context, see:

```text
docs/HANDOFF.md
docs/PIPELINE_PLAN.md
docs/QUESTIONS.md
docs/RUNBOOK.md
DECISIONS.md
TROUBLESHOOTING.md
```

## Current State

Cluster-proven:

```text
00a  Build STAR index
00b  Convert GTF to BED12
01   STAR alignment across all six samples
02   Hardened canonical sort/read-group/index BAM across all six samples
02b  BAM QC refreshed across all six final hardened Step 02 BAMs
03   RSeQC strandedness/orientation inference across all six samples
04   Picard MarkDuplicates across all six samples
```

Planned / not implemented:

```text
00c  GATK reference sidecars / reference FASTA index and sequence dictionary
```

Scaffolded and intentionally non-runnable; not cluster-proven:

```text
05   SplitNCigarReads
```

Scaffolded / not implemented / not cluster-proven:

```text
06   Split BAM by read orientation
07   bcftools mpileup
08   VCF preprocessing
09   CMH editing-site calling
```

All six libraries are paired-end and reverse-stranded / first-strand-style.

## Immediate TODOs

### 1. Resolve Java 17 Availability

Work with CSU HPC or cluster documentation to identify one durable Java 17 path:

```text
HPC-supported Java 17 module that works consistently across nodes
administrator-provided cluster-wide Java 17 path
explicit verified executable supplied through JAVA_BIN_OVERRIDE
administrator remediation of inconsistent node images
```

Temporary node pinning to `node003` is operational mitigation, not architecture.

Do not copy a JDK from the head node or another compute node.

### 2. Inspect And Implement Step 05

Step `05` remains scaffolded and intentionally non-runnable; not cluster-proven.

Needs:

```text
confirmed GATK invocation path
duplicate-marked BAM
reference FASTA
FASTA .fai
sequence dictionary .dict
Step 00c sidecar validation
processed-BAM output layout decision
local tests / dry-run behavior
SLURM wrapper validation
```

Current Step `05` scaffold files intentionally exit with code `2`, print that Step `05` is not implemented, and perform no analysis. The old `sorted.md.bam` and `sorted.md.splitncigar.bam` scaffold path examples are stale and not current interfaces.

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`.

Before Step `05`, formalize Step `00c` so it creates and validates:

```text
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

The sidecars already exist from an ad hoc cluster prep task that completed with exit code `0:0`; FAI, DICT, and BAM header contig counts all matched at 194, and the reference/BAM SQ check passed. Step `05` should treat these files as prerequisites, fail clearly if they are missing, and must not silently create shared reference sidecars inside per-sample jobs.

## Architecture Reminders

### Design Manifest-Driven Sample Selection Helpers

The next orchestration piece is manifest-driven sample selection for SLURM arrays or targeted per-sample runs.

Eventually needed:

```bash
scripts/get_manifest_row.py \
  --manifest samples.tsv \
  --row "$SLURM_ARRAY_TASK_ID"
```

or:

```bash
scripts/get_sample_from_manifest.py \
  --manifest samples.tsv \
  --sample-id ABE_EV_2
```

Purpose:

```text
Allow SLURM array task N to select sample N from samples.tsv.
Allow explicit single-sample reruns without hardcoding sample IDs in wrappers.
```

Do not overbuild this before the relevant per-step behavior is proven. Revisit before broader cohort-scale reruns or downstream array execution.

### Decide Durable Processed-BAM Output Layout

Current likely layout:

```text
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt

results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai

results/orientation/<sample>/<sample>.<orientation>.bam
results/orientation/<sample>/<sample>.<orientation>.bam.bai
```

Confirm this before implementing Steps `05` and `06` too deeply.

## External Blockers / Unresolved Items

### R / Rscript Availability

Still unresolved.

Needed for:

```text
Step 08: VCF preprocessing
Step 09: CMH editing-site calling
```

### Storage Quotas

Still unresolved.

Need to document:

```text
home quota
/mnt/stor-pool-01/users/2609214 quota
scratch availability
whether temp files should use scratch or /tmp
```

### Exact Annotation Version

Partially unresolved.

Known:

```text
Reference came from Novogene 04.Ref delivery.
Genome is GRCh38-like.
Chromosome names are numeric-style.
```

Still need:

```text
Exact annotation release/version if recoverable from files or Novogene docs.
```

## Later TODOs

### Step 06: Split BAM By Read Orientation

Old workflow used samtools flag groupings similar to:

```text
FWD-like: 99 and 147
REV-like: 83 and 163
```

Important:

```text
Do not assume old FWD/REV labels equal biological sense/antisense.
The cohort is reverse-stranded / first-strand-style.
```

Step `06` must clearly document read orientation versus transcript strand.

### Step 07: bcftools mpileup

Needs decisions:

```text
use confirmed bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
chromosome/region handling
reference FASTA path
per-sample vs grouped mpileup strategy
FWD/REV or orientation-specific output naming
```

### Step 08: VCF Preprocessing

Port from uploaded `vcf_preprocess1.R`.

Needs:

```text
remove hardcoded paths
make CLI-driven
make manifest-driven where appropriate
document strand/orientation assumptions
define output table format
```

### Step 09: CMH Editing-Site Calling

Port from uploaded `Edit_call_cmh.R`.

Needs:

```text
remove hardcoded paths
define expected input tables
define comparison structure
define final output tables/plots
document statistical assumptions
```

## Deferred Roadmap: Structured Artifacts And Reporting

This work should begin only after the core computational workflow is substantially proven. It is planned, deferred, and non-runnable for now. Do not create schema files, placeholder scripts, templates, report directories, sidecar files, or SLURM jobs until this roadmap is explicitly activated.

Deferred phases:

```text
A. Define and version the artifact schema.
B. Add shared artifact-writing utilities.
C. Retrofit proven steps to emit sidecars.
D. Define the richer CMH/editing-site artifact schema.
E. Aggregate sidecars into run_summary.json.
F. Implement HTML reporting.
G. Add PDF and TSV renderers.
```

## Resolved Items

Resolved:

```text
Build STAR reference index.
Convert annotation to BED12.
Generate GATK reference sidecars as an ad hoc cluster prep task.
Align all six samples.
Harden Step 02.
Add sample-specific read groups.
Validate Step 02 across all six samples.
Determine strandedness.
Confirm strandedness across all six samples.
Confirm ABE_EV_2 Step 03 output remains unchanged after Step 02 hardening.
Refresh Step 02b across all six final hardened Step 02 BAMs.
Implement Step 04.
Prove Step 04 on ABE_EV_2.
Prove Step 04 across all six samples.
Compare Step 04 duplication metrics across all six samples.
Confirm GATK availability on node002.
Confirm bcftools availability on node002.
```

## Development Rule

Do not jump ahead.

Continue using:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs -> proceed
```

A TODO is not done until the relevant outputs have been inspected and the docs are updated.
