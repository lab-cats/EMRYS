# REVIEW-ARCH-03A — Review validation-publication migration architecture

## Objective

Challenge the ownership, dependency direction, import strategy, and reversible
cutover proposed for `MIG-03A` before executable work begins.

## Why this exists

The shared protocol is currently hidden inside a stage-named validator. A
careless extraction could replace one reverse dependency with packaging
bootstrap, a generic utility bucket, duplicate ownership, or a permanent
compatibility layer.

## Fixed decisions

- Review only; corrections land in the planning/card documentation, never in
  executable source under this card.
- Apply the approved neutral-library threshold, vertical topology, and direct
  migration mechanics without reopening them absent contradictory evidence.
- Reject stage-to-stage implementation imports, generic `utils`, global
  `PYTHONPATH` assumptions, dependency installation, and permanent wrappers.

## Blocked by

- [PLAN-02Z](../COMPLETED/PLAN-02Z-integrate-future-task-sequence.md) — Required: the proposed unit, owner, consumer roster, and migration card must exist.

## Completion unblocks

- [REVIEW-REL-03A](../TODO/REVIEW-REL-03A-review-validation-publication-migration.md) — Fully: reliability review can inspect an architecture-corrected unit.

## Prerequisites

- Review a committed planning checkpoint without editing executable files; use
  a separate reviewer where available and otherwise record the reviewer-
  independence limitation explicitly.

## Required context

- `MIG-03A`, `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, the functional-
  owner inventory, `RA-007`, the complete direct import graph, all proposed
  current/final paths, and direct-script arbitrary-working-directory evidence.

## Questions owned by this card

- None.

## In scope

- Neutral-owner fitness, API cohesion, dependency direction, local import
  bootstrap, wrapper necessity, one-implementation invariant, test ownership,
  caller-cutover order, rollback order, and later stage-migration compatibility.

## Out of scope

- Publication fault semantics except where ownership obscures them, code
  changes, packaging/distribution, later shared-library candidates, or any
  stage migration.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions and exact
  `MIG-03A` corrections recorded in the dated refactor log.

## Acceptance evidence

- No unresolved owner, dependency-direction, import, wrapper, duplicate-
  implementation, or rollback question remains in `MIG-03A`.
- Every finding is reflected in the card or explicitly retained with a named
  consequence and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03A`, `PIPELINE_PLAN.md` if sequencing changes, and the dated
  pre-migration refactor log.

## Escalation conditions

- Stop if a usable final import requires packaging work, an unapproved global
  bootstrap, or a second neutral concern.

## Completion record

Not started. Selection authorizes review only, not implementation.
