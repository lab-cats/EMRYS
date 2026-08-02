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
- Treat the overview's nine narrative phases as explanatory groupings, not
  stable machine identities. Current scripts and jobs remain separately
  invoked; arrows express data or contract dependency, not automatic
  scheduling or a one-command runner.

## Blocked by

- [ARCH-02B](../COMPLETED/ARCH-02B-define-semantic-stage-map.md) — Required: the overview needs approved semantic names and DAG order.
- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: audience, owner, and navigation placement must be settled.

## Completion unblocks

- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: the conceptual map is one integrated-plan input.

## Prerequisites

- Verify every conceptual claim against current behavior and distinguish target
  branch points from implemented flow.
- Re-synthesize only on a corrected, reviewed `DOC-REF-02` parent. That order
  is lineage/readiness, not a new technological blocker.

## Required context

- Semantic stage map/DAG, current `pipeline.mmd`, current/future architecture,
  glossary, input/output contracts, and scientist-facing report language.
- Treat completed `ARCH-02B` and its immutable `STAGE_MAP.md` as accepted input,
  not as an active blocker or a second identity owner.

## Questions owned by this card

- None.

## In scope

- `docs/architecture/PIPELINE_OVERVIEW.md`, one adjacent Mermaid source,
  concise stage table, and navigation links.

## Out of scope

- Replacing the technical pipeline diagram, documenting commands, embedding
  branch/commit status, or presenting future analysis modules as implemented.

## Deliverables

- A reviewed conceptual table and Mermaid source with accessible prose fallback.
- An explicit mapping from each explanatory phase to one or more canonical
  `ARCH-02B` semantic identities, allowing one-to-many and many-to-one
  relationships; every discrepancy with `STAGE_MAP.md` is resolved before
  acceptance rather than hidden by phase labels.
- An exact-input table preserving BED12 for library-orientation inference;
  reference/FAI through cohort observation; sample and partition manifests
  through Steps `07`–`09`; and GTF through Step `08`.
- Narrow current wording for Step `08`: validate the declared VCF set, expand
  alternate alleles, apply provisional orientation conversion, annotate, and
  publish deterministic TSVs. Step `09` states the declared RNA reference/
  alternate comparison plus depth, statistical, and effect thresholds, with
  an optional independent background cohort.
- A standalone `docs/architecture/diagrams/current_user_pipeline.mmd` source
  whose legend states that arrows are data/contract dependencies. Keep
  scientific review optional, mechanical orientation distinct from biological
  interpretation, and reporting conditional on selected HTML and/or PDF plus
  deterministic summary TSV and a validated identity-bound receipt last.
- The diagram uses at most two restrained shared-input nodes (reference/
  annotation contracts and sample/partition/analysis contracts), thin or
  dotted continuing-consumption edges, a dashed optional-background input, a
  dashed scientific-review branch labeled `if explicitly supplied`, and a
  direct rank-to-evidence path that does not make review mandatory.

## Acceptance evidence

- A scientist unfamiliar with the repository can explain the major flow,
  branch points, ordering reasons, and artifacts without reading code.
- The overview remains consistent with the semantic map and evidence cautions.
- Independent scientist/usability and architecture/traceability reviews cover
  current Steps `03`, `07`, `08`, `09`, and reporting; table, prose, and
  standalone Mermaid agree; no-loss, link, terminology, diagram, diff, and
  target documentation-gate checks pass.

## Canonical documentation updates

- `README.md`, `docs/architecture/PIPELINE_OVERVIEW.md`, glossary links,
  diagram index, and this card. Only after the corrected overview and diagram
  pass review, add their current/target routes to `ARCHITECTURE.md` and
  `FUTURE_ARCHITECTURE.md`, record durable ownership/rationale in
  `DECISIONS.md` and the documentation ownership map, and regenerate concise
  navigation/state links from actual canonical status.

## Escalation conditions

- Stop if simplification erases a scientifically meaningful branch or makes a
  target capability look current.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
