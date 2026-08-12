# Design documentation

This directory owns durable cross-cutting decisions, planned acceptance,
unresolved choices, test policy, and application-level contracts. Current Git
state and evidence belong in the operations handoff; commands belong in the
runbook or the applicable functional owner.

- [`DECISIONS.md`](DECISIONS.md) routes durable rationale to focused records
  under [`decisions/`](decisions/).
- [`LOGGING_CONTRACT.md`](LOGGING_CONTRACT.md) defines the approved application
  logging interface and adoption boundary.
- [`ORCHESTRATION_CONTRACT.md`](ORCHESTRATION_CONTRACT.md) defines the accepted
  local-first Snakemake lifecycle, authority, identity, completion, resume, and
  evidence boundaries before implementation.
- [`ORCHESTRATION_READINESS.md`](ORCHESTRATION_READINESS.md) is the canonical
  owner-by-owner admission disposition and proof-target view for that pilot.
- [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md) owns roadmap and acceptance boundaries.
- [`QUESTIONS.md`](QUESTIONS.md) owns unresolved product, operational, and
  scientific choices.
- [`TEST_BASELINE.md`](TEST_BASELINE.md) owns test policy, evidence vocabulary,
  contract risks, and current recheck routes.
