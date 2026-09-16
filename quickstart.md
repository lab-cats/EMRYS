# EMRYS quickstart: synthetic Project to Results

This guide takes a CSU Viking user from a fresh installation to two reports
for a small supplied study, then through creating a study with your own data.
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

Paste each block in order. Stop at an error and retain its output and any
printed log path. Do not delete partial setup or results to retry.
Keep quotation marks when pasting commands. `$HOME` means your Viking home
directory; the `EMRYS_...` variables below remember locations for later commands.
A backslash (`\`) at the end of a line continues the same command on the next
line. Paste the whole block, keeping each backslash as the final character.

## 1. Install EMRYS

uv manages Python; Pixi supplies the scientific tools and R, and Doctor uses
renv to install the required R packages. Install uv and Pixi in your own account
with these commands. Their installers may update your shell startup files:

```bash
curl -LsSf https://astral.sh/uv/0.12.3/install.sh | sh
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.75.0 bash
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
uv --version
pixi --version
```

Download EMRYS and install its locked Python environment:

```bash
cd "$HOME"
git clone https://github.com/lab-cats/EMRYS.git
cd EMRYS
export EMRYS_SOURCE_ROOT="$(pwd -P)"
git rev-parse HEAD
uv sync --locked --no-default-groups --group workflow --python 3.14
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
emrys --version
```

uv downloads the selected Python version if needed. The final command prints
the installed EMRYS version; a missing-command or installation error must be
resolved before continuing. Keep the printed Git commit ID with your notes and
leave this checkout unchanged for the exercise. EMRYS records the implementation
used for a Run. The path commands use `pwd -P` so EMRYS receives the actual
storage location rather than a symbolic-link shortcut.

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

Create the supplied Project with the built-in Viking settings:

```bash
export EMRYS_PROJECT_ROOT="${EMRYS_PROJECTS_ROOT:?Choose a Projects home first}/emrys-smoke"
emrys init synthetic --site viking --output-dir "$EMRYS_PROJECT_ROOT" --execute
cd "$EMRYS_PROJECT_ROOT"
emrys validate
```

Continue after `Project validation: PASS`. The reads, reference and scientific
settings are supplied; there is no configuration file to edit. `--execute`
creates the Project; `validate` only checks it. Creation will not overwrite an
existing destination. Preserve any partial directory if creation fails.

The Viking choice is saved in this Project. It supplies the account, partition,
resource request and temporary-storage location for subsequent commands; you
do not need to look up those values or provide them again.

## 3. Prepare the scientific tools

```bash
emrys doctor --repair
```

Doctor names the planned actions: **repair and verification** when package-manager
work is needed, or **verification** when the selected runtime already passes.
Answer `y` to begin the displayed plan. **Allow more than ten minutes for setup;
downloads, compilation and queue waits can extend it considerably.** This is a
planning allowance, not a completion deadline: verification alone can exceed
ten minutes. The progress display names the current stage and shows elapsed
time. Complete installation output is retained at the printed log location.
For optional detail while setup runs, see
[watching the installation log](docs/operations/TROUBLESHOOTING.md#watching-doctors-installation-log).

When needed, Doctor checks/updates the tools on the head node; Pixi and renv
report which packages they reuse or change in the retained package output.
The plan's `Runtime work` line distinguishes a currently verified runtime,
preparing a missing managed inventory, and checking/updating tools selected by
a retained inventory. A missing inventory can follow an interrupted setup;
it does not mean all tools must be installed again. The manager output at
`package-output.log` records actual package reuse and changes.
An unchanged retry still checks current files, tools and storage at the required
boundaries. An interrupted setup may reuse retained packages while completing
missing work; changed inputs or tools must pass fresh checks. A previous success
is retained evidence of that attempt, not a promise that the current files pass.
Doctor then submits the required compute-node checks and confirms that the
study's storage works across both nodes. Keep
this command running until it reports `EMRYS is ready.` All of the scheduler
and storage setup is handled by EMRYS.
At return, Slurm accounting timing separates submitted-to-start and eligible
queue waits from allocation wall time when an exact record is available.
Allocation wall time includes launch and verification overhead; it is not
scientific compute time. Unavailable timing does not change Doctor's result.

Read Doctor's status words and the accompanying execution requirements:

| Status | Meaning |
| --- | --- |
| Runtime `NOT PREPARED` | The default runtime inventory has not been created. Review the proposed setup actions. |
| Runtime `CHECKS FAILED` | The selected runtime was inspected and failed required checks; retain the named diagnostics. |
| Storage `NOT QUALIFIED` | Required storage proof is unavailable or invalid. The detail distinguishes the observed problem; this is not always fresh setup. |
| Execution `NOT ADMITTED` | The execution profile cannot be used as selected. Follow its diagnostic before running. |

`PASS` means that domain passed its current checks. `DOCTOR BLOCKED` means the
requested maintenance operation itself cannot proceed; it remains a refusal.
Downloads, compilation, verification, and Slurm queue waits can all add time.

A verification-only plan reuses the selected runtime without invoking package
managers. It repeats current input/runtime checks and, for Slurm, compute checks
and head-node finalization because earlier success cannot establish that those
files and environments are still unchanged. Elapsed time for the Slurm stage
includes both queue waiting and compute work.
For precise phase times, use `--log-level verbose`; the full invocation time
also includes time spent waiting for your confirmation.

Doctor changes only the Project-owned tools and preparation records. It does
not obtain your scientific inputs, change your study design or repair Results.
An empty answer or `n` declines the repair. If repair exits with an error, retain
the printed log and resolve its cause before another attempt. Do not change
dependency locks or clear installation folders to force it through.

## 4. Run the study

```bash
emrys run
```

Review the short submission summary and answer `y`. Slurm will run the Analysis
and generate both reports on a compute node. EMRYS prints the job number and
log locations. Submit once and keep the Project and its inputs in place.

At `Execute this plan? [y/N]`, `y` or `yes` starts submission; Enter or `n`
declines it. After successful submission, the head-node prompt returns and
Slurm continues the work independently. Save the printed job number and log
paths. You do not need to stay logged in to keep a submitted Run running.

Check the Run from the head node:

```bash
emrys inspect
```

Inspection first lists retained submission requests, including their exact
directories, recorded response job IDs and diagnostics. It then selects an
available Run. A queued job has not created its Run yet; `Runs: none found at
inspection time` does not mean you should submit again. The retained response
alone does not prove the job's current state. Keep uncertain or partial records,
wait and repeat `emrys inspect`; it does not start or change work.
To check one exact request's queue state or accounting result, follow
[submission inspection](docs/operations/RUNBOOK.md#retain-a-submission-before-its-run-exists).
An `UNKNOWN` observation leaves the request unresolved; keep its records before
considering another submission.
For one terminal view of scheduler observations, dated Task evidence and logs,
use [inspection watch](docs/operations/RUNBOOK.md#watch-one-fixed-selection).
Press `r` there to verify progress again and `q` to leave; leaving the view does
not stop a job. Read the evidence dates before relying on a displayed result.
Completion is confirmed by all four lines:

```text
Run admission: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting admission: complete
```

**Scientific task observations** counts the evidence already admitted. `Started;
completion unverified` means a start record is present, not that a worker is
currently running. `No admitted start` can mean absent or invalid records; read
the printed blockers before choosing an action. These counts do not override
the completion lines or recovery decision.

For retained Task outcomes and their exact stdout/stderr paths, add
`--detail verbose` to inspection. Each row names its original Attempt, including
failed retries. A recorded `succeeded` outcome still needs verified scientific
completion. Missing or changed log evidence remains a blocker; keep the files.

Keep the original Project, inputs, runtime, logs and complete Run so
the computation remains inspectable. An unsuccessful inspection prints the
problem and the next supported action; retain that output before attempting
recovery.

## 5. Open the reports

Inspection prints the report paths. In your usual CSU file-transfer application,
copy the Run's complete `results` directory to your computer. Keep its folders
together so links to tables and other report files continue to work.
For a terminal-only transfer with a checksum comparison, follow the
[report retrieval procedure](docs/operations/RUNBOOK.md#retrieve-reports-from-a-terminal)
from a terminal on your own computer.

On Viking, the reports sit within this layout. Use the actual paths printed
by inspection; `<PROJECT>` and `<RUN_ID>` below explain the folder structure:

```text
<PROJECT>/runs/<RUN_ID>/results/reports/<RUN_ID>/
    <RUN_ID>.scientific_report.html
    <RUN_ID>.evidence_report.html
```

Inside the copied directory, open these two HTML files in your web browser:

```text
reports/<RUN_ID>/<RUN_ID>.scientific_report.html
reports/<RUN_ID>/<RUN_ID>.evidence_report.html
```

The **Scientific report** presents the candidates. The **Evidence report**
explains how the data was generated and which checks passed. The supplied
study should produce three Step 09 candidate rows, with one significant row.
`FWD_like` and `REV_like` are alignment groups, not biological strand labels.
Copied reports still name the original input and runtime locations. Keep the
original Project and its supporting files on Viking; copying the reports does
not replace those records.

This completes the synthetic walkthrough. It demonstrates this particular
software, input and execution path; it does not establish biological validity
or readiness for every dataset.

## 6. If execution or reporting did not complete

Run `emrys inspect` from the Project and read **Next supported action:** and
any listed blockers. The same saved Viking settings apply to recovery and
report generation; issue the commands below from the head node.

| What inspection reports | What to do |
| --- | --- |
| Work is still running | Wait and inspect again. Do not submit another Run or resume active work. |
| Run lock says `remote ownership unverified` | The recorded owner is on another host. Keep its host/job details and inspect again; this observation does not prove the job stopped or authorize recovery. |
| Computation failed or was interrupted, with `Recovery available: yes` | Run `emrys resume`, review its plan and answer `y` for the supported retry. It checks completed work before reusing it and records a new Attempt for the same Run. |
| Scientific Results are complete, but reports are missing and generation is unblocked | Run `emrys report` to check the proposed reporting work, then `emrys report --execute` to submit it. Inspect again when it finishes. Completed scientific work does not need to be repeated. |
| A state is blocked, or reporting refuses partial files | Stop and retain the inspection output and printed logs for the EMRYS maintainer. Do not delete files, remove locks or force a retry. |

Keep partial outputs, logs, locks, backups and receipts. With several Runs,
select the intended one by its printed name or ID when prompted; do not assume
the newest directory is the one you want. `validate`, `doctor` without repair,
`inspect` and `report` without `--execute` are read-only.

## 7. Create a Project for your own data

Stay on the **Viking head node**, with the EMRYS Python environment from step 1
activated. Use a new Project so the supplied study and its results remain intact.
You can reuse the installed EMRYS command; each Project has its own runtime
inventory and preparation records.

### Gather the study inputs and scientific choices

Have the study's scientist or analyst confirm these before starting:

- **Paired-end reads:** one R1 FASTQ and one R2 FASTQ for each library, together
  with the sequencing provider's checksums. R1 and R2 are the two reads from
  one library; they are not the control/treatment pairing used in the analysis.
- **Experimental assignments:** a unique sample ID, condition, pairing group,
  and library strandedness for every library. The built-in Analysis needs at
  least two pairing groups, each containing exactly one control and one
  treatment. The same group name joins the intended control and treatment;
  filenames and row order cannot establish that relationship. Do not count
  technical sequencing lanes as independent biological replicates.
- **Reference:** an uncompressed genome FASTA and matching gene-annotation GTF,
  with their source and release recorded. EMRYS creates or checks `.fai` and
  `.dict` index files beside the FASTA, so that directory must be writable.
  Arrange a study copy if the shared reference belongs to another team.
- **Regions and analysis settings:** explicit chromosome/region selectors or an
  existing file of nonoverlapping regions, STAR index parameters appropriate to
  the reads and reference, the control and treatment labels, the nucleotide
  change to test, and the study's thresholds.
  The example values offered during setup are suggestions, not validated
  settings for every study.

Strandedness must be `forward`, `reverse`, `unstranded`, or `unknown`. Use the
library preparation information; `unknown` records that you do not know, and
does not turn a stranded library into an unstranded one. It is distinct from
the later mechanical `FWD_like` and `REV_like` alignment labels.

Region selectors and regions files must use the same chromosome or contig names
as the FASTA.
For a `.bed` file, columns are separated by tabs and coordinates are zero-based
with the end excluded: `chr1`, `0`, `100` selects the first 100 bases of `chr1`.
A plain three-column region table instead uses one-based coordinates with both
ends included: `chr1`, `1`, `100` selects that same interval. Do not change the
filename extension without converting the coordinates. Use regions chosen for
the study; do not use this illustrative interval automatically.

EMRYS does not download study data or decide experimental pairing. Keep the
input files, their checksums and their declared locations for the life of the
Run. Success with the tiny supplied study does not establish that a full
dataset will fit the same allocation.

### Create the Project and its input lists

EMRYS creates the two input lists inside the new Project. `samples.tsv` records
libraries and biological assignments; `partitions.tsv` records the regions to
process. You do not construct or format either file.

FASTQ names must end in `_R1`/`_R2` or `_1`/`_2`, followed by `.fastq` or `.fq`
and optional `.gz`. The shared prefix becomes the proposed sample ID. The
terminal shows every detected pair and asks for its condition, pairing group,
and strandedness. EMRYS never infers those biological values from filenames.

From the supplied Projects home, start guided setup:

```bash
cd "$EMRYS_PROJECTS_ROOT"
emrys init my-study --site viking
```

Enter the absolute directory containing the FASTQs. For regions, enter one
existing BED, VCF, or tab-separated regions file, or leave that prompt empty
and enter space-separated chromosome/region selectors such as `1 2 X` or
`1:1-100`. Declare every intended selector; the examples are not automatic
whole-genome choices. EMRYS then asks for the reference and scientific settings
below. Type each agreed value and press Enter. Where a value appears in brackets,
Enter accepts it.

| Prompt | What to enter |
| --- | --- |
| `reference fasta` | Absolute path to the study's uncompressed reference FASTA. |
| `reference gtf` | Absolute path to the matching gene-annotation GTF. |
| `sjdb overhang` | The STAR splice-junction overhang selected for the study's read length. Obtain this from the analyst who chose the alignment settings. |
| `genome sa index nbases` | The STAR suffix-array index length selected for this reference. It controls index construction and must suit the genome size. |
| `control condition` | The exact control label in your sample assignments; `control` in the example above. |
| `treatment condition` | The exact treatment label; `treatment` in the example above. |
| `target change` | Two different bases separated by `>`, such as `A>G`, according to the study question. |
| `min sample dp [1]` | Minimum usable read depth in every paired sample for a site to be tested. This cutoff is inclusive. |
| `mean dp threshold [50]` | The candidate's mean depth across paired control and treatment samples must be greater than this value. |
| `fdr threshold [0.05]` | The cutoff for p-values adjusted for testing many candidates. A candidate's adjusted value must be below it. |
| `common or threshold [1.2]` | The odds-ratio cutoff, greater than 1. An increase requires an odds ratio above it; a decrease requires an odds ratio below its reciprocal. |
| `absolute difference threshold [0.005]` | The minimum change in the mean fraction of reads carrying the tested alternate base, alongside the odds-ratio cutoff. Enter a fraction: `0.005` is half a percentage point. |
| `background max fraction [0.01]` | Press Enter for this walkthrough. No background cohort was selected, so this setting is unused. |

The first pass checks the paths, assignments, selectors, and settings without
reading every FASTQ. Review the displayed interpretation, then paste the exact
creation command printed by EMRYS. You do not answer the questions again or
edit the generated command. Creation hashes each FASTQ once, checks reference
and region compatibility, and rejects any input whose filesystem identity
changes before publication completes. Large inputs can take several minutes.
If setup is interrupted, preserve the partial Project and printed diagnostic;
do not delete it to retry the same name.

After `Project ready:`, enter the new Project and validate it:

```bash
export EMRYS_PROJECT_ROOT="$(pwd -P)/my-study"
cd "$EMRYS_PROJECT_ROOT"
emrys validate
```

Continue only after `Project validation: PASS`. Setup references the original
FASTQs and references rather than copying them. The Project owns the generated
`samples.tsv` and `partitions.tsv` beside `project.yaml`.

### Prepare, run and open your study's reports

On the head node, prepare this Project. To reuse another Project's managed tools,
first follow [sealed runtime reuse](docs/operations/RUNBOOK.md#reuse-a-sealed-managed-runtime)
before this Project has an inventory. That optional operation permanently
disables managed repair of the donor; this Project still needs its own checks.

```bash
emrys doctor --repair
```

Review the plan, answer `y`, and wait for `EMRYS is ready.` Doctor prepares the
managed tools and coordinates the compute and head-node storage checks. The
Viking settings were selected during initialization; no scheduler or storage
configuration needs to be written by hand. If a check fails, stop and retain
the diagnostic and log path instead of deleting state or changing resources.

Submit the study once, reviewing the summary and answering `y`:

```bash
emrys run
```

Review the requested hosts, exclusivity, CPUs, time, and memory, followed by
workflow and stage limits. A CPU reservation can exceed the workflow's CPU
ceiling; it does not guarantee that every CPU will be used. Site-default memory
and scheduler-selected hosts remain unknown until allocation. Doctor shows the
same requested placement when it plans compute qualification. If the requested
settings are unsuitable, decline submission and select an appropriate profile;
do not lower a stage allowance merely to make a plan pass.

Use the same explicit profile with Doctor and the later submission. For example,
if your Project already has `runtime/profiles/cohort.yaml`, run
`emrys doctor --profile cohort --repair`, then `emrys run --profile cohort`.
An absolute profile path is also accepted. Omission selects the Project default;
an invalid explicit selection stops with its diagnostic. Each invocation
reviews its current profile, so retain the selected file unchanged between
qualification and submission.

To create that named profile without editing YAML, use
`emrys profile create cohort --site viking` with your explicit allocation and
workflow options, review its output, then repeat with `--execute`. Follow the
[profile creation guide](configs/README.md#create-a-named-profile-without-writing-yaml)
for the complete options and an illustrative example. Initial fixture settings
are not a measured full-cohort preset.

Keep the printed job number and log paths. From the same Project on the head
node, check progress with:

```bash
emrys inspect
```

A queued job has not created its Run yet. Keep the retained submission request
shown by inspection; an absent Run does not authorize another submission. Once
the Run appears, repeat inspection until the four completion lines shown in
step 4 appear. Inspection prints both
report paths. Copy this Run's complete `results` directory to your computer
and open its Scientific and Evidence reports using the instructions in step 5.

Your study need not produce the synthetic fixture's candidate counts. Review
its results with the study's scientist or analyst. Keep the original Project,
inputs, runtime, complete Run and logs at their original locations so the work
remains inspectable and recoverable.

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

For your own study, replace the final Project `cd` line with
`cd "$EMRYS_PROJECTS_ROOT/my-study"`. For an existing Project elsewhere, use
`cd "/full/path/to/existing-project"` instead; keep it at its original location.
Reconnecting does not require reinstalling EMRYS, recreating the Project or
resubmitting work. From another directory, select it explicitly with
`emrys inspect --project "/full/path/to/existing-project/project.yaml"`.

## Further help

This guide contains the complete Viking setup and study workflow. If a step
fails, [troubleshooting](docs/operations/TROUBLESHOOTING.md) explains common
errors and supported recovery. The [advanced runbook](docs/operations/RUNBOOK.md)
covers other installation environments, administrator setup and advanced
execution options; it is not required for this walkthrough.
