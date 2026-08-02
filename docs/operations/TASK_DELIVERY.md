# Task delivery

Task selection and context routing remain in
[`TASK_START.md`](TASK_START.md), with conditional routes in the
[top-level sitemap](../sitemap/TOP_LEVEL.md#temporary-task-start-routing).

## Neutral cleanup capture

During an active slice, a cleanup-queue entry contains only the slice ID, the
touched source or path, and a neutral observation. Creating an entry performs
no ownership, destination, impact, or solution discovery. An unrelated
observation cannot expand the active card.

## Delayed movement

Misplaced information directly implicated by the active work becomes a move
candidate. Movement occurs only during cleanup: move the information, repair
its references, and remove the old copy. Do not copy information into a second
owner.

## Cleanup classification

During cleanup, inspect one queue entry only until one disposition is possible,
then stop discovery:

- `FIX_NOW_REQUIRED` — leaving the item unresolved would make current
  information incorrect, broken, unsafe, contradictory, or misleading.
- `FIX_NOW_TRIVIAL` — semantics are settled, the owner is obvious, scope is
  tiny and bounded, and correction is lower effort and risk than later intake.
  Decision-bearing public, scientific, schema, safety, or evidence changes are
  not trivial.
- `KNOWN_CARD` — the exact card is already known from authorized active
  context. Do not search for alternatives, and update that card only when the
  active scope authorizes it.
- `TASK_INTAKE` — every other potential task. Do not search the task registry
  during cleanup, and preserve the item until it has a durable intake
  destination.
- `NO_CHANGE` — the observation requires no repository change.

## Input-dependent decision records

When a noncritical disposition still requires user input, retain its active
record as a decision artifact until the disposition is durable. Retention does
not expand the active card, authorize related work, or by itself prevent close
of an otherwise accepted card.

## Slice start and close

Start a slice with exactly three lines labeled `Outcome`, `Touches`, and
`Stop`: one outcome, one bounded owner or path area, and one stopping
condition. If the charter needs multiple outcomes or stopping conditions,
split it again.

A slice closes when the bounded result exists, collateral observations are in
the cleanup queue, and the result is committed. Focused validation is optional
feedback unless continuing would be unsafe or a later slice directly depends
on the unverified behavior. Ordinary slice close performs no canonical
reconciliation or lifecycle maintenance.

## Card close

After feature or procedure work freezes, close the card in this order:

1. **Review** — semantically assess the final change and its affected owners.
2. **Validation** — run the applicable automated structural or behavioral
   checks.
3. **Verification** — prove the acceptance, lifecycle, Git, and publication
   conditions.

Exact commands remain in the
[`RUNBOOK.md` local validation gate](RUNBOOK.md#local-validation-gate). This
procedure neither copies those commands nor introduces another validation
framework. Change the existing validator only if its tooling makes the
procedure impossible.
