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

Implemented core compute stages, locally tested but not runtime/cluster-proven:

```text
07   Cohort bcftools mpileup by declared partition and mechanical orientation
08   Deterministic VCF preprocessing and annotation
09   Paired CMH editing-site calling
```

Implemented local evidence tooling, fixture-tested but without production
review evidence:

```text
09c  Explicit scientific-evidence validation and review-summary publication
```

Implemented local artifact-contract tooling, focused-fixture-tested without
production source inspection or generated reporting artifacts:

```text
artifact-schema-v1  Five schema files total, read-only validator, and
                    67-row synthetic explicit physical-artifact inventory
artifact-adapters-v1 49 explicit read-only adapters and receipt-last artifact
                     transaction; fixture-tested only, no production index
artifact-run-summary Canonical JSON, deterministic artifact/QC TSV views, and
                     receipt-last transaction; fixture-tested only, no
                     production summary
```

The active Step `07` shell suite uses a fake bcftools executable. Real
bcftools is unavailable on this workstation, and no Step `07` cluster dry-run,
execute run, or output evidence has been inspected.

The official signed and notarized Apple-silicon CRAN R `4.6.1` package is now
installed locally. Its published SHA-1
`fc9f4ada15589e8e037b9bf05563d21e97181635` and installer signature were
verified before installation. The guarded repository-local `renv` `1.2.3`
environment is pinned to Bioconductor `3.23` and locks the eight direct Step
`08` namespaces plus their dependency closure.

Normal restore and an empty cache-disabled binary restore pass. Namespace
loading, `BiocManager::valid()`, `renv::status()`, and headless PDF creation
also pass. On `step-09b1-real-r-fixes`, both Step `08` and Step `09` real-R
suites now pass without `SKIP`, as do the aggregate local R, shell, Python,
and `r-check` gates. Step `08` now rejects malformed raw `FORMAT/DP`,
`FORMAT/AD`, and `INFO/AD` lexemes before `VariantAnnotation` can coerce them;
its existing partition-overlap rejection was already correct. Step `09` now
checks PDF EOF bytes without locale-sensitive text conversion. No Step
`07`-`09` cluster or production evidence has been added.

Step `09c` is implemented locally at `b674a31`. Its Python and shell fixtures
cover side-effect-free dry-run, the 13-file summary-last transaction, explicit
incomplete evidence, exploratory completion, reserved-state rejection,
immutable hashes, locks, cleanup, and rollback. No production Step `09c`
evidence package or completed scientific review is recorded or supported by
inspected evidence; local completion is fixture-only and does not unlock
biological interpretation.

The tightened Step `09c` contract now preserves human reviewer/owner text,
requires dates for complete/incomplete source evidence, keeps primary,
superseded, and sensitivity analysis sets disjoint, enforces
category-specific analysis ownership, forbids support on pending decisions,
requires complete/not-applicable support for recorded decisions, and requires
defined complete roles for passed/failed/proven computational claims.
Runtime/cluster roles additionally require explicit underlying paths/hashes;
blocked/not-run states are not proof. The tracked example declares
`local_test_status=not_run` because it attaches no local-test evidence;
repository fixture tests remain independently passing.

All six libraries are paired-end and reverse-stranded / first-strand-style.

## Immediate TODOs

The immediate sequence is local-only. Remote and cluster promotion are paused.
Every package uses its own descendant branch, implementation/test commit,
separate repository-wide docpatch, clean-history check, and push.

Required lineage:

```text
step-09a-roadmap-docpatch
└── step-09b-local-r-runtime
    └── step-09b1-real-r-fixes
        └── step-09c-scientific-validation
            └── artifact-schema-v1          # implemented at 5f4d3b4
                └── artifact-adapters-v1    # implemented at 4dbd32d
                    └── artifact-run-summary # implemented at 209bb19
                        └── report-html-v1    # next
                            └── report-exports-v1
                                └── post09-runtime-preflight
                                    └── post09-reference-provenance
                                        └── post09-storage-inventory-retention
                                            └── post09-validation-report-00a
                                                └── post09-validation-report-00b
                                                    └── post09-validation-report-00c
                                                        └── post09-validation-report-01
                                                            └── post09-validation-report-02
                                                                └── post09-validation-report-02b
                                                                    └── post09-validation-report-03
                                                                        └── post09-validation-report-04
                                                                            └── post09-validation-report-05
                                                                                └── post09-validation-report-06
                                                                                    └── post09-validation-report-07
                                                                                        └── post09-validation-report-08
                                                                                            └── post09-validation-report-09
```

The Step `09b` runtime and Step `09b1` corrective gates are complete locally.
Commit `eae5eca` contains the Step `09b1` implementation and tests. Step `09c`
is implemented at `b674a31`. `artifact-schema-v1` is implemented at `5f4d3b4`,
and `artifact-adapters-v1` is implemented at `4dbd32d`.
`artifact-run-summary` is implemented at `209bb19`. After this run-summary
documentation gate is committed and pushed, `report-html-v1` is next.

Completed local gate:

```text
step-09c-scientific-validation
  explicit-input dry-run-first validation
  13-file atomic evidence transaction with summary last
  Python and shell synthetic-fixture suites
  no production scientific evidence or review

artifact-schema-v1
  one shared common schema plus four public Draft 2020-12 record schemas
  read-only explicit document and inventory validator
  67-row synthetic explicit physical-artifact inventory for Steps 00a-09c
  current 58 focused synthetic contract tests
  no production source inspection, generated artifact index, run summary,
    report, runtime/cluster evidence, or scientific evidence

artifact-adapters-v1
  dry-run-first explicit run-contract and inventory interface
  49 read-only adapters covering all 67 declared Step 00a-09c artifacts
  deterministic records/index/receipt transaction with receipt published last
  revisionable inventories recorded as distinct adapter attempts under one
    unchanged immutable run contract
  50 focused adapter tests and 108 combined schema/adapter tests
  synthetic fixture execution only; no production artifact index, run summary,
    report, runtime/cluster proof, completed science review, or readiness

artifact-run-summary
  dry-run-first exact artifact-receipt and optional Step 09c summary interface
  canonical JSON plus deterministic artifact/QC TSV views
  rollback-protected four-file transaction with the receipt published last
  immutable run identity, attempt lineage, exact evidence normalization,
    owned locking, adapter/Step 09c transaction-member rechecks, rollback,
    and recovery validation
  39 focused tests and 213 complete Python tests
  synthetic fixture execution only; no production artifact index or summary,
    report, runtime/cluster proof, completed science review, or readiness
```

Step `09c` may publish only:

```text
evidence_incomplete
science_review_complete_exploratory
```

It must reject the reserved `biological_interpretation_ready` state until a
separately approved policy branch unlocks its scientific exit criteria.

### 1. Continue Reports Immediately

Do not defer reporting. The schema, adapter, and run-summary packages are
complete locally; continue in order:

1. `report-html-v1`: checksum-verified local Quarto `1.9.38`, a static QMD
   view, and one self-contained accessible HTML report.
2. `report-exports-v1`: the same report as HTML/PDF plus summary TSV and a
   report receipt, using bundled Typst for PDF.

Reports must separate computational and scientific state, carry persistent
limitations banners, call rows “CMH-ranked candidates,” declare any
truncation with full-table path/hash, and never imply that rendering is
validation.

### 2. Implement Foundational Read-Only Engineering

After reporting, implement:

1. `post09-runtime-preflight`;
2. `post09-reference-provenance`;
3. `post09-storage-inventory-retention`.

These packages inspect and record explicit inputs. They do not install tools,
repair references, or delete/move/compress outputs.

### 3. Add One Validator Branch Per Pipeline Step

Each branch publishes
`results/qc/validation/<step>/<scope>.validation.tsv`, adds its artifact
adapter, and proves through fixtures that its evidence reaches the structured
run summary and consolidated HTML/PDF report. Use one branch each for:

```text
00a 00b 00c 01 02 02b 03 04 05 06 07 08 09
```

Stop local work after `post09-validation-report-09`.

### 4. Resume Remote Work Later

Only after that final clean branch, continue:

```text
validate-step-07
-> validate-step-08
-> validate-step-09
-> validate-step-09c-scientific-evidence
-> post09-targeted-reruns
```

Remote validation remains upstream-sequential. Each remote evidence branch
regenerates the structured run summary and HTML/PDF report after evidence
inspection, then records report paths and hashes in its docpatch. Cluster
proof and biological readiness remain independent.

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

results/scientific_validation/<review_id>/<review_id>.step09c_review_plan.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_evidence_index.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_orientation_locus_audit.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_annotation_audit.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_qc_funnel.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_replicate_effects.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_sensitivity_matrix.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_leave_one_pair_out.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_candidate_selection.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_candidate_adjudication.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_decisions.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_limitations.tsv
results/scientific_validation/<review_id>/<review_id>.step09c_review_summary.tsv

results/artifacts/<run_id>/records/<artifact_id>.json
results/artifacts/<run_id>/<run_id>.artifacts.tsv
results/artifacts/<run_id>/<run_id>.artifact_receipt.tsv
results/artifacts/<run_id>/<run_id>.run_summary.json
results/artifacts/<run_id>/<run_id>.run_summary.tsv
results/artifacts/<run_id>/<run_id>.qc_summary.tsv
results/artifacts/<run_id>/<run_id>.run_summary_receipt.tsv
```

The Step `05` and Step `06` portions of this layout are cluster-proven across
all six samples. The Step `07`-`09` portions are implemented and tested only at
their available local boundaries. Step `09c` is implemented and
synthetic-fixture-tested only; its output layout is a contract, not evidence
that a production review exists. Continue to treat `FWD_like` / `REV_like` as
mechanical read-orientation groups, not biological strand calls.

## External Blockers / Unresolved Items

### Runtime Sample Manifest

`samples.tsv` is the runtime source of truth but is absent from this checkout.
Before Step `07`, determine whether the full six-row manifest is intentionally
cluster-local or should be safely tracked, add explicit replicate values,
validate it, and record where the immutable runtime copy and SHA-256 live.

### R / Rscript Availability

Resolved locally:

```text
official Apple-silicon CRAN R 4.6.1
renv 1.2.3
Bioconductor 3.23
guarded project library and locked Step 08 dependency closure
normal and empty cache-disabled binary restores
namespace, BiocManager, renv-status, and headless-PDF checks
```

Both semantic suites pass without `SKIP` under the guarded local environment
after `step-09b1-real-r-fixes`. CSU compute/batch R, package restore, and
hash-tool visibility remain unresolved and will be handled only when remote
validation resumes.

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
pass locally. The real-R suite now also passes without `SKIP`. The prior
generic negative-fixture error had misattributed a later malformed-count
failure to the already-working partition-overlap validator. Commit `eae5eca`
adds a streaming raw-VCF preflight that checks exact DP/AD widths and permits
only `.` or non-negative integer tokens before semantic parsing. A single `.`
is valid for a wholly missing AD vector; otherwise AD width must equal REF
plus every ALT. Negative fixtures assert each failure reason. All production
and cluster validation remains pending.

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
real-R suite passes locally; PDF EOF fixture uses raw-byte matching
```

The shell/fake-R suite is locally passing. The real-R fixtures include a known
CMH result and odds-ratio direction, global BH behavior, strict threshold
boundaries, background mode, empty and degenerate inputs, deterministic
subsets, and PDF signatures. They now pass locally without `SKIP` after the
fixture was changed to search raw PDF bytes without locale-sensitive text
conversion. This local fixture pass is not production or cluster evidence.

## Activated Roadmap And Deferred Boundaries

Scientific-validation tooling, the explicit artifact schemas/validator, the
read-only adapter indexer, and the canonical run-summary builder are
implemented and fixture-tested locally. HTML/PDF/TSV reports, the three
foundational read-only packages, and one validator branch per pipeline step
remain activated in the exact local sequence above. Each becomes available
only after its own implementation/docpatch gate.

### Foundational Operational Packages

Create each package as a clean descendant with its own implementation/evidence
commit when applicable and separate docpatch:

These exact labels and their order are approved. They follow the report
vertical slice:

1. `post09-runtime-preflight`: read-only tool/runtime/package probe from STAR
   through bcftools, R/Rscript, required packages, and RSeQC. It supplements,
   but never replaces, per-step validation and never installs software.
2. `post09-reference-provenance`: reference identities/checksums for FASTA,
   GTF, BED, FAI, DICT, and STAR index plus contig-agreement checks.
3. `post09-storage-inventory-retention`: read-only size/quota/scratch inventory
   followed by an approved retention matrix; it is not a cleanup tool.
4. Thirteen explicit `post09-validation-report-*` branches for `00a`, `00b`,
   `00c`, `01`, `02`, `02b`, `03`, `04`, `05`, `06`, `07`, `08`, and `09`.
5. `post09-targeted-reruns` remains deferred to the later remote sequence,
   after validator stabilization and production evidence.

### Reporting And Artifact Layer

This layer is activated for immediate local implementation after Step `09c`.
Its read-only schema validator, explicit adapter indexer, and canonical
run-summary builder are runnable and locally focused-tested. No production
adapter transaction or run summary exists. Report production remains
non-runnable at this boundary; `report-html-v1` is the next package.

Ordered packages:

These branch IDs and their dependency order are approved.

```text
artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
```

Implemented boundary and remaining roadmap:

* `artifact-schema-v1` now defines the versioned JSON Schemas, valid fixtures,
  explicit physical inventory, and read-only validator for run IDs,
  attempts/failures/incomplete states, version conflicts, paths/hashes,
  evidence roles, scientific state, and richer Step `09` fields. Its current 58
  focused tests pass locally.
* `artifact-adapters-v1` implements 49 read-only adapters over the explicit
  Step `00a`-`09c` inventory without changing proven CLIs or paths. It requires
  the six-field immutable run contract plus a revisionable inventory, emits
  missing/failed/incomplete/unavailable states explicitly, and publishes
  records, the ordered index, and the receipt last. All 50 focused tests pass
  on synthetic fixtures; no production index exists. Native emitters may come
  later.
* `artifact-run-summary` is implemented at `209bb19`. It represents missing,
  failed, and incomplete work, consumes one exact complete adapter receipt and
  optional exact Step `09c` summary, and publishes canonical
  `<run_id>.run_summary.json`, deterministic artifact/QC TSV views, and a
  receipt last. Its 39 focused tests pass; no production summary exists.
* `report-html-v1` consumes only validated canonical run-summary JSON. Any
  approved table path/hash is already explicit in that model; the renderer
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
* The explicit `00a` and `00b` validator branches will add their focused
  validation coverage. `make real-r-test` now executes both semantic suites
  locally under the guarded environment, and both pass without `SKIP`.
* Keep active runnable tests under `tests/shell/` and non-runnable future test plans under `tests/pending/`.
* Add validation/reporting Makefile targets only on the branch that implements
  the underlying stable command.

### Long-Term Handoff And Admin Utilities

These ideas are for later handoff and maintenance:

* Decide whether a cluster tool-path config file is useful. Candidate names and variables are not decided; scripts should remain portable through CLI/env overrides.
* Add a compact failure taxonomy or troubleshooting index that maps symptom to likely cause, confirmation command, and fix once enough repeated failures exist.
* Consider conservative stale-lock inspection and cleanup utilities after lock behavior is stable and safety rules are documented.
* Keep any admin utility cautious by default; do not delete or repair shared outputs without explicit operator intent.

Explicitly premature now: a generic dispatcher, job arrays, broad shared
shell/SLURM extraction, automatic R-package installation, unproven tool-path
configuration, automatic cleanup or stale-lock deletion, moving proven scripts
into modules, public-data ingestion, or any report template that discovers
inputs by glob.

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
Install and verify signed CRAN R 4.6.1 locally without using the damaged Homebrew checkout.
Create the guarded renv 1.2.3 / Bioconductor 3.23 lock and pass normal plus empty cache-disabled restores.
Pass local namespace, BiocManager, renv-status, and headless-PDF runtime checks.
Execute both real-R suites without SKIP and record the initial failing fixtures without overstating them.
Correct Step 08 raw DP/AD/INFO AD lexical validation and make its negative fixtures reason-specific at eae5eca.
Make the Step 09 PDF EOF fixture locale-independent with raw-byte matching at eae5eca.
Pass both real-R suites, the aggregate local R target, shell/Python gates, and r-check locally after those corrections.
Implement Step 09c locally as explicit-input, dry-run-first Python/shell evidence validation at b674a31.
Publish and validate the synthetic-fixture Step 09c 13-file summary-last transaction with owned locking, immutable hashes, rollback, and cleanup.
Promote Step 09c Python and shell fixtures into the active repository gate, including incomplete/exploratory and reserved-state cases.
Implement artifact-schema-v1 at 5f4d3b4 with one shared common schema and four public Draft 2020-12 schemas.
Add and validate the 67-row synthetic explicit physical-artifact inventory for Steps 00a-09c.
Pass all 58 current focused artifact-contract tests without claiming source inspection,
generated outputs, production evidence, or cluster proof.
Implement artifact-adapters-v1 at 4dbd32d with the strict run-contract input, 49 explicit read-only adapters, and a receipt-last transaction.
Pass all 50 focused adapter tests and all 108 current combined schema/adapter tests without claiming a production index, production run summary/report, runtime/cluster proof, or scientific evidence.
Implement artifact-run-summary at 209bb19 with exact receipt inputs, canonical JSON, deterministic artifact/QC TSV views, and a receipt-last transaction.
Pass all 39 focused run-summary tests and the complete 213-test Python gate without claiming a production index/summary, report, runtime/cluster proof, completed production science review, or biological readiness.
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
