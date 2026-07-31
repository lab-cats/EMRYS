# AUDIT-99 — Final refactor and documentation audit

## Objective

Prove that the active local refactor program closed every in-scope finding and
decision without behavior, evidence, documentation, or usability drift.

## Why this exists

Many small packages can each pass locally while leaving cross-package gaps,
stale wrappers, contradictory docs, oversized owners, or lost contract
traceability. A final independent audit is the local program exit, not a
runtime/cluster/scientific promotion.

## Fixed decisions

- Audit only the implemented program; do not use this card to add features.
- Compare the final executable state against behavior contracts and approved
  explicit migrations, not legacy paths for their own sake.
- Preserve evidence-language boundaries and classify every original/new finding.
- Completion does not begin remote, cluster, public-data, package, analysis-
  module, or biological-policy work.

## Blocked by

- [RPT-06](../TODO/RPT-06-make-science-report-the-default.md) — Required: report target/default work must be complete.
- [LOG-05](../TODO/LOG-05-activate-concise-default-logging.md) — Required: logging rollout/default work must be complete.
- [SIZE-07A](../TODO/SIZE-07A-decompose-artifact-index-builder.md) — Required: the artifact-index mandatory size family must be closed.
- [SIZE-07B](../TODO/SIZE-07B-decompose-scientific-validation-tooling.md) — Required: the scientific-validation mandatory size family must be closed.
- [SIZE-07D](../TODO/SIZE-07D-decompose-run-summary-builder.md) — Required: the run-summary mandatory size family must be closed.
- [SIZE-07E](../TODO/SIZE-07E-resolve-step08-r-module-size.md) — Required: the Step 08 size-policy conflict must be explicitly resolved.
- [SIZE-07F](../TODO/SIZE-07F-decompose-artifact-contract-validator.md) — Required: the artifact-validator mandatory size family must be closed.
- [DOC-SKILL-10](../TODO/DOC-SKILL-10-build-documentation-health-skill.md) — Required: recurring documentation-health review must be proven.

## Completion unblocks

- [SKILL-11](../TODO/SKILL-11-evaluate-repository-skill-opportunities.md) — Fully: broader skill evaluation may occur without diverting the current program.
- [FUT-ANALYSIS-01](../TODO/FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md) — Fully: future analysis-extension design may begin separately.
- [FUT-DATA-02](../TODO/FUT-DATA-02-public-reference-and-sra-acquisition.md) — Fully: future public-data design may begin separately.
- [FUT-CLI-03](../TODO/FUT-CLI-03-installable-norad-control-plane.md) — Fully: future packaging/control-plane design may begin separately.
- [FUT-SUCCESS-04](../TODO/FUT-SUCCESS-04-optional-analysis-and-archival-semantics.md) — Fully: future optional-analysis success policy may begin separately.

## Prerequisites

- Every in-scope dynamic `MIG-03-*`, `LOG-04-*`, `CODEDOC-06-*`,
  `DOC-CONS-08-*`, correction, extraction, and additional size card created by
  `PLAN-02Z` or the reviews is complete and linked here before planning ends.
- Each dynamic-card creation commit must add that card as a direct blocker here
  and add this audit to the new card's reciprocal unblock list before this card
  may enter planning.
- The final predecessor is clean, pushed, upstream-equal, and fully docpatched.

## Required context

- Original and updated refactor audits, behavior matrix, all task completion
  records, current/future architecture, Git lineage, full local validation,
  documentation gate, and user/operator/scientist journeys.

## Questions owned by this card

- None.

## In scope

- Finding/decision/card crosswalk, final architecture/import/size analysis,
  wrapper/dead-path audit, behavior/migration parity, complete local gates,
  documentation/diagram/skill audit, and clean handoff.

## Out of scope

- New implementation, cluster execution, production scientific review, public
  data, packaging, analysis modules, or biological-readiness policy.

## Deliverables

- Final evidence-ranked audit, compatibility comparison, residual-risk ledger,
  documentation consistency result, and exact next-state handoff.

## Acceptance evidence

- Every original and newly discovered in-scope finding is resolved, retained
  intentionally, deferred with owner/trigger, or explicitly accepted.
- Applicable preserved contracts and approved migrations pass; current topology,
  docs, diagrams, task status, and local context agree with implementation.
- Worktree/history/upstream gates are clean. No remote/cluster/scientific claim
  is inferred.

## Canonical documentation updates

- `REFACTOR_AUDIT.md`, `TEST_BASELINE.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`,
  `TODO.md`, current/future architecture, `DECISIONS.md`, `QUESTIONS.md`, task
  registry, and all affected current operator/user owners.

## Escalation conditions

- Stop for any unresolved high-risk contract, missing dynamic card, evidence
  mismatch, stale compatibility layer, or request to treat local audit as
  cluster/scientific proof.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
