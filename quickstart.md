# EMRYS quickstart: synthetic Project to Results

Run a supplied synthetic study, open its reports, then move to
[your own data](#7-create-a-project-for-your-own-data). The exercise includes
reads, a reference, and experimental assignments.

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

The exercise uses real tools on four libraries of 130 read pairs and a
100,000-base reference. Its resource needs do not predict those of your study.

Run commands in order and stop at an error. Replace `/absolute/path/...`, keep
the quotation marks, and keep this terminal open. A final `\` continues a
command on the next line.

## 1. Install the locked command

uv manages Python; Pixi and renv provide scientific tools and R packages.
Use your site's **uv** and **Pixi** installations if available. EMRYS needs Pixi
`>=0.75.0,<0.76`. Otherwise, if user-level installation is permitted, use these
[uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Pixi](https://pixi.prefix.dev/latest/installation/#installer-script-options)
installers. They install into your account and may update shell startup files:

```bash
curl -LsSf https://astral.sh/uv/0.12.3/install.sh | sh
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.75.0 bash
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
uv --version
pixi --version
```

Keep the required tool versions and dependency locks. Choose a revision with
your team: set `EMRYS_REVISION` to a release tag or full commit ID from the
[commit history](https://github.com/lab-cats/EMRYS/commits/master/). Selecting a
revision does not qualify it for your institution or science. The source
parent must exist; its `EMRYS` child must be absent.

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

uv can download Python 3.14; EMRYS requires Python 3.11 or newer. Record the
printed commit ID and keep this checkout at that revision. Help must work,
and the final Git command must print **nothing**. Both tracked changes and
nonignored untracked files prevent execution; resolve unexpected files without
deleting them just to pass the check.

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

Continue after `Project validation: PASS`. The supplied configuration,
manifests, inputs, and execution profile need no edits. If creation fails,
preserve the partial directory and use a new absent destination.

## 3. Prepare the runtime and storage

**Slurm users:** follow [Slurm setup and submission](docs/operations/RUNBOOK.md#slurm-setup-and-submission)
for site settings, runtime preparation, compute/head-node storage checks, and
submission. After the job finishes, return to **step 5**. Never run the
standalone commands below on a login node.

**Standalone compute-host users:** from the Project root, run:

```bash
emrys doctor --repair
```

Review Doctor's locations and answer `y` to install the managed runtime and
qualify Project and reference-sidecar storage. This can update the checkout's
`.venv` and Project runtime and writes a maintenance log. It neither downloads
scientific inputs nor repairs results. When it finishes, check readiness:

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

Review the plan for Analysis `primary`, including its Project and resources.
Answer `y` or `yes` at `Execute this plan? [y/N]` to start; any other answer or
interruption before confirmation starts no work. Reports follow successful
computation. Keep the terminal/job alive until the command ends.

For automation, the equivalent explicit command is
`emrys run --analysis primary --execute`. Use **one** execution form, not both.
`--no-report` deliberately skips report generation; omit it for this exercise.

Initialization and report commands require `--execute` to write files.
Run, resume, and Doctor repair can also proceed after terminal confirmation;
answer `n` to preview only. `validate`, `doctor`, and `inspect` are read-only.
See the [command contract](src/emrys/orchestration/run_coordinator/CONTRACT.md#public-model-and-admission)
for interactive input and automation rules.

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

Open the **Scientific report** and **Evidence report** paths printed by
inspection using your browser's **Open File** command. The first presents
candidates; the second explains computation and provenance. Their layout is:

```text
<PROJECT>/runs/<RUN_ID>/results/reports/<RUN_ID>/
    <RUN_ID>.scientific_report.html
    <RUN_ID>.evidence_report.html
```

Use the printed paths. From a cluster, transfer the complete `results/`
directory with your institution's file browser or approved transfer service.
Open its `reports/` files locally, keeping the layout intact for report/table
links. Provenance still names the original locations; retain the Project,
inputs, runtime, and complete Run on their original storage.

The synthetic fixture expects three Step `09` candidate rows, one significant.
These check software behavior, not biological truth. `FWD_like` and `REV_like`
are mechanical alignment groups, not biological strand. Completion confirms
this input/source/runtime/storage/route combination; it does not establish
production readiness, institutional qualification, scientific review, or
biological validation.

## 6. If execution or reporting did not complete

Follow **Next supported action:** and the blockers printed by `emrys inspect`.
For Slurm resume, include `--profile slurm` or your selected profile name; the
default is direct execution. `report` has no Slurm submission option: use an
approved compute shell as described in the
[runbook](docs/operations/RUNBOOK.md#inspect-and-open-reports).

| Inspection result | Next step |
| --- | --- |
| Attempt is still running | Wait for it or check the exact Slurm job. Do not start another writer. |
| Failed/interrupted computation with `Recovery available: yes` | Review `emrys resume` and confirm only the supported retry. It creates another Attempt for the same Run. |
| Scientific Results complete; reporting absent/incomplete and unblocked | Run `emrys report` to preview. If accepted, use `emrys report --execute`, then inspect again. |
| Any state is blocked, or report generation refuses retained partial files | Preserve the Run and follow [troubleshooting](docs/operations/TROUBLESHOOTING.md). Reporting failure is not a reason to rerun completed computation. |

Preserve Runs, locks, partial outputs, logs, backups, and receipts. With
multiple Runs, select the printed two-word name, full ID, or unique ID prefix.
Interactive selection is available; automation never assumes latest.

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

Write [tab-separated manifests](configs/README.md#sample-manifest) directly
for arbitrary FASTQ names, or use the helper below. `samples.example.tsv` is
a generic ingestion example, not a complete paired-CMH Project manifest.

Replace the four example library names, paths, and assignments with your study
values. The helper expects `_R1.fastq.gz`/`_R2.fastq.gz` suffixes; plain FASTQ and
`.fq` also work. Use known library strandedness instead of `unknown` when
available. The regions file must exist: tab-separated BED uses zero-based,
half-open coordinates; the plain region table uses one-based, inclusive
coordinates. See [partition format](configs/README.md#partition-manifest).

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

Supply absolute manifest/FASTA/GTF paths, STAR parameters, exact condition
labels, target change (such as `A>G`), and study thresholds. Consult the
[field guide](configs/README.md#built-in-analysis-fields); Enter accepts a
suggestion that still needs scientific review. This command checks the plan
without writing. Repeat with the same answers to create it:

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
libraries and a 5-Mb reference; select it with `--dataset-profile production-like-v1` on both
synthetic initialization commands in a new Project.
