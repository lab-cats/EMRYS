# Task delivery

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
