# RPT-01 — Characterize the comprehensive report

## Objective

Freeze the current comprehensive report's content, data provenance,
interaction, transaction, and format behavior before introducing a new default.

## Why this exists

The current report is valuable as a complete diagnostic view but is too dense
for the default scientist experience. A new science-facing view must not
silently lose evidence or weaken the existing bundle.

## Fixed decisions

- Retain the current comprehensive report explicitly; do not redefine it as
  the future science view.
- Report generation remains a projection of one validated canonical summary
  and authorized tables, never evidence generation.
- Existing bundles remain immutable and new outputs must coexist without
  overwrite.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest behavior-sufficiency decision is affirmative.

## Completion unblocks

- [RPT-02](../TODO/RPT-02-define-science-report-contract.md) — Fully: the science view can be specified against a protected comprehensive baseline.

## Prerequisites

- Refresh current renderer entry points, approved table roles, bundle formats,
  fixtures, receipts, and interaction tests.

## Required context

- Current report implementation, schemas, styles, Quarto assets, report tests,
  `ARCHITECTURE.md`, demo contract, run summary, and authorization rules.

## Questions owned by this card

- None.

## In scope

- Exact field/section inventory, source-to-view traceability, default `all`
  behavior, wide-table scrolling, HTML/PDF/TSV semantics, accessibility,
  determinism, and receipt-last publication.

## Out of scope

- Changing the report, deleting sections, renaming public profiles, moving
  modules, or accepting current usability as the target design.

## Deliverables

- A comprehensive-report contract/catalog and focused missing characterization
  tests if separately approved by this card's plan.

## Acceptance evidence

- Every current report field and interaction maps to an authorized source and
  a protected behavior or explicit characterized defect.
- HTML/PDF/TSV and transaction behavior are independently traceable.

## Canonical documentation updates

- `TEST_BASELINE.md` when new characterization lands, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, `QUESTIONS.md`, and this card.

## Escalation conditions

- Stop if a field's provenance is implicit, a current display encodes an
  unsupported scientific claim, or characterization would require behavior
  changes.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
