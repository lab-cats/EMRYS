# Test baseline and contract-risk index

This document owns test policy and cross-cutting risk routes. Current test
inventory, thresholds, durations, and exact counts live in tracked machine
baselines and executable tooling, not duplicated prose.

## Evidence boundary

Python coverage measures executed Python statements and branches, including its
traced subprocess routes. It does not measure shell or R source, prove
expectation independence, or replace scenario, transaction, recovery,
real-runtime, scheduler, numerical-oracle, scientific-review, or biological
evidence. A ratio is a regression signal, not authority to change behavior.

The vocabulary used in review is:

- **preserved contract:** independent protection covers the declared boundary;
- **characterized defect:** observed behavior remains a defect, not an approved
  contract;
- **decision required:** semantics are unresolved, so implementation stops; and
- **environment-deferred:** local protection exists but the named runtime,
  scheduler, site, production, or review evidence is absent.

A protection is executable/static defense. Evidence is a retained result or
artifact supporting a bounded claim, reproduction, or recovery. A fixture,
golden, or oracle may be both. Protection replacement follows
[`AC-GUARD-005`](decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails);
retained-evidence deletion separately follows `AC-GUARD-008`.

## Python coverage policy

[`tests/baselines/python_coverage.json`](../../tests/baselines/python_coverage.json)
is the authoritative reviewed snapshot. The comparator and policy tests are
[`python_coverage_baseline.py`](../../tests/tools/python_coverage_baseline.py)
and [`test_python_coverage_baseline.py`](../../tests/test_python_coverage_baseline.py).

The gate measures branches over `scripts` and `src/emrys`, includes configured
subprocess coverage, rejects exact-ratio regression globally and for every
critical-owner aggregate, and requires newly declared shared modules to meet
the configured introduction floors. Private modules may move or disappear when
their aggregate owner remains protected. Baseline changes are explicit reviewed
mutations:

```bash
make python-coverage-check
make python-coverage-baseline-update
git diff -- tests/baselines/python_coverage.json
make python-coverage-check
```

CI shards the complete Python inventory using the executable plan and duration
data under `tests/tools/` and `tests/baselines/`. Merge requires complete,
disjoint, current receipts matching that deterministic plan before combining
coverage. Duration estimates affect scheduling only.

## Independent expectations

An expectation must not import or derive the production rule it is intended to
detect. Producer-coupled fixtures remain useful only as additional integration
evidence. Important independent routes include:

| Risk | Protection |
|---|---|
| Public CLI, arbitrary CWD, shell/R/file-mode behavior | `tests/test_public_cli_contracts.py` and the affected owner suite |
| Direct/Slurm placement, recovery, and synthetic parity | run-coordinator execution, submission, lifecycle, materialization, and `tests/tools/real_synthetic_e2e.py` suites |
| Exact validation check rosters | `tests/contract_integration/validation_rosters/` |
| Schemas, deterministic bytes, and statuses | contract-owner tests plus `tests/contract_integration/independent_contract_goldens/` |
| Step 09 statistics and estimability | independent CMH oracle, fixed owner corpus, and guarded real-R comparison |
| Shared validation/publication primitives | direct library tests and affected consumer transaction suites |

Validators may intentionally publish readable `status=fail` rows while exiting
zero; malformed or unsafe operation exits nonzero and publishes nothing.
Restore and baseline-update targets are explicit operator mutations, never test
side effects.

## Validation lanes

`make all-checks` is the assembled local gate. It checks the selected locked
environment without repairing it, runs static preflight first, then the
independent Python coverage, installed-wheel, shell-owner, and guarded-real-R
lanes. CI may run the same inventory in verified shards and supplies selected
long real-synthetic lanes. Exact commands and evidence ceilings are in the
[`runbook`](../operations/RUNBOOK.md#local-validation).

Use focused owner tests during implementation and the complete applicable gate
once on the final affected state. Long checks run in CI. Quiet successful logs
may be ephemeral; failed, interrupted, and peer-cancelled lanes retain bounded
diagnostics. Nox remains rejected because matching the current process-group
cancellation and retained-failure behavior would require a larger custom
supervisor; `uv` remains the environment authority.

## Contract-risk checklist

For a changed boundary, inspect the applicable risks rather than relying on
coverage alone:

- public help, dry-run, execute, malformed input, overwrite, exit, and
  no-write/no-log refusal behavior;
- producer-specific locks, staging, validation, publication, rollback,
  interruption, recovery, and unrelated-file behavior;
- literal validation schemas and ordered check rosters;
- deterministic schemas, headers, bytes, identities, and statuses;
- same-size mutations, restored mtimes, symlinks/hardlinks, descriptor/path
  identity, signals, cleanup, and recovery evidence;
- arbitrary CWD, environment isolation, direct/Slurm placement, runtime and
  storage admission, and exact source/tool identity;
- report read-only behavior, transaction boundaries, missing evidence, and
  non-promotion; and
- Step 09 count construction, CMH calculation, multiple-testing family, and
  independent numerical comparison.

Scenario, owner, integration, and real-environment protection should overlap
only where they detect different failures or support different evidence levels.
Delete check-only duplication after proving the surviving defense; retain
independent fault and scientific oracles. Current characterized defects remain
with their owner contracts and tests rather than in a duplicate central matrix.
