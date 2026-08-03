# REVIEW-REL-03C — Review `convert_GTF_to_BED12` migration reliability

## Objective

Challenge `MIG-03C` against producer, validator, scheduler, publication,
artifact-evidence, coverage, and rollback behavior before source movement.

## Why this exists

The producer immediately and silently replaces its output, the validator
reuses producer logic for its strongest check, and the job publishes an
intermediate plus redirect-truncated final without a transaction. Relocation
must preserve rather than normalize every success, failure, and residue state.

## Fixed decisions

- Review only; do not fix or bless characterized defects.
- Preserve exact converter normalization, scheduler directives/commands/
  failures, validator publication behavior, artifact identity, and coverage.
- Treat old/new identical-input parity and failure residue as named obligations;
  a passing broad suite is not a substitute.

## Blocked by

- [REVIEW-ARCH-03C](../COMPLETED/REVIEW-ARCH-03C-review-convert-gtf-to-bed12-migration.md) — Required: reliability review needs the architecture-corrected owner and caller boundary.

## Completion unblocks

- [REVIEW-UX-03C](REVIEW-UX-03C-review-convert-gtf-to-bed12-migration.md) — Fully: public and maintainer continuity follows fixed fault and parity obligations.

## Prerequisites

- Start from the committed architecture-reviewed card and map each current
  producer, validator, job, artifact, and coverage state to one final-path
  regression owner without modifying or running executable files.

## Required context

- `MIG-03C`; producer/validator/job; direct owner tests; Step `00b` mocked job
  case; validation-report fault matrix; exact roster suites; artifact evidence;
  coverage config/tool/baseline; and applicable `TEST_BASELINE.md` risk rows.

## Questions owned by this card

- None.

## In scope

- Converter parse/warning/failure/replace states; deterministic BED bytes;
  validator producer coupling, dry-run/execute/repeat, report faults, stable
  inputs, locks, rollback, cleanup, and residue; scheduler preflight, directory
  timing, module/child/sort/awk failures, intermediate/final truncation and
  residue; modes/hashes; artifact evidence; coverage rename; commit rollback.

## Out of scope

- Correcting transactions, adding dry-run/no-clobber, independent scientific
  normalization, changing GTF/BED contracts, dependency work, cluster execution,
  scientific policy, or another owner.

## Deliverables

- A risk-to-test disposition for every applicable success, failure, side-
  effect, residue, and rollback state, with exact card corrections in the dated
  refactor log.

## Acceptance evidence

- Every high-risk current state has a preserved or characterized-defect
  disposition and a named old/new regression owner.
- Coverage rename proof distinguishes local fixture/mock evidence from runtime,
  scheduler, production, scientific-review, and biological evidence.

## Canonical documentation updates

- This card, `MIG-03C`, roadmap/handoff only if status changes, and the dated
  refactor log.

## Escalation conditions

- Stop if a high-risk state lacks an oracle, relocation changes BED/job/report
  behavior, artifact evidence needs schema change, or coverage parity cannot be
  measured.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
reliability-selection checkpoint `60698cc` after architecture checkpoint
`aed342d`. One high finding replaces the monolithic reused-state mocked-job case
with fresh isolated old/new scenarios: preflight failures, module failure,
converter failure, bedtools failure, malformed sorted output, and success each
must prove exact directory timing, calls, bytes/absence, streams, exit, and
residue. In particular, bedtools redirection can create or truncate the final
before child success, and awk prints its current success text from `END` even
after a bad-field error; both remain defects. A second high finding adds the
missing full validator dry-run/execute/repeat journey from a non-repository CWD
with exact streams, report bytes, and residue parity. Artifact evidence must
assert the final producer path and unchanged producer hash; coverage must move
both frozen rows plus the required-subprocess identity only after inspected
measurement. The existing producer tests, public-CLI matrix, exact rosters, and
neutral publisher fault suite otherwise cover applicable conversion,
publication, rollback, interruption, collision, and cleanup states. No
escalation condition was triggered. The same campaign agent performed the pass;
independent authorship is not claimed. No executable/test file changed and no
computational test ran.
