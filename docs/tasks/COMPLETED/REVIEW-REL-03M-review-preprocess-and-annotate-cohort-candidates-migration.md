# REVIEW-REL-03M — Review cohort preprocessing migration reliability

## Objective

Challenge `MIG-03M` against shell/R/validator/scheduler contracts, split-root
transaction and restoration behavior, input stability, shared-contract loader
faults, guarded-real-R semantics, artifact-marker interpretation, and coverage
before any executable move.

## Why this exists

Current tests protect normal publication and successful rollback, but
relocation must not hide or bless the receipt-visible-before-commit window,
incomplete restoration with lock release and no recovery marker, cross-root
residue, input mutation, validator evidence ceilings, shared Step `09c`
dependency, or stale scheduler success. The R semantic engine is nearly two
thousand lines and must remain byte/behavior-equivalent apart from reviewed
path text without restoring or changing dependencies.

## Fixed decisions

- Review only; add no reliability behavior and run no computational test under
  this card. Findings may require later bounded old-path test-only checkpoints.
- Preserve every characterized defect as a named ceiling; never convert a
  migration oracle into hardening, recovery redesign, schema extraction, or
  evidence promotion.
- Keep local fake-R, guarded-real-R fixture, scheduler mock, and Python evidence
  separate from cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-ARCH-03M](../COMPLETED/REVIEW-ARCH-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Required: architecture fixed the eight-move/ten-integration cutover, private loaders, artifact/coverage ownership, production hashes, and rollback boundary.

## Completion unblocks

- [REVIEW-UX-03M](../TODO/REVIEW-UX-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Fully: usability review needs the fixed failure, residue, recovery, R, validator, and scheduler obligations.

## Prerequisites

- Inspect only the committed architecture-reviewed card state and existing
  old-path implementation/tests; do not mutate or execute them.

## Required context

- `MIG-03M`; architecture review; all Step `08` native and direct-test assets;
  neutral report and flat Step `09c` loader owners/tests; central scheduler,
  guarded-R, artifact, validation-roster, publication-fault, public-CLI, and
  coverage surfaces; current runbook/troubleshooting recovery language; and
  the exact three-file two-root transaction.

## Questions owned by this card

- Which smallest old-path test-only slices are required for child/publication/
  restoration failures, receipt visibility, signal exits, same-scope lock
  concurrency, stale paths, unrelated bytes, and cross-root residue?
- Which admitted inputs are hash-bound and snapshot-rechecked, which mutations
  remain visible or invisible, and what receipt/runtime/attempt identities are
  absent without changing provenance?
- Which guarded-real-R fixtures and exact output comparisons are sufficient to
  prove path-only relocation while preserving lexical/semantic parsing,
  annotation, provisional policy, and dependency state?
- Which compact validator matrix owns all five rows, exit-`0` failed evidence,
  candidate/order limits, annotation-path disagreement, stable-input and
  publication behavior, plus neutral-report and Step `09c` exact-loader faults?
- Which scheduler cases preserve module/renv/R resolution, submit-CWD/log
  effects, child failures, three-file checks, and stale-complete false success?
- How is the native input-receipt marker versus artifact summary failure marker
  distinction tested and described without changing either contract?

## In scope

- Test-gap inventory; minimal old-path checkpoint ordering; exact shell
  transaction/restore/mutation/signal/concurrency oracles; guarded-R semantic
  parity; validator/report/Step-`09c` loader and evidence ceilings; scheduler
  diagnostics/stale outputs; artifact marker meaning; coverage policy; and
  rollback consequences.

## Out of scope

- Production mutation; defect fixes; R dependency restoration/installation;
  schema/helper extraction; public imports; new recovery or attempt markers;
  transaction/artifact/scheduler policy changes; Step `09`/`09c` migration; or
  cluster/production/scientific work.

## Deliverables

- Finding-by-finding reliability disposition and the smallest ordered test-only
  slices required before atomic cutover, recorded in `MIG-03M` and the audit.

## Acceptance evidence

- Every high-risk state has an existing or required safe local oracle with
  exact bytes, paths, streams, exits, locks, backups, residue, unrelated files,
  and evidence ceiling. No proposed oracle requires a production behavior,
  dependency, method, policy, schema, or scientific-meaning change.

## Canonical documentation updates

- This card, `MIG-03M`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk restoration/mutation/R-semantic state lacks a safe local
  oracle, parity needs production or dependency work, native/report bytes must
  change beyond reviewed paths, or a defect must be fixed or blessed.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `88eef71e30737ede8165b60a30211312f407ab91`.

- **High — runtime resolution and every admitted input need one exact shell
  oracle:** publish one old-path test-only checkpoint in the existing direct
  shell owner. Freeze missing/nonexecutable explicit Rscript and missing R
  program rejection before output/QC mutation, plus basename/PATH Rscript
  resolution from arbitrary CWD. Extend the controlled fake-R mutation matrix
  across sample manifest, partition manifest, annotation GTF, Step `07`
  receipt, and Step `07` VCF; each is hash-bound and must fail before
  publication with exact diagnostic, clean owned scratch/lock, preserved
  unrelated bytes, and no final set. In contrast, mutate the selected R
  program after admission and preserve the current exit-`0` publication:
  neither R program/runtime/package identity nor attempt identity is recorded.
  Assert that the native input receipt also omits sibling sites/summary hashes;
  this is a provenance ceiling, not approval.
- **High — receipt visibility and incomplete restoration need split-root byte
  oracles:** publish one old-path direct-shell transaction checkpoint. Log the
  exact final move order—sites under the cohort output root, summary under the
  QC root, then input receipt under the cohort output root—and barrier-observe
  all three finals after receipt publication while final validation is pending
  and `publication_committed` remains false. Inject receipt-publication exit
  `67` followed by prior-sites restoration exit `68`: preserve exit `67`, leave
  the prior sites final absent while its output-root backup survives, restore
  prior input-receipt and QC-summary bytes exactly, remove owned temps and the
  lock, preserve unrelated bytes in both roots, and create no recovery marker.
  This is an ambiguous preservation-first state, not successful rollback or
  retry authority. Existing tests remain owners of all-three-or-none admission,
  ordinary rollback, first-publication cleanup, final-validation rollback,
  foreign locks, and stale run-token paths.
- **High — signals and same-cohort contention need a separate small shell
  checkpoint:** after the receipt becomes visible for a complete predecessor,
  controlled `TERM` must exit `143`, restore all three prior files byte-exactly
  across both roots, preserve unrelated bytes, and remove owned scratch/lock
  without inventing a recovery marker. A fake-R barrier must hold one admitted
  same-cohort run while a second exits `1` on the cohort lock; releasing the
  winner yields exactly one complete set and no owned residue. Receipt
  presence, names, counts, hashes, or timestamps still do not identify a
  durable attempt.
- **High — direct validator evidence and the new Step `09c` bridge need bounded
  coverage:** publish one old-path checkpoint in the existing direct validator
  owner. Add arbitrary-CWD dry-run/execute/repeat byte parity with unchanged six
  inputs and no invocation-CWD residue; a compact mutation table that makes
  each of the five exact check IDs publish exit-`0` failed evidence; and post-
  build mutation of sample manifest, partition manifest, annotation, sites,
  inputs, and summary as exit `2` preserving a valid predecessor report.
  Freeze equivalent annotation-path spelling as exit-`0`
  `manifest_annotation_identity` failure, and arbitrary unique candidate IDs
  plus reversed site rows as current all-pass ceilings: the validator does not
  recompute candidate identity/order or rerun R, GTF overlap, allele mapping,
  or upstream filtering. The neutral report suite remains owner of common
  loader/publication faults. During the atomic cutover, replace the test's root
  `sys.path` mutation with private exact-file roster/Step-`09c` loaders and add
  final-path coverage of the production bridge's exact-owner initialization,
  valid cache reuse, foreign/partial cache preservation, missing specification/
  loader, execution failure, owned partial-cache cleanup, sanitized public exit
  `2`, and unchanged `sys.path`.
- **High — Step `08` scheduler R and stale-set behavior needs one central
  checkpoint:** add direct Step `08` cases for tolerated Rscript version-probe
  failure; warning-only missing/nonexecutable Rscript with unchanged
  delegation; PATH-basename forwarding; unchanged delegation of the selected
  R-program path for child-owned validation; dynamic launch-CWD fallback when
  `SLURM_SUBMIT_DIR` is absent; dry-run `logs/`-only mutation; and an exit-`0`
  child that emits nothing while three stale nonempty outputs across output/QC
  roots are accepted byte-for-byte. Existing generic cases retain exact mode,
  directives, one tolerated `module list`, full arguments, invalid mode, child
  exit, and missing-output rejection. The wrapper neither activates nor
  validates `renv`; it inherits caller R startup state, while the central
  local-R suite remains the opt-in environment owner. These are scheduler
  defects and boundaries, not hardening or submitted-job proof.
- **Accepted R, artifact, slices, and coverage boundary:** the committed
  guarded-real-R runner/test already exercise exact tables/order, candidate and
  multiallelic behavior, lexical and semantic VCF/count failures, GTF overlap,
  annotation/intergenic/header-only cases, provisional orientation policy,
  and Step `07` receipt/VCF mutation. Add no R semantic test-only checkpoint;
  run that exact guarded suite at final-path acceptance without dependency
  action. Existing artifact tests own native receipt versus artifact
  `step08_summary_v1` marker reconciliation; cutover adds only the final
  producer path/hash assertion. Publish exactly five sequential test-only
  checkpoints—runtime/input provenance, transaction/recovery,
  signal/concurrency, validator, scheduler—before the atomic eight-move/
  ten-update cutover. Only the direct shell, direct validator, and central
  scheduler test owners may change; add no fixture file, fourth test owner,
  production edit, coverage baseline, documentation batch, dependency, or
  future card. Final measurement must retain validator rates at or above
  `122/129` lines and `26/36` branches, keep every non-target row exact, and
  preserve global covered-count floors `9561/11720` lines and `3351/4772`
  branches.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, R package/runtime, scheduler, cluster, production,
  scientific-review, provisional-policy, variant/editing-site, or biological
  state changed or ran.
- **Card-boundary gate:** `git diff --check` passes and the exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings. No reliability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only result is
  nonpassing, not green and not authority to alter inherited lifecycle state.
