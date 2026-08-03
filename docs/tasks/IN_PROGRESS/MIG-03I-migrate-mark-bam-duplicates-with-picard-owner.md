# MIG-03I — Migrate the mark-BAM-duplicates-with-Picard owner

## Objective

Move the complete `mark_BAM_duplicates_with_Picard` producer, validator,
scheduler asset, and owner-local tests to their frozen final stage-owner homes
while preserving every public, serialization, scheduler, validation, artifact,
coverage, and marked-BAM contract.

## Why this exists

After `MIG-03H`, the refreshed live semantic DAG has exactly one eligible
unmigrated owner: `mark_BAM_duplicates_with_Picard`. Its sole direct artifact
predecessor, `construct_canonical_BAM`, is migrated. Historical Step `05`
remains blocked on this owner, and no Step `05` card is created or selected.
This card defines Step `04` as the smallest next JIT unit but does not select
it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `ef990c892626ba720b79b8998a783cabf2360cab`, the clean, published,
  local/upstream/live-remote-equal `MIG-03H` documentation close on the one
  active campaign branch.
- Semantic identity is `mark_BAM_duplicates_with_Picard`, kind `stage`,
  machine key `norad.stage.mark_BAM_duplicates_with_Picard.v1`, historical
  alias `04`, final source home
  `src/norad/stages/mark_BAM_duplicates_with_Picard/`, and mirrored test home
  `tests/stages/mark_BAM_duplicates_with_Picard/`.
- Move the mode-`0644` Bash producer `scripts/step_04_mark_duplicates.sh`,
  mode-`0644` validator `scripts/validate_step_04_mark_duplicates.py`, and
  mode-`0644` scheduler entry point `jobs/step_04_mark_duplicates.slurm`
  without changing basenames or modes. Producer and job remain interpreter/
  submission surfaces, not directly executable files.
- Move only the mode-`0644` direct shell test
  `tests/shell/test_step_04_mark_duplicates.sh` and mode-`0644` direct
  validator test `tests/test_validate_step_04_mark_duplicates.py` to the
  mirrored stage test home. Keep scheduler behavior in the independent central
  wrapper suite.
- The three native assets total `22,336` bytes and `679` lines. Frozen SHA-256
  values are producer
  `cd1b52c2e2a2ba1a5de93efd1b32c11f753616b28f527567780d42fe5b88aa41`,
  validator
  `8b1a4bf54731281c5636d16a27292589864a446d23e1d3b459043ea30b3152a6`,
  and job
  `c0be74fc58b8ef343aaa48d62f9bc118ea08e652d3f28ba07b3c744295baa684`.
  Direct-test rollback hashes are shell
  `c92426b4e7594795e5f6a3b3f00c1174418aa870b17ffc5d576f0f7bc63283a7`
  and validator
  `e3ed5075abf29b3715b4f2dfa0ecbf95f76f4f079419083dbcd7c9985c4b77d6`.
- Architecture-reviewed owner cutover is exactly five moves plus ten explicit
  updates:
  `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/libraries/test_bam_validation.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`. The BAM-
  helper caller matrix is the Step `04`-specific tenth update. Dedicated
  architecture review confirms this fifteen-logical-file ceiling. An eleventh
  update or sixth move reopens architecture review.
- Production bytes may change only for the producer usage self-path, both
  validator neutral-library root depths, and scheduler child path. The
  projected hashes after only those changes are producer
  `b845aa910ccabaf8799e000dc62e8939b0203c7848511524fadf51c79292eb2d`,
  validator
  `17a541e7b9d9822df5de0721747187621035f0dae7aaa0f1a35995f727bfb178`,
  and job
  `4e41c4cd7ee1ec36169797bfc4897968e38010e78aec35d16c6921dfd55217fc`.
  Any semantic producer, validator, or scheduler edit requires an explicit
  review finding before mutation.
- Freeze each moved file's path-only adjustment. The producer changes only its
  usage self-path; both validator bridges resolve the repository through
  `Path(__file__).parents[4]`; and the job delegates to the final producer. The
  moved shell test resolves the repository root through `SCRIPT_DIR/../../..`
  and the final producer. The moved Python test resolves `ROOT` through
  `parents[3]`, uses the final validator, and exact-loads unchanged
  `tests/validation_roster_expectations.py` by repository path because its flat
  direct import will not resolve from the deeper owner home. This creates no
  package, `PYTHONPATH`, new logical file, or production change. Any other
  moved-file edit reopens architecture review.
- Preserve the producer CLI, Bash-only invocation, exact `<bam>.bai` input,
  explicit output and metrics directories, explicit Picard jar, path-or-command
  Java and samtools selection, caller-owned existing writable `TMPDIR`, side-
  effect-free dry-run, command order, `REMOVE_DUPLICATES=false`, execute-only
  directory creation, direct-final Picard outputs, quickcheck-before-index,
  final nonempty checks, streams, exits, and silent replacement.
- Preserve rather than approve direct-final multi-output behavior. There is no
  lock, staging, no-clobber rule, stable-input recheck, receipt, rollback, or
  all-or-none transaction. Picard, quickcheck, index, or final-check failure can
  leave partial or cross-attempt BAM/BAI/metrics state. Reliability review owns
  safe predecessor-bearing and residue oracles; it may not repair the behavior.
- Reliability review requires exactly three existing old-path test owners,
  published in bounded producer, validator, and scheduler slices. The direct
  shell suite freezes tokenized Picard exit-`42`, quickcheck exit-`43`, index
  exit-`44`, empty-metrics final-check, arbitrary-CWD/tool-admission, and input-
  mutation states with exact new/partial/prior triplet bytes and no recovery
  artifacts. The direct validator suite freezes arbitrary-CWD repeat parity,
  exit-`0` failed evidence, exit-`2` nonpublication, and stable-input failure.
  The central scheduler suite freezes Java-home/PATH/version selection, missing
  `PICARD`, list-only diagnostic tolerance, dry-run logs, stale-three-file false
  success, and the unguarded unset-`JAVA_HOME` abort. These tests characterize;
  they do not bless or repair any defect.
- Preserve the producer/validator boundary: producer success does not parse
  metrics, verify duplicate flags, prove BAM/BAI or metrics/BAM correspondence,
  or bind sample/library/platform/tool identity. Validator exit `0` may publish
  failed rows. Preserve all five check IDs, metrics parsing, container/header/
  quickcheck semantics, stable-input recheck, report bytes, streams, and exits.
- The validator continues to privately exact-load neutral
  `src/norad/libraries/validation_report.py` and
  `src/norad/libraries/bam_validation.py`. Change only final-depth resolution;
  add no package identity, wrapper, import alias, `PYTHONPATH`, or shared-helper
  change.
- Preserve scheduler mode/directives, submit-directory fallback, exported
  `/tmp`, defaults, dry-run `logs/` mutation, strict Picard `3.1.1` and
  samtools `1.19.2` loads, `PICARD` requirement, Java override/`JAVA_HOME`/PATH
  resolution, actual version parsing and Java-17 floor, tolerated `module list`
  diagnostics, execution mapping, child path, streams/exits, three-nonempty-
  file post-check, and Bash `3.2` empty-array dry-run defect. Reliability review
  must explicitly disposition unset-`JAVA_HOME`, stale-output, and child/tool
  selection states without hardening them.
- `STEP_PRODUCERS["04"]` changes only to the final producer path. Preserve
  artifact status, evidence ID, Git projection, four public Step `04` artifact
  identities, schemas, contents, ordering, reconciliation, consumers, and
  scientific meaning; add an exact final producer path/hash assertion to the
  existing migrated-implementation evidence test.
- Frozen starting coverage is validator `144/155` covered lines and `33/42`
  branches with global `9508/11677` lines and `3331/4756` branches. Final
  measurement must retain the validator line and branch rates, keep every non-
  target row exact, and preserve global covered-count floors before the row
  moves to its final path.
- Once producer and job leave flat wildcards, add their exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move direct shell
  and validator recipes. Step `04` has no Make demo target to move. Keep public
  CLI, SLURM, validation, neutral BAM-helper, artifact, and coverage maps
  explicit rather than adding recursive discovery.
- Direct shell and validator tests move with the stage owner. Central public-
  CLI, scheduler, validation-roster, validation-report, neutral BAM-helper,
  artifact, coverage, and Make suites remain independent cross-owner
  consumers. Every known executable caller is repository-owned and fits the
  same atomic cutover, so no legacy wrapper, alias, symlink, or compatibility
  path is warranted. Documentation paths are deferred to the separate close
  and do not justify a compatibility owner.
- Run only minimal old/final focused checks inside executable slices. Run the
  full applicable computational gate once at the assembled executable card
  boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  producer/validator/scheduler root and arbitrary-CWD journeys, truthful dry-
  run effects, Picard/Java/samtools/`TMPDIR` selection, partial/mixed/stale
  output preservation, focused tests, provenance, rollback, and the local-only
  evidence ceiling.
- Usability review freezes those journeys as explicit-path surfaces. Root use
  invokes the mode-`0644` producer through Bash, the mode-`0644` validator
  through an explicit Python interpreter, and the mode-`0644` job through
  `sbatch` after creating `logs/`; arbitrary-CWD use makes every executable,
  input, output, metrics, jar, and temp path absolute. The docs must distinguish
  producer no-write dry-run, validator stdout-only dry-run, and wrapper/log/
  Bash-`3.2` effects; name the unguarded unset-`JAVA_HOME` abort; route isolated
  retry only after preserving the exact triplet and ruling out downstream
  readers; and state that Git rollback cannot recover runtime artifacts.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction, receipt, recovery marker, scheduler abstraction,
  duplicate-classification policy, manifest mutation, or public library API.

## Blocked by

- [REVIEW-UX-03I](../COMPLETED/REVIEW-UX-03I-review-mark-bam-duplicates-with-picard-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of recovery, index-lock, or overlapping mutable-lane state
  before selection or executable mutation.
- Refresh only the named native assets, explicit path consumers, modes, hashes,
  artifact evidence, coverage row, active documentation, and applicable Step
  `04` failure states.
- Establish identical-input old-path baselines without real Picard, samtools,
  Java changes, scheduler submission, dependency action, production input, or
  scientific/biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `04`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated stage contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Producer, validator, job, two direct tests, central scheduler suite, neutral
  validation-report and BAM-helper suites, public CLI/roster maps, Make/literal
  fixture, artifact mapping, coverage baseline, and current Java/Picard/
  samtools diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact paths,
  artifact/helper/test boundaries, and cutover ceiling; reliability owns multi-
  output predecessor/residue oracles; usability owns final commands, Java/tool/
  temp selection, recovery navigation, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers, artifacts, defects, parity rows,
  coverage counts, and rollback evidence before mutation.
- Move only this stage owner and its two direct tests, cut over every reviewed
  explicit caller, and make only reviewed path/depth changes in production.
- Validate executable slices minimally, run the complete applicable gate at the
  card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `05` or any later owner; changing BAM, BAI,
  metrics, duplicate marking, Java/Picard/samtools policy, or scheduler
  hardening; adding transactions/receipts/recovery; artifact/schema changes;
  package/descriptor work; dependency installation; or cluster/production
  execution.

## Deliverables

- One assembled old-path reliability checkpoint reached through at most three
  small sequential test-only slices, one exact final-owner/caller/test cutover
  checkpoint, and one separate documentation/lifecycle close, sequentially
  published on the same branch.
- Final native assets under
  `src/norad/stages/mark_BAM_duplicates_with_Picard/`, direct tests under
  `tests/stages/mark_BAM_duplicates_with_Picard/`, and no live legacy path,
  duplicate, wrapper, or compatibility owner.
- Exact path/hash artifact transition, coverage accounting, supported commands,
  complete card-boundary validation, and a precise local-only evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, exact BAI admission, Picard/Java/samtools/
  temp selection, side-effect-free dry-run, command order, execute output bytes,
  controlled child failures, predecessor/cross-attempt residue, streams, exits,
  unrelated-file immunity, and absent recovery controls as required by review.
- Validator parity preserves arguments, five rows, metrics and BAM/header
  behavior, dry-run/execute/repeat effects, report bytes, stable-input and
  publication behavior, both neutral loaders, and arbitrary-CWD use.
- Scheduler parity preserves mode, directives, submit CWD, modules, Picard/
  Java/samtools resolution, dry-run logs, Bash `3.2`, delegation, three-output
  checks, streams/exits, and stale-output risk.
- Exact searches find one final owner and no undeclared legacy path, wrapper,
  duplicate, stale command, or lifecycle link. Coverage and the complete gate
  satisfy reviewed policy without evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `04`
  commands in `RUNBOOK.md`; Step `04` partial/mixed/stale-output, Picard/Java/
  samtools/`TMPDIR`, validation, and recovery routes in `TROUBLESHOOTING.md`;
  the impacted `construct_canonical_BAM/README.md` helper/test paths; this card;
  review lifecycle links; and the dated audit log. Update diagrams only if
  final inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unmovable caller, required public import/package identity,
  permanent wrapper, second functional-owner migration, artifact/schema change
  beyond implementation path/hash, parity that requires blessing a defect,
  missing high-risk oracle, dependency or cluster/production action, or scope
  that cannot remain this one stage owner and its direct evidence wiring.

## Completion record

Selected from clean, published, local/upstream/live-remote-equal usability-
completion checkpoint `beee633f6671662cc0cb1d9acdfba82f40cce233` after all
three dedicated reviews completed sequentially. Execution is not started: no
executable/test path changed, no computational test ran, and no Step `05` or
later owner is preloaded.

### Task-specific execution plan

Selection checkpoint `0c883901d1541a6aea1b947bac4cb73a5b02caa5` is the
clean, published, local/upstream/live-remote-equal planning parent. Keep the
remaining work to five bounded, independently revertible slices and publish/
prove each checkpoint before the next:

1. add and run only the old-path direct-producer reliability oracles;
2. add and run only the old-path direct-validator reliability oracles;
3. add and run only the old-path central-scheduler reliability oracles, then
   record the assembled three-test baseline identity;
4. apply the atomic five-move/ten-update cutover, run minimal final-path checks,
   then run the complete applicable computational gate once at the assembled
   executable card boundary and publish the executable checkpoint;
5. batch canonical paths/commands, owner README/contract repair, migration and
   lifecycle links, current status/evidence, and audit proof in the separate
   documentation close.

The first baseline slice changes only
`tests/shell/test_step_04_mark_duplicates.sh`. Add the reviewed tokenized
Picard exit-`42`, quickcheck exit-`43`, index exit-`44`, and empty-metrics final-
check states, plus arbitrary-CWD explicit-tool admission, missing explicit
samtools before directory creation, controlled admitted-input mutation,
unrelated-file preservation, and absence of recovery artifacts. Run only
`bash -n` on that test and the complete direct shell test; record exact
streams, exits, triplet bytes, mode, bytes, lines, and SHA-256. Do not run
Python, scheduler, coverage, or broad gates in this slice.

The second baseline slice changes only
`tests/test_validate_step_04_mark_duplicates.py`. Add arbitrary-CWD dry-run/
execute/repeat byte parity, quickcheck nonzero as exit-`0` failed evidence,
header-tool failure as exit-`2` nonpublication, and post-build input mutation
with predecessor-report preservation. Run only that direct pytest file with
the existing repository interpreter; record exact report effects, mode, bytes,
lines, and SHA-256. Do not run shell, scheduler, coverage, or broad gates.

The third baseline slice changes only `tests/test_slurm_wrapper_contracts.py`.
Add Java-home and PATH fallback, Java `-version` failure, unparseable and
under-17 rejection, missing `PICARD`, list-only module failure tolerance,
dry-run log mutation, stale-three-file false success, and the unguarded unset-
`JAVA_HOME` abort. Run only scheduler cases selected by
`step_04_mark_duplicates`; record exact counts, streams, delegation/output
effects, mode, bytes, lines, and SHA-256. This tip is the assembled old-path
baseline. No fourth test, production, harness, fixture, coverage-baseline,
canonical-documentation, dependency, or later-owner file enters any baseline
slice.

The executable cutover is atomic because all known callers are repository-
owned. Move exactly producer, validator, mode-`0644` job, shell test, and
validator test to their reviewed stage-owner homes. Update exactly `Makefile`,
`scripts/build_artifact_index.py`, `tests/test_artifact_adapters.py`,
`tests/test_public_cli_contracts.py`, `tests/test_slurm_wrapper_contracts.py`,
`tests/test_validation_check_rosters.py`,
`tests/libraries/test_validation_report.py`,
`tests/libraries/test_bam_validation.py`,
`tests/baselines/python_coverage.json`, and
`tests/fixtures/public_cli_contracts/make_target_expansions.json`. Apply only
the reviewed producer usage path, both validator library depths, job child
path, shell-test root/target, Python-test root/target/private roster load,
explicit map paths, artifact path/hash assertion, coverage row, and literal
Make expansion. No wrapper, alias, duplicate, package, descriptor, schema,
transaction, receipt, recovery marker, dependency action, documentation path,
or later owner enters the cutover.

Before the complete gate, run only final producer/job/moved-shell-test syntax;
the moved direct shell and validator suites; the Step `04` scheduler subset;
and the smallest explicit public-CLI/Make, roster/report/BAM-helper, artifact,
and coverage-path assertions affected by the cutover. Then measure final Python
coverage once with only
`tests/git_orchestration/test_validators.py::test_documentation_validator_accepts_repository_from_arbitrary_cwd`
deselected so intentionally deferred documentation does not prevent exact
moved-row accounting. Update only the moved validator row and mechanically
changed global counts, keep every non-target row exact, and enforce the frozen
target rates and covered-count floors.

Run the canonical RUNBOOK aggregate once against the assembled executable tree
with `RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks` and an explicit
result JSON under `/private/tmp`. Canonical documentation is intentionally
deferred, so the aggregate may report only the repository documentation
assertion with the exact Step `04` migration-caused stale paths plus the nine
inherited `UNREFINED` locations. Record the exact list and report this as an
expected-only nonpassing ceiling, never a green gate. Any other failure,
coverage regression, missing tool, or lane fault must be understood before the
executable commit. Do not install dependencies or use scheduler, cluster, or
production resources.

At documentation close, use the full canonical roster, add no unrelated docs,
repair every migration-caused path and inbound lifecycle link, move this card
to `COMPLETED`, and run exactly the RUNBOOK documentation-only sequence. The
accepted close may retain only the nine inherited `UNREFINED` locations and
must contain no migration-caused finding. Roll back documentation first, the
atomic cutover second, then scheduler, validator, and producer baseline slices
in reverse order. Git rollback never deletes or changes runtime evidence,
production data, locks, logs, or recovery artifacts.
