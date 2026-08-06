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

- [RPT-05A](../COMPLETED/RPT-05A-relocate-reporting-to-final-source-home.md) — Required: decompose the builder inside the final reporting owner rather than creating more temporary flat implementation.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- At task start, refresh only `src/norad/reporting/build_artifact_index.py`:
  record its live line count, responsibilities, consumers/import graph,
  contract risks, and mandatory disposition. Do not run or require a
  repo-wide size inventory.
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

- The completion record captures the target-only starting and resulting size,
  responsibility/consumer map, extracted seams, and final size disposition.
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

Completed in the explicitly approved PI-readiness tranche. The target-only
refresh measured `src/norad/reporting/build_artifact_index.py` at 5,681 lines
and 201,647 bytes. It owned exact contract loading; models, constants, rosters,
and registry data; text and binary inspection; native, Step `09`, and review
reconciliation; record/index/receipt assembly and validation; stable-input
context checks; the public CLI; and receipt-last transaction control. Direct
consumers are `build_run_summary.py`, the reporting fixture and adapter suites,
the independent contract goldens, and public CLI contracts; report renderers
consume it transitively through the run summary.

The same public path is now a 766-line CLI and compatibility facade over 15
substantive reporting-private modules plus `__init__.py`. The extracted seams
own contracts, models, rosters, registry, core helpers, text/binary readers,
inspection, native/Step `09`/review reconciliation, cross-scope reconciliation,
records, context, and validation. The largest private module is 570 lines. The
facade remains above the 600-line advisory threshold because it coherently
retains the public loader and transaction/fault boundary, including write,
fsync, lock, signal, replace, remove, rollback, and recovery hooks; it is below
both mandatory decomposition thresholds.

Focused local evidence passed: 95 adapter, fault, native, and parity tests; 82
independent contract goldens; 72 run-summary tests; 22 exact-loader/private-
dependency cases; two exact public CLI cases; compile/import checks; and
`git diff --check`. Added live-owner mutation tests prove that header
serialization, source rechecks, and predecessor validation bind to the moved
owners. This is local structural and contract-parity evidence only; it adds no
cluster, production, scientific-review, or biological proof.
