# PROFILE-03A — Materialize the local-pilot workflow profile

## Objective

Materialize the current CMH RNA-editing workflow as one explicit local-pilot
profile with a declarative projection of the canonical typed graph, authorized
inputs, outputs, assets, evidence boundaries, and references to public local
runner surfaces.

## Why this exists

The repository contains scripts, validators, receipts, and reports, but a
researcher-facing workflow needs one declared profile explaining how the
current functional owners fit together. A concrete profile can make the pilot
runnable and inspectable without prematurely creating an assay registry,
plugin system, or generic orchestrator.

## Fixed decisions

- The first profile covers the current CMH workflow only.
- It projects the canonical semantic-stage map and DAG into one declarative
  profile with explicit inputs, outputs, assets, direct and dry-run semantics,
  artifact propagation, and evidence projections.
- Existing scripts and validators remain with their respective functional
  stage, analysis, or evidence owners; the profile references their public
  surfaces rather than invoking or reimplementing them.
- This card exclusively owns the declarative profile schema, its validation,
  and a deterministic non-executable projection of canonical DAG nodes and
  public runner references. Orchestration retains executable plan generation,
  declared-contract resolution, runner-adapter selection and invocation,
  workflow coordination, and run and attempt state.
- The profile does not own semantic stage identities, artifact edges, target
  source topology, direct migration mechanics, environment readiness, success
  promotion, or the user-facing command dispatcher.
- Mechanical orientation labels remain distinct from biological strand
  interpretation. Outputs are `CMH-ranked candidates`, never validated editing
  sites.
- Future profile generalization requires concrete additional use cases.
- `CHOICE-ANALYSIS-01` remains owned by
  [`FUT-ANALYSIS-01`](FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md)
  for future custom-module trust and registration. It is context, not a
  blocker or question owned here.

## Blocked by

- None.

## Completion unblocks

- [CLI-03A](CLI-03A-implement-local-pilot-control-plane.md) — Partially: the control plane needs one concrete typed workflow profile before it can request an orchestration-owned plan for a complete local-pilot run.

## Prerequisites

- Use the current canonical semantic-stage map, functional inventory, and
  complete evidence and reporting chain at selection, rather than a frozen
  numeric-step roster.
- Keep abstract profile inputs separate from concrete run-state integration
  until the intake design is settled.
- Completed `ARCH-02C` and `ARCH-02D` are fixed context, not blockers. If
  the task needs to change descriptor ownership, source topology, or migration
  mechanics, stop and route that work to a separately reviewed amendment or
  migration card.

## Required context

- [`STAGE_MAP.md`](../../../src/norad/contracts/STAGE_MAP.md) for canonical
  stage identities and artifact edges,
  [`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md) for
  target ownership and dependency direction, and
  [`MIGRATION_MECHANICS.md`](../../../src/norad/contracts/MIGRATION_MECHANICS.md)
  for migration boundaries.
- Completed [`ARCH-02C`](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md)
  and [`ARCH-02D`](../COMPLETED/ARCH-02D-define-direct-migration-mechanics.md)
  as historical decision and acceptance context.
- [`FUT-ANALYSIS-01`](FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md),
  [`CHOICE-ANALYSIS-01`](../../design/QUESTIONS.md#choice-analysis-01--analysis-module-trust-and-registration-model),
  and [`FUT-SUCCESS-04`](FUT-SUCCESS-04-optional-analysis-and-archival-semantics.md)
  for future-only extension and optional-analysis boundaries.
- The current functional-owner inventory, scripts, jobs, schemas, reports,
  fixtures, receipts, artifact summaries, and report consumers.

## Questions owned by this card

- None. Profile serialization and any intake or migration split remain
  task-plan decision points within the existing architecture and question
  owners; unresolved cross-owner choices require integration-owner routing.

## In scope

- One named local-pilot profile for the current CMH workflow.
- Typed profile references to canonical stages, inputs, outputs, assets,
  prerequisites, and evidence projections.
- Declarative references to each stage's public local invocation and dry-run
  semantics.
- Artifact and report propagation through the profile.
- Profile validation and small fixture-backed non-executable projection
  generation.
- Explicit boundaries for optional, unavailable, or cluster-only stages.

## Out of scope

- A universal assay registry, plugin system, or generic orchestration layer.
- Rewriting analysis tools, validators, or report renderers.
- Atomic run claiming, run/attempt state and recovery, environment-readiness
  semantics, and user-facing command routing.
- New scientific methods, biological interpretation, altered CMH policy, CSU
  batch execution, production-data migration, or unplanned source migration.

## Deliverables

- A validated local-pilot profile definition.
- An inspectable non-executable projection naming every required canonical
  stage, artifact, and public runner reference.
- Fixture-backed profile validation, projection, dry-run-declaration, and
  negative-case evidence.

## Acceptance evidence

- A valid profile produces one deterministic, inspectable non-executable
  projection without glob discovery.
- Every profile node references one canonical stage identity and preserves the
  canonical direct-artifact edges, inputs, outputs, and evidence boundaries.
- Invalid profile, missing asset or predecessor, and unauthorized input cases
  fail before analysis.
- Existing artifact, report, transaction, and evidence contracts are preserved.
- Fixture output traces from input authorization through the final report
  without implying production, cluster, completed scientific-review, or
  biological evidence.

## Canonical documentation updates

- Target architecture and any owned profile diagram; accepted decisions and
  questions; exact profile and dry-run commands; task, roadmap, and current-
  state owners when required by the final integrated result.

## Escalation conditions

- Stop for untyped discovery, implicit installation, biological inference from
  mechanical orientation, or abstraction beyond the concrete CMH workflow.
- Re-plan if descriptor ownership, direct source migration, intake-state
  coupling, cross-owner or artifact schemas beyond the profile schema,
  executable planning, runner-adapter selection or invocation, reports,
  evidence status, or cluster execution enters scope.

## Completion record

Not started. This recovered TODO card selects no profile format, migration, or
scientific change.
