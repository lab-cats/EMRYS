# ARCH-02A — Inventory functional stages and contracts

**JIT slice record**

- Slice 1 records historical Step `00a` under the working name
  `construct_STAR_index` in its colocated
  [`CONTRACT.md`](../../../src/norad/stages/construct_STAR_index/CONTRACT.md).
  The slice inventories current behavior and the shared-validator ownership
  leak without moving code or settling later naming, topology, extraction, or
  migration decisions.

## Objective

Produce an implementation-backed inventory of functional stages, shared
domains, public entry points, and cross-stage contracts.

## Why this exists

Numeric names and flat `scripts/`/`jobs/` ownership obscure what each stage
does and where one stage's responsibility ends. A vertical target cannot be
designed safely from filenames alone.

## Fixed decisions

- Inventory behavior before choosing target names or moving files.
- Treat stages as future black boxes whose neighbors know only typed input and
  output contracts; do not infer a universal preprocessing trunk.
- Preserve current numeric identifiers as historical provenance until a
  [semantic map](../../design/DECISIONS.md#identify-stages-semantically-and-order-them-with-a-dag)
  is approved.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest sufficiency decision is affirmative.

## Completion unblocks

- [ARCH-02B](../TODO/ARCH-02B-define-semantic-stage-map.md) — Fully: semantic names can be derived from inspected responsibilities.
- [LIB-02F](../TODO/LIB-02F-define-shared-library-ownership.md) — Partially: shared-domain candidates also require the target topology.
- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Partially: size findings can be mapped to functional ownership.

## Prerequisites

- Refresh the live script, job, test, schema, config, report, and Make-target
  inventories.

## Required context

- Current `ARCHITECTURE.md` and `pipeline.mmd`, `REFACTOR_AUDIT.md`,
  `TEST_BASELINE.md`, all public entry points, their consumers, and directly
  associated tests/contracts.

## Questions owned by this card

- None.

## In scope

- Stage purposes, entry points, job boundaries, inputs, outputs, validators,
  contracts, consumers, shared domains, and observed dependency direction.
- Explicit classification of orchestration, scheduler, evidence, reporting,
  ingestion, and library responsibilities that are not stages.

## Out of scope

- Renaming, relocation, package creation, generic abstraction, or changing
  current step order and behavior.

## Deliverables

- A source-backed stage/domain inventory with unresolved ambiguities called out.
- Direct links from each row to implementation and protected tests.

## Acceptance evidence

- Every current public workflow entry point and validator maps exactly once to
  a functional owner or an explicitly justified cross-cutting domain.
- Inputs, outputs, upstream/downstream consumers, and contract ownership are
  traceable without relying on filename inference.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, `FUTURE_ARCHITECTURE.md` only if the target constraints
  need correction, `QUESTIONS.md`, and this card.

## Escalation conditions

- Stop if one file's mixed responsibilities cannot be assigned without making
  an implementation decision, or if scientific boundaries are ambiguous.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
