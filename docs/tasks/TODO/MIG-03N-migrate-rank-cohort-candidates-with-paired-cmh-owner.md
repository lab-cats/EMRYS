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
- Candidate production moves are the mode-`0755` Bash transaction entry point
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
- Candidate owner-local protection moves are the mode-`0755` shell test
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
  These seven files total `125,573` bytes and `3,111` lines. Architecture
  review must prove whether all seven belong in the mirrored owner and that no
  Step `09` pending scaffold exists.
- The evidence-backed cutover hypothesis is eleven moves plus ten explicit
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
  must add an exact final Step `09` producer path/hash assertion even if no old
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
- Preserve shell CLI/help, safe analysis/cohort IDs, explicit sample and
  partition manifests, Step `08` root, output root, control/treatment and
  optional background conditions, target RNA substitution, thresholds,
  Rscript/R-program resolution, side-effect-free shell dry-run, exact manifest
  pairing authority, repeated input stability checks, streams, exits, and
  current local fake-R evidence.
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
- Preserve scheduler mode/directives, submit-directory fallback, analysis/
  cohort/input/output/condition/threshold/R defaults, tolerated module
  diagnostics, explicit execute gate, delegation, streams/exits, six-file
  post-check, and body-level `logs/` behavior. Reliability review must
  disposition missing/unusable Rscript or R program, child, stale-complete-
  output, and submitted-job states without hardening them.
- `STEP_PRODUCERS["09"]` changes only to the final shell producer path.
  Preserve artifact IDs, schemas, Step `09` native/report identities, ordering,
  reconciliation, consumers, and scientific meaning. Step `09c` remains the
  scientific-review fan-in and must not move with this owner.
- Frozen starting coverage is validator `154/158` covered lines and `34/40`
  branches with global floors `9601/11758` lines and `3367/4784` branches.
  Final measurement must retain target rates, keep every non-target row exact,
  and preserve global covered-count floors after the path move.
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

- [REVIEW-UX-03N](REVIEW-UX-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

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
