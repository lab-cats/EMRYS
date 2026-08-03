# MIG-03J — Migrate the split-N-cigar-reads-with-GATK owner

## Objective

Move the complete `split_N_cigar_reads_with_GATK` producer, validator,
scheduler asset, and owner-local tests to their frozen final stage-owner homes
while preserving every public, transaction, scheduler, validation, reference,
artifact, coverage, and split-BAM contract.

## Why this exists

After `MIG-03I`, the refreshed live semantic DAG has exactly one eligible
unmigrated owner: `split_N_cigar_reads_with_GATK`. Its two direct artifact
predecessors, `mark_BAM_duplicates_with_Picard` and
`construct_FASTA_sidecars`, are migrated. Historical Step `06` remains blocked
on this owner, and no Step `06` card is created or selected. This card defines
Step `05` as the smallest next JIT unit but does not select it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `c6814e01352998ee4ebc01014737fac731f2e029`, the clean, published,
  local/upstream/live-remote-equal `MIG-03I` documentation close on the one
  active campaign branch.
- Semantic identity is `split_N_cigar_reads_with_GATK`, kind `stage`, machine
  key `norad.stage.split_N_cigar_reads_with_GATK.v1`, historical alias `05`,
  final source home `src/norad/stages/split_N_cigar_reads_with_GATK/`, and
  mirrored test home `tests/stages/split_N_cigar_reads_with_GATK/`.
- Move the mode-`0644` Bash producer
  `scripts/step_05_split_n_cigar_reads.sh`, mode-`0644` validator
  `scripts/validate_step_05_split_ncigar.py`, and mode-`0644` scheduler entry
  point `jobs/step_05_split_n_cigar_reads.slurm` without changing basenames or
  modes. Producer and job remain interpreter/submission surfaces, not directly
  executable files.
- Move only the mode-`0644` direct shell test
  `tests/shell/test_step_05_split_n_cigar_reads.sh` and mode-`0644` direct
  validator test `tests/test_validate_step_05_split_ncigar.py` to the mirrored
  stage test home. Keep independent scheduler behavior in the central wrapper
  suite.
- The three native assets total `34,030` bytes and `1,023` lines. Frozen
  SHA-256 values are producer
  `19b3ac73934c28760127a7f447863251e127362bb1cdaeef9346d6a310d3d01e`,
  validator
  `ceb3a9720b01c1de60d5f23026dea3f9daf3c9b4d1c93a8a140514ffc29c502a`,
  and job
  `00944fc0997117197b155f6f2e5222f27a371ab4d623c091544d9656fc2dddc6`.
  Direct-test rollback hashes are shell
  `a2d748f064139b0ed6c2f3c6f0664f445acf83689d379b0787d4f1b2b247a8b6`
  and validator
  `9f24713234b0b2ec35d9fd424d8a590334c8071d15078f4095faaf4417e232c4`.
- Proposed owner cutover is five moves plus the same ten explicit integration
  owners used by the adjacent BAM stages: `Makefile`,
  `scripts/build_artifact_index.py`, `tests/test_artifact_adapters.py`,
  `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/libraries/test_bam_validation.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`.
  Architecture review must prove the complete caller/reference-helper set and
  exact logical-file ceiling before execution planning.
- Production edits are limited to final self/delegation paths, final-depth
  private loaders, and replacing the validator's ambient
  `import reference_provenance` with a private exact-file bridge to unchanged
  public `scripts/reference_provenance.py`. Architecture review must decide the
  exact bridge and projected hashes; no package import, `PYTHONPATH`, helper
  move, or reference-owner redesign is permitted without a recorded finding.
- Preserve producer CLI/help, exact `<bam>.bai` and FASTA/FAI/DICT admission,
  GATK/samtools/Java argument-override/PATH/`JAVA_HOME` resolution, execute-only
  version checks, side-effect-free dry-run, run-token names, project-storage
  GATK temp directory, output-directory lock, complete-pair predecessor rule,
  staged validation, sequential publication, final revalidation, streams,
  exits, replacement, cleanup, and signal traps.
- Preserve rather than approve the transaction defects. Inputs are not
  snapshot-rechecked; the lock is output-directory-wide; successful
  publication has no receipt; restoration moves are best-effort; and cleanup
  can delete backups and the lock after a failure inside rollback. Reliability
  review owns exact predecessor/recovery-residue and input-mutation oracles and
  may not repair or bless these behaviors.
- Preserve producer/validator asymmetry. Producer structural success does not
  prove the GATK split-N-cigar transformation or bind output to an input/tool
  attempt. Validator exit `0` may publish failed rows and does not prove the
  transform. Preserve five check IDs, BAM/header/quickcheck semantics, exact
  reference contig/length agreement, stable-input recheck, report bytes,
  streams, and exits.
- The validator continues to privately exact-load neutral
  `src/norad/libraries/validation_report.py` and
  `src/norad/libraries/bam_validation.py` and must privately resolve unchanged
  public `scripts/reference_provenance.py` after movement. Add no package
  identity, wrapper, alias, `PYTHONPATH`, public helper API, or helper behavior
  change.
- Preserve scheduler mode/directives, submit-directory fallback, exported
  `/tmp`, sample/input/reference/output defaults, tolerated samtools module
  load, fixed default GATK/samtools paths with overrides, Java override/home/
  PATH selection and actual Java-17 floor, tool diagnostics, delegation,
  streams/exits, two-nonempty-file post-check, dry-run `logs/` mutation, and
  Bash `3.2` empty-array defect. Reliability review must disposition stale
  output, missing/unusable tool, module, version, and child states without
  hardening them.
- `STEP_PRODUCERS["05"]` changes only to the final producer path. Preserve
  artifact status, evidence ID, Git projection, three public Step `05` artifact
  identities, schemas, contents, ordering, reconciliation, consumers, and
  scientific meaning. Architecture review must require an exact final producer
  path/hash assertion in the migrated-implementation evidence test.
- Frozen starting coverage is validator `138/149` covered lines and `31/38`
  branches with global `9510/11677` lines and `3333/4756` branches. Final
  measurement must retain target rates, keep every non-target row exact, and
  preserve global covered-count floors after the row moves to its final path.
- Once producer and job leave flat wildcards, add their exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move direct shell
  and validator recipes; keep public CLI, SLURM, validation, neutral BAM/report,
  public reference-provenance, artifact, and coverage routes explicit rather
  than adding recursive discovery.
- Run only minimal old/final focused checks inside executable slices. Run the
  complete applicable computational gate once at the assembled executable card
  boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  producer/validator/scheduler root and arbitrary-CWD journeys, reference and
  GATK/Java/samtools selection, project-storage temp and lock behavior,
  rollback/residue preservation, focused tests, provenance, Git rollback, and
  the local-only evidence ceiling.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, new transaction/receipt/recovery mechanism, scheduler abstraction,
  reference parser, GATK policy, manifest mutation, or public library API.

## Blocked by

- [REVIEW-UX-03J](REVIEW-UX-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of recovery, index-lock, or overlapping mutable-lane state
  before selection or executable mutation.
- Refresh only the named native assets, explicit path consumers, modes, hashes,
  reference/helper bridges, artifact evidence, coverage row, active
  documentation, and applicable Step `05` failure/recovery states.
- Establish identical-input old-path baselines without real GATK, samtools,
  Java changes, scheduler submission, dependency action, production input, or
  scientific/biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `05`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated stage contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Producer, validator, job, two direct tests, central scheduler suite, neutral
  validation-report and BAM-helper suites, public reference-provenance owner/
  tests, public CLI/roster maps, Make/literal fixture, artifact mapping,
  coverage baseline, and current GATK/Java/samtools diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact paths,
  reference/helper/test boundaries, artifact provenance, and cutover ceiling;
  reliability owns transaction, rollback-failure, residue, and scheduler
  oracles; usability owns final commands, reference/tool/temp/lock selection,
  recovery navigation, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers, artifacts, helper identities,
  defects, parity rows, coverage counts, and rollback evidence before mutation.
- Move only this stage owner and its two direct tests, cut over every reviewed
  explicit caller, and make only reviewed path/loader changes in production.
- Validate executable slices minimally, run the complete applicable gate at the
  card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `06` or any later owner; changing GATK,
  samtools, Java, reference, temp, lock, BAM/BAI, transaction, or scheduler
  policy; adding receipts/recovery controls; artifact/schema changes; package/
  descriptor work; dependency installation; or cluster/production execution.

## Deliverables

- One or more small reviewed old-path reliability checkpoints only where
  required, one exact final-owner/caller/test cutover checkpoint, and one
  separate documentation/lifecycle close, sequentially published on the same
  branch.
- Final native assets under `src/norad/stages/split_N_cigar_reads_with_GATK/`,
  direct tests under `tests/stages/split_N_cigar_reads_with_GATK/`, and no live
  legacy path, duplicate, wrapper, or compatibility owner.
- Exact path/hash artifact transition, coverage accounting, supported commands,
  complete card-boundary validation, rollback/residue evidence, and a precise
  local-only evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, exact input/reference admission, GATK/Java/
  samtools resolution, side-effect-free dry-run, run-token scratch/lock paths,
  execute bytes, validation, predecessor rules, controlled child/publication/
  rollback failures, residue, signals, streams, exits, and unrelated files as
  required by review.
- Validator parity preserves arguments, five rows, reference/BAM/header
  behavior, dry-run/execute/repeat effects, report bytes, stable-input and
  publication behavior, all three private owners, and arbitrary-CWD use.
- Scheduler parity preserves mode, directives, submit CWD, module/tool/runtime
  resolution, dry-run logs, Bash `3.2`, delegation, two-output checks, streams,
  exits, and stale-output risk.
- Exact searches find one final owner and no undeclared legacy path, wrapper,
  duplicate, stale command, or lifecycle link. Coverage and the complete gate
  satisfy reviewed policy without evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `05`
  commands in `RUNBOOK.md`; Step `05` lock/temp/partial/rollback-failure/stale-
  output, GATK/Java/samtools/reference, validation, and recovery routes in
  `TROUBLESHOOTING.md`; directly impacted neutral-library, reference-
  provenance, canonical-BAM, FASTA-sidecar, and Step `04` owner routes; this
  card; review lifecycle links; and the dated audit log. Update diagrams only
  if final inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unmovable caller, required public import/package identity,
  permanent wrapper, second functional-owner migration, reference/helper or
  artifact/schema redesign, parity that requires blessing a defect, missing
  high-risk rollback oracle, dependency or cluster/production action, or scope
  that cannot remain this one stage owner and its direct evidence wiring.

## Completion record

Not selected. Defined from clean, published, local/upstream/live-remote-equal
`MIG-03I` documentation checkpoint `c6814e0`. All three dedicated review cards
remain unselected in `TODO`; no executable/test path changed, no computational
test ran, and no Step `06` or later owner is preloaded.
