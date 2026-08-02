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
  `tests/test_validate_step_00a_star_index.py` to the mirrored test home.
- No legacy wrapper is required. Every named repository caller can cut over in
  the same atomic executable/test commit, the architecture decision records no
  justified external consumer, and a wrapper would retain an accidental public
  path without implementation value. The old job, validator, and direct-test
  paths are absent from the accepted tree.
- The existing `CONTRACT.md` remains the detailed behavior owner. Add only a
  concise owner `README.md` during documentation close. Do not add a package
  marker, descriptor/schema, loader framework, scheduler abstraction, new CLI,
  reference-preparation owner, or installation contract.
- The moved validator continues loading the exact neutral
  `src/norad/libraries/validation_report.py` file through its private cache
  identity without global `sys.path` mutation. The owner-relative path changes;
  the shared protocol and the twelve still-legacy validators do not.
- Expand the coverage measurement root from `src/norad/libraries` to
  `src/norad` so the neutral library and every physically migrated owner remain
  measured through one stable source boundary. Preserve the moved validator's
  exact counts/rates across the reviewed baseline update; do not treat it as a
  deletion plus unrelated new code.

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
  path and that the approved Python/R environments required by the complete
  gate are already available.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `00a`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `construct_STAR_index` contract; the functional-
  owner inventory; and `TEST_BASELINE.md`.
- The current SLURM job, validator, direct validator test, Step `00a` cases in
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
  direct validator test to the mirrored owner home.
- Cut over the independent SLURM, public-CLI, validator-roster, validation-
  report-loader, artifact-provenance, coverage, Make, and literal-expansion
  consumers to explicit final paths in the same atomic executable/test commit.
- Preserve `STEP_PRODUCERS["00a"]` evidence identity and job hash while
  intentionally changing only its recorded implementation path to the final
  owner.
- Update the tracked coverage snapshot only through the reviewed baseline-
  update command after proving the moved validator remains measured and global
  line/branch rates do not regress.
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
  `src/norad/stages/construct_STAR_index/`, direct test under
  `tests/stages/construct_STAR_index/`, and no legacy implementation, direct-
  test path, wrapper, compatibility copy, or duplicate owner.
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
  validation.
- The validator preserves mode `0644`, explicit-interpreter invocation,
  arbitrary-CWD help/malformed behavior, all arguments, dry-run/execute effects,
  stdout/stderr, exit status, five ordered check IDs, deterministic report
  bytes, stable-input recheck, lock/publication behavior, and foreign-state
  preservation through the exact neutral owner.
- Loader tests prove the moved validator resolves the exact final neutral file,
  uses the same private module object, leaves `sys.path` unchanged, rejects a
  wrong/partial cache, cleans only its owned partial on execution failure, and
  retains actionable artifact-free failure diagnostics. The twelve remaining
  legacy loaders retain their prior path logic and behavior.
- Public CLI and SLURM inventories contain every current entry exactly once at
  its actual path; Step `00a` independent wrapper, roster, artifact-index,
  shared publication, public-CLI, Make-expansion, and direct-validator tests
  pass without weakening their cross-owner assertions.
- Artifact implementation evidence changes only the Step `00a` source path to
  the final job while retaining status, evidence ID, Git commit, job bytes/hash,
  artifact identities, schemas, ordering, and consumer behavior.
- Coverage metadata names exactly `scripts` and `src/norad`; the legacy
  validator baseline row is replaced by its final path with comparable counts,
  the neutral library remains threshold-enforced, and global exact line and
  branch rates do not decrease.
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
