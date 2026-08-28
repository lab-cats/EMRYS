# Orchestration schemas

This directory stores versioned machine resources for the neutral local-pilot
orchestration contract owner. The supported registry and validation API are
documented in [`../../orchestration`](../../orchestration/README.md).

- [`v1/`](v1/) — shared definitions plus active execution, reference, policy,
  attempt, task, lock, receipt, and reporting-ledger records.
- [`v2/`](v2/) — the active workflow profile and retired resource-embedded
  request contract.
- [`v3/`](v3/) — the active resource-independent request and public combined
  execution profile. Its resource-config schema remains an internal/historical
  dependency for the Run-bound resource projection and identity.

[`contracts/orchestration/api.py`](../../orchestration/api.py) selects and
validates this mixed-version registry and owns canonical JSON. These directories
are packaged resources, not separate public validators.
