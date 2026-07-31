# REVIEW-UX-03 — Review usability plan

## Objective

Independently review the plan from scientist, operator, maintainer, and
automation perspectives before executable architecture work begins.

## Why this exists

A technically sound architecture can still expose opaque names, excessive
output, overwhelming reports, unclear intake states, hard-to-find recovery
instructions, or local context that omits critical caveats.

## Fixed decisions

- Review only; do not implement changes in this card.
- The science report, concise logging, semantic stage map, YAML+TSV intake,
  glossary, directory READMEs, and local context are target constraints.
- Accessibility and inspectability apply to failure states, not just happy paths.

## Blocked by

- [REVIEW-REL-02](../TODO/REVIEW-REL-02-review-reliability-plan.md) — Required: usability review needs architecture and reliability corrections incorporated.
- [DOC-REF-02](../TODO/DOC-REF-02-create-glossary.md) — Required: terminology support must exist for meaningful onboarding review.

## Completion unblocks

- [RPT-03](../TODO/RPT-03-build-format-neutral-report-projection.md) — Partially: the science report contract is also required.
- [LOG-03](../TODO/LOG-03-build-two-sink-logging-foundation.md) — Partially: the logging contract is also required.
- [SIZE-07A](../TODO/SIZE-07A-decompose-artifact-index-builder.md) — Partially: the refreshed size inventory is also required.
- [SIZE-07B](../TODO/SIZE-07B-decompose-scientific-validation-tooling.md) — Partially: the refreshed size inventory is also required.
- [SIZE-07D](../TODO/SIZE-07D-decompose-run-summary-builder.md) — Partially: the refreshed size inventory is also required.
- [SIZE-07E](../TODO/SIZE-07E-resolve-step08-r-module-size.md) — Partially: the refreshed size inventory is also required.
- [SIZE-07F](../TODO/SIZE-07F-decompose-artifact-contract-validator.md) — Partially: the refreshed size inventory is also required.
- [DOC-SKILL-10](../TODO/DOC-SKILL-10-build-documentation-health-skill.md) — Partially: proven documentation rollout/consolidation inputs are also required.

## Prerequisites

- Use representative scientist, operator, maintainer, and machine journeys,
  including malformed input, failed run, resume, and incomplete evidence.

## Required context

- Corrected integrated plan, glossary, conceptual pipeline, intake/report/log
  contracts, directory/local-context standards, CLI/SLURM characterization,
  and current troubleshooting paths.

## Questions owned by this card

- None.

## In scope

- Findability, terminology, cognitive load, accessibility, responsive/print
  behavior, console signal, report hierarchy, intake status, error recovery,
  local context, and automation clarity.

## Out of scope

- Implementation, aesthetic redesign without user value, unsupported biology,
  or deleting comprehensive diagnostics.

## Deliverables

- Journey-based findings, severity/rationale, and exact plan/card revisions.

## Acceptance evidence

- Each critical journey has clear inputs, state, next action, outputs, and
  limitations without requiring repository-wide source reading.
- Findings are resolved, accepted explicitly, or assigned to bounded cards.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, task registry, `QUESTIONS.md`, `DECISIONS.md` only for
  approved durable changes, and this card.

## Escalation conditions

- Stop if usability requires changing scientific meaning, evidence promotion,
  or a public interface beyond the approved target direction.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
