# REVIEW-ARCH-03G — Review canonical-BAM-QC evidence migration architecture

## Objective

Challenge `MIG-03G` for live-DAG choice, evidence-owner placement, exact caller
cutover, test ownership, artifact provenance, and reversible removal of all
three flat Step `02b` native-asset paths.

## Why this exists

Three owners are now DAG-eligible, so selection must not be misrepresented as
unique or preload the other two. Historical Step `02b` is a non-gating evidence
operation with direct native outputs, validation, artifact projection, and a
scheduler wrapper. Moving it as if it were a computational stage, or changing
artifact/evidence identity merely because its source path changes, would break
the frozen topology.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen evidence identity, direct DAG, target evidence/test homes,
  dependency direction, and migration mechanics without reopening descriptors,
  orchestration, artifact schemas, or evidence policy.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, package identity, and another functional-owner move.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03G](REVIEW-REL-03G-review-collect-canonical-bam-qc-evidence-migration.md) — Fully: reliability review requires an architecture-corrected owner, caller, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03G` against frozen parent `543eb8f` without running or
  changing executable/test files.

## Required context

- `MIG-03G`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `02b` evidence contract; producer,
  validator, job, and direct tests; public path maps; Make and literal fixture;
  neutral validation-report owner; artifact implementation mapping; coverage
  identity; and every proposed current/final path.

## Questions owned by this card

- Is Step `02b` the smallest deterministic choice among the three currently
  eligible identities, with the other two remaining wholly uncreated and
  unselected?
- Is five moves plus nine updates the complete executable/test ceiling, and do
  artifact path/hash and direct/cross-owner tests remain assigned to exactly one
  owner without a wrapper or compatibility path?

## In scope

- DAG eligibility and non-uniqueness; evidence-owner fitness; final source/test
  placement; job delegation; validation-report depth; owner-local versus cross-
  owner tests; explicit caller maps; wrapper necessity; atomic cutover;
  permissible production edits; artifact identity/provenance; coverage row;
  Make/static inclusion; documentation ownership; and reverse-order rollback.

## Out of scope

- Reliability fault detail except where ownership obscures it; code changes;
  transaction repair; package/descriptor/schema design; evidence-policy
  redesign; migrating Step `03`, Step `04`, or another owner; and future units.

## Deliverables

- Evidence-ranked accept/revise/defer findings, an exact executable/test path
  ceiling, and corresponding `MIG-03G` corrections recorded in the dated audit
  log.

## Acceptance evidence

- No unresolved DAG-choice, source/test owner, dependency direction, path
  caller, wrapper, duplicate, artifact identity, coverage owner, atomicity, or
  rollback question.
- Every finding is incorporated into `MIG-03G` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03G`, roadmap/handoff only where current status changes, and
  the dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, permanent
  wrapper, second owner, artifact/schema redesign, or a caller set that cannot
  fit one bounded evidence-owner cutover.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
