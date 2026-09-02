# Runbook

This guide owns cross-cutting operator and maintainer procedures. The
[`quickstart`](../../quickstart.md) owns the first synthetic journey;
[`configs/README.md`](../../configs/README.md) owns authored configuration;
exact producer, validator, transaction, and recovery behavior remains with each
functional owner.

Dry-runs, fixtures, availability probes, scheduler exits, and synthetic reports
do not establish production, institutional-site, scientific-review, or
biological proof. Execution, dependency changes, cleanup, and publication need
the applicable authority.

## Checkout and site orientation

Confirm the intended clean source and execution context:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
command -v emrys
```

Before Slurm work, also inspect `hostname`, `command -v sbatch`, `sinfo`, and
the loaded module set. Login nodes are for source control, small transfers,
inspection, and submission—not direct scientific execution. A remembered path,
alias, module name, or login-node executable is not compute-node evidence.

## Project and Run operations

From the exact Project root:

```bash
emrys validate
emrys runtime discover
emrys runtime discover --execute
emrys doctor
emrys run [--analysis NAME] [--profile NAME|ABSOLUTE_PATH]
emrys inspect [RUN]
emrys resume [RUN]
emrys report [RUN]
```

`runtime discover --execute` publishes the admitted inventory at
`runtime/runtime.tsv`; it does not install or load modules. Doctor derives
Project, input, runtime, storage, and execution readiness. `doctor --repair`
previews a bounded managed repair and asks on a terminal; automation requires
`--repair --execute`. Repair delegates to `uv`, Pixi, and `renv`, mutates only
the active checkout-owned `.venv`, Project `runtime/managed`, admitted storage
evidence, and one maintenance log, then requalifies.

The packaged [`runtime_policy.tsv`](../../src/emrys/resources/runtime/runtime_policy.tsv)
is the exact required-check roster. `runtime discover` reports mismatches; it
does not silently select another installation.

Omitted `--profile` selects `runtime/profiles/default.yaml`; a safe name selects
the matching Project-local file; an absolute path is exact. A profile may
select direct or whole-Run single-node Slurm placement. Slurm prints one frozen
submission plan and submits once after confirmation or explicit `--execute`.
It remains transport around the same Snakemake backend, not distributed
scientific execution.

`run` displays one immutable plan before terminal execution. Refusal, EOF, or
interruption writes and logs nothing. Full Runs invoke reporting after the
scientific receipt unless `--no-report` is supplied. `report` can independently
generate or reuse the receipt-bound report transaction without changing Run or
Attempt identity.

Omitting `[RUN]` selects the sole Run or offers a terminal picker. Automation
uses an unambiguous two-word name, exact ID, or unique ID prefix; latest is never
inferred. Inspection is read-only. Add verbose detail for canonical identities,
profile, allocation, and aggregates; use debug detail for exact paths, hashes,
receipts, task commands, and scheduler/engine facts.

Resume is valid only when inspection says recovery is available for a failed or
interrupted between-task boundary. It creates a new Attempt for the same Run,
re-admits completed work, and exposes no force, unlock, cleanup, or raw-engine
bypass. Blocked state requires explicit owner-level reconciliation.

### Reusable processing

```bash
emrys run --analysis NAME --through processing
emrys run --analysis NAME --from-processing-run PROCESSING_RUN
```

The first command creates a complete evidence-bearing Steps 00–06 Run with no
reporting. The second creates a distinct downstream Run. It requires the same
Project, compatible Reference and processing declaration, and an exact source
sample subset. Source artifacts remain stationary and content-bound; the new
Run owns Steps 07 onward, Results, reports, Attempts, and logs.

### Advanced owner routes

Direct scientific owner commands are specialist interfaces and do not create or
adopt an orchestrated Run. Current routes are indexed under
[`src/emrys`](../../src/emrys/) and by the
[`functional-owner inventory`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md).
Technical evidence commands live under `emrys debug`, including runtime
availability and storage inventory/qualification. `emrys validate all-pass`
checks the semantic meaning of one owner-validation report because validator
exit zero alone is insufficient.

The CSU-oriented live dashboard is stale and frozen. It is not the supported
status, Results, recovery, or completion surface. Use `emrys inspect` and exact
Slurm accounting/streams; its code and final disposition remain separate work.

## Slurm inspection and promotion

Use the exact job ID and `OUT`/`ERR` paths printed by submission:

```bash
squeue -j JOB_ID
sacct -X -j JOB_ID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -n +1 -F /exact/OUT /exact/ERR
```

Control-C stops `tail`, not the allocation. Empty stderr, visible output, or
`COMPLETED 0:0` is not EMRYS completion. Bind the source commit, command, input
identities, job ID, accounting, streams, native artifacts, validation records,
receipts, and evidence ceiling to the same Attempt before promotion.

Promotion is upstream-sequential. Never mix Attempts, delete a foreign lock,
hand-edit a receipt, or advance a downstream owner before required upstream
evidence passes. Use [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) before cleanup
or retry.

## Dependency maintenance

`pyproject.toml` and `uv.lock` own Python requirements; `renv.lock` owns the R
snapshot. Restore or update only as an explicit operator action. A stale lock is
an error, not authority to relock. Workflow execution, validation, rendering,
and scheduler bootstraps never install or repair dependencies.

```bash
uv lock --check
uv sync --locked --check
RENV_LIBRARY=/absolute/path/to/library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

Online freshness checks, lock updates, and snapshots require a separately
approved dependency-maintenance review. A local restored environment proves
only that configured environment.

## Resource benchmarking

`scripts/benchmark_stage_resources.py` is an opt-in low-level harness. It
accepts a closed manifest of exact setup, producer, and validator argument
vectors; previews by default; and writes trials only with `--execute`. It records
logs, wall time, peak child RSS, and validator status. Its five-percent summary
is advisory for the tested data, host, runtime, memory, and storage only and is
never silently applied. The higher-level setup integration remains backlog
work.

## Local validation

Use focused tests for feedback:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
.venv/bin/python tests/tools/source_dependencies.py --repo "$PWD"
uv lock --check
uv sync --locked --check
make -s shell-test
```

Run the assembled gate once against a final executable state when proportionate:

```bash
RSCRIPT_BIN=/absolute/path/to/Rscript make -s all-checks
```

Use `VALIDATION_ARGS=--serial` or `--verbose` only for diagnosis. Long suites
run in CI. A documentation-only change normally uses:

```bash
git diff --check
make -s documentation-check
git status --short
git diff --name-status
```

The documentation gate checks the canonical kernel, derived semantic-owner
contracts, retired paths, repository-local links and anchors, and basic Mermaid
source shape. It does not review prose, external destinations, or rendered diagrams.

## CI evidence

The executable workflow at [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
is authoritative. Pull requests run static/docs/wheel checks, Python 3.14
behavior and branch coverage, Python 3.11 compatibility, shell-owner contracts,
guarded R fixtures, workflow lint, and the managed direct golden path. Complete
Python 3.11 and 130-pair real-synthetic direct/Slurm lanes are scheduled or
manually selected; the 100,000-pair lane is weekly or explicit, not per-change.

CI may restore its selected dependencies, but validation commands themselves do
not. Green hosted CI is engineering evidence for the exact revision. The
selected real-synthetic lane adds locked-tool, single-node disposable-Slurm
evidence on that hosted runner. Neither establishes CSU/site filesystem or
module behavior, multi-node execution, production data, scientific review, nor
biological interpretation.

## Task selection

[`backlog_matrix.md`](../tasks/backlog_matrix.md) is the only durable backlog.
Select one accepted row or state one bounded objective, obtain its authority,
and follow the [`workflow kernel`](WORKFLOW.md).
