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
It writes no logs and identifies the executing installation independently of
the working directory and Git checkout.
Version flags cannot accompany a command.

## Create a Project for your own data

Use a **new Project**, leaving the completed synthetic exercise intact. Obtain
the following from the study's scientist/analyst before setup:

- Paired-end FASTQs and their source checksums; explicit sample IDs, conditions,
  library strandedness, and matched replicate strata. The built-in Analysis
  needs at least two strata with one control and one treatment sample each.
  Technical lanes are not automatically independent biological replicates.
- An uncompressed reference FASTA and matching GTF, with their source/release
  identities. EMRYS needs permission to create/check `.fai` and `.dict` sidecars
  beside the FASTA; arrange a writable study copy rather than modifying a
  shared reference owned by another team.
- Nonoverlapping regions to analyze, with contig names matching the reference;
  STAR index parameters appropriate to the reads/reference; and the Analysis
  thresholds and target substitution approved for the study. The example
  numbers in the configuration guide are not universal scientific defaults.
- A resource/allocation choice appropriate to the actual reads and reference.
  A successful tiny synthetic run is not a full-dataset capacity estimate.

EMRYS does not acquire public reads/references or decide experimental pairing.
Keep input files at their declared locations for the life of their Runs.

### Prepare the manifests

Write [tab-separated manifests](../../configs/README.md#sample-manifest) directly
for arbitrary FASTQ names, or use the helper below. `samples.example.tsv` is
a generic ingestion example, not a complete paired-CMH Project manifest.

Replace the four example library names, paths, and assignments with your study
values. The helper expects `_R1.fastq.gz`/`_R2.fastq.gz` suffixes; plain FASTQ and
`.fq` also work. Use known library strandedness instead of `unknown` when
available. The regions file must exist: tab-separated BED uses zero-based,
half-open coordinates; the plain region table uses one-based, inclusive
coordinates. See [partition format](../../configs/README.md#partition-manifest).

```bash
EMRYS_READS=/absolute/path/to/reads
EMRYS_REGIONS=/absolute/path/to/regions.bed
EMRYS_MANIFEST_ROOT=/absolute/durable/path/study-manifests
emrys init manifests --output-dir "$EMRYS_MANIFEST_ROOT" \
  --fastq "$EMRYS_READS/control_1_R1.fastq.gz" "$EMRYS_READS/control_1_R2.fastq.gz" \
          "$EMRYS_READS/treatment_1_R1.fastq.gz" "$EMRYS_READS/treatment_1_R2.fastq.gz" \
          "$EMRYS_READS/control_2_R1.fastq.gz" "$EMRYS_READS/control_2_R2.fastq.gz" \
          "$EMRYS_READS/treatment_2_R1.fastq.gz" "$EMRYS_READS/treatment_2_R2.fastq.gz" \
  --sample control_1 control pair_1 unknown \
  --sample treatment_1 treatment pair_1 unknown \
  --sample control_2 control pair_2 unknown \
  --sample treatment_2 treatment pair_2 unknown \
  --regions-file study "$EMRYS_REGIONS" --execute
```

The destination must be absent under an existing writable parent. This command
publishes `samples.tsv` and `partitions.tsv`; omit `--execute` for a preview
first. Review the resulting rows and assignments before creating the Project.

### Create and validate the Project

From the existing durable parent where the new `my-study` child should live:

```bash
cd /absolute/durable/path
emrys init my-study --site viking
```

Supply absolute manifest/FASTA/GTF paths, STAR parameters, exact condition
labels, target change (such as `A>G`), and study thresholds. Consult the
[field guide](../../configs/README.md#built-in-analysis-fields); Enter accepts a
suggestion that still needs scientific review. This command checks the plan
without writing. Repeat with the same answers to create it:

```bash
emrys init my-study --site viking --execute
export EMRYS_PROJECT_ROOT="$(pwd -P)/my-study"
cd "$EMRYS_PROJECT_ROOT"
export EMRYS_REFERENCE_FASTA=/absolute/path/to/reference.fa
emrys validate
```

Use the same FASTA path you supplied during initialization. For an optional
background cohort, supply `--background-condition CONDITION` to both init
invocations and include its samples in the manifest. If scripting setup, use
`emrys init --help` for the explicit field flags; all required answers must be
supplied outside a terminal.

After `Project validation: PASS`, run `emrys doctor --repair`, then `emrys run`
and inspect the completed Run from the head node. Each Project has its
own runtime inventory and qualification records. Compare the real-data outputs
with the study design, not the synthetic fixture's expected counts.

For named Analyses, processing reuse, alternate profiles, and larger synthetic
exercises, use the sections below. The optional
`production-like-v1` fixture has 100,000 pairs **per library** across four
libraries and a 5-Mb reference; select it with `--dataset-profile production-like-v1` on both
synthetic initialization commands in a new Project.

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

Inside a real Slurm allocation, use `emrys doctor --compute` for that diagnosis.
Ordinary head-node or non-Slurm diagnosis uses `emrys doctor` without the flag.

The first discovery previews without writing; execute only after every required
check passes. Success prints `Runtime inventory admitted.` and creates
`runtime/runtime.tsv`. Discovery never replaces an inventory, loads modules,
or installs software.

The inventory stores 12 selected paths in `check_id` and `target` columns.
Version requirements and probe arguments come from the installed EMRYS policy;
analysis-specific dependencies come from the selected analysis module. Doctor
and execution use those policies to check the same tools and packages.

The previous eight-column inventory format is retired. Before using a Project
with this version, preserve its old inventory outside `runtime/runtime.tsv`,
then repeat discovery and admission above. Discovery still refuses to overwrite
an existing inventory. Old Attempt inventories are retained as records and are
not accepted for execution by this version.

If Doctor finds the runtime ready but single-host storage unqualified:

```bash
emrys doctor --repair
```

Review the plan and answer `y` for the intended storage qualification. With a
ready runtime, this writes storage evidence and a maintenance log without
package installation or inventory changes. Continue after `EMRYS is ready.`
A failing institutional runtime needs institutional repair. For Slurm, return
to the head node and run the ordinary `emrys doctor --repair`; it coordinates
both storage phases. Advanced repair inside an allocation needs `--compute`
and subsequent head-node finalization, as described below.

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
then preview from the Project. This read-only preview can run on the head node:

```bash
emrys report
```

The command never prompts to write. Only when generation is admitted, run
`emrys report --execute`, then inspect again. Complete bundles are verified and
reused; partial or blocked bundles need [recovery](TROUBLESHOOTING.md#run-and-reporting-state).
Reporting does not overwrite arbitrary bundles, change scientific Results, or
create another scientific Attempt. Generation follows the Project's default
execution profile: Slurm placement submits it to a compute node, while direct
placement executes on the current host. Use `--profile NAME` to select another
existing profile; direct execution requires a permitted compute host.

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

Scientific computation runs through `emrys run` and `emrys resume`.
Specialist commands validate existing outputs, reconcile reference provenance
(`emrys reconcile reference-provenance`), or qualify workflow storage
(`emrys debug storage-qualification`). `emrys validate all-pass` checks one
owner-validation report because validator exit zero alone does not establish
semantic success.

The CSU dashboard is stale and frozen pending separate replacement work.
Use `emrys inspect` and exact Slurm accounting/streams for status and completion.

## Slurm setup and submission

Viking users select `--site viking` when creating either a synthetic or a
real-data Project. EMRYS writes the Project's default execution profile with
account `viking-users`, partition `long`, QoS `normal`, four CPUs, eight hours,
site-default memory and private temporary files beneath `/tmp`. These placement
settings come from the September 2026 site walkthrough; they are not a
full-dataset resource estimate. The retained EV/PUM1 profile describes a
separate six-library computational policy.

From the head node, prepare the Project and submit its Analysis:

```bash
emrys doctor --repair
emrys run
```

Doctor installs the managed tools on the head node, then submits compute-side
runtime and storage checks through Slurm and finishes the storage check on the
head node. It retains the existing qualification evidence. A successful repair
means these checks passed; it does not establish scientific completion.

Slurm runs the complete Analysis and its reports on one compute node. Normal
Run, resume and report execution use the Project's default profile. Inspecting
results and previewing reports remain local read-only operations. Keep the
checkout, Python environment, Project, runtime and inputs accessible at the same
physical paths on the head and compute nodes.

### Other placements and advanced setup

For another cluster, the site administrator supplies a Project-local profile
using [the example](../../configs/execution_profile.example.yaml). Account,
partition, QoS, CPU, memory, wall time, module setup and scratch must reflect the
actual site. Existing profile selection remains available through
`emrys run --profile NAME` and `emrys resume RUN --profile NAME`; omission uses
`runtime/profiles/default.yaml`. Profiles contain literal absolute paths, without
shell expansion, and must remain unchanged while a job is queued or running.

The batch wrapper starts with `PATH=/usr/bin:/bin`, loads only the declared
module roster and uses the admitted runtime's absolute paths. It creates and
removes its own temporary directory. Runtime repair is an explicit Doctor
operation; scientific execution does not install packages.

Advanced operators may run `emrys doctor --repair --compute` inside an actual
allocation. Return to the head node to complete preparation with
`emrys doctor --repair`. The separate compute and finalization commands remain
available for investigating storage failures; their exact contract lives with
[storage qualification](../../src/emrys/evidence/storage_inventory/README.md).
Do not alter scheduler variables to imitate an allocation or erase existing
qualification evidence to retry.

For detailed submission diagnostics, use `--log-level debug`. Normal operator
instructions use the default output level. Scheduler job success alone does
not establish valid Results; use `emrys inspect` and the retained reports.

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

Institutional R restoration below requires the installed EMRYS R guard and
permission to install packages. The [engineering guide](ENGINEERING_CONVENTIONS.md#dependencies-and-environments)
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
export EMRYS_RENV_RESTORE_ROOT=/absolute/path/to/operator-owned/r-environment
mkdir -p "$EMRYS_RENV_RESTORE_ROOT"
RENV_PROJECT="$EMRYS_RENV_RESTORE_ROOT" \
RENV_PATHS_LIBRARY="$EMRYS_RENV_RESTORE_ROOT/library" \
RENV_PATHS_CACHE="$EMRYS_RENV_RESTORE_ROOT/cache" \
  make r-restore RSCRIPT_BIN="$EMRYS_RSCRIPT"
```

This installs through `renv` and needs locked package sources and system build
dependencies. The explicit external project holds renv settings, locks, staging,
and downloaded sources; installed EMRYS supplies the pinned activation and lockfile.
Obtain dependencies from the institution, or use managed Doctor repair
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
