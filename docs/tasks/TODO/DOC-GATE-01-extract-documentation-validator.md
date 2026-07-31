# DOC-GATE-01 — Extract documentation validator

## Objective

Replace the inline documentation-validator program in `RUNBOOK.md` with a
tested executable while preserving its observable validation behavior.

## Why this exists

The documentation gate began as a copy-paste command and has grown into a
roughly 255-line Python program embedded in a shell heredoc. It now owns link,
anchor, task-card, dependency-graph, orphan, and Mermaid validation. Keeping
that implementation in an operational runbook makes the behavior difficult to
test, review, reuse, or change safely.

## Fixed decisions

- `RUNBOOK.md` owns the exact operator invocation and a concise behavior
  summary, not the validator implementation.
- Characterize current success, failure, output, and exit behavior before
  extraction; this package is behavior-preserving.
- Prefer `scripts/validate_documentation.py` plus focused tests under `tests/`
  unless task-specific inspection proves that an existing executable owner is
  more appropriate.
- A concise Make target may wrap the executable, but it must not duplicate the
  validation logic.
- Dependency-semantic changes belong to `TASK-REG-01`, not this extraction.

## Blocked by

- None.

## Completion unblocks

- None.

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
