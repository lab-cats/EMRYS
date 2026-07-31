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
   consumers, tests, and fixtures.
4. Read only the applicable current-state, roadmap, command, decision,
   question, troubleshooting, and architecture sections identified below.
5. Expand immediately when an escalation trigger applies.
6. State the inspected revision, proposed scope, validation evidence, and any
   unresolved blocker in the task-specific plan. Obtain approval before
   mutation, apart from the permitted card-selection move in `AGENTS.md`.

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

| Need | Canonical route |
| --- | --- |
| Current checkout, evidence boundary, blockers, or resume point | Applicable sections of [`HANDOFF.md`](HANDOFF.md) |
| Package status, lineage, order, or acceptance | Applicable sections of [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) |
| Exact setup, validation, cluster, or recovery command | Applicable heading in [`RUNBOOK.md`](RUNBOOK.md) |
| Concurrent lane roles, authority, coupling, handoff, or integration | [`CONCURRENT_WORK.md`](CONCURRENT_WORK.md) plus live lanes in `HANDOFF.md` |
| Durable rationale or settled constraint | Applicable decision in [`DECISIONS.md`](../design/DECISIONS.md) |
| Open operational, scientific, or design choice | Applicable entry in [`QUESTIONS.md`](../design/QUESTIONS.md) |
| Symptom, cause, diagnosis, or fix | Applicable heading in [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| Current topology or contract flow | Applicable section of [`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) |
| Target topology or deferred constraint | Applicable section of [`FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md) |
| Task scope, dependencies, and acceptance | Selected card and [`docs/tasks/README.md`](../tasks/README.md) |
| Concise user entry point or repository map | Applicable section of [`README.md`](../../README.md) |
| Prioritized pending work | Applicable section of [`TODO.md`](../../TODO.md) |

Use repository-wide targeted search to find changed names, paths, commands,
interfaces, schema versions, evidence terms, and inbound references. Search
coverage may be repository-wide without loading every matching file in full.

## Situation matrix

| Situation | Required inspection |
| --- | --- |
| New agent or unknown prior context | This document and selected card in full, governing instructions, live Git state, and card-routed canonical sections |
| Same task with an exact verified baseline | Changes since that baseline; reuse unchanged material while the freshness-and-sufficiency conditions above still hold |
| New task in the same verified context | New card in full, live Git state, changes since the prior task, and newly relevant canonical sections |
| Phase boundary | Closing evidence, new phase/card, applicable lineage and acceptance sections, diff since the prior boundary, and changed or affected owners |
| Documentation patch | Complete final diff, affected sections and owners, inbound references, and affected diagrams |
| Starting a candidate lane | Assigned lane packet, absolute worktree, candidate branch or detached execution state, base, write set, prohibited overlaps, and coupling assumptions |
| Integrating a candidate | Latest canonical state, immutable candidate handoff, complete base-to-candidate diff, overlap/coupling recheck, and combined validation obligation |
| Cross-cutting or high-risk uncertainty | Every relevant canonical owner and direct consumer; broaden until the risk is resolved |
| Ownership migration, contradiction, or broad audit | Broader full-file or corpus reading as the evidence requires |

A phase boundary is an expansion signal, not an automatic instruction to read
the complete canonical corpus. Reassess ownership, interfaces, acceptance, and
changes since the prior boundary, then broaden according to impact.

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

For every final change, use the complete diff from the package predecessor or
validated implementation commit—not only the current worktree—to identify
affected documentation and diagrams. Before commit, include staged, unstaged,
and untracked paths; after commit, compare the exact commits. Search the full
repository for each changed interface, path, command, schema, status, evidence
term, and ownership claim. Inspect the affected sections, canonical owners,
direct references, and changed diagrams. Broaden semantic reading only when an
expansion trigger applies.

Candidate-only validation is provisional. When concurrent work exists, impact
classification and closure use the final combined canonical diff after
serialized integration; no candidate branch alone can publish package status,
completion, or evidence.

Keep the automated repository-wide documentation gate. Its global link,
anchor, card, dependency, and Mermaid checks provide broad structural coverage
without loading the full corpus into agent context. Automated structure does
not replace targeted semantic comparison.

When the complete package diff contains only documentation artifacts and none
is consumed by executable, configuration, generation, schema, fixture, report-
template, or test-harness selection or execution behavior, computational
validation is not applicable. Run only the Git and documentation checks owned
by [`RUNBOOK.md`](RUNBOOK.md#local-validation-gate). Do not run computational
Python, shell, R, or report-runtime test suites.

A documentation patch following implementation may rely on that executable
state's recorded computational gate when Git proves the state unchanged. A
standalone documentation-only package records computational validation as not
applicable rather than claiming a new computational pass.
