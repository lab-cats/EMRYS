# DOC-SITEMAP-01 — Classify temporary task-start routing

## Objective

Classify and relocate the temporary task-start material without duplicating
its information or prescribing the final child-map hierarchy.

## Why this exists

JIT-01 preserved conditional task-start material in `TOP_LEVEL.md` so the
universal router could become concise before permanent destinations were
settled.

## Fixed decisions

- Classify temporary material before moving it.
- Move information to one canonical owner, repair references, and remove the
  old copy; never copy it into a second owner.
- Restore `TOP_LEVEL.md` as a concise map after relocation.
- Parent maps reference child maps without duplicating their entries or
  contents.
- Do not prescribe the final child-map hierarchy before source and owner
  inspection.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- The completed [JIT-01 procedure](../COMPLETED/JIT-01-establish-self-hosting-thin-slice-delivery.md)
  supplies the frozen temporary routing material and move-not-copy rules.

## Required context

- The [temporary task-start routing](../../sitemap/TOP_LEVEL.md#temporary-task-start-routing),
  targeted stubs in [`TASK_START.md`](../../operations/TASK_START.md), and the
  cleanup rules in [`TASK_DELIVERY.md`](../../operations/TASK_DELIVERY.md).
- Only affected canonical owners and inbound references identified one
  temporary block at a time.

## Questions owned by this card

- None.

## In scope

- Classifying each temporary block in `TOP_LEVEL.md`.
- Moving blocks into child maps or existing canonical owners, repairing
  references, removing old copies, and restoring a concise top-level map.
- Applying touch-move-delete migration as later documentation is changed.

## Out of scope

- Designing the final child-map hierarchy in advance, general documentation
  reorganization, or copying content into parallel owners.

## Deliverables

- A source-to-destination disposition for every temporary block.
- One canonical copy of retained information, repaired references, and a
  concise `TOP_LEVEL.md`.

## Acceptance evidence

- Every temporary block has one inspected owner or approved no-change
  disposition.
- Moved information remains reachable, old copies are removed, and parent maps
  do not duplicate child-map content.
- The documentation gate passes against the final routing structure.

## Canonical documentation updates

- `TOP_LEVEL.md`, `TASK_START.md`, affected canonical owners or child maps, and
  this card.

## Escalation conditions

- Stop if unique information lacks a safe owner, two owners disagree, or
  relocation would change safety, scientific, evidence, or operational
  meaning.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
