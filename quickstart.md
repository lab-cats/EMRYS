# EMRYS quickstart: fresh checkout to processed results

This is the single supported first-run sequence for taking either a deterministic
synthetic fixture or paired FASTQ data from a fresh checkout through runtime
admission, data ingestion, processing, inspection, and the automatic reports.
Run scientific work only on the intended compute host. Every dry-run, doctor
result, scheduler job, and report has the evidence ceiling stated below.

## Plan and stop gates

| Phase | Operator action | Required result before continuing |
| --- | --- | --- |
| 1. Source | Clone, select one immutable commit, and install the locked Python environment | Clean detached commit and working `emrys --help` |
| 2. Runtime | Provision exact scientific tools and restore/check the canonical R library outside workflow execution | Canonical compute-node paths and passing `r-check` |
| 3. Inputs | Generate a create-absent starter set, then stage FASTQ, FASTA, GTF, and optional regions files | Explicit request, paired sample rows, and nonoverlapping partitions |
| 4. Profile | Render a new runtime profile from the observed canonical paths | Complete create-absent runtime TSV |
| 5. Admission | Validate the request and finalize two-phase storage qualification | Request PASS and matching final storage receipt |
| 6. Readiness | Run doctor in the execution context | Exact `READY` result |
| 7. Plan | Run the full no-write workflow plan | Reviewed deterministic run ID, run root, and owner commands |
| 8. Process | Submit the generated single-allocation wrapper first with no mode flag, then with explicit `--execute` | Terminal scheduler success plus verified EMRYS task records |
| 9. Results | Inspect the run and retain its complete evidence tree | `local_pipeline_complete` and automatic scientific/evidence HTML reports |

Do not skip a gate, hand-edit the generated scheduler wrapper, adopt outputs from
standalone stages into an orchestrated run, or interpret computational
candidates as biologically validated editing sites.

## 1. Clone and install the locked Python workflow

Clone the repository and freeze the exact remote-default commit you just
cloned. That is an executable starting point for both the synthetic check and
your own analysis. If your lab or project supplied a designated release tag or
full commit, select that ref instead. A moving branch name is never the
admitted identity.

```sh
git clone https://github.com/lab-cats/EMRYS.git
cd emrys
git fetch --tags --force

# Executable zero-context path: select the exact commit just cloned.
EMRYS_REF="$(git rev-parse HEAD)"

# Optional project policy: replace EMRYS_REF with a designated release tag or
# full commit before detaching.
git checkout --detach "$EMRYS_REF"
git rev-parse HEAD
git status --short
```

Require empty status output and record the printed full commit with the
analysis. Using the cloned commit means **you selected a development snapshot**;
it does not make that snapshot an EMRYS release or authorize a biological
claim. If your organization requires an approved release record, verify the
printed commit against that record before execution. EMRYS's receipts bind the
commit you actually selected either way, so a no-context user can begin without
an invented tag while a governed project can impose a stricter release rule.

Install `uv` as an explicit user-level prerequisite when it is absent, then
verify it and synchronize the immutable lock. The installer is the
[official uv standalone installer](https://docs.astral.sh/uv/getting-started/installation/);
review site policy before downloading it.

```sh
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh |
    env UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version
uv sync --locked --group workflow
```

This installs EMRYS and locked Snakemake `9.25.1` into `.venv`. It does not
install scientific tools, R, or R packages, and it never relocks the project.

The EMRYS cutover is an identity boundary. New package, CLI, environment,
adjacent-config, schema, receipt, and recovery-state identities use EMRYS only;
EMRYS does not adopt or resume a run root created by a pre-cutover checkout.
Use that exact historical checkout to inspect or resume retained historical
runs. Rename `norad.launcher.yaml`, `norad.resources.yaml`, and `NORAD_*`
operator selectors before using this checkout; detected legacy adjacent files
or R selectors fail closed rather than silently falling back to defaults.

The onboarding commands in this guide intentionally use templates and policy
from this exact source checkout. Run them through this checkout's editable
`.venv`; a copied non-editable wheel by itself is not a standalone onboarding
bundle.

Create one controlled command in every terminal used for this checkout:

```sh
EMRYS_REPO="$(pwd -P)"
EMRYS_PY="$EMRYS_REPO/.venv/bin/python"
emrys() {
  "$EMRYS_PY" -X pycache_prefix=/dev/null -I -m emrys "$@"
}
emrys --help
test -z "$(git status --porcelain=v1)"
```

The isolated invocation prevents a different checkout or ambient `PYTHONPATH`
from becoming the package authority. If the final command prints anything,
stop and review the working-tree changes before asking doctor to bind it.

## 2. Provide the scientific runtime

Install or select these exact accepted identities before continuing:

| Tool | Accepted version or rule |
| --- | --- |
| GNU Bash | `3.2` or newer |
| Python | `3.11` or newer from this checkout's locked `.venv` |
| Snakemake | `9.25.1` through that Python |
| STAR | `2.7.11b` |
| samtools | `1.19.2` |
| Java | canonical `<JAVA_HOME>/bin/java`, major `17` or newer |
| GATK | `4.6.1.0` |
| Picard | `3.1.1` jar, including the bound `3.1.1-16-g5b0b4c014-SNAPSHOT` build |
| bcftools | `1.21` |
| RSeQC | `infer_experiment.py 5.0.4` |
| gzip | compatible `gunzip` |
| R | `Rscript 4.6.1` |
| R namespaces | Exact lock-selected versions in `local_pilot_runtime.example.tsv` |

The runtime profile binds canonical executable or jar paths, versions, and
SHA-256 identities. An environment-module name is not sufficient. On a cluster,
discover the runtime inside the intended compute allocation before preparing
the profile; head-node visibility is not evidence.

```sh
hostname
for tool in STAR samtools gatk bcftools infer_experiment.py gunzip Rscript java; do
  printf '%-24s' "$tool"
  command -v "$tool" || printf 'MISSING\n'
done
java -version 2>&1 || true
Rscript --version 2>&1 || true
```

Load only the site's approved modules in that allocation, record the canonical
targets actually observed there, and provision missing tools outside EMRYS
before continuing.

The exact clean checkout is also the guarded `renv` project. It requires an
existing canonical R library with the lock-selected `renv` and Step `08`
namespaces. Explicitly restoring packages is a separate operator-authorized
mutation:

```sh
RENV_LIBRARY=/absolute/path/to/canonical/renv-library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-restore
RENV_LIBRARY=/absolute/path/to/canonical/renv-library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

If an approved canonical library already exists, do not restore another one:

```sh
RENV_LIBRARY=/absolute/path/to/canonical/renv-library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

Doctor and execution never restore, bootstrap, install, download, or repair a
runtime.

## 3. Initialize and ingest synthetic or real inputs

Choose durable storage visible from the execution host. The parent must exist;
the selected input directory and workspace leaf must not:

```sh
EMRYS_OPERATOR_ROOT=/absolute/path/to/operator-managed-storage
EMRYS_WORKSPACE_PATH="$EMRYS_OPERATOR_ROOT/emrys-workspace"

test -d "$EMRYS_OPERATOR_ROOT" &&
test -w "$EMRYS_OPERATOR_ROOT" &&
test ! -e "$EMRYS_WORKSPACE_PATH"
```

If that check fails, stop and choose the correct existing parent or a new
absent workspace. EMRYS does not recursively create a missing workspace parent.

### Path A: deterministic synthetic science smoke

Generate the small input fixture directly outside the checkout. Both
initializer commands are dry-run-first and refuse an existing destination:

```sh
EMRYS_INPUT_DIR="$EMRYS_OPERATOR_ROOT/emrys-synthetic-inputs"

emrys init synthetic-local-pilot --output-dir "$EMRYS_INPUT_DIR"
emrys init synthetic-local-pilot \
  --output-dir "$EMRYS_INPUT_DIR" \
  --dataset-profile smoke-v1 \
  --execute

test -f "$EMRYS_INPUT_DIR/fixture.manifest.json"
EMRYS_REQUEST_PATH="$EMRYS_INPUT_DIR/request.yaml"
```

The fixture has a deterministic 100 kb reference, matching GTF, one partition,
and four gzip-compressed paired libraries with 130 read pairs each. Its
engineered expectation is three Step `09` all-sites rows and one significant
computational row when the complete real-tool workflow succeeds. Those facts
are a smoke oracle only; they are not production, scientific-review, or
biological evidence.

For the larger production-like functional exercise, use a different absent
destination and select `--dataset-profile production-like-v1` on both the plan
and execute commands. It preserves the engineered oracle while expanding to a
5 Mb reference and 100,000 pairs per library. It is intentionally much slower
than `smoke-v1` and still uses only synthetic data.

If this synthetic run will use SLURM, also generate one separate launcher set.
Its request/manifests are unused for the synthetic run; only its reviewed
single-allocation wrapper is selected later:

```sh
EMRYS_LAUNCHER_DIR="$EMRYS_OPERATOR_ROOT/emrys-slurm-launcher"
emrys init local-pilot --output-dir "$EMRYS_LAUNCHER_DIR"
emrys init local-pilot \
  --output-dir "$EMRYS_LAUNCHER_DIR" \
  --execute
EMRYS_SLURM_WRAPPER="$EMRYS_LAUNCHER_DIR/run-in-slurm.sh"
```

### Path B: ingest your data

Generate one matched, create-absent starter set:

```sh
EMRYS_INPUT_DIR="$EMRYS_OPERATOR_ROOT/emrys-inputs"

emrys init local-pilot --output-dir "$EMRYS_INPUT_DIR"
emrys init local-pilot \
  --output-dir "$EMRYS_INPUT_DIR" \
  --execute

test -f "$EMRYS_INPUT_DIR/starter-set.manifest.tsv"
EMRYS_REQUEST_PATH="$EMRYS_INPUT_DIR/request.yaml"
EMRYS_SLURM_WRAPPER="$EMRYS_INPUT_DIR/run-in-slurm.sh"
```

The completion manifest is published last. Preserve a partial generated
directory without that manifest for inspection; choose a new absent directory
instead of rerunning over it. The manifest proves the initial starter
publication only; the expected edits below intentionally make its recorded
starter hashes historical rather than a current input attestation.

The generated layout is:

```text
emrys-inputs/
|-- request.yaml
|-- emrys.launcher.yaml
|-- emrys.resources.yaml
|-- samples.tsv
|-- partitions.tsv
|-- runtime.tsv
|-- run-in-slurm.sh
|-- starter-set.manifest.tsv
`-- inputs/
    |-- reads/       # one explicit R1/R2 pair per manifest sample
    |-- reference/   # one matching materialized FASTA and GTF
    `-- regions/     # optional files used by regions_file partitions
```

Create and populate `inputs/` without replacing an earlier staging tree. Then
edit `request.yaml`, `emrys.resources.yaml`, `samples.tsv`, and
`partitions.tsv`:

```sh
test ! -e "$EMRYS_INPUT_DIR/inputs" &&
mkdir -m 700 "$EMRYS_INPUT_DIR/inputs" &&
mkdir -m 700 \
  "$EMRYS_INPUT_DIR/inputs/reads" \
  "$EMRYS_INPUT_DIR/inputs/reference" \
  "$EMRYS_INPUT_DIR/inputs/regions"
```

1. Give the request stable reference, cohort, and analysis IDs; point it to the
   matching FASTA/GTF; select STAR-index parameters and analysis policy.
2. Give every sample an explicit R1/R2 FASTQ, condition, replicate, and
   strandedness declaration. Each of at least two replicate strata needs
   exactly one control and one treatment row. Pairing comes from `replicate`,
   not row order or sample names.
3. Select one or more nonoverlapping genomic partitions using contigs present
   in the reference. Start small for the first real-runtime check.
4. Keep the conservative resource defaults or author reviewed per-stage
   concurrency, threads, and memory. The YAML is optional at execution time;
   if absent, packaged defaults apply.

The [configuration guide](configs/README.md) explains every field, threshold,
path rule, sample-pairing requirement, and runtime row. Relative paths resolve
from the request file's directory—not the terminal's current directory.

## 4. Prepare one explicit runtime profile

The starter's `runtime.tsv` records policy and already fills this checkout and
workflow Python. The safer preparation helper accepts exact existing runtime
paths, fills the complete fixed roster, and emits TSV to standard output. It
does not install tools, probe versions, or write a file.

Redirect it to a **new absent filename**, never over the generated starter:

```sh
EMRYS_RUNTIME_PROFILE_PATH="$EMRYS_INPUT_DIR/runtime.selected.tsv"

test ! -e "$EMRYS_RUNTIME_PROFILE_PATH" && (
  set -C
  emrys prepare local-pilot-runtime \
    --bash /canonical/path/to/bash \
    --star /canonical/path/to/STAR \
    --samtools /canonical/path/to/samtools \
    --gatk /canonical/path/to/gatk \
    --bcftools /canonical/path/to/bcftools \
    --infer-experiment /canonical/path/to/infer_experiment.py \
    --gunzip /canonical/path/to/gunzip \
    --java /canonical/java-home/bin/java \
    --picard-jar /canonical/path/to/picard.jar \
    --rscript /canonical/path/to/Rscript \
    --renv-library /canonical/path/to/renv-library \
    > "$EMRYS_RUNTIME_PROFILE_PATH"
)
```

All explicit paths must be absolute canonical real files/directories. An
ordinary tool option may be omitted only when `PATH` contains one distinct
executable for that command. The helper still does not prove versions; doctor
does. If preparation fails after shell redirection creates an incomplete file,
preserve it for diagnosis and select a new absent output name.

## 5. Validate data compatibility without scientific tools

Run Steps 5–7 only on the intended workstation or inside an interactive compute
allocation. For scheduled execution, do not perform their data reads or runtime
probes on the login node; continue to the generated SLURM-wrapper section,
whose default no-mode submission runs the same validation, doctor, and no-write
plan inside its allocation.

Run the read-only intake validator first:

```sh
emrys validate local-pilot-request --request "$EMRYS_REQUEST_PATH"
```

Continue only after `Local-pilot request validation: PASS`. It normalizes and
hashes the declared files, proves paired strata, checks FASTA/GTF contigs and
bounds, and checks region or regions-file bounds. FASTQ hashing streams in
bounded chunks, but time and I/O still scale with the declared read bytes. No
scientific executable is probed and no output is written.

Qualify the exact workspace and Step `00c` reference-sidecar storage before
doctor. Run the compute phase inside a short allocation on the intended compute
node, let that allocation end, then run the finalize phase from the durable
control context:

```sh
EMRYS_REFERENCE_FASTA=/absolute/path/from/request/to/reference.fa
emrys inspect storage-qualification \
  --workspace "$EMRYS_WORKSPACE_PATH" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase compute
# Repeat the same command with --execute inside the allocation.
emrys inspect storage-qualification \
  --workspace "$EMRYS_WORKSPACE_PATH" \
  --reference-fasta "$EMRYS_REFERENCE_FASTA" --phase finalize
# Repeat the same command with --execute after the allocation has ended.
```

Doctor rejects missing, failed, stale, or mismatched final qualification. A
node-local workspace is not supported unless the same qualification establishes
its durable retention path.

## 6. Require full runtime `READY`

The doctor safely re-admits the request and source files plus the workspace
plan, checkout, locked workflow, tools, jar, R project/library, and namespaces:

```sh
emrys doctor local-pilot \
  --request "$EMRYS_REQUEST_PATH" \
  --workspace "$EMRYS_WORKSPACE_PATH" \
  --runtime-profile "$EMRYS_RUNTIME_PROFILE_PATH"
```

Continue only after:

```text
READY: local-pilot prerequisites passed.
```

Exit `1` prints one or more `BLOCKER` and `REMEDIATION` entries. Exit `2`
means the authored request, profile, or path boundary is malformed or unsafe.
Doctor does not create the workspace, execute Snakemake or scientific tools,
load modules, or alter an input.

## 7. Review the strict no-write plan

`emrys run` is a dry run unless `--execute` is present:

```sh
emrys run \
  --request "$EMRYS_REQUEST_PATH" \
  --workspace "$EMRYS_WORKSPACE_PATH" \
  --runtime-profile "$EMRYS_RUNTIME_PROFILE_PATH"
```

Review the deterministic run ID and run root, workflow-attempt identity,
expanded owner-job count, three reporting transactions, Snakemake command, and
each public owner producer/validator command. A successful plan ends by saying
that no workspace state was written.

Copy the exact run root printed by the plan:

```sh
EMRYS_RUN_ROOT=/absolute/path/to/emrys-workspace/runs/run-DIGEST
```

The run ID is derived from the exact normalized inputs and policy. Formatting
the optional label does not change it; changing data, manifests, reference,
partitions, profile, or analysis policy does.

## 8. Execute on a workstation or one compute node

Step `00c` creates or reuses `<reference-fasta>.fai` and
`<reference-stem>.dict` beside the external FASTA. Confirm that this directory
is the intended durable writable sidecar authority. A partial sidecar pair or
retained adjacent recovery state is a blocker; do not remove it merely to make
the run proceed.

### Workstation or interactive compute allocation

Run only on the intended compute host. Preserve the live control stream and
the pipeline's true exit status:

```sh
(
  set -o pipefail
  EMRYS_CONTROL_DIR="$(mktemp -d \
    "$EMRYS_OPERATOR_ROOT/.emrys-control.XXXXXX")" || exit 1
  EMRYS_CONTROL_LOG="$EMRYS_CONTROL_DIR/emrys-run-control.log"
  printf 'Control log: %s\n' "$EMRYS_CONTROL_LOG"
  emrys run \
    --request "$EMRYS_REQUEST_PATH" \
    --workspace "$EMRYS_WORKSPACE_PATH" \
    --runtime-profile "$EMRYS_RUNTIME_PROFILE_PATH" \
    --execute 2>&1 | tee "$EMRYS_CONTROL_LOG"
)
```

### One SLURM batch allocation

Use the executable `run-in-slurm.sh` published by `emrys init local-pilot`.
The generated wrapper is the supported single-allocation starter: submission
mode validates every required value, requests one node/task, publishes exact
`%j` stream paths, and resubmits itself as the job body. The job initializes
modules, enters the selected checkout, runs input/runtime preflight, and then
uses the public local executor.

Edit adjacent `emrys.launcher.yaml` for non-private allocation policy. Keep
site/private values in the selected checkout's ignored root `.env`, using the
tracked `.env.example` only as a placeholder template:

```sh
cd "$EMRYS_REPO"
test ! -e .env || { test -f .env && test ! -L .env; }
test -e .env || { cp .env.example .env && chmod 600 .env; }

# Replace every placeholder referenced by emrys.launcher.yaml. Keep this file
# private and untracked; do not put credentials or EMRYS_EXECUTE in it.
${EDITOR:-vi} .env

# Review requested CPUs, memory, time, exclusive placement, and optional
# nodelist. These are the resources Slurm will be asked for, not minima.
${EDITOR:-vi} "$EMRYS_INPUT_DIR/emrys.launcher.yaml"

"$EMRYS_SLURM_WRAPPER"
```

Launcher precedence is packaged defaults, adjacent `emrys.launcher.yaml`, then
explicit wrapper options. A YAML `{env: EMRYS_NAME}` reference reads the
invocation environment before root `.env`; scalar `$VAR` and shell syntax are
never evaluated. The `.env` must be an owner-only nonsymlink file and is not
copied into the generated starter or printed.

`memory: site-default` emits no `--mem`; an explicit Slurm size is passed
exactly once. `exclusive: true` emits `--exclusive`, and a configured nodelist
emits one exact `--nodelist=...`. Module mode `none` requires empty module
values and uses absolute runtime paths unchanged. Use `exact` only with a real
nonsymlink module-init file and an exact module list. Submission seals the
batch `PATH` to the generation-bound Python parent followed by `/usr/bin:/bin`;
the source checkout and Python cannot be replaced from launcher configuration.
The submit shell's `USER` and `LOGNAME` must both match `/usr/bin/id -un`.
The wrapper binds that live user and numeric UID into the batch and rechecks
them before any runtime or workspace action.
`EMRYS_SCRATCH_PARENT` must already be a real writable compute-node directory;
the job creates a private mode-`700` child, exports it as `TMPDIR`, logs its
filesystem/capacity, and removes it at exit. The wrapper installs nothing.
Inside the job, EMRYS observes the Slurm CPU and memory allocation together
with process CPU affinity and memory limits. It resolves packaged resource
defaults, adjacent `emrys.resources.yaml`, and any explicit resource CLI
overrides in that order. Execution fails before workflow entry if the effective
cores, memory, concurrency, or threads cannot fit.

The first submission uses no mode flag: it performs compute-context preflight
and prints the complete no-write workflow plan in the job log. Ambient or
authored `EMRYS_EXECUTE` cannot activate execution. Copy
the printed job ID, wait for both streams, and confirm scheduler exit plus the
plan. Copy the exact run root printed in that completed dry-run log into the
shell that will submit and inspect the execution:

```sh
EMRYS_RUN_ROOT=/absolute/path/printed/by/the/dry-run/plan
case "$EMRYS_RUN_ROOT" in
  /*/runs/run-*) ;;
  *) printf 'Invalid EMRYS_RUN_ROOT: %s\n' "$EMRYS_RUN_ROOT" >&2; false ;;
esac
export EMRYS_RUN_ROOT
```

Do not infer this value from the job ID or workspace name. Only after the
sanity check succeeds should you submit the execution job with the otherwise
identical values:

```sh
"$EMRYS_SLURM_WRAPPER" --execute
```

Submitting one allocation does not make this distributed workflow execution;
configured concurrent owners still run on that one compute node.

The scheduler's stdout/stderr directory may use site-supported shared storage
for login-node inspection. That does **not** qualify the workspace or reference
sidecars. Those exact mutation roots need the final two-phase qualification
above and stable absolute paths. A passing receipt admits only that tested
site/path pair; an unqualified NFS, distributed, or node-local arrangement
remains unsupported.

## 9. Observe the run from another terminal

For a workstation or interactive allocation, tail the exact control-log path
printed when execution began:

```sh
tail -n +1 -F /exact/path/to/emrys-run-control.log
```

For a submitted SLURM job, use the exact job ID and `%j` stream paths printed
by the generated wrapper. The Runbook owns the reusable
[stream-wait and accounting procedure](docs/operations/RUNBOOK.md#manual-job-inspection).
Control-C stops a local `tail`; it does not cancel the allocation. Confirm
scheduler state separately from EMRYS completion evidence.

EMRYS inspection is read-only and derives state from immutable records rather
than `.snakemake` metadata. Run it only on a host where the exact workspace path
is available under the supported filesystem contract. A login node that can see
only the shared scheduler logs cannot inspect or collect a node-local workspace;
the generated wrapper does not copy results. Arrange a reviewed site-native
retention/transfer path before execution if the workspace will otherwise become
unreachable when the allocation ends.

Before inspecting from a new terminal, repeat Step 1's `cd`, `EMRYS_PY`, and
`emrys` function setup, then export the exact `EMRYS_RUN_ROOT` copied from the
dry-run plan. Tailing the scheduler streams requires only `job_id` and
`EMRYS_LOG_DIR`; running EMRYS requires the controlled checkout setup too.

```sh
emrys inspect local-pilot-run --run-root "$EMRYS_RUN_ROOT"
```

Inspection rehashes bound evidence, so run it at stage boundaries, after a long
quiet interval, or once execution ends—not in a tight loop. Owner task logs are
retained under
`<run-root>/attempts/<workflow-attempt-id>/tasks/<machine-key>/<scope-id>/`,
but they publish at the task's terminal boundary and are not the continuous
live-tail surface. Use the top-level control or SLURM stream while running.

Do not launch a second initial run against the same run root after a terminal
disconnect or uncertain exit. Inspect the existing run first.

## 10. Confirm completion and find the report

| Route | Result |
| --- | --- |
| Owner-local stage scheduler entry points | Native stage outputs and validation TSVs; no orchestration report or adoption |
| `emrys run` | Attempts, verified records, artifact index, run summary, and automatic scientific and evidence HTML reports |
| `emrys build report` | Rebuild from an existing canonical run summary; never adopt standalone outputs |

The reporting sequence is part of the orchestrated workflow. Run a final
inspection:

```sh
emrys inspect local-pilot-run --run-root "$EMRYS_RUN_ROOT"
```

Successful automatic completion prints:

```text
State: local_pipeline_complete
Local pipeline complete: yes
```

Compute the exact report paths without searching the tree:

```sh
EMRYS_RUN_ID="${EMRYS_RUN_ROOT##*/}"
EMRYS_SCIENTIFIC_REPORT_PATH="$EMRYS_RUN_ROOT/products/report/$EMRYS_RUN_ID/$EMRYS_RUN_ID.scientific_report.html"
EMRYS_EVIDENCE_REPORT_PATH="$EMRYS_RUN_ROOT/products/report/$EMRYS_RUN_ID/$EMRYS_RUN_ID.evidence_report.html"
test -f "$EMRYS_SCIENTIFIC_REPORT_PATH" && printf '%s\n' "$EMRYS_SCIENTIFIC_REPORT_PATH"
test -f "$EMRYS_EVIDENCE_REPORT_PATH" && printf '%s\n' "$EMRYS_EVIDENCE_REPORT_PATH"
```

Copy either self-contained HTML file to a trusted workstation or open it with
the local browser allowed by your environment. The scientific report presents
the admitted scientifically relevant computational results; the evidence
report presents run status and provenance. Their presence alone is not
completion proof.

### Read the computational results

The scientific report presents the admitted computational results and its fixed
eight-figure views of candidates, editing rates, locations, sequence context,
the registered PUM motif, and sample behavior; it does not turn a threshold-
passing row into a validated editing site. The
[reporting owner](src/emrys/reporting/README.md) defines the two views, source
admission, display and figure policy, and direct build transaction. The
[Step 09 owner](src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
defines the complete native scientific tables and field semantics.

Use those native TSVs for complete machine-readable results. Candidate review,
adjudication, and biological interpretation remain external research work and
never alter or promote EMRYS's computational tables.

## 11. Keep the whole run root

Output presence is not completion authority. Preserve the entire run root:
contracts, attempts, owner logs, task/reporting records, native results,
products, locks, partials, backups, and recovery evidence belong to one
content-bound execution history.

The local-pilot
[contract](src/emrys/orchestration/local_pilot/CONTRACT.md#run-root-output-contract)
owns the durable directory and product roster. Do not copy a report or result
table and then discard its run evidence.

## 12. Stop safely after an incomplete run

Do not launch a second initial run, delete a lock, or repair output after a
disconnect, terminal scheduler state, or uncertain exit. Preserve the run root
and inspect it first. If inspection reports a supported between-task resume,
follow the Runbook's
[dry-run-first resume procedure](docs/operations/RUNBOOK.md#recurring-inspection-and-resume).
All other blocked states belong to
[troubleshooting](docs/operations/TROUBLESHOOTING.md).

## Final stop/go checklist

| Gate | GO | STOP |
| --- | --- | --- |
| Source and Python | Exact clean commit; `uv --version` works; `uv sync --locked --group workflow` succeeds | Wrong checkout, dirty tree, missing `uv`, or stale lock |
| Compute runtime | Canonical tools are observed on the intended compute node; guarded `r-check` passes | Login-only path, guessed module, wrong Java/R, or missing namespace |
| Storage | Final qualification covers the workspace and Step `00c` sidecar parents | Missing, failed, stale, or mismatched qualification |
| Inputs and plan | Request validation passes, doctor prints `READY`, and the generated no-write plan is reviewed | Any blocker, malformed input/profile, or hand-edited generated wrapper |
| Execution | Only `--execute` changes on the reviewed command or generated wrapper | Manual output adoption, head-node science work, or an uncertain existing run root |

The full [troubleshooting matrix](docs/operations/TROUBLESHOOTING.md) owns
recovery detail. Standalone stages remain supported, but they do not create the
immutable run state required by automatic reporting.
