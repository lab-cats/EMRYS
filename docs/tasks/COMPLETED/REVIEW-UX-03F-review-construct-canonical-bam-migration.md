# REVIEW-UX-03F — Review `construct_canonical_BAM` migration usability

## Objective

Review `MIG-03F` for scientist, operator, maintainer, automation, and recovery
continuity across the neutral-helper transition and every explicit Step `02`
path change.

## Why this exists

The migration changes a directly executable producer path, an interpreter-only
validator path, a submitted-job path and its delegated command, Make/coverage/
test paths, helper provenance, and recovery navigation. Correct code can still
leave incomplete commands, misleading dry-run or rollback claims, hidden
caller-CWD/module behavior, or an undiscoverable owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler policy,
  BAM/read-group semantics, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import/PYTHONPATH discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real samtools, scheduler,
  cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03F](../COMPLETED/REVIEW-REL-03F-review-construct-canonical-bam-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03F](../IN_PROGRESS/MIG-03F-migrate-construct-canonical-bam-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper-diagnostic, and rollback journeys.

## Required context

- `MIG-03F`; Step `02` runbook/troubleshooting commands; producer and validator
  help; public CLI and SLURM characterization; Make/literal expansions;
  coverage and artifact paths; owner contract; neutral-helper diagnostic
  boundary; and current/future topology.

## Questions owned by this card

- None.

## In scope

- Direct and explicit-`bash` producer commands; help/malformed/arbitrary-CWD
  journeys; dry-run no-write guarantee; samtools resolution; execute,
  replacement, partial/ambiguous rollback preservation; interpreter-only
  validator and exact-loader diagnostics; scheduler submit/CWD/default/override/
  module/Bash `3.2` guidance; streams/logs; Make/test commands; helper and
  implementation provenance transitions; owner findability; links; rollback;
  and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/PYTHONPATH redesign,
  rollback repair, receipts/markers, BAM/read-group policy, scheduler hardening,
  cluster submission, dependency actions, downstream-owner commands beyond
  loader diagnostics, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported transition and healthy/failure journey has one final command,
  owned diagnostic, artifact expectation, preservation/rollback route, and
  evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run,
  replacement, ambiguous rollback, helper-integrity, focused-test, and rollback
  boundaries discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03F`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public helper import, or an unreviewed alias/package
  contract.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
selection checkpoint `308f02e33fd573f9f45df95d043f7120bb454132` and the
reliability-corrected migration card.

One high finding requires replacement of the stale, incomplete Step `02`
runbook journey at documentation close. Final instructions must use the final
producer, validator, and job paths; include repository-root direct and
explicit-`bash` producer dry-run/execute forms plus arbitrary-CWD absolute
paths; explain that producer samtools resolution is PATH-only; and retain the
mode-`0644` validator as an explicit-interpreter dry-run/execute/repeat journey
with an explicit samtools path. Producer dry-run checks inputs and PATH but
invokes no samtools command and creates no output directory, lock, scratch,
backup, BAM, or BAI.

A second high finding requires operator-safe scheduler and recovery routes.
Submission must `cd` to the checkout, create `logs/`, use the exact final job,
and expose `SAMPLE_ID`, `INPUT_ALIGNMENT`, `OUTPUT_DIR`, `THREADS`, and
`EXECUTE`; the wrapper ignores `SLURM_SUBMIT_DIR`, forces `TMPDIR=/tmp`, creates
logs/output directories in dry-run, strictly loads samtools `1.19.2`, tolerates
only module-list diagnostics, and retains the Bash `3.2` empty-array defect.
Runbook prose must stop promising complete rollback: a failed restore can
leave only the prior BAI with no BAM, backups, lock, receipt, or marker.
Troubleshooting must preserve the pair directory, producer/scheduler streams,
run-token paths, and exact final/backup state; it must authorize neither
cleanup nor retry without ownership and provenance inspection.

Medium findings require the adjacent owner README to explain the private
neutral helper and exact-loader diagnostic as checkout-integrity boundaries,
not a `PYTHONPATH`, package, or public-CLI workaround. It must route the moved
owner suites, neutral helper suite, unchanged Step `04`/`05` direct regressions,
and central scheduler suite; record the producer implementation path/hash-only
artifact transition; and state documentation-first reverse rollback and the
local fixture/mock evidence ceiling. Every known journey has a final path, so
no compatibility alias is justified.

The same campaign agent performed this separate committed-time pass, so
independent authorship is not claimed. No executable, test, dependency,
runtime-tool, scheduler, production, scientific-review, or biological evidence
changed or ran.
