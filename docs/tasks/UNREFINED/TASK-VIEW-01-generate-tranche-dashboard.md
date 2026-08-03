# TASK-VIEW-01 — Generate a tranche tracking dashboard

State: [`UNREFINED` proposal](README.md). No dashboard, generator, lifecycle
transition, status, or evidence claim is implemented by preserving it.

## Proposal

Generate a user-facing Markdown dashboard for the current delivery tranche,
with a Mermaid overview and an ordered table linking participating stable card
identities.

## Why preserve it

Users need a quickly scannable view of active work. Reading cards, roadmap,
handoff, lane packets, and validation evidence separately creates friction, but
manually copying those facts would create another source of truth.

## Settled boundaries

- The dashboard is a deterministic projection of canonical structured inputs;
  its body is not hand-maintained.
- It owns no status, priority, order, dependency, branch, execution, evidence,
  gate, or authorization state.
- Only genuine authored blocker relationships are shown. Reverse and unblock
  views are derived.
- Branch, execution, or gate outcome appears only when a matching canonical
  machine-readable source exists. Missing or ambiguous data is shown as
  unavailable; prose is not scraped and evidence is never inferred.
- Any gate result must come from an identity-bound receipt whose validation
  subject, gate definition, environment, and inputs match. The dashboard links
  that receipt and cannot override it.
- Generated output identifies its sources and input digest and provides an
  exact refresh/check command without embedding an unrelated repository-wide
  identity that would churn after every commit.
- The selected target uses durable
  `docs/operations/tranches/<TRANCHE-ID>.md` artifacts plus one recoverable
  current pointer, not a replaceable `TRANCHE.md` dashboard.
- Generated lifecycle, dependency, epic, and tranche Markdown is committed and
  byte-for-byte check-regenerated rather than produced only on demand.

## Questions before refinement

- Which approved structured source supplies tranche membership and ordering?
- Which structured lane, execution, and receipt inputs are safe to join?
- What Mermaid layout remains readable as tranche size changes?

## Refinement inputs

- [`PROGRAM-01`](../IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
  owns accepted tranche semantics and approval envelopes.
- [`TASK-LIFECYCLE-01`](../COMPLETED/TASK-LIFECYCLE-01-implement-unrefined-and-integration-review-states.md)
  records the implemented flat lifecycle roots and transition rules.
- [`TASK-REG-01`](../TODO/TASK-REG-01-correct-task-dependency-semantics.md)
  owns the authored dependency direction and generated reverse views.
- [`TASK-EPIC-01`](../TODO/TASK-EPIC-01-implement-logical-epic-definitions-and-indexes.md)
  owns logical epic definitions and indexes.
- Recovered TODO
  [`GATE-REC-01`](../TODO/GATE-REC-01-define-machine-readable-gates-and-validation-receipts.md),
  if selected and completed, would own any machine-readable validation-receipt
  projection.

These are refinement inputs, never dependency relationships or blockers for an
`UNREFINED` proposal.

## Promotion conditions

- Complete and inspect the tranche semantics, stable card metadata, dependency
  direction, and any receipt contract that the view would consume.
- Choose the artifact model and identify every canonical input, missing-data
  behavior, failure mode, and regeneration owner.
- Convert the proposal into a complete reviewed TODO card through an explicit
  integration-owner decision.
