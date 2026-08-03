# REVIEW-ARCH-03H — Review RSeQC-paired-orientation evidence migration architecture

## Objective

Challenge `MIG-03H` for live-DAG choice, evidence-owner placement, exact caller
cutover, test ownership, artifact provenance, and reversible removal of all
three flat Step `03` native-asset paths.

## Why this exists

Two owners remain DAG-eligible, so selection must not be misrepresented as
unique or preload Step `04`. Historical Step `03` is a non-gating evidence
operation with two upstream artifact dependencies, one native report,
validation, artifact projection, demo targets, and a scheduler wrapper. Moving
it as a computational policy stage or changing artifact/evidence identity would
break the frozen topology.

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

- [REVIEW-REL-03H](REVIEW-REL-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Fully: reliability review requires an architecture-corrected owner, caller, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03H` against frozen parent `eafec29` without running or
  changing executable/test files.

## Required context

- `MIG-03H`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `03` evidence contract; producer,
  validator, job, and direct tests; public path maps; Make and literal fixture;
  neutral validation-report owner; artifact implementation mapping; coverage
  identity; and every proposed current/final path.

## Questions owned by this card

- Is Step `03` the smallest deterministic choice among the two currently
  eligible identities, with Step `04` remaining wholly uncreated and
  unselected?
- Is five moves plus nine updates the complete executable/test ceiling, and do
  artifact path/hash, demo targets, and direct/cross-owner tests remain assigned
  exactly once without a wrapper or compatibility path?

## In scope

- DAG eligibility and non-uniqueness; evidence-owner fitness; final source/test
  placement; job delegation; validation-report depth; owner-local versus cross-
  owner tests; explicit caller maps; wrapper necessity; atomic cutover;
  permissible production edits; artifact identity/provenance; coverage row;
  Make/static/demo inclusion; documentation ownership; and reverse rollback.

## Out of scope

- Reliability fault detail except where ownership obscures it; code changes;
  transaction repair; package/descriptor/schema design; evidence-policy or
  strandedness-classification design; migrating Step `04`; and future units.

## Deliverables

- Evidence-ranked accept/revise/defer findings, an exact executable/test path
  ceiling, and corresponding `MIG-03H` corrections recorded in the dated audit
  log.

## Acceptance evidence

- No unresolved DAG-choice, source/test owner, dependency direction, path
  caller, wrapper, duplicate, artifact identity, coverage owner, atomicity, or
  rollback question.
- Every finding is incorporated into `MIG-03H` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03H`, roadmap/handoff only where current status changes, and
  the dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, permanent
  wrapper, second owner, artifact/schema redesign, or a caller set that cannot
  fit one bounded evidence-owner cutover.

## Completion record

Selected from clean, published, local/upstream/live-remote-equal definition
checkpoint `0cd872e6a46f0b6310caf857bde5cd7fb1e8e086`. This is a read-only
independent-in-time adversarial pass by the same campaign agent; independent
authorship is not claimed. No executable/test mutation or computational test is
part of review selection.
