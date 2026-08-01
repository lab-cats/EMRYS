# TEST-01D — Characterize public CLI contracts

## Objective

Record and protect every applicable public CLI, direct-execution,
working-directory, side-effect, and exit contract.

## Why this exists

The `TG-04` matrix is incomplete and diagnostic/exit conventions vary across
Python, shell, R, and Make entry points. Source relocation would otherwise
change behavior without a complete observable contract.

## Fixed decisions

- Characterize current behavior before deciding whether it is preserved,
  migrated, corrected, or explicitly deferred.
- Future path changes are allowed only as approved contract migrations; see
  the [direct-migration decision](../../design/DECISIONS.md#target-a-vertical-package-with-direct-contract-preserving-migrations).
- A valid published failed-evidence report is not automatically a process
  failure.

## Blocked by

- [TEST-01C](../COMPLETED/TEST-01C-characterize-validation-check-rosters.md) — Required: exact validation outputs must be independently fixed first.

## Completion unblocks

- [TEST-01E](TEST-01E-characterize-slurm-wrapper-contracts.md) — Fully: completed locally with protected delegated CLI behavior.

## Prerequisites

- Refresh the live public-entrypoint inventory, including Make targets and
  documented invocation forms.

## Required context

- `TEST_BASELINE.md` `TG-04`, `REFACTOR_AUDIT.md` findings `RA-011` and
  `RA-023`, `RUNBOOK.md`, all public entry points, and their tests.

## Questions owned by this card

- None.

## In scope

- Applicable decisions for help, parse failure, dry-run, execute, malformed
  and missing input, direct script use, arbitrary CWD, unrelated files,
  side effects, and exit propagation.
- Characterization of stdout/stderr behavior without activating the future
  logging design.

## Out of scope

- Normalizing exit codes, renaming commands, moving files, quieting current
  output, or fixing characterized defects.

## Deliverables

- A complete public-contract matrix and focused missing-case tests.
- Explicit labels for legacy exceptions and decision-required behavior.

## Acceptance evidence

- Every live public entry point has an applicable-case decision with a named
  test or an explicit, justified deferral.
- Focused and complete applicable gates pass without changing public behavior.

## Canonical documentation updates

- `TEST_BASELINE.md`, `PIPELINE_PLAN.md`, `RUNBOOK.md` only if an invocation
  was inaccurately documented, `HANDOFF.md`, `TODO.md`, and this card.

## Escalation conditions

- Stop if current behavior is unsafe enough that preserving it would be an
  architectural decision, or if a documented and implemented interface
  conflict cannot be resolved as characterization alone.

## Completion record

Completed locally on 2026-07-31 on
`codex/refactor-01d-public-cli-contracts`.

- Implementation commit `a003065` adds an exact test-only inventory of all 25
  public Python entry points, 13 shell workflows, four R entry points, and 23
  callable Make targets, while keeping the one private Python module excluded.
- The central matrix protects help or current no-help behavior, parse/missing
  failures, arbitrary-CWD invocation, working-directory side-effect freedom,
  file modes, and exact Make-target applicability and command expansion.
  Existing focused suites remain authoritative for command-specific dry-run,
  execute, malformed-input, output, rollback, and child-exit behavior.
- Characterized exceptions remain unchanged: 17 Python files are
  interpreter-only; direct Python shebang execution selects the caller's
  environment; Steps `03`, `04`, and `05` shell files require explicit `bash`;
  two R environment utilities have no help mode; two analysis R files are
  Rscript-only; and `gtf_to_bed12.py` silently overwrites its declared output.
- The focused 116-test Python set, guarded local-R shell contract, and Step
  `08`/`09` real-R fixtures passed. The complete local gate passed every lane
  in 164.719 seconds.
- No production, schema, workflow, Makefile, dependency, scientific, runtime,
  cluster, or biological behavior changed. The next approved local descendant
  is `TEST-01E`.
