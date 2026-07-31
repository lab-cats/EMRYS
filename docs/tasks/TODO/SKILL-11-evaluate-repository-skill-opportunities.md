# SKILL-11 — Evaluate repository skill opportunities

## Objective

Evaluate which additional recurring NORAD workflows merit skills after the
documentation-health skill and current refactor are complete.

## Why this exists

Some repeated audits or handoffs may benefit from reusable guidance, but
premature skill creation would divert attention and freeze unstable workflows.

## Fixed decisions

- This is an evaluation card, not authorization to create multiple skills.
- Prioritize low-lift, high-value, stable, repeated workflows with clear safety
  boundaries.
- Prefer repository docs/scripts when a workflow is not reusable enough to
  justify a skill.

## Blocked by

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Required: evaluate only after the current refactor and first documentation skill are closed.

## Completion unblocks

- None.

## Prerequisites

- Inspect actual repeated task history and the effectiveness/maintenance cost
  of `DOC-SKILL-10`.

## Required context

- Completed task registry, documentation-health skill, runbook workflows,
  refactor retrospectives, and then-current skill platform guidance.

## Questions owned by this card

- None.

## In scope

- Candidate inventory, frequency/value/risk/stability analysis, recommendation,
  and exact follow-up card for each approved skill.

## Out of scope

- Creating candidates during evaluation, broad plugin work, or automating
  destructive/runtime/cluster operations without explicit authority.

## Deliverables

- A short evidence-based recommendation: create, keep as docs/scripts, or defer.

## Acceptance evidence

- Every recommendation cites repeated use and a stable contract; rejected ideas
  state why a skill would add cost or risk.

## Canonical documentation updates

- Task registry, `DECISIONS.md` only for durable skill-governance changes, and
  this card.

## Escalation conditions

- Stop if evaluation would divert into building a skill or if usage evidence is
  too sparse to justify a decision.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
