# CONCURRENCY-01 — Enable isolated concurrent documentation lanes

## Objective

Define and operationalize isolated documentation/card sidecars that can work
while implementation or execution continues, without creating competing
canonical state or contaminating another agent's worktree and evidence.

## Why this exists

The current single-descendant workflow serializes all repository mutation.
That protects package evidence but unnecessarily prevents maintainers from
creating future cards or improving independent documentation during a long
implementation or immutable execution. Allowing multiple writers in one
worktree would instead corrupt status, staging, validation, and handoff truth.

## Fixed decisions

- Parallel authoring uses separate branches and sibling worktrees followed by
  serialized integration into one authoritative linear lineage.
- Multiple documentation/card sidecars are permitted at the same time. Every
  authoring lane receives an absolute worktree path, unique branch, exact base
  commit, integration target, reserved card IDs or paths, explicit write set,
  prohibited overlaps, and coupling classification. Immutable execution uses a
  locked detached worktree at its exact pushed commit and records that identity
  instead of a branch.
- At most one implementation-candidate or immutable-execution lane may be
  active beside those sidecars. This card does not authorize parallel
  implementation candidates.
- The primary worktree is the single-writer integration/control lane.
  The implementation candidate and documentation branches are proposals until
  the integration owner accepts them.
- Independent documentation may land while implementation continues.
  Documentation that changes or relies on an unsettled active contract,
  acceptance criterion, architecture decision, or evidence claim is coupled:
  it remains a draft or triggers a committed checkpoint and re-plan.
- The integration owner alone finalizes live handoff, authoritative
  lineage/status, priority, active-card lifecycle, and completion/evidence
  claims. Completed cards remain historical.
- New cards created by sidecars remain TODO and never authorize themselves.
  Concurrent card IDs and central inbound references are reserved and
  reconciled by the integration owner.
- Long-running execution may coexist only when pinned to an immutable commit;
  later documentation never changes which code or inputs were executed.
- Final integration revalidates the combined tree. Computational evidence may
  be reused only when Git proves intervening documentation cannot affect any
  executable, configuration, schema, fixture, report-template, or test-harness
  consumer.
- Pause after this card is completed and pushed for a user strategy discussion
  before selecting `PROGRAM-01` or using the new workflow for active delivery.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Begin from a clean, pushed, upstream-equal canonical documentation package.
- Inspect the live worktree list, branch topology, task lifecycle, validation
  gate, and canonical current-state owners during task-specific planning.

## Required context

- The descendant-package decision and documentation-only gate in
  [`DECISIONS.md`](../../design/DECISIONS.md), task-start rules in
  [`TASK_START.md`](../../operations/TASK_START.md), the card lifecycle in
  [`../README.md`](../README.md), current lineage and handoff ownership, and
  exact Git commands in `RUNBOOK.md`.
- Current Codex/subagent filesystem behavior and the live `git worktree list`;
  do not infer isolation from agent identity alone.

## Questions owned by this card

- The exact reviewed worktree-creation, candidate-handoff, integration,
  verification, and recoverable-cleanup commands. These implement the fixed
  model; they do not reopen whether multiple sidecars are allowed.

## In scope

- A single-purpose concurrent-work policy owner with lane roles, write tiers,
  coupling rules, multi-sidecar coordination, handoff packet, and integration
  checkpoints.
- Concise automatic enforcement in agent/task-start instructions and exact
  commands in the runbook.
- Current-state representation for active lanes without making candidate
  branches canonical.
- Task-registry clarification for concurrent card creation, multiple active
  cards, ID/path reservation, and integration-time status authority.
- Sidecar and combined-state validation rules, stale-draft handling, conflict
  escalation, immutable-execution attribution, and recovery expectations.

## Out of scope

- Running a real implementation package concurrently, changing the program's
  planning methodology, migrating legacy blocker edges, adding an orchestration
  service or lock daemon, or modifying NORAD workflow/scientific behavior.

## Deliverables

- Durable parallel-authoring/serialized-integration decision and one canonical
  operational policy.
- A concise lane packet and write-authority matrix that supports multiple
  simultaneous documentation/card sidecars.
- Reviewed runbook commands for provisioning, inspecting, integrating, and
  preserving candidate worktrees without merging or rebasing active branches.
- Aligned task-start, registry, handoff, lineage, validation, and recovery
  guidance.

## Acceptance evidence

- A new agent can distinguish canonical, implementation-candidate,
  independent-sidecar, and coupled-draft state without relying on conversation
  history.
- The documented scenario supports at least two disjoint card/documentation
  sidecars while an implementation or immutable execution lane remains active.
- Only the integration owner can publish current status or completion claims;
  no two lanes share a mutable worktree, branch, reserved card ID, or write
  path.
- Independent and coupled documentation have unambiguous landing, re-planning,
  computational-evidence reuse, and final-validation rules.
- `git diff --check`, the repository documentation gate, and an independent
  read-only consistency audit pass; computational suites are not applicable to
  the policy-only package.

## Canonical documentation updates

- `AGENTS.md`, `README.md`, `TODO.md`, `DECISIONS.md`, `PIPELINE_PLAN.md`,
  `TASK_START.md`, `RUNBOOK.md`, `HANDOFF.md`, the task-registry lifecycle, the
  new concurrent-work policy owner, and this card.

## Escalation conditions

- Stop if two lanes require the same mutable path, a sidecar changes active
  behavior or acceptance without re-planning, integration would require
  rewriting an active branch, executable-tree identity cannot be proved, or a
  candidate's base/worktree/owner cannot be identified exactly.

## Completion record

Completed on 2026-07-31. The package added `CONCURRENT_WORK.md` as the canonical
policy owner; aligned agent, task-start, task-registry, roadmap, handoff,
decision, entry-point, and troubleshooting guidance; and added fail-closed Git
2.54 worktree, handoff, integration, evidence-reuse, publication, and
recoverable-cleanup commands to the runbook.

The settled model permits multiple isolated documentation/card sidecars beside
at most one implementation-candidate or locked detached immutable-execution
lane. One integration owner records durable packets, reserves paths and card
IDs, serializes frozen single-commit proposals into fresh canonical
descendants, amends integration-owned state before publication, validates the
combined tree, and preserves candidates by default. First active use remains
paused for the required user strategy discussion.

No concurrent delivery experiment ran and the preserved detached demo-report
worktree was not modified. The complete predecessor-to-final diff contains
Markdown only and changes no executable or test-affecting consumer, so
computational suites were not applicable. `git diff --check` and the repository
documentation gate passed with 72 Markdown documents, 51 task cards, and 6
Mermaid sources. Independent policy/ownership and Git/recovery audits found no
remaining actionable issue.
