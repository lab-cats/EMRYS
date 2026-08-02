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
- Preserve the user-owned `ARCHITECTURE.md` edit outside JIT-01.
- Defer general documentation migration, validator redesign, `AGENTS.md`
  cleanup, child-sitemap design, and `ARCH-02B`.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- The completed [ARCH-02A inventory](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md)
  is the inspected predecessor.
- The user-owned architecture edit remains unchanged and outside every JIT-01
  commit.

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

- The temporary `work/active/JIT-01.md` record and its removal at reconciliation.
- The top-level sitemap bootstrap and the bounded task-delivery procedure.
- The reduced task-start router, the three named card enrichments, and one
  concise sitemap follow-up card.
- A fully dispositioned cleanup queue and a final published documentation-only
  package.

## Acceptance evidence

- Every slice was bounded by the exact three-line charter and committed at its
  stopping condition without future-slice inspection or collateral expansion.
- Final review confirms information preservation, owner separation, and complete
  cleanup dispositions.
- Git checks and one final repository documentation validation pass; computational,
  R, shell, report-runtime, and cluster suites remain not applicable.
- The final branch is clean, published, and upstream-equal, and the temporary
  active record is absent.

## Canonical documentation updates

- Only this card, its required registry references, and the documentation owners
  explicitly named by the active slice or final reconciliation.

## Escalation conditions

- Stop if the preservation-only architecture diff changes, the current validator
  makes the bounded procedure impossible, or safe information preservation
  requires work outside the active slice.

## Completion record

In progress. The approved bootstrap selects this card before content slices
begin; final stable evidence will be recorded once during reconciliation.
