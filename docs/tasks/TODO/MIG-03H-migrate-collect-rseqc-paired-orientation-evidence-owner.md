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
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction, receipt, recovery marker, scheduler abstraction,
  strandedness classifier, manifest mutation, or public library API.
- Roll back the documentation close first, the final owner/caller/coverage
  cutover second, and the old-path test-baseline checkpoint third before
  returning to the frozen parent. Keep Make and its literal oracle together and
  artifact producer path/hash plus its assertion together during rollback.

## Blocked by

- [REVIEW-UX-03H](REVIEW-UX-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

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

Not selected. Defined from clean, published, local/upstream/live-remote-equal
`MIG-03G` documentation checkpoint `eafec29`. `REVIEW-ARCH-03H` and
`REVIEW-REL-03H` are complete; usability remains unselected in `TODO`. No
executable/test path changed, no computational test ran, and no later owner is
preloaded.
