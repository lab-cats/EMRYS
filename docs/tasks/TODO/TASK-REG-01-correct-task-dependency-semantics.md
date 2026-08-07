# TASK-REG-01 — Correct task-dependency semantics

## Objective

Redefine card dependency fields as genuine technological blockers and migrate
the active registry and its validator away from execution-order metadata.

## Why this exists

The first task-registry model uses reciprocal dependency edges to encode much
of the preferred program sequence. That makes a recommendation look like a
technical impossibility, requires completed historical cards to be rewritten
when live plans change, and obscures which tasks truly cannot make meaningful
progress without another task's output.

## Fixed decisions

- `Blocked by` is reserved for a card whose incomplete technical output makes
  meaningful progress on the target impossible; preference or chronology is
  not a blocker.
- Preferred order belongs in `PIPELINE_PLAN.md` or the short `TODO.md` view.
  Repository state, approvals, environment, and other non-card conditions
  belong under `Prerequisites`.
- `Completion unblocks` is the reciprocal view of genuine blocker removal.
  `Partially` means one of multiple genuine blockers was removed, not that the
  source merely supplied useful context.
- Completed cards are immutable historical records apart from necessary link
  repair or factual correction. Live dependency maintenance must not rewrite
  them solely to preserve reciprocity.
- Active references to completed work are resolved history, not live blockers;
  the validator must distinguish active edges from historical records.
- Every existing active edge requires evidence-based classification. Do not
  mechanically preserve or delete the current graph.
- Keep preferred order, scope expansion, authority expansion, and blockers
  distinct. An operational blocker in a plan or handoff may be a missing
  input, decision, capability, or evidence, but a card's `Blocked by` field is
  limited to an unavailable technological output that prevents meaningful
  progress.
- The selected target uses stable card IDs and one authored forward
  technological-dependency direction with mechanically derived reverse views.
  Current reciprocal card fields remain canonical until a separately approved
  atomic migration passes parity and final validation.
- Blocker meaning remains independent of whether current lifecycle directories
  or the selected permanent-path model stores the authored edge.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Recount and inventory every live card, status, blocker edge, unblock edge,
  and validator rule at the selected revision.
- Inspect the current program-order owners before moving sequence information
  out of card metadata.

## Required context

- [`../README.md`](../README.md), the file-backed-registry decision in
  [`DECISIONS.md`](../../design/DECISIONS.md#govern-future-work-through-a-file-backed-task-registry),
  the authoritative sequence in
  [`PIPELINE_PLAN.md`](../../design/PIPELINE_PLAN.md), all task cards, and the
  documentation-validator implementation and tests that exist when this card
  is selected.

## Questions owned by this card

- None. The core semantic decision is fixed; task-specific planning owns only
  the exact migration mechanics and test cases discovered from the live graph.

## In scope

- Inventory and classify all active blocker and unblock relationships.
- Update active cards, task-registry instructions, durable rationale, and
  roadmap sequence without rewriting completed history.
- Update validator behavior and focused tests for active-edge reciprocity,
  completed-card history, stale resolved blockers, self-dependencies, and
  genuine cycles.
- Preserve any true technical blockers with concise evidence-oriented reasons.

## Out of scope

- Executing or reprioritizing the work described by migrated cards, rewriting
  completed-card narratives for cosmetic consistency, or changing NORAD
  workflow, scientific, report, schema, or evidence behavior.

## Deliverables

- A documented blocker definition and field-placement guide.
- An evidence-backed before/after edge inventory and migrated active registry.
- One stable-ID-keyed authored dependency direction plus deterministic full or
  partial reverse views. Reject unknown IDs, self-dependencies, genuine
  cycles, and active references that merely restate completed history.
- Include the historical `DOC-REF-02` and `DOC-PIPE-04` edges to completed
  `DOC-IA-01` and `ARCH-02B` in the migration inventory. Classify only
  still-pending edges as preserve, remove-with-reason, or sequence-only
  relocation; do not rewrite completed records or turn the corrected
  DOC-REF-before-DOC-PIPE integration lineage into a blocker.
- Tested documentation-validator rules that do not require completed-card
  mutation to maintain live consistency.
- Roadmap or TODO ordering for every removed sequence-only edge that still
  represents an intentional recommendation.

## Acceptance evidence

- Every remaining active blocker identifies a concrete unavailable technical
  output whose absence prevents meaningful progress.
- No active card uses a blocker field merely to encode preferred order,
  approval, Git state, environment state, or useful context.
- Completed cards remain unchanged except for separately justified link repair
  or factual correction.
- Focused validator tests, the complete documentation gate, and Git diff checks
  pass.

## Canonical documentation updates

- `docs/tasks/README.md`, `DECISIONS.md`, `PIPELINE_PLAN.md`, `TODO.md`,
  `RUNBOOK.md` or its extracted validator owner, `HANDOFF.md`, and all affected
  active task cards.

## Escalation conditions

- Stop if an edge cannot be distinguished from scientific policy, an active
  card contradicts its canonical roadmap owner, or preserving validation
  would require rewriting completed history without factual cause.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
