# TEST-01F — Create independent contract goldens

## Objective

Add small, independent goldens and mutation-resistant oracles for critical
serialized and scientific-state contracts.

## Why this exists

The `TG-06` baseline shows that broad integrated fixture builders often import
production vocabulary. Independent known-good artifacts are needed to detect
producer/test shared defects before structural migration.

## Fixed decisions

- A golden is a small reviewed known-good output whose expected bytes or
  semantics are stored independently from production code.
- Independent goldens supplement rather than replace integrated fixtures.
- TSV, JSON, schemas, receipts, and byte-sensitive fixtures receive adjacent
  prose, not inline comments.

## Blocked by

- [TEST-01E](../TODO/TEST-01E-characterize-slurm-wrapper-contracts.md) — Required: all public and scheduler boundaries must be inventoried first.

## Completion unblocks

- [TEST-01Z](../TODO/TEST-01Z-decide-behavior-contract-sufficiency.md) — Fully: the measured behavior-sufficiency decision can be made.

## Prerequisites

- Reclassify current fixtures as independent, mixed, or producer-coupled at
  the live predecessor.

## Required context

- `TEST_BASELINE.md` `TG-06` and golden-output table, `REFACTOR_AUDIT.md`
  findings `RA-019`, `RA-020`, and `RA-024`, public schemas, serializers,
  fixtures, and evidence-state rules.

## Questions owned by this card

- None.

## In scope

- Independent representative schemas, headers, canonical JSON/TSV/receipt
  bytes, status transitions, evidence boundaries, and shared-policy mutation
  cases.
- Concise adjacent documentation for each opaque golden fixture family.

## Out of scope

- Rebuilding every fixture, importing production constants into the oracle,
  changing serializers, or asserting production/cluster/scientific evidence.

## Deliverables

- Bounded independent fixture/oracle files and focused mutation tests.
- An updated independence classification and gap disposition.

## Acceptance evidence

- Named production-constant mutations fail while unmodified valid outputs pass.
- Golden bytes are deterministic and independently reviewable.
- Focused and complete applicable gates pass without production behavior change.

## Canonical documentation updates

- `TEST_BASELINE.md`, applicable adjacent fixture READMEs, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, `TODO.md`, and this card.

## Escalation conditions

- Stop if a golden would freeze an unapproved biological interpretation,
  duplicate a huge integrated fixture, or require deriving expectations from
  the producer under test.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
