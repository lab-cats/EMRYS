# MIG-03B — Migrate the construct-STAR-index owner

## Objective

Move the complete `construct_STAR_index` implementation and its owner-local
validator test to their frozen final homes while preserving the current public,
scheduler, validation, provenance, and coverage contracts.

## Why this exists

After the shared validation-report protocol moved to neutral ownership,
`construct_STAR_index` is the smallest dependency-valid functional owner. It
is a DAG root, has only one embedded-compute SLURM producer and one Python
validator, and has no stage-to-stage implementation import. Leaving those
assets in `jobs/` and `scripts/` keeps the flat layout authoritative and leaves
the first functional owner physically unmigrated.

## Fixed decisions

- Frozen parent and rollback target:
  `f3f2c2ab335d5a803550defd7676e9e9f9eb9fa4`, the clean, published,
  local/upstream/live-remote-equal `MIG-03A` closure on the one active campaign
  branch.
- Semantic identity is `construct_STAR_index`, machine key
  `norad.stage.construct_STAR_index.v1`, historical alias `00a`, with final
  source home `src/norad/stages/construct_STAR_index/` and mirrored test home
  `tests/stages/construct_STAR_index/`.
- Move mode-`0644` job
  `jobs/step_00a_build_novogene_star_index.slurm` and mode-`0644` validator
  `scripts/validate_step_00a_star_index.py` to those final owner paths without
  renaming their basenames. Move mode-`0644` direct validator test
  `tests/test_validate_step_00a_star_index.py` and the Step `00a`-specific
  mocked-job behavior test plus its narrow fixtures to the mirrored test home.
  Keep the cross-owner job roster, directive, mode, and generic wrapper checks
  in `tests/test_slurm_wrapper_contracts.py` as independent consumers.
- No legacy wrapper is required. Every named repository caller can cut over in
  the same atomic executable/test commit, the architecture decision records no
  justified external consumer, and a wrapper would retain an accidental public
  path without implementation value. The old job, validator, and direct-test
  paths are absent from the accepted tree.
- The existing `CONTRACT.md` remains the detailed behavior owner. Add only a
  concise owner `README.md` during documentation close. It links to the
  contract and states that physical native-asset placement is implemented while
  the target descriptor/schema remains unrealized; it does not claim the mature
  descriptor shape is complete. Do not add a package marker, descriptor/schema,
  loader framework, scheduler abstraction, new CLI, reference-preparation owner,
  or installation contract.
- The moved validator continues loading the exact neutral
  `src/norad/libraries/validation_report.py` file through its private cache
  identity without global `sys.path` mutation. The owner-relative path changes;
  the shared protocol and the twelve still-legacy validators do not.
- Expand the coverage measurement root from `src/norad/libraries` to
  `src/norad` so the neutral library and every physically migrated owner remain
  measured through one stable source boundary. Preserve the moved validator's
  exact counts/rates across the reviewed baseline update; do not treat it as a
  deletion plus unrelated new code. The source boundary is coverage/static
  selection only and creates no Python package or public import identity.
- Preserve each cross-owner inventory's public basename/semantic keys while
  adding an explicit repository-relative path map for the mixed flat/final
  layout. Only Step `00a` changes path in this unit; do not weaken exact roster
  equality, infer paths from numeric aliases, add recursive runtime discovery,
  or use a legacy path to keep basename-only test code working.
- Extend the owner-local mocked producer characterization before moving it, then
  run the same cases at the final path. Cover default eight-thread fallback,
  preservation/reuse of existing nonempty FASTA and GTF bytes, creation timing,
  success without complete index validation, and the exact module/STAR failure
  exits and retained side effects. These tests preserve current behavior; they
  do not approve its nontransactional design.
- Preserve the inherited validation-publication defects exactly: same-size and
  restored-mtime rewrite blindness, unenforced report-row order, late foreign-
  final deletion, incomplete rollback with lock/recovery loss, previous/staged
  cleanup residue, open-file-descriptor/lock retention during cleanup failure, and
  post-publication lock-cleanup failure. This migration neither fixes nor
  blesses any of them.
- Freeze the moved validator's coverage entry at `165/189` covered/statements
  and `42/60` covered/total branches on the planning parent. After the final
  path and `src/norad` source boundary are active, measure first, compare the
  final-path entry to those exact counts, and only then run the reviewed
  baseline-update command. Do not overwrite the only comparison evidence.
- The reviewed public path transition has no alias. The supported scheduler
  command becomes
  `sbatch src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm`
  from the same caller-owned working directory required today; the mode-`0644`
  job is not a direct-execution CLI and remains CWD-dependent. The supported
  validator form becomes an explicit compatible Python interpreter plus
  `src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py`; with
  explicit input/output paths it remains CWD-independent. Keep those two CWD
  contracts distinct in tests and documentation.
- The owner README must list the final job, validator, and mirrored test paths;
  show the supported invocation forms; warn about implicit job execution and
  caller-relative inputs; link the detailed contract and exact runbook; explain
  the intentional artifact implementation-evidence path transition; state the
  no-wrapper/no-package/no-descriptor boundary; and label all migration evidence
  as local fixture/mock evidence only.

## Blocked by

- [REVIEW-UX-03B](../COMPLETED/REVIEW-UX-03B-review-construct-star-index-migration.md) — Required: the dedicated architecture, reliability, and usability passes must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is still clean, published, upstream-equal, and
  free of merge/rebase/cherry-pick/revert, index-lock, recovery, or overlapping
  mutable-lane state before selection or executable mutation.
- Refresh all named path consumers and modes from the frozen parent. Inspect a
  supported local mocked-job run and validator dry run before the cutover; do
  not submit to SLURM, use production inputs, or install/restore dependencies.
- Confirm the pre-move coverage snapshot measures the validator at its legacy
  path with `165/189` covered/statements and `42/60` covered/total branches, and
  that the approved Python/R environments required by the complete gate are
  already available.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `00a`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `construct_STAR_index` contract; the functional-
  owner inventory; and `TEST_BASELINE.md`.
- The current SLURM job, validator, direct validator test, the Step `00a`
  behavior case and shared inventory assertions in
  `test_slurm_wrapper_contracts.py`, validator-roster and public-CLI suites, and
  the validation-report loader matrix.
- The `STEP_PRODUCERS["00a"]` provenance consumer in
  `build_artifact_index.py`; affected artifact-index tests and independent
  goldens; `.coveragerc`; the coverage snapshot tool/tests/baseline; Make
  static/smoke/shell-test recipes; and the literal Make-expansion fixture.
- Current Step `00a` runbook commands and all nonhistorical Markdown links to
  the legacy job, validator, and direct-test paths.

## Questions owned by this card

- None.

## In scope

- Freeze the exact direct-caller, path, mode, contract, defect, parity, and
  rollback evidence before source mutation.
- Move the job and validator once into the final functional-owner directory,
  adjust only the validator's exact neutral-library resolution, and move the
  direct validator test plus the Step `00a`-specific mocked-job behavior case
  and narrow fixtures to the mirrored owner home. Remove that owner-specific
  case from the cross-owner module while retaining its exact roster/directive/
  mode assertions as independent consumers.
- Before the move, extend and run that mocked-job case against the legacy path
  for reference reuse, default threads, partial-success/no-validation, and
  module/STAR failure side effects. Run identical assertions at the final path.
- Run the validator's full dry-run and execute/repeat journeys from a non-repo
  working directory with identical explicit absolute inputs before and after
  the move; compare stdout/stderr, exit status, output bytes, and invocation-CWD
  residue in addition to the existing help/malformed public matrix.
- Cut over the independent SLURM, public-CLI, validator-roster, validation-
  report-loader, artifact-provenance, coverage, Make, and literal-expansion
  consumers to explicit final paths in the same atomic executable/test commit.
  Use exact path maps keyed by the existing public basename or semantic ID so
  mixed-layout characterization stays exhaustive without compatibility files.
- Rebuild copied-validator missing/corrupt-owner fixtures under each validator's
  actual repository-relative path. The moved Step `00a` copy must occupy its
  final owner path and resolve the same copied `src/norad/libraries` owner; do
  not flatten it back into `scripts` and thereby test a path contract that no
  longer exists.
- Preserve `STEP_PRODUCERS["00a"]` evidence identity and job hash while
  intentionally changing only its recorded implementation path to the final
  owner. Add a focused assertion for the final relative path, evidence ID,
  status, Git commit, and unchanged source SHA-256.
- Update the tracked coverage snapshot only through the reviewed baseline-
  update command after a separate final-path measurement proves the moved
  validator retains the frozen `165/189` line and `42/60` branch counts and
  global line/branch rates do not regress.
- Update `validation-static` and `smoke` so each still syntax-checks every flat
  job plus the exact final Step `00a` job path. Do not leave the moved job
  outside the gate, restore the legacy path for a wildcard, or replace explicit
  paths with runtime discovery; update the literal Make oracle in the same
  executable/test commit.
- After executable state is final, add the concise owner README and update only
  impact-directed topology, inventory, commands, test-baseline, roadmap,
  handoff, card lifecycle, links, and dated audit documentation in a separate
  commit. Replace every active Step `00a` job, validator, and focused-test path
  in `RUNBOOK.md`; document the job as an explicit `sbatch` command and retain
  the validator's explicit-interpreter form. Do not retain a legacy command as
  an alias or fallback.

## Out of scope

- Extracting reference decompression/materialization; changing the hardcoded
  Novogene paths, STAR version, thread/default policy, overhang, module policy,
  implicit-execute behavior, CWD dependence, reuse behavior, output layout, or
  absence of final producer validation/transactionality.
- Moving `convert_GTF_to_BED12`, `construct_FASTA_sidecars`, STAR alignment, a
  neutral scheduler concern, artifact-index ownership, reference-provenance
  ownership, any other validator, or any other functional owner.
- Changing validator inputs, five check IDs, report rows/bytes, failures,
  publication behavior, shared-library defects, artifact schema, scientific
  meaning, evidence state, or biological-readiness policy.
- Adding descriptors, schemas, packages, imports by public package name,
  global path mutation, symlinks, compatibility copies, dependency actions,
  cluster/production execution, or unrelated test-harness redesign.

## Deliverables

- One atomic final-owner/caller/test/harness cutover commit with no supported
  intermediate path state and one separate documentation/lifecycle-close
  commit.
- Final job and validator under
  `src/norad/stages/construct_STAR_index/`, direct validator and mocked-job
  behavior tests under `tests/stages/construct_STAR_index/`, and no legacy
  implementation, owner-specific test case, direct-test path, wrapper,
  compatibility copy, or duplicate owner.
- Path-aware independent caller inventories that continue covering all public
  Python and SLURM surfaces without pretending final-owner files remain flat.
- One discoverable owner README and one authoritative final command for the
  scheduler job, validator dry run/execute, and focused tests; no legacy alias.
- Coverage/static/smoke/Make wiring that measures and compiles the final owner,
  plus a reviewed baseline whose moved-validator counts remain traceable.
- Exact legacy-path searches, focused old/new parity evidence, one complete
  applicable local gate, clean commits, publication/upstream equality, and an
  explicit local-only evidence ceiling.

## Acceptance evidence

- Before/after comparisons preserve the job's seven `#SBATCH` directives,
  `/usr/bin/env bash` shebang, mode `0644`, caller-CWD behavior, strict module
  load/list handling, default eight-thread fallback, `sjdbOverhang=149`, reuse
  of nonempty prepared references, directory creation timing, exact mocked STAR
  arguments, streams, child/module exit propagation, and lack of final output
  validation. Failure assertions preserve the exact prepared references and
  directories left behind rather than treating their cleanup as approved.
- The validator preserves mode `0644`, explicit-interpreter invocation,
  arbitrary-CWD help/malformed behavior, all arguments, dry-run/execute effects,
  stdout/stderr, exit status, five ordered check IDs, deterministic report
  bytes, stable-input recheck, lock/publication behavior, and foreign-state
  preservation through the exact neutral owner. Full dry-run and execute/repeat
  fixture journeys pass from a non-repository working directory without
  invocation-CWD residue.
- Loader tests prove the moved validator resolves the exact final neutral file,
  uses the same private module object, leaves `sys.path` unchanged, rejects a
  wrong/partial cache, cleans only its owned partial on execution failure, and
  retains actionable artifact-free failure diagnostics. The twelve remaining
  legacy loaders retain their prior path logic and behavior. Missing/corrupt-
  owner copies reproduce each validator's actual relative layout.
- Public CLI and SLURM inventories contain every current entry exactly once at
  its actual path; Step `00a` independent wrapper, roster, artifact-index,
  shared publication, public-CLI, Make-expansion, and direct-validator tests
  pass without weakening their cross-owner assertions. The Step `00a` mocked
  producer behavior case and its narrow fixtures live in the mirrored owner
  test home rather than the cross-owner inventory module.
- Artifact implementation evidence changes only the Step `00a` source path to
  the final job while retaining status, evidence ID, Git commit, job bytes/hash,
  artifact identities, schemas, ordering, and consumer behavior; a focused
  final-path assertion protects this transition.
- Coverage metadata names exactly `scripts` and `src/norad`; the legacy
  validator baseline row is replaced by its final path only after a separate
  measurement shows `165/189` covered/statements and `42/60` covered/total
  branches, the neutral library remains threshold-enforced, and global exact
  line and branch rates do not decrease.
- Exact searches find no live legacy job, validator, or direct-test path; no
  wrapper, duplicate implementation, package marker, stage-to-stage import,
  undeclared caller, stale runbook command, or stale Markdown link remains.
- `validation-static`, `smoke`, `shell-test`, and their literal Make expansions
  invoke or inspect the exact final paths. The runbook and owner README
  distinguish the job's caller-CWD dependence from the validator's explicit-
  path arbitrary-CWD behavior and do not imply direct execution of a mode-`0644`
  file.
- The complete applicable computational gate runs on the final executable tree.
  After the documentation-only close, Git/documentation validation reports no
  migration-caused finding. Any inherited nonpassing condition is recorded
  exactly and is never claimed as a passing gate.

## Canonical documentation updates

- Owner `README.md`; `ARCHITECTURE.md`; `FUNCTIONAL_OWNER_INVENTORY.md`;
  `TEST_BASELINE.md`; `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`;
  `HANDOFF.md`; Step `00a` paths in `RUNBOOK.md`; this card; and the dated
  refactor log. Update diagrams only if final inspection finds a material DAG
  or public-flow change; a pure owner-path relocation should not.

## Escalation conditions

- Stop for an unknown or unmovable caller, any required permanent wrapper,
  public packaging/import decision, stage-to-stage implementation import,
  changed STAR/reference behavior, provenance/schema change beyond the recorded
  final source path, parity that requires blessing a defect, missing independent
  mocked-job or validator evidence, required dependency action, cluster or
  production action, or scope that cannot remain one functional owner plus its
  directly required evidence wiring.

## Completion record

Selected for execution planning at clean, published, local/upstream/live-
remote-equal checkpoint `be1b658`. The architecture, reliability, and
usability reviews are complete. The task-specific baseline below changes
planning documentation only; no executable or test path has moved.

### Frozen task-specific execution baseline

- Semantic planning category: behavior or architecture planning. Validation
  impact: executable/test-affecting. Execution remains the one reviewed
  `construct_STAR_index` owner; it does not activate another owner or neutral
  concern.
- The executable/test write set is limited to `.coveragerc`, `Makefile`, the
  three moved native/test files, `scripts/build_artifact_index.py`, the owner-
  local mocked-producer test added beneath the final mirrored home,
  `tests/test_slurm_wrapper_contracts.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/test_artifact_adapters.py`, the coverage tool and its direct test, the
  tracked coverage snapshot, and the literal Make-expansion fixture. No schema,
  report asset, scientific implementation, dependency, or other owner changes.
- Exact path inventories remain keyed by the current public basenames or
  semantic IDs. They name every mixed flat/final path literally; they do not
  discover recursively, derive from historical numbers, or retain an old-path
  compatibility file. The wrapper decision remains `not required`.
- The uncommitted execution sequence first extends the owner-local mocked job
  and validator arbitrary-CWD parity cases at the old paths, runs them, moves
  the three files once with mode/bytes preserved, moves the mocked producer
  case and narrow fakes out of the cross-owner suite, and cuts over all named
  path consumers. It then runs the identical owner cases at the final paths.
- The pre-move job is mode `0644`, 1,954 bytes, and SHA-256
  `f27924e80fee3b8f207a41fd7af472897ad51f06aa2e4c670973eb51f25b5fcc`;
  the validator is mode `0644`, 11,883 bytes, and SHA-256
  `0bb5ce8f87f1542fd731bcdd80f606d2f3a3982df1f65f8a17e6bc39bf9c0a6e`.
  The direct test is mode `0644`, 4,621 bytes, and SHA-256
  `65a9f07b6f8465290b44c9b4dde76a44ad0c59d51b225421fc749fb955a8c95a`.
- Focused pre-move evidence at `be1b658`: direct validator `5 passed`; Step
  `00a` mocked/inventory selection `4 passed, 109 deselected`; public-path
  selection `3 passed, 116 deselected`; validator rosters `105 passed`; shared
  validator/loader selection `113 passed, 24 deselected`; coverage-tool unit
  tests `7 passed`; and artifact-index dry-run `1 passed, 68 deselected`.
  These are local fixture/mock checks only.
- The tracked pre-move validator coverage row is exactly `165/189` lines and
  `42/60` branches; global totals are `9343/11506` lines and `3281/4698`
  branches. Final-path `make python-coverage-measure` must be inspected against
  both before `make python-coverage-baseline-update`, followed by
  `make python-coverage-check` and the one complete final `make -s all-checks`.
- The approved environment is already present without restoration or install:
  repository `.venv` Python `3.14.5`, coverage `7.15.2`, pytest `9.0.3`,
  pytest-xdist `3.8.0`, execnet `2.1.2`, `/usr/local/bin/Rscript` `4.6.1`, the
  repository R library, and the pinned Quarto tools root. The complete runner
  must demonstrably start before its result is classified.
- Rollback for executable failure is the stable pre-mutation commit containing
  this record, then the earlier clean selection checkpoint `be1b658`; do not
  copy files back, retain a duplicate, or touch runtime/production/lock/
  recovery artifacts. Documentation close is a later separate commit and is
  reverted before the executable cutover if rollback occurs after closure.
