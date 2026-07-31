# TASK-LIFECYCLE-01 — Implement unrefined and integration-review states

## Objective

Implement the approved `UNREFINED` proposal intake and
`INTEGRATION_REVIEW` frozen-handoff state across the task registry, concurrent
workflow, and tested documentation validator.

## Why this exists

Rough ideas currently must either masquerade as fully refined TODO cards or
remain outside the durable registry, while frozen sidecar work has no precise
canonical state between active execution and completed integration. Explicit
states can make intake and the integration queue inspectable without treating
proposals or unintegrated work as approved or complete.

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
- [`PROGRAM-01`](PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
  decides the objective trigger for persisting `INTEGRATION_REVIEW`; routine
  immediate integration must not create meaningless status churn.
- Lifecycle directories remain flat. Logical epic navigation is implemented
  separately after the lifecycle roots are stable.

## Blocked by

- [CONCURRENCY-02](CONCURRENCY-02-define-integration-fragment-protocol.md) — Required: frozen handoff and integration-owner acceptance require a stable fragment protocol.
- [DOC-GATE-01](DOC-GATE-01-extract-documentation-validator.md) — Required: new locations and schemas require the extracted, tested validator owner.
- [PROGRAM-01](PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md) — Required: the rolling tranche model must settle when an asynchronous handoff enters the durable review queue.

## Completion unblocks

- [TASK-EPIC-01](TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md) — Fully: stable lifecycle roots allow the epic index to distinguish non-status navigation from authoritative task state.

## Prerequisites

- Reinventory every live card location, inbound status link, lifecycle command,
  concurrent handoff state, and validator rule at the selected revision.
- Verify the completed fragment protocol and `PROGRAM-01` tranche contract
  without integrating preserved candidate content as part of this task.

## Required context

- [`docs/tasks/README.md`](../README.md),
  [`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md),
  [`TASK_START.md`](../../operations/TASK_START.md), the task-registry and
  rolling-delivery decisions in
  [`DECISIONS.md`](../../design/DECISIONS.md), and the extracted documentation
  validator plus focused tests.
- The completed `CONCURRENCY-02`, `DOC-GATE-01`, and `PROGRAM-01` records and
  the live handoff/roadmap owners.

## Questions owned by this card

- None. `PROGRAM-01` owns the remaining integration-review trigger; this card
  owns only implementation mechanics after that decision is complete.

## In scope

- Add the lifecycle directories and concise READMEs, the lightweight unrefined
  proposal schema, the full integration-review card schema, and exact permitted
  transitions.
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
  taxonomy; changing card scope; reviewing or integrating preserved pilot
  content; recasting the refactor program; or changing workflow, schema,
  scientific, report, runtime, or evidence behavior.

## Deliverables

- Implemented `UNREFINED` and `INTEGRATION_REVIEW` directories, schemas,
  transition rules, authority model, and supported commands.
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

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
