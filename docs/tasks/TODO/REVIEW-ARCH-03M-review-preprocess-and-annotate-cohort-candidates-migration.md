# REVIEW-ARCH-03M — Review cohort preprocessing migration architecture

## Objective

Challenge `MIG-03M` for live-DAG choice, final stage/test placement, exact
caller cutover, private neutral-report and flat-Step-`09c` loading, guarded-R
test ownership, artifact provenance, coverage ownership, executable-mode
continuity, and reversible removal of all four flat Step `08` native paths.

## Why this exists

Step `08` is the only dependency-valid unmigrated owner, but it spans Bash, R,
Python, SLURM, two output roots, and four direct protection assets. Its
validator ambient-imports shared Step `08` contracts from the still-flat Step
`09c` implementation, while the guarded-R runner and Python test depend on
root test paths/imports. Relocation must preserve those boundaries without
migrating Step `09c`, creating a package, changing global `sys.path`, installing
R dependencies, duplicating schemas, or leaving a compatibility owner.

## Fixed decisions

- Review only; corrections land in cards and current planning documentation,
  never executable/test source under this card.
- Apply the frozen semantic identity, direct DAG, stage/test homes, dependency
  direction, and migration mechanics without reopening descriptors,
  orchestration, schemas, provisional policy, R method/dependencies, artifact
  policy, or Step `09c` ownership.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, package identity, ambient import paths, and any Step
  `09` or later owner.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03M](REVIEW-REL-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Fully: reliability review requires an architecture-corrected owner, loader, caller, artifact, test, and rollback boundary.

## Prerequisites

- Review committed `MIG-03M` against frozen parent `4562ec3` without running or
  changing executable/test files.

## Required context

- `MIG-03M`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `08` stage contract; shell/R producer,
  validator, job, and four direct protection assets; public path maps; Make and
  literal fixture; guarded-R/local-R owners; neutral report owner/tests; flat
  Step `09c` shared contracts; artifact mapping and Step `08` reconciliation;
  coverage identity; manifests; and every proposed current/final path.

## Questions owned by this card

- Is Step `08` the only dependency-valid unmigrated identity after MIG-03L,
  with Step `09` and Step `09c` wholly uncreated and unselected?
- Are eight moves plus ten integration-owner updates complete, including the
  guarded-R runner/test, local-R oracle, Make/static routes, and no hidden
  scaffold, import, schema, or compatibility owner?
- What exact final roots and private module identities preserve the neutral
  report loader, flat Step `09c` shared-contract dependency, root roster helper,
  and cache/path/failure semantics without global `sys.path` mutation?
- Do native/test modes, projected hashes, Rscript-only behavior, exact final
  artifact producer path/hash, receipt-versus-summary marker interpretation,
  coverage row, atomic cutover, and reverse rollback remain assigned exactly
  once without a wrapper or schema change?

## In scope

- DAG eligibility; final source/test placement; eight-move hypothesis; modes;
  Bash/R/Python/SLURM sibling relationships; private loader identities/depths;
  explicit caller/import maps; atomic cutover; permissible production edits;
  artifact identity/provenance; coverage row; guarded-R ownership; old/final
  path/hash evidence; and exact reverse rollback.

## Out of scope

- Executable/test mutation; reliability or usability execution; schema/helper
  extraction; public package/import identity; transaction, R method, policy,
  dependency, scheduler, or artifact redesign; Step `09`/`09c` migration; and
  cluster/production work.

## Deliverables

- Finding-by-finding architecture disposition with exact corrections to
  `MIG-03M`, this review, and current status/audit owners.

## Acceptance evidence

- Every native/test asset, caller/import, Make/R/static route, artifact adapter,
  coverage row, and rollback edge has one old owner and one projected final
  owner. Exact searches support the fixed ceiling, and loader reasoning covers
  cache/path/spec/partial-initialization failures without changing public
  identity.

## Canonical documentation updates

- This card, `MIG-03M`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop for an unmovable caller/import, unavoidable Step `09c` move or public
  package, wrapper requirement, schema/artifact redesign, dependency action,
  or any boundary broader than one Step `08` owner and direct evidence wiring.

## Completion record

Not selected. Defined from clean, published MIG-03L close `4562ec3`; no
executable/test file changed or ran.
