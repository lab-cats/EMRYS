# REVIEW-REL-03L — Review partitioned cohort mpileup migration reliability

## Objective

Challenge `MIG-03L` against producer, validator, scheduler, artifact, coverage,
three-file receipt-last publication, predecessor restoration, cleanup/residue,
stable-input, selector, manifest, VCF/count, bcftools, and rollback behavior
before source movement.

## Why this exists

The producer has a cohort/partition lock, run-token scratch, staged VCF
validation, three backups, receipt-last publication, and rollback, but the
receipt becomes visible before final validation and has no durable attempt
identity. Only manifests are hash-bound and snapshot-rechecked; restoration is
best-effort; VCFs are unhashed; and validator coverage is intentionally
shallower than producer selector and bcftools validation. The wrapper adds
module, tool, logging, and stale-output states. Migration must preserve and
characterize these defects without fixing or approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer transaction, mechanical-label/pileup/filter
  behavior, validator/report semantics, scheduler directives/tool modes/
  failures, artifact identity, and coverage policy.
- Treat identical-input old/final parity, restoration failure, predecessor
  and recovery residue, input mutation, receipt visibility/identity,
  relative-path disagreement, stable input, selector asymmetry, and exact
  streams/exits as named obligations; broad suite success is not a substitute.

## Blocked by

- [REVIEW-ARCH-03L](../COMPLETED/REVIEW-ARCH-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Required: completed architecture review fixed the exact owner, loader, caller, artifact, test, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03L](../TODO/REVIEW-UX-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from committed architecture-reviewed cards and map every producer,
  validator, scheduler, private loader/test helper, artifact, coverage, and
  recovery state to one named regression owner without modifying or running
  executable files.

## Required context

- `MIG-03L`; Step `07` producer/validator/job and direct tests; central
  scheduler matrix; neutral validation-report fault suite; roster/public-CLI
  suites; artifact reconciliation and coverage evidence; partition manifests;
  runbook/troubleshooting; historical bcftools/Step `07` evidence; and
  applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled mpileup, filter, VCF-header/sample/count, receipt-write,
  backup, publication, final-validation, restoration, cleanup, signal, lock,
  stale-path, and input-mutation states safely freeze predecessor/recovery
  residue, and which bytes, directories, streams, exits, and unrelated files
  must old/final paths retain?
- How are receipt-last visibility, all-three-or-none predecessor admission,
  manifest-only stability, absent input/output hashes and attempt marker,
  relative output-root mismatch, header-only VCFs, and validator exit-`0`
  failed rows preserved without claiming immutable, scientific, calling, or
  biological guarantees?
- Which `region`/`regions_file`, FAI bounds, compressed selector, manifest
  ordering/hash, sample order, malformed VCF/receipt, repeat/arbitrary-CWD,
  submit-CWD, module, bcftools override/PATH/version, log, stale-three-file,
  child, and stable-input states require direct final-path coverage?

## In scope

- Producer admission, CLI/help, dry-run nonmutation, selector and exact
  pileup/filter commands, lock/scratch lifecycle, execute success, child/
  publication/final-check/restoration/cleanup/signal failures, predecessor
  replacement, receipt visibility, residue, input mutation, unrelated files,
  streams, exits, and absent durable attempt identity; validator five rows,
  receipt/VCF/selector/manifest/count parsing, private report loader, dry-run/
  execute/repeat, stable-input and publication faults; scheduler submit-CWD/
  module/bcftools/log/child/stale-output/stream states; modes, hashes, artifact
  evidence, coverage rename, and commit rollback.

## Out of scope

- Adding or changing locks, staging, receipts, rollback, recovery markers,
  output hashes, provenance fields, selectors, pileup/filter/depth policy,
  calling, schemas, bcftools policy, scheduler hardening, dependency work,
  real tool/SLURM/production execution, or scientific/biological
  interpretation.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, ambiguous-recovery, selector, receipt, mutation, and
  scheduler state, with exact card corrections and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/fake-tool evidence from real
  bcftools, scheduler, cluster, production, scientific-review, variant/
  editing-site, or biological-readiness evidence.

## Canonical documentation updates

- This card, `MIG-03L`, roadmap/handoff only where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if a high-risk rollback/mutation state lacks a safe oracle, relocation
  changes native/report bytes beyond reviewed paths, artifact evidence needs
  schema change, or coverage/parity requires production, dependency, or
  cluster work.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `3d2b9c0ada9b970bac533a72d910be010e74da3f`.

- **High — pipeline, tool, manifest, and selector failures need exact
  oracles:** publish one old-path test-only checkpoint in the existing direct
  shell owner. Exercise controlled FWD/REV mpileup and filter failures; the
  producer intentionally normalizes each child failure to exit `1`. Preserve
  exact diagnostics, unrelated bytes, no final outputs, and removal of owned
  lock/scratch. Also freeze rejection of missing/nonexecutable explicit
  bcftools before output creation, basename/PATH resolution from arbitrary CWD,
  detection of sample/partition-manifest mutation, compressed relative
  `regions_file` acceptance, and unchanged exact commands, sample order,
  depth/filter defaults, annotations, `-I`, header-only VCF support, and absence
  of `bcftools call`. Existing admission and selector cases remain owners of
  unsafe IDs, duplicates, missing FAI/BAI, out-of-bounds selectors, and dry-run
  nonmutation.
- **High — receipt-last publication and failed restoration need byte
  oracles:** publish one old-path direct-shell transaction checkpoint. Log the
  exact final move order—FWD VCF, REV VCF, receipt—and barrier-observe all three
  outputs while final validation is pending and `publication_committed` is
  still false. Preserve the all-three-or-none predecessor, foreign lock, stale
  run-token path, ordinary rollback, and unrelated-file states. Inject receipt-
  publication exit `67` followed by prior-FWD restoration exit `68`: exit `67`
  remains authoritative, the prior FWD final is absent but its backup remains,
  prior REV and receipt finals are restored byte-exactly, owned temps and lock
  are removed, unrelated bytes remain, and no recovery marker appears. That is
  a characterized ambiguous recovery state, not rollback approval or retry
  authority.
- **High — most admitted inputs and attempt identity are unprotected:** publish
  one old-path stability/provenance checkpoint. During a controlled fake-tool
  barrier, mutate admitted BAM/BAI, FASTA/FAI, and regions-file bytes after
  validation; the producer must remain blind, exit `0`, and publish. In
  contrast, a mutated sample or partition manifest must fail before
  publication. Controlled `TERM` exits `143`, restores a complete predecessor,
  preserves unrelated bytes, and removes owned scratch/lock. Two barrier-
  controlled same-scope runs prove one cohort/partition lock admits one and
  rejects the other without altering the winner. Exact receipt-header
  assertions preserve absence of run token, BAM/reference/tool/depth/filter
  identity, and VCF hashes. Receipt presence, names, counts, and timestamps do
  not establish current-attempt or immutable-computation identity.
- **High — direct validator semantic and stable-input coverage is incomplete:**
  publish one old-path checkpoint in the existing direct validator owner. Add
  arbitrary-CWD dry-run/execute/repeat byte parity with unchanged inputs and no
  CWD residue; a compact mutation table that owns each of the five check IDs as
  exit-`0` failed evidence; and a six-input post-build mutation matrix that
  exits `2` while preserving a valid predecessor report. Explicitly freeze
  producer-valid compressed regions files as validator exit-`0`
  `selector_reconciliation` failure; out-of-bounds BED coordinates, VCF rows
  outside a declared selector, and unchecked REF/ALT/FORMAT fields as current
  false-pass ceilings; and relative receipt VCF paths against resolved
  arguments as exit-`0` `vcf_record_counts` failure. The neutral report suite
  remains the owner of loader cache/path/readiness and publication faults, and
  the roster suite remains the exact five-ID owner.
- **High — Step 07 scheduler tool and stale-set states need direct coverage:**
  publish one old-path central-scheduler checkpoint for executable bcftools
  version-command failure before delegation; missing/nonexecutable tool warning
  with unchanged delegation; PATH-basename forwarding; dynamic fallback to
  launch CWD when `SLURM_SUBMIT_DIR` is absent; dry-run `logs/`-only mutation;
  and an exit-`0` child that emits nothing while three stale nonempty outputs
  are accepted and retained byte-for-byte. Existing generic tests retain exact
  mode/directives, one CPU, submit-CWD rule, tolerated module calls, full
  argument/depth/filter forwarding, invalid execute mode, child exit, and
  missing-output rejection. Step `07` has no characterized Bash `3.2` empty-
  array defect; do not copy that Step `06` claim.
- **Accepted slices, artifact, coverage, and evidence boundary:** publish
  exactly five small sequential old-path test-only checkpoints—pipeline/
  selector, transaction/recovery, stability/provenance, validator, scheduler—
  before the atomic cutover. Only the existing direct shell, direct validator,
  and central scheduler test owners may change. Add no fixture file, fourth
  owner, production edit, coverage-baseline edit, documentation batch,
  dependency, or future card. Existing artifact tests own VCF/receipt/report
  schemas and reconciliation; the final cutover alone adds path/hash evidence.
  Coverage may increase but may not regress below `167/198` lines, `48/72`
  branches, or global covered-count floors. All planned results are local
  fake-tool/fixture evidence, not real bcftools, scheduler, cluster,
  production, scientific review, variant/editing-site, or biological evidence.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-
  review, variant/editing-site, or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No reliability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not a green gate and not authority to alter inherited lifecycle
  state.
