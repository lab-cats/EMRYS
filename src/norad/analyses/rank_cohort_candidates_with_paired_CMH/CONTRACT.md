# `rank_cohort_candidates_with_paired_CMH` analysis contract

This is the observed contract of historical Step `09` for `ARCH-02A`. It is an
analysis operation rather than another preprocessing stage. The working name
is not a stable slug or implemented source location; executables remain in
`scripts/` and `jobs/`.

## Responsibility and execution dependencies

Consume the committed Step `08` cohort candidates, construct explicit paired
control/treatment replicate strata, run cohort-wide paired Cochran–Mantel–
Haenszel analysis for a requested RNA substitution, apply one Benjamini–
Hochberg correction, classify results under explicit thresholds, and publish
tables and diagnostic plots. Its outputs are CMH-ranked candidates, not
validated RNA-editing sites.

Step `09` requires the Step `08` sites table and input receipt, the sample and
partition manifests, and explicit analysis policy. It does not consume the
Step `08` QC summary or standalone validation report. Step `09c` consumes the
complete six-output transaction together with upstream evidence for scientific
review.

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

[`step_09_cmh_editing_site_calling.R`](../../../../scripts/step_09_cmh_editing_site_calling.R)
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

[`step_09_cmh_editing_site_calling.sh`](../../../../scripts/step_09_cmh_editing_site_calling.sh)
is side-effect-free in dry-run. Execute mode hashes and repeatedly rechecks
manifests plus both Step `08` inputs, uses an analysis-owned lock and run-token
scratch/backups, requires all six previous outputs or none, validates all
temporaries, publishes the summary last as native commit marker, then
revalidates contents and hashes. If rollback cannot restore a predecessor, it
retains the owned lock and recovery evidence for operator intervention.

The summary becomes visible before final post-publication checks and does not
hash its five sibling outputs, so presence alone is not independent proof that
the producer returned success or that the current set is immutable.

[`step_09_cmh_editing_site_calling.slurm`](../../../../jobs/step_09_cmh_editing_site_calling.slurm)
owns cluster defaults, dependency environment, execution gating, delegation,
and final path checks; it does not own statistical behavior. Unlike the public
script, the wrapper currently creates its `logs/` directory even in dry-run.

## Validation interface

[`validate_step_09_cmh_outputs.py`](../../../../scripts/validate_step_09_cmh_outputs.py)
accepts explicit manifests, Step `08` inputs, all six native outputs, analysis
and cohort IDs, and report output. It does not invoke R. Dry-run prints the
common report; `--execute` snapshot-rechecks inputs and uses Step `00a`'s shared
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
implementation. Its current `status_semantics` expected-text nevertheless says
“recomputed ... CMH,” which overstates the production validator's evidence.

Content mismatches publish `status=fail`; unsafe structure or report-
publication failures exit `2`.

## Consumers and protected evidence

- Step `09c` scientific review consumes the full native transaction, Step `08`
  three-table transaction, manifests, declared review evidence, and review
  policy. It independently validates native outputs but does not require the
  standalone Step `09` validation report or rerun CMH analysis.
- Artifact adapters register all six outputs and
  `step09_validation_report_v1`; reporting consumes the later canonical review
  package rather than treating raw significant rows as biological truth.
- Direct shell/R/validator tests protect manifests and pairing, statuses,
  thresholds, method metadata, dry-run, transaction, rollback, plots, and the
  independent validation boundary.
- Independent Python-oracle and real-R corpus comparisons protect CMH/BH
  behavior; wrapper, roster, publication-fault, public-CLI, artifact, report,
  coverage, and Step `09c` tests protect cross-boundary behavior.

This is local fixture and guarded real-R/oracle evidence, not production,
cluster, completed scientific review, or biological interpretation readiness.

## Ownership gaps and deferred decisions

- Step `09` schemas and reusable validators live in the Step `09c` scientific-
  review module, creating a reverse dependency for the standalone validator
  and artifact adapter.
- Method/schema/status logic is duplicated across shell, R, Python, oracle,
  artifact, and scientific-review surfaces; shared report publication remains
  owned by the Step `00a` validator.
- Producer-recorded relative paths are later interpreted from a consumer's
  working directory, and the summary omits implementation, runtime, R/package,
  attempt, and sibling-output identities.
- The analysis boundary requires ingestion-oriented FASTQ and strandedness
  manifest columns that its method does not use, and it trusts rather than
  dereferences the Step `07`/annotation identities recorded by Step `08`.
- A complete predecessor is checked for six-file presence, not semantic
  validity, before replacement.
- Analysis-policy versioning, method-module interface, sibling-output binding,
  stable identity, target files, recovery tooling, and migration mechanics
  remain deferred.
