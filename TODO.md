# TODO

This is NORAD's short current-priority view. It links instead of copying task
scope, roadmap, current state, blockers, or open questions.

## Current priority

The neutral validation-report concern and fourteen semantic DAG-owner
migrations are complete through
[`MIG-03O`](docs/tasks/COMPLETED/MIG-03O-migrate-assemble-scientific-review-evidence-package-owner.md),
and all fourteen frozen owners occupy their final homes. Completed
[`DOC-GATE-01`](docs/tasks/COMPLETED/DOC-GATE-01-extract-documentation-validator.md),
[`TASK-LIFECYCLE-01`](docs/tasks/COMPLETED/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md),
and
[`DOC-CONS-08E`](docs/tasks/COMPLETED/DOC-CONS-08E-separate-live-state-from-history.md)
leave the repository-health and first live-state compression boundaries
closed. Published documentation-only
[`PLAN-03A`](docs/tasks/COMPLETED/PLAN-03A-inventory-and-sequence-residual-source-topology-convergence.md)
dispositions the remaining cross-cutting source/test convergence without moving
files. Documentation-only
[`LIB-02F`](docs/tasks/COMPLETED/LIB-02F-define-shared-library-ownership.md)
then settled the two observed peer-implementation seams. Completed
[`MIG-04A`](docs/tasks/COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
moved the neutral artifact validator, five schemas, direct suite, and valid
fixtures to their permanent owners at executable checkpoint `17090ac` and cut
over every reviewed consumer. Completed
[`LIB-02G`](docs/tasks/COMPLETED/LIB-02G-extract-step08-scientific-evidence-contract.md)
then moved the public Step `08` scientific-evidence contract and direct suite
to their permanent neutral owners at executable checkpoint `f72cc0f`, with all
reviewed consumers cut over and no compatibility owner. The sole selected
residual package is
[`LIB-02H`](docs/tasks/IN_PROGRESS/LIB-02H-extract-step09-scientific-evidence-contract.md),
the bottom-up Step `09` contract extraction required before public Step `09c`
and reporting dependency removal. Selection begins bounded plan/review; no
LIB-02H executable or test change has begun. Scheduler, ingestion,
orchestration/profile, runtime, cluster, and default-branch work remain
deferred or unselected. `PROGRAM-01` and unrelated work remain frozen outside
their completed slices. Execute only one dependency-valid package at a time
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
