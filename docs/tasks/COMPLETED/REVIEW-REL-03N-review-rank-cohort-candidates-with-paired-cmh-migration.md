# REVIEW-REL-03N — Review paired-CMH analysis migration reliability

## Objective

Challenge `MIG-03N` against shell/R/validator/scheduler contracts, six-output
transaction and restoration behavior, input stability, shared-contract loader
faults, guarded-real-R and independent-oracle semantics, artifact
interpretation, and coverage before any executable move.

## Why this exists

Current tests protect normal publication and method behavior, but relocation
must not hide or bless the summary-visible-before-commit window, incomplete
restoration states, retained lock/recovery evidence, input mutation, validator
evidence ceilings, shared Step `09c` dependency, or stale scheduler success.
The R semantic engine is over one thousand lines and must remain behavior-
equivalent apart from reviewed path text without restoring or changing
dependencies.

## Fixed decisions

- Review only; add no reliability behavior and run no computational test under
  this card. Findings may require later bounded old-path test-only checkpoints.
- Preserve every characterized defect as a named ceiling; never convert a
  migration oracle into hardening, recovery redesign, schema extraction, or
  evidence promotion.
- Keep local fake-R, guarded-real-R fixture, independent Python oracle,
  scheduler mock, and validator evidence separate from cluster, production,
  completed scientific review, or biological proof.

## Blocked by

- [REVIEW-ARCH-03N](../COMPLETED/REVIEW-ARCH-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Required: completed architecture review supplies the corrected cutover and loader boundary.

## Completion unblocks

- [REVIEW-UX-03N](../IN_PROGRESS/REVIEW-UX-03N-review-rank-cohort-candidates-with-paired-cmh-migration.md) — Fully: selected usability review consumes the fixed failure, residue, recovery, R/oracle, validator, and scheduler obligations.

## Prerequisites

- Inspect only the committed architecture-reviewed card state and existing
  old-path implementation/tests; do not mutate or execute them.

## Required context

- `MIG-03N`; architecture review; all Step `09` native and candidate direct-
  test assets; neutral report and flat Step `09c` loader owners/tests; central
  scheduler, guarded-R, independent-oracle, artifact, validation-roster,
  publication-fault, public-CLI, and coverage surfaces; current runbook/
  troubleshooting recovery language; and the exact six-file transaction.

## Questions owned by this card

- Which smallest old-path test-only slices are required for child/publication/
  restoration failures, summary visibility, signal exits, same-scope lock
  concurrency, stale paths, unrelated bytes, and retained recovery evidence?
- Which admitted inputs are hash-bound and snapshot-rechecked, which mutations
  remain visible or invisible, and what summary/runtime/attempt/sibling
  identities are absent without changing provenance?
- Which guarded-real-R fixtures and independent count-derived oracle cases are
  sufficient to prove path-only relocation while preserving pairing,
  estimability, continuity correction, odds ratios, global BH, statuses, and
  dependency state?
- Which compact validator matrix owns all seven rows, exit-`0` failed evidence,
  non-recomputed CMH limits, stable-input and publication behavior, plus
  neutral-report and Step `09c` exact-loader faults?
- Which scheduler cases preserve module/R resolution, submit-CWD/log effects,
  child failures, six-file checks, and stale-complete false success?

## In scope

- Test-gap inventory; minimal old-path checkpoint ordering; exact shell
  transaction/restore/mutation/signal/concurrency oracles; guarded-R and
  independent-oracle semantic parity; validator/report/Step-`09c` loader and
  evidence ceilings; scheduler diagnostics/stale outputs; artifact meaning;
  coverage policy; and rollback consequences.

## Out of scope

- Production mutation; defect fixes; R dependency restoration/installation;
  schema/helper extraction; public imports; new recovery or attempt markers;
  transaction/artifact/scheduler/statistical policy changes; Step `09c`
  migration; or cluster/production/scientific work.

## Deliverables

- Finding-by-finding reliability disposition and the smallest ordered
  test-only slices required before atomic cutover, recorded in `MIG-03N` and
  the audit.

## Acceptance evidence

- Every high-risk state has an existing or required safe local oracle with
  exact bytes, paths, streams, exits, locks, backups, residue, unrelated files,
  and evidence ceiling. No proposed oracle requires a production behavior,
  dependency, method, policy, schema, or scientific-meaning change.

## Canonical documentation updates

- This card, `MIG-03N`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk restoration/mutation/R-semantic state lacks a safe local
  oracle, parity needs production or dependency work, native/report bytes must
  change beyond reviewed paths, or a defect must be fixed or blessed.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `6fc186847c991a931471d5d7591be24a9524201d`.

- **High — runtime resolution and all four admitted inputs need one exact shell
  oracle:** publish one old-path test-only checkpoint in the existing direct
  shell owner. Freeze missing/nonexecutable explicit Rscript, missing R
  program, and basename/PATH Rscript resolution from an arbitrary CWD before
  final-output mutation. Extend the controlled fake-R mutation matrix across
  sample manifest, partition manifest, Step `08` sites, and Step `08` input
  receipt; each is hash-bound and must fail with its exact diagnostic, no final
  set or owned scratch/lock, and preserved unrelated bytes. In contrast,
  mutate the selected R program after admission and preserve the current
  exit-`0` six-file publication. Assert that the summary omits Rscript path or
  version, R-program path or hash, R/package environment, run-token/attempt
  identity, and hashes for the other five native outputs. These omissions are
  provenance ceilings, not approval.
- **High — summary visibility needs one publication-order byte oracle:**
  publish one old-path direct-shell transaction checkpoint. Log the exact move
  order as all-sites, significant-sites, mutation-spectrum TSV, mutation-
  spectrum PDF, depth/delta PDF, then summary. Barrier-observe all six new
  finals after summary publication while final validation/hash checks are
  still pending, the owned lock remains, and a complete predecessor's six
  backups remain. Preserve unrelated bytes and release the barrier to complete
  one clean replacement. Summary visibility is not proof that
  `publication_committed` was reached. Existing cases remain owners of the
  all-six-or-none predecessor rule, ordinary publication and first-publication
  rollback, final-hash rollback, and incomplete restoration that leaves one
  final absent, its exact backup plus the owned recovery lock retained, the
  other five predecessors restored byte-for-byte, and owned temps removed.
- **High — signals and same-analysis contention need a separate small shell
  checkpoint:** after the summary becomes visible for a complete predecessor,
  controlled `TERM` must exit `143`, restore all six prior files byte-exactly,
  preserve unrelated bytes, and remove owned temps/backups/lock. A fake-R
  barrier must hold one admitted same-analysis run while a second exits `1` on
  the analysis lock; releasing the winner yields exactly one complete set and
  no owned residue. Neither the visible summary, names, hashes, timestamps,
  nor lock owner metadata provide a durable completed-attempt identity.
- **High — direct validator stability, evidence ceilings, and the new Step
  `09c` bridge need one bounded checkpoint:** in the existing validator test,
  add arbitrary-CWD dry-run/execute/repeat byte parity with no invocation-CWD
  residue and post-build mutation of each of the ten admitted inputs as exit
  `2` preserving a valid predecessor report. Existing exact cases already make
  every one of the seven check IDs independently observable as exit-`0` failed
  evidence. Add one all-pass false-evidence case with fabricated but internally
  self-consistent CMH statistic, p-value/BH, and common odds ratio to freeze
  that the validator recomputes depth/AF/background/status and BH only from
  reported p-values, but not count-table estimability, CMH statistic, p-value,
  or odds ratio. Preserve the overclaiming `status_semantics` expected text as
  a named defect. The neutral report suite remains owner of common loader and
  publication faults. During atomic cutover, add final-path coverage of the
  production Step `09c` bridge's exact-owner initialization, valid cache reuse,
  foreign/partial cache preservation, missing specification/loader, execution
  failure, owned partial-cache cleanup, sanitized public exit `2`, and
  unchanged `sys.path`.
- **High — Step `09` scheduler forwarding and stale-set behavior need one
  central checkpoint:** add direct Step `09` cases for unchanged forwarding of
  missing/nonexecutable or PATH-basename Rscript selections and a missing R
  program to child-owned validation; dynamic launch-CWD fallback when
  `SLURM_SUBMIT_DIR` is absent; dry-run `logs/`-only mutation; and an exit-`0`
  child that emits nothing while six stale nonempty outputs are accepted and
  retained byte-for-byte. Existing generic cases retain exact directives,
  explicit mode, one tolerated `module list`, full arguments, submit-CWD use,
  invalid mode, child exit, and missing-output rejection. The job performs no
  Rscript version probe or R/package activation and does not establish
  submitted-job behavior. These are scheduler defects and boundaries, not
  hardening.
- **Accepted R/oracle, artifact, slices, and coverage boundary:** the committed
  guarded-real-R and independent Python-oracle assets already cover manifest
  pairings, at least two strata, count-derived continuity-corrected two-sided
  CMH statistics/p-values/odds ratios, global BH, thresholds, background,
  degenerate/missing/low-coverage states, ordering, determinism, invalid
  pairings, and header-only output. Add no R/oracle test-only checkpoint or
  dependency action; run both exact owners at final-path acceptance. Existing
  artifact tests retain native/report identities, with cutover adding only the
  reviewed final producer path/hash assertion. Publish exactly five sequential
  test-only checkpoints—runtime/input provenance, publication order, signal/
  concurrency, validator, then scheduler—before the atomic eleven-move/ten-
  update cutover. Only the direct shell, direct validator, and central
  scheduler test owners may change; add no fixture, fourth test owner,
  production edit, coverage baseline, documentation batch, dependency, or
  future card. Final measurement must retain validator rates at or above
  `154/158` lines and `34/40` branches, keep every non-target row exact, and
  preserve global covered-count floors `9601/11758` lines and `3367/4784`
  branches.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, R package/runtime, scheduler, cluster, production, scientific-
  review, provisional-policy, editing-site, or biological state changed or
  ran.
- **Card-boundary gate:** `git diff --check` passes and the exact RUNBOOK
  documentation validator reports `PASS documentation structure (208 Markdown
  documents, 129 task cards, 6 Mermaid sources)`. No reliability-review path,
  lifecycle, dependency, cycle, orphan, schema, anchor, or diagram finding
  remains.
