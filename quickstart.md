# EMRYS quickstart: synthetic Project to Results

Start here to run EMRYS for the first time and open its reports. The first
exercise supplies synthetic reads, a reference, and experimental assignments;
you do not need to find sequencing data. Afterward, use
[your own data](#7-create-a-project-for-your-own-data).

A **Project** is a directory containing your input definitions and EMRYS's
runtime and outputs. An **Analysis** selects the samples and scientific
settings. A **Run** freezes those choices; its **Results** include computational
outputs and two HTML reports. EMRYS is alpha research software. Reported
CMH-ranked candidates are not validated RNA-editing sites.

## Before you begin

Use a Bash terminal on the computer that will run EMRYS. A terminal on your
laptop is not automatically a terminal on your institution's cluster.

| You need | How to prepare |
| --- | --- |
| A suitable compute host | The managed runtime requires x86-64 Linux, kernel 4.18 or newer and glibc 2.28 or newer. The unchanged execution profile needs at least four visible CPUs. Ask your computing support team to confirm the host, memory, disk quota, and permitted wall time. |
| An execution route | On an approved standalone compute host, follow steps 1–6. On a Slurm cluster, complete steps 1–2 where site policy permits, then follow the linked Slurm setup in step 3. Never execute the workflow on a login node. |
| Bash, Git, and curl | Check `bash --version`, `git --version`, and `curl --version`. If unavailable, use your institution's supported installation route. |
| Permission and network access for setup | Python and scientific packages must be downloaded during installation/repair. Sites with restricted compute-node networking need an approved setup route; a login-node installation does not establish compute-node readiness. |
| Two writable locations | Choose an existing directory for the source checkout and a durable parent for Projects outside it. Use real absolute paths without symbolic-link aliases. `pwd -P` prints the physical path of your current directory. |

The small exercise has four libraries, each with 130 read pairs, and a
100,000-base synthetic reference. It still installs and uses the real tools.
This is not a memory or runtime estimate for your own reference and reads.

Run one command at a time, in order, and stop at an error.
Replace text such as `/absolute/path/...` before running a command. Preserve
quotation marks; a line ending in `\` continues onto the next line. Keep this
terminal open so that the variables and activated environment remain available.

## 1. Install the locked command

EMRYS uses **uv** for its Python environment and **Pixi** plus **renv** for
scientific tools and R packages. If your site supplies uv and Pixi, use those
installations. The bundled runtime requires Pixi `>=0.75.0,<0.76`; the following
versions match the managed workflow's CI setup.

If user-level installation is permitted and the tools are absent, these
[official uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Pixi installer](https://pixi.prefix.dev/latest/installation/#installer-script-options)
commands install them in your account and can update your shell startup files:

```bash
curl -LsSf https://astral.sh/uv/0.12.3/install.sh | sh
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.75.0 bash
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
uv --version
pixi --version
```

Do not use an incompatible Pixi release or update the dependency locks to make
installation proceed. Your institution can supply an equivalent approved
installation instead of running these installers.

Choose the source parent and revision. `EMRYS_REVISION` must be a full commit
ID or release tag selected by your team; copy a full commit ID from the
[repository's commit history](https://github.com/lab-cats/EMRYS/commits/master/)
if evaluating a particular development revision. Selection alone does not
establish that the revision is scientifically or institutionally qualified.
The child directory `EMRYS` must not already exist.

```bash
cd /absolute/path/to/source-parent
EMRYS_REVISION='REPLACE_WITH_FULL_COMMIT_ID_OR_TAG'
git clone https://github.com/lab-cats/EMRYS.git
cd EMRYS
git checkout --detach "$EMRYS_REVISION"
export EMRYS_SOURCE_ROOT="$(pwd -P)"
git rev-parse HEAD
uv sync --locked --no-default-groups --group workflow --python 3.14
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
emrys --help
git status --porcelain=v1 --untracked-files=all
```

uv can download Python 3.14 if needed; EMRYS requires Python 3.11 or newer.
Record the full commit ID printed above. Help must work and the final Git
command must print **nothing**: modified tracked files and nonignored untracked
files both prevent execution. Preserve unexpected files and resolve their
ownership; do not delete them just to pass this check. Keep the checkout at
this commit for the life of the exercise.

In a later terminal, restore the environment before using EMRYS:

```bash
export EMRYS_SOURCE_ROOT=/absolute/path/to/source-parent/EMRYS
source "$EMRYS_SOURCE_ROOT/.venv/bin/activate"
```

## 2. Create the synthetic Project

Choose a new child beneath an existing writable, durable parent outside the
checkout. Do not create the child yourself. This example uses `emrys-smoke`:

```bash
export EMRYS_PROJECT_ROOT=/absolute/durable/path/emrys-smoke
emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT"
```

This displays a plan and writes nothing. Check the destination, then create it:

```bash
emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT" --execute
cd "$EMRYS_PROJECT_ROOT"
export EMRYS_REFERENCE_FASTA="$EMRYS_PROJECT_ROOT/inputs/reference/reference.fa"
emrys validate
```

Continue after `Project validation: PASS`. The Project includes `project.yaml`,
sample and partition manifests, synthetic inputs, and a default execution
profile. You do not need to edit them. If creation is interrupted, preserve
the partial directory and choose a new absent destination.

## 3. Prepare the runtime and storage

**Slurm users:** follow [Slurm setup and submission](docs/operations/RUNBOOK.md#slurm-setup-and-submission)
now. That procedure obtains site settings, prepares the runtime in an approved
allocation, qualifies shared storage from compute and head nodes, and submits
one whole Run. After that job finishes, return to **step 5**. The standalone
commands below are not a login-node shortcut.

**Standalone compute-host users:** from the Project root, run:

```bash
emrys doctor --repair
```

Doctor shows its repair plan and asks for confirmation in a terminal. Review
the locations, then answer `y` to install the managed runtime and qualify the
Project and reference-sidecar storage. It may update the active checkout's
`.venv` and Project-owned runtime state and writes a maintenance log. It does
not download scientific inputs or repair result artifacts. Wait for completion;
then check again:

```bash
emrys doctor
```

Continue only when it prints `EMRYS is ready.` If setup fails, retain the
reported log and use [Project and runtime checks](docs/operations/TROUBLESHOOTING.md#project-and-runtime-checks).
Do not relock packages or repeatedly retry an unexplained failure.

If your institution supplies the scientific tools and R library, use the
[institution-provided runtime procedure](docs/operations/RUNBOOK.md#institution-provided-runtime)
instead of managed installation. That route includes both the required explicit
tool selections and storage qualification; discovery alone is insufficient.

## 4. Execute the Analysis

On the approved standalone compute host, still inside the Project:

```bash
emrys run --log-level verbose
```

The synthetic Project has one Analysis, `primary`. EMRYS shows the direct Run
plan and asks `Execute this plan? [y/N]`. Check the Project, Analysis, and
resources before answering `y`. An answer other than `y` or `yes`, or an
interruption before confirmation, starts no work. Reporting follows successful
computation automatically. Keep the terminal/job alive until the command ends.

For automation, the equivalent explicit command is
`emrys run --analysis primary --execute`. Use **one** execution form, not both.
`--no-report` deliberately skips report generation; omit it for this exercise.

Different commands have different confirmation behavior:

| Command without `--execute` | Behavior |
| --- | --- |
| `init`, `init synthetic`, `init manifests`, `runtime discover`, `report` | Plans or checks only; no publication. Project initialization may ask for missing input values. |
| `doctor --repair`, `run`, `resume` | Shows a plan and can execute after terminal confirmation. For a no-write preview, answer `n`; automation needs `--execute`. |
| `validate`, `doctor`, `inspect` | Read-only checks; no execution confirmation. |

## 5. Confirm completion and open both reports

From the Project root, after execution finishes:

```bash
emrys inspect
```

For the completed synthetic exercise, require all four lines:

```text
Run integrity: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting: complete
```

Inspection also prints **Scientific report** and **Evidence report** with their
exact HTML paths. Open the Scientific report with your browser's **Open File**
command; its sibling Evidence report explains the computation and provenance
evidence. These Run reports are HTML. The files normally live beneath:

```text
<PROJECT>/runs/<RUN_ID>/results/reports/<RUN_ID>/
    <RUN_ID>.scientific_report.html
    <RUN_ID>.evidence_report.html
```

Use the printed paths rather than typing these placeholders. On a cluster,
use your institution's file browser or approved transfer service to download
the built-in Analysis's complete `results/` directory to your workstation,
then open the two files beneath its `reports/` directory. Keep the directory
layout intact so links to the companion report and result tables work. The
provenance still identifies the original locations. Keep the authoritative
Project, inputs, runtime, and complete Run on their original storage.

The default fixture expects three Step `09` candidate rows and one significant
row. These are synthetic regression expectations, not biological truth. Use the
scientific report and its linked full result tables to examine the candidates;
`FWD_like` and `REV_like` describe mechanical alignment groups, not biological
strand. Successful completion shows that these inputs, this source commit,
runtime, storage, and execution route worked together. It does not establish
production readiness, institutional-site qualification, scientific review, or
biological validation.

## 6. If execution or reporting did not complete

Follow **Next supported action:** and the blockers printed by `emrys inspect`:

For Slurm Runs, pass `--profile slurm` (or your selected profile name) to
`resume`; the generated default still selects direct execution. The standalone
`report` command has no Slurm submission option: obtain an approved compute
shell before regenerating reports, as described in the
[runbook](docs/operations/RUNBOOK.md#inspect-and-open-reports).

| Inspection result | Next step |
| --- | --- |
| Attempt is still running | Wait for it or check the exact Slurm job. Do not start another writer. |
| Failed/interrupted computation with `Recovery available: yes` | Review `emrys resume` and confirm only the supported retry. It creates another Attempt for the same Run. |
| Scientific Results complete; reporting absent/incomplete and unblocked | Run `emrys report` to preview. If accepted, use `emrys report --execute`, then inspect again. |
| Any state is blocked, or report generation refuses retained partial files | Preserve the Run and follow [troubleshooting](docs/operations/TROUBLESHOOTING.md). Reporting failure is not a reason to rerun completed computation. |

Do not delete or rename a Run, lock, partial output, log, backup, or receipt to
make a command proceed. With multiple Runs, give `inspect`, `resume`, or
`report` the exact two-word Run name printed by EMRYS, full ID, or unique ID
prefix. Interactive selection is available; automation never assumes latest.

## 7. Create a Project for your own data

Use a **new Project**, leaving the completed synthetic exercise intact. Obtain
the following from the study's scientist/analyst before setup:

- Paired-end FASTQs and their source checksums; explicit sample IDs, conditions,
  library strandedness, and matched replicate strata. The built-in Analysis
  needs at least two strata with one control and one treatment sample each.
  Technical lanes are not automatically independent biological replicates.
- An uncompressed reference FASTA and matching GTF, with their source/release
  identities. EMRYS needs permission to create/check `.fai` and `.dict` sidecars
  beside the FASTA; arrange a writable study copy rather than modifying a
  shared reference owned by another team.
- Nonoverlapping regions to analyze, with contig names matching the reference;
  STAR index parameters appropriate to the reads/reference; and the Analysis
  thresholds and target substitution approved for the study. The example
  numbers in the configuration guide are not universal scientific defaults.
- A resource/allocation choice appropriate to the actual reads and reference.
  A successful tiny synthetic run is not a full-dataset capacity estimate.

EMRYS does not acquire public reads/references or decide experimental pairing.
Keep input files at their declared locations for the life of their Runs.

### Prepare the manifests

The [sample and partition formats](configs/README.md#sample-manifest) define
literal tab-separated files. You may author those files directly; this also
supports FASTQ filenames that do not follow the helper's naming convention.
The repository's `samples.example.tsv` is a generic ingestion fixture, not a
complete paired-CMH Project manifest.

For the helper route below, assume four libraries named `control_1`,
`treatment_1`, `control_2`, and `treatment_2`. Each filename must end in
`_R1.fastq.gz` or `_R2.fastq.gz` (plain FASTQ and `.fq` are also supported).
Replace paths and assignments with your actual study values. `unknown` is an
explicit strandedness value, not an instruction to ignore known library design.
The regions file must already exist; a tab-separated `.bed` uses zero-based,
half-open intervals, while the supported plain region-table format uses
one-based, inclusive intervals. See [partition format](configs/README.md#partition-manifest).

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

The destination must be absent under an existing writable parent. This command
publishes `samples.tsv` and `partitions.tsv`; omit `--execute` for a preview
first. Review the resulting rows and assignments before creating the Project.

### Create and validate the Project

From the existing durable parent where the new `my-study` child should live:

```bash
cd /absolute/durable/path
emrys init my-study
```

Answer the prompts with the absolute paths to `samples.tsv`, `partitions.tsv`,
FASTA, and GTF; then the STAR parameters, exact control/treatment labels, target
change (for example `A>G`), and your study's thresholds. The
[configuration field guide](configs/README.md#built-in-analysis-fields) explains
the thresholds. Pressing Enter accepts a displayed suggestion; review it as a
scientific choice. This first invocation checks the proposed Project and
writes nothing. Rerun with publication enabled and provide the same answers:

```bash
emrys init my-study --execute
export EMRYS_PROJECT_ROOT="$(pwd -P)/my-study"
cd "$EMRYS_PROJECT_ROOT"
export EMRYS_REFERENCE_FASTA=/absolute/path/to/reference.fa
emrys validate
```

Use the same FASTA path you supplied during initialization. For an optional
background cohort, supply `--background-condition CONDITION` to both init
invocations and include its samples in the manifest. If scripting setup, use
`emrys init --help` for the explicit field flags; all required answers must be
supplied outside a terminal.

After `Project validation: PASS`, return to **step 3** for this new Project,
then follow the selected execution route through reports. Each Project has its
own runtime inventory and qualification records. Compare the real-data outputs
with the study design, not the synthetic fixture's expected counts.

For named Analyses, processing reuse, alternate profiles, and larger synthetic
exercises, use the [runbook](docs/operations/RUNBOOK.md). The optional
`production-like-v1` fixture has 100,000 pairs **per library** across four
libraries; select it with `--dataset-profile production-like-v1` on both
synthetic initialization commands in a new Project.
