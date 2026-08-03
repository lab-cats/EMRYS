# REVIEW-UX-03H — Review RSeQC-paired-orientation evidence migration usability

## Objective

Review `MIG-03H` for scientist, operator, maintainer, automation, and recovery
continuity across every explicit Step `03` path change.

## Why this exists

The migration changes a Bash-only producer path, an interpreter-only validator
path, a submitted-job path and delegated command, demo targets, Make/coverage/
test paths, implementation provenance, and direct-final output diagnostics.
Correct code can still leave stale commands, hidden CWD-sensitive RSeQC
selection, incorrect dry-run mutation claims, biological-strandedness overclaim,
or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, native output, messages, scheduler
  policy, tool selection, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real RSeQC, scheduler,
  cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03H](../COMPLETED/REVIEW-REL-03H-review-collect-rseqc-paired-orientation-evidence-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03H](../IN_PROGRESS/MIG-03H-migrate-collect-rseqc-paired-orientation-evidence-owner.md) — Fully: migration selection began after all three reviews closed.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make/demo, runbook/
  troubleshooting, artifact, evidence-status, and rollback journeys.

## Required context

- `MIG-03H`; Step `03` runbook/troubleshooting commands; producer and validator
  help; public CLI and SLURM characterization; Make/literal expansions;
  coverage/artifact paths; owner contract; current/future topology; and non-
  gating mechanical-orientation evidence boundary.

## Questions owned by this card

- None.

## In scope

- Explicit-`bash` producer commands; help/malformed/arbitrary-CWD journeys;
  truthful side-effect-free dry-run and CWD-sensitive `.venv`/PATH RSeQC
  selection; execute, replacement, partial/truncated-output preservation;
  explicit-interpreter validator dry-run/execute/repeat/arbitrary-CWD journeys;
  scheduler submit CWD, virtualenv, defaults/overrides, Bash `3.2`, logs and
  output checks; Make/demo/test commands; implementation and evidence
  provenance; owner findability; links; rollback; non-gating mechanical-
  orientation status; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  transaction repair, receipts/markers, BAI/sample/tool/scientific policy,
  strandedness derivation, scheduler hardening, cluster submission, dependency
  actions, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, binary selection, partial/stale output, focused tests, evidence
  status, provenance, and rollback boundaries discoverable without an alias or
  proof overclaim.

## Canonical documentation updates

- This card, `MIG-03H`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `c0c60da38c3c2f3d254faa48aa675e975a9454c7`.

- **High — stale commands need complete final journeys:** at documentation
  close, replace every active Step `03` producer, validator, job, demo, and
  focused-test path. Repository-root producer journeys must invoke the mode-
  `0644` file through Bash with explicit sample, BAM, BED12, output directory,
  and RSeQC binary. The arbitrary-CWD journey must use absolute producer,
  input, output, and binary paths because the default `.venv` lookup is
  relative to the caller's CWD. Dry-run validates BAM, either adjacent BAI,
  BED12, and the selected executable without creating the output directory or
  report; only an explicit `--execute` permits those mutations.
- **High — validator and scheduler routes need distinct effects:** validator
  journeys must use an explicit Python interpreter for dry-run, execute,
  repeat, and arbitrary-CWD forms, create the output parent before execute,
  and distinguish exit `0` with published failed rows from exit `2` with no
  new publication. Scheduler submission must start at the checkout and use the
  final mode-`0644` job path. Document `SLURM_SUBMIT_DIR`, exported `/tmp`,
  `SAMPLE_ID`, `BAM`, `BED12`, `OUTPUT_DIR`, `INFER_EXPERIMENT_BIN`, and
  `EXECUTE`; optional activation; `.venv` preference and PATH fallback;
  tolerated `module list`; dry-run `logs/` creation; and the Bash `3.2` empty-
  array failure. The two Make demo targets exercise wrapper commands with
  local mocks and may mutate logs; they are not scheduler or cluster proof.
- **High — recovery guidance must preserve characterized evidence:** direct-
  final producer execution has no lock, stage, backup, receipt, stable-input
  check, or rollback. A tool failure or empty success can replace a predecessor
  with partial or zero bytes, and the wrapper can report success after an
  exit-`0` child emitted nothing if a stale named report is already nonempty.
  Troubleshooting must preserve the report, unrelated files, stdout, stderr,
  scheduler job identity, logs, selected tool/path, BAM/BAI, and BED12 before
  any retry or cleanup decision; it must not promise repository recovery for
  runtime artifacts.
- **Medium — status and provenance need explicit ceilings:** producer exit `0`
  proves only a nonempty file. Validator exit `0` can publish failed rows. The
  fractions remain non-gating mechanical paired-read-orientation evidence and
  do not establish transcript strand, biological sense/antisense, an approved
  library-strandedness policy, or a manifest update. The owner README must
  route exact final producer/hash provenance, direct and central focused tests,
  reverse-order Git rollback, and the fixture/mock local-only ceiling. Existing
  operational observations must not be presented as migration, scheduler,
  cluster, production, scientific-review, or biological proof.
- **Accepted findability and rollback:** one adjacent README plus the updated
  contract, runbook, troubleshooting, inventory, baseline, ownership map,
  architecture, roadmap, handoff, lifecycle links, and audit provide complete
  navigation. Roll back documentation first, the final owner/caller/coverage
  cutover second, and the old-path test baseline third; no legacy alias,
  wrapper, compatibility copy, package, or installable command is justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, real RSeQC, scheduler, production, scientific-
  review, or biological evidence changed or ran.
