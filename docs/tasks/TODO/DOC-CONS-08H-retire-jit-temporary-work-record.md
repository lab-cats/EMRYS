# DOC-CONS-08H — Retire the JIT temporary work record

## Objective

Move both still-unique cleanup entries from `work/active/JIT-01.md` to
authorized durable owners, repair backlinks, and remove the temporary record.

## Why this exists

The completed JIT card still links an active-work file whose two cleanup items
have no accepted durable destination. Removing it now would lose discoverable
work; retaining it forever would make completed work look active.

## Fixed decisions

- Treat Git recoverability as insufficient: each cleanup item needs an indexed
  authorized owner before removal.
- Do not inspect, integrate, depend on, or infer acceptance from any isolated
  sidecar or reserved reconciliation path.
- Move each item, repair references, and delete the old copy in one coherent
  change; do not create a permanent compatibility record.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: the temporary-record disposition and no-loss rule must be approved.

## Completion unblocks

- None.

## Prerequisites

- The integration owner must identify and authorize one canonical destination
  for each of the two cleanup entries from accepted canonical state alone.

## Required context

- `work/active/JIT-01.md`, only its direct backlinks in the completed JIT card,
  the authorized destinations, and the corresponding ownership-ledger row.

## Questions owned by this card

- None.

## In scope

- Moving each cleanup entry to its authorized destination without changing its
  unresolved meaning.
- Repairing direct backlinks and removing the now-empty temporary work record.
- Verifying no current route still treats JIT-01 as active.

## Out of scope

- Resolving the cleanup work itself, reading or integrating sidecar content,
  creating unapproved recovery/reconciliation records, or changing completed
  JIT evidence.

## Deliverables

- Two durable cleanup records, repaired completed-card links, and removal of
  `work/active/JIT-01.md`.

## Acceptance evidence

- Each original cleanup entry remains semantically intact and reachable once.
- The completed JIT card links only accepted canonical owners.
- No inbound link or active-work route points to the removed file.
- Documentation links and the documentation gate pass.

## Canonical documentation updates

- Authorized cleanup owners, completed JIT backlinks, the ownership ledger,
  work navigation if present, and this card.

## Escalation conditions

- Stop if either destination is missing, unauthorized, disputed, or dependent
  on isolated sidecar/reconciliation state.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
