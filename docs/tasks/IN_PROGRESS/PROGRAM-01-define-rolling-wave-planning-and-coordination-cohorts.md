# PROGRAM-01 — Define rolling-wave planning and coordination cohorts

**Current execution boundary — Slice 1**

Only this slice is active. It establishes the temporary execution boundary
needed to reach the first physical source migration without activating the
rest of the program.

**Active objective**

- Record the temporary freeze, active architecture runway, just-in-time
  decision boundary, and quiet-validation rule in
  [`TASK_START.md`](../../operations/TASK_START.md).
- Keep this card in progress for later separately planned slices.

**Active scope**

- Select `ARCH-02A` through `ARCH-02D`, in dependency order, as the only active
  runway after this slice.
- Freeze every other task, candidate, integration, and program family until
  the first migration is complete and the user reassesses the program.
- Require each architecture card to be planned just in time and executed in
  smaller internal phases rather than as one comprehensive pass.
- Use quiet validation immediately; retain complete output for failures or an
  explicitly requested verbose run.

**Active acceptance evidence**

- `TASK_START.md` states the temporary boundary, its exception rule, and its
  explicit sunset condition without weakening mandatory safety or context-
  expansion triggers.
- No downstream design, review, correction, migration, integration, or
  implementation decision is made by this slice.
- Existing program information below remains present and unchanged in meaning.
- Mandatory card-move links resolve, Git checks pass, and the quiet
  documentation gate passes. Computational validation is not applicable.

**Currently dead / out of scope**

Every remaining section below is preserved as a program-design record but is
currently dead and out of scope. Its content is not an active dependency,
acceptance criterion, required-context route, or authorization for this slice.
Do not execute, expand, reconcile, or routinely maintain it while the temporary
freeze is active. A later slice may reactivate only the information needed for
the then-current decision, with explicit user approval and just-in-time
inspection.

## Objective

Replace the waterfall-shaped whole-program design sequence with a reviewed
architecture runway, explicit planning cohorts, and just-in-time vertical
delivery cards.

## Why this exists

The current roadmap is iterative within each package but stage-gated across
the program: all characterization precedes all design, one integrated plan,
three whole-plan reviews, and then implementation. That protects systemic
decisions but risks stale detailed plans, speculative cards, delayed feedback,
and unnecessary context for bounded work.

## Fixed decisions

- Decide expensive-to-reverse, cross-cutting invariants early; decide local,
  reversible implementation details just in time.
- A normal bounded card completes its own inspect, plan, approve, execute,
  validate, document, integrate, and feedback loop before dependent delivery
  advances. A design card executes by delivering a reviewed decision, not by
  absorbing every downstream implementation.
- Truly coupled decision cards share a small cohort charter and reconciliation
  boundary while retaining separate deliverables. Independent inventory,
  characterization, maintenance, and documentation work may proceed alone or
  concurrently under the approved integration policy.
- `TEST-01Z` gates structural architectural mutation, not read-only inventory,
  characterization, glossary, documentation analysis, or size measurement.
- `PLAN-02Z` integrates the minimum shared architecture and creates only the
  next evidence-supported delivery tranche; it does not pre-author the entire
  Phase `03` implementation backlog.
- Architecture, reliability, and usability reviews remain independent but are
  applied at the risk boundaries they govern, with selective re-review when a
  tranche changes an assumption. Final cross-system review remains in
  `AUDIT-99`.
- Future-only cards preserve constraints without joining the current release
  gate or receiving speculative detailed plans.
- Use minimal coordination metadata rather than recreating an external project
  tracker. `Blocked by` remains reserved for genuine technological blockers.
- `docs/operations/TRANCHE.md` will own only the concise current-tranche
  selection, coordination boundary, reconciliation basis, integration/exit
  evidence requirements, links to live evidence, and next reconciliation
  trigger. `PIPELINE_PLAN.md` retains the durable roadmap, task directories
  retain lifecycle status, and `HANDOFF.md` retains live checkout, results,
  and evidence state. `TRANCHE.md` never copies those live facts.
- A tranche is coordination documentation, not a task card or authorization.
  Integration, combined validation, publication, and upstream equality are
  part of tranche completion; the next tranche is selected only after that
  closeout and its feedback review.
- `UNREFINED` and `INTEGRATION_REVIEW` are lifecycle concepts whose transition,
  authority, and exit semantics must be settled here before later
  implementation. Logical epics are orthogonal navigation groups, not
  lifecycle states, blocker substitutes, or physical status categories.
- The preserved researcher-path sidecar is the intended first substantive
  fragment-integration candidate, but it is not the synthetic exchange used to
  stabilize `CONCURRENCY-02` and is not reviewed or integrated by this card.
  This card creates only its bounded future integration card from recorded
  lane metadata and infrastructure prerequisites.
- Do not select this card before the `CONCURRENCY-01` package is complete,
  clean, pushed, and upstream-equal and `HANDOFF.md` records the user strategy
  discussion about how to leverage the new workflow as complete. This is
  approved program order, not a technological blocker edge.

## Blocked by

- None.

## Completion unblocks

- [TASK-LIFECYCLE-01](../TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md) — Partially: Defines the rolling-wave, current-tranche, and refactor-plan reconciliation semantics required by the lifecycle implementation; completed `CONCURRENCY-02` is satisfied and `DOC-GATE-01` remains required.

## Prerequisites

- Verify the published `CONCURRENCY-01` package is upstream-equal, then
  reinspect every active card and the then-current roadmap after the required
  post-concurrency strategy discussion is recorded complete in `HANDOFF.md`.
- Use the completed manual fragment protocol in
  [`CONCURRENCY-02`](../COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md)
  before selecting this card; this is approved program order rather than a
  blocker edge.
- Preserve the approved behavior-first and evidence-language gates while
  separating structural mutation from safe discovery work.

## Required context

- `PIPELINE_PLAN.md`, `TODO.md`, the Program-owned entries in `QUESTIONS.md`,
  all active task-card objectives and scopes, the file-backed-registry and
  behavior-first decisions, `TEST_BASELINE.md`, `REFACTOR_AUDIT.md`, and the
  completed concurrency policy.
- The completed fragment protocol plus the planned lifecycle and epic
  implementation boundaries in
  [`TASK-LIFECYCLE-01`](../TODO/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md)
  and [`TASK-EPIC-01`](../TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md).
- The settled architecture direction and future-only extension constraints;
  these are guardrails, not prewritten implementation plans.

## Questions owned by this card

- [`CHOICE-PROGRAM-01`](../../design/QUESTIONS.md#choice-program-01--first-planning-cohorts-and-delivery-tranche).
- [`CHOICE-LIFECYCLE-01`](../../design/QUESTIONS.md#choice-lifecycle-01--durable-integration-review-trigger).
- [`CHOICE-EPIC-01`](../../design/QUESTIONS.md#choice-epic-01--initial-logical-epic-taxonomy-and-membership).

## In scope

- Classify active cards as standalone, cohort, generated, or deferred with
  concise decision-input relationships distinct from blockers.
- Define the minimum core architecture cohort and smaller domain cohorts.
- Recast `PLAN-02Z` as a rolling integration checkpoint and revise review-card
  scopes from one whole-plan waterfall to relevant risk boundaries.
- Identify safe pre-gate inventories/characterizations and just-in-time
  implementation families without executing them.
- Define the feedback questions that update only unstarted work after every
  integrated pilot or tranche.
- Define the bounded contract for `docs/operations/TRANCHE.md`, including its
  ownership boundary, required fields, initialization, integration and exit
  criteria, reconciliation triggers, and closure/replacement behavior.
- Define implementation-ready semantics for `UNREFINED`,
  `INTEGRATION_REVIEW`, and logical epics without creating directories, moving
  cards, or changing validator behavior.
- Reconcile the current refactor plan and active card registry under the
  rolling-wave model by classifying each still-live item as retained, split,
  deferred, superseded, current-tranche, or future-tranche work without
  rewriting completed history.
- Define the exact infrastructure-ready boundary for the preserved pilot and
  create one separately selectable integration card using only its recorded
  branch, base, commit, and reserved paths; leave substantive inspection to
  that future card's own planning stage.

## Out of scope

- Implementing any migration, report, logging, intake, source-layout, or
  scientific behavior; migrating the complete dependency graph; completing
  future-only cards; or generating detailed plans for the full program.
- Implementing lifecycle directories or transitions, integration-fragment
  enforcement, validator changes, logical epic indexes, or pilot-candidate
  integration; those remain with `TASK-LIFECYCLE-01`, `CONCURRENCY-03`,
  `DOC-GATE-01`, `TASK-EPIC-01`, and the separately reviewed integration lane.

## Deliverables

- A durable rolling-wave workflow decision and concise coordination-mode
  vocabulary.
- An evidence-backed current-card classification and cohort map.
- Revised roadmap, `PLAN-02Z`, review boundaries, and first-tranche selection
  rule.
- A documented `docs/operations/TRANCHE.md` contract and initialized first
  current-tranche view that links exact existing cards without duplicating
  their status.
- Implementation-ready lifecycle and authority semantics for `UNREFINED` and
  `INTEGRATION_REVIEW`, plus logical epic identity, membership, reference, and
  index semantics.
- A reconciled `PIPELINE_PLAN.md`, priority view, and active-card map in which
  every still-live refactor item has one explicit disposition and owner.
- One unselected pilot-integration card with explicit infrastructure
  prerequisites and a read-only first planning stage; it must not incorporate
  or summarize candidate substance during this package.
- Bounded correction cards for any mixed task that must be split; completed
  cards remain unchanged.

## Acceptance evidence

- Every active card has an unambiguous coordination mode without using
  preferred order as a blocker.
- Shared architecture invariants and review boundaries are explicit, while no
  unstarted implementation card contains a stale task-specific plan.
- `TEST-01Z` still prevents unprotected structural mutation but no longer
  delays independent read-only evidence work without technical cause.
- `PLAN-02Z` can select one small delivery tranche, incorporate its feedback,
  and repeat without rewriting completed history.
- `docs/operations/TRANCHE.md` identifies exactly one current tranche, its
  objective, included cards or epics, coordination boundary, entry/exit
  evidence requirements and links to `HANDOFF.md`, integration sequence,
  reconciliation basis, and next trigger without duplicating roadmap, card-
  status, Git, results, or evidence ownership.
- Lifecycle semantics define allowed transitions, authority, entry and exit
  criteria, and prohibited uses for `UNREFINED` and `INTEGRATION_REVIEW`;
  epic semantics define stable IDs, membership, references, and index
  integrity while remaining orthogonal to lifecycle and blockers.
- Every active refactor-plan row and mutable card is reconciled as retained,
  split, deferred, superseded, current-tranche, or future-tranche work; no
  completed history is rewritten and no preferred sequence becomes a blocker.
- The preserved pilot has one unselected future integration card and remains
  substantively unreviewed; the card cannot be selected until the protocol,
  lifecycle, validator, and enforcement prerequisites recorded by this program
  are complete.
- The documentation gate and an independent architecture/reliability/usability
  consistency review pass; no executable behavior changes.

## Canonical documentation updates

- `TODO.md`, `PIPELINE_PLAN.md`, `DECISIONS.md`, `QUESTIONS.md`,
  `docs/operations/TRANCHE.md`, applicable review and planning cards,
  one concise future-direction link in task-registry guidance, `HANDOFF.md`,
  and this card. Active lifecycle rules remain unchanged until
  `TASK-LIFECYCLE-01` implements them.

## Escalation conditions

- Stop if a proposed standalone card has an unresolved shared contract, a
  cohort becomes a disguised implementation epic, a review boundary weakens a
  scientific/safety/recovery gate, or first-tranche selection requires
  speculative implementation detail.

## Completion record

Not started. Select this card only after the `CONCURRENCY-01` and completed
`CONCURRENCY-02` packages are clean, pushed, and upstream-equal, and
`HANDOFF.md` records the required post-concurrency strategy discussion as
complete. This ordering is a prerequisite, not a blocker edge; implementation
requires a separately approved task-specific plan.
