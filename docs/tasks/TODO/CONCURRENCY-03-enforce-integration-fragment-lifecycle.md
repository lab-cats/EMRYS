# CONCURRENCY-03 — Enforce integration-fragment lifecycle

## Objective

Add focused, tested structural enforcement for the stabilized integration-
fragment contract while preserving human ownership of semantic review and
canonical composition.

## Why this exists

A manual protocol can establish useful semantics, but repeated sidecar work
needs deterministic checks for malformed identity, stale provenance,
unresolvable destinations, and fragments accidentally surviving canonical
publication. Enforcement must follow the observed protocol rather than encode
speculative rules or automate integration decisions.

## Fixed decisions

- Extend the standalone, tested documentation validator produced by
  [`DOC-GATE-01`](../IN_PROGRESS/DOC-GATE-01-extract-documentation-validator.md); do not add
  another embedded runbook program.
- Reuse stable parsing or checks from `scripts/git_orchestration/` when that
  avoids duplication, but do not turn the operator helpers into a central
  dispatcher or semantic integration engine.
- Characterize accepted fragment examples and observed failures before fixing
  the validation contract.
- Candidate and final-canonical validation use an explicit declared mode or
  command surface. Never infer authority or publication state from a branch
  name, worktree path, or agent identity.
- Structural checks may validate identity, provenance, targets, required
  fields, duplicate names, and permitted claims. Humans retain responsibility
  for scientific meaning, conflict resolution, wording, and whether an update
  belongs in a canonical owner.
- Validation does not compose documents, move cards, accept candidates, close
  lanes, delete branches, or authorize publication.

## Blocked by

- [DOC-GATE-01](../IN_PROGRESS/DOC-GATE-01-extract-documentation-validator.md) — Required: fragment rules need the extracted, behavior-locked validator and focused test harness.

## Completion unblocks

- None.

## Prerequisites

- Inspect the synthetic manual fragment exchange completed by
  [`CONCURRENCY-02`](../COMPLETED/CONCURRENCY-02-define-integration-fragment-protocol.md)
  plus any retained malformed or stale examples before approving exact
  validation behavior. The original pilot and consumed consolidated-recovery
  source are not required evidence for this card and must not be reopened or
  treated as pending integration work.
- Reinspect the extracted validator's public command, fixture conventions, and
  current accepted repository states at the selected revision.

## Required context

- The completed fragment protocol, its first inspected handoff evidence,
  [`DOC-GATE-01`](../IN_PROGRESS/DOC-GATE-01-extract-documentation-validator.md), the current
  documentation-validator implementation and tests, and the fragment-related
  operator procedure and linked helpers in
  [`RUNBOOK.md`](../../operations/RUNBOOK.md).
- Card inbound-link and orphan rules in [`../README.md`](../README.md), because
  a fragment backlink must not make an otherwise disconnected card appear
  properly integrated.

## Questions owned by this card

- None. Task-specific planning may choose the smallest explicit command or mode
  compatible with the implemented validator without reopening fragment
  semantics.

## In scope

- Add independent valid, invalid, stale, duplicate, malformed-target,
  prohibited-claim, candidate-mode, and final-mode fixtures and tests.
- Validate required fragment identity, base/provenance, target owner and
  anchor, coupling, requested-update, assumption, conflict, and disposition
  structure established by the completed protocol.
- Reject a canonical publication state that retains a pending fragment other
  than `docs/fragments/README.md`.
- Ensure fragment links cannot be the sole inbound reference satisfying task-
  card reachability.
- Update the supported validator invocation and concise troubleshooting only
  for behavior implemented by this card.

## Out of scope

- Semantic correctness of requested documentation changes; automatic
  integration or conflict resolution; task-lifecycle or epic-path support;
  pilot-card review; repository workflow behavior; or scientific/evidence
  promotion.

## Deliverables

- Tested fragment-validation behavior in the extracted documentation
  validator.
- Independent fixtures covering candidate and final-canonical states.
- Concise supported commands and actionable diagnostics for every enforced
  failure class.

## Acceptance evidence

- Valid candidate fragments pass only in the declared candidate context, while
  malformed, stale, duplicated, or authority-claiming fragments fail with
  actionable diagnostics.
- Final-canonical validation fails when an unconsumed fragment survives and
  passes when only the protocol README remains.
- Existing documentation-validator behavior remains covered and unchanged
  outside the newly approved fragment rules.
- Focused tests, the complete applicable documentation gate, Git diff checks,
  and independent validation/ownership review pass.

## Canonical documentation updates

- The extracted validator owner and tests, `RUNBOOK.md`,
  `docs/fragments/README.md`, `CONCURRENT_WORK.md`, `TROUBLESHOOTING.md`,
  `PIPELINE_PLAN.md`, `TODO.md`, `HANDOFF.md`, and this card.

## Escalation conditions

- Stop if enforcement requires semantic document composition, branch-name
  inference, a second validator implementation, destructive cleanup, or a rule
  that rejects previously accepted non-fragment documentation unexpectedly.

## Completion record

Not started. Select this card for read-only planning; implementation requires
a separately approved task-specific plan.
