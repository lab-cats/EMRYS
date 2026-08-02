# DOC-GATE-01 — Extract documentation validator

## Objective

Complete independent behavior characterization and supported command exposure
for the documentation validator extracted during `CONCURRENCY-02`.

## Why this exists

The implementation now lives at
`scripts/git_orchestration/validate_documentation.py`, and `RUNBOOK.md` contains
only its invocation. That urgent extraction removed the embedded program but
did not supply independent invalid-state fixtures for every inherited rule or
decide whether a Make target should become the stable public entry point.

## Fixed decisions

- `RUNBOOK.md` owns the exact operator invocation and a concise behavior
  summary, not the validator implementation.
- Characterize current success, failure, output, and exit behavior before
  extraction; this package is behavior-preserving.
- Preserve the current executable as the starting implementation; any move is
  a separately justified source-layout decision, not incidental cleanup.
- A concise Make target may wrap the executable, but it must not duplicate the
  validation logic.
- Semantic review, automated validation, and completion verification remain
  separate ordered responsibilities; the validator owns only validation.
- Smaller, independently understandable gate stages may be exposed through
  modes or orchestration only when they reuse one validator engine rather than
  duplicate implementations.
- Ordinary thin-slice close does not require validation unless continuing
  would be unsafe or a later slice directly depends on unverified behavior.
- Reserve complete repository documentation validation for the final
  reconciliation boundary.
- Dependency-semantic changes belong to `TASK-REG-01`, not this extraction.

## Blocked by

- None.

## Completion unblocks

- [CONCURRENCY-03](CONCURRENCY-03-enforce-integration-fragment-lifecycle.md) — Fully: Provides the remaining extracted, testable validator required to enforce the fragment lifecycle; completed `CONCURRENCY-02` supplies the manual protocol and synthetic exchange.
- [TASK-LIFECYCLE-01](TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md) — Partially: Provides the extracted, testable validator required to enforce the new lifecycle states; completed `CONCURRENCY-02` is satisfied and `PROGRAM-01` remains required.

## Prerequisites

- Capture the current inline validator and its observed repository-level
  success and representative failure behavior from a known Git revision.
- Inspect current Python-test, Make-target, and command-output conventions
  before approving the task-specific implementation plan.

## Required context

- The documentation gate in
  [`RUNBOOK.md`](../../operations/RUNBOOK.md#local-validation-gate), the task
  lifecycle in [`../README.md`](../README.md), the current `Makefile`, and the
  directly relevant Python-test conventions.
- Current card-location, dependency, link, anchor, orphan, and Mermaid rules.

## Questions owned by this card

- Whether the final command should be exposed only as a script or also through
  a Make target, based on live command-surface inspection during planning.

## In scope

- Independent fixtures and focused tests for every current validator rule.
- Behavior-preserving extraction of the inline Python implementation.
- A thin runbook invocation, concise behavior summary, and any justified Make
  wrapper.
- Exact success/failure exit behavior and actionable diagnostic preservation.

## Out of scope

- Changing task-dependency meaning, reclassifying existing card edges,
  consolidating unrelated documentation, or changing NORAD workflow,
  scientific, report, or evidence behavior.

## Deliverables

- A standalone documentation-validator executable with a separable testable
  core.
- Focused regression tests covering valid and invalid local links and anchors,
  task-card structure and identity, dependency checks, cycles, orphans, and
  Mermaid-source structure.
- A runbook section reduced to the supported invocation and behavior summary.

## Acceptance evidence

- The extracted command accepts the same repository state and rejects the
  same representative invalid states as the characterized inline program.
- Focused tests and the complete applicable documentation gate pass.
- Each supported stage or mode has an independently understandable result while
  exercising the same underlying validator engine.
- The command surface supports complete reconciliation validation without
  making that full gate mandatory at every thin-slice boundary.
- The runbook contains no embedded validator implementation.
- No workflow, schema, fixture, scientific-method, report, or evidence-state
  behavior changes.

## Canonical documentation updates

- `RUNBOOK.md`, `PIPELINE_PLAN.md`, `TODO.md`, `HANDOFF.md`, the task registry,
  and any justified Make-target documentation.

## Escalation conditions

- Stop if current behavior cannot be characterized independently, extraction
  would silently change accepted repository states, or the proposed owner
  conflicts with an approved source-layout decision.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
