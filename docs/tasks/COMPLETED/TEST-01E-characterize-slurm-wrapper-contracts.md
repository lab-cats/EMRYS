# TEST-01E — Characterize SLURM wrapper contracts

## Objective

Give every SLURM and utility job an explicit, locally testable wrapper
contract.

## Why this exists

The `TG-05` gap shows strong coverage for later jobs but uneven mode, module,
CWD, delegation, argument, output-validation, and exit coverage for early and
utility wrappers. These boundaries become fragile during source migration.

## Fixed decisions

- Use mocked local tools and tiny fixtures; do not run heavy compute or claim
  cluster proof.
- Characterize embedded-compute and other legacy exceptions rather than
  refactoring them in this card.
- Preserve dry-run-first and explicit `EXECUTE` semantics.

## Blocked by

- [TEST-01D](../COMPLETED/TEST-01D-characterize-public-cli-contracts.md) — Required: delegated public interfaces and exit behavior are characterized and protected.

## Completion unblocks

- [TEST-01F](../TODO/TEST-01F-create-independent-contract-goldens.md) — Fully: the final independent-golden package can close cross-language boundaries.

## Prerequisites

- Refresh every tracked `jobs/*.slurm` and utility-job entry point.
- Confirm no cluster execution is authorized by this test-only package.

## Required context

- `TEST_BASELINE.md` `TG-05`, `REFACTOR_AUDIT.md` findings `RA-018` and
  `RA-023`, current jobs, delegated scripts, shell fixtures, and SLURM
  conventions in `AGENTS.md`.

## Questions owned by this card

- None.

## In scope

- Default, execute, invalid-mode, module list/load, submit CWD, delegation,
  exact argument, output-validation, and exit-propagation decisions.
- Explicit labels for wrappers that intentionally differ.

## Out of scope

- Real submission, module installation, job arrays, a generic dispatcher,
  resource-policy changes, or wrapper thinning.

## Deliverables

- Focused wrapper tests and a complete applicability matrix.
- Documented legacy exceptions suitable for later migration planning.

## Acceptance evidence

- Every live wrapper has a test or explicit non-applicable rationale for each
  contract category.
- The complete applicable local gate passes; no cluster or runtime evidence is
  claimed.

## Canonical documentation updates

- `TEST_BASELINE.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, `TODO.md`, and this
  card; correct `RUNBOOK.md` only if current commands are wrong.

## Escalation conditions

- Stop if a wrapper test would execute real workload, require CSU-only state,
  or reveal a production correction outside characterization scope.

## Completion record

Completed locally on 2026-07-31 on
`codex/refactor-01e-slurm-contracts`.

- Implementation commit `9a4fb09` adds an exact, independent test-only matrix
  for all 16 tracked SLURM and utility jobs, including literal SBATCH
  directives, file modes, mode applicability, module policy, submit CWD,
  delegation, arguments, output validation, and exit propagation.
- All dynamic cases use only generated child stubs, mocked modules and tools,
  and tiny temporary fixtures. No scheduler, CSU module system, real workflow
  executable, production input, dependency restore, or cluster work ran.
- Characterized exceptions remain unchanged: Steps `00a`/`00b` embed implicit
  compute; three utility jobs have no execution mode; seven wrappers have a
  Bash 3.2 empty-array dry-run defect; Step `01` creates default placeholders;
  Steps `02`/`02b` create dry-run output directories; submit-CWD, module, file
  mode, and output-validation policies are non-uniform.
- All 113 focused tests passed. The complete local gate passed every lane in
  168.770 seconds.
- No production job, script, Makefile, schema, dependency, resource,
  scientific, runtime, cluster, or biological behavior changed. All real
  scheduler/module/runtime evidence remains environment-deferred. The next
  approved local descendant is `TEST-01F`.
