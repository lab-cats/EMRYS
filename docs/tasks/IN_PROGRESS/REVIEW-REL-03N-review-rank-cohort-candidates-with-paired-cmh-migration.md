# REVIEW-REL-03N — Review paired-CMH analysis migration reliability

## Objective

Challenge `MIG-03N` against shell/R/validator/scheduler contracts, six-output
transaction and restoration behavior, input stability, shared-contract loader
faults, guarded-real-R and independent-oracle semantics, artifact
interpretation, and coverage before any executable move.

## Why this exists

Current tests protect normal publication and method behavior, but relocation
must not hide or bless the summary-visible-before-commit window, incomplete
restoration states, retained lock/recovery evidence, input mutation, validator
evidence ceilings, shared Step `09c` dependency, or stale scheduler success.
The R semantic engine is over one thousand lines and must remain behavior-
equivalent apart from reviewed path text without restoring or changing
dependencies.

## Fixed decisions

- Review only; add no reliability behavior and run no computational test under
  this card. Findings may require later bounded old-path test-only checkpoints.
- Preserve every characterized defect as a named ceiling; never convert a
  migration oracle into hardening, recovery redesign, schema extraction, or
  evidence promotion.
- Keep local fake-R, guarded-real-R fixture, independent Python oracle,
  scheduler mock, and validator evidence separate from cluster, production,
  completed scientific review, or biological proof.

## Blocked by

- [REVIEW-ARCH-03N](../COMPLETED/REVIEW-ARCH-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Required: completed architecture review supplies the corrected cutover and loader boundary.

## Completion unblocks

- [REVIEW-UX-03N](REVIEW-UX-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Fully: usability review needs the fixed failure, residue, recovery, R/oracle, validator, and scheduler obligations.

## Prerequisites

- Inspect only the committed architecture-reviewed card state and existing
  old-path implementation/tests; do not mutate or execute them.

## Required context

- `MIG-03N`; architecture review; all Step `09` native and candidate direct-
  test assets; neutral report and flat Step `09c` loader owners/tests; central
  scheduler, guarded-R, independent-oracle, artifact, validation-roster,
  publication-fault, public-CLI, and coverage surfaces; current runbook/
  troubleshooting recovery language; and the exact six-file transaction.

## Questions owned by this card

- Which smallest old-path test-only slices are required for child/publication/
  restoration failures, summary visibility, signal exits, same-scope lock
  concurrency, stale paths, unrelated bytes, and retained recovery evidence?
- Which admitted inputs are hash-bound and snapshot-rechecked, which mutations
  remain visible or invisible, and what summary/runtime/attempt/sibling
  identities are absent without changing provenance?
- Which guarded-real-R fixtures and independent count-derived oracle cases are
  sufficient to prove path-only relocation while preserving pairing,
  estimability, continuity correction, odds ratios, global BH, statuses, and
  dependency state?
- Which compact validator matrix owns all seven rows, exit-`0` failed evidence,
  non-recomputed CMH limits, stable-input and publication behavior, plus
  neutral-report and Step `09c` exact-loader faults?
- Which scheduler cases preserve module/R resolution, submit-CWD/log effects,
  child failures, six-file checks, and stale-complete false success?

## In scope

- Test-gap inventory; minimal old-path checkpoint ordering; exact shell
  transaction/restore/mutation/signal/concurrency oracles; guarded-R and
  independent-oracle semantic parity; validator/report/Step-`09c` loader and
  evidence ceilings; scheduler diagnostics/stale outputs; artifact meaning;
  coverage policy; and rollback consequences.

## Out of scope

- Production mutation; defect fixes; R dependency restoration/installation;
  schema/helper extraction; public imports; new recovery or attempt markers;
  transaction/artifact/scheduler/statistical policy changes; Step `09c`
  migration; or cluster/production/scientific work.

## Deliverables

- Finding-by-finding reliability disposition and the smallest ordered
  test-only slices required before atomic cutover, recorded in `MIG-03N` and
  the audit.

## Acceptance evidence

- Every high-risk state has an existing or required safe local oracle with
  exact bytes, paths, streams, exits, locks, backups, residue, unrelated files,
  and evidence ceiling. No proposed oracle requires a production behavior,
  dependency, method, policy, schema, or scientific-meaning change.

## Canonical documentation updates

- This card, `MIG-03N`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk restoration/mutation/R-semantic state lacks a safe local
  oracle, parity needs production or dependency work, native/report bytes must
  change beyond reviewed paths, or a defect must be fixed or blessed.

## Completion record

Selected alone from clean, published, local/upstream/live-remote-equal
architecture-completion checkpoint
`e36cb9463fe5cf54777b48d5a063c28e28a44e62` for a read-only
reliability pass. MIG-03N, usability, Step `09c`, and all executable/test files
remain unselected and unchanged; no computational test runs in this review.
