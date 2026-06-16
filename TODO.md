# TODO

Current tactical TODOs for the NORAD / Novogene Remora RNA-seq pipeline.

This file is for actionable next work. For broader context, see:

```text
docs/operations/HANDOFF.md
docs/design/PIPELINE_PLAN.md
docs/design/QUESTIONS.md
docs/operations/RUNBOOK.md
docs/design/ decision records
docs/operations/ troubleshooting guide
```

## Current State

Cluster-proven:

```text
00a  Build STAR index
00b  Convert GTF to BED12
00c  GATK reference sidecars / reference FASTA index and sequence dictionary
01   STAR alignment across all six samples
02   Hardened canonical sort/read-group/index BAM across all six samples
02b  BAM QC refreshed across all six final hardened Step 02 BAMs
03   RSeQC strandedness/orientation inference across all six samples
04   Picard MarkDuplicates across all six samples
05   SplitNCigarReads across all six samples
06   Read-orientation BAM split across all six samples
```

Scaffolded / not implemented / not cluster-proven:

```text
07   bcftools mpileup
08   VCF preprocessing
09   CMH editing-site calling
```

All six libraries are paired-end and reverse-stranded / first-strand-style.

## Immediate TODOs

### 1. Implement Step 07 bcftools mpileup

Step `06` is cluster-proven across all six samples and publishes the orientation-specific BAM/BAI inputs for Step `07`:

```text
results/orientation/<sample>/<sample>.FWD_like.bam
results/orientation/<sample>/<sample>.FWD_like.bam.bai
results/orientation/<sample>/<sample>.REV_like.bam
results/orientation/<sample>/<sample>.REV_like.bam.bai
results/qc/orientation/<sample>.orientation_counts.tsv
```

Preserve the legacy mechanical read-orientation flag groups:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

Preserve the normal gate:

```text
local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs
```

Implement Step `07` narrowly before full-cohort execution. Do not implement Steps `08`-`09` until Step `07` behavior is proven.

## Architecture Reminders

### Durable Processed-BAM Output Layout

Current likely layout:

```text
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt

results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai

results/orientation/<sample>/<sample>.FWD_like.bam
results/orientation/<sample>/<sample>.FWD_like.bam.bai
results/orientation/<sample>/<sample>.REV_like.bam
results/orientation/<sample>/<sample>.REV_like.bam.bai
results/qc/orientation/<sample>.orientation_counts.tsv
```

The Step `05` and Step `06` portions of this layout are now implemented and cluster-proven across all six samples. Continue to treat `FWD_like` / `REV_like` as mechanical read-orientation groups, not biological strand calls.

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

### Read-Orientation Interpretation Caution

Old workflow used samtools flag groupings similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

Important:

```text
Do not assume `FWD_like` / `REV_like` labels equal biological sense/antisense.
The cohort is reverse-stranded / first-strand-style.
samtools view -f FLAG means has all bits in FLAG, not exact flag equality.
```

Step `06` is cluster-proven across all six samples. Downstream Steps `07`-`09` must continue to document read-orientation/mechanical flag groups without making unsupported transcript-strand claims.

### Step 07: bcftools mpileup

Needs decisions:

```text
use confirmed bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
chromosome/region handling
reference FASTA path
per-sample vs grouped mpileup strategy
FWD_like/REV_like or other read-orientation-specific output naming
```

### Step 08: VCF Preprocessing

Port from uploaded `vcf_preprocess1.R`.

Needs:

```text
remove hardcoded paths
make CLI-driven
make manifest-driven where appropriate
document read-orientation assumptions without unsupported biological strand claims
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

## Deferred Roadmap: Engineering Improvements

These are deferred engineering improvements and roadmap ideas. They do not block Step `05` or the remaining compute pipeline. Do not create schemas, helper libraries, validators, Makefile targets, config files, JSON sidecars, cleanup utilities, report templates, report directories, or new SLURM jobs until a roadmap item is explicitly activated.

Deferred architecture: evaluate separating the reusable preprocessing backbone from assay-specific analysis modules and a reporting layer. First reproduce the legacy Steps `07`-`09` workflow, then decide whether to formalize modules such as `rna_editing_cmh`, manifest/config contracts, artifact indexes, report generation, and possible public-dataset import support.

### After Steps 00c-09 Are Proven

These items belong after the full compute path is substantially proven:

* Add manifest-driven submission and validation helpers for targeted sample reruns and later cohort-scale execution. Possible future helpers include `scripts/submit_step.sh --step ... --manifest ...` and `scripts/validate_step.sh --step ... --manifest ...`, but their names and interfaces are not decided.
* Add SLURM job-array support only after single-sample behavior is stable and manifest-driven sample lookup is clear.
* Add an environment/tool probe step for STAR, samtools, bedtools, Picard, Java, GATK, bcftools, R/Rscript, required R packages, and Python/RSeQC. This should be a preflight report, not a replacement for per-step validation.
* Add reference provenance and checksum tracking for `genome.fa`, `genome.gtf`, `genome.bed`, the STAR index, `genome.fa.fai`, and `genome.dict` to reduce reference mismatch risk.
* Define output retention and cleanup policy for raw FASTQs, STAR BAMs, canonical BAMs, markdup BAMs, split-N-cigar BAMs, pileups/VCFs, temp files, backups, and logs.
* Add standardized validation reports after the existing per-step validation behavior is stable. Decide later whether these are per-step validators, a generic dispatcher, or both.

### Reporting And Artifact Layer

This layer remains planned, deferred, and non-runnable. It should not be implemented until the core compute workflow is substantially proven.

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

Roadmap ideas:

* Future per-step JSON sidecars may eventually record command context, inputs, outputs, tool versions, runtime, node, validation results, and metrics.
* A future aggregation layer may combine sidecars into `results/artifacts/run_summary.json`.
* Future cohort QC summary tables may include alignment, strandedness, and duplication summaries for handoff and sanity checks.
* Future demo/reporting artifacts may include HTML/PDF summaries, but report generation should remain decoupled from compute steps.

### Later Maintainability And Refactor Work

These are refactor candidates, not active implementation requirements:

* Consider shared shell helper libraries only after behavior is covered by tests and outputs are stable. Candidate future files include `scripts/lib/norad_common.sh` and `scripts/lib/norad_slurm_common.sh`.
* Candidate shared helpers include repo-root detection, strict-mode/logging conventions, dry-run/execute handling, tool resolution and version logging, Java runtime validation, common file/path validation, lock handling, temp-path cleanup traps, samtools quickcheck/index validation, standardized error messages, and SLURM job context logging.
* Future helper-library refactors must preserve existing step CLIs, output paths, dry-run/execute semantics, and proven cluster contracts.
* Expand shell coverage only after inspecting the current `Makefile`, `tests/shell/`, and `tests/pending/`. In this checkout, `make shell-test` wires Step `00c` and Steps `01`-`05`, while no Step `00a` or Step `00b` shell test exists under `tests/shell/` or `tests/pending/`; adding Step `00a` / `00b` shell coverage is deferred future work.
* Keep active runnable tests under `tests/shell/` and non-runnable future test plans under `tests/pending/`.
* Possible future Makefile targets may include validation/reporting conveniences, but do not add targets until the underlying commands exist and are stable.

### Long-Term Handoff And Admin Utilities

These ideas are for later handoff and maintenance:

* Decide whether a cluster tool-path config file is useful. Candidate names and variables are not decided; scripts should remain portable through CLI/env overrides.
* Add a compact failure taxonomy or troubleshooting index that maps symptom to likely cause, confirmation command, and fix once enough repeated failures exist.
* Consider conservative stale-lock inspection and cleanup utilities after lock behavior is stable and safety rules are documented.
* Keep any admin utility cautious by default; do not delete or repair shared outputs without explicit operator intent.

## Resolved Items

Resolved:

```text
Build STAR reference index.
Convert annotation to BED12.
Generate GATK reference sidecars as an ad hoc cluster prep task.
Prove formal Step 00c GATK reference sidecar preparation on the cluster.
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
Implement Step 05 locally with dry-run-first GATK SplitNCigarReads script, SLURM wrapper, and shell tests.
Harden Step 05 GATK temp handling to use project-storage per-run temp space.
Harden Step 05 failure cleanup for owned temp files, sidecars, temp directories, and locks.
Prove Step 05 across all six samples.
Implement Step 06 locally with dry-run-first read-orientation splitting.
Prove Step 06 across all six samples.
```

## Development Rule

Do not jump ahead.

Continue using:

```text
implement locally -> local tests -> commit/push -> pull on cluster -> dry-run -> execute -> inspect outputs -> update docs -> proceed
```

A TODO is not done until the relevant outputs have been inspected and the docs are updated.
