# ONBOARD-03A — Publish researcher onboarding path

## Objective

Publish a concise researcher-facing path from clone and explicit setup through
data intake, validation, local execution, recovery, reporting, and evidence
interpretation.

## Why this exists

The intended experience is operationally simple, but setup is necessarily
demanding because the workflow depends on explicit runtimes, references, data
contracts, and evidence boundaries. Onboarding should make that path navigable
and honest rather than hide it in brittle automation.

## Fixed decisions

- Onboarding describes the shortest supported local-pilot path demonstrated by
  the fresh-clone proof.
- It links to canonical commands instead of copying mutable runbook details.
- Setup prerequisites, data and request preparation, validation and planning,
  dry-run and execute, status and resume, outputs, receipts, logs, reports,
  recovery, and evidence limits remain explicit.
- The guide distinguishes fixture evidence, local real-runtime evidence,
  runtime blocking, cluster evidence, scientific review, and biological
  interpretation.
- It claims no cluster proof, production validation, or biological conclusion.
- The final onboarding destination is an integration-time ownership decision
  governed by `DOC-IA-01`; this card does not create a competing owner.

## Blocked by

- [E2E-03A](E2E-03A-prove-fresh-clone-local-pilot.md) — Required: onboarding must reflect an observed clean-clone and recovery path.

## Completion unblocks

- None.

## Prerequisites

- Canonical setup, operation, reporting, and recovery commands have one current
  owner at the revision used for onboarding.
- The integration owner confirms the final audience route and document owner
  under the accepted documentation information architecture.

## Required context

- [E2E-03A](E2E-03A-prove-fresh-clone-local-pilot.md) for observed researcher
  friction, transitions, and evidence boundaries.
- Completed [`DOC-IA-01`](../COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md)
  for audience, navigation, and ownership rules.
- [`REVIEW-UX-03`](REVIEW-UX-03-review-usability-plan.md) for review standards;
  its earlier plan review does not replace review of this eventual artifact.
- [`CONTEXT-09`](CONTEXT-09-define-local-maintainer-context.md), `README.md`,
  [`RUNBOOK.md`](../../operations/RUNBOOK.md), the accepted setup, intake,
  profile, and control-plane contracts, and report and evidence owners.

## Questions owned by this card

- None. The integration owner applies `DOC-IA-01` to select the destination;
  any unresolved ownership choice must be routed to its canonical question
  owner before implementation.

## In scope

- Researcher prerequisites and explicit setup.
- Data and reference placement plus manifest and request preparation.
- Validate, plan, dry-run, execute, status, resume, and report navigation.
- Expected outputs, receipts, logs, recovery, and common failure diagnosis.
- Clear local, cluster, scientific, and biological evidence boundaries.
- A short troubleshooting handoff that routes stable diagnosis to
  `TROUBLESHOOTING.md`.

## Out of scope

- Changing command or schema contracts for prose convenience; duplicating the
  runbook, architecture, or scientific policy; CSU onboarding; production
  operations; or unsupported assay claims.

## Deliverables

- A concise researcher onboarding document or entry-point section in the
  integration-owner-selected canonical location.
- Links to canonical setup, run, status, recovery, report, and evidence
  commands and owners.
- A reviewed checklist matching every required fresh-clone transition.
- Routed unresolved usability issues rather than silently invented behavior.

## Acceptance evidence

- A new researcher can identify prerequisites, add data through the declared
  contract, validate and run the local pilot, find outputs, and recover from
  the demonstrated failure path.
- Every command is canonical or clearly illustrative; executable detail remains
  in `RUNBOOK.md`.
- Setup burden and evidence limits remain explicit without implying that a
  local pass is cluster or biological validation.
- A review of the actual proof-matched guide finds no missing required
  transition.

## Canonical documentation updates

- `README.md` for the minimal entry route; `RUNBOOK.md` only when its command or
  recovery ownership changes; `TROUBLESHOOTING.md` for durable diagnosis;
  navigation, roadmap, current-state, and task owners as required by the
  accepted artifact and evidence.

## Escalation conditions

- Stop if onboarding would invent commands, hide setup, duplicate mutable
  facts, or disagree with the observed proof.
- Broaden review if audience, ownership, evidence, or public-interface claims
  change.

## Completion record

Not started. This recovered TODO card publishes no onboarding artifact and
does not select its final canonical owner.
