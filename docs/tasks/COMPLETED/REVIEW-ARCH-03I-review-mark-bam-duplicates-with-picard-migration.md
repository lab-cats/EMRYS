# REVIEW-ARCH-03I — Review MarkDuplicates migration architecture

## Objective

Challenge `MIG-03I` for live-DAG choice, stage-owner placement, exact caller
cutover, neutral-helper and test ownership, artifact provenance, and reversible
removal of all three flat Step `04` native-asset paths.

## Why this exists

Step `04` is the only currently eligible unmigrated owner, but it couples a
three-output producer, two neutral private libraries, artifact projection,
central helper tests, and a scheduler wrapper. Moving its BAM helpers into the
stage, changing artifact identity, or preloading Step `05` would violate the
frozen topology and migration boundary.

## Fixed decisions

- Review only; corrections land in cards and planning documentation, never in
  executable/test source under this card.
- Apply the frozen stage identity, direct DAG, target stage/test homes,
  dependency direction, and migration mechanics without reopening descriptors,
  orchestration, artifact schemas, BAM-helper API, or duplicate-marking policy.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, package identity, and another functional-owner move.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03I](../IN_PROGRESS/REVIEW-REL-03I-review-mark-bam-duplicates-with-picard-migration.md) — Fully: reliability review requires an architecture-corrected owner, caller, helper, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03I` against frozen parent `ef990c8` without running or
  changing executable/test files.

## Required context

- `MIG-03I`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `04` stage contract; producer, validator,
  job, and direct tests; public path maps; Make and literal fixture; neutral
  validation-report and BAM-helper owners/tests; artifact implementation
  mapping; coverage identity; and every proposed current/final path.

## Questions owned by this card

- Is Step `04` the only dependency-valid unmigrated identity after `MIG-03H`,
  with Step `05` remaining wholly uncreated and unselected?
- Is five moves plus ten updates the complete executable/test ceiling, including
  the central BAM-helper caller matrix, and do artifact path/hash and direct/
  cross-owner tests remain assigned exactly once without a wrapper?

## In scope

- DAG eligibility; stage-owner fitness; final source/test placement; job
  delegation; both neutral-library depths; owner-local versus cross-owner
  tests; explicit caller maps; wrapper necessity; atomic cutover; permissible
  production edits; artifact identity/provenance; coverage row; Make/static
  inclusion; documentation ownership; and reverse rollback.

## Out of scope

- Reliability fault detail except where ownership obscures it; code changes;
  transaction repair; package/descriptor/schema design; duplicate-marking or
  scheduler policy; migrating Step `05`; and future units.

## Deliverables

- Evidence-ranked accept/revise/defer findings, an exact executable/test path
  ceiling, and corresponding `MIG-03I` corrections recorded in the dated audit
  log.

## Acceptance evidence

- No unresolved DAG-choice, source/test/helper owner, dependency direction,
  path caller, wrapper, duplicate, artifact identity, coverage owner,
  atomicity, or rollback question.
- Every finding is incorporated into `MIG-03I` or retained with a consequence
  and recheck trigger.

## Canonical documentation updates

- This card, `MIG-03I`, roadmap/handoff only where current status changes, and
  the dated refactor log.

## Escalation conditions

- Stop if final placement requires a public package/import runtime, permanent
  wrapper, second owner, artifact/schema/helper redesign, or a caller set that
  cannot fit one bounded stage-owner cutover.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `d277bc383382b30bf3d51fe0a7e721a3f3aa1636`.

- **High — moved-test and dual-loader depths needed an explicit boundary:**
  freeze only the producer usage path, both validator neutral-library roots at
  `parents[4]`, scheduler child path, shell-test root `SCRIPT_DIR/../../..`, and
  Python-test root `parents[3]`. The moved Python test must exact-load the
  unchanged root roster oracle by repository path; package creation or
  `PYTHONPATH` mutation is rejected. Any other moved-file edit reopens review.
- **High — exact cutover ceiling confirmed:** one atomic direct cutover is five
  moves plus ten updates: Make, artifact producer, artifact assertion, public
  CLI, SLURM, validation roster, validation-report map, neutral BAM-helper
  caller matrix, coverage row, and literal Make fixture. Both final shell
  assets become exact static/smoke inputs; Step `04` has no Make demo target.
  An eleventh update or sixth move reopens this review.
- **Medium — helper, test, artifact, and documentation ownership confirmed:**
  the validator retains private exact loads of both neutral libraries; neither
  helper moves or changes API. Direct shell/validator suites move with the
  stage, while all ten central files remain cross-owner consumers. Artifact
  evidence changes only Step `04` implementation path and projected producer
  hash `b845aa910ccabaf8799e000dc62e8939b0203c7848511524fadf51c79292eb2d`;
  evidence ID, four artifact identities, schemas, contents, ordering, meaning,
  and consumers stay fixed. Documentation close also repairs the impacted
  canonical-BAM owner README; diagrams are conditional on a material flow
  change, which relocation does not propose.
- **Accepted architecture and rollback:** Step `04` is uniquely eligible after
  `MIG-03H`; Step `05` remains blocked and uncreated. Every known executable
  caller is repository-owned and fits the atomic cutover, so no wrapper,
  duplicate, package, descriptor, schema, alias, symlink, helper extraction, or
  second owner is warranted. Roll back documentation, then owner/caller/helper-
  matrix/coverage cutover, then any reliability test baseline; keep Make/oracle
  and artifact path/hash/assertion changes together.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. That expected-only result is not a green gate; no architecture-
  review-caused finding remains.
