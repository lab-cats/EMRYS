# REVIEW-REL-02 — Review reliability plan

## Objective

Independently challenge transaction, identity, retry, concurrency, recovery,
logging, scheduler, and evidence-preservation behavior in the integrated plan.

## Why this exists

NORAD's similar-looking publication paths have important state-machine
differences. Relocation, ingestion, logging, and decomposition can introduce
TOCTOU, rollback, stale-lock, or evidence-loss regressions even when topology
looks clean.

## Fixed decisions

- Review only; do not normalize characterized unsafe states or implement fixes.
- Preserve independent validation layers and receipt/summary-last semantics.
- Runtime, cluster, scientific, and biological evidence states remain distinct.

## Blocked by

- [REVIEW-ARCH-01](../TODO/REVIEW-ARCH-01-review-architecture-plan.md) — Required: reliability review needs an architecture-corrected plan.

## Completion unblocks

- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Partially: usability review also requires the glossary foundation.

## Prerequisites

- Assign a reviewer/agent independent from the plan author and architecture
  reviewer where practical.

## Required context

- Transaction/fault characterization, intake state machine, migration mechanics,
  logging contract, scheduler contracts, evidence schemas, and recovery docs.

## Questions owned by this card

- None.

## In scope

- Lock ownership, staging, stable-input rechecks, hashes, no-clobber, signals,
  rollback, recovery markers, run/attempt identity, retries, stream/log failure,
  scheduler materialization, and deterministic serialization.

## Out of scope

- Implementing corrections, automatic cleanup, weakening evidence checks, or
  treating a characterized defect as a preserved safe contract.

## Deliverables

- Evidence-ranked reliability findings, fault-scenario gaps, and exact card
  revisions/additions.

## Acceptance evidence

- Every affected state machine has explicit success/failure/recovery acceptance
  and no plan step can erase or mislabel evidence.
- Accepted risks have owner, rationale, and recheck trigger.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, task registry, `QUESTIONS.md`, `DECISIONS.md` only for
  approved durable changes, and this card.

## Escalation conditions

- Stop for a risk that cannot be bounded without runtime/cluster evidence,
  operator policy, or a destructive recovery decision.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
