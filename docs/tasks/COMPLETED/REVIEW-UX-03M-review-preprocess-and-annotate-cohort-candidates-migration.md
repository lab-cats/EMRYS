# REVIEW-UX-03M — Review cohort preprocessing migration usability

## Objective

Review `MIG-03M` for operator, maintainer, automation, recovery, provisional-
policy, R-environment, and evidence continuity across every explicit Step `08`
path change.

## Why this exists

The migration changes Bash, Rscript, validator, submitted-job, guarded-R,
Make/test/helper, and implementation-provenance paths across separate output
and QC roots. Correct relocation can still leave stale commands, hidden
R/input/output/lock selection, incorrect dry-run claims, unsafe split-root
retry guidance, biological overclaim, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, tables, messages, R packages,
  provisional orientation policy, annotation/candidate behavior, transaction,
  scheduler policy, artifact meaning, or evidence state.
- Preserve explicit repository-relative and absolute-path invocation without
  installation, ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fake-R/guarded-real-R migration evidence distinct from scheduler,
  cluster, production, completed scientific review, variant/editing-site, or
  biological-readiness proof.

## Blocked by

- [REVIEW-REL-03M](../COMPLETED/REVIEW-REL-03M-review-preprocess-and-annotate-cohort-candidates-migration.md) — Required: completed reliability review supplies the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03M](../TODO/MIG-03M-migrate-preprocess-and-annotate-cohort-candidates-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public Bash/R/
  Python CLI, arbitrary-CWD, guarded-R, scheduler submission, Make, runbook/
  troubleshooting, artifact, evidence-status, and rollback journeys.

## Required context

- `MIG-03M`; Step `08` runbook/troubleshooting commands; shell/R/validator
  help; public CLI and scheduler characterization; guarded-R/local-R routes;
  Make/literal expansions; coverage/artifact/helper paths; owner contract;
  current/future topology; manifests; Step `07`/annotation/R/output/QC/lock/
  receipt diagnostics; provisional-orientation language; and the split-root
  three-file transaction evidence boundary.

## Questions owned by this card

- None.

## In scope

- Root/arbitrary-CWD shell dry-run/execute and validator dry-run/execute/repeat
  journeys; direct Rscript and guarded-R test journeys; Rscript/R-program,
  manifest, Step `07`, annotation, output/QC, scratch, lock, and receipt
  selection; provisional-policy and non-biological wording; staged
  publication, restoration failure, mutation, relative annotation-path
  disagreement, cross-root residue, and safe preservation; scheduler submit
  CWD, modules/renv, logs, delegation, and stale outputs; Make/test commands;
  implementation/evidence provenance; owner findability; links; rollback; and
  next-safe-action instructions.

## Out of scope

- New aliases/wrappers, package installation, PATH/`PYTHONPATH` redesign,
  R/schema/method/policy changes, transaction or recovery redesign, scheduler
  hardening, cluster submission, dependency action, scientific/biological
  interpretation, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make Bash/R/validator/scheduler, distinct dry-
  run effects, cohort-barrier/provisional meaning, R/input/output/QC/lock/
  receipt selection, restoration residue, guarded-R/focused tests, evidence
  status, provenance, and rollback discoverable without an alias or overclaim.

## Canonical documentation updates

- This card, `MIG-03M`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, policy/scientific/
  biological claim, or an unreviewed alias/package contract.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `a6effa287ac88142aba785c827ab42261954077e`.

- **High — four supported journeys need exact final paths and prerequisites:**
  at documentation close replace every live shell, R, validator, job, direct-
  test, helper, artifact, and coverage path. Root shell use invokes the mode-
  `0755` final producer at
  `src/norad/stages/preprocess_and_annotate_cohort_candidates/step_08_vcf_preprocessing.sh`;
  its sibling R program is selected by default and direct Rscript use is a
  maintainer/fixture diagnostic, not a production bypass. Invoke the mode-
  `0644` validator with an explicit interpreter from the same owner. Submit the
  mode-`0644` owner-local job with `sbatch` from the checkout only after
  `mkdir -p logs`; explicit Bash is a local wrapper diagnostic, not scheduler
  execution. Arbitrary-CWD shell/validator use makes code, interpreter,
  Rscript, R program, both manifests, Step `07` root, annotation, output/QC,
  three native inputs, and report paths absolute. Use absolute Step `07` and
  annotation paths during production so recorded spelling is stable and
  validator-resolved annotation identity agrees. No installed command, public
  package/import, legacy alias, wrapper, symlink, ambient `PYTHONPATH`, or
  global `sys.path` route is supported.
- **High — shell, validator, guarded R, and scheduler effects must remain
  distinct:** shell dry-run validates every declared input plus Rscript/R-
  program resolution, prints the exact R command and split-root transaction,
  invokes no R child, and creates no output/QC directory, lock, scratch, or
  final. Validator dry-run snapshots six explicit inputs, prints five rows,
  invokes no R, and writes no report; execute requires the exact report parent
  to exist and may return `0` with failed rows. The owner-local guarded-R runner
  is semantic fixture evidence and a missing explicit runtime/package is a
  failure, not a pass or scheduler proof. Scheduler `EXECUTE=0` changes to the
  submit/fallback CWD, creates `logs/`, tolerates `module list` and Rscript
  version diagnostics, inherits caller R/`renv` startup state, and delegates
  shell dry-run. It neither restores packages nor makes dry-run side-effect-
  free; execute can accept a stale three-file set after a zero-output child.
- **High — split-root recovery is preservation-first and requires two fresh
  roots for any later diagnostic retry:** before cleanup, restoration, or
  retry, preserve all three finals; every output- and QC-root run-token temp/
  backup; lock/owner; manifests; annotation; Step `07` receipts/VCFs; selected
  Rscript/R program and package environment; unrelated bytes in both roots;
  producer/wrapper streams; scheduler job/accounting/logs; and checkout/submit
  CWD. Receipt-publication exit `67` plus prior-sites restoration exit `68`
  leaves the sites final absent with its backup surviving, restores prior input
  receipt and QC summary, removes the lock, and creates no marker. Do not
  combine attempts, reconstruct a member, remove a foreign lock, trust receipt
  visibility/counts/hashes/timestamps or stale wrapper success, or retry the
  same names. Rule out every Step `08` writer and Step `09`/`09c`/artifact
  reader first. A separately authorized nonproduction diagnostic retry uses an
  isolated output-root and QC-root pair.
- **Medium — cohort barrier, provisional policy, validation, and artifact
  language must stay exact:** Step `08` requires the full declared partition
  by `FWD_like`,`REV_like` universe. Under `legacy_provisional_v1`, FWD-like
  maps to annotation `+` with complemented genomic alleles and REV-like maps
  to `-` unchanged only as compatibility behavior. It is not validated library
  strand, sense/antisense, a variant or editing-site call, completed scientific
  review, or biological readiness. Producer exit `0` proves current local
  checks and publication but not R/package or attempt identity; the receipt
  omits sibling hashes. Validator exit `0` can contain failed rows and does not
  recompute candidate IDs/order, GTF overlap, allele mapping, or upstream
  filtering. Guarded-real-R passes remain local semantic fixtures; fake-R
  passes remain orchestration fixtures; scheduler exit `0` may be stale.
  Preserve the native input-receipt commit marker versus artifact
  `step08_summary_v1` failure-marker distinction without treating either as
  immutable-computation or readiness proof.
- **Accepted findability, tests, documentation, and rollback:** add one
  adjacent owner README that routes root/arbitrary-CWD shell and validator,
  sibling R and guarded-R use, checkout-root scheduler submission, manifest/
  Step `07`/annotation/R/output/QC/lock/receipt choices, focused direct and
  central tests, recovery preservation, artifact provenance, evidence limits,
  and next safe action. Correct the contract's unimplemented/flat/shared-
  publisher/deferred-migration wording and update every impact-directed
  architecture, inventory, test, ownership, runbook, troubleshooting,
  predecessor/consumer, artifact, manifest, local-R, roadmap/handoff, and
  lifecycle route only at migration close. Add a dedicated Step `08` split-
  root partial/restoration-failure route and link structured validation to it.
  Diagrams need no update because identity, direct DAG edges, and public flow
  do not change. Focused final commands use the owner-local shell, Python, and
  guarded-R tests plus central Step `08` scheduler selection. Revert
  documentation first, atomic cutover second, then scheduler, validator,
  signal/concurrency, transaction/recovery, and runtime/input-provenance
  baselines in reverse order. Git rollback never changes runtime artifacts or
  recovery evidence, and no compatibility surface is justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, R runtime/package, scheduler, cluster, production,
  scientific-review, provisional-policy, variant/editing-site, or biological
  evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passes and the exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings. No usability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only result is
  nonpassing, not green and not authority to alter inherited lifecycle state.
