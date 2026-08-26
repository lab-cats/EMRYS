# Task planning

## Authority

| Concern | Owner | Boundary |
|---|---|---|
| Working backlog | [`backlog_matrix.md`](backlog_matrix.md) | Owns accepted task IDs, status, required outcomes, acceptance, and dispositions |
| Unsliced architecture context | [`architecture_campaign.md`](architecture_campaign.md) | Temporarily preserves source feedback, rationale, ideal states, alternatives, and slicing traceability; it does not create tasks |
| Architecture campaign ranking | [`architecture_backlog_matrix.md`](architecture_backlog_matrix.md) | Provides provisional Architecture Priority and Indicative Complexity for campaign cards; it does not own implementation status or final task scoring |
| Unsliced performance context | [`performance_campaign.md`](performance_campaign.md) | Temporarily preserves scaling diagnoses, hypotheses, alternatives, experiment rules, and context not yet accepted into the backlog; it does not create tasks |
| Performance campaign ranking | [`performance_backlog_matrix.md`](performance_backlog_matrix.md) | Provides provisional Importance, Complexity, correctness/evidence Risk, Benchmark, and Parity for performance cards; it does not own implementation status or acceptance |
| Historical planning detail | Git history and [`docs/history`](../history/) | Supplies dated context only; it does not own current state or requirements |

The findings matrix is the repository's only durable backlog. Do not create a
parallel registry, task-card directory, status list, or campaign-only task.
Campaign documents and their provisional ranking views are temporary and must
eventually be fully sliced into the matrix or retired.

A successful experiment or CI timing result does not itself authorize
integration. Only an accepted main-matrix item whose parity and evidence
requirements have been satisfied may enter the performance-integration branch.

None of these documents grants mutation, publication, cluster execution,
scientific review, or evidence promotion authority. Select one accepted matrix
item or state one explicitly bounded objective, then use the
[workflow kernel](../operations/WORKFLOW.md) and the directly affected owners.
The matrix intentionally has no blocker graph; priority labels remain
provisional until the planned Importance and Complexity scoring pass.

Completing, retiring, absorbing, or discarding an item removes it from the
active table and adds an explicit terminal entry to the matrix disposition log.
Before deleting detailed planning, move durable contracts, safety rules,
defects, decisions, recovery guidance, and evidence ceilings to their subject
owners. Chronology, repeated totals, and superseded proposals remain history.

## Archived detail

The predecessor registry and detailed task directories remain retrievable at
Git commit `755678ec28a6aa4e58149447704551312e365254` without restoring a second
live backlog:

```bash
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/BACKLOG.md
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/TODO/<file>.md
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/UNREFINED/<file>.md
```

Reconcile historical detail against the current matrix, live implementation,
contracts, decisions, and Git state before reusing it.
