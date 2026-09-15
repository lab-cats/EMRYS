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

This guide creates separate `EMRYS` and `emrys-smoke` folders in your Viking
home. Both names must be unused; do not create the folders yourself. `EMRYS`
holds the installed software and `emrys-smoke` holds the study. Keep study data
outside the software checkout and on storage that will remain available.

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

Create the supplied Project with the built-in Viking settings:

```bash
cd "$HOME"
export EMRYS_PROJECT_ROOT="$(pwd -P)/emrys-smoke"
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

Doctor explains the setup it will perform. Answer `y` to begin. **Allow roughly
5–15 minutes for first setup; downloads, compilation and queue waits can make
it longer.** The progress display names the current stage and shows elapsed
time. Complete installation output is retained at the printed log location.
For optional detail while setup runs, see
[watching the installation log](docs/operations/TROUBLESHOOTING.md#watching-doctors-installation-log).

Doctor installs the tools on the head node, submits the required compute-node
checks, and confirms that the study's storage works across both nodes. Keep
this command running until it reports `EMRYS is ready.` All of the scheduler
and storage setup is handled by EMRYS.

On a fresh Project, Doctor may initially mark Runtime and Storage as `FAIL`
because they have not been prepared yet. The repair that follows is intended
to resolve those findings. Downloads and R-package compilation take most of
the first setup; a later stage may wait for Slurm to start its checks.

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

The Run becomes available when Slurm starts the job; a queued submission has
not created it yet. An inspection finding no Run immediately after submission
does not mean you should submit again. Wait and repeat `emrys inspect`; it
does not start or change work. Completion is confirmed by all four lines:

```text
Run integrity: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting: complete
```

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
- **Regions and analysis settings:** an existing file of nonoverlapping regions,
  STAR index parameters appropriate to the reads and reference, the control and
  treatment labels, the nucleotide change to test, and the study's thresholds.
  The example values offered during setup are suggestions, not validated
  settings for every study.

Strandedness must be `forward`, `reverse`, `unstranded`, or `unknown`. Use the
library preparation information; `unknown` records that you do not know, and
does not turn a stranded library into an unstranded one. It is distinct from
the later mechanical `FWD_like` and `REV_like` alignment labels.

The regions file must use the same chromosome or contig names as the FASTA.
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

### Create the input lists

The helper below writes two **manifests**: `samples.tsv` lists libraries and
their assignments; `partitions.tsv` identifies the regions file. These are
ordinary text tables with tab-separated columns.

Replace the paths and example library names with your own. This route expects
each library's filenames to end in `_R1.fastq.gz` and `_R2.fastq.gz`; `.fastq`,
`.fq`, and `.fq.gz` also work. R1 and R2 must use the same compression. Each
`--sample` line gives, in order, the sample ID, condition, pairing group and
strandedness. Add both FASTQ paths and a matching assignment for every further
library. Replace `unknown` when the library's strandedness is known.

Choose a new manifest directory beneath an existing writable parent; do not
create that final directory yourself. The input FASTQs and regions file must
already exist.

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

Review the resulting `samples.tsv` and `partitions.tsv` with your study
assignments before continuing. A successful file check cannot establish that
the pairing or biological labels are correct.

### Answer the scientific setup questions once

Set the actual reference paths, then enter the existing durable directory
where your new `my-study` Project should be created. Its `my-study` child must
not exist. This directory must be outside the EMRYS source checkout.

```bash
EMRYS_REFERENCE_FASTA=/absolute/path/to/reference.fa
EMRYS_REFERENCE_GTF=/absolute/path/to/genes.gtf
cd /absolute/durable/path
emrys init my-study --site viking \
  --sample-manifest "$EMRYS_MANIFEST_ROOT/samples.tsv" \
  --partition-manifest "$EMRYS_MANIFEST_ROOT/partitions.tsv" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" \
  --reference-gtf "$EMRYS_REFERENCE_GTF" --execute
```

The input paths are already supplied, so the terminal asks the following
scientific questions. Type each agreed value and press Enter. Where a value
appears in brackets, Enter accepts it. This command validates the answers and
creates the Project; you do not need to repeat the questionnaire.

| Prompt | What to enter |
| --- | --- |
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

After `Project ready:`, enter the new Project and validate it:

```bash
export EMRYS_PROJECT_ROOT="$(pwd -P)/my-study"
cd "$EMRYS_PROJECT_ROOT"
emrys validate
```

Continue only after `Project validation: PASS`. Setup references the original
inputs rather than copying them into the Project.

### Prepare, run and open your study's reports

On the head node, prepare this Project:

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

Keep the printed job number and log paths. From the same Project on the head
node, check progress with:

```bash
emrys inspect
```

A queued job has not created its Run yet. Once it starts, repeat inspection
until the four completion lines shown in step 4 appear. Inspection prints both
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
cd "$HOME/EMRYS"
export EMRYS_SOURCE_ROOT="$(pwd -P)"
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
cd "$HOME/emrys-smoke"
export EMRYS_PROJECT_ROOT="$(pwd -P)"
emrys inspect
```

For your own study, replace the entire `cd "$HOME/emrys-smoke"` line with
`cd "/full/path/to/my-study"`, using the actual Project location chosen in
step 7. Reconnecting does not require reinstalling EMRYS, recreating the
Project or resubmitting work.

## Further help

This guide contains the complete Viking setup and study workflow. If a step
fails, [troubleshooting](docs/operations/TROUBLESHOOTING.md) explains common
errors and supported recovery. The [advanced runbook](docs/operations/RUNBOOK.md)
covers other installation environments, administrator setup and advanced
execution options; it is not required for this walkthrough.
