# MIG-03M — Migrate the cohort preprocessing and annotation owner

## Objective

Move the complete `preprocess_and_annotate_cohort_candidates` shell/R
producer, validator, scheduler asset, and owner-local tests to their frozen
final stage-owner homes while preserving every public, cohort-barrier,
annotation, provisional-orientation, transaction, validation, scheduler,
artifact, guarded-R, and coverage contract.

## Why this exists

After `MIG-03L`, the refreshed live required-artifact DAG has exactly one
eligible unmigrated owner: `preprocess_and_annotate_cohort_candidates`. Its
complete declared-partition-and-orientation Step `07` predecessor is migrated.
The Step `09` analysis remains blocked on the Step `08` sites table and input
receipt, and Step `09c` additionally consumes the complete Step `08`
transaction. No Step `09` or later card is created or selected. This card
defines Step `08` as the smallest next JIT unit but does not select it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `4562ec3218453fe6869cf98ca2a382d09d796ca2`, the clean, published,
  local/upstream/live-remote-equal `MIG-03L` documentation/lifecycle close on
  the active fresh campaign branch.
- Semantic identity is `preprocess_and_annotate_cohort_candidates`, kind
  `stage`, machine key
  `norad.stage.preprocess_and_annotate_cohort_candidates.v1`, historical alias
  `08`, final source home
  `src/norad/stages/preprocess_and_annotate_cohort_candidates/`, and mirrored
  test home
  `tests/stages/preprocess_and_annotate_cohort_candidates/`.
- Architecture-reviewed production moves are the mode-`0755` Bash transaction entry point
  `scripts/step_08_vcf_preprocessing.sh`, mode-`0644` R implementation
  `scripts/step_08_vcf_preprocessing.R`, mode-`0644` Python validator
  `scripts/validate_step_08_preprocessing_outputs.py`, and mode-`0644`
  scheduler entry point `jobs/step_08_vcf_preprocessing.slurm`, without
  changing basenames or modes. Preserve direct/Bash producer use, Rscript-only
  R use, explicit-interpreter validator use, and `sbatch` or explicit-Bash job
  use.
- The four native assets total `124,401` bytes and `3,380` lines. Frozen
  SHA-256 values are shell
  `28d1188aa53a3bf2ca53b3b2b8d5e95ac8451c4a1a71e1e87a1ad4eb858afb07`,
  R implementation
  `f2580880ed0947efc8b41697a7ebd6f227a38556bb82922635b1bc8ba4cbc883`,
  validator
  `8a2dfd21f3e42b4ee4cf890da2686d686928b0b2cedce82ebc9d5d7cde2af410`,
  and job
  `a369dfbb9a7ad3bcaf8e5013a76a3d04e9e225e8b97c49d9f30a892cb45f221c`.
- Architecture-reviewed owner-local protection moves are the mode-`0755` shell test
  `tests/shell/test_step_08_vcf_preprocessing.sh`, mode-`0755` guarded-R
  runner `tests/r/run_step_08_vcf_preprocessing_tests.sh`, mode-`0644` R
  semantic test `tests/r/test_step_08_vcf_preprocessing.R`, and mode-`0644`
  validator test `tests/test_validate_step_08_preprocessing_outputs.py`.
  Their frozen hashes are respectively
  `9df2c71ad0aa7b4e8ae315fd2d8164eb2714edd5b87cbab0bedd7c37eee69ed0`,
  `c7828ab35c57687b2349b3d6a5bf01456abc3d9fa0d9bad4e17745a8dc8ec052`,
  `819337936bd780d633967a9075ce7e368f0294ee70ee19e1648354e7427bbc7d`,
  and
  `f2a312e0647cb4588d16fd9e683ce2d58996baa1b95ac8b0f8fba8c29561b5dd`.
  All four belong in the mirrored owner; the guarded-R runner is Step `08`-
  specific, while the central Make/local-R environment owners remain central.
  Exact tracked-path and scaffold searches find no Step `08` pending scaffold.
- The architecture-reviewed executable cutover is exactly eight moves plus ten explicit
  integration owners: `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/shell/test_local_r_environment.sh`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`.
  Exact tracked-path, basename, import, Make, R, job, artifact, and test searches
  prove the full caller/import/test set and no eleventh integration owner. The
  artifact test adds the exact final Step `08` producer path/hash assertion even
  though it has no old producer literal. An eleventh integration update, ninth
  move, or different production file reopens architecture review.
- Production path edits are limited to shell/R usage text, validator owner-root
  and exact-file dependency resolution, and scheduler R/child defaults. The
  shell and R implementation remain siblings. The validator must continue to
  exact-load neutral `src/norad/libraries/validation_report.py` and must replace
  its ambient sibling import of flat
  `scripts/step_09c_scientific_validation.py` with a private exact-file bridge,
  without moving or changing the Step `09c` owner, adding `PYTHONPATH`, changing
  global `sys.path`, or creating a public package identity. The bridge uses
  private identity `_norad_step_09c_scientific_validation_contracts`, resolves
  repository root with `parents[4]`, targets exact flat
  `scripts/step_09c_scientific_validation.py`, inserts only that private
  identity before execution for dataclass safety, validates cached `__file__`
  plus a post-execution readiness marker, removes its own partial cache entry on
  failure, and reports sanitized exit-`2` diagnostics. The neutral report bridge
  changes only `parents[1]` to `parents[4]` while retaining its existing private
  identity, readiness, cache, and failure behavior.
- Exact reviewed path/root edits project final native values: shell mode `0755`,
  `39,954` bytes / `1,024` lines / SHA-256
  `578542fefa02aa23667bb40e582cbab215e6d3efec0a7c2fbb002290f1cfc1f3`;
  R program mode `0644`, `69,505` bytes / `1,939` lines /
  `50cae0523ea68f87535866cbe9e86d38c3812f96a2c8a06ebd66a72177268699`;
  validator mode `0644`, `12,918` bytes / `346` lines /
  `57a227c478c0caec60fe2ff8d84f7feb1fce28c5248338f1369b2a186284c78f`;
  and job mode `0644`, `4,597` bytes / `134` lines /
  `e51d0df86609ca5d3d39b60f6036ee225bc17c11b6a83d68c683603842c57de6`.
  Any production hash, byte, line, or mode difference reopens architecture
  review.
- The moved shell test and guarded-R runner resolve repository root with
  `../../..`; the runner targets the final R program and owner-local R test.
  The R test continues to require repository-root CWD and targets the final R
  program. The moved Python test uses `parents[3]`, targets the final validator,
  and exact-loads root `tests/validation_roster_expectations.py` plus flat
  `scripts/step_09c_scientific_validation.py` under private test identities.
  Only the Step `09c` private identity is installed in `sys.modules` for
  dataclass-safe execution; no global path, public module identity, production
  helper, or second test owner is added.
- `tests/test_public_cli_contracts.py` gains an explicit R basename-to-path map
  analogous to its Python and shell maps so the moved Rscript-only entry point
  and remaining flat R files are inventoried exactly once. Make moves the
  shell, validator, and guarded-R runner recipes; the central local-R oracle
  changes only its expected Step `08` test path. Exact final shell/job paths
  leave flat wildcards and enter `validation-static`/`smoke` plus their literal
  expansion evidence.
- Preserve shell CLI/help, safe cohort IDs, explicit sample/partition manifests,
  Step `07` root, annotation GTF, output/QC roots, Rscript/R-program resolution,
  side-effect-free dry-run, exact manifest order, complete nonoverlapping
  partition barrier, exact two-orientation receipt/VCF admission, Step `07`
  receipt/VCF hash checks, repeated input stability checks, streams, exits, and
  current local fake-R evidence.
- Preserve the R implementation's bounded raw-VCF lexical validation,
  VariantAnnotation parsing, allele expansion, supported-SNV selection,
  deterministic candidate IDs/order, exact dynamic tables, GTF overlap,
  DP/AD/AF arithmetic, skipped symbolic/non-SNV counts, header-only behavior,
  and fixed `legacy_provisional_v1` mapping. Relocation changes no R package,
  dependency, method, policy, schema, threshold, or biological meaning.
- Preserve exact provisional language: `FWD_like` maps to annotation strand `+`
  with complemented genomic alleles and `REV_like` maps to `-` unchanged for
  RNA alleles only under compatibility policy. This is not validated biological
  strand, library strandedness, sense/antisense interpretation, variant or
  RNA-editing-site proof, completed scientific review, or biological readiness.
- Preserve the cohort lock, run-token scratch/backups split across output and QC
  roots, stale-path refusal, all-three-or-none predecessor rule, prepublication
  validation, sites/summary/input-receipt publication order, receipt-last native
  marker, final revalidation, predecessor replacement, input-hash rechecks,
  cleanup, and signal traps.
- Preserve rather than approve transaction/provenance gaps. The input receipt
  becomes visible before final post-publication validation and the in-memory
  commit flag. Failed restore moves retain remaining backups but no durable
  recovery marker or automated recovery interface exists, and cleanup releases
  the lock even after incomplete restoration. The receipt does not hash sibling
  sites/summary outputs or record R/package, Step `07` tool/reference/filter, or
  attempt identity. Reliability review owns exact child/publication/restore
  failure, receipt visibility, signal, lock/concurrency, residue, input-mutation,
  and absent-attempt-identity oracles without fixing or blessing these states.
- Publish one old-path runtime/input-provenance checkpoint in the direct shell
  test. Freeze pre-mutation rejection of missing/nonexecutable explicit
  Rscript and missing R program, plus PATH-basename resolution from arbitrary
  CWD. Mutations of the sample manifest, partition manifest, annotation GTF,
  Step `07` receipt, and Step `07` VCF must each fail before publication with
  preserved unrelated bytes and clean owned residue. A controlled mutation of
  the selected R program remains undetected and permits publication; assert
  the input receipt records no R program/runtime/package or attempt identity
  and no sibling sites/summary hashes. Preserve that provenance ceiling.
- Publish one old-path transaction/recovery checkpoint in the direct shell
  test. Freeze the final move order as sites, cross-root QC summary, then input
  receipt, and barrier-observe all three finals after receipt visibility but
  before final validation/commit. Inject receipt-publication exit `67` followed
  by prior-sites restoration exit `68`: propagate `67`, leave the prior sites
  final absent while retaining its output-root backup, restore prior input
  receipt and QC summary byte-exactly, clean owned temps/lock, preserve
  unrelated bytes in both roots, and create no recovery marker. This is
  ambiguous manual recovery, not successful rollback or retry authority.
- Publish one separate old-path signal/concurrency checkpoint in the direct
  shell test. Controlled `TERM` after receipt visibility exits `143`, restores
  a complete predecessor across both roots, preserves unrelated bytes, cleans
  owned scratch/lock, and creates no marker. A fake-R barrier proves one
  same-cohort lock winner and one exit-`1` loser, followed by one complete
  winner set and no owned residue. Do not add attempt identity or recovery
  behavior.
- Preserve the exact three-output transaction: sites and input receipt under
  `<output-root>/<cohort>/`, summary under the separate QC root. Preserve exact
  headers, partition/orientation ordering, manifest/annotation and Step `07`
  path/hash identities, per-input and aggregate counts, policy, candidate
  uniqueness, sample DP/AD/AF columns, and header-only validity.
- Preserve producer/validator asymmetry. The validator invokes no R, publishes
  five exact rows, may exit `0` with failed evidence, and validates internal
  table contracts without rerunning VariantAnnotation, GTF overlap, allele
  expansion, complementation, or upstream filtering. Its
  `sites_order_uniqueness` check does not recompute candidate IDs or prove
  deterministic row order; it does not reopen Step `07` inputs to recompute
  their hashes. Equivalent annotation paths can fail because producer spelling
  and validator resolution differ. Reliability review must characterize these
  ceilings rather than broaden claims.
- Preserve the five validator check IDs: `output_transaction`,
  `manifest_annotation_identity`, `input_receipt_reconciliation`,
  `sites_order_uniqueness`, and `summary_count_reconciliation`; common report
  bytes; stable-input recheck; report publication; streams; and exits. Shared
  Step `08` schema/validation functions remain physically owned by flat Step
  `09c`; this migration does not extract, redesign, or reassign them.
- Publish one old-path direct-validator checkpoint. Add arbitrary-CWD dry-run/
  execute/repeat byte parity; make each exact check ID independently observable
  as exit-`0` failed evidence; and mutate each of the six snapshotted inputs
  after build as exit `2` while preserving a valid predecessor report. Freeze
  equivalent annotation-path spelling as failed identity evidence and
  arbitrary unique candidate IDs plus reversed site rows as current false-pass
  ceilings. Common report loading/publication faults remain centrally owned.
  At atomic cutover, replace the test's ambient imports with private exact-file
  loaders and add final-path direct tests for the new production Step `09c`
  bridge's exact/foreign/partial cache, specification/loader, execution,
  cleanup, sanitized-exit, and `sys.path` behavior.
- Preserve scheduler mode/directives, submit-directory fallback, cohort/input/
  annotation/output/QC/R defaults, tolerated module diagnostics, optional
  repository-local R environment, explicit execute gate, delegation, streams/
  exits, three-file post-check, and body-level `logs/` behavior. Reliability
  review must disposition missing/unusable Rscript or R program, module/renv,
  child, stale-complete-output, and submitted-job states without hardening them.
- Publish one old-path central-scheduler checkpoint for tolerated Rscript
  version-probe failure; warning-only missing/nonexecutable Rscript;
  PATH-basename and selected R-program forwarding; absent-submit-directory
  launch-CWD fallback; dry-run `logs/`-only mutation; and stale three-file
  false success across output/QC roots after a zero-output child. Generic tests
  retain mode/directives, the tolerated `module list`, arguments, invalid mode,
  child exit, and missing outputs. The wrapper inherits caller R startup state
  and neither activates nor validates `renv`; the central local-R suite owns
  the guarded opt-in environment contract.
- `STEP_PRODUCERS["08"]` changes only to final shell producer path
  `src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh`
  with projected hash
  `578542fefa02aa23667bb40e582cbab215e6d3efec0a7c2fbb002290f1cfc1f3`.
  Preserve artifact IDs, schemas, Step `08` native/report identities, ordering,
  reconciliation, consumers, and scientific meaning. Preserve the existing
  distinction between the producer's input-receipt native marker and the
  artifact adapter's `step08_summary_v1` failure marker; do not select a new
  marker or change either interpretation.
- Frozen starting coverage is validator `122/129` covered lines and `26/36`
  branches with global floors `9561/11720` lines and `3351/4772` branches.
  Final measurement must retain target rates, keep every non-target row exact,
  and preserve global covered-count floors after the path move.
- The existing guarded-real-R suite is sufficient for semantic relocation
  parity and receives no test-only behavior slice. Existing artifact tests own
  native input-receipt versus `step08_summary_v1` reconciliation; only final
  path/hash evidence changes at cutover. Publish exactly five sequential
  test-only checkpoints—runtime/input provenance, transaction/recovery,
  signal/concurrency, validator, then scheduler—before atomic cutover. Only the
  existing direct shell, direct validator, and central scheduler test owners
  may change; add no fixture file, fourth owner, production edit, coverage
  baseline, documentation batch, dependency, or future card in those slices.
- Once shell/job leave flat wildcards, add exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move shell, validator,
  and guarded-R recipes; preserve the exact guarded environment and update the
  local-R evidence oracle. Keep public CLI, R, SLURM, validation, neutral report,
  Step `09c` bridge, artifact, and coverage routes explicit rather than adding
  recursive discovery.
- Final root use directly invokes the mode-`0755` shell at
  `src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh`;
  it selects its sibling R program by default. Direct Rscript use is a
  maintainer/fixture diagnostic, not a production orchestration route. Invoke
  the mode-`0644` validator from the same owner with an explicit interpreter.
  From checkout root, create `logs/` before submitting the mode-`0644` job with
  `sbatch`; explicit Bash is only a local wrapper diagnostic. Arbitrary-CWD
  shell/validator use makes code, interpreter, Rscript/R program, manifests,
  Step `07`, annotation, output/QC, native inputs, and report paths absolute.
  Use absolute Step `07` and annotation paths for stable recorded spelling and
  validator agreement. Add no installed, public-import, `PYTHONPATH`, legacy,
  alias, wrapper, or symlink route.
- Preserve distinct effects. Shell dry-run resolves runtime/program and fully
  validates/enumerates inputs but invokes no R and creates no output/QC path.
  Validator dry-run reads/snapshots six inputs, prints five rows, and writes no
  report; execute needs an existing real report parent and may return `0` with
  failed rows. The guarded-R runner is local semantic-fixture evidence and an
  explicit runtime/package failure is not a pass. Scheduler `EXECUTE=0`
  changes CWD, creates `logs/`, performs tolerated module/Rscript diagnostics,
  inherits caller R/`renv` startup state, and delegates shell dry-run. It does
  not install/restore dependencies and is not side-effect-free.
- Recovery documentation must preserve both split roots, all finals/temps/
  backups, lock/owner, manifests, annotation, Step `07` receipts/VCFs, selected
  R runtime/program/package context, unrelated bytes, streams, scheduler
  records/logs, and checkout/submit CWD before action. Name the controlled exit-
  `67`/restore-exit-`68` state where sites final is absent but its backup
  survives while prior input receipt and QC summary are restored and the lock
  is gone. Never combine attempts, reconstruct a member, remove a foreign lock,
  trust receipt visibility/hash/count/time or stale scheduler success, or retry
  the same names. Rule out Step `08` writers and Step `09`/`09c`/artifact
  readers first. Any separately authorized nonproduction diagnostic retry uses
  a distinct output-root and QC-root pair.
- Documentation must keep `legacy_provisional_v1` as compatibility behavior:
  FWD-like maps to annotation `+` with complemented genomic alleles and REV-
  like maps to `-` unchanged. It is not validated strand, sense/antisense,
  variant/editing-site proof, completed scientific review, or biological
  readiness. Distinguish fake-R orchestration, guarded-real-R semantics,
  validator failed evidence/non-recomputation, stale scheduler success, native
  receipt marker, and artifact summary failure marker without promoting any to
  runtime, production, scientific, or biological proof.
- Old and final executable/test paths may not coexist. After reviewed
  reliability baselines, apply all eight moves, ten integrations, and exact
  production path/loader edits atomically. Reverse rollback restores
  documentation last-in-first-out, then the eight-move/ten-update cutover,
  then any test-only reliability checkpoints in reverse order. No wrapper,
  alias, symlink, compatibility copy, descriptor, schema, or future-owner
  preload is justified.
- Use only minimal old/final focused checks inside executable slices. Run the
  complete applicable computational gate once at the assembled executable card
  boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  shell/R/validator/scheduler root and arbitrary-CWD journeys, cohort-barrier
  and provisional-policy meaning, R/dependency/input/output/QC/lock/receipt
  choices, split-root rollback/residue preservation, focused shell/Python/
  guarded-R tests, artifact provenance, Git rollback, and the local fixture-
  only evidence ceiling.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction/receipt/recovery redesign, shared-schema extraction,
  scheduler abstraction, policy/method change, dependency action, public
  library API, or Step `09`/`09c` migration.

## Blocked by

- [REVIEW-UX-03M](REVIEW-UX-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Required: completed architecture, reliability, and usability reviews fixed task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of recovery, index-lock, or overlapping mutable-lane state
  before selection or executable mutation.
- Refresh only the named native assets, explicit callers/imports, modes, hashes,
  test-helper/Step `09c`/report bridges, artifact evidence, coverage row, active
  documentation, and applicable Step `08` failure/recovery states.
- Establish identical-input old-path baselines without dependency installation,
  R restoration, scheduler submission, production input, or scientific/
  biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `08`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated stage contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Shell/R producer, validator, job, four direct protection assets, central
  scheduler and guarded-R environment suites, neutral validation-report suite,
  flat Step `09c` shared-contract implementation, public CLI/roster maps,
  Make/literal fixture, artifact mapping/reconciliation, coverage baseline,
  manifests, and current Step `07`/annotation/transaction diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact move/
  caller/loader/test/artifact boundaries; reliability owns transaction,
  restoration, mutation, R semantics, validator, and scheduler oracles;
  usability owns final commands, provisional language, R/input/output/lock
  choices, split-root recovery navigation, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers/imports, artifacts, helper
  identities, defects, parity rows, coverage counts, and rollback evidence
  before mutation.
- Move only this stage owner and its reviewed direct tests, cut over every
  reviewed explicit caller, and make only reviewed path/root/private-loader
  changes in production.
- Validate executable slices minimally, run the complete applicable gate at the
  card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `09`, Step `09c`, or another owner; changing R
  dependencies, VCF/GTF parsing, annotation, allele/count/candidate semantics,
  provisional orientation policy, inputs, locks, output/receipt placement,
  transaction, validation, artifact, or scheduler policy; schema/helper
  extraction; dependency installation/restoration; or cluster/production work.

## Deliverables

- Small reviewed old-path reliability checkpoints only where required, one
  exact final-owner/caller/test cutover checkpoint, and one separate
  documentation/lifecycle close, sequentially published on the same branch.
- Final native assets under
  `src/norad/stages/preprocess_and_annotate_cohort_candidates/`, direct tests
  under `tests/stages/preprocess_and_annotate_cohort_candidates/`, and no live
  legacy path, duplicate, wrapper, or compatibility owner.
- Exact artifact transition, coverage accounting, supported commands,
  proportional full card-boundary validation, rollback/residue evidence, and a
  precise local fake-R/guarded-real-R fixture evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, exact barrier/input admission, manifest and
  upstream hash checks, R resolution, side-effect-free dry-run, execute bytes,
  candidate/annotation/count behavior, predecessor rules, controlled child/
  publication/restore failures, receipt visibility, mutation, locks/signals/
  concurrency, streams, exits, and unrelated files as required by review.
- R parity preserves exact tables, ordering, provisional policy, lexical and
  semantic VCF/count checks, annotation, header-only/multiallelic/skipped-
  allele behavior, streams/exits, and guarded real-R evidence without changing
  dependencies.
- Validator parity preserves arguments, five rows, dynamic schemas and counts,
  dry-run/execute/repeat effects, report bytes, stable-input/publication
  behavior, private report/Step `09c` ownership, and arbitrary-CWD use.
- Scheduler parity preserves mode, directives, submit CWD, modules/renv/R
  resolution, dry-run logs, delegation, three-output checks, streams, exits,
  and stale-output risk.
- Exact searches find one final owner and no undeclared old path, wrapper,
  duplicate, ambient import, stale command, or lifecycle link. Coverage and the
  complete gate satisfy reviewed policy without evidence overclaim.
- After separate documentation close, documentation validation has no
  migration-caused finding; inherited findings are reported exactly and never
  called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `08`
  final paths, shell/R/validator/scheduler commands, guarded-R route, and
  acceptance language in `RUNBOOK.md`; Step `08` lock/temp/partial/restore-
  failure/receipt, manifest/Step `07`/annotation mutation, relative-path,
  validation, R dependency, scheduler, and split-root recovery routes in
  `TROUBLESHOOTING.md`; directly impacted neutral-library, Step `07`
  predecessor, Step `09`/`09c` consumer, artifact-provenance, manifest, and
  guarded-R routes; this card; review lifecycle links; and the dated audit log.
  Update diagrams only if final inspection finds a material DAG or public-flow
  change.

## Escalation conditions

- Stop for an unmovable caller/import, required public package identity,
  permanent wrapper, second functional-owner migration, Step `09c` schema or
  policy extraction, R method/dependency change, artifact/schema redesign,
  parity that requires blessing a defect, missing high-risk rollback oracle,
  dependency or cluster/production action, or scope that cannot remain this one
  stage owner and its direct evidence wiring.

## Completion record

Selected as the sole active migration from clean, published,
local/upstream/live-remote-equal usability-review completion
`a8e7f0aa32e62cc9771277b9b6def7e08d8bd59e`. Architecture, reliability, and
usability reviews completed before execution. No Step `09` or later owner or
review card was created, selected, or preloaded.

- Published old-path checkpoints are runtime/input provenance `d29f87b`,
  transaction/recovery `44e649d`, signal/concurrency `6e2e2f6`, validator
  `3f02d19`, and scheduler `7a667ee`. Atomic executable/test checkpoint
  `5e51496fdef8835bdef297b946d99382ed24574b` moved exactly the eight reviewed
  assets and changed exactly the ten reviewed integration owners. It added no
  wrapper, alias, compatibility copy, package identity, descriptor, schema,
  recovery marker, policy change, Step `09c` extraction, or DAG change.
- Final native identities match review: shell mode/bytes/lines/SHA-256 is
  `0755` / `39,954` / `1,024` /
  `578542fefa02aa23667bb40e582cbab215e6d3efec0a7c2fbb002290f1cfc1f3`;
  R is `0644` / `69,505` / `1,939` /
  `50cae0523ea68f87535866cbe9e86d38c3812f96a2c8a06ebd66a72177268699`;
  validator is `0644` / `12,918` / `346` /
  `57a227c478c0caec60fe2ff8d84f7feb1fce28c5248338f1369b2a186284c78f`;
  and job is `0644` / `4,597` / `134` /
  `e51d0df86609ca5d3d39b60f6036ee225bc17c11b6a83d68c683603842c57de6`.
- Final-path acceptance passed the complete direct shell suite, all `17`
  owner-validator tests, and `597` integration/scheduler/report tests. The
  complete shell-contract lane and isolated existing-library Step `08` and
  Step `09` real-R semantic suites passed. Pinned report runtime passed `17`
  tests with `60` deselected. These are local fixture/fake-tool or local-runtime
  results, not scheduler, cluster, production, scientific-review, variant/
  editing-site, or biological evidence.
- Coverage with only the deliberately deferred documentation assertion
  deselected passed `1,219` tests with `17` skips. The moved validator is
  tracked at `162/167` lines and `42/48` branches; global floors are
  `9601/11758` lines and `3367/4784` branches. Every non-target tracked row
  stayed exact and the standalone policy comparison passed. Higher transient
  Step `09c` raw counts caused by early exact-file loading were deliberately
  not promoted into a non-target baseline.
- The aggregate gate was not green. Static preflight passed; guarded `r-check`
  failed status `2` after `5.615s` on the inherited ignored malformed `macos`
  library entry and unavailable Bioconductor DNS, cancelling other aggregate
  lanes. The orchestrator ended status `2` after `5.842s`; no dependency was
  installed, restored, removed, or changed. Separately passing lanes remain
  separate evidence. An untouched full Python run reached `1,219` passes and
  `17` skips before its sole documentation assertion listed twelve deliberately
  deferred MIG-03M links plus nine inherited `UNREFINED` locations.
- Preserved producer defects include receipt visibility before final
  validation/commit, missing sibling-output/R-runtime/package/attempt identity,
  admitted R-program mutation blindness, best-effort split-root restoration,
  cleanup after incomplete restore, and no durable recovery marker. Controlled
  publication exit `67` plus sites-restore exit `68` leaves the prior sites
  final absent with its backup retained while prior summary/receipt are
  restored, removes owned scratch/lock, and writes no marker. This is ambiguous
  preservation-first recovery evidence, not successful rollback.
- Preserved validator defects include exit-`0` failed rows, annotation spelling
  asymmetry, non-recomputed candidate IDs/order, upstream-hash trust, and
  semantic non-recomputation. Preserved scheduler defects include warning-only
  unusable Rscript, tolerated version failure, submit-CWD and body-level log
  effects, and stale-three-output false success. None is fixed, approved, or
  readiness evidence.
- The separate documentation/lifecycle close adds the owner README, repairs
  all twelve migration-caused links and final commands, updates current
  topology/status/evidence and recovery routes, records this audit evidence,
  and moves only this card to `COMPLETED`. No diagram changed because semantic
  identities, direct DAG edges, and public data flow did not change. Exact
  documentation validation retains only the nine inherited `UNREFINED`
  locations; that expected-only result remains nonpassing, never green.
- Git rollback order is this documentation close, executable `5e51496`,
  scheduler `7a667ee`, validator `3f02d19`, signal/concurrency `6e2e2f6`,
  transaction/recovery `44e649d`, then runtime/input `d29f87b`. Before runtime
  recovery or retry, preserve both roots, every final/scratch/backup/lock,
  manifests, Step `07` receipts/VCFs, annotation, R identity/library, streams,
  scheduler records/CWD, and unrelated bytes. Git rollback never alters
  runtime evidence. Publication and equality end this campaign boundary; no
  next owner is selected.
