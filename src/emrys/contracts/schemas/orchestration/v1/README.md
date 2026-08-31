# Local-pilot orchestration schemas v1

This directory contains fourteen Draft 2020-12 JSON resources: one shared
definition resource plus thirteen registered selectors for the active Project,
successor Analysis/Execution-Plan/Run model, historical normalized execution
identity, reference and analysis policy, run locks, workflow attempts, the
historical v1 attempt receipt, task entry/attempt/verified records, and
reporting entry/verified records.

The workflow-profile resource is a v2 sibling, while the combined execution
profile and privately retained historical request are v3 siblings. The
canonical registry, JSON bytes, and validation API live in
[`contracts/orchestration`](../../../orchestration/README.md); this directory
is packaged schema storage and produces no independent output.
