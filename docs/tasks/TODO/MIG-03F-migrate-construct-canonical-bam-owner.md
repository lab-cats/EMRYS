# MIG-03F — Migrate the construct-canonical-BAM owner

## Objective

Move the complete `construct_canonical_BAM` producer, validator, scheduler
asset, and owner-local tests to their frozen final homes while removing the
current downstream imports of its validator through one bounded neutral-helper
preparation slice and preserving every public, transaction, scheduler,
validation, artifact, and coverage contract.

## Why this exists

After `MIG-03E`, `construct_canonical_BAM` is the only next functional owner
supported by the live semantic DAG: its sole hard predecessor,
`align_RNA_reads_with_STAR`, is migrated, while every remaining computational
or evidence owner has an unmigrated hard predecessor. The owner was not selected
earlier because the Step `04` and Step `05` validators import `run_tool` and
`parse_header` directly from its stage-named validator. This card resolves that
known target-dependency violation before moving the owner; it does not select or
migrate either downstream stage.

## Fixed decisions

- Frozen definition parent and rollback target:
  `fa79883683b37559dfa90880a3f04a978bbfb530`, the clean, published,
  local/upstream/live-remote-equal `MIG-03E` documentation close on the one
  active campaign branch.
- Semantic identity is `construct_canonical_BAM`, machine key
  `norad.stage.construct_canonical_BAM.v1`, historical alias `02`, with final
  source home `src/norad/stages/construct_canonical_BAM/` and mirrored test home
  `tests/stages/construct_canonical_BAM/`.
- Move the mode-`0755` shell producer `scripts/step_02_sort_index_bam.sh`,
  mode-`0644` Python validator `scripts/validate_step_02_canonical_bam.py`, and
  intentionally mode-`0644` scheduler entry point
  `jobs/step_02_sort_index_bam.slurm` to the final owner without changing their
  basenames or modes.
- Move the mode-`0755` direct shell test
  `tests/shell/test_step_02_sort_index_bam.sh` and mode-`0644` direct validator
  test `tests/test_validate_step_02_canonical_bam.py` to the mirrored owner
  home. Keep scheduler behavior in the independent parametrized wrapper suite.
- The three native assets currently total `23,743` bytes and `746` lines.
  Frozen hashes are producer
  `ad73a5476447cba0cd5265864a16710492a2e313150ab2ac7293fef8c26a627c`,
  validator
  `d805f17c4c95aea004f4a440c82241d7d5f5e8d3024fac94fb1de90421bb67ac`,
  and job
  `b67f50db365aba533d882746df02a1f9ea0c5e6b5c25170e9251978cc8be6f8b`.
  Direct-test rollback hashes are shell
  `239646b44d6b411fe9b590108e6e7e977427ee93c62cee1b16212f90c275e29c`
  and validator
  `f7f9dd25ec9ad7e70a4d5566a09039e67f3b27cee5dd0294bffaa48990260492`.
- Resolve the known peer-implementation imports before the owner move with one
  private neutral
  `src/norad/libraries/bam_validation.py` containing only behavior-preserving
  `run_tool` and `parse_header` helpers extracted from the Step `02` validator.
  Freeze private module identity `_norad_bam_validation`, readiness attribute
  `_NORAD_BAM_VALIDATION_READY`, and the complete required API as callable
  `run_tool` and `parse_header`. Step `02`, Step `04`, and Step `05` validators
  resolve that exact mode-`0644` file through caller-local loaders. Each loader
  verifies cached `__file__`, readiness and API shape, preserves foreign cache
  state and `sys.path`, removes only its owned partial module after execution
  failure, and exits before report publication with
  `ERROR: unable to load NORAD BAM-validation owner at <path>: <type>: <reason>`.
  The neutral file has no public CLI, package identity, validation-report
  dependency, or stage-specific check logic.
- Freeze the helper preparation slice to exactly five tracked files: add
  `src/norad/libraries/bam_validation.py` and
  `tests/libraries/test_bam_validation.py`; modify only
  `scripts/validate_step_02_canonical_bam.py`,
  `scripts/validate_step_04_mark_duplicates.py`, and
  `scripts/validate_step_05_split_ncigar.py`. The neutral suite owns exact helper
  behavior and the three-caller healthy/missing/wrong-cache/incomplete/owned-
  failure matrix. Existing Step `02`, `04`, and `05` direct tests remain
  unchanged but run as the smallest affected regression set.
- Before that extraction, capture an old-path helper baseline that exact-loads
  the current Step `02` functions and freezes `run_tool` argv, stdout, stderr,
  return code, and representative valid/multiple/missing/mismatched
  `parse_header` results. After extraction, the neutral suite must prove exact
  result/exception parity and the complete loader matrix for all three callers
  at the flat layout and final Step `02` depth, including foreign-cache and
  unchanged-`sys.path` preservation, owned-partial cleanup, fail-closed
  diagnostics, no report publication, and no invocation-CWD residue.
- Freeze the subsequent owner cutover to exactly fifteen logical tracked files:
  five moves of the producer, validator, job, shell test, and validator test;
  plus `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/libraries/test_bam_validation.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`. The moved
  validator changes only both exact-owner depths; the producer changes only its
  help self-path; and the job changes only its delegated child path. Any sixth
  move, eleventh caller/harness modification, or downstream direct-test edit
  reopens architecture review.
- The helper preparation and native owner move are separate executable slices
  under this one card. Publish the reviewed helper checkpoint first, using only
  the smallest direct checks at that slice boundary; then move the owner and
  caller paths, again using only minimal final-path checks. Run the full
  applicable computational gate once after the complete final executable state
  is assembled at the card boundary. Batch migration links and other canonical
  documentation into the separate card close.
- Test ownership follows implementation ownership without duplicating
  frameworks: the new neutral suite owns the helper and private loader contract;
  Step-specific direct suites continue to own their check rosters and user-
  visible behavior; the central scheduler, validation-report, public-CLI,
  artifact, coverage, and Make suites remain independent cross-owner callers.
- Artifact evidence does not change in the helper slice. The owner cutover
  changes only the Step `02` producer path and reviewed post-help hash, with one
  new exact assertion in the existing migrated-implementation evidence test.
  Public artifact identities, schemas, contents, ordering, and consumers remain
  unchanged.
- Do not leave a legacy Step `02` validator wrapper merely to satisfy Step `04`
  or Step `05`. Do not copy the helpers into either downstream validator, import
  the final Step `02` implementation from a peer owner, or introduce package
  identity, installation, runtime discovery, or `sys.path` mutation.
- Preserve the producer's CLI, `samtools` PATH resolution, dry-run default and
  no-write behavior, command bytes, output names, read-group fields, staged
  validation, pair-state precondition, lock ownership, run-token paths, backup
  order, replacement, final validation, streams, exits, cleanup, and rollback
  attempts. Its help self-path must name the final producer; any other producer
  change requires a review finding.
- Preserve rather than approve the producer's recovery boundary: rollback
  restoration moves are best-effort, their failures are ignored, backups may
  then be removed, and no receipt or recovery marker records an incomplete
  restore. Reviews must decide the exact old/final-path fault oracle and
  evidence-preservation response without changing this behavior.
- The reliability oracle is one synthetic previous-pair case in the moved
  shell suite: fail final BAI publication, then fail restoration of the prior
  BAM. Old and final paths must fail nonzero with both diagnostics, retain only
  the prior BAI bytes, leave the canonical BAM and both backups absent, remove
  the owned lock, and leave no run-token scratch. This lockless partial pair and
  lost prior BAM are an intentionally preserved ambiguous/data-loss defect; do
  not repair, bless, or use it as authority for cleanup.
- Preserve the validator's mode, public basename, five check IDs, report bytes,
  dry-run/execute behavior, stable-input recheck, and publication semantics.
  Preserve its characterized disagreement with the producer: zero-record BAMs,
  missing `LB`/`PL`, quickcheck detail, and BAI/BAM identity are not silently
  normalized by relocation.
- Extend only the moved validator suite with one non-repository-CWD dry-run,
  execute, and repeat journey. Require exact ordered five-row bytes, empty
  successful stderr, stable replacement, unchanged input bytes/modes, and no
  invocation-directory residue. Shared publication-fault and roster suites
  remain the independent owners of their existing contracts.
- Change the validator's exact neutral validation-report lookup only as required
  by final owner depth. The new BAM-helper loader is the only reviewed semantic-
  ownership correction; stage-specific `integer_stdout`, checks, CLI, and
  publication stay with Step `02`.
- Change the scheduler's delegated child to the exact final producer. Preserve
  all directives, mode, strictness, caller-CWD behavior, module calls, defaults,
  output-directory/log creation, `EXECUTE` handling, output checks, streams,
  exits, and Bash `3.2` empty-array dry-run defect.
- Final scheduler instructions must `cd` to the checkout, create `logs/`, submit
  the exact final job, and expose `SAMPLE_ID`, `INPUT_ALIGNMENT`, `OUTPUT_DIR`,
  `THREADS`, and `EXECUTE`. State that the wrapper ignores `SLURM_SUBMIT_DIR`,
  forces `TMPDIR=/tmp`, creates log/output directories in dry-run, strictly
  loads samtools `1.19.2`, tolerates only module-list diagnostics, and can fail
  before producer delegation on Bash `3.2`. Do not imply local mocked coverage
  proves a real submission.
- `STEP_PRODUCERS["02"]` intentionally changes to the final producer path.
  Preserve status, evidence ID, Git projection, artifact identities, schemas,
  contents, ordering, reconciliation, and consumers. Record the reviewed final
  producer hash after the required help self-path change.
- Coverage already measures `scripts` and `src/norad`. Frozen starting rows are
  Step `02` `105/115` covered lines and `21/28` branches, Step `04` `105/114`
  and `22/28`, and Step `05` `98/108` and `19/24`; the current global snapshot
  is `9381/11549` lines and `3293/4714` branches. Extraction may change only
  those three rows plus the new helper. Final measurement must retain each old
  row's line/branch rate, retain at least the combined `308` covered lines and
  `62` covered branches across the four rows, keep every non-target row exact,
  preserve the global covered-count floors, and give the helper at least 90%
  line and 85% branch coverage before the committed baseline changes.
- Once both shell assets leave flat wildcards, add their exact final paths to
  `validation-static` and `smoke` shell syntax and to the literal Make-expansion
  oracle. Move the direct shell/validator recipe paths. Keep public CLI, SLURM,
  validator, shared-loader, artifact, and coverage inventories explicit; do not
  add recursive discovery.
- The existing `CONTRACT.md` remains the detailed behavior owner. Add one
  concise owner `README.md` only at documentation close. It must route complete
  root/arbitrary-CWD producer and validator commands, scheduler submission,
  transaction diagnostics, ambiguous rollback preservation, final paths,
  focused tests, implementation-provenance transition, rollback, and the local-
  only evidence ceiling.
- The README and Step `02` runbook must show final-path producer dry-run and
  `--execute` in both direct and explicit-`bash` forms. Explain that the
  producer resolves samtools only from PATH, that dry-run invokes no samtools
  command and creates no output directory/lock/scratch/backup/BAM/BAI, and that
  arbitrary-CWD use requires absolute producer/input/output paths. Show the
  mode-`0644` validator through an explicit interpreter for dry-run, execute,
  repeat, and arbitrary-CWD use with an explicit samtools path.
- Replace any unconditional complete-rollback claim. The owner README, runbook,
  and troubleshooting route must name the possible prior-BAI-only lockless
  state and require preservation of the pair directory, producer and scheduler
  streams, run-token temporary/backup paths, and exact final/backup bytes before
  any separately authorized recovery decision. The absence of a lock, backup,
  receipt, or marker does not authorize deletion, adoption, or retry.
- Route the exact-loader diagnostic to checkout-integrity inspection of private
  `src/norad/libraries/bam_validation.py`; do not suggest `PYTHONPATH`, package
  installation, a public helper CLI, or a legacy Step `02` path. Focused local
  commands must include the moved shell/validator suites, neutral helper suite,
  unchanged Step `04`/`05` validator regressions, and central scheduler suite.
- Add no descriptor, schema, package marker, compatibility copy, symlink,
  scheduler abstraction, receipt, recovery marker, transaction redesign,
  manifest policy, or public neutral-helper CLI.
- Rollback order is documentation close first, owner cutover second, helper
  preparation third, then the published pre-card parent. Reverting the owner
  move restores the flat Step `02` validator while it still uses the neutral
  helper; only then may the helper slice restore the original peer import graph.

## Blocked by

- [REVIEW-UX-03F](../COMPLETED/REVIEW-UX-03F-review-construct-canonical-bam-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal,
  live-remote-equal, and free of recovery, index-lock, or overlapping mutable-
  lane state before selection or executable mutation.
- Refresh only the named path/import consumers, modes, hashes, Make/static/
  coverage wiring, artifact evidence, active documentation, and Step `02`/`04`/
  `05` helper use needed by this owner.
- Establish identical-input pre-move baselines for the helper semantics,
  producer transaction, validator, and mocked scheduler behavior without real
  samtools work, SLURM submission, dependency action, or production input.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `02`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `construct_canonical_BAM` contract; the
  functional-owner inventory; and `TEST_BASELINE.md`.
- The producer, validator, scheduler job, two direct tests, central scheduler
  suite, public-CLI and validation rosters, shared validation-report suite,
  Make/literal fixtures, artifact mapping, and coverage policy/baseline.
- Step `04` and Step `05` validators and their direct tests, limited to the
  exact `run_tool`/`parse_header` dependency and any reviewed private-loader
  fault coverage. Their stage behavior and migration remain out of scope.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture review owns the
  neutral-helper boundary; reliability owns missing fault oracles; usability
  owns final commands and recovery routes.

## In scope

- Freeze the exact helper call graph and byte/exception behavior, native paths,
  modes, hashes, caller maps, defects, parity rows, coverage counts, and rollback
  evidence before mutation.
- Extract only the shared `run_tool` and `parse_header` behavior to one reviewed
  neutral private library, add its direct tests, and replace the three current
  stage-to-stage imports with exact-file private loaders.
- Move the three Step `02` native assets and two direct tests to final homes and
  cut over every explicit repository caller, job delegation, Make recipe,
  artifact implementation record, public map, validation roster, shared loader,
  coverage row, and literal expansion.
- Make only reviewed path/loading changes in production code. Any broader
  behavior change, another helper, another functional owner, or an unplanned
  executable/test path requires a recorded review correction before mutation.
- Validate each executable slice minimally, then run the complete applicable
  local gate once on final executable state. Commit and publish stable
  checkpoints sequentially before the separate documentation/lifecycle close.

## Out of scope

- Migrating or redesigning Step `04`, Step `05`, Step `02b`, Step `03`, or any
  later owner; changing their checks, CLIs, outputs, artifact evidence, or jobs.
- Keeping a legacy Step `02` module, wrapper, re-export, symlink, alias, or
  compatibility copy for peer imports.
- Correcting producer/validator asymmetries, sample/library/platform policy,
  input-stability checks, BAI/BAM identity, replacement policy, rollback
  guarantees, receipts, or recovery markers.
- Correcting scheduler mode, caller CWD, module policy, default bindings,
  directory creation, Bash `3.2`, output checks, or cluster behavior.
- Broad shared-library ownership design, packaging, descriptors, schemas,
  installation, dependency restore/install, cluster/production work, scientific
  claims, or unrelated test-harness redesign.

## Deliverables

- One reviewed neutral-helper preparation checkpoint, one final-owner/caller/
  test cutover checkpoint, and one separate documentation/lifecycle-close
  checkpoint, published sequentially on the same branch.
- Final producer, validator, and job under
  `src/norad/stages/construct_canonical_BAM/`; direct owner tests under
  `tests/stages/construct_canonical_BAM/`; no legacy Step `02` path or peer-
  implementation import.
- Explicit private neutral-helper ownership, exact mixed-layout caller maps,
  artifact path/hash transition, coverage accounting, supported final commands,
  complete card-boundary validation, clean publication equality, and a precise
  local-only evidence ceiling.

## Acceptance evidence

- Helper parity proves exact `run_tool` argument/result behavior and
  `parse_header` outcomes before/after extraction, plus healthy, missing,
  wrong-cache, partial-load, owned-failure, foreign-state, and unchanged-
  `sys.path` loader states for each distinct caller depth required by review.
- Producer parity preserves every CLI, dry-run, execute, transaction, lock,
  replacement, rollback-attempt, cleanup, stream, exit, and characterized
  ambiguous-recovery state apart from the final displayed self-path, including
  the exact lockless prior-BAI-only result when BAM restoration fails.
- Validator parity preserves all arguments, five rows, mismatch evidence,
  dry-run/execute/repeat effects, report bytes, streams/exits, stable-input
  recheck, publication faults, and documented producer asymmetries.
- Scheduler parity preserves mode `0644`, directives, CWD/module/default/
  execute/directory/output behavior, exact final child path, streams/exits, and
  Bash `3.2` defect.
- Exact searches find one final owner, no live legacy path or peer-stage import,
  and no duplicate, wrapper, package marker, descriptor, schema, stale command,
  or stale active lifecycle link.
- Final coverage meets the existing per-file/global policies and new-shared-
  module threshold without hiding moved or extracted lines.
- The complete applicable computational gate runs once at the final executable
  card boundary. After the separate documentation close, documentation
  validation has no migration-caused finding; inherited findings are reported
  exactly and never called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; neutral libraries README;
  `ARCHITECTURE.md` where current mixed placement/helper ownership changes;
  `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `02`
  commands in `RUNBOOK.md`; Step `02` transaction/validation routes in
  `TROUBLESHOOTING.md`; this card; review lifecycle links; and the dated audit
  log. Update diagrams only if final inspection finds a material DAG or public-
  flow change.

## Escalation conditions

- Stop for an unmovable caller, required public package/import identity,
  helper behavior that cannot be extracted without redesign, required second
  functional-owner migration, permanent wrapper, artifact/schema change beyond
  implementation path/hash, parity that requires blessing a defect, missing
  high-risk oracle, dependency or cluster/production action, or scope that
  cannot remain the one Step `02` owner plus its directly required neutral
  helper and evidence wiring.

## Completion record

Not selected. Defined from clean, published, local/upstream/live-remote-equal
`MIG-03E` documentation checkpoint `fa79883`. All three dedicated review cards
remain unselected in `TODO`; no executable/test path changed, no computational
test ran, and no later owner is preloaded.
