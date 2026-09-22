# EMRYS quickstart: Viking data to Results

Run this EV/PUM1 study from the **Viking head node**. EMRYS prepares the tools
and submits the analysis to Slurm. A **Project** holds the study; each **Run**
keeps its fixed analysis plan, results and execution records.

## Before you begin

You need a writable Viking home, permission to download software, and:

- the six paired EV/PUM1 FASTQ libraries listed below;
- the delivered reference FASTA and its matching GTF annotation.

The FASTA contains reference sequences; the GTF describes their features.
EMRYS does not supply these real-study files. If either is missing, obtain the
matching pair before continuing. The FASTA directory must be writable for
reference sidecars. Keep any provider checksums with the delivery records.

Stop at an error and keep its output and log path. Do not delete partial setup,
locks or results to retry. `$HOME` means your Viking home; a final backslash
continues a command on the next line.

## 1. Install EMRYS

Install the tools that manage Python and the scientific software. These commands
may update your shell startup files:

```bash
set -o pipefail &&
curl -LsSf https://astral.sh/uv/0.12.3/install.sh | sh &&
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.75.0 bash &&
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH" &&
uv --version &&
pixi --version
```

Download EMRYS and activate its locked Python environment:

```bash
cd "$HOME" &&
git clone https://github.com/lab-cats/EMRYS.git &&
cd EMRYS &&
export EMRYS_SOURCE_ROOT="$(pwd -P)" &&
uv sync --locked --no-default-groups --group workflow --python 3.14 &&
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
```

Check that EMRYS prints its version:

```bash
emrys --version
```

Keep this checkout unchanged while a Run uses it. Save the Viking choices:

```bash
emrys setup --execute
```

Press Enter for the default `Projects` home and `viking` site; leave the optional
log root empty. The commands below use those defaults. EMRYS supplies:

| Setting | Requested value |
| --- | --- |
| Account / partition / QoS | `viking-users` / `long` / `normal` |
| Node | One scheduler-selected exclusive node |
| CPU and memory | All CPUs and memory on that node |
| Maximum runtime | 12 hours |
| Batch temporary files | A private directory under `/tmp` |

These requests do not guarantee a completion time. Other temporary files follow
[their operation's storage rules](docs/operations/RUNBOOK.md#temporary-files).

You can now try the [optional smoke test](docs/operations/SMOKE_TEST.md) with
tiny made-up data. It adds setup and queue time; skip it to start the real study.

## 2. Gather the study inputs and scientific choices

Keep the FASTQs, FASTA and GTF at their existing absolute Viking paths.
FASTQ mate names must end in `_R1`/`_R2` or `_1`/`_2`, followed by `.fastq`,
`.fq`, or either extension plus `.gz`. Use these sample assignments:

| Sample | Condition | Pairing group |
| --- | --- | --- |
| `ABE_EV_2` | `EV` | `2` |
| `ABE_PUM1_2` | `PUM1` | `2` |
| `ABE_EV_3` | `EV` | `3` |
| `ABE_PUM1_3` | `PUM1` | `3` |
| `ABE_EV4` | `EV` | `4` |
| `ABE_PUM1_4` | `PUM1` | `4` |

## 3. Create the Project

From the repository root, start guided creation. EMRYS uses the Projects home
saved during setup:

```bash
emrys init pum1-study
```

Enter the FASTA path, matching GTF path and FASTQ directory. Check that all six
pairs were found. Enter `reverse` for study strandedness, then enter each
sample's condition and pairing group from the table above.

When asked, choose `y` for the EV/PUM1 whole-sequence selection. EMRYS reads
the maintained `1`–`22`, `X`, `Y` and `MT` names, checks them against your
reference, and saves them inside the Project. If a name is missing, stop and
confirm the intended reference and selection.

Choose the number beside `EV -> PUM1`, and enter `A>G` for target change.
At `Use these paired-CMH defaults?`, review and accept minimum sample depth `1`,
mean-depth threshold `50`, FDR `0.05`, common odds ratio `1.2` and absolute
difference `0.005`. This study has no background cohort.

Review the preview: all six samples should be `reverse`, the comparison should
be `EV -> PUM1`, the target should be `A>G`, and the five paired-CMH values
should match those above. Confirm that no background cohort is selected.

Once these choices are correct, answer `y` at `Create this Project? [y/N]`.
Pressing Enter or `n` leaves the Project uncreated; `--preview` offers review
only. Creation may take several minutes. Continue only after `Project ready:`
prints the path to `project.yaml`.

## 4. Validate the Project

Enter the Project:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects/pum1-study"
```

Check its inputs and definitions:

```bash
emrys validate
```

Continue only after `Project validation: PASS`.

## 5. Prepare the scientific tools and storage

Check for tools already prepared in another Project, whether or not you ran
the optional [smoke test](docs/operations/SMOKE_TEST.md):

```bash
emrys runtime discover --from-project
```

If you ran the smoke test, choose `emrys-smoke` from the numbered Projects.
Otherwise, choose a Project whose tools you want to reuse. The list shows
possible sources, not verified compatibility. Continue only after the chosen
source reports `Runtime discovery: READY`; answer `y` at
`Admit this runtime inventory? [y/N]` and wait for `Runtime inventory admitted:`.
If a source fails, run the choice again for another Project. When no prepared
Project is found or none qualifies, Doctor will prepare the tools needed here.

Verify this Project and prepare tools only if needed:

```bash
emrys doctor --repair
```

Review the plan and resource request, then answer `y`. First setup can take
5–25 minutes; Slurm queue time can extend the wait. Continue only after
`EMRYS is ready.`. A blocker must be resolved before submitting.

## 6. Submit and watch the Run

Preview the Run:

```bash
emrys run
```

Review its resource request and answer `y` once. Keep the printed job and log
paths. Submission returns your prompt while Slurm runs; it is not completion.

Watch the submitted work:

```bash
emrys watch
```

If a picker appears, choose the intended submission or Run. Press `r` to
recheck and `q` to leave; leaving does not stop the job. Use Up to scroll back
and `G` to follow the newest log lines. The
[watch guide](docs/operations/RUNBOOK.md#watch-one-fixed-selection)
has the other controls.

**A queued job may not show a Run yet. Do not submit it again.**
After watch announces `Run complete`, leave it and check:

```bash
emrys inspect
```

Continue only when inspection shows `Run complete` and:

```text
Run admission: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting admission: complete
```

Otherwise follow its `Next supported action` and the
[recovery guide](docs/operations/TROUBLESHOOTING.md#run-and-reporting-state).

## 7. Copy and open the reports

`emrys inspect` prints the verified report paths. Use your CSU file-transfer
application to copy the Run's **complete `results/` directory** to your computer,
keeping its folders together. The
[terminal transfer procedure](docs/operations/RUNBOOK.md#retrieve-reports-from-a-terminal)
also explains how to compare the copy with the original.

Open `reports/<RUN_ID>/<RUN_ID>.scientific_report.html`, then its Evidence report
link. The Scientific report presents CMH-ranked candidates; the Evidence report
explains inputs, checks and execution. These are computational candidates,
not validated editing sites. `FWD_like` and `REV_like` are mechanical labels,
not biological strand assignments.

### Where the data is

Inside the copied `results/`, use the generated IDs already present in the
folder names. Scientific filenames start with `<ANALYSIS_ID>.`; report filenames
start with `<RUN_ID>.`.

| Folder | Filename suffix | Contents |
| --- | --- | --- |
| `editing/<ANALYSIS_ID>/` | `cmh_all_sites.tsv` | All candidates, counts, test outcomes, FDR and effect estimates. |
| `editing/<ANALYSIS_ID>/` | `cmh_significant_sites.tsv` | The subset passing the configured thresholds. |
| `editing/<ANALYSIS_ID>/` | `cmh_summary.tsv` | Analysis settings, counts and input hashes. |
| `editing/<ANALYSIS_ID>/` | `mutation_spectrum.tsv`, `mutation_spectrum.pdf` | Counts by RNA-change type and their plot. |
| `editing/<ANALYSIS_ID>/` | `depth_delta.pdf` | Read-depth and between-condition difference plots. |
| `scientific_context/<ANALYSIS_ID>/` | `candidate_context.tsv` | Candidate sequences, positions and context availability. |
| `scientific_context/<ANALYSIS_ID>/` | `motif_hits.tsv` | Individual motif matches and their positions. |
| `scientific_context/<ANALYSIS_ID>/` | `sequence_logo.tsv` | Base counts and fractions used for sequence logos. |
| `scientific_context/<ANALYSIS_ID>/` | `motif_statistics.tsv` | Motif summaries and enrichment calculations. |
| `scientific_context/<ANALYSIS_ID>/` | `context_receipt.tsv` | Context inputs, settings, file hashes and software provenance. |
| `reports/<RUN_ID>/` | `scientific_report.html` | Candidate findings, figures and interpretation limits. |
| `reports/<RUN_ID>/` | `evidence_report.html` | Provenance, checks and execution history. |
| `reports/<RUN_ID>/` | `report_outputs.tsv` | Report publication record. |

TSV files are tab-separated tables. The
[analysis contract](src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md#inputs-and-six-output-transaction)
and [context contract](src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/CONTRACT.md#inputs-and-scientific-outputs)
explain their detailed meaning.

Keep the original Project, inputs, runtime, logs and **complete Run** on Viking.
Its `contract/`, `attempts/` and `products/artifact-summary/` retain the full
[execution and recovery evidence](src/emrys/orchestration/run_coordinator/CONTRACT.md#run-root-contract).
Copying reports does not replace that evidence or complete scientific review.

## If execution or reporting did not complete

Use `emrys inspect` and follow its supported action. The
[recovery guide](docs/operations/TROUBLESHOOTING.md#run-and-reporting-state)
explains when to wait, resume or generate reports. Preserve blocked state and
logs; do not create another Run to bypass a failure.

## Returning to the Project in a new terminal

Reconnect to the Viking head node and activate the installed command:

```bash
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
cd "$HOME/EMRYS" &&
export EMRYS_SOURCE_ROOT="$(pwd -P)" &&
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate" &&
cd "$EMRYS_SOURCE_ROOT/Projects/pum1-study"
```

For the smoke Project, replace the last path with
`"$EMRYS_SOURCE_ROOT/Projects/emrys-smoke"`. Then inspect existing work:

```bash
emrys inspect
```

Reconnecting does not require installation, Project creation or resubmission.
The [Runbook](docs/operations/RUNBOOK.md) covers advanced operation.
