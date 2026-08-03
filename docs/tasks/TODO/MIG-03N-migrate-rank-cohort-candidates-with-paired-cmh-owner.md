# MIG-03N — Migrate the paired-CMH cohort-ranking owner

## Objective

Move the complete `rank_cohort_candidates_with_paired_CMH` shell/R analysis
producer, validator, scheduler asset, and owner-local tests to their frozen
final analysis-owner homes while preserving every public, pairing, statistical,
transaction, validation, scheduler, artifact, real-R, independent-oracle, and
coverage contract.

## Why this exists

After the repository-health close at `57d7ea4`, the refreshed live required-
artifact DAG has exactly one eligible unmigrated owner:
`rank_cohort_candidates_with_paired_CMH`. Its Step `08` sites table and input
receipt predecessor is migrated. The Step `09c` scientific-review evidence
owner remains blocked on the complete six-output Step `09` transaction. No
Step `09c` migration or later owner card is created or selected. This card
defines Step `09` as the smallest next JIT unit but does not select it.

## Fixed decisions

- Frozen definition parent and rollback target:
  `57d7ea4f84d117dcca3586c9e5e4a32a6e69b63e`, the clean, published,
  local/upstream/live-remote-equal repository-health documentation close.
- Semantic identity is `rank_cohort_candidates_with_paired_CMH`, kind
  `analysis`, machine key
  `norad.analysis.rank_cohort_candidates_with_paired_CMH.v1`, historical alias
  `09`, final source home
  `src/norad/analyses/rank_cohort_candidates_with_paired_CMH/`, and mirrored
  test home `tests/analyses/rank_cohort_candidates_with_paired_CMH/`.
- Architecture-reviewed production moves are the mode-`0755` Bash transaction
  entry point
  `scripts/step_09_cmh_editing_site_calling.sh`, mode-`0644` R implementation
  `scripts/step_09_cmh_editing_site_calling.R`, mode-`0644` Python validator
  `scripts/validate_step_09_cmh_outputs.py`, and mode-`0755` scheduler entry
  point `jobs/step_09_cmh_editing_site_calling.slurm`, without changing
  basenames or modes. Preserve direct/Bash producer use, Rscript-only R use,
  explicit-interpreter validator use, and `sbatch` or explicit-Bash job use.
- The four native assets total `127,393` bytes and `3,081` lines. Frozen
  SHA-256 values are shell
  `87efee38a716270584827be87066891bfb0c12e0fd27959dfe3787aa0b2200f5`,
  R implementation
  `8c422a2e93adb35f0fd48e554293ba01ec7497b04eeab27a20f750bd3016641c`,
  validator
  `1b24184273a33b9e0389de12816b78ce396d408319556141dad6b66a0c5957ba`,
  and job
  `5d78f88bc0eed7e48821d7abaf7986c9f38c49ebbb7191b90729a08ea9124049`.
- Architecture-reviewed owner-local protection moves are the mode-`0755` shell
  test
  `tests/shell/test_step_09_cmh_editing_site_calling.sh`, mode-`0755` guarded-R
  runner `tests/r/run_step_09_cmh_tests.sh`, mode-`0644` R semantic test
  `tests/r/test_step_09_cmh_editing_site_calling.R`, mode-`0644` validator test
  `tests/test_validate_step_09_cmh_outputs.py`, mode-`0644` independent-oracle
  test `tests/test_step_09_cmh_oracle.py`, mode-`0644` independent oracle
  `tests/tools/step_09_cmh_oracle.py`, and mode-`0644` golden corpus
  `tests/fixtures/step_09_cmh_oracle.tsv`. Their frozen hashes are respectively
  `73b378453d7f1cc043a2366da4c000617cc2be43cc89343c94dd870d185760dc`,
  `53956688c2216b799daf58187f48c846923a3dde758a69d7a5d719448096e2cb`,
  `aed284fac43c5a4837f09d36ae7cb4d90b5d55ab4fa7a380dec2c7a68188460c`,
  `bd08e4ad4bcbd1b12e4ac9ab0b28b746fe4c4742cac9325a65366cde31271f1e`,
  `e7a2906052c1ae81f56e11b2698a253652a91af42076edc5e570e772379a1b57`,
  `c0888fcf97204b04d78fb02089a25e0d164108ad80b34dfa9253d885406a8438`,
  and `61dd40ca6a128cc06c5457d963d4569484512f34b57fbf544cf4608c01a429e7`.
  These seven files total `125,573` bytes and `3,111` lines. All seven belong
  in the mirrored analysis-test owner: the R runner/test, Python oracle/test,
  and golden corpus are Step `09`-specific and no other tracked owner consumes
  the oracle implementation. The R semantic test alone also consumes the
  corpus. Exact tracked-path and target-root searches find no Step `09` pending
  scaffold; the existing final `CONTRACT.md` is documentation, not a second
  executable or test owner.
- The architecture-reviewed executable cutover is exactly eleven moves plus
  ten explicit integration owners: `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/shell/test_local_r_environment.sh`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`.
  Exact tracked-path, basename, import, Make, R, job, artifact, and test
  searches prove the full caller/import/test set and no eleventh integration
  owner. The artifact test adds the exact final Step `09` producer path/hash
  assertion even though it has no old producer literal. The unchanged
  `tests/test_report_exports_v1.py` basename occurrence is a negative rendered-
  report assertion, not a path consumer. The unchanged Step `09c` and run-
  summary imports consume the still-flat Step `09c` contract owner, not the
  moved Step `09` implementation. A twelfth move, eleventh integration update,
  or different production file reopens architecture review.
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
  plus readiness marker `_NORAD_STEP09C_CONTRACTS_READY`, removes its own
  partial cache entry on failure, and reports sanitized exit-`2` diagnostics.
  The neutral report bridge changes only `parents[1]` to `parents[4]` while
  retaining its existing private identity, readiness, cache, and failure
  behavior.
- Exact reviewed path/root edits project final native values: shell mode
  `0755`, `58,279` bytes / `1,331` lines / SHA-256
  `7926d13bd9f0192522a20224c24716b7b8dca7a1348803cb7e8aefa1b056123a`;
  R program mode `0644`, `48,993` bytes / `1,205` lines /
  `f429fa71d91794f0a5f3bf4c77c7ce1981cbf5ebe98ea1ab50302dda2b18d1dc`;
  validator mode `0644`, `18,201` bytes / `487` lines /
  `ab14263de43d624f39490e080ead040309d9584d6bf08f101346192a8758763a`;
  and job mode `0755`, `4,387` bytes / `121` lines /
  `d84cfbd9afe3822b7abe8e1e5a249444801030387c77c46a29ca61cd97dcc677`.
  Any production hash, byte, line, or mode difference reopens architecture
  review.
- The moved shell test resolves repository root with `../../..`, targets the
  final producer/job/R paths, and constructs its delegated-job fixture at the
  exact final child path. The moved guarded-R runner resolves root with
  `../../..`, targets the owner-local R test and final R program, and remains
  the Make/local-R route. The R test resolves root with three parent segments,
  targets the final R program, and consumes the owner-local golden corpus. The
  moved validator test uses `parents[3]`, targets the final validator, and
  exact-loads root `tests/validation_roster_expectations.py` without ambient
  import or global path mutation; its existing exact Step `09c` fixture loader
  remains private and dataclass-safe. The moved oracle test uses `parents[3]`
  and sibling oracle/corpus paths under its owner. The oracle implementation
  and corpus move byte-identically.
- Make moves the shell, validator, and guarded-R runner recipes; the central
  local-R oracle changes only its expected Step `09` test path. Once the shell
  and job leave flat wildcards, their exact final paths enter both
  `validation-static` and `smoke` plus the literal Make expansion evidence.
  Public CLI, R, SLURM, validation roster, neutral report, artifact producer,
  and coverage routes remain explicit rather than adding recursive discovery.
- Preserve shell CLI/help, safe analysis/cohort IDs, explicit sample and
  partition manifests, Step `08` root, output root, control/treatment and
  optional background conditions, target RNA substitution, thresholds,
  Rscript/R-program resolution, side-effect-free shell dry-run, exact manifest
  pairing authority, repeated input stability checks, streams, exits, and
  current local fake-R evidence.
- Reliability-reviewed runtime/input checkpoint: in the existing old-path
  shell test only, freeze missing/nonexecutable explicit Rscript, missing R
  program, basename/PATH resolution from arbitrary CWD, and separate mutation
  of sample manifest, partition manifest, Step `08` sites, and Step `08` input
  receipt. Each admitted-input mutation must fail without finals or owned
  residue and preserve unrelated bytes. A selected-R-program mutation after
  admission must retain the current exit-`0` publication, and the summary must
  remain without Rscript/R-program/package, attempt, or five sibling-output
  hash identity. These are defects/evidence ceilings, not new guarantees.
- Preserve the R implementation's exact pairing validation, minimum two paired
  strata, count-table construction, two-sided continuity-corrected
  `stats::mantelhaen.test`, failed/degenerate characterization, one global
  Benjamini-Hochberg family, strict thresholds, result ordering, exact status
  classification, summaries, mutation spectrum, plots, and header-only
  behavior. Relocation changes no R dependency, method, policy, schema,
  threshold, or scientific meaning.
- Preserve exact evidence language. Outputs are CMH-ranked cohort candidates,
  not validated RNA-editing sites. `legacy_provisional_v1` remains upstream
  compatibility metadata, not validated strand, sense/antisense interpretation,
  variant/editing-site proof, completed scientific review, or biological
  readiness.
- Preserve the analysis lock, run-token scratch/backups, all-six-or-none
  predecessor rule, temporary validation, publication order, summary-last
  native marker, final validation and hash rechecks, predecessor replacement,
  retained recovery evidence after incomplete restoration, cleanup, and signal
  traps. Reliability review owns exact child/publication/restore failure,
  summary visibility, signal, lock/concurrency, stale-path, unrelated-byte,
  residue, input-mutation, and absent-attempt/sibling-identity oracles without
  fixing or blessing any state.
- Reliability-reviewed transaction checkpoints: the old-path shell test must
  prove exact publication order—all-sites, significant-sites, mutation TSV,
  mutation PDF, depth PDF, summary—then barrier-observe all six finals, the
  lock, and six predecessor backups after summary publication but before final
  validation/hash commit. A separate `TERM` case at that barrier must exit
  `143` and restore all six predecessors, while a fake-R barrier must prove
  one same-analysis contender loses on the lock and the released winner alone
  publishes. Preserve existing incomplete-restoration evidence: one absent
  final, its exact backup and owned lock retained, five exact restored finals,
  no owned temps, and no claim that a visible summary is committed evidence.
- Preserve the exact six-output transaction under
  `<output-root>/<analysis-id>/`: all-sites TSV, significant-sites TSV,
  mutation-spectrum TSV/PDF, depth/delta PDF, and summary TSV. Preserve exact
  headers, complete Step `08` candidate universe/order, significant subset,
  pairing and policy identity, input paths/hashes, counts, statuses,
  statistics, plots, and header-only validity.
- Preserve producer/validator asymmetry. The validator invokes no R, publishes
  seven exact rows, may exit `0` with failed evidence, derives BH only from
  reported p-values, and does not independently recompute count-table
  estimability, CMH statistic, p-value, or common odds ratio. Its current
  `status_semantics` expected text overstates that evidence by saying CMH was
  recomputed; preserve and characterize that defect rather than silently
  blessing or repairing it. The independent Python oracle and guarded real-R
  corpus remain separate evidence owners.
- Preserve the seven validator check IDs: `output_transaction`,
  `upstream_identity_and_candidate_order`, `status_semantics`,
  `significant_subset`, `summary_count_reconciliation`,
  `mutation_spectrum_reconciliation`, and `pdf_structure`; common report bytes;
  stable-input recheck; report publication; streams; and exits. Shared Step
  `09` schema/validation functions remain physically owned by flat Step `09c`;
  this migration does not extract, redesign, or reassign them.
- Reliability-reviewed validator checkpoint: add arbitrary-CWD dry-run/
  execute/repeat byte parity, post-build mutation of each of the ten admitted
  inputs as exit `2` with predecessor report preservation, and an all-pass
  fabricated-but-self-consistent CMH statistic/p-value/BH/odds-ratio case that
  freezes the non-recomputation ceiling. Existing cases already expose each of
  the seven exact rows as exit-`0` failed evidence. At cutover, add exact Step
  `09c` private-loader initialization/cache/spec/loader/execution/cleanup/
  sanitization and unchanged-`sys.path` coverage; common report faults remain
  owned by the neutral report suite.
- Preserve scheduler mode/directives, submit-directory fallback, analysis/
  cohort/input/output/condition/threshold/R defaults, tolerated module
  diagnostics, explicit execute gate, delegation, streams/exits, six-file
  post-check, and body-level `logs/` behavior. Reliability review must
  disposition missing/unusable Rscript or R program, child, stale-complete-
  output, and submitted-job states without hardening them.
- Reliability-reviewed scheduler checkpoint: in the central scheduler test
  only, freeze child-owned handling/unchanged forwarding for missing,
  nonexecutable, and PATH-basename Rscript selections plus a missing R
  program; absent-`SLURM_SUBMIT_DIR` launch-CWD fallback; dry-run `logs/`-only
  mutation; and stale-six-output false success after an exit-`0`, no-output
  child. The job has no Rscript version probe, package activation, or submitted-
  job evidence; do not add or imply any.
- `STEP_PRODUCERS["09"]` changes only to the final shell producer path.
  Preserve artifact IDs, schemas, Step `09` native/report identities, ordering,
  reconciliation, consumers, and scientific meaning. Step `09c` remains the
  scientific-review fan-in and must not move with this owner.
- Frozen starting coverage is validator `154/158` covered lines and `34/40`
  branches with global floors `9601/11758` lines and `3367/4784` branches.
  Final measurement must retain target rates, keep every non-target row exact,
  and preserve global covered-count floors after the path move.
- Old and final executable/test paths may not coexist. After reviewed
  reliability baselines, apply all eleven moves, ten integrations, and exact
  production/test path and loader edits atomically. Reverse rollback restores
  documentation last-in-first-out, then the eleven-move/ten-update cutover,
  then any test-only reliability checkpoints in reverse order. No wrapper,
  alias, symlink, compatibility copy, descriptor, schema, or future-owner
  preload is justified.
- Publish exactly five small old-path test-only checkpoints in order: runtime/
  input provenance, publication order, signal/concurrency, validator, and
  scheduler. Only the existing direct shell test, direct validator test, and
  central scheduler test may change. The guarded-real-R and independent-
  oracle assets already cover the statistical path and receive no test-only
  checkpoint. Add no fixture, fourth test owner, production change, coverage
  change, documentation batch, dependency action, or future-card content in
  those slices.
- Use only minimal old/final focused checks inside executable slices. Run the
  complete applicable computational gate once at the assembled executable card
  boundary, then batch canonical paths, commands, migration links, small
  documentation updates, lifecycle repair, and audit evidence in a separate
  close.
- Add one adjacent owner `README.md` only at documentation close. It must route
  shell/R/validator/scheduler root and arbitrary-CWD journeys, pairing/policy
  meaning, R/input/output/lock/summary choices, six-file recovery and residue
  preservation, focused shell/Python/guarded-R/oracle tests, artifact
  provenance, Git rollback, and the local fixture-only evidence ceiling.
- Add no descriptor, schema, package marker, wrapper, compatibility copy,
  symlink, transaction/summary/recovery redesign, shared-schema extraction,
  scheduler abstraction, statistical/policy change, dependency action, public
  library API, or Step `09c` migration.

## Blocked by

- [REVIEW-UX-03N](../IN_PROGRESS/REVIEW-UX-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of recovery, index-lock, or overlapping mutable-lane state
  before selection or executable mutation.
- Refresh only the named native assets, explicit callers/imports, modes, hashes,
  test helpers/corpus, Step `09c`/report bridges, artifact evidence, coverage
  row, active documentation, and applicable Step `09` failure/recovery states.
- Establish identical-input old-path baselines without dependency installation,
  R restoration, scheduler submission, production input, or scientific/
  biological evidence.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `09`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the colocated analysis contract;
  `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- Shell/R producer, validator, job, seven candidate owner-local protection
  assets, central scheduler and guarded-R environment suites, neutral
  validation-report suite, flat Step `09c` shared-contract implementation,
  public CLI/roster maps, Make/literal fixture, artifact mapping/reconciliation,
  coverage baseline, manifests, and current Step `08`/transaction diagnostics.

## Questions owned by this card

- None after the three dedicated reviews close. Architecture owns exact move/
  caller/loader/test/artifact boundaries; reliability owns transaction,
  restoration, mutation, R/oracle semantics, validator, and scheduler oracles;
  usability owns final commands, scientific language, R/input/output/lock/
  summary choices, recovery navigation, and evidence language.

## In scope

- Freeze exact paths, modes, hashes, callers/imports, artifacts, helper
  identities, defects, parity rows, coverage counts, and rollback evidence
  before mutation.
- Move only this analysis owner and its reviewed direct tests, cut over every
  reviewed explicit caller, and make only reviewed path/root/private-loader
  changes in production.
- Validate executable slices minimally, run the complete applicable gate at the
  card boundary, and publish executable and documentation checkpoints
  separately before considering another owner.

## Out of scope

- Migrating or redesigning Step `09c` or another owner; changing R
  dependencies, pairing, count-table/CMH/BH/statistical semantics, statuses,
  thresholds, inputs, locks, output/summary placement, transaction, validation,
  artifact, or scheduler policy; schema/helper extraction; dependency
  installation/restoration; or cluster/production work.

## Deliverables

- Small reviewed old-path reliability checkpoints only where required, one
  exact final-owner/caller/test cutover checkpoint, and one separate
  documentation/lifecycle close, sequentially published on the same branch.
- Final native assets under
  `src/norad/analyses/rank_cohort_candidates_with_paired_CMH/`, direct tests and
  their owner-specific oracle/corpus under
  `tests/analyses/rank_cohort_candidates_with_paired_CMH/`, and no live legacy
  path, duplicate, wrapper, or compatibility owner.
- Exact artifact transition, coverage accounting, supported commands,
  proportional full card-boundary validation, rollback/residue evidence, and a
  precise local fake-R/guarded-real-R/independent-oracle evidence ceiling.

## Acceptance evidence

- Old/final parity covers CLI/help, pairing/input admission, manifest and Step
  `08` hash checks, R resolution, side-effect-free shell dry-run, execute bytes,
  CMH/BH/status behavior, predecessor rules, controlled child/publication/
  restore failures, summary visibility, mutation, locks/signals/concurrency,
  streams, exits, and unrelated files as required by review.
- R/oracle parity preserves exact tables, ordering, pairings, count-derived
  method, statuses, thresholds, BH family, plots, streams/exits, and guarded
  real-R evidence without changing dependencies.
- Validator parity preserves arguments, seven rows, dynamic schemas and counts,
  dry-run/execute/repeat effects, report bytes, stable-input/publication
  behavior, private report/Step `09c` ownership, evidence ceilings, and
  arbitrary-CWD use.
- Scheduler parity preserves mode, directives, submit CWD, module/R resolution,
  dry-run logs, delegation, six-output checks, streams, exits, and stale-output
  risk.
- Exact searches find one final owner and no undeclared old path, wrapper,
  duplicate, ambient import, stale command, or lifecycle link. Coverage and the
  complete gate satisfy reviewed policy without evidence overclaim.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` where implemented
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `09`
  final paths, shell/R/validator/scheduler commands, guarded-R/oracle routes,
  and acceptance language in `RUNBOOK.md`; Step `09` lock/temp/partial/restore-
  failure/summary, manifest/Step `08` mutation, relative-path, validation,
  R-runtime, scheduler, and six-file recovery routes in `TROUBLESHOOTING.md`;
  directly impacted Step `08` predecessor, Step `09c` consumer, artifact-
  provenance, manifest, local-R, and report-validation routes; this card; review
  lifecycle links; and the dated audit log. Update diagrams only if final
  inspection finds a material DAG or public-flow change.

## Escalation conditions

- Stop for an unmovable caller/import, required public package identity,
  permanent wrapper, second functional-owner migration, Step `09c` schema or
  policy extraction, R method/dependency change, artifact/schema redesign,
  parity that requires blessing a defect, missing high-risk rollback oracle,
  dependency or cluster/production action, or scope that cannot remain this one
  analysis owner and its direct evidence wiring.

## Completion record

Not selected. Defined from clean, published repository-health close
`57d7ea4`; no executable/test file changed or ran, and no Step `09c` migration
or later owner card was created.
