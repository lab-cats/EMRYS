# MIG-03E — Migrate the construct-FASTA-sidecars owner

## Objective

Move the complete `construct_FASTA_sidecars` producer, validator, scheduler
asset, and owner-local tests to their frozen final homes while preserving
current public, validation, reference-sidecar, scheduler, artifact, and
coverage contracts.

## Why this exists

After `MIG-03D`, both `construct_FASTA_sidecars` and
`construct_canonical_BAM` are data-DAG eligible. Select only
`construct_FASTA_sidecars`: it has no hard stage predecessor and no peer stage
imports its implementation. `construct_canonical_BAM` is not migration-ready
because the Step `04` and Step `05` validators still import helpers directly
from its stage-named validator. This selection follows the semantic DAG and
target dependency direction, not historical alias order or raw file size.

## Fixed decisions

- Frozen parent and rollback target:
  `5259acbf3b717487e78eecfd938cc793665673f8`, the clean, published,
  local/upstream/live-remote-equal `MIG-03D` documentation close on the one
  active campaign branch.
- Semantic identity is `construct_FASTA_sidecars`, machine key
  `norad.stage.construct_FASTA_sidecars.v1`, historical alias `00c`, with final
  source home `src/norad/stages/construct_FASTA_sidecars/` and mirrored test
  home `tests/stages/construct_FASTA_sidecars/`.
- Move the mode-`0755` shell producer
  `scripts/step_00c_prepare_gatk_reference.sh`, mode-`0644` Python validator
  `scripts/validate_step_00c_reference_sidecars.py`, and mode-`0755` scheduler
  entry point `jobs/step_00c_prepare_gatk_reference.slurm` to the final owner
  without renaming their basenames or changing modes.
- Move the mode-`0755` direct shell test
  `tests/shell/test_step_00c_prepare_gatk_reference.sh` and mode-`0644` direct
  validator test `tests/test_validate_step_00c_reference_sidecars.py` to the
  mirrored owner home. Keep Step `00c` scheduler behavior in the independent
  cross-owner wrapper suite because it shares the parametrized harness.
- Preserve the producer's arguments, explicit tool-resolution precedence,
  dry-run default, execute control, Java/GATK probes, command bytes, output
  names, validation, reuse, lock ownership, temporary naming, streams, exits,
  and cleanup. Its self-identifying help path must name the final producer; any
  other source change requires a review finding.
- Preserve rather than approve the producer's nontransactional two-sidecar
  publication: when the final FAI move succeeds and final DICT move fails, the
  first final can remain without the second and no receipt or recovery marker
  is created. Reviews must assign an old/final-path fault oracle before cutover.
- Change the validator's exact neutral validation-report lookup only as
  required by final owner depth. Preserve its mode, public basename, five check
  IDs, report bytes, dry-run/execute behavior, and publication semantics.
- Do not move, duplicate, or redesign `scripts/reference_provenance.py` in this
  unit. Replace the moved validator's ambient sibling import with one private
  caller-local exact-file bridge to that existing path. Freeze the private
  module identity as `_norad_reference_provenance`, resolve the exact repository
  path independently of caller CWD, and treat `ProvenanceError`, `parse_fasta`,
  `parse_fai`, and `parse_dict` as the complete required API. The bridge verifies
  cached `__file__`, requires `ProvenanceError` to be an exception type and the
  three parser symbols to be callable, rejects wrong or partial cache state,
  removes only its owned partial state on execution failure, preserves foreign
  state, leaves `sys.path` unchanged, and fails before report publication with
  `ERROR: unable to load NORAD reference-provenance owner at <path>: <type>: <reason>`.
  No readiness sentinel may be added to the separate owner merely for this move.
- Keep the public reference-provenance CLI, its direct test and coverage row,
  and the separate Step `05` consumer unchanged. This temporary mixed-layout
  dependency does not approve a library extraction, package identity, or
  permanent target topology; it is an explicit deferred coupling.
- Extend the moved validator suite with a non-repository-CWD dry-run, execute,
  and repeat journey using absolute inputs plus exact reference-owner loading.
  Freeze exit/stream parity, five ordered rows, deterministic bytes, stable
  repeat replacement, no invocation-directory residue, and fail-closed missing,
  wrong-cache, and partial-load states identified by review.
- The owner-local validator suite must exact-load the validator in process to
  exercise the private reference loader. Cover healthy exact-path reuse,
  missing owner, foreign wrong-path cache, correct-path incomplete API, and an
  injected owned execution failure; preserve every preexisting cache object,
  remove only the loader-created partial, prove `sys.path` equality, and prove
  no report or invocation-CWD residue. The public reference-provenance suite is
  not reused as this expectation and remains unchanged.
- Change the scheduler's delegated producer argument to the exact final path.
  Preserve all seven directives, fallback `SLURM_SUBMIT_DIR` behavior, strict
  mode, tolerated module calls, CSU defaults and overrides, Java discovery and
  version validation, `EXECUTE` handling, logs, output checks, streams, exits,
  executable mode, and the Bash `3.2` empty-array dry-run defect.
- Final public instructions must use complete commands. From repository root,
  document direct and explicit-`bash` producer forms with the reference and
  explicit tool paths. From another CWD, require an absolute checkout path and
  explicit absolute reference/tool paths. Document the mode-`0644` validator
  only through an explicit interpreter and exact final path.
- The supported scheduler journey creates `logs/`, changes to the intended
  checkout, and submits the exact final job. State that `EXECUTE=0` is default,
  Bash `3.2` can stop before delegation, `EXECUTE=1` is required to publish,
  current CSU tool defaults are site bindings, modules are tolerated, and the
  wrapper checks only that the two declared output files are nonempty.
- No legacy wrapper is required. Every named source-path caller is repository-
  owned and can cut over in one atomic executable/test commit; a wrapper would
  preserve accidental flat placement without an unmovable consumer.
- `STEP_PRODUCERS["00c"]` intentionally changes to the final producer path.
  Preserve status, evidence ID, Git commit projection, artifact identities,
  schemas, ordering, contents, reconciliation, and consumers. The old producer
  SHA-256
  `f041c55a0e9a3b36c14dcc9b929cfa56190e1c00d23a5a62fa72ac3669f0c478`
  is rollback evidence because the help path must change; record and assert the
  reviewed final hash after cutover.
- Coverage already uses stable roots `scripts` and `src/norad`. Move the
  validator's tracked `90/96` line and `23/26` branch row to its final path only
  after inspected final-path measurement proves exact or improved counts and
  global non-regression. Any review-required loader branches must be measured
  and explained rather than hidden by a path rename.
- Once both shell assets leave the flat wildcards, add their exact final paths
  to `validation-static` and `smoke` shell-syntax commands and to the literal
  Make expansion oracle. Move the shell-test and validator-test recipe paths.
  Publish a focused validation block that runs the moved shell suite, moved
  validator suite, and independent central scheduler suite by exact path.
- Existing public-CLI, SLURM, validator, loader, artifact, coverage, and Make
  inventories must retain explicit basename or semantic-ID path maps and exact
  one-owner equality. Do not introduce recursive runtime discovery, alias-
  derived placement, package identity, installation, or global path mutation.
- In the shared validation-report suite, route the final Step `00c` validator
  through the existing path-validating exact-file test loader already used by
  other non-flat validators. Keep module-name import only for validators whose
  declared parent remains `scripts/`; do not add a Step-specific loader or test
  framework.
- The existing `CONTRACT.md` remains the detailed behavior owner. Add one
  concise owner `README.md` only at the documentation close. It must route
  final commands, FAI/DICT diagnostics, dry-run guarantees, partial-publication
  preservation, scheduler caveats, validation evidence, rollback,
  implementation-provenance transition, and the local-only migration evidence
  ceiling. Do not add a descriptor/schema, scheduler abstraction, transaction,
  receipt, recovery marker, or reference-provenance extraction.

## Blocked by

- [REVIEW-UX-03E](../IN_PROGRESS/REVIEW-UX-03E-review-construct-fasta-sidecars-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, live-remote-
  equal, and free of merge/rebase/cherry-pick/revert, index-lock, recovery, or
  overlapping mutable-lane state before selection or executable mutation.
- Refresh only the named path/import consumers, modes, hashes, Make/static/
  coverage wiring, artifact evidence, and active documentation for this owner.
- Establish identical-input pre-move baselines for producer, validator,
  reference-provenance loading, and mocked scheduler behavior without SLURM
  submission, real GATK/samtools work, production inputs, dependency
  installation, or dependency restoration.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `00c`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `construct_FASTA_sidecars` contract; the
  functional-owner inventory; and `TEST_BASELINE.md`.
- The producer, validator, scheduler job, both direct tests, Step `00c` behavior
  in `test_slurm_wrapper_contracts.py`, public-CLI and validator-roster suites,
  and the shared validation-report loader/fault matrix.
- `scripts/reference_provenance.py`, its direct fault suite and public CLI
  contract, plus the separate Step `05` consumer that must remain unchanged.
- `STEP_PRODUCERS["00c"]`, artifact-provenance tests, coverage
  config/tool/tests/baseline, Make static/smoke/shell-test recipes, and the
  literal Make-expansion fixture.
- All nonhistorical Markdown links and supported commands naming the producer,
  validator, scheduler job, or focused tests. Public artifacts and the semantic
  DAG remain unchanged unless review finds contrary evidence.

## Questions owned by this card

- None.

## In scope

- Freeze exact invocation/import graphs, paths, modes, hashes, defects, parity
  rows, coverage counts, and rollback evidence before source mutation.
- Move the producer, validator, and scheduler entry point once to the final
  owner; make only the reviewed self-path, final-owner relative-path,
  reference-provenance exact-bridge, and job-delegation edits.
- Move the two direct tests. Keep independent cross-owner scheduler, roster,
  CLI, loader, artifact, Make, and coverage suites as explicit path-aware
  consumers.
- Cut over every named repository caller in one atomic executable/test commit,
  including Make/static/smoke, literal expansions, artifact provenance, public
  CLI, SLURM roster, validator roster, shared loader, direct tests, and tracked
  coverage path.
- Freeze that atomic write set to exactly fourteen tracked files: five moves
  (producer, validator, job, shell test, validator test) plus `Makefile`,
  `scripts/build_artifact_index.py`, `tests/test_artifact_adapters.py`,
  `tests/test_public_cli_contracts.py`, `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`. Any
  fifteenth executable/test path requires a recorded review correction before
  mutation.
- Update the moved shell test's repository-root calculation and native-asset
  paths and the moved Python test's repository-root calculation and validator
  path. These are relocation edits; the production diff is limited to the
  producer help self-path, both validator owner/dependency resolutions, the
  private reference-provenance loader, and the scheduler delegated child path.
- Extend old/final parity only where sequential reviews identify a missing
  named behavior. Measure coverage and run the complete applicable local gate
  once on final executable state at the card boundary.
- Before cutover, use a temporary old-path fake-`mv` probe that fails only the
  final DICT publication after the final FAI publication. Freeze a nonzero exit,
  nonempty final FAI, absent final DICT, removed owned lock, and no run-token
  temporary paths. Add the equivalent case to the moved shell suite and rerun
  it on the final path; do not delete or relabel the retained FAI as successful
  transaction output.
- After executable state is fixed, batch the owner README, migration path/link
  repairs, topology/status/evidence owners, lifecycle links, and dated audit
  updates into one separate documentation-close commit.

## Out of scope

- Moving, extracting, packaging, or changing `reference_provenance.py`, its
  CLI, its tests, its coverage row, or its Step `05` consumer.
- Moving `construct_canonical_BAM`, another functional owner, or any Step `05`
  asset; extracting BAM helpers; or correcting a peer implementation import.
- Changing sidecar names, contig rules, tool/version requirements, reuse,
  overwrite, lock, temp, cleanup, stream, exit, or dry-run semantics.
- Making FAI/DICT publication atomic; adding a receipt, recovery marker,
  rollback restoration, new no-clobber policy, or automatic cleanup of
  ambiguous final artifacts.
- Correcting the scheduler's Bash `3.2` empty-array defect, site defaults,
  tolerated modules, Java policy, fallback submit-CWD behavior, or file-only
  post-validation.
- Changing validator checks, parser semantics, report ordering, stable-input
  recheck, publication faults, or the neutral validation-report library.
- Adding packages, descriptors, schemas, wrappers, symlinks, compatibility
  copies, global path mutation, dependency actions, cluster/production work,
  scientific claims, or unrelated harness redesign.

## Deliverables

- One atomic final-owner/caller/test/harness cutover commit and one separate
  documentation/lifecycle-close commit, both published sequentially.
- Final producer, validator, and job under
  `src/norad/stages/construct_FASTA_sidecars/`; direct owner tests under
  `tests/stages/construct_FASTA_sidecars/`; no legacy path, wrapper,
  compatibility copy, duplicate implementation, package marker, descriptor,
  or schema.
- Explicit mixed-layout caller/import inventories, exact artifact-evidence
  transition, coverage rename accounting, supported final commands, exact
  searches, complete applicable local validation at the card boundary, clean
  publication equality, and a precise local-only evidence ceiling.

## Acceptance evidence

- Producer parity preserves mode `0755`, direct and explicit-`bash` help,
  missing/malformed arguments, arbitrary CWD, tool precedence, dry-run/execute,
  existing-sidecar reuse, one-missing generation, version failures, contig
  validation, commands, output names, locks, temp paths, streams, exits,
  cleanup, and the characterized partial-final publication defect apart from
  the displayed final self-path.
- Validator parity preserves mode `0644`, explicit-interpreter/arbitrary-CWD
  behavior, all arguments, five ordered rows, dry-run/execute/repeat effects,
  deterministic bytes, streams/exits, stable-input recheck, locks, foreign
  state, and validation-report identity. Its new private reference-provenance
  bridge proves exact healthy, missing, wrong-cache, partial-load, foreign-
  state, and unchanged-`sys.path` outcomes without moving that owner.
- Scheduler parity preserves mode `0755`, seven directives, strict mode,
  fallback submit CWD, tolerated samtools module policy, CSU defaults and
  overrides, Java selection/version, `EXECUTE`, logs, exact final child path,
  streams, failures, wrapper file checks, and the Bash `3.2` dry-run defect.
- The partial-publication oracle proves the exact FAI-only residue and owned
  cleanup state on both paths. The loader matrix independently proves healthy,
  missing, wrong-path, incomplete-API, and owned-execution-failure outcomes;
  neither oracle is replaced by the broad suite or treated as approval.
- Artifact evidence records the final producer path and reviewed final source
  hash while public Step `00c` artifact IDs, schemas, contents, ordering,
  reconciliation, and report consumers remain unchanged.
- Coverage retains or improves the validator's old-path `90/96` line and
  `23/26` branch counts after accounting for review-required loader logic and
  does not decrease the committed global floor of `9343/11506` lines and
  `3281/4698` branches.
- Exact searches find no live legacy source/test/job path, undeclared caller,
  duplicate basename, wrapper, package marker, new peer-stage import, stale
  command, or stale active lifecycle link. Final owner tests and independent
  caller suites pass without weakening exact inventories.
- The complete applicable computational gate runs once on final executable
  state. After the separate documentation close, documentation validation has
  no migration-caused finding. Any inherited nonpassing condition is recorded
  exactly and never called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` only where mixed
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `00c`
  commands in `RUNBOOK.md`; the Step `00c` troubleshooting route if final
  inspection finds one; this card; review lifecycle links; and the dated
  refactor log. Update diagrams only if final inspection finds a material DAG
  or public-flow change.

## Escalation conditions

- Stop for an unknown or unmovable caller, required permanent wrapper, public
  package/import decision, required `reference_provenance.py` extraction or
  mutation, new peer-owner implementation import, changed tool/scheduler/
  publication behavior beyond reviewed path/loading edits, artifact/schema
  change beyond implementation path/hash, parity that requires blessing a
  defect, missing high-risk oracle, dependency or cluster/production action, or
  scope that cannot remain one functional owner plus directly required
  evidence wiring.

## Completion record

Not started. JIT-carded from clean published parent
`5259acbf3b717487e78eecfd938cc793665673f8`. Architecture, reliability, and
usability reviews must close sequentially before selection. This definition is
documentation-only; no executable or test path has moved.
