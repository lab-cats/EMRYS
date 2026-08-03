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

Selected as the sole active migration review from clean, published,
local/upstream/live-remote-equal reliability completion
`fd000947d01807fcce00c5eb283181929f26caed`. No usability finding is
recorded yet, no migration or later card is selected, and no executable/test
file changed or ran.
