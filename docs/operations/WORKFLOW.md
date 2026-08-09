# Workflow kernel

This is the complete repository-development workflow. The root
[`AGENTS.md`](../../AGENTS.md) supplies the safety and authority guard,
[`TASK_START.md`](TASK_START.md) selects the smallest sufficient context, and a
task card supplies scope and acceptance but never mutation authority.

## Start

1. Follow [`TASK_START.md`](TASK_START.md) to assemble the smallest sufficient
   current context for the bounded task.
2. State the outcome, touched owners, exclusions, validation, evidence ceiling,
   and stopping condition. Obtain approval before mutation.

## Deliver

- Work sequentially in one authoritative worktree. Keep each package or slice
  to one outcome and one coherent owner boundary.
- Change implementation, direct tests, contracts, and subject-affected
  documentation together. One semantic commit is the default.
- Use focused checks as useful feedback. Review the complete final diff and run
  one de-duplicated applicable gate after the final state is assembled; rerun
  only evidence invalidated by later changes.
- A documentation-only change runs Git and documentation checks. Executable or
  consumed changes run their affected behavioral checks and the applicable
  repository gate from the [runbook](RUNBOOK.md#local-validation).
- Stop for scope or authority expansion, unresolved semantics, unsafe recovery,
  missing required evidence, or an external decision. Do not turn an unrelated
  observation into current scope.

## Documentation and cards

Update a canonical document only when its subject changes. Branch names,
commits, routine progress, repeated test totals, and unchanged facts are not
documentation triggers. Keep exact commands and defects with their functional
owner; cross-cutting procedures and recovery rules stay in the operations docs.

Cards retain their paths during selection, pause, review, and execution.
Delete a card when its work is completed or retired; do not maintain a
completed-card archive or repair surviving cards because former targets were
deleted. History and `UNREFINED` are not live path-maintenance surfaces.

## Close and publish

Close by reviewing the semantic result, running the applicable validation, and
verifying acceptance. Commit the completed result once. A clean local commit
does not authorize publication: push only when explicitly approved, then prove
the intended remote ref and upstream equality. Runtime and cluster promotion
remain separately authorized and upstream-sequential.
