# REVIEW-ARCH-03L — Review partitioned cohort mpileup migration architecture

## Objective

Challenge `MIG-03L` for live-DAG choice, final stage/test placement, exact
caller cutover, private report/test-helper loading, artifact provenance,
coverage ownership, executable-mode continuity, and reversible removal of all
three flat Step `07` native-asset paths.

## Why this exists

Step `07` is the only currently eligible unmigrated owner. Its validator
privately exact-loads the neutral report library from a flat-path root, while
its direct test uses an ambient root-test helper import. Relocation must
correct both depths, preserve the directly executable producer and mode-
`0644` scheduler surface, and cut over artifact provenance without creating a
package, `PYTHONPATH` dependency, wrapper, duplicate test owner, schema
extraction, or second functional-owner migration.

## Fixed decisions

- Review only; corrections land in cards and current planning documentation,
  never executable/test source under this card.
- Apply the frozen semantic identity, direct DAG, stage/test homes, dependency
  direction, and migration mechanics without reopening descriptors,
  orchestration, schemas, pileup/filter/selector policy, artifact policy, or
  bcftools policy.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, package identity, ambient import paths, and any Step
  `08` or later owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03L](../TODO/REVIEW-REL-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Fully: reliability review requires an architecture-corrected owner, loader, caller, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03L` against frozen parent `b73b12b` without running
  or changing executable/test files.

## Required context

- `MIG-03L`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `07` stage contract; producer, validator,
  job, and direct tests; public path maps; Make and literal fixture; neutral
  validation-report owner/tests; artifact mapping and Step `07` reconciliation;
  coverage identity; partition manifests; and every proposed current/final
  path.

## Questions owned by this card

- Is Step `07` the only dependency-valid unmigrated identity after `MIG-03K`,
  with Step `08` remaining wholly uncreated and unselected?
- What final repository-root depths preserve the neutral report loader and
  root test-roster helper without `sys.path` mutation, and what cache/path/
  failure cases belong to the moved direct test?
- Is five moves plus nine integration-owner updates the complete executable/
  test ceiling, with no hidden config, scaffold, package, or compatibility
  owner?
- Do modes, exact final producer artifact path/hash, Step `07` artifact
  identities and receipt-marker interpretation, coverage row, Make/static
  routes, atomic cutover, and reverse rollback remain assigned exactly once
  without a wrapper or schema change?

## In scope

- DAG eligibility; stage-owner fitness; final source/test placement; modes;
  scheduler delegation; private report/test-helper identities and depths;
  explicit caller maps; atomic cutover; permissible production edits;
  artifact identity/provenance; coverage row; Make/static inclusion;
  documentation ownership; and reverse rollback.

## Out of scope

- Reliability fault detail except where ownership obscures it; code changes;
  transaction repair; package/descriptor/schema design; bcftools,
  pileup/filter/selector, or scheduler policy; migrating Step `08`; and future
  units.

## Deliverables

- Evidence-ranked accept/revise/defer findings, an exact executable/test path
  ceiling, loader/test-helper plan, corresponding `MIG-03L` corrections, and a
  dated audit record.

## Acceptance evidence

- No unresolved DAG-choice, source/test/helper owner, dependency direction,
  path caller, mode, loader, wrapper, duplicate, artifact identity, coverage
  owner, atomicity, or rollback question.
- Every finding is incorporated into `MIG-03L` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03L`, roadmap/handoff only where current status changes, and
  the dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, permanent
  wrapper, helper movement/redesign, second owner, artifact/schema redesign,
  mode change, or a caller set that cannot fit one bounded stage-owner
  cutover.

## Completion record

Selected as the sole active migration review from clean, published,
local/upstream/live-remote-equal definition checkpoint
`8dc61287819d7ea10ca4bcc38934a0819161d24a`. No architecture finding is
recorded yet, no later review or migration card is selected, and no
executable/test file changed or ran.
