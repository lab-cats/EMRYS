# DOC-CONS-08G — Consolidate demo views

## Objective

Keep distinct walkthrough and PI discussion value while consolidating shared
product/report prose and giving any cohort snapshot a dated evidence owner.

## Why this exists

The two demo documents repeat product, report, and evidence prose. They also
contain presentation-specific narrative and scientific cautions that are
useful at the action point, while one undated cohort snapshot is currently
described elsewhere as dated.

## Fixed decisions

- Preserve walkthrough order, the PI evidence-model table, discussion prompts,
  and presentation action-point scientific cautions.
- Shared mutable product/report/current-evidence facts link their canonical
  owners rather than remaining copied.
- A historical snapshot must be explicitly dated/provenanced beneath the
  established history owner or removed as a current claim; do not invent a
  date.

## Blocked by

- [DOC-CONS-08D](../IN_PROGRESS/DOC-CONS-08D-establish-dated-documentation-history.md) — Required: a dated demo snapshot needs an indexed history destination.

## Completion unblocks

- None.

## Prerequisites

- Verify whether the cohort snapshot has repository-backed date/provenance and
  whether `PI_DEMO_REPORT.md` is a current presentation or a frozen snapshot.

## Required context

- The two demo files, direct root/current-evidence/report links, the history
  index, and the demo rows in `DOCUMENTATION_OWNERSHIP.md`.

## Questions owned by this card

- None.

## In scope

- Creating and registering the `docs/history/demos/` child beneath the
  established shallow history index when a dated snapshot is retained.
- Adding local demo navigation if not already supplied by `DOC-README-03`.
- Replacing shared mutable prose with precise owner links.
- Dating/archiving the cohort snapshot or removing its stale current copy after
  preserving any unique evidence.
- Relabeling presentation versus historical artifacts accurately and repairing
  direct links.

## Out of scope

- Changing report behavior, evidence state, scientific conclusions, current
  handoff truth, or presentation-specific safety cautions.

## Deliverables

- Two distinct, concise demo views and one explicit disposition for every
  snapshot/history statement.

## Acceptance evidence

- Walkthrough narrative, PI evidence table, prompts, and cautions remain.
- No demo owns mutable current evidence or report contracts.
- Every historical statement is dated/provenanced and indexed exactly once.
- Documentation links and the documentation gate pass.

## Canonical documentation updates

- `docs/demo/`, affected root/history/current-evidence links, the ownership
  ledger, and this card.

## Escalation conditions

- Stop if a snapshot cannot be dated/provenanced or consolidation weakens a
  scientific caveat needed during presentation.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
