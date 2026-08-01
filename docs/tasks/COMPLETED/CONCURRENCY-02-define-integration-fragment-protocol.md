# CONCURRENCY-02 — Define integration-fragment protocol

## Objective

Define a manual, inspectable protocol for candidate-owned integration
instructions at `docs/fragments/<fragment-id>.md` without granting sidecars
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
- Candidate fragments use `docs/fragments/<fragment-id>.md`, where `fragment-id`
  is the stable card ID or reserved stable slug. `docs/fragments/README.md`
  owns only the filename and candidate-field syntax.
- A fragment is a coupled proposal, never canonical documentation, a task
  card, lifecycle status, blocker, roadmap entry, evidence claim, or task
  authorization.
- The sidecar owns its exact candidate deliverables plus at most one fragment
  path until frozen handoff. Canonical target declarations are nonexclusive
  requests; only the integration owner writes those owners.
- The integration owner assigns `accept`, `partial`, `reject`, `defer`, or
  request-local `stale` and records every request and residual. A `defer` must
  name an implemented, authorized destination; it cannot create a question,
  card, lifecycle state, or `UNREFINED` item by implication.
- The integration owner removes a consumed fragment before canonical
  publication. The immutable published candidate ref provides durable raw
  history; do not build a fragment archive or shadow backlog.
- Human review retains every semantic decision. This card may provide tested,
  operator-invoked Git safeguards for the established manual lifecycle;
  [`CONCURRENCY-03`](../TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md)
  remains the owner of automatic repository-wide structural enforcement. This
  card does not inspect or approve the current pilot's substantive content.

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
  [`RUNBOOK.md`](../../operations/RUNBOOK.md#manual-integration-fragment-exchange),
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

- Define the fragment README's fields, naming, target references, provenance,
  coupling, assumptions, and conflicts, with the disposition vocabulary kept
  in `CONCURRENT_WORK.md`.
- Define candidate creation, frozen handoff, integration-owner consumption,
  partial-use, rejection, deferral, staleness, deletion, and recovery rules.
- Align the concurrent-work policy, task-start routing, task-registry
  clarification, exact runbook workflow, durable rationale, and live handoff.
- Move mechanical candidate, target, application, finalization, no-op, and
  publication checks into small, tested programs under
  `scripts/git_orchestration/`; Markdown links to those programs rather than
  embedding their implementations.

## Out of scope

- Reviewing or integrating current pilot content; creating new task statuses
  or epic indexes; extracting or changing the documentation validator;
  automatically choosing dispositions, composing canonical documents,
  resolving conflicts, authorizing publication, or implementing a daemon,
  queue, archive, orchestration framework, or external project-management
  system.

## Deliverables

- `docs/fragments/README.md` with local schema, naming, and routing guidance;
  `CONCURRENT_WORK.md` remains the owner of freeze, handoff, consumption,
  disposition, and publication lifecycle.
- One consistent authority and disposition protocol across concurrency,
  task-start, task-registry, command, decision, and handoff owners.
- Exact manual handoff and consume/remove/amend checks suitable for the first
  reviewed fragment integration.
- Independent, dry-run-first Git orchestration helpers and focused local tests;
  operator-supplied identities, paths, and terminal records remain mandatory.
- One completed synthetic, non-substantive manual fragment exchange that
  exercises frozen handoff, integration-owner disposition, consumption, and
  final cleanup without reading or integrating the preserved pilot.

## Acceptance evidence

- A maintainer can determine who owns a fragment and each target document at
  every point from candidate authoring through canonical publication.
- Invalid-handoff return, acceptance, rejection, deferral, request-local
  staleness, partial use, no-op closure, and recovery have explicit
  non-destructive outcomes.
- The final canonical protocol leaves only `docs/fragments/README.md`; raw
  fragment history remains recoverable from the immutable published candidate
  ref.
- The recorded synthetic exchange identifies its exact base and candidate,
  exercises at least one accepted or partially used request, proves final
  fragment removal, and supplies observed contract evidence for
  `CONCURRENCY-03` without making a project decision or accepting pilot work.
- Git diff checks, the complete documentation gate, and an independent
  ownership/concurrency review pass.
- Focused helper tests, static validation, the complete Python/coverage lane,
  shell contracts, and report runtime pass; the guarded-R lane is explicitly
  environment-deferred because required lockfile packages are absent. Dry runs
  are side-effect free, normal cherry-pick conflicts restore the exact clean
  parent, and post-application failures preserve recovery state.

## Canonical documentation updates

- `scripts/git_orchestration/`, focused tests, the static/public-command gates,
  `docs/fragments/README.md`, `CONCURRENT_WORK.md`, `RUNBOOK.md`,
  `TASK_START.md`, `docs/tasks/README.md`, `DECISIONS.md`, `HANDOFF.md`,
  `PIPELINE_PLAN.md`, `TEST_BASELINE.md`, `TODO.md`, and concise entry-point
  links required by the final protocol.

## Escalation conditions

- Stop if a fragment would become a second canonical owner, two lanes require
  the same fragment or candidate write reservation, a sidecar must publish
  status or evidence, unresolved material has no authorized disposition, or
  safe integration would require inspecting or changing the pilot's approved
  scope. Duplicate target declarations alone are serialized, not blockers.

## Completion record

Completed by the reconciliation package after a durable coordination
checkpoint and one frozen, remotely published synthetic sidecar. Mechanical
checks that had grown into embedded runbook programs were extracted into
tested, dry-run-first helpers under `scripts/git_orchestration/`; semantic
review and authority remain manual.
The integration owner accepted request `C02-SYNTH-V2-01`, partially accepted
`C02-SYNTH-V2-02` while rejecting its automatic-acceptance residual, rejected
the shadow-archive request `C02-SYNTH-V2-03`, and deferred structural
enforcement request `C02-SYNTH-V2-04` to the existing `CONCURRENCY-03` card.
The fragment was removed before final publication; its immutable source and
the complete disposition evidence are recorded in
[`HANDOFF.md`](../../operations/HANDOFF.md#completed-concurrency-02-synthetic-exchange).
The completion evidence includes focused orchestration tests, the applicable
local computational gate, the documentation gate, exact Git checks, and
independent adversarial review; it does not establish runtime, cluster,
scientific, or biological evidence.
