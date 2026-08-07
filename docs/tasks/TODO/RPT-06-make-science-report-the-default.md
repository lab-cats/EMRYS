# RPT-06 — Make science report the default

## Objective

Switch the public default to the approved science profile while preserving an
explicit comprehensive profile and immutable output coexistence.

## Why this exists

The usability benefit is not realized until a normal run produces the concise
science report, but changing a default is a public contract migration that must
happen only after content, UX, relocation, and decomposition are stable.

## Fixed decisions

- Science becomes the default; comprehensive remains explicitly selectable.
- Public profile names/flags follow the approved `RPT-02` contract.
- Existing report bundles are not overwritten or silently reinterpreted.
- Default selection does not promote evidence or change analysis.

## Blocked by

- [RPT-04](../TODO/RPT-04-implement-science-report-usability.md) — Required: the science presentation and cross-format usability contract must be implemented before it becomes the default.
- [RPT-05B](../TODO/RPT-05B-decompose-report-rendering-modules.md) — Required: report ownership and internals must be stable before the public default changes.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: the final audit also requires logging, size, documentation-skill, and generated in-scope tasks.

## Prerequisites

- Reconfirm all current consumers, Make/demo commands, output paths, receipts,
  migration notices, and comprehensive-profile tests.

## Required context

- All preceding report cards, CLI contracts, run request/report selection,
  schemas/receipts, docs, demos, and user journeys.

## Questions owned by this card

- None.

## In scope

- Default/flag wiring, output naming/coexistence, migration documentation,
  comprehensive regression, and end-to-end science-default tests.

## Out of scope

- Removing comprehensive reporting, adding fields, changing logging verbosity,
  or modifying science computations/evidence states.

## Deliverables

- New default behavior, explicit comprehensive selection, coexistence tests,
  and updated user/operator documentation.

## Acceptance evidence

- An omitted profile produces exactly the approved science bundle; an explicit
  comprehensive request reproduces its protected contract.
- Both profiles coexist deterministically without overwrite or evidence change.

## Canonical documentation updates

- `README.md`, `ARCHITECTURE.md`, `RUNBOOK.md`, `TROUBLESHOOTING.md`, schemas or
  configs if approved, diagrams, `PIPELINE_PLAN.md`, `HANDOFF.md`, this card,
  and only verified presenter or audience guides whose reviewed user journey
  changes. Do not silently edit opaque or dormant preservation bodies or treat
  them as current consumers.

## Escalation conditions

- Stop if a consumer cannot migrate, bundle identity is ambiguous, or default
  selection changes artifacts beyond the declared report projection.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
