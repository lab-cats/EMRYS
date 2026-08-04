# LIB-02F — Define shared-library ownership

## Objective

Turn the approved promotion rule into an implementation-backed map of local,
shared, and intentionally independent code ownership.

## Why this exists

Repeated parsing, publication, and validation vocabulary suggests extraction,
but similar-looking safety state machines and scientific checks often differ.
Premature DRY abstractions could create repository-wide coupling or common-mode
test defects.

## Fixed decisions

- Keep the first use local. At the second use, compare full semantics; extract
  at two only if safety-critical or complex, otherwise normally at the third.
- Place an abstraction in the narrowest neutral owner; shared code never
  depends on stages.
- Require independent API and consumer tests; do not force cross-language DRY.
- Preserve intentionally independent validation and transaction logic.
- Decide the two observed direction leaks first: reporting and the Step `08`/
  `09` validators exact-load Step `09c` implementation, while the Step `00c`
  and Step `05` validators exact-load the public reference-provenance command.
  Similar nearby code remains outside the first JIT decision.
- Neither peer exact-file dependency is an allowed final retention outcome.
  Approve a neutral seam or an independently tested owner-local dependency
  removal; otherwise keep the affected migration explicitly blocked.

## Blocked by

- [ARCH-02A](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md) — Required: observed reuse and ownership must be inventoried.
- [ARCH-02C](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: the neutral ownership domains and dependency direction must be settled.

## Completion unblocks

- [RPT-05A](../TODO/RPT-05A-relocate-reporting-to-final-source-home.md) — Partially: this card settles the reporting/Step `09c` ownership decision, but any concrete extraction and artifact-contract relocation must also complete before reporting moves.

## Prerequisites

- Build semantic comparisons for candidate repeated code, including failure,
  recovery, determinism, and scientific meaning.

## Required context

- `REFACTOR_AUDIT.md` findings `RA-007`, `RA-009`, `RA-020`, `RA-022`, and
  `RA-024`, the functional inventory, import graph, tests, target topology, and
  completed `PLAN-03A` residual disposition.
- `scripts/build_artifact_index.py`, `scripts/_run_summary_science.py`, the Step
  `08`/`09` validators, and the Step `09c` evidence implementation and direct
  tests; `scripts/reference_provenance.py`, the Step `00c`/`05` validators, and
  their direct and neutral-library tests.

## Questions owned by this card

- None.

## In scope

- Candidate ownership matrix, promotion/retention rationale, allowed APIs,
  dependency constraints, and test obligations.
- Full-semantic comparison of the Step `09c` contract/policy consumers and the
  reference parsing/provenance consumers, including failure, bytes,
  independence, and characterized-defect boundaries.

## Out of scope

- Extracting libraries, creating `utils`, universal transaction frameworks,
  generic dispatchers, or sharing the rule an independent test verifies.

## Deliverables

- A reviewed shared-library promotion matrix for both observed seams and only
  the first dependency-valid neutral-extraction or owner-local dependency-
  removal card justified by that matrix. If neither is safe, record the
  affected migration as blocked. Later cards remain JIT rather than pre-
  authored.

## Acceptance evidence

- Every proposed shared seam demonstrates equivalent semantics and a narrower
  owner; every retained duplicate states the independence or locality value.
- No proposed shared library imports a stage or erases language boundaries.
- The first generated card has one neutral concern, exact consumers/tests, and
  a stop condition; no reporting, provenance, scheduler, ingestion, or
  orchestration implementation is selected or moved by this decision card.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, `DECISIONS.md` if the policy changes,
  `PIPELINE_PLAN.md`, and this card.

## Escalation conditions

- Stop if equivalence depends on names rather than behavior, extraction would
  weaken recovery/science boundaries, or consumers would need a catch-all API.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
