# TASK-LIFECYCLE-01 — Implement unrefined and integration-review states

**Approved task-specific plan — current flat lifecycle only**

- Inspected revision: published/upstream-equal selection `5766a65` in
  `/Users/elisteiger/dev/norad` on branch
  `codex/post-mig-03m-completion`; no concurrent mutable lane shares this
  worktree.
- Planning category: `behavior or architecture planning`. Validation impact:
  `executable/test-affecting`.
- Current outcome: make the existing eight `UNREFINED` proposals and their
  README valid under an explicit lightweight, nonactionable schema; add the
  flat `INTEGRATION_REVIEW` status README and full-card validation; and document
  the already resolved manual transitions and authority boundary.
- Schema boundary: an unrefined proposal retains one canonical ID/H1 and
  matching filename, the exact local proposal-state declaration, and ordered
  `Proposal`, `Why preserve it`, `Settled boundaries`, `Questions before
  refinement`, and `Promotion conditions` sections. Additional proposal
  sections may remain. Full-card lifecycle/dependency/completion headings and
  dependency-edge syntax are prohibited. Proposals do not count as actionable
  cards and need no canonical inbound status link.
- Integration-review boundary: cards use the unchanged full actionable-card
  schema and unique IDs, participate in ordinary reachability/dependency
  validation, and require completed blockers like active/completed cards.
  Persistence is limited to an asynchronous frozen handoff beyond the current
  unpublished integration package; same-package handoff stays `IN_PROGRESS`.
- Execution slices: first add independent accepted/rejected proposal and
  review-state fixtures; then change only the existing validator and create
  the required status README; then run the focused validator/transition gate;
  finally batch all impact-directed command, policy, status, evidence, audit,
  and inbound-link updates into the separate card close.
- Implementation write set: `scripts/git_orchestration/validate_documentation.py`,
  `tests/git_orchestration/test_documentation_validator.py`,
  `tests/git_orchestration/test_validators.py`, and new
  `docs/tasks/INTEGRATION_REVIEW/README.md`. The final documentation close may
  touch only the card's canonical documentation roster and discovered inbound
  lifecycle links.
- Validation: smallest affected tests at slice boundaries; at the card
  boundary, the complete focused documentation/public-command set, exact
  `make -s documentation-check`, Git checks, and a separate lifecycle/
  concurrency semantic review. No dependency installation, network, runtime,
  cluster, production, scientific-review, biological, or default-branch work.
- Explicit exclusions: no permanent ID-only path migration, generated
  lifecycle/dependency/epic/tranche projections, blocker-edge migration,
  transition daemon or automation, fragment enforcement, proposal promotion,
  existing-proposal rewrite, or card movement into `INTEGRATION_REVIEW`.

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
- Current lifecycle directories remain flat and authoritative in this package.
  Permanent ID-only paths and generated lifecycle/dependency/epic/tranche
  projections remain later atomic-registry target constraints; they are not
  deliverables or acceptance criteria here.

## Blocked by

- [DOC-GATE-01](../COMPLETED/DOC-GATE-01-extract-documentation-validator.md) — Required: new locations and schemas require the extracted, tested validator owner.

## Completion unblocks

- [TASK-EPIC-01](../TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md) — Fully: stable lifecycle roots allow the epic index to distinguish non-status navigation from authoritative task state.

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
  recovery source; recasting the refactor program; or changing computational
  workflow, data schema, scientific, report, runtime, or evidence behavior.
- Permanent ID-only card-path migration; structured lifecycle metadata;
  generated lifecycle, dependency, epic, or tranche projections; mixed-root
  compatibility; parity manifests; generator/check commands; or atomic
  registry cutover. Those require later separately selected registry,
  dependency, epic, and tranche owners.

## Deliverables

- Tested support for the authorized `UNREFINED` location and implemented
  `INTEGRATION_REVIEW` directory, schemas, transition rules, authority model,
  and supported commands.
- Independent fixtures and validator rules that accept the reviewed
  lightweight `UNREFINED` schema while rejecting selection, priority,
  dependency, blocker, unblock, completion, and full-card authority there.
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

Selected on 2026-08-03 from clean, published, upstream-equal DOC-GATE-01 close
`dc3ee2e`. The authorized UNREFINED directory, README, and recovered proposals
exist, while validator and transition support remain unimplemented. Selection
starts bounded task-specific planning only; it does not implement a lifecycle
state, generated projection, permanent-path migration, or transition.
