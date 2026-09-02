# Architecture diagrams

This directory contains tracked Mermaid sources for the system views owned by
the parent architecture documents. A diagram illustrates its named view; it
does not replace implementation contracts or prove that a future design exists.

Current-system views:

- [`current_user_pipeline.mmd`](current_user_pipeline.mmd) — scientist-facing
  workflow phases.
- [`pipeline.mmd`](pipeline.mmd) — grouped implemented-system projection.
- [`reliability.mmd`](reliability.mmd) — validation, publication, and recovery
  flow.
- [`run_coordinator.mmd`](run_coordinator.mmd) — implemented
  local-first request, readiness, public control, execution, validation,
  failure, resume, and completion flow.

Interpret current diagrams through [`ARCHITECTURE.md`](../ARCHITECTURE.md).
Accepted future outcomes live in the
[findings matrix](../../tasks/backlog_matrix.md), while unsliced alternatives
remain in the temporary
[architecture campaign](../../tasks/architecture_campaign.md).
