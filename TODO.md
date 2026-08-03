# TODO

This is NORAD's short current-priority view. It links instead of copying task
scope, roadmap, current state, blockers, or open questions.

## Current priority

The physical-migration campaign is paused after completed
[`MIG-03M`](docs/tasks/COMPLETED/MIG-03M-migrate-preprocess-and-annotate-cohort-candidates-owner.md).
No Step `09` or later migration/review card is created or selected. The current
boundary is Slice `3` of
[`PROGRAM-01`](docs/tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md),
which activates only one separately planned repository-health package at a
time under the
[critical-runway route](docs/design/PIPELINE_PLAN.md#active-critical-runway).
Completed [`DOC-GATE-01`](docs/tasks/COMPLETED/DOC-GATE-01-extract-documentation-validator.md)
and completed
[`TASK-LIFECYCLE-01`](docs/tasks/COMPLETED/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md)
now supply the tested documentation gate and flat lifecycle/proposal support.
No follow-on card is selected. The already-approved repository-health campaign
next quarantines only the malformed ignored R-library entry and rechecks the
guarded environment without dependency installation or restoration. Unrelated
work and the preserved program remainder remain frozen. Roadmap order is not
blocker metadata.

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
