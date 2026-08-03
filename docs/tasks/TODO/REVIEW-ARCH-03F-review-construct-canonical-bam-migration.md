# REVIEW-ARCH-03F — Review `construct_canonical_BAM` migration architecture

## Objective

Challenge `MIG-03F` for live-DAG selection, one-owner placement, bounded neutral
BAM-helper extraction, complete caller cutover, test ownership, and reversible
removal of all three flat Step `02` native-asset paths.

## Why this exists

The Step `04` and Step `05` validators ambient-import helper functions from the
Step `02` validator. Moving that validator directly would preserve a prohibited
peer-implementation dependency or require a legacy wrapper. A neutral extraction
could instead overreach into broad library design, public package identity, or
downstream-stage migration unless its exact API, callers, tests, and rollback
are bounded first.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen semantic DAG, final owner home, dependency direction, and
  direct-migration mechanics without reopening stage identity, descriptors,
  orchestration, or scientific BAM policy.
- Reject peer-stage implementation imports, copied helpers, global path
  mutation, runtime discovery, speculative wrappers, symlinks, compatibility
  copies, public package identity, and another functional-owner migration.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03F](REVIEW-REL-03F-review-construct-canonical-bam-migration.md) — Fully: reliability review requires an architecture-corrected helper, owner, caller, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03F` against frozen parent `fa79883` without running or
  changing executable/test files.

## Required context

- `MIG-03F`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; Step `02`, `04`, and `05` contracts and validators;
  exact helper call graph; producer/job/tests; neutral libraries owner; public
  path maps; Make; artifact evidence; coverage identity; and every proposed
  current/final path.

## Questions owned by this card

- Is one private `bam_validation.py` containing exactly `run_tool` and
  `parse_header` the smallest valid neutral owner, and what readiness/API/cache
  contract must its three caller-local exact loaders enforce?
- Which direct and cross-owner tests remain with their functional owner, which
  helper behaviors require one neutral direct suite, and can the helper and
  owner move remain two separately reversible executable slices under one card?

## In scope

- DAG eligibility; final-owner fitness; neutral helper name/API/dependencies;
  Step `02`/`04`/`05` loader direction and distinct caller depths; job
  delegation; validation-report loading; owner-local versus neutral/cross-owner
  tests; explicit caller maps; wrapper necessity; executable-slice atomicity;
  permissible source edits; one-owner invariants; artifact identity; coverage
  ownership; and rollback order.

## Out of scope

- Reliability fault detail except where ownership obscures it; code changes;
  package/descriptor/schema design; broad BAM library design; scheduler
  hardening; validator/scientific-contract redesign; moving Step `04`, Step
  `05`, or another owner; and future units.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions, an exact
  executable/test path ceiling for both slices, and corresponding `MIG-03F`
  corrections recorded in the dated refactor log.

## Acceptance evidence

- No unresolved source/test owner, dependency direction, import identity,
  helper API, path caller, wrapper, duplicate, atomicity, evidence identity,
  coverage owner, or rollback question.
- Every finding is incorporated into `MIG-03F` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03F`, roadmap/handoff only where current status changes, and
  the dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, a permanent
  wrapper, copied helpers, another functional-owner migration, or shared-helper
  scope that cannot stay limited to the two proven functions and three current
  validators.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
