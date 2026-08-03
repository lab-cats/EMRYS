# REVIEW-REL-03E — Review `construct_FASTA_sidecars` migration reliability

## Objective

Challenge `MIG-03E` against producer, validator, reference-loader, scheduler,
artifact-evidence, coverage, fault, residue, and rollback behavior before
source movement.

## Why this exists

The producer conditionally reuses or publishes two sidecars but can leave only
the FAI after a second publication failure. The scheduler has a Bash `3.2`
default-dry-run defect and site-bound tool setup. The validator publishes
structural evidence while depending on two separate implementation owners.
Relocation must preserve and characterize every state without approving it.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact producer commands/state machine, scheduler directives/modes/
  failures, validator publication, reference-parser behavior, artifact
  identity, and coverage.
- Treat old/final identical-input parity, exact-loader faults, and isolated
  partial-publication residue as named obligations; a broad passing suite is
  not a substitute.

## Blocked by

- [REVIEW-ARCH-03E](REVIEW-ARCH-03E-review-construct-fasta-sidecars-migration.md) — Required: reliability review needs the architecture-corrected owner, import, and caller boundary.

## Completion unblocks

- [REVIEW-UX-03E](REVIEW-UX-03E-review-construct-fasta-sidecars-migration.md) — Fully: public and maintainer continuity follows fixed fault and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed card and map each current
  producer, validator, import, job, artifact, and coverage state to one final-
  path regression owner without modifying or running executable files.

## Required context

- `MIG-03E`; producer/validator/job; direct owner tests; Step `00c` mocked-job
  behavior; validation-report fault matrix; reference-provenance implementation
  and fault suite; exact roster suites; artifact evidence; coverage
  config/tool/baseline; and applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- None.

## In scope

- Producer argument/tool/dry-run/execute/reuse/generation/validation/lock/temp/
  cleanup/failure states and partial final residue; validator parser, dry-run/
  execute/repeat, stable-input, lock, rollback, cleanup, report-loader, and
  reference-loader states; scheduler preflight, fallback submit CWD, site
  defaults, tolerated modules, Java version, Bash `3.2`, child/output failure,
  streams, and residue; modes/hashes; artifact evidence; coverage rename; and
  commit rollback.

## Out of scope

- Correcting publication atomicity, adding receipts/recovery markers, changing
  sidecar/parser contracts, moving reference provenance, changing scheduler
  policy, dependency work, cluster execution, scientific policy, or another
  owner.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and rollback state, with exact card corrections in the dated
  refactor log.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/final-path regression owner.
- Coverage and loader proof distinguish local fixture/mock evidence from real
  tool runtime, scheduler, production, scientific-review, and biological
  evidence.

## Canonical documentation updates

- This card, `MIG-03E`, roadmap/handoff only if status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks an oracle, relocation changes command/job/
  report/parser behavior, artifact evidence needs schema change, or coverage
  and exact-loader parity cannot be measured.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
