# REVIEW-ARCH-03N — Review paired-CMH analysis migration architecture

## Objective

Challenge `MIG-03N` for live-DAG choice, final analysis/test placement, exact
caller cutover, private neutral-report and flat-Step-`09c` loading, guarded-R
and independent-oracle ownership, artifact provenance, coverage ownership,
executable-mode continuity, and reversible removal of all four flat Step `09`
native paths.

## Why this exists

Step `09` is the only dependency-valid unmigrated owner, but it spans Bash, R,
Python, SLURM, a six-file transaction, and seven candidate protection assets.
Its validator ambient-imports shared Step `09` contracts from the still-flat
Step `09c` implementation, while the guarded-R runner, Python validator test,
independent oracle, and corpus depend on root test paths/imports. Relocation
must preserve those boundaries without migrating Step `09c`, creating a
package, changing global `sys.path`, installing R dependencies, duplicating
schemas, or leaving a compatibility owner.

## Fixed decisions

- Review only; corrections land in cards and current planning documentation,
  never executable/test source under this card.
- Apply the frozen semantic identity, direct DAG, analysis/test homes,
  dependency direction, and migration mechanics without reopening descriptors,
  orchestration, schemas, statistical policy, R method/dependencies, artifact
  policy, or Step `09c` ownership.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, package identity, ambient import paths, and any Step
  `09c` migration or later owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03N](REVIEW-REL-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Fully: reliability review requires an architecture-corrected owner, loader, caller, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03N` against frozen parent `57d7ea4` without running or
  changing executable/test files.

## Required context

- `MIG-03N`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `09` analysis contract; shell/R producer,
  validator, job, and seven candidate protection assets; public path maps;
  Make and literal fixture; guarded-R/local-R owners; neutral report owner/
  tests; flat Step `09c` shared contracts; artifact mapping and Step `09`
  reconciliation; coverage identity; manifests; and every proposed current/
  final path.

## Questions owned by this card

- Is Step `09` the only dependency-valid unmigrated identity after MIG-03M,
  with Step `09c` wholly uncreated and unselected as a migration unit?
- Are eleven candidate moves plus ten integration-owner updates complete,
  including the R runner/test, independent oracle/tool/corpus, local-R oracle,
  Make/static routes, and no hidden scaffold, import, schema, or compatibility
  owner?
- What exact final roots and private module identities preserve the neutral
  report loader, flat Step `09c` shared-contract dependency, root roster and
  fixture helpers, and cache/path/failure semantics without global `sys.path`
  mutation?
- Do native/test modes, projected hashes, Rscript-only behavior, exact final
  artifact producer path/hash, coverage row, atomic cutover, and reverse
  rollback remain assigned exactly once without a wrapper or schema change?

## In scope

- DAG eligibility; final source/test placement; eleven-move hypothesis; modes;
  Bash/R/Python/SLURM sibling relationships; private loader identities/depths;
  explicit caller/import maps; atomic cutover; permissible production edits;
  artifact identity/provenance; coverage row; guarded-R/oracle ownership;
  old/final path/hash evidence; and exact reverse rollback.

## Out of scope

- Executable/test mutation; reliability or usability execution; schema/helper
  extraction; public package/import identity; transaction, R method,
  statistical policy, dependency, scheduler, or artifact redesign; Step `09c`
  migration; and cluster/production work.

## Deliverables

- Finding-by-finding architecture disposition with exact corrections to
  `MIG-03N`, this review, and current status/audit owners.

## Acceptance evidence

- Every native/test asset, caller/import, Make/R/static route, artifact adapter,
  coverage row, and rollback edge has one old owner and one projected final
  owner. Exact searches support the fixed ceiling, and loader reasoning covers
  cache/path/spec/partial-initialization failures without changing public
  identity.

## Canonical documentation updates

- This card, `MIG-03N`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop for an unmovable caller/import, unavoidable Step `09c` move or public
  package, wrapper requirement, schema/artifact redesign, dependency action,
  or any boundary broader than one Step `09` owner and direct evidence wiring.

## Completion record

Selected alone from clean, published, local/upstream/live-remote-equal
definition checkpoint `8bb27d43a970551cc739f4deac25345b02c72042` for a
read-only architecture pass. MIG-03N, reliability, usability, Step `09c`, and
all executable/test files remain unselected and unchanged; no computational
test runs in this review.
