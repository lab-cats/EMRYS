# DOC-GATE-01 — Extract documentation validator

## Objective

Complete independent behavior characterization and supported command exposure
for the documentation validator extracted during `CONCURRENCY-02`.

## Why this exists

The implementation now lives at
`scripts/git_orchestration/validate_documentation.py`, and `RUNBOOK.md` contains
only its invocation. That urgent extraction removed the embedded program but
did not supply independent invalid-state fixtures for every inherited rule.
The stable public-entry choice is now resolved as a future logic-free Make
wrapper, but neither that wrapper nor its equivalence proof exists yet.

## Fixed decisions

- `RUNBOOK.md` owns the exact operator invocation and a concise behavior
  summary, not the validator implementation.
- Characterize and independently lock the current extracted engine's success,
  failure, output, traversal, diagnostics, root handling, and exit behavior;
  this package is behavior-preserving.
- Preserve the current executable as the starting implementation; any move is
  a separately justified source-layout decision, not incidental cleanup.
- A concise Make target may wrap the executable, but it must not duplicate the
  validation logic.
- The selected target is a stable, logic-free Make wrapper over the same
  explicit-root validator engine. The current direct Runbook invocation stays
  authoritative until wrapper expansion and behavior are proved exactly
  equivalent.
- Semantic review, automated validation, and completion verification remain
  separate ordered responsibilities; the validator owns only validation.
- Smaller, independently understandable gate stages may be exposed through
  modes or orchestration only when they reuse one validator engine rather than
  duplicate implementations.
- Ordinary thin-slice close does not require validation unless continuing
  would be unsafe or a later slice directly depends on unverified behavior.
- Reserve complete repository documentation validation for the final
  reconciliation boundary.
- Dependency-semantic changes belong to `TASK-REG-01`, not this behavior lock.

## Blocked by

- None.

## Completion unblocks

- [CONCURRENCY-03](../TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md) — Fully: Provides the independently behavior-locked validator required to enforce the fragment lifecycle; completed `CONCURRENCY-02` supplies the manual protocol and synthetic exchange.
- [TASK-LIFECYCLE-01](../TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md) — Fully: Provides the independently tested validator owner required for lifecycle support; completed `CONCURRENCY-02` and the resolved program-owned integration-review trigger are already satisfied.

## Prerequisites

- Freeze the current extracted engine and its observed repository-level success
  and representative failure behavior at one known Git revision.
- Inspect current Python-test, Make-target, and command-output conventions
  before approving the task-specific implementation plan.

## Required context

- The documentation gate in
  [`RUNBOOK.md`](../../operations/RUNBOOK.md#local-validation-gate), the task
  lifecycle in [`../README.md`](../README.md), the current `Makefile`, and the
  directly relevant Python-test conventions.
- Current card-location, dependency, link, anchor, orphan, and Mermaid rules.

## Questions owned by this card

- The command-surface choice is resolved as
  [`CHOICE-DOC-GATE-01`](../../design/QUESTIONS.md#resolved-index): implement a
  stable, logic-free Make wrapper over the same engine. Live planning must
  still inspect the current public command inventory and interpreter boundary;
  this decision does not claim the wrapper exists.

## In scope

- Independent fixtures and focused tests for every current validator rule.
- Behavior-lock the current extracted Python implementation in place; any move
  remains a separately justified source-layout decision.
- Preserve the current thin Runbook invocation until the selected logic-free
  Make wrapper and exact equivalence evidence land atomically.
- Exact success/failure exit behavior and actionable diagnostic preservation.

## Out of scope

- Changing task-dependency meaning, reclassifying existing card edges,
  consolidating unrelated documentation, or changing NORAD workflow,
  scientific, report, or evidence behavior.

## Deliverables

- An independent behavior-lock suite for the current standalone validator and
  its separable testable core.
- A hard-coded, test-owned legacy card-heading oracle frozen from the selected
  baseline, with an explicit equality assertion against production rather
  than production-derived expected values.
- Focused regression tests with exact complete ordered problem tuples for
  every isolated invalid rule: links and anchors, card structure and identity,
  dependencies, cycles, orphans, and Mermaid-source structure.
- Distinct `TODO`, `IN_PROGRESS`, and `COMPLETED` boundary scenarios, including
  a completed card that is still named as an active blocker; one aggregate CLI
  scenario covering exact stdout, stderr, diagnostic order, and exit status;
  and explicit-root scenarios for unavailable, non-Git, nested non-root, and
  fail-closed Git-inventory inputs.
- A stable, logic-free Make wrapper with literal expansion/golden coverage and
  exact behavioral equivalence to the same explicit-root engine.
- A runbook section reduced to the supported invocation and behavior summary.

## Acceptance evidence

- The current command continues to accept and reject the frozen representative
  repository states with identical ordered diagnostics and exit behavior.
- Focused tests and the complete applicable documentation gate pass.
- Independent fixtures, not expectations derived from the production
  implementation, lock every inherited rule and aggregate diagnostic order.
- The Make wrapper contains no validation logic and is proved exactly
  equivalent to direct invocation of the explicit-root engine.
- Each supported stage or mode has an independently understandable result while
  exercising the same underlying validator engine.
- The command surface supports complete reconciliation validation without
  making that full gate mandatory at every thin-slice boundary.
- The runbook contains no embedded validator implementation.
- No workflow, schema, fixture, scientific-method, report, or evidence-state
  behavior changes.

## Canonical documentation updates

- `RUNBOOK.md`, `PIPELINE_PLAN.md`, `TODO.md`, `HANDOFF.md`, the task registry,
  and any justified Make-target documentation. After corrected tests pass, a
  separate factual documentation patch updates `TEST_BASELINE.md` with only
  observed behavior-lock evidence and `DECISIONS.md` with the implemented
  engine/wrapper ownership; neither may claim independent coverage or wrapper
  availability early.

## Escalation conditions

- Stop if current behavior cannot be characterized independently, the behavior
  lock or wrapper would silently change accepted repository states, or the
  current owner conflicts with an approved source-layout decision.
- If independent fixtures expose semantic drift, restore characterized
  behavior or reopen the semantic owner; do not silently rewrite expectations.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
