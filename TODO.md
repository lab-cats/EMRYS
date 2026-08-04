# TODO

This is NORAD's short current-priority view. It links instead of copying task
scope, roadmap, current state, blockers, or open questions.

## Current priority

The physical-migration campaign is complete through
[`MIG-03O`](docs/tasks/COMPLETED/MIG-03O-migrate-assemble-scientific-review-evidence-package-owner.md),
and all fourteen frozen functional owners occupy their final homes. Completed
[`DOC-GATE-01`](docs/tasks/COMPLETED/DOC-GATE-01-extract-documentation-validator.md),
[`TASK-LIFECYCLE-01`](docs/tasks/COMPLETED/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md),
and
[`DOC-CONS-08E`](docs/tasks/COMPLETED/DOC-CONS-08E-separate-live-state-from-history.md)
leave the repository-health and first live-state compression boundaries
closed. No follow-on card, final audit, runtime, cluster, or default-branch
integration is selected. `PROGRAM-01` and unrelated work remain frozen outside
their completed slices. Select only one dependency-valid package at a time
under the
[critical-runway route](docs/design/PIPELINE_PLAN.md#active-critical-runway);
roadmap order is not blocker metadata.

## Canonical routes

- Task scope, dependencies, acceptance, and lifecycle:
  [`task registry`](docs/tasks/README.md).
- Roadmap order, status matrix, and lineage:
  [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md).
- Current checkout, evidence, and exact resume point:
  [`HANDOFF.md`](docs/operations/HANDOFF.md). Live blockers remain in its
  [current-blockers section](docs/operations/HANDOFF.md#current-blockers).
- Open operational and scientific questions:
  [`QUESTIONS.md`](docs/design/QUESTIONS.md#open-operational-and-scientific-questions).
