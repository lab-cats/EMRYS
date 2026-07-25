# TODO

Current tactical TODOs for the NORAD / Novogene Remora RNA-seq pipeline.

This file is for actionable next work. For broader context, see:

```text
docs/operations/HANDOFF.md
docs/design/PIPELINE_PLAN.md
docs/design/QUESTIONS.md
docs/operations/RUNBOOK.md
docs/design/DECISIONS.md
docs/operations/TROUBLESHOOTING.md
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

Implemented locally and locally tested, but not fully runtime-validated or cluster-proven:

```text
07   Cohort bcftools mpileup by declared partition and mechanical orientation
08   Deterministic VCF preprocessing and annotation
09   Paired CMH editing-site calling
```

The active Step `07` shell suite uses a fake bcftools executable. Real bcftools is unavailable on this workstation, and no Step `07` cluster dry-run, execute run, or output evidence has been inspected.

The active Step `08` shell suite uses a fake `Rscript` to test the wrapper and
publication boundary. Its real-R fixture suite is implemented, but `Rscript`
is unavailable on this workstation, so semantic R execution remains pending.
No Step `08` cluster dry-run, execute run, or output evidence has been
inspected.

Step `09` is implemented locally at implementation commit `e4371de`. Its
shell/fake-R suite covers pairing, the Step `08` sites/input-receipt contract,
threshold/output validation, dry-run behavior, locks, cleanup, and rollback.
Its real-R fixture suite is implemented, but `Rscript` is unavailable on this
workstation, so it reports `SKIP`; this is not semantic R validation. No Step
`09` cluster dry-run, execute run, log, or output evidence has been inspected.

All six libraries are paired-end and reverse-stranded / first-strand-style.

## Immediate TODOs

The Step `09` implementation/docpatch gate is complete at `9ac8307`.
`step-09a-roadmap-docpatch` records this reconciled roadmap and is the required
clean/pushed base for the next runtime branch; it has no implementation or
runtime claim of its own.

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

Steps `07`-`09` have implementation commits, active local tests, separate
docpatch commits, clean histories, and pushed branches. A documentation-only
package uses one docs commit plus validation/clean/push; it never fabricates an
implementation commit.

Required lineage:

```text
step-09-cmh
└── step-09a-roadmap-docpatch
    └── validate-step-07
        └── validate-step-08
            └── validate-step-09
                └── step-09b-scientific-validation
```

### 1. Establish The Runtime Promotion Preconditions

Before any Step `07` cluster dry-run:

1. Locate or deliberately provision the full cluster `samples.tsv`. It is
   absent from this Git checkout, and the cluster-local copy has not been
   inspected.
2. Add the approved explicit replicate `2`, `3`, and `4` values to that
   six-row manifest. Validate it, record its SHA-256, and keep the exact same
   bytes/hash through Steps `07`-`09`; the tracked pairing reference is not a
   runtime overlay.
3. Resolve a compute-node-visible `Rscript`, the Step `08` Bioconductor
   packages, and `sha256sum` or `shasum`. Run both real-R fixture suites in
   that same supported environment before promotion.
4. Verify the clean cluster checkout, `logs/`, all 12 Step `06` orientation
   BAM/BAI pairs, the Novogene FASTA/FAI, primary-contig selectors including
   `MT`, bcftools `1.21`, available storage/quota, and the provisional
   eight-hour/one-CPU request.

If this resolution requires tracking or changing repository manifest/config
content, create `step-07a-runtime-manifest` (or the approved sequential
inserted-package name) from `step-09a-roadmap-docpatch`, commit the config/
validation change, docpatch, clean, and push. Then create `validate-step-07`
from that branch. If the durable runtime file is a byte-identical cluster-local
copy, record its path/hash as validation evidence without fabricating an
implementation commit.

### 2. Promote Step 07 On `validate-step-07`

Run and inspect, in order:

1. pilot dry-run;
2. pilot execute;
3. chromosome `1` dry-run;
4. chromosome `1` execute;
5. each of the remaining 24 primary partitions explicitly.

Record pilot/chromosome-1 runtime and VCF size and use them to estimate
remaining storage before the production fan-out. Do not add a dispatcher or
job array.

Exit only with 25 primary receipts and 50 structurally valid primary VCFs,
exact six-sample order, identical manifest hashes throughout, reconciled
record counts, `COMPLETED 0:0` jobs, inspected logs/outputs, and no owned lock
or run-token scratch residue. The separate `pilot_1` transaction is
validation-only and never enters the primary correction universe. Commit the
evidence/status docpatch, require clean status/history, and push before Step
`08`.

### 3. Promote Step 08 On `validate-step-08`

Require the supported environment to pass both real-R fixture suites. Inspect
one successful dry-run and execute transaction over exactly 25 partitions by
two orientations. Exit only with three valid outputs, exactly 50 input-receipt
rows in partition order with `FWD_like` then `REV_like`, matching hashes and
sample columns, unique candidate IDs, reconciled observed/supported/skipped/
published counts, `COMPLETED 0:0`, and no owned lock or scratch residue.
Docpatch, clean, and push before Step `09`.

### 4. Promote Step 09 On `validate-step-09`

The dry-run must show the three explicit replicate pairs, current upstream
hashes, and frozen default thresholds. Execute once with background disabled.
Exit only with `COMPLETED 0:0`, six reconciled outputs, all-sites row count
equal to Step `08` candidates, the exact ordered rows whose `call_status` is
`significant_up` or `significant_down`, one summary row, 12 mutation-spectrum
rows, valid PDF `%PDF-`/`%%EOF` markers, and no lock/scratch residue. Docpatch,
clean, and push. This can establish
computational cluster proof; it cannot biologically validate
`legacy_provisional_v1`.

### 5. Run The Post-Step-09 Scientific Gate

Create `step-09b-scientific-validation` from the clean, pushed
`validate-step-09` branch. This is an evidence-and-decision package, not a
runnable Step `10`.

Required evidence:

* independently validate read flags, transcript strand, genomic/RNA alleles,
  and raw counts at predeclared plus-strand and minus-strand transcript loci;
  compare the current and inverted normalization policies. A>G enrichment is
  supporting evidence only, not proof;
* record the Novogene GTF path/identity/SHA-256 and delivery provenance; record
  the exact release if recoverable, otherwise retain it as an accepted
  unresolved limitation; audit predeclared CDS, UTR, exon, intron, intergenic,
  overlapping-gene, and multi-transcript cases;
* reconcile the production funnel from Step `07` records through Step `08`
  exclusions and Step `09` statuses by partition/orientation;
* freeze the legacy defaults, predeclare sensitivity analyses, review
  per-replicate AF/delta and leave-one-pair-out results, and explicitly review
  the unweighted mean-sample-AF effect metric, `ABE_EV_2` mapping behavior,
  replicate `4` duplication, and replicate-direction discordance;
* adjudicate deterministic top, discordant, and near-threshold candidate sets
  for coverage, quality/bias, splice/repeat/multimapping/duplicate/indel,
  annotation, and polymorphism concerns;
* decide whether a genuine distinct comparable background cohort exists. EV
  is not no-dox. Adding one changes the manifest hash and reopens Steps
  `07`-`09`.

Before viewing concordance/candidate rankings, freeze deterministic selection,
sample size, both orientations and plus/minus transcript-strand coverage, the
sensitivity grid/decision thresholds, input hashes, git commit,
commands/scripts/software versions, reviewer/date/owner, and
current/superseded analysis IDs. Sensitivity and leave-one-pair-out runs use
distinct analysis IDs and never overwrite the primary transaction; any
testability/family change recomputes BH.

The evidence package should include compact audit/threshold/leave-one-out/
adjudication TSVs in approved results storage. The docpatch records compact
non-sensitive summaries, paths, and hashes; do not commit production-derived
biological TSV snapshots without explicit approval.
Record `science_review_complete_exploratory` when review is complete but
results remain provisional. Record `biological_interpretation_ready` only with
a validated orientation policy plus accepted annotation provenance/
limitations, approved primary thresholds, reviewed replicate sensitivity,
candidate adjudication, and background/matched-DNA decisions.

Rerun rules:

```text
manifest or partition universe -> gated config/evidence package, then Steps 07-09
Step 07 filter or maximum depth
  -> contract/versioning decision plus distinct namespace or added provenance,
     then Steps 07-09
new background samples -> prove their Steps 01-06 inputs, then Steps 07-09
existing unchanged Step 08 background columns -> new Step 09 analysis ID
GTF input -> Steps 08-09
orientation normalization policy
  -> Steps 08-09 contract/code/tests/docpatch, then Steps 08-09 runtime
supported Step 09 target/unchanged-manifest contrast/background/min-DP/defaults
  -> new Step 09 analysis ID and full applicable-family BH
CMH method/correction or testability logic
  -> Step 09 implementation/tests/docpatch, then new-ID runtime validation
FASTA/coordinate change -> upstream reference/alignment impact review
manual adjudication labels -> no compute rerun
new automated candidate filter -> separate implementation/test/docpatch
```

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

results/mpileup/<cohort>/<partition>/<cohort>.<partition>.FWD_like.mpileup.vcf
results/mpileup/<cohort>/<partition>/<cohort>.<partition>.REV_like.mpileup.vcf
results/mpileup/<cohort>/<partition>/<cohort>.<partition>.step07_outputs.tsv

results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv

results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

The Step `05` and Step `06` portions of this layout are cluster-proven across
all six samples. The Step `07`-`09` portions are implemented and tested only at
their available local boundaries. Continue to treat `FWD_like` / `REV_like` as
mechanical read-orientation groups, not biological strand calls.

## External Blockers / Unresolved Items

### Runtime Sample Manifest

`samples.tsv` is the runtime source of truth but is absent from this checkout.
Before Step `07`, determine whether the full six-row manifest is intentionally
cluster-local or should be safely tracked, add explicit replicate values,
validate it, and record where the immutable runtime copy and SHA-256 live.

### R / Rscript Availability

Still unresolved.

Needed for:

```text
Step 08: real-R fixture and runtime validation of the implemented workflow
Step 09: real-R fixture and runtime validation of the implemented workflow
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

This is a Step `07` safety preflight, not merely a later administrative item.
Record pilot and chromosome-1 VCF size/runtime before submitting the remaining
primary partitions.

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

Also unresolved before Step `07`/`08` promotion: confirm `MT` against the
runtime FAI and determine whether the provisional eight-hour, one-CPU
resources are sufficient.

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

Step `06` is cluster-proven across all six samples. Step `07` preserves the
neutral mechanical labels. Steps `08` and `09` retain
`orientation_policy=legacy_provisional_v1`; it must never be described as
biologically validated.

### Step 07: bcftools mpileup

Resolved local contract:

```text
use confirmed bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
partition_id / selector_type / selector_value TSV contract
region -> bcftools -r
regions_file -> bcftools -R
approved primary correction universe: 1-22, X, Y, MT
separate one-row pilot manifest
all manifest samples together in manifest order
both FWD_like and REV_like outputs
legacy depth, annotation, indel-skip, and filter defaults
plain VCF with no bcftools call stage
receipt-last publication under results/mpileup/<cohort>/<partition>/
```

Remaining gates:

```text
real bcftools runtime validation
cluster dry-run
one-row pilot execute and inspection
one-chromosome execute and inspection
approved primary-contig execution and inspection
Step 07 validation docpatch
```

### Step 08: VCF Preprocessing

Implemented locally at `90335d8` behind the shell/SLURM entry points. The
workflow consumes exactly the approved partition-manifest cross-product with
`FWD_like` and `REV_like`, verifies Step `07` receipts/hashes/paths/sample
order/counts, and never globs VCFs. `VariantAnnotation`, `GenomicRanges`, and
`rtracklayer` provide semantic VCF/GTF parsing; multiallelic records are
expanded by ALT index, while symbolic and non-SNV alleles are counted and
excluded.

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
orientation_policy=legacy_provisional_v1, never biologically validated
wide DP__/AD__/AF__ sample columns in manifest order
input receipt published last as the three-output commit marker
```

The wrapper uses an owned lock, run-token temporary paths, stable hashes,
validation-before-publication, cleanup, and rollback. Active shell/fake-R tests
pass locally. `make real-r-test` is implemented, but reports `SKIP` on this
workstation because `Rscript` is unavailable; real-R and all cluster validation
remain pending.

### Step 09: CMH Editing-Site Calling

Implemented locally at `e4371de` behind the shell/SLURM entry points. The
sample manifest is the only runtime pairing source and requires one EV control
and one PUM1 treatment per explicit replicate, identical replicate sets, and
at least two strata. The tracked `configs/step_09_pairs.NORAD_EV_PUM1.tsv`
records the approved replicate `2`, `3`, and `4` relationships for reference
only; pairing is never inferred from sample names.

```text
explicit replicate metadata; never infer pairing from sample names
paired EV/PUM1 strata and approved A>G/default thresholds
two-sided continuity-corrected CMH; common OR is treatment relative to control
one BH family across all successfully tested A>G candidates
missing, low-coverage, degenerate, and non-target rows retained with statuses
optional explicit background condition; disabled by default; EV is not no-dox
four TSVs plus fixed-size, signature-validated mutation-spectrum and depth-delta PDFs
summary published last as the six-output transaction commit marker
real-R runtime validation pending until an R-capable environment is available
```

The shell/fake-R suite is locally passing. The real-R fixtures include a known
CMH result and odds-ratio direction, global BH behavior, strict threshold
boundaries, background mode, empty and degenerate inputs, deterministic
subsets, and PDF signatures, but have not executed on this workstation.

## Deferred Roadmap: Engineering Improvements

These are deferred cross-cutting engineering improvements and roadmap ideas. They do not block the remaining compute pipeline. Do not create generic schemas, helper libraries, dispatchers, validation frameworks, JSON sidecars, cleanup utilities, report templates, or report directories until a roadmap item is explicitly activated. This deferral does not prohibit stage-specific manifests, wrappers, tests, or configuration files explicitly required by an activated pipeline step.

Deferred architecture: evaluate separating the reusable preprocessing backbone from assay-specific analysis modules and a reporting layer. First reproduce the legacy Steps `07`-`09` workflow, then decide whether to formalize modules such as `rna_editing_cmh`, manifest/config contracts, artifact indexes, report generation, and possible public-dataset import support.

### Ordered Post-Proof Operational Packages

Create each package as a clean descendant with its own implementation/evidence
commit when applicable and separate docpatch:

These are candidate package/branch labels; approve each exact interface/name
when activated. The order is fixed. Promotion-specific environment,
reference, and storage evidence is collected manually now; these later
packages turn those checks into reusable tooling for future runs/cohorts.

1. `post09-runtime-preflight`: read-only tool/runtime/package probe from STAR
   through bcftools, R/Rscript, required packages, and RSeQC. It supplements,
   but never replaces, per-step validation and never installs software.
2. `post09-reference-provenance`: reference identities/checksums for FASTA,
   GTF, BED, FAI, DICT, and STAR index plus contig-agreement checks.
3. `post09-storage-inventory-retention`: read-only size/quota/scratch inventory
   followed by an approved retention matrix; it is not a cleanup tool.
4. `post09-validation-reports`: step-specific read-only validators and missing
   Step `00a`/`00b` shell coverage before any generic dispatcher.
5. `post09-targeted-reruns`: manifest-driven rerun planning/submission only
   after validators stabilize; job arrays remain optional and require repeated
   operational need.

### Reporting And Artifact Layer

This layer remains planned, deferred, and non-runnable. It should not be implemented until the core compute workflow is substantially proven.

Ordered packages:

These IDs are candidate labels until separately activated; their dependency
order is fixed.

```text
artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
```

Roadmap ideas:

* `artifact-schema-v1` defines versioned JSON Schema, fixtures, and a validator,
  after resolving run IDs, attempted/failed/incomplete states, version
  conflicts, paths/hashes, and richer Step `09` fields.
* `artifact-adapters-v1` adds read-only adapters over existing Step `07`
  receipts, Step `08` receipt/summary, and Step `09` summary without changing
  proven CLIs or paths. Native emitters may come later.
* `artifact-run-summary` represents missing, failed, and incomplete work and
  aggregates approved artifacts into `run_summary.json` plus an index/QC table.
* `report-html-v1` consumes only structured artifacts and final tables. It
  never reruns computation or discovers inputs by path glob.
* `report-exports-v1` adds PDF/TSV exports only after HTML is stable.

### Later Maintainability And Refactor Work

These are refactor candidates, not active implementation requirements:

* After the evidence gates, `analysis-config-v1` may separate the sample
  manifest (what data exist) from a required analysis config (what contrast,
  reference, strandedness/orientation policy, and filters to run).
* Only then may `rna-editing-cmh-module` wrap Steps `07`-`09` as a thin module
  while preserving every existing CLI and output path; Step `06` can be an
  optional prerequisite for orientation-aware modules.
* General core refactoring requires evidence from a second real cohort.
  Public SRA/GEO/ENA ingestion comes last and must enter through the same
  manifest/config/provenance contracts.
* Consider shared shell helper libraries only after behavior is covered by tests and outputs are stable. Candidate future files include `scripts/lib/norad_common.sh` and `scripts/lib/norad_slurm_common.sh`.
* Candidate shared helpers include repo-root detection, strict-mode/logging conventions, dry-run/execute handling, tool resolution and version logging, Java runtime validation, common file/path validation, lock handling, temp-path cleanup traps, samtools quickcheck/index validation, standardized error messages, and SLURM job context logging.
* Future helper-library refactors must preserve existing step CLIs, output paths, dry-run/execute semantics, and proven cluster contracts.
* Expand shell coverage only after inspecting the current `Makefile`, `tests/shell/`, and `tests/pending/`. In this checkout, `make shell-test` wires Step `00c` and Steps `01`-`09`, while no Step `00a` or Step `00b` shell test exists under `tests/shell/` or `tests/pending/`; adding Step `00a` / `00b` shell coverage is deferred future work. `make real-r-test` runs the Step `08` and Step `09` semantic fixtures when `Rscript` is available and otherwise reports explicit skips.
* Keep active runnable tests under `tests/shell/` and non-runnable future test plans under `tests/pending/`.
* Possible future Makefile targets may include validation/reporting conveniences, but do not add targets until the underlying commands exist and are stable.

### Long-Term Handoff And Admin Utilities

These ideas are for later handoff and maintenance:

* Decide whether a cluster tool-path config file is useful. Candidate names and variables are not decided; scripts should remain portable through CLI/env overrides.
* Add a compact failure taxonomy or troubleshooting index that maps symptom to likely cause, confirmation command, and fix once enough repeated failures exist.
* Consider conservative stale-lock inspection and cleanup utilities after lock behavior is stable and safety rules are documented.
* Keep any admin utility cautious by default; do not delete or repair shared outputs without explicit operator intent.

Explicitly premature now: a generic dispatcher, job arrays, broad shared
shell/SLURM extraction, automatic R-package installation, unproven tool-path
configuration, automatic cleanup or stale-lock deletion, moving proven scripts
into modules, public-data ingestion, or report templates that glob paths.

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
Implement Step 07 locally with cohort-wide, manifest-ordered mpileup for both mechanical orientations.
Add approved primary-contig, one-row pilot, and example Step 07 partition manifests.
Promote the Step 07 mocked-bcftools plan into the active shell suite and `make shell-test`.
Define the Step 07 receipt-last output contract and rollback-protected publication boundary.
Implement Step 08 locally with a deterministic R engine, dry-run-first shell wrapper, and SLURM entry point.
Promote the Step 08 fake-R wrapper plan into the active shell suite and add a conditional real-R fixture suite.
Define the Step 08 exact receipt-set, fixed wide-table schemas, count reconciliation, and provisional orientation policy.
Define the Step 08 three-output transaction with owned locking, stable hashes, rollback, and the input receipt published last.
Implement Step 09 locally with explicit manifest-defined pairing, a base-R CMH engine, dry-run-first shell wrapper, and SLURM entry point.
Promote the former Step 09 pending test plan into active shell and conditional real-R suites.
Define the Step 09 fixed all-sites/significant/summary/mutation schemas, status vocabulary, global BH family, and treatment-relative odds-ratio direction.
Define the Step 09 six-output transaction with owned locking, stable hashes, exact reconciliation, rollback, and the summary published last.
Complete and push the separate Step 07, Step 08, and Step 09 local docpatch gates; Step 09 is at 9ac8307.
Reconcile the descendant runtime, scientific-validation, and post-proof roadmap on step-09a-roadmap-docpatch.
```

## Development Rule

Do not jump ahead.

Continue using:

```text
stage branch -> implement -> focused/full local tests -> implementation commit
-> repository-wide docpatch -> documentation-only commit -> clean/push
-> next descendant local stage when explicitly approved
-> upstream-first cluster dry-run/execute -> inspect evidence -> validation docpatch
```

A TODO is not done until the relevant outputs have been inspected and the docs are updated.
