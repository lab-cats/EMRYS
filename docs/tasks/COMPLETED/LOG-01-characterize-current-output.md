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

- [LOG-02](LOG-02-define-logging-contract.md) — Fully: target logging semantics can be based on a complete current inventory.

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

Completed as a documentation-only characterization on a fresh descendant of
the published Phase `0` tip. The
[`LOG-01` inventory](../../design/TEST_BASELINE.md#log-01-current-output-and-log-inventory)
uses normalized profiles plus a per-surface crosswalk to classify every current
public Python, shell, R, SLURM, and Make surface; the validation orchestrator,
documentation gate, operational data checks, and durable-copy/evidence roles
are included explicitly.

The inventory preserves machine and recovery-critical content, characterizes
the validators' mixed stdout, conditional scheduler capture, local validation
retention cardinality in quiet mode, verbose streaming without retained lane
logs, the Step `05` operational check's unsafe duplicate-tee publication,
exposure boundaries, repeated low-value narration, and missing application
logs. External consumers remain uninspected, and future logging semantics
remain owned by `LOG-02`.

The earlier `4d01152` candidate supplied useful inventory structure but was
not merged, rebased, cherry-picked, or treated as completed state because it
predated the corrected and published Phase `0` tip. No runtime output,
executable, test, artifact, receipt, evidence state, validation, rollback,
transaction, or exit behavior changed. Computational validation was therefore
not applicable; the documentation gate and exact publication evidence are
recorded in [`HANDOFF.md`](../../operations/HANDOFF.md#immediate-resume-point).
Completion fully unblocks `LOG-02` for separate selection and planning.
