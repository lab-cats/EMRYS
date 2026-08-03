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

- [REVIEW-REL-03J](../TODO/REVIEW-REL-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Fully: reliability review requires an architecture-corrected owner, exact-loader, caller, artifact, test, and rollback boundary.

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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `032e4fb72998d479001a21561207fba2d327b386`.

- **High — ambient reference import and moved-test discovery needed explicit
  owners:** replace only Step `05`'s ambient import with the proven Step-`00c`
  private exact-file bridge to unchanged public
  `scripts/reference_provenance.py`. Reuse module identity
  `_norad_reference_provenance`; validate exact file, exception type, and all
  three parser callables; preserve foreign/incomplete caches; remove only an
  owned failed partial; and make no `sys.path` change. Keep report/BAM paths on
  repository-root `parents[4]`. The moved Python test uses root `parents[3]`,
  privately exact-loads the unchanged root roster oracle, and owns reference-
  bridge consumer tests. The public reference owner/test does not change.
- **High — exact cutover ceiling confirmed:** one atomic direct cutover is five
  moves plus ten updates: Make, artifact producer mapping, artifact path/hash
  assertion, public CLI, SLURM, validation roster, validation-report map,
  neutral BAM-helper caller/cache matrix, coverage row, and literal Make
  fixture. The moved shell test uses `SCRIPT_DIR/../../..` and final producer/
  job paths. Both final shell assets become explicit static/smoke inputs. An
  eleventh update, sixth move, or different moved-file edit reopens review.
- **Medium — projected native and artifact evidence frozen:** final producer
  is `18,920` bytes / `596` lines /
  `e25c8d94d940aa02187e5550c51a71b8fdd8ca75660a07f5851dc215679248ac`;
  validator `12,584` / `334` /
  `f1a1128510de0c4e2b40800185c6cc039c7bb4ed5bf158396d87ee5d0730cdf3`;
  and job `5,383` / `167` /
  `3931b0976a9c97438b5980706a86203eb49ed472390a5a2f201830ae7ccfa147`.
  All remain mode `0644`. Step `05` artifact evidence changes only to the final
  producer path and first hash; evidence ID, three artifact identities,
  schemas, contents, ordering, reconciliation, consumers, and meaning stay
  fixed. Coverage renames the validator row while preserving target rates,
  every non-target row, and global covered-count floors.
- **Accepted architecture and rollback:** the live DAG leaves only Step `05`
  eligible after both direct predecessors migrated; Step `06` remains blocked,
  uncreated, and unselected. All supported callers are repository-owned and
  fit one direct cutover, so no wrapper, alias, duplicate, package, descriptor,
  schema, helper move, or second owner is justified. Roll back documentation,
  then the five-move/ten-update cutover with Make/oracle and artifact path/hash/
  assertion together, then any reliability baselines in reverse order.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. That expected-only result is not green; no architecture-
  review-caused finding remains.
