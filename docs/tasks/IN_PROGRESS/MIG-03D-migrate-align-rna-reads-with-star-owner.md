# MIG-03D — Migrate the align-RNA-reads-with-STAR owner

## Objective

Move the complete `align_RNA_reads_with_STAR` producer, validator, scheduler
asset, and owner-local tests to their frozen final homes while preserving
current public, scheduler, validation, artifact, coverage, and alignment
contracts.

## Why this exists

After `MIG-03C`, both `align_RNA_reads_with_STAR` and
`construct_FASTA_sidecars` are dependency-valid. Select
`align_RNA_reads_with_STAR`: its sole hard DAG predecessor,
`construct_STAR_index`, is already migrated; its three native assets are the
smaller live surface; and its validator depends only on the already migrated
neutral validation-report library. The FASTA-sidecar validator still imports
the separate flat `reference_provenance` implementation. This selection follows
the semantic DAG and live coupling, not historical alias order.

## Fixed decisions

- Frozen parent and rollback target:
  `f9d638199c6d60cbe81c992fde6a1090cb364302`, the clean, published,
  local/upstream-equal `MIG-03C` documentation close on the one active campaign
  branch.
- Semantic identity is `align_RNA_reads_with_STAR`, machine key
  `norad.stage.align_RNA_reads_with_STAR.v1`, historical alias `01`, with final
  source home `src/norad/stages/align_RNA_reads_with_STAR/` and mirrored test
  home `tests/stages/align_RNA_reads_with_STAR/`.
- Move the mode-`0755` shell producer `scripts/step_01_star_align.sh`,
  mode-`0644` Python validator
  `scripts/validate_step_01_star_alignment.py`, and mode-`0644` scheduler entry
  point `jobs/step_01_star_align.slurm` to the final owner without renaming their
  basenames. Preserve, rather than silently correct, the nonexecutable job mode.
- Move the mode-`0755` direct shell test
  `tests/shell/test_step_01_star_align.sh` and mode-`0644` direct validator test
  `tests/test_validate_step_01_star_alignment.py` to the mirrored test home.
  Keep the Step `01` fixture adapter and default-placeholder assertion in the
  independent cross-owner scheduler suite: they share its parametrized wrapper
  harness, and extraction would duplicate or cross-import test infrastructure.
  Update only that suite's explicit job path and delegated producer path.
- Extend the moved shell suite with one controlled fake-STAR failure that proves
  exact child status propagation, invocation logging, and the characterized
  output-directory residue. Run the same case against the frozen old path and
  final path; do not synthesize STAR outputs or turn the check into runtime
  evidence.
- Preserve the shell producer's arguments, dry-run default, execute control,
  command bytes, compression handling, streams, exits, and output-directory
  side effect. Its self-identifying help path must name the final producer; any
  other source change requires a review finding.
- Change the validator's exact neutral-library lookup only as required by the
  final owner depth. Preserve its private exact-file report identity, no
  `sys.path` mutation, public basename, interpreter-only mode, five check IDs,
  report bytes, dry-run/execute behavior, and publication semantics.
- Extend the moved validator suite with one full non-repository-CWD dry-run,
  execute, and repeat journey using absolute inputs. Freeze exit/stream parity,
  no dry-run publication, deterministic five-row bytes, stable repeat
  replacement, and no invocation-directory residue across old and final paths.
- In the shared validation-report suite, route every declared non-flat
  validator through the existing path-validating exact-file test loader while
  retaining module-name import for validators still in `scripts/`. This reuses
  the established loader, rejects a foreign cached validator path, preserves
  `sys.path`, and avoids a Step-`01` special case or new loader framework.
- Change the scheduler's delegated producer argument to the exact final path.
  Preserve all seven directives, caller-CWD behavior, module policy, defaults,
  `EXECUTE` handling, thread binding, mutable default fixtures, streams, exits,
  and lack of independent output validation.
- Final public instructions must use complete commands, never bare path labels.
  From repository root, document both direct and explicit-`bash` producer forms
  with every required argument. From another CWD, require an absolute checkout
  path for the producer plus explicit input/output paths. Document the validator
  only through an explicit interpreter and exact final path.
- The supported scheduler journey starts with `cd <checkout>` and submits the
  exact final job path. State that `EXECUTE=0` is default but mutates placeholder
  FASTQs/index under default bindings, `EXECUTE=1` refuses those bindings, the
  five input/output overrides are required for real work, threads come from the
  allocation, and the wrapper performs no independent output validation.
- No legacy wrapper is required. Every named source-path caller is repository-
  owned and can cut over in one atomic executable/test commit; a wrapper would
  preserve accidental flat placement without an unmovable consumer.
- `STEP_PRODUCERS["01"]` intentionally changes to the final producer path.
  Preserve status, evidence ID, Git commit projection, artifact identities,
  schemas, ordering, and consumers. The old producer SHA-256
  `25e2120ca9843ea25f2e1f3b4084aced6261976ab46f7cb25c33d7911f82d0ba`
  is rollback evidence because the help path must change; record and assert the
  reviewed final hash after cutover.
- Coverage already uses stable roots `scripts` and `src/norad`. Move the
  validator's tracked `125/140` line and `34/44` branch row to its final path
  only after inspected final-path measurement proves exact or improved counts
  and global non-regression.
- Once both shell assets leave the flat wildcards, add their exact final paths
  to `validation-static` and `smoke` shell-syntax commands and to the literal
  Make expansion oracle. Move the shell-test and validator-test recipe paths.
  Publish a focused validation block that runs the moved shell suite, moved
  validator suite, and independent central scheduler suite by exact path.
- Existing public-CLI, SLURM, validator, loader, artifact, coverage, and Make
  inventories must retain explicit basename or semantic-ID path maps and exact
  one-owner equality. Do not introduce recursive runtime discovery, alias-
  derived placement, package identity, installation, or global path mutation.
- Replace flat-root inference for public shell entry points with an explicit
  `SHELL_ENTRYPOINT_PATHS` map parallel to the existing Python map, derive the
  public basename set from its keys, and keep exact flat-root inventory equality
  only for entries whose declared parent is `scripts/`. All shell CLI tests must
  resolve paths through that map.
- The existing `CONTRACT.md` remains the detailed behavior owner. Its stale
  Step-00a publication dependency is repaired only in the documentation close.
  Add one concise owner `README.md` only at that card boundary. It must route
  final commands, STAR-native and scheduler diagnostics, five expected outputs,
  validation evidence, dry-run mutations, partial-output preservation,
  rollback, implementation-provenance transition, and the local-only migration
  evidence ceiling. Do not add the target descriptor/schema, scheduler
  abstraction, new CLI, transaction, or scientific alignment policy.

## Blocked by

- [REVIEW-UX-03D](../COMPLETED/REVIEW-UX-03D-review-align-rna-reads-with-star-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, and free of
  merge/rebase/cherry-pick/revert, index-lock, recovery, or overlapping mutable
  lane state before selection or executable mutation.
- Refresh only the named path/import consumers, modes, hashes, Make/static/
  coverage wiring, artifact evidence, and active documentation for this owner.
- Establish identical-input pre-move baselines for direct and explicit-
  interpreter producer behavior, validator behavior, and mocked scheduler
  behavior without SLURM submission, real STAR execution, production inputs,
  dependency installation, or dependency restoration.
- The expanded pre-move baseline must include the controlled producer child
  failure and full non-repository-CWD validator dry-run/execute/repeat journey.
  The central scheduler matrix already owns invalid mode, module failure, child
  exit, caller-CWD failure, delegate-only output validation, and default
  placeholder mutation; do not duplicate that harness.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `01`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `align_RNA_reads_with_STAR` contract; the
  functional-owner inventory; `TEST_BASELINE.md`; and the Step `01`
  troubleshooting route.
- The producer, validator, scheduler job, both direct tests, Step `01` behavior
  in `test_slurm_wrapper_contracts.py`, public-CLI and validator-roster suites,
  and the shared validation-report loader/fault matrix.
- `STEP_PRODUCERS["01"]` and artifact-provenance consumers; coverage
  config/tool/tests/baseline; Make static/smoke/shell-test recipes; and the
  literal Make-expansion fixture.
- All nonhistorical Markdown links and supported commands naming the producer,
  validator, scheduler job, or focused tests. Artifact identities and STAR
  outputs remain unchanged unless a review identifies contrary evidence.

## Questions owned by this card

- None.

## In scope

- Freeze the exact direct invocation graph, paths, modes, hashes, contract
  defects, parity rows, coverage counts, and rollback evidence before source
  mutation.
- Move the producer, validator, and scheduler entry point once to the final
  owner; change only the producer's displayed self-path, the validator's
  owner-relative neutral-library lookup, and the job's delegated producer path
  unless a completed review records another required path-only edit.
- Move the two direct tests to the mirrored owner home. Keep the independent
  cross-owner scheduler fixture adapter and default-placeholder assertion in
  its existing comparative suite, together with mode, directive, roster, CLI,
  loader, artifact, Make, and coverage suites as explicit path-aware consumers.
- Cut over every named repository caller in the same atomic executable/test
  commit, including Make/static/smoke, literal expansions, artifact provenance,
  public CLI, SLURM roster, validator roster, shared loader, direct tests, and
  tracked coverage path.
- Update the moved shell test's repository-root calculation and producer path,
  and the moved Python test's repository-root calculation and validator path;
  those are test-location edits, not new behavior. The production diff is
  limited to the producer usage self-path, validator neutral-owner depth, and
  scheduler delegated child path.
- Extend old/new parity only where the sequential reviews find a missing named
  behavior. Measure coverage at the card boundary, then run the complete
  applicable local gate once on final executable state.
- Add only the two durable regression journeys identified by reliability
  review: controlled producer child failure/residue and non-repository-CWD
  validator dry-run/execute/repeat. The shared neutral-publisher fault matrix
  remains the owner for snapshot, cache, collision, lock, rollback,
  interruption, cleanup, and known late-foreign/reordering defects.
- After executable state is fixed, batch the owner README, migration path/link
  repairs, current topology/status/evidence owners, lifecycle links, and dated
  audit updates into one separate documentation-close commit.

## Out of scope

- Changing STAR arguments, coordinate sorting, gzip selection, sample-ID path
  handling, input-content checks, output names, output validation, or direct
  final-path writes.
- Correcting dry-run output-directory creation, adding a lock, receipt,
  no-clobber rule, staging transaction, cleanup, recovery, or post-STAR checks.
- Correcting scheduler caller-CWD dependence, placeholder creation, module
  version/policy, implicit fixture mutation, `EXECUTE` behavior, or lack of
  independent output validation. These remain characterized defects.
- Changing validator checks, BAM/BGZF recognition, log or splice-junction
  parsing, report ordering, stable-input recheck, lock/rollback behavior, or
  the neutral validation-report library.
- Moving `construct_FASTA_sidecars`, `construct_canonical_BAM`, an artifact or
  report owner, another validator, or another functional owner.
- Adding packages, descriptors, schemas, wrappers, symlinks, compatibility
  copies, global path mutation, dependency actions, cluster/production work,
  scientific claims, or unrelated harness redesign.

## Deliverables

- One atomic final-owner/caller/test/harness cutover commit and one separate
  documentation/lifecycle-close commit, both published sequentially.
- Final producer, validator, and job under
  `src/norad/stages/align_RNA_reads_with_STAR/`; direct owner tests under
  `tests/stages/align_RNA_reads_with_STAR/`; no legacy path, wrapper,
  compatibility copy, duplicate implementation, package marker, descriptor, or
  schema.
- Explicit mixed-layout caller inventories, exact artifact-evidence transition,
  coverage rename accounting, supported final commands, exact searches,
  complete applicable local validation at the card boundary, clean publication
  equality, and a precise local-only evidence ceiling.

## Acceptance evidence

- Producer parity preserves mode `0755`, direct and explicit-interpreter help,
  missing/malformed arguments, arbitrary CWD, dry-run/execute modes, required
  paths, matching compression, command construction, output-directory side
  effects, streams, child status, and exact STAR invocation apart from the
  displayed final self-path.
- A controlled fake STAR exit proves the producer propagates the child status
  after logging the invocation and retains its already-created output directory;
  this residue is characterized, not approved or cleaned up.
- Validator parity preserves mode `0644`, explicit-interpreter and arbitrary-
  CWD behavior, all arguments, five ordered report rows, dry-run/execute/repeat
  effects, deterministic bytes, streams/exits, stable-input recheck, locks,
  foreign state, rollback/cleanup behavior, and exact neutral owner identity
  without global `sys.path` mutation.
- The full validator journey from a non-repository CWD preserves dry-run,
  execute, and repeat stdout/stderr and exits, deterministic five-row bytes, no
  dry-run report, stable replacement, absolute inputs, and no invocation-CWD
  residue. Shared publication tests retain ownership of inherited publisher
  gaps; relocation neither repairs nor blesses them.
- Scheduler parity preserves mode `0644`, seven directives, strict mode,
  caller-CWD delegation, STAR module `2.7.11b`, allocation-derived threads,
  all five overrides plus `EXECUTE`, default dry-run fixture mutation, execute-
  with-default refusal, TMPDIR behavior, exact final child path, streams, child
  and module failures, and no independent output validation.
- The runbook and owner README provide complete final producer direct/`bash`,
  validator dry-run/execute, exact scheduler submission, and three-suite focused
  validation commands. They distinguish repository-root and arbitrary-CWD use,
  warn that producer and scheduler dry-runs mutate different paths, and name
  diagnostics, partial-artifact preservation, rollback, and the next safe
  validation action without claiming new STAR or cluster proof.
- Artifact evidence records the final producer path and reviewed final source
  hash while public Step `01` artifact IDs, schemas, contents, ordering, and
  report consumers remain unchanged.
- Coverage moves validator `125/140` lines and `34/44` branches to its final
  path, or records only review-driven parity improvement, without decreasing
  the committed global floor of `9343/11506` lines and `3281/4698` branches.
- Exact searches find no live legacy source/test/job path, undeclared caller,
  duplicate basename, wrapper, package marker, stage-to-stage import, stale
  command, or stale active lifecycle link. Final owner tests and independent
  caller suites pass without weakening exact inventories.
- The complete applicable computational gate runs once on final executable
  state. After the separate documentation close, documentation validation has
  no migration-caused finding. Any inherited nonpassing condition is recorded
  exactly and never called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` only where mixed
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `01`
  commands in `RUNBOOK.md`; the Step `01` troubleshooting source path if final
  inspection finds one; this card; review lifecycle links; and the dated
  refactor log. Update diagrams only if final inspection finds a material DAG
  or public-flow change.

## Escalation conditions

- Stop for an unknown or unmovable caller, required permanent wrapper, public
  package/import decision, cross-owner implementation import, changed STAR or
  scheduler behavior beyond final path text, artifact/schema change beyond the
  recorded implementation path/hash, parity that requires blessing a defect,
  missing high-risk oracle, dependency or cluster/production action, or scope
  that cannot remain one functional owner plus directly required evidence
  wiring.

## Completion record

Selected for task-specific read-only planning after published usability-review
checkpoint `7d31459ceea981fa4a809afcdc1c8e24dd599874`. The frozen migration parent
remains `f9d638199c6d60cbe81c992fde6a1090cb364302`; all three sequential reviews
are complete. Selection checkpoint
`d6abed12a303dabc9b8166c511969b87f8c41ff2` is the clean, published,
upstream-equal planning parent. Task-specific plan checkpoint
`03cbc97be2fd58944c8f19eb0fb2672416648cce` is also clean, published, and
upstream-equal. The targeted old-path fixture/mock baseline below has run; no
executable or test path has moved.

### Task-specific execution plan

The executable/test write set is exactly fourteen tracked files:

- move `scripts/step_01_star_align.sh`,
  `scripts/validate_step_01_star_alignment.py`, and
  `jobs/step_01_star_align.slurm` into
  `src/norad/stages/align_RNA_reads_with_STAR/` without basename or mode
  changes;
- move `tests/shell/test_step_01_star_align.sh` and
  `tests/test_validate_step_01_star_alignment.py` into
  `tests/stages/align_RNA_reads_with_STAR/` without basename or mode changes;
- update `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`; and
- change no `.coveragerc`, coverage tool/policy test, package marker,
  descriptor, schema, unrelated owner, or documentation file in the executable
  commit.

The production source diff is limited to three path strings: the producer help
self-path becomes its final path; the validator neutral owner resolves from
`Path(__file__).parents[2] / "libraries" / "validation_report.py"`; and the job
delegates through `bash` to the exact final producer path. The producer retains
mode `0755`, the validator mode `0644`, and the job its characterized mode
`0644`. No wrapper or duplicate exists at the legacy paths.

The moved shell test changes only its repository-root depth and producer path,
then makes the fake STAR exit controllable and adds the reviewed child-failure/
output-directory-residue case. The moved Python test changes only its
repository-root depth and validator path, adds an optional subprocess CWD, and
adds the reviewed non-repository-CWD dry-run/execute/repeat case. The central
scheduler suite keeps its Step `01` adapter and placeholder test while updating
the explicit job/delegation paths.

Caller cutover remains literal. Public shell tests gain an explicit path map and
helper parallel to the Python inventory; the validation-report matrix exact-
loads declared non-flat validators with its existing helper; artifact evidence
records the final producer path/hash; validator roster and coverage baseline
rename the exact path; Make static/smoke name both final shell assets; and Make
test recipes and their literal oracle name the moved direct tests.

Old-path baseline is a targeted local fixture/mock tranche, not the full card
gate. It runs syntax on the two shell assets; the existing direct shell suite;
the direct validator, public CLI, SLURM, validation-roster, shared publisher,
artifact-adapter, and coverage-policy test modules; plus temporary untracked-
free probes for the controlled producer child failure and full arbitrary-CWD
validator repeat journey. Record exact counts, streams/exits, deterministic
report hash, residue, modes, and source hashes. Do not run real STAR, submit a
job, restore/install a dependency, or update the coverage baseline.

After that baseline checkpoint is published/equal, apply the fourteen-file
atomic cutover, run the same focused probes at final paths, inspect the final
producer/job diff and hash, then run the complete applicable local gate once at
the `MIG-03D` executable card boundary. Documentation and lifecycle closure
remain a separate batched commit after executable state is fixed.

### Old-path fixture/mock baseline

The baseline ran from clean, published, upstream-equal plan checkpoint
`03cbc97be2fd58944c8f19eb0fb2672416648cce` with no tracked or untracked file,
recovery marker, index lock, or mutable-lane collision. It is local
fixture/mock evidence only:

- `bash -n` passed for the producer and job, and the existing direct shell
  suite passed all of its syntax, help, dry-run, execute, paired-compression,
  mixed-compression, invalid-thread, missing-argument, and missing-input cases.
- The exact targeted Python surface named in the plan passed `555` tests in
  `62.65s`: the direct validator, public CLI, SLURM wrapper, validation roster,
  shared validation-report, artifact-adapter, and coverage-policy modules.
- A temporary fake `STAR` exiting `37` was invoked with the reviewed arguments;
  the producer returned `37`, emitted no stderr, retained its already-created
  output directory, and left that directory empty. This characterizes the
  child-failure residue and does not approve or repair it.
- From a temporary non-repository CWD, the validator returned `0` for dry-run,
  first execute, and repeat execute. Dry-run wrote no report; both executions
  produced the same five all-pass rows and byte-identical report with SHA-256
  `13a6540f578ed55a7c2e5ba66346ec41df45e95df06e746b920cb31dcd5d3a94`;
  stderr, invocation-CWD residue, and publisher lock/temp residue were empty.
- Frozen asset evidence is producer mode `0755`, 5,600 bytes, 195 lines,
  SHA-256
  `25e2120ca9843ea25f2e1f3b4084aced6261976ab46f7cb25c33d7911f82d0ba`;
  validator mode `0644`, 8,506 bytes, 229 lines, SHA-256
  `40b878493949b3d095379aae1413999f1cbfca5954c31299c2a1a34ba89d2aed`;
  and job mode `0644`, 3,348 bytes, 114 lines, SHA-256
  `1b75457580d294a7a4e06017c80aea36b3a9abd68794b8047f47172be3706aa4`.
  The direct shell test remains mode `0755`, SHA-256
  `f86f797b9d8a77437b92a1315c355f2f811ac4d09628c85e775846a2deb9f535`;
  the direct Python test remains mode `0644`, SHA-256
  `2ec9ab15cc2da5f59582b71c778da2b2358a3aee9eb47f38ea353201c7def3c3`.
- No tracked coverage measurement ran. The committed rollback floor remains
  validator `125/140` lines and `34/44` branches and global `9343/11506` lines
  and `3281/4698` branches. Full validation remains deferred to the final-path
  executable card boundary as required.

No real STAR process, scheduler submission, production input, dependency
action, cluster state, scientific review, or biological-readiness evidence was
created. The next slice is the reviewed fourteen-file atomic cutover only.
