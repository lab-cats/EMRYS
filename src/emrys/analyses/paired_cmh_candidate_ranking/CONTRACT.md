# `rank_cohort_candidates_with_paired_CMH` analysis contract

This is the observed contract of historical Step `09` for `ARCH-02A`. It is an
analysis operation rather than another preprocessing stage. The exact public
identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
retains that semantic identity while the physical/package owner uses the
capability-oriented name `paired_cmh_candidate_ranking`.

## Responsibility and execution dependencies

Consume the committed
[`preprocess_and_annotate_cohort_candidates`](../../stages/cohort_candidate_preprocessing/CONTRACT.md)
cohort candidates, construct explicit paired
control/treatment replicate strata, run cohort-wide paired Cochran–Mantel–
Haenszel analysis for a requested RNA substitution, apply one Benjamini–
Hochberg correction, classify results under explicit thresholds, and publish
tables and diagnostic plots. Its outputs are CMH-ranked candidates, not
validated RNA-editing sites.

Step `09` requires that final owner's sites table and input receipt, the sample and
partition manifests, and explicit analysis policy. It does not consume the
Step `08` QC summary or standalone validation report. Artifact indexing and
reporting consume the validated six-output transaction without changing its
computational meaning. External review or adjudication may reference these
outputs and their provenance, but it is not a pipeline dependency.

## Pairing, method, and policy

The sample manifest is the only pairing authority. Control and treatment must
have exactly one sample for each identical replicate label and at least two
paired strata; pairing is never inferred from filenames. An optional background
condition must be distinct and present. Step `08` candidate order, sample
columns, counts, manifest identities, and `legacy_provisional_v1` are
independently reconciled and stability-checked.

Defaults are:

```text
control=EV                 treatment=PUM1
target RNA change=A>G      minimum sample DP=1
mean analysis DP>50        BH FDR<0.05
common OR>1.2 or <1/1.2    absolute AF difference>0.005
optional background AF<0.01 in every background sample
```

For each target-change candidate with complete minimum-depth counts, the R
implementation builds treatment/control by edited/unedited tables for each
replicate and runs `stats::mantelhaen.test` two-sided, asymptotic, with
continuity correction. Failed or degenerate tests are characterized rather
than discarded. BH adjustment spans every successfully tested target
candidate in the cohort. Threshold comparisons are strict; results become
`significant_up`, `significant_down`, or an explicit non-call status.

[`step_09_cmh_editing_site_calling.R`](step_09_cmh_editing_site_calling.R)
owns pairing validation, count tables, CMH/BH computation, classification,
summary and mutation-spectrum aggregation, and plot generation. The historical
filename's “calling” does not elevate the scientific evidence state.

## Inputs and six-output transaction

Inputs are safe analysis/cohort IDs, manifests, Step `08` root, output root,
control/treatment and optional background conditions, target RNA alleles,
coverage/FDR/effect/background thresholds, and explicit Rscript/R-program
resolution. The six outputs under `<output-root>/<analysis-id>/` are:

```text
<analysis>.cmh_all_sites.tsv
<analysis>.cmh_significant_sites.tsv
<analysis>.mutation_spectrum.tsv
<analysis>.mutation_spectrum.pdf
<analysis>.depth_delta.pdf
<analysis>.cmh_summary.tsv
```

All-sites preserves the complete Step `08` candidate universe and order while
adding method, status, depth, AF, background, CMH, BH, and effect fields.
Significant-sites is its exact ordered `significant_up`/`significant_down`
subset. The one-row summary binds manifests and consumed Step `08` paths and
hashes, analysis conditions, thresholds, method, provisional policy, and
reconciled counts. Mutation-spectrum TSV/PDF and depth/delta PDF are derived
diagnostics. Header-only candidate tables are valid when all counts reconcile.

Private [`producer.py`](producer.py) is side-effect-free in dry-run. Execute
mode hashes and repeatedly rechecks
manifests plus both Step `08` inputs, uses an analysis-owned lock and run-token
scratch/backups, requires all six previous outputs or none, validates all
temporaries, publishes the summary last as native commit marker, then
revalidates contents and hashes. If rollback cannot restore a predecessor, it
retains the owned lock and recovery evidence for operator intervention.
`--no-clobber` is the orchestration-safe policy: while holding the owner lock,
it rejects a complete predecessor set without invoking R or changing stable
outputs. Direct invocations retain complete-set replacement unless the flag is
supplied.
First publication in that mode is create-exclusive and retains all six staging
inode anchors through validation; ambiguous replacement preserves the owner
lock and residue.

The summary becomes visible before final post-publication checks and does not
hash its five sibling outputs, so presence alone is not independent proof that
the producer returned success or that the current set is immutable.

## Validation interface

The grouped `emrys validate paired-cmh-candidate-ranking` route,
implemented by private [`validator.py`](validator.py), accepts explicit
manifests, Step `08` inputs, all six native outputs, analysis and cohort IDs,
and report output. It does not invoke R. Dry-run prints the common report;
`--execute` snapshot-rechecks inputs and uses the neutral validation-report
publisher.

Exact checks are:

- `output_transaction`;
- `upstream_identity_and_candidate_order`;
- `status_semantics`;
- `significant_subset`;
- `summary_count_reconciliation`;
- `mutation_spectrum_reconciliation`; and
- `pdf_structure`.

The validator checks exact basenames/headers/distinct files, Step `08` identity
and complete candidate order, reported target/test/call/depth/AF/background
semantics, BH values derived from reported p-values, exact significant subset,
summary provenance/counts, canonical mutation spectrum, and PDF containers. It
does not independently recompute CMH count-table estimability, statistic,
p-value, or common odds ratio. The separate independent oracle and committed
real-R corpus protect that method boundary without importing production
implementation. Its `status_semantics` evidence text explicitly states that
CMH values are not independently recomputed.

Content mismatches publish `status=fail`; this includes invalid UTF-8 inside an
otherwise admitted native table, which is recorded as failed evidence rather
than rejected as a runtime error. Unsafe filesystem structure or report-
publication failures exit `2`.

## Consumers and protected evidence

- Artifact adapters register all six outputs and
  `step09_validation_report_v1`; reporting presents them as computational
  candidates rather than treating threshold-passing rows as biological truth.
- Direct producer/R/validator tests protect manifests and pairing, statuses,
  thresholds, method metadata, dry-run, transaction, rollback, plots, and the
  independent validation boundary.
- Independent Python-oracle and real-R corpus comparisons protect CMH/BH
  behavior; roster, publication-fault, public-CLI, artifact, report, and
  coverage tests protect cross-boundary behavior.

This is local fixture and guarded real-R/oracle evidence, not production,
cluster, completed scientific review, or biological interpretation readiness.

## Current ownership boundaries and deferred decisions

- The Step `08` input contract now belongs to neutral
  [`step08.py`](../../contracts/scientific_evidence/step08.py), imported by
  neutral Step `09`, this validator, and the artifact index under one
  shared module/error/table identity.
- Step `09` schemas and reusable validators now belong to neutral
  [`step09.py`](../../contracts/scientific_evidence/step09.py), imported by
  this validator and artifact indexing under one shared ready-owner identity.
- Method/schema/status logic remains distributed across the R implementation,
  neutral Python contract, independent oracle, artifact, and validation
  surfaces; shared report publication belongs to
  neutral [`validation/report.py`](../../libraries/validation/report.py).
- Producer-recorded relative paths are later interpreted from a consumer's
  working directory, and the summary omits implementation, runtime, R/package,
  attempt, and sibling-output identities.
- The analysis boundary requires ingestion-oriented FASTQ and strandedness
  manifest columns that its method does not use, and it trusts rather than
  dereferences the Step `07`/annotation identities recorded by Step `08`.
- A complete predecessor is checked for six-file presence, not semantic
  validity, before replacement.
- Analysis-policy versioning, method-module interface, sibling-output binding,
  target files, recovery tooling, and migration mechanics
  remain deferred.
