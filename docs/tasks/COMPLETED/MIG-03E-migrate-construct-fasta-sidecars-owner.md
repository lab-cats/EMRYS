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
  document direct and explicit-`bash` producer forms with the reference plus
  explicit samtools, GATK, and Java paths. Use `--execute` only after the
  resolved dry-run command has been inspected. From another CWD, require an
  absolute checkout path and explicit absolute reference/tool paths. State
  that dry-run resolves tools but invokes no tool version or generation
  command and creates no directory, lock, temporary path, FAI, or DICT.
  Document the mode-`0644` validator only through an explicit interpreter and
  exact final path.
- The supported scheduler journey creates `logs/`, changes to the intended
  checkout, and submits the exact final job. The real-work form must export
  `REFERENCE_FASTA`, `SAMTOOLS_BIN_OVERRIDE`, `GATK_BIN_OVERRIDE`,
  `JAVA_BIN_OVERRIDE`, `TMPDIR`, and `EXECUTE=1`; omission of `EXECUTE` keeps
  the default dry-run. State that Bash `3.2` can stop before delegation,
  current CSU tool defaults are site bindings rather than portable defaults,
  module setup is tolerated, and the wrapper checks only that the two declared
  output files are nonempty.
- At documentation close, replace the runbook's bare source-path labels,
  missing Java override, missing scheduler log preflight and portable
  overrides, and stale ad hoc/BAM evidence language. Route both Step `00c`
  troubleshooting entries to final producer and validator commands. Distinguish
  malformed or mismatched sidecars from the characterized FAI-only partial-
  publication state; preserve producer context, scheduler stdout/stderr, the
  lock state, run-token temporaries, and final FAI/DICT state before any
  separately authorized rerun or cleanup decision.
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
  preservation, scheduler stdout/stderr and residue inspection, separately
  authorized recovery, validation evidence, rollback, implementation-
  provenance transition, and the local-only migration evidence ceiling. It
  must explain that exact reference-loader failure is a checkout-integrity
  diagnostic, not a `PYTHONPATH` workaround, and that the public flat
  `reference_provenance.py` owner remains separate. Do not add a descriptor/
  schema, scheduler abstraction, transaction, receipt, recovery marker, or
  reference-provenance extraction.

## Blocked by

- [REVIEW-UX-03E](REVIEW-UX-03E-review-construct-fasta-sidecars-migration.md) — Required: architecture, reliability, and usability reviews closed before task-specific execution planning.

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
  commands in `RUNBOOK.md`; both Step `00c` routes in `TROUBLESHOOTING.md`;
  this card; review lifecycle links; and the dated refactor log. Update diagrams
  only if final inspection finds a material DAG or public-flow change.

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

Completed from clean, published, local/upstream/live-remote-equal executable/test
checkpoint `cd3b5479d64592563d4dd6a557efb52840f9edda`. Architecture,
reliability, usability, baseline, cutover, and final-path acceptance are
complete. The commit containing this record is the separate documentation and
lifecycle close; no later owner is selected by this card.

### Task-specific execution plan

Selection checkpoint `177a912f1c171155f01f1d35708c0ccfebbc5021` is the
clean, published, local/upstream/live-remote-equal planning parent. The atomic
executable/test write set is exactly fourteen tracked files:

- move `scripts/step_00c_prepare_gatk_reference.sh`,
  `scripts/validate_step_00c_reference_sidecars.py`, and
  `jobs/step_00c_prepare_gatk_reference.slurm` into
  `src/norad/stages/construct_FASTA_sidecars/` without basename or mode
  changes;
- move `tests/shell/test_step_00c_prepare_gatk_reference.sh` and
  `tests/test_validate_step_00c_reference_sidecars.py` into
  `tests/stages/construct_FASTA_sidecars/` without basename or mode changes;
- update `Makefile`, `scripts/build_artifact_index.py`,
  `tests/test_artifact_adapters.py`, `tests/test_public_cli_contracts.py`,
  `tests/test_slurm_wrapper_contracts.py`,
  `tests/test_validation_check_rosters.py`,
  `tests/libraries/test_validation_report.py`,
  `tests/baselines/python_coverage.json`, and
  `tests/fixtures/public_cli_contracts/make_target_expansions.json`; and
- change no public `reference_provenance.py` owner or test, Step `05` consumer,
  `.coveragerc`, coverage tool/policy test, package marker, descriptor, schema,
  unrelated owner, or documentation file in the executable commit.

Production edits are path/loading-only. The producer usage literal becomes its
exact final path. The validator resolves the report owner from
`Path(__file__).resolve().parents[2] / "libraries" /
"validation_report.py"` and adds one
private `_norad_reference_provenance` exact-file bridge to unchanged
`Path(__file__).resolve().parents[4] / "scripts" /
"reference_provenance.py"`. That
bridge verifies exact `__file__`, requires `ProvenanceError` to be an exception
type and all three parsers callable, preserves foreign cache state and
`sys.path`, removes only its own partial module after execution failure, and
uses the reviewed path-bearing exit-`2` diagnostic. The job delegates to the
exact final producer. Preserve producer, validator, and job modes `0755`,
`0644`, and `0755`; add no readiness sentinel, wrapper, duplicate, or alias.

The moved shell test changes only its repository-root depth and producer/job
paths, then adds the reviewed fake-`mv` case that fails only final DICT
publication after final FAI publication. It requires nonzero exit, nonempty
final FAI, absent final DICT, removed owned lock, and no run-token temporary
paths while preserving the FAI as incomplete-attempt evidence. The moved Python
test changes only its root/validator paths and subprocess-CWD helper, adds one
non-repository-CWD dry-run/execute/repeat parity journey, and exact-loads the
validator for the healthy, missing-owner, foreign-wrong-cache, correct-path-
incomplete-API, and owned-execution-failure matrix. Every case proves cache
ownership, unchanged `sys.path`, and no report or invocation-CWD residue.

Caller cutover remains literal. Public CLI, SLURM, validation-roster, and shared
validation-report maps receive exact final paths; the shared report suite uses
its existing path-validating loader for the now-non-flat validator. Artifact
evidence receives only the final Step `00c` producer path and reviewed hash.
Coverage renames the validator row only after final measurement. Make moves the
two direct recipes, adds both final shell assets to static/smoke syntax, and
updates only the matching literal-expansion entries. The independent central
scheduler matrix remains the sole owner of wrapper behavior.

The old-path baseline is a targeted local fixture/mock tranche, not the full
card gate. Run syntax for the producer and job; the current direct shell suite;
the direct validator, public CLI, SLURM, validation-roster, shared publisher,
artifact-adapter, and coverage-policy modules; plus temporary untracked-free
probes for final-DICT `mv` failure and non-repository-CWD validator dry-run/
execute/repeat. Record exact counts, streams/exits, deterministic report hash,
residue, modes, sizes, lines, and source hashes. Do not alter tracked coverage,
run real samtools/GATK/Java work, submit a job, install/restore a dependency, or
touch production inputs.

After that baseline checkpoint is published and equal, apply only the fourteen-
file atomic cutover. Run the smallest final-path focused suites and reviewed
oracles, inspect modes/hashes and exact legacy-path searches, then run the
complete applicable local gate once at the executable card boundary. Commit and
publish executable/test state before the separate batched documentation and
lifecycle close.

### Old-path fixture/mock baseline

The baseline ran from clean, published, local/upstream/live-remote-equal plan
checkpoint `d7c29ada72486855efda0f603badf6adfe658349`, with no tracked or
untracked file, recovery marker, index lock, or mutable-lane collision. It is
local fixture/mock evidence only:

- `bash -n` passed for the producer and job. The unchanged direct shell suite
  passed syntax, help, missing-argument/input, side-effect-free dry-run,
  execute, valid reuse, one-missing generation, mismatch, Java-version, foreign-
  lock, and stale-Step-`05` cases.
- The exact seven-module affected Python surface passed `555` tests in
  `61.43s`: direct validator, public CLI, central SLURM wrapper, validation
  roster, shared validation-report, artifact adapter, and coverage policy.
  This targeted run is not the complete card gate.
- A temporary fake `mv` returned `73` only for final DICT publication after
  final FAI publication. The producer propagated `73`, retained a nonempty
  `26`-byte final FAI with SHA-256
  `a5c1d01825f0a3c585991b63efa4d0cccb96007c8ece00d78eb4c72096c82068`,
  left final DICT absent, removed its owned lock, and left no run-token
  temporary path. The FAI is incomplete-attempt evidence, not a successful
  transaction or cleanup authority.
- From a temporary non-repository CWD, the validator returned `0` for dry-run,
  first execute, and repeat execute. Dry-run wrote no report; both executions
  produced five ordered all-pass rows and byte-identical `493`-byte reports
  with SHA-256
  `b8fb138d7c0087eb02e8b217d11ff1b9ecb4d326869f10a0db67272f2597a6d4`.
  Stderr, invocation-CWD residue, publisher residue, and input changes were
  empty.
- Frozen rollback evidence is producer mode/bytes/lines/hash `0755` / `14,477`
  / `515` /
  `f041c55a0e9a3b36c14dcc9b929cfa56190e1c00d23a5a62fa72ac3669f0c478`;
  validator `0644` / `5,945` / `161` /
  `5aa6358412a56b5ddb8ce963a6d7431cfb07c1bbd9fbb37c8237fc3cbebe15fd`;
  job `0755` / `4,532` / `151` /
  `78b00abb7751e78264bae30d6b3dbfb7792ca5532850f192b1b2098cbf8e85d0`;
  direct shell test `0755` / `12,698` / `414` /
  `a477786e5f331c7ecc91ef338b89abc8cc209aae14c62dac2877f684e18fc7d5`;
  and direct validator test `0644` / `2,545` / `73` /
  `7ec48d7394268e451a2087a2892a6435a02f5216d08b692fce6a3cc2094c6d48`.
- No tracked coverage measurement, real samtools/GATK/Java generation,
  scheduler submission, dependency action, production input, cluster state,
  scientific-review state, or biological evidence was created. The committed
  floor remains validator `90/96` lines and `23/26` branches and global
  `9343/11506` lines and `3281/4698` branches. Publish this documentation-only
  checkpoint and prove live remote equality before the fourteen-file cutover.

### Delivered state and acceptance evidence

- The mode-`0755` producer now lives at its final owner with only the reviewed
  usage self-path change: `14,511` bytes, `515` lines, SHA-256
  `ed3e9ca039102c881c4f91cb02fd32e4a67d09ad799300c789cbab27ce1ab0a1`.
  The mode-`0644` validator is `8,699` bytes, `234` lines, SHA-256
  `d2554dea8888d51cbcb7a02a6638e09d05ea16526f9d0d82ba0c36f18b3c2a5a`;
  it changes owner-depth resolution and adds only the reviewed exact public
  reference-provenance bridge. The mode-`0755` job is `4,566` bytes, `151`
  lines, SHA-256
  `c084f8bcbc9173b3f99c2a0baf6f443f2a8121e8bf90b8af345c21b751593d51`
  with only the final child path changed.
- The two direct suites moved to
  `tests/stages/construct_FASTA_sidecars/`. The mode-`0755` shell test has
  SHA-256
  `35bfce22da1aa08d155bd74ed4a306a10d0002c5df43f63fe1a7914013940882`;
  the mode-`0644` validator test has SHA-256
  `e768515779268206728a21a8ef0a1fbddb8b8ba2cb4031648b3cafae7afdb900`.
  Final-path shell acceptance passed, including retained nonempty FAI, absent
  DICT, removed owned lock, and no run-token residue after controlled final-DICT
  move failure. The direct validator suite passed `11` tests, and the exact
  affected Python surface passed `561` tests in `62.92s`.
- Deterministic serial coverage passed `1,079` tests with `17` skips and one
  explicit documentation-validator deselection. It measured the final validator
  at `128/139` lines and `35/42` branches (`0.920863`/`0.833333`) and the global
  surface at `9381/11549` lines and `3293/4714` branches
  (`0.812278`/`0.698557`), above the frozen covered-count floor. Every non-target
  row was identical to the prior baseline, and the standalone coverage policy
  comparison passed after the final row was placed in lexical order.
- The complete aggregate gate was not fully green. Static preflight, shell
  contracts, guarded R, and report runtime passed. The first sandboxed guarded-R
  attempt was blocked only by DNS access to Bioconductor metadata; the exact
  network-enabled rerun used the existing project library and installed,
  restored, deleted, and updated nothing. The ignored malformed `macos`
  directory warning remains characterized local state. Python executed `1,079`
  passes and `17` skips before the documentation-validator test reported exactly
  ten migration-caused stale links plus the nine inherited `invalid card
  location` findings under `docs/tasks/UNREFINED/`. This documentation close
  repairs the ten migration links; the nine inherited findings remain an
  expected-only nonpassing condition and are never called a passing gate.
- Exact inspection found one final owner for each moved basename and no live
  non-documentation legacy path, wrapper, compatibility copy, symlink, package
  marker, descriptor, schema, or peer-stage implementation import. Artifact
  evidence names and hashes the final producer without changing public artifact
  identities, contents, ordering, schemas, reconciliation, or consumers. The
  public reference-provenance CLI, its tests and coverage row, and the Step `05`
  consumer remain unchanged.
- FAI-first nontransactional publication, lack of receipt/recovery marker, the
  scheduler's Bash `3.2` empty-array dry-run defect, current CSU site bindings,
  tolerated module setup, fallback submit CWD, Java policy, and file-only output
  checks remain characterized defects. The private reference bridge remains
  bounded mixed-layout debt. Relocation neither fixes nor blesses any of them.
- Published rollback points are old-path baseline `9850a8d`, executable/test
  checkpoint `cd3b547`, and the commit containing this completion record.
  Reverse the documentation close before reverting the executable cutover;
  preserve runtime artifacts and do not restore duplicate source files.

No real samtools, GATK, or Java generation, scheduler submission, cluster or
production input, dependency change, scientific review, or biological-readiness
evidence was created. The public DAG and artifact flow did not change, so no
diagram edit was warranted.
