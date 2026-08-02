# DOC-SKILL-10 — Build documentation health skill

## Objective

Create and forward-test a reusable Codex skill that audits NORAD documentation
health using the conventions proven by the cleanup program.

## Why this exists

Documentation ownership, links, local context, glossary coverage, headers, and
task-card integrity will drift without periodic review. A skill can make that
review repeatable after the underlying rules are stable.

## Fixed decisions

- Do not create `docs/skills/` or a standalone `DOC_CLEANUP.md` pseudo-skill.
- Build the future skill in a proper skill directory with `SKILL.md` using the
  supported skill-creation workflow.
- Default to read-only auditing; require explicit approval before mutations.
- Combine deterministic checks with semantic responsibility-drift review.
- Forward-test the skill against known good and intentionally broken fixtures.

## Blocked by

- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: usability expectations must be independently reviewed.
- [DOC-REF-02](../TODO/DOC-REF-02-create-glossary.md) — Required: glossary practice must be implemented.
- [DOC-README-03](../TODO/DOC-README-03-establish-directory-readme-coverage.md) — Required: directory README practice must be implemented.
- [CODEDOC-05](../TODO/CODEDOC-05-inventory-code-documentation.md) — Required: code-header/comment classification must be defined.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: the final audit also requires report, logging, size, and generated in-scope tasks.

## Prerequisites

- At least one concrete `DOC-CONS-08-*` consolidation package and one
  `CODEDOC-06-*` rollout card are complete, so the skill encodes proven
  practice rather than speculation.
- The commits that create those concrete cards must add them as direct blockers
  here, with reciprocal unblock links, before this card may enter planning.
- Use the `skill-creator` instructions when this card is selected.
- When corrected `DOC-REF-02` completes canonically, relink its glossary input
  to the accepted lifecycle location while retaining every independent
  blocker. Consume its revision-bounded audit method, category precision,
  selective-link rule, receipt/evidence cautions, and semantic review as proven
  practice; do not encode a permanent term-candidate ledger or infer that the
  glossary alone makes this card selectable.

## Required context

- Documentation ownership/navigation map, glossary, README matrix, code-doc
  inventory, task registry/gate, completed consolidation ledgers, and current
  Codex skill conventions.

## Questions owned by this card

- [`CHOICE-SKILL-01`](../../design/QUESTIONS.md#choice-skill-01--documentation-health-skill-name-and-discovery-location).

## In scope

- Link/anchor, README, glossary, module-header, orphan, task-link/status,
  canonical-owner, diagram, and semantic responsibility-drift checks;
  read-only report format; approval boundary; forward tests.

## Out of scope

- Automatic edits by default, repository-wide code refactoring, replacing the
  documentation gate, or evaluating unrelated skill ideas.

## Deliverables

- Proper skill package, deterministic helpers where justified, clear audit
  output, approval-safe repair workflow, and forward-test evidence.

## Acceptance evidence

- The skill passes a clean repository, detects seeded broken links/anchors,
  stale task references, missing README/glossary/header coverage, and owner
  drift, and performs no mutation without approval.

## Canonical documentation updates

- Task registry, `AGENTS.md` only if task-start use is approved, `RUNBOOK.md`
  for exact invocation, skill documentation, `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if the practice is still unstable, the platform requires a different
  skill structure, or a proposed automated fix could overwrite canonical truth.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
