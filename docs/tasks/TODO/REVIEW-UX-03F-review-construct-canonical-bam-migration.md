# REVIEW-UX-03F — Review `construct_canonical_BAM` migration usability

## Objective

Review `MIG-03F` for scientist, operator, maintainer, automation, and recovery
continuity across the neutral-helper transition and every explicit Step `02`
path change.

## Why this exists

The migration changes a directly executable producer path, an interpreter-only
validator path, a submitted-job path and its delegated command, Make/coverage/
test paths, helper provenance, and recovery navigation. Correct code can still
leave incomplete commands, misleading dry-run or rollback claims, hidden
caller-CWD/module behavior, or an undiscoverable owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler policy,
  BAM/read-group semantics, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import/PYTHONPATH discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real samtools, scheduler,
  cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03F](REVIEW-REL-03F-review-construct-canonical-bam-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03F](MIG-03F-migrate-construct-canonical-bam-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper-diagnostic, and rollback journeys.

## Required context

- `MIG-03F`; Step `02` runbook/troubleshooting commands; producer and validator
  help; public CLI and SLURM characterization; Make/literal expansions;
  coverage and artifact paths; owner contract; neutral-helper diagnostic
  boundary; and current/future topology.

## Questions owned by this card

- None.

## In scope

- Direct and explicit-`bash` producer commands; help/malformed/arbitrary-CWD
  journeys; dry-run no-write guarantee; samtools resolution; execute,
  replacement, partial/ambiguous rollback preservation; interpreter-only
  validator and exact-loader diagnostics; scheduler submit/CWD/default/override/
  module/Bash `3.2` guidance; streams/logs; Make/test commands; helper and
  implementation provenance transitions; owner findability; links; rollback;
  and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  rollback repair, receipts/markers, BAM/read-group policy, scheduler hardening,
  cluster submission, dependency actions, downstream-owner commands beyond
  loader diagnostics, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported transition and healthy/failure journey has one final command,
  owned diagnostic, artifact expectation, preservation/rollback route, and
  evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run,
  replacement, ambiguous rollback, helper-integrity, focused-test, and rollback
  boundaries discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03F`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public helper import, or an unreviewed alias/package
  contract.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
