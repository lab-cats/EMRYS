# REVIEW-LEGACY-05A — Confirm Step 05 operational checker ownership

## Objective

Complete a no-loss ownership review of
`tests/data_checks/validate_step05_outputs.sh` and record its permanent current
repository owner without changing the executable or its behavior.

## Why this exists

The residual source-topology campaign has completed every planned `MOVE`
through `MIG-04F`, but `PLAN-03A` retained this repository-level Step `05`
operator checker for a separate review. It still supplies scheduler-state,
multi-sample status, a best-effort persisted TSV snapshot, output-size, and
scratch-inspection behavior
that the final stage validator does not own. A bounded review must therefore
close the current path intentionally rather than infer that the checker is a
duplicate test or move it into a stage or deferred scheduler owner.

## Fixed decisions

- Review only `tests/data_checks/validate_step05_outputs.sh`. The pending Step
  `04` scaffold remains a separate unselected no-loss review.
- Treat the checker as a repository-level operational inspection interface,
  not a direct Step `05` regression test or stage-native structured validator.
- The evidence-supported current end state is `RETAIN_ROOT` at
  `tests/data_checks/validate_step05_outputs.sh`. Its permanent owner under the
  current architecture is `tests/data_checks/`; only a separately selected
  future scheduler or operator-interface redesign may reconsider that
  boundary.
- Keep the file byte-identical at mode `0755`, size `5,413` bytes, and SHA-256
  `aa72defed3f96bd327e969dfd98f303182ede6d7fe417d8bf7039faedbaa95a9`.
- Preserve its current CLI, six-sample default cohort, optional `--jobs`
  mapping, `squeue`/`sacct` fallback, twelve-column TSV, BAM/BAI and header/read-
  group checks, scratch census, aggregate statuses, and exit codes `0`, `1`,
  and `2`.
- Preserve without approving or repairing the characterized duplicate
  truncating `tee` writers and silent replacement of a writable output file.
- The final Step `05` validator remains the stage-native structured validator.
  It accepts one explicit BAM/BAI/reference scope and emits the neutral
  validation-report contract; it does not replace the checker's scheduler,
  cohort, scratch, TSV, or aggregate-exit behavior.
- Retain the current Runbook reference to its historical six-sample operator
  use. This review creates no new runtime, cluster, production, scientific-
  review, or biological evidence.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Start from clean, published, live-remote-equal `MIG-04F`
  documentation/lifecycle close
  `65be0878269752dd8482d1807e41ce68c08fd6ad`.
- Reverify the file identity, Git history, exact repository references, lack of
  an automated caller, current Runbook reference to historical operator use,
  known defects, and behavior not supplied by the final Step `05` validator.

## Required context

- Completed `PLAN-03A` and `MIG-04F`; the functional-owner inventory;
  `SOURCE_TOPOLOGY.md`; `PIPELINE_PLAN.md`; the Step `05` checker, final
  validator, and adjacent contract; the current test baseline; and the exact
  Runbook section that records its historical operator use.

## Questions owned by this card

- None.

## In scope

- One static no-loss behavior/ownership comparison; a permanent current
  `RETAIN_ROOT` decision; exact current-path, mode, hash, reference, and defect-
  preservation evidence; and impact-directed documentation/lifecycle close.

## Out of scope

- Editing, running, moving, renaming, retiring, hardening, or automating the
  checker; adding a Make/test route; changing its CLI, TSV, status, scheduler,
  scratch, output, overwrite, or exit behavior; changing the Step `05`
  producer or final validator; selecting a scheduler owner; the pending Step
  `04` scaffold; final residual audit; ingestion, orchestration/profile,
  runtime execution, cluster, production, scientific-review, or biological
  work.

## Deliverables

- A documented no-loss disposition that keeps the exact checker at its
  permanent current repository-level owner and distinguishes it from the
  stage-native final validator.

## Acceptance evidence

- Exact static searches show the current Runbook historical reference and
  ownership references, no Make/test-harness caller, and no substitute for the
  checker's unique scheduler/cohort/TSV behavior.
- An explicit behavior crosswalk distinguishes the checker from the final
  Step `05` validator and records why neither `MOVE` nor `RETIRE` is safe or
  necessary under the current architecture.
- Git proves the checker remains byte-identical at mode `0755`, size `5,413`
  bytes, and the frozen SHA-256 above.
- `git diff --check`, documentation validation, and independent semantic close
  reviews pass. Computational tests are not applicable because no executable,
  test, fixture, configuration, dependency, or selection surface changes.
- Evidence remains static no-loss review plus preserved historical operator
  evidence only, not new runtime, cluster, production, scientific-review, or
  biological-readiness evidence.

## Canonical documentation updates

- Functional-owner inventory, source-topology repository-development
  boundary, current test-baseline defect boundary, Runbook ownership
  clarification, `PIPELINE_PLAN.md`, `HANDOFF.md`, lifecycle routes,
  documentation ownership, and this card.

## Escalation conditions

- Stop for any external or automated caller not represented in the repository;
  any need to change or execute the checker; any unresolved unique behavior;
  any need to choose a stage or scheduler owner; any defect repair or evidence
  promotion; or scope into the pending Step `04` scaffold, final audit,
  scheduler, ingestion, orchestration/profile, runtime execution, cluster,
  production, scientific-review, or biological work.

## Completion record

Selected from clean, published, live-remote-equal `MIG-04F`
documentation/lifecycle close
`65be0878269752dd8482d1807e41ce68c08fd6ad`. Three bounded read-only audits
confirmed the checker is a tracked repository-level operator utility with a
current historical Runbook reference and no Make, test-harness, source, or
automated-job caller; that the final Step `05` validator does not supply its
scheduler-state, cohort, scratch, best-effort persisted TSV snapshot, or
aggregate-exit behavior; and that moving or retiring it would create an
unowned contract or needless public-path break. Documentation-only decision
work has not begun.
