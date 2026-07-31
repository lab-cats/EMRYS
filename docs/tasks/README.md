# NORAD task registry

This directory is the bounded planning registry for future repository work.
One Markdown file represents one task card. The directory containing the card
is its only status signal:

- [`TODO/`](TODO/) — available or blocked work that has not entered planning;
- [`IN_PROGRESS/`](IN_PROGRESS/) — a task selected for task-specific,
  read-only planning or approved execution;
- [`COMPLETED/`](COMPLETED/) — historical records whose acceptance evidence
  has been inspected.

Cards preserve decisions already made, define scope and dependencies, and
state what evidence would close the task. They are not implementation plans
and never authorize mutation. Selecting a card means moving it to
`IN_PROGRESS` with `git mv`, reading the card in full, following the
[`task-start router`](../operations/TASK_START.md), inspecting the live
repository, proposing a task-specific plan, and obtaining user approval before
editing or running mutating commands.

The registry begins with the completed `ARCH-DOC-00` bootstrap card. It does
not reconstruct retrospective cards for earlier refactor packages; their
historical scope and evidence remain in `REFACTOR_AUDIT.md`,
`TEST_BASELINE.md`, `PIPELINE_PLAN.md`, and `HANDOFF.md`.

## Ownership boundary

Cards own bounded task scope, dependencies, deliverables, acceptance evidence,
and completion history. They link rather than duplicate durable truth:

- architectural rationale belongs in
  [`../design/DECISIONS.md`](../design/DECISIONS.md);
- current and target topology belong in
  [`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) and
  [`../architecture/FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md);
- current checkout and evidence belong in
  [`../operations/HANDOFF.md`](../operations/HANDOFF.md);
- exact commands belong in
  [`../operations/RUNBOOK.md`](../operations/RUNBOOK.md);
- task-start freshness, routing, and expansion rules belong in
  [`../operations/TASK_START.md`](../operations/TASK_START.md);
- roadmap order belongs in
  [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
- unresolved choices belong in
  [`../design/QUESTIONS.md`](../design/QUESTIONS.md).

`PIPELINE_PLAN.md` owns pipeline/package/evidence state and lineage. The task
card's directory is the only owner of TODO/IN_PROGRESS/COMPLETED workflow
status; roadmap rows link to the card rather than restating that lifecycle.

Do not put live branch names, commit IDs, test totals, or mutable status in a
TODO card. A completion record links to the canonical evidence owner instead
of copying mutable snapshots.

## Lifecycle

1. Create a stable card ID and filename directly in `TODO` unless the card
   documents work completed by the same approved bootstrap package.
2. Move a selected card to `IN_PROGRESS` with `git mv`; update every inbound
   link in the same commit. This starts read-only planning only.
3. If planning is paused or blocked, move the card back to `TODO`, record the
   reason in its completion record, and update inbound links. There is no
   separate `BLOCKED` directory.
4. Move a card to `COMPLETED` only after its acceptance evidence and required
   canonical documentation updates have been inspected. Update every inbound
   link in the same commit.
5. Completed cards are immutable historical records apart from link repair or
   factual correction. New work gets a new follow-up card.

## Dependency semantics

`Blocked by` contains only genuine technological blockers: card IDs whose
incomplete work makes the task unsafe or impossible to proceed. Preferred
sequence, roadmap order, useful context, and planning convenience are not
blockers; record them under `Prerequisites`, `Required context`, or the
canonical roadmap instead.

`Completion unblocks` labels each relationship:

- `Fully` means the target has no other card blocker after this card completes;
- `Partially` means completion removes one of several genuine technological
  blockers, so it does not by itself permit the target to proceed.

Useful context alone never belongs in `Completion unblocks`. For new or edited
active cards, maintain reciprocal metadata only between cards that are still
mutable. Do not rewrite a completed card merely to add a reciprocal link;
completed evidence needed by new work belongs under `Prerequisites` or
`Required context`.

Every card named under `Blocked by` must appear in the source card's
`Completion unblocks` list as `Fully` or `Partially`, and every `Fully`
relationship must appear in the target's `Blocked by` list. Every referenced
card must exist. Hard dependencies must be acyclic and free of
self-dependencies. Do not create wildcard placeholder cards; an inventory or
design card creates concrete children after their scope is known.

Some existing cards predate this forward rule. Do not copy or opportunistically
migrate their sequence-only edges. `TASK-REG-01` owns the bounded legacy-graph
migration and validator correction.

When an inventory/design task creates concrete child cards, that same commit
must replace every family prerequisite in affected cards with explicit direct
`Blocked by` links and add reciprocal `Completion unblocks` links to the new
cards. An affected card cannot enter planning while a known concrete blocker
exists only as prose.

## Card template

Use the headings below once each and in this order. Replace every instruction
with card-specific content.

```markdown
# CARD-ID — Short task title

## Objective

One outcome-oriented sentence.

## Why this exists

The problem, evidence, and user value.

## Fixed decisions

- Concise settled constraints with links to canonical decisions.

## Blocked by

- `CARD-ID` — Required: link the completed card and explain the hard gate.

## Completion unblocks

- `CARD-ID` — Fully: link the target and explain why it can then start.
- `CARD-ID` — Partially: link the target and explain the context supplied.

## Prerequisites

- Live, non-card conditions that must be verified.

## Required context

- Exact canonical sections and bounded implementation, contract, consumer,
  test, and fixture surfaces to inspect in addition to `TASK_START.md`.

## Questions owned by this card

- Stable choice IDs from `QUESTIONS.md`, or `None.`

## In scope

- Bounded work this card may plan.

## Out of scope

- Neighboring work deliberately excluded.

## Deliverables

- Concrete artifacts the task must produce.

## Acceptance evidence

- Observable proof required to close the card.

## Canonical documentation updates

- Owners that must change if the task is approved and completed.

## Escalation conditions

- Card-specific conditions that require broader inspection, stopping, or
  requesting direction in addition to the global `TASK_START.md` triggers.

## Completion record

Not started. On completion, link the inspected evidence and summarize only
stable historical facts.
```

Run the documentation gate in
[`../operations/RUNBOOK.md`](../operations/RUNBOOK.md) after creating or moving
cards.
