# DOC-CONS-08E — Separate live state from history

## Objective

Remove completed and dated narrative from live handoff, roadmap, and
concurrency views after moving it to the established history/card owners.

## Why this exists

`HANDOFF.md`, `PIPELINE_PLAN.md`, and `CONCURRENT_WORK.md` mix current takeover
truth with completed rosters, branch lineage, timings, totals, and dated
first-use milestones. That duplication makes stale history look operational.

## Fixed decisions

- `HANDOFF.md` retains current checkout, lanes, blockers, evidence boundary,
  and exact resume point.
- `PIPELINE_PLAN.md` retains current roadmap/status/acceptance and branch
  lineage required for active delivery.
- `CONCURRENT_WORK.md` retains durable authority and lifecycle policy.
- Completed cards and `docs/history/` own frozen evidence; links replace copied
  rosters and narratives.

## Blocked by

- [DOC-CONS-08D](DOC-CONS-08D-establish-dated-documentation-history.md) — Required: dated material needs an indexed history destination before removal.

## Completion unblocks

- None.

## Prerequisites

- Reconcile live Git/card status and current evidence immediately before
  editing; use the then-current values, not the DOC-IA audit snapshot.

## Required context

- Only the current/completed boundary sections of `HANDOFF.md`,
  `PIPELINE_PLAN.md`, and `CONCURRENT_WORK.md`, their direct cards/history
  destinations, and the source ledger.

## Questions owned by this card

- None.

## In scope

- Creating and registering the `docs/history/operations/` child beneath the
  established shallow history index.
- Moving dated operational/lineage records to the established history owner or
  linking existing completed cards.
- Compressing duplicate completion rosters, totals, timings, and first-use
  state after no-loss review.
- Retaining concise current evidence and status tables with explicit evidence
  boundaries.
- Repairing direct links and removing old copies.

## Out of scope

- Changing branch state, card lifecycle, roadmap decisions, runtime/scientific
  evidence, concurrency authority, commands, or historical records.

## Deliverables

- One indexed operational-history child and three concise live owners whose
  remaining mutable facts are unambiguously current.

## Acceptance evidence

- Current checkout/lane/blocker/evidence/resume facts remain in `HANDOFF.md`.
- Current roadmap/status/acceptance/required lineage remain in
  `PIPELINE_PLAN.md`.
- Concurrency authority and recovery policy remain in `CONCURRENT_WORK.md`.
- Every removed historical fact exists once in history or a completed card.
- Documentation links and the documentation gate pass.

## Canonical documentation updates

- `HANDOFF.md`, `PIPELINE_PLAN.md`, `CONCURRENT_WORK.md`, affected history/card
  links, the ownership ledger, and this card.

## Escalation conditions

- Stop if a statement cannot be classified as current or historical, owners
  disagree, or evidence/lineage would become ambiguous.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
