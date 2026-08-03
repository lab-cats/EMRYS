# REVIEW-UX-03E — Review `construct_FASTA_sidecars` migration usability

## Objective

Review `MIG-03E` for scientist, operator, maintainer, automation, and recovery
continuity across every explicit Step `00c` path transition.

## Why this exists

The migration changes a directly executable shell path, an interpreter-only
validator path, an executable submitted-job path and its delegated command,
Make/coverage paths, test paths, and implementation provenance. Correct code
can still leave stale commands, hidden site defaults, misleading dry-run or
recovery guidance, or an undiscoverable owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler policy,
  reference semantics, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient PATH/PYTHONPATH discovery, global `sys.path`, or a legacy alias.
- Keep fixture/mock migration evidence distinct from real samtools/GATK/Java
  runtime, scheduler, cluster, production, scientific-review, or biological
  proof.

## Blocked by

- [REVIEW-REL-03E](../COMPLETED/REVIEW-REL-03E-review-construct-fasta-sidecars-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03E](../TODO/MIG-03E-migrate-construct-fasta-sidecars-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed card against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, tool override,
  Make, runbook/troubleshooting, artifact, documentation, and rollback journeys.

## Required context

- `MIG-03E`; Step `00c` runbook/troubleshooting commands; public CLI and SLURM
  characterization; Make/literal expansions; coverage path; artifact
  implementation evidence; owner contract; reference-provenance diagnostic
  boundary; and current/future topology.

## Questions owned by this card

- None.

## In scope

- Direct and explicit-`bash` producer paths; help/malformed and arbitrary-CWD
  journeys; dry-run guarantees; tool resolution/version diagnostics; sidecar
  reuse/publication/partial-state recovery; interpreter-only validator and
  exact-loader diagnostics; scheduler submission/CWD/default/override/Bash
  `3.2` guidance; streams and logs; Make/test commands; provenance transition;
  owner findability; links; rollback; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH discovery, reference-
  provenance relocation, logging redesign, data/reference policy changes,
  scheduler hardening, cluster submission, dependency actions, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported transition and healthy/failure journey has one final command,
  owned diagnostic, artifact expectation, preservation/rollback route, and
  evidence ceiling.
- The owner README and runbook make direct/`bash`, validator, scheduler, tool,
  dry-run, reuse, partial publication, recovery, and evidence boundaries
  discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03E`, current roadmap/handoff when status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, moved reference provenance, or an unreviewed alias/
  package contract.

## Completion record

Not started. This will be an independent-in-time adversarial pass by the same
campaign agent; independent authorship will not be claimed.
