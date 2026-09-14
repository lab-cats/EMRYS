# Orchestration contract tests

These cases test shared records from the
[orchestration contract](../../../src/emrys/contracts/orchestration/README.md):

- `test_orchestration_contracts.py`: the registered schemas, canonical bytes and
  digests, cross-record consistency, paired strata, terminal Attempt/task rules,
  and results that remain stable across workspaces.
- `test_reporting_ledger_contracts.py`: identity and validation of reporting
  start and verified records.

[Run-coordinator tests](../../orchestration/run_coordinator/README.md) separately
cover execution, resume, inspection, and recovery.
