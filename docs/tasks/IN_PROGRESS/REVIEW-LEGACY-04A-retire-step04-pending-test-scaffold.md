# REVIEW-LEGACY-04A — Review the Step 04 pending test scaffold

## Objective

Complete a no-loss review of
`tests/pending/test_step_04_mark_duplicates.sh` and retire it only if every
unique planned check is already protected by the final Step `04` owner.

## Why this exists

The residual source-topology campaign has completed every executable `MOVE`
and the separate Step `05` operational-checker review. One nine-line,
mode-`0644` Step `04` test-plan scaffold remains under `tests/pending/`. It was
introduced before the final producer, validator, wrapper, and owner-local test
surfaces existed. A bounded no-loss comparison must distinguish an obsolete
planning note from an unimplemented requirement before the file can be
removed.

## Fixed decisions

- Review only `tests/pending/test_step_04_mark_duplicates.sh` and the final
  Step `04` contract and direct protection needed to evaluate its four listed
  checks.
- Treat the file as documentation-only/non-consuming: it has no shebang or
  executable body, explicitly prohibits Make or `shell-test` selection, has no
  automated caller, and remains mode `0644`.
- Retire the scaffold only if exact evidence proves that the required sorted
  BAM input is validated before Picard, deterministic output naming and safe
  dry-run command projection are protected, and missing-input/tool diagnostics
  are all protected in current owners.
- Do not change, run, relocate, or reinterpret the final Step `04` producer,
  validator, SLURM wrapper, tests, fixtures, contracts, or characterized
  defects.
- This review creates no new runtime, cluster, production, scientific-review,
  or biological evidence.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal `REVIEW-LEGACY-05A`
  documentation/lifecycle close
  `916737bf33fb8a0a96a765ce48979ee41d9e2668`.
- Reverify the scaffold identity, history, exact repository references, lack of
  a Make or test-harness caller, and the current final Step `04` contract and
  direct test coverage.

## Required context

- The scaffold; final Step `04` contract and owner-local shell suite;
  `FUNCTIONAL_OWNER_INVENTORY.md`; `PIPELINE_PLAN.md`; `HANDOFF.md`; and the
  current task-delivery/documentation-only gate.

## Questions owned by this card

- None.

## In scope

- One static requirement/caller/history comparison; one final `RETIRE` or
  `RETAIN_ROOT` disposition; deletion of only the obsolete scaffold if no
  unique requirement remains; and impact-directed documentation/lifecycle
  close.

## Out of scope

- Any Step `04` executable, validator, wrapper, fixture, contract, test, CLI,
  publication, transaction, recovery, scheduler, or runtime change; the final
  residual-layout audit; documentation-consolidation cards; dependency work;
  default-branch integration; cluster, production, scientific-review, or
  biological work.

## Deliverables

- A documented four-requirement no-loss crosswalk and one final disposition
  for the pending scaffold.

## Acceptance evidence

- Git proves the pre-disposition scaffold is nine lines, `417` bytes, mode
  `0644`, and SHA-256
  `bfbec48adee7307f93890986f7087f60583fdc4a6c550056e6155dabc9d129a1`.
- Exact searches prove the scaffold has no Make, test-harness, source, job, or
  automated caller; its sole current inbound ownership reference is updated in
  the same close.
- A four-row crosswalk maps each planned check to exact current contract and
  owner-local test evidence without inferring broader behavior.
- If retired, exact searches prove the old path is absent and the final Step
  `04` source/test owners and selectors remain unchanged.
- `git diff --check`, documentation validation, and independent semantic close
  review pass. Computational tests are not applicable because the removed file
  is an unselected documentation scaffold and no executable, selected test,
  fixture, configuration, dependency, schema, report template, or harness
  behavior changes.
- Evidence remains static no-loss review and existing local fixture/mock
  characterization only.

## Canonical documentation updates

- Functional-owner inventory and residual count, `PIPELINE_PLAN.md`,
  `HANDOFF.md`, `TODO.md`, lifecycle routes, documentation ownership, and this
  card.

## Escalation conditions

- Stop for any unique uncovered requirement, external or automated caller,
  ambiguous current protection, need to change or execute a Step `04` surface,
  or scope into the final residual audit, documentation consolidation,
  dependencies, default-branch integration, cluster, production,
  scientific-review, or biological work.

## Completion record

Selected from clean, published, live-remote-equal `REVIEW-LEGACY-05A`
documentation/lifecycle close
`916737bf33fb8a0a96a765ce48979ee41d9e2668`. Read-only planning confirmed the
scaffold's frozen identity and sole ownership reference and found no automated
caller. It also found that pre-Picard input-sort validation and adversarial
dry-run shell escaping are not yet proven by the current owner-local suite;
the selected review must disposition those gaps without expanding into an
executable correction. Disposition work has not begun.
