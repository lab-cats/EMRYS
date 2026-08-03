# REVIEW-ARCH-03D — Review `align_RNA_reads_with_STAR` migration architecture

## Objective

Challenge `MIG-03D` for dependency-valid selection, one-owner placement,
complete caller cutover, test ownership, and reversible removal of all three
flat source paths.

## Why this exists

The job embeds the producer path, the validator exact-loads a neutral library,
artifact evidence hashes the producer, and public CLI and validation tests
still assume flat script placement. A path-only-looking move could weaken an
inventory, introduce a package/runtime-discovery dependency, duplicate an
owner, or lose scheduler-specific test behavior.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen semantic DAG, target home, and direct-migration mechanics
  without reopening descriptors, packaging, transactions, or alignment policy.
- Reject cross-owner stage imports, global path mutation, runtime discovery,
  duplicate assets, speculative wrappers, symlinks, compatibility copies, and
  another migration owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03D](../TODO/REVIEW-REL-03D-review-align-rna-reads-with-star-migration.md) — Fully: reliability review requires an architecture-corrected owner, caller, and rollback boundary.

## Prerequisites

- Review committed `MIG-03D` against frozen parent `f9d6381` without running or
  changing executable/test files.

## Required context

- `MIG-03D`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `01` contract/inventory; producer,
  validator, job, exact invocation graph, tests, artifact evidence, coverage
  identity, and every proposed current/final path.

## Questions owned by this card

- None.

## In scope

- DAG eligibility; final-owner fitness; job-to-producer delegation; neutral
  report loading; artifact producer evidence; owner-local versus independent
  tests; explicit mixed-layout maps; wrapper necessity; atomic cutover; exact
  permissible path-only source edits; one-owner invariant; and rollback order.

## Out of scope

- Reliability fault detail except where ownership obscures it, code changes,
  package/descriptor/schema design, scheduler hardening, validator redesign,
  another stage, or a future unit.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions and exact
  `MIG-03D` corrections recorded in the dated refactor log.

## Acceptance evidence

- No unresolved source/test owner, dependency direction, path consumer,
  wrapper, duplicate, atomicity, evidence identity, or rollback question.
- Every finding is incorporated into `MIG-03D` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03D`, roadmap/handoff only if current status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, a separate
  neutral extraction, or a supported caller that cannot cut over atomically.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
