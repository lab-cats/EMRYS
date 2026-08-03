# REVIEW-UX-03H — Review RSeQC-paired-orientation evidence migration usability

## Objective

Review `MIG-03H` for scientist, operator, maintainer, automation, and recovery
continuity across every explicit Step `03` path change.

## Why this exists

The migration changes a Bash-only producer path, an interpreter-only validator
path, a submitted-job path and delegated command, demo targets, Make/coverage/
test paths, implementation provenance, and direct-final output diagnostics.
Correct code can still leave stale commands, hidden CWD-sensitive RSeQC
selection, incorrect dry-run mutation claims, biological-strandedness overclaim,
or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, native output, messages, scheduler
  policy, tool selection, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real RSeQC, scheduler,
  cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03H](../COMPLETED/REVIEW-REL-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03H](MIG-03H-migrate-collect-rseqc-paired-orientation-evidence-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make/demo, runbook/
  troubleshooting, artifact, evidence-status, and rollback journeys.

## Required context

- `MIG-03H`; Step `03` runbook/troubleshooting commands; producer and validator
  help; public CLI and SLURM characterization; Make/literal expansions;
  coverage/artifact paths; owner contract; current/future topology; and non-
  gating mechanical-orientation evidence boundary.

## Questions owned by this card

- None.

## In scope

- Explicit-`bash` producer commands; help/malformed/arbitrary-CWD journeys;
  truthful side-effect-free dry-run and CWD-sensitive `.venv`/PATH RSeQC
  selection; execute, replacement, partial/truncated-output preservation;
  explicit-interpreter validator dry-run/execute/repeat/arbitrary-CWD journeys;
  scheduler submit CWD, virtualenv, defaults/overrides, Bash `3.2`, logs and
  output checks; Make/demo/test commands; implementation and evidence
  provenance; owner findability; links; rollback; non-gating mechanical-
  orientation status; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  transaction repair, receipts/markers, BAI/sample/tool/scientific policy,
  strandedness derivation, scheduler hardening, cluster submission, dependency
  actions, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, binary selection, partial/stale output, focused tests, evidence
  status, provenance, and rollback boundaries discoverable without an alias or
  proof overclaim.

## Canonical documentation updates

- This card, `MIG-03H`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
