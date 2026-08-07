# E2E-03A — Prove fresh-clone local pilot

## Objective

Prove that a researcher can start from a clean clone, perform explicit setup,
add authorized data, validate and run the local pilot, inspect outputs and
reports, and recover from a controlled failure.

## Why this exists

Component-level setup, intake, profile, and control-plane evidence can all pass
while the researcher journey remains fragmented. A fresh-clone proof exposes
the integrated setup burden, runtime requirements, recovery behavior, and
evidence ceiling.

## Fixed decisions

- The proof starts from a clean checkout and uses explicit operator-controlled
  dependency restoration.
- Data and references are authorized by exact path and hash; filenames do not
  infer scientific meaning.
- Acceptance may use an approved small real-data pilot or safe fixtures, but
  the choice remains explicit. Fixture-only results are locally fixture-tested;
  real-runtime claims require approved real inputs and an actual guarded run.
- A passing local run remains local evidence. It is not cluster proof,
  completed scientific review, or biological validation.
- Outputs remain `CMH-ranked candidates`, not validated editing sites.
- Failure, status, and resume evidence are required; a clean success alone is
  insufficient.

## Blocked by

- [CLI-03A](CLI-03A-implement-local-pilot-control-plane.md) — Required: the complete setup, intake, profile, and local coordination path must exist before the integrated proof.

## Completion unblocks

- [ONBOARD-03A](ONBOARD-03A-publish-researcher-onboarding.md) — Fully: onboarding can then be written against an observed clean-clone and recovery journey.

## Prerequisites

- An operator supplies or approves the small data and reference set, records
  exact identity and hashes, and confirms that no private or large artifacts
  will be committed.
- Select fixture-only or approved real-runtime evidence explicitly before
  execution; do not upgrade the evidence label after the fact.

## Required context

- [SETUP-03A](SETUP-03A-implement-local-pilot-dependency-profile-and-doctor.md),
  [INTAKE-03A](INTAKE-03A-implement-yaml-tsv-run-lifecycle.md),
  [PROFILE-03A](PROFILE-03A-materialize-local-pilot-workflow-profile.md), and
  [CLI-03A](CLI-03A-implement-local-pilot-control-plane.md).
- [`RUNBOOK.md`](../../operations/RUNBOOK.md) setup, local validation,
  execution, failure, recovery, report, and evidence-boundary sections.
- [`REVIEW-UX-03`](REVIEW-UX-03-review-usability-plan.md) for usability review
  context, not a blocker.
- Current tiny fixtures, receipts, validation outputs, report bundle, status
  inspection, and recovery surfaces.

## Questions owned by this card

- None. The approved task plan must explicitly choose and label fixture versus
  real-runtime lanes without creating a durable question-owner conflict.

## In scope

- Clean-clone preparation and explicit dependency restoration.
- Input and reference authorization, request and manifest creation,
  validation, and dry-run.
- Small local-pilot execution plus artifact, status, receipt, and report
  inspection.
- Controlled stage failure, diagnosis, resume, and final recovery.
- Recording setup and run friction, missing prerequisites, and exact evidence
  states.
- A reproducible proof command or checklist that never installs dependencies.

## Out of scope

- Cluster execution, CSU module claims, production scale, scientific review,
  fixture output relabeled as real-runtime evidence, broad benchmarking, or
  universal assay compatibility.

## Deliverables

- An immutable, revision- and input-bound fresh-clone proof record that does
  not become a second current-state owner.
- A small approved input and reference manifest or fixture recipe.
- Success, controlled-failure, status, resume, output, report, and evidence-
  classification results.
- A bounded list of remaining setup or onboarding defects.

## Acceptance evidence

- A clean clone reaches a validated dry-run using only documented explicit
  setup actions.
- The pilot produces inspectable outputs, receipts, status, and report
  artifacts without hidden input discovery.
- An injected failure remains diagnosable and resumable; resume preserves
  identity, rechecks inputs, and publishes no invalid or partial final
  transaction.
- Fixture, local real-runtime, runtime-blocked, cluster, scientific-review, and
  biological states are labeled exactly according to inspected evidence.

## Canonical documentation updates

- `RUNBOOK.md` for verified commands and recovery; `README.md` for the concise
  route; `HANDOFF.md` for current inspected evidence; `PIPELINE_PLAN.md` for
  roadmap state; and only the stable evidence or limitation owners affected by
  the accepted proof.

## Escalation conditions

- Stop for unrecorded private data, uncontrolled paths, hidden installation,
  production artifacts, or any attempt to promote local results into cluster,
  scientific, or biological evidence.
- Re-plan if the proof exposes a contract, acceptance, or ownership defect in
  a prerequisite card.

## Completion record

Not started. This recovered TODO card authorizes no data use or execution; both
require a separately approved task plan and explicit input authority.
