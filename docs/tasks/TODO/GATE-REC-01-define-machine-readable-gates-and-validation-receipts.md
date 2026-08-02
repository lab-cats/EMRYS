# GATE-REC-01 — Define machine-readable gates and validation receipts

## Objective

Define and implement a versioned local gate catalog and reusable validation
receipts keyed to the exact executable and test-affecting state they validate.

## Why this exists

Current gate evidence is conveyed through commands, logs, summaries, and Git
comparison. A documentation-only descendant may reuse a computational result,
but proving equivalence is manual. A commit ID, pass total, or remembered result
cannot identify the gate definition, command, inputs, environment, and exact
validation subject.

## Fixed decisions

- A versioned gate catalog declares each stable gate ID and version,
  applicability, supported invocation, subject classification, required
  environment and inputs, constituent checks, and result fields.
- A receipt records its schema and gate-definition digest, exact command and
  working directory, Git provenance, content-derived validation-subject
  manifest and digest, relevant environment and toolchain identity, declared
  input or fixture hashes, timestamps, per-check results and exits, overall
  result, and required log or evidence hashes or locations.
- The content-derived validation-subject digest is the reuse key. Commit and
  tree identity are provenance, not sufficient equivalence by themselves.
- Reuse requires a matching gate definition and subject digest, compatible
  environment, identical declared inputs, and a complete successful result.
  Relevant dirty or unrepresented state, executable or test-affecting change,
  missing evidence, or a changed gate definition invalidates reuse.
- Final documentation validation still runs on every integrated documentation
  tree. A receipt never promotes runtime, cluster, scientific-review, or
  biological state and never grants execution, integration, push, or
  publication authority.
- Preserve current command selection, assertions, thresholds, failure output,
  cancellation and cleanup, coverage, and evidence boundaries. This card
  records and identifies gates; it does not redesign them.
- Existing result summaries, logs, test totals, and commit identities are not
  conforming receipts unless they satisfy the reviewed catalog, identity,
  input, environment, completeness, and evidence contract.
- Keep the implementation small and repository-local. Do not build a generic
  orchestration framework, external service, plugin, or skill.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Inventory the then-current complete computational gate, documentation gate,
  focused-check conventions, machine-readable result output, environment
  profiles, and evidence-reuse procedure at one selected revision.
- Decide an ignored or tracked receipt-location and retention policy without
  copying current results into canonical prose or risking private data.
- Sequence documentation-gate incorporation and final cross-gate closeout
  after [`DOC-GATE-01`](DOC-GATE-01-extract-documentation-validator.md)
  supplies an accepted extracted command and separable result boundary. This
  is readiness and integration order, not a technological blocker: catalog
  schema, computational-gate inventory, subject hashing, and emitter or
  verifier work can proceed meaningfully first.

## Required context

- Applicable validation and evidence rationale in
  [`DECISIONS.md`](../../design/DECISIONS.md), task-start validation-impact
  routing in [`TASK_START.md`](../../operations/TASK_START.md), and the local
  validation and integration commands in
  [`RUNBOOK.md`](../../operations/RUNBOOK.md).
- [`CONCURRENT_WORK.md`](../../operations/CONCURRENT_WORK.md), the current
  [`DOC-GATE-01`](DOC-GATE-01-extract-documentation-validator.md) contract and
  accepted state at selection, and every then-current gate script,
  configuration, consumer, and test.
- [`TEST_BASELINE.md`](../../design/TEST_BASELINE.md) for the selected
  revision's observed validation-output and evidence-reuse boundaries.
- The recovered workflow-friction rationale routed through this card and any
  accepted integration-time decision updates; do not treat an unpublished
  source candidate as canonical implementation evidence.

## Questions owned by this card

- [`CHOICE-GATE-REC-01`](../../design/QUESTIONS.md#choice-gate-rec-01--validation-receipt-contract-and-storage)
  owns the receipt schema, storage, retention, compatibility, result-extension,
  and subject-classification choices. Option selection is deliberately deferred
  until before schema or persistence implementation. That deferral does not
  block recovery reintegration, corrected `DOC-GATE-01` work, or non-receipt
  task views, and it grants no implementation authority.

## In scope

- Characterize each current gate's applicability, command, inputs, subject
  paths, environment, constituent results, failure behavior, and evidence
  boundary.
- Define and version a minimal catalog and receipt schema with deterministic
  subject-manifest hashing and explicit invalidation rules.
- Implement a local emitter, verifier, and reuse check with independent
  fixtures for documentation-only descendants, executable changes, gate
  changes, environment or input mismatch, relevant dirty and untracked state,
  failed or incomplete receipts, and tampered evidence.
- Integrate concise supported invocations and receipt interpretation into the
  runbook and concurrent handoff process.

## Out of scope

- Changing test selection, assertions, coverage thresholds, scientific or
  biological policy, runtime or cluster promotion, dependency restoration,
  publication authority, task lifecycle, external receipt storage, generic
  workflow orchestration, or automatic execution based only on a receipt.

## Deliverables

- A reviewed machine-readable gate catalog and validation-receipt schema.
- A small repository-local emitter, verifier, and deterministic subject-
  manifest implementation with focused independent tests.
- Runbook and concurrent-handoff integration that retains human-readable
  failure diagnosis and exact evidence boundaries.

## Acceptance evidence

- Identical executable and test-affecting state can reuse a matching successful
  receipt across a documentation-only descendant.
- Every relevant byte, gate-definition, environment, declared input, failure,
  incompleteness, missing evidence, dirty-state, or tampering change is rejected
  deterministically.
- Final documentation validation still runs, and no receipt promotes evidence
  state or grants execution, integration, or publication authority.
- Focused independent tests, one complete applicable computational gate, the
  documentation gate, Git diff checks, and semantic evidence-boundary review
  pass on the exact final state.

## Canonical documentation updates

- `DECISIONS.md`, `TASK_START.md`, `CONCURRENT_WORK.md`, `RUNBOOK.md`, task-
  registry guidance, applicable gate documentation, and this card.

## Escalation conditions

- Stop if subject classification cannot conservatively include every
  executable or test-affecting consumer, environment compatibility would be
  guessed, current gate behavior would change silently, or receipt persistence
  risks credentials, private data, logs, production artifacts, or misleading
  evidence promotion.

## Completion record

Not started. This candidate preserves an explicitly classified TODO proposal;
it authorizes neither implementation nor use of unpublished validator work.
