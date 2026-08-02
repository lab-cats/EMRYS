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
The first unit,
[`MIG-03A`](docs/tasks/COMPLETED/MIG-03A-extract-validation-report-library.md),
is complete: the validation-report protocol has one neutral owner, all thirteen
legacy validators use the final file, and the executable checkpoint is
published/upstream-equal. The authorized physical-migration campaign now
selects only the next dependency-valid unit just in time; no later migration
card is pre-created here.

Unrelated work remains frozen under the
[active critical runway](docs/design/PIPELINE_PLAN.md#active-critical-runway)
while that campaign proceeds. Roadmap order is not blocker metadata.

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
