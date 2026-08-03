# REVIEW-REL-03F — Review `construct_canonical_BAM` migration reliability

## Objective

Challenge `MIG-03F` against neutral-helper, producer, validator, scheduler,
artifact, coverage, fault, residue, and rollback behavior before source
movement.

## Why this exists

The producer replaces a canonical BAM/BAI pair through staged validation,
backup, two final moves, final validation, and best-effort rollback. A failure
inside rollback can lose recovery evidence without a receipt or marker. The
validator is intentionally less strict than the producer, and the proposed
helper extraction adds three exact-loader fault surfaces. Relocation must
preserve and characterize each state without approving it.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer commands/state machine, scheduler directives/modes/
  failures, validator publication/asymmetries, helper bytes/exceptions, artifact
  identity, and coverage policy.
- Treat old/helper/final identical-input parity, exact-loader faults, rollback-
  failure residue, and stable-input evidence as named obligations; a broad
  passing suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03F](../IN_PROGRESS/REVIEW-ARCH-03F-review-construct-canonical-bam-migration.md) — Required: reliability review needs the architecture-corrected helper, owner, caller, and slice boundary.

## Completion unblocks

- [REVIEW-UX-03F](REVIEW-UX-03F-review-construct-canonical-bam-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed cards and map every helper,
  producer, validator, job, artifact, coverage, and recovery state to one named
  regression owner without modifying or running executable files.

## Required context

- `MIG-03F`; Step `02` producer/validator/job and direct tests; Step `04`/`05`
  helper uses and direct tests; central scheduler matrix; shared validation-
  report faults; proposed neutral helper/loader contract; roster and public-CLI
  suites; artifact evidence; coverage tool/baseline; and applicable
  `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled fault can freeze the current failure-inside-rollback state
  without changing cleanup, and exactly which final/backup/lock/temp bytes must
  be preserved as ambiguous recovery evidence?
- What loader fault matrix is required once for the neutral owner and at each
  distinct caller depth without duplicating an entire framework across Step
  `02`, Step `04`, and Step `05` tests?

## In scope

- Helper argument/result/header parity and cache/spec/load failures; producer
  CLI/dry-run/execute/staging/validation/pair-state/lock/temp/backup/publish/
  rollback/cleanup/signal/stream states; validator tool/header/count, dry-run/
  execute/repeat, stable-input, publication, and documented asymmetries;
  scheduler CWD/module/directory/Bash `3.2`/child/output/stream states; modes,
  hashes, artifact evidence, coverage extraction/rename, and commit rollback.

## Out of scope

- Correcting rollback, adding receipts/recovery markers, changing replacement
  or BAM/read-group policy, tightening the validator to producer semantics,
  moving downstream owners, scheduler hardening, dependency work, real
  samtools/SLURM/production execution, or scientific policy.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and rollback state, with exact card corrections and dated
  audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named pre-extraction/helper/final-path regression owner.
- Coverage and parity distinguish local fixture/mock evidence from real
  samtools, scheduler, cluster, production, scientific-review, and biological
  evidence.

## Canonical documentation updates

- This card, `MIG-03F`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks a safe oracle, extraction changes helper
  results/exceptions, relocation changes producer/job/report behavior, artifact
  evidence needs schema change, or coverage and exact-loader parity cannot be
  measured.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
