# PLAN-03A — Inventory and sequence residual source-topology convergence

## Objective

Assign every bounded residual flat source, native asset, configuration,
test, and fixture one explicit final disposition and record the dependency-
correct just-in-time order for moving the implemented owners that remain.

## Why this exists

The completed `MIG-03A` through `MIG-03O` campaign moved the fourteen frozen
pipeline owners, but the current functional-owner inventory still identifies
implemented cross-cutting application concerns under root `scripts/`,
`schemas/`, and `reports/`. Treating that narrower campaign close as complete
repository convergence would leave accidental paths, ambiguous test homes,
and prohibited reverse dependencies unresolved.

## Fixed decisions

- Give every tracked path in the bounded residual roots exactly one disposition:
  move to an exact final owner, retain intentionally at repository level,
  retire through separately approved cleanup, or defer to a named unimplemented
  domain.
- Defer scheduler, ingestion, and scientific-workflow orchestration/profile
  implementation. Repository Git orchestration is developer tooling, not that
  runtime domain.
- Retain public operator examples and reference surfaces under root `configs/`
  when they are inputs rather than owner-native implementation assets.
- Create and select executable migration cards one owner at a time just in
  time. This card does not pre-author wildcard children or authorize a move.
- Move each owner's direct tests, fixtures, and native assets with that owner;
  place only genuinely cross-owner suites in the target integration homes.
- Preserve current interfaces, schemas, output semantics, characterized
  defects, file modes, evidence ceilings, and direct-caller behavior.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Reverify a clean, stable descendant of the latest documentation-patched
  migration predecessor, its upstream relationship, and the absence of a
  conflicting mutable lane.
- Refresh the tracked residual-path roster and the live direct import,
  invocation, Make, schema, configuration, test, fixture, and documentation
  consumer graph.

## Required context

- The current
  [functional-owner inventory](../../architecture/FUNCTIONAL_OWNER_INVENTORY.md),
  target [`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md),
  direct [`MIGRATION_MECHANICS.md`](../../../src/norad/contracts/MIGRATION_MECHANICS.md),
  current [`PIPELINE_PLAN.md`](../../design/PIPELINE_PLAN.md), and report/shared-
  library TODO cards.
- Every tracked path under root `scripts/`, `jobs/`, `reports/`, `schemas/`, and
  `configs/`; remaining root-level and shared tests/fixtures; their direct
  consumers; and the completed migration records that deliberately retained
  public configuration surfaces.

## Questions owned by this card

- None.

## In scope

- Record one exhaustive grouped path-disposition ledger in the current
  functional-owner inventory, with exact target source/test homes or an
  explicit repository-level, retirement, or deferred boundary.
- Extend the target topology only where an implemented cross-cutting owner or
  repository-level exception lacks an exact final home.
- Record the dependency-correct JIT owner order, delayed domains, next eligible
  read-only selection, and residual close condition in the roadmap.
- Correct mutable reporting-card dependencies so behavior-preserving relocation
  precedes new report feature implementation and internal decomposition.
- Fix the reporting-relocation provenance rule for physical template/style
  paths without authorizing the relocation itself.
- Reconcile the current-priority and handoff routes with this documentation-
  only package.

## Out of scope

- Moving, renaming, copying, wrapping, deleting, decomposing, or changing any
  executable, schema, configuration, fixture, template, style, test-harness,
  dependency, scheduler, runtime, cluster, scientific, or evidence surface.
- Creating or selecting executable child cards, completing shared-library
  extraction, implementing setup/profile/CLI behavior, or beginning the final
  audit.
- Default-branch integration, network or cluster activity, dependency
  installation, evidence promotion, or branch publication without separate
  authority.

## Deliverables

- An exhaustive residual path-disposition ledger with exact owner boundaries.
- Exact cross-cutting source/test homes and documented repository-level
  exceptions in the target topology.
- A dependency-correct one-owner-at-a-time roadmap with scheduler, ingestion,
  and orchestration/profile deferrals.
- Corrected reporting relocation dependencies and physical-path provenance
  policy.
- Reconciled task lifecycle, current-priority, handoff, and canonical inbound
  links.

## Acceptance evidence

- Exact tracked-path searches prove that the bounded roots and shared residual
  test surfaces are covered once by the ledger and that no path is silently
  omitted or assigned two implementation owners.
- Every `MOVE` row has one exact final source/test home and a named prerequisite
  boundary; every other row states why repository retention, retirement, or
  deferral is intentional.
- The roadmap creates no wildcard child, false technological blocker, implicit
  selection, executable authorization, or claim that deferred domains exist.
- Semantic no-loss review, `git diff --check`, and the complete documentation
  gate pass; computational, report-runtime, R, shell, cluster, and scientific
  validation are not applicable to the non-consuming Markdown-only diff.

## Canonical documentation updates

- `FUNCTIONAL_OWNER_INVENTORY.md`, `SOURCE_TOPOLOGY.md`, `DECISIONS.md`,
  `PIPELINE_PLAN.md`, `HANDOFF.md`, `TODO.md`, the affected mutable report
  cards, documentation ownership links if required, and this card.

## Escalation conditions

- Stop if a residual path cannot be assigned one owner, an unknown executable
  consumer invalidates the sequence, a supposedly public configuration is an
  owner-native asset, or a proposed final dependency crosses into a peer
  implementation.
- Stop if an exact destination requires packaging, installation, scheduler,
  ingestion, orchestration, scientific-policy, evidence-promotion, or
  characterized-behavior decisions beyond this documentation package.
- Stop if lifecycle repair requires rewriting immutable completed evidence or
  if the worktree, branch, base, or approved write set becomes unexplained.

## Completion record

Selected from clean upstream-equal parent
`a8aa28b6d5331c9c7f9cec9d50c6f774ba0d8bf8` on the dedicated
`codex/plan-03a-residual-source-topology-convergence` branch after approval of
the documentation-only/non-consuming plan. The approved envelope changes only
the named documentation, task-lifecycle, and mutable dependency surfaces;
physical movement, successor selection, publication, and computational or
cluster validation remain outside it.
