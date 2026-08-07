# RPT-04 — Implement science report usability

## Objective

Build clear, accessible HTML and PDF presentations of the science projection
without inner-panel horizontal scrolling.

## Why this exists

The current comprehensive report optimizes breadth, leaving dense tables and
local scroll regions that can overwhelm a typical scientist. The new default
needs strong hierarchy, plain descriptions, and readable responsive/print
behavior.

## Fixed decisions

- Use the approved science projection without adding/removing fields in view
  code.
- Provide proper titles and descriptions for every field/section.
- Avoid inner-panel horizontal scrolling in the science view; transform wide
  information into responsive records, summaries, or deliberate page layout.
- Preserve accessibility, explicit evidence banners, and HTML/PDF semantic parity.

## Blocked by

- [RPT-03](../TODO/RPT-03-build-format-neutral-report-projection.md) — Required: the renderer-independent science model must be stable.

## Completion unblocks

- [RPT-06](../TODO/RPT-06-make-science-report-the-default.md) — Partially: default activation also requires stable decomposed reporting internals.

## Prerequisites

- Establish representative narrow/wide browser, keyboard, print, and PDF cases
  without downloading new tooling implicitly.

## Required context

- Science projection, accessibility/usability review, current style/report
  fixtures, comprehensive view, Quarto/Typst constraints, and evidence language.

## Questions owned by this card

- None.

## In scope

- Information hierarchy, titles/descriptions, responsive records, print/PDF
  layout, keyboard/focus behavior, banners, and readability tests.

## Out of scope

- Changing the field contract, source relocation, default activation,
  JavaScript-heavy application behavior, or comprehensive-view redesign.

## Deliverables

- Science HTML/PDF templates/styles and focused accessibility/usability tests.

## Acceptance evidence

- Required science information is usable without nested horizontal scrolling
  across approved viewport/print cases.
- Keyboard, structural, text-extraction, banner, and HTML/PDF parity checks pass.

## Canonical documentation updates

- `ARCHITECTURE.md`, report documentation, `TROUBLESHOOTING.md` for current
  behavior only after implementation, `PIPELINE_PLAN.md`, `HANDOFF.md`, and
  this card.

## Escalation conditions

- Stop if removing scroll requires hiding contracted science information or if
  HTML and PDF must communicate different evidence meaning.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
