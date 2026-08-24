# Orchestration contract tests

This directory directly protects the neutral
[`contracts/orchestration`](../../../src/emrys/contracts/orchestration/README.md)
owner. It tests shared record and projection semantics, not lifecycle execution
or recovery.

- `test_orchestration_contracts.py` covers the closed schema registry,
  canonical bytes and digests, cross-record invariants, paired-strata admission,
  terminal attempt/task semantics, and workspace-independent projection.
- `test_reporting_ledger_contracts.py` covers reporting start and verified
  record identity and admission.

Local-pilot execution, resume, inspection, and recovery remain protected under
`tests/orchestration/local_pilot/`. These fixtures establish local contract
behavior only.
