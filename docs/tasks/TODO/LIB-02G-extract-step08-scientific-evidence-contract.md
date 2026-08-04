# LIB-02G — Extract the Step 08 scientific-evidence contract

## Objective

Extract the public Step `08` table/manifest contract into its permanent neutral
owner and cut over every repository-owned Python consumer without changing
accepted/rejected inputs, returned values, exceptions/messages, output bytes,
or scientific/runtime behavior.

## Why this exists

Step `08`/`09` validators and reporting-chain consumers currently obtain
public Step `08` structures through the private Step `09c` implementation.
Completed `LIB-02F` requires bottom-up neutral contracts so later reporting
relocation does not preserve that prohibited dependency direction.

## Fixed decisions

- Target `src/norad/contracts/scientific_evidence/step08.py` with mirrored
  direct tests at `tests/contracts/scientific_evidence/test_step08.py`.
- Extract only public Step `08` headers, closed vocabularies, manifest and
  artifact validation, and private subordinate parsing helpers required to
  implement that public contract.
- The bounded surface is the sample-manifest required/allowed columns,
  partition-manifest header, Step `08` metadata/inputs/summary headers, safe-ID
  checks, and sample-manifest, partition-manifest, Step `08` inputs/sites/
  summary validation.
- Preserve every accepted/rejected input, exception, message, ordering rule,
  deterministic byte, and consumer-visible identity through an exact-file,
  package-independent cutover.
- Preserve one shared module, error, and table identity across consumers; do
  not introduce a compatibility owner to manufacture identity.
- Keep Step `08` shell and R checks independent. Do not move or share its R
  algorithm, orientation/allele/filtering/annotation logic, runtime setup,
  publication, rollback, or recovery behavior.
- Do not extract Step `09` or public Step `09c` contracts in this card, and do
  not move reporting code or introduce packaging, installation metadata,
  `PYTHONPATH` mutation, or a permanent compatibility owner.

## Blocked by

- None.

## Completion unblocks

- [RPT-05A](../TODO/RPT-05A-relocate-reporting-to-final-source-home.md) — Partially: Step `09`, public Step `09c`, and reporting-local dependency-removal slices must still close before reporting relocation.

## Prerequisites

- Use completed [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md)
  as the semantic boundary and completed
  [MIG-04A](../COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
  as the neutral-contract ownership predecessor.
- Reverify the exact current Step `08` public symbols, all direct imports and
  calls, exception identity, path-independent behavior, tests, goldens, and
  measured coverage before extraction.

## Required context

- The `LIB-02F` promotion matrix; `SOURCE_TOPOLOGY.md`; direct-migration
  mechanics; the Step `08`, Step `09`, and Step `09c` Python validators;
  `build_artifact_index.py`; and only their direct Step `08` tests/fixtures.
  `_run_summary_science.py` uses review-package rather than Step `08` public
  symbols and remains outside this slice unless refreshed direct evidence
  proves otherwise.

## Questions owned by this card

- None.

## In scope

- One neutral Python contract owner and independent direct tests; remove the
  extracted Step `08` ownership from the Step `09c` implementation and cut over
  the Step `08` validator, Step `09` validator, artifact-index builder, and
  their direct Python tests. Include only path/import repairs, focused parity,
  coverage, legacy-dependency absence searches, and impact-directed
  documentation close.

## Out of scope

- Scientific-method or threshold changes; R or shell consolidation; Step `09`
  or Step `09c` extraction; artifact/schema redesign; reporting relocation;
  scheduler, ingestion, orchestration/profile, runtime, cluster, production,
  or biological-readiness work.

## Deliverables

- One final Step `08` neutral contract module and mirrored suite, with every
  reviewed direct consumer cut over and no duplicate or private Step `09c`
  ownership of the extracted public surface.

## Acceptance evidence

- Frozen pre/post API and consumer parity proves exact accepted/rejected
  inputs, outputs, exceptions/messages, ordering, bytes, and arbitrary-CWD
  behavior.
- The neutral module imports no functional owner; Step `08` shell/R checks and
  Step `09c` evidence policy/publication remain independent and unchanged.
- Direct and affected integration/golden suites, measured Python coverage,
  complete applicable local gate, documentation gate, and exact old-
  dependency/duplicate-owner searches pass at the final executable state.

## Canonical documentation updates

- Current architecture and functional-owner inventory, `SOURCE_TOPOLOGY.md`
  only if owner wording needs clarification, `PIPELINE_PLAN.md`, `HANDOFF.md`,
  mutable dependency links, coverage path if applicable, and this card.

## Escalation conditions

- Stop for any Step `09` or public review-package contract; review-plan or
  evidence-payload policy; `Artifact`, `ReviewContext`, or `build_context`;
  algorithm, threshold, table/schema, error-contract, transaction, publication,
  locking, rollback, recovery, reporting, shell/R, or scientific-policy
  change; an external consumer; packaging/path mutation/wrapper need; loss of
  exact shared identity; or a missing independent parity oracle.

## Completion record

Not started. This card is the next unselected JIT candidate after completed
MIG-04A; lifecycle selection begins read-only plan/review before implementation.
