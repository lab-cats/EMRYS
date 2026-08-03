# MIG-03D — Migrate the align-RNA-reads-with-STAR owner

## Objective

Move the complete `align_RNA_reads_with_STAR` producer, validator, scheduler
asset, and owner-local tests to their frozen final homes while preserving
current public, scheduler, validation, artifact, coverage, and alignment
contracts.

## Why this exists

After `MIG-03C`, both `align_RNA_reads_with_STAR` and
`construct_FASTA_sidecars` are dependency-valid. Select
`align_RNA_reads_with_STAR`: its sole hard DAG predecessor,
`construct_STAR_index`, is already migrated; its three native assets are the
smaller live surface; and its validator depends only on the already migrated
neutral validation-report library. The FASTA-sidecar validator still imports
the separate flat `reference_provenance` implementation. This selection follows
the semantic DAG and live coupling, not historical alias order.

## Fixed decisions

- Frozen parent and rollback target:
  `f9d638199c6d60cbe81c992fde6a1090cb364302`, the clean, published,
  local/upstream-equal `MIG-03C` documentation close on the one active campaign
  branch.
- Semantic identity is `align_RNA_reads_with_STAR`, machine key
  `norad.stage.align_RNA_reads_with_STAR.v1`, historical alias `01`, with final
  source home `src/norad/stages/align_RNA_reads_with_STAR/` and mirrored test
  home `tests/stages/align_RNA_reads_with_STAR/`.
- Move the mode-`0755` shell producer `scripts/step_01_star_align.sh`,
  mode-`0644` Python validator
  `scripts/validate_step_01_star_alignment.py`, and mode-`0644` scheduler entry
  point `jobs/step_01_star_align.slurm` to the final owner without renaming their
  basenames. Preserve, rather than silently correct, the nonexecutable job mode.
- Move the mode-`0755` direct shell test
  `tests/shell/test_step_01_star_align.sh` and mode-`0644` direct validator test
  `tests/test_validate_step_01_star_alignment.py` to the mirrored test home.
  Keep the Step `01` fixture adapter and default-placeholder assertion in the
  independent cross-owner scheduler suite: they share its parametrized wrapper
  harness, and extraction would duplicate or cross-import test infrastructure.
  Update only that suite's explicit job path and delegated producer path.
- Preserve the shell producer's arguments, dry-run default, execute control,
  command bytes, compression handling, streams, exits, and output-directory
  side effect. Its self-identifying help path must name the final producer; any
  other source change requires a review finding.
- Change the validator's exact neutral-library lookup only as required by the
  final owner depth. Preserve its private exact-file report identity, no
  `sys.path` mutation, public basename, interpreter-only mode, five check IDs,
  report bytes, dry-run/execute behavior, and publication semantics.
- In the shared validation-report suite, route every declared non-flat
  validator through the existing path-validating exact-file test loader while
  retaining module-name import for validators still in `scripts/`. This reuses
  the established loader, rejects a foreign cached validator path, preserves
  `sys.path`, and avoids a Step-`01` special case or new loader framework.
- Change the scheduler's delegated producer argument to the exact final path.
  Preserve all seven directives, caller-CWD behavior, module policy, defaults,
  `EXECUTE` handling, thread binding, mutable default fixtures, streams, exits,
  and lack of independent output validation.
- No legacy wrapper is required. Every named source-path caller is repository-
  owned and can cut over in one atomic executable/test commit; a wrapper would
  preserve accidental flat placement without an unmovable consumer.
- `STEP_PRODUCERS["01"]` intentionally changes to the final producer path.
  Preserve status, evidence ID, Git commit projection, artifact identities,
  schemas, ordering, and consumers. The old producer SHA-256
  `25e2120ca9843ea25f2e1f3b4084aced6261976ab46f7cb25c33d7911f82d0ba`
  is rollback evidence because the help path must change; record and assert the
  reviewed final hash after cutover.
- Coverage already uses stable roots `scripts` and `src/norad`. Move the
  validator's tracked `125/140` line and `34/44` branch row to its final path
  only after inspected final-path measurement proves exact or improved counts
  and global non-regression.
- Once both shell assets leave the flat wildcards, add their exact final paths
  to `validation-static` and `smoke` shell-syntax commands and to the literal
  Make expansion oracle. Move the shell-test and validator-test recipe paths.
- Existing public-CLI, SLURM, validator, loader, artifact, coverage, and Make
  inventories must retain explicit basename or semantic-ID path maps and exact
  one-owner equality. Do not introduce recursive runtime discovery, alias-
  derived placement, package identity, installation, or global path mutation.
- Replace flat-root inference for public shell entry points with an explicit
  `SHELL_ENTRYPOINT_PATHS` map parallel to the existing Python map, derive the
  public basename set from its keys, and keep exact flat-root inventory equality
  only for entries whose declared parent is `scripts/`. All shell CLI tests must
  resolve paths through that map.
- The existing `CONTRACT.md` remains the detailed behavior owner. Its stale
  Step-00a publication dependency is repaired only in the documentation close.
  Add one concise owner `README.md` only at that card boundary. Do not add the
  target descriptor/schema, scheduler abstraction, new CLI, transaction, or
  scientific alignment policy.

## Blocked by

- [REVIEW-UX-03D](REVIEW-UX-03D-review-align-rna-reads-with-star-migration.md) — Required: architecture, reliability, and usability reviews must close before task-specific execution planning.

## Completion unblocks

- None.

## Prerequisites

- Reverify the frozen parent is clean, published, upstream-equal, and free of
  merge/rebase/cherry-pick/revert, index-lock, recovery, or overlapping mutable
  lane state before selection or executable mutation.
- Refresh only the named path/import consumers, modes, hashes, Make/static/
  coverage wiring, artifact evidence, and active documentation for this owner.
- Establish identical-input pre-move baselines for direct and explicit-
  interpreter producer behavior, validator behavior, and mocked scheduler
  behavior without SLURM submission, real STAR execution, production inputs,
  dependency installation, or dependency restoration.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate and Step `01`
  commands in `RUNBOOK.md`; `STAGE_MAP.md`; `SOURCE_TOPOLOGY.md`;
  `MIGRATION_MECHANICS.md`; the `align_RNA_reads_with_STAR` contract; the
  functional-owner inventory; `TEST_BASELINE.md`; and the Step `01`
  troubleshooting route.
- The producer, validator, scheduler job, both direct tests, Step `01` behavior
  in `test_slurm_wrapper_contracts.py`, public-CLI and validator-roster suites,
  and the shared validation-report loader/fault matrix.
- `STEP_PRODUCERS["01"]` and artifact-provenance consumers; coverage
  config/tool/tests/baseline; Make static/smoke/shell-test recipes; and the
  literal Make-expansion fixture.
- All nonhistorical Markdown links and supported commands naming the producer,
  validator, scheduler job, or focused tests. Artifact identities and STAR
  outputs remain unchanged unless a review identifies contrary evidence.

## Questions owned by this card

- None.

## In scope

- Freeze the exact direct invocation graph, paths, modes, hashes, contract
  defects, parity rows, coverage counts, and rollback evidence before source
  mutation.
- Move the producer, validator, and scheduler entry point once to the final
  owner; change only the producer's displayed self-path, the validator's
  owner-relative neutral-library lookup, and the job's delegated producer path
  unless a completed review records another required path-only edit.
- Move the two direct tests to the mirrored owner home. Keep the independent
  cross-owner scheduler fixture adapter and default-placeholder assertion in
  its existing comparative suite, together with mode, directive, roster, CLI,
  loader, artifact, Make, and coverage suites as explicit path-aware consumers.
- Cut over every named repository caller in the same atomic executable/test
  commit, including Make/static/smoke, literal expansions, artifact provenance,
  public CLI, SLURM roster, validator roster, shared loader, direct tests, and
  tracked coverage path.
- Update the moved shell test's repository-root calculation and producer path,
  and the moved Python test's repository-root calculation and validator path;
  those are test-location edits, not new behavior. The production diff is
  limited to the producer usage self-path, validator neutral-owner depth, and
  scheduler delegated child path.
- Extend old/new parity only where the sequential reviews find a missing named
  behavior. Measure coverage at the card boundary, then run the complete
  applicable local gate once on final executable state.
- After executable state is fixed, batch the owner README, migration path/link
  repairs, current topology/status/evidence owners, lifecycle links, and dated
  audit updates into one separate documentation-close commit.

## Out of scope

- Changing STAR arguments, coordinate sorting, gzip selection, sample-ID path
  handling, input-content checks, output names, output validation, or direct
  final-path writes.
- Correcting dry-run output-directory creation, adding a lock, receipt,
  no-clobber rule, staging transaction, cleanup, recovery, or post-STAR checks.
- Correcting scheduler caller-CWD dependence, placeholder creation, module
  version/policy, implicit fixture mutation, `EXECUTE` behavior, or lack of
  independent output validation. These remain characterized defects.
- Changing validator checks, BAM/BGZF recognition, log or splice-junction
  parsing, report ordering, stable-input recheck, lock/rollback behavior, or
  the neutral validation-report library.
- Moving `construct_FASTA_sidecars`, `construct_canonical_BAM`, an artifact or
  report owner, another validator, or another functional owner.
- Adding packages, descriptors, schemas, wrappers, symlinks, compatibility
  copies, global path mutation, dependency actions, cluster/production work,
  scientific claims, or unrelated harness redesign.

## Deliverables

- One atomic final-owner/caller/test/harness cutover commit and one separate
  documentation/lifecycle-close commit, both published sequentially.
- Final producer, validator, and job under
  `src/norad/stages/align_RNA_reads_with_STAR/`; direct owner tests under
  `tests/stages/align_RNA_reads_with_STAR/`; no legacy path, wrapper,
  compatibility copy, duplicate implementation, package marker, descriptor, or
  schema.
- Explicit mixed-layout caller inventories, exact artifact-evidence transition,
  coverage rename accounting, supported final commands, exact searches,
  complete applicable local validation at the card boundary, clean publication
  equality, and a precise local-only evidence ceiling.

## Acceptance evidence

- Producer parity preserves mode `0755`, direct and explicit-interpreter help,
  missing/malformed arguments, arbitrary CWD, dry-run/execute modes, required
  paths, matching compression, command construction, output-directory side
  effects, streams, child status, and exact STAR invocation apart from the
  displayed final self-path.
- Validator parity preserves mode `0644`, explicit-interpreter and arbitrary-
  CWD behavior, all arguments, five ordered report rows, dry-run/execute/repeat
  effects, deterministic bytes, streams/exits, stable-input recheck, locks,
  foreign state, rollback/cleanup behavior, and exact neutral owner identity
  without global `sys.path` mutation.
- Scheduler parity preserves mode `0644`, seven directives, strict mode,
  caller-CWD delegation, STAR module `2.7.11b`, allocation-derived threads,
  all five overrides plus `EXECUTE`, default dry-run fixture mutation, execute-
  with-default refusal, TMPDIR behavior, exact final child path, streams, child
  and module failures, and no independent output validation.
- Artifact evidence records the final producer path and reviewed final source
  hash while public Step `01` artifact IDs, schemas, contents, ordering, and
  report consumers remain unchanged.
- Coverage moves validator `125/140` lines and `34/44` branches to its final
  path, or records only review-driven parity improvement, without decreasing
  the committed global floor of `9343/11506` lines and `3281/4698` branches.
- Exact searches find no live legacy source/test/job path, undeclared caller,
  duplicate basename, wrapper, package marker, stage-to-stage import, stale
  command, or stale active lifecycle link. Final owner tests and independent
  caller suites pass without weakening exact inventories.
- The complete applicable computational gate runs once on final executable
  state. After the separate documentation close, documentation validation has
  no migration-caused finding. Any inherited nonpassing condition is recorded
  exactly and never called passing.

## Canonical documentation updates

- Owner `README.md`; owner `CONTRACT.md`; `ARCHITECTURE.md` only where mixed
  placement changes; `FUNCTIONAL_OWNER_INVENTORY.md`; `TEST_BASELINE.md`;
  `DOCUMENTATION_OWNERSHIP.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; Step `01`
  commands in `RUNBOOK.md`; the Step `01` troubleshooting source path if final
  inspection finds one; this card; review lifecycle links; and the dated
  refactor log. Update diagrams only if final inspection finds a material DAG
  or public-flow change.

## Escalation conditions

- Stop for an unknown or unmovable caller, required permanent wrapper, public
  package/import decision, cross-owner implementation import, changed STAR or
  scheduler behavior beyond final path text, artifact/schema change beyond the
  recorded implementation path/hash, parity that requires blessing a defect,
  missing high-risk oracle, dependency or cluster/production action, or scope
  that cannot remain one functional owner plus directly required evidence
  wiring.

## Completion record

Not started. JIT-carded from clean published parent
`f9d638199c6d60cbe81c992fde6a1090cb364302`. Architecture, reliability, and
usability reviews must close sequentially before selection. This definition is
documentation-only; no executable or test path has moved.
