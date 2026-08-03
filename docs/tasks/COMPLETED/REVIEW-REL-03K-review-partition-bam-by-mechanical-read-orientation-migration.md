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

- [REVIEW-ARCH-03K](REVIEW-ARCH-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) — Required: completed architecture review fixes the owner, loader, caller, artifact, test, pending-scaffold, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03K](REVIEW-UX-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

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

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `7ca503d7224f068fe51df0e9ad54c35b1d346583`.

- **High — child/count failures and producer reconciliation need exact
  oracles:** publish a first old-path test-only baseline in the existing direct
  shell owner. Controlled filter, merge, index, and count-command exits `71`,
  `72`, `73`, and `74` must propagate exactly, retain each injected stderr
  line, preserve an unrelated file, publish no final, and remove owned lock and
  dual-directory scratch. Also freeze missing explicit samtools rejection
  before either output directory exists, basename/PATH execution from an
  arbitrary CWD, assigned-greater-than-input rejection, and the current defect
  in which flag `99 + 147` disagrees with the merged FWD count yet the producer
  exits `0` and publishes the internally inconsistent counts row. Existing
  success fixes the exact commands, threads, six-decimal fraction, and counts;
  existing zero-group and temporary-quickcheck cases retain their failure
  ownership.
- **High — five-file predecessor and failed-restoration states need byte
  oracles:** publish a second old-path direct-shell baseline. It must prove the
  final move order is FWD BAM/BAI, REV BAM/BAI, then counts; reject and preserve
  an incomplete predecessor plus an unrelated file; restore all five prior
  files byte-for-byte after a final-path quickcheck failure; and inject
  publication exit `67` followed by FWD-BAM restoration exit `68`. That last
  state propagates `67`, leaves only the prior FWD BAM missing, restores the
  other four prior files, preserves the unrelated file, and exposes cleanup's
  deletion of every backup, lock, scratch path, and recovery marker. This
  ambiguous data-loss state is characterized, not approved.
- **High — input stability, signal, shared-QC collision, and attempt identity
  are unprotected:** publish a third old-path direct-shell baseline. A
  controlled first-filter mutation of the admitted BAM and exact `.bai` must
  still allow exit `0` and five-output publication. Controlled `TERM` must exit
  `143`, preserve a complete predecessor and unrelated bytes, and remove owned
  lock/scratch. A barrier-controlled pair of same-sample runs with distinct
  output directories and one shared QC directory must prove their two locks do
  not serialize: both exit `0`, both four-file BAM/BAI sets remain, and the
  deterministic last writer replaces the shared counts TSV, creating mixed-
  attempt evidence. Assert that none of these states creates a receipt or
  durable recovery marker; do not add one.
- **High — direct validator parity and stable-input coverage are incomplete:**
  publish one old-path baseline in the existing validator test. Add arbitrary-
  CWD dry-run/execute/repeat byte parity with unchanged inputs and no CWD
  residue; invalid BAM/BAI container magic as exit-`0` failed evidence; and a
  compact five-input post-build mutation matrix that exits `2` while preserving
  a valid predecessor report. The existing count-disagreement case owns
  producer-style flag/merged and assigned arithmetic failures. The neutral
  report suite remains the owner of exact-loader cache/failure and publication-
  fault mechanics; the roster suite remains the five-ID oracle.
- **High — Step 06 scheduler tool/resource and stale-set states need direct
  coverage:** publish one old-path central-scheduler baseline for samtools
  version-command exit propagation before delegation; missing/nonexecutable
  path warnings with unchanged child delegation; PATH basename forwarding;
  dynamic absent-`SLURM_SUBMIT_DIR` fallback; dry-run `logs/`-only mutation;
  explicit `THREADS` forwarding independent of the one-CPU request; and an
  exit-`0` child that emits nothing while five stale nonempty outputs are
  accepted and retained byte-for-byte. Existing generic cases retain exact
  directives/mode, module calls and tolerance, override arguments, invalid
  mode, child exit, missing-output rejection, and the Bash `3.2` empty-array
  defect.
- **Accepted slice, artifact, coverage, and evidence boundary:** publish
  exactly five small sequential old-path test-only checkpoints—producer child/
  count, producer transaction, producer stability/collision, validator, then
  scheduler—before the atomic five-move/nine-update cutover. Only the existing
  direct shell, direct validator, and central scheduler test owners may change;
  add no fixture, fourth test owner, production edit, coverage-baseline edit,
  documentation batch, dependency, or later owner. Existing artifact tests own
  all six Step `06` records, native reconciliation, and six-decimal fraction.
  Coverage may increase but may not regress below the frozen target rates or
  global covered-count floors. Every planned result is local fake-tool/fixture
  evidence, not real samtools, scheduler, cluster, production, scientific-
  review, biological-orientation, or biological-readiness evidence.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  biological-orientation, or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No reliability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not a green gate and not authority to alter inherited lifecycle
  state.
