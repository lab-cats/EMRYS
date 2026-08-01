# SIZE-07 — Refresh large-file inventory

## Objective

Refresh the source/test size evidence, map large files to responsibilities and
risks, and create bounded disposition cards before architectural mutation.

## Why this exists

Large mixed-responsibility files make local reasoning and review expensive,
but line count alone does not justify unsafe splitting. The inventory must
combine size, cohesion, contract sensitivity, and scientific constraints.

## Fixed decisions

- More than 600 lines triggers advisory cohesion review when materially
  changed; new files normally stay below 600.
- More than 1,000 lines requires a decomposition plan or explicit justification
  before architectural modification.
- More than 1,500 lines must be eliminated during the active repo-spanning
  refactor unless an explicit exception is approved.
- Split tests by scenario/comprehension rather than arbitrary length.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest sufficiency decision is affirmative.
- [ARCH-02A](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md) — Required: size must be interpreted through functional ownership.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: size dispositions are one integrated-plan input.
- [SIZE-07A](../TODO/SIZE-07A-decompose-artifact-index-builder.md) — Partially: implementation also waits for the independent reviews.
- [SIZE-07B](../TODO/SIZE-07B-decompose-scientific-validation-tooling.md) — Partially: implementation also waits for the independent reviews.
- [SIZE-07D](../TODO/SIZE-07D-decompose-run-summary-builder.md) — Partially: implementation also waits for the independent reviews.
- [SIZE-07E](../TODO/SIZE-07E-resolve-step08-r-module-size.md) — Partially: implementation also waits for the independent reviews.
- [SIZE-07F](../TODO/SIZE-07F-decompose-artifact-contract-validator.md) — Partially: implementation also waits for the independent reviews.

## Prerequisites

- Recompute counts from the live predecessor; the 2026-07-31 snapshot of 15
  files above 600, 10 above 1,000, and 6 above 1,500 is evidence, not a live
  invariant.

## Required context

- `REFACTOR_AUDIT.md` cohesion/coupling findings, current tests/coverage,
  functional-stage inventory, import/consumer graph, and scientific boundaries.

## Questions owned by this card

- None.

## In scope

- Tracked source/test counts, responsibility and risk classification,
  mandatory-family confirmation, exceptions, and additional exact cards.

## Out of scope

- Splitting files, changing behavior, enforcing a blind line-count linter, or
  presuming every long test file is poorly organized.

## Deliverables

- Dated reproducible inventory and disposition table.
- Exact follow-up cards for all mandatory or newly justified large-file work.

## Acceptance evidence

- Every file above 1,000 lines has a reviewed plan/justification; every file
  above 1,500 maps to a mandatory card or explicit exception.
- The six known families remain covered: artifact index, scientific validation,
  report rendering (`RPT-05B`), run summary, Step 08 R, and artifact contracts.

## Canonical documentation updates

- `REFACTOR_AUDIT.md` only as a new dated addendum rather than rewriting old
  evidence, `PIPELINE_PLAN.md`, task registry, and this card.

## Escalation conditions

- Stop if a size disposition would cross scientific-policy boundaries, merge
  unrelated migrations, or split solely to satisfy a number.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
