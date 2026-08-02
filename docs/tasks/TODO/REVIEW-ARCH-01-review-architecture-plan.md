# REVIEW-ARCH-01 — Review architecture plan

## Objective

Independently challenge the integrated topology, dependency direction,
contract placement, migration sequence, and extension seams.

## Why this exists

The plan will combine many locally reasonable decisions. An independent review
is needed to catch cycles, ambiguous ownership, framework creep, accidental
compatibility layers, and branch-point category mistakes before implementation.

## Fixed decisions

- Review only; do not implement fixes in the review card.
- Evaluate the approved vertical target and direct-migration policy rather than
  reopening settled preferences without evidence.
- Reject stage-to-stage implementation imports, generic `utils`, and a
  universal preprocessing trunk.

## Blocked by

- [PLAN-02Z](../COMPLETED/PLAN-02Z-integrate-future-task-sequence.md) — Required: the rolling plan boundary and generated card set must exist.

## Completion unblocks

- [REVIEW-REL-02](../TODO/REVIEW-REL-02-review-reliability-plan.md) — Fully: reliability review can operate on an architecture-corrected plan.

## Prerequisites

- Assign a reviewer/agent that did not author the integrated plan and provide
  read-only access to all evidence.

## Required context

- Integrated task DAG, target/current architecture, behavior matrix, functional
  inventory, semantic map, migration policy, shared-library map, and future
  extension constraints.

## Questions owned by this card

- None.

## In scope

- Ownership, dependency direction, cohesion, contract/API placement, test
  topology, migration reversibility, non-Python assets, and future extension
  compatibility.

## Out of scope

- Reliability fault detail except where topology creates it, usability polish,
  implementation, or package distribution.

## Deliverables

- Evidence-ranked findings with accept/revise/defer dispositions and exact card
  changes.

## Acceptance evidence

- Every finding is resolved in the plan/cards or explicitly accepted by the
  user with consequences recorded.
- No implementation card remains dependent on an unresolved ownership or
  dependency-direction question.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, task registry, `QUESTIONS.md`, `DECISIONS.md` only for
  approved durable changes, and this card.

## Escalation conditions

- Stop if the review requires overturning a settled decision, changing
  scientific policy, or implementing to determine whether the design is valid.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
