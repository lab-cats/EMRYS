# Design documentation

This directory owns durable cross-cutting decisions, test policy, and
application-level contracts. Accepted work and acceptance belong in the
[findings matrix](../tasks/backlog_matrix.md); checkout state comes from live
Git and validation observations from exact checks and retained artifacts.
Commands belong in the runbook or the applicable functional owner.

- [`DECISIONS.md`](DECISIONS.md) routes durable rationale to focused records
  under [`decisions/`](decisions/).
- [`LOGGING_CONTRACT.md`](LOGGING_CONTRACT.md) defines the approved application
  logging interface and adoption boundary.
- [`ORCHESTRATION_CONTRACT.md`](ORCHESTRATION_CONTRACT.md) defines the accepted
  local-first Snakemake lifecycle, authority, identity, completion, resume, and
  evidence boundaries before implementation.
- [`TEST_BASELINE.md`](TEST_BASELINE.md) owns test policy, evidence vocabulary,
  contract risks, and current recheck routes.
