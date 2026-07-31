# SIZE-07B — Decompose scientific validation tooling

## Objective

Eliminate the oversized Step `09c` tooling monolith without changing scientific
state policy or validation meaning.

## Why this exists

The roughly 4,500-line module owns shared parsing/hash/table utilities,
Step `08`/`09` contract checks, scientific evidence state, and transaction
publication. Its broad reuse reverses dependency direction and raises change
risk.

## Fixed decisions

- Scientific/statistical algorithms and readiness policy remain unchanged
  absent separate scientific authorization.
- Extract only proven-neutral contracts, parsing, serialization, or publication
  seams; retain independent validation even when logic looks similar.
- Preserve exact state vocabulary, schemas, bytes, errors, evidence boundaries,
  and unauthorized-ready-state rejection.
- Use bounded child cards if more than one concern is required.

## Blocked by

- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Required: live size, responsibilities, consumers, and mandatory disposition must be refreshed.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent architecture/reliability/usability reviews must be incorporated.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- Map every imported symbol and independently protect Step `08`/`09` headers,
  tables, status transitions, hashes, and failure/publication behavior.

## Required context

- `RA-007`, `RA-008`, `RA-010`, `RA-024`, `RA-025`, scientific decisions,
  schemas, Step `08`/`09` validators/tests, and target contract/library owners.

## Questions owned by this card

- None.

## In scope

- Neutral model/parser/serializer/publication extraction, scientific-domain
  module cohesion, import-direction correction, compatibility tests, and child
  cards for separate seams.

## Out of scope

- Changing CMH/BH/threshold/orientation algorithms, unlocking biological
  readiness, collapsing independent validators, or redesigning evidence policy.

## Deliverables

- Cohesive neutral and scientific modules, corrected dependency direction, and
  removal/justification of the monolith.

## Acceptance evidence

- Exact public and scientific contract parity passes, including unauthorized
  state, corruption, deterministic, transaction, and independent R/Python/shell
  layers.
- No extracted neutral module imports a stage or owns scientific policy.

## Canonical documentation updates

- Current architecture, local READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop if a seam cannot be proven scientifically neutral, changes evidence
  language/state, or requires production/cluster data not authorized here.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
