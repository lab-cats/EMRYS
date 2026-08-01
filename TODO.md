# TODO

This file is the short prioritized index. Detailed scope, dependencies,
questions, and acceptance evidence belong to one card in
[`docs/tasks/`](docs/tasks/); authoritative package order belongs in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and exact resume point belong in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Continue the explicitly approved local-only Phase `01` characterization
   tranche. [`TEST-01C`](docs/tasks/COMPLETED/TEST-01C-characterize-validation-check-rosters.md)
   is complete locally; select
   [`TEST-01D`](docs/tasks/TODO/TEST-01D-characterize-public-cli-contracts.md)
   next from its clean committed descendant.
2. Promote only through `TEST-01D` → `TEST-01E` → `TEST-01F` → `TEST-01Z`
   when each card's acceptance, focused and complete local gates,
   documentation consistency, clean state, and adversarial review pass.
3. Stop after `TEST-01Z`. A negative decision may create only its bounded
   `TEST-01G-*` closure cards and later `TEST-01Z-R*` reassessment card; do not
   execute them in this tranche. A positive decision names released Phase `02`
   roots but does not begin them.

This tranche is local and unpushed. `CONCURRENCY-02`, `PROGRAM-01`, the paused
concurrency attempts, the preserved researcher pilot, and Phase `02` remain
untouched and are not sequencing blockers for these five selected cards.

Selecting a card starts read-only planning under the
[`task-start router`](docs/operations/TASK_START.md) and requires a separate
approved plan before implementation.

## Recommended maintenance order

The following is roadmap order, not card-blocker metadata. None of these cards
technologically blocks `TEST-01C` or authorizes work without its own approved
plan:

1. Preserve the completed isolated multi-sidecar/serialized-integration policy
   in
   [`CONCURRENCY-01`](docs/tasks/COMPLETED/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
   and the completed 2026-07-31 strategy discussion as the basis for this
   card-bootstrap package.
2. Establish the manual fragment contract through
   [`CONCURRENCY-02`](docs/tasks/TODO/CONCURRENCY-02-define-integration-fragment-protocol.md)
   in its own separately planned and approved package.
3. Then establish rolling-wave planning and coordination cohorts through
   [`PROGRAM-01`](docs/tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md).
4. Reassess rather than freezing the remaining order now. The current expected
   candidates begin with extracting and behavior-locking the documentation
   validator through
   [`DOC-GATE-01`](docs/tasks/TODO/DOC-GATE-01-extract-documentation-validator.md).
5. After their recorded prerequisites are complete, add structural fragment
   enforcement through
   [`CONCURRENCY-03`](docs/tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md),
   implement proposal/review lifecycle states through
   [`TASK-LIFECYCLE-01`](docs/tasks/TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md),
   and then implement logical epic indexes through
   [`TASK-EPIC-01`](docs/tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md).
   `CONCURRENCY-03` uses the synthetic `CONCURRENCY-02` exchange rather than
   requiring early pilot integration.
6. Select the `PROGRAM-01`-generated pilot-integration card only after
   `CONCURRENCY-02`, `PROGRAM-01`, `DOC-GATE-01`, `CONCURRENCY-03`, and
   `TASK-LIFECYCLE-01` are complete. `TASK-EPIC-01` is not a prerequisite
   unless later evidence establishes a genuine dependency.
7. Correct live task-dependency semantics and validator enforcement through
   [`TASK-REG-01`](docs/tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md).
8. Put [`DOC-IA-01`](docs/tasks/TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md)
   first within the Phase `02` documentation family so it can produce the
   no-loss `AGENTS.md` slim-down and later consolidation cards.

## Current-program task families

- Architecture, semantic stages, direct migration, intake, and shared-library
  design: [`ARCH-02A`](docs/tasks/TODO/ARCH-02A-inventory-functional-stages-and-contracts.md)
  through [`LIB-02F`](docs/tasks/TODO/LIB-02F-define-shared-library-ownership.md).
- Science/comprehensive reporting and concise/durable logging:
  [`RPT-01`](docs/tasks/TODO/RPT-01-characterize-comprehensive-report.md) and
  [`LOG-01`](docs/tasks/TODO/LOG-01-characterize-current-output.md) onward.
- Operating model and coordination:
  [`CONCURRENCY-01`](docs/tasks/COMPLETED/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
  through
  [`CONCURRENCY-03`](docs/tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md),
  [`PROGRAM-01`](docs/tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md),
  [`TASK-LIFECYCLE-01`](docs/tasks/TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md),
  and
  [`TASK-EPIC-01`](docs/tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md).
- Documentation ownership, glossary, READMEs, user overview, code comments, and
  local context, with documentation-validator and task-registry maintenance
  tracked separately:
  [`DOC-GATE-01`](docs/tasks/TODO/DOC-GATE-01-extract-documentation-validator.md),
  [`TASK-REG-01`](docs/tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md),
  [`DOC-IA-01`](docs/tasks/TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md)
  through [`CONTEXT-09`](docs/tasks/TODO/CONTEXT-09-define-local-maintainer-context.md).
- Large-file dispositions:
  [`SIZE-07`](docs/tasks/TODO/SIZE-07-refresh-large-file-inventory.md) and its
  named family cards; report rendering is owned by
  [`RPT-05B`](docs/tasks/TODO/RPT-05B-decompose-report-rendering-modules.md).
- Final local closure:
  [`AUDIT-99`](docs/tasks/TODO/AUDIT-99-final-refactor-and-documentation-audit.md).

## Runtime and scientific blockers

The live blockers and evidence boundary are canonical in
[`HANDOFF.md`](docs/operations/HANDOFF.md#current-blockers). The unresolved
operator and scientific questions are canonical in
[`QUESTIONS.md`](docs/design/QUESTIONS.md#open-operational-and-scientific-questions).
Remote, cluster, production scientific-review, and biological-policy work do
not begin as part of the local architecture program.

## Future-only

- Preprocessing profiles, analysis modules, and custom R boundary:
  [`FUT-ANALYSIS-01`](docs/tasks/TODO/FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md).
- Public reference and SRA acquisition:
  [`FUT-DATA-02`](docs/tasks/TODO/FUT-DATA-02-public-reference-and-sra-acquisition.md).
- Installable `norad` control plane:
  [`FUT-CLI-03`](docs/tasks/TODO/FUT-CLI-03-installable-norad-control-plane.md).
- Required/optional analysis and archival semantics:
  [`FUT-SUCCESS-04`](docs/tasks/TODO/FUT-SUCCESS-04-optional-analysis-and-archival-semantics.md).
- Documentation-health skill and later skill evaluation:
  [`DOC-SKILL-10`](docs/tasks/TODO/DOC-SKILL-10-build-documentation-health-skill.md)
  and
  [`SKILL-11`](docs/tasks/TODO/SKILL-11-evaluate-repository-skill-opportunities.md).

Do not mark an item complete until its acceptance evidence has been inspected,
its canonical owners are updated, and its card is moved with all inbound links
repaired.
