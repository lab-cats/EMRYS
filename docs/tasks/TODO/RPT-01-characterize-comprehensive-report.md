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
- Immutable coexistence without overwrite remains the target. Current behavior
  instead replaces the prior receipt-declared set at stable paths through
  observable absence and partial windows, and complete-set format transitions
  can delete a prior presentation; characterize those divergences as defects
  without changing them in this package.

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
- Only verified presenter or audience guides are narrative consumers whose
  report and evidence wording must be characterized. Dormant, opaque,
  unverified demo bodies are preservation sources, not report-contract inputs.

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

- A test-supported catalog classifying each observed behavior as a preserved
  contract, characterized defect, or environment-deferred observation. Cover
  exhaustive HTML; smaller PDF; 13-column summary TSV; 17-column receipt TSV/
  JSON; authorized supplemental roles; disclosure ordering; determinism;
  receipt-last behavior; and the `html|pdf|all` format interface with `all` as
  default and no report-profile selector.
- Characterization of the canonical-builder versus public-renderer trust
  boundary; complete known and safe unknown role handling; responsive/browser/
  print evidence limits, including that the column-count focusability heuristic
  has no live-browser, responsive-viewport, or print validation; replacement,
  partial-publication, and format-
  transition windows; attempt identity; omitted CSS/renderer/tool identity;
  unused PDF input recorded for HTML-only builds; and the `all` receipt's exact
  defect of recording only the PDF template while omitting the HTML QMD and
  CSS. Also cover limited SVG ARIA checks and hostile PDF terminology or markup
  risk.
- Focused public-bundle transition and fault tests with test-owned expected
  values and ordering, including exact TSV/receipt contents, disclosure order,
  renderer authorization, attempt identity, resolved SVG descriptions, and
  hostile PDF extracted text. Production corrections remain separately
  selectable work rather than characterization changes.

## Acceptance evidence

- Every current report field and interaction maps to an authorized source and
  a protected behavior or explicit characterized defect.
- HTML/PDF/TSV and transaction behavior are independently traceable.
- Every catalog row cites its focused test or inspected artifact. Live-browser,
  responsive, print, unavailable-runtime, scientific, and biological claims
  remain outside the evidence unless independently observed.

## Canonical documentation updates

- `TEST_BASELINE.md` when new characterization lands, `PIPELINE_PLAN.md`,
  `ARCHITECTURE.md`, `HANDOFF.md`, `QUESTIONS.md`, and this card. Factual
  current-architecture changes wait for the repaired tests and final catalog.

## Escalation conditions

- Stop if a field's provenance is implicit, a current display encodes an
  unsupported scientific claim, or characterization would require behavior
  changes.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
