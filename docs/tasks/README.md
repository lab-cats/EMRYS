# Task registry

[`BACKLOG.md`](BACKLOG.md) is the single live inventory of open work and
nonselectable proposals. It is intentionally coarse: one item records only its
kind, genuine technological blockers, intent, and boundaries.

Create a detailed file under [`cards/`](cards/) only when an actionable item is
selected. Delete that file when the package completes, pauses without an active
execution plan, or is retired. Remove the backlog item only when the obligation
is completed, absorbed into a named canonical owner, or explicitly retired.
Git preserves former wording and completed detail.

## Status

Render the read-only derived view from the repository root:

```bash
./scripts/git_orchestration/task_status.py \
  --repo "$(git rev-parse --show-toplevel)"
```

The view grants no approval and owns no priority or execution order. Preferred
sequence belongs in [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); current
state and evidence belong in [`HANDOFF.md`](../operations/HANDOFF.md).

## Dependency meaning

`Blocked by` names only an open actionable item whose unavailable technical
output prevents meaningful progress. It never encodes preference, chronology,
approval, environment state, useful context, or a completed prerequisite.
Proposals cannot block or be blocked. Reverse dependency views are derived.

The documentation gate rejects duplicate or unknown IDs, proposal blockers,
self-dependencies, and cycles. Deleting a blocker without removing or replacing
its dependent edge is an error; absence is never interpreted as completion.

## Archived detail

The detailed predecessor registry is preserved at Git commit
`755678ec28a6aa4e58149447704551312e365254`. Retrieve an old item without
restoring it to the worktree:

```bash
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/TODO/<file>.md
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/UNREFINED/<file>.md
```

The compact item is live authority. Archived prose is refinement input only;
reconcile it against current code, contracts, decisions, questions, and Git
state before creating a JIT card.
