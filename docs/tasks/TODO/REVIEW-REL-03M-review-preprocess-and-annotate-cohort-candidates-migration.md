# REVIEW-REL-03M — Review cohort preprocessing migration reliability

## Objective

Challenge `MIG-03M` against shell/R/validator/scheduler contracts, split-root
transaction and restoration behavior, input stability, shared-contract loader
faults, guarded-real-R semantics, artifact-marker interpretation, and coverage
before any executable move.

## Why this exists

Current tests protect normal publication and successful rollback, but
relocation must not hide or bless the receipt-visible-before-commit window,
incomplete restoration with lock release and no recovery marker, cross-root
residue, input mutation, validator evidence ceilings, shared Step `09c`
dependency, or stale scheduler success. The R semantic engine is nearly two
thousand lines and must remain byte/behavior-equivalent apart from reviewed
path text without restoring or changing dependencies.

## Fixed decisions

- Review only; add no reliability behavior and run no computational test under
  this card. Findings may require later bounded old-path test-only checkpoints.
- Preserve every characterized defect as a named ceiling; never convert a
  migration oracle into hardening, recovery redesign, schema extraction, or
  evidence promotion.
- Keep local fake-R, guarded-real-R fixture, scheduler mock, and Python evidence
  separate from cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-ARCH-03M](REVIEW-ARCH-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Required: reliability review needs the architecture-corrected cutover and loader boundary.

## Completion unblocks

- [REVIEW-UX-03M](REVIEW-UX-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Fully: usability review needs the fixed failure, residue, recovery, R, validator, and scheduler obligations.

## Prerequisites

- Inspect only the committed architecture-reviewed card state and existing
  old-path implementation/tests; do not mutate or execute them.

## Required context

- `MIG-03M`; architecture review; all Step `08` native and direct-test assets;
  neutral report and flat Step `09c` loader owners/tests; central scheduler,
  guarded-R, artifact, validation-roster, publication-fault, public-CLI, and
  coverage surfaces; current runbook/troubleshooting recovery language; and
  the exact three-file two-root transaction.

## Questions owned by this card

- Which smallest old-path test-only slices are required for child/publication/
  restoration failures, receipt visibility, signal exits, same-scope lock
  concurrency, stale paths, unrelated bytes, and cross-root residue?
- Which admitted inputs are hash-bound and snapshot-rechecked, which mutations
  remain visible or invisible, and what receipt/runtime/attempt identities are
  absent without changing provenance?
- Which guarded-real-R fixtures and exact output comparisons are sufficient to
  prove path-only relocation while preserving lexical/semantic parsing,
  annotation, provisional policy, and dependency state?
- Which compact validator matrix owns all five rows, exit-`0` failed evidence,
  candidate/order limits, annotation-path disagreement, stable-input and
  publication behavior, plus neutral-report and Step `09c` exact-loader faults?
- Which scheduler cases preserve module/renv/R resolution, submit-CWD/log
  effects, child failures, three-file checks, and stale-complete false success?
- How is the native input-receipt marker versus artifact summary failure marker
  distinction tested and described without changing either contract?

## In scope

- Test-gap inventory; minimal old-path checkpoint ordering; exact shell
  transaction/restore/mutation/signal/concurrency oracles; guarded-R semantic
  parity; validator/report/Step-`09c` loader and evidence ceilings; scheduler
  diagnostics/stale outputs; artifact marker meaning; coverage policy; and
  rollback consequences.

## Out of scope

- Production mutation; defect fixes; R dependency restoration/installation;
  schema/helper extraction; public imports; new recovery or attempt markers;
  transaction/artifact/scheduler policy changes; Step `09`/`09c` migration; or
  cluster/production/scientific work.

## Deliverables

- Finding-by-finding reliability disposition and the smallest ordered test-only
  slices required before atomic cutover, recorded in `MIG-03M` and the audit.

## Acceptance evidence

- Every high-risk state has an existing or required safe local oracle with
  exact bytes, paths, streams, exits, locks, backups, residue, unrelated files,
  and evidence ceiling. No proposed oracle requires a production behavior,
  dependency, method, policy, schema, or scientific-meaning change.

## Canonical documentation updates

- This card, `MIG-03M`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk restoration/mutation/R-semantic state lacks a safe local
  oracle, parity needs production or dependency work, native/report bytes must
  change beyond reviewed paths, or a defect must be fixed or blessed.

## Completion record

Not selected. Blocked on unselected `REVIEW-ARCH-03M`; no executable/test file
changed or ran.
