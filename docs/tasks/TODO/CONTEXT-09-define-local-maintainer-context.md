# CONTEXT-09 — Define local maintainer context

## Objective

Define the minimal code-adjacent context bundle that lets a maintainer plan one
stage or domain without loading the entire repository.

## Why this exists

Correct work currently requires broad reads because responsibilities and
contracts are distributed. Local context can reduce token and cognitive cost,
provided it links to canonical cross-cutting truth rather than copying it.

## Fixed decisions

- Correctness outranks token reduction; local bundles extend the freshness,
  routing, and impact-based expansion rules in
  [`TASK_START.md`](../../operations/TASK_START.md).
- Load only context relevant to the current thin slice. Use task-oriented maps
  and targeted anchors for traversal rather than broad document bundles.
- Do not routinely reread unchanged documents when the task-start freshness
  conditions permit reuse, and do not load unrelated test or implementation
  context.
- Keep `TASK_START.md` universal and route conditional information elsewhere.
- Add child maps progressively as the repository evolves; parent maps link to
  them without duplicating their entries or contents.
- Observing cleanup debt does not expand the active slice or its context.
- Each local context explains purpose, local files, input/output contracts,
  direct upstream/downstream interfaces, relevant tests, and canonical links.
- Local context never duplicates mutable branch, evidence, command, or roadmap
  state.

## Blocked by

- [ARCH-02C](../IN_PROGRESS/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: local domain and contract ownership must be settled.
- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: canonical ownership and audiences must be settled.
- [DOC-README-03](../TODO/DOC-README-03-establish-directory-readme-coverage.md) — Required: the local README convention must be proven.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: local planning boundaries are one integrated-plan input.

## Prerequisites

- Sample representative stages, reporting, evidence, and scheduler domains to
  measure what context a bounded task actually needs.

## Required context

- Global `TASK_START.md` rules, target topology, semantic map, README matrix,
  contract placement, representative cards, and the canonical owner table.

## Questions owned by this card

- None. The global reading policy is resolved by `CONTEXT-00`; this card owns
  the later evidence needed to refine local stage/domain bundles.

## In scope

- Local README/contract template, upstream/downstream link rule, required test
  references, escalation triggers, and a token/cognitive-load evaluation.

## Out of scope

- Replacing the global task-start router, embedding full repository state in
  each stage, or generating summaries from unverified code.

## Deliverables

- A reviewed local-context standard and integration instructions for migration,
  README, and code-documentation cards.

## Acceptance evidence

- A maintainer can correctly scope representative local work from the bundle
  and canonical links; cross-cutting risks still trigger broader inspection.
- Representative tasks traverse targeted maps and anchors without routine
  unchanged-document rereads or unrelated test and implementation context.
- Cleanup observations remain deferred without expanding the active context.
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
