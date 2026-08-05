# DOC-CONS-08F — Compress design and architecture views

## Objective

Keep architecture and design documents conceptual and rationale-focused while
routing exact identities, contracts, target homes, and migration procedure to
their dedicated owners.

## Why this exists

Recent architecture work created exact owners beside the target contracts, but
older architecture/design views still contain detailed rosters, identity and
edge tables, contract prose, procedures, status, and a waterfall-style roadmap
diagram.

## Fixed decisions

- Never merge implemented current topology with target architecture.
- `STAGE_MAP.md`, `SOURCE_TOPOLOGY.md`, `MIGRATION_MECHANICS.md`, the functional
  inventory, and colocated contracts remain exact owners.
- `DECISIONS.md` retains rationale, alternatives, and consequences rather than
  copied procedure or mutable status.
- `QUESTIONS.md` retains open choices and a concise resolved index.
- Standalone Mermaid files remain canonical sources until unique diagram
  meaning has an inspected destination.
- Semantic category: bounded documentation or low-risk maintenance.
- Validation category: documentation-only/non-consuming. Computational,
  runtime, report-rendering, dependency, cluster, scientific-review, and
  biological evidence are not changed or promoted.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: conceptual/exact owner boundaries and destinations must be settled.

## Completion unblocks

- None.

## Prerequisites

- Compare each proposed removal with the exact contract owner and direct
  diagram references; broaden only on contradiction or unique meaning.

## Required context

- `ARCHITECTURE.md`, `FUTURE_ARCHITECTURE.md`,
  `FUNCTIONAL_OWNER_INVENTORY.md`, `DECISIONS.md`, `QUESTIONS.md`, affected
  Mermaid sources, and the three neutral contract owners. Read a local
  functional contract only to resolve a concrete mismatch.

## Questions owned by this card

- None.

## In scope

- Moving/removing copied rosters, identity/edge tables, contract detail,
  target homes, and migration procedure after destination parity.
- Compressing decision crosswalks, copied procedures/status, and verbose
  resolved-choice prose to durable links.
- Rewriting or retiring `future_roadmap_sequence.mmd` only after preserving its
  semantically unique target relationships without a universal waterfall claim.
- Repairing links and retaining minimal accurate current and target summaries.

## Out of scope

- Changing topology, DAG, contracts, architecture decisions, migration
  mechanics, scientific meaning, implementation, or roadmap order.

## Deliverables

- Concise conceptual architecture/design views with exact, nonduplicated links
  to contract owners and a reconciled future-roadmap diagram disposition.

## Acceptance evidence

- Current and target topology remain explicitly distinct and accurate.
- Every removed exact table/procedure exists once in its dedicated owner.
- Every durable rationale, rejected alternative, consequence, and unique
  diagram relationship remains discoverable.
- Reciprocal architecture/contract links and the documentation gate pass.

## Canonical documentation updates

- The five architecture/design views, affected Mermaid sources and contract
  links, the ownership ledger, and this card.

## Escalation conditions

- Stop if current and target owners conflict, a diagram contains unmapped
  meaning, or compression would change a scientific/architectural decision.

## Completion record

Selected on 2026-08-05 from clean, published, live-remote-equal predecessor
`a772f791141aee9fdb3fcfbd932f2dd2c1e93521` on
`codex/residual-source-topology-convergence`. This status-only selection does
not compress a view, change an exact owner, select a successor, or promote
evidence. The approved implementation is limited to the named conceptual
architecture/design views and their directly affected navigation links; it
stops on any current/target contradiction or unique unmapped meaning.
