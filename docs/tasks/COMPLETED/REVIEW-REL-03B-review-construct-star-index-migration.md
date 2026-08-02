# REVIEW-REL-03B — Review `construct_STAR_index` migration reliability

## Objective

Challenge `MIG-03B` against the complete mocked job, validator, publication,
artifact-evidence, coverage, and rollback behavior before source movement.

## Why this exists

The current producer executes implicitly, mutates caller-relative reference
paths, reuses materialized inputs, and has no final validation transaction; the
validator has safety-critical publication behavior and known retained defects.
Relocation must not normalize, hide, or accidentally correct those states.

## Fixed decisions

- Review only; do not fix or bless a characterized defect.
- Preserve exact SLURM directives/module/STAR/exit behavior and the validator's
  complete neutral-report publication contract.
- Treat coverage and artifact implementation-evidence paths as explicit
  migration obligations, not disposable metadata.

## Blocked by

- [REVIEW-ARCH-03B](../COMPLETED/REVIEW-ARCH-03B-review-construct-star-index-migration.md) — Required: reliability review needs the corrected owner, caller, and rollback boundary.

## Completion unblocks

- [REVIEW-UX-03B](REVIEW-UX-03B-review-construct-star-index-migration.md) — Fully: public and maintainer continuity can be reviewed after failure-state obligations are fixed.

## Prerequisites

- Start from the committed architecture-reviewed card and map each current job,
  validator, publication, artifact, and coverage state to a final-path test
  owner without modifying or running it.

## Required context

- `MIG-03B`; the job and validator; the owner contract;
  `test_slurm_wrapper_contracts.py`; the direct validator suite;
  `test_validation_report.py`; `test_validation_check_rosters.py`;
  artifact-index producer evidence; coverage config/tool/baseline; and the
  applicable risk rows in `TEST_BASELINE.md`.

## Questions owned by this card

- None.

## In scope

- Implicit execution, caller-CWD and directory effects, decompression/reuse,
  module and STAR failures, stdout/stderr and exits, validator dry-run/execute,
  deterministic reports, locks/replacement/rollback/cleanup/residue,
  implementation evidence hashes/paths, file modes, exact coverage rename
  accounting, atomic commit safety, and reverse rollback.

## Out of scope

- Correcting job transactions or validator publication gaps, adding a dry-run,
  changing reference inputs, cluster execution, dependency work, scientific
  policy, or another owner.

## Deliverables

- A risk-to-test disposition for each applicable success, failure, side-effect,
  residue, and rollback state, with exact `MIG-03B` corrections in the dated
  refactor log.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named final-path regression owner.
- The planned gate proves the coverage rename and distinguishes mocked/local
  parity from real-runtime, cluster, production, scientific, and biological
  evidence.

## Canonical documentation updates

- This card, `MIG-03B`, `PIPELINE_PLAN.md` only if order changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a fault state lacks a local oracle, path relocation changes reference
  or publication behavior, artifact evidence requires a schema change, or
  coverage parity cannot be measured across the rename.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
architecture checkpoint `94199dc` after selection checkpoint `22dd2d4`. One
high finding added missing old/new mocked-producer coverage for prepared-
reference reuse, default threads, partial-success/no-validation, module/STAR
failures, and their retained side effects. A second high finding added full
validator dry-run and execute/repeat parity from a non-repository CWD. Two
medium findings require copied-validator fault fixtures to reproduce each real
relative layout and require a focused artifact implementation-evidence path/
hash assertion. Coverage is frozen at `165/189` covered/statements and `42/60`
covered/total branches; final measurement must prove those counts before the
reviewed baseline update overwrites the tracked snapshot. All shared
publication success/failure/interruption/residue states and named defects remain
owned by the neutral fault suite and are explicitly preserved. No escalation
condition was triggered. The same campaign agent performed the pass, so
independent authorship is not claimed. No executable/test file changed and no
computational test ran.
