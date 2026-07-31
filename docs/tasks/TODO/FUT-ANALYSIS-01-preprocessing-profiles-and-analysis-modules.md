# FUT-ANALYSIS-01 — Preprocessing profiles and analysis modules

## Objective

Design the future typed extension model for selectable preprocessing profiles,
built-in analysis modules, and scientist-authored R analyses.

## Why this exists

The intended long-term system should preprocess compatible DNA/RNA inputs and
branch into a library of analyses or a custom R implementation. Different
assays may require different preprocessing, so treating one fixed trunk as
universal would be a category error.

## Fixed decisions

- This capability is future-only and must not expand the current refactor.
- Use typed profile DAGs and typed branch artifacts, not one universal
  preprocessing core.
- The current CMH workflow may become the first built-in analysis module.
- Preserve a path for exploratory custom modules and more trusted registered
  modules, with explicit provenance and evidence limits.
- Do not build a generic loader, registry, or universal schema before concrete
  modules justify it.

## Blocked by

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Required: this future capability must not divert the current refactor.

## Completion unblocks

- None.

## Prerequisites

- Inspect the final stage/contracts topology, intake/run model, current CMH
  module candidate, and at least one concrete additional analysis use case.

## Required context

- Future architecture, semantic DAG, run identity/evidence contracts, R
  execution rules, report projection model, and scientific-review boundaries.

## Questions owned by this card

- [`CHOICE-ANALYSIS-01`](../../design/QUESTIONS.md#choice-analysis-01--analysis-module-trust-and-registration-model).

## In scope

- Feasibility, profile/module interfaces, typed artifacts, custom R boundary,
  trust/provenance model, analysis-specific reports, and bounded prototype plan.

## Out of scope

- Implementing a registry now, claiming every assay is compatible, public-data
  acquisition, changing current CMH science, or arbitrary unvalidated plugins.

## Deliverables

- A future design with concrete compatibility criteria and one small prototype
  recommendation or explicit infeasibility boundary.

## Acceptance evidence

- At least two concrete analysis cases can be expressed without weakening typed
  contracts, run identity, evidence states, or assay-specific preprocessing.
- Custom R execution has explicit inputs/outputs, dependency, isolation,
  provenance, failure, and reporting semantics.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, future diagrams, `DECISIONS.md`, `QUESTIONS.md`,
  task registry, and this card.

## Escalation conditions

- Stop if the model requires untyped file discovery, conflates exploratory and
  trusted analysis, or assumes biological equivalence across assays.

## Completion record

Not started. This future-only card requires a separate planning discussion and
approval after the current refactor.
