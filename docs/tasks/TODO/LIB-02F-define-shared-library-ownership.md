# LIB-02F — Define shared-library ownership

## Objective

Turn the approved promotion rule into an implementation-backed map of local,
shared, and intentionally independent code ownership.

## Why this exists

Repeated parsing, publication, and validation vocabulary suggests extraction,
but similar-looking safety state machines and scientific checks often differ.
Premature DRY abstractions could create repository-wide coupling or common-mode
test defects.

## Fixed decisions

- Keep the first use local. At the second use, compare full semantics; extract
  at two only if safety-critical or complex, otherwise normally at the third.
- Place an abstraction in the narrowest neutral owner; shared code never
  depends on stages.
- Require independent API and consumer tests; do not force cross-language DRY.
- Preserve intentionally independent validation and transaction logic.

## Blocked by

- [ARCH-02A](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md) — Required: observed reuse and ownership must be inventoried.
- [ARCH-02C](../TODO/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: the neutral ownership domains and dependency direction must be settled.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: shared-library scope is one required design input.

## Prerequisites

- Build semantic comparisons for candidate repeated code, including failure,
  recovery, determinism, and scientific meaning.

## Required context

- `REFACTOR_AUDIT.md` findings `RA-007`, `RA-009`, `RA-020`, `RA-022`, and
  `RA-024`, the functional inventory, import graph, tests, and target topology.

## Questions owned by this card

- None.

## In scope

- Candidate ownership matrix, promotion/retention rationale, allowed APIs,
  dependency constraints, and test obligations.

## Out of scope

- Extracting libraries, creating `utils`, universal transaction frameworks,
  generic dispatchers, or sharing the rule an independent test verifies.

## Deliverables

- A reviewed shared-library promotion matrix and concrete extraction or
  retention cards where justified.

## Acceptance evidence

- Every proposed shared seam demonstrates equivalent semantics and a narrower
  owner; every retained duplicate states the independence or locality value.
- No proposed shared library imports a stage or erases language boundaries.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, `DECISIONS.md` if the policy changes,
  `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if equivalence depends on names rather than behavior, extraction would
  weaken recovery/science boundaries, or consumers would need a catch-all API.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
