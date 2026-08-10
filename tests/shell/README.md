# Cross-cutting shell tests

This directory owns shell-level guards that span multiple implementation
owners. The current check protects selection of the repository-local R
environment; supported validation and restoration behavior remains owned by
the [operations runbook](../../docs/operations/RUNBOOK.md).

Shell guards provide local contract evidence only. Real R, scheduler, module,
cluster, and production-runtime evidence remain separate lanes.
