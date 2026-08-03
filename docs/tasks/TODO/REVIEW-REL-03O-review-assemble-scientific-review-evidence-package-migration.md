# REVIEW-REL-03O — Review scientific-review package migration reliability

## Objective

Challenge `MIG-03O` against Python/shell contracts, thirteen-output
transaction and restoration behavior, input stability, scientific-state gates,
shared import consumers, artifact/run-summary interpretation, and coverage
before any executable move.

## Why this exists

Relocation must not hide or bless summary-visible-before-commit windows,
incomplete rollback and retained recovery evidence, source mutation,
all-thirteen predecessor rules, reserved-state rejection, imported-contract
faults, or evidence overclaim. The implementation combines schemas, review
policy, normalization, locking, and publication, so path parity requires
focused oracles without redesigning those concerns.

## Fixed decisions

- Review only; add no reliability behavior and run no computational test under
  this card. Findings may require later bounded old-path test-only checkpoints.
- Preserve every characterized defect as a named ceiling; never convert a
  migration oracle into hardening, recovery redesign, schema extraction, or
  evidence promotion.
- Keep local synthetic fixtures, public-shell tests, import-consumer tests,
  artifact/run-summary/report tests, scientific review, cluster, production,
  and biological evidence as distinct states.

## Blocked by

- [REVIEW-ARCH-03O](../IN_PROGRESS/REVIEW-ARCH-03O-review-assemble-scientific-review-evidence-package-migration.md) — Required: reliability review needs the architecture-corrected cutover and import/asset boundary.

## Completion unblocks

- [REVIEW-UX-03O](REVIEW-UX-03O-review-assemble-scientific-review-evidence-package-migration.md) — Fully: usability review needs the fixed failure, residue, recovery, import, state, and provenance obligations.

## Prerequisites

- Inspect only the committed architecture-reviewed card state and existing
  old-path implementation/tests; do not mutate or execute them.

## Required context

- `MIG-03O`; architecture review; all candidate native/test/support assets;
  transaction, lock, replacement, rollback, recovery-notice, signal, and
  input-stability tests; migrated Step `08`/`09` private loaders; artifact/run-
  summary/report and independent-golden consumers; public CLI/Make routes;
  coverage; current runbook/troubleshooting; and the thirteen-file transaction.

## Questions owned by this card

- Which smallest old-path test-only slices are required for input admission,
  publication/summary visibility, predecessor replacement, rollback/incomplete
  restoration, signals/locks/concurrency, stale paths, unrelated bytes, and
  retained recovery evidence?
- Which of the manifests, Step `08`/`09` files, review plan, evidence manifest,
  and evidence payloads are snapshot-bound and rechecked, and which mutation
  or attempt identities remain absent?
- Which compact matrices preserve exact schema/category/state/decision/
  adjudication gates, reserved biological-state rejection, dry-run/execute
  bytes, and exit behavior without changing policy?
- Which import-loader cases protect Step `08`/`09`, artifact, run-summary,
  fixtures, and independent goldens under initialization, cache collision,
  wrong-file, partial execution, and sanitized failure?
- Which shell/Python resolution, arbitrary-CWD, publication-fault, artifact/
  run-summary/report, and coverage cases are sufficient for path-only parity?

## In scope

- Test-gap inventory; minimal checkpoint ordering; exact input/stability/
  transaction/restore/signal/concurrency oracles; schema/state/evidence gates;
  import-consumer faults; shell/Python resolution; artifact/run-summary/report
  meaning; coverage policy; and rollback consequences.

## Out of scope

- Production mutation; defect fixes; dependency installation; schema/state/
  policy extraction; public imports; new recovery or attempt markers;
  transaction/artifact/report redesign; scheduler/cluster/production or
  completed scientific-review work; and future packages.

## Deliverables

- Finding-by-finding reliability disposition and the smallest ordered test-
  only slices required before atomic cutover, recorded in `MIG-03O` and the
  audit.

## Acceptance evidence

- Every high-risk state has an existing or required safe local oracle with
  exact bytes, paths, streams, exits, locks, backups, recovery notice, residue,
  unrelated files, import identity, and evidence ceiling. No oracle requires a
  production behavior, dependency, schema, state, or scientific-meaning change.

## Canonical documentation updates

- This card, `MIG-03O`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk restoration/mutation/import/state path lacks a safe local
  oracle, parity needs production or dependency work, bytes must change beyond
  reviewed paths, or a defect must be fixed or blessed.

## Completion record

Not selected. Blocked on unselected `REVIEW-ARCH-03O`; no executable/test/
configuration file changed or ran.
