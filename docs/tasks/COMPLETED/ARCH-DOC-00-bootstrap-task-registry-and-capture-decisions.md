# ARCH-DOC-00 — Bootstrap task registry and capture architecture decisions

## Objective

Create the documentation substrate that preserves the approved architecture
direction and turns later work into separately planned, dependency-aware tasks.

## Why this exists

The repository-spanning refactor was already active, but the newly settled
source-layout, intake, reporting, logging, documentation, and extension
decisions existed only in one discussion. Without canonical rationale and
bounded cards, later agents could repeat those decisions or mistake broad
roadmap language for implementation approval.

## Fixed decisions

- Use the registry lifecycle and ownership boundary in
  [`../README.md`](../README.md).
- Record durable rationale in
  [`../../design/DECISIONS.md`](../../design/DECISIONS.md#approved-architecture-direction-2026-07-31)
  and target constraints in
  [`../../architecture/FUTURE_ARCHITECTURE.md`](../../architecture/FUTURE_ARCHITECTURE.md).
- This package changes documentation only; it does not execute or replace the
  active repository-spanning refactor.

## Blocked by

- None.

## Completion unblocks

- [TEST-01C](../COMPLETED/TEST-01C-characterize-validation-check-rosters.md) — Fully: the next existing refactor package has a canonical card and resume path.

## Prerequisites

- The `refactor-01b-validation-publication-faults` predecessor is clean,
  pushed, upstream-equal, and fully documented.
- The user has approved this documentation-only preparation package.

## Required context

- `AGENTS.md`, the nine canonical task-start documents, current/future
  architecture, Mermaid sources, `REFACTOR_AUDIT.md`, and `TEST_BASELINE.md`.
- The current Git lineage and the approved discussion decisions.

## Questions owned by this card

- None; unresolved implementation choices are transferred to stable entries
  in [`../../design/QUESTIONS.md`](../../design/QUESTIONS.md#open-choices).

## In scope

- Create the registry, lifecycle, template, and prospective task cards.
- Record approved decisions, reasoning, future constraints, open choices,
  roadmap relationships, and the next resume point.
- Update only future diagrams whose meaning changed.

## Out of scope

- Executable code, tests, schemas, configs, fixtures, report behavior, log
  behavior, source relocation, ingestion, or scientific policy.
- Task-specific planning or execution for any TODO card.

## Deliverables

- A file-backed task registry with reciprocal direct dependencies.
- A decision-capture crosswalk covering every settled or deferred discussion
  item.
- Updated canonical roadmap, future architecture, questions, README, agent
  instructions, handoff, and future Mermaid sources.

## Acceptance evidence

- Every prospective card has one status location, the required headings, a
  stable unique ID, valid links, and no hard-dependency cycle.
- Every approved decision maps to a durable owner and one or more task cards.
- The diff contains only Markdown and Mermaid sources and passes the
  documentation gate.

## Canonical documentation updates

- `AGENTS.md`, `README.md`, `TODO.md`, `docs/design/DECISIONS.md`,
  `docs/design/QUESTIONS.md`, `docs/design/PIPELINE_PLAN.md`,
  `docs/architecture/FUTURE_ARCHITECTURE.md`, future Mermaid sources,
  `docs/operations/RUNBOOK.md`, and `docs/operations/HANDOFF.md`.

## Escalation conditions

- Stop if recording the direction would require representing target behavior
  as implemented, changing current architecture truth, or authorizing a future
  task without its own plan.

## Completion record

Completed by the approved documentation-only architecture-direction package.
The canonical handoff records the inspected documentation evidence; no
executable or scientific evidence state changed.
