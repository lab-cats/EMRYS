# SIZE-07A — Decompose artifact index builder

## Objective

Eliminate the oversized artifact-index monolith through small, parity-proven
seams with explicit neutral ownership.

## Why this exists

The roughly 5,400-line builder combines registry data, native readers,
stage-specific semantics, evidence assembly, transaction control, and CLI
orchestration. It is the largest current source file and a high-coupling
change surface.

## Fixed decisions

- Decompose only along observed seams and under the approved vertical topology.
- Keep stage-specific rules explicit; do not create a generic semantic
  dispatcher or catch-all utility.
- Preserve exact JSON/TSV/receipt bytes, identity, no-clobber, rollback,
  recovery, direct CLI, and adapter roster contracts.
- Split implementation through bounded child cards if one approved task cannot
  remain locally understandable.

## Blocked by

- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Required: live size, responsibilities, consumers, and mandatory disposition must be refreshed.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent architecture/reliability/usability reviews must be incorporated.
- [RPT-05A](../IN_PROGRESS/RPT-05A-relocate-reporting-to-final-source-home.md) — Required: decompose the builder inside the final reporting owner rather than creating more temporary flat implementation.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- Complete exact adapter roster, CLI, deterministic-byte, mutation, lock,
  rollback, recovery, and stage-anchor characterization at the live predecessor.

## Required context

- `RA-005`, `RA-007` through `RA-010`, target topology, shared-library policy,
  artifact schemas/adapters, consumers, tests, and fault matrix.

## Questions owned by this card

- None.

## In scope

- Reporting-local models/registry, native readers, evidence assembly,
  publication, CLI seams, internal caller migration, and bounded child-card
  creation inside the final reporting owner.

## Out of scope

- Source relocation, changing stage semantics, public schemas/bytes, universal
  transaction abstraction, report redesign, or unrelated artifact pipeline
  features.

## Deliverables

- Cohesive reporting-owner modules, narrowed tests, and a removed monolith;
  relocation wrappers and legacy-path caller cutover remain `RPT-05A` scope.

## Acceptance evidence

- No resulting file violates the approved size policy without justification.
- Complete parity, determinism, transaction-fault, direct CLI, adapter, summary,
  and report-consumer gates pass.

## Canonical documentation updates

- Current architecture, local READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop if a seam changes identity/publication semantics, hides stage-specific
  rules, requires a broad framework, or exceeds one bounded review context.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
