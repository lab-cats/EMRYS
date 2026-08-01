# LOG-01 — Characterize current output

## Objective

Inventory and classify current stdout, stderr, scheduler, Make, test, and
durable-log behavior before changing verbosity.

## Why this exists

Many entry points print extensive context and exact commands, but consumers,
tests, and recovery workflows may rely on portions of that output. Quieting
the console without a map could hide actionable failure evidence or corrupt
machine-readable streams.

## Fixed decisions

- Characterize before changing output.
- The future model sends machine output to stdout and human logs to stderr,
  with concise default console output and durable detail.
- Log level must never change artifacts, hashes, receipts, evidence,
  validation, rollback, or exit behavior.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest behavior-sufficiency decision is affirmative.

## Completion unblocks

- [LOG-02](../TODO/LOG-02-define-logging-contract.md) — Fully: target logging semantics can be based on a complete current inventory.

## Prerequisites

- Refresh every public entry point, Make/validation lane, SLURM wrapper, R
  script, report renderer, and current log path.

## Required context

- Public CLI characterization, shell/R/SLURM tests, Makefiles, current
  `AGENTS.md` logging conventions, runbook commands, and failure/recovery paths.

## Questions owned by this card

- None.

## In scope

- Output sink, audience, severity, stability, test dependency, machine
  parsability, failure value, durable-copy status, and secret/path exposure
  classification.

## Out of scope

- Changing output, introducing a logger, deleting context, redirecting streams,
  or activating quiet defaults.

## Deliverables

- A repository-wide output/log inventory and protected-behavior map.
- Candidate low-value repetition and missing durable evidence, clearly labeled.

## Acceptance evidence

- Every public/runtime entry point and validation lane has an explicit output
  classification and consumer/test trace.
- Machine-readable and recovery-critical content is distinguished from human
  progress detail.

## Canonical documentation updates

- `TEST_BASELINE.md` if behavior gaps are found, `PIPELINE_PLAN.md`,
  `QUESTIONS.md`, and this card.

## Escalation conditions

- Stop if a stream contains both machine and human contracts that cannot be
  separated compatibly, or if removing verbosity could remove recovery proof.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
