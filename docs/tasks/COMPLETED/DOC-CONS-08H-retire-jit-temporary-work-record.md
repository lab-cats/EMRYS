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
`codex/residual-source-topology-convergence`; status-only selection checkpoint
`0081762f9aecd401a1aaad8eab6873ec2f214648` was published and proved
live-remote-equal before the temporary record was opened.

The completed documentation-only/non-consuming package:

- confirms that former Slice `7A` is `NO_CHANGE` because completed
  [`DOC-GATE-01`](DOC-GATE-01-extract-documentation-validator.md) already owns
  the independently locked extraction behavior and supported logic-free Make
  exposure; only the cleanup provenance needed a final record;
- routes the second entry to existing nonselectable
  [`TASK-INTAKE-01`](../UNREFINED/TASK-INTAKE-01-design-persistent-task-inbox.md)
  and adds only the two semantics missing there: read-only batched search of
  the canonical task registry and a distinct proposed-new-card classification;
- preserves deduplication plus proposed amend/new/`UNREFINED`/defer/reject
  outcomes while explicitly prohibiting the classification from creating or
  amending canonical task state or gaining selection, priority, approval, or
  implementation authority;
- repairs the completed JIT card to link both accepted canonical owners,
  records the two original dispositions once, and removes
  `work/active/JIT-01.md` with no compatibility record;
- removes every live inbound/current-inventory row for the retired path and
  updates the current residual inventory from the audit-time 87 paths and
  eleven groups to 86 paths and ten groups: 76 `RETAIN_ROOT`, 10 `DEFER`, and
  no current `RETIRE`; and
- uses only accepted canonical state. No isolated sidecar or reserved
  reconciliation path was inspected or inferred.

Independent first-entry ownership, second-entry semantic, and inbound/current-
inventory reviews found the two destinations authorized and complete after the
bounded proposal edit. Final no-loss and lifecycle review, `git diff --check`,
and `make -s documentation-check` pass on the exact completed tree: 231
Markdown documents, 148 task cards, and 5 Mermaid sources. Computational,
shell, R, report-runtime, dependency, full-suite, runtime, cluster,
scientific-review, and biological validation are not applicable because the
complete selection-to-close diff is non-consuming documentation only. No
successor is selected by this close.
