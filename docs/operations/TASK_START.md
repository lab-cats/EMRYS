# Task-start context

Use this file to give an agent the **smallest sufficient current context** for
one bounded NORAD task. It selects what to inspect before planning; it does not
copy mutable project state, authorize changes, or replace the delivery
[workflow](WORKFLOW.md).

## Minimum context packet

Load only these sources at task start:

1. The exact current root [`AGENTS.md`](../../AGENTS.md).
2. Live Git identity and state: repository root, branch, `HEAD`, worktree
   changes, upstream relation, and any competing worktree relevant to the task.
3. The selected task card in full, or one explicitly bounded objective when no
   card is needed. `UNREFINED` proposals are not selectable.
4. The directly affected functional owners: implementation, adjacent
   `README.md` or `CONTRACT.md`, public callers and consumers, tests, and
   fixtures that define or exercise the affected behavior.
5. Only the applicable sections of canonical documents linked by the card or
   affected owners. Use [HANDOFF](HANDOFF.md) for current evidence and blockers,
   [PIPELINE_PLAN](../design/PIPELINE_PLAN.md) for roadmap and acceptance, and
   the [architecture index](../architecture/README.md) for cross-owner identity
   and dependency direction.

Do not preload the full documentation corpus, history, unrelated cards, every
owner, all tests, or entire canonical documents merely for orientation. Do not
infer live state from memory, an agent identity, a conversation summary, an old
test total, or a former branch.

## Reuse exact context

Prior context may replace a reread only when its exact revision is known, the
live diff proves the relevant content unchanged, and the retained context is
sufficient for the current decision. Otherwise read the current source.

## Expand when required

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
always outrank context reduction. Once the context packet is sufficient, use
the [workflow](WORKFLOW.md) to propose the plan, obtain approval, deliver,
validate, and close the task.
