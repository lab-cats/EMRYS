# PLAN-02Z — Integrate the next migration tranche

## Objective

Select and bound only the next evidence-supported physical source migration,
including the review gates that must close before its execution begins.

## Why this exists

The earlier card assumed that every design family had to finish before any
migration could be named. The approved rolling-wave decision instead requires
the minimum shared architecture plus one reversible delivery unit. Live import
inspection shows that moving a functional stage first would preserve a
stage-to-stage dependency: twelve validators currently import the shared
validation-report protocol from the Step `00a` validator.

## Fixed decisions

- This card creates and reviews one tranche; it does not pre-author the rest of
  Phase `03` or execute any migration.
- The first unit is the separately owned validation-evidence publication
  protocol already identified in the functional-owner inventory. Stage-local
  validation checks and heterogeneous publication transactions remain local.
- Incomplete intake, reporting, logging, documentation, size, and broad
  shared-library work is future context, not a technological blocker for this
  unit.
- Tranche-specific architecture, reliability, and usability reviews remain
  separate read-only cards. The broad `REVIEW-*` cards remain frozen and do not
  gate or receive completion credit from this tranche.
- Every executable card still requires a clean, pushed, upstream-equal
  documentation-patched predecessor and its own live task-start inspection.

## Blocked by

- None.

## Completion unblocks

- [REVIEW-ARCH-03A](REVIEW-ARCH-03A-review-validation-publication-migration.md) — Fully: the bounded migration candidate and its exact ownership proposal are available for architecture review.
- [REVIEW-ARCH-01](../TODO/REVIEW-ARCH-01-review-architecture-plan.md) — Partially: this rolling checkpoint supplies one reviewed tranche, not the future cross-program review corpus.

## Prerequisites

- Freeze the clean, upstream-equal canonical result of the sidecar integration
  and verify that no later canonical commit supersedes it.
- Reproduce the integration's known documentation-validation ceiling before
  attributing any new finding to this card.

## Required context

- `REFACTOR_AUDIT.md` findings `RA-002`, `RA-007`, `RA-009`, `RA-019`,
  `RA-022`, and `RA-024`; `TEST_BASELINE.md`; the functional-owner inventory;
  target source topology; and direct migration mechanics.
- `validate_step_00a_star_index.py`, every direct validator importer, the
  validation-publication fault suite, check-roster tests, public CLI tests, and
  the tracked Python coverage policy.

## Questions owned by this card

- None.

## In scope

- Prove the smallest dependency-correct first migration unit and reject any
  stage move that would retain a prohibited implementation dependency.
- Create `MIG-03A` plus tranche-specific architecture, reliability, and
  usability review cards with reciprocal technological dependencies.
- Record exact source/test homes, consumer and symbol rosters, preserved
  contracts, characterized defects, import strategy, reversible checkpoints,
  validation obligations, documentation impact, and stop conditions.
- Update only the current priority, roadmap, handoff, durable shared-library
  rationale, registry links, and the dated risk/decision log required for this
  tranche.

## Out of scope

- Source, executable, schema, fixture, test-harness, dependency, packaging,
  scheduler, report, cluster, scientific-policy, or evidence-state mutation.
- Planning later stage migrations, correcting shared-publication defects,
  extracting BAM/scientific helpers, completing `LIB-02F`, or activating any
  recovered TODO or UNREFINED proposal.
- Implementing the future tranche registry, lifecycle state, generated view,
  or current-pointer design.

## Deliverables

- [MIG-03A](../TODO/MIG-03A-extract-validation-report-library.md), a single
  neutral-concern migration card.
- [REVIEW-ARCH-03A](REVIEW-ARCH-03A-review-validation-publication-migration.md),
  [REVIEW-REL-03A](../TODO/REVIEW-REL-03A-review-validation-publication-migration.md),
  and
  [REVIEW-UX-03A](../TODO/REVIEW-UX-03A-review-validation-publication-migration.md)
  as the narrow pre-execution review chain.
- A reconciled roadmap and handoff that keep all other work frozen and identify
  the exact pre-migration stop.

## Acceptance evidence

- The live import graph, current owner inventory, and independent fault tests
  support the selected neutral concern; no uninspected stage or application
  owner is pulled into the unit.
- The generated card satisfies every applicable migration-mechanics field and
  preserves each named public interface and characterized defect.
- Dependencies are acyclic and reciprocal, and completing this tranche's
  reviews does not unblock unrelated reporting, logging, size, or documentation
  implementation cards.
- Git whitespace validation passes and documentation validation adds no finding
  beyond the inherited nine unsupported-`UNREFINED` locations.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, `TODO.md`, `HANDOFF.md`, `DECISIONS.md`, task-registry
  links, documentation ownership, and the dated pre-migration audit log.

## Escalation conditions

- Stop if the selected unit requires a stage-to-stage import, a catch-all
  library, implicit dependency installation, a public CLI change, correction
  of a characterized defect, or an executable choice that cannot be bounded by
  current tests and contracts.

## Completion record

Completed as a documentation-only rolling checkpoint rooted at integrated
canonical parent `15aba53c538cabf2b7d2284575be0089b0ca90cf`; the immutable
planning proposal is checkpoint `c45e748`. Live inspection found exactly twelve
validator importers and the nine shared symbols recorded in `MIG-03A`, with all
affected current files at mode `0644`. The card created one migration and three
dedicated review cards, removed seven obsolete waterfall blockers, and left
unrelated work frozen. `git diff --check` passed, and documentation validation
reported only the inherited nine unsupported-`UNREFINED` locations. No
executable file changed, no computational test ran, and no physical migration
or evidence promotion began.
