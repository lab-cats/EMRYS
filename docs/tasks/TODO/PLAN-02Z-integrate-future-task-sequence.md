# PLAN-02Z — Integrate future task sequence

## Objective

Turn the approved target decisions and completed design inventories into a
small, dependency-correct sequence of separately planned future tasks.

## Why this exists

The active repository-spanning refactor needs to absorb the new architecture
direction without becoming one massive implementation plan. Exact migration
packages cannot be named safely until stage, topology, intake, report, logging,
documentation, size, and local-context designs are inspected together.

## Fixed decisions

- This card plans and creates bounded task cards; it does not execute the
  refactor.
- Each generated card requires its own live inspection, plan, and approval.
- Prefer one architectural concern and locally relevant context per card;
  correctness and contract parity outrank smallness.
- Preserve the linear descendant gate for executable packages while using the
  DAG to express task prerequisites.

## Blocked by

- [ARCH-02D](../TODO/ARCH-02D-define-direct-migration-mechanics.md) — Required: migration mechanics must be settled.
- [INTAKE-02E](../TODO/INTAKE-02E-define-yaml-tsv-run-lifecycle.md) — Required: intake boundaries must be designed.
- [LIB-02F](../TODO/LIB-02F-define-shared-library-ownership.md) — Required: extraction/retention rules must be applied to candidates.
- [RPT-02](../TODO/RPT-02-define-science-report-contract.md) — Required: report design packages must be scoped.
- [LOG-02](../COMPLETED/LOG-02-define-logging-contract.md) — Required: logging foundation and rollout boundaries must be scoped.
- [DOC-IA-01](../TODO/DOC-IA-01-define-documentation-ownership-and-navigation.md) — Required: documentation sequencing and consolidation ownership must be known.
- [DOC-PIPE-04](../TODO/DOC-PIPE-04-create-user-pipeline-overview.md) — Required: the human conceptual flow must agree with the stage map.
- [CODEDOC-05](../TODO/CODEDOC-05-inventory-code-documentation.md) — Required: local code-documentation cards must be known.
- [SIZE-07](../TODO/SIZE-07-refresh-large-file-inventory.md) — Required: mandatory decomposition/exception work must be known.
- [CONTEXT-09](../TODO/CONTEXT-09-define-local-maintainer-context.md) — Required: each generated task needs a bounded context set.

## Completion unblocks

- [REVIEW-ARCH-01](../TODO/REVIEW-ARCH-01-review-architecture-plan.md) — Fully: an independent architecture review can inspect the integrated sequence.

## Prerequisites

- Refresh the live Git lineage and ensure no intervening package invalidated an
  input design or behavior contract.

## Required context

- Every blocking card and its canonical outputs, `REFACTOR_AUDIT.md`,
  `TEST_BASELINE.md`, current/future architecture, and active task registry.

## Questions owned by this card

- None.

## In scope

- Dependency DAG, migration groups, card generation for `MIG-03-*`,
  `LOG-04-*`, `CODEDOC-06-*`, `DOC-CONS-08-*`, and justified narrow
  corrections/extractions; acceptance and rollback boundaries for each.

## Out of scope

- Implementing any generated card, preauthorizing production mutation,
  collapsing all work into one branch, or adding future-only analysis/public
  data/package capabilities.

## Deliverables

- An integrated card DAG, updated roadmap, explicit dynamic card set, and
  review packet with traceability from findings/decisions to tasks.
- In the same commit that creates each dynamic card, explicit direct blockers
  replace family prerequisites in `LOG-05`, `DOC-SKILL-10`, `AUDIT-99`, and any
  other affected card, with reciprocal unblock links.

## Acceptance evidence

- Every in-scope finding and approved current-program decision has exactly one
  disposition; dependencies are acyclic and reciprocal.
- No known concrete dependency remains only as a wildcard/family prerequisite.
- Each executable card is independently understandable, testable, reversible,
  and small enough for local context unless correctness requires otherwise.

## Canonical documentation updates

- `PIPELINE_PLAN.md`, task registry, `TODO.md`, `QUESTIONS.md`, and this card;
  update durable owners only when a design decision changes.

## Escalation conditions

- Stop for unresolved behavior contracts, cross-card circularity, an oversized
  migration that cannot be decomposed safely, or a new architectural choice not
  already approved.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
