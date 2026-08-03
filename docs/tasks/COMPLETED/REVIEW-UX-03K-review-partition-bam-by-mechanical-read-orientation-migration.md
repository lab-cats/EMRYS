# REVIEW-UX-03K — Review mechanical-orientation partition migration usability

## Objective

Review `MIG-03K` for operator, maintainer, automation, recovery, scientific-
language, and evidence continuity across every explicit Step `06` path change.

## Why this exists

The migration changes a directly executable Bash producer path, explicit-
interpreter validator path, submitted-job path and delegated command, Make/
coverage/test/helper paths, and implementation provenance. Correct relocation
can still leave stale commands, hidden samtools/thread/output/QC/lock
selection, biological-orientation overclaim, incorrect dry-run claims, unsafe
retry guidance, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler or tool
  policy, mechanical flag groups, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/fake-tool migration evidence distinct from real samtools,
  scheduler, cluster, production, scientific-review, biological-orientation,
  or biological-readiness proof.

## Blocked by

- [REVIEW-REL-03K](REVIEW-REL-03K-review-partition-bam-by-mechanical-read-orientation-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03K](../IN_PROGRESS/MIG-03K-migrate-partition-bam-by-mechanical-read-orientation-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03K`; Step `06` runbook/troubleshooting commands; producer and validator
  help; public CLI and scheduler characterization; Make/literal expansions;
  coverage/artifact/helper paths; owner contract; current/future topology;
  samtools/thread/output/QC/lock diagnostics; mechanical-orientation language;
  and five-file transaction evidence boundary.

## Questions owned by this card

- None.

## In scope

- Direct producer and explicit-interpreter validator root/arbitrary-CWD dry-
  run/execute/repeat journeys; exact mechanical-orientation wording; samtools,
  thread, output/QC, scratch, and lock selection; staged publication, rollback
  failure, collision, residue, and safe preservation; scheduler submit CWD,
  modules, overrides, version, CPU/thread state, logs, Bash `3.2`, delegation,
  and stale outputs; Make/test commands; implementation/evidence provenance;
  owner findability; links; rollback; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/`PYTHONPATH` redesign,
  transaction repair, receipts/markers, counts or flag policy, scheduler
  hardening, cluster submission, dependency action, biological-orientation
  interpretation, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, mechanical labels, tool/thread/directory/lock selection, rollback
  residue, focused tests, evidence status, provenance, and rollback
  discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03K`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, biological-orientation
  claim, or an unreviewed alias/package contract.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `3f71f877627d039b158ded9b5f470c04ee1424b0`.

- **High — every supported journey needs one explicit final path:** at
  documentation close, replace every live Step `06` producer, validator, job,
  focused-test, helper-matrix, artifact-provenance, and coverage path. Root use
  directly invokes the mode-`0755` producer at
  `src/norad/stages/partition_BAM_by_mechanical_read_orientation/step_06_split_bam_by_read_orientation.sh`
  and uses an explicit interpreter for the mode-`0644` validator. Arbitrary-CWD
  use makes the producer/interpreter, input BAM, output and QC directories,
  samtools, validator BAM/BAI/counts/report, scheduler checkout, and final owner
  paths absolute. No installed command, package import, legacy alias, wrapper,
  symlink, ambient `PYTHONPATH`, or global `sys.path` route is supported.
- **High — producer, validator, and scheduler dry runs have distinct effects:**
  producer dry-run validates the exact adjacent BAI, positive threads, and
  samtools resolution; prints both directories, run-token temp/backup/lock
  paths, mechanical flags, counts, validation, publication, and rollback plan;
  invokes no samtools command; and creates neither directory. Validator dry-run
  reads all five explicit inputs, prints five TSV rows plus the completion line,
  invokes no samtools, and writes no report. Scheduler submission starts at the
  checkout, creates `logs/` before `sbatch`, and names the final mode-`0755`
  job. Preserve submit-CWD fallback, exported `/tmp`, sample/input/output/QC/
  thread defaults and overrides, tolerated module diagnostics, fixed samtools
  path with override, version-command failure, warning-only unusable preflight,
  one requested CPU independent of `THREADS`, body-level `logs/`, Bash `3.2`
  dry-run failure, exact delegation, and stale-five-file false success.
- **High — recovery guidance must cover two directories and nonserializing
  locks:** before cleanup, same-name retry, or recovery, preserve all five
  finals, every run-token temporary/backup in both output and QC directories,
  output-directory lock and owner, input BAM/BAI, unrelated files, producer and
  wrapper streams, job/accounting/logs, checkout/submit CWD, overrides, and
  selected samtools path/version. A failed restore can leave the prior FWD BAM
  missing while restoring the other four files and erasing backups, lock,
  scratch, and every recovery marker. Distinct output-directory locks can both
  succeed while a shared QC path is last-writer-wins. Absence of residue is not
  proof of clean or single-attempt state. Rule out every producer and Step `07`
  reader; do not combine members, infer identity from timestamps/counts, remove
  a foreign lock, reconstruct a missing file, or adopt stale wrapper success.
  Any separately authorized diagnostic retry uses both isolated output and QC
  directories. Git rollback never restores or authenticates runtime artifacts.
- **Medium — ownership, validation, and provenance wording must match the
  final implementation:** update the contract's unimplemented/flat-owner,
  stale test-path, generic Step-`00a` publisher attribution, and deferred-
  migration text to the final owner, mirrored tests, and neutral
  `validation_report.py`. Producer exit `0` proves nonempty/quickchecked merged
  BAMs, indexes, bounds, and publication but can retain flag-subcount/merged-
  count disagreement; it proves neither biological orientation nor current-
  attempt identity. Validator exit `0` may publish failed rows and neither
  quickchecks nor recounts BAMs. Scheduler exit `0` may accept five stale
  files. Artifact evidence changes only implementation path/hash; six
  identities and meanings stay fixed. Historical six-sample cluster
  observations remain historical, not migration proof.
- **Accepted findability, tests, documentation, and rollback:** add one adjacent
  owner README, repair the contract, inventory, architecture count, test
  baseline, documentation ownership, Step `06` runbook commands, and a new
  Step `06` producer/wrapper recovery route that the structured-validation
  section links. Direct predecessor/consumer semantics already use stable
  Step `05`/`07` identities and need no path change; diagrams need no update.
  The README and runbook own root/arbitrary-CWD producer and validator commands,
  checkout-root scheduler submission, focused direct/central tests,
  preservation, provenance, evidence ceiling, and next safe action. Revert
  documentation first, the atomic five-move/nine-update cutover second, then
  scheduler, validator, producer stability/collision, transaction, and child/
  count baselines in reverse order. No compatibility surface is justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, real samtools, scheduler, production, scientific-
  review, biological-orientation, or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No usability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not green and not authority to alter inherited lifecycle state.
