# CODEDOC-05 — Inventory code documentation

## Objective

Classify every source file's module/header documentation and maintainer-comment
needs, then create small local rollout cards.

## Why this exists

Some files are thousands of lines and many modules, scripts, jobs, and fixtures
do not state their purpose, invariants, failure model, or scientific boundary
near the code. A repository-wide comment pass without inventory would create
noise and invite accidental behavior changes.

## Fixed decisions

- Classify every code file as `sufficient`, `update`, `defer`, or `exclude`.
- Module/header text explains purpose, inputs/outputs, side effects, invariants,
  failure/publication behavior, and scientific limits as applicable.
- Inline comments explain why, non-obvious invariants, safety/recovery, and
  scientific boundaries—not line-by-line mechanics.
- Preserve CLI help before changing any Python module docstring used through
  `ArgumentParser(description=__doc__)`.
- Do not comment TSV/JSON/schema/lock/byte-sensitive fixtures inline; document
  them adjacently.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest sufficiency decision is affirmative.
- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: code-adjacent documentation ownership must be settled.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: the integrated plan needs exact local comment/header work.
- [DOC-SKILL-10](../TODO/DOC-SKILL-10-build-documentation-health-skill.md) — Partially: the skill also depends on proven glossary, README, review, and consolidation practices.

## Prerequisites

- Refresh all tracked Python, shell, R, SLURM, Quarto/template, and executable
  support files; identify generated and byte-sensitive exclusions.

## Required context

- Public CLI help tests, source-size inventory, functional-stage map, local
  READMEs/contracts, scientific caution, and the 15 known Python CLIs that use
  module docstrings for help descriptions.

## Questions owned by this card

- None.

## In scope

- File-by-file inventory, comment quality rubric, help-preservation map,
  adjacency rules, and concrete local `CODEDOC-06-*` cards grouped by stage or
  narrow domain.

## Out of scope

- Performing the repository-wide comment rollout, changing behavior while
  documenting it, commenting obvious code, or adding comments to data fixtures.

## Deliverables

- Complete inventory and bounded rollout card set with local context and tests.

## Acceptance evidence

- Every tracked code file has one justified classification and owner.
- Every `update` item maps to a small card; every `defer`/`exclude` item states
  why and where adjacent explanation lives.
- CLI help baselines exist before docstring changes are authorized.

## Canonical documentation updates

- `DECISIONS.md` if the code-documentation policy changes, relevant local
  READMEs, `PIPELINE_PLAN.md`, task registry, and this card.

## Escalation conditions

- Stop if a comment would assert unverified behavior, scientific meaning, or
  recovery guarantees, or if documentation reveals a defect requiring code
  correction.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
