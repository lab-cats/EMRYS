# REVIEW-UX-03G — Review canonical-BAM-QC evidence migration usability

## Objective

Review `MIG-03G` for scientist, operator, maintainer, automation, and recovery
continuity across every explicit Step `02b` path change.

## Why this exists

The migration changes a directly executable producer path, an interpreter-only
validator path, a submitted-job path and delegated command, Make/coverage/test
paths, implementation provenance, and partial-output recovery navigation.
Correct code can still leave stale commands, a false no-write dry-run claim,
hidden `SLURM_SUBMIT_DIR`/module behavior, evidence-status overclaim, or an
undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, native output, messages, scheduler
  policy, quickcheck semantics, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real samtools, scheduler,
  cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03G](../COMPLETED/REVIEW-REL-03G-review-collect-canonical-bam-qc-evidence-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03G](../TODO/MIG-03G-migrate-collect-canonical-bam-qc-evidence-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, evidence-status, and rollback journeys.

## Required context

- `MIG-03G`; Step `02b` runbook/troubleshooting commands; producer and
  validator help; public CLI and SLURM characterization; Make/literal
  expansions; coverage/artifact paths; owner contract; current/future topology;
  and non-gating evidence boundary.

## Questions owned by this card

- None.

## In scope

- Direct and explicit-`bash` producer commands; help/malformed/arbitrary-CWD
  journeys; truthful dry-run output-directory mutation and PATH-only samtools;
  execute, replacement, partial/mixed-output preservation; explicit-interpreter
  validator dry-run/execute/repeat/arbitrary-CWD journeys; scheduler submit CWD,
  `SLURM_SUBMIT_DIR`, default/override/module/Bash `3.2` guidance; streams/logs;
  Make/test commands; implementation and evidence provenance; owner
  findability; links; rollback; non-gating status; and next-safe-action
  instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  transaction repair, receipts/markers, quickcheck/BAI/sample policy, scheduler
  hardening, cluster submission, dependency actions, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  mutation, partial/mixed output, focused tests, evidence status, provenance,
  and rollback boundaries discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03G`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Selected from clean, published, local/upstream/live-remote-equal reliability-
review checkpoint `56bac4242478e95376aa6721431d1339769b1ffc`. This is a
read-only independent-in-time adversarial pass by the same campaign agent;
independent authorship is not claimed. No executable/test mutation or
computational test is part of review selection.
