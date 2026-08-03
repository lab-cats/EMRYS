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

- [REVIEW-REL-03N](../TODO/REVIEW-REL-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Fully: reliability review requires this completed architecture-corrected owner, loader, caller, artifact, test, and rollback boundary.

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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `cf6deb8f3a53634b0a0870f69cd82edf9c73ac0e`.

- **Accepted DAG and owner boundary:** migrated Step `08` supplies the required
  sites table and input receipt, so `rank_cohort_candidates_with_paired_CMH`
  is the sole dependency-valid unmigrated owner. Step `09c` remains blocked on
  the complete Step `09` transaction and is neither selected nor moved.
- **Accepted eleven-move boundary:** move exactly four native assets and seven
  Step `09`-specific protection assets. The final source directory currently
  contains only its contract and the final test directory is absent; neither
  is a competing scaffold. The guarded-R runner/test, independent Python
  oracle/test, and corpus belong together because their direct consumers are
  Step `09`-specific. Preserve all eleven basenames and modes.
- **Accepted ten-integration ceiling:** update exactly Make, artifact producer
  mapping/evidence, public CLI, SLURM contracts, validation roster, neutral
  report-loader matrix, guarded local-R oracle, coverage baseline, and literal
  Make expansion. Exact path/basename/import/R/job/test searches find no
  eleventh integration owner. `tests/test_report_exports_v1.py` remains an
  unchanged negative rendered-report assertion, and Step `09c`/run-summary
  imports remain consumers of the still-flat Step `09c` owner.
- **Accepted production edits and hashes:** change only shell/R usage text,
  validator root/Step-`09c` loading, and job R/child defaults. Final shell is
  mode/bytes/lines/hash `0755` / `58,279` / `1,331` /
  `7926d13bd9f0192522a20224c24716b7b8dca7a1348803cb7e8aefa1b056123a`;
  R is `0644` / `48,993` / `1,205` /
  `f429fa71d91794f0a5f3bf4c77c7ce1981cbf5ebe98ea1ab50302dda2b18d1dc`;
  validator is `0644` / `18,201` / `487` /
  `ab14263de43d624f39490e080ead040309d9584d6bf08f101346192a8758763a`;
  and job is `0755` / `4,387` / `121` /
  `d84cfbd9afe3822b7abe8e1e5a249444801030387c77c46a29ca61cd97dcc677`.
- **Accepted private-loader boundary:** both neutral report and flat Step `09c`
  paths resolve from `parents[4]`. Preserve the neutral bridge. Replace only
  the ambient Step `09c` import with private identity
  `_norad_step_09c_scientific_validation_contracts`, exact cached-file and
  readiness checks, insertion before dataclass execution, owned partial-cache
  cleanup, sanitized exit `2`, and no public module or `sys.path` change.
- **Accepted test/path boundary:** moved shell and R-runner tests resolve the
  repository through three parent segments; the R test targets final code and
  owner-local corpus. The validator test uses `parents[3]`, exact-loads the
  root roster and existing Step `09c` fixture privately, and targets final
  code. The oracle test uses `parents[3]` with sibling oracle/corpus paths.
  Central scheduler, local-R, neutral-report, public-CLI, artifact, roster,
  coverage, and Make-literal tests remain central.
- **Accepted artifact, coverage, and atomicity boundary:**
  `STEP_PRODUCERS["09"]` becomes only the final shell path with frozen hash
  `7926d13...6123a`; the artifact test asserts that exact identity without
  changing native/report semantics. Move the coverage row from the flat
  validator path while retaining target rates at or above `154/158` lines and
  `34/40` branches, every non-target row exact, and global floors
  `9601/11758` lines and `3367/4784` branches. Apply eleven moves plus ten
  integrations atomically; old/final code and tests never coexist.
- **Accepted rollback and escalation boundary:** reverse documentation close,
  then the atomic cutover, then reviewed test-only checkpoints. No wrapper,
  alias, symlink, compatibility copy, package, descriptor, schema, Step `09c`
  extraction, dependency action, or later-owner preload is justified. Any
  hash/mode/count/caller variance reopens architecture review.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. Temporary
  copies were used only to project path-only bytes. No repository executable,
  test, harness, dependency, R runtime/package, scheduler, cluster, production,
  scientific-review, or biological state changed or ran.
- **Card-boundary gate:** `git diff --check` passes and the exact RUNBOOK
  documentation validator reports `PASS documentation structure (208 Markdown
  documents, 129 task cards, 6 Mermaid sources)`. No architecture-review path,
  lifecycle, dependency, cycle, orphan, schema, anchor, or diagram finding
  remains.
