# CONCURRENCY-02 — Define integration-fragment protocol

## Objective

Define a manual, inspectable protocol for candidate-owned integration
instructions at `docs/fragments/<card-name>.md` without granting sidecars
authority over canonical documents.

## Why this exists

Sidecars need a durable way to report changes that the integration owner must
distribute across central documentation. Ad hoc temporary files can be lost,
while direct edits to shared owners create path conflicts and competing truth.
A bounded fragment contract preserves the proposed facts, provenance, and
disposition work without creating another canonical documentation layer.

## Fixed decisions

- [`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md) remains the
  canonical owner of lane authority, handoff, and serialized integration.
- Candidate fragments use `docs/fragments/<card-name>.md`, where `card-name`
  is the stable card ID or reserved stable slug. `docs/fragments/README.md`
  owns the filename and field schema.
- A fragment is a coupled proposal, never canonical documentation, a task
  card, lifecycle status, blocker, roadmap entry, evidence claim, or task
  authorization.
- The sidecar owns its exact reserved fragment path until a frozen handoff.
  The integration owner then accepts, rejects, or defers each requested update
  and remains the sole writer of canonical owners.
- Incorporated facts enter their proper canonical owners. Deferred work
  becomes an open question, an unrefined proposal, or a refined TODO card.
  Rejected material is recorded only when its rationale is durably useful.
- The integration owner removes a consumed fragment before canonical
  publication. The preserved candidate branch provides history; do not build
  a fragment archive or shadow backlog.
- Establish the human-reviewed protocol before adding automated structural
  enforcement. This card does not inspect or approve the current pilot's
  substantive card or fragment content.

## Blocked by

- None.

## Completion unblocks

- [CONCURRENCY-03](../TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md) — Partially: the validator cannot enforce a fragment lifecycle until this card publishes its stable manual contract.
- [TASK-LIFECYCLE-01](../TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md) — Partially: `INTEGRATION_REVIEW` cannot safely represent a frozen handoff until fragment ownership and disposition are defined.

## Prerequisites

- Verify the canonical integration branch and every participating candidate
  worktree, branch, base, and reserved path from live Git state.
- Preserve the current pilot as unreviewed candidate input; do not treat its
  temporary handoff file as the approved schema or integrate its content.

## Required context

- [`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md), its exact
  commands in
  [`RUNBOOK.md`](../../operations/RUNBOOK.md#concurrent-worktrees-and-serialized-integration),
  the task lifecycle in [`../README.md`](../README.md), and the isolated-
  authoring decision in
  [`DECISIONS.md`](../../design/DECISIONS.md#permit-isolated-concurrent-authoring-with-serialized-integration).
- The live pilot lane packet and candidate identity in
  [`HANDOFF.md`](../../operations/HANDOFF.md#active-concurrent-lanes), without
  reading pilot card substance as part of this task.

## Questions owned by this card

- None. The location, authority boundary, transient lifecycle, and manual-
  before-automation direction are settled.

## In scope

- Define the fragment README, required fields, stable naming, target-owner and
  anchor references, provenance, coupling, assumption, conflict, and
  disposition vocabulary.
- Define candidate creation, frozen handoff, integration-owner consumption,
  partial-use, rejection, deferral, staleness, deletion, and recovery rules.
- Align the concurrent-work policy, task-start routing, task-registry
  clarification, exact runbook workflow, durable rationale, and live handoff.
- Define manual candidate and final-canonical checks that remain usable before
  automated enforcement exists.

## Out of scope

- Reviewing or integrating current pilot content; creating new task statuses
  or epic indexes; extracting or changing the documentation validator;
  automatically composing canonical documents; or implementing an
  orchestration, queue, archive, or external project-management system.

## Deliverables

- `docs/fragments/README.md` with local schema, naming, and routing guidance;
  `CONCURRENT_WORK.md` remains the owner of freeze, handoff, consumption,
  disposition, and publication lifecycle.
- One consistent authority and disposition protocol across concurrency,
  task-start, task-registry, command, decision, and handoff owners.
- Exact manual handoff and consume/remove/amend checks suitable for the first
  reviewed fragment integration.
- One completed synthetic, non-substantive manual fragment exchange that
  exercises frozen handoff, integration-owner disposition, consumption, and
  final cleanup without reading or integrating the preserved pilot.

## Acceptance evidence

- A maintainer can determine who owns a fragment and each target document at
  every point from candidate authoring through canonical publication.
- Acceptance, rejection, deferral, stale-base handling, partial use, and
  recovery have explicit non-destructive outcomes.
- The final canonical protocol leaves only `docs/fragments/README.md`; raw
  fragment history remains recoverable from the preserved candidate branch.
- The recorded synthetic exchange identifies its exact base and candidate,
  exercises at least one accepted or partially used request, proves final
  fragment removal, and supplies observed contract evidence for
  `CONCURRENCY-03` without making a project decision or accepting pilot work.
- Git diff checks, the complete documentation gate, and an independent
  ownership/concurrency review pass without changing executable behavior.

## Canonical documentation updates

- `docs/fragments/README.md`, `CONCURRENT_WORK.md`, `RUNBOOK.md`,
  `TASK_START.md`, `docs/tasks/README.md`, `DECISIONS.md`, `HANDOFF.md`,
  `PIPELINE_PLAN.md`, `TODO.md`, and concise entry-point or conduct links only
  when required by the final protocol.

## Escalation conditions

- Stop if a fragment would become a second canonical owner, two lanes require
  the same fragment or target path, a sidecar must publish status or evidence,
  unresolved material has no proper canonical disposition, or safe
  integration would require inspecting or changing the pilot's approved scope.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
