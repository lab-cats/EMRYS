# MIG-03A — Extract the validation-report library

## Objective

Move the proven shared validation-report and publication protocol out of the
Step `00a` validator into its final neutral library owner, cut over every known
validator consumer, and preserve all public and fault behavior.

## Why this exists

Twelve validators import nine shared primitives from
`validate_step_00a_star_index.py`, although that public CLI belongs only to
`construct_STAR_index`. Moving any functional owner first would retain or
create a prohibited stage-to-stage implementation dependency. The shared seam
already has exact-roster, independent-golden, and adversarial publication-fault
coverage, making it the smallest evidence-supported migration unit.

## Fixed decisions

- The one neutral concern has final source owner
  `src/norad/libraries/validation_report.py`; its mirrored direct test owner is
  `tests/libraries/test_validation_report.py`. This source placement does not
  create a public/import/package identity, `__init__.py`, or distribution
  contract.
- Move the nine shared API names `ValidationError`, `Snapshot`, `fail`, `clean`,
  `regular_snapshot`, `stable_text`, `render`, `validate_report`, and `publish`,
  plus their internal `HEADER` constant. Step `00a` parsing, STAR-specific
  validation, report rows, CLI, and all other stage-specific checks remain with
  their functional owners.
- All thirteen current validator scripts remain at their public legacy paths
  in this unit. Each uses a caller-local `importlib` loader to resolve the exact
  final file from its own location, cache one private internal module identity,
  and reject a cached module whose resolved `__file__` is not that exact path.
  On first load it registers the owned module before execution and removes only
  that exact owned cache entry if execution fails; it never overwrites or
  deletes a foreign entry, and it never reuses a partially initialized module.
  The loader does not change `sys.path`, install anything, assume caller CWD or
  global `PYTHONPATH`, introduce a shared bootstrap helper, or establish a
  public import name. Its caller-local scaffolding leaves with that validator
  in the validator's later owner migration.
- No legacy wrapper is required: all repository-owned import consumers can cut
  over atomically, and no public Python module API for the Step `00a`
  implementation is declared. Final-owner introduction, all caller/test
  cutovers, and removal of the old embedded implementation therefore form one
  executable commit; no temporary re-export or compatibility commit is allowed.
- When the exact shared owner cannot be loaded, each validator fails before
  argument parsing or validation with one concise, stable stderr diagnostic
  that names the expected owner path and causal exception type/reason. That
  failure is nonzero, leaves stdout empty, creates no report or invocation-CWD
  artifact, and does not convert `KeyboardInterrupt` or another control-flow
  exception into an ordinary load error. Healthy-repository `--help`, malformed-
  argument, dry-run, and execute behavior remain byte-for-byte or
  outcome-equivalent to the characterized public contract.
- The same-size/restored-mtime snapshot gap, report-row-order gap, late foreign-
  final deletion, incomplete rollback without a retained lock/recovery marker,
  previous/staged cleanup residue, open-descriptor/lock retention, and
  post-publication lock-cleanup behavior remain characterized defects. This
  migration neither corrects nor approves them.
- All thirteen public validators remain interpreter-only files at mode `0644`;
  the supported public form remains an explicit Python interpreter plus the
  existing script path, not direct `./script.py` execution. The new source and
  direct-test owners are also `0644`. Public validator filenames, shebangs,
  arguments, help, streams, exit statuses, dry-run/execute effects, TSV bytes,
  check rosters, and evidence meanings remain unchanged.

## Blocked by

- [REVIEW-UX-03A](../COMPLETED/REVIEW-UX-03A-review-validation-publication-migration.md) — Required: tranche-specific architecture, reliability, and public-boundary reviews must be incorporated before execution planning closes.

## Completion unblocks

- None.

## Prerequisites

- At task start, freeze the exact clean, pushed, upstream-equal planning tip as
  the executable parent and refresh branch, worktree, import, path, mode, and
  test evidence from that commit.
- Confirm `TEST-01Z` still releases structural mutation and that no concurrent
  lane owns any listed source, test, coverage, runbook, architecture, roadmap,
  handoff, or card path.
- Inspect a supported direct-script dry run before any execute-mode fixture;
  do not install or restore dependencies.

## Required context

- `TASK_START.md`; `TASK_DELIVERY.md`; the local validation gate in
  `RUNBOOK.md`; `SOURCE_TOPOLOGY.md`; `MIGRATION_MECHANICS.md`; the validation-
  evidence row in `FUNCTIONAL_OWNER_INVENTORY.md`; and `TEST_BASELINE.md`.
- `validate_step_00a_star_index.py`; its twelve `validate_step_*` importers;
  all thirteen direct validator tests; `test_validation_publication_faults.py`;
  `test_validation_check_rosters.py`; `test_independent_contract_goldens.py`;
  `test_public_cli_contracts.py`; and the tracked Python coverage snapshot.

## Questions owned by this card

- None.

## In scope

- Record the exact frozen parent, refreshed consumer roster, pre-move modes,
  applicable contract rows, complete shared fault-outcome matrix, and rollback
  targets before source mutation.
- Introduce the final neutral module, move the direct fault-test owner, cut all
  thirteen validators and affected direct tests through the exact file-based
  private loader, and remove the old embedded implementation in one atomic
  executable commit.
- Prove that the caller-local loaders resolve one exact module object, leave
  `sys.path` unchanged, reject a wrong cached path, and preserve arbitrary-CWD
  direct execution without a package install or compatibility re-export. Fault
  injection must also prove owned partial-cache removal and foreign-cache
  preservation when module execution fails.
- Prove the owner-missing, wrong-cache, and ordinary module-execution failure
  journeys through focused import/subprocess tests: one actionable stderr-only
  diagnostic, nonzero exit, no traceback for an ordinary load failure, and no
  report or invocation-CWD artifact. Preserve the existing healthy-owner
  arbitrary-CWD `--help` and malformed-argument matrix for all thirteen
  interpreter-only validators.
- Add a module docstring, a concise caller-local loader comment pointing to the
  final owner, and `src/norad/libraries/README.md`. The README names the nine
  shared API symbols and internal `HEADER`, records that no package/import
  identity is established, lists the preserved characterized defects, and
  explains that the repeated caller-local loaders leave only with later
  validator-owner migrations.
- Update the explicit coverage baseline path/rates through its reviewed command
  only if measurement requires it; a moved module may not disappear from the
  baseline or evade the new-shared-module thresholds.
- After executable state is final, update current topology, functional-owner
  inventory, runbook links only where paths actually changed, roadmap, handoff,
  this card, and the dated refactor log in a separate documentation commit.

## Out of scope

- Moving or renaming a public validator, stage, analysis, evidence operation,
  SLURM wrapper, Make target, schema, fixture unrelated to this library, or
  report artifact.
- Correcting any characterized validation/publication defect; changing report
  fields, row order, check rosters, failures, transactions, logging, or evidence
  state; extracting BAM helpers or Step `09c` science helpers; or creating a
  generic transaction, I/O, validation, or utility framework.
- `__init__.py`, packaging/import identity, dependency installation/restoration,
  cluster execution, production data, scientific review, or biological
  interpretation.

## Deliverables

- Frozen-baseline evidence and a stable pre-mutation reversion commit.
- One atomic final-owner/caller/test cutover commit plus a separate
  documentation-close commit, with reverse-order rollback boundaries. The
  executable commit is reverted as one unit because no supported intermediate
  caller state exists.
- One implementation at `src/norad/libraries/validation_report.py`, direct
  library tests at `tests/libraries/test_validation_report.py`, and no remaining
  import of shared primitives from `validate_step_00a_star_index.py`.
- Maintainer-facing owner documentation at `src/norad/libraries/README.md`, a
  focused module docstring, and local loader comments without a package marker,
  install step, public import name, new CLI flag, or logging dependency.
- A legacy-path/import search, focused parity results, complete applicable local
  gate, clean worktree, publication/upstream-equality evidence, and explicit
  local-only evidence ceiling.

## Acceptance evidence

- Old/new comparison preserves direct interpreter and arbitrary-CWD behavior,
  malformed input, dry run, execute effects, stdout/stderr, exit status,
  deterministic TSV bytes, exact per-stage rosters, import identity, and file
  modes for every affected validator.
- With the owner unavailable or invalid, every affected entry point emits the
  planned stable diagnostic only on stderr, exits nonzero, and leaves stdout,
  report targets, and the invocation directory unchanged. Under a valid owner,
  `--help` remains successful and malformed arguments retain argparse's stderr
  usage and nonzero status without result artifacts.
- Import tests prove all validators reference the one exact final file and
  module object, `sys.path` is unchanged, wrong-path cache collisions fail
  closed, and no package installation or public import identity is required.
- The full publication-fault matrix still observes each current success,
  failure, interruption, rollback, residue, and characterized-defect state
  against the final module. It includes first/repeat publication, malformed
  staged/predecessor bytes, symlink rejection, staged fsync, predecessor and
  final moves, post-publication validation, `KeyboardInterrupt`, late foreign
  collision, failed restoration, previous/staged/lock cleanup, and descriptor
  retention. Independent golden and roster expectations remain independent of
  production rules.
- Every affected direct validator test passes, the complete Python suite and
  coverage gate pass, the new shared module satisfies at least 90% line and 85%
  branch coverage, and Git/documentation validation passes at the final tree.
- Exact searches find no undeclared Step `00a` shared-helper importer,
  compatibility re-export, duplicate implementation, stale test owner, or
  documentation claim that relocation corrected a defect or established
  runtime, cluster, scientific-review, or biological-readiness evidence.

## Canonical documentation updates

- `ARCHITECTURE.md`, `FUNCTIONAL_OWNER_INVENTORY.md`, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, `src/norad/libraries/README.md`, this card, and the dated pre-
  migration/refactor log; update `RUNBOOK.md`, public CLI fixtures, and coverage
  baseline only when the final executable diff makes their owned bytes or
  commands change.

## Escalation conditions

- Stop if live inspection finds an external/unmovable importer, a declared
  public module API, unavoidable package or global-path dependency,
  path-sensitive side effect, missing parity owner, changed publication state,
  or need to touch a second neutral concern or scientific contract.

## Completion record

Selected for task-specific read-only planning from clean review checkpoint
`b714f61`. The lifecycle move does not begin the supported dry run, create an
implementation branch, or authorize executable source/test mutation. The exact
clean, pushed, upstream-equal planning tip remains to be frozen from live Git as
the executable parent at the separate execution boundary.
