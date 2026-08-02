# ARCH-02D — Define direct migration mechanics

## Objective

Define a reversible, contract-preserving pattern for moving each owner directly
from the flat layout to its final source home.

## Why this exists

There are no external consumers that justify indefinite legacy paths, but
moving entry points without parity evidence can silently break scripts, jobs,
tests, or operators. The migration pattern must preserve behavior without
preserving accidental paths forever.

## Fixed decisions

- Move code directly to its final home; hybrid layout is temporary migration
  scaffolding, not a target architecture.
- Use a temporary root wrapper only where required, migrate callers/tests/docs,
  prove parity, then remove the wrapper in bounded work.
- Preserve behavior, science, output, evidence, recovery, and dry-run
  contracts; path/interface changes are explicit migrations.

## Blocked by

- [ARCH-02C](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: the final destination and dependency rules must be settled.

## Completion unblocks

- None.

## Prerequisites

- Reconfirm the live consumer/import/invocation graph and applicable behavior
  characterization at planning time.

## Required context

- The target topology, `TEST_BASELINE.md`, direct/arbitrary-CWD and SLURM
  characterization, current file modes, imports, Make targets, and runbook
  commands.

## Questions owned by this card

- None.

## In scope

- Wrapper criteria and lifetime, caller migration order, parity methods,
  rollback boundaries, documentation timing, and removal acceptance.

## Out of scope

- Performing migrations, maintaining a permanent compatibility layer,
  versioning a public package, or changing scientific behavior.

## Deliverables

- A reusable migration checklist and evidence matrix for concrete `MIG-03-*`
  cards.

## Acceptance evidence

- The pattern handles Python, shell, R, SLURM, Make, reports, and non-Python
  assets without ambiguous dual ownership.
- It defines how old/new parity is proven and when a wrapper is safely removed.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, `PIPELINE_PLAN.md`, `DECISIONS.md` if migration
  policy changes, and this card.

## Escalation conditions

- Stop if a migration would require an indefinite duplicate implementation,
  untested interface break, or packaging/versioning decision outside scope.

## Completion record

Completed as a documentation-only JIT package. The canonical
[`MIGRATION_MECHANICS.md`](../../../src/norad/contracts/MIGRATION_MECHANICS.md)
defines reversible checkpoints, strict temporary-wrapper criteria, caller
cutover order, rollback and wrapper-removal boundaries, a parity matrix for
Python, shell, R, SLURM, Make callers, reports, and non-Python assets, and a
reusable concrete-card checklist.

No implementation or asset was moved, no compatibility layer was created, and
no packaging or public-versioning work began. The final combined documentation
gate passed; computational validation was not applicable.
