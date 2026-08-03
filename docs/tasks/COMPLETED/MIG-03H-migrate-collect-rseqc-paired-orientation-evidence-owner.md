# MIG-03H — Migrate the collect-RSeQC-paired-orientation-evidence owner

## Objective

Move the complete `collect_RSeQC_paired_orientation_evidence` producer,
validator, scheduler asset, and owner-local tests to their frozen final
evidence-owner homes while preserving every public, serialization, scheduler,
validation, artifact, coverage, and non-gating scientific-evidence contract.

## Why this exists

After `MIG-03G`, two owners are supported by the live semantic DAG:
`collect_RSeQC_paired_orientation_evidence` and
`mark_BAM_duplicates_with_Picard`. This card selects neither. It defines only
the first eligible identity in the canonical stage map, historical Step `03`,
as the smallest next JIT unit. Its two hard predecessors,
`construct_canonical_BAM` and `convert_GTF_to_BED12`, are migrated. The other
eligible owner remains uncreated and unselected.

## Fixed decisions

- Frozen definition parent and rollback target:
  `eafec29c1aaddf30c87cb9139897de81883af123`, the clean, published,
  local/upstream/live-remote-equal `MIG-03G` documentation close on the one
  active campaign branch.
- Semantic identity is `collect_RSeQC_paired_orientation_evidence`, kind
  `evidence`, machine key
  `norad.evidence.collect_RSeQC_paired_orientation_evidence.v1`, historical
  alias `03`, final source home
  `src/norad/evidence/collect_RSeQC_paired_orientation_evidence/`, and mirrored
  test home `tests/evidence/collect_RSeQC_paired_orientation_evidence/`.
- Move the mode-`0644` Bash producer
  `scripts/step_03_infer_strandedness_and_orientation.sh`, mode-`0644`
  validator `scripts/validate_step_03_rseqc_orientation.py`, and mode-`0644`
  scheduler entry point `jobs/step_03_infer_strandedness_and_orientation.slurm`
  without changing their basenames or modes. The producer and job remain
  interpreter/submission surfaces, not direct executable files.
- Move only the mode-`0644` direct shell test
  `tests/shell/test_step_03_infer_strandedness_and_orientation.sh` and
  mode-`0644` direct validator test
  `tests/test_validate_step_03_rseqc_orientation.py` to the mirrored evidence
  test home. Keep scheduler behavior in the independent central wrapper suite.
- The three native assets total `17,760` bytes and `515` lines. Frozen hashes
  are producer
  `9bcb3ddfa2c62a3666195a2949af5cfa57582a6fdeb1492586dccccdc1ca5948`,
  validator
  `b4ade297afb85e917b0be130b37dacbe38cb1d0b62e9ce688f82d7ab19edd862`,
  and job
  `d1a21a635531794c29b87b5f47301459b4531297803c1ad245b31a3cb318ee9e`.
  Direct-test rollback hashes are shell
  `f4337355c08f4e6a0601d33edb91f16e26e51bf0ea70f28674d27b38cf0872bb`
  and validator
  `152447fbd85c8122f360373273d8fe1b99aff3139a325d6c16d615ca414c596a`.
- Architecture-reviewed owner cutover is exactly five moves plus nine explicit
  updates:
  `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`. This is a
  fourteen-logical-file ceiling. A sixth move or tenth update reopens
  architecture review.
- Freeze each moved file's path-only adjustments. The producer changes its
  usage self-path to
  `src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh`;
  the validator resolves the neutral report from `Path(__file__).parents[4]`;
  the job delegates to the final producer path; and the moved shell test
  resolves the repository root through `SCRIPT_DIR/../../..` and the final
  producer. The moved Python test resolves `ROOT` through `parents[3]`, uses the
  final validator, and exact-loads unchanged
  `tests/validation_roster_expectations.py` by repository path within that same
  test because its direct flat-test import will not resolve from the deeper
  owner home. This creates no package, `PYTHONPATH`, new logical file, or
  production change. No other moved-file edit is architecture-authorized.
- Production bytes may change only for the producer usage self-path, validator
  exact neutral-report depth, and scheduler child path. The projected producer
  hash after only its usage-path change is
  `01aa11cc60d9042ac541cfe445aec3e562a198a761c45449e82e96b7b9ab0784`.
  Any semantic producer, validator, or scheduler edit requires an explicit
  review finding before mutation.
- Preserve the producer CLI, Bash-only invocation, both BAI-name admissions,
  explicit BAM/BED12/output/sample inputs, path-or-command RSeQC selection,
  CWD-relative `.venv` preference, PATH fallback, side-effect-free dry-run,
  exact `-r`/`-i` order, execute-only directory creation, direct-final stdout
  redirect, nonempty-only success check, preview, streams, exits, and silent
  replacement.
- Preserve rather than approve direct-final report behavior. There is no lock,
  staging path, no-clobber rule, stable-input recheck, receipt, or rollback.
  RSeQC failure or empty success can truncate a predecessor or leave partial
  final bytes. Reliability review owns exact safe old/final-path predecessor
  and residue oracles; it may not repair the behavior.
- Before movement, publish one test-only old-path baseline limited to
  `tests/shell/test_step_03_infer_strandedness_and_orientation.sh`,
  `tests/test_validate_step_03_rseqc_orientation.py`, and
  `tests/test_slurm_wrapper_contracts.py`. No production, fixture, coverage-
  baseline, documentation, or later-owner file belongs in that checkpoint.
- The shell baseline must freeze two predecessor-bearing faults with separated
  stdout/stderr and exact statuses. RSeQC partial stdout followed by child exit
  `42` propagates `42`, replaces the predecessor with only partial child bytes,
  exposes the child diagnostic on stderr, and preserves an unrelated file. An
  exit-`0` empty result makes the producer exit `1`, truncates the predecessor
  to zero bytes, emits the exact producer diagnostic, and preserves the
  unrelated file. Both retain the output directory and prove there is no lock,
  stage, backup, receipt, or recovery artifact; these are characterized
  defects, not approved behavior.
- The shell baseline also freezes a nonempty structurally malformed RSeQC
  report as producer success and one explicit-binary arbitrary-CWD journey.
  The validator baseline turns that readable malformed report into published
  failed evidence, adds arbitrary-CWD dry-run/execute/repeat with exact input
  and report bytes, and adds post-build input mutation that exits `2` while
  preserving a valid prior report. Shared report-publication faults remain in
  the neutral suite rather than being duplicated.
- The scheduler baseline adds Step `03`-specific default-selection and stale-
  predecessor coverage. Without `INFER_EXPERIMENT_BIN`, a repository `.venv`
  executable is preferred and its activation is sourced; without that file,
  the command name is delegated through PATH. Dry-run creates `logs/` but no
  scientific output. In execute mode, an exit-`0` child that emits nothing can
  still succeed when the named final report is already nonempty; its stale
  bytes remain unchanged. Preserve these states without blessing or repairing
  them.
- Preserve the producer/validator boundary: producer nonempty success does not
  prove the three required fractions, and validator exit `0` may publish failed
  rows. Preserve the unused shallow BAI admission, sample/input nonbinding,
  ignored unrecognized lines, three exact labels, five check IDs, tolerance
  range/default, exact report bytes, dry-run/execute behavior, stable-input
  recheck, publication behavior, and mechanical-orientation-only meaning.
- The validator continues to exact-load neutral
  `src/norad/libraries/validation_report.py` through its private caller-local
  bridge. Change only final-depth resolution; add no package identity, wrapper,
  import alias, `PYTHONPATH`, or new shared helper.
- Preserve scheduler mode/directives, submit-directory fallback, exported
  `/tmp`, defaults, optional repository virtual-environment activation,
  `.venv`/PATH RSeQC selection, tolerated `module list`, dry-run log-directory
  creation, `EXECUTE` mapping, exact child path, streams/exits, nonempty-file
  post-check, and Bash `3.2` empty-array dry-run defect.
- `STEP_PRODUCERS["03"]` changes only to the final producer path. Preserve
  artifact status, evidence ID, Git projection, public artifact identities,
  schemas, contents, ordering, reconciliation, consumers, and scientific
  interpretation; add an exact final producer path/hash assertion to the
  existing migrated-implementation evidence test.
- Frozen starting coverage is validator `100/115` covered lines and `25/34`
  branches with global `9505/11677` lines and `3328/4756` branches. Final
  measurement must retain the validator line and branch rates, keep every
  non-target row exact, and preserve global covered-count floors before the
  committed row moves to its final path.
- Once both shell assets leave flat wildcards, add their exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move direct shell and
  validator recipes plus both Step `03` demo-job paths; keep public CLI, SLURM,
  validation, artifact, and coverage maps explicit rather than introducing
  recursive discovery.
- Direct shell and validator tests move with the evidence owner. Central public
  CLI, scheduler, validation-roster, validation-report, artifact, coverage, and
  Make suites remain independent cross-owner consumers; no test framework or
  contract is duplicated under the owner.
- All known executable callers are repository-owned and fit the same atomic
  cutover, so no legacy wrapper, alias, symlink, or compatibility path is
  warranted. Documentation paths are deferred to the separate close and do not
  justify an executable compatibility owner.
- Run only minimal old/final focused checks inside executable slices. Run the
  full applicable computational gate once at the assembled executable card
  boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  producer/validator/scheduler root and arbitrary-CWD journeys, truthful dry-run
  effects, tool-selection ambiguity, partial/stale evidence preservation,
  non-gating mechanical-orientation semantics, focused tests, provenance,
  rollback, and the local-only evidence ceiling.
- At documentation close, the repository-root producer forms must use
  `bash src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.sh`
  with explicit sample, BAM, BED12, output directory, and selected RSeQC
  binary. The arbitrary-CWD form must use absolute producer, BAM, BED12,
  output, and `--infer-experiment-bin` paths; do not imply that the CWD-relative
  `.venv` preference follows the checkout from another directory. State that
  dry-run validates inputs and the executable without creating the output
  directory or native report.
- Route validator dry-run, execute, repeat, and arbitrary-CWD forms through an
  explicit interpreter and the final validator path. Create its output parent
  before execute. Preserve the distinction between exit `0` with rendered or
  published failed rows and exit `2` with no new publication, including stable-
  input recheck behavior and prior valid-report preservation.
- Route scheduler submission from the checkout through final
  `src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.slurm`.
  Document `SLURM_SUBMIT_DIR`, exported `/tmp`, all six public overrides,
  optional virtual-environment activation, `.venv` preference/PATH fallback,
  tolerated module listing, dry-run `logs/` mutation, Bash `3.2` dry-run
  failure, and stale-nonempty-report false success. The two Make demo targets
  use local mocks and may create logs; they are not scheduler or cluster proof.
- Troubleshooting must preserve the native report, unrelated files, producer
  stdout/stderr, scheduler job identity/logs, selected tool/path, BAM/BAI, and
  BED12 before retry or cleanup. It must state that Git rollback does not
  recover runtime evidence and that no lock, stage, backup, receipt, or
  recovery artifact exists. Historical operational observations must remain
  separate from migration evidence and may not turn paired-orientation
  fractions into validated biological strandedness or manifest policy.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction, receipt, recovery marker, scheduler abstraction,
  strandedness classifier, manifest mutation, or public library API.
- Roll back the documentation close first, the final owner/caller/coverage
  cutover second, and the old-path test-baseline checkpoint third before
  returning to the frozen parent. Keep Make and its literal oracle together and
  artifact producer path/hash plus its assertion together during rollback.

## Blocked by

- [REVIEW-UX-03H](../COMPLETED/REVIEW-UX-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal,
  live-remote-equal, and free of recovery, index-lock, or overlapping mutable-
  lane state before selection or executable mutation.
- Refresh only the named native assets, explicit path consumers, modes, hashes,
  artifact evidence, coverage row, active documentation, and applicable Step
  `03` failure states.
- Establish identical-input old-path baselines without real RSeQC, scheduler
  submission, dependency action, production input, scientific review, or
  biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `03`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated evidence contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Producer, validator, job, two direct tests, central scheduler suite, public
  CLI and roster maps, shared validation-report suite, Make/literal fixture,
  artifact mapping, coverage baseline, and current operator diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact path,
  artifact, and test boundaries; reliability owns direct-final/stale-output
  oracles; usability owns final commands, recovery navigation, tool selection,
  and mechanical-orientation evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers, artifacts, defects, parity rows,
  coverage counts, and rollback evidence before mutation.
- Move only this evidence owner and its two direct tests, cut over every
  reviewed explicit caller, and make only reviewed path/depth changes in
  production code.
- Validate executable slices minimally, run the complete applicable gate at the
  card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `04` or any later owner; changing BAM, BED12,
  or RSeQC output; deriving manifest strandedness; biological interpretation;
  adding transactions, receipts, or recovery markers; schema or artifact-
  identity changes; package/descriptor work; dependency installation; or
  cluster/production execution.

## Deliverables

- One reviewed old-path baseline checkpoint, one exact final-owner/caller/test
  cutover checkpoint, and one separate documentation/lifecycle close,
  sequentially published on the same branch.
- Final native assets under
  `src/norad/evidence/collect_RSeQC_paired_orientation_evidence/`, direct tests
  under `tests/evidence/collect_RSeQC_paired_orientation_evidence/`, and no live
  legacy path, duplicate, wrapper, or compatibility owner.
- Exact path/hash artifact transition, coverage accounting, supported commands,
  complete card-boundary validation, and a precise local-only evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, both BAI names, binary selection, side-
  effect-free dry-run, execute output bytes, tool failure, empty/nonempty
  success, predecessor truncation/partial output, streams, exits, and unrelated-
  file immunity as required by reliability review.
- Validator parity preserves all arguments, five rows, malformed-but-nonempty
  producer evidence, dry-run/execute/repeat effects, report bytes, stable-input
  and publication behavior, and arbitrary-CWD use required by usability review.
- Scheduler parity preserves mode, directives, submit-CWD/venv/default/execute/
  directory/output behavior, exact final child, streams/exits, stale-output
  risk, and Bash `3.2` defect.
- Exact searches find one final owner and no undeclared legacy path, wrapper,
  duplicate, stale command, or stale lifecycle link. Coverage and the complete
  applicable gate satisfy reviewed policy without evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `03`
  commands in `RUNBOOK.md`; Step `03` partial/truncated/stale-output, RSeQC-
  selection, validation, and evidence-meaning routes in `TROUBLESHOOTING.md`;
  this card; review lifecycle links; and the dated audit log. Update diagrams
  only if final inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unmovable caller, required public import/package identity,
  permanent wrapper, second functional-owner migration, artifact/schema change
  beyond implementation path/hash, parity that requires blessing a defect,
  missing high-risk oracle, dependency or cluster/production action, or scope
  that cannot remain this one evidence owner and its direct evidence wiring.

## Completion record

Selected from clean, published, local/upstream/live-remote-equal usability-
completion checkpoint `76923e14c3da42b9adacea2bf506f139ecc0b3e8` after all
three reviews closed. This selection changes lifecycle documentation only; no
executable/test path changed, no computational test ran, and no later owner is
preloaded. Task-specific planning is the next bounded slice.

### Task-specific execution plan

Selection checkpoint `13b8a7e0da4c80ef99df1d03c30cbfd3811cd77e` is the
clean, published, local/upstream/live-remote-equal planning parent. Keep the
remaining work to three independently revertible slices and publish/prove each
checkpoint before the next:

1. add and run the exact three-test old-path reliability baseline;
2. apply the atomic five-move/nine-update cutover, run only minimal final-path
   checks, then run the complete applicable computational gate once at the
   assembled executable card boundary and publish the executable checkpoint;
3. batch canonical commands, owner README/contract links, current topology,
   migration links, lifecycle repair, and complete evidence in the separate
   documentation close.

The baseline changes exactly three existing test files and no production,
harness, fixture, coverage-baseline, or documentation file:

- `tests/shell/test_step_03_infer_strandedness_and_orientation.sh` adds exact
  partial-exit-`42` and empty-success predecessor/residue oracles, malformed-
  nonempty producer success, and explicit-binary arbitrary-CWD execution;
- `tests/test_validate_step_03_rseqc_orientation.py` adds malformed producer-
  success validation, arbitrary-CWD dry-run/execute/repeat byte parity, and
  post-build input-mutation/prior-report preservation; and
- `tests/test_slurm_wrapper_contracts.py` adds repository `.venv` preference
  and activation, PATH fallback, dry-run log-only mutation, and stale-report
  false-success assertions for Step `03`.

Run only `bash -n` for the changed shell test, that direct shell test, the
direct Step `03` validator suite, and the central scheduler cases selected by
`step_03_infer_strandedness_and_orientation` at the baseline boundary. Record
the exact test counts, streams, exits, residue, file modes, lines, bytes, and
hashes before movement; do not run coverage or a broad suite in this slice.

The executable cutover is atomic because every known caller is repository-
owned. Move exactly the producer, validator, mode-`0644` job, shell test, and
validator test to their reviewed evidence-owner homes. Update exactly
`Makefile`, `scripts/build_artifact_index.py`,
`tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
`tests/test_slurm_wrapper_contracts.py`,
`tests/test_validation_check_rosters.py`,
`tests/libraries/test_validation_report.py`,
`tests/baselines/python_coverage.json`, and
`tests/fixtures/public_cli_contracts/make_target_expansions.json`. Apply only
the reviewed producer usage path, validator report-owner depth, job child path,
shell-test root/path, and Python-test root/path/exact roster-load adjustments.
No wrapper, alias, duplicate, package, descriptor, schema, transaction,
receipt, recovery marker, dependency action, or documentation path belongs in
this slice.

Before the complete gate, run only final producer/job/shell-test syntax, the
moved direct shell and validator suites, the Step `03` scheduler cases, and the
small explicit inventory/roster/report/artifact/Make path assertions affected
by the cutover. Then measure final Python coverage with only
`tests/git_orchestration/test_validators.py::test_documentation_validator_accepts_repository_from_arbitrary_cwd`
deselected so the intentionally deferred links do not prevent an exact moved-
row measurement. Update only the moved validator row and mechanically changed
global counts, require every non-target row exact, and enforce the frozen rate/
covered-count floors.

Run the canonical RUNBOOK gate once against the assembled executable tree with
`RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks` and an explicit result
JSON under `/private/tmp`. Because documentation is intentionally deferred,
the aggregate may report only the one documentation assertion containing the
ten Step `03` migration-link findings plus nine inherited `UNREFINED` card-
location findings. Report that as an expected-only nonpassing ceiling, never a
green gate. Any other failing test, link count, coverage regression, missing
tool, or lane failure must be understood before the executable commit. Do not
install dependencies or use cluster/production resources.

At documentation close, use the card's canonical roster, add no unrelated
documentation, repair all ten migration links and every inbound lifecycle
link, move this card to `COMPLETED`, and run exactly the RUNBOOK documentation-
only sequence. The accepted close may still report only the nine inherited
`UNREFINED` locations; it must contain no migration-caused finding. Roll back
documentation first, cutover second, and baseline third. Git rollback never
deletes or alters runtime evidence, production data, locks, logs, or recovery
artifacts.

### Completion evidence

- **Old-path reliability baseline:** published checkpoint
  `88f499487ea69fb0b884bec3572af9808912e28a` changed only the three reviewed
  tests. The shell test was mode `0644`, `14,875` bytes, `400` lines, SHA-256
  `82d757100d3e95dbdb92162b9cb5ab926230c48028970a2f631f0213e94725fa`;
  the validator test was mode `0644`, `6,048` bytes, `178` lines, SHA-256
  `2677bce92fcc32fc743fdff98131a4a3669f69a4973e225f08fbb629b459a324`;
  and the central scheduler suite was mode `0644`, `53,153` bytes, `1,564`
  lines, SHA-256
  `de05bb939bbb409956cb0715257b701ee927608399d27bc54ffd37391f5b3d8b`.
  Shell syntax and the complete direct shell suite passed; the validator suite
  passed `8`; and Step `03` scheduler selection passed `8` with `108`
  unrelated cases deselected. The partial exit-`42`, empty exit-`0`, malformed-
  nonempty, arbitrary-CWD, input-mutation, venv/PATH, dry-run-log, and stale-
  output states are characterized defects/evidence boundaries, not approvals.
- **Exact executable cutover:** published checkpoint
  `24ed9b1ec98f63944a963628907a4c310558a420` contains exactly the five reviewed
  moves and nine reviewed caller/harness updates. Final producer mode/bytes/
  lines/SHA-256 is `0644` / `6,857` / `209` /
  `01aa11cc60d9042ac541cfe445aec3e562a198a761c45449e82e96b7b9ab0784`;
  validator is `0644` / `6,888` / `183` /
  `d92eac61eeedec553b2541e446256836406f81c75e5fb8f6b12369f11bf58e67`;
  and the mode-`0644` job is `4,121` bytes / `123` lines /
  `d65fde6e7cb3d0ebccf76cb7101dffaf0ea42edfa49e1387d4cac3c3568d8c08`.
  Final shell test is mode `0644`, `14,931` bytes, `400` lines, SHA-256
  `123d464fa26d623aacacff5a5b7ebb316051bc8f984a26bdff630adeefd2bf80`;
  final validator test is mode `0644`, `6,493` bytes, `189` lines, SHA-256
  `0b1b3802e65309856b5aa04f33682b6f4ce193453dde0a8440d7578cb98734a5`.
  Exact inspection found no live legacy executable/test path, wrapper, alias,
  duplicate, package marker, descriptor, schema, transaction, receipt,
  recovery marker, or later-owner preload.
- **Focused final-path acceptance:** producer, job, and moved-shell-test syntax
  passed; the complete moved shell suite passed; the moved validator passed
  `8`; and the Step `03` scheduler subset passed `8` with `108` deselected.
  The exact artifact final-path/hash assertion passed `1` with `69` deselected;
  public CLI/Make targeting passed `28` with `91` deselected; the complete
  validation-roster suite passed `105`; and targeted shared-report/inventory
  coverage passed `9` with `129` deselected. Those four wiring groups total
  `143` passing assertions.
- **Coverage:** deterministic serial measurement passed `1,120` tests with
  `17` skips and one explicit deselection of only
  `tests/git_orchestration/test_validators.py::test_documentation_validator_accepts_repository_from_arbitrary_cwd`.
  The final validator improved from `100/115` lines and `25/34` branches to
  `103/115` and `28/34`; global coverage improved from `9505/11677` lines and
  `3328/4756` branches to `9508/11677` and `3331/4756`. Every non-target row
  remained exact, the baseline was copied mechanically from the measured
  current snapshot, and the standalone policy comparison passed at line rate
  `0.814250` and branch rate `0.700378` across `32` tracked files.
- **Complete computational gate:** the aggregate was not fully green. The
  first sandboxed attempt passed static preflight, then guarded R stopped on
  Bioconductor DNS while retaining the inherited malformed `macos` warning.
  The exact network-enabled rerun used the existing project library and
  installed, restored, deleted, and updated nothing. Static preflight passed in
  `0.118s`, shell contracts in `116.947s`, guarded R in `432.217s`, and report
  runtime in `325.043s`. Python ran `1,120` passes and `17` skips before its
  sole documentation assertion failed; the aggregate ended at `455.541s`.
  That assertion contained exactly five stale inventory links, five stale
  owner-contract links, and nine inherited `UNREFINED` card-location findings.
  The result JSON is `/private/tmp/norad-mig-03h-validation.json`; the retained
  Python log is
  `/var/folders/y0/bg0yx6g54bs0403dn0x_k28w0000gn/T/norad-validation-python-coverage-gqps7nta.log`.
  This is an expected-only documentation ceiling, not a green gate.
- **Preserved behavior and evidence ceiling:** direct-final partial/empty
  replacement, silent replacement, nonempty malformed success, absence of
  lock/stage/no-clobber/stable-input recheck/receipt/rollback, validator exit
  `0` with failed rows, validator exit `2` without new publication, Bash `3.2`
  dry-run failure, dry-run log mutation, CWD-relative tool selection, and stale-
  report false success remain characterized and unapproved. Fractions remain
  non-gating mechanical paired-read orientations, not transcript strand,
  biological sense/antisense, approved strandedness, or manifest policy. No
  real RSeQC, scheduler, cluster, production, scientific-review, or biological
  evidence was created.
- **Rollback:** revert the documentation/lifecycle close containing this
  record, then executable/test checkpoint `24ed9b1`, then test-only baseline
  `88f4994`; task-specific planning is `3388466`. Keep Make with its literal
  oracle and artifact path/hash with its assertion. Git rollback never deletes,
  restores, or authenticates runtime evidence, production data, locks, logs,
  or recovery artifacts.
- **Documentation/lifecycle close:** added the adjacent owner README, updated
  the owner contract and impact-directed canonical topology/status/test/command/
  troubleshooting owners, repaired the five inventory and five contract links,
  moved this card to `COMPLETED`, and repaired every inbound lifecycle link.
  No diagram changed because implementation placement did not change semantic
  DAG edges or public data flow. `git diff --check` passed. The complete
  documentation validator reported exactly the nine inherited `UNREFINED`
  card-location findings and no migration-caused finding. That remains a
  nonpassing expected-only documentation ceiling, not a green gate. The close
  is the commit containing this record; publish it and prove local/upstream/
  live-remote equality before refreshing the DAG or defining another owner.
