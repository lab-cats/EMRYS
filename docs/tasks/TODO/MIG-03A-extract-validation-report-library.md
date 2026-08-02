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

- The one neutral concern is `norad.libraries.validation_report`, implemented
  at `src/norad/libraries/validation_report.py`; its mirrored direct test owner
  is `tests/libraries/test_validation_report.py`.
- Move only `HEADER`, `ValidationError`, `Snapshot`, `fail`, `clean`,
  `regular_snapshot`, `stable_text`, `render`, `validate_report`, and `publish`.
  Step `00a` parsing, STAR-specific validation, report rows, CLI, and all other
  stage-specific checks remain with their functional owners.
- All thirteen current validator scripts remain at their public legacy paths
  in this unit. Each resolves the repository-local `src` directory from its own
  file location before importing the final neutral module; no installation,
  global `PYTHONPATH`, working-directory assumption, or shared bootstrap helper
  is introduced.
- No legacy wrapper is required: all repository-owned import consumers can cut
  over within the bounded checkpoints, and no public Python module API for the
  Step `00a` implementation is declared. A temporary re-export is allowed only
  between committed cutover checkpoints and must be removed before acceptance.
- The same-size/restored-mtime snapshot gap, report-row-order gap, late foreign-
  final deletion, incomplete rollback/recovery, previous/staged cleanup, and
  lock-cleanup behaviors remain characterized defects. This migration neither
  corrects nor approves them.
- Source and direct-test modes are `0644`; public validator filenames, shebangs,
  arguments, help, streams, exit statuses, dry-run/execute effects, TSV bytes,
  check rosters, and evidence meanings remain unchanged.

## Blocked by

- [REVIEW-UX-03A](REVIEW-UX-03A-review-validation-publication-migration.md) — Required: tranche-specific architecture, reliability, and public-boundary reviews must be incorporated before execution planning closes.

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
  applicable contract rows, and rollback targets before source mutation.
- Introduce the final neutral module and mirrored direct tests with a temporary
  Step `00a` re-export only if required to leave the first checkpoint usable.
- Cut all thirteen validators and direct tests to the final module using
  file-relative repository-local `src` resolution, then remove every temporary
  re-export and prove one implementation remains.
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
- Packaging, dependency installation/restoration, cluster execution, production
  data, scientific review, or biological interpretation.

## Deliverables

- Frozen-baseline evidence and a stable pre-mutation reversion commit.
- Final-owner introduction, complete caller cutover, compatibility removal,
  and documentation-close commits with reverse-order rollback boundaries.
- One implementation at `src/norad/libraries/validation_report.py`, direct
  library tests at `tests/libraries/test_validation_report.py`, and no remaining
  import of shared primitives from `validate_step_00a_star_index.py`.
- A legacy-path/import search, focused parity results, complete applicable local
  gate, clean worktree, publication/upstream-equality evidence, and explicit
  local-only evidence ceiling.

## Acceptance evidence

- Old/new comparison preserves direct interpreter and arbitrary-CWD behavior,
  malformed input, dry run, execute effects, stdout/stderr, exit status,
  deterministic TSV bytes, exact per-stage rosters, import identity, and file
  modes for every affected validator.
- The full publication-fault matrix still observes each current success,
  failure, interruption, rollback, residue, and characterized-defect state
  against the final module; independent golden and roster expectations remain
  independent of production rules.
- Every affected direct validator test passes, the complete Python suite and
  coverage gate pass, the new shared module satisfies at least 90% line and 85%
  branch coverage, and Git/documentation validation passes at the final tree.
- Exact searches find no undeclared Step `00a` shared-helper importer,
  compatibility re-export, duplicate implementation, stale test owner, or
  documentation claim that relocation corrected a defect or established
  runtime, cluster, scientific-review, or biological-readiness evidence.

## Canonical documentation updates

- `ARCHITECTURE.md`, `FUNCTIONAL_OWNER_INVENTORY.md`, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, this card, and the dated pre-migration/refactor log; update
  `RUNBOOK.md`, public CLI fixtures, and coverage baseline only when the final
  executable diff makes their owned bytes or commands change.

## Escalation conditions

- Stop if live inspection finds an external/unmovable importer, a declared
  public module API, packaging-dependent import, path-sensitive side effect,
  missing parity owner, changed publication state, or need to touch a second
  neutral concern or scientific contract.

## Completion record

Not started. Selection begins task-specific read-only planning only; executable
source mutation requires a separately authorized execution boundary.
