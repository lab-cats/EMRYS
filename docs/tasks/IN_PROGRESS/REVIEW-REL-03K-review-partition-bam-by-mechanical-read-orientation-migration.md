# REVIEW-REL-03K — Review mechanical-orientation partition migration reliability

## Objective

Challenge `MIG-03K` against producer, validator, scheduler, artifact, coverage,
five-file publication across output/QC directories, predecessor restoration,
cleanup/residue, stable-input, counts arithmetic, samtools/thread, and rollback
behavior before source movement.

## Why this exists

The producer has a per-sample output-directory lock, run-token scratch, staged
validation, five backups, counts-last publication, and rollback, but
restoration moves are best-effort and cleanup can erase backups after rollback
itself fails. Inputs are not snapshot-rechecked, the native counts TSV is not
an attempt receipt, and the output-directory lock does not by itself serialize
the separately selected QC path. The wrapper adds module, samtools, CPU/thread,
Bash-version, logging, and stale-output states. Migration must preserve and
characterize these defects without fixing or approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer transaction, mechanical flag/count behavior,
  validator/report semantics, scheduler directives/tool modes/failures,
  artifact identity, and coverage policy.
- Treat identical-input old/final parity, restoration failure, predecessor and
  recovery residue, cross-directory collision, input mutation, stable input,
  count disagreement, and exact streams/exits as named obligations; broad suite
  success is not a substitute.

## Blocked by

- [REVIEW-ARCH-03K](../COMPLETED/REVIEW-ARCH-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) — Required: completed architecture review fixes the owner, loader, caller, artifact, test, pending-scaffold, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03K](../TODO/REVIEW-UX-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from committed architecture-reviewed cards and map every producer,
  validator, scheduler, private loader/test helper, artifact, coverage, and
  recovery state to one named regression owner without modifying or running
  executable files.

## Required context

- `MIG-03K`; Step `06` producer/validator/job and active direct tests; central
  scheduler matrix; neutral validation-report fault suite; roster/public-CLI
  suites; artifact reconciliation and coverage evidence; runbook/
  troubleshooting; historical samtools/Step `06` evidence; and applicable
  `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled filter, merge, index, count, quickcheck, backup,
  publication, final-validation, restoration, cleanup, signal, lock, stale-
  path, output/QC collision, and input-mutation states safely freeze current
  predecessor/recovery residue, and which bytes, directories, streams, exits,
  and unrelated files must old/final paths retain?
- How are producer flag-subcount versus merged-count disagreement, assigned
  bounds/fraction, nonempty groups, counts-last behavior, all-five-or-none
  predecessor admission, absent receipt, and validator exit-`0` failed rows
  preserved without claiming a biological or current-attempt guarantee?
- Which submit-CWD, module, samtools override/PATH/version, one-CPU versus
  `THREADS`, log, stale-five-file, Bash `3.2`, validator arbitrary-CWD/repeat/
  input-mutation/report-loader, child, and stable-input states require direct
  final-path coverage?

## In scope

- Producer admission, CLI/help, dry-run nonmutation, mechanical flag/merge/
  count commands, lock and dual-directory scratch lifecycle, execute success,
  child/publication/final-check/restoration/cleanup/signal failures,
  predecessor replacement, residue, input mutation, unrelated files, streams,
  exits, and absent receipt; validator five rows, container/count parsing,
  private report loader, dry-run/execute/repeat, stable-input and publication
  faults; scheduler submit-CWD/module/samtools/thread/log/Bash `3.2`/child/
  stale-output/stream states; modes, hashes, artifact evidence, coverage rename,
  and commit rollback.

## Out of scope

- Adding or changing locks, staging, receipts, rollback, recovery markers,
  counts schemas, flag groups, samtools/thread policy, scheduler hardening,
  dependency work, real tool/SLURM/production execution, or scientific/
  biological interpretation.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, ambiguous-recovery, count, collision, and scheduler state,
  with exact card corrections and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/fake-tool evidence from real
  samtools, scheduler, cluster, production, scientific-review, biological-
  orientation, or biological-readiness evidence.

## Canonical documentation updates

- This card, `MIG-03K`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk rollback/collision state lacks a safe oracle, relocation
  changes native/report bytes beyond reviewed paths, artifact evidence needs
  schema change, or coverage/parity requires production, dependency, or cluster
  work.

## Completion record

Selected as the sole active migration review from clean, published,
local/upstream/live-remote-equal architecture checkpoint
`2452332d463f9517eeaf0b2a5af13b9f0bf65fbc`. No reliability finding is
recorded yet, no usability review or migration card is selected, and no
executable/test file changed or ran.
