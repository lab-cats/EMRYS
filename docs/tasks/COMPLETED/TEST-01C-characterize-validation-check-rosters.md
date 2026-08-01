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

- [TEST-01D](TEST-01D-characterize-public-cli-contracts.md) — Fully: completed locally as the next approved Phase 01 characterization package.

## Prerequisites

- Verify the documented predecessor is clean, pushed, and upstream-equal.
- Reconfirm the live validator inventory before planning test cases.

## Required context

- [`TEST_BASELINE.md` `TG-03`](../../design/TEST_BASELINE.md#evidence-derived-characterization-gaps)
  plus its [validator inventory](../../design/TEST_BASELINE.md#python-entry-points).
- [`REFACTOR_AUDIT.md` `RA-017`](../../design/REFACTOR_AUDIT.md#ra-017--incomplete-public-contract-traceability)
  and [`RA-019`](../../design/REFACTOR_AUDIT.md#ra-019--productiontest-shared-defect-exposure).
- The live `scripts/validate_step_*.py` validator family and each directly
  associated `tests/test_validate_step_*.py` module or fixture.

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

Completed locally on 2026-07-31 on
`codex/refactor-01c-validation-check-rosters`.

- Implementation commit `8d58fc6` adds one independently authored test-only
  ordered roster for each of the 13 live validators and binds every producer's
  successful output test to that expectation.
- `tests/test_validation_check_rosters.py` proves the literal inventory is
  exact and that missing, extra, duplicate, and reordered mutations fail the
  independent oracle.
- Shared report-consumer tests preserve the characterized defect that an
  exact-ID reorder is accepted; artifact-adapter tests preserve acceptance of
  reordered and wrong-but-unique IDs while proving row-count and duplicate-ID
  mutations are rejected.
- The focused validator/adapter set passed all 250 tests.
- The de-duplicated complete local gate passed static preflight, shell
  contracts, Python line/branch non-regression, guarded R and Step `08`/`09`
  real-R fixtures, and pinned report runtime in 164.635 seconds.
- No production, schema, workflow, scientific, runtime, cluster, or biological
  behavior changed. The next approved local descendant is `TEST-01D`.
