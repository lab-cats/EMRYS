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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `25dbef637b8df87e77ec49a28dac5f8bee6e481c`.

- **High — four producer cut points lacked predecessor-bearing byte oracles:**
  add a test-only old-path baseline in the existing direct shell owner. A
  Picard stub that writes tokenized partial BAM and metrics bytes and exits `42`
  must propagate `42`, retain the prior BAI byte-exactly, expose child stderr,
  and preserve an unrelated file. A quickcheck exit `43` after successful
  Picard replacement must leave new BAM/metrics plus the prior BAI and must not
  invoke index. An index stub that writes a partial BAI and exits `44` must
  propagate `44` and leave new BAM/metrics plus that partial BAI. A zero-exit
  Picard result with nonempty BAM but empty metrics must pass quickcheck/index,
  fail the final metrics `-s` check with producer exit `1`, and leave new BAM/
  BAI plus empty metrics. None of these mixed states is approved.
- **High — producer admission and stable-input gaps need direct disposition:**
  add explicit Java/samtools paths from arbitrary CWD; a missing explicit
  samtools failure before output-directory creation; and one controlled Picard
  success that mutates the admitted input BAM/BAI while the producer still
  reports success. Freeze exact inputs, outputs, streams, exits, unrelated-file
  immunity, and absence of lock/stage/backup/receipt/recovery artifacts. Keep
  existing help, exact `<bam>.bai`, dry-run nonmutation, missing Picard, and bad
  `TMPDIR` oracles; the missing stable-input recheck remains a defect.
- **High — validator direct-path parity was incomplete:** in the existing
  direct validator owner, add arbitrary-CWD dry-run/execute/repeat journeys
  with byte-identical reports; quickcheck nonzero as exit-`0` failed evidence;
  header-tool failure as exit-`2` nonpublication; and a post-build input
  mutation that exits `2` while preserving a valid predecessor report. The
  neutral validation-report and BAM-helper suites remain the owners for both
  exact-loader caches and shared publication faults; no helper duplication is
  warranted.
- **High — Step 04 scheduler selection and stale-triplet defects need direct
  oracles:** in the central SLURM suite, add `JAVA_HOME/bin/java` selection,
  PATH fallback after an unusable but set `JAVA_HOME`, Java `-version` failure,
  unparseable/under-17 rejection, missing `PICARD`, list-only module failure
  tolerance, dry-run `logs/` mutation, and a zero-exit child that emits nothing
  while three stale nonempty outputs satisfy the wrapper and remain byte-exact.
  Also freeze the current unset-`JAVA_HOME` defect: even with a valid override,
  the later unguarded diagnostic exits before delegation under `set -u`.
  Existing generic cases retain submit-CWD fallback, strict module loads,
  exported `/tmp`, override priority, PATH samtools delegation, Bash `3.2`,
  invalid mode, child exit, and missing-output failure.
- **Accepted slice, coverage, and evidence boundary:** the old-path baseline is
  limited to exactly three existing test files and may be published as three
  small sequential test-only slices: direct producer, direct validator, then
  central scheduler. No fourth test owner, production edit, fixture, coverage-
  baseline edit, documentation batch, dependency, or later owner enters those
  slices. Coverage may increase but cannot regress below the frozen target
  rates or global covered-count floors. All evidence remains local fake-tool/
  fixture behavior; no real Picard, Java, samtools, scheduler, cluster,
  production, scientific-review, or biological result is created.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
