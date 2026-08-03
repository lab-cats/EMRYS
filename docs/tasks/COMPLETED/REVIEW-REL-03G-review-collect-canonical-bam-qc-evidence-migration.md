# REVIEW-REL-03G — Review canonical-BAM-QC evidence migration reliability

## Objective

Challenge `MIG-03G` against producer, validator, scheduler, artifact, coverage,
partial-output, mixed-attempt, residue, and rollback behavior before source
movement.

## Why this exists

The producer writes quickcheck and flagstat directly to stable final paths with
no lock, staging, no-clobber rule, stable-input recheck, transaction receipt,
or rollback. A fault can replace one predecessor and preserve or truncate the
other. Producer and validator also disagree on nonempty zero-exit quickcheck
output. Relocation must preserve and characterize those states without
approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer commands/serialization, validator report semantics,
  scheduler directives/modes/failures, artifact identity, and coverage policy.
- Treat identical-input old/final parity, predecessor-bearing quickcheck and
  flagstat faults, stable-input evidence, and exact residue as named
  obligations; a broad passing suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03G](../COMPLETED/REVIEW-ARCH-03G-review-collect-canonical-bam-qc-evidence-migration.md) — Required: reliability review needs the architecture-corrected owner, caller, artifact, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03G](../IN_PROGRESS/REVIEW-UX-03G-review-collect-canonical-bam-qc-evidence-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed cards and map every producer,
  validator, job, artifact, coverage, and recovery state to one named
  regression owner without modifying or running executable files.

## Required context

- `MIG-03G`; Step `02b` producer/validator/job and direct tests; central
  scheduler matrix; shared validation-report faults; roster/public-CLI suites;
  artifact evidence; coverage tool/baseline; current Step `02b` runbook and
  troubleshooting routes; and applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled predecessor-bearing quickcheck and flagstat faults safely
  freeze current mixed-attempt or truncated final evidence, and exactly which
  bytes, siblings, directories, streams, and exits must old/final paths retain?
- Which arbitrary-CWD, repeat-publication, input-mutation, and scheduler states
  require direct final-path coverage beyond the existing shared suites?

## In scope

- Producer CLI/help/malformed input, both BAI names, PATH resolution, dry-run
  directory effect, execute, empty/nonempty quickcheck success, quickcheck and
  flagstat failures, predecessor replacement, partial/mixed output, unrelated
  files, streams, exits, and absence of recovery controls; validator parsing,
  five rows, marker mismatch, dry-run/execute/repeat, stable-input and shared
  publication faults; scheduler submit-CWD/module/directory/Bash `3.2`/child/
  output/stream states; modes, hashes, artifact evidence, coverage rename, and
  commit rollback.

## Out of scope

- Adding locking, staging, no-clobber, receipts, rollback, or recovery markers;
  reconciling quickcheck semantics; removing BAI admission; changing sample,
  output, or evidence policy; scheduler hardening; dependency work; real
  samtools/SLURM/production execution; or scientific policy.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and ambiguous-recovery state, with exact card corrections
  and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/mock evidence from real
  samtools, scheduler, cluster, production, scientific-review, and biological
  evidence.

## Canonical documentation updates

- This card, `MIG-03G`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks a safe oracle, relocation changes native or
  report bytes beyond reviewed paths, artifact evidence needs schema change, or
  coverage/parity cannot be measured without production or dependency action.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `9b4b5a858c76785f23a9ba0fb6387b7db60575dd`.

- **High — predecessor-bearing producer faults lacked exact oracles:** add one
  test-only old-path baseline across exactly the direct shell test, direct
  validator test, and central SLURM suite. Quickcheck exit `42` must become
  producer exit `1`, replace only quickcheck with the combined diagnostic, and
  retain prior flagstat. Flagstat exit `43` must follow a new PASS quickcheck,
  replace prior flagstat with partial stdout, expose its stderr, and propagate
  `43`. Both preserve one unrelated file and prove the absence of transactional
  or recovery artifacts without approving the behavior.
- **High — validator direct-path reliability was incomplete:** add an explicit
  nonempty producer-success marker that becomes failed validator evidence; an
  arbitrary-CWD dry-run/execute/repeat journey with exact bytes and no input or
  invocation-directory mutation; and a post-build input mutation that exits `2`
  while preserving one valid prior report. Keep shared publication fault
  mechanics in the neutral validation-report suite.
- **High — scheduler stale-file acceptance lacked a direct assertion:** when the
  mocked child exits `0` without emitting outputs, two preexisting Step `02b`
  files satisfy the wrapper's `-f` checks and remain byte-exact while the job
  reports success. Preserve this false-success defect and the existing required
  submit CWD, strict load/tolerated list, exported `/tmp`, Bash `3.2` dry-run,
  and child-exit behavior.
- **Accepted evidence and coverage boundary:** add a PATH-only missing-samtools
  case before output-directory creation. Existing shared public-CLI, roster,
  report, artifact, and coverage owners remain sufficient; the test-only
  baseline adds no fourth file and the final cutover keeps the architecture-
  reviewed five-move/nine-update ceiling. Coverage may increase but may not
  regress below the frozen target rates or global covered-count floors.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
