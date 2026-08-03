# REVIEW-REL-03D — Review `align_RNA_reads_with_STAR` migration reliability

## Objective

Challenge `MIG-03D` against producer, validator, scheduler, artifact-evidence,
coverage, fault, residue, and rollback behavior before source movement.

## Why this exists

The producer creates its output directory in dry-run and writes STAR artifacts
directly to final paths; the scheduler mutates placeholder inputs in its default
dry-run and relies on caller CWD; the validator separately publishes structural
evidence. Relocation must preserve, not normalize or approve, each success,
failure, and residue state.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer command construction, scheduler directives/modes/
  failures, validator publication behavior, artifact identity, and coverage.
- Treat old/new identical-input parity and isolated failure residue as named
  obligations; a broad passing suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03D](../COMPLETED/REVIEW-ARCH-03D-review-align-rna-reads-with-star-migration.md) — Required: reliability review needs the architecture-corrected owner and caller boundary.

## Completion unblocks

- [REVIEW-UX-03D](../TODO/REVIEW-UX-03D-review-align-rna-reads-with-star-migration.md) — Fully: public and maintainer continuity follows fixed fault and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed card and map each current
  producer, validator, job, artifact, and coverage state to one final-path
  regression owner without modifying or running executable files.

## Required context

- `MIG-03D`; producer/validator/job; direct owner tests; Step `01` mocked-job
  behavior; shared validation-report fault matrix; exact roster suites; artifact
  evidence; coverage config/tool/baseline; and applicable `TEST_BASELINE.md`
  risk rows.

## Questions owned by this card

- None.

## In scope

- Producer input/compression/command/dry-run/execute/failure states; direct
  final-path output and residue; validator dry-run/execute/repeat, parse/check,
  stable-input, lock, rollback, cleanup, and loader states; scheduler preflight,
  caller-CWD, placeholder/TMPDIR mutation, module/child failure, streams, and
  lack of post-validation; modes/hashes; artifact evidence; coverage rename;
  and commit rollback.

## Out of scope

- Correcting publication, adding locks/staging/no-clobber, removing fixture
  mutation, changing STAR or scheduler policy, changing validator checks,
  dependency work, cluster execution, scientific policy, or another owner.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and rollback state, with exact card corrections in the dated
  refactor log.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/new regression owner.
- Coverage rename proof distinguishes local fixture/mock evidence from runtime,
  scheduler, production, scientific-review, and biological evidence.

## Canonical documentation updates

- This card, `MIG-03D`, roadmap/handoff only if status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks an oracle, relocation changes command/job/
  report behavior, artifact evidence needs schema change, or coverage parity
  cannot be measured.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
