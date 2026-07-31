# TODO

This file is the short prioritized index. Detailed scope, dependencies,
questions, and acceptance evidence belong to one card in
[`docs/tasks/`](docs/tasks/); authoritative package order belongs in
[`docs/design/PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the current
checkout and exact resume point belong in
[`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md).

## Immediate

1. Select and plan
   [`TEST-01C`](docs/tasks/TODO/TEST-01C-characterize-validation-check-rosters.md),
   the next remaining behavior-characterization package.
2. Complete the approved Phase 01 sequence through
   [`TEST-01D`](docs/tasks/TODO/TEST-01D-characterize-public-cli-contracts.md),
   [`TEST-01E`](docs/tasks/TODO/TEST-01E-characterize-slurm-wrapper-contracts.md),
   and
   [`TEST-01F`](docs/tasks/TODO/TEST-01F-create-independent-contract-goldens.md).
3. Make the explicit behavior-readiness decision in
   [`TEST-01Z`](docs/tasks/TODO/TEST-01Z-decide-behavior-contract-sufficiency.md).
   A negative decision creates bounded closure cards; it does not begin
   architecture work.
4. Only after an affirmative decision, proceed through the Phase 02 design
   cards and
   [`PLAN-02Z`](docs/tasks/TODO/PLAN-02Z-integrate-future-task-sequence.md),
   then the three independent reviews.

Selecting a card starts read-only planning and requires a separate approved
plan before implementation.

## Current-program task families

- Architecture, semantic stages, direct migration, intake, and shared-library
  design: [`ARCH-02A`](docs/tasks/TODO/ARCH-02A-inventory-functional-stages-and-contracts.md)
  through [`LIB-02F`](docs/tasks/TODO/LIB-02F-define-shared-library-ownership.md).
- Science/comprehensive reporting and concise/durable logging:
  [`RPT-01`](docs/tasks/TODO/RPT-01-characterize-comprehensive-report.md) and
  [`LOG-01`](docs/tasks/TODO/LOG-01-characterize-current-output.md) onward.
- Documentation ownership, glossary, READMEs, user overview, code comments, and
  local context:
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
