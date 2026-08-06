# SIZE-07 — Retire standalone large-file inventory refresh

## Objective

Remove the repo-wide inventory refresh as a standalone prerequisite and make
each mandatory size slice refresh only its own target before decomposition.

## Why this exists

A full-source inventory before every size package duplicated context and made a
bounded refactor depend on unrelated files. Size still matters, but its useful
evidence is the live target's responsibilities, consumers, contract risk, and
disposition at the moment that target changes.

## Fixed decisions

- More than 600 lines triggers advisory cohesion review when materially
  changed; new files normally stay below 600.
- More than 1,000 lines requires a decomposition plan or explicit justification
  before architectural modification.
- More than 1,500 lines must be eliminated during the active repo-spanning
  refactor unless an explicit exception is approved.
- Split tests by scenario/comprehension rather than arbitrary length.
- `SIZE-07A`, `SIZE-07B`, `SIZE-07D`, `SIZE-07E`, and `SIZE-07F` each own a
  target-only live refresh in their implementation package. No repo-wide
  refresh is a prerequisite to those slices.

## Blocked by

- None.

## Completion unblocks

- None. The five target cards retain their other explicit prerequisites and
  blockers.

## Prerequisites

- None.

## Required context

- The five active `SIZE-07X` cards and the source-size decision in
  `DECISIONS.md`.

## Questions owned by this card

- None.

## In scope

- Retiring the standalone refresh and routing the target-only evidence
  obligation into each existing mandatory size slice.

## Out of scope

- Splitting files, changing behavior, running a new repo-wide inventory,
  changing thresholds, or resolving any target card's other blockers.

## Deliverables

- One completed retirement record and target-specific refresh requirements in
  `SIZE-07A`, `SIZE-07B`, `SIZE-07D`, `SIZE-07E`, and `SIZE-07F`.

## Acceptance evidence

- No active size card depends on this card.
- Each active size card requires its own live path, line count,
  responsibility/consumer map, contract-risk review, and final disposition.

## Canonical documentation updates

- The affected size cards, dependency references, documentation ownership map,
  and the final tranche roadmap reconciliation.

## Escalation conditions

- Stop if distributing the refresh would change a size target, contract,
  scientific boundary, or implementation scope.

## Completion record

Retired by the approved cleanup queue. No repo-wide source inventory was
performed or claimed. The five existing target cards now own narrowly scoped
live refreshes inside their respective packages, and this completed record is
not an implementation prerequisite.
