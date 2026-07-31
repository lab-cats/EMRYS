# RPT-05B — Decompose report rendering modules

## Objective

Split oversized report rendering into cohesive model, projection, format,
publication, and dispatch modules inside the final reporting owner.

## Why this exists

The report renderer is a mandatory large-file family and currently participates
in an import cycle. Bounded decomposition should reduce cognitive load without
changing public/report contracts or duplicating the relocation concern.

## Fixed decisions

- This card owns the report-renderer large-file disposition; do not create a
  duplicate `SIZE-07C` card.
- Decompose along observed seams, not arbitrary line targets.
- Preserve explicit-input, deterministic, profile, format, accessibility,
  transaction, rollback, receipt-last, and direct-invocation contracts.
- Shared neutral report code remains inside the reporting domain unless broader
  reuse independently satisfies the library-promotion rule.

## Blocked by

- [RPT-05A](../TODO/RPT-05A-relocate-reporting-to-final-source-home.md) — Required: decomposition must occur in the final ownership boundary.

## Completion unblocks

- [RPT-06](../TODO/RPT-06-make-science-report-the-default.md) — Fully: the stable decomposed domain can safely expose the new default.

## Prerequisites

- Refresh line counts, import graph/cycle, private-helper consumers, coverage,
  and exact report transaction fault matrix.

## Required context

- `RPT-05A`, comprehensive/science contracts, `RA-006` and `RA-008`, report
  tests/assets, target topology, and shared-library policy.

## Questions owned by this card

- None.

## In scope

- Neutral models, projection/format boundaries, dispatch, publication, import
  cycle removal, focused module tests, and compatibility shims if temporary.

## Out of scope

- New report features, default activation, generic rendering frameworks,
  source relocation, or changing deterministic outputs.

## Deliverables

- Cohesive modules, removed cycle, narrower tests, and updated size disposition.

## Acceptance evidence

- No resulting module mixes unrelated responsibilities or exceeds the size
  policy without explicit review.
- Complete report parity, deterministic, fault, direct-import, and runtime
  renderer gates pass.

## Canonical documentation updates

- Current architecture, report/module READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, and this card.

## Escalation conditions

- Stop if extraction would change bytes, weaken transaction recovery, create a
  generic utility, or require simultaneous unrelated report redesign.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
