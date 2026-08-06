# SIZE-07B — Decompose scientific validation tooling

## Objective

Eliminate the oversized Step `09c` tooling monolith without changing scientific
state policy or validation meaning.

## Why this exists

The roughly 4,500-line module owns shared parsing/hash/table utilities,
Step `08`/`09` contract checks, scientific evidence state, and transaction
publication. Its broad reuse reverses dependency direction and raises change
risk.

## Fixed decisions

- Scientific/statistical algorithms and readiness policy remain unchanged
  absent separate scientific authorization.
- Extract only proven-neutral contracts, parsing, serialization, or publication
  seams; retain independent validation even when logic looks similar.
- Preserve exact state vocabulary, schemas, bytes, errors, evidence boundaries,
  and unauthorized-ready-state rejection.
- Use bounded child cards if more than one concern is required.

## Blocked by

- None.

## Completion unblocks

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Partially: other mandatory families and generated tasks must also close.

## Prerequisites

- At task start, refresh only
  `src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.py`:
  record its live line count, responsibilities, consumers/import graph,
  scientific/contract risks, and mandatory disposition. Do not run or require
  a repo-wide size inventory.
- Map every imported symbol and independently protect Step `08`/`09` headers,
  tables, status transitions, hashes, and failure/publication behavior.

## Required context

- `RA-007`, `RA-008`, `RA-010`, `RA-024`, `RA-025`, scientific decisions,
  schemas, Step `08`/`09` validators/tests, and target contract/library owners.

## Questions owned by this card

- None.

## In scope

- Neutral model/parser/serializer/publication extraction, scientific-domain
  module cohesion, import-direction correction, compatibility tests, and child
  cards for separate seams.

## Out of scope

- Changing CMH/BH/threshold/orientation algorithms, unlocking biological
  readiness, collapsing independent validators, or redesigning evidence policy.

## Deliverables

- Cohesive neutral and scientific modules, corrected dependency direction, and
  removal/justification of the monolith.

## Acceptance evidence

- The completion record captures the target-only starting and resulting size,
  responsibility/consumer map, extracted seams, and final size disposition.
- Exact public and scientific contract parity passes, including unauthorized
  state, corruption, deterministic, transaction, and independent R/Python/shell
  layers.
- No extracted neutral module imports a stage or owns scientific policy.

## Canonical documentation updates

- Current architecture, local READMEs, `REFACTOR_AUDIT.md` disposition,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, task registry, and this card.

## Escalation conditions

- Stop if a seam cannot be proven scientifically neutral, changes evidence
  language/state, or requires production/cluster data not authorized here.

## Completion record

Completed in the explicitly approved PI-readiness tranche. The target-only
refresh measured
`src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.py`
at 2,886 lines and 108,319 bytes. It owned exact Step `08`, Step `09`, and
review-package loading; Step `09c` constants and models; plan and evidence-
manifest intake; scientific audits and review analyses; computational evidence
and state assembly; explicit context construction; the public CLI; and the
thirteen-output receipt-last publication transaction. Direct consumers are the
adjacent shell launcher and fixture/test suite, run-summary fixture generation,
independent contract goldens, and public CLI contracts.

The exact public path is now a 568-line compatibility, CLI, and publication
facade over six owner-private modules plus `__init__.py`. The private seams own
contract identities/constants, intake/models, scientific audits, review
analysis, computational evidence/summary assembly, and context construction;
the largest is 570 lines. The facade retains live exact-loader wrappers,
`read_tsv`, `write_tsv`, stable-input rechecks, locking, staging, rollback,
recovery, `os.replace`, and summary-last publication hooks. Exact-file callers
and arbitrary-CWD execution require no `sys.path` mutation. Every resulting
file is below the 600-line advisory threshold.

Focused local evidence passed: 86 direct Step `09c` Python tests; 185 neutral
Step `08`/Step `09`/review-package and independent-golden tests; the adjacent
shell contract; two exact public CLI cases; six downstream run-summary science
checks; compile/import and exact-file loading checks; moved-body AST parity;
and `git diff --check`. Added live-owner tests prove context reaches the moved
evidence validator and all thirteen staged outputs reach the facade-live
writer. This is local structural and contract-parity evidence only; scientific
policy, state vocabulary, schemas, output bytes, and the production/cluster/
review/biological evidence ceilings remain unchanged.
