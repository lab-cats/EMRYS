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

- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Required: live size, responsibilities, consumers, and mandatory disposition must be refreshed.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent architecture/reliability/usability reviews must be incorporated.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- Independently protect canonical JSON/TSV/QC/receipt bytes, status projection,
  input mutation, lock, rollback, and report consumers.

## Required context

- `RA-008`, `RA-010`, `RA-019`, artifact/run-summary schemas, adapters,
  `_run_summary_science.py`, approved tables, reports, and tests.

## Questions owned by this card

- None.

## In scope

- Input adapters, neutral internal models, science-policy projection boundary,
  serializers, publication, CLI orchestration, tests, and child-card split.

## Out of scope

- Public schema redesign, report field selection, evidence-state promotion,
  intake identity, or generic artifact frameworks.

## Deliverables

- Cohesive modules, narrower tests, eliminated monolith, and stable consumer APIs.

## Acceptance evidence

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

Not started. Select this card for read-only planning; implementation requires
separate approval.
