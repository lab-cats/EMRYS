# Task delivery

Task selection and context routing remain in
[`TASK_START.md`](TASK_START.md), with conditional routes in the
[top-level sitemap](../sitemap/TOP_LEVEL.md#temporary-task-start-routing).

## Package delivery

Every implementation package uses a linear descendant branch from the latest
clean, documentation-patched predecessor. Verify that predecessor is pushed and
upstream-equal before branching.

Deliver an implementation package in this order:

1. Create the approved package branch and implement only that package and its
   directly required contracts.
2. Add focused tests. During implementation, use focused checks repeatedly and
   reserve one de-duplicated complete applicable computational gate for the
   final executable state.
3. Commit the implementation and tests.
4. Use the final diff, the
   [documentation ownership map](../sitemap/DOCUMENTATION_OWNERSHIP.md), and
   targeted link/search results to select affected documents and diagrams.
   Inspect their canonical owners and direct references.
5. Perform a repository-wide documentation impact check. Broaden semantic
   inspection only when the change is cross-cutting, changes ownership, reveals
   a contradiction, or cannot otherwise be bounded safely.
6. When behavior changes, update every affected status, interface, command,
   path, schema, limitation, diagram, and next-step claim. Durable truth belongs
   in its canonical owner, not in the selected card.
7. For any selected card, update its lifecycle, completion record, and all
   inbound status links in the same patch, regardless of whether behavior
   changed.
8. Commit the impact-directed documentation patch separately.
9. Run the documentation gate. Do not repeat computational suites when the
   documentation patch leaves executable configuration, dependencies, Make
   targets, schemas, fixtures, report templates, and test-harness selection and
   execution semantics unchanged.
10. Require a clean worktree, inspect history, push, and prove upstream equality
    before creating the next package branch.

If executable behavior changes after the documentation patch, reopen the gate:
retest the corrected final executable state, commit it, and perform another
separate impact-directed documentation patch.

A standalone documentation-only package uses one documentation commit after
any applicable status-only card-selection commit. When the complete
predecessor-to-final diff changes only documentation artifacts that are not
consumed by executable, configuration, generation, schema, fixture,
report-template, dependency, or test-harness selection or execution behavior,
computational validation is not applicable. Run Git and documentation
validation only; do not fabricate an implementation commit or run computational
Python, shell, R, report-runtime, full-suite, or cluster validation.

Pytest is quiet by default and retains captured output for failures. Use the
quiet Make and log-capture procedures in the
[`RUNBOOK.md` local validation gate](RUNBOOK.md#local-validation-gate); full
output is for failures or an explicitly requested verbose run. A recorded full
gate may be reused after a documentation-only patch only when Git inspection
proves the executable state is unchanged.

Runtime and cluster promotion remain upstream-sequential, including during an
approved local-only descendant sequence. Never promote a downstream stage
before its prerequisite runtime gates pass.

After each task, suggest relevant owner updates that remain outside the
authorized write set and preserve them through the cleanup process below rather
than expanding the active package.

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
