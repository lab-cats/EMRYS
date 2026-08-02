# DOC-TASK-SCAN-01 — Scan documentation for unowned future commitments

## Objective

Perform one reviewed, repository-wide documentation scan that maps explicit
future commitments to existing owners or gives genuine unowned work one bounded
disposition.

## Why this exists

Semantically unique obligations can remain stranded in prose and be lost
during consolidation. Scanning before ownership, retention, and stale-content
rules are settled would instead manufacture duplicate or obsolete tasks from
historical narrative.

## Fixed decisions

- Search matches are evidence for human review, never authority to create,
  select, prioritize, promote, or complete work automatically.
- Every candidate receives one reviewed disposition: covered by an existing
  card, existing-card amendment, new actionable card, `UNREFINED`, open choice,
  absorbed, stale or superseded, ambiguous or deferred, or rejected with a
  reason.
- The scan owns repository-wide discovery and traceability. Proposed intake
  mechanisms may consume its reviewed result but do not run or own the scan.
- Unique conceptual, operational, architectural, scientific, evidence,
  recovery, and legacy-behavior meaning must remain discoverable. Repeated
  status, generated counts, and obsolete mutable detail do not become cards.
- A concrete later documentation-consolidation card becomes a hard dependency
  only when its missing output genuinely prevents safe interpretation. Family,
  wildcard, placeholder, and sequence-only dependencies are prohibited.
- Completed [`DOC-IA-01`](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md)
  supplies the ownership, retention, audience, source-to-destination, and
  stale-content rules required to interpret findings safely. Its accepted
  output is prerequisite context, so no blocker or reciprocal dependency edge
  is required.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Use the completed `DOC-IA-01` output as prerequisite context when defining
  the scan; do not install a new dependency edge to the completed card.
- Verify that the approved documentation cleanup needed to determine the
  current corpus is complete; this is a repository-state prerequisite, not a
  placeholder dependency.
- Require a clean canonical checkout and a passing complete documentation gate
  at the exact revision to be scanned.
- Require an internally consistent current task registry and documentation
  ownership and retention ledger.

## Required context

- Completed [`DOC-IA-01`](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md)
  and the resulting ownership, audience, retention, source-to-destination, and
  stale-content rules.
- Current canonical Markdown and Mermaid sources, task registry, roadmap,
  decisions, open questions, current and target architecture, and
  documentation-validator behavior at the selected revision.
- Existing card scopes, loaded through targeted ID and concept searches before
  full semantic inspection of unmatched commitments.
- [`TASK_START.md`](../../operations/TASK_START.md) and the documentation-impact
  route that applies at the selected revision.

## Questions owned by this card

- None. Task-specific planning may choose exact search and report mechanics
  from the then-current corpus without weakening the review boundary.

## In scope

- Inventory explicit prospective commitments, promised follow-ups, migrations,
  audits, reviews, deferred corrections, and named future capabilities in the
  authorized current documentation corpus.
- Map each commitment to one existing owner or one reviewed disposition with
  exact source location and rationale.
- Distinguish durable commitments from examples, historical narrative,
  superseded plans, open choices, non-card conditions, and speculative ideas.
- Draft only bounded cards or amendments explicitly authorized from the
  reviewed gap list.
- Record false-positive and ambiguity classes so later scans do not repeat the
  same mistakes.

## Out of scope

- Performing documentation cleanup; opening separately restricted dormant
  sources; implementing discovered work; changing priority; selecting or
  completing cards; resolving scientific or architectural questions; or
  creating tasks directly from search output.
- Inventing consolidation cards, owners, or dependency edges whose required
  output is not yet concrete.

## Deliverables

- A revision-bound, source-linked commitment-to-owner traceability matrix.
- A reviewed gap report with explicit covered, amend, actionable,
  `UNREFINED`, choice, absorbed, stale, ambiguous, and rejected dispositions.
- Separately reviewable card or amendment drafts only for approved,
  semantically unique gaps.
- A concise record of corpus boundaries, false-positive classes, unresolved
  ambiguities, and exact follow-up authority.

## Acceptance evidence

- Every explicit future commitment in the inspected corpus maps to a current
  owner or one reviewed non-silent disposition.
- No new card duplicates an existing scope, derives only from stale prose, or
  gains selection or priority through the scan.
- Every installed blocker names one concrete card whose unavailable output
  genuinely prevents the scan; no wildcard or placeholder dependency exists.
- Git diff checks, targeted semantic review, and the complete documentation
  gate pass on the exact final documentation tree. Computational suites remain
  not applicable unless an approved diff changes an executable consumer.

## Canonical documentation updates

- The task registry and only those canonical ownership, roadmap, decision, or
  question owners affected by accepted findings.
- Current state, priority, and completion owners change only under separate
  authority and when factually required.

## Escalation conditions

- Stop when source ownership is contradictory, semantic uniqueness cannot be
  determined, a finding changes scientific or evidence meaning, a necessary
  cleanup output lacks a concrete owner, or resolving a gap would expand into
  executing the discovered work.

## Completion record

Not started. This candidate preserves an already-classified TODO proposal; it
does not select itself or authorize planning or implementation.
