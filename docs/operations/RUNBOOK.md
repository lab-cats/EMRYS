# Runbook

This guide explains the commands available after an EMRYS Project has been set
up. The [`quickstart`](../../quickstart.md) owns the first successful journey;
[`configs/README.md`](../../configs/README.md) defines Project inputs and
execution settings; exact component recovery behavior stays beside the code
that owns it.

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

`runtime discover --execute` saves the checked inventory at
`runtime/runtime.tsv`; it does not install or load modules. Doctor checks the
Project, inputs, runtime, storage, and execution setup. `doctor --repair`
previews a managed repair and asks on a terminal; automation requires
`--repair --execute`. Repair delegates to `uv`, Pixi, and `renv`, changes only
the active checkout-owned `.venv`, Project `runtime/managed`, storage-check
records, and one maintenance log, then checks readiness again.

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
generate or reuse the report tied to the completed Run without changing Run or
Attempt identity.

Omitting `[RUN]` selects the sole Run or offers a terminal picker. Automation
uses an unambiguous two-word name, exact ID, or unique ID prefix; latest is never
inferred. Inspection is read-only. Add verbose detail for canonical identities,
profile, allocation, and aggregates; use debug detail for exact paths, hashes,
receipts, task commands, and scheduler/engine facts.

Resume is valid only when inspection says recovery is available after a failed
or interrupted task boundary. It creates a new Attempt for the same Run and
checks completed work before reuse. It offers no force, unlock, cleanup, or raw
Snakemake bypass. A blocked state requires the named component's recovery
procedure.

### Reusable processing

```bash
emrys run --analysis NAME --through processing
emrys run --analysis NAME --from-processing-run PROCESSING_RUN
```

The first command creates a complete Steps 00–06 Run with its supporting
records and no report. The second creates a distinct downstream Run. It
requires the same Project, a compatible Reference and processing definition,
and an exact subset of the source samples. Source artifacts remain in the
original Run and are checked by content; the new Run owns Steps 07 onward,
Results, reports, Attempts, and logs.

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

## Inspecting a Slurm Run

Before submission, confirm that `sbatch` and `sinfo` refer to the intended
cluster and that the required modules will be available on the compute node.
Login nodes are for source control, small transfers, inspection, and
submission—not scientific execution.

Use the exact job ID and `OUT`/`ERR` paths printed by submission:

```bash
squeue -j JOB_ID
sacct -X -j JOB_ID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -n +1 -F /exact/OUT /exact/ERR
```

Control-C stops `tail`, not the allocation. Empty stderr, visible output, or
`COMPLETED 0:0` means only that Slurm finished successfully; use `emrys inspect`
to determine whether EMRYS completed. Keep the source commit, command, inputs,
job ID, accounting, streams, outputs, validation records, and receipts tied to
the same Attempt.

Never mix Attempts, delete an unfamiliar lock, hand-edit a receipt, or start
downstream work before the required upstream checks pass. Use
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) before cleanup or retry.

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

Checking for newer packages, updating locks, and creating new snapshots are
separate maintenance work. A successful local restore applies only to that
configured environment.

## Resource benchmarking

`scripts/benchmark_stage_resources.py` is an optional low-level tool. Its input
lists the exact setup, production, and validation commands to measure. It
previews by default and writes trials only with `--execute`. It records logs,
wall time, peak child memory, and validation status. Its recommendation applies
only to the tested data, host, runtime, memory, and storage, and EMRYS never
applies it automatically.
