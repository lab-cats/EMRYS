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
- When this frozen remainder is explicitly reactivated, tranche contracts must
  carry or link the approved objective and included cards; semantic planning
  category and validation impact as two independent fields; exact base and
  lane identities; write sets; allowed mutations and commits; external-
  authority boundary; exclusions; unresolved choices; stop conditions; and
  final evidence boundary. Routine in-envelope transitions need no renewed
  approval, while scope or authority expansion requires deferral or revised
  approval. Preferred order remains distinct from technological blockers.
- The selected target uses durable
  `docs/operations/tranches/<TRANCHE-ID>.md` artifacts plus one recoverable
  current pointer, with committed, deterministic, byte-for-byte check-
  regenerated projections. `PIPELINE_PLAN.md` retains the durable roadmap,
  task metadata retains lifecycle status, and `HANDOFF.md` retains live
  checkout, results, and evidence state. No tranche view copies those facts.
  The current single-file `TRANCHE.md` concept remains only pre-implementation
  design context until a separately approved migration defines and validates
  the artifact and pointer contracts.
- A tranche is coordination documentation, not a task card or authorization.
  Integration, combined validation, publication, and upstream equality are
  part of tranche completion; the next tranche is selected only after that
  closeout and its feedback review.
- `UNREFINED` is an authorized proposal-intake classification outside
  actionable task status, with fixed nonselectability and integration-owner
  promotion authority. `TASK-LIFECYCLE-01` owns its remaining validator and
  transition support. This program owns only tranche/handoff interaction with
  the future `INTEGRATION_REVIEW` concept. The intake location does not
  reactivate this card. Logical epics are orthogonal navigation groups, not
  lifecycle states, blocker substitutes, or physical status categories.
- The separately authorized consolidated recovery integration supersedes the
  earlier plan to create a future researcher-path integration card. It reviews
  and routes the frozen source without making this program card the owner of
  any recovered proposal or selecting its implementation.
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
- Define the bounded contract for durable per-tranche files plus one
  recoverable current pointer, including ownership, required fields,
  deterministic committed-view checking, initialization, integration and exit
  criteria, reconciliation triggers, and closure behavior. The superseded
  single-file `TRANCHE.md` concept is not an implementation target.
- Reconcile the selected future registry target: permanent ID-only canonical
  card paths with structured lifecycle metadata; one authored technological-
  dependency direction; and committed, byte-for-byte check-regenerated
  lifecycle, dependency, epic, and tranche views. Preserve the current path
  and registry authority until an atomic migration passes parity and final
  validation; decide lifecycle/dependency/minimum-epic cutover order, epic
  cardinality and taxonomy, and the single owner of tranche membership/order.
- Preserve the fixed UNREFINED prohibitions/promotion boundary while defining
  program-specific handoff semantics for `INTEGRATION_REVIEW` and logical epics
  without moving actionable cards or changing validator behavior.
- Reconcile the current refactor plan and active card registry under the
  rolling-wave model by classifying each still-live item as retained, split,
  deferred, superseded, current-tranche, or future-tranche work without
  rewriting completed history.
- Record that the separately authorized consolidated recovery superseded the
  planned pilot-integration card, and route each recovered TODO or UNREFINED
  proposal to its own current owner without duplicating integration work here.

## Out of scope

- Implementing any migration, report, logging, intake, source-layout, or
  scientific behavior; migrating the complete dependency graph; completing
  future-only cards; or generating detailed plans for the full program.
- Implementing lifecycle transitions or registry migration, integration-
  fragment enforcement, validator changes, generated views, logical epic
  indexes, or recovered pilot cards; those remain with `TASK-LIFECYCLE-01`,
  `TASK-REG-01`, `CONCURRENCY-03`, `DOC-GATE-01`, `TASK-EPIC-01`, and the
  separately selected card owners.

## Deliverables

- A durable rolling-wave workflow decision and concise coordination-mode
  vocabulary.
- An evidence-backed current-card classification and cohort map.
- Revised roadmap, `PLAN-02Z`, review boundaries, and first-tranche selection
  rule.
- A documented durable per-tranche artifact and recoverable-current-pointer
  contract, plus an initialized first current-tranche projection that links
  exact existing cards without duplicating their status.
- Program-ready interaction with the fixed UNREFINED boundary and future
  `INTEGRATION_REVIEW`, plus logical epic identity, membership, reference, and
  index semantics.
- A reconciled `PIPELINE_PLAN.md`, priority view, and active-card map in which
  every still-live refactor item has one explicit disposition and owner.
- One durable route to the completed recovery record and the unselected
  recovered owners, with no duplicate pilot-integration card or transfer of
  their scope into this program.
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
- The recoverable current pointer identifies exactly one durable tranche, its
  objective, included cards or epics, coordination boundary, entry/exit
  evidence requirements and links to `HANDOFF.md`, integration sequence,
  reconciliation basis, and next trigger without duplicating roadmap, card-
  status, Git, results, or evidence ownership.
- Program handoff semantics preserve UNREFINED's fixed nonselectability and
  promotion authority while defining entry and exit criteria for future
  `INTEGRATION_REVIEW`; epic semantics define stable IDs, membership,
  references, and index integrity while remaining orthogonal to lifecycle and
  blockers.
- Every active refactor-plan row and mutable card is reconciled as retained,
  split, deferred, superseded, current-tranche, or future-tranche work; no
  completed history is rewritten and no preferred sequence becomes a blocker.
- The separately authorized recovery integration reviews and routes the pilot
  proposals without selecting or implementing them. Any materialized TODO card
  still requires its own task-specific planning and applicable then-current
  prerequisites; UNREFINED files remain nonselectable and nonblocking.
- The documentation gate and an independent architecture/reliability/usability
  consistency review pass; no executable behavior changes.

## Canonical documentation updates

- `TODO.md`, `PIPELINE_PLAN.md`, `DECISIONS.md`, `QUESTIONS.md`,
  future durable per-tranche artifacts/current pointer, applicable review and
  planning cards, one concise future-direction link in task-registry guidance,
  `HANDOFF.md`, and this card. Existing UNREFINED rules remain authoritative;
  other lifecycle mechanics wait for `TASK-LIFECYCLE-01`.

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
