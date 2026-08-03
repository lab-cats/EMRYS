# REVIEW-ARCH-03J — Review SplitNCigarReads migration architecture

## Objective

Challenge `MIG-03J` for live-DAG choice, final stage/test placement, exact
caller cutover, private reference/report/BAM-helper loading, artifact
provenance, coverage ownership, and reversible removal of all three flat Step
`05` native-asset paths.

## Why this exists

Step `05` is the only currently eligible unmigrated owner. Its validator
currently receives `reference_provenance` through ambient `scripts/` import
resolution while privately exact-loading two neutral libraries. Relocation
must establish an exact private bridge to the unchanged public reference owner
without creating a package, `PYTHONPATH` dependency, wrapper, helper move, or
second functional-owner migration.

## Fixed decisions

- Review only; corrections land in cards and current planning documentation,
  never executable/test source under this card.
- Apply the frozen semantic identity, direct DAG, stage/test homes, dependency
  direction, and migration mechanics without reopening descriptors,
  orchestration, schemas, reference parsing, BAM helpers, or GATK policy.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, package identity, ambient import paths, and any Step
  `06` or later owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03J](REVIEW-REL-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Fully: reliability review requires an architecture-corrected owner, exact-loader, caller, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03J` against frozen parent `c6814e0` without running or
  changing executable/test files.

## Required context

- `MIG-03J`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `05` stage contract; producer, validator,
  job, and direct tests; public path maps; Make and literal fixture; neutral
  validation-report/BAM-helper owners; public reference-provenance owner and
  tests; artifact mapping; coverage identity; and every proposed current/final
  path.

## Questions owned by this card

- Is Step `05` the only dependency-valid unmigrated identity after `MIG-03I`,
  with Step `06` remaining wholly uncreated and unselected?
- What exact-file bridge preserves the unchanged public
  `scripts/reference_provenance.py` owner from the final validator depth, and
  what neutral report/BAM roots and moved-test roots are required?
- Is five moves plus ten updates the complete executable/test ceiling, or does
  the reference bridge require another explicit test owner/caller? Do artifact
  path/hash, coverage, Make/static, and rollback obligations remain assigned
  exactly once without a wrapper?

## In scope

- DAG eligibility; stage-owner fitness; final source/test placement; scheduler
  delegation; all three private-loader identities/depths; owner-local versus
  cross-owner tests; explicit caller maps; atomic cutover; permissible
  production edits; artifact identity/provenance; coverage row; Make/static
  inclusion; documentation ownership; and reverse rollback.

## Out of scope

- Reliability fault detail except where ownership obscures it; code changes;
  transaction repair; package/descriptor/schema/reference-helper design; GATK
  or scheduler policy; migrating Step `06`; and future units.

## Deliverables

- Evidence-ranked accept/revise/defer findings, an exact executable/test path
  ceiling and private-loader plan, corresponding `MIG-03J` corrections, and a
  dated audit record.

## Acceptance evidence

- No unresolved DAG-choice, source/test/helper owner, dependency direction,
  path caller, loader, wrapper, duplicate, artifact identity, coverage owner,
  atomicity, or rollback question.
- Every finding is incorporated into `MIG-03J` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03J`, roadmap/handoff only where current status changes, and
  the dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, permanent
  wrapper, helper movement/redesign, second owner, artifact/schema redesign,
  or a caller set that cannot fit one bounded stage-owner cutover.

## Completion record

Not selected. Defined with `MIG-03J` from clean, published, local/upstream/
live-remote-equal parent `c6814e0`; no executable/test file changed or ran.
