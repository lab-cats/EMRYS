# ARCH-02B — Define semantic stage map

## Objective

Assign each functional stage a user-facing title, public slug, stable versioned
key, and explicit DAG position.

## Why this exists

Identifiers such as `00c`, `02b`, and `09c` preserve history but do not help a
scientist understand purpose. Removing numbers without a stable machine key or
explicit ordering model would create a different ambiguity.

## Fixed decisions

- Use three identities: display title, public slug, and stable versioned key.
- Numeric IDs remain historical aliases/provenance only after migration.
- The DAG, not lexical filename order, defines execution order.
- Keep the high-level user sequence conceptual and implementation-neutral.

## Blocked by

- [ARCH-02A](../COMPLETED/ARCH-02A-inventory-functional-stages-and-contracts.md) — Required: names and order must derive from the functional inventory.

## Completion unblocks

- [ARCH-02C](../IN_PROGRESS/ARCH-02C-define-vertical-source-contract-and-test-topology.md) — Fully: target directories and contract ownership can use stable semantic identities.
- [DOC-PIPE-04](../TODO/DOC-PIPE-04-create-user-pipeline-overview.md) — Partially: the documentation information architecture must also be settled.

## Prerequisites

- Resolve every stage-boundary ambiguity exposed by `ARCH-02A` or record an
  owning choice.

## Required context

- The functional inventory, current pipeline table/diagram, user-facing
  language, public schemas, report labels, and historical stage references.

## Questions owned by this card

- [`CHOICE-STAGE-01`](../../design/QUESTIONS.md#choice-stage-01--exact-semantic-stage-identities-and-dag).

## In scope

- Exact titles, slugs, versioned keys, historical aliases, DAG edges, and a
  migration map for documentation and contracts.

## Out of scope

- Moving files, changing behavior, editing current technical topology as if
  migration were complete, or creating a universal assay sequence.

## Deliverables

- A reviewed semantic-stage map and DAG contract.
- Explicit naming rules for future stages and branch points.

## Acceptance evidence

- Every functional stage has unique identities and an unambiguous place in the
  DAG.
- Names are comprehensible to scientists and stable enough for machine
  contracts without encoding mutable order.

## Canonical documentation updates

- `DECISIONS.md`, `FUTURE_ARCHITECTURE.md`, `PIPELINE_PLAN.md`,
  `QUESTIONS.md`, and this card. Current architecture changes only when the map
  is implemented.

## Escalation conditions

- Stop if a name implies unsupported scientific interpretation, hides a
  branch, or requires combining stages with distinct contracts.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
