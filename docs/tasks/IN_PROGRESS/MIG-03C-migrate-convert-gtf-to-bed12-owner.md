# MIG-03C — Migrate the convert-GTF-to-BED12 owner

## Objective

Move the complete `convert_GTF_to_BED12` producer, validator, scheduler asset,
and owner-local tests to their frozen final homes while preserving current
public, scheduler, validation, provenance, coverage, and BED12 contracts.

## Why this exists

After `MIG-03B`, `convert_GTF_to_BED12` and `construct_FASTA_sidecars` are both
typed-external-input DAG roots eligible for migration. `convert_GTF_to_BED12`
is the smaller dependency-safe unit: its only implementation import is from
its validator to its same-owner producer, whereas the FASTA-sidecar validator
also depends on the still-flat cross-cutting reference-provenance parser owner.
This selection follows semantic dependency and live coupling, not historical
alias order.

## Fixed decisions

- Frozen parent and rollback target:
  `1b82e4f04b926ac12e6306e40d03fee7840f3fa6`, the clean, published,
  local/upstream-equal `MIG-03B` documentation close on the one active campaign
  branch.
- Semantic identity is `convert_GTF_to_BED12`, machine key
  `norad.stage.convert_GTF_to_BED12.v1`, historical alias `00b`, with final
  source home `src/norad/stages/convert_GTF_to_BED12/` and mirrored test home
  `tests/stages/convert_GTF_to_BED12/`.
- Move the mode-`0755` Python producer `scripts/gtf_to_bed12.py`, mode-`0644`
  validator `scripts/validate_step_00b_bed12.py`, and mode-`0755` scheduler
  entry point `jobs/step_00b_gtf_to_bed12.slurm` to the final owner without
  renaming their basenames. Move mode-`0644` direct tests
  `tests/test_gtf_to_bed12.py` and `tests/test_validate_step_00b_bed12.py` plus
  the Step `00b`-specific mocked-job behavior and narrow fakes to the mirrored
  test home. Cross-owner roster, directive, mode, and generic scheduler checks
  remain independent consumers.
- Preserve the producer-validator relationship as a same-owner sibling import;
  do not introduce a package marker, public import identity, global `sys.path`
  mutation, install step, or generic loader framework. Adjust only paths needed
  by exact-file test loading and by the validator's neutral publication owner.
- Production retains the literal sibling `import gtf_to_bed12`. The independent
  shared-loader suite must exact-load the final sibling producer under that
  existing module identity before exact-loading the validator, reject a cached
  producer from any other file, preserve `sys.path`, and restore only test-owned
  cache state. Copied-validator missing/corrupt-neutral-owner fixtures recreate
  the final relative layout and include the sibling producer rather than
  flattening or silently importing a legacy path.
- The scheduler job must change its delegated producer argument from the legacy
  path to the exact final producer path. Every directive, mode, environment
  override, submit-directory rule, command argument, stream, side effect,
  module policy, exit, and output check otherwise remains frozen.
- No legacy wrapper is required. Every named source-path caller is repository-
  owned and can cut over in one atomic executable/test commit; a wrapper would
  preserve accidental flat placement without an unmovable consumer.
- Final public instructions must use complete commands, not bare path labels.
  From the repository root, document both the mode-`0755` producer's direct
  invocation and its exact-interpreter form with explicit GTF/BED arguments;
  from another CWD, require an absolute checkout path or an explicit `cd`.
  Document the validator only through an explicit interpreter. Document the
  scheduler entry point as `cd <checkout>` followed by `sbatch` of its exact
  final path because `SLURM_SUBMIT_DIR` is mandatory and becomes the job CWD.
  State that submission executes implicitly, has no dry-run control, honors
  the four existing overrides, and publishes nontransactionally.
- `STEP_PRODUCERS["00b"]` intentionally changes only its implementation path
  to the final producer. Preserve status, evidence ID, Git commit projection,
  producer bytes/SHA-256, artifact identities, schemas, ordering, and consumer
  behavior with a focused assertion.
- Coverage already uses stable roots `scripts` and `src/norad`. Move both
  tracked rows to their final paths, move the required-subprocess identity for
  `gtf_to_bed12.py`, and update the snapshot only after a separate reviewed
  final-path measurement proves exact counts and global non-regression.
- Once the job leaves `jobs/*.slurm`, add its exact final path to both
  `validation-static` and `smoke` shell-syntax commands and to the literal Make
  expansion oracle. Existing `compileall` roots already cover `src/norad`.
  Move the `shell-test` validator path and publish one focused command covering
  the moved producer, validator, and owner-local mocked-job suites.
- Existing explicit path maps stay keyed by public basename or semantic ID.
  They name the final producer, validator, and job literally, continue proving
  every flat and owner-local surface exists exactly once, and do not infer
  locations from aliases, recurse for runtime discovery, or weaken inventory
  equality to accommodate the move.
- The existing `CONTRACT.md` remains the detailed behavior owner. Add one
  concise owner `README.md` only during documentation close. Do not add the
  target descriptor/schema, package identity, scheduler abstraction, new CLI,
  reference-materialization owner, sorting redesign, or independent scientific
  normalization policy.

## Blocked by

- [REVIEW-UX-03C](../COMPLETED/REVIEW-UX-03C-review-convert-gtf-to-bed12-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, and free of
  merge/rebase/cherry-pick/revert, index-lock, recovery, or overlapping mutable
  lane state before selection or executable mutation.
- Refresh all named path/import consumers, modes, hashes, Make/static/coverage
  wiring, artifact evidence, and active documentation from the frozen parent.
- Establish identical-input pre-move baselines for direct producer,
  validator, and mocked scheduler behavior without SLURM submission, production
  inputs, dependency installation, or dependency restoration.
- Extend the validator baseline to one full non-repository-CWD dry-run and
  execute/repeat journey with identical explicit inputs, comparing streams,
  exits, report bytes, and invocation-directory residue before and after the
  move. Extend scheduler baselines as isolated fresh-fixture scenarios so prior
  success artifacts cannot mask failure timing or residue.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `00b`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `convert_GTF_to_BED12` contract; the functional-
  owner inventory; `TEST_BASELINE.md`; and the Step `00b` troubleshooting route.
- The producer, validator, scheduler job, both direct test modules, the Step
  `00b` behavior case in `test_slurm_wrapper_contracts.py`, public-CLI and
  validator-roster suites, and the validation-report loader/fault matrix.
- `STEP_PRODUCERS["00b"]` and its artifact-provenance consumers; coverage
  config/tool/tests/baseline; Make static/smoke/shell-test recipes; and the
  literal Make-expansion fixture.
- All nonhistorical Markdown links and supported commands naming the producer,
  validator, scheduler job, or focused tests. No config, public schema, report
  template, or scientific consumer currently names a source path; their BED12
  artifact identities and contents remain unchanged.

## Questions owned by this card

- None.

## In scope

- Freeze the exact direct import/invocation graph, paths, modes, hashes,
  contract defects, parity rows, coverage counts, and rollback evidence before
  source mutation.
- Move the producer, validator, and scheduler entry point once to the final
  owner; update only the scheduler's delegated producer path and the validator's
  owner-relative neutral-library lookup while retaining the sibling producer
  import and all public behavior.
- Move the two direct tests and Step `00b`-specific mocked scheduler behavior/
  fakes to the mirrored owner home. Keep independent cross-owner inventory,
  directive, mode, CLI, roster, loader, artifact, Make, and coverage suites as
  explicit path-aware consumers.
- In the shared validation-report tests, exact-load and path-validate the final
  sibling producer before the moved validator without mutating `sys.path`.
  Rebuild copied Step `00b` fault fixtures at their actual final paths with the
  sibling producer present, so tests do not exercise a flattened topology that
  production will not have.
- Cut over every named repository caller in the same atomic executable/test
  commit, including Make/static/smoke, literal expansions, artifact provenance,
  public CLI, SLURM roster, validator roster, shared loader, direct tests,
  required-subprocess coverage, and tracked coverage rows.
- Extend old/new parity where reviews find a missing named behavior. Measure
  coverage before using the reviewed baseline-update command, then run the
  exact coverage check and one de-duplicated complete applicable local gate.
- Replace the monolithic Step `00b` mocked-job case with owner-local isolated
  scenarios for success; missing submit directory; colliding output paths;
  missing GTF; nonexecutable Python; module-load failure; converter failure;
  bedtools failure; and bad-field output. Freeze exact module/tool calls,
  directory creation timing, intermediate/final bytes or absence, redirect-
  created empty final behavior, contradictory field-check stdout, and exits.
  Run the expanded cases against the old path before movement and unchanged at
  the final path except for the intentional delegated producer argument.
- After executable state is fixed, add the owner README and update only impact-
  directed current topology, inventory, test baseline, commands,
  troubleshooting, ownership, roadmap, handoff, lifecycle links, and dated
  audit documentation in a separate commit.
- In that README and the runbook, distinguish repository-root direct and
  exact-interpreter producer commands from arbitrary-CWD absolute-path use;
  give the validator dry-run/execute commands and the exact scheduler
  submission/CWD/override contract. Name silent producer replacement, job
  nontransactional residue, diagnostics, recovery, implementation-provenance
  path transition, local-only evidence ceiling, and the next safe validation
  action. Troubleshooting must name the exact final producer path.

## Out of scope

- Changing GTF parsing, attribute grammar, coordinate conversion, transcript
  grouping, sorting, name construction, warning/skip policy, deterministic BED
  bytes, exit semantics, output-parent creation, or silent replacement.
- Removing the scheduler's second bedtools sort; changing bedtools version,
  environment overrides, `SLURM_SUBMIT_DIR`, implicit execution, directory/log
  creation, intermediate/final paths, field-count check, preview, diagnostics,
  or nontransactional publication and failure residue.
- Making the validator producer-independent; changing its five check IDs,
  ordered report bytes, dry-run/execute behavior, publication/lock/rollback
  semantics, or the neutral validation-report library.
- Moving `construct_FASTA_sidecars`, the RSeQC evidence consumer,
  reference-provenance ownership, artifact-index ownership, another validator,
  another owner, or any scientific/report/schema surface.
- Adding packages, descriptors, schemas, wrappers, symlinks, compatibility
  copies, global path mutation, dependency actions, cluster/production work, or
  unrelated harness redesign.

## Deliverables

- One atomic final-owner/caller/test/harness cutover commit and one separate
  documentation/lifecycle-close commit, both published sequentially.
- Final producer, validator, and job under
  `src/norad/stages/convert_GTF_to_BED12/`; direct and mocked-job behavior tests
  under `tests/stages/convert_GTF_to_BED12/`; no legacy path, wrapper,
  compatibility copy, duplicate implementation, or owner-specific case in the
  cross-owner suite.
- Explicit mixed-layout caller inventories, exact artifact-evidence transition,
  coverage rename accounting, supported final commands, exact searches,
  complete applicable local validation, clean publication/equality, and a
  precise local-only evidence ceiling.

## Acceptance evidence

- Producer parity preserves mode `0755`, shebang/direct and explicit-interpreter
  invocation, help/malformed handling, arbitrary CWD, configurable feature and
  attributes, warnings, skip/failure cases, deterministic sorting/bytes,
  stdout/stderr, output-parent creation, and characterized silent replacement.
- Validator parity preserves mode `0644`, explicit-interpreter and arbitrary-
  CWD behavior, sibling-producer normalization, all arguments, five ordered
  checks, dry-run/execute/repeat effects, streams/exits, deterministic report,
  stable-input recheck, locks, foreign state, rollback, cleanup, and exact
  neutral publication identity without global `sys.path` mutation.
- Shared-loader evidence proves the final validator binds the exact final
  producer file, uses the same neutral report object, preserves `sys.path`, and
  does not accept a foreign cached producer during its test-owned exact-file
  load. The remaining validators and producer imports retain their current
  identities and behavior.
- A full validator dry-run/execute/repeat journey from a non-repository CWD
  preserves stdout/stderr, exit status, deterministic five-row report bytes,
  explicit inputs, no dry-run output, stable repeat replacement, and no
  invocation-directory residue. Shared neutral fault tests remain the owner for
  same-size/restored-mtime, collision, rollback, interruption, cleanup, and lock
  defects; relocation does not bless or repair them.
- Scheduler parity preserves mode `0755`, seven directives, `/usr/bin/env bash`,
  strict mode, required `SLURM_SUBMIT_DIR`, all four environment overrides,
  preflight, directory/log creation timing, tolerant module lists, strict
  bedtools load, exact final producer argument, bedtools sort/redirection,
  field-count diagnostic and exit, summary/preview, child/module failure
  propagation, and existing intermediate/final residue.
- Fresh-fixture fault evidence proves preflight failures precede directory and
  module/tool effects; module failure follows directory creation but precedes
  conversion; converter failure leaves created directories without producer
  outputs; bedtools failure retains the intermediate and leaves the redirect-
  created final at its characterized bytes; and malformed sorted output remains
  published while the awk `END` message still prints its existing success text
  before the job exits nonzero. These defects are characterized, not approved.
- Artifact evidence records the final producer path with unchanged producer
  bytes SHA-256
  `5c69dabba9139598a9c67331b3200b8db8a29793334ff80f19850eb37ad57a04`.
  Public artifact IDs, BED12/validation schemas, contents, ordering, and report
  consumers remain unchanged.
- Coverage moves producer `151/167` lines and `44/56` branches and validator
  `127/140` lines and `29/36` branches to final paths, preserves required
  subprocess tracing for the producer, and does not decrease global exact
  `9343/11506` line or `3281/4698` branch totals/rates across the reviewed
  baseline transition.
- Exact searches find no live legacy source/test/job path, undeclared caller,
  duplicate basename, wrapper, package marker, stage-to-stage import, stale
  command, or stale active link. Final owner tests and independent caller
  suites pass without weakening exact inventories.
- The runbook contains complete final producer direct/exact-interpreter,
  validator dry-run/execute, exact `sbatch`, and three-suite focused-test
  commands; it does not present a bare file path as an invocation. The owner
  README preserves repository-root versus arbitrary-CWD guidance and makes the
  no-dry-run, replacement, scheduler-residue, recovery, provenance, and
  local-only evidence boundaries findable. Troubleshooting names the exact
  final producer.
- `validation-static` and `smoke` continue syntax-checking the moved job by its
  exact path, `compileall` continues covering both moved Python files through
  `src/norad`, `shell-test` names the final validator test, and the literal Make
  oracle records those expansions exactly.
- The accepted job diff changes its delegated producer path and nothing else;
  the original job hash remains rollback evidence rather than an impossible
  final-byte invariant. The producer itself remains byte-identical so artifact
  implementation evidence retains its frozen source hash.
- The complete applicable computational gate runs on final executable state.
  After documentation close, the documentation gate has no migration-caused
  finding. Any inherited nonpassing condition is recorded exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` only where mixed
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `00b`
  commands in `RUNBOOK.md`; the Step `00b` troubleshooting source path; this
  card; review lifecycle links; and the dated refactor log. Update diagrams only
  if final inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unknown or unmovable caller, required permanent wrapper, public
  package/import decision, cross-owner implementation import, changed BED12 or
  scheduler behavior, artifact/schema change beyond the recorded source path,
  parity that requires blessing a defect, missing high-risk oracle, required
  dependency action, cluster/production action, or scope that cannot remain one
  functional owner plus directly required evidence wiring.

## Completion record

Selected and task-specific read-only execution planning complete after all
three reviews. The selected parent `28acbbb` was clean, published, and
local/upstream-equal; the frozen campaign rollback parent remains
`1b82e4f04b926ac12e6306e40d03fee7840f3fa6`. Old-path characterization and
coverage are recorded below. No executable or test path has moved. The next
agent begins with the atomic cutover in the exact write set below, only after
proving the commit containing this plan is clean, published, and upstream-equal.

### Task-specific execution plan and frozen old-path baseline

Planning was completed on clean, published, local/upstream-equal selection tip
`28acbbb871fd77815ea03d1631ff7462dbe50c2f`. Git showed no merge, rebase,
cherry-pick, revert, index-lock, or recovery state and no overlapping mutable
lane. Execution has not begun.

The exact executable/test cutover write set is:

- move `scripts/gtf_to_bed12.py`, `scripts/validate_step_00b_bed12.py`, and
  `jobs/step_00b_gtf_to_bed12.slurm` without basename changes into
  `src/norad/stages/convert_GTF_to_BED12/`;
- move `tests/test_gtf_to_bed12.py` and
  `tests/test_validate_step_00b_bed12.py` into
  `tests/stages/convert_GTF_to_BED12/`, and add owner-local
  `test_step_00b_gtf_to_bed12.py` with the frozen isolated scheduler matrix;
- change only the job's delegated producer argument, and change only the moved
  validator's neutral-owner lookup to `parents[2] / "libraries"` while keeping
  its literal sibling `import gtf_to_bed12`;
- update explicit path consumers in `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_public_cli_contracts.py`, `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/test_artifact_adapters.py`, `tests/test_python_coverage_baseline.py`,
  `tests/tools/python_coverage_baseline.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`;
- remove only the Step `00b` fake setup and reused-state behavior case from the
  cross-owner SLURM suite. Keep its exact path map, semantic contract, directive,
  mode, inventory, and generic scheduler assertions, pointed to the final job;
  and
- make no `.coveragerc`, package-marker, wrapper, compatibility-copy, descriptor,
  schema, unrelated owner, or documentation change in the executable commit.

Execute that cutover atomically, then run the moved owner tests first. Prove the
shared validator loader exact-loads and path-validates the final sibling producer
without `sys.path` mutation or a foreign cache, and make copied Step `00b`
neutral-owner fault layouts include the sibling producer. Update the artifact
adapter assertion to require the final producer path and unchanged producer
SHA-256. Run a reviewed final-path coverage measurement before updating the
snapshot, then the coverage check and one de-duplicated complete applicable
local gate. Only after the executable checkpoint is committed, published, and
upstream-equal may the impact-directed documentation/lifecycle close begin.

Frozen old-path evidence on `28acbbb`:

- modes, byte hashes, and line counts match the fixed decisions: producer
  `0755`, SHA-256 `5c69dabba9139598a9c67331b3200b8db8a29793334ff80f19850eb37ad57a04`,
  341 lines; validator `0644`, SHA-256
  `e7f2caac22bf461374e23c18dd3a92c9c61456422b0fcf960b52aa7b7076d97d`,
  226 lines; and job `0755`, SHA-256
  `7eb6b3f904daa7ec6cb74f7a55377d0be1aa485b2c80cdd1464d025f9129414f`,
  121 lines;
- the eight existing focused and cross-owner modules passed `566` tests in
  `62.90s`;
- a temporary out-of-tree harness passed all `11` independent cases in `1.81s`:
  direct/exact-interpreter producer parity, non-repository-CWD validator dry-
  run/execute/repeat parity, and nine fresh scheduler fixtures for success plus
  the eight named failure/residue states;
- the unmodified full coverage invocation executed `1,079` tests and ended with
  exactly `1` expected inherited documentation-validator failure, `1,061`
  passes, and `17` skips. A second measurement ran the same failing test body
  under one temporary strict expected-failure marker, yielding `1,061` passes,
  `17` skips, and `1` xfail; coverage comparison passed. This does not make the
  documentation gate pass;
- measured coverage retains producer `151/167` lines and `44/56` branches and
  validator `127/140` lines and `29/36` branches. Current global measurement is
  `9472/11506` lines and `3353/4698` branches (`0.823223`/`0.713708`), above the
  committed `9343/11506` and `3281/4698` baseline; and
- the documentation gate still reports exactly the nine authorized inherited
  `invalid card location` findings under `docs/tasks/UNREFINED/` and no
  migration-caused finding.
