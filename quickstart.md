# EMRYS quickstart: Viking data to Results

This guide takes a first-time CSU Viking user from installation to one complete
EV/PUM1 analysis. **Run every command on the Viking head node.** EMRYS supplies
the Viking settings, prepares the scientific tools and submits compute work
through Slurm.

A **Project** is the folder for one study's inputs, software environment and
results. An **Analysis** selects its samples and scientific settings; this guide
uses the name `primary`. A **Run** is the fixed plan EMRYS executes. Its
**Results** contain the generated data and two HTML reports.

The fastest route is the numbered path below. A separate
[optional smoke test](#optional-smoke-test) can check the installation and
Viking execution with tiny made-up data first, but it is not required.

## Before you begin

Log in to Viking using your usual CSU connection. A terminal on your laptop
alone is not a Viking terminal. Keep the Viking terminal open during setup.

You need:

- your normal writable Viking home directory and permission to download software;
- the delivered six paired EV/PUM1 FASTQs;
- the delivered reference FASTA and its matching GTF annotation.

The FASTA contains the reference sequences. The GTF describes features on those
same sequences. EMRYS does not generate or download either file for real data.
If one is missing, stop and obtain the matching pair from the data provider or
the reference source. Do not substitute an unrelated FASTA or GTF. The FASTA
directory must be writable so EMRYS can create or verify its `.fai` and `.dict`
sidecars.

Stop at an error and retain its output and any printed log path. Do not delete
partial setup, locks, logs or results to retry. `$HOME` below means your Viking
home directory. A backslash (`\`) continues the same shell command on the next
line; keep it as the final character when pasting a block.

## 1. Install EMRYS

uv manages Python; Pixi supplies the scientific tools and R; Doctor uses renv
for the required R packages. These installer commands belong together and may
update your shell startup files:

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
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
```

Confirm that the command is available:

```bash
emrys --version
```

Continue only after it prints an EMRYS version. Leave this checkout unchanged;
EMRYS records the implementation used for a Run.

Save the repeated Viking choices:

```bash
emrys setup --execute
```

Press Enter for the displayed `Projects` home and `viking` site. Leave the
optional log root empty so each Project keeps its own application logs. Success
creates a repository-root `.env`. If setup reports an error, stop there.

New Projects created with the saved `viking` site use these supplied placement
values; you do not enter them during guided initialization:

| Setting | Supplied value |
| --- | --- |
| Account | `viking-users` |
| Partition | `long` |
| QoS | `normal` |
| Node | One scheduler-selected exclusive node |
| CPU and memory | All CPUs and all memory on that node |
| Time limit | 12 hours |
| Scratch space | A private directory under `/tmp` |

These are requested limits, not a performance measurement or a promise that a
particular Run will finish within them.

## 2. Gather the study inputs and scientific choices

Keep the delivered FASTQs, FASTA and GTF at their existing absolute Viking
paths. FASTQ names must end in `_R1`/`_R2` or `_1`/`_2`, followed by `.fastq`,
`.fq`, or either extension plus `.gz`.

If the data provider supplied checksums, retain them with the delivery records.
This guided path does not ask you to enter them. Project creation records its
own hashes of the FASTQ bytes it admits; those hashes do not establish the
files' external provenance.

This guide uses the following delivered EV/PUM1 assignments:

| Sample | Condition | Pairing group | Strandedness |
| --- | --- | --- | --- |
| `ABE_EV_2` | `EV` | `2` | `reverse` |
| `ABE_PUM1_2` | `PUM1` | `2` | `reverse` |
| `ABE_EV_3` | `EV` | `3` | `reverse` |
| `ABE_PUM1_3` | `PUM1` | `3` | `reverse` |
| `ABE_EV4` | `EV` | `4` | `reverse` |
| `ABE_PUM1_4` | `PUM1` | `4` | `reverse` |

The known analysis values are supplied in the next step. Only the filesystem
locations depend on your delivery.

## 3. Create the Project

Enter the Projects directory supplied by the repository:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects"
```

The next command starts a questionnaire and previews the Project. It does not
create the Project on this first pass:

```bash
emrys init pum1-study
```

Enter the absolute path to the reference FASTA, then the absolute path to its
matching GTF. EMRYS next asks for the absolute FASTQ directory. Confirm that all
six pairs were detected and enter the condition, pairing group and strandedness
from the table in step 2.

At `optional regions file`, press Enter. This study uses reference sequence
names directly rather than a separate BED- or VCF-like regions file. At the
following prompt, whose label includes the FASTA filename, paste this complete
space-separated list:

```text
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 X Y MT
```

Immediately before the prompt, EMRYS prints the number of accepted FASTA names
and a bounded list taken from the first words after `>` in its headers. The
entered names are checked immediately and Project creation rechecks them. If the
delivery uses different names, stop and confirm the intended selectors rather
than guessing.

STAR index settings are no longer questionnaire prompts. Preview derives
`genomeSAindexNbases` from the admitted reference length and should show `14` for
this delivery. It labels `sjdbOverhang` and `genomeChrBinNbits` automatic until
creation, when EMRYS validates every FASTQ record during the one hashing pass and
uses the maximum read length with the admitted reference summary. For this known
150-base delivery, the creation report should show `sjdbOverhang=149`,
`genomeSAindexNbases=14`, and `genomeChrBinNbits=18`.
After the partitions are selected, use these remaining scientific values:

| Prompt | Enter |
| --- | --- |
| `control condition` | `EV` |
| `treatment condition` | `PUM1` |
| `target change` | `A>G` |
| `min sample dp (Press ENTER for 1)` | Press Enter |
| `mean dp threshold (Press ENTER for 50)` | Press Enter |
| `fdr threshold (Press ENTER for 0.05)` | Press Enter |
| `common or threshold (Press ENTER for 1.2)` | Press Enter |
| `absolute difference threshold (Press ENTER for 0.005)` | Press Enter |
| `background max fraction (Press ENTER for 0.01)` | Press Enter; it is unused because no background cohort is selected |

The preview ends with `Preview complete; Project not created.` It then prints
one long command under `Next action`. Review the interpretation immediately
above it, then copy and run that entire generated command. The command carries
the explicit answers forward while leaving the automatic STAR flags omitted;
creation freshly derives them, hashes each FASTQ once, checks the reference and
selectors, and creates the Project without another questionnaire.

Do not type another command from this guide until the generated command ends
with `Project ready:` and the path to `project.yaml`. If it stops instead, keep
the partial Project and the printed diagnostic.

## 4. Validate the Project

Enter the newly created Project:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects/pum1-study"
```

Check its inputs and definitions:

```bash
emrys validate
```

Continue only after `Project validation: PASS`. Validation does not run the
analysis or modify the Project.

## 5. Prepare the scientific tools and storage

If you skipped the [optional smoke test](#optional-smoke-test), continue to
Doctor below. If you completed it, do not run Doctor yet: first preview the
prepared tools for reuse in this Project:

```bash
emrys runtime discover --from-project "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke"
```

`Runtime discovery: READY` means the source generation is compatible. Review
the preview, then answer `y` at `Admit this runtime inventory? [y/N]`. EMRYS
reuses that in-memory inspection and performs focused freshness checks before
writing. Press Enter or answer `n` to leave the Project unchanged. Advanced
noninteractive automation may add `--execute` to the same command.

Continue after `Runtime inventory admitted:`. The reuse command installs
nothing. If you skipped the smoke test, there is no source Project to select
and no runtime-discovery command to run.

Now let Doctor prepare or verify this Project, its storage and the intended
compute placement:

```bash
emrys doctor --repair
```

Doctor first shows a no-write plan. Answer `y` once to approve it. First setup
normally takes 5–25 minutes; Slurm queue time is separate and may extend the
wait. A selected smoke runtime does not reinstall passing packages. Doctor
creates a new generation if the shared owner later needs repair; it never
changes the sealed generation already selected here.

Continue only after the distinct `EMRYS is ready.` message. If Doctor reports a
blocker, including a saved-site/profile mismatch, stop and follow its exact
remediation before running or submitting the Project.

## 6. Submit and watch the Run

Preview the Run and its Slurm submission:

```bash
emrys run
```

Review the short summary and answer `y` once. EMRYS prints `JOB_ID`, `JOB_NAME`
and log paths, then says the job was submitted and completion is not yet
verified. The head-node prompt returns while Slurm runs. Submit once.

Open the dashboard from the Project:

```bash
emrys watch
```

EMRYS automatically selects a sole retained submission or Run. If several are
plausible, choose the intended one from the picker. Press `r` to recheck the
fixed selection and its evidence; press `q` to leave. Leaving the dashboard
does not stop the job.

The evidence/log view starts at the newest retained line and follows new text.
Use `k` or Up to move back, which visibly pauses following; press `G` to return
to the bottom. Counts such as `99k`/`99j` move several lines. Type `/pattern`
and Enter to search the retained tail, then `n`/`N` for the next/previous match.
Its line numbers are relative to the retained tail rather than the whole file.

A queued job may not have created its Run yet. **No Run shown is not a reason to
submit again.** Keep the job number and request record, wait and watch again.

After the dashboard announces `Run complete`, leave it and inspect the admitted
Run evidence:

```bash
emrys inspect
```

Completion requires the distinct `Run complete` message and these four values:

```text
Run admission: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting admission: complete
```

If inspection prints a blocker or a different state, follow its `Next supported
action` rather than submitting again.

## 7. Copy and open the reports

`emrys inspect` prints the verified report paths. In your usual CSU file-transfer
application, copy the Run's complete `results` directory to your computer. Keep
its folders together so report links continue to work. Open:

```text
reports/<RUN_ID>/<RUN_ID>.scientific_report.html
reports/<RUN_ID>/<RUN_ID>.evidence_report.html
```

The Scientific report presents CMH-ranked candidates. The Evidence report
explains how the data was generated and which checks passed. `FWD_like` and
`REV_like` are mechanical alignment labels, not biological strand claims. The
Results are computational candidates, not validated editing sites.

Keep the original Project, inputs, runtime, logs and complete Run on Viking so
the computation remains inspectable and recoverable.

## If execution or reporting did not complete

Read the static state again:

```bash
emrys inspect
```

If work may still be running or another host's ownership is unverified, wait and
inspect again. If inspection offers recovery, preview it:

```bash
emrys resume
```

Review the plan and answer `y` only for the selected Run. If Scientific Results
are complete and reporting is the only remaining work, preview reporting:

```bash
emrys report
```

When the preview is correct, execute it:

```bash
emrys report --execute
```

If inspection remains blocked, preserve its output, logs, locks, partial files
and backups. The [recovery guide](docs/operations/TROUBLESHOOTING.md#run-and-reporting-state)
explains each supported state.

## Optional smoke test

The smoke test uses tiny made-up reads, its own reference and supplied settings.
It can catch installation, tool-preparation and Viking execution problems before
you use the real study. It adds Doctor setup, queue and execution time and does
not prove that the real dataset will fit the same resources or that its
scientific choices are correct. Skip this section for the fastest route.

From the supplied Projects directory, create the example Project:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects"
```

```bash
emrys init synthetic --output-dir "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke" --execute
```

Success prints `Synthetic Project: ready` followed by `Project:` and its path.
Enter it:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke"
```

Validate the supplied smoke inputs. Continue only after `Project validation:
PASS`:

```bash
emrys validate
```

Prepare and verify its scientific tools. Continue only after `EMRYS is ready.`:

```bash
emrys doctor --repair
```

Preview and submit the smoke Run once:

```bash
emrys run
```

Watch that submitted Run; leaving with `q` does not stop it:

```bash
emrys watch
```

After the dashboard announces completion, verify the admitted outcome:

```bash
emrys inspect
```

The supplied smoke study should produce three Step 09 candidate rows, with one
significant row. Its successful completion is an environment/site confidence
check, not biological validation. Return to step 2 for the EV/PUM1 Project; step
5 explains how to reuse the smoke Project's prepared tools.

## Returning to the Project in a new terminal

Reconnect to the Viking head node and restore the installed command:

```bash
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
cd "$HOME/EMRYS" &&
export EMRYS_SOURCE_ROOT="$(pwd -P)" &&
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate" &&
cd "$EMRYS_SOURCE_ROOT/Projects/pum1-study"
```

Then inspect the existing Project:

```bash
emrys inspect
```

For the optional smoke Project, use
`cd "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke"` instead. Reconnecting does not
require reinstalling EMRYS, recreating the Project or resubmitting work.

## Further help

If a step fails, [troubleshooting](docs/operations/TROUBLESHOOTING.md) explains
common errors and supported recovery. The
[runbook](docs/operations/RUNBOOK.md) covers advanced installation, existing
Projects, runtime repair and execution options.
