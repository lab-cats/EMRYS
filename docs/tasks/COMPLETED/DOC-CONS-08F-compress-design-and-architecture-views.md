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
`codex/residual-source-topology-convergence`; status-only selection checkpoint
`1da90c561cf5abb93fa695157b64624ce2089bf0` was published and proved
live-remote-equal before authoring.

The completed documentation-only/non-consuming package:

- reduces the five architecture/design views from 2,710 to 2,132 lines:
  `ARCHITECTURE.md` 287 to 170, `FUTURE_ARCHITECTURE.md` 563 to 553,
  `FUNCTIONAL_OWNER_INVENTORY.md` 188 to 154, `DECISIONS.md` 1,314 to
  1,000, and `QUESTIONS.md` 358 to 255;
- makes `ARCHITECTURE.md` a conceptual current-system view, retains the exact
  executable/residual roster in the inventory, and routes identities, DAG,
  interfaces, defects, target homes, and migration mechanics to their owners;
- removes stale flat-layout, unfinished-migration, reverse-dependency, and
  Step-00a shared-helper claims without changing a topology or contract;
- preserves the unique intake, filesystem-state, logging, reporting,
  extension, acquisition, documentation, deferral, scientific, and evidence
  constraints while replacing mutable status/procedure and the duplicate task
  crosswalk with canonical links;
- retains all thirteen unresolved choice headings and their card backlinks,
  gives every previously unique resolved `CHOICE-*` ID a durable decision
  label, and replaces verbose resolved prose with a compact owner index;
- retires `future_roadmap_sequence.mmd` after proving that its relationships
  already live in the roadmap, future constraints, and task graph and that its
  universal-waterfall implication conflicts with rolling JIT delivery; and
- corrects the grouped current pipeline and reliability diagrams, the neutral-
  seam implementation tense, and the ownership/no-loss ledger.

Three independent semantic reviews found no remaining current/target
contradiction, owner misrouting, unresolved-choice loss, diagram-semantic loss,
or evidence overclaim after their findings were corrected. Final
`git diff --check` and `make -s documentation-check` pass on the exact completed
tree: 231 Markdown documents, 148 task cards, and 5 Mermaid sources.
Computational, shell, R, report-runtime, dependency, full-suite, runtime,
cluster, scientific-review, and biological validation are not applicable
because the complete selection-to-close diff is non-consuming documentation
only. No successor is selected by this close.
