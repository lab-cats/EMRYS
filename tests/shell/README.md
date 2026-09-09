# Cross-cutting shell tests

These shell checks cover behavior shared across source owners. The current
check verifies selection of the repository-local R environment. Validation
and restoration commands belong to the
[operations runbook](../../docs/operations/RUNBOOK.md); the check does not run
or qualify the full R workflow.
