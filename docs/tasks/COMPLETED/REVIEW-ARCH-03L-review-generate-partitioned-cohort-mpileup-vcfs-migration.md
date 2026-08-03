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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `e34edb55e93b9874830fcc66688e5ac3b0d3f9dd`.

- **High — exact cutover ceiling accepted:** move exactly the producer,
  validator, mode-`0644` job, direct shell test, and direct validator test to
  the frozen stage/test homes. Update exactly nine integration owners: Make,
  artifact producer mapping and final path/hash evidence, public CLI, SLURM,
  validation roster, neutral report-loader matrix, coverage baseline, and the
  literal Make expansion. Searches prove no tenth integration owner. The
  three root Step `07` partition manifests remain shared operator inputs and
  the adjacent contract remains documentation; neither is a sixth move. No
  Step `07` pending scaffold exists.
- **High — permissible production edits and hashes fixed:** only the producer
  usage path, validator `parents[1]` to `parents[4]` report-root depth, and
  scheduler child path change bytes. Projected final producer is mode `0755`,
  `31,526` bytes, `893` lines, SHA-256
  `e3af9900b6f7831f2feafbc6d13f3755a475f02e5013c8b756107ddd90d22297`;
  validator is mode `0644`, `13,524` bytes, `334` lines,
  `3191a379a4c2e1d589eeb3f327314d91dcb70f5e79da6e2b4f344ffb2b68763b`;
  and job is mode `0644`, `4,421` bytes, `133` lines,
  `fbd8144a362cdd688ac14efcd8c003a3527b878d90ab525277a92018ac9a1ed6`.
  Any difference reopens this review.
- **High — private helper ownership accepted:** the validator keeps its
  unchanged exact-file neutral report identity and readiness/path/cache
  behavior. The moved shell test uses `SCRIPT_DIR/../../..` and final producer/
  job targets. The moved Python test uses `parents[3]`, final validator path,
  and an exact-file bridge to unchanged root
  `tests/validation_roster_expectations.py` under private identity
  `generate_partitioned_cohort_mpileup_vcfs_validation_roster_oracle`, binding
  only `assert_exact_check_roster` without `sys.path` or module-cache mutation.
  No production helper, package import, or second test owner is needed.
- **High — artifact and coverage assignment accepted:**
  `STEP_PRODUCERS["07"]` changes only to the final producer path and projected
  hash; the existing migrated-implementation evidence test gains the exact
  Step `07` assertion. VCF/receipt/report identities, schemas, dependency
  ordering, completion-marker interpretation, and scientific meaning do not
  change. The coverage row moves to the final validator path while retaining
  `167/198` lines, `48/72` branches, non-target exactness, and global covered-
  count floors.
- **Medium — Make/static and documentation boundaries accepted:** exact final
  producer/job paths replace flat wildcards; direct test recipes move; central
  maps remain explicit. Contract, inventory, topology status, test baseline,
  documentation ownership, runbook/troubleshooting, artifact provenance,
  current roadmap/handoff, lifecycle links, and the adjacent README change
  only in the later batched migration documentation close. No diagram change
  is expected because semantic identities, direct DAG edges, and public flow
  remain unchanged.
- **Accepted atomicity and rollback:** old and final executable/test paths may
  not coexist. Apply the five moves and nine integrations atomically after
  reviewed reliability baselines. Roll back documentation first, then the
  five-move/nine-update cutover, then any test-only reliability checkpoints in
  reverse order. Git rollback never authenticates or changes runtime VCF,
  receipt, lock, scratch, backup, log, or recovery evidence. No wrapper, alias,
  symlink, compatibility copy, package marker, descriptor, schema, or future-
  owner preload is justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, real bcftools, scheduler, production, scientific-
  review, variant/editing-site, or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No review path, lifecycle, dependency, cycle, orphan,
  anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not green and not authority to alter inherited lifecycle state.
