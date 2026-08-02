# NORAD task registry

This directory is the bounded planning registry for future repository work.
One Markdown file represents one task card. The directory containing the card
on the canonical integration branch is its only authoritative status signal:

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
- concurrent lane roles and authority belong in
  [`../operations/CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md);
- integration-fragment filenames and candidate fields belong in
  [`../fragments/README.md`](../fragments/README.md), while authority,
  dispositions, and lifecycle remain in `CONCURRENT_WORK.md`;
- task-start freshness, routing, and expansion rules belong in
  [`../operations/TASK_START.md`](../operations/TASK_START.md);
- roadmap order belongs in
  [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
- unresolved choices belong in
  [`../design/QUESTIONS.md`](../design/QUESTIONS.md).
- documentation audiences, canonical responsibility boundaries, and
  consolidation dispositions belong in
  [`../sitemap/DOCUMENTATION_OWNERSHIP.md`](../sitemap/DOCUMENTATION_OWNERSHIP.md).

`PIPELINE_PLAN.md` owns pipeline/package/evidence state and lineage. The task
card's directory is the only owner of TODO/IN_PROGRESS/COMPLETED workflow
status; roadmap rows link to the card rather than restating that lifecycle.

Do not put live branch names, commit IDs, test totals, or mutable status in a
TODO card. A completion record links to the canonical evidence owner instead
of copying mutable snapshots.

## Lifecycle

1. Create a stable card ID and filename directly in `TODO` unless the card
   documents work completed by the same approved bootstrap package.
2. The integration owner moves a selected card to `IN_PROGRESS` with `git mv`
   and updates every inbound link in the same commit. This starts read-only
   planning only.
3. If planning is paused or blocked, move the card back to `TODO`, record the
   reason in its completion record, and update inbound links. There is no
   separate `BLOCKED` directory.
4. Move a card to `COMPLETED` only after its acceptance evidence and required
   canonical documentation updates have been inspected. Update every inbound
   link in the same commit.
5. Completed cards are immutable historical records apart from link repair or
   factual correction. New work gets a new follow-up card.

Multiple cards may be `IN_PROGRESS` only when
[`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md) records isolated,
non-overlapping lanes. Candidate-directory placement is proposal state until
the integration owner accepts it; sidecars never move canonical card status.

An integration fragment is not a card or lifecycle location. It cannot select,
block, authorize, complete, or supply a canonical inbound reference for a
card. Accepted facts enter their proper owners. Deferred task work must name an
existing or simultaneously authorized destination; naming a future question,
card, `UNREFINED` item, or lifecycle state does not create it.

## Concurrent card creation

The integration owner reserves each sidecar's card IDs and paths before
mutation. Sidecars create new cards directly in `TODO`, edit only the recorded
write set, and never select, approve, or complete their own cards. The
integration owner serializes landing, adds central inbound references, repairs
status links, and runs the combined documentation gate. A card-only sidecar
with a deliberately pending central inbound reference is handoff-ready, not
complete or independently gate-passing.

A sidecar may instead reserve exact deliverables plus at most one
[`integration fragment`](../fragments/README.md). Its candidate write
reservations stay exclusive, while its canonical target declarations are
nonexclusive requests. The integration owner validates and dispositions every
request, writes accepted registry changes, and removes the fragment before
canonical publication. Fragment links are ignored when determining canonical
task-registry connectivity.

Concurrency preparation and preferred landing order never create `Blocked by`
or `Completion unblocks` metadata.

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

When an inventory/design task creates a concrete child that is a genuine
technological blocker, the integration commit replaces the affected mutable
card's family prerequisite with an explicit direct `Blocked by` link and adds
reciprocal `Completion unblocks` metadata when both cards remain mutable.
Sequence, context, and preferred order stay in prose; completed cards are not
rewritten merely for reciprocity.

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
- `CARD-ID` — Partially: link the target and explain which one of several
  genuine technological blockers this completion removes.

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
