# Tests

This tree owns local regression, contract, and characterized-behavior
protection. The canonical policy, evidence vocabulary, coverage rules, and
risk routes are in the
[test baseline](../docs/design/TEST_BASELINE.md); supported validation commands
are in the [operations runbook](../docs/operations/RUNBOOK.md).

## Routes

- `analyses/`, `stages/`, `evidence/`, `ingestion/`, and `reporting/` protect
  their matching functional owners.
- `orchestration/local_pilot/` protects Project admission, readiness, fixed
  graph materialization, task/reporting records, lifecycle, inspection, resume,
  and focused failure/resume behavior for the application owner. The tracked
  CI workflow owns the clean-clone, real-tool managed golden path.
- `contracts/` and `contract_integration/` protect shared and independent
  public contracts.
- `libraries/`, `documentation/`, `shell/`, and `data_checks/` own
  cross-cutting support checks.
- `fixtures/`, `baselines/`, and `tools/` own shared test inputs, accepted
  comparator state, and test-only runners.

The files directly under this directory protect cross-cutting public CLI,
whole-Run Slurm transport/parity, validation-runner, coverage-policy, package,
and grouped-CLI behavior.
All results remain local engineering evidence unless a separate canonical
owner explicitly establishes a higher evidence state.
