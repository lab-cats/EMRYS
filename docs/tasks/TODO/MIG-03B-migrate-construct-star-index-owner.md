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

## Blocked by

- [REVIEW-UX-03B](REVIEW-UX-03B-review-construct-star-index-migration.md) — Required: the dedicated architecture, reliability, and usability passes must close before task-specific execution planning.

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
- After executable state is final, add the concise owner README and update only
  impact-directed topology, inventory, commands, test-baseline, roadmap,
  handoff, card lifecycle, links, and dated audit documentation in a separate
  commit.

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

Not started. JIT carded from frozen published parent
`f3f2c2ab335d5a803550defd7676e9e9f9eb9fa4`. Architecture, reliability, and
usability review must close sequentially before selection; no executable or
test path has moved under this card.
