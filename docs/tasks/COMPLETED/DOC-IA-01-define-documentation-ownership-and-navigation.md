# DOC-IA-01 — Define documentation ownership and navigation

## Objective

Create an audience-aware documentation map, responsibility ledger, and
lossless consolidation plan with bounded follow-up cards.

## Why this exists

The documentation corpus has grown through responsibility leak: large owners
are hard to navigate, some facts overlap, and opaque directories/files lack
local context. Cleanup without a ledger risks deleting unique operational or
scientific meaning.

## Fixed decisions

- Preserve one canonical owner per mutable fact and link from secondary views.
- Compress aggressively around strict single-purpose owners rather than retain
  broad documents for convenience.
- Relocate unique information before deleting its old copy. Move the
  information, repair references, and remove the prior copy; never copy it into
  a second owner.
- Touch-driven migration eliminates a duplicate owner directly implicated by
  the active work instead of preserving both copies.
- Use `README.md` for eligible durable directories; parent READMEs stay shallow
  and child READMEs own detail.
- The top-level sitemap routes to documentation categories; future child maps
  may route within one category. Parent maps reference child maps without
  duplicating their entries or contents.
- A directory `README.md` explains local purpose and links to contracts; it
  does not restate those contracts.
- Architecture documentation stays conceptual and links to contract
  inventories or canonical contracts rather than reproducing their entries.
- Consolidation requires a source-to-destination ledger and no-loss review;
  intentional safety repetition remains at action points.
- The repository-root `AGENTS.md` remains a concise automatically loaded
  project router: it keeps only always-needed approval, safety, evidence, and
  task-routing guardrails plus links to canonical owners.
- Reusable cross-repository working preferences belong in global agent
  guidance, while detailed NORAD commands, topology, scientific policy,
  conventions, and mutable state remain in repository documents rather than
  being copied into `AGENTS.md`.
- Do not create `docs/skills/`; reusable skills belong in the actual skill
  system after the practice is proven.

## Blocked by

- [TEST-01Z](../COMPLETED/TEST-01Z-decide-behavior-contract-sufficiency.md) — Required: the latest behavior-sufficiency decision is affirmative.

## Completion unblocks

- [DOC-CONS-08A](DOC-CONS-08A-slim-root-agent-router.md) — Fully: every root rule has a settled destination and reachability boundary.
- [DOC-CONS-08B](DOC-CONS-08B-compress-root-entry-and-priority-views.md) — Fully: root audiences and retained facts have settled owners.
- [DOC-CONS-08C](../IN_PROGRESS/DOC-CONS-08C-compress-operational-guidance.md) — Fully: runbook/troubleshooting boundaries and no-loss constraints are settled.
- [DOC-CONS-08D](../TODO/DOC-CONS-08D-establish-dated-documentation-history.md) — Fully: the history location and migration rules are settled.
- [DOC-CONS-08F](../TODO/DOC-CONS-08F-compress-design-and-architecture-views.md) — Fully: conceptual and exact contract-owner boundaries are settled.
- [DOC-CONS-08H](../TODO/DOC-CONS-08H-retire-jit-temporary-work-record.md) — Fully: the temporary-record disposition is settled, subject to its live prerequisites.
- [DOC-REF-02](../TODO/DOC-REF-02-create-glossary.md) — Fully: glossary ownership and navigation will be settled.
- [DOC-README-03](../TODO/DOC-README-03-establish-directory-readme-coverage.md) — Fully: directory-audience and detail rules will be settled.
- [DOC-PIPE-04](../TODO/DOC-PIPE-04-create-user-pipeline-overview.md) — Partially: the semantic stage map is also required.
- [CODEDOC-05](../TODO/CODEDOC-05-inventory-code-documentation.md) — Partially: an affirmative behavior gate is also required.
- [CONTEXT-09](../TODO/CONTEXT-09-define-local-maintainer-context.md) — Partially: target topology and README coverage are also required.
- [PLAN-02Z](../TODO/PLAN-02Z-integrate-future-task-sequence.md) — Partially: documentation sequencing is one integrated-plan input.

## Prerequisites

- Inventory every tracked Markdown/Mermaid owner, audience, inbound/outbound
  link, duplicated topic, and unique operational/scientific fact.

## Required context

- All canonical documents, demos, architecture diagrams, historical snapshots,
  repository directories, existing documentation gate, and `RA-012` through
  `RA-015`.

## Questions owned by this card

- `CHOICE-DOC-01` — Resolved in the
  [documentation decision](../../design/DECISIONS.md#treat-documentation-and-maintainer-context-as-architecture)
  and indexed under [resolved questions](../../design/QUESTIONS.md#resolved-index).

## In scope

- Audience/navigation map, responsibility matrix, source-to-destination ledger,
  orphan/stale classification, RUNBOOK/TROUBLESHOOTING boundary, historical
  evidence treatment, a rule-by-rule `AGENTS.md` disposition, and creation of
  concrete `DOC-CONS-08-*` cards including a bounded `AGENTS.md` slim-down.

## Out of scope

- Performing the full consolidation, deleting unique content, editing behavior
  claims before implementation, or building the documentation skill.

## Deliverables

- A no-loss documentation information architecture and exact bounded cleanup
  cards with dependencies and acceptance evidence.
- An `AGENTS.md` source-to-destination ledger classifying every current rule as
  retained always-on guidance, moved repository detail, global reusable
  preference, intentional duplication, or separately justified removal.

## Acceptance evidence

- Every current document and unique fact has one retained owner/destination or
  an explicitly approved historical disposition.
- Every touched migration relocates unique information before removal and
  leaves no duplicate owner behind.
- Sitemap, directory-README, and architecture views route to authoritative
  detail without restating it.
- Every current `AGENTS.md` rule has a reviewed disposition, all critical
  approval, safety, scientific-evidence, and destructive-action guards remain
  automatically reachable, and a concrete slim-down card has been created.
- The proposed root file is materially shorter and functions as a router; line
  count is diagnostic rather than a substitute for the no-loss review.
- A user, operator, scientist, and maintainer each have a short navigable path.

## Canonical documentation updates

- `AGENTS.md`, `README.md`, `DECISIONS.md`, `PIPELINE_PLAN.md`,
  `QUESTIONS.md`, task registry, and this card.

## Escalation conditions

- Stop if two owners contain different live truth, a deletion lacks a mapped
  destination, or safety repetition is mistaken for accidental duplication.

## Completion record

Completed 2026-08-02 as an explicitly approved local-only documentation
package. The canonical
[`documentation ownership and consolidation map`](../../sitemap/DOCUMENTATION_OWNERSHIP.md)
records audience routes, responsibility boundaries, all 114 Markdown and six
Mermaid dispositions, semantic inbound/outbound link roles, the no-loss move
ledger, and every current `AGENTS.md` rule class. `CHOICE-DOC-01` is resolved
in `DECISIONS.md`, and concrete `DOC-CONS-08A` through `DOC-CONS-08H` cards
bound later work without selecting it or duplicating existing sitemap, README,
validator, overview, code-documentation, or task-index scopes.

Independent read-only operations, design, navigation, structure, and no-loss
reviews found no remaining permitted corpus-category omission; their boundary
corrections are incorporated. The final link/anchor/card/dependency/cycle/
orphan/Mermaid documentation gate passes against the combined tree.
Computational validation is not applicable because the package changes only
Markdown documentation and no executable, configuration, generation, schema,
fixture, report-template, dependency, or test-harness behavior.
