# SIZE-07F — Decompose artifact contract validator

## Objective

Split the oversized artifact-contract validator into cohesive schema,
cross-artifact, evidence-state, and CLI/reporting checks without weakening
independent validation.

## Why this exists

The roughly 1,900-line validator combines many contract families and public
failure modes. Its size hinders local review, yet careless sharing with
producers would create common-mode defects.

## Fixed decisions

- Independent public-schema and cross-artifact validation remains mandatory.
- Preserve exact schema bytes/identities, semantic validation, contracted
  messages, inventory reconciliation, and CLI stdout/stderr/exit behavior.
- The validator remains read-only; it owns no report publication transaction
  or check-ID/status roster.
- Do not import producer rules into the validator solely to reduce duplication.
- Use bounded child cards if multiple contract families require separate work.

## Blocked by

- None.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- At task start, refresh only
  `src/norad/contracts/artifacts/validate_artifact_contracts.py`: record its
  live line count, responsibilities, consumers/CLI routes, independent-check
  risks, and mandatory disposition. Do not run or require a repo-wide size
  inventory.
- Completed
  [MIG-04A](../COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
  places the validator, schemas, direct test, and fixtures in their permanent
  neutral owner.
- Complete independent roster/golden/CLI characterization and refresh the
  validator's schema/status/consumer matrix.
- Verify that the validator and its five public schemas occupy the final
  neutral-contract homes fixed by `SOURCE_TOPOLOGY.md`. If they do not, leave
  this card unselected and create the one-owner relocation card just in time.

## Required context

- `RA-008`, `RA-017`, `RA-019`, public schemas, artifact fixtures, semantic
  validators, exact-file consumers, CLI exit behavior, and consumer tests.

## Questions owned by this card

- None.

## In scope

- Cohesive check modules, neutral result/report types where justified, CLI
  orchestration, independent tests, and child-card split.

## Out of scope

- Source relocation, changing schemas/evidence states, sharing producer rules,
  normalizing all validator exits, or building a generic validator framework.

## Deliverables

- Cohesive validator modules, narrower independent tests, and eliminated
  oversized owner.

## Acceptance evidence

- The completion record captures the target-only starting and resulting size,
  responsibility/consumer map, extracted seams, and final size disposition.
- Exact schema hashes/identities, semantic and inventory behavior, malformed-
  input handling, exact-loader identities, and CLI output/exit tests pass.
- Mutating a producer constant still fails the independent validator/golden.

## Canonical documentation updates

- Current architecture, local READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop if decomposition would reduce independent verification, change a public
  check/report contract, or require universal validator infrastructure.

## Completion record

Completed in the explicitly approved PI-readiness tranche. The target-only
refresh measured
`src/norad/contracts/artifacts/validate_artifact_contracts.py` at 1,895 lines
and 72,138 bytes. It owned five schema locations and strict JSON/schema
loading; path, run-contract, attempt/evidence, artifact, scientific-review, and
run-summary semantics; report-receipt semantics; explicit inventory validation
and reconciliation; exact-file consumer identity; and the read-only CLI.
Direct consumers are artifact indexing, run-summary science normalization,
Python and shell report rendering, direct contract/golden suites, and the
public CLI roster.

The exact public path is now a 573-line schema/document, semantic-dispatch,
inventory-reconciliation, compatibility, and CLI facade over four owner-
private modules plus `__init__.py`. Private seams own core schema/path/evidence
primitives, artifact semantics, scientific-review semantics, and run-summary
semantics; they range from 131 to 559 lines. The exact owner-relative loader is
arbitrary-identity/CWD safe, leaves `sys.path` unchanged, rejects unsafe caches,
cleans failed owned loads, validates child paths, and preserves one shared
`ContractValidationError`. Every implementation file is below 600 lines.

All 38 predecessor function/class bodies remain AST-equivalent exactly once
and every predecessor facade binding remains available. The five public schema
files, paths, `$id`/`$ref` values, and hashes are unchanged. Focused local
evidence passed: 64 direct contract cases (including six new loader/live-hook
checks), 82 independent contract goldens, two targeted arbitrary-CWD public
CLI cases, exact consumer-identity checks, compilation, schema-hash/path
verification, and `git diff --check`. The original card's references to a
check-ID/status roster and report publication were stale and were corrected;
this validator remains read-only. No producer, runtime, cluster, scientific-
review, or biological evidence was added.
