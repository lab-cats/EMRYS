# Runbook

Use the [quickstart](../../quickstart.md) for installation and a first synthetic
Project. This guide covers institutional runtimes, routine operation, and Slurm.
The [configuration guide](../../configs/README.md) explains Project inputs and
execution settings; [Troubleshooting](TROUBLESHOOTING.md) covers recovery.

Commands use Bash and the quickstart's `EMRYS_SOURCE_ROOT` and
`EMRYS_PROJECT_ROOT`. In a new terminal, set them to the same full physical paths,
then activate the checkout's command and enter the Project:

```bash
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
cd "$EMRYS_PROJECT_ROOT"
```

Stop at a failed command. Replace names such as `NAME`, `RUN`, and `JOB_ID` with
actual values; square brackets in command descriptions mark optional arguments.

`emrys --version` works from any directory without a Project or scientific
runtime. Add `-v` to see the loaded package path and Python version/executable.
It writes no logs and can identify an installation from another checkout;
ordinary commands reject a checkout that differs from the imported package.
Version flags cannot accompany a command.

## Institution-provided runtime

Use this route when the institution supplies the exact versions in
[`runtime_policy.tsv`](../../src/emrys/resources/runtime/runtime_policy.tsv):
STAR 2.7.11b, Samtools 1.19.2, GATK 4.6.1.0, Picard 3.1.1, Bcftools 1.21,
RSeQC 5.0.4, Java 17+, and R 4.6.1 with the locked R packages. For managed
installation, use [Doctor repair in the quickstart](../../quickstart.md).

On the intended execution host, load the approved modules and reactivate the
checkout's `.venv`. Each `PATH` directory must be absolute and nonempty, with
only one distinct installation per tool. If set, `JAVA_HOME` must agree with
Java on `PATH`. Replace all three example paths before running:

```bash
export EMRYS_RSCRIPT=/absolute/path/to/Rscript
export EMRYS_PICARD_JAR=/absolute/path/to/picard.jar
export EMRYS_RENV_LIBRARY=/absolute/path/to/restored/platform/library
```

Picard and R-library selectors are mandatory. The R-library path must contain
installed packages, including `renv`, not point to their parent or cache. Rscript may
instead be found on `PATH`. If the library is missing, complete
[its restore and check](#dependency-maintenance) first.

```bash
emrys validate
emrys runtime discover
emrys runtime discover --execute
emrys doctor
```

The first discovery previews without writing; execute only after every required
check passes. Success prints `Runtime inventory admitted.` and creates
`runtime/runtime.tsv`. Discovery never replaces an inventory, loads modules,
or installs software.

If Doctor finds the runtime ready but single-host storage unqualified:

```bash
emrys doctor --repair
```

Review the plan and answer `y` for the intended storage qualification. With a
ready runtime, this writes storage evidence and a maintenance log without
package installation or inventory changes. Continue after `EMRYS is ready.`
A failing institutional runtime needs institutional repair. Slurm also needs
the two storage phases below.

## Project and Run operations

For a ready Project with one Analysis and one Run:

```bash
emrys validate
emrys doctor
emrys run --log-level verbose
emrys inspect
```

For several Analyses, add `--analysis NAME` to `doctor` and `run`. Choose the
execution profile for the intended host; see the
[profile selection rules](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
and [configuration guide](../../configs/README.md).

A direct Run asks `Execute this plan? [y/N]`: `y` executes and Enter declines.
Preview without writing with `emrys run --log-level verbose </dev/null`;
automation executes with `emrys run --execute`. Full Runs generate reports
unless `--no-report` is supplied. Use the [Slurm route](#slurm-setup-and-submission)
for cluster submission.

`emrys inspect` reads the sole Run or offers a terminal picker. To select one
explicitly, use its two-word name, full ID, or unique ID prefix; EMRYS never
assumes latest. `--detail verbose` adds Run/Attempt identities and reporting
transactions; `--detail debug` adds paths, hashes, receipts, and task commands.
Planning, execution, and Doctor instead use `--log-level verbose` or `debug`.
For failed or interrupted Runs, follow [resume and recovery](TROUBLESHOOTING.md#run-and-reporting-state).

### Inspect and open reports

A successful full Run shows `Run integrity: valid`, `Attempt outcome: succeeded`,
`Scientific Results: complete`, and `Reporting: complete`. Open the printed
`Scientific report` for candidate results and `Evidence report` for execution
and provenance. Linked machine-readable tables contain the complete data;
reports do not establish biological conclusions or validate editing sites.

For the built-in Analysis, transfer the complete Run `results/` directory using
an institution-approved method, preserving its structure so HTML and table links
work. These files may contain study data. Open the copied HTML locally; retain
the complete canonical Run at its original location for provenance and recovery.
A collaborator Analysis may have different transfer requirements.

When scientific Results are complete but reporting was skipped, inspect first,
then preview on a permitted compute host:

```bash
emrys report
```

The command never prompts to write. Only when generation is admitted, run
`emrys report --execute`, then inspect again. Complete bundles are verified and
reused; partial or blocked bundles need [recovery](TROUBLESHOOTING.md#run-and-reporting-state).
Reporting does not overwrite arbitrary bundles, change scientific Results, or
create another scientific Attempt. Standalone `report` has no Slurm profile
option: obtain an approved compute allocation if the site requires one.

### Reusable processing

```bash
emrys run --analysis NAME --through processing
emrys run --analysis NAME --from-processing-run PROCESSING_RUN
```

The first creates a complete Steps 00–06 Run with supporting records and no
report. The second creates a distinct downstream Run in the same Project, with
a compatible Reference/processing definition and an exact subset of source
samples. Source artifacts remain in their original Run and are checked by
content. The new Run owns Steps 07 onward, Results, reports, Attempts, and logs.

### Advanced owner routes

Specialist scientific commands publish native outputs without creating or
adopting a Run. Find them under [`src/emrys`](../../src/emrys/) and in the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md).
`emrys debug` includes runtime and storage evidence commands;
`emrys validate all-pass` checks one owner-validation report because validator
exit zero alone does not establish semantic success.

The CSU dashboard is stale and frozen pending separate replacement work.
Use `emrys inspect` and exact Slurm accounting/streams for status and completion.

## Slurm setup and submission

Slurm submits one whole Run, including default reports, to one compute node
using the same Snakemake executor. First create the Project as in the quickstart.
Do not execute its generated direct profile on a login node.

### 1. Prepare the compute environment

Obtain the site's account, partition, QoS, CPU, memory, time, scratch, and module
settings. Viking users should start with the institution's
[access and transfer instructions](https://academic.csuohio.edu/adam/how-to-access-the-viking-cluster/).

Use the site's interactive-compute procedure. Where direct interactive
[`srun`](https://slurm.schedmd.com/srun.html) is supported, replace every
`REPLACE_...` value below. Memory is integer MiB and time is `HH:MM:SS`;
add `--qos` or another option only when supplied by the site:

```bash
srun --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --account=REPLACE_WITH_ACCOUNT --partition=REPLACE_WITH_PARTITION \
  --mem=REPLACE_WITH_MEMORY_MIB --time=REPLACE_WITH_TIME --pty bash -l
```

Wait for the compute shell: `hostname` must name the compute node and
`printenv SLURM_JOB_ID` must show its job ID. Reserving an allocation alone is
insufficient; never set the variable by hand. Defaults need at least four CPUs;
choose memory and time for the dataset/reference, not from the example profile.
The checkout, `.venv`, Project, inputs, and runtime must be visible at the same
physical paths on head and compute nodes.

In the compute shell, restore the path variables, activate the checkout's
`.venv`, and enter the Project. For the quickstart fixture:

```bash
export EMRYS_REFERENCE_FASTA="$EMRYS_PROJECT_ROOT/inputs/reference/reference.fa"
emrys validate
```

For real data, use the exact FASTA printed by validation. Prepare one runtime
here: managed `emrys doctor --repair` with approved package/download access, or
[the institutional route](#institution-provided-runtime). Keep the default
profile direct during preparation. Doctor's single-host readiness is not Slurm
qualification.

### 2. Qualify the exact storage roots

Inside that allocation, preview and execute the compute phase:

```bash
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase compute
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase compute --execute
```

Continue after `Published compute qualification receipt:` and keep its receipt
and probes. Although `--workspace` names the Project, this route tests the
**Project's parent directory** and the FASTA's parent; preview prints both.

Exit and release the allocation, return to the head node, reactivate the same
checkout, and restore the same paths. `printf '%s\n' "${SLURM_JOB_ID:-}"` must
print an empty line; do not unset it to imitate leaving an allocation. Then run:

```bash
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase finalize
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase finalize --execute
```

Continue after `Published final storage qualification receipt:`. Without
`--execute`, both phases preview without writing. They test compute-to-head
storage behavior, not the workflow, and retain evidence under
`.emrys-storage-qualification/` in the **Project's parent**. Doctor's direct
receipt lives under the Project's `runtime/` and cannot replace this requirement.
For failed or existing qualification state, follow [storage recovery](TROUBLESHOOTING.md#storage-and-slurm).

### 3. Create the Slurm profile

From the Project, copy the example to an absent profile name:

```bash
cp -n "$EMRYS_SOURCE_ROOT/configs/execution_profile.example.yaml" \
  runtime/profiles/slurm.yaml
```

Edit `runtime/profiles/slurm.yaml` with the approved site settings:

| Field under `placement` | Value |
| --- | --- |
| `account`, `partition`, `qos` | Exact site values; `qos` is the site's Quality of Service class. Use `null` only for an authorized default. |
| `cpus_per_task` | At least the requested CPUs; the unchanged default is four. |
| `memory_mb`, `time` | Integer MiB and wall-time limit. Establish adequate site memory before using `memory_mb: null`. |
| `exclusive`, `nodelist` | Keep `false` and `null` unless the site requires otherwise. |
| `scratch_parent` | A literal absolute, existing, writable compute directory with enough capacity. |
| `modules` | `mode: none`, `init: ""`, `load: []` if no module setup is needed; otherwise `mode: exact`, an absolute init file, and exact module names under `load`. |

The batch wrapper starts with `PATH=/usr/bin:/bin`. Exact module setup sources
the declared init file, purges modules, and loads only the listed names; it
neither inherits interactive modules nor installs dependencies. Record the
setup used to admit the runtime. Values are literal: no `$VARIABLE`, `~`, or
shell expansion. Keep the profile unchanged while jobs are queued or running.

### 4. Preview and submit

On the submission node, check that `command -v sbatch` and `command -v sinfo`
refer to the intended cluster, then preview without writing:

```bash
emrys run --profile slurm --log-level debug </dev/null
```

Check the profile, account/partition, resources, scheduler command, and stream
paths. `verbose` also shows profile and streams; `debug` adds the command.
This checks submission only: runtime, storage, allocation, and scientific
planning are checked again on the compute node. When the preview matches:

```bash
emrys run --profile slurm --execute
```

Add `--analysis NAME` to both commands for several Analyses. Save the printed
`JOB_ID=`, `OUT=`, and `ERR=` values. Keep supplying `--profile slurm` for cluster
Runs; the generated default profile remains direct.

## Inspecting a Slurm Run

Use the exact submitted job ID and stream paths:

```bash
squeue -j JOB_ID
sacct -X -j JOB_ID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -n +1 -F /exact/OUT /exact/ERR
```

Replace the placeholders above. Control-C stops `tail`, not the allocation.
`COMPLETED 0:0` establishes scheduler success; use `emrys inspect` for EMRYS
completion. Keep the source commit, command, inputs, job ID, accounting,
streams, outputs, validation records, and receipts tied to the same Attempt.
See [Troubleshooting](TROUBLESHOOTING.md) before retry or cleanup.

## Dependency maintenance

Institutional R restoration below requires a clean checkout and permission to
install packages. The [engineering guide](ENGINEERING_CONVENTIONS.md#dependencies-and-environments)
owns dependency policy and developer maintenance. First check the Python locks
and selected workflow environment without changing them:

```bash
cd "$EMRYS_SOURCE_ROOT"
uv lock --check
uv sync --locked --no-default-groups --group workflow --check
```

For a missing institutional R library, select the actual R 4.6.1 executable as
`EMRYS_RSCRIPT` and replace the example with an operator-owned root outside the
checkout:

```bash
export EMRYS_RENV_RESTORE_ROOT=/absolute/path/to/operator-owned/library-root
RENV_PATHS_LIBRARY="$EMRYS_RENV_RESTORE_ROOT" \
  make r-restore RSCRIPT_BIN="$EMRYS_RSCRIPT"
```

This installs through `renv` and needs locked package sources and system build
dependencies. Obtain them from the institution, or use managed Doctor repair
for a fresh managed Project; it does not authorize changing a shared library.
Copy the printed `project library:` path into `EMRYS_RENV_LIBRARY`, including
any R/platform subdirectory, then check that exact library:

```bash
make r-check RSCRIPT_BIN="$EMRYS_RSCRIPT" RENV_LIBRARY="$EMRYS_RENV_LIBRARY"
cd "$EMRYS_PROJECT_ROOT"
```

Continue to [discovery](#institution-provided-runtime) only after this read-only
check passes. Changing an admitted runtime may prevent reuse or recovery;
retain the old environment and plan changes with its owner. Local restoration
only establishes that environment; package updates and new snapshots are
separate maintenance work.

## Resource benchmarking

`scripts/benchmark_stage_resources.py` measures explicitly listed setup,
production, and validation commands. It previews by default; `--execute` writes
trials, logs, wall time, peak child memory, and validation status. Recommendations
apply only to the tested data, host, runtime, memory, and storage. EMRYS never
applies them automatically.
