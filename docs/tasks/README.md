# NORAD task registry

This directory is the bounded planning registry for repository work. One
Markdown file represents one actionable task card. Cards preserve scope,
settled decisions, genuine technological dependencies, and acceptance evidence;
they do not authorize mutation or replace live inspection and an approved plan.

## Current model

Create every new actionable card at a stable path under [`cards/`](cards/):

```text
docs/tasks/cards/<CARD-ID>-<slug>.md
```

The filename does not change when the card is selected, paused, reviewed,
completed, or retired. Its exact explicit `State:` field owns lifecycle state:

| State | Meaning |
| --- | --- |
| `planned` | The card is eligible for planning or execution when approval and blockers allow. It may also be the transiently selected work; selection is not persistent state. |
| `review` | An exact candidate is intentionally frozen for asynchronous review or integration. Correction authoring first returns the card to `planned`. |
| `completed` | Acceptance evidence and directly affected canonical documentation have been inspected, and the completion record is non-placeholder. |
| `retired` | The work is no longer intended as written; the completion record gives the rationale and a successor or explicitly says none. |

Readiness is derived rather than authored. A `planned` card is ready when every
direct `Blocked by` card is `completed`; other lifecycle states are not reported
as ready. Selection, agent activity, branch identity, and preferred sequence do
not change readiness.

Use the deterministic read-only view from any checkout root:

```bash
./scripts/git_orchestration/task_status.py --repo "$(git rev-parse --show-toplevel)"
```

The view sorts by card ID and derives reverse edges and readiness from canonical
card metadata. It contains no timestamp, branch, SHA, or mutable stored
projection and must not be committed as a second authority.

## Lifecycle rules

1. Create a stable ID and a complete `planned` card under `cards/`.
2. Select, plan, pause, resume, accept, or decline work without moving or
   rewriting the card. Those are execution events, not lifecycle events.
3. Change explicit state only when lifecycle itself changes and include that
   update in the package's semantic commit. Never create a status-only
   selection/deselection commit.
4. Use `review` only for a frozen candidate that will remain under asynchronous
   review or integration beyond the current unpublished package. Routine
   same-package review does not change state.
5. A correction to a `review` card first returns it to `planned` in the approved
   correction package. No candidate bytes change while it remains `review`.
6. Use `completed` only after acceptance evidence and directly affected owners
   have been inspected. Record durable evidence or link its canonical owner;
   do not copy mutable branch names, SHAs, test totals, or current-state prose.
7. Use `retired` when the objective is deliberately abandoned or superseded.
   Record `Rationale:` and `Successor:` in the completion record; `None.` is a
   valid explicit successor value.
8. Completed cards are historical records. Apart from link repair or factual
   correction, new work receives a new card.

No actionable card needs an external inbound status link. Roadmaps, priority
views, and generated views may link cards when the relationship is useful, but
connectivity is not a lifecycle requirement.

## Legacy compatibility

The existing [`TODO/`](TODO/), [`IN_PROGRESS/`](IN_PROGRESS/),
[`INTEGRATION_REVIEW/`](INTEGRATION_REVIEW/), and [`COMPLETED/`](COMPLETED/)
trees remain valid. This cutover deliberately performs no bulk card move,
reciprocal-edge rewrite, or completed-archive migration.

For a legacy card without an explicit state, tooling infers:

| Legacy directory | Inferred state |
| --- | --- |
| `TODO` | `planned` |
| `IN_PROGRESS` | `planned` |
| `INTEGRATION_REVIEW` | `review` |
| `COMPLETED` | `completed` |

If a legacy card later changes for a real semantic reason, an exact explicit
`State:` value overrides its directory without moving the file or repairing
inbound paths. Legacy cards retain their original heading schema. Legacy
`Completion unblocks` fields remain accepted and validated for reciprocal
consistency, but do not add or opportunistically migrate those fields. New
stable cards use only `Blocked by`; reverse edges are derived.

The completed archive stays untouched unless a link repair or factual
correction is itself authorized. New cards must use the stable directory and
new schema even when they document work completed by the same package.

## Dependency semantics

`Blocked by` contains only genuine technological blockers: card IDs whose
incomplete work makes the task unsafe or impossible to proceed. Preferred
sequence, roadmap order, useful context, and planning convenience belong under
`Prerequisites`, `Required context`, or the roadmap.

Each dependency is authored once, on the blocked card, using:

```markdown
- `CARD-ID` linked to its card — Required: explain the hard gate.
```

Use `- None.` when there is no direct blocker. Every referenced card must exist;
hard dependencies must be acyclic and free of self-dependencies. A card in
`review` or `completed` must have only completed direct blockers. Reverse
`Unblocks` relationships and readiness are generated by `task_status.py`.

Do not use dependencies for concurrency preparation, landing order, context,
epic membership, or approval state. An inventory or design card creates
concrete children only after their scope is known; do not create wildcard
placeholder blockers.

## Ownership boundary

Cards own bounded task scope, dependencies, deliverables, acceptance evidence,
documentation triggers, and completion history. They link rather than duplicate
durable truth:

- rationale belongs in [`../design/DECISIONS.md`](../design/DECISIONS.md);
- current and target topology belong in
  [`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) and
  [`../architecture/FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md);
- non-reconstructable checkout, lane, blocker, and evidence state belongs in
  [`../operations/HANDOFF.md`](../operations/HANDOFF.md);
- exact commands belong in
  [`../operations/RUNBOOK.md`](../operations/RUNBOOK.md);
- concurrency exception policy belongs in
  [`../operations/CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md);
- task-start and delivery defaults belong in
  [`../operations/TASK_START.md`](../operations/TASK_START.md) and
  [`../operations/TASK_DELIVERY.md`](../operations/TASK_DELIVERY.md);
- roadmap order and package acceptance belong in
  [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
- unresolved choices belong in
  [`../design/QUESTIONS.md`](../design/QUESTIONS.md); and
- documentation responsibility belongs in
  [`../sitemap/DOCUMENTATION_OWNERSHIP.md`](../sitemap/DOCUMENTATION_OWNERSHIP.md).

## `UNREFINED` proposals

[`UNREFINED/`](UNREFINED/) is a nonselectable proposal-intake location outside
the actionable registry. Its files cannot be selected, started, prioritized,
placed in dependency relationships, block or unblock work, claim implementation
authority, or satisfy an actionable card. Promotion requires explicit review,
conversion to the stable actionable schema, and an integration-owner decision.
File presence preserves an idea; it does not approve or schedule it.

Each proposal uses one `# CARD-ID — Title` H1 whose ID matches its filename,
the exact local ``State: [`UNREFINED` proposal](README.md). ...`` declaration,
and these headings once in order: `Proposal`, `Why preserve it`, `Settled
boundaries`, `Questions before refinement`, and `Promotion conditions`.
Additional proposal headings are permitted. Actionable-card headings and
dependency-edge syntax are prohibited.

## Concurrent card creation

Sequential creation in the authoritative worktree is the default. If an
approved concurrency exception creates cards, the integration owner reserves
IDs and stable paths before mutation. Sidecars edit only their recorded write
sets and cannot select, approve, review, complete, retire, or publish their own
cards. The integration owner serializes accepted changes and runs the final
combined gate. An integration fragment is not a card or lifecycle location and
cannot select, block, authorize, complete, or provide registry authority.

## Stable card template

Use the headings below once each and in this order. Replace every instruction
with card-specific content.

```markdown
# CARD-ID — Short task title

State: planned

## Objective

One outcome-oriented sentence.

## Why this exists

The problem, evidence, and user value.

## Fixed decisions

- Concise settled constraints with links to canonical decisions.

## Blocked by

- None.

## Prerequisites

- Live non-card conditions that must be verified.

## Required context

- Exact canonical sections and bounded implementation, contract, consumer,
  test, and fixture surfaces to inspect.

## Questions owned by this card

- Stable choice IDs from `QUESTIONS.md`, or `None.`

## In scope

- Bounded work this card may plan.

## Out of scope

- Neighboring work deliberately excluded.

## Deliverables

- Concrete artifacts the task must produce.

## Acceptance evidence

- Observable evidence required to close the task.

## Documentation impact triggers

- Canonical owners to update only if this task changes their subject.

## Escalation conditions

- Evidence, semantic, safety, authority, or scope gaps that require direction.

## Completion record

Not complete.
```

The documentation validator enforces stable paths, exact state values, heading
order, blocker syntax, unique IDs across legacy and stable cards, dependency
existence and acyclicity, completed-blocker requirements for `review` and
`completed`, non-placeholder completed records, and structured retirement
records. It continues to accept the frozen legacy schema during gradual,
subject-triggered convergence.
