# Orchestration schemas

The [orchestration contract](../../orchestration/README.md) registers and
validates these packaged resources and defines canonical JSON:

- [`v1/`](v1/README.md): shared definitions and Project, Analysis/Execution-Plan/Run,
  execution, reference, policy, Attempt, task, lock, receipt, and reporting records.
- [`v2/`](v2/README.md): active workflow profile and Attempt receipt, plus the
  retired request that embedded resources.
- [`v3/`](v3/README.md): public combined execution profile and historical request.
  Its resource-config schema remains an internal/historical dependency for
  Run-bound resource values and identity.

These files provide no separate commands or mutable configuration. The common
[version rules](../README.md#version-and-identity-rules) apply.
