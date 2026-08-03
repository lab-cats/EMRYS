# REVIEW-UX-03L — Review partitioned cohort mpileup migration usability

## Objective

Review `MIG-03L` for operator, maintainer, automation, recovery, scientific-
language, and evidence continuity across every explicit Step `07` path change.

## Why this exists

The migration changes a directly executable Bash producer path, explicit-
interpreter validator path, submitted-job path and delegated command, Make/
coverage/test/helper paths, and implementation provenance. Correct relocation
can still leave stale commands, hidden selector/depth/filter/tool/output/lock
selection, calling or biological overclaim, incorrect dry-run claims, unsafe
retry guidance, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler or tool
  policy, mechanical labels, selectors, pileup/filter behavior, transaction,
  or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/fake-tool migration evidence distinct from real bcftools,
  scheduler, cluster, production, scientific-review, variant/editing-site,
  or biological-readiness proof.

## Blocked by

- [REVIEW-REL-03L](REVIEW-REL-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03L](MIG-03L-migrate-generate-partitioned-cohort-mpileup-vcfs-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03L`; Step `07` runbook/troubleshooting commands; producer and
  validator help; public CLI and scheduler characterization; Make/literal
  expansions; coverage/artifact/helper paths; owner contract; current/future
  topology; partition manifests; selector/depth/filter/bcftools/output/lock/
  receipt diagnostics; mechanical-orientation and non-calling language; and
  the three-file transaction evidence boundary.

## Questions owned by this card

- None.

## In scope

- Direct producer and explicit-interpreter validator root/arbitrary-CWD dry-
  run/execute/repeat journeys; exact mechanical and non-calling wording;
  partition/selector/FAI/regions-file, depth, filter, bcftools, input, output,
  scratch, lock, and receipt selection; staged publication, rollback failure,
  mutation, relative-path disagreement, residue, and safe preservation;
  scheduler submit CWD, modules, overrides, version, logs, delegation, and
  stale outputs; Make/test commands; implementation/evidence provenance;
  owner findability; links; rollback; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/`PYTHONPATH` redesign,
  transaction repair, receipt/provenance/recovery redesign, selector or
  pileup/filter/depth policy, calling, scheduler hardening, cluster
  submission, dependency action, scientific/biological interpretation, or
  future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, mechanical/non-calling meaning, selector/depth/filter/tool/output/
  lock/receipt selection, rollback residue, focused tests, evidence status,
  provenance, and rollback discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03L`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, calling/scientific/
  biological claim, or an unreviewed alias/package contract.

## Completion record

Not selected. Blocked on unselected `REVIEW-REL-03L`; no executable/test file
changed or ran.
