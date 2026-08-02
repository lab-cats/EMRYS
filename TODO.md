# TODO

This file is the short prioritized index. Detailed scope, dependencies,
questions, and acceptance evidence belong to one card in
[`docs/tasks/`](docs/tasks/); authoritative package order belongs in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and exact resume point belong in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Preserve the completed and published Phase `01` characterization tranche.
   [`TEST-01C`](docs/tasks/COMPLETED/TEST-01C-characterize-validation-check-rosters.md)
   through [`TEST-01Z`](docs/tasks/COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md)
   are complete, the row-by-row TEST-01Z decision is affirmative, and the
   corrected tip passed adversarial review before publication.
2. Preserve the completed documentation-only logging-design lineage:
   [`LOG-01`](docs/tasks/COMPLETED/LOG-01-characterize-current-output.md)
   characterizes current behavior, and
   [`LOG-02`](docs/tasks/COMPLETED/LOG-02-define-logging-contract.md) defines the
   target contract. Neither changes current output or activates logging.
3. Preserve the completed manual fragment protocol in
   [`CONCURRENCY-02`](docs/tasks/COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md).
   Its synthetic exchange is protocol evidence only; the researcher pilot
   remains substantively unreviewed and unintegrated.
4. Preserve the completed implementation-backed functional inventory in
   [`ARCH-02A`](docs/tasks/COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md).
   Preserve the completed interposed workflow bootstrap in
   [`JIT-01`](docs/tasks/COMPLETED/JIT-01-establish-self-hosting-thin-slice-delivery.md).
   The next eligible critical-runway package is `ARCH-02B`, followed by
   `ARCH-02C` and `ARCH-02D` in dependency order; none is selected merely by
   being eligible.
5. TEST-01Z's side of `CODEDOC-05` is satisfied, but that card retains its
   `DOC-IA-01` blocker. Both recorded prerequisites for `SIZE-07` are now
   complete; its technical eligibility does not override the active runway
   freeze.

The temporary critical runway in
[`TASK_START.md`](docs/operations/TASK_START.md#temporary-critical-runway)
freezes all other work until the first physical source migration and explicit
reassessment. `PROGRAM-01` remains in progress with only its first runway slice
complete. Roadmap order is not blocker metadata.

## Frozen pre-runway maintenance context

The following earlier sequence is preserved for later reassessment but is
currently dead/out of scope. It is roadmap context, not card-blocker metadata,
and authorizes no work without a separately approved plan:

1. Preserve the completed isolated multi-sidecar/serialized-integration policy
   in
   [`CONCURRENCY-01`](docs/tasks/COMPLETED/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
   and the completed 2026-07-31 strategy discussion as the basis for this
   card-bootstrap package.
2. Preserve the completed `codex/strategy-task-cards` bootstrap; its future
   cards remain subject to separate selection and planning.
3. Preserve the completed manual fragment contract and synthetic exchange in
   [`CONCURRENCY-02`](docs/tasks/COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md).
4. Preserve the first completed critical-runway slice of
   [`PROGRAM-01`](docs/tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md);
   its unsliced remainder remains in progress and frozen during the current
   architecture runway.
5. Reassess rather than freezing the remaining order now. The current expected
   candidates begin with extracting and behavior-locking the documentation
   validator through
   [`DOC-GATE-01`](docs/tasks/TODO/DOC-GATE-01-extract-documentation-validator.md).
6. After their recorded prerequisites are complete, add structural fragment
   enforcement through
   [`CONCURRENCY-03`](docs/tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md),
   implement proposal/review lifecycle states through
   [`TASK-LIFECYCLE-01`](docs/tasks/TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md),
   and then implement logical epic indexes through
   [`TASK-EPIC-01`](docs/tasks/TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md).
   `CONCURRENCY-03` uses the synthetic `CONCURRENCY-02` exchange rather than
   requiring early pilot integration.
7. Select the `PROGRAM-01`-generated pilot-integration card only after
   `CONCURRENCY-02`, `PROGRAM-01`, `DOC-GATE-01`, `CONCURRENCY-03`, and
   `TASK-LIFECYCLE-01` are complete. `TASK-EPIC-01` is not a prerequisite
   unless later evidence establishes a genuine dependency.
8. Correct live task-dependency semantics and validator enforcement through
   [`TASK-REG-01`](docs/tasks/TODO/TASK-REG-01-correct-task-dependency-semantics.md).
9. Put [`DOC-IA-01`](docs/tasks/TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md)
   first within the Phase `02` documentation family so it can produce the
   no-loss `AGENTS.md` slim-down and later consolidation cards.

## Current-program task families

- Architecture, semantic stages, direct migration, intake, and shared-library
  design: [`ARCH-02A`](docs/tasks/COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md)
  is complete; the remaining family runs from
  [`ARCH-02B`](docs/tasks/IN_PROGRESS/ARCH-02B-define-semantic-stage-map.md) through
  [`LIB-02F`](docs/tasks/TODO/LIB-02F-define-shared-library-ownership.md).
- Science/comprehensive reporting and concise/durable logging:
  [`RPT-01`](docs/tasks/TODO/RPT-01-characterize-comprehensive-report.md) and
  completed [`LOG-01`](docs/tasks/COMPLETED/LOG-01-characterize-current-output.md)
  followed by completed
  [`LOG-02`](docs/tasks/COMPLETED/LOG-02-define-logging-contract.md).
- Operating model and coordination:
  [`CONCURRENCY-01`](docs/tasks/COMPLETED/CONCURRENCY-01-enable-isolated-concurrent-documentation-lanes.md)
  and completed
  [`CONCURRENCY-02`](docs/tasks/COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md),
  followed by
  [`CONCURRENCY-03`](docs/tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md),
  [`PROGRAM-01`](docs/tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md),
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
