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

- A versioned science-view contract and format-neutral field catalog covering
  authorized normalized experimental design, cohort, condition/contrast,
  organism/reference build, genomic locus, gene/transcript, run/attempt,
  source hashes, and explicit unavailable states without manufacturing
  metadata in reporting. Preserve the source six-section proposal and field
  tables only as inputs to correct and review, never as settled truth.
- A mechanical RFC 6901, multi-binding, selector, and keyed-join grammar that
  enumerates every field ID, unit, exact source, display state, and mapping;
  separates projection availability from domain status; and exhaustively maps
  blocked, not-run, failed, empty, externally unavailable, and successful
  states.
- Literal non-executable rendering and hostile markup/Unicode extracted-text
  equality across HTML and PDF, semantic parity, and no inner-panel science
  scrolling. Accessibility/usability scenarios include 320-, 768-, and
  1280-pixel viewports, keyboard order, print expansion, and PDF extracted
  text; proposed scenarios are inputs to prove, not current evidence.
- Selector and normalized-reporting semantics, profile/request receipts,
  retry/supersession identity, used implementation/tool/template/style hashes,
  content-addressed no-clobber bundles, and either one parent completion
  receipt with explicitly allowed pre-completion cache visibility or one atomic
  request-root publication. Correct the reporting diagram so profile and
  format selection are conditional rather than unconditional parallel output.
- Explicit ownership: `INTAKE-02E` retains top-level V1 YAML syntax,
  validation, and representation; an upstream canonical metadata/schema owner
  supplies normalized reporting fields; and every selector, projection,
  layout, comprehensive-PDF, publication, dispatch, rollback, and default-
  activation interface has one downstream owner before release.

## Acceptance evidence

- A scientist can identify what happened, what passed/failed, what was found,
  why it matters, and the limitations without reading operational diagnostics.
- Every displayed value has one authorized source and neutral evidence language.
- Independent science/usability, accessibility, architecture, transaction, and
  security review passes before any `RPT-03` or later feature implementation
  is released. Corrected and freshly reviewed `RPT-01` evidence is the parent;
  this is readiness order, not a new technological blocker.

## Canonical documentation updates

- `DECISIONS.md`, `FUTURE_ARCHITECTURE.md`, future reporting diagram,
  `QUESTIONS.md`, `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if a field requires new analysis, collapses computational and
  scientific state, or forces HTML/PDF semantic divergence.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
