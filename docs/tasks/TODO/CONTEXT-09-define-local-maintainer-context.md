# CONTEXT-09 — Define local maintainer context

## Objective

Define the minimal code-adjacent context bundle that lets a maintainer plan one
stage or domain without loading the entire repository.

## Why this exists

Correct work currently requires broad reads because responsibilities and
contracts are distributed. Local context can reduce token and cognitive cost,
provided it links to canonical cross-cutting truth rather than copying it.

## Fixed decisions

- Correctness outranks token reduction; broad reads remain required at phase
  and cross-cutting boundaries.
- Each local context explains purpose, local files, input/output contracts,
  direct upstream/downstream interfaces, relevant tests, and canonical links.
- Local context never duplicates mutable branch, evidence, command, or roadmap
  state.

## Blocked by

- [ARCH-02C](../TODO/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: local domain and contract ownership must be settled.
- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: canonical ownership and audiences must be settled.
- [DOC-README-03](../TODO/DOC-README-03-establish-directory-readme-coverage.md) — Required: the local README convention must be proven.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: local planning boundaries are one integrated-plan input.

## Prerequisites

- Sample representative stages, reporting, evidence, and scheduler domains to
  measure what context a bounded task actually needs.

## Required context

- Target topology, semantic map, README matrix, contract placement, task-start
  rules, and current canonical owner table.

## Questions owned by this card

- [`CHOICE-CONTEXT-01`](../../design/QUESTIONS.md#choice-context-01--exact-scope-aware-canonical-reading-policy).

## In scope

- Local README/contract template, upstream/downstream link rule, required test
  references, escalation triggers, and a token/cognitive-load evaluation.

## Out of scope

- Weakening canonical task-start reads globally, embedding full repository
  state in each stage, or generating summaries from unverified code.

## Deliverables

- A reviewed local-context standard and integration instructions for migration,
  README, and code-documentation cards.

## Acceptance evidence

- A maintainer can correctly scope representative local work from the bundle
  and canonical links; cross-cutting risks still trigger broader inspection.
- No mutable fact gains a second owner.

## Canonical documentation updates

- `AGENTS.md`, `FUTURE_ARCHITECTURE.md`, local README conventions,
  `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if token savings require omitting scientific, recovery, publication, or
  public-contract context needed for correctness.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
