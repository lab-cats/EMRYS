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

- [REVIEW-UX-03J](REVIEW-UX-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Fully: completed usability review follows fixed fault, preservation, and parity obligations.

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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `5785b87660d4274b07e39fba07590fb50f75f6d2`.

- **High — restoration failure can erase the only recoverable BAM:** publish a
  small old-path transaction baseline in the existing direct shell owner. It
  must freeze lone-final rejection with byte-exact preservation, final-path
  revalidation failure with byte-exact predecessor restoration, and injected
  BAI-publication exit `67` followed by BAM-restoration exit `68`. The last
  state propagates `67`, leaves the prior BAM missing and prior BAI restored,
  preserves an unrelated file, and exposes the current deletion of backups,
  lock, scratch, and recovery evidence. This ambiguous/data-loss state is not
  approved.
- **High — producer admission, mutation, and signal states need a second
  bounded baseline:** in the same direct shell owner, separately freeze
  missing explicit samtools rejection before output-directory creation;
  controlled GATK-time mutation of the admitted BAM, BAI, FASTA, FAI, and DICT
  while the producer still exits `0`; and controlled `TERM` exit `143` with
  predecessor and unrelated bytes preserved and owned lock/scratch removed.
  Assert that no receipt or recovery marker exists without adding one. Keep
  existing help, argument, input/reference, dry-run, success, Java-floor,
  lock, GATK, quickcheck, header, publication, and ordinary rollback cases.
- **High — validator parity and private-reference failure ownership were
  incomplete:** publish one old-path direct-validator baseline for arbitrary-
  CWD dry-run/execute/repeat byte parity with unchanged inputs, quickcheck
  nonzero as exit-`0` failed evidence, header-tool failure as exit-`2`
  nonpublication, and post-build input mutation as exit `2` preserving a valid
  predecessor report. During cutover, add five owner-local reference-bridge
  cases: cache reuse without `sys.path` mutation, missing owner/spec cleanup,
  foreign-cache preservation, correct-path incomplete-API preservation, and
  execution-failure owned-partial cleanup. Neutral report/BAM-helper suites
  retain their existing loader and publication-fault matrices.
- **High — Step 05 scheduler selection and stale-pair behavior need exact
  cases:** publish one old-path central-scheduler baseline for
  `JAVA_HOME/bin/java` selection, PATH fallback after unusable `JAVA_HOME`,
  missing/unusable Java override, Java command failure, unparseable output,
  under-17 rejection, GATK/samtools version-command failure, missing or
  unusable GATK/samtools warning with unchanged delegation, dynamic absent-
  `SLURM_SUBMIT_DIR` fallback, dry-run `logs/`-only mutation, and zero-exit
  child with two stale nonempty outputs falsely accepted byte-exactly. Existing
  generic cases retain directives, mode, overrides, module tolerance, invalid
  mode, child exit, missing output, and Bash-`3.2` behavior.
- **Accepted slice, coverage, and evidence boundary:** publish exactly four
  small sequential old-path test-only checkpoints—producer transaction,
  producer admission/signal, validator, then scheduler—before the atomic five-
  move/ten-update cutover. Use only the existing direct shell, direct validator,
  and central scheduler owners; add no fixture, fourth test owner, production
  edit, coverage-baseline edit, documentation batch, dependency, or later
  owner. Coverage may increase but may not regress below the frozen target
  rates or global covered-count floors. All planned evidence is local fake-
  tool/fixture behavior; no real GATK, Java, samtools, scheduler, cluster,
  production, scientific-review, or biological result is created.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No reliability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not a green gate and not authority to alter inherited lifecycle
  state.
