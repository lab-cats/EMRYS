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
- The Step `08`/`09` and public Step `09c` table contracts move bottom-up into
  the neutral `scientific_evidence` contract owner. Stage/analysis Python
  validators may consume that executable public contract, while their shell
  and R checks remain independent. Step `09c` review policy, evidence-source
  validation, locks, rollback, publication, and recovery remain evidence-
  owner implementation.
- Reporting does not reuse or relocate Step `09c` `build_context`,
  `ReviewContext`, or publication state. It receives a reporting-local reader
  and projection over the committed public thirteen-file review package and
  indexed artifact records, with its own source-stability checks.
- FASTA/FAI/DICT parsing moves to the narrow neutral
  `reference_contigs` library. Only the parser exception and three ordered
  contig parsers are shared; each consumer retains its own aggregation,
  evidence rows, CLI, publication, and recovery behavior.

## Blocked by

- [ARCH-02A](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md) — Required: observed reuse and ownership must be inventoried.
- [ARCH-02C](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Required: the neutral ownership domains and dependency direction must be settled.

## Completion unblocks

- [RPT-05A](../COMPLETED/RPT-05A-relocate-reporting-to-final-source-home.md) — Partially: this card settles the reporting/Step `09c` ownership decision, but any concrete extraction and artifact-contract relocation must also complete before reporting moves.

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

- A reviewed shared-library promotion matrix for both observed seams and
  child-ready boundaries for their later one-concern JIT cards.
- Exactly one first campaign successor:
  [`MIG-04A`](../COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md),
  the already-bounded neutral artifact-contract migration required before
  reporting relocation. Seam-extraction children remain uncreated until their
  JIT turn.

## Acceptance evidence

- Every proposed shared seam demonstrates equivalent semantics and a narrower
  owner; every retained duplicate states the independence or locality value.
- No proposed shared library imports a stage or erases language boundaries.
- The first campaign successor has one neutral concern, exact consumers/tests,
  and a stop condition; no reporting, provenance, scheduler, ingestion, or
  orchestration implementation is selected or moved by this decision card.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, `FUNCTIONAL_OWNER_INVENTORY.md`,
  `SOURCE_TOPOLOGY.md`, `DECISIONS.md`, `PIPELINE_PLAN.md`, `TODO.md`,
  `HANDOFF.md`, documentation ownership and lifecycle links, mutable
  `RPT-05A`/`SIZE-07F` dependency edges, the new `MIG-04A` card, and this card.

## Escalation conditions

- Stop if equivalence depends on names rather than behavior, extraction would
  weaken recovery/science boundaries, or consumers would need a catch-all API.

## Completion record

Completed as a documentation-only/non-consuming decision package from
published `PLAN-03A` parent
`3efe461ee7111291852417ad5e4165977937de4c`. Direct import and call-graph
inspection established these dispositions:

| Observed direction leak | Disposition | Preserved independence and future boundary |
| --- | --- | --- |
| Step `08`/`09` validators, artifact indexing, and run-summary science exact-load Step `09c` implementation | Mixed neutral extraction plus owner-local removal | Extract public Step `08`, Step `09`, and Step `09c` artifact/table contracts bottom-up under `src/norad/contracts/scientific_evidence/`. Keep Step `09c` evidence policy/publication local; keep artifact-index reconciliation independent; replace reporting's private `build_context` reuse with a reporting-local committed-package reader/projection. |
| Step `00c` and Step `05` validators exact-load the reference-provenance command | Neutral library extraction | Move `ProvenanceError`-equivalent parser failure and `parse_fasta`, `parse_fai`, and `parse_dict` semantics to `src/norad/libraries/reference_contigs.py`. Preserve each consumer's distinct per-role versus short-circuit aggregation and all CLI/evidence/publication behavior. |

The neutral scientific-contract package may contain only public headers,
closed vocabularies, manifest and Step `08`/`09` artifact validation, public
review-package roster/state reduction, and their private subordinate parsing
helpers. It may not import an application owner or absorb review-plan/evidence-
payload policy, `Artifact`, `ReviewContext`, `build_context`, stable-input
publication rechecks, locks, rollback, or recovery. The reference library
preserves exact ordered outputs, parser messages, encoding behavior, and raw
read exceptions without adding repair, snapshots, symlink policy, or contig
agreement decisions.

No executable, test, schema, fixture, configuration, report, dependency, or
scientific behavior changed. Semantic no-loss review, `git diff --check`, and
the documentation gate passed; computational and cluster validation were not
applicable. Only `MIG-04A` was created, in `TODO`, and no successor was
selected.
