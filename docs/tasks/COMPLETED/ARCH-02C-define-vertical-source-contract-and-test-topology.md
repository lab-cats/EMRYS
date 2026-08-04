# ARCH-02C — Define vertical source, contract, and test topology

## Objective

Specify the final `src/norad` vertical package, contract placement rules, and
mirrored test topology without moving implementation.

## Why this exists

The current repository has evolved beyond a collection of scripts, but an
interim package can become permanent accidental architecture. The final
ownership model must be explicit before direct migrations begin.

## Fixed decisions

- Target `src/norad/stages/<semantic-stage>/` for stage implementation,
  validator, job template, stage README, and stage-only contracts.
- Target `src/norad/{cli,orchestration,scheduler,contracts,libraries,analyses,evidence,reporting,ingestion}`
  for cross-cutting domains.
- Root `tests/` mirrors source domains/stages and retains independent
  contract/integration suites.
- Stages do not import other stage implementations; cross-stage/public
  contracts are centrally owned; there is no generic `utils` bucket.

## Blocked by

- [ARCH-02B](../COMPLETED/ARCH-02B-define-semantic-stage-map.md) — Required: target paths need stable semantic identities.

## Completion unblocks

- [ARCH-02D](../COMPLETED/ARCH-02D-define-direct-migration-mechanics.md) — Fully: migration mechanics can target one final topology.
- [INTAKE-02E](../TODO/INTAKE-02E-define-yaml-tsv-run-lifecycle.md) — Fully: ingestion and orchestration ownership have a target home.
- [LIB-02F](../IN_PROGRESS/LIB-02F-define-shared-library-ownership.md) — Partially: the functional inventory is also required.
- [CONTEXT-09](../TODO/CONTEXT-09-define-local-maintainer-context.md) — Partially: documentation ownership and README coverage are also required.

## Prerequisites

- Confirm language/runtime boundaries and non-Python assets that cannot move as
  ordinary Python modules.

## Required context

- `ARCH-02A`, `ARCH-02B`, current imports and invocations, public contracts,
  jobs, reports, fixtures, packaging constraints, and
  `FUTURE_ARCHITECTURE.md`.

## Questions owned by this card

- `CHOICE-ARCH-01` is closed in the
  [resolved index](../../design/QUESTIONS.md#resolved-index); exact results live
  in [`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md).

## In scope

- Directory ownership, allowed dependency directions, contract taxonomy,
  test mirroring, README/contract colocation, and non-Python asset ownership.

## Out of scope

- Creating `src/norad`, changing imports, packaging/versioning, materializing
  jobs, or introducing an orchestration framework.

## Deliverables

- A reviewed target tree, dependency rules, contract-placement matrix, and
  test-topology map.

## Acceptance evidence

- Every inventoried owner has one target home and every cross-stage dependency
  flows through an allowed neutral domain or explicit contract.
- The topology supports typed assay branch points without pretending all
  analyses share one preprocessing trunk.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, future topology diagrams, `DECISIONS.md` if a
  constraint changes, `PIPELINE_PLAN.md`, `QUESTIONS.md`, and this card.

## Escalation conditions

- Stop for dependency cycles, stage-to-stage implementation imports, a
  catch-all library, or any target that cannot house existing non-Python
  runtime assets without premature packaging decisions.

## Completion record

Completed as a documentation-only JIT package. The canonical
[`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md) assigns
all 14 inventoried functional owners one source home, one kind-specific
versioned YAML descriptor name, explicit native-asset ownership, and one
mirrored test home. It preserves `analyses/` as first-class, fixes stage-local
versus neutral JSON-Schema ownership, and defines acyclic import/invocation
directions for every target domain. The focused audit matched all 14 identity
rows to 14 unique source/test homes with no kind/path mismatch.

No descriptor file, schema, loader, package, orchestrator, job, or physical
source move was implemented. The final combined documentation gate passed;
computational validation was not applicable.
