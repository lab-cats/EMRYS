# Workflow kernel

This is the complete repository-development workflow. The root
[`AGENTS.md`](../../AGENTS.md) supplies the safety and authority guard,
[`TASK_START.md`](TASK_START.md) selects the smallest sufficient context, and a
selected JIT card supplies scope and acceptance but never mutation authority.

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
- For a physical ownership move, freeze the old public and fault boundary,
  move the implementation, direct tests, affected callers, contracts, and
  tooling together, and leave one live final owner. Do not accept a temporary
  implementation shadow as completion.
- Use focused checks as useful feedback. Review the complete final diff and run
  one de-duplicated applicable gate after the final state is assembled; rerun
  only evidence invalidated by later changes.
- A documentation-only change runs Git and documentation checks. Executable or
  consumed changes run their affected behavioral checks and the applicable
  repository gate from the [runbook](RUNBOOK.md#local-validation).
- Stop for scope or authority expansion, unresolved semantics, unsafe recovery,
  missing required evidence, or an external decision. Do not turn an unrelated
  observation into current scope.

## Documentation and task detail

Update a canonical document only when its subject changes. Branch names,
commits, routine progress, repeated test totals, and unchanged facts are not
documentation triggers. Keep exact commands and defects with their functional
owner; cross-cutting procedures and recovery rules stay in the operations docs.

The compact backlog retains stable identities, real open blockers, intent, and
boundaries. Create a detailed card only for selected work and delete it when
the execution package completes or pauses. Completing or retiring an item must
also remove or replace every live dependent edge; missing blockers are errors,
not implicit completion. Before deleting detail, move every durable contract,
safety rule, defect, decision, and evidence ceiling to its canonical subject
owner; then discard chronology, repeated totals, and superseded planning.

## Close and publish

Close by reviewing the semantic result, running the applicable validation, and
verifying acceptance. Commit the completed result once. A clean local commit
does not authorize publication: push only when explicitly approved, then prove
the intended remote ref and upstream equality. Runtime and cluster promotion
remain separately authorized and upstream-sequential.
