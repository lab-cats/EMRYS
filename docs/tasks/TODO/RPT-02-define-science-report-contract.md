# RPT-02 — Define the science report contract

## Objective

Define the minimal scientist-facing content model, descriptions, profile
interface, and cross-format semantics that will become the future default.

## Why this exists

Most scientists need the evidence necessary to interpret the data, not every
operational and diagnostic field. A field-level contract is required before
UI work so “minimal” does not become subjective or scientifically incomplete.

## Fixed decisions

- The future default is science-facing; the current comprehensive view remains
  explicitly available.
- Start from evidence state, CMH-ranked findings, QC/filter funnel,
  sensitivity/replicates, decisions/limitations, and concise methods.
- Use a format-neutral projection with HTML/PDF semantic parity.
- The science view has no inner-panel horizontal scrolling.
- Profile outputs coexist and do not overwrite immutable existing bundles.

## Blocked by

- [RPT-01](../TODO/RPT-01-characterize-comprehensive-report.md) — Required: the retained comprehensive baseline must be known first.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: report design is one input to the integrated sequence.
- [RPT-03](../TODO/RPT-03-build-format-neutral-report-projection.md) — Partially: implementation also waits for the independent reviews.

## Prerequisites

- Reconcile every candidate science field with canonical summary/table roles
  and evidence-language restrictions.

## Required context

- `RPT-01`, report schemas and fixtures, scientific-state decisions,
  Step `07`–`09c` evidence boundaries, demo feedback, and future report diagram.

## Questions owned by this card

- [`CHOICE-REPORT-01`](../../design/QUESTIONS.md#choice-report-01--public-report-profile-names-and-selection-interface).
- [`CHOICE-REPORT-02`](../../design/QUESTIONS.md#choice-report-02--exact-science-report-field-roster).
- [`CHOICE-REPORT-03`](../../design/QUESTIONS.md#choice-report-03--profile-output-layout-and-transaction-boundary).

## In scope

- Field catalog, plain-language titles/descriptions, inclusion rules,
  ordering, missing/failed/empty states, profile names/selection, HTML/PDF
  parity, and output coexistence.

## Out of scope

- Rendering implementation, default activation, module relocation,
  comprehensive-view deletion, or new scientific computation.

## Deliverables

- A versioned science-view contract and format-neutral field catalog.
- Accessibility/usability acceptance scenarios and implementation-card inputs.

## Acceptance evidence

- A scientist can identify what happened, what passed/failed, what was found,
  why it matters, and the limitations without reading operational diagnostics.
- Every displayed value has one authorized source and neutral evidence language.

## Canonical documentation updates

- `DECISIONS.md`, `FUTURE_ARCHITECTURE.md`, future reporting diagram,
  `QUESTIONS.md`, `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if a field requires new analysis, collapses computational and
  scientific state, or forces HTML/PDF semantic divergence.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
