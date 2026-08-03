# REVIEW-UX-03I — Review MarkDuplicates migration usability

## Objective

Review `MIG-03I` for operator, maintainer, automation, recovery, and evidence
continuity across every explicit Step `04` path change.

## Why this exists

The migration changes a Bash-only producer path, an interpreter-only validator
path, a submitted-job path and delegated command, Make/coverage/test/helper
paths, implementation provenance, and direct-final multi-output diagnostics.
Correct code can still leave stale commands, hidden Picard/Java/samtools/temp
selection, incorrect dry-run claims, unsafe retry guidance, or an
undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, native outputs, messages, scheduler
  policy, tool selection, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real Picard, Java,
  samtools, scheduler, cluster, production, scientific-review, or biological
  proof.

## Blocked by

- [REVIEW-REL-03I](../COMPLETED/REVIEW-REL-03I-review-mark-bam-duplicates-with-picard-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03I](MIG-03I-migrate-mark-bam-duplicates-with-picard-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03I`; Step `04` runbook/troubleshooting commands; producer and validator
  help; public CLI and SLURM characterization; Make/literal expansions;
  coverage/artifact/helper paths; owner contract; current/future topology;
  Java/Picard/samtools/`TMPDIR` diagnostics; and multi-output evidence boundary.

## Questions owned by this card

- None.

## In scope

- Explicit-Bash producer commands; help/malformed/arbitrary-CWD journeys;
  truthful side-effect-free dry-run; Picard jar, Java, samtools, and `TMPDIR`
  selection; execute, silent replacement, partial/empty/cross-attempt output
  preservation; explicit-interpreter validator dry-run/execute/repeat/
  arbitrary-CWD journeys; scheduler submit CWD, modules, overrides, actual Java
  version, Bash `3.2`, logs and output checks; Make/test commands;
  implementation/evidence provenance; owner findability; links; rollback; and
  next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  transaction repair, receipts/markers, duplicate/sample/library/platform/tool
  policy, scheduler hardening, cluster submission, dependency actions, or
  future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, tool/temp selection, partial/mixed/stale outputs, focused tests,
  evidence status, provenance, and rollback discoverable without an alias or
  proof overclaim.

## Canonical documentation updates

- This card, `MIG-03I`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
