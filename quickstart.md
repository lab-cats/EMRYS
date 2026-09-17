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

**Steps 1–5 are ready to paste unchanged.** The setup command in step 1 asks
three questions whose defaults are given there. Step 7 asks for the locations
of the delivered EV/PUM1 FASTQs, reference and annotation; every other known
value is given in that step. Paste blocks in order. Stop at an error and retain its
output and any printed log path. Do not delete partial setup or results to retry.
Keep quotation marks when pasting commands. `$HOME` means your Viking home
directory. `EMRYS_SOURCE_ROOT` below names the checkout; prompted setup saves the
repeated EMRYS command defaults.
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

Save the values that EMRYS will reuse. Run this from the repository root:

```bash
emrys setup --execute
```

Press Enter to accept the displayed `Projects` home and `viking` site. Leave the
optional log root empty so each Project keeps its own application logs. EMRYS
creates the ignored repository-root `.env` with mode `0600`; commands run in the
checkout or its Project directories load it automatically. An explicit command
line value wins over the process environment, which wins over `.env`, which wins
over a built-in default.

The [returning to the Project](#returning-to-the-project-in-a-new-terminal)
instructions below restore this environment after reconnecting.

## 2. Create the supplied study

### Enter the Projects home

Enter the Projects directory supplied by the repository:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects"
```

The saved Projects home records this physical directory. Project children are
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
emrys init synthetic --output-dir "$(pwd -P)/emrys-smoke" --execute &&
cd emrys-smoke &&
emrys validate
```

Continue after `Project validation: PASS`. The reads, reference and scientific
settings are supplied; there is no configuration file to edit. `--execute`
creates the Project; `validate` only checks it. Creation will not overwrite an
existing destination. Preserve any partial directory if creation fails.

The saved Viking settings request all CPUs and RAM on one exclusive node for
12 hours, using account `viking-users`, partition `long`, QoS `normal` and private
temporary storage under `/tmp`. Slurm chooses the node. The workflow and STAR
indexing use the granted, process-accessible capacity; other stages retain their
historical thread, concurrency and memory settings. The
saved `viking` choice supplies the placement automatically; you do not
configure Slurm or write a resource profile. The same default applies to
real-data Projects.

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
cd "$EMRYS_SOURCE_ROOT/Projects" &&
emrys init pum1-study
```

The first two prompts ask for an existing reference FASTA and its matching GTF.
These are study inputs supplied with the sequencing delivery or obtained from
the same reference source; EMRYS does not generate or download them. The FASTA
contains the reference sequences, and the GTF describes features on those same
sequences. If either file is missing, stop and obtain the matching pair from the
data provider or reference source rather than substituting an unrelated file.
Enter their absolute Viking paths.

Next enter the scientific settings below. Prompts show optional defaults as
`Press ENTER for VALUE`; those words remain visible without terminal color, and
the default itself is dimmed when color is available.

| Prompt | EV/PUM1 value |
| --- | --- |
| `sjdb overhang` | `149` |
| `genome sa index nbases` | `14` |
| `control condition` | `EV` |
| `treatment condition` | `PUM1` |
| `target change` | `A>G` |
| `min sample dp (Press ENTER for 1)` | Press Enter |
| `mean dp threshold (Press ENTER for 50)` | Press Enter |
| `fdr threshold (Press ENTER for 0.05)` | Press Enter |
| `common or threshold (Press ENTER for 1.2)` | Press Enter |
| `absolute difference threshold (Press ENTER for 0.005)` | Press Enter |
| `background max fraction (Press ENTER for 0.01)` | Press Enter; no background cohort is selected, so it is unused |

EMRYS then asks for the absolute FASTQ directory. This path depends on where the
delivered files were stored on Viking. Confirm that all six FASTQ pairs were
found, then assign them exactly as follows:

| Sample | Condition | Pairing group | Strandedness |
| --- | --- | --- | --- |
| `ABE_EV_2` | `EV` | `2` | `reverse` |
| `ABE_PUM1_2` | `PUM1` | `2` | `reverse` |
| `ABE_EV_3` | `EV` | `3` | `reverse` |
| `ABE_PUM1_3` | `PUM1` | `3` | `reverse` |
| `ABE_EV4` | `EV` | `4` | `reverse` |
| `ABE_PUM1_4` | `PUM1` | `4` | `reverse` |

EMRYS offers two mutually exclusive ways to divide the reference for analysis:

- An existing regions file is a BED- or VCF-like text file listing selected
  intervals. Use this only when the study delivery includes the intended file.
- Otherwise, press Enter at `optional regions file` and type reference sequence
  names or regions separated by spaces. Sequence names are the first words after
  `>` in the FASTA headers. Project creation validates them against that FASTA.

The delivered EV/PUM1 study does not require a separate regions file. Press
Enter, then enter this complete space-separated list at the prompt that names
your FASTA:

```text
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 X Y MT
```

The first pass admits the reference paths and reviews assignments, selectors and
settings without hashing every FASTQ. It then says `Preview complete; Project
not created.` Review the displayed interpretation. Under `Next action`, copy and
run the entire command—although long, it carries every answer forward without
asking again. That command hashes each FASTQ once, validates reference and
partition compatibility, and refuses changed inputs. Keep any partial Project
and the printed diagnostic if creation stops. Successful creation ends with
`Project ready:` followed by the new `project.yaml` path.

After `Project ready:`, validate the new Project:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects/pum1-study" &&
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
emrys runtime discover --from-project "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke"
emrys runtime discover --from-project "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke" --execute
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
cd "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke" &&
emrys inspect
```

For the EV/PUM1 study, replace the final Project `cd` line with
`cd "$EMRYS_SOURCE_ROOT/Projects/pum1-study"`. For an existing Project elsewhere,
use `cd "/full/path/to/existing-project"` instead; keep it at its original location.
Reconnecting does not require reinstalling EMRYS, recreating the Project or
resubmitting work. From another directory, select it explicitly with
`emrys inspect --project "/full/path/to/existing-project/project.yaml"`.

## Further help

If a step fails, [troubleshooting](docs/operations/TROUBLESHOOTING.md) explains
common errors and supported recovery. The
[runbook](docs/operations/RUNBOOK.md) covers other installation environments,
existing Projects and advanced execution options.
