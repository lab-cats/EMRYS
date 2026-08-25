# Task planning and registry transition

## Authority during transition

| Concern | Current owner | Boundary |
|---|---|---|
| Current planning backlog | [`backlog_matrix.md`](backlog_matrix.md) | Owns accepted task IDs, status, required outcomes, acceptance, dispositions, and the later Importance/Complexity scores |
| Unsliced architecture context | [`architecture_campaign.md`](architecture_campaign.md) | Temporarily owns source feedback, cross-task rationale, ideal states, alternatives, decisions, and slicing traceability; it does not create tasks by itself |
| Architecture campaign ranking | [`architecture_backlog_matrix.md`](architecture_backlog_matrix.md) | Provisional Architecture Priority/Indicative Complexity view of campaign cards; it does not own implementation status, acceptance, or final task scoring |
| Legacy registry and cards | [`BACKLOG.md`](BACKLOG.md) and [`cards/`](cards/) | Frozen mechanically consumed surfaces pending `BACKLOG-01`; do not add or mirror current planning work here |
| Legacy evidence and roadmap sources | [`HANDOFF.md`](../operations/HANDOFF.md) and [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) | Mechanically referenced but user-identified as stale and unverified pending `DOC-02`; not reliable current authorities |

The main matrix is the current planning backlog. The campaign is temporary and
cannot become a second permanent backlog. Its architecture-only matrix is a
provisional ranking view, not another implementation-status or final-scoring
authority. The legacy registry and card format remain present only because
existing selection guidance, status rendering, and documentation validation
still consume them. Their callers and useful validation behavior receive
separate dispositions under `BACKLOG-01` and `DOC-TOOL-01`.

None of these documents grants mutation, implementation, publication, cluster
execution, scientific-review, or evidence-promotion authority. Use
[`WORKFLOW.md`](../operations/WORKFLOW.md) and an explicitly approved bounded
objective. Do not create a duplicate legacy item merely because current tooling
does not yet understand a matrix-only ID.

[`HANDOFF.md`](../operations/HANDOFF.md) and
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) remain mechanically named by
existing repository guards, navigation, and cross-links, but the user has
identified both as stale. Pending `DOC-02`, treat them as legacy, unverified
transition inputs rather than reliable current evidence or roadmap authorities.
Verify any retained claim against live Git, source, tests, the current matrix,
and the applicable durable owner. Do not add current planning or evidence solely
to either file. `DOC-02` must decide their destinations and update every inbound
route atomically.

## Legacy status tooling

The existing read-only renderer still reports only [`BACKLOG.md`](BACKLOG.md):

```bash
./scripts/git_orchestration/task_status.py \
  --repo "$(git rev-parse --show-toplevel)"
```

Its output is a legacy-registry view, not the current planning inventory. The
current documentation gate likewise validates legacy registry/card structure;
it does not yet validate matrix rows, campaign source IDs, or
Importance/Complexity scoring.

## Legacy dependency meaning

The matrix intentionally owns no blocker/dependency graph. Within the frozen
legacy registry, `Blocked by` retains its former mechanical meaning: an open
actionable item whose unavailable technical output prevents meaningful
progress. It never grants approval or establishes current matrix priority.

The documentation gate continues to reject duplicate or unknown legacy IDs,
proposal blockers, self-dependencies, and cycles. This behavior remains in
place until `BACKLOG-01` and `DOC-TOOL-01` migrate or retire it deliberately.

## Archived detail

The detailed predecessor registry is preserved at Git commit
`755678ec28a6aa4e58149447704551312e365254`. Retrieve an old item without
restoring it to the worktree:

```bash
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/TODO/<file>.md
git show 755678ec28a6aa4e58149447704551312e365254:docs/tasks/UNREFINED/<file>.md
```

Archived prose and the frozen compact registry are refinement input only.
Reconcile them against the current matrix, code, contracts, decisions,
questions, and Git state before using any retained detail.
