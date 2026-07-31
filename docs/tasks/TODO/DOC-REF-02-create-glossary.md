# DOC-REF-02 — Create glossary

## Objective

Create `docs/reference/GLOSSARY.md` as the canonical maintainer-facing source
for abbreviations, formats, tools, and project-specific terms.

## Why this exists

Terms such as STAR, GTF, BED12, CMH, BH, BAM, VCF, and evidence-state labels
appear throughout the corpus without one concise definition and contextual
meaning.

## Fixed decisions

- The canonical path is `docs/reference/GLOSSARY.md`.
- Entries expand the term, define it in NORAD context, and link to the owner of
  detailed semantics; they do not duplicate procedures.
- Source documents link selectively where a term is genuinely blocking, rather
  than linking every occurrence.

## Blocked by

- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: reference ownership and navigation placement must be settled.

## Completion unblocks

- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Partially: usability review also requires the architecture and reliability reviews.
- [DOC-SKILL-10](../TODO/DOC-SKILL-10-build-documentation-health-skill.md) — Partially: the skill also depends on other proven documentation practices.

## Prerequisites

- Derive candidate terms from the full tracked documentation and public
  interface corpus; verify definitions against authoritative implementation or
  primary scientific references where needed.

## Required context

- The documentation information architecture, current/future architecture,
  schemas, public help, reports, evidence-state vocabulary, and canonical
  scientific decisions.

## Questions owned by this card

- None.

## In scope

- Alphabetized entries, aliases, expansion, concise NORAD meaning, ambiguity
  warnings, and canonical cross-links.

## Out of scope

- Tutorials, command examples, encyclopedic biology, duplicating schema fields,
  or changing terminology in code.

## Deliverables

- The glossary, navigation links, and an update rule for future terms.

## Acceptance evidence

- Every unexplained abbreviation and project-specific evidence term has a
  concise verified entry or an explicit exclusion rationale.
- Link and terminology consistency checks pass.

## Canonical documentation updates

- New glossary, `README.md`, applicable canonical owners, `AGENTS.md` ownership
  table if needed, and this card.

## Escalation conditions

- Stop if a definition would resolve an open scientific policy, conflate a file
  format with an analysis, or contradict a public schema.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
