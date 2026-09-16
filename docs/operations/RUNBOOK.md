# Runbook

## Retain a submission before its Run exists

Run, resume, and report print an exact `Submission request:` directory after
approval. Keep that directory along with the printed job and stream paths.
`request.json` records the command, Project, selected profile binding, and
application-log location; `sbatch.stdout` and `sbatch.stderr` preserve the raw
scheduler response. These records can exist while no Run has been created.
New submissions use request-specific scheduler stream names. Preserve the
complete printed paths, including the request token; the job number alone can
be reused and does not identify those logs. Existing v1 records remain readable.

From the Project, run `emrys inspect` to list every retained request before
selecting a Run. The roster prints each exact directory, recorded command/time,
requested Run, application-log root, response job/cluster, and a bounded stderr
excerpt when readable. `partial`, `malformed`, or `unconfirmed` records remain
visible. An explicit `emrys inspect RUN` selects that Run directly.

`Runs: none found at inspection time` is a successful read-only observation.
It does not establish rejection, startup failure, or absence of a queued job.
A recorded job ID is historical response data; this roster does not query the
scheduler or associate that request with a Run. An unavailable log directory
is an inspection error, not an empty roster.

To query one request, pass its exact printed directory name or absolute path:

```bash
emrys inspect --submission "submission-REPLACE_WITH_THE_EXACT_REQUEST_TOKEN"
```

This selects a submission instead of a Run. It prints the recorded scheduler
stream paths and queries only that request: one `squeue` call and, only after
a successful empty queue reply, at most one `sacct` call. Each has a ten-second
timeout. A v2 request requires an exact job ID, current numeric UID, cluster
and both request-specific stream paths; v3 also checks the token-specific job
name. The output reports state and queue
reason or accounting exit status when admitted. Unsupported fields, missing
proof, duplicate records or query failure produce `UNKNOWN`. Legacy v1 or
incomplete request records stay unknown without scheduler calls.

Selected inspection also searches the request's retained application-log root
and command scope for one exact matching log. It shows that log and its snapshot
digest, any recorded preparation or reporting start, and an admitted Run/Attempt
when their retained contracts agree with the request. If admission fails, a
recorded candidate stays distinct from an admitted Run. Missing, changing,
ambiguous or oversized evidence stays unknown; it never selects the newest log.
The printed Run-inspection command checks the broader workflow evidence.

An explicit Run selection also discovers its recorded application logs:

```bash
emrys inspect RUN --project "$EMRYS_PROJECT_ROOT" --detail verbose
emrys inspect RUN --project "$EMRYS_PROJECT_ROOT" --log-root /absolute/historical/log/root --watch
```

The search uses `--log-root`, then `EMRYS_LOG_ROOT`, then the selected Project's
`logs/application` directory. Historical custom roots are not retained in Run
contracts; supply the root used for those invocations. One search covers new-Run
preparation and that exact Run's resume/report scope, preserving all admitted
historical matches. A reporting-only log names a Run, not a scientific Attempt.
Missing, malformed or bounded-out evidence leaves the scan unknown; zero matches
does not mean no logs exist elsewhere. The selector creates no logs and cannot
override a selected submission's frozen root. It requires an explicit Run.

The ordinary roster makes no scheduler calls or application-log scans. These
observations do not establish workflow entry, current progress, Run completion,
native process absence or recovery eligibility. They do not authorize
cancellation or lock removal.

An empty or malformed response does not prove that submission was rejected.
If acceptance is uncertain or the client was interrupted, resolve the exact
request with the scheduler and its logs before submitting again. Do not choose
the most recently modified directory as the intended request. Retain every
partial request; its presence alone is neither completion evidence nor recovery
authority.

## Watch one fixed selection

The dashboard offers the legacy overview and detail screens plus verified
Run evidence and selected logs. From a Project, the ordinary command selects
the sole retained submission before its Run exists, or the sole Run afterward:

```bash
emrys watch
```

Several plausible selections open a terminal picker. Noninteractive use must
provide an exact selector; EMRYS never selects the newest Run or request. A Run
name or ID uses Project evidence. A numeric ID or exact scheduler name selects
scheduler diagnostics:

```bash
emrys watch international-jackrabbit
emrys watch 12345
emrys watch emrys-local-pilot-EXACT_REQUEST_TOKEN
```

When `EMRYS_PROJECTS_ROOT` names the canonical Projects home, `emrys watch`
can be started from another directory. It scans only immediate Project children,
selects one available Run, or opens the same picker. This is read-only discovery,
not a registry or current/latest marker. An exact `--project` also works from
any directory.

For a submitted Project request selected explicitly, including before its Run
exists:

```bash
emrys inspect --project "$EMRYS_PROJECT_ROOT" --submission "submission-EXACT_TOKEN" --watch
```

Use `emrys inspect RUN --watch` for a Run's evidence and application/Task logs.
Its recorded job number does not establish current scheduler identity; select
its retained request for scheduler observations and the workflow trace.

The dashboard also reproduces standalone scheduler discovery and historical
selection without requiring a Project:

```bash
emrys inspect --watch --job-id
emrys inspect --watch --job-id 12345
emrys inspect --snapshot --job-id 12345 --log-dir /absolute/scheduler/logs
emrys inspect --snapshot --job-id 12345 --offline --out /absolute/scheduler/logs/emrys-local-pilot-12345.out --err /absolute/scheduler/logs/emrys-local-pilot-12345.err
```

Without a current Project, declared Projects home, or explicit selector, plain
`emrys watch` and `emrys inspect --watch` discover
a current-user EMRYS job. Discovery checks live jobs and bounded recent
accounting; it never scans storage for a newest log. Explicit IDs never fall
back to another job. `EMRYS_DASHBOARD_JOB_ID` and `EMRYS_DASHBOARD_LOG_DIR` are
fallbacks for scheduler selection; command-line values take precedence.
Offline requires an exact ID and both owned regular streams and makes no
scheduler queries. Raw scheduler selection permits no operational actions and
never admits a Project or Run from text printed in a log.

| Control | Behavior |
| --- | --- |
| `1` / `o`, `2` / `d`, Tab | Overview, details, or switch between them. |
| `3` / `v` | Dated Run evidence and selected diagnostic log. |
| `[` / `]` | Previous/next log; opens the evidence/log view. |
| Arrows / `j` / `k`, Page Up/Down, Home / `g` | Scroll or return to the top. |
| `r` | Read-only recheck of the fixed selection: refresh diagnostics, recheck association, and fully verify its Run evidence. |
| `q` | Quit and restore the terminal. |

Overview/details preserve pipeline progress, stage explanations and resources,
sample lanes and timings, peer comparisons, recent activity, errors, scheduler
placement and batch usage. Counts come from the reported invocation; unknown
counts stay unknown. Logs describe observed workflow activity and cannot prove
scientific completion. Resource maxima are per-task batch-step observations,
not total job I/O or whole-process memory. Read their observation dates.
When admitted Run evidence establishes completed Results, its verified Task
counts replace stale diagnostic stage counts and the view announces completion.
Scheduler completion and log text alone never produce that announcement.

Automatic refresh checks scheduler diagnostics and stream updates every 30
seconds; `--refresh SECONDS` accepts intervals of at least five seconds. A
terminal scheduler observation stays dated until `r` requests another query.
Full Run verification runs initially and on `r`, and can read substantial
scientific data. Screen painting performs no reads. Timers cannot refresh the
authority of dated Run/Task/reporting evidence or infer recovery eligibility.
The selected request's historical Attempt stays distinct from the Run's latest
Attempt. Reconnecting to the same selection reconstructs its full workflow
trace. The dashboard never switches to another job or a guessed latest log.

Workflow stdout/stderr use the shared full-history reader; other selected tails
retain at most 64 KiB and 256 lines. Missing, changed, truncated or replaced
streams are identified, previous generations are cleared, and terminal controls
are sanitized. A stalled read preserves its earlier date and cannot prevent
quitting after the view opens. Initial selection remains synchronous. Memory
for the parsed workflow trace grows with retained diagnostic history.

Both interactive entry points capture and ignore mouse reports; use the
documented keyboard controls to navigate. A tmux binding can instead translate
wheel movement into arrow keys before EMRYS receives it. EMRYS cannot distinguish
those translated keys from physical arrow-key input; adjust that tmux binding if
wheel movement still scrolls. Log colors distinguish literal severity and common
workflow prefixes without hiding or reinterpreting lines; `NO_COLOR` makes the
same text plain.

An explicit Run's `r` refresh searches its selected application-log root again
and removes associations no longer admitted. Independent Task streams remain
available. Expected Task paths require an admitted start; they prove neither
file existence nor worker liveness. Static verbose/debug inspection lists the
same exact paths. Use `--log-root` to select a historical custom application root.

`--snapshot`, redirected output, or a noninteractive terminal produces one
plain snapshot. `NO_COLOR` disables optional status colors. Ordinary watch
creates no operational action, log or persistent state. The original standalone
entry point remains supported until institutional validation and coordinated
retirement are complete.

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

Each command freshly checks its selection; dated watch observations do not
authorize recovery or cancellation. Run handoffs use the ordinary default
profile. Use the corresponding CLI directly to choose another profile or to
execute a report/stop plan. Noninteractive action mode is refused.

The terminal is restored before the CLI handler runs. A read already in
progress may finish in the background, but its result is discarded. The command
returns that handler's result and does not reopen watch. Slurm resume follows the
existing submission preview: scientific resume admission happens on compute,
so a concurrent resume can make an allocation unnecessary without bypassing
recovery checks. A request handoff never selects an associated historical Run.

## Stop one exact Slurm request

Use the exact retained request printed by Run, resume or report, with the
Project that submitted it. Preview first:

```bash
emrys stop --project "$EMRYS_PROJECT_ROOT" --submission "submission-EXACT_TOKEN"
```

Review the Project, request, numeric owner, cluster, root job ID, token-specific
job name and current scheduler observation. Add `--execute` to issue the
displayed stop request. Preview creates no log or cancellation records.
Only complete v3 requests are eligible; older records remain inspectable.
EMRYS requires a confirmed `scancel` release of at least 23.11.6 so the
controller applies owner, name and job-ID filters together. An unsupported
client or uncertain target refuses before cancellation.

Execution retains a synchronized intent and raw `scancel.stdout`/`scancel.stderr`
beside the printed maintenance log. It rechecks the request, exact scheduler
identity and client before issuing one whole-job cancellation, then observes
the scheduler again. There is no retry or fallback to cancellation by job ID
alone. A timeout or interrupted client can leave the request outcome uncertain;
retain the printed records and inspect that exact submission before acting again.

A processed cancellation request is not proof that every native process stopped.
A matching terminal scheduler observation is still separate from EMRYS recovery
eligibility. Inspect the associated Run and use its supported resume action only
when its retained evidence admits recovery. Missing terminal records, ambiguous
locks and partial outputs remain preserved; stop never removes or repairs them.

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
continue at [quickstart step 2](../../quickstart.md#2-create-the-supplied-study).

## Standalone compute host with a managed runtime

Use this route on an approved non-Slurm compute host, never on a cluster login
node. Managed setup requires x86-64 Linux, kernel 4.18 or newer and glibc 2.28
or newer. The default profile needs at least 12 visible CPUs and 512 GiB.
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
[input and manifest guidance](../../quickstart.md#gather-the-study-inputs-and-scientific-choices).
Create a new Project on this host using its Project-creation commands with
`--site viking` omitted, then return to Doctor and Run above after validation.
Confirm resources for the actual data using the
[execution settings](../../configs/README.md#execution-profile), and retain the
synthetic Project separately. Use [recovery guidance](TROUBLESHOOTING.md#run-and-reporting-state)
for incomplete Runs rather than deleting their files.

## Create a Project for your own data

Follow the [quickstart's own-data continuation](../../quickstart.md#7-create-a-project-for-your-own-data)
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
checks paths and scientific structure without hashing FASTQ contents. The
printed creation command carries every answer; creation hashes each FASTQ once
and rejects an input whose filesystem identity changes through publication.
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
installation, use [Viking's Doctor procedure](../../quickstart.md#3-prepare-the-scientific-tools)
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
assumes latest. `--detail verbose` adds Run/Attempt identities and admitted
terminal Task records with their original Attempt, recorded outcome, and exact
stdout/stderr paths. Failed retries remain visible in Attempt-chain order per
Task. Recorded success alone does not establish verified scientific completion.
Missing, changed or malformed log evidence stays blocked; preserve it for
diagnosis. `--detail debug` also adds authority hashes, receipts and task commands.
Planning, execution, and Doctor instead use `--log-level verbose` or `debug`.
For failed or interrupted Runs, follow [resume and recovery](TROUBLESHOOTING.md#run-and-reporting-state).

The **Scientific task observations** count only admitted evidence. `Started;
completion unverified` records a start, not proof that its worker still runs.
`No admitted start` may reflect absent or invalid records. Read printed blockers
before choosing an action; neither count overrides the four completion lines
or inspection's recovery decision.

`emrys watch` uses the same Run picker and inspection authority. A successful
Slurm submission is labelled **submitted** and returns before completion;
`watch` and `inspect` announce completion only after current Run evidence admits
the successful Attempt, complete Results, and applicable reporting state.

Selected submission inspection also prints the retained scheduler name for new
v3 requests and requires that exact name in scheduler metadata. Older requests
remain readable with their original evidence limits. A matching name or a
terminal scheduler state alone does not authorize recovery or prove completion.

### Inspect and open reports

A successful full Run shows `Run admission: valid`, `Attempt outcome: succeeded`,
`Scientific Results: complete`, and `Reporting admission: complete`. Open the printed
`Scientific report` for candidate results and `Evidence report` for execution
and provenance. Linked machine-readable tables contain the complete data;
reports do not establish biological conclusions or validate editing sites.

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
The normal inspection table shows `No admitted start`, `Started; completion
unverified`, or `Verified complete` for each reporting transaction. A start
without completion can reflect work in progress or an interrupted publication;
it does not establish that a reporter is alive. Preserve the records and follow
the printed supported action. Do not delete partial files or rerun science to
make a reporting blocker disappear.

Reporting does not overwrite arbitrary bundles, change scientific Results, or
create another scientific Attempt. Generation follows the Project's default
execution profile: Slurm placement submits it to a compute node, while direct
placement executes on the current host. Use `--profile NAME` to select another
existing profile; direct execution requires a permitted compute host.

### Retrieve reports from a terminal

1. On the cluster head node, select the exact completed Run from its Project:

   ```bash
   emrys inspect RUN --detail debug
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
inspection and recovery. The copied reports retain those original provenance
paths; the results copy is not a relocated executable Project. Record visual
review separately, including Run identity, report names, and any broken links
or unreadable figures. Copying and opening the files does not complete visual
acceptance or biological review.

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

The installed dashboard shares the legacy selection, scheduler and diagnostic
presentation owners. The original CSU entry point remains supported until
institutional validation and coordinated retirement. Shared observation checks
numeric ownership, exact root IDs, duplicate accounting records and selected
stream paths; uncertainty appears as `UNKNOWN`. Log interpretation does not
replace Run inspection or establish which retained request owns a reused job ID.
Its existing `--offline` mode requires an explicit job ID and both stream paths.
Selection, snapshots and interactive refresh make no Slurm queries; scheduler
state stays `UNKNOWN` while the same sanitized diagnostic streams remain usable.

## Slurm setup and submission

Viking users select `--site viking` when creating either a synthetic or a
real-data Project. EMRYS writes the Project's default execution profile with
account `viking-users`, partition `long`, QoS `normal`, 256 CPUs, 12 hours,
exclusive placement, site-default memory and private temporary files beneath
`/tmp`. Packaged resources restore the historical six-library EV/PUM1 policy:
12 workflow cores, 512 GiB and the retained stage-specific allowances. Both
synthetic and real-data initialization select these defaults automatically.
Existing Projects can select them through
[named profile creation](../../configs/README.md#create-a-named-profile-without-writing-yaml).

From the head node, prepare the Project and submit its Analysis:

```bash
emrys doctor --repair
emrys run
```

Doctor installs the managed tools on the head node, then submits compute-side
runtime and storage checks through Slurm and finishes the storage check on the
head node. It retains the existing qualification evidence. A successful repair
means these checks passed; it does not establish scientific completion.

Qualification covers the selected inventory's exact tools, not every tool
installed on the node. A different system default is not itself a reason to
cancel a healthy job that is using the admitted targets. Read the
[qualification scope](../../src/emrys/evidence/runtime_availability/README.md#what-qualification-establishes)
for the checks at each boundary and their limits. Slurm may choose another
eligible node unless the profile requests a pin; that node still must pass
runtime, allocation, and storage admission. Single-host direct storage evidence
does not replace shared-storage qualification.

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

Review the observed tools and printed seal path. This previews without writing.
The next command installs nothing and creates the new Project's inventory only
after the source generation and fresh checks succeed:

```bash
emrys runtime discover --project /absolute/borrower/project.yaml --from-project /absolute/donor/project.yaml --execute
emrys doctor --project /absolute/borrower/project.yaml --repair
```

Doctor still qualifies the new Project, storage and selected placement;
inspect its plan before confirming. Reuse does not copy storage receipts or
qualify every eligible node. Python/EMRYS and Analysis dependencies retain
their independent requirements. Continue only after borrower readiness passes.

Keep every selected seal and managed generation with its dependent Runs. A seal
covers fixed executable/jar bytes and required R package trees; it does not
freeze the full environment or transitive libraries. Avoid external upgrades,
removal, moves or edits. Changed or inaccessible content blocks reuse, Run and
resume.

Doctor never repairs a shared generation in place. If the source Project's
selected tools fail, `emrys doctor --repair` prepares and verifies a new
generation, then moves only that Project's current selection. Other Projects
continue to name the old generation and must explicitly select the replacement:

```bash
emrys runtime discover --project /absolute/dependent/project.yaml --from-project /absolute/source/project.yaml --replace
emrys runtime discover --project /absolute/dependent/project.yaml --from-project /absolute/source/project.yaml --replace --execute
```

Replacement is allowed only when the existing inventory already shares tools
from that same source Project. The previous generation and seal remain for
retained Runs and Attempts. A failed seal, generation or selection publication
may leave a `maintenance.lock`; retain it and the partial generation for explicit
reconciliation. Do not edit an inventory, seal or digest to bypass admission.

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

`PASS` means that domain passed current checks. `DOCTOR BLOCKED` means the
requested maintenance action cannot proceed. Doctor changes only Project-owned
tools and preparation records; it does not obtain scientific inputs, change a
study design, or repair Results. A verification-only plan does not invoke package
managers, but repeats current file/runtime checks and, for Slurm, compute checks
and head-node finalization. Declining the plan with Enter or `n` makes no repair.
After an error, retain diagnostics; do not change dependency locks or clear
installation folders to force another attempt.

Doctor prints its full invocation elapsed time and exit outcome, including time
spent awaiting operator confirmation. Add `--log-level verbose` for precise
phase times. For approved maintenance, the same phase measurements appear in
the existing diagnostic JSONL as `doctor_phase_timing`; read-only diagnosis does
not create a log. Compute observations stay distinct from head observations.
`Slurm submission-to-return wait` includes waiting, launch, compute and return
overhead. It cannot by itself tell you how long the job spent queued. After a
waited submission, Doctor makes one bounded accounting lookup using the recorded
job identity and exact maintenance stream paths. Its normal summary separates
submitted-to-start wait, eligible queue wait and allocation wall time; time
before eligibility is not eligible queue wait. Allocation wall time includes
launch/verification overhead and does not measure scientific compute time.
Missing, delayed, inconsistent, requeued or suspended accounting leaves derived
intervals unavailable. The existing maintenance log retains admitted UTC dates,
accounting counters and limitations as `doctor_scheduler_timing`, after the
maintenance outcome. Normal output also shows the accounting state, source and
scheduler exit status. This separates observed `CANCELLED` from `FAILED`; missing
accounting stays `UNKNOWN`. A `COMPLETED` accounting observation does not erase
a client/submission failure or establish completed qualification.
Lookup duration is a separate phase, outside the waited
submission timer. Timing never establishes qualification or permits recovery.
Keep complete diagnostics when investigating slow verification; these timings
do not justify removing input reads or changing resource requests.
Maintenance logs also retain `runtime_check_passed` details for their actual
Doctor phases, buffered until the operation outcome. Verbose/debug diagnosis
shows escaped passing details, including available subprocess durations.
Separate Snakemake version/startup times from content hashing; the SHA-256
utility check measures only its known test payload. These observations still
do not attribute runtime-file bytes, physical I/O or memory.

Allow more than ten minutes when planning setup; downloads, compilation and
queue waits can take considerably longer, and verification alone can exceed
that allowance. Read the named phase and retained diagnostics instead of treating
elapsed time as failure. An unchanged retry preserves package reuse but repeats
current admission checks. Interrupted setup may reuse retained tools even when
the inventory is missing; changed dependencies or inputs require fresh checks.
The immutable plan names required work, while `package-output.log` records actual
package-manager reuse and changes. Earlier successful evidence remains retained
without qualifying the present files. Comparable site measurements and any
reduction of repeated checks remain CV-26 work.

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
