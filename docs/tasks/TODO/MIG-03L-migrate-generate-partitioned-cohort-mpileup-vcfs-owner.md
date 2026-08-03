# MIG-03L — Migrate the partitioned cohort mpileup VCF owner

## Objective

Move the complete `generate_partitioned_cohort_mpileup_VCFs` producer,
validator, scheduler asset, and owner-local tests to their frozen final stage-
owner homes while preserving every public, mechanical-orientation, selector,
transaction, validation, scheduler, artifact, and coverage contract.

## Why this exists

After `MIG-03K`, the refreshed live semantic DAG has exactly one eligible
unmigrated owner: `generate_partitioned_cohort_mpileup_VCFs`. Its direct
predecessors—`partition_BAM_by_mechanical_read_orientation` for every declared
sample and `construct_FASTA_sidecars` for the reference FAI—are migrated.
Historical Step `08` remains blocked on this owner, and no Step `08` card is
created or selected. This card defines Step `07` as the smallest next JIT unit
but does not select it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `b73b12bfb7d5af02f9e2c5bb7749a91cfb030f6d`, the clean, published,
  local/upstream/live-remote-equal `MIG-03K` documentation close on the one
  active campaign branch.
- Semantic identity is `generate_partitioned_cohort_mpileup_VCFs`, kind
  `stage`, machine key
  `norad.stage.generate_partitioned_cohort_mpileup_VCFs.v1`, historical alias
  `07`, final source home
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/`, and mirrored
  test home
  `tests/stages/generate_partitioned_cohort_mpileup_VCFs/`.
- Move the mode-`0755` Bash producer
  `scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh`, mode-`0644`
  validator `scripts/validate_step_07_mpileup_outputs.py`, and mode-`0644`
  scheduler entry point
  `jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm` without changing
  basenames or modes. Preserve the producer as a directly executable and
  Bash-invocable surface, the validator as an explicit-interpreter surface,
  and the nonexecutable-mode job as an `sbatch` or explicit-Bash surface.
- Move only the mode-`0755` direct shell test
  `tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh` and mode-
  `0644` direct validator test `tests/test_validate_step_07_mpileup_outputs.py`
  to the mirrored stage test home. Keep independent scheduler behavior in the
  central wrapper suite. No Step `07` pending scaffold exists.
- The three native assets total `49,371` bytes and `1,360` lines. Frozen
  SHA-256 values are producer
  `e790946db19ad26f8f8e75a325ced9035fcc69d58819ca3b43a1032131fac858`,
  validator
  `4171442377c9c115d54baf9dc303cf22e37f2094b89daec9a982ad3c2704a85a`,
  and job
  `a2c64ceaebbf367f1c3f4c01cce663d16e958252a5a9dbd49ad26990b42d7659`.
  Direct-test rollback hashes are shell
  `9e46296ad22c3a08cb73f5b596844f2b0f13464ccf75739873454390d24189ba`
  and validator
  `2e13076b65bebad9c09de43a099ec45aa9970e6e6cefa65b9df247415b976180`.
- Architecture-reviewed executable cutover is exactly five moves plus nine
  explicit integration
  owners: `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`.
  Exact tracked-path, basename, Make-recipe, and artifact-provenance searches
  prove no tenth integration owner. The artifact test adds the final Step `07`
  path/hash assertion even though it has no old producer literal. The three
  root `configs/step_07_partitions.*.tsv` files remain shared operator inputs,
  not owner implementation or a sixth move. No pending Step `07` scaffold
  exists. A tenth update, sixth move, or different production-file edit
  reopens architecture review.
- Production edits are exactly: replace the producer usage path; change the
  validator repository root from `parents[1]` to `parents[4]` for unchanged
  neutral `src/norad/libraries/validation_report.py`; and replace the
  scheduler child path. The existing private report identity and loader
  behavior remain unchanged. No package import, `PYTHONPATH`, helper move,
  schema extraction, or other production edit is permitted.
- Projected final native values after only those reviewed path/root edits are
  producer `31,526` bytes / `893` lines / SHA-256
  `e3af9900b6f7831f2feafbc6d13f3755a475f02e5013c8b756107ddd90d22297`,
  validator `13,524` bytes / `334` lines / SHA-256
  `3191a379a4c2e1d589eeb3f327314d91dcb70f5e79da6e2b4f344ffb2b68763b`,
  and job `4,421` bytes / `133` lines / SHA-256
  `fbd8144a362cdd688ac14efcd8c003a3527b878d90ab525277a92018ac9a1ed6`.
  Producer remains mode `0755`; validator and job remain mode `0644`. Any
  production hash or mode difference reopens architecture review.
- The moved shell test changes only its repository root to
  `SCRIPT_DIR/../../..` and producer/job targets to final paths before
  reliability additions. The moved Python test changes its root to
  `parents[3]`, targets the final validator, and exact-loads unchanged root
  `tests/validation_roster_expectations.py` through
  `importlib.util.spec_from_file_location` under private test identity
  `generate_partitioned_cohort_mpileup_vcfs_validation_roster_oracle`. It
  validates the spec/loader, binds only `assert_exact_check_roster`, inserts no
  global module or path, and needs no production helper or separate test owner.
- Preserve producer CLI/help, filename-safe cohort/partition/sample IDs,
  positive maximum depth, nonempty filter, bcftools argument/override/PATH
  resolution, side-effect-free dry-run, exact manifest order, reference
  FASTA/FAI admission, partition selection, FAI-bound `region` and
  `regions_file` validation, relative selector-file resolution, exact
  orientation BAM/BAI paths, and manifest hash rechecks.
- Preserve exact mechanical groups and language. Step `07` consumes the
  complete `FWD_like` and `REV_like` Step `06` BAM/BAI pairs for every
  declared sample. It performs pileup and filtering, not `bcftools call`, and
  establishes neither biological strand nor variants, RNA-editing sites, or
  scientific readiness.
- Preserve both orientation pipelines: `bcftools mpileup -Ou -f`, the
  manifest selector, depth, `-I`, and exact DP/AD/ADF/ADR/SP annotations,
  piped to `bcftools filter -i ... -Ov`. Preserve header-only VCF validity,
  exact sample order, record counting, streams, exits, and current fake-tool
  evidence without changing bcftools policy.
- Preserve the cohort/partition output-directory lock, run-token scratch and
  backup names, stale-path refusal, all-three-or-none predecessor rule,
  temporary validation, sequential VCF/VCF/receipt publication, receipt-last
  ordering, final revalidation, predecessor replacement, cleanup, and signal
  traps.
- Preserve rather than approve transaction and provenance gaps. The receipt
  becomes visible before post-publication validation and the in-memory
  committed flag. Only both manifests are hash-bound and snapshot-rechecked;
  BAMs/BAIs, FASTA/FAI, regions file, bcftools identity, maximum depth, filter,
  and VCF bytes are not. Restoration is best-effort, no durable recovery or
  attempt marker exists, and receipt presence alone is not proof of a
  successful immutable computation. Reliability review owns exact rollback-
  failure, residue, signal, mutation, receipt-visibility, and absent-attempt-
  identity oracles without repairing or blessing these states.
- Publish one old-path producer pipeline/selector test-only baseline in the
  existing direct shell owner. Freeze all four controlled FWD/REV mpileup and
  filter child failures as normalized producer exit `1`, with exact diagnostic,
  no final outputs, cleaned owned lock/scratch, and unrelated-file
  preservation. Add missing/nonexecutable explicit bcftools rejection before
  output creation, basename/PATH resolution from arbitrary CWD, manifest-
  mutation rejection, compressed `regions_file` producer acceptance, and
  unchanged exact command/depth/filter/sample-order/non-calling evidence.
- Publish one old-path producer transaction/recovery test-only baseline. Fix
  final move order as FWD VCF, REV VCF, then receipt; observe the receipt and
  both VCFs during the post-publication/pre-commit validation window; retain
  exact all-three-or-none predecessor and foreign-lock/stale-path behavior;
  and inject receipt-publication exit `67` followed by prior-FWD restoration
  exit `68`. The last state must propagate `67`, leave the prior FWD final
  absent while preserving its backup, restore prior REV and receipt bytes,
  remove owned temps/lock, preserve unrelated bytes, and create no recovery
  marker. This is ambiguous manual recovery, not successful rollback.
- Publish one old-path producer stability/provenance test-only baseline. A
  controlled post-admission mutation of BAM/BAI, FASTA/FAI, and regions-file
  inputs must remain undetected and permit exit `0`; manifest mutation remains
  rejected. Controlled `TERM` exits `143`, restores a complete predecessor,
  preserves unrelated bytes, and removes owned scratch/lock. A barrier-
  controlled same-scope pair proves the cohort/partition lock admits one run
  and rejects the other. Assert the receipt has no run token, BAM/reference/
  tool/depth/filter identity, or VCF hash and cannot prove current-attempt or
  immutable-input identity. Do not add those fields or a recovery marker.
- Preserve the exact ten-column, two-row receipt, ordered `FWD_like` then
  `REV_like`, including declared selector value, explicit VCF paths, manifest
  hashes, sample count, and record counts. Preserve the relative-output-root
  versus resolved-validator-path mismatch risk rather than silently changing
  receipt semantics.
- Preserve producer/validator asymmetry. The independent validator invokes no
  bcftools; checks receipt shape/order, VCF row shape/numeric position, FAI-
  bounded selector declarations, manifest hashes/sample order, VCF paths, and
  record counts; and may exit `0` while publishing failed rows. It does not
  prove data coordinates obey the selector, REF/ALT or FORMAT annotation
  semantics, filter compliance, BAM/reference/tool/policy identity, VCF
  hashes, biological meaning, or current-attempt identity. Its
  `regions_file` validation is intentionally less detailed than the producer.
- Preserve the five validator check IDs: `receipt_structure`,
  `vcf_structure`, `selector_reconciliation`,
  `manifest_identity_and_sample_order`, and `vcf_record_counts`; common report
  bytes; stable-input recheck; report publication; streams; and exits.
- Publish one old-path direct-validator test-only baseline. Add arbitrary-CWD
  dry-run/execute/repeat byte parity with unchanged inputs and no invocation-
  CWD residue; a compact semantic-failure matrix owning all five check IDs as
  exit-`0` failed evidence; and a compact post-build mutation matrix across all
  six snapshotted inputs that exits `2` while preserving a valid predecessor
  report. Characterize producer-valid compressed regions as exit-`0` selector
  failure, out-of-bounds BED coordinates and VCF rows outside the declared
  selector plus unchecked REF/ALT/FORMAT as current false-pass ceilings, and
  relative receipt VCF paths versus resolved arguments as exit-`0`
  `vcf_record_counts` failure. Neutral report-loader/publication-fault and
  exact-roster suites remain shared owners; add no duplicate helper.
- The validator continues to privately exact-load neutral
  `src/norad/libraries/validation_report.py`. Add no VCF/selector helper,
  package identity, wrapper, alias, ambient `PYTHONPATH`, public helper API,
  or neutral-library behavior change.
- Preserve scheduler mode/directives, one-CPU request, submit-directory
  fallback, exported `/tmp`, cohort/manifest/partition/orientation/reference/
  output/depth/filter defaults, tolerated bcftools module load, fixed default
  bcftools path with override, tool/version diagnostics, explicit execute
  gate, delegation, streams/exits, three-nonempty-file post-check, and body-
  level `logs/` mutation. Reliability review must disposition missing/
  unusable tool, module, version, child, stale complete output, and submitted-
  job states without hardening them.
- Publish one old-path central-scheduler test-only baseline for Step `07`:
  executable bcftools version-command failure before delegation; missing/
  nonexecutable warning with unchanged delegation; PATH-basename forwarding;
  dynamic absent-submit-directory fallback; dry-run `logs/`-only mutation; and
  a zero-output child with three stale nonempty outputs falsely accepted byte-
  exactly. Existing generic cases retain exact directives/mode, tolerated
  module calls, override arguments, invalid execute mode, child exit, output-
  missing rejection, and exact depth/filter forwarding.
- `STEP_PRODUCERS["07"]` changes only to final path
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh`
  with projected hash
  `e3af9900b6f7831f2feafbc6d13f3755a475f02e5013c8b756107ddd90d22297`.
  Preserve
  artifact status, evidence ID, Git projection, Step `07` VCF/receipt/report
  identities, schemas, ordering, reconciliation, downstream Step `08`
  dependency, completion-marker interpretation, consumers, and scientific
  meaning. Architecture review must require an exact final producer path/hash
  assertion in the migrated-implementation evidence test.
- Frozen starting coverage is validator `167/198` covered lines and `48/72`
  branches with global `9551/11720` lines and `3348/4772` branches. Final
  measurement must retain target rates, keep every non-target row exact, and
  preserve global covered-count floors after the row moves to its final path.
- Once producer and job leave flat wildcards, add their exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move direct shell
  and validator recipes; keep public CLI, SLURM, validation, neutral report,
  artifact, and coverage routes explicit rather than adding recursive
  discovery.
- Run only minimal old/final focused checks inside executable slices. Run the
  complete applicable computational gate once at the assembled executable
  card boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Final producer use is the mode-`0755` repository path
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh`;
  final validator use is an explicit interpreter plus
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/validate_step_07_mpileup_outputs.py`;
  and scheduler use is `sbatch` plus the mode-`0644` final owner-local job from
  a checkout with `logs/` created first. Arbitrary-CWD use makes every code,
  input, selector, output/report, tool, and checkout path absolute. Use an
  absolute producer output root in supported commands so receipt VCF paths
  agree with validator-resolved arguments. Add no installed or legacy route.
- Producer dry-run is side-effect-free after validating manifests, FAI/selector,
  BAM/BAIs, tool, depth/filter, and hashes and printing exact pipelines plus
  output/lock/temp/publication paths. Validator dry-run reads six inputs and
  prints five rows without writing. Scheduler `EXECUTE=0` is not side-effect-
  free: it changes to the submit/fallback directory, creates `logs/`, performs
  module/tool/version diagnostics as applicable, and delegates producer dry-
  run. Documentation must keep these three effects distinct.
- Recovery guidance must preserve all finals, temps/backups, lock/owner,
  manifests, BAM/BAIs, FASTA/FAI, regions file, unrelated bytes, streams,
  scheduler evidence, CWD, tool/version, depth/filter, and environment before
  action. It must name the controlled exit-`67`/restore-exit-`68` state where
  prior FWD is absent but its backup survives while prior REV/receipt are
  restored, with no marker. Never combine attempts, reconstruct a member,
  remove a foreign lock, trust receipt presence/counts/timestamps, or retry the
  same output path. Any separately authorized diagnostic retry uses an
  isolated output root after ruling out producer and Step `08` readers.
- Publish exactly five small sequential old-path test-only checkpoints—
  producer pipeline/selector, producer transaction/recovery, producer
  stability/provenance, validator, then scheduler—before the atomic five-move/
  nine-update cutover. Only the existing direct shell, direct validator, and
  central scheduler test owners may change. Add no separate fixture, fourth
  test owner, production edit, coverage-baseline edit, documentation batch,
  dependency, or future owner in those slices.
- Add one adjacent owner `README.md` only at documentation close. It must
  route producer/validator/scheduler root and arbitrary-CWD journeys,
  mechanical-orientation and non-calling meaning, selector/depth/filter/tool
  choice, output/lock/receipt selection, rollback and residue preservation,
  focused tests, provenance, Git rollback, and the local mocked-runtime
  evidence ceiling.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction/receipt/recovery redesign, scheduler abstraction,
  calling step, selector/filter policy change, manifest mutation, or public
  library API.

## Blocked by

- [REVIEW-UX-03L](../COMPLETED/REVIEW-UX-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Required: architecture, reliability, and usability reviews are complete before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of recovery, index-lock, or overlapping mutable-lane state
  before selection or executable mutation.
- Refresh only the named native assets, explicit path consumers, modes,
  hashes, report-loader/test-helper bridges, artifact evidence, coverage row,
  active documentation, and applicable Step `07` failure/recovery states.
- Establish identical-input old-path baselines without real bcftools changes,
  scheduler submission, dependency action, production input, or scientific/
  biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `07`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated stage contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Producer, validator, job, two direct tests, central scheduler suite, neutral
  validation-report suite, public CLI/roster maps, Make/literal fixture,
  artifact mapping/reconciliation, coverage baseline, partition manifests,
  and current bcftools/selector/receipt diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact
  paths, loader/test boundaries, artifact provenance, and cutover ceiling;
  reliability owns transaction, rollback-failure, mutation, receipt,
  selector, validator, and scheduler oracles; usability owns final commands,
  mechanical/non-calling language, selector/tool/output/lock choice, recovery
  navigation, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers, artifacts, helper identities,
  defects, parity rows, coverage counts, and rollback evidence before
  mutation.
- Move only this stage owner and its two active direct tests, cut over every
  reviewed explicit caller, and make only reviewed path/root changes in
  production.
- Validate executable slices minimally, run the complete applicable gate at
  the card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `08` or any later owner; changing bcftools,
  pileup/filter/selector/depth policy, mechanical labels, inputs, locks,
  output/receipt placement, transaction, validation, artifact, or scheduler
  policy; adding calling, provenance/recovery controls, output hashes, or
  schemas; package/descriptor work; dependency installation; or cluster/
  production execution.

## Deliverables

- One or more small reviewed old-path reliability checkpoints only where
  required, one exact final-owner/caller/test cutover checkpoint, and one
  separate documentation/lifecycle close, sequentially published on the same
  branch.
- Final native assets under
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/`, direct tests
  under `tests/stages/generate_partitioned_cohort_mpileup_VCFs/`, and no live
  legacy path, duplicate, wrapper, or compatibility owner.
- Exact path/hash artifact transition, coverage accounting, supported
  commands, complete card-boundary validation, rollback/residue evidence, and
  a precise local mocked-runtime-only evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, exact input/selector admission, manifest
  order/hash checks, bcftools/depth/filter resolution, side-effect-free dry-
  run, exact pipeline construction, execute bytes, VCF/sample/count
  validation, predecessor rules, controlled child/publication/rollback
  failures, residue, signals, streams, exits, and unrelated files as required
  by review.
- Validator parity preserves arguments, five rows, receipt/VCF/selector/
  manifest/count semantics, dry-run/execute/repeat effects, report bytes,
  stable-input and publication behavior, private report ownership, and
  arbitrary-CWD use.
- Scheduler parity preserves mode, directives, submit CWD, module/tool/runtime
  resolution, dry-run logs, delegation, three-output checks, streams, exits,
  and stale-output risk.
- Exact searches find one final owner and no undeclared legacy path, wrapper,
  duplicate, stale command, or lifecycle link. Coverage and the complete gate
  satisfy reviewed policy without evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `07`
  paths and commands in `RUNBOOK.md`; Step `07` lock/temp/partial/rollback-
  failure/receipt, selector/FAI/regions-file, manifest/input-mutation,
  bcftools/depth/filter, relative-path, validation, scheduler, and recovery
  routes in `TROUBLESHOOTING.md`; directly impacted neutral-library, Step
  `06` predecessor, Step `08` consumer, artifact-provenance, and partition-
  manifest routes; this card; review lifecycle links; and the dated audit
  log. Update diagrams only if final inspection finds a material DAG or public-
  flow change.

## Escalation conditions

- Stop for an unmovable caller, required public import/package identity,
  permanent wrapper, second functional-owner migration, pileup/filter/
  selector or artifact/schema redesign, parity that requires blessing a
  defect, missing high-risk rollback oracle, dependency or cluster/production
  action, or scope that cannot remain this one stage owner and its direct
  evidence wiring.

## Completion record

Not selected. Architecture, reliability, and usability reviews completed from
published/equal checkpoints. The next separate reversible boundary is a fresh
branch cut from the published usability-completion checkpoint before migration
selection. No executable/test path changed, no computational test ran, and no
Step `08` or later owner is preloaded.
