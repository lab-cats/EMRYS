# TASK-INTAKE-01 — Design a persistent task inbox and reviewed batch intake

State: [`UNREFINED` proposal](README.md). This proposal creates no worktree,
branch, file, automation, schedule, or canonical task state.

## Proposal

Explore a persistent freeform inbox where users can capture ideas under stable
intake IDs without per-note card ceremony, then periodically classify reviewed
notes into nonselectable proposals without interrupting active work.

## Why preserve it

Requiring the complete task-card schema at capture time risks lost notes or
premature TODO cards. A separate intake surface could preserve original intent
while leaving lifecycle, priority, approval, and integration authority intact.

## Settled boundaries

- Original wording remains immutable or append-only under a stable intake ID
  with timestamp and authorship provenance; later disposition links to the
  canonical result without mirroring its live lifecycle status.
- Capture does not weaken classification, approval, worktree isolation,
  integration, validation, publication, privacy, or retention controls.
- A persistent intake branch, if chosen, is not merged wholesale and never
  acts as the canonical integration lane. Selected drafts are re-authored from
  current canonical state in a properly reserved sidecar.
- Batch processing may produce a read-only classification report. Reviewed
  dispositions explicitly distinguish a duplicate, an existing-card
  amendment, a candidate `UNREFINED` proposal, a deferred choice, and a
  rejection with reason, recorded as append-only resolutions. Classification
  cannot promote, select, prioritize, approve, complete, delete, or infer work.
- A documentation-to-card scan is a separate proposed owner. Intake may consume
  its reviewed output but does not run or interpret that scan automatically.
- Inbox-to-UNREFINED and UNREFINED-to-TODO are separate explicit decisions.

## Questions before refinement

- What note format, location, intake-ID scheme, authorship record, and commit
  cadence minimize friction while protecting privacy?
- How is the intake made durable, and is it local-only or privately backed up?
- Is batching manual, reminder-driven, or scheduled read-only automation, and
  who reviews its output?
- How are duplicate or partially overlapping notes linked without losing
  unique meaning?
- What retention rule applies after absorption, rejection, or promotion?

## Related work

- `TASK-LIFECYCLE-01` owns any implemented canonical UNREFINED schema and
  promotion authority.
- `DOC-TASK-SCAN-01` is the separately classified repository-wide scan
  proposal.
- `DOC-IA-01` owns the no-loss and stale-information classifications that any
  future scan or intake disposition must use.
- Concurrent-work policy must own any persistent-intake lane and its isolation.

These are refinement inputs, not dependency relationships.

## Promotion conditions

- Observe at least one representative batch of real notes and document
  duplicates, ambiguity, privacy risks, and review effort.
- Settle durability, scheduling, review, authorship, and retention choices.
- Convert the proposal to a complete reviewed card and obtain an explicit
  integration-owner TODO promotion before implementation.
