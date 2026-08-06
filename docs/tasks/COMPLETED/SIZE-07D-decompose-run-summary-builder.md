# SIZE-07D — Decompose run summary builder

## Objective

Split the oversized run-summary builder into cohesive input, projection,
validation, serialization, and publication owners while preserving the public
summary contract.

## Why this exists

The roughly 2,800-line builder combines artifact reading, policy projection,
cross-table reconciliation, output generation, and transaction handling. Its
central evidence role makes broad edits difficult to review.

## Fixed decisions

- Public JSON/TSV/QC bytes, ordering, hashes, missing/failed states, table
  approvals, and receipt/summary publication remain exact.
- Internal types never replace independent public-schema validation.
- Extract only cohesive seams and use bounded child cards if required.
- Keep reporting projection separate from canonical summary evidence.

## Blocked by

- [RPT-05A](../COMPLETED/RPT-05A-relocate-reporting-to-final-source-home.md) — Required: decompose the builder inside the final reporting owner rather than creating more temporary flat implementation.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- At task start, refresh only `src/norad/reporting/build_run_summary.py`:
  record its live line count, responsibilities, consumers/import graph,
  contract risks, and mandatory disposition. Do not run or require a
  repo-wide size inventory.
- Independently protect canonical JSON/TSV/QC/receipt bytes, status projection,
  input mutation, lock, rollback, and report consumers.

## Required context

- `RA-008`, `RA-010`, `RA-019`, artifact/run-summary schemas, adapters,
  `_run_summary_science.py`, approved tables, reports, and tests.

## Questions owned by this card

- None.

## In scope

- Reporting-local input adapters and internal models, science-policy projection
  boundary, serializers, publication, CLI orchestration, tests, and child-card
  split inside the final reporting owner.

## Out of scope

- Source relocation, public schema redesign, report field selection, evidence-
  state promotion, intake identity, or generic artifact frameworks.

## Deliverables

- Cohesive reporting-owner modules, narrower tests, an eliminated monolith, and
  stable internal consumer APIs; legacy-path cutover remains `RPT-05A` scope.

## Acceptance evidence

- The completion record captures the target-only starting and resulting size,
  responsibility/consumer map, extracted seams, and final size disposition.
- Exact-byte, schema, status, deterministic, mutation, fault, CLI, artifact, and
  report integration gates pass.
- No internal model can bypass public validation or evidence-state rules.

## Canonical documentation updates

- Current architecture, local READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop if decomposition changes canonical serialization, evidence policy, or
  requires simultaneous report/intake redesign.

## Completion record

Completed in the explicitly approved PI-readiness tranche. The target-only
refresh measured `src/norad/reporting/build_run_summary.py` at 2,793 lines and
98,275 bytes. It owned CLI/input admission, immutable transaction snapshots,
report-table approvals, run/status/science projection, canonical JSON/TSV/QC
and receipt validation, context preparation, predecessor reconciliation, and
receipt-last publication/rollback. Direct consumers are the Make/runbook CLI
route, reporting fixtures and direct tests, independent contract goldens, and
the HTML/export report integrations.

The exact public path is now a 954-line compatibility, preparation, CLI, and
publication facade over six reporting-private modules plus `__init__.py`.
Private seams own models/headers, inputs, approvals, transaction helpers,
projection, and validation; they range from 230 to 406 lines. The facade keeps
the live `_build_document` hook, shared adapter/contract/science identities,
input rechecks, canonical serialization, public-schema validation, locking,
signals, replacement, rollback/recovery, and receipt-last transaction. Every
changed file is below 1,000 lines and each new private module is below 600.

The unchanged `_run_summary_science.py` remains 1,312 lines and 48,135 bytes.
It is retained with explicit justification: it is one cohesive, read-only
committed Step `09c` package validation/normalization boundary, has no private
Step `09c` implementation dependency, is below the mandatory 1,500-line
threshold, and was not materially changed in this target-only slice. A future
architectural edit to that scientific-policy boundary requires its own bounded
decomposition plan.

Focused local evidence passed: 72 direct transaction/fault tests; the new live
header/serializer test; 84 independent-golden and HTML/export consumer tests;
two exact public-CLI arbitrary-CWD cases; compile/import identity checks; moved-
body AST parity; facade-binding review; and `git diff --check`. This is local
structural and contract-parity evidence only; public bytes, evidence policy,
and production, cluster, scientific-review, and biological evidence ceilings
remain unchanged.
