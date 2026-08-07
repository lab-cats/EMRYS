# INTAKE-02E — Define YAML plus TSV run lifecycle

## Objective

Specify the versioned request, sample-manifest, claiming, run-identity,
attempt, success-promotion, retry, and failure lifecycle for current-format
ingestion.

## Why this exists

The intended user experience is to place a valid request in a known location,
start NORAD, and receive artifacts and a report autonomously. Current
`data/raw` is storage for pre-staged inputs, not an intake state machine.

## Fixed decisions

- One ready YAML request references one TSV sample manifest: YAML owns run
  policy; TSV owns repeated sample rows.
- V1 accepts paired FASTQ/FASTQ.GZ plus registered FASTA/GTF inputs.
- Claim atomically before execution; normalize/hash an immutable run contract.
- Identical normalized requests reuse a run with a new attempt; changed input
  or policy creates a new run.
- Failed requests remain resumable. Promote request metadata only after
  current required tasks, validators, evidence assembly, and requested report
  succeed. Raw data remains stationary.
- This card owns top-level YAML fields, representation, directory, identity,
  and transition design. In the target implementation, ingestion owns
  admission and normalization, `contracts/` owns neutral schemas that cross
  owners, orchestration owns run/attempt state and coordination, and
  operational directories remain outside source ownership.
- The corrected `RPT-02` contract owns report-profile selectors and normalized
  reporting semantics. Intake may reference that contract but must not copy
  its profile names, field roster, projection grammar, or publication policy.
- Deliberate deferral of `CHOICE-INTAKE-01` does not block this recovery
  integration. It still must be resolved before `INTAKE-03A` implementation
  planning reaches the fields, directories, identity, or transitions it owns;
  no report-related dependency is inferred while the intake and reporting
  choices remain deferred.

## Blocked by

- [ARCH-02C](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: ingestion, orchestration, contract, and state ownership must have target homes.

## Completion unblocks

- [INTAKE-03A](INTAKE-03A-implement-yaml-tsv-run-lifecycle.md) — Fully: implementation cannot proceed meaningfully until this card accepts the exact V1 fields, directories, identity, claim, transition, retry, and success-promotion design.

## Prerequisites

- Inventory current manifest fields, reference contracts, output roots,
  retry/receipt semantics, and report request behavior.

## Required context

- Current configs, schemas, manifest consumers, `data/raw` policy, publication
  transactions, future intake diagram, and filesystem-inspectable state
  constraints.

## Questions owned by this card

- [`CHOICE-INTAKE-01`](../../design/QUESTIONS.md#choice-intake-01--exact-v1-request-fields-run-package-and-operational-directories).

## In scope

- YAML and TSV schemas, lifecycle states, atomic claim, normalized identity,
  attempts, resumability, computational-success boundary, promotion metadata,
  and operator-visible failure state.

## Out of scope

- Implementing ingestion, moving raw files, automatic cleanup, SRA/GenBank
  acquisition, analysis-module registries, or future optional-analysis archive
  policy.

## Deliverables

- A contract/state-machine design and concrete implementation-card split.
- Valid, invalid, duplicate, retry, changed-contract, failure, and promotion
  acceptance scenarios.

## Acceptance evidence

- Identity and state transitions are deterministic, inspectable, crash-safe,
  and do not permit duplicate claims or premature success promotion.
- YAML and TSV responsibilities do not overlap or infer metadata from names.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, future intake diagram, `DECISIONS.md`,
  `QUESTIONS.md`, `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if exact success semantics depend on unapproved optional analyses, if
  raw input movement is proposed, or if identity can vary with mutable paths.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
