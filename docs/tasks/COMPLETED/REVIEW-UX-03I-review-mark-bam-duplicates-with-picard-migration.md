# REVIEW-UX-03I — Review MarkDuplicates migration usability

## Objective

Review `MIG-03I` for operator, maintainer, automation, recovery, and evidence
continuity across every explicit Step `04` path change.

## Why this exists

The migration changes a Bash-only producer path, an interpreter-only validator
path, a submitted-job path and delegated command, Make/coverage/test/helper
paths, implementation provenance, and direct-final multi-output diagnostics.
Correct code can still leave stale commands, hidden Picard/Java/samtools/temp
selection, incorrect dry-run claims, unsafe retry guidance, or an
undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, native outputs, messages, scheduler
  policy, tool selection, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real Picard, Java,
  samtools, scheduler, cluster, production, scientific-review, or biological
  proof.

## Blocked by

- [REVIEW-REL-03I](../COMPLETED/REVIEW-REL-03I-review-mark-bam-duplicates-with-picard-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03I](../TODO/MIG-03I-migrate-mark-bam-duplicates-with-picard-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03I`; Step `04` runbook/troubleshooting commands; producer and validator
  help; public CLI and SLURM characterization; Make/literal expansions;
  coverage/artifact/helper paths; owner contract; current/future topology;
  Java/Picard/samtools/`TMPDIR` diagnostics; and multi-output evidence boundary.

## Questions owned by this card

- None.

## In scope

- Explicit-Bash producer commands; help/malformed/arbitrary-CWD journeys;
  truthful side-effect-free dry-run; Picard jar, Java, samtools, and `TMPDIR`
  selection; execute, silent replacement, partial/empty/cross-attempt output
  preservation; explicit-interpreter validator dry-run/execute/repeat/
  arbitrary-CWD journeys; scheduler submit CWD, modules, overrides, actual Java
  version, Bash `3.2`, logs and output checks; Make/test commands;
  implementation/evidence provenance; owner findability; links; rollback; and
  next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  transaction repair, receipts/markers, duplicate/sample/library/platform/tool
  policy, scheduler hardening, cluster submission, dependency actions, or
  future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, tool/temp selection, partial/mixed/stale outputs, focused tests,
  evidence status, provenance, and rollback discoverable without an alias or
  proof overclaim.

## Canonical documentation updates

- This card, `MIG-03I`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `8a85fb3b09f584d3b888f4b12505e3a625a6434a`.

- **High — every active journey needs one unambiguous final path:** at the
  documentation close, replace all live Step `04` producer, validator, job,
  focused-test, helper-matrix, artifact-provenance, and coverage commands. The
  repository-root producer remains a mode-`0644` Bash surface at
  `src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh`;
  the arbitrary-CWD form must use absolute producer, input, output, metrics,
  Picard, Java, samtools, and `TMPDIR` paths. The mode-`0644` validator requires
  an explicit interpreter for dry-run, execute, repeat, and absolute-path
  arbitrary-CWD journeys. No installed command, package import, legacy alias,
  wrapper, symlink, or ambient `PYTHONPATH` route is supported.
- **High — producer, validator, and scheduler dry runs have distinct effects:**
  the producer validates exact `<bam>.bai`, tools, jar, and existing writable
  `TMPDIR` but creates no output or metrics directory; validator dry-run prints
  five TSV rows and writes no report. Scheduler submission starts at the
  checkout, creates `logs/` before `sbatch` because SLURM opens log paths before
  the body, and uses the final mode-`0644` job path. Document `SLURM_SUBMIT_DIR`
  fallback, exported `/tmp`, `SAMPLE_ID`, `INPUT_BAM`, `OUTPUT_DIR`,
  `METRICS_DIR`, `EXECUTE`, strict Picard/samtools loads, required `PICARD`,
  Java override/home/PATH resolution, actual-version floor, PATH samtools,
  tolerated module lists, body-level `logs/` mutation, and Bash `3.2` dry-run
  failure.
- **High — the unset-`JAVA_HOME` defect needs an owned next action:** even with
  a valid `JAVA_BIN_OVERRIDE`, a truly absent `JAVA_HOME` reaches the later
  unguarded diagnostic and aborts under `set -u` before child delegation. The
  runbook and troubleshooting route must name this defect without calling it a
  clean Java-selection failure or fixing it. Preserve stdout/stderr, module
  diagnostics, selected executable and actual `-version`, `PICARD`, samtools
  path, submit directory, and job identity; explicitly setting the intended
  environment for a new isolated attempt is operator action, not migration
  evidence.
- **High — direct-final recovery guidance must not authorize same-name retry:**
  preserve BAM, BAI, metrics, canonical input pair, unrelated files, output and
  metrics directories, child/wrapper streams, scheduler logs, job identity,
  and exact tool paths/versions before deciding anything. Picard, quickcheck,
  index, final-check, or stale-wrapper success can leave a new/partial/prior
  triplet with no lock, stage, backup, receipt, stable-input check, or recovery
  marker. Do not combine members, delete residue, or infer one attempt from
  timestamps. After confirming no downstream reader and retaining the original
  evidence, a deliberately isolated output/metrics destination is the safe
  diagnostic retry route; Git rollback never restores runtime artifacts.
- **Medium — validation, ownership, and provenance need explicit ceilings:**
  producer exit `0` proves quickcheck plus nonempty paths, not duplicate flags,
  BAM/BAI/metrics correspondence, or sample/library/platform binding. Validator
  exit `0` may publish failed rows; exit `2` means no new publication. Update
  the contract's stale pre-migration text and stale Step-`00a`/Step-`02` helper
  attribution to the final owner plus neutral `validation_report.py` and
  `bam_validation.py` exact-file owners. Artifact evidence changes only the
  implementation path/hash; four identities and meaning stay fixed. Historical
  cluster observations remain historical, not new migration proof.
- **Accepted findability, tests, and rollback:** one adjacent owner README plus
  the reviewed canonical roster provides the final commands, focused direct
  producer/validator and central scheduler/helper/artifact tests, provenance,
  evidence ceiling, and recovery links. Roll back documentation first, the
  atomic five-move/ten-update cutover second, then scheduler, validator, and
  producer baseline slices in reverse order. No alias or compatibility path is
  justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, real Picard, Java, samtools, scheduler, production,
  scientific-review, or biological evidence changed or ran.
