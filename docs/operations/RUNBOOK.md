# Runbook

Operational observations establish only the layer they directly check. Scheduler
state, files, logs, receipts, reports, and local validation do not by themselves
promote a Run, scientific, performance, or biological claim. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
owns exact semantics; this runbook owns operator procedures.

## Retain a submission before its Run exists

Run, resume, and report print an exact `Submission request:` directory after
approval. Retain it with the printed job and stream paths; a request can exist
before its Run. From the Project, `emrys inspect` lists retained requests,
including partial or malformed records, without querying Slurm or application
logs. `emrys inspect RUN` instead selects that Run.

Query one request by its printed directory name or absolute path:

```bash
emrys inspect --submission "submission-REPLACE_WITH_THE_EXACT_REQUEST_TOKEN"
```

This prints that request's recorded streams, scheduler observation, matching
application log, and any independently admitted Run/Attempt. Preserve
`UNKNOWN`, partial, and legacy observations.

An explicit Run selection also discovers its recorded application logs:

```bash
emrys inspect RUN --project "$EMRYS_PROJECT_ROOT" --verbose
emrys inspect RUN --project "$EMRYS_PROJECT_ROOT" --log-root /absolute/historical/log/root --watch
```

The Run search uses `--log-root`, then `EMRYS_LOG_ROOT`, then the Project's
`logs/application` directory. Supply an historical custom root explicitly. The
[submission and inspection contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#resume-inspection-results-and-reporting)
owns the exact admission, query, evidence, and recovery limits.

## Watch one fixed selection

The installed watch offers overview, detail, and dated evidence/log views. From
a Project, it selects the sole retained request or otherwise-unrepresented Run;
an associated request keeps supplying exact scheduler identity after its Run
appears. Ambiguity, including multiple requests for one Run, opens a picker:

```bash
emrys watch
```

Select a Run by name/ID or scheduler diagnostics by numeric ID/exact job name:

```bash
emrys watch international-jackrabbit
emrys watch 12345
emrys watch emrys-EXACT_REQUEST_TOKEN
```

`EMRYS_PROJECTS_ROOT` enables the same read-only picker outside a Project;
`--project` selects an exact Project from any directory.

For a submitted Project request selected explicitly, including before its Run
exists:

```bash
emrys inspect --project "$EMRYS_PROJECT_ROOT" --submission "submission-EXACT_TOKEN" --watch
```

Use `emrys inspect RUN --watch` for Run evidence and application/Task logs. If
one retained request identifies that Run, watch keeps it selected for scheduler
state and resource usage; multiple matching requests require an explicit
choice.

Watch also supports scheduler discovery and historical selection without
requiring a Project:

```bash
emrys inspect --watch --job-id
emrys inspect --watch --job-id 12345
emrys inspect --snapshot --job-id 12345 --log-dir /absolute/scheduler/logs
emrys inspect --snapshot --job-id 12345 --offline --out /absolute/scheduler/logs/emrys-EXACT_REQUEST_TOKEN-12345.out --err /absolute/scheduler/logs/emrys-EXACT_REQUEST_TOKEN-12345.err
```

`emrys inspect --watch --job-id` is the expert bounded current-user discovery
form. Ordinary no-argument `emrys watch` selects only admitted Project targets
and refuses to enumerate unrelated scheduler jobs when none exists. Explicit
command-line diagnostic selection precedes
`EMRYS_DASHBOARD_JOB_ID`/`EMRYS_DASHBOARD_LOG_DIR`. Offline mode needs an exact
ID plus both streams.

The resource panel labels active `sstat` values as a live sample and terminal
`sacct` values as final accounting. Either may be unavailable without erasing
the admitted root scheduler state; usage is diagnostic and does not establish
Run completion, recovery safety, or a wall-time improvement.

| Control | Behavior |
| --- | --- |
| `1` / `o`, `2` / `d`, Tab | Overview, details, or switch between them. |
| `3` / `v` | Dated Run evidence and selected diagnostic log. |
| `[` / `]` | Previous/next log; opens the evidence/log view. |
| Arrows / `j` / `k`, Page Up/Down, Home / `g` | Scroll or return to the top. |
| `G`, count + `j` / `k`, `/`, `n` / `N` | Follow the bottom, counted movement, and regex search in logs. |
| `r` | Read-only recheck of the fixed selection: refresh diagnostics, recheck association, and fully verify its Run evidence. |
| `q` | Quit and restore the terminal. |

The control strip shows the active view and selected log as `position/total`.
Cyan keys and labels are distinct from their values; green marks verified
success/following, yellow marks pending/warning/paused state, red marks failures,
and dim text is secondary metadata. Log styling recognizes literal Snakemake and
structured severity forms without rewriting retained text. `NO_COLOR`, redirected
output and dumb terminals remain fully labeled and plain.

Automatic diagnostic refresh defaults to 30 seconds; `--refresh` accepts at
least five seconds. Workflow streams retain full diagnostic history; other
tails retain at most 64 KiB/256 lines. `--snapshot`, redirection, or a
noninteractive terminal emits one snapshot. Use `--log-root` for a historical
application-log root. See the
[inspection contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#resume-inspection-results-and-reporting)
for admission and recovery semantics.

### Review CLI operations from watch

For an interactive view, opt in to the shortcuts for one exact selection:

```bash
emrys inspect RUN --project "$EMRYS_PROJECT_ROOT" --watch --actions
emrys inspect --submission REQUEST --project "$EMRYS_PROJECT_ROOT" --watch --actions
```

| Selection | Key | Operation after leaving watch |
| --- | --- | --- |
| Run | `p` | Ordinary resume plan and confirmation; decline to leave without starting work. |
| Run | `b` | Report preview; does not generate or submit reporting work. |
| Submission request | `s` | Stop preview for the exact retained request; does not cancel the job. |

Each handoff restores the terminal and freshly admits the exact selection.
Use the direct CLI to choose another profile or execute a report/stop plan.

## Stop one exact Slurm request

Use the exact retained request printed by Run, resume or report, with the
Project that submitted it. Preview first:

```bash
emrys stop --project "$EMRYS_PROJECT_ROOT" --submission "submission-EXACT_TOKEN"
```

Review the displayed identity and scheduler observation. Add `--execute` to
issue that stop request; retain its records if the result is uncertain. The
[stop contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)
owns the exact identity, mutation, and evidence rules.

Use the [quickstart](../../quickstart.md) for Viking installation, a first
synthetic Project and your own study. For other setup needs, start with
[a chosen release or commit](#install-a-chosen-release-or-commit) or
[a standalone compute host](#standalone-compute-host-with-a-managed-runtime).
This guide also covers institutional runtimes, advanced operation, and Slurm.
The [configuration guide](../../configs/README.md) explains Project inputs and
execution settings; [Troubleshooting](TROUBLESHOOTING.md) covers recovery.

Commands use Bash. If you already have an installation and Project, set
`EMRYS_SOURCE_ROOT` and `EMRYS_PROJECT_ROOT` to their full physical paths in a
new terminal, then activate the installed command and enter the Project:

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

## Install a chosen release or commit

Use this procedure when a study or team requires a specific EMRYS revision.
On the intended host, first install uv and Pixi using the installer block in
[quickstart step 1](../../quickstart.md#1-install-emrys), or use your institution's
supported installations. Keep the required versions and dependency locks;
managed repair requires Pixi `>=0.75.0,<0.76`. Then use the commands below in
place of the quickstart's clone/install block.

Replace `EMRYS_REVISION` with the chosen release tag or full commit ID and
replace the source-parent path. The parent must exist and its `EMRYS` child
must be absent. Use a fresh checkout rather than change one used by an
existing Project.

```bash
cd "/absolute/path/to/source-parent"
EMRYS_REVISION='REPLACE_WITH_FULL_COMMIT_ID_OR_TAG'
git clone https://github.com/lab-cats/EMRYS.git
cd EMRYS
git checkout --detach "$EMRYS_REVISION"
export EMRYS_SOURCE_ROOT="$(pwd -P)"
git rev-parse HEAD
uv sync --locked --no-default-groups --group workflow --python 3.14
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
emrys --version
```

Record the printed full commit ID, including when you selected a tag. Leave
the checkout and installed environment unchanged for the Project's Runs.
Choosing a revision identifies the installation; it does not establish that
it is qualified for your institution or scientific study. Viking users can
continue with the [optional smoke test](../../quickstart.md#optional-smoke-test).

## Standalone compute host with a managed runtime

Use this route on an approved non-Slurm compute host, never on a cluster login
node. Managed setup requires x86-64 Linux, kernel 4.18 or newer and glibc 2.28
or newer. The default workflow uses process-visible capacity; its retained
concurrent-stage allowances require at least 12 CPUs and 240 GiB.
Confirm that the host's memory, disk space and permitted running time suit the study;
the tiny synthetic exercise is not a full-study capacity estimate.

Use Bash with Git and curl available, permission and network access for package
downloads, and a writable durable checkout. Install the tools and locked command
with [the procedure above](#install-a-chosen-release-or-commit). Keep that
environment active. Enter the repository-supplied Projects home, then use an
absent child for the supplied study:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects"
export EMRYS_PROJECTS_ROOT="$(pwd -P)"
export EMRYS_PROJECT_ROOT="${EMRYS_PROJECTS_ROOT:?Choose a Projects home first}/emrys-smoke"
emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT" --execute
cd "$EMRYS_PROJECT_ROOT"
emrys validate
```

Without `--site`, initialization writes a direct execution profile: computation
runs on this host. Continue after `Project validation: PASS`; the supplied
inputs and configuration need no edits. Preserve a partial directory if
creation fails and use a new absent destination.

Prepare the Project's scientific runtime and storage:

```bash
emrys doctor --repair
```

Review the displayed repair-and-verification or verification plan and answer
`y` to approve its listed actions.
Doctor manages Project-owned native tools and R packages and retains a maintenance
log; Python dependencies remain the package manager's responsibility. The
ordinary command is correct on this non-Slurm host; `--compute` is for advanced
diagnosis inside a real Slurm allocation. Continue only after `EMRYS is ready.`
For a failure, retain the printed log and follow
[Project and runtime checks](TROUBLESHOOTING.md#project-and-runtime-checks).

Run the supplied Analysis and inspect it when the command finishes:

```bash
emrys run
emrys inspect
```

Review Analysis `primary`, its paths and resources, then answer `y` at
`Execute this plan? [y/N]`. Keep the terminal alive until execution finishes;
successful computation generates both reports automatically. Follow
[Inspect and open reports](#inspect-and-open-reports) to check completion,
view the outputs or finish reporting without repeating completed computation.

For your own study, use the quickstart's
[input and manifest guidance](../../quickstart.md#2-gather-the-study-inputs-and-scientific-choices).
Create a new Project on this host using its Project-creation commands with
`--site viking` omitted, then return to Doctor and Run above after validation.
Confirm resources for the actual data using the
[execution settings](../../configs/README.md#execution-profile), and retain the
synthetic Project separately. Use [recovery guidance](TROUBLESHOOTING.md#run-and-reporting-state)
for incomplete Runs rather than deleting their files.

## Create a Project for your own data

Follow the [Quickstart's real-data path](../../quickstart.md#3-create-the-project)
for the complete Viking sequence: prepare study inputs, create the Project,
run Doctor, submit the study, inspect it and open the reports.
The ordinary `emrys init NAME` creates beneath the current directory, so first
enter the repository-supplied `Projects/` parent. Synthetic `--output-dir` may
select an external absolute destination when an advanced workflow requires it.
These routes share the same absent-child and canonical-parent checks; neither
moves or adopts an existing Project. Use `--project /absolute/Project/project.yaml`
with Project-aware commands when working from another directory.

Interactive named initialization discovers recognized FASTQ pairs in one
directory, asks for their biological assignments and the study regions, and
publishes `samples.tsv` and `partitions.tsv` inside the Project. Its preview
checks paths and scientific structure without reading FASTQ contents, derives an
omitted `genomeSAindexNbases` from the reference, and labels omitted
`sjdbOverhang` and `genomeChrBinNbits` values as automatic at creation. The
printed creation command carries every explicit answer while preserving those
omissions. Creation hashes each FASTQ's stored bytes once while validating every
plain or gzip-decoded record, then freezes the maximum read length minus one and
the reference/read-length chromosome-bin setting. The reference summary is bound
to its device, inode, size, nanosecond modification time and nanosecond change
time until full admission; changed reference or FASTQ identity stops publication.
Explicit `--sjdb-overhang`, `--genome-sa-index-nbases`, and
`--genome-chr-bin-nbits` values remain advanced overrides and are reported as
such. The [configuration guide](../../configs/README.md#projectyaml) owns the
exact derivation and legacy-default rules.
Existing advanced manifests may be supplied together with `--sample-manifest`
and `--partition-manifest`; EMRYS copies normalized manifest content into the
new Project. Existing Projects remain supported at their current paths.

For studies with additional input requirements:

- For arbitrary FASTQ names, prepare the [sample manifest](../../configs/README.md#sample-manifest)
  and [partition manifest](../../configs/README.md#partition-manifest) directly,
  then supply both advanced inputs during initialization.
  `samples.example.tsv` demonstrates ingestion fields; it is not a complete
  paired-CMH Project manifest.
- For a background cohort, include its samples in the manifest and pass
  `--background-condition CONDITION` when creating the Project. The condition
  must match those sample rows; the [Analysis field guide](../../configs/README.md#built-in-analysis-fields)
  explains the background filter and other scientific settings.
- For noninteractive setup, use the explicit field flags shown by
  `emrys init --help`. Supply every required answer when no terminal is available.

For a larger software exercise, `production-like-v1` contains 100,000 pairs
per library across four libraries and a 5-Mb reference. Create a new synthetic
Project with `--dataset-profile production-like-v1`; retain `--site viking`
for Viking placement. A successful synthetic exercise does not establish
capacity for a full study.

## Institution-provided runtime

Use this route when the institution supplies the exact versions in
[`runtime_policy.tsv`](../../src/emrys/resources/runtime/runtime_policy.tsv):
STAR 2.7.11b, Samtools 1.19.2, GATK 4.6.1.0, Picard 3.1.1, Bcftools 1.21,
RSeQC 5.0.4, Java 17+, and R 4.6.1 with the locked R packages. For managed
installation, use [Viking's Doctor procedure](../../quickstart.md#5-prepare-the-scientific-tools-and-storage)
or the [standalone procedure](#standalone-compute-host-with-a-managed-runtime).

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
emrys doctor
```

Inside a real Slurm allocation, use `emrys doctor --compute` for that diagnosis.
Ordinary head-node or non-Slurm diagnosis uses `emrys doctor` without the flag.

Discovery previews first. In a terminal, answer `y` only after every required
check passes; Enter or `n` leaves the Project unchanged. The confirmed command
reuses its in-memory inspection and performs focused freshness checks before
publication. Noninteractive automation uses `emrys runtime discover --execute`.
Success prints `Runtime inventory admitted.` and creates `runtime/runtime.tsv`.
Discovery never replaces an inventory, loads modules, or installs software.

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
emrys run
emrys inspect
```

For several Analyses, add `--analysis NAME` to `doctor` and `run`. Choose the
execution profile for the intended host; see the
[profile selection rules](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
and [configuration guide](../../configs/README.md).

A direct Run asks `Execute this plan? [y/N]`: `y` executes and Enter declines.
Its normal plan shows the Run name and location, pending/reusable work, and
reporting disposition. A Slurm submission normally adds only placement and the
allocation request. Add `--verbose` for profile limits, identities, commands,
Task detail, and the evidence-boundary explanation. Preview without writing
with `emrys run </dev/null`;
automation executes with `emrys run --execute`. Full Runs generate reports
unless `--no-report` is supplied. Use the [Slurm route](#slurm-setup-and-submission)
for cluster submission.

`emrys inspect` reads the sole Run or offers a terminal picker. Select one by
two-word name, full ID, or unique ID prefix. The normal view shows admission,
outcome, blockers, recovery, next action, and verified reports; `--verbose`
adds identities, milestones, timing, application associations, reporting
transactions, Task records, authority hashes, receipts, and commands.
For failed or interrupted Runs, follow [resume and recovery](TROUBLESHOOTING.md#run-and-reporting-state).

Read printed blockers before choosing an action. `emrys watch` uses the same
selection and inspection authority. The
[inspection contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#resume-inspection-results-and-reporting)
defines its Task, submission, and completion states.

### Inspect and open reports

A successful full Run shows `Run admission: valid`, `Attempt outcome: succeeded`,
`Scientific Results: complete`, and `Reporting admission: complete`. Open the printed
`Scientific report` for candidate results and `Evidence report` for execution
and provenance. Linked machine-readable tables contain the complete data.

For the built-in Analysis, copy the complete Run `results/` directory, preserving
its structure so HTML and table links work. Use your institution's file-transfer
application or the [terminal procedure below](#retrieve-reports-from-a-terminal).
A collaborator Analysis may have different transfer requirements.

When scientific Results are complete but reporting was skipped, inspect first,
then preview from the Project. This read-only preview can run on the head node:

```bash
emrys report
```

The command never prompts to write. Only when generation is admitted, run
`emrys report --execute`, then inspect again. Complete bundles are verified and
reused; partial or blocked bundles need [recovery](TROUBLESHOOTING.md#run-and-reporting-state).
Preserve blocked or partial records and follow the printed supported action.

Reporting does not overwrite arbitrary bundles, change scientific Results, or
create another scientific Attempt. Generation follows the Project's default
execution profile: Slurm placement submits it to a compute node, while direct
placement executes on the current host. Use `--profile NAME` to select another
existing profile; direct execution requires a permitted compute host.

### Retrieve reports from a terminal

1. On the cluster head node, select the exact completed Run from its Project:

   ```bash
   emrys inspect RUN --verbose
   ```

   Replace `RUN` with its name, full ID, or unique ID prefix. Continue after
   inspection shows valid Run admission, a succeeded Attempt, complete Scientific
   Results, and complete Reporting. Copy the printed report paths; their common
   `results/` ancestor is the directory to transfer. Do not choose a directory
   by modification time or copy a bundle still being published.

2. Open a terminal **on your own computer**. The example uses SSH and rsync 3
   on both computers; use your institution's transfer application if unavailable.
   Set the approved login/transfer host and the exact remote results path, then
   copy into a new local directory:

   ```bash
   report_host='YOUR_LOGIN@YOUR_TRANSFER_HOST'
   report_results='/absolute/Project/runs/RUN_ID/results'
   report_copy=$(mktemp -d "$HOME/emrys-report.XXXXXX")
   rsync --protect-args -rlt -- "$report_host:$report_results/" \
     "${report_copy:?Create the local report directory first}/"
   ```

   Replace both example values. The trailing slash copies the directory's
   contents without flattening its folders. The files may contain study data;
   use an approved computer and destination. If transfer fails, keep the paths
   and error; rerun the same transfer after resolving the cause.

3. Compare file contents with the original without changing either copy:

   ```bash
   rsync --protect-args -rlcni -- "$report_host:$report_results/" \
     "${report_copy:?Create the local report directory first}/"
   printf 'Local results: %s\n' "$report_copy"
   ```

   A successful comparison prints no file changes. Any listed missing/changed
   file or error means the copy is not yet verified; resolve it and compare
   again. This uses rsync's [checksum and dry-run options](https://download.samba.org/pub/rsync/rsync.1).
   It checks transfer consistency, not Run integrity or scientific validity.

4. In that local directory, open
   `reports/RUN_ID/RUN_ID.scientific_report.html` and
   `reports/RUN_ID/RUN_ID.evidence_report.html` in your browser. Replace `RUN_ID`
   with the inspected full ID. Follow the links between reports and to candidate
   tables; retain the complete copied tree. No web server or tunnel is needed.

Keep the original Project, complete Run, inputs, runtime, and logs available for
inspection and recovery. Record visual review separately, including Run identity,
report names, and any broken links or unreadable figures.

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

## Slurm setup and submission

Viking users select `--site viking` when creating a Project. Existing Projects
can select the current site defaults through
[named profile creation](../../configs/README.md#create-a-named-profile-without-writing-yaml).

From the head node, prepare the Project and submit its Analysis:

```bash
emrys doctor --repair
emrys run
```

Doctor installs the managed tools on the head node, submits compute-side
runtime and storage checks through Slurm, then finishes storage qualification
on the head node. Read the
[qualification scope](../../src/emrys/evidence/runtime_availability/README.md#what-qualification-establishes)
for the exact checks and limits.

Slurm runs the complete Analysis and its reports on one compute node. Normal
Run, resume and report execution use the Project's default profile. Inspecting
results and previewing reports remain local read-only operations. Keep the
checkout, Python environment, Project, runtime and inputs accessible at the same
physical paths on the head and compute nodes.

### Other placements and advanced setup

For another cluster, the site administrator supplies a Project-local profile
using [the example and field guidance](../../configs/README.md#execution-profile). Account,
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

For detailed submission diagnostics, use `--verbose`; use `emrys inspect` for
the Run result.

## Inspecting a Slurm Run

Use the exact submitted job ID and stream paths:

```bash
squeue -j JOB_ID
sacct -X -j JOB_ID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -n +1 -F /exact/OUT /exact/ERR
```

Replace the placeholders above. Control-C stops `tail`, not the allocation.
Use `emrys inspect` for the Run result and follow
[Troubleshooting](TROUBLESHOOTING.md#storage-and-slurm) before retry or cleanup.

## Reuse prepared managed tools

Use this path after creating a new Project and before Doctor installs tools for
it. Select a prepared source Project owned by the same UID. Its managed tool
paths and R package trees must be inside one of its canonical managed runtime
generations and visible from the new Project's intended nodes. Keep both Project
locations stable. An existing runtime inventory is preserved unless `--replace`
explicitly selects a newer generation from the same source Project.

```bash
emrys runtime discover --project /absolute/borrower/project.yaml --from-project /absolute/donor/project.yaml
```

This previews first. Add `--verbose` to review every observed tool check and the
selected source seal; the normal view shows readiness and the no-write/admission
outcome. Answer `y` to create the new Project's inventory only after the source
generation and focused freshness checks succeed. The command installs nothing;
`--execute` is the noninteractive equivalent. Then run:

```bash
emrys doctor --project /absolute/borrower/project.yaml --repair
```

Doctor still qualifies the new Project, storage and selected placement;
inspect its plan before confirming. Continue only after borrower readiness
passes. Keep both Projects and every selected runtime generation available; the
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md#sealed-managed-runtime-reuse)
defines the seal, replacement, and qualification boundaries.

Doctor never repairs a shared generation in place. If the source Project's
selected tools fail, `emrys doctor --repair` prepares and verifies a new
generation, then moves only that Project's current selection. Other Projects
continue to name the old generation and must explicitly select the replacement:

```bash
emrys runtime discover --project /absolute/dependent/project.yaml --from-project /absolute/source/project.yaml --replace
```

Review the replacement and answer `y`; noninteractive automation adds
`--execute` to that command. Preserve previous generations and any partial or
locked publication for [recovery](TROUBLESHOOTING.md#project-and-runtime-checks).

## Dependency maintenance

### Doctor status and timing

Doctor's plan says **repair and verification** when package-manager work is
needed and **verification** when the selected runtime already passes. The
`Runtime work` line distinguishes a verified runtime, a missing managed
inventory, and tools selected by a retained inventory. A missing inventory
after interruption does not prove that packages need reinstalling. Pixi and
renv record actual package reuse and changes in `package-output.log` beside
the maintenance JSONL; see [installation logs](TROUBLESHOOTING.md#watching-doctors-installation-log).

| Status | Meaning |
| --- | --- |
| Runtime `NOT PREPARED` | The default runtime inventory has not been created; review proposed setup actions. |
| Runtime `CHECKS FAILED` | The selected runtime failed required checks; retain named diagnostics. |
| Storage `NOT QUALIFIED` | Required storage proof is unavailable or invalid; read the observed problem. |
| Execution `NOT ADMITTED` | The selected execution profile cannot be used; follow its diagnostic. |

Declining the plan with Enter or `n` makes no repair. After an error, retain the
diagnostics and selected runtime rather than clearing installation state.

Doctor prints full invocation elapsed time and exit outcome; add `--verbose` for
phase times and transcript paths. Allow for downloads, compilation, and queue
waits; use the named phase and retained diagnostics rather than elapsed time
alone. The
[Doctor contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)
owns timing and admission semantics.

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
