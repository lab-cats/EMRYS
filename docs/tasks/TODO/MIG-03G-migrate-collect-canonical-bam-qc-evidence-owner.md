# MIG-03G — Migrate the collect-canonical-BAM-QC-evidence owner

## Objective

Move the complete `collect_canonical_BAM_QC_evidence` producer, validator,
scheduler asset, and owner-local tests to their frozen final evidence-owner
homes while preserving every public, serialization, scheduler, validation,
artifact, coverage, and non-gating evidence contract.

## Why this exists

After `MIG-03F`, three owners are supported by the live semantic DAG:
`collect_canonical_BAM_QC_evidence`,
`collect_RSeQC_paired_orientation_evidence`, and
`mark_BAM_duplicates_with_Picard`. This card selects none of them yet. It
defines only the first eligible identity in the canonical stage map,
historical Step `02b`, as the smallest next JIT unit. Its sole hard predecessor,
`construct_canonical_BAM`, is migrated. The other two eligible owners remain
uncreated and unselected.

## Fixed decisions

- Frozen definition parent and rollback target:
  `543eb8fe28385f5da077ca45c2d35d17fd5bc7c6`, the clean, published,
  local/upstream/live-remote-equal `MIG-03F` documentation close on the one
  active campaign branch.
- Semantic identity is `collect_canonical_BAM_QC_evidence`, kind `evidence`,
  machine key `norad.evidence.collect_canonical_BAM_QC_evidence.v1`, historical
  alias `02b`, final source home
  `src/norad/evidence/collect_canonical_BAM_QC_evidence/`, and mirrored test
  home `tests/evidence/collect_canonical_BAM_QC_evidence/`.
- Move the mode-`0755` producer `scripts/step_02b_bam_qc.sh`, mode-`0644`
  validator `scripts/validate_step_02b_bam_qc.py`, and intentionally
  mode-`0644` scheduler entry point `jobs/step_02b_bam_qc.slurm` without
  changing their basenames or modes.
- Move only the mode-`0755` direct shell test
  `tests/shell/test_step_02b_bam_qc.sh` and mode-`0644` direct validator test
  `tests/test_validate_step_02b_bam_qc.py` to the mirrored evidence-owner test
  home. Keep scheduler behavior in the independent central wrapper suite.
- The three native assets total `13,045` bytes and `436` lines. Frozen hashes
  are producer
  `642210134e4ad3e5d7b4b2b3989e3d14c87bd4997dc04bbff4865c056798509c`,
  validator
  `b1f5ff7bd574d227ec8cbf7f06f0369a4543582ef9ee46011280ba5eaf222748`,
  and job
  `44e1573b049247fc48c07c799dfc8d9d5b32b9fa746daef23094240746e2932b`.
  Direct-test rollback hashes are shell
  `7fa961166c7da085ca87d2b60c5786fedb3f7b64f40636f565d2cfa2600a5a99`
  and validator
  `1386a416ba7bb607a4b7a0ab305981363c548bb879202c819b6b27a4eead0e07`.
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
- Freeze each moved file's only path adjustment. The producer changes its usage
  self-path to
  `src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh`;
  the validator resolves the neutral report from `Path(__file__).parents[4]`;
  the job delegates to the final producer path; the moved shell test resolves
  the repository root through `SCRIPT_DIR/../../..` and the final producer; and
  the moved Python test resolves `ROOT` through `parents[3]` and the final
  validator. No other moved-file edit is architecture-authorized.
- Production bytes may change only for the producer help self-path, validator
  exact neutral-report depth, and scheduler child path. The reviewed projected
  producer hash after only its help change is
  `92895b2dbd1117e72703e8261a66ce1a7cc34db6000280e23753cd5f9132101c`.
  Any semantic producer, validator, or scheduler edit requires an explicit
  review finding before mutation.
- Preserve the producer's CLI, PATH-only samtools resolution, dry-run default,
  output-directory creation before mode dispatch, adjacent-index admission,
  command construction, direct-final writes, exact empty-success marker,
  nonempty zero-exit quickcheck stream, failure diagnostics, native flagstat
  bytes, streams, exits, and silent replacement.
- Preserve rather than approve the producer's nontransactional evidence-pair
  behavior. There is no lock, stage, stable-input recheck, no-clobber rule,
  rollback, receipt, or set validation. Quickcheck or flagstat faults can leave
  partial or mixed-attempt final files, including when predecessors already
  exist. Reliability review owns the exact safe old/final-path fault oracles
  and evidence-preservation response; it may not repair the behavior.
- Before movement, publish one test-only old-path baseline limited to
  `tests/shell/test_step_02b_bam_qc.sh`,
  `tests/test_validate_step_02b_bam_qc.py`, and
  `tests/test_slurm_wrapper_contracts.py`. No production, harness, fixture,
  coverage-baseline, or documentation file belongs in that checkpoint.
- The shell baseline must freeze two predecessor-bearing faults with separated
  stdout/stderr and exact statuses. Quickcheck exit `42` is normalized by the
  producer to exit `1`, replaces the quickcheck predecessor with the combined
  child diagnostic, and leaves the prior flagstat and unrelated file byte-
  exact. Flagstat exit `43` follows a new exact quickcheck PASS marker, replaces
  the flagstat predecessor with partial child stdout, exposes the child
  diagnostic on stderr, and preserves the unrelated file. Both cases retain
  the output directory and prove there is no lock, staging, backup, receipt, or
  recovery artifact; these are characterized defects, not approved behavior.
- The shell baseline also freezes the PATH-only missing-samtools failure before
  output-directory creation. The validator baseline adds the explicit producer-
  successful nonempty quickcheck marker as failed validation evidence; one
  arbitrary-CWD dry-run/execute/repeat journey with exact input and report
  bytes; and one post-build input mutation that exits `2` while preserving a
  valid prior report. Shared report-publication faults remain in the neutral
  suite rather than being duplicated.
- The scheduler baseline adds one Step `02b`-specific stale-predecessor case:
  an exit-`0` child that emits no outputs still lets the wrapper succeed when
  both named final files already exist, and their stale bytes remain unchanged.
  Preserve this file-existence-only false success without blessing or repairing
  it.
- Preserve the producer/validator mismatch: a nonempty zero-exit quickcheck
  stream is successful producer output but failed validator evidence. Preserve
  the unused and shallow BAI admission requirement, sample/path nonbinding,
  five check IDs, exact report bytes, dry-run/execute behavior, stable-input
  recheck, publication behavior, and zero-count acceptance.
- The validator continues to exact-load neutral
  `src/norad/libraries/validation_report.py` through its private caller-local
  bridge. Change only the final-depth resolution; add no package identity,
  wrapper, import alias, `PYTHONPATH`, or new shared helper.
- Preserve scheduler mode/directives, required `SLURM_SUBMIT_DIR` and `cd`,
  exported `/tmp`, strict samtools `1.19.2` load, tolerated `module list`,
  defaults, dry-run directory creation, `EXECUTE` mapping, exact child path,
  streams/exits, file-existence-only post-checks, and Bash `3.2` empty-array
  dry-run defect.
- `STEP_PRODUCERS["02b"]` changes only to the final producer path. Preserve
  artifact status, evidence ID, Git projection, public artifact identities,
  schemas, contents, ordering, reconciliation, and consumers; add an exact
  final producer path/hash assertion to the existing migrated-implementation
  evidence test.
- Frozen starting coverage is validator `102/110` covered lines and `23/30`
  branches with global `9504/11677` lines and `3327/4756` branches. Final
  measurement must retain the validator's line and branch rates, keep every
  non-target row exact, and preserve the global covered-count floors before the
  committed row moves to its final path.
- Once both shell assets leave flat wildcards, add their exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move direct shell and
  validator recipes; keep public CLI, SLURM, validation, artifact, and coverage
  maps explicit rather than introducing recursive discovery.
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
  boundary, then batch canonical paths, commands, small documentation updates,
  lifecycle repair, and audit evidence in a separate close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  producer/validator/scheduler root and arbitrary-CWD journeys, truthful dry-run
  directory effects, mixed-attempt evidence preservation, non-gating evidence
  semantics, focused tests, implementation provenance, rollback, and the local-
  only evidence ceiling.
- `RUNBOOK.md` owns the complete final commands: repository-root direct and
  explicit-Bash producer dry-run/execute, absolute-path arbitrary-CWD producer,
  explicit-interpreter validator dry-run/execute/repeat and absolute-CWD use,
  final focused tests, and checkout-root `sbatch`. Every producer journey names
  sample, BAM, and output directory; samtools remains PATH-only; dry-run still
  creates the output directory.
- Scheduler guidance must expose defaults plus `SAMPLE_ID`, `BAM`,
  `OUTPUT_DIR`, and `EXECUTE`; required `SLURM_SUBMIT_DIR`; forced `/tmp`;
  strict samtools `1.19.2` loading; tolerated module-list diagnostics; the Bash
  `3.2` dry-run defect; and file-existence-only postchecks. Never equate wrapper
  exit `0` with fresh evidence because two stale named files can satisfy it.
- `TROUBLESHOOTING.md` owns separate final-path PATH and partial/mixed-attempt
  routes. Preserve both evidence files, unrelated files, producer/job streams,
  and exact path state. Do not authorize deletion, recombination, or same-name
  retry until ownership and attempt provenance are established; there is no
  lock, receipt, recovery token, or automatic rollback to inspect.
- Documentation must state that producer exit `0` does not imply validator
  pass, validator exit `0` can publish failed evidence rows, and Step `02b`
  remains non-gating. Artifact provenance changes only to the reviewed final
  producer path/hash; local fixture/mock parity is not real samtools, scheduler,
  cluster, production, scientific-review, or biological evidence.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction, receipt, recovery marker, scheduler abstraction,
  manifest policy, or public library API.
- Roll back the documentation close first, the final owner/caller/coverage
  cutover second, and the old-path test-baseline checkpoint third before
  returning to the frozen parent. Keep Make and its literal oracle together and
  artifact producer path/hash plus its assertion together during rollback.

## Blocked by

- [REVIEW-UX-03G](../COMPLETED/REVIEW-UX-03G-review-collect-canonical-bam-qc-evidence-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal,
  live-remote-equal, and free of recovery, index-lock, or overlapping mutable-
  lane state before selection or executable mutation.
- Refresh only the named native assets, explicit path consumers, modes, hashes,
  artifact evidence, coverage row, active documentation, and applicable Step
  `02b` failure states.
- Establish identical-input old-path baselines without real samtools, scheduler
  submission, dependency action, production input, scientific review, or
  biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `02b`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated evidence contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Producer, validator, job, two direct tests, central scheduler suite, public
  CLI and roster maps, shared validation-report suite, Make/literal fixture,
  artifact mapping, coverage baseline, and current operator diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact path/
  evidence/test boundaries; reliability owns missing mixed-attempt oracles;
  usability owns final commands, recovery navigation, and non-gating evidence
  language.

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

- Migrating or redesigning Step `03`, Step `04`, or any later owner; changing
  canonical BAM production; altering samtools output; reconciling the producer/
  validator marker mismatch; removing BAI admission; adding transactions,
  receipts, or recovery markers; schema or artifact-identity changes; package/
  descriptor work; dependency installation; or cluster/production execution.

## Deliverables

- One reviewed old-path baseline checkpoint, one exact final-owner/caller/test
  cutover checkpoint, and one separate documentation/lifecycle close,
  sequentially published on the same branch.
- Final native assets under
  `src/norad/evidence/collect_canonical_BAM_QC_evidence/`, direct tests under
  `tests/evidence/collect_canonical_BAM_QC_evidence/`, and no live legacy path,
  duplicate, wrapper, or compatibility owner.
- Exact path/hash artifact transition, coverage accounting, supported commands,
  complete card-boundary validation, and a precise local-only evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI, both BAI names, dry-run directory mutation,
  execute output bytes, empty/nonempty quickcheck success, quickcheck and
  flagstat faults, predecessor/mixed-attempt residue, streams, exits, and
  unrelated-file immunity as required by reliability review.
- Validator parity preserves all arguments, five rows, mismatch evidence,
  dry-run/execute/repeat effects, report bytes, stable-input and publication
  behavior, and arbitrary-CWD use required by usability review.
- Scheduler parity preserves mode, directives, submit-CWD/module/default/
  execute/directory/output behavior, exact final child, streams/exits, and Bash
  `3.2` defect.
- Exact searches find one final owner and no undeclared legacy path, wrapper,
  duplicate, stale command, or stale lifecycle link. Coverage and the complete
  applicable gate satisfy reviewed policy without evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `02b`
  commands in `RUNBOOK.md`; Step `02b` partial/mixed-output and validation routes
  in `TROUBLESHOOTING.md`; this card; review lifecycle links; and the dated
  audit log. Update diagrams only if final inspection finds a material DAG or
  public-flow change.

## Escalation conditions

- Stop for an unmovable caller, required public import/package identity,
  permanent wrapper, second functional-owner migration, artifact/schema change
  beyond implementation path/hash, parity that requires blessing a defect,
  missing high-risk oracle, dependency or cluster/production action, or scope
  that cannot remain this one evidence owner and its direct evidence wiring.

## Completion record

Not selected. Defined from clean, published, local/upstream/live-remote-equal
`MIG-03F` documentation checkpoint `543eb8f`. All three dedicated reviews are
complete; no executable/test path changed, no computational test ran, and no
later owner is preloaded.
