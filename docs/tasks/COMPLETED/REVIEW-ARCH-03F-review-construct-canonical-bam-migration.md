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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `bc2112ce22118c89fdbdc850738eae616208ead4`.

- **High — neutral API and loader identity were underspecified:** accept one
  mode-`0644` private `src/norad/libraries/bam_validation.py` containing exactly
  behavior-preserving `run_tool` and `parse_header`. Freeze identity
  `_norad_bam_validation`, readiness `_NORAD_BAM_VALIDATION_READY`, exact
  cached-`__file__` and callable checks, owned-partial cleanup, foreign-state and
  `sys.path` preservation, and one path-bearing fail-closed diagnostic in each
  caller. Add no report dependency, CLI, package identity, or stage-specific
  check logic.
- **High — the two executable slices lacked exact file ceilings:** helper
  preparation is exactly five files: add the neutral module and one neutral test
  suite, modify only the Step `02`, `04`, and `05` validators. Owner cutover is
  exactly five moves plus ten caller/harness updates: Make, artifact producer and
  assertion, public CLI, SLURM, validation roster, validation-report map,
  BAM-helper caller map, coverage row, and literal Make fixture. A sixth move,
  eleventh update, or downstream direct-test edit reopens architecture review.
- **Medium — test and artifact ownership needed separation:** the new neutral
  suite owns helper behavior and the three-caller loader matrix. Existing
  Step-specific direct tests remain stage-owned and unchanged during helper
  extraction but run as its affected regression set. Artifact evidence does not
  change until owner cutover, when only Step `02` producer path/hash and its
  exact existing assertion change; public artifact contracts remain unchanged.
- **Accepted architecture and rollback:** `construct_canonical_BAM` is the only
  live-DAG-supported next owner. Two published executable slices are preferable
  to a wrapper or copied helper. Revert documentation, then the native owner
  move, then the neutral helper so the temporarily restored flat validator never
  loses its dependency. No descriptor, schema, package marker, wrapper,
  compatibility copy, peer import, or downstream-owner migration is warranted.
- **Evidence boundary:** this was a read-only committed-time adversarial pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
