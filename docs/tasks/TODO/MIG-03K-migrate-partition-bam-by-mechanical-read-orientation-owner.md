# MIG-03K — Migrate the partition-BAM-by-mechanical-read-orientation owner

## Objective

Move the complete `partition_BAM_by_mechanical_read_orientation` producer,
validator, scheduler asset, and owner-local tests to their frozen final stage-
owner homes while preserving every public, mechanical-orientation,
transaction, scheduler, validation, artifact, coverage, and BAM-partition
contract.

## Why this exists

After `MIG-03J`, the refreshed live semantic DAG has exactly one eligible
unmigrated owner: `partition_BAM_by_mechanical_read_orientation`. Its sole
direct artifact predecessor, `split_N_cigar_reads_with_GATK`, is migrated.
Historical Step `07` remains blocked on this owner, and no Step `07` card is
created or selected. This card defines Step `06` as the smallest next JIT unit
but does not select it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `db60dfa965f4c878aacfe3221dfc50d30644cb74`, the clean, published,
  local/upstream/live-remote-equal `MIG-03J` documentation close on the one
  active campaign branch.
- Semantic identity is `partition_BAM_by_mechanical_read_orientation`, kind
  `stage`, machine key
  `norad.stage.partition_BAM_by_mechanical_read_orientation.v1`, historical
  alias `06`, final source home
  `src/norad/stages/partition_BAM_by_mechanical_read_orientation/`, and mirrored
  test home
  `tests/stages/partition_BAM_by_mechanical_read_orientation/`.
- Move the mode-`0755` Bash producer
  `scripts/step_06_split_bam_by_read_orientation.sh`, mode-`0644` validator
  `scripts/validate_step_06_orientation_outputs.py`, and mode-`0755` scheduler
  entry point `jobs/step_06_split_bam_by_read_orientation.slurm` without
  changing basenames or modes. Preserve the producer as a directly executable
  and Bash-invocable surface, the validator as an explicit-interpreter
  surface, and the job as an `sbatch` surface.
- Move only the mode-`0755` direct shell test
  `tests/shell/test_step_06_split_bam_by_read_orientation.sh` and mode-`0644`
  direct validator test `tests/test_validate_step_06_orientation_outputs.py`
  to the mirrored stage test home. Keep independent scheduler behavior in the
  central wrapper suite. Delete the obsolete documentation-only scaffold
  `tests/pending/test_step_06_split_bam_by_read_orientation.sh` only in the
  separate documentation close: every one of its four future-test bullets is
  already implemented by the active direct suite, and retaining or moving it
  would create stale duplicate ownership. Its deletion is not a sixth
  executable move or a reliability baseline.
- The three native assets total `37,398` bytes and `1,136` lines. Frozen
  SHA-256 values are producer
  `bb0ebbaea9158c0dfceb3a0cd2e083c99e8f63913859c10df93ec85314de2275`,
  validator
  `7b39b8fc27b9992c8ca4b2b4111e5ae872b15806e520c4ca9d595b81e6cc7c69`,
  and job
  `3c0bf399187cb7624350d9896fd2e0228daaf61a7fa71e89c5ba4ce22b7a1419`.
  Direct-test rollback hashes are shell
  `948d07f6a570b0ae97ee3ae45c6bd04ec8d09eed0de1116b03d92d55c7c62193`
  and validator
  `53ebf9d53b00cf8507835e8cf9f62f8027bd5fe2d73315545c442360389e2f2e`.
- Architecture-reviewed executable cutover is exactly five moves plus nine
  explicit integration
  owners: `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`. Exact
  tracked-path and basename searches prove no tenth integration owner;
  `tests/test_artifact_adapters.py` adds the final Step `06` path/hash assertion
  even though it has no old path literal. A tenth update, sixth executable
  move, or different moved-file edit reopens architecture review.
- Production edits are exactly: replace the producer usage path; change the
  validator repository root from `parents[1]` to `parents[4]` for unchanged
  neutral `src/norad/libraries/validation_report.py`; and replace the scheduler
  child path. The existing private report identity and loader behavior remain
  unchanged and are already covered across every validator by the neutral
  report-loader matrix. No package import, `PYTHONPATH`, helper move, schema
  extraction, or other production edit is permitted.
- Projected final native values after only those reviewed path/root edits are
  producer `24,542` bytes / `784` lines / SHA-256
  `74399ceb42cb081b213256977b03137d7ae8513c07f98fb4cd06b2f7ee6a2730`,
  validator `8,892` bytes / `227` lines / SHA-256
  `96385f8988219a486094c05d490acc8d2b228001d241ee29af784ec269460b33`,
  and job `4,072` bytes / `125` lines / SHA-256
  `fc1ddbce861293fac9dcbd9e87571d8b4f955ae602f4f2daa6afa7908d5251af`.
  Producer and job remain mode `0755`; validator remains mode `0644`. Any
  production hash or mode difference reopens architecture review.
- The moved shell test changes only its repository root to
  `SCRIPT_DIR/../../..` and producer/job targets to final paths before
  reliability additions. The moved Python test changes its root to
  `parents[3]`, targets the final validator, and exact-loads unchanged root
  `tests/validation_roster_expectations.py` through
  `importlib.util.spec_from_file_location` under private test identity
  `partition_bam_by_mechanical_read_orientation_validation_roster_oracle`.
  It validates the spec/loader, binds only `assert_exact_check_roster`, inserts
  no global module or path, and needs no production helper or separate test
  owner.
- Preserve producer CLI/help, exact `<bam>.bai` admission, positive threads,
  samtools argument/override/PATH resolution, execute-only version call,
  side-effect-free dry-run, run-token names, per-sample output-directory lock,
  output/QC directory split, stale owned-path refusal, staged filters/merges/
  indexes/counts, temporary validation, all-five-or-none predecessor rule,
  sequential publication with counts last, final revalidation, streams, exits,
  replacement, cleanup, and signal traps.
- Preserve exact mechanical groups: `FWD_like` is `-f 99` plus `-f 147` and
  `REV_like` is `-f 83` plus `-f 163`; `-f` permits additional bits.
  Preserve non-exhaustive assignment and never promote these labels to
  biological strand, strandedness, sense, or antisense claims.
- Preserve rather than approve transaction defects. Inputs are not snapshot-
  rechecked; the counts TSV is a native output rather than an attempt receipt;
  restoration moves are best-effort; cleanup can erase backups after failed
  restoration; and the lock lives only under the selected output directory
  while the counts file may live in a shared QC directory. Preserve these
  behaviors through exact predecessor, cross-directory collision, recovery-
  residue, input-mutation, signal, and absent-attempt-identity oracles without
  repairing or blessing them.
- Publish three small old-path producer test-only baselines in the existing
  direct shell owner. The child/count slice adds exact filter, merge, index,
  and count-command exits `71`-`74`; missing explicit samtools rejection before
  directory creation; basename/PATH execution from arbitrary CWD; assigned-
  greater-than-input rejection; and successful publication of the current
  flag-subcount/merged-count mismatch defect. The transaction slice fixes
  counts-last move order, incomplete-final-set preservation, byte-exact five-
  file restoration after final-path quickcheck failure, and publication exit
  `67` followed by restoration exit `68`, which leaves the prior FWD BAM
  missing while restoring the other four prior files and erasing backup/lock/
  scratch/recovery evidence. The stability/collision slice fixes admitted BAM/
  BAI mutation blindness, `TERM` exit `143`, and barrier-controlled same-sample
  runs whose distinct output-directory locks both succeed while the last
  writer replaces their shared counts TSV. Preserve unrelated files and assert
  absent receipts/recovery markers throughout.
- Preserve producer/validator asymmetry. The producer quickchecks both merged
  BAMs and enforces nonempty groups plus assigned/input bounds, but it does not
  prove biological orientation or current-attempt identity. The independent
  validator does not invoke samtools, quickcheck, recount records, inspect
  flags, verify BAM/BAI correspondence, or validate sort/read-group metadata.
  Validator exit `0` may publish failed rows.
- Preserve the eleven-column, one-row orientation-counts TSV, six-decimal
  assigned fraction, five validator check IDs, container magic, typed counts,
  both flag-group sums, assigned/unassigned arithmetic, stable-input recheck,
  report bytes, streams, and exits. The producer's lack of explicit flag-
  subcount-to-merged-count reconciliation remains a characterized defect.
- Publish one old-path direct-validator test-only baseline: arbitrary-CWD dry-
  run/execute/repeat byte parity with unchanged inputs and no invocation-CWD
  residue; invalid BAM/BAI container magic as exit-`0` failed evidence; and a
  compact post-build mutation matrix across all five inputs that exits `2`
  while preserving a valid predecessor report. The existing disagreement case
  owns flag/merged and assigned arithmetic failure. Neutral report-loader and
  publication-fault suites remain the shared owners; add no duplicate helper.
- The validator continues to privately exact-load neutral
  `src/norad/libraries/validation_report.py`. Add no BAM helper, package
  identity, wrapper, alias, ambient `PYTHONPATH`, public helper API, or neutral-
  library behavior change.
- Preserve scheduler mode/directives, one-CPU request, submit-directory
  fallback, exported `/tmp`, sample/input/output/QC/thread defaults, tolerated
  samtools module load, fixed default samtools path with override, tool/version
  diagnostics, delegation, streams/exits, five-nonempty-file post-check, body-
  level `logs/` mutation, and Bash `3.2` empty-array defect.
- Publish one old-path central-scheduler test-only baseline for Step `06`:
  samtools version-command failure before delegation; missing/nonexecutable
  warnings with unchanged delegation; PATH basename forwarding; dynamic absent-
  submit-directory fallback; dry-run `logs/`-only mutation; explicit `THREADS`
  independent of the one-CPU request; and a zero-exit child with five stale
  nonempty outputs falsely accepted byte-exactly. Existing generic cases retain
  directives/mode, module calls/tolerance, override arguments, invalid mode,
  child exit, missing outputs, and Bash `3.2` behavior.
- `STEP_PRODUCERS["06"]` changes only to final path
  `src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh`
  with projected hash
  `74399ceb42cb081b213256977b03137d7ae8513c07f98fb4cd06b2f7ee6a2730`.
  Preserve
  artifact status, evidence ID, Git projection, six public Step `06` artifact
  identities, schemas, contents, ordering, reconciliation, completion-marker
  interpretation, consumers, and scientific meaning. Add the exact final
  producer path/hash assertion to the existing migrated-implementation
  evidence test; no artifact adapter or schema behavior changes.
- Frozen starting coverage is validator `107/119` covered lines and `23/30`
  branches with global `9550/11720` lines and `3347/4772` branches. Final
  measurement must retain target rates, keep every non-target row exact, and
  preserve global covered-count floors after the row moves to its final path.
- Once producer and job leave flat wildcards, add their exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move direct shell
  and validator recipes; keep public CLI, SLURM, validation, neutral report,
  artifact, and coverage routes explicit rather than adding recursive
  discovery.
- Run only minimal old/final focused checks inside executable slices. Run the
  complete applicable computational gate once at the assembled executable card
  boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  producer/validator/scheduler root and arbitrary-CWD journeys, mechanical-
  orientation meaning, samtools/thread/output/QC/lock selection, rollback and
  residue preservation, focused tests, provenance, Git rollback, and the
  local-only evidence ceiling.
- Every supported path consumer is repository-owned and can change in one
  atomic direct cutover, so no temporary wrapper is justified. Roll back the
  documentation close and pending-scaffold deletion first, then the five-move/
  nine-update executable cutover with Make/oracle and artifact path/hash
  assertion together, then scheduler, validator, producer stability/collision,
  producer transaction, and producer child/count baselines in reverse order.
  Git rollback never alters runtime BAM/BAI/counts, lock, backup, scratch, log,
  or recovery evidence.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction/receipt/recovery mechanism, scheduler abstraction,
  orientation-policy change, manifest mutation, or public library API.

## Blocked by

- [REVIEW-UX-03K](REVIEW-UX-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of recovery, index-lock, or overlapping mutable-lane state
  before selection or executable mutation.
- Refresh only the named native assets, explicit path consumers, modes, hashes,
  report-loader/test-helper bridges, artifact evidence, coverage row, pending
  scaffold, active documentation, and applicable Step `06` failure/recovery
  states.
- Establish identical-input old-path baselines without real samtools changes,
  scheduler submission, dependency action, production input, or scientific/
  biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `06`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated stage contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Producer, validator, job, two direct tests, pending scaffold, central
  scheduler suite, neutral validation-report suite, public CLI/roster maps,
  Make/literal fixture, artifact mapping/reconciliation, coverage baseline, and
  current samtools/mechanical-orientation diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact paths,
  loader/test boundaries, pending-scaffold disposition, artifact provenance,
  and cutover ceiling; reliability owns transaction, counts, rollback-failure,
  collision, residue, and scheduler oracles; usability owns final commands,
  mechanical-language, tool/thread/directory/lock selection, recovery
  navigation, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers, artifacts, helper identities,
  defects, parity rows, coverage counts, and rollback evidence before mutation.
- Move only this stage owner and its two active direct tests, cut over every
  reviewed explicit caller, and make only reviewed path/root changes in
  production.
- Validate executable slices minimally, run the complete applicable gate at the
  card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `07` or any later owner; changing samtools,
  flags, mechanical-orientation meaning, threads, locks, output/QC placement,
  counts, transaction, validation, artifact, or scheduler policy; adding
  receipts/recovery controls; schema changes; package/descriptor work;
  dependency installation; or cluster/production execution.

## Deliverables

- Exactly five small reviewed old-path test-only checkpoints—producer child/
  count, producer transaction, producer stability/collision, validator, then
  scheduler—one exact final-owner/caller/test cutover checkpoint, and one
  separate documentation/lifecycle close, sequentially published on the same
  branch.
- Final native assets under
  `src/norad/stages/partition_BAM_by_mechanical_read_orientation/`, direct tests
  under `tests/stages/partition_BAM_by_mechanical_read_orientation/`, and no
  live legacy path, duplicate, wrapper, or compatibility owner; the obsolete
  pending scaffold has one reviewed terminal disposition and cannot become an
  active owner.
- Exact path/hash artifact transition, coverage accounting, supported commands,
  complete card-boundary validation, rollback/residue evidence, and a precise
  local-only evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, exact input admission, samtools/thread
  resolution, side-effect-free dry-run, run-token scratch/lock/output/QC paths,
  flag/merge/count command construction, execute bytes, validation,
  predecessor rules, controlled child/publication/rollback failures, residue,
  signals, streams, exits, and unrelated files as required by review.
- Validator parity preserves arguments, five rows, container/count arithmetic,
  dry-run/execute/repeat effects, report bytes, stable-input and publication
  behavior, private report ownership, and arbitrary-CWD use.
- Scheduler parity preserves mode, directives, CPU/thread state, submit CWD,
  module/tool/runtime resolution, dry-run logs, Bash `3.2`, delegation,
  five-output checks, streams, exits, and stale-output risk.
- Exact searches find one final owner and no undeclared legacy path, wrapper,
  duplicate, stale command, unresolved pending-test ownership, or lifecycle
  link. Coverage and the complete gate satisfy reviewed policy without
  evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `06`
  commands in `RUNBOOK.md`; Step `06` lock/temp/output-QC/partial/rollback-
  failure/stale-set, samtools/thread, counts, validation, and recovery routes in
  `TROUBLESHOOTING.md`; directly impacted neutral-library, Step `05`
  predecessor, Step `07` consumer, artifact, and pending-test routes; this
  card; review lifecycle links; and the dated audit log. Update diagrams only
  if final inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unmovable caller, required public import/package identity,
  permanent wrapper, second functional-owner migration, mechanical-policy or
  artifact/schema redesign, parity that requires blessing a defect, missing
  high-risk rollback oracle, dependency or cluster/production action, or scope
  that cannot remain this one stage owner and its direct evidence wiring.

## Completion record

Not selected. Defined from clean, published, local/upstream/live-remote-equal
`MIG-03J` documentation checkpoint `db60dfa`. All three dedicated review cards
remain unselected in `TODO`; no executable/test path changed, no computational
test ran, and no Step `07` or later owner is preloaded.
