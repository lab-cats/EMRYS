# TASK-LIFECYCLE-01 — Implement unrefined and integration-review states

## Objective

Complete tested validator and transition support for the authorized
`UNREFINED` proposal intake, and implement the `INTEGRATION_REVIEW`
frozen-handoff state across the task registry and concurrent workflow.

## Why this exists

Rough ideas now have an authorized durable, nonselectable `UNREFINED` location,
but the current validator still rejects it and no tested transition support
exists. Frozen sidecar work also has no precise canonical state between active
execution and completed integration. Completing these mechanisms makes intake
and the integration queue inspectable without treating proposals or
unintegrated work as approved or complete.

## Fixed decisions

- `UNREFINED` is a canonical but nonselectable proposal-intake area. Its files
  may use a smaller proposal schema, cannot block or unblock cards, do not join
  the committed roadmap, and are not actionable task cards.
- Promotion from `UNREFINED` to `TODO` is integration-owner-only and requires
  the complete refined-card contract. `TODO` remains the first selectable
  state.
- `INTEGRATION_REVIEW` is a canonical state for work frozen at an exact
  candidate handoff and awaiting canonical integration. Candidate placement is
  proposal state until the integration owner records the authoritative move.
- `INTEGRATION_REVIEW` permits no scope expansion or candidate movement. A
  correction returns the card to `IN_PROGRESS`; acceptance reaches
  `COMPLETED` only after canonical integration, final validation, publication,
  and upstream equality.
- Exact candidate SHA, worktree, checks, and fragment identity remain live
  state in `HANDOFF.md`, not duplicated in the task card.
- The resolved
  [`CHOICE-LIFECYCLE-01`](../../design/DECISIONS.md#govern-future-work-through-a-file-backed-task-registry)
  persists `INTEGRATION_REVIEW` only for asynchronous review beyond the current
  unpublished integration package; routine same-package integration remains in
  the active-card lifecycle.
- Current lifecycle directories remain flat and authoritative until an atomic
  migration passes parity and final validation. The selected target then uses
  permanent ID-only canonical card paths with reviewed structured lifecycle
  state; logical epic navigation remains a separate concern.
- Target lifecycle, dependency, epic, and tranche Markdown projections are
  committed and byte-for-byte check-regenerated. This is a selected target,
  not a claim that generated views or the permanent path model exist today.

## Blocked by

- [DOC-GATE-01](../COMPLETED/DOC-GATE-01-extract-documentation-validator.md) — Required: new locations and schemas require the extracted, tested validator owner.

## Completion unblocks

- [TASK-EPIC-01](TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md) — Fully: stable lifecycle roots allow the epic index to distinguish non-status navigation from authoritative task state.

## Prerequisites

- Reinventory every live card location, inbound status link, lifecycle command,
  concurrent handoff state, and validator rule at the selected revision.
- Verify the completed
  [`CONCURRENCY-02` fragment protocol](../COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md)
  and the consolidated recovery record without reopening or re-integrating
  preserved source content as part of this task.

## Required context

- [`docs/tasks/README.md`](../README.md),
  [`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md),
  [`TASK_START.md`](../../operations/TASK_START.md), the task-registry and
  rolling-delivery decisions in
  [`DECISIONS.md`](../../design/DECISIONS.md), and the extracted documentation
  validator plus focused tests.
- Completed `CONCURRENCY-02`, completed `DOC-GATE-01`, the resolved program-owned
  integration-review trigger, and the live handoff/roadmap owners.

## Questions owned by this card

- None. The program-owned integration-review trigger is resolved; this card
  owns implementation mechanics only.

## In scope

- Formalize and validate the existing lightweight UNREFINED proposal schema,
  add the `INTEGRATION_REVIEW` directory and concise README, define its full
  card schema, and specify exact permitted transitions for both mechanisms.
- Define selectability, mutability, dependency participation, inbound-link
  repair, sidecar proposal, integration-owner authority, return, acceptance,
  and durable-checkpoint behavior.
- Extend the extracted validator and independent fixtures for accepted and
  rejected locations, schemas, transitions, dependency participation, and
  card reachability.
- Align task-registry, concurrency, task-start, runbook, decision, roadmap,
  handoff, entry-point, and concise conduct guidance with implemented truth.

## Out of scope

- Reclassifying blocker/unblock edges; defining or materializing epic
  taxonomy; changing card scope; reopening or re-integrating the consumed
  recovery source; recasting the refactor program; or changing workflow,
  schema, scientific, report, runtime, or evidence behavior.

## Deliverables

- Tested support for the authorized `UNREFINED` location and implemented
  `INTEGRATION_REVIEW` directory, schemas, transition rules, authority model,
  and supported commands.
- Independent fixtures and validator rules that accept the reviewed
  lightweight `UNREFINED` schema while rejecting selection, priority,
  dependency, blocker, unblock, completion, and full-card authority there.
- For the later permanent-path migration, a frozen old/new manifest covering
  every ID, path, lifecycle state, H1, body, completion record, dependency,
  and inbound link; legacy-read/new-write transition testing without a mixed
  canonical registry; exact parity and stale-view checks; one atomic cutover;
  and abort/rollback that leaves the old registry canonical until every gate
  passes.
- Committed lifecycle projections that name their generator, relevant input
  digest, and exact refresh/check behavior and that are regenerated in
  temporary space for byte-for-byte comparison.
- Tested documentation-validator support that distinguishes proposals,
  actionable cards, frozen review work, and completed history.
- Updated canonical documentation with no duplicated live candidate identity
  or program-order ownership.

## Acceptance evidence

- Unrefined proposals cannot be selected, enter dependency relationships, or
  satisfy the full card count/schema until promoted by the integrator.
- Only the integration owner can make `INTEGRATION_REVIEW` canonical, and a
  frozen candidate cannot change without returning to `IN_PROGRESS`.
- `COMPLETED` remains impossible before canonical integration, validation,
  publication, and upstream equality.
- Focused validator tests, transition fixtures, the complete documentation
  gate, Git diff checks, and independent lifecycle/concurrency review pass.

## Canonical documentation updates

- `docs/tasks/README.md`, status READMEs, `CONCURRENT_WORK.md`, `TASK_START.md`,
  `RUNBOOK.md`, the extracted validator and tests, `DECISIONS.md`,
  `PIPELINE_PLAN.md`, `TODO.md`, `HANDOFF.md`, `README.md`, concise `AGENTS.md`
  enforcement if necessary, and this card.

## Escalation conditions

- Stop if a proposal becomes selectable without refinement, a sidecar can
  publish authoritative status, review state duplicates live candidate facts,
  a transition weakens completion evidence, or implementation requires the
  blocker-graph migration owned by `TASK-REG-01`.
- Sequence `TASK-REG-01` before or with the final dependency cutover as
  migration readiness, not as a blocker on independent lifecycle design.

## Completion record

Not started as an implementation package. The authorized UNREFINED directory,
README, and recovered proposals exist, while validator and transition support
remain unimplemented. Select this card for read-only planning; implementation
requires a separately approved task-specific plan.
