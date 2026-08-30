# EMRYS quickstart: synthetic Project to Results

This is the shortest supported path through the real EMRYS workflow. It creates
a deterministic synthetic Project, admits a managed runtime, executes one
immutable Run, generates reports, and inspects the retained result.

Use an intended Linux compute host, a clean EMRYS checkout, and durable storage
outside that checkout. Do not run scientific work on a cluster login node.

## Evidence boundary

Completing this guide shows that the exact synthetic inputs, source commit,
admitted runtime, storage, and execution path worked for that Run. It is not
production-data, cluster/site, distributed-scheduler, scientific-review,
biological-validation, or biological-interpretation evidence. EMRYS reports
**CMH-ranked computational candidates**, not validated editing sites.

The default `smoke-v1` fixture contains four paired libraries. Its engineered
oracle is three Step `09` all-sites rows and one significant computational row.
That oracle detects workflow regressions; it does not establish biological
truth. Reporting presents retained evidence and creates no new scientific
evidence.

## 1. Clone and install the locked Python workflow

Select the intended commit. Install Python 3.11 or newer and
[`uv`](https://docs.astral.sh/uv/getting-started/installation/) through your
site's approved route, then bootstrap the locked EMRYS command:

```sh
git clone https://github.com/lab-cats/EMRYS.git
cd EMRYS
git checkout --detach FULL_COMMIT_OR_RELEASE_TAG
uv sync --locked --group workflow
```

Bind every command below to this checkout rather than an ambient installation:

```sh
EMRYS_REPO="$(pwd -P)"
emrys() {
  "$EMRYS_REPO/.venv/bin/python" -X pycache_prefix=/dev/null -I -m emrys "$@"
}
emrys --help
git status --short
```

Stop if the selected commit is wrong, help fails, or tracked files are dirty.
Do not relock dependencies as an incidental setup action.

## 2. Provide the scientific runtime

The managed path uses existing package managers rather than an EMRYS-specific
installer. Install [Pixi](https://pixi.sh/latest/installation/) through site
policy before asking Doctor to repair the runtime. Doctor delegates the locked
Python, native/R, and R-library work to `uv`, Pixi, and `renv`.

Managed repair currently supports Linux x86-64. For institution-provided tools,
modules, or Slurm placement, use the [operations runbook](docs/operations/RUNBOOK.md)
instead of changing the managed Project by hand.

## 3. Initialize and ingest synthetic or real inputs

Choose an absolute, absent Project directory under an existing writable,
durable parent. EMRYS creates the Project and its owned directories; do not put
it inside the source checkout.

```sh
EMRYS_PROJECT_ROOT=/absolute/durable/path/emrys-smoke
EMRYS_PROJECT_PATH="$EMRYS_PROJECT_ROOT/project.yaml"

emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT"
emrys init synthetic --output-dir "$EMRYS_PROJECT_ROOT" --execute
```

The first command is a no-write plan. The second publishes the create-absent
`smoke-v1` Project and its completion manifest. If the destination already
exists or publication is interrupted, preserve it for inspection and choose a
new absent destination; do not delete uncertain state to force a retry.

For the larger synthetic exercise, add
`--dataset-profile production-like-v1` to both commands. It uses 100,000 pairs
per library and a 5 Mb reference, remains synthetic, and is intentionally much
slower.

For real FASTQs and references, use `emrys init manifests` followed by
`emrys init project`. Those commands require explicit biological assignments
and scientific thresholds and leave inputs in place. See the
[configuration guide](configs/README.md); this quickstart does not duplicate
that advanced intake.

## 4. Discover and admit the runtime

The managed golden path lets Doctor create and admit the single Project runtime
profile. Do not author or edit that generated profile manually.

If the institution owns the tools, use `emrys runtime discover` in the intended
execution environment. It refuses missing or ambiguous installations and does
not load modules or install software. Site-runtime selection and exact tool
requirements are documented in the [runbook](docs/operations/RUNBOOK.md).

## 5. Validate data compatibility without scientific tools

An optional early check admits and validates the Project definition and its
declared files without running scientific tools or writing workflow output:

```sh
emrys validate project --project "$EMRYS_PROJECT_PATH"
```

Continue only after `Project validation: PASS`. Doctor remains the authority
for complete execution readiness, including the admitted runtime and storage
checks. Do not manufacture or bypass readiness evidence.

## 6. Diagnose readiness and optionally repair the managed runtime

Run the bounded managed repair and requalification:

```sh
emrys doctor \
  --project "$EMRYS_PROJECT_PATH" \
  --repair --execute
```

Doctor diagnoses first, changes only supported EMRYS-owned runtime state when
repair is needed, delegates installation to the package managers, and then
rechecks the Project. It does not modify declared inputs or overwrite an
institution- or user-owned runtime profile. Omit `--execute` to preview and
confirm interactively.

Continue only after Doctor prints `EMRYS is ready.` Readiness is bounded
admission evidence, not a capacity estimate or proof that the workflow ran. If
Doctor reports a blocker, stop and use the
[troubleshooting guide](docs/operations/TROUBLESHOOTING.md).

## 7. Review and confirm one immutable plan

For explicit noninteractive execution, run:

```sh
emrys run --project "$EMRYS_PROJECT_PATH" --execute
```

EMRYS prints the immutable Run plan before executing it. On a terminal, omit
`--execute` to review the same plan and answer one confirmation prompt. Refusal,
EOF, or interruption before confirmation writes nothing, submits nothing, and
opens no application log.

Reporting runs automatically after successful scientific work. Add
`--no-report` only when reporting should be skipped; this does not change the
scientific Run or its Results. An explicit execution profile may place the same
one-host workflow in one Slurm allocation; follow the [runbook](docs/operations/RUNBOOK.md)
rather than adapting this direct golden path.

## 8. Inspect Results

Record the exact Run root printed by `emrys run`, then inspect EMRYS's admitted
records rather than inferring completion from process or scheduler status:

```sh
EMRYS_RUN_ROOT=/absolute/path/printed/by/emrys
emrys inspect run --run-root "$EMRYS_RUN_ROOT"
```

Inspection is read-only. A successful process, scheduler job, or visible file
does not replace `complete` admitted Results. Scientist-facing outputs and the
automatic reports are retained beneath the Run's `results/` tree.

If scientific Results are complete but reports were skipped or failed, preview
`emrys report --run-root "$EMRYS_RUN_ROOT"`, then add `--execute` only for an
admissible absent report bundle. Preserve partial or ambiguous report state.

For failure classification, resume rules, exact Slurm/site setup, or detailed
inspection, use the [runbook](docs/operations/RUNBOOK.md) and
[troubleshooting guide](docs/operations/TROUBLESHOOTING.md). Never delete or
rename a Run root, lock, partial result, log, or retained receipt merely to make
a command proceed.
