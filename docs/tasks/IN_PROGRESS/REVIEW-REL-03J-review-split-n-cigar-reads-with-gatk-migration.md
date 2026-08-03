# REVIEW-REL-03J — Review SplitNCigarReads migration reliability

## Objective

Challenge `MIG-03J` against producer, validator, scheduler, artifact, coverage,
staged BAM/BAI publication, predecessor restoration, cleanup/residue, stable-
input, reference, tool/runtime, and rollback behavior before source movement.

## Why this exists

The producer has a lock, run-token scratch, staged validation, backups, and
rollback, but restoration moves are best-effort and later cleanup can erase
backups and the lock after rollback itself fails. Inputs are not snapshot-
rechecked and no receipt binds output to an attempt. The wrapper adds module,
GATK, Java, samtools, Bash-version, logging, and stale-output states. Migration
must preserve and characterize these defects without fixing or approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer transaction, validator/report/reference semantics,
  scheduler directives/tool modes/failures, artifact identity, and coverage
  policy.
- Treat identical-input old/final parity, restoration failure, predecessor and
  recovery residue, input mutation, stable reference/input evidence, and exact
  streams/exits as named obligations; broad suite success is not a substitute.

## Blocked by

- [REVIEW-ARCH-03J](../COMPLETED/REVIEW-ARCH-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Required: completed architecture review fixes the owner, loader, caller, artifact, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03J](../TODO/REVIEW-UX-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from committed architecture-reviewed cards and map every producer,
  validator, scheduler, private loader, artifact, coverage, and recovery state
  to one named regression owner without modifying or running executable files.

## Required context

- `MIG-03J`; Step `05` producer/validator/job and direct tests; central
  scheduler matrix; neutral validation-report/BAM-helper fault suites; public
  reference-provenance owner/tests; roster/public-CLI suites; artifact and
  coverage evidence; runbook/troubleshooting; historical GATK/Java/samtools
  evidence; and applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled GATK, quickcheck, publication, final-validation,
  restoration, cleanup, signal, lock, and input-mutation states safely freeze
  current predecessor/recovery residue, and which bytes, directories, streams,
  exits, and unrelated files must old/final paths retain?
- Which submit-CWD, module, GATK, Java override/`JAVA_HOME`/PATH/version,
  samtools, log, stale-pair, Bash `3.2`, validator arbitrary-CWD/repeat/input-
  mutation/reference-loader, and stable-reference states require direct final-
  path coverage?

## In scope

- Producer admission, CLI/help, dry-run nonmutation, lock/scratch lifecycle,
  execute success, child/publication/final-check/restoration/cleanup/signal
  failures, predecessor replacement, residue, input mutation, unrelated files,
  streams, exits, and absent receipt; validator five rows, BAM/reference
  parsing, three private loaders, dry-run/execute/repeat, stable-input and
  publication faults; scheduler submit-CWD/module/GATK/Java/samtools/log/Bash
  `3.2`/child/stale-output/stream states; modes, hashes, artifact evidence,
  coverage rename, and commit rollback.

## Out of scope

- Adding or changing locks, staging, receipts, rollback, recovery markers,
  reference parsing, GATK/samtools/Java policy, scheduler hardening, dependency
  work, real tool/SLURM/production execution, or scientific interpretation.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, ambiguous-recovery, reference, and scheduler state, with
  exact card corrections and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/fake-tool evidence from real
  GATK, Java, samtools, scheduler, cluster, production, scientific-review, and
  biological evidence.

## Canonical documentation updates

- This card, `MIG-03J`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk rollback state lacks a safe oracle, relocation changes
  native/report bytes beyond reviewed paths, artifact evidence needs schema
  change, or coverage/parity requires production, dependency, or cluster work.

## Completion record

Selected as the sole active migration review from clean, published,
local/upstream/live-remote-equal architecture checkpoint
`e40fb3b90462b0f0bf77410b8e035995ce03a13d`. No reliability finding is
recorded yet, no later review or migration card is selected, and no
executable/test file changed or ran.
