# TODO

This is NORAD's short current-priority view. It links instead of copying task
scope, roadmap, current state, blockers, or open questions.

## Current priority

[`PLAN-02Z`](docs/tasks/COMPLETED/PLAN-02Z-integrate-future-task-sequence.md)
has completed the documentation-only first-tranche plan. Its dedicated
[`architecture review`](docs/tasks/COMPLETED/REVIEW-ARCH-03A-review-validation-publication-migration.md)
and
[`reliability review`](docs/tasks/COMPLETED/REVIEW-REL-03A-review-validation-publication-migration.md)
are complete; the
[`usability review`](docs/tasks/COMPLETED/REVIEW-UX-03A-review-validation-publication-migration.md)
has now closed the dedicated review chain.
The proposed unit is
[`MIG-03A`](docs/tasks/TODO/MIG-03A-extract-validation-report-library.md),
which is now the next eligible action for task-specific read-only selection and
planning. No physical source migration is selected or executing yet.

All other work remains frozen under the
[active critical runway](docs/design/PIPELINE_PLAN.md#active-critical-runway)
until the first physical source migration and explicit user reassessment.
Roadmap order is not blocker metadata.

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
