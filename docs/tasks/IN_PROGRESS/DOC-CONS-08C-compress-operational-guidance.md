# DOC-CONS-08C — Compress operational guidance

## Objective

Index and separate exact operator commands from symptom-driven diagnosis and
functional contract detail while preserving all recovery and safety meaning.

## Why this exists

`RUNBOOK.md` and `TROUBLESHOOTING.md` are the largest documentation owners.
They repeat commands, validator templates, policy, stage contracts, and dated
state, yet also contain unique recovery procedures and scientific-review
instructions that cannot be deleted safely.

## Fixed decisions

- `RUNBOOK.md` owns supported setup, validation, execution, inspection, and
  recovery commands.
- `TROUBLESHOOTING.md` owns symptom, cause, diagnosis, and fix and links the
  exact runbook command.
- Stage semantics and scientific limits belong in colocated functional
  contracts.
- Transaction-specific lock, rollback, signal, and partial-publication
  recovery stays distinct even when wording overlaps.
- Substantive embedded programs remain until an equivalent tested executable
  owner exists; documentation compression never performs an untested code
  extraction.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: the operations boundary and no-loss ledger must be approved.

## Completion unblocks

- None.

## Prerequisites

- Inventory headings and internal/inbound links in both live files; compare
  only the direct contract or helper needed for each proposed removal.

## Required context

- The runbook/troubleshooting rows in
  `DOCUMENTATION_OWNERSHIP.md`, `RUNBOOK.md`, `TROUBLESHOOTING.md`, adjacent
  `scripts/git_orchestration/README.md`, and locally implicated contracts.

## Questions owned by this card

- None.

## In scope

- Adding durable human-readable indexes.
- Replacing exact duplicated commands in troubleshooting with precise runbook
  links while preserving diagnostic steps and limitations.
- Consolidating genuinely common validator explanation into one template plus
  per-owner differences.
- Replacing detailed stage semantics in the runbook with contract links after
  sentence-level no-loss review.
- Moving or linking status/history only to already established owners.
- Classifying every substantive inline program as already-owned, retained, or
  requiring a separately approved executable extraction card.

## Out of scope

- Changing a command, CLI, executable, validator, schema, test, scientific
  policy, recovery contract, or runtime behavior; extracting code without
  parity tests; merging distinct transaction recovery paths.

## Deliverables

- Indexed, single-purpose operations owners and a disposition for every
  removed duplicate or retained inline program.

## Acceptance evidence

- Every supported command remains exact and reachable from the runbook.
- Every symptom retains cause, diagnosis, fix, and stage-specific limitation.
- Every moved contract/scientific statement is present in its destination
  before the old copy is removed.
- Dry-run, login-node, dependency, destructive-action, evidence, and recovery
  cautions remain at action points.
- Documentation links and the documentation gate pass; computational tests are
  not run unless the final diff unexpectedly changes an executable consumer.

## Canonical documentation updates

- `RUNBOOK.md`, `TROUBLESHOOTING.md`, only directly affected contracts/helper
  READMEs, the ownership ledger, and this card.

## Escalation conditions

- Stop if two operational owners disagree, a command lacks a tested owner, or
  compression could change recovery, scientific, evidence, or exit meaning.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
