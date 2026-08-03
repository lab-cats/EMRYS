# REVIEW-REL-03I — Review MarkDuplicates migration reliability

## Objective

Challenge `MIG-03I` against producer, validator, scheduler, artifact, coverage,
direct-final multi-output publication, cross-attempt residue, tool/runtime
selection, stable-input, and rollback behavior before source movement.

## Why this exists

Picard writes BAM and metrics directly to final paths before quickcheck and
indexing, with no lock, staging, no-clobber rule, stable-input recheck, receipt,
or rollback. Picard, quickcheck, index, or final-check failure can combine new,
partial, empty, and prior BAM/BAI/metrics bytes. The wrapper adds module, Java,
temp, Bash-version, and stale-output states. Relocation must preserve and
characterize them without approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer commands/serialization, validator report semantics,
  scheduler directives/tool modes/failures, neutral-helper identities, artifact
  identity, and coverage policy.
- Treat identical-input old/final parity, predecessor-bearing child failures,
  multi-output residue, stable-input evidence, and exact streams/exits as named
  obligations; a broad passing suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03I](../COMPLETED/REVIEW-ARCH-03I-review-mark-bam-duplicates-with-picard-migration.md) — Required: reliability review needs the architecture-corrected owner, caller, helper, artifact, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03I](../TODO/REVIEW-UX-03I-review-mark-bam-duplicates-with-picard-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed cards and map every producer,
  validator, job, helper, artifact, coverage, and recovery state to one named
  regression owner without modifying or running executable files.

## Required context

- `MIG-03I`; Step `04` producer/validator/job and direct tests; central
  scheduler matrix; neutral validation-report and BAM-helper fault suites;
  roster/public-CLI suites; artifact evidence; coverage tool/baseline; current
  Step `04` runbook and troubleshooting routes; historical Java/Picard/
  samtools evidence; and applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled Picard, quickcheck, index, empty-output, and temp/tool
  failures safely freeze current predecessor/cross-attempt BAM/BAI/metrics
  residue, and exactly which bytes, directories, streams, exits, and unrelated
  files must old/final paths retain?
- Which submit-CWD, `PICARD`, Java override/`JAVA_HOME`/PATH/version, samtools,
  `TMPDIR`, Bash `3.2`, stale-wrapper, validator arbitrary-CWD/repeat/input-
  mutation, and neutral-loader states require direct final-path coverage?

## In scope

- Producer CLI/help/input/tool/temp validation, dry-run nonmutation, command
  order, execute, success, child/final-check failures, predecessor replacement,
  partial/empty/mixed output, unrelated files, streams, exits, and absent
  recovery controls; validator metrics/container/header/tool parsing, five rows,
  dry-run/execute/repeat, stable-input and shared publication faults; scheduler
  submit-CWD/module/Picard/Java/samtools/temp/directory/Bash `3.2`/child/output/
  stream states; modes, hashes, artifact evidence, coverage rename, and commit
  rollback.

## Out of scope

- Adding locking, staging, no-clobber, receipts, rollback, or recovery markers;
  changing duplicate marking, sample/library/platform/tool/output policy;
  scheduler hardening; dependency work; real Picard/Java/samtools/SLURM/
  production execution; or scientific interpretation.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and ambiguous-recovery state, with exact card corrections
  and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/mock evidence from real Picard,
  Java, samtools, scheduler, cluster, production, scientific-review, and
  biological evidence.

## Canonical documentation updates

- This card, `MIG-03I`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks a safe oracle, relocation changes native or
  report bytes beyond reviewed paths, artifact evidence needs schema change,
  or coverage/parity requires production, dependency, or cluster action.

## Completion record

Selected from clean, published, local/upstream/live-remote-equal architecture-
completion checkpoint `403fdf58dd410fc58421a45b903924c514a6ea70`.
This is a read-only independent-in-time adversarial pass by the same campaign
agent; independent authorship is not claimed. No executable/test mutation or
computational test is part of review selection.
