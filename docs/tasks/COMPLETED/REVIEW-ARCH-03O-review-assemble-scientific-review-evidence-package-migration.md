# REVIEW-ARCH-03O — Review scientific-review package migration architecture

## Objective

Challenge `MIG-03O` for live-DAG choice, final evidence/test/support-asset
placement, exact import/caller cutover, migrated Step `08`/`09` private loading,
artifact/run-summary/report ownership, coverage continuity, and reversible
removal of the flat Step `09c` implementation paths.

## Why this exists

Step `09c` is the only dependency-valid unmigrated functional owner, but its
4,533-line Python implementation is also imported by migrated validators and
flat artifact/run-summary code. Its public examples and thirteen evidence
schema TSVs may be evidence-local assets or separately retained configuration
surfaces. Relocation must assign every asset and consumer once without a
package, ambient import path, compatibility owner, schema change, or future-
package preload.

## Fixed decisions

- Review only; corrections land in cards and current planning documentation,
  never executable/test/configuration source under this card.
- Apply the frozen semantic identity, direct DAG, evidence/test homes,
  dependency direction, and migration mechanics without reopening descriptor,
  schema, scientific-state, artifact, report, or transaction policy.
- Reject speculative wrappers, aliases, symlinks, compatibility copies,
  recursive discovery, installed/public package identity, ambient
  `PYTHONPATH`, global `sys.path` mutation, and any later owner or audit preload.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-REL-03O](REVIEW-REL-03O-review-assemble-scientific-review-evidence-package-migration.md) — Fully: completed reliability review consumed this architecture-corrected owner, asset, loader, consumer, artifact, coverage, and rollback boundary.

## Prerequisites

- Review committed `MIG-03O` against frozen parent `68fd2a9` without running or
  changing executable/test/configuration files.

## Required context

- `MIG-03O`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the Step `09c` evidence contract; Python/shell
  implementation; candidate direct tests/fixture and example/schema assets;
  migrated Step `08`/`09` private loaders; artifact/run-summary imports and
  fixtures; report consumers; independent goldens; public CLI/Make literal
  maps; coverage identity; and every proposed current/final path.

## Questions owned by this card

- Is Step `09c` the only dependency-valid unmigrated owner and the last unit in
  the frozen functional-owner target topology?
- Which native, test, fixture, example, and evidence-schema assets move, which
  remain under a justified owner, and what are the exact move and integration-
  owner ceilings?
- What exact final roots and private module identities preserve migrated Step
  `08`/`09`, artifact, run-summary, fixture, and independent-golden consumers,
  including initialization/cache/path/failure behavior, without a public
  package or global search-path mutation?
- Do modes, projected hashes, direct/explicit-interpreter behavior, artifact
  producer identity, coverage row, atomic cutover, and reverse rollback remain
  assigned exactly once without a wrapper or schema change?

## In scope

- DAG eligibility; final source/test/support placement; modes/hashes; Python/
  shell sibling relationship; exact imports/callers; private-loader identities;
  permissible path edits; atomic cutover; artifact/run-summary/report
  provenance; coverage row; old/final evidence; and exact reverse rollback.

## Out of scope

- Executable/test/configuration mutation; reliability or usability execution;
  schema/state/helper extraction; public package identity; transaction,
  scientific-review, artifact, or report redesign; dependency action;
  scheduler/cluster/production work; and future packages.

## Deliverables

- Finding-by-finding architecture disposition with exact corrections to
  `MIG-03O`, this review, and current status/audit owners.

## Acceptance evidence

- Every native/test/support asset, import/caller, Make/public route, artifact/
  run-summary/report consumer, coverage row, and rollback edge has one old
  owner and one projected final owner. Exact searches support the fixed ceiling
  and loader reasoning covers initialization/cache/path/spec/partial failures
  without changing public identity.

## Canonical documentation updates

- This card, `MIG-03O`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop for an unmovable import/caller, unavoidable public package or permanent
  wrapper, schema/artifact/report redesign, dependency action, or any boundary
  broader than one Step `09c` owner and its direct wiring.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `a46f94bd1b22831ec9407594a14d0a58c800b7a0`.

- **Accepted DAG and owner boundary:** migrated Step `08` supplies its complete
  three-output transaction and migrated Step `09` supplies its complete six-
  output transaction, so `assemble_scientific_review_evidence_package` is the
  sole dependency-valid unmigrated functional owner and the last unit in the
  frozen fourteen-owner topology. No later owner or final-audit package is
  selected or preloaded.
- **Accepted five-move boundary:** move exactly the Python implementation,
  sibling shell launcher, direct Python test, direct shell test, and Step `09c`
  fixture builder to the frozen evidence/test homes. The final source home
  contains only `CONTRACT.md` and the final test home is absent; neither is a
  competing implementation or test scaffold. Preserve all five basenames and
  modes.
- **Retained public configuration boundary:** keep both example TSVs and all
  thirteen evidence-schema TSVs byte-identical at their existing `configs/`
  paths. They are explicit operator configuration/reference inputs, not native
  implementation assets; production does not resolve them at runtime, the
  direct owner test is their only executable consumer, and documentation will
  continue to route them at close. Moving them would change fifteen public
  paths without an implementation-owner requirement.
- **Accepted fourteen-integration ceiling:** update exactly `Makefile`,
  `scripts/build_artifact_index.py`, `scripts/_run_summary_science.py`, both
  migrated Step `08`/`09` validators and their tests, the artifact-run-summary
  fixture builder, artifact-adapter and artifact-run-summary tests, public CLI
  contracts, independent contract goldens, the coverage baseline, and the
  literal Make-expansion fixture. Exact path/basename/import searches find no
  fifteenth integration owner. Artifact/run-summary fixtures and schema tests
  that consume unchanged semantic identities remain otherwise unchanged.
- **Accepted projected moved bytes:** final Python is unchanged at mode/bytes/
  lines/hash `0644` / `159,620` / `4,533` /
  `7b6b48b71c07249cb791ceb818bd4aef5c30015724cb2406127159815c1e09f8`.
  The shell changes only its displayed usage path and projects to `0755` /
  `5,458` / `200` /
  `275b4598bac35a794b746973aa667cfe4b91ed14b4833635a8f24a4560ff2037`.
  Path-only test corrections project the Python test to `0644` / `37,326` /
  `1,206` / `4e6da67232873679fc0844982e70602f9a43c68eeaedc71a477bd59fe523e118`,
  shell test to `0755` / `5,668` / `170` /
  `fe2c6637e2eb3da167725d4c6a9682695088159e47029b53067c7183f241ec0c`,
  and fixture builder to `0644` / `55,129` / `1,532` /
  `a4df19f681956934244331688260ae6074e378cbca08426edfb83bccee74ac4f`.
- **Accepted private-loader boundary:** migrated Step `08`/`09`, artifact
  indexing, and run-summary science normalization share private identity
  `_norad_step_09c_scientific_validation_contracts`, final exact-file path,
  cached-file and readiness checks, insertion before dataclass execution,
  owned partial-cache cleanup, sanitized one-line exit `2`, and unchanged
  `sys.path`. The two migrated validators resolve the repository through
  `parents[4]`; both flat artifact/run-summary consumers use `parents[1]`.
  Independent goldens consume the artifact loader's exact private module while
  retaining the historical golden key; no public import or installed package
  identity is introduced.
- **Accepted test and public-path boundary:** the moved Python test uses
  `parents[3]`, final production paths, and its final sibling fixture; the moved
  shell test uses three parent segments and final source/test paths. The moved
  fixture retains `parents[3]` and changes only the contract path. The Step
  `09` validator test and artifact-run-summary fixture point to the final
  fixture. Make, public CLI maps, and literal expansion use only final paths.
- **Accepted artifact and coverage boundary:** `STEP_PRODUCERS["09c"]` becomes
  only the final Python path with unchanged producer hash `7b6b48b...e09f8`,
  and the artifact test binds that exact identity. The 32-row frozen coverage
  snapshot moves the target row while retaining at least `1,262/1,534` lines
  and `561/788` branches. New loader code in artifact indexing and run-summary
  science must retain at least their frozen rates (`0.798522`/`0.709446` and
  `0.779614`/`0.631250` line/branch respectively); the other 29 rows remain
  exact and global ratios remain at least `9601/11758` lines and `3367/4784`
  branches.
- **Accepted atomicity and rollback boundary:** after only reliability-reviewed
  test baselines, apply five moves and fourteen integrations as one cutover so
  old and final implementation/test paths never coexist. A wrapper, alias,
  symlink, compatibility copy, package marker, descriptor, or schema move is
  not justified. Roll back documentation first, then the atomic cutover, then
  any test-only checkpoints in reverse order; Git rollback never changes
  runtime outputs, locks, backups, evidence, or review state.
- **Preserved risk boundary:** architecture does not bless or repair visible-
  summary-before-final-checks, incomplete restoration with retained lock/
  backup, missing sibling hashes, admitted-input mutation gaps, producer-
  recorded relative-path sensitivity, provisional scientific state, or any
  artifact/run-summary/report evidence ceiling. Reliability must characterize
  the high-risk gaps without redesigning transaction, schema, state, or
  recovery behavior.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. Temporary
  copies were used only to project path-only bytes. No repository executable,
  test, configuration, dependency, runtime, scheduler, cluster, production,
  scientific-review, or biological state changed or ran.
- **Card-boundary gate:** `git diff --check` passes and the exact RUNBOOK
  documentation validator reports `PASS documentation structure (213 Markdown
  documents, 133 task cards, 6 Mermaid sources)`. No architecture-review path,
  lifecycle, dependency, cycle, orphan, schema, anchor, or diagram finding
  remains.
