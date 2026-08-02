# TASK-EPIC-01 — Implement logical epic definitions and indexes

## Objective

Implement one canonical README/index per logical task epic while preserving
flat lifecycle directories and existing status ownership.

## Why this exists

Stable card prefixes already describe broad task families, but maintainers
lack a concise local explanation of each family and its relationships. Copying
category directories beneath every lifecycle state would multiply READMEs,
move links whenever classification changes, and force cross-cutting work into
one physical hierarchy.

## Fixed decisions

- Under current authority, cards remain flat beneath lifecycle-status
  directories and no physical category subdirectories are created. The
  selected future target uses permanent ID-only canonical card paths; neither
  current nor target placement encodes epic identity.
- `docs/tasks/epics/README.md` owns the epic index, identifier rules, and
  membership conventions. Each `docs/tasks/epics/<EPIC-ID>/README.md` owns one
  stable thematic description and links to member cards.
- An epic is navigation and bounded shared context, never lifecycle status,
  authorization, execution order, a dependency edge, a planning cohort, or a
  delivery tranche.
- Epic indexes link to card-owned scope and status rather than copying mutable
  priority, branch, evidence, blocker, or completion claims.
- [`PROGRAM-01`](../IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
  settles the initial taxonomy, membership cardinality, and distinction among
  category, epic, cohort, and tranche. This card implements that reviewed
  model without reopening it.
- Physical category nesting remains deferred unless later measured navigation
  evidence justifies a separately approved migration.
- Epic indexes or pages are committed generated views and must be
  byte-for-byte check-regenerated. This selected target does not create a
  generator, structured metadata, or permanent card path before its separately
  approved implementation and atomic cutover.

## Blocked by

- [TASK-LIFECYCLE-01](TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md) — Required: the validator and indexes need the complete stable lifecycle roots before introducing non-status Markdown beneath `docs/tasks`.

## Completion unblocks

- None.

## Prerequisites

- Reinspect the `PROGRAM-01` taxonomy and every live card prefix at the
  selected revision; do not infer epic membership only from filename text.
- Measure current navigation and context-loading needs so the initial indexes
  stay concise and locally useful.

## Required context

- The completed `PROGRAM-01` epic/cohort/tranche model, the completed lifecycle
  implementation, [`docs/tasks/README.md`](../README.md), the extracted
  documentation validator and tests, and `PIPELINE_PLAN.md`.
- Inspect the current TODO-card scopes of `DOC-IA-01` and `DOC-README-03` only
  to avoid overlap. Their uncompleted outputs are not required context or
  blockers for this card.

## Questions owned by this card

- None. Taxonomy and membership rules come from `PROGRAM-01`; task-specific
  planning owns only their bounded implementation against the live registry.

## In scope

- Add the epic index, one concise README per approved epic, stable identifiers,
  member-card links, and local navigation from the task registry.
- Extend the extracted validator and independent fixtures for epic identity,
  README existence, membership references, duplicates, stale links, and the
  prohibition on task cards inside the epic tree.
- Repair directly affected links and update concise task-registry, roadmap,
  handoff, and documentation-navigation owners.

## Out of scope

- Moving cards into category subdirectories; changing lifecycle status,
  blocker semantics, roadmap order, card scope, planning cohorts, tranche
  membership, repository-wide README coverage, or implementation behavior.

## Deliverables

- A single canonical epic index and one bounded README for each approved epic.
- A minimal authored epic-definition source and stable-ID membership metadata.
  Each committed generated output names its generator, relevant input digest,
  and refresh/check command; regeneration occurs in temporary space and exact
  bytes are compared.
- Fail closed on stale or manually edited output, duplicate or unknown card or
  epic IDs, and any attempt to interpret epic membership as lifecycle,
  authorization, order, cohort, tranche, or dependency.
- Tested validator support that treats epic documents as non-card navigation
  and preserves lifecycle-directory status authority.
- Concise links that allow an agent to load one relevant epic boundary without
  reading the entire task registry.

## Acceptance evidence

- Every approved epic has exactly one canonical description and valid member
  links, with no duplicated mutable card state.
- No task card exists beneath the epic tree, and no epic membership is
  interpreted as status, authorization, order, or dependency.
- Navigation can locate cards by lifecycle state and by logical epic without
  physical category migration.
- Focused validator tests, the complete documentation gate, Git diff checks,
  and independent registry/navigation review pass.

## Canonical documentation updates

- `docs/tasks/epics/`, `docs/tasks/README.md`, the extracted validator and
  tests, `PIPELINE_PLAN.md`, `TODO.md`, `HANDOFF.md`, applicable task-local
  documentation navigation, and this card.

## Escalation conditions

- Stop if an epic needs to own mutable task state, cards require multiple
  conflicting physical homes, taxonomy changes an approved program decision,
  validator support requires moving cards, or the work expands into the
  repository-wide navigation audits owned by `DOC-IA-01` or `DOC-README-03`.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
