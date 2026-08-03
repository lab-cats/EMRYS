# REVIEW-UX-03D — Review `align_RNA_reads_with_STAR` migration usability

## Objective

Review `MIG-03D` for scientist, operator, maintainer, automation, and recovery
continuity across all explicit public path transitions.

## Why this exists

The migration changes a directly executable shell path, an interpreter-only
validator path, a submitted-job path and its delegated command, Make/coverage
paths, focused test paths, and implementation provenance. Correct internals can
still leave stale commands, misleading CWD guidance, hidden dry-run mutation,
or an undiscoverable owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler policy,
  evidence state, or alignment meaning.
- Preserve explicit repository-relative invocation without installation,
  ambient PATH/PYTHONPATH discovery, global `sys.path`, or a legacy alias.
- Keep local fixture/mock evidence distinct from real STAR runtime, scheduler,
  cluster, production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03D](REVIEW-REL-03D-review-align-rna-reads-with-star-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03D](MIG-03D-migrate-align-rna-reads-with-star-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed card against public CLI,
  arbitrary-CWD, direct/explicit-interpreter, scheduler submission, Make,
  runbook/troubleshooting, artifact, documentation, and rollback journeys.

## Required context

- `MIG-03D`; Step `01` runbook/troubleshooting commands; public CLI and SLURM
  characterization; Make/literal expansions; coverage path; artifact
  implementation evidence; owner contract; and current/future topology.

## Questions owned by this card

- None.

## In scope

- Direct and explicit-interpreter producer paths; help/malformed and arbitrary-
  CWD journeys; dry-run directory mutation and final artifacts; interpreter-
  only validator; scheduler submission/CWD/default/override guidance; streams
  and diagnostics; Make/operator/test commands; provenance transition; owner
  findability; links; rollback; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH discovery, logging redesign,
  data or alignment policy changes, scheduler hardening, cluster submission,
  dependency actions, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported transition and healthy/failure journey has one final command,
  owned diagnostic, artifact expectation, and rollback route.
- The owner README and runbook make direct/explicit-interpreter, scheduler CWD,
  dry-run mutation, final-path publication, recovery, and evidence ceilings
  discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03D`, current roadmap/handoff when status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, or an unreviewed alias/package contract.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
