# FUT-SUCCESS-04 — Optional analysis and archival semantics

## Objective

Define future required-versus-optional analysis success and request archival
semantics for runs with multiple analysis modules.

## Why this exists

Current success can require every requested current task, validator, evidence
assembly, and report. A future library of analyses needs explicit policy for
optional module failure, partial reports, retry, completion, and request
metadata archival without moving raw inputs.

## Fixed decisions

- This policy is future-only and must not alter current run success.
- Raw input data remains stationary; only request/run metadata may be promoted
  or archived after the approved success boundary.
- Required/optional status, evidence, and failure remain explicit and
  filesystem-inspectable.
- Computational success never implies scientific or biological readiness.

## Blocked by

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Required: optional-analysis policy waits until the current refactor is complete.

## Completion unblocks

- None.

## Prerequisites

- Inspect the implemented intake/run lifecycle and the then-current analysis
  module design before choosing state transitions.

## Required context

- Intake identity/attempt/promotion model, future analysis modules, report
  profiles, evidence states, recovery rules, and operator retention policy.

## Questions owned by this card

- [`CHOICE-SUCCESS-01`](../../design/QUESTIONS.md#choice-success-01--requiredoptional-analysis-success-and-request-archival).

## In scope

- Required/optional declarations, success/partial/failure states, retry,
  module/report visibility, metadata archival/promotion, and migration from the
  current all-required model.

## Out of scope

- Automatic raw-data movement/deletion, production retention policy, scientific
  evidence promotion, or implementing analysis modules.

## Deliverables

- Versioned state-transition and archival contract with failure/retry scenarios
  and implementation cards.

## Acceptance evidence

- Optional failure cannot masquerade as success or invalidate required outputs;
  required failure cannot be archived as complete.
- Every state, attempt, report, and metadata move is deterministic, recoverable,
  and inspectable.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, intake/evidence docs, `DECISIONS.md`,
  `QUESTIONS.md`, task registry, and this card.

## Escalation conditions

- Stop if policy depends on undeclared analysis trust, destructive data
  handling, or conflates computational and scientific completion.

## Completion record

Not started. This future-only card requires a separate planning discussion and
approval after the current refactor.
