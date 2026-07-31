# TEST-01C — Characterize validation check rosters

## Objective

Freeze an independent, exact, ordered check roster for every step validator.

## Why this exists

The `TG-03` baseline gap shows that many tests import or mirror production
`CHECK_IDS`. A production and test edit can therefore agree on the same
missing, extra, duplicated, or reordered check without detecting a contract
regression.

## Fixed decisions

- This is a test-characterization package, not a validator refactor.
- Expectations must be independently spelled and mutation-resistant under the
  [behavior-first gate](../../design/DECISIONS.md#protect-behavior-before-architectural-mutation).
- Existing scientifically intentional check differences remain local.

## Blocked by

- [ARCH-DOC-00](../COMPLETED/ARCH-DOC-00-bootstrap-task-registry-and-capture-decisions.md) — Required: the task registry and architecture constraints must be canonical first.

## Completion unblocks

- [TEST-01D](../TODO/TEST-01D-characterize-public-cli-contracts.md) — Fully: the next approved Phase 01 characterization package may begin planning.

## Prerequisites

- Verify the documented predecessor is clean, pushed, and upstream-equal.
- Reconfirm the live validator inventory before planning test cases.

## Required context

- `TEST_BASELINE.md` `TG-03`, `REFACTOR_AUDIT.md` findings `RA-017` and
  `RA-019`, every step validator, and the directly associated tests/fixtures.

## Questions owned by this card

- None.

## In scope

- Independent ordered rosters for all applicable validators.
- Cases for missing, extra, duplicate, and reordered checks at the correct
  consumer boundary.
- Focused and complete applicable regression evidence.

## Out of scope

- Changing check IDs, validator semantics, output bytes, recovery behavior,
  schemas, or scientific algorithms.

## Deliverables

- Test-only roster expectations and mutation-resistant negative cases.
- Updated baseline traceability and task completion evidence.

## Acceptance evidence

- Every live validator has an explicit applicable roster decision.
- Mutating a production roster without the independent expectation fails.
- Focused tests and one de-duplicated complete applicable gate pass with no
  production behavior change.

## Canonical documentation updates

- `TEST_BASELINE.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, `TODO.md`, and this
  card's completion record.

## Escalation conditions

- Stop if the live roster cannot be distinguished from scientific policy, or
  if a test requires changing production code to become observable.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
