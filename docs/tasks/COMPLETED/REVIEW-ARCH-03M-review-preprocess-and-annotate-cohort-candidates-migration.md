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

- [REVIEW-REL-03M](REVIEW-REL-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Fully: reliability review completed against the architecture-corrected owner, loader, caller, artifact, test, and rollback boundary.

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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `a0d1af9422d47a22a6aa308b750e53e4c8506a1f`.

- **High — live-DAG and eight-move ceiling accepted:** Step `08` is the sole
  eligible unmigrated owner. Move exactly the shell, R implementation,
  validator, mode-`0644` job, shell test, guarded-R runner, R test, and
  validator test to the frozen stage/test homes. The runner is owner-specific;
  Make and the local-R environment oracle remain central. No Step `08` pending
  scaffold, config move, wrapper, duplicate test owner, or Step `09`/`09c`
  preload exists or is justified.
- **High — ten integration owners accepted:** update exactly Make, artifact
  producer mapping and final path/hash evidence, public Python/shell/R CLI
  maps, SLURM path/delegation, validation roster, neutral report-loader matrix,
  local-R expected path, coverage baseline, and literal Make expansion. Exact
  tracked-path, basename, import, Make, job, artifact, and test searches prove
  no eleventh integration owner. Documentation/contract paths remain for the
  later close and are not executable integrations.
- **High — dependency direction and private loaders accepted:** shell and R
  stay sibling assets. The moved validator changes neutral-report root only to
  `parents[4]` and exact-loads still-flat
  `scripts/step_09c_scientific_validation.py` under private identity
  `_norad_step_09c_scientific_validation_contracts`. It inserts that identity
  before execution for dataclass safety, validates cached path/readiness,
  removes its own partial cache entry, and emits sanitized exit-`2` failure.
  The moved Python test uses `parents[3]` and private exact-file loaders for the
  root roster helper and Step `09c`; it adds no ambient path or public import.
  No shared schema/helper, Step `09c` implementation, or public API moves.
- **High — exact production bytes fixed:** only shell/R usage paths,
  validator root/private-loader bytes, and job R/child paths change. Projected
  final shell is mode `0755`, `39,954` bytes / `1,024` lines /
  `578542fefa02aa23667bb40e582cbab215e6d3efec0a7c2fbb002290f1cfc1f3`;
  R program mode `0644`, `69,505` / `1,939` /
  `50cae0523ea68f87535866cbe9e86d38c3812f96a2c8a06ebd66a72177268699`;
  validator mode `0644`, `12,918` / `346` /
  `57a227c478c0caec60fe2ff8d84f7feb1fce28c5248338f1369b2a186284c78f`;
  and job mode `0644`, `4,597` / `134` /
  `e51d0df86609ca5d3d39b60f6036ee225bc17c11b6a83d68c683603842c57de6`.
  Any production difference reopens this review.
- **High — test, R, artifact, and coverage ownership accepted:** shell and
  guarded-R tests use `../../..`; R test stays repository-CWD-bound and targets
  final R; Python test uses `parents[3]`. Public CLI gains one explicit R path
  map so flat and final R entry points remain exact. `STEP_PRODUCERS["08"]`
  changes only to final shell path/hash above; native input receipt and artifact
  `step08_summary_v1` failure-marker interpretations remain distinct and
  unchanged. The coverage row moves from the flat validator at starting
  `122/129` lines and `26/36` branches while final loader tests must preserve
  target rates, every non-target row, and global covered-count floors.
- **Medium — Make/static/documentation boundary accepted:** direct shell,
  validator, and guarded-R recipes move; exact final shell/job paths enter
  static/smoke after leaving flat wildcards; the local-R oracle changes only
  its expected Step `08` test path. Contract, inventory, topology status,
  baseline, ownership, runbook/troubleshooting, artifact provenance, roadmap/
  handoff, lifecycle links, and adjacent README wait for the separate migration
  documentation close. No diagram change is expected because identity, DAG,
  and public flow are unchanged.
- **Accepted atomicity and rollback:** old and final paths may not coexist.
  Apply eight moves plus ten integrations atomically after reliability test-
  only baselines. Roll back documentation first, then the atomic cutover, then
  test-only checkpoints in reverse order. Git rollback does not recover or
  alter output/QC transactions, locks, backups, logs, R state, or evidence. No
  alias, symlink, compatibility copy, descriptor, schema, dependency action, or
  future owner is justified.
- **Evidence boundary:** this was a committed-time read-only review by the same
  campaign agent; independent authorship is not claimed. No executable, test,
  harness, R dependency, scheduler, cluster, production, scientific-review,
  provisional-policy, or biological state changed or ran.
- **Card-boundary gate:** `git diff --check` passes and the exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings. No review path, lifecycle, dependency, cycle, orphan,
  anchor, or diagram finding remains. This expected-only result is nonpassing,
  not green and not authority to alter inherited lifecycle state.
