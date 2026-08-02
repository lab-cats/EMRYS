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

Completed 2026-08-02 as a separately approved local-only documentation
exception. `RUNBOOK.md` now has a durable command index, a workflow-contract
crosswalk for Steps `00a` through `09c`, one shared structured-validator
convention, and an explicit disposition for substantive inline programs. Exact
setup, validation, execution, inspection, recovery, and scientific-review
commands remain reachable; transaction recovery and action-point cautions stay
in place. Repeated stage semantics now link colocated contracts, including the
Step `08` DP/AD parsing rules added to its canonical contract before their
runbook copy was removed. The runbook is reduced from 4,559 to 4,327 lines.

`TROUBLESHOOTING.md` now has a durable issue index, retains symptom, cause,
diagnosis, fix, owner-specific limitations, and distinct transaction recovery,
and links exact duplicated commands to the runbook. Common structured-validator
response guidance is stated once with each owner's material differences kept
locally. The troubleshooting owner is reduced from 2,705 to 2,651 lines.

Independent anchor/ownership, diagnostic-owner, and sentence-level no-loss
reviews passed. The complete package diff changes only Markdown documentation;
`git diff --check` and the final repository documentation gate pass.
Computational Python, shell, R, report-runtime, full-suite, and cluster
validation are not applicable. No executable, configuration, generation,
schema, fixture, report-template, dependency, source-layout, public-interface,
scientific-policy, or test-harness behavior changed, and no runtime, cluster,
scientific-review, or biological-readiness evidence was created. The branch
remains intentionally local-only and must not be pushed by this package.
`DOC-CONS-08D` through `DOC-CONS-08H` remain unselected; this completion does
not change ordinary runway order.
