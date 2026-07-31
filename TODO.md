# TODO

This file is the short prioritized index. Detailed scope, dependencies,
questions, and acceptance evidence belong to one card in
[`docs/tasks/`](docs/tasks/); authoritative package order belongs in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and exact resume point belong in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. After the current context-policy documentation package is clean, pushed,
   and upstream-equal, select and plan
   [`CONCURRENCY-01`](docs/tasks/TODO/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md).
2. Complete and push `CONCURRENCY-01`, then pause for the required user
   discussion about how to leverage multiple documentation/card sidecars and
   choose a safe first concurrency strategy.
3. Select
   [`PROGRAM-01`](docs/tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
   only after that discussion and separate task-specific approval.
4. Reassess the maintenance and main-refactor tranches under the resulting
   program model. `TEST-01C` remains the first uncompleted Phase `01`
   characterization card in the inherited roadmap, but its position and the
   rest of that sequence are provisional until this reassessment. Do not treat
   maintenance order as a blocker or these notes as task authorization.

Before `PROGRAM-01`, the preserved baseline is `TEST-01C` through `TEST-01F`,
then the explicit `TEST-01Z` behavior-readiness decision, followed only after
an affirmative decision by architecture delivery, applicable reviews, and
`PLAN-02Z`. `PROGRAM-01` must confirm or revise that sequence before another
card is selected.

Selecting a card starts read-only planning under the
[`task-start router`](docs/operations/TASK_START.md) and requires a separate
approved plan before implementation.

## Recommended maintenance order

The following is roadmap order, not card-blocker metadata. None of these cards
technologically blocks `TEST-01C` or authorizes work without its own approved
plan:

1. Establish isolated multi-sidecar authoring and serialized integration
   through
   [`CONCURRENCY-01`](docs/tasks/TODO/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md),
   then pause for the required user strategy discussion.
2. If separately selected after that discussion, establish rolling-wave
   planning and coordination cohorts through
   [`PROGRAM-01`](docs/tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md).
3. Reassess rather than freezing the remaining order now. The current expected
   candidates begin with extracting and behavior-locking the documentation
   validator through
   [`DOC-GATE-01`](docs/tasks/TODO/DOC-GATE-01-extract-documentation-validator.md).
4. Correct live task-dependency semantics and validator enforcement through
   [`TASK-REG-01`](docs/tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md).
5. Put [`DOC-IA-01`](docs/tasks/TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md)
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
  [`CONCURRENCY-01`](docs/tasks/TODO/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
  and
  [`PROGRAM-01`](docs/tasks/TODO/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md).
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
