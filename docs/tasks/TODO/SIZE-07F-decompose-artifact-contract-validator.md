# SIZE-07F — Decompose artifact contract validator

## Objective

Split the oversized artifact-contract validator into cohesive schema,
cross-artifact, evidence-state, and CLI/reporting checks without weakening
independent validation.

## Why this exists

The roughly 1,900-line validator combines many contract families and public
failure modes. Its size hinders local review, yet careless sharing with
producers would create common-mode defects.

## Fixed decisions

- Independent public-schema and cross-artifact validation remains mandatory.
- Preserve exact check IDs/order, statuses, messages where contracted, exit
  behavior, deterministic report bytes, and failure-first publication.
- Do not import producer rules into the validator solely to reduce duplication.
- Use bounded child cards if multiple contract families require separate work.

## Blocked by

- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Required: live size, responsibilities, consumers, and mandatory disposition must be refreshed.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent architecture/reliability/usability reviews must be incorporated.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- Complete independent roster/golden/CLI characterization and refresh the
  validator's schema/status/consumer matrix.

## Required context

- `RA-008`, `RA-017`, `RA-019`, public schemas, artifact fixtures, check
  rosters, report publication, exit behavior, and consumer tests.

## Questions owned by this card

- None.

## In scope

- Cohesive check modules, neutral result/report types where justified, CLI
  orchestration, independent tests, and child-card split.

## Out of scope

- Changing schemas/evidence states, sharing producer rules, normalizing all
  validator exits, or building a generic validator framework.

## Deliverables

- Cohesive validator modules, narrower independent tests, and eliminated
  oversized owner.

## Acceptance evidence

- Exact roster, schema, status, bytes, exit, malformed-input, mutation, and
  report-publication tests pass.
- Mutating a producer constant still fails the independent validator/golden.

## Canonical documentation updates

- Current architecture, local READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop if decomposition would reduce independent verification, change a public
  check/report contract, or require universal validator infrastructure.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
