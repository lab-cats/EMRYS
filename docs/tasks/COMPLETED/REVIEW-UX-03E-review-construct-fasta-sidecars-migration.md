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

Completed as a read-only independent-in-time adversarial pass against published
selection checkpoint `4750161` and the reliability-corrected migration card.

One high finding requires replacement of the stale and incomplete Step `00c`
runbook journey at the migration documentation close. Final instructions must
use the final producer, validator, and job paths; include direct and explicit-
`bash` producer forms plus explicit samtools, GATK, and Java paths; create
`logs/` before submission; expose every portable scheduler override; and remove
the stale ad hoc/BAM evidence text. Dry-run documentation must state that tool
paths are resolved but no version or generation command runs and no directory,
lock, temporary path, FAI, or DICT is created. The mode-`0644` validator remains
an explicit-interpreter journey.

A second high finding assigns an operator-safe route to the characterized
FAI-only partial-publication state without fixing or blessing it. Both Step
`00c` troubleshooting entries and the owner README must distinguish malformed
or mismatched sidecars from an incomplete attempt that retained a nonempty FAI
but no DICT. Preserve producer context, scheduler stdout/stderr, lock and run-
token temporary state, and both final paths before deciding on cleanup. A
separately authorized rerun may generate a missing DICT only after provenance
and ownership inspection; the migration does not authorize deletion or call
the retained FAI successful transaction output.

Medium findings require the adjacent owner README to route root and arbitrary-
CWD producer forms, validator dry-run/execute/repeat, scheduler defaults and
overrides, focused owner tests plus the independent central scheduler suite,
rollback in documentation-then-executable order, and the local-only evidence
ceiling. It must explain that failure to exact-load the still-flat public
`reference_provenance.py` owner is a checkout-integrity diagnostic, not a
`PYTHONPATH` workaround or approval to move that owner.

The same campaign agent performed this separate committed-time pass, so
independent authorship is not claimed. No executable, test, dependency,
runtime-tool, scheduler, production, scientific-review, or biological evidence
changed or ran.
