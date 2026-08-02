# CLI-03A — Implement local-pilot control plane

## Objective

Implement a thin user-facing local-pilot command surface that routes setup,
intake, profile planning, local execution, status, resume, and report handoff
to their accepted owners.

## Why this exists

A researcher should not need to memorize repository-internal script order or
assemble state transitions manually. One inspectable entry path can coordinate
the current owners without taking over scientific algorithms, dependency
restoration, or evidence policy.

## Fixed decisions

- The control plane is thin, filesystem-inspectable, and new implementation;
  the current repository has no autonomous whole-pipeline orchestrator.
- It owns user-facing command selection, argument parsing and translation into
  neutral contracts, exit mapping, and presentation of status, failure, and
  report handoff. Its thin dispatch invokes SETUP-owned readiness,
  ingestion-owned admission, PROFILE-owned plan projection, and
  orchestration-owned execution and lifecycle operations through public
  interfaces; it does not redefine or persist those semantics.
- Orchestration owns workflow order, run and attempt state, resume decisions,
  status facts, and requested report coordination. The CLI never infers order
  from paths or numeric aliases and never imports private owner implementation.
- Existing scientific scripts, validators, and renderers retain their behavior
  and ownership; the control plane does not reimplement STAR, samtools,
  bcftools, R, validation, or rendering.
- It never installs dependencies, infers scientific inputs by glob, hides
  state, or promotes evidence.
- The repository-local pilot is distinct from the later installable and public
  interface under [`FUT-CLI-03`](FUT-CLI-03-installable-norad-control-plane.md).
- Dry-run is the default and publishes no final output.
- Direct runner means approved local execution only. This card authorizes no
  SLURM submission or scheduler policy.

## Blocked by

- [SETUP-03A](SETUP-03A-implement-local-pilot-dependency-profile-and-doctor.md) — Required: explicit setup readiness must exist before the control plane can run a pilot.
- [INTAKE-03A](INTAKE-03A-implement-yaml-tsv-run-lifecycle.md) — Required: request, manifest, run identity, and attempt state must be stable before coordination.
- [PROFILE-03A](PROFILE-03A-materialize-local-pilot-workflow-profile.md) — Required: the control plane needs one concrete typed workflow profile.

## Completion unblocks

- [E2E-03A](E2E-03A-prove-fresh-clone-local-pilot.md) — Fully: the complete local-pilot control path can then be exercised from a clean checkout.

## Prerequisites

- Freeze exact local command names, supported subcommands, exit behavior,
  filesystem state locations, and output roots during the approved task plan.
- Bound execution to local direct runners; inspecting job definitions must not
  authorize scheduler submission.
- Keep the control-plane mechanics fixture distinct from the later clean-clone
  researcher-journey proof.

## Required context

- The three direct blocker cards above and their final accepted contracts.
- [`FUT-CLI-03`](FUT-CLI-03-installable-norad-control-plane.md) and
  [`CHOICE-CONTROL-01`](../../design/QUESTIONS.md#choice-control-01--exact-installable-cli-surface-and-asset-materialization)
  as later packaging and public-interface context, not a question owned here.
- [`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md) for
  CLI, orchestration, public-entry-point, and dependency-direction boundaries;
  [`STAGE_MAP.md`](../../../src/norad/contracts/STAGE_MAP.md) for the semantic
  identities and DAG the CLI must not duplicate.
- Completed [`ARCH-02C`](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md)
  as historical decision and acceptance context, plus
  completed [`DOC-IA-01`](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md),
  current and future architecture control-state sections, and the functional-
  owner inventory.
- Current scripts, Make targets, validators, receipts, reports, runtime
  preflight, and public-contract characterization surfaces.

## Questions owned by this card

- None. Exact local interface choices are task-plan decisions within this
  bounded card; installable/public choices remain with `FUT-CLI-03`.

## In scope

- A thin local entry point for validate, plan, run, status, resume, report, and
  stage inspection.
- Explicit configuration, authorized inputs, and resolved output roots.
- Delegation to ingestion-owned admission and orchestration-owned claim,
  identity, retry/resume, status, failure, and report coordination, with
  command-level reporting of their exact results.
- Delegation to setup, intake, and profile validation before expensive work,
  to the profile-owned plan projection, and to orchestration for workflow
  ordering and execution decisions.
- Thin dispatch only through public orchestration or functional-owner entry
  points; never direct import of private scripts, validators, or renderers.
- Focused command, exit, status, failure, and resume tests with tiny fixtures
  and mocked tools.

## Out of scope

- Universal packaging or public versioning; hidden installation; service or
  cloud control planes; scientific reimplementation; SLURM submission;
  scheduler policy; production evidence; threshold changes; or evidence-state
  promotion.

## Deliverables

- The local-pilot entry point and command contract.
- Command projections of profile-owned plans and orchestration-owned status,
  resume, and failure state without a second persistence model.
- Public-interface dispatch to orchestration and functional owners for the
  materialized local profile.
- Focused contract tests and a small inspectable mechanics fixture.

## Acceptance evidence

- A valid request can be validated and planned without executing analysis.
- Local execute mode delegates to declared owners and publishes only validated
  outputs.
- An injected failure leaves inspectable status; resume preserves run identity,
  rechecks inputs, predecessors, locks, and profile identity through the owning
  interfaces, and does not make an unauthorized duplicate claim.
- Invalid setup, intake, profile, predecessor, and output conditions fail early
  with actionable messages.
- Repository development and local-pilot operation expose the same contracts
  without hidden state or dependency bootstrap.

## Canonical documentation updates

- `RUNBOOK.md` for exact commands, state inspection, and recovery; `README.md`
  for the minimal researcher route; architecture, decision, question, roadmap,
  and task owners only for accepted interface and ownership changes.

## Escalation conditions

- Stop if the control plane would own scientific algorithms, workflow order,
  run or attempt state, hide state, infer inputs, import private owner
  implementation, install dependencies, submit cluster jobs, or change an
  unresolved public contract.
- Stop if resume can publish without stable input, predecessor, lock, and
  profile-identity checks.
- Broaden review for SLURM, schema, report, transaction, or evidence-promotion
  effects.

## Completion record

Not started. This recovered TODO card creates no local command or execution
authority.
