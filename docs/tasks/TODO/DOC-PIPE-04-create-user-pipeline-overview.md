# DOC-PIPE-04 — Create user pipeline overview

## Objective

Create a short scientist-facing table and Mermaid overview that explain what
the pipeline does, why stages occur in sequence, and the conceptual inputs and
outputs.

## Why this exists

Maintainers need the detailed technical pipeline, but users also need a
minimal conceptual map. Numeric stage names and implementation-specific detail
currently make the overall scientific flow hard to grasp.

## Fixed decisions

- Preserve a conceptual general order even after the DAG becomes the machine
  authority.
- Use both a compact table and a Mermaid diagram.
- Explain purpose, sequence rationale, and contract shape without dense
  implementation details.
- Keep the current technical `pipeline.mmd` as a separate current-truth view.

## Blocked by

- [ARCH-02B](../TODO/ARCH-02B-define-semantic-stage-map.md) — Required: the overview needs approved semantic names and DAG order.
- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: audience, owner, and navigation placement must be settled.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: the conceptual map is one integrated-plan input.

## Prerequisites

- Verify every conceptual claim against current behavior and distinguish target
  branch points from implemented flow.

## Required context

- Semantic stage map/DAG, current `pipeline.mmd`, current/future architecture,
  glossary, input/output contracts, and scientist-facing report language.

## Questions owned by this card

- None.

## In scope

- One user-facing overview document or owned section, one Mermaid source,
  concise stage table, and navigation links.

## Out of scope

- Replacing the technical pipeline diagram, documenting commands, embedding
  branch/commit status, or presenting future analysis modules as implemented.

## Deliverables

- A reviewed conceptual table and Mermaid source with accessible prose fallback.

## Acceptance evidence

- A scientist unfamiliar with the repository can explain the major flow,
  branch points, ordering reasons, and artifacts without reading code.
- The overview remains consistent with the semantic map and evidence cautions.

## Canonical documentation updates

- `README.md`, appropriate architecture/user owner selected by `DOC-IA-01`,
  glossary links, diagram index, and this card.

## Escalation conditions

- Stop if simplification erases a scientifically meaningful branch or makes a
  target capability look current.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
