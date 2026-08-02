# REVIEW-ARCH-03B — Review `construct_STAR_index` migration architecture

## Objective

Challenge `MIG-03B` for one-owner placement, dependency direction, complete
caller cutover, test ownership, and reversible removal of both flat paths.

## Why this exists

The Step `00a` job combines STAR-index construction with operational reference
materialization, while its validator reaches a neutral library and several
cross-owner tests inventory flat paths. A path-only-looking move could create a
stage import, duplicate owner, premature descriptor/package contract, or
permanent compatibility surface.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen semantic DAG, target home, and direct migration mechanics;
  do not reopen them absent contradictory live evidence.
- Reject stage-to-stage implementation imports, package/bootstrap work,
  duplicate assets, speculative wrappers, symlinks, path discovery, and a new
  reference-preparation design.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03B](../TODO/REVIEW-REL-03B-review-construct-star-index-migration.md) — Fully: reliability review needs an architecture-corrected owner, consumer, and rollback boundary.

## Prerequisites

- Review the committed `MIG-03B` planning checkpoint against frozen parent
  `f3f2c2ab335d5a803550defd7676e9e9f9eb9fa4` without running or changing
  executable files.

## Required context

- `MIG-03B`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `00a` functional-owner inventory and
  contract; the complete direct path/import graph; and every proposed current
  and final path.

## Questions owned by this card

- None.

## In scope

- Final-owner fitness; semantic versus operational coupling; native-asset and
  test ownership; exact-file neutral-library loading; artifact-producer path
  evidence; independent cross-owner test placement; wrapper necessity; atomic
  cutover; one-implementation invariant; and reverse rollback order.

## Out of scope

- Reliability fault parity except where ownership obscures it, code changes,
  descriptor/package design, reference-preparation extraction, another stage,
  or a future campaign unit.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions and exact
  `MIG-03B` corrections recorded in the dated refactor log.

## Acceptance evidence

- No unresolved source/test owner, implementation-import, path-consumer,
  wrapper, duplicate-asset, atomicity, or rollback question remains.
- Every finding is incorporated into `MIG-03B` or retained with a named
  consequence and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03B`, `PIPELINE_PLAN.md` only if order changes, and the dated
  refactor log.

## Escalation conditions

- Stop if final placement requires a new package/descriptor runtime, a separate
  reference-materialization owner, or a supported caller that cannot cut over
  atomically.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
selection checkpoint `9507e03` and planning checkpoint `5ac7723`. One high
finding corrected mirrored test ownership: the Step `00a`-specific mocked-job
behavior case and its narrow fixtures move with the validator test, while the
cross-owner job roster/directive/mode assertions remain independent consumers.
One medium finding requires explicit relative-path maps keyed by existing public
basenames or semantic IDs in each mixed-layout inventory, preventing flat-root
assumptions from forcing wrappers or weakening exact roster equality. One low
finding makes the owner README state that native-asset placement is implemented
without claiming the still-unrealized descriptor/schema or package identity.
The stable `scripts` plus `src/norad` coverage boundary, artifact-producer path
transition, exact-file neutral-library dependency, direct atomic cutover,
reference-materialization non-edge, and no-wrapper/one-owner rollback design
otherwise pass. The campaign agent authored or reconciled and reviewed the
plan, so independent authorship is not claimed. No executable/test file changed
and no computational test ran.
