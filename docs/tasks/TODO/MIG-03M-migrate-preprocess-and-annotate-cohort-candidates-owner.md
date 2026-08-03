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
- Candidate production moves are the mode-`0755` Bash transaction entry point
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
- Candidate owner-local protection moves are the mode-`0755` shell test
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
  Architecture review must prove whether all four belong in the mirrored owner
  and that no Step `08` pending scaffold exists.
- The evidence-backed cutover hypothesis is eight moves plus ten explicit
  integration owners: `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/shell/test_local_r_environment.sh`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`.
  Architecture review must prove the full caller/import/test set, exact move
  count, and logical-file ceiling before execution planning. Artifact evidence
  must add an exact final Step `08` producer path/hash assertion even if no old
  literal currently exists in that test.
- Production path edits are limited to shell/R usage text, validator owner-root
  and exact-file dependency resolution, and scheduler R/child defaults. The
  shell and R implementation remain siblings. The validator must continue to
  exact-load neutral `src/norad/libraries/validation_report.py` and must replace
  its ambient sibling import of flat
  `scripts/step_09c_scientific_validation.py` with a private exact-file bridge,
  without moving or changing the Step `09c` owner, adding `PYTHONPATH`, changing
  global `sys.path`, or creating a public package identity. Architecture review
  owns exact identities, cache/path/failure behavior, root depths, and projected
  final hashes.
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
- Preserve scheduler mode/directives, submit-directory fallback, cohort/input/
  annotation/output/QC/R defaults, tolerated module diagnostics, optional
  repository-local R environment, explicit execute gate, delegation, streams/
  exits, three-file post-check, and body-level `logs/` behavior. Reliability
  review must disposition missing/unusable Rscript or R program, module/renv,
  child, stale-complete-output, and submitted-job states without hardening them.
- `STEP_PRODUCERS["08"]` changes only to the final shell producer path.
  Preserve artifact IDs, schemas, Step `08` native/report identities, ordering,
  reconciliation, consumers, and scientific meaning. Architecture review must
  resolve and preserve the existing distinction between the producer's input-
  receipt native marker and the artifact adapter's summary failure marker.
- Frozen starting coverage is validator `122/129` covered lines and `26/36`
  branches with global floors `9561/11720` lines and `3351/4772` branches.
  Final measurement must retain target rates, keep every non-target row exact,
  and preserve global covered-count floors after the path move.
- Once shell/job leave flat wildcards, add exact final paths to
  `validation-static`/`smoke` and the literal Make oracle. Move shell, validator,
  and guarded-R recipes; preserve the exact guarded environment and update the
  local-R evidence oracle. Keep public CLI, R, SLURM, validation, neutral report,
  Step `09c` bridge, artifact, and coverage routes explicit rather than adding
  recursive discovery.
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

- [REVIEW-UX-03M](REVIEW-UX-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

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

Not selected. Defined from clean, published, local/upstream/live-remote-equal
`MIG-03L` documentation checkpoint `4562ec3`. All three dedicated review cards
remain unselected in `TODO`; no executable/test path changed, no computational
test ran, and no Step `09` or later owner is preloaded.
