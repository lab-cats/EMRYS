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

- [REVIEW-ARCH-03E](../COMPLETED/REVIEW-ARCH-03E-review-construct-fasta-sidecars-migration.md) — Required: reliability review needs the architecture-corrected owner, import, and caller boundary.

## Completion unblocks

- [REVIEW-UX-03E](../IN_PROGRESS/REVIEW-UX-03E-review-construct-fasta-sidecars-migration.md) — Fully: public and maintainer continuity follows fixed fault and parity obligations.

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

Completed as a read-only independent-in-time adversarial pass against published
selection checkpoint `e39f4b2` and architecture-corrected checkpoint `494889f`.

One high finding assigns an exact oracle to the characterized two-output
publication defect. A fake `mv` fails only the final DICT move after the final
FAI move. Old and final paths must both return nonzero, retain a nonempty final
FAI, leave the final DICT absent, remove the owned lock, and leave no run-token
temporary files. The retained FAI is preserved evidence of an incomplete
attempt, not a successful transaction or authority for cleanup.

A second high finding makes the new private-loader fault matrix independent of
the public reference-provenance tests. The moved validator suite exact-loads
the validator in process and proves healthy reuse, missing owner, foreign wrong-
path cache, correct-path incomplete API, and injected loader-owned execution
failure. `ProvenanceError` must be an exception type and every parser callable;
preexisting cache objects survive, only the loader-created partial is removed,
`sys.path` is unchanged, and no report or invocation-CWD residue appears.

One medium finding requires a single non-repository-CWD validator dry-run,
execute, and repeat parity journey with exact five-row deterministic bytes,
stable replacement, and unchanged inputs. Another retains the existing central
scheduler matrix as sufficient for directives, executable mode, fallback submit
CWD, tolerated modules, site defaults, Java selection/version, explicit mode,
Bash `3.2`, child exit, output checks, and streams; duplicating that harness is
not justified.

Coverage moves only after final measurement. The old row supplies minimum
covered counts `90/96` lines and `23/26` branches, not permission to hide new
loader branches; the global `9343/11506` and `3281/4698` floor remains binding.
Artifact IDs, schemas, reconciliation, public reference-provenance behavior,
and Step `05` stay unchanged. The same campaign agent performed this separate
committed-time pass, so independent authorship is not claimed. No executable,
test, dependency, runtime, scheduler, production, scientific-review, or
biological evidence changed or ran.
