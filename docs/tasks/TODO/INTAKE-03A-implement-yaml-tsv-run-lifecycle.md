# INTAKE-03A — Implement YAML plus TSV run lifecycle

## Objective

Implement the bounded local-pilot request-admission and orchestration
lifecycle from validated YAML and TSV inputs through deterministic identity,
atomic claiming, attempts, resumability, and guarded success promotion.

## Why this exists

Researchers need to add data through an explicit contract rather than learn
filename conventions, hidden pairing rules, or state scattered across output
directories. The design owner must first settle the exact V1 lifecycle; this
card then turns that contract into inspectable local-pilot behavior.

## Fixed decisions

- One ready YAML request owns run policy and references one TSV sample
  manifest. The TSV owns repeated sample rows and pairing metadata.
- Filenames never determine pairing, sample order, partitions, or scientific
  meaning; inputs and policy are normalized and hashed before execution.
- Claiming is atomic. An identical normalized request may create a new attempt,
  while changed inputs or policy create a new run identity.
- Failed work remains inspectable and resumable, and raw data remains
  stationary.
- Success metadata is promoted only after required tasks, validators, evidence
  assembly, and the requested report succeed.
- This card coordinates one acceptance package across existing owners:
  `ingestion/` owns request, manifest, and input-reference admission and
  normalization; `contracts/` owns neutral schemas crossing owner boundaries;
  and `orchestration/` owns run and attempt identity and state, atomic claim
  persistence, lifecycle transitions, retry and resume decisions, requested
  report coordination, and guarded success promotion.
- Operational inboxes, run-state directories, locks, receipts, and recovery
  evidence remain outside source ownership.
- The package does not own the canonical semantic DAG, functional runner
  implementation, environment readiness, or the user-facing command surface.
  Orchestration consumes declared contracts and public owner entry points.
- [`INTAKE-02E`](INTAKE-02E-define-yaml-tsv-run-lifecycle.md) owns
  `CHOICE-INTAKE-01` and the exact V1 fields, directories, and transition
  design. Its accepted design is a genuine prerequisite for this implementation
  card.

## Blocked by

- [INTAKE-02E](INTAKE-02E-define-yaml-tsv-run-lifecycle.md) — Required: the exact V1 fields, directories, identity, claiming, transition, retry, and success-promotion design must be settled before implementation.

## Completion unblocks

- [CLI-03A](CLI-03A-implement-local-pilot-control-plane.md) — Partially: the control plane needs a stable request, manifest, run identity, and attempt lifecycle before it can plan or resume work.

## Prerequisites

- Require completed `INTAKE-02E` design and its settled `CHOICE-INTAKE-01`
  before implementation planning begins.
- Inventory current local-pilot input fields, reference contracts, output
  roots, receipt semantics, manifest consumers, report-request behavior, and
  the boundary between ingestion and orchestration.
- Require the exact V1 choices to be settled before implementation planning;
  unresolved fields or directories cannot be deferred into code. Keep each
  implementation slice within one source owner even though this card closes one
  cross-owner acceptance package.

## Required context

- [`INTAKE-02E`](INTAKE-02E-define-yaml-tsv-run-lifecycle.md) and
  [`CHOICE-INTAKE-01`](../../design/QUESTIONS.md#choice-intake-01--exact-v1-request-fields-run-package-and-operational-directories).
- [`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md) for
  ingestion, neutral-contract, orchestration, operational-state, and dependency
  boundaries, plus [`STAGE_MAP.md`](../../../src/norad/contracts/STAGE_MAP.md)
  for the canonical DAG consumed by orchestration.
- Completed [`ARCH-02C`](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md)
  as historical decision and acceptance context, not a blocker.
- Current configs, schemas, manifest consumers, publication transactions,
  receipt builders, report requests, input authorization, and recovery tests.

## Questions owned by this card

- None. Exact V1 request and state-layout choices remain with `INTAKE-02E` and
  its canonical question until an integration owner explicitly changes that
  ownership.

## In scope

- Ingestion-owned YAML request parsing, validation, and normalization.
- Ingestion-owned TSV manifest parsing, required columns, row validation, and
  normalization.
- Neutral request and manifest schemas plus explicit input and reference
  authorization and stable content identity.
- Orchestration-owned atomic claim persistence, run identity, attempt identity,
  and state transitions.
- Duplicate, changed-contract, retry, failure, resume, and success-promotion
  behavior.
- Inspectable run metadata, receipts, and operator-facing failure details.
- Tiny valid and invalid fixtures covering every lifecycle boundary.

## Out of scope

- Moving or cleaning raw data; public-data acquisition; a universal analysis-
  module registry; optional-analysis archival policy; cluster scheduling; or
  production-scale execution.
- Canonical DAG ownership, workflow-profile schema semantics, private runner
  implementation, environment readiness, and user-facing command routing.
- Storing operational inboxes, run state, locks, receipts, or recovery evidence
  under a source-code owner.

## Deliverables

- Versioned neutral local-pilot YAML and TSV schemas plus ingestion-owned
  admission and normalization implementations.
- Orchestration-owned run and attempt state plus atomic claim handling with
  explicit recovery outside source ownership.
- Deterministic normalization and identity artifacts.
- Focused fixtures and tests for valid, invalid, duplicate, changed, retry,
  resume, competing-claim, and premature-success cases.

## Acceptance evidence

- Equivalent normalized requests produce deterministic identity behavior, and
  duplicate claims cannot create competing active runs.
- Changed input or policy cannot silently reuse an old run.
- Failed attempts remain inspectable and resumable without corrupting or moving
  raw inputs.
- Success is not published before required work, validation, evidence, and
  authorized report outputs pass.
- No pairing, ordering, partition, input, or scientific meaning is inferred
  from a filename or uncontrolled glob.

## Canonical documentation updates

- Relevant schemas and contract documents; intake and state architecture;
  settled choices; exact supported commands and recovery behavior; roadmap,
  task-registry, and current-state owners when factually required.

## Escalation conditions

- Stop if identity depends on mutable paths or filename inference, if raw
  inputs must move, if cleanup is hidden, or if success can be promoted early.
- Broaden review when the state model changes report, evidence, schema,
  publication, or scientific contracts, or when an implementation slice would
  blur ingestion, neutral-contract, orchestration, or operational-state
  ownership.

## Completion record

Not started. This recovered TODO card does not settle `CHOICE-INTAKE-01` or
authorize implementation before its design owner is reconciled.
