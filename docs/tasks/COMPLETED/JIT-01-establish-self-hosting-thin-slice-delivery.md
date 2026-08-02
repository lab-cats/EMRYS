# JIT-01 — Establish self-hosting thin-slice delivery

## Objective

Establish a minimal, self-hosting thin-slice procedure before `ARCH-02B`
without beginning general documentation reorganization.

## Why this exists

The repository needs a small delivery procedure that is exercised by its own
creation before the next architecture card is selected.

## Fixed decisions

- Use one card, branch, and worktree; slices are linear checkpoint commits.
- Each active slice has exactly `Outcome`, `Touches`, and `Stop`; read and plan
  only that slice.
- Capture collateral observations neutrally without investigating or resolving
  them during a slice.
- Include the user-owned `ARCHITECTURE.md` deletion unchanged in the final
  JIT-01 reconciliation commit.
- Retain noncritical input-dependent items in the active record as decision
  artifacts until their dispositions are durable.
- Defer general documentation migration, validator redesign, `AGENTS.md`
  cleanup, child-sitemap design, and `ARCH-02B`.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- The completed [ARCH-02A inventory](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md)
  is the inspected predecessor.
- The user-owned architecture deletion remains unchanged until its authorized
  inclusion in final reconciliation.

## Required context

- The [task-start router](../../operations/TASK_START.md), this card, and only
  the owners and paths named by the active three-line slice charter.
- The current documentation validator only when its existing registry or link
  requirements directly constrain the active slice.

## Questions owned by this card

- None.

## In scope

- A temporary active-work record and neutral cleanup queue.
- A minimal top-level sitemap bootstrap.
- A thin-slice delivery procedure and a concise universal task-start router.
- Constraint-only enrichment of the three cards explicitly named by the
  approved objective.
- Final cleanup, reconciliation, review, documentation validation, verification,
  and publication.

## Out of scope

- General documentation reorganization, permanent child-map design, validator
  redesign, executable behavior, dependency changes, and `ARCH-02B` work.
- Routine roadmap, handoff, status, diagram, card, or reference maintenance at
  ordinary slice boundaries.

## Deliverables

- The temporary `work/active/JIT-01.md` record, retained after reconciliation
  only while it contains input-dependent decision artifacts.
- The top-level sitemap bootstrap and the bounded task-delivery procedure.
- The reduced task-start router, the three named card enrichments, and one
  concise sitemap follow-up card.
- Resolved cleanup items plus explicit durable classifications for retained
  input-dependent decisions, and a final published documentation-only package.

## Acceptance evidence

- Every slice was bounded by the exact three-line charter and committed at its
  stopping condition without future-slice inspection or collateral expansion.
- Final review confirms information preservation, owner separation, resolved
  cleanup corrections, and durable classification of retained decisions.
- Git checks and one final repository documentation validation pass; computational,
  R, shell, report-runtime, and cluster suites remain not applicable.
- The final branch is clean, published, and upstream-equal. The active record is
  absent unless it retains an explicitly classified input-dependent decision.

## Canonical documentation updates

- Only this card, its required registry references, and the documentation owners
  explicitly named by the active slice or final reconciliation.
- Final reconciliation updates `HANDOFF.md`, `PIPELINE_PLAN.md`, and `TODO.md`
  once so the completed bootstrap and `ARCH-02B` resume point agree.

## Escalation conditions

- Stop if the architecture deletion changes beyond its authorized content, the
  current validator makes the bounded procedure impossible, or safe information
  preservation requires work outside the active slice.

## Completion record

Completed as a documentation-only self-hosting procedure before `ARCH-02B`.
The final reconciliation preserves one concise task-start router, temporary
targeted routing in the top-level sitemap, bounded delivery and cleanup rules,
and the approved architecture deletion. The base-to-tip semantic review and
the repository documentation gate cover the final published content;
computational, R, shell, report-runtime, and cluster validation are not
applicable.

The retained [decision record](../../../work/active/JIT-01.md) preserves only
noncritical input-dependent items. Future sitemap classification and
touch-move-delete migration are owned by
[`DOC-SITEMAP-01`](../TODO/DOC-SITEMAP-01-classify-temporary-task-start-routing.md).
Publication and exact checkout evidence remain in
[`HANDOFF.md`](../../operations/HANDOFF.md).
