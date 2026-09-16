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

This guide keeps software in `$HOME/EMRYS` and studies beneath
`$HOME/emrys-projects`. The software directory and each new Project child
(`emrys-smoke` or `my-study`) must be absent; do not create them yourself.
The Projects parent may already exist. Use durable storage outside the software
checkout. Existing Projects keep their original locations and references;
these instructions do not require moving them.

**Steps 1–5 are ready to paste unchanged.** Step 7 uses your own study files;
replace the marked example paths and sample details before running it. Paste
blocks in order. Stop at an error and retain its output and any printed log
path. Do not delete partial setup or results to retry.
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

### Choose a Projects home

Use this Projects home on Viking:

```bash
mkdir -p "$HOME/emrys-projects" &&
cd "$HOME/emrys-projects" &&
export EMRYS_PROJECTS_ROOT="$(pwd -P)"
```

The variable records the physical path from `pwd -P`. Keep this location outside
the software checkout and accessible from the compute nodes. Initialization
requires a real existing parent and an absent Project child, and refuses
symlink aliases supplied as destination paths. Stop if entering the parent
fails; do not continue from the previous directory.

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

The saved Viking smoke-test settings are account `viking-users`, partition
`long`, QoS `normal`, four CPUs, eight hours, site-default memory and private
temporary storage under `/tmp`. The allocation is not exclusive and Slurm
chooses the node. The `--site viking` choice supplies these settings;
you do not enter them or configure Slurm. They are smoke-test settings,
not a tested budget for a full PUM1 study.

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

Review the submission summary and answer `y` once. Slurm runs the Analysis and
both reports on a compute node. Save the printed job number and log paths. The
head-node prompt returns while Slurm continues; you may disconnect without
stopping the submitted Run.

Check the Run from the head node:

```bash
emrys inspect
```

Inspection shows the retained submission and any available Run. A queued job
may not have created its Run yet. **No Run shown is not a reason to submit
again.** Keep the job number and request record, wait, and inspect again.
Inspection does not start or change work. If the job's state stays unclear,
use the [exact-request check](docs/operations/RUNBOOK.md#retain-a-submission-before-its-run-exists)
before deciding what to do.
Completion is confirmed by all four lines:

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

Stay on the **Viking head node**, with the EMRYS Python environment from step 1
activated. Use a new Project so the supplied study and its results remain intact.
You can reuse the installed EMRYS command; each Project has its own runtime
inventory and preparation records.

### Gather the study inputs and scientific choices

Before using your own data, have its files and scientific assignments ready:

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

Use the library preparation information for strandedness; `unknown` records
missing information and is not a claim that the library is unstranded. Regions
must use the same chromosome names as the FASTA. The
[region file formats](configs/README.md#partition-manifest) explain coordinates
if you are creating a new regions file.

EMRYS does not download study data or decide experimental pairing. Keep the
input files, their checksums and their declared locations for the life of the
Run. Success with the tiny supplied study does not establish that a full
dataset will fit the same allocation.

### Create the input lists

The helper below writes two **manifests**: `samples.tsv` lists libraries and
their assignments; `partitions.tsv` declares the selected regions. These are
ordinary text tables with tab-separated columns.

Replace the paths and example library names with your own. The helper recognizes
R1/R2 filenames ending in `_R1`/`_R2` or `_1`/`_2`, with `.fastq` or `.fq` and
optional `.gz`. Each `--sample` line gives the sample ID, condition, pairing
group and strandedness in that order. Add both FASTQs and one assignment for
every further library. Replace `unknown` when strandedness is known.

The block below is a **template, not a command to paste unchanged**. Replace
the `REPLACE_WITH_...` paths, example FASTQ names, sample assignments and
regions-file choice with your study's existing files and agreed design before
running it. Choose a new manifest directory beneath an existing writable
parent; do not create that final directory yourself. Current EMRYS creates
these manifests outside the Project. The input FASTQs and regions file must
already exist.

```bash
EMRYS_READS="/REPLACE_WITH_READS_DIRECTORY"
EMRYS_REGIONS="/REPLACE_WITH_REGIONS_FILE.bed"
EMRYS_MANIFEST_ROOT="/REPLACE_WITH_DURABLE_PARENT/my-study-manifests"
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

If you have explicit chromosome or interval selectors instead of a regions
file, replace `--regions-file study "$EMRYS_REGIONS"` with `--region
PARTITION_ID SELECTOR` for each region. This does not automatically select the
whole genome. See the [partition manifest guide](configs/README.md#partition-manifest)
for selector formats; Project creation checks them against the reference.

Review the resulting `samples.tsv` and `partitions.tsv` with your study
assignments before continuing. A successful file check cannot establish that
the pairing or biological labels are correct.

### Answer the scientific setup questions once

Replace both `REPLACE_WITH_...` paths below with your existing reference and
annotation files. Set the actual reference paths, then enter the durable directory
where your new `my-study` Project should be created. Its `my-study` child must
not exist. Use the [Projects home](#choose-a-projects-home) selected above.
The ordinary `init NAME` command creates beneath the current directory;
the synthetic route's `--output-dir` selects an absolute destination instead.

```bash
EMRYS_REFERENCE_FASTA="/REPLACE_WITH_REFERENCE_FASTA.fa"
EMRYS_REFERENCE_GTF="/REPLACE_WITH_REFERENCE_GTF.gtf"
cd "$EMRYS_PROJECTS_ROOT" &&
emrys init my-study --site viking \
  --sample-manifest "$EMRYS_MANIFEST_ROOT/samples.tsv" \
  --partition-manifest "$EMRYS_MANIFEST_ROOT/partitions.tsv" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" \
  --reference-gtf "$EMRYS_REFERENCE_GTF"
```

The input paths are already supplied, so the terminal asks the following
scientific questions. Type each agreed value and press Enter. Where a value
appears in brackets, Enter accepts it. This command validates the answers and
prints a review without creating the Project. Review the explicit sample/mate
assignments, biological pairing groups, strandedness, reference and region
identities, scientific settings, and selected site. Then copy the printed
creation command. It carries every answer into the same Python environment;
you do not need to repeat the questionnaire. It also rechecks the inputs,
because a preview does not freeze external files.

Preparation reads and hashes the complete declared inputs and checks reference
and region compatibility. Large inputs can take several minutes. The terminal
shows the current phase and elapsed time, then rechecks the published Project
before printing `Project ready:`. Elapsed time is not a completion estimate.
If interrupted, retain any published or partial Project directory and the
diagnostic; do not delete it to retry the same name.

| Prompt | What to enter |
| --- | --- |
| `sjdb overhang` | Study-specific STAR setting for read length; the Viking smoke preset does not select it for your data. |
| `genome sa index nbases` | Study-specific STAR index setting for reference size; the Viking smoke preset does not select it for your data. |
| `control condition` | The exact control label in your sample assignments; `control` in the example above. |
| `treatment condition` | The exact treatment label; `treatment` in the example above. |
| `target change` | Two different bases separated by `>`, such as `A>G`, according to the study question. |
| `min sample dp [1]` | Minimum usable read depth in every paired sample for a site to be tested. This cutoff is inclusive. |
| `mean dp threshold [50]` | The candidate's mean depth across paired control and treatment samples must be greater than this value. |
| `fdr threshold [0.05]` | The cutoff for p-values adjusted for testing many candidates. A candidate's adjusted value must be below it. |
| `common or threshold [1.2]` | The odds-ratio cutoff, greater than 1. An increase requires an odds ratio above it; a decrease requires an odds ratio below its reciprocal. |
| `absolute difference threshold [0.005]` | The minimum change in the mean fraction of reads carrying the tested alternate base, alongside the odds-ratio cutoff. Enter a fraction: `0.005` is half a percentage point. |
| `background max fraction [0.01]` | Press Enter for this walkthrough. No background cohort was selected, so this setting is unused. |

After `Project ready:`, enter the new Project and validate it:

```bash
export EMRYS_PROJECT_ROOT="$(pwd -P)/my-study"
cd "$EMRYS_PROJECT_ROOT" &&
emrys validate
```

Continue only after `Project validation: PASS`. Setup references the original
inputs rather than copying them into the Project.

### Prepare, run and open your study's reports

On the head node, prepare this Project. To reuse another Project's managed tools,
first follow [sealed runtime reuse](docs/operations/RUNBOOK.md#reuse-a-sealed-managed-runtime)
before this Project has an inventory. Current EMRYS does not select the smoke
Project's tools automatically. Reuse prevents later EMRYS-managed repair of
the smoke Project's shared installation, and this Project still needs its own
readiness checks. Do not apply reuse after its runtime has already been prepared.

Before Doctor, check the study's resource needs. The saved four-CPU,
eight-hour settings are for the smoke test; they are not a tested PUM1 cohort
budget. If unsuitable, select an existing named profile or use
[profile creation](configs/README.md#create-a-named-profile-without-writing-yaml)
with reviewed values. Use the same selected profile for Doctor and Run. For a
profile named `cohort`, replace the two default commands below with
`emrys doctor --profile cohort --repair` and `emrys run --profile cohort`.
Do not lower a stage allowance merely to make a plan pass.

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

Review Doctor's allocation and workflow limits before confirming. Review the
same limits in Run's submission summary; if they are unsuitable, decline
submission and revise the selection before another readiness check.

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
cd "$HOME/emrys-projects" &&
export EMRYS_PROJECTS_ROOT="$(pwd -P)" &&
cd "$EMRYS_PROJECTS_ROOT/emrys-smoke" &&
export EMRYS_PROJECT_ROOT="$(pwd -P)" &&
emrys inspect
```

If you chose a different Projects parent, replace `$HOME/emrys-projects` with
its actual path. For your own study, replace the final Project `cd` line with
`cd "$EMRYS_PROJECTS_ROOT/my-study"`. For an existing Project elsewhere, use
`cd "/full/path/to/existing-project"` instead; keep it at its original location.
Reconnecting does not require reinstalling EMRYS, recreating the Project or
resubmitting work. From another directory, select it explicitly with
`emrys inspect --project "/full/path/to/existing-project/project.yaml"`.

## Further help

If a step fails, [troubleshooting](docs/operations/TROUBLESHOOTING.md) explains
common errors and supported recovery. The
[runbook](docs/operations/RUNBOOK.md) covers other installation environments,
existing Projects and advanced execution options.
