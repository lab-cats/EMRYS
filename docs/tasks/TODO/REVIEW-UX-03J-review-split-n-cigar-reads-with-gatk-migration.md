# REVIEW-UX-03J — Review SplitNCigarReads migration usability

## Objective

Review `MIG-03J` for operator, maintainer, automation, recovery, and evidence
continuity across every explicit Step `05` path change.

## Why this exists

The migration changes a Bash producer path, explicit-interpreter validator
path, submitted-job path and delegated command, Make/coverage/test/helper
paths, and implementation provenance. Correct relocation can still leave stale
commands, hidden GATK/Java/samtools/reference/temp/lock selection, incorrect
dry-run claims, unsafe retry guidance, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler or tool
  policy, reference behavior, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/fake-tool migration evidence distinct from real GATK, Java,
  samtools, scheduler, cluster, production, scientific-review, or biological
  proof.

## Blocked by

- [REVIEW-REL-03J](REVIEW-REL-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03J](MIG-03J-migrate-split-n-cigar-reads-with-gatk-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03J`; Step `05` runbook/troubleshooting commands; producer and validator
  help; public CLI and scheduler characterization; Make/literal expansions;
  coverage/artifact/helper/reference paths; owner contract; current/future
  topology; GATK/Java/samtools/reference/temp/lock diagnostics; and BAM/BAI
  transaction evidence boundary.

## Questions owned by this card

- None.

## In scope

- Explicit-Bash producer and explicit-interpreter validator root/arbitrary-CWD
  dry-run/execute/repeat journeys; GATK/Java/samtools/reference selection;
  project-storage temp and lock paths; staged publication, rollback failure,
  residue and safe preservation; scheduler submit CWD, modules, overrides,
  versions, logs, Bash `3.2`, delegation and stale outputs; Make/test commands;
  implementation/evidence provenance; owner findability; links; rollback; and
  next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/`PYTHONPATH` redesign,
  transaction repair, receipts/markers, reference or GATK policy, scheduler
  hardening, cluster submission, dependency action, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, tool/reference/temp/lock selection, rollback residue, focused tests,
  evidence status, provenance, and rollback discoverable without an alias or
  proof overclaim.

## Canonical documentation updates

- This card, `MIG-03J`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Not selected. Blocked on unselected `REVIEW-REL-03J`; no executable/test file
changed or ran.
