# Task-start context

This document is the concise routing owner for repository task starts. Read it
in full when beginning a task unless the exact current version is already
available in the active context. It points to canonical truth; it does not copy
current branch, evidence, command, roadmap, or test-total state.

A task is one selected card or other explicitly bounded package, not each user
message within an uninterrupted task. A materially different objective starts
a new context-routing decision even if it arrives in the same conversation.

`AGENTS.md` remains the governing conduct and safety instruction. Repository
tooling may supply it automatically. If the active context does not contain its
exact current version, read it before planning.

## Temporary critical runway

Open only the
[temporary critical runway route](../sitemap/TOP_LEVEL.md#temporary-critical-runway)
when current work selection or frozen-scope boundaries are relevant.

## Minimum start

Before proposing a task-specific plan:

1. Inspect the live branch, `HEAD`, worktree, upstream relationship, worktree
   list, and the latest clean, docpatched package predecessor identified by
   `HANDOFF.md` and `PIPELINE_PLAN.md`, when applicable. If concurrent work is
   recorded, verify the assigned absolute worktree, candidate branch or
   detached execution state, base, lane packet, and write set against
   `CONCURRENT_WORK.md`. Do not infer current state from agent identity,
   conversation, or memory.
2. Read the selected task card in full. If no card exists, bound the objective
   explicitly and decide whether a card is required before mutation.
3. Follow the card's `Required context` links, named anchors, and named local
   surfaces; inspect the directly affected implementation, contracts,
   consumers, tests, and fixtures. For an integration-fragment handoff, also
   read the candidate-side schema and inspect the exact blob at the frozen
   published source SHA; do not substitute a moving worktree copy.
4. Read only the applicable current-state, roadmap, command, decision,
   question, troubleshooting, and architecture sections identified below.
5. Expand immediately when an escalation trigger applies.
6. State the inspected revision, proposed scope, validation evidence, and any
   unresolved blocker in the task-specific plan. Obtain approval before
   mutation, apart from the permitted card-selection move in `AGENTS.md`.

After approval, follow the bounded slice and card-close procedure in
[`TASK_DELIVERY.md`](TASK_DELIVERY.md).

## Context freshness and reuse

Existing context may replace a reread only when all of these are true:

- the exact prior file revision or worktree content is identifiable;
- live Git inspection proves the relevant content unchanged;
- the active context retains the detail needed for the current decision; and
- no contradiction, ownership change, or escalation trigger makes broader
  inspection necessary.

For a known prior revision, inspect the diff and the changed sections with
enough surrounding context to recover meaning. A full-file reread is required
only when the change reorganizes ownership or structure, affects dispersed
sections, creates a contradiction, or cannot otherwise be bounded safely.

An unversioned summary, memory, prior-agent statement, old handoff excerpt, or
test total is orientation only. Verify mutable claims against the live checkout.
Compaction does not automatically invalidate context, but reread the exact
relevant source when the retained summary lacks necessary wording or evidence.

## Canonical routing

Open only the needed entry in the
[canonical routing table](../sitemap/TOP_LEVEL.md#canonical-routing); do not
read the entire top-level map.

## Situation matrix

Open only the applicable row in the
[situation matrix](../sitemap/TOP_LEVEL.md#situation-matrix); do not read the
entire top-level map.

## Mandatory expansion triggers

Broaden inspection when any of these applies:

- the prior revision or relevant context cannot be identified reliably;
- targeted sources disagree or a mutable fact appears to have two owners;
- canonical documentation ownership or document structure changes;
- a public CLI, schema, file format, path, command, contract, or compatibility
  promise changes;
- scientific method, evidence language, biological interpretation, or
  promotion state is involved;
- safety, concurrency, locking, publication, rollback, cleanup, recovery,
  cluster execution, credentials, or production artifacts are involved;
- a concurrent lane packet is missing or stale, the worktree/branch/base does
  not match it, write sets overlap, or a coupling assumption changed;
- shared code, dependencies, configuration, test-harness selection or
  execution, generated inputs, or several stages/domains may be affected; or
- the affected surface cannot be bounded confidently from the selected card,
  canonical owners, implementation, consumers, and tests.

Correctness, safety, scientific and evidence integrity, and effective task
completion always outrank context reduction.

## Documentation impact and validation

At final documentation-impact or validation selection, open only the
[documentation impact and validation route](../sitemap/TOP_LEVEL.md#documentation-impact-and-validation).
