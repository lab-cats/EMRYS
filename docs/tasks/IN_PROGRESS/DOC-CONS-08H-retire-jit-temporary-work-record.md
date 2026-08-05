# DOC-CONS-08H — Retire the JIT temporary work record

## Objective

Give both cleanup entries in `work/active/JIT-01.md` final no-loss
dispositions, preserve any still-unique material in authorized durable owners,
repair backlinks, and remove the temporary record.

## Why this exists

The completed JIT card still links an active-work file. The first `NO_CHANGE`
entry's substance is already durable in completed `DOC-GATE-01`; the task-
intake entry remains unique and has no accepted durable destination. Removing
the record without checking both entries could lose discoverable work;
retaining it forever would make completed work look active.

## Fixed decisions

- Treat Git recoverability as insufficient for unique material. Confirm the
  first entry's accepted `DOC-GATE-01` owner and give the second an indexed,
  authorized owner before removal.
- Do not duplicate the already durable `NO_CHANGE` substance merely to move
  both entries mechanically.
- Do not inspect, integrate, depend on, or infer acceptance from any isolated
  sidecar or reserved reconciliation path.
- Move each item, repair references, and delete the old copy in one coherent
  change; do not create a permanent compatibility record.

## Blocked by

- [DOC-IA-01](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: the temporary-record disposition and no-loss rule must be approved.

## Completion unblocks

- None.

## Prerequisites

- The integration owner must verify the accepted canonical owner for the first
  entry and identify and authorize one canonical destination for the second
  from accepted canonical state alone.

## Required context

- `work/active/JIT-01.md`, only its direct backlinks in the completed JIT card,
  the authorized destinations, and the corresponding ownership-ledger row.

## Questions owned by this card

- None.

## In scope

- Recording the first entry's `NO_CHANGE` disposition against its existing
  durable owner and moving the still-unique second entry to its authorized
  destination without changing its unresolved meaning.
- Repairing direct backlinks and removing the now-empty temporary work record.
- Verifying no current route still treats JIT-01 as active.

## Out of scope

- Resolving the cleanup work itself, reading or integrating sidecar content,
  creating unapproved recovery/reconciliation records, or changing completed
  JIT evidence.

## Deliverables

- Two final no-loss dispositions, one durable destination for the still-unique
  task-intake material, repaired completed-card links, and removal of
  `work/active/JIT-01.md`.

## Acceptance evidence

- Each original cleanup entry is semantically accounted for once without
  duplicating already durable material.
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

Selected on 2026-08-05 from clean, published, live-remote-equal predecessor
`db4272c925278efd4952091f259e2cd8297dedaa` on
`codex/residual-source-topology-convergence`. This status-only selection does
not open or change `work/active/JIT-01.md`, choose either destination, inspect
sidecar/reconciliation state, retire the record, select a successor, or promote
evidence. The approved implementation is limited to two no-loss dispositions,
their accepted canonical owners, direct backlinks, and removal of the empty
temporary record; it stops if accepted canonical state cannot supply either
destination.
