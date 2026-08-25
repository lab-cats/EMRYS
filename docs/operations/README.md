# Operations documentation

This directory routes repository development, operator commands, common
diagnosis, and engineering conventions. Functional commands, faults, and
recovery detail remain beside the owner when they are not genuinely
cross-cutting. Current validation observations come from exact checks and
retained artifacts bound to a commit, not from a rolling handoff document.

- [`WORKFLOW.md`](WORKFLOW.md) defines context selection, approval, delivery,
  validation, and publication boundaries.
- [`HANDOFF.md`](HANDOFF.md) is a visibly marked legacy source retained only
  for bounded historical-evidence and recovery reconciliation under `DOC-04`.
- [`RUNBOOK.md`](RUNBOOK.md) owns supported cross-cutting commands.
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) routes symptoms, diagnosis, and
  common recovery without authorizing destructive cleanup.
- [`ENGINEERING_CONVENTIONS.md`](ENGINEERING_CONVENTIONS.md) maps repository
  tooling and stable implementation conventions.
