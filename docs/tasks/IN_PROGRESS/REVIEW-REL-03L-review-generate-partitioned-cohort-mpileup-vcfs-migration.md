# REVIEW-REL-03L — Review partitioned cohort mpileup migration reliability

## Objective

Challenge `MIG-03L` against producer, validator, scheduler, artifact, coverage,
three-file receipt-last publication, predecessor restoration, cleanup/residue,
stable-input, selector, manifest, VCF/count, bcftools, and rollback behavior
before source movement.

## Why this exists

The producer has a cohort/partition lock, run-token scratch, staged VCF
validation, three backups, receipt-last publication, and rollback, but the
receipt becomes visible before final validation and has no durable attempt
identity. Only manifests are hash-bound and snapshot-rechecked; restoration is
best-effort; VCFs are unhashed; and validator coverage is intentionally
shallower than producer selector and bcftools validation. The wrapper adds
module, tool, logging, and stale-output states. Migration must preserve and
characterize these defects without fixing or approving them.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer transaction, mechanical-label/pileup/filter
  behavior, validator/report semantics, scheduler directives/tool modes/
  failures, artifact identity, and coverage policy.
- Treat identical-input old/final parity, restoration failure, predecessor
  and recovery residue, input mutation, receipt visibility/identity,
  relative-path disagreement, stable input, selector asymmetry, and exact
  streams/exits as named obligations; broad suite success is not a substitute.

## Blocked by

- [REVIEW-ARCH-03L](../COMPLETED/REVIEW-ARCH-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Satisfied: architecture fixed the exact owner, loader, caller, artifact, test, and cutover boundary.

## Completion unblocks

- [REVIEW-UX-03L](../TODO/REVIEW-UX-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Fully: public and maintainer continuity follows fixed fault, preservation, and parity obligations.

## Prerequisites

- Start from committed architecture-reviewed cards and map every producer,
  validator, scheduler, private loader/test helper, artifact, coverage, and
  recovery state to one named regression owner without modifying or running
  executable files.

## Required context

- `MIG-03L`; Step `07` producer/validator/job and direct tests; central
  scheduler matrix; neutral validation-report fault suite; roster/public-CLI
  suites; artifact reconciliation and coverage evidence; partition manifests;
  runbook/troubleshooting; historical bcftools/Step `07` evidence; and
  applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- Which controlled mpileup, filter, VCF-header/sample/count, receipt-write,
  backup, publication, final-validation, restoration, cleanup, signal, lock,
  stale-path, and input-mutation states safely freeze predecessor/recovery
  residue, and which bytes, directories, streams, exits, and unrelated files
  must old/final paths retain?
- How are receipt-last visibility, all-three-or-none predecessor admission,
  manifest-only stability, absent input/output hashes and attempt marker,
  relative output-root mismatch, header-only VCFs, and validator exit-`0`
  failed rows preserved without claiming immutable, scientific, calling, or
  biological guarantees?
- Which `region`/`regions_file`, FAI bounds, compressed selector, manifest
  ordering/hash, sample order, malformed VCF/receipt, repeat/arbitrary-CWD,
  submit-CWD, module, bcftools override/PATH/version, log, stale-three-file,
  child, and stable-input states require direct final-path coverage?

## In scope

- Producer admission, CLI/help, dry-run nonmutation, selector and exact
  pileup/filter commands, lock/scratch lifecycle, execute success, child/
  publication/final-check/restoration/cleanup/signal failures, predecessor
  replacement, receipt visibility, residue, input mutation, unrelated files,
  streams, exits, and absent durable attempt identity; validator five rows,
  receipt/VCF/selector/manifest/count parsing, private report loader, dry-run/
  execute/repeat, stable-input and publication faults; scheduler submit-CWD/
  module/bcftools/log/child/stale-output/stream states; modes, hashes, artifact
  evidence, coverage rename, and commit rollback.

## Out of scope

- Adding or changing locks, staging, receipts, rollback, recovery markers,
  output hashes, provenance fields, selectors, pileup/filter/depth policy,
  calling, schemas, bcftools policy, scheduler hardening, dependency work,
  real tool/SLURM/production execution, or scientific/biological
  interpretation.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, ambiguous-recovery, selector, receipt, mutation, and
  scheduler state, with exact card corrections and dated audit findings.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and parity distinguish local fixture/fake-tool evidence from real
  bcftools, scheduler, cluster, production, scientific-review, variant/
  editing-site, or biological-readiness evidence.

## Canonical documentation updates

- This card, `MIG-03L`, roadmap/handoff only where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if a high-risk rollback/mutation state lacks a safe oracle, relocation
  changes native/report bytes beyond reviewed paths, artifact evidence needs
  schema change, or coverage/parity requires production, dependency, or
  cluster work.

## Completion record

Selected as the sole active migration review from clean, published,
local/upstream/live-remote-equal architecture-completion checkpoint
`ec7e8d911c575418ac5fc89fbfb5fef2793b6dc0`. No reliability finding is
recorded yet, usability and migration remain unselected, and no executable/
test file changed or ran.
