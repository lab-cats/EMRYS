# TODO

This is NORAD's short current-priority view. It links instead of copying task
scope, roadmap, current state, blockers, or open questions.

## Current priority

The physical-migration campaign is paused after completed
[`MIG-03M`](docs/tasks/COMPLETED/MIG-03M-migrate-preprocess-and-annotate-cohort-candidates-owner.md).
No Step `09` or later migration/review card is created or selected. The active
boundary is Slice `2` of
[`PROGRAM-01`](docs/tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md),
which activates only one separately planned repository-health package at a
time under the
[critical-runway route](docs/design/PIPELINE_PLAN.md#active-critical-runway).
Unrelated work and the preserved program remainder remain frozen; roadmap
order is not blocker metadata.

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
