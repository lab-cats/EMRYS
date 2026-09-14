# EMRYS quickstart: synthetic Project to Results

This guide takes a CSU Viking user from a fresh installation to two reports
for a small supplied study. **Run every command on the Viking head node.**
EMRYS submits compute work through Slurm and supplies the Viking settings.

The exercise contains four libraries of 130 read pairs and a small reference.
It checks that the software runs; its candidates are not biological findings.

## Before you begin

Log in to Viking using your usual CSU connection. Keep that terminal open
throughout the guide. You need your normal home-directory access and permission
to download software. The directories `EMRYS` and `emrys-smoke` in your home
must be unused; this walkthrough creates them.

Paste each block in order. Stop at an error and retain its output and any
printed log path. Do not delete partial setup or results to retry.

## 1. Install EMRYS

Install the two tools that manage EMRYS's software environment:

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

The final command prints the installed EMRYS version. Keep this checkout
unchanged for the exercise; EMRYS records the implementation used for a Run.

## 2. Create the supplied study

A **Project** holds the study's input definitions, software environment and
results. Create the supplied Project with the built-in Viking settings:

```bash
cd "$HOME"
export EMRYS_PROJECT_ROOT="$(pwd -P)/emrys-smoke"
emrys init synthetic --site viking --output-dir "$EMRYS_PROJECT_ROOT" --execute
cd "$EMRYS_PROJECT_ROOT"
emrys validate
```

Continue after `Project validation: PASS`. The reads, reference and scientific
settings are supplied; there is no configuration file to edit.

## 3. Prepare the scientific tools

```bash
emrys doctor --repair
```

Doctor explains the setup it will perform. Answer `y` to begin. **Allow roughly
5–15 minutes for first setup; downloads, compilation and queue waits can make
it longer.** The progress display names the current stage and shows elapsed
time. Complete installation output is retained at the printed log location.

Doctor installs the tools on the head node, submits the required compute-node
checks, and confirms that the study's storage works across both nodes. Keep
this command running until it reports `EMRYS is ready.` All of the scheduler
and storage setup is handled by EMRYS.

## 4. Run the study

```bash
emrys run
```

Review the short submission summary and answer `y`. Slurm will run the Analysis
and generate both reports on a compute node. EMRYS prints the job number and
log locations. Submit once and keep the Project and its inputs in place.

Check the Run from the head node:

```bash
emrys inspect
```

The Run becomes available when Slurm starts the job; a queued submission has
not created it yet. Repeat this inspection while the job runs. Completion is
confirmed by all four lines:

```text
Run integrity: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting: complete
```

A **Run** records the fixed scientific plan. The **Results** are its data and
reports. Keep the original Project, inputs, runtime, logs and complete Run so
the computation remains inspectable. An unsuccessful inspection prints the
problem and the next supported action; retain that output before attempting
recovery.

## 5. Open the reports

Inspection prints the report paths. In your usual CSU file-transfer application,
copy the Run's complete `results` directory to your computer. Keep its folders
together so links to tables and other report files continue to work.

Inside the copied directory, open these two HTML files in your web browser:

```text
reports/<RUN_ID>/<RUN_ID>.scientific_report.html
reports/<RUN_ID>/<RUN_ID>.evidence_report.html
```

The **Scientific report** presents the candidates. The **Evidence report**
explains how the data was generated and which checks passed. The supplied
study should produce three Step 09 candidate rows, with one significant row.
`FWD_like` and `REV_like` are alignment groups, not biological strand labels.

This completes the synthetic walkthrough. It demonstrates this particular
software, input and execution path; it does not establish biological validity
or readiness for every dataset. Instructions for your own data, recovery and
other environments are in the [runbook](docs/operations/RUNBOOK.md).
