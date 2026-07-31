# CONTEXT-00 — Define minimal task-start context

## Objective

Replace blanket canonical-document rereads with a version-aware task-start and
documentation-impact protocol that preserves correctness while reducing
unnecessary context.

## Why this exists

The replaced phase-boundary rule can require complete reads of a nine-document
corpus exceeding 9,000 lines even when most files are unchanged or unrelated
to the selected task. Existing active context and exact Git revisions can
safely avoid some rereads, but only if freshness, routing, and escalation rules
are explicit.

## Fixed decisions

- Correctness, safety, scientific and evidence integrity, and effective task
  completion outrank context or token reduction.
- Reuse existing context only when its exact revision is known and live Git
  inspection proves the relevant content unchanged.
- Repository-wide consistency means repository-wide impact discovery and
  automated validation, not automatic line-by-line reading.
- A documentation-only package runs documentation validation and Git checks,
  not computational suites, when its complete diff has no executable or
  test-affecting consumer.
- The startup router links to canonical owners and never duplicates mutable
  branch, evidence, command, roadmap, or test-total state.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Verify the architecture-direction predecessor is pushed and upstream-equal.
- Preserve the user's existing responsible-context instruction in `AGENTS.md`.
- Inspect the complete package diff from the predecessor, not only the current
  worktree, before classifying validation as documentation-only.

## Required context

- Current task-start and development-gate rules in `AGENTS.md`.
- Canonical-reading and documentation-as-architecture decisions, the open
  context choice, task-card context fields, and the documentation gate.
- Current handoff, roadmap lineage, and the later `CONTEXT-09` boundary.

## Questions owned by this card

- `CHOICE-CONTEXT-01`, resolved by the approved version-aware policy in
  [`TASK_START.md`](../../operations/TASK_START.md) and
  [`DECISIONS.md`](../../design/DECISIONS.md#route-task-context-by-revision-and-impact).

## In scope

- A concise task-start routing document, context-freshness rules, and a
  task-class reading matrix.
- Selective phase-boundary reading with explicit broadening triggers.
- Impact-directed manual documentation and diagram inspection backed by the
  existing repository-wide automated documentation gate.
- Explicit documentation-only computational-test inapplicability.
- Task-card guidance for routing to exact canonical sections and local
  implementation surfaces.

## Out of scope

- Mature stage/domain README or contract bundles, which remain in
  `CONTEXT-09`.
- Documentation consolidation, source relocation, code comments, executable
  behavior, tests, schemas, fixtures, report templates, or scientific policy.
- Treating summaries, memory, or another agent's unversioned inspection as
  current repository proof.

## Deliverables

- `docs/operations/TASK_START.md` as the concise, full-read routing owner.
- Aligned conduct, decision, question, task-registry, runbook, roadmap, README,
  future-context, and handoff references.
- A documentation-only validation record with computational suites marked not
  applicable.

## Acceptance evidence

- New-agent, same-context, new-task, phase-boundary, documentation-only, and
  high-risk/cross-cutting cases each have an unambiguous reading route.
- Unchanged exact-version content may be reused, while unknown revisions,
  contradictions, ownership changes, and scientific/safety/recovery/public-
  contract uncertainty broaden inspection.
- Repository-wide automated link, anchor, card, dependency, and Mermaid checks
  remain intact and quiet.
- The complete predecessor-to-final diff is documentation-only and the
  documentation gate passes without computational test execution.

## Canonical documentation updates

- `AGENTS.md`, `README.md`, `docs/operations/TASK_START.md`,
  `docs/design/DECISIONS.md`, `docs/design/QUESTIONS.md`,
  `docs/design/PIPELINE_PLAN.md`, `docs/architecture/FUTURE_ARCHITECTURE.md`,
  `docs/tasks/README.md`, `docs/operations/RUNBOOK.md`,
  `docs/operations/HANDOFF.md`, and affected task cards.

## Escalation conditions

- Stop if a narrower route would omit context required to resolve scientific,
  evidence, safety, recovery, publication, public-contract, or ownership risk.
- Stop if a purported documentation artifact is consumed by executable,
  configuration, generation, schema, fixture, report-template, or test-harness
  selection or execution behavior.
- Stop if the startup router would become a second owner of mutable project
  state or executable commands.

## Completion record

Completed on 2026-07-31. The package added the version-aware task-start router
and aligned its canonical owners. Review before publication then corrected
sequence-only dependency metadata, restored the completed `ARCH-DOC-00` card
instead of rewriting history, and created four bounded TODO cards:
`DOC-GATE-01`, `TASK-REG-01`, `CONCURRENCY-01`, and `PROGRAM-01`. The latter two
record approved future operating-model decisions without activating them.

The complete predecessor-to-final diff contains Markdown only and changes no
executable, dependency, schema, configuration, fixture, report-template, test-
harness, scientific-method, runtime, cluster, or evidence-state surface.
Computational suites were therefore not applicable. `git diff --check` and the
repository documentation gate passed with 71 Markdown documents, 51 task
cards, and 6 Mermaid sources. Independent read-only review found the final
status, scope, lineage, dependency, and ownership model consistent.
