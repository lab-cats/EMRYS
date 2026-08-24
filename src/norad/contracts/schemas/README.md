# Contract schemas

This directory contains versioned machine-readable schema resources owned by
neutral contract packages. It is storage, not an independent registry or
validation interface.

- [`artifacts/`](artifacts/) — artifact, run-summary, and report-receipt schema
  resources.
- [`orchestration/`](orchestration/) — request, profile, execution, attempt,
  task, and reporting-ledger resources.

The owning [`artifacts`](../artifacts/README.md) and
[`orchestration`](../orchestration/README.md) contracts define their selectors,
registries, canonical validation APIs, compatibility, and direct tests. This
directory publishes no output and exposes no independent validation interface.
