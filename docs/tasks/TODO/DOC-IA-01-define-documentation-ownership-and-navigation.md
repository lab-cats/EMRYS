# DOC-IA-01 — Define documentation ownership and navigation

## Objective

Create an audience-aware documentation map, responsibility ledger, and
lossless consolidation plan with bounded follow-up cards.

## Why this exists

The documentation corpus has grown through responsibility leak: large owners
are hard to navigate, some facts overlap, and opaque directories/files lack
local context. Cleanup without a ledger risks deleting unique operational or
scientific meaning.

## Fixed decisions

- Preserve one canonical owner per mutable fact and link from secondary views.
- Use `README.md` for eligible durable directories; parent READMEs stay shallow
  and child READMEs own detail.
- Consolidation requires a source-to-destination ledger and no-loss review;
  intentional safety repetition remains at action points.
- Do not create `docs/skills/`; reusable skills belong in the actual skill
  system after the practice is proven.

## Blocked by

- [TEST-01Z](../TODO/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest behavior-sufficiency decision must be affirmative.

## Completion unblocks

- [DOC-REF-02](../TODO/DOC-REF-02-create-glossary.md) — Fully: glossary ownership and navigation will be settled.
- [DOC-README-03](../TODO/DOC-README-03-establish-directory-readme-coverage.md) — Fully: directory-audience and detail rules will be settled.
- [DOC-PIPE-04](../TODO/DOC-PIPE-04-create-user-pipeline-overview.md) — Partially: the semantic stage map is also required.
- [CODEDOC-05](../TODO/CODEDOC-05-inventory-code-documentation.md) — Partially: an affirmative behavior gate is also required.
- [CONTEXT-09](../TODO/CONTEXT-09-define-local-maintainer-context.md) — Partially: target topology and README coverage are also required.
- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: documentation sequencing is one integrated-plan input.

## Prerequisites

- Inventory every tracked Markdown/Mermaid owner, audience, inbound/outbound
  link, duplicated topic, and unique operational/scientific fact.

## Required context

- All canonical documents, demos, architecture diagrams, historical snapshots,
  repository directories, existing documentation gate, and `RA-012` through
  `RA-015`.

## Questions owned by this card

- [`CHOICE-DOC-01`](../../design/QUESTIONS.md#choice-doc-01--documentation-consolidation-overview-and-history-locations).

## In scope

- Audience/navigation map, responsibility matrix, source-to-destination ledger,
  orphan/stale classification, RUNBOOK/TROUBLESHOOTING boundary, historical
  evidence treatment, and creation of concrete `DOC-CONS-08-*` cards.

## Out of scope

- Performing the full consolidation, deleting unique content, editing behavior
  claims before implementation, or building the documentation skill.

## Deliverables

- A no-loss documentation information architecture and exact bounded cleanup
  cards with dependencies and acceptance evidence.

## Acceptance evidence

- Every current document and unique fact has one retained owner/destination or
  an explicitly approved historical disposition.
- A user, operator, scientist, and maintainer each have a short navigable path.

## Canonical documentation updates

- `AGENTS.md`, `README.md`, `DECISIONS.md`, `PIPELINE_PLAN.md`,
  `QUESTIONS.md`, task registry, and this card.

## Escalation conditions

- Stop if two owners contain different live truth, a deletion lacks a mapped
  destination, or safety repetition is mistaken for accidental duplication.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
