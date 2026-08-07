# DOC-README-03 — Establish directory README coverage

## Objective

Give every eligible durable directory a concise `README.md` that explains its
purpose, contents, local contracts, and relationship to child directories.

## Why this exists

Many directories and opaque artifacts are inspectable only by reading code or
history. Local explanations reduce onboarding and token cost while keeping
detail near the files it governs.

## Fixed decisions

- Use the conventional name `README.md`.
- Parent READMEs mention child purpose but leave child detail to the child's
  README.
- Generated, cache, runtime, lock, and transient directories are eligible for
  explicit exclusion.
- TSV/JSON/schema/generated/lock/byte-sensitive files receive adjacent prose;
  do not insert comments into the data format.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: directory audiences and ownership rules must be settled.

## Completion unblocks

- [CONTEXT-09](../TODO/CONTEXT-09-define-local-maintainer-context.md) — Partially: target topology and documentation ownership are also required.
- [DOC-SKILL-10](../TODO/DOC-SKILL-10-build-documentation-health-skill.md) — Partially: the skill also depends on other proven documentation practices.

## Prerequisites

- Inventory all tracked and intentionally empty durable directories, including
  test fixtures and future target-directory templates.

## Required context

- `DOC-IA-01`, repository tree, directory consumers, schemas/contracts, fixture
  builders, ignore policy, and current README conventions.

## Questions owned by this card

- None.

## In scope

- Coverage matrix, README template variants, concise local files, adjacent
  opaque-fixture descriptions, and link/navigation updates.

## Out of scope

- Explaining child implementation in parent files, embedding comments in TSV
  fixtures, creating future source directories prematurely, or doc consolidation.

## Deliverables

- Reviewed README/exclusion matrix and bounded rollout cards if the work is too
  large for one approved package.

## Acceptance evidence

- Every eligible durable directory has one local README or an explicit,
  inspected exception.
- Parent/child detail is not duplicated and opaque files have adjacent context.

## Canonical documentation updates

- Directory READMEs, root/documentation maps, `DECISIONS.md` if an exception
  changes policy, and this card.

## Escalation conditions

- Stop if a README would become a second owner for mutable state or if a
  directory's lifecycle cannot be classified safely.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
