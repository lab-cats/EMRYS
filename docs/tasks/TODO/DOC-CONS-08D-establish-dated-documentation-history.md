# DOC-CONS-08D — Establish dated documentation history

## Objective

Create a shallow dated-history route and separate frozen audit/testing evidence
from the concise current owners that reference it.

## Why this exists

`REFACTOR_AUDIT.md` and `TEST_BASELINE.md` interleave valuable dated evidence,
failed approaches, current gates, and stale recommendations. Git recovery alone
does not make that evidence discoverable or explain its status.

## Fixed decisions

- Create `docs/history/README.md` as a shallow index with dated topic children,
  initially `audits/` and `testing/`; reserve `demos/` and operational history
  for later cards.
- Historical records are explicitly dated, immutable evidence views and never
  second owners of current state, roadmap, or contracts.
- Preserve unique evidence, methods, rejected approaches, limitations, and
  recheck triggers before removing old copies.
- Leave a concise current audit/baseline owner or route where ongoing gates and
  recheck triggers require one.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: history ownership and no-loss migration rules must be settled.

## Completion unblocks

- [DOC-CONS-08E](DOC-CONS-08E-separate-live-state-from-history.md) — Fully: the root history route and date/provenance rules then exist for an operational child owned by that card.
- [DOC-CONS-08G](DOC-CONS-08G-consolidate-demo-views.md) — Fully: the root history route and date/provenance rules then exist for a demo child owned by that card.

## Prerequisites

- Establish the exact date/provenance of each moved record from repository
  evidence; do not invent a date from file modification time.

## Required context

- `REFACTOR_AUDIT.md`, `TEST_BASELINE.md`, their direct inbound links, related
  completed cards, and the history rows in `DOCUMENTATION_OWNERSHIP.md`.

## Questions owned by this card

- None.

## In scope

- Creating the shallow history index and dated audit/testing children.
- Moving frozen audit and gate narratives with provenance intact.
- Retaining or creating concise current routes for active risk matrices,
  baseline gates, and recheck triggers.
- Repairing all inbound links and removing each old copy atomically.

## Out of scope

- Changing current evidence claims, test behavior, thresholds, roadmap status,
  scientific conclusions, completed cards, or demo/live-state content owned by
  later packages.

## Deliverables

- An indexed dated-history structure, migrated audit/testing records, and
  concise current audit/baseline owners or routes.

## Acceptance evidence

- Every historical paragraph has a date/provenance and one discoverable owner.
- Current gates and recheck triggers remain clearly current and do not rely on
  a frozen record as mutable truth.
- No unique failure, risk, evidence limitation, or rejected approach is lost.
- All repaired links and the documentation gate pass.

## Canonical documentation updates

- `docs/history/`, `REFACTOR_AUDIT.md`, `TEST_BASELINE.md`, direct inbound
  references, the ownership ledger, dependent cards, and this card.

## Escalation conditions

- Stop if a record cannot be dated/provenanced, current and historical truth
  conflict, or removal would make evidence or failure knowledge less
  discoverable.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
