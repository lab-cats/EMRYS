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
- Target `src/norad/{cli,orchestration,scheduler,contracts,libraries,evidence,reporting,ingestion}`
  for cross-cutting domains.
- Root `tests/` mirrors source domains/stages and retains independent
  contract/integration suites.
- Stages do not import other stage implementations; cross-stage/public
  contracts are centrally owned; there is no generic `utils` bucket.

## Blocked by

- [ARCH-02B](../IN_PROGRESS/ARCH-02B-define-semantic-stage-map.md) — Required: target paths need stable semantic identities.

## Completion unblocks

- [ARCH-02D](../IN_PROGRESS/ARCH-02D-define-direct-migration-mechanics.md) — Fully: migration mechanics can target one final topology.
- [INTAKE-02E](../TODO/INTAKE-02E-define-yaml-tsv-run-lifecycle.md) — Fully: ingestion and orchestration ownership have a target home.
- [LIB-02F](../TODO/LIB-02F-define-shared-library-ownership.md) — Partially: the functional inventory is also required.
- [CONTEXT-09](../TODO/CONTEXT-09-define-local-maintainer-context.md) — Partially: documentation ownership and README coverage are also required.

## Prerequisites

- Confirm language/runtime boundaries and non-Python assets that cannot move as
  ordinary Python modules.

## Required context

- `ARCH-02A`, `ARCH-02B`, current imports and invocations, public contracts,
  jobs, reports, fixtures, packaging constraints, and
  `FUTURE_ARCHITECTURE.md`.

## Questions owned by this card

- [`CHOICE-ARCH-01`](../../design/QUESTIONS.md#choice-arch-01--machine-stage-descriptor-and-contract-serialization).

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

Not started. Select this card for read-only planning; implementation requires
separate approval.
