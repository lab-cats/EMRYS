# REVIEW-UX-03B — Review `construct_STAR_index` migration usability

## Objective

Review `MIG-03B` for scientist, operator, maintainer, automation, and recovery
continuity across the explicit public path transition.

## Why this exists

The migration intentionally changes a submitted job path, an interpreter-only
validator path, a Make test path, and implementation provenance. A correct
internal move can still leave stale commands, misleading diagnostics, broken
arbitrary-CWD behavior, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign job or validator arguments, output, messages,
  evidence state, scheduler policy, or reference handling.
- Preserve explicit repository-relative invocation without installation,
  ambient `PATH`, global `PYTHONPATH`, or a legacy forwarding path.
- Document the final path transition accurately and keep local fixture/mock
  evidence distinct from runtime or cluster proof.

## Blocked by

- [REVIEW-REL-03B](../COMPLETED/REVIEW-REL-03B-review-construct-star-index-migration.md) — Required: usability review needs the corrected architecture and reliability obligations.

## Completion unblocks

- [MIG-03B](MIG-03B-migrate-construct-star-index-owner.md) — Fully: the reviewed migration is complete.

## Prerequisites

- Inspect the committed reliability-reviewed card against public CLI,
  arbitrary-CWD, Make, runbook, artifact-provenance, documentation-link, and
  rollback journeys.

## Required context

- `MIG-03B`; Step `00a` commands in `RUNBOOK.md`; the public CLI and SLURM
  characterization; Make and literal expansions; artifact implementation
  evidence; current/future architecture routes; and the Step `00a` contract.

## Questions owned by this card

- None.

## In scope

- Submitted job and explicit-interpreter validator paths; help/malformed
  behavior; arbitrary CWD; dry-run/execute and result-artifact journeys;
  stdout/stderr and actionable load errors; Make/operator commands; artifact
  producer provenance; maintainer findability; link repair; and rollback
  instructions.

## Out of scope

- A new CLI alias, compatibility wrapper, package install, PATH discovery,
  logging redesign, reference-policy change, cluster submission, or future
  migration.

## Deliverables

- Journey-based findings with exact `MIG-03B` or documentation corrections,
  recorded with dispositions in the dated refactor log.

## Acceptance evidence

- Every supported path transition and healthy/failure journey has one final
  command, owned diagnostic, result-artifact expectation, and rollback route.
- The card makes the next safe action and local evidence ceiling discoverable
  without implying a legacy alias or cluster proof.

## Canonical documentation updates

- This card, `MIG-03B`, current handoff/priority if the next action changes,
  and the dated refactor log.

## Escalation conditions

- Stop if continuity requires retaining a public legacy path, changing a
  user-facing interface, installing software, or adding an unreviewed alias.

## Completion record

Completed as a read-only independent-in-time adversarial pass against published
reliability checkpoint `581879f` after selection checkpoint `2f39154`. One high
finding replaces the ambiguous bare job path with the explicit final `sbatch`
command and requires documentation/tests to distinguish its preserved caller-
CWD dependence from the explicit-interpreter validator's arbitrary-CWD
behavior. One medium finding requires `validation-static` and `smoke` plus their
literal Make oracle to keep syntax-checking the final job after it leaves the
flat wildcard. A second medium finding freezes the owner README journey: final
paths and invocation forms, implicit-execute/CWD warning, contract/runbook
links, provenance transition, no-wrapper/package/descriptor boundary, and
local-only evidence ceiling. All known repository commands and consumers can
move coherently, so no alias or compatibility wrapper is justified and no
escalation condition was triggered. The same campaign agent performed the pass,
so independent authorship is not claimed. No executable/test file changed and
no computational test ran.
