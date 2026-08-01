# LOG-02 — Define logging contract

## Objective

Define stable console, durable-log, level, stream, failure-tail, and retention
semantics for local and SLURM execution.

## Why this exists

Users need a quiet, relevant default and maintainers need complete diagnostics.
Those goals require two explicit sinks and stable invariants rather than ad hoc
print suppression.

## Fixed decisions

- Default console output is concise and directly relevant; verbose and debug
  modes remain available.
- Complete durable logs are always produced for executable runs.
- Machine output uses stdout; human logs use stderr.
- Changing log level never changes computational or publication behavior.

## Blocked by

- [LOG-01](../COMPLETED/LOG-01-characterize-current-output.md) — Required: current output and consumers must be fully mapped.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: logging design is one input to the integrated sequence.
- [LOG-03](../TODO/LOG-03-build-two-sink-logging-foundation.md) — Partially: implementation also waits for the independent reviews.

## Prerequisites

- Resolve every output item that currently mixes machine and human audiences.

## Required context

- `LOG-01`, public CLI/SLURM contracts, transaction/recovery evidence, ignored
  runtime paths, security policy, and validation-lane behavior.

## Questions owned by this card

- [`CHOICE-LOG-01`](../../design/QUESTIONS.md#choice-log-01--exact-public-log-levels-and-flags).
- [`CHOICE-LOG-02`](../../design/QUESTIONS.md#choice-log-02--durable-log-layout-retention-and-failure-tail).

## In scope

- Public levels/flags, default messages, stream rules, durable record content,
  run/attempt identity, timestamps/context, failure summaries, retention
  ownership, and compatibility/error semantics.

## Out of scope

- Implementing the foundation, migrating stages, altering artifacts, changing
  exit codes, or defining production data-retention policy.

## Deliverables

- A logging contract with scenario matrix and concrete foundation/rollout cards.

## Acceptance evidence

- The contract serves scientist, operator, automation, and maintainer audiences
  without mixed streams or evidence loss.
- Equivalent runs at different levels produce identical non-log outputs,
  receipts, hashes, states, and exit results.

## Canonical documentation updates

- `DECISIONS.md`, `FUTURE_ARCHITECTURE.md`, `QUESTIONS.md`,
  `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if the design requires hiding a command needed for recovery, logging
  secrets, or treating scheduler files and application logs as interchangeable.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
