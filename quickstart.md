# EMRYS quickstart: synthetic Project to Results

This is the shortest supported path through the real EMRYS workflow. It creates
a deterministic synthetic Project, admits an EMRYS-managed runtime, executes
one immutable Run, generates reports, and inspects the retained Results.

Use an intended Linux compute host, a clean EMRYS checkout, and durable storage
outside that checkout. Do not run scientific work on a cluster login node.

## What this proves

Success shows that the exact synthetic inputs, source commit, admitted runtime,
storage, and execution path worked together for one Run. It is not production,
institutional-site, distributed-scheduler, scientific-review, or biological
evidence. The fixture's expected three Step `09` rows and one significant row
are a regression oracle, not biological truth.

## 1. Install the locked command

Select the intended release or commit. With Python 3.11 or newer and
[`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed by an
approved route:

```sh
git clone https://github.com/lab-cats/EMRYS.git
cd EMRYS
git checkout --detach FULL_COMMIT_OR_RELEASE_TAG
uv sync --locked --group workflow
source .venv/bin/activate

emrys --help
git status --short
```

Stop if the commit is wrong, help fails, or tracked files are dirty. Do not
relock dependencies as part of setup.

## 2. Create the synthetic Project

Choose an absolute, absent directory under an existing writable, durable
parent. The first command displays the no-write plan; the second publishes it.

```sh
EMRYS_PROJECT_ROOT=/absolute/durable/path/emrys-smoke

emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT"
emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT" --execute
cd "$EMRYS_PROJECT_ROOT"
```

If creation is interrupted, preserve the partial directory for inspection and
choose a new absent destination. For the larger 100,000-pair synthetic
exercise, add `--dataset-profile production-like-v1` to both commands.

For real data, first create strict manifest drafts with `emrys init manifests`,
then run `emrys init PROJECT_NAME` from the intended parent. The
[configuration guide](configs/README.md) defines the Project and input fields.

## 3. Admit a runtime

The managed path needs Pixi installed through site policy. Doctor delegates
dependency installation to `uv`, Pixi, and `renv`; EMRYS does not implement a
package manager.

```sh
emrys validate
emrys doctor --repair --execute
```

Continue only after `Project validation: PASS` and `EMRYS is ready.` Repair
touches only supported EMRYS-owned environment state, then rechecks readiness.
Omit `--execute` to preview and confirm interactively.

If the institution provides the tools, load that environment on the execution
host and use:

```sh
emrys runtime discover
emrys runtime discover --execute
emrys doctor
```

Discovery refuses missing or ambiguous installations and never loads modules
or installs software. The [runbook](docs/operations/RUNBOOK.md) covers
institutional modules, Slurm placement, and exact runtime requirements.

Readiness is bounded admission evidence, not a capacity estimate or proof that
the workflow ran.

## 4. Run one Analysis

The synthetic Project contains one Analysis, so its name may be omitted:

```sh
emrys run
```

On a terminal, EMRYS displays the immutable plan and asks once before writing
or executing. Refusal, EOF, or interruption before confirmation writes
nothing, submits nothing, and opens no application log. Automation uses the
same plan with explicit execution:

```sh
emrys run --analysis primary --execute
```

Reporting follows successful full scientific work. Add `--no-report` only when
it should be skipped. A named or absolute `--profile` can place the same
single-host executor inside one Slurm allocation; use the runbook rather than
running on the login node.

## 5. Inspect and report

Inspect admitted state instead of inferring completion from a process, Slurm
job, or visible file:

```sh
emrys inspect
```

With one Run, omission selects it. With several, a terminal offers their stable
two-word names; automation must supply a human name, full Run ID, or unique ID
prefix. Inspection is read-only and reports the retained Results and report
locations beneath the Run.

If reports were skipped or failed after scientific Results completed, preview
and then publish an admissible absent report bundle:

```sh
emrys report
emrys report --execute
```

Do not delete or rename a Run root, lock, partial result, log, or receipt to
make a command proceed. Inspect first; use `emrys resume [RUN]` only for a
supported failed or interrupted state. The
[troubleshooting guide](docs/operations/TROUBLESHOOTING.md) owns recovery, and
the [runbook](docs/operations/RUNBOOK.md) covers processing-only Runs,
downstream reuse, Slurm, and advanced operation.
