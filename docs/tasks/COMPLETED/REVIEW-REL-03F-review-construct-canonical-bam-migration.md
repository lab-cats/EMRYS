# REVIEW-REL-03F — Review `construct_canonical_BAM` migration reliability

## Objective

Challenge `MIG-03F` against neutral-helper, producer, validator, scheduler,
artifact, coverage, fault, residue, and rollback behavior before source
movement.

## Why this exists

The producer replaces a canonical BAM/BAI pair through staged validation,
backup, two final moves, final validation, and best-effort rollback. A failure
inside rollback can lose recovery evidence without a receipt or marker. The
validator is intentionally less strict than the producer, and the proposed
helper extraction adds three exact-loader fault surfaces. Relocation must
preserve and characterize each state without approving it.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer commands/state machine, scheduler directives/modes/
  failures, validator publication/asymmetries, helper bytes/exceptions, artifact
  identity, and coverage policy.
- Treat old/helper/final identical-input parity, exact-loader faults, rollback-
  failure residue, and stable-input evidence as named obligations; a broad
  passing suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03F](../COMPLETED/REVIEW-ARCH-03F-review-construct-canonical-bam-migration.md) — Required: reliability review needs the architecture-corrected helper, owner, caller, and slice boundary.

## Completion unblocks

- [REVIEW-UX-03F](../IN_PROGRESS/REVIEW-UX-03F-review-construct-canonical-bam-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed cards and map every helper,
  producer, validator, job, artifact, coverage, and recovery state to one named
  regression owner without modifying or running executable files.

## Required context

- `MIG-03F`; Step `02` producer/validator/job and direct tests; Step `04`/`05`
  helper uses and direct tests; central scheduler matrix; shared validation-
  report faults; proposed neutral helper/loader contract; roster and public-CLI
  suites; artifact evidence; coverage tool/baseline; and applicable
  `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled fault can freeze the current failure-inside-rollback state
  without changing cleanup, and exactly which final/backup/lock/temp bytes must
  be preserved as ambiguous recovery evidence?
- What loader fault matrix is required once for the neutral owner and at each
  distinct caller depth without duplicating an entire framework across Step
  `02`, Step `04`, and Step `05` tests?

## In scope

- Helper argument/result/header parity and cache/spec/load failures; producer
  CLI/dry-run/execute/staging/validation/pair-state/lock/temp/backup/publish/
  rollback/cleanup/signal/stream states; validator tool/header/count, dry-run/
  execute/repeat, stable-input, publication, and documented asymmetries;
  scheduler CWD/module/directory/Bash `3.2`/child/output/stream states; modes,
  hashes, artifact evidence, coverage extraction/rename, and commit rollback.

## Out of scope

- Correcting rollback, adding receipts/recovery markers, changing replacement
  or BAM/read-group policy, tightening the validator to producer semantics,
  moving downstream owners, scheduler hardening, dependency work, real
  samtools/SLURM/production execution, or scientific policy.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and rollback state, with exact card corrections and dated
  audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named pre-extraction/helper/final-path regression owner.
- Coverage and parity distinguish local fixture/mock evidence from real
  samtools, scheduler, cluster, production, scientific-review, and biological
  evidence.

## Canonical documentation updates

- This card, `MIG-03F`, roadmap/handoff only where status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks a safe oracle, extraction changes helper
  results/exceptions, relocation changes producer/job/report behavior, artifact
  evidence needs schema change, or coverage and exact-loader parity cannot be
  measured.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `a49e45c765582126d42cffa3a039524db4a190a5` after architecture
checkpoint `c429d8d`.

- **High — failure inside rollback lacked an exact safe oracle:** extend only
  the moved producer shell suite's fake `mv` so final BAI publication fails and
  restoration of the prior BAM then fails. Old and final paths must return
  nonzero, report both the rollback attempt and forced restoration failure,
  retain the prior BAI bytes while leaving the canonical BAM absent, remove
  both backups and the owned lock, and leave no run-token scratch. This
  lockless partial pair and lost prior BAM are a characterized ambiguous/data-
  loss defect, not a successful restore or authority to repair production data.
- **High — helper extraction needed byte/exception and loader-fault proof:**
  capture the old Step `02` `run_tool` argv/result and representative
  `parse_header` outcomes before extraction. The neutral suite must compare
  those bytes/results after extraction and own healthy reuse, missing file,
  foreign wrong-path cache, correct-path incomplete API, and loader-owned
  execution failure for all three callers at both flat and final Step `02`
  depths. It must preserve foreign cache objects and `sys.path`, remove only an
  owned partial, require both callables plus readiness, and prove the exact
  path/type/reason diagnostic appears before report publication or CWD residue.
- **Medium — the direct validator suite lacked a complete relocated journey:**
  add one non-repository-CWD dry-run, execute, and repeat journey at the moved
  path. It must preserve the exact ordered five rows and deterministic report
  bytes, empty successful stderr, stable replacement, input bytes/modes, and an
  empty invocation directory. Existing shared publication-fault and roster
  suites continue to own their independent contracts.
- **Accepted independent owners:** the moved shell suite owns the producer
  state machine and new rollback-failure oracle. The neutral BAM suite owns
  helper/loader faults. The moved validator suite owns the arbitrary-CWD
  journey. The existing central scheduler matrix already freezes mode `0644`,
  directives, caller CWD, strict/tolerated modules, defaults, Bash `3.2`, child
  status, output checks, and streams; no duplicate scheduler harness is
  justified.
- **Coverage disposition:** the exact starting rows are Step `02` `105/115`
  lines and `21/28` branches, Step `04` `105/114` and `22/28`, and Step `05`
  `98/108` and `19/24`; global covered-count floors are `9381/11549` lines and
  `3293/4714` branches. Only those three rows plus the new helper may change.
  Final measurement must retain each old row's line/branch rate, retain at least
  the combined `308` covered lines and `62` covered branches across those four
  rows, keep every non-target row exact, and give the helper at least 90% line
  and 85% branch coverage before updating the committed baseline.
- **Evidence boundary:** this was a read-only committed-time adversarial pass
  by the same campaign agent; independent authorship is not claimed. No source,
  test, dependency, runtime tool, scheduler, production, scientific-review, or
  biological evidence changed or ran. The safe fixture oracle exists, so no
  escalation condition was triggered.
