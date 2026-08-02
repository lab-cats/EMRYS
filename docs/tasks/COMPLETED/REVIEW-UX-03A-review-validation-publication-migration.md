# REVIEW-UX-03A — Review validation-publication migration usability

## Objective

Review `MIG-03A` for scientist, operator, maintainer, and automation continuity
at the public validator boundary before executable work begins.

## Why this exists

An internally correct extraction can still break direct invocation, arbitrary
working-directory use, diagnostics, output routing, or the discoverability of
the shared owner and its known limitations.

## Fixed decisions

- Review only; do not rename public validator scripts, flags, report fields,
  check IDs, messages, or evidence states.
- Preserve explicit local execution without installing NORAD, setting a global
  `PYTHONPATH`, or discovering scripts through `PATH`.
- Keep stage-specific validation meaning with each functional owner.

## Blocked by

- [REVIEW-REL-03A](../COMPLETED/REVIEW-REL-03A-review-validation-publication-migration.md) — Required: usability review needs the corrected architecture and reliability boundary.

## Completion unblocks

- [MIG-03A](../TODO/MIG-03A-extract-validation-report-library.md) — Fully: the first executable migration may enter task-start planning after all tranche-specific reviews close.

## Prerequisites

- Inspect the committed reliability-reviewed card against current public CLI,
  arbitrary-CWD, Make, runbook, and failure-diagnostic evidence.

## Required context

- `MIG-03A`, the public CLI matrix and tests, all thirteen validator entry
  points, affected runbook links, current/future architecture routes, and the
  evidence-language boundary in `TEST_BASELINE.md`.

## Questions owned by this card

- None.

## In scope

- Direct interpreter behavior, arbitrary working directory, help/malformed
  invocation, stdout/stderr, exit status, dry-run/execute effects, import
  failure visibility, maintainer findability, and accurate documentation of
  local-only evidence.

## Out of scope

- New CLI surfaces, package installation, logging adoption, report redesign,
  glossary/onboarding work, scientific wording changes, or stage migration.

## Deliverables

- Journey-based findings and exact `MIG-03A` or documentation corrections,
  recorded with dispositions in the dated refactor log.

## Acceptance evidence

- Current validator commands and machine report files remain discoverable and
  behaviorally unchanged in the plan, including malformed and failure paths.
- The card states the next safe action, local evidence ceiling, and excluded
  operator/runtime/cluster work without requiring broad repository context.

## Canonical documentation updates

- This card, `MIG-03A`, current priority and handoff if the next action changes,
  and the dated pre-migration refactor log.

## Escalation conditions

- Stop if import continuity requires a public command change, environment
  bootstrap, dependency installation, or a new user-facing policy.

## Completion record

Completed as a read-only public-boundary review against reliability checkpoint
`102510b` after selection checkpoint `22f7a5b`. The current matrix proves all
thirteen validators are mode-`0644` interpreter-only entry points whose
healthy-repository help and malformed-argument journeys are arbitrary-CWD and
result-artifact free. A high finding added a stable stderr-only, nonzero,
artifact-free diagnostic for missing, wrong-cache, or ordinarily failing shared
owner loads while preserving control-flow exceptions. A medium finding added a
maintainer README, module docstring, and caller-local owner comments without
creating a package/import identity. The card now separates those new corrupted-
owner tests from the unchanged healthy CLI contract and names the exact stop
before source mutation. The same-author review limitation remains disclosed.
No executable file changed or computational test ran.
