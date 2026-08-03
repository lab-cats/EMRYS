# REVIEW-UX-03C — Review `convert_GTF_to_BED12` migration usability

## Objective

Review `MIG-03C` for scientist, operator, maintainer, automation, and recovery
continuity across all explicit public path transitions.

## Why this exists

The migration changes an executable Python path, a submitted-job path and its
delegated command, an interpreter-only validator path, Make/coverage paths,
focused test paths, and implementation provenance. A correct internal move can
still leave stale commands, misleading CWD guidance, broken direct execution,
or an undiscoverable owner.

## Fixed decisions

- Review only; do not redesign arguments, warnings, outputs, messages,
  scheduler policy, evidence state, or GTF/BED meaning.
- Preserve explicit repository-relative invocation without installation,
  ambient PATH/PYTHONPATH discovery, global `sys.path`, or a legacy alias.
- Keep local fixture/mock evidence distinct from guarded runtime, cluster,
  production, scientific-review, or biological proof.

## Blocked by

- [REVIEW-REL-03C](../COMPLETED/REVIEW-REL-03C-review-convert-gtf-to-bed12-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03C](../TODO/MIG-03C-migrate-convert-gtf-to-bed12-owner.md) — Fully: migration selection may begin after all three reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed card against public CLI,
  arbitrary-CWD, direct/exact-interpreter, scheduler submission, Make,
  runbook/troubleshooting, artifact, documentation, and rollback journeys.

## Required context

- `MIG-03C`; Step `00b` runbook/troubleshooting commands; public CLI and SLURM
  characterization; Make/literal expansions; coverage required-subprocess path;
  artifact implementation evidence; owner contract; current/future topology.

## Questions owned by this card

- None.

## In scope

- Executable producer and explicit-interpreter validator paths; help/malformed
  and arbitrary-CWD journeys; output replacement and validation artifacts;
  submitted job, submit-directory and override guidance; streams/diagnostics;
  Make/operator/test commands; provenance transition; owner findability; links;
  rollback and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package install, PATH discovery, logging redesign,
  data-policy changes, cluster submission, dependency actions, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported transition and healthy/failure journey has one final command,
  owned diagnostic, artifact expectation, and rollback route.
- The owner README and runbook make direct/exact-interpreter, scheduler CWD,
  replacement, evidence ceiling, and next safe action discoverable without an
  alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03C`, current roadmap/handoff when status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, or an unreviewed alias/package contract.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
usability-selection checkpoint `b01b6f1` after reliability checkpoint
`f12bc8b`. One high finding replaces bare producer and job path listings with
complete final-path commands and distinguishes repository-root direct and
explicit-interpreter producer use, arbitrary-CWD absolute-path use, the
interpreter-only validator, and `cd <checkout>` before the exact `sbatch`
command. The job remains implicit execution with no dry-run and preserves its
required submit-directory and override behavior. One medium finding requires
`validation-static` and `smoke`, plus their literal Make oracle, to name the
final job after it leaves `jobs/*.slurm`; existing `compileall` coverage of
`src/norad` remains sufficient. A second medium finding requires the focused
command to include producer, validator, and owner-local mocked-job suites and
requires an owner README covering final commands, replacement/nontransactional
warnings, artifact-path provenance, diagnostics, recovery, evidence ceiling,
and the no-wrapper/package/descriptor boundary. Troubleshooting must name the
exact final producer path. All repository consumers can cut over coherently, so
no compatibility alias is justified and no escalation condition was triggered.
The same campaign agent performed the pass, so independent authorship is not
claimed. No executable/test file changed and no computational test ran.
