# FUT-CLI-03 — Installable NORAD control plane

## Objective

Design and prototype a thin installable Python `norad` control plane after the
internal architecture and interfaces stabilize.

## Why this exists

An installable command can give scientists one coherent interface for
validation, planning, execution, status, resume, reporting, and stage
inspection without requiring knowledge of repository paths.

## Fixed decisions

- This capability is future-only; do not introduce versioning/distribution
  pressure during the current refactor.
- Keep the Python layer thin: own contracts, DAG, submission, filesystem state,
  and report coordination; do not reimplement STAR, samtools, bcftools, R, or
  install dependencies during compute.
- `validate`, `plan`, `run`, `status`, `resume`, `report`, and `stages` are
  illustrative direction, not frozen commands.
- Filesystem state remains directly inspectable without the CLI.

## Blocked by

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Required: packaging waits until the current architecture is stable.

## Completion unblocks

- None.

## Prerequisites

- Stable `src/norad`, semantic DAG, intake/run lifecycle, report profiles,
  logging contract, scheduler boundary, and non-Python asset inventory.

## Required context

- Final architecture/contracts, user journeys, direct migration results,
  packaging standards at execution time, report assets, R/scripts, and SLURM
  templates.

## Questions owned by this card

- [`CHOICE-CONTROL-01`](../../design/QUESTIONS.md#choice-control-01--exact-installable-cli-surface-and-asset-materialization).

## In scope

- Feasibility, command/API design, package metadata, non-Python asset inclusion,
  immutable job materialization, filesystem state, installation boundaries, and
  one small prototype.

## Out of scope

- Rewriting analysis tools in Python, implicit dependency installation,
  service/cloud orchestration, hidden database state, or immediate public release.

## Deliverables

- Reviewed package/control-plane design and bounded prototype/release cards.

## Acceptance evidence

- Installed and repository-development modes produce equivalent plans/contracts;
  materialized jobs/assets are versioned, immutable, and inspectable.
- Users can operate and recover runs without hidden state or tool bootstrapping.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, user/installation docs, `DECISIONS.md`,
  `QUESTIONS.md`, task registry, and this card.

## Escalation conditions

- Stop if packaging forces unstable public versioning, hides run state, embeds
  mutable jobs, or begins installing compute dependencies implicitly.

## Completion record

Not started. This future-only card requires a separate planning discussion and
approval after the current refactor.
