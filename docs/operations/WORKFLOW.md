# Workflow kernel

This is the complete repository-development workflow. The root
[`AGENTS.md`](../../AGENTS.md) supplies the safety and authority guard. A
selected matrix item or explicitly bounded objective supplies scope and
acceptance but never mutation authority.

## Context

Start with the **smallest sufficient current context** for one bounded task.
Context selection does not copy mutable project state or authorize changes.

Load only:

1. The exact current root [`AGENTS.md`](../../AGENTS.md).
2. Live Git identity and state: repository root, branch, `HEAD`, worktree
   changes, upstream relation, and any competing relevant worktree.
3. The selected item in the canonical
   [findings matrix](../tasks/backlog_matrix.md) in full, plus any explicitly
   approved package boundary needed to make the work decision-complete.
   Campaign proposals are not selectable until accepted into the matrix.
4. Directly affected functional owners: implementation, adjacent `README.md`
   or `CONTRACT.md`, public callers and consumers, tests, and fixtures that
   define or exercise the behavior.
5. Only applicable canonical sections linked by the matrix item or affected
   owners. Use live Git for checkout state, checks and retained artifacts for
   exact validation observations, the matrix for accepted outcomes and
   acceptance, and the [architecture index](../architecture/README.md) for
   cross-owner identity and dependency direction.

Do not preload the full documentation corpus, history, unrelated backlog
items, every owner, all tests, or entire canonical documents merely for
orientation. Do not infer live state from memory, an agent identity, a
conversation summary, an old test total, or a former branch.

Prior context may replace a reread only when its exact revision is known, the
live diff proves the relevant content unchanged, and the retained context is
sufficient for the current decision. Otherwise read the current source.

Broaden the packet only when targeted inspection reveals:

- a contradiction, stale route, ownership change, or uncertain boundary;
- a public CLI, path, schema, format, command, contract, or compatibility
  change;
- shared code, dependencies, configuration, generated inputs, or multiple
  functional owners;
- scientific method, evidence state, or biological interpretation;
- safety, credentials, cluster or production execution, publication, locking,
  rollback, recovery, cleanup, or destructive action; or
- impact that cannot be bounded confidently from the selected task and its
  direct owners and consumers.

Correctness, recoverability, scientific meaning, and honest evidence claims
always outrank context reduction.

## Start

State the outcome, touched owners, exclusions, validation, evidence ceiling,
and stopping condition. Obtain approval before mutation.

Repository surface growth requires explicit approval. Surface includes a new
public command or option, supported path, schema or serialized record, receipt
or output, evidence state, functional owner or shared seam, tracked directory,
workflow rule or starter, dependency, scheduler entry point, and recovery or
transaction mechanism. Tests, contracts, and reader-orienting documentation
required to support an already approved surface are part of that approval.
Moving or splitting an existing concept without retiring its former owner is
surface growth, not maintainability progress.

Before selecting a design for an architecture-campaign slice, complete the
read-only compression audit and register required by the campaign's
[per-slice compression and mutation protocol](../tasks/architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol).
For an implementation slice, the default closure is net-negative maintained
product code with no product-file growth. Stop for explicit user approval of
any quantified exception; counts cannot be satisfied by moving or weakening
responsibility.

## Deliver

- Work sequentially in one authoritative worktree. Keep each package or slice
  to one outcome and one coherent owner boundary.
- Change implementation, direct tests, contracts, and subject-affected
  documentation together. One semantic commit is the default.
- For a physical ownership move, freeze the old public and fault boundary,
  move the implementation, direct tests, affected callers, contracts, and
  tooling together, and leave one live final owner. A separately approved
  compatibility path has a named owner, bounded scope, parity protection, and
  an explicit retirement condition. Do not accept that temporary shadow as
  completion; retire the superseded path when the condition is met.
- Before removing a direct-owner, adversarial, seeded-fault, or synthetic
  end-to-end defense, map the protected invariant to an equal-or-stronger
  replacement at the same declared evidence level. Coverage or a
  scientist-facing golden path alone is not replacement evidence. See the
  [ratified architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
- Treat boundary values as immutable by default. Every mutable exception must
  have a named owner, narrow lifecycle, and recorded justification; it must not
  modify an immutable Run plan or reconstruct a different plan in place.
- Audit, task, and implementation approval never authorize evidence deletion.
  Follow the campaign's exact proposal gate, obtain separate explicit user
  approval, and put any approved deletion in its own commit; it cannot offset
  maintained product growth.
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

Audit a small owner README as `sufficient`, `revise`, or `missing`; size alone
is never a reason to remove it. A reader who opens the directory should learn
its purpose, pipeline role, high-level capability, principal entry point and
output, important non-goals, and where the exact contract lives without needing
project history or substantial outside context. The README orients maintainers;
the adjacent contract owns exact inputs, outputs, checks, and failure semantics.

The findings matrix retains stable identities, status, required outcomes,
acceptance, and terminal dispositions. It intentionally has no blocker graph.
Completing or retiring an item must update the matrix and every live reference
in the same package. Before deleting detail, move every durable contract,
safety rule, defect, decision, and evidence ceiling to its canonical subject
owner; then discard chronology, repeated totals, and superseded planning.

## Close and publish

Close by reviewing the semantic result, running the applicable validation, and
verifying acceptance. For every architecture-campaign slice, report actual
deltas separately for maintained product implementation, protections/tests,
retained evidence, configuration/documentation, public concepts, compatibility
paths, and justified mutable state; do not net categories. Update the campaign
register and temporary-path disposition. Commit the completed result once,
except that approved evidence deletion remains its own commit. A clean local
commit does not authorize publication: push only when explicitly approved,
then prove the intended remote ref and upstream equality. Runtime and cluster
promotion remain separately authorized and upstream-sequential.
