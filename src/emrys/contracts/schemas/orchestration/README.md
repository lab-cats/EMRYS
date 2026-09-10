# Orchestration schemas

The [orchestration contract](../../orchestration/README.md) registers and
validates these packaged resources and defines canonical JSON:

- [`v1/`](v1/README.md): shared definitions and current Project,
  Analysis/Execution-Plan/Run, reference, module policy, workflow Attempt, task,
  lock, and reporting records.
- [`v2/`](v2/README.md): workflow profile and scientific Attempt receipt.
- [`v3/`](v3/README.md): combined execution profile and its Run-bound resource
  values.

These files provide no separate commands or mutable configuration. The common
[version rules](../README.md#version-and-identity-rules) and
[version-support policy](../../../../../docs/design/decisions/platform-direction.md#version-support)
apply. Directory names locate resources; the registry selects the current
record identifiers and never chooses a historical schema from input content.
