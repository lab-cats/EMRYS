# REVIEW-REL-03H — Review RSeQC-paired-orientation evidence migration reliability

## Objective

Challenge `MIG-03H` against producer, validator, scheduler, artifact, coverage,
direct-final output, predecessor truncation, stale-output, and rollback behavior
before source movement.

## Why this exists

The producer redirects RSeQC stdout directly to a stable final path with no
lock, staging, no-clobber rule, stable-input recheck, receipt, or rollback. A
tool fault or empty success can truncate a valid predecessor or leave partial
bytes. The producer accepts any nonempty report while the validator requires
three exact fractions. Relocation must preserve and characterize those states
without approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer commands/serialization, validator report semantics,
  scheduler directives/modes/failures, artifact identity, and coverage policy.
- Treat identical-input old/final parity, predecessor-bearing tool-failure and
  empty-success faults, stable-input evidence, and exact residue as named
  obligations; a broad passing suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03H](../COMPLETED/REVIEW-ARCH-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Required: reliability review needs the architecture-corrected owner, caller, artifact, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03H](REVIEW-UX-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed cards and map every producer,
  validator, job, artifact, coverage, and recovery state to one named
  regression owner without modifying or running executable files.

## Required context

- `MIG-03H`; Step `03` producer/validator/job and direct tests; central
  scheduler matrix; shared validation-report faults; roster/public-CLI suites;
  artifact evidence; coverage tool/baseline; current Step `03` runbook and
  troubleshooting routes; and applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled predecessor-bearing RSeQC failure, partial-stdout, and empty-
  success faults safely freeze current truncation/residue, and exactly which
  bytes, directories, streams, and exits must old/final paths retain?
- Which CWD-sensitive tool selection, arbitrary-CWD validator, repeat-
  publication, input-mutation, and stale-wrapper states require direct final-
  path coverage beyond the existing shared suites?

## In scope

- Producer CLI/help/malformed input, both BAI names, binary path/PATH/CWD
  selection, dry-run nonmutation, execute, valid and malformed nonempty success,
  tool/empty failures, predecessor replacement, partial output, unrelated
  files, streams, exits, and absence of recovery controls; validator parsing,
  five rows, tolerance, dry-run/execute/repeat, stable-input and shared
  publication faults; scheduler submit-CWD/venv/module/directory/Bash `3.2`/
  child/output/stream states; modes, hashes, artifact evidence, coverage rename,
  and commit rollback.

## Out of scope

- Adding locking, staging, no-clobber, receipts, rollback, or recovery markers;
  deriving strandedness; changing BAI/sample/tool/output/evidence policy;
  scheduler hardening; dependency work; real RSeQC/SLURM/production execution;
  or scientific interpretation.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and ambiguous-recovery state, with exact card corrections
  and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/mock evidence from real RSeQC,
  scheduler, cluster, production, scientific-review, and biological evidence.

## Canonical documentation updates

- This card, `MIG-03H`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks a safe oracle, relocation changes native or
  report bytes beyond reviewed paths, artifact evidence needs schema change, or
  coverage/parity cannot be measured without production or dependency action.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `13755af8e878ca6ffa2f92a7279730e698087b0d`.

- **High — predecessor-bearing producer faults lacked exact oracles:** add one
  test-only old-path baseline across exactly the direct shell test, direct
  validator test, and central SLURM suite. Partial RSeQC stdout followed by exit
  `42` must propagate `42`, replace the predecessor with only partial bytes,
  preserve an unrelated file, and expose child stderr. Empty exit `0` must make
  the producer exit `1`, truncate the predecessor to empty, preserve the
  unrelated file, and expose the producer diagnostic. Neither behavior is
  approved.
- **High — producer/validator and stable-input coverage was incomplete:** add a
  nonempty malformed report that the producer accepts but the validator
  publishes as failed evidence; explicit-binary arbitrary-CWD producer use;
  arbitrary-CWD validator dry-run/execute/repeat byte parity; and post-build
  input mutation that exits `2` while preserving a valid predecessor report.
  Keep shared publication fault mechanics in the neutral report suite.
- **High — scheduler tool and stale-file states lacked direct assertions:**
  freeze `.venv` preference plus activation, PATH fallback, dry-run `logs/`
  creation without scientific output, and a mocked exit-`0` child that emits
  nothing while one stale nonempty Step `03` report satisfies the wrapper's
  `-s` check and remains byte-exact. Existing submit-CWD fallback, tolerated
  module list, exported `/tmp`, Bash `3.2`, invalid mode, and child-exit oracles
  remain applicable.
- **Accepted evidence and coverage boundary:** no fourth test file, production
  edit, fixture, coverage-baseline, documentation, dependency, or later owner
  enters the old-path baseline. The final cutover retains the architecture-
  reviewed five-move/nine-update ceiling. Coverage may increase but cannot
  regress below the frozen target rates or global covered-count floors.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
