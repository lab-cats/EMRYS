# PROGRAM-01 — Define rolling-wave planning and coordination cohorts

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
- Do not select this card before `CONCURRENCY-01` is completed and the user has
  discussed how to leverage the new workflow; this is approved program order,
  not a technological blocker edge.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Reinspect every active card and the then-current roadmap after the required
  post-concurrency strategy discussion.
- Preserve the approved behavior-first and evidence-language gates while
  separating structural mutation from safe discovery work.

## Required context

- `PIPELINE_PLAN.md`, `TODO.md`, all active task-card objectives and scopes,
  the file-backed-registry and behavior-first decisions, `TEST_BASELINE.md`,
  `REFACTOR_AUDIT.md`, and the completed concurrency policy.
- The settled architecture direction and future-only extension constraints;
  these are guardrails, not prewritten implementation plans.

## Questions owned by this card

- Exact membership and shared acceptance boundary of each planning cohort,
  based on the live card inventory and post-concurrency strategy discussion.
- The first low-risk vertical migration pilot and the smallest initial
  evidence-supported delivery tranche.

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

## Out of scope

- Implementing any migration, report, logging, intake, source-layout, or
  scientific behavior; migrating the complete dependency graph; completing
  future-only cards; or generating detailed plans for the full program.

## Deliverables

- A durable rolling-wave workflow decision and concise coordination-mode
  vocabulary.
- An evidence-backed current-card classification and cohort map.
- Revised roadmap, `PLAN-02Z`, review boundaries, and first-tranche selection
  rule.
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
- The documentation gate and an independent architecture/reliability/usability
  consistency review pass; no executable behavior changes.

## Canonical documentation updates

- `TODO.md`, `PIPELINE_PLAN.md`, `DECISIONS.md`, applicable review and planning
  cards, task-registry guidance, `HANDOFF.md`, and this card.

## Escalation conditions

- Stop if a proposed standalone card has an unresolved shared contract, a
  cohort becomes a disguised implementation epic, a review boundary weakens a
  scientific/safety/recovery gate, or first-tranche selection requires
  speculative implementation detail.

## Completion record

Not started. Select this card only after the required post-concurrency strategy
discussion; implementation requires a separately approved task-specific plan.
