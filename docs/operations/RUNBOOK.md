# Runbook

Use the [`quickstart`](../../quickstart.md) for installation and a first
synthetic Project. This guide covers institution-provided runtimes, Slurm,
repeat operation, and maintenance. The [configuration guide](../../configs/README.md)
defines Project inputs and execution settings.

Commands below use Bash and the quickstart's `EMRYS_SOURCE_ROOT` and
`EMRYS_PROJECT_ROOT` variables. Set them again to the same full, physical paths
when opening another terminal. Activate the checkout's command and enter the
Project before using ordinary EMRYS commands:

```bash
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
cd "$EMRYS_PROJECT_ROOT"
```

Stop at a failed command and use the matching diagnosis below before
continuing. Names such as
`NAME`, `RUN`, and `JOB_ID` in command descriptions are values to replace;
square brackets describe optional arguments and are not typed literally.

## Institution-provided runtime

Use this alternative only when the institution can supply the exact runtime.
For a managed runtime, follow Doctor repair in the quickstart instead. Loading
a generic bioinformatics or R module is not sufficient: the packaged
[`runtime_policy.tsv`](../../src/emrys/resources/runtime/runtime_policy.tsv)
specifies the required versions and checks. These include STAR 2.7.11b,
Samtools 1.19.2, GATK 4.6.1.0, Picard 3.1.1, Bcftools 1.21, RSeQC 5.0.4,
Java 17 or newer, and R 4.6.1 with the locked R packages.

On the intended execution host, load the exact site-approved modules, then
activate the checkout's `.venv` again. Every directory in `PATH` must be
absolute and nonempty. Discovery requires one distinct installation of each
tool; it rejects ambiguity instead of choosing the first executable on `PATH`.
If `JAVA_HOME` is set, its Java must agree with the Java exposed on `PATH`.

Set the following selectors to the **actual absolute paths** supplied by the
institution. Replace all three example values before running this block:

```bash
export EMRYS_RSCRIPT=/absolute/path/to/Rscript
export EMRYS_PICARD_JAR=/absolute/path/to/picard.jar
export EMRYS_RENV_LIBRARY=/absolute/path/to/restored/platform/library
```

`EMRYS_PICARD_JAR` and `EMRYS_RENV_LIBRARY` are mandatory. The latter is the
existing directory containing installed packages, including `renv`, rather
than a library parent or cache. `EMRYS_RSCRIPT` explicitly selects Rscript;
otherwise discovery searches `PATH`. If the institution has not restored the
locked R library, complete [dependency maintenance](#dependency-maintenance)
before discovery.

```bash
emrys validate
emrys runtime discover
emrys runtime discover --execute
emrys doctor
```

The first discovery is read-only. Continue to publication only when every
required check passes. Publication prints `Runtime inventory admitted.` and
creates `runtime/runtime.tsv`; it never overwrites an existing inventory.
Discovery neither loads modules nor installs software.

A fresh Project still needs storage qualification. If Doctor reports that the
runtime is ready but single-host storage is unqualified, run:

```bash
emrys doctor --repair
```

Review the plan and answer `y` only for the intended storage qualification.
With an already-ready institution runtime, this plan probes storage and writes
its receipt and maintenance log without invoking package managers or changing
the admitted runtime inventory. Continue only after `EMRYS is ready.` If the
runtime itself is failing, repair it through the institution; Doctor preserves
site-owned environments. Slurm additionally requires both phases below.

## Project and Run operations

After readiness, these are the ordinary commands for a Project with one
Analysis and one Run:

```bash
emrys validate
emrys doctor
emrys run --log-level verbose
emrys inspect
```

Omitted `--profile` selects `runtime/profiles/default.yaml`; a safe name selects
the matching Project-local file without typing `.yaml`; an absolute path is
exact. For several Analyses, add `--analysis NAME` to `doctor` and `run`.

For direct placement, `run` displays the plan and asks
`Execute this plan? [y/N]` in a terminal. `--log-level verbose` shows resources
and execution detail. Answering `y` executes; pressing Enter declines. A
guaranteed no-write preview uses `emrys run --log-level verbose </dev/null`.
Automation executes with `emrys run --execute`. Full Runs generate reports after scientific
completion unless `--no-report` is supplied. Slurm submission is described
[below](#slurm-setup-and-submission).

Omitting `[RUN]` selects the sole Run or offers a terminal picker. Automation
uses an unambiguous two-word name, exact ID, or unique ID prefix; latest is never
inferred. Inspection is read-only: `emrys inspect --detail verbose` shows Run
and Attempt identities and reporting transactions; `--detail debug` adds exact
paths, hashes, receipts, and task commands. For planning, execution, or Doctor
diagnostics, use `--log-level verbose` or `--log-level debug` instead.

Resume is valid only when inspection says recovery is available after a failed
or interrupted task boundary. It creates a new Attempt for the same Run and
checks completed work before reuse. It offers no force, unlock, cleanup, or raw
Snakemake bypass. A blocked state requires the named component's recovery
procedure. On a terminal, `emrys resume RUN` asks before executing; use
`emrys resume RUN </dev/null` to preview without confirmation. For a Slurm
Attempt, select the appropriate profile explicitly, for example
`emrys resume RUN --profile slurm`.

### Inspect and open reports

For a successful full Run, `emrys inspect` should show `Run integrity: valid`,
`Attempt outcome: succeeded`, `Scientific Results: complete`, and
`Reporting: complete`. Read the displayed `Scientific report` and
`Evidence report` locations. Open the scientific HTML for candidate results and
the evidence HTML for execution and provenance details. Use the linked
machine-readable tables for complete data. A report does not validate editing
sites or establish biological conclusions.

For the built-in Analysis, copy the Run's complete `results/` directory to a
permitted local location, retaining its directory structure so relative report
and table links work. Use the institution's file-transfer method; these files
may contain study data. Open the copied HTML files in a browser. Copying only
the two HTML files can break downloadable-table links. Retain the complete
canonical Run at its original location; this viewing copy is not a replacement
for its provenance and recovery records. A collaborator Analysis may have
different transfer requirements.

If scientific Results are complete but reporting was skipped, inspect first,
then preview on a permitted compute host:

```bash
emrys report
```

This command never prompts to write. Only if it admits report generation use
`emrys report --execute`, then inspect again. An already-complete bundle is
verified and reused. Partial, inconsistent, or blocked reporting state must be
preserved for [recovery](TROUBLESHOOTING.md#run-and-reporting-state). The command
does not overwrite or regenerate arbitrary bundles, change scientific Results,
or create another scientific Attempt. Standalone `report` has no Slurm profile
option; obtain an approved compute allocation when the site requires one.

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

## Slurm setup and submission

This route submits one whole Run, including default reporting, to one compute
node. Slurm is transport around the same Snakemake executor. Start after
creating the Project in the quickstart; do not execute `emrys run` with its
generated direct profile on a login node.

### 1. Prepare the compute environment

Obtain cluster access and the institution's authorized account, partition,
QoS, CPU, memory, time, scratch, and module settings. For Cleveland State's
Viking cluster, start with the institution's
[access and file-transfer instructions](https://academic.csuohio.edu/adam/how-to-access-the-viking-cluster/).

Use the site's interactive-compute procedure. Where the site supports a direct
interactive [`srun`](https://slurm.schedmd.com/srun.html), the command has this
shape. Replace every `REPLACE_...` value; memory is an integer in MiB, and time
uses `HH:MM:SS`. Add a site-required `--qos` or other allocation option only
with the site's supplied value:

```bash
srun --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --account=REPLACE_WITH_ACCOUNT --partition=REPLACE_WITH_PARTITION \
  --mem=REPLACE_WITH_MEMORY_MIB --time=REPLACE_WITH_TIME --pty bash -l
```

Wait for the allocated compute shell. A shell on the login node after merely
reserving an allocation is insufficient. Confirm that `hostname` names the
compute node and `printenv SLURM_JOB_ID` prints its job ID. Do not set that
variable by hand.

The unchanged EMRYS resource defaults require at least four allocated CPUs.
Memory and time must be chosen for the dataset and reference; the example
profile is not a capacity recommendation. The same canonical source checkout,
its `.venv`, the Project, all inputs, and admitted runtime paths must remain
visible at the same paths from the head and compute nodes.

In that compute shell, set the path variables again if needed, activate the
checkout's `.venv`, and enter the Project. For the quickstart fixture:

```bash
export EMRYS_REFERENCE_FASTA="$EMRYS_PROJECT_ROOT/inputs/reference/reference.fa"
emrys validate
```

For real data, set `EMRYS_REFERENCE_FASTA` to the exact FASTA printed by
`emrys validate`. Prepare **one** runtime route here: either the quickstart's
`emrys doctor --repair` managed setup, with its package managers and approved
download access, or the [institution-provided runtime](#institution-provided-runtime)
procedure above. Keep `runtime/profiles/default.yaml` as direct during this
initial preparation. Doctor's single-host readiness does not qualify Slurm.

### 2. Qualify the exact storage roots

While still in the compute allocation, preview and then execute the first
phase for this Project and reference:

```bash
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase compute
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase compute --execute
```

Continue only after `Published compute qualification receipt:`. Preserve the
receipt and probes. The command takes the Project path as `--workspace`, but
the two-phase route probes its **parent directory** and the FASTA's parent;
the preview prints both exact roots.
Exit the compute shell and finish/release that allocation using the site's
procedure. Return to the head/login node, reactivate the same checkout, and
restore the same path variables. `printf '%s\n' "${SLURM_JOB_ID:-}"` must now
print an empty line; do not unset it to imitate having left an allocation.

Run the second phase there:

```bash
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase finalize
emrys debug storage-qualification \
  --workspace "$EMRYS_PROJECT_ROOT" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase finalize --execute
```

Continue only after `Published final storage qualification receipt:`. Both
commands preview without writing when `--execute` is absent. This checks
compute-to-head storage behavior and retains the evidence in
`.emrys-storage-qualification/` under the **Project's parent directory**; it
does not run the scientific workflow. The direct Doctor receipt instead lives
under the Project's `runtime/` directory.
If qualification fails or evidence already exists, use
[storage troubleshooting](TROUBLESHOOTING.md#storage-and-slurm). Do not delete
receipts or probes and repeat the commands. Doctor repair cannot substitute a
direct receipt for this two-phase Slurm requirement.

### 3. Create the Slurm profile

From the Project root, copy the example to an **absent** Project profile name:

```bash
cp -n "$EMRYS_SOURCE_ROOT/configs/execution_profile.example.yaml" \
  runtime/profiles/slurm.yaml
```

Open `runtime/profiles/slurm.yaml` in a text editor. Replace the example values
with the institution's approved settings before proceeding:

| Field under `placement` | What to enter |
| --- | --- |
| `account`, `partition`, `qos` | The exact site values; use YAML `null` only when the scheduler's default is authorized. |
| `cpus_per_task` | At least the workflow's requested CPUs; the unchanged default is four. |
| `memory_mb`, `time` | Approved integer memory in MiB and wall-time limit. `memory_mb: null` asks Slurm to use its site default, whose adequacy you must establish. |
| `exclusive`, `nodelist` | Keep `false` and `null` unless the site explicitly requires otherwise. |
| `scratch_parent` | An existing real writable directory on the compute node with suitable capacity; enter its literal absolute path. |
| `modules` | Use `mode: none`, `init: ""`, `load: []` only when the admitted tools need no module setup. Otherwise use `mode: exact`, a literal absolute module-init file, and the exact module names under `load`. |

The batch wrapper resets `PATH` to `/usr/bin:/bin`. With exact module policy it
sources the declared init file, purges modules, and loads only the listed names.
It does not inherit your interactive module setup or install dependencies.
Record the module setup needed by the runtime you admitted in step 1.
Profile values are literal: `$VARIABLE`, `~`, and shell commands are not
expanded. Keep the Project profile unchanged while a job is queued or running.

### 4. Preview and submit

On the head/submission node, confirm `command -v sbatch` and `command -v sinfo`
refer to the intended cluster. This command guarantees a no-write preview:

```bash
emrys run --profile slurm --log-level debug </dev/null
```

Check the exact profile, scheduler command, account/partition, resource request,
and stdout/stderr paths. `--log-level verbose` shows the profile and stream
paths; `debug` also shows the scheduler command. The head-node preview covers
submission. Runtime, storage, allocation, and the scientific plan are admitted
again on the compute node; successful preview does not prove they will pass.

When the displayed submission matches the approved setup:

```bash
emrys run --profile slurm --execute
```

For several Analyses, add `--analysis NAME` to both commands. Submission prints
`JOB_ID=`, `OUT=`, and `ERR=`. Save those exact values. The generated direct
default remains available, so keep supplying `--profile slurm` for cluster Runs.

## Inspecting a Slurm Run

Use the exact job ID and `OUT`/`ERR` paths printed by submission:

```bash
squeue -j JOB_ID
sacct -X -j JOB_ID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -n +1 -F /exact/OUT /exact/ERR
```

Replace `JOB_ID` and both stream paths above with the printed values.
Control-C stops `tail`, not the allocation. Empty stderr, visible output, or
`COMPLETED 0:0` means only that Slurm finished successfully; use `emrys inspect`
to determine whether EMRYS completed. Keep the source commit, command, inputs,
job ID, accounting, streams, outputs, validation records, and receipts tied to
the same Attempt.

Never mix Attempts, delete an unfamiliar lock, hand-edit a receipt, or start
downstream work before the required upstream checks pass. Use
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) before cleanup or retry.

## Dependency maintenance

Run maintenance from the clean source checkout in an institution-approved
context with permission to install dependencies. `pyproject.toml` and `uv.lock`
own Python requirements; `renv.lock` owns the R snapshot. Restore or update only
as an explicit operator action. A stale lock is
an error, not authority to relock. Workflow execution, validation, rendering,
and scheduler bootstraps never install or repair dependencies.

```bash
cd "$EMRYS_SOURCE_ROOT"
uv lock --check
uv sync --locked --no-default-groups --group workflow --check
```

For an institution runtime that lacks the locked R library, first select the
actual R 4.6.1 executable as `EMRYS_RSCRIPT`. Choose an operator-owned library
root outside the checkout; replace the example path below before running:

```bash
export EMRYS_RENV_RESTORE_ROOT=/absolute/path/to/operator-owned/library-root
RENV_PATHS_LIBRARY="$EMRYS_RENV_RESTORE_ROOT" \
  make r-restore RSCRIPT_BIN="$EMRYS_RSCRIPT"
```

This is an explicit package installation through `renv`, requires access to
the locked package sources and the system build dependencies, and never
authorizes modifying a shared institution library. Ask the institution to
provide those prerequisites, or use managed Doctor repair for a fresh managed
Project. When restoration succeeds, copy the exact `project library:` path
printed at the end into `EMRYS_RENV_LIBRARY`. It may be beneath the chosen root
in an R/platform-specific subdirectory. Check that exact library:

```bash
make r-check RSCRIPT_BIN="$EMRYS_RSCRIPT" RENV_LIBRARY="$EMRYS_RENV_LIBRARY"
cd "$EMRYS_PROJECT_ROOT"
```

Proceed to [runtime discovery](#institution-provided-runtime) only after this
read-only check succeeds. For existing admitted Runs, changes to runtime bytes
may invalidate reuse or recovery; preserve the previous environment and plan
maintenance with its owner before changing it.

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
