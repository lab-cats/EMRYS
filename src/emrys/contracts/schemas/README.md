# Contract schemas

This directory contains versioned machine-readable schema resources owned by
neutral contract packages. It is storage, not an independent registry or
validation interface.

- [`artifacts/`](artifacts/) — artifact, run-summary, and report-receipt schema
  resources.
- [`orchestration/`](orchestration/) — Project, profile, execution, Attempt,
  task, reporting-ledger, and historical-compatibility resources.

The owning [`artifacts`](../artifacts/README.md) and
[`orchestration`](../orchestration/README.md) contracts define their selectors,
registries, canonical validation APIs, compatibility, and direct tests. This
directory publishes no output and exposes no independent validation interface.

The EMRYS namespace is a deliberate hard identity cutover. Version numbers
retain the contract lineage, but EMRYS schema IDs and schema-name values are
new identities rather than aliases for `urn:norad:*` records. This checkout
does not register pre-cutover schemas; retained records require their exact
historical checkout.
