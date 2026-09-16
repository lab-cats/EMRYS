# EMRYS quickstart: synthetic Project to Results

This guide takes a CSU Viking user from a fresh installation to two reports
for a small supplied study, then through the original six-library EV/PUM1 study.
**Run every command on the Viking head node.** EMRYS supplies the Viking
settings, prepares its tools and storage, and submits compute work through Slurm.

A **Project** is the folder containing a study's input definitions, software
environment and results. An **Analysis** selects the samples and scientific
settings; the supplied one is called `primary`. A **Run** records those choices
as a fixed plan. Its **Results** contain the generated data and two HTML reports.

EMRYS is alpha research software. The exercise contains four libraries of 130
read pairs and a 100,000-base reference. It checks that the software runs;
reported candidates are not validated RNA-editing sites.

## Before you begin

Log in to Viking using your usual CSU connection. A terminal on your laptop
alone is not a Viking terminal. Keep the Viking terminal open during setup.

You need your normal writable home directory, permission to download software,
and the standard Bash, Git and curl commands. If an installation command says
one is unavailable or access is denied, keep the error and ask CSU computing
support to resolve that prerequisite.

This guide keeps software in `$HOME/EMRYS` and new studies beneath its tracked
`Projects/` directory. The clone already contains that parent; do not create it
or a new Project child yourself. Existing Projects keep their original locations
and references; these instructions do not move them.

**Steps 1–5 are ready to paste unchanged.** Step 7 asks for the locations of
the delivered EV/PUM1 FASTQs, reference and annotation; every other known value
is given in that step. Paste blocks in order. Stop at an error and retain its
output and any printed log path. Do not delete partial setup or results to retry.
Keep quotation marks when pasting commands. `$HOME` means your Viking home
directory; the `EMRYS_...` variables below remember locations for later commands.
A backslash (`\`) at the end of a line continues the same command on the next
line. Paste the whole block, keeping each backslash as the final character.

## 1. Install EMRYS

uv manages Python; Pixi supplies the scientific tools and R, and Doctor uses
renv to install the required R packages. Install uv and Pixi in your own account
with these commands. Their installers may update your shell startup files:

```bash
set -o pipefail &&
curl -LsSf https://astral.sh/uv/0.12.3/install.sh | sh &&
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.75.0 bash &&
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH" &&
uv --version &&
pixi --version
```

Download EMRYS and install its locked Python environment:

```bash
cd "$HOME" &&
git clone https://github.com/lab-cats/EMRYS.git &&
cd EMRYS &&
export EMRYS_SOURCE_ROOT="$(pwd -P)" &&
uv sync --locked --no-default-groups --group workflow --python 3.14 &&
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate" &&
emrys --version
```

uv downloads the selected Python version if needed. The final command prints
the installed EMRYS version; a missing-command or installation error must be
resolved before continuing. Leave this checkout unchanged for the exercise;
EMRYS records the implementation used for a Run. The path commands use `pwd -P`
so EMRYS receives the actual storage location rather than a symbolic-link
shortcut.

The [returning to the Project](#returning-to-the-project-in-a-new-terminal)
instructions below restore this environment after reconnecting.

## 2. Create the supplied study

### Enter the Projects home

Enter the Projects directory supplied by the repository:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects" &&
export EMRYS_PROJECTS_ROOT="$(pwd -P)"
```

The variable records the physical path from `pwd -P`. Project children are
ignored by Git, while `Projects/README.md` explains what belongs here.
Initialization requires an absent child and refuses a symlink destination.
Stop if entering the supplied parent fails; do not continue from the previous
directory.

### Create the synthetic Project

"Synthetic" means that EMRYS supplies a tiny example study, including made-up
reads, a reference and scientific settings. This smoke test checks that the
installation can prepare tools, run work on Viking and produce reports before
you use your own data. It does not test whether your study will fit the same
resources or whether its scientific choices are correct. Create it with the
built-in Viking settings:

```bash
export EMRYS_PROJECT_ROOT="$EMRYS_PROJECTS_ROOT/emrys-smoke"
emrys init synthetic --site viking --output-dir "$EMRYS_PROJECT_ROOT" --execute &&
cd "$EMRYS_PROJECT_ROOT" &&
emrys validate
```

Continue after `Project validation: PASS`. The reads, reference and scientific
settings are supplied; there is no configuration file to edit. `--execute`
creates the Project; `validate` only checks it. Creation will not overwrite an
existing destination. Preserve any partial directory if creation fails.

The saved Viking settings request one exclusive node with 256 CPUs for 12 hours,
using account `viking-users`, partition `long`, QoS `normal`, site-default memory
and private temporary storage under `/tmp`. Slurm chooses the node.
EMRYS uses the historical EV/PUM1 policy: 12 workflow cores, 512 GiB and the
restored stage-specific thread, concurrency and memory allowances. The
`--site viking` choice supplies the placement automatically; you do not configure
Slurm or write a resource profile. The same defaults apply to real-data Projects.

## 3. Prepare the scientific tools

```bash
emrys doctor --repair
```

Doctor shows its plan before changing Project-owned tools. Answer `y` to start;
Enter or `n` declines. Allow more than ten minutes: downloads, verification and
Slurm queue waits can take considerably longer, even when tools are reused.
Doctor names the current stage and elapsed time. Keep it running until it says
`EMRYS is ready.` It checks the tools and storage on the head and compute nodes;
EMRYS handles Slurm setup. If Doctor reports a refusal or fails, stop and keep
the printed diagnostic and log path. Do not clear installation folders to retry.
See [Doctor status and timing](docs/operations/RUNBOOK.md#doctor-status-and-timing)
for detailed status words and [installation logs](docs/operations/TROUBLESHOOTING.md#watching-doctors-installation-log)
if you need to diagnose setup.

## 4. Run the study

```bash
emrys run
```

Review the short submission summary and answer `y` once. EMRYS prints `JOB_ID`,
`JOB_NAME` and the log paths, then says that the Slurm job was submitted and
completion is not yet verified. The head-node prompt returns while Slurm runs
the Analysis and reports; you may disconnect without stopping it. Submit once
and keep the Project and its inputs in place.

Watch progress from the Project on the head node:

```bash
emrys watch
```

With one retained submission or one Run, EMRYS selects it automatically. If
several are plausible, choose the intended one from the picker; EMRYS never
assumes the newest. You can instead use the exact printed
job ID or job name, for example `emrys watch 12345`. Press `r` to recheck the
fixed selection and its evidence; press `q` to leave. Leaving the dashboard
does not stop the job.

A queued job may not have created its Run yet. **No Run shown is not a reason
to submit again.** Keep the job number and request record, wait, and watch
again. A retained response or scheduler observation does not prove completion.
If the job's state stays unclear, use the
[exact-request check](docs/operations/RUNBOOK.md#retain-a-submission-before-its-run-exists).
An `UNKNOWN` observation remains unresolved.

The dashboard and static inspection announce `Run complete` only from admitted
Run evidence. When Results are complete, verified Task counts replace stale
log-derived stage counts. Read the evidence dates before relying on the display.
Completion is confirmed by the announcement and all four lines:

```text
Run admission: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting admission: complete
```

Keep the original Project, inputs, runtime, logs and complete Run so
the computation remains inspectable. An unsuccessful inspection prints the
problem and the next supported action; retain that output before recovery.
For dated Task evidence, retries and exact logs, see
[inspection detail](docs/operations/RUNBOOK.md#project-and-run-operations).

## 5. Open the reports

Inspection prints the report paths. In your usual CSU file-transfer application,
copy the Run's complete `results` directory to your computer. Keep its folders
together so links to tables work. In the copied directory, open the two files
below in your browser. Use the actual Run ID printed by inspection:

```text
reports/<RUN_ID>/<RUN_ID>.scientific_report.html
reports/<RUN_ID>/<RUN_ID>.evidence_report.html
```

The **Scientific report** presents the candidates. The **Evidence report**
explains how the data was generated and which checks passed. The supplied
study should produce three Step 09 candidate rows, with one significant row.
`FWD_like` and `REV_like` are alignment groups, not biological strand labels.
Keep the original Project and supporting files on Viking. If you use only a
terminal to transfer files, follow the [checked transfer procedure](docs/operations/RUNBOOK.md#retrieve-reports-from-a-terminal)
from your own computer.

This completes the synthetic walkthrough. It demonstrates this particular
software, input and execution path; it does not establish biological validity
or readiness for every dataset.

## 6. If execution or reporting did not complete

Run `emrys inspect` from the Project and read **Next supported action:** and
its blockers. If work may still be running or another host's ownership is
unverified, wait and inspect again; do not submit or resume it. If inspection
offers recovery, use `emrys resume`, review the plan and answer `y`. If
Scientific Results are complete and report generation is unblocked, preview
with `emrys report`, then submit with `emrys report --execute` and inspect
again. If inspection is blocked, stop and keep its output, logs, locks, partial
files and backups for diagnosis. Do not delete or force a retry. The
[recovery guide](docs/operations/TROUBLESHOOTING.md#run-and-reporting-state)
explains each state and how to select one Run when several exist.

## 7. Create a Project for your own data

### Gather the study inputs and scientific choices

Stay on the **Viking head node**, with the environment from step 1 active. Keep
the delivered FASTQs, their checksums, the delivered Novogene reference FASTA
and its matching GTF available at their existing locations. The FASTA directory
must be writable so EMRYS can create or check its `.fai` and `.dict` sidecars.

### Create the Project and its input lists

EMRYS discovers paired FASTQs and creates `samples.tsv` and `partitions.tsv`
inside the new Project. FASTQ names must end in `_R1`/`_R2` or `_1`/`_2`, then
`.fastq`, `.fq`, or either extension plus `.gz`.

```bash
cd "$EMRYS_PROJECTS_ROOT" &&
emrys init pum1-study --site viking
```

Enter the absolute FASTQ directory, delivered reference FASTA and matching GTF
when asked. These paths depend on where the files are stored on Viking and are
the only values this guide cannot supply. Confirm that all six FASTQ pairs were
found, then assign them exactly as follows:

| Sample | Condition | Pairing group | Strandedness |
| --- | --- | --- | --- |
| `ABE_EV_2` | `EV` | `2` | `reverse` |
| `ABE_PUM1_2` | `PUM1` | `2` | `reverse` |
| `ABE_EV_3` | `EV` | `3` | `reverse` |
| `ABE_PUM1_3` | `PUM1` | `3` | `reverse` |
| `ABE_EV4` | `EV` | `4` | `reverse` |
| `ABE_PUM1_4` | `PUM1` | `4` | `reverse` |

Leave the regions-file prompt empty. At the selector prompt, enter this complete
space-separated list; the names must match the delivered reference:

```text
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 X Y MT
```

The original study has 150-base reads. Enter the remaining values exactly as
shown:

| Prompt | EV/PUM1 value |
| --- | --- |
| `sjdb overhang` | `149` |
| `genome sa index nbases` | `14` |
| `control condition` | `EV` |
| `treatment condition` | `PUM1` |
| `target change` | `A>G` |
| `min sample dp [1]` | Press Enter for `1` |
| `mean dp threshold [50]` | Press Enter for `50` |
| `fdr threshold [0.05]` | Press Enter for `0.05` |
| `common or threshold [1.2]` | Press Enter for `1.2` |
| `absolute difference threshold [0.005]` | Press Enter for `0.005` |
| `background max fraction [0.01]` | Press Enter for `0.01`; no background cohort is selected, so it is unused |

The first pass validates paths, assignments, selectors and settings without
hashing every FASTQ. Review the displayed interpretation, then paste the exact
creation command printed by EMRYS. That command carries every answer forward,
hashes each FASTQ once and refuses changed inputs. Keep any partial Project and
the printed diagnostic if creation stops.

After `Project ready:`, validate the new Project:

```bash
export EMRYS_PROJECT_ROOT="$EMRYS_PROJECTS_ROOT/pum1-study"
cd "$EMRYS_PROJECT_ROOT" &&
emrys validate
```

Continue only after `Project validation: PASS`. The Project references the
original FASTQs and reference files and owns its generated manifests beside
`project.yaml`.

### Prepare, run and open the EV/PUM1 reports

On the head node, select the tools that the smoke Project just prepared. The
first command below previews and verifies the selection without writing. The
second verifies it again and records it for this Project. Neither command
installs packages.

Initialization selects the historical EV/PUM1 resource policy automatically,
with the same Viking placement described in step 2. Doctor checks the selected
profile and the compute allocation before Run submission. No resource editing
is needed for this path. For a Project created with older settings, follow
[existing Project profile selection](configs/README.md#create-a-named-profile-without-writing-yaml)
and use that profile for both Doctor and Run.

```bash
emrys runtime discover --from-project "$EMRYS_PROJECTS_ROOT/emrys-smoke"
emrys runtime discover --from-project "$EMRYS_PROJECTS_ROOT/emrys-smoke" --execute
emrys doctor --repair
```

Doctor still checks this Project, storage and intended compute placement. If the
shared tools pass, Doctor performs no package installation. If their owning
smoke Project later needs repair, Doctor creates a separate verified generation;
it does not change the files selected by this Project. This Project remains
blocked on a damaged old generation until you explicitly select the replacement
named by Doctor with `runtime discover --from-project ... --replace --execute`.

Review the Doctor plan, answer `y`, and wait for `EMRYS is ready.` The Viking
settings were selected during initialization; no scheduler or storage
configuration needs to be written by hand. If a check fails, stop and retain
the diagnostic and log path instead of deleting state or changing resources.

Submit the study once, reviewing the summary and answering `y`:

```bash
emrys run
```

Review Doctor's allocation and workflow limits before confirming. Review the
same limits in Run's submission summary; if they are unsuitable, decline
submission and revise the selection before another readiness check.

Keep the printed job number and log paths. From the same Project on the head
node, check progress with:

```bash
emrys watch
```

A queued job has not created its Run yet. Keep the retained submission request
shown by inspection; an absent Run does not authorize another submission. Once
the Run appears, repeat inspection until the four completion lines shown in
step 4 appear. Static `emrys inspect` prints both
report paths. Copy this Run's complete `results` directory to your computer
and open its Scientific and Evidence reports using the instructions in step 5.

The EV/PUM1 study need not produce the synthetic fixture's candidate counts.
Its output is a set of computational candidates, not validated editing sites.
Keep the original Project, inputs, runtime, complete Run and logs at their
original locations so the work remains inspectable and recoverable.

## Returning to the Project in a new terminal

Reconnect to the Viking head node, then restore the installed command and enter
the existing synthetic Project:

```bash
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
cd "$HOME/EMRYS" &&
export EMRYS_SOURCE_ROOT="$(pwd -P)" &&
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate" &&
cd "$EMRYS_SOURCE_ROOT/Projects" &&
export EMRYS_PROJECTS_ROOT="$(pwd -P)" &&
cd "$EMRYS_PROJECTS_ROOT/emrys-smoke" &&
export EMRYS_PROJECT_ROOT="$(pwd -P)" &&
emrys inspect
```

For the EV/PUM1 study, replace the final Project `cd` line with
`cd "$EMRYS_PROJECTS_ROOT/pum1-study"`. For an existing Project elsewhere, use
`cd "/full/path/to/existing-project"` instead; keep it at its original location.
Reconnecting does not require reinstalling EMRYS, recreating the Project or
resubmitting work. From another directory, select it explicitly with
`emrys inspect --project "/full/path/to/existing-project/project.yaml"`.

## Further help

If a step fails, [troubleshooting](docs/operations/TROUBLESHOOTING.md) explains
common errors and supported recovery. The
[runbook](docs/operations/RUNBOOK.md) covers other installation environments,
existing Projects and advanced execution options.
