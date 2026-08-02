# REVIEW-REL-03A — Review validation-publication migration reliability

## Objective

Challenge `MIG-03A` against the complete validation-report publication and
stable-input fault evidence before executable work begins.

## Why this exists

Relocating a shared safety-critical protocol can silently normalize known
faults, weaken monkeypatch/fault coverage, or alter exception, cleanup, lock,
and rollback behavior even when normal validator output is unchanged.

## Fixed decisions

- Review only; do not correct or bless a characterized defect.
- Preserve the exact seven-column report, per-stage roster ownership, readable
  failed reports, malformed/unsafe failure behavior, and existing lock,
  staging, rollback, cleanup, and retry semantics.
- Do not infer that other repository publication transactions are equivalent.

## Blocked by

- [REVIEW-ARCH-03A](../IN_PROGRESS/REVIEW-ARCH-03A-review-validation-publication-migration.md) — Required: reliability review needs the corrected owner/API/cutover boundary.

## Completion unblocks

- [REVIEW-UX-03A](REVIEW-UX-03A-review-validation-publication-migration.md) — Fully: user-facing continuity can be reviewed after safety obligations are fixed.

## Prerequisites

- Start from the committed architecture-reviewed card and map each existing
  fault test to the final implementation owner without running or modifying it.

## Required context

- `MIG-03A`, `RA-002`, `RA-009`, `RA-019`, the test-baseline risk checklist,
  `test_validation_publication_faults.py`, check-roster and independent-golden
  tests, and all shared symbols currently embedded in the Step `00a` validator.

## Questions owned by this card

- None.

## In scope

- Stable snapshots, deterministic bytes, exception identity/messages, report
  validation, lock creation, staged fsync, predecessor validation/replacement,
  rollback, cleanup, interruption, late collisions, residue, and the known
  report-row-order boundary.

## Out of scope

- Fixing metadata-only rewrite blindness, late foreign-final deletion,
  incomplete rollback/recovery, cleanup failures, stale locks, or any unrelated
  transaction protocol.

## Deliverables

- A risk-to-test disposition for each applicable publication state and exact
  additions or corrections required in `MIG-03A`.

## Acceptance evidence

- Every known success, failure, interruption, and residue state has a named
  preserved or characterized-defect disposition and regression owner.
- The planned validation gate distinguishes local fixture evidence from
  runtime, cluster, scientific-review, and biological-readiness evidence.

## Canonical documentation updates

- This card, `MIG-03A`, `PIPELINE_PLAN.md` if sequencing changes, and the dated
  pre-migration refactor log.

## Escalation conditions

- Stop if parity requires changing a fault state, deleting recovery evidence,
  or relying on runtime/cluster behavior not present in the local baseline.

## Completion record

Not started. Selection authorizes review only, not implementation.
