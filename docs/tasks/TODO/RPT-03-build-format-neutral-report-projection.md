# RPT-03 — Build format-neutral report projection

## Objective

Implement the versioned science-view projection as a renderer-independent model
derived only from authorized canonical inputs.

## Why this exists

HTML-first selection would make PDF parity fragile and entangle scientific
content decisions with layout. A neutral projection gives both formats the
same fields, ordering, missing states, and language.

## Fixed decisions

- Implement the approved `RPT-02` field catalog exactly.
- Projection consumes one validated canonical run summary and explicitly
  authorized tables; it does not discover files or compute evidence.
- HTML and PDF share semantic content while retaining format-appropriate layout.
- Preserve deterministic serialization and immutable existing bundles.

## Blocked by

- [RPT-02](../TODO/RPT-02-define-science-report-contract.md) — Required: the versioned field/profile contract must be approved.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent plan reviews must be incorporated.
- [RPT-05A](../IN_PROGRESS/RPT-05A-relocate-reporting-to-final-source-home.md) — Required: new projection implementation must begin inside the final reporting owner rather than extending the temporary flat tree.

## Completion unblocks

- [RPT-04](../TODO/RPT-04-implement-science-report-usability.md) — Fully: UI work can consume a stable neutral model.

## Prerequisites

- Reconfirm live run-summary/report schema versions and behavior-test parity at
  the selected predecessor.

## Required context

- Science report contract, comprehensive characterization, schemas, summary
  policy projection, approved table roles, renderer tests, and migration plan.

## Questions owned by this card

- None.

## In scope

- Typed projection model, validation, deterministic serialization, independent
  tests, and explicit comprehensive/science separation.

## Out of scope

- Final HTML/CSS/PDF layout, source relocation, changing defaults, new
  computations, or deleting comprehensive fields.

## Deliverables

- Projection implementation, schema/contract changes if approved, focused
  tests, and parity fixtures.

## Acceptance evidence

- Identical canonical inputs produce semantically identical HTML/PDF projection
  data and deterministic bytes where contracted.
- Missing, failed, exploratory, empty, and reserved states remain lawful and
  neutrally worded.

## Canonical documentation updates

- `ARCHITECTURE.md`, `RUNBOOK.md` if an explicit command changes,
  `PIPELINE_PLAN.md`, schemas/contracts, `HANDOFF.md`, and this card.

## Escalation conditions

- Stop if projection needs an undeclared input, analysis computation, evidence
  promotion, or format-specific scientific field.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
