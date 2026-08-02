# DOC-CONS-08B — Compress root entry and priority views

## Objective

Make `README.md` a concise newcomer entry and `TODO.md` a short current-priority
view without duplicating history, roadmap, or task-registry ownership.

## Why this exists

Both root views contain valuable routes. DOC-IA replaced the README's full
documentation roster with the sitemap route, but the development model remains
detailed while TODO preserves completed lineages, frozen sequences, and
task-family catalogs owned elsewhere or awaiting a real index.

## Fixed decisions

- Preserve product identity, the evidence boundary, minimal start, shallow
  repository map, and action-point data/approval cautions in `README.md`.
- Preserve only current prioritized gates and blocker routes in `TODO.md`.
- Link the documentation ownership map, current handoff, roadmap, and task
  registry instead of copying their contents.
- Do not turn `TODO.md` into a logical registry index; that remains
  `TASK-EPIC-01` work.
- Retain any semantically unique task-family grouping in `TODO.md` until an
  existing owner is verified or `TASK-EPIC-01` creates the accepted index.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: root audiences, retained facts, and destinations must be settled.

## Completion unblocks

- None.

## Prerequisites

- Reconcile the live current priority against `HANDOFF.md`, `PIPELINE_PLAN.md`,
  and card-directory status immediately before editing.

## Required context

- Root `README.md` and `TODO.md`, the audience routes and root ledger rows in
  `DOCUMENTATION_OWNERSHIP.md`, and only affected current-state/roadmap/task
  sections.

## Questions owned by this card

- None.

## In scope

- Preserving and tightening the concise sitemap route that replaced the former
  root documentation roster.
- Compressing development-process prose to canonical links while retaining
  newcomer safety meaning.
- Removing completed history, frozen sequence detail, family catalogs, and
  future catalogs from `TODO.md` only after each retained fact is reachable in
  an existing owner; otherwise retaining the unique grouping explicitly.
- Repairing direct inbound links.

## Out of scope

- Changing task order, lifecycle, blockers, architecture, evidence state, or
  creating logical epic indexes.

## Deliverables

- Short, audience-specific root entry and priority documents with verified
  canonical routes.

## Acceptance evidence

- A user, operator, scientist, and maintainer can each reach the appropriate
  owner from the root in a short path.
- No completed history, roadmap, status matrix, or registry catalog has two
  owners.
- Unique product, evidence, start, and data-safety meaning remains visible.
- Documentation links and the documentation gate pass.

## Canonical documentation updates

- `README.md`, `TODO.md`, affected sitemap routes, and this card.

## Escalation conditions

- Stop if current owners disagree, a root safety caveat would disappear, or a
  historical statement lacks a discoverable destination.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
