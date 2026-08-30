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
| 3. Inputs | Generate a create-absent starter set, then stage FASTQ, FASTA, GTF, and optional regions files | Explicit Project definition, paired sample rows, and nonoverlapping partitions |
| 4. Profile | Render a new runtime profile from the observed canonical paths | Complete create-absent runtime TSV |
| 5. Admission | Validate the Project and finalize two-phase storage qualification | Project PASS and matching final storage receipt |
| 6. Readiness | Run doctor in the execution context | Exact `READY` result |
| 7. Plan | Invoke `emrys run` once and review its Run or Slurm-placement plan | Direct: deterministic Run ID and root; Slurm: one admitted submission plan |
| 8. Process | Confirm on the terminal, or use `--execute` for automation | Verified EMRYS records; scheduler success is only placement evidence |
| 9. Results | Inspect the run and retain its complete evidence tree | Complete scientific Results and separately verified scientific/evidence HTML reports |

Do not skip a gate, bypass the execution-profile/control boundary, adopt
outputs from standalone stages into an orchestrated Run, or interpret
computational candidates as biologically validated editing sites.

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
runs. Retired adjacent `emrys.launcher.yaml` or `emrys.resources.yaml` files
fail closed when no explicit execution profile is selected; migrate them into
one profile rather than allowing silent fallback.

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
EMRYS_PROJECT_PATH="$EMRYS_INPUT_DIR/project.yaml"
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

The synthetic initializer also publishes `emrys.execution.yaml` with direct
placement and fixture-sized resources. Direct execution may select it
explicitly or use the built-in direct default. For Slurm, replace its direct
placement with the closed Slurm shape from the tracked execution-profile
example and fill the site values.

### Path B: ingest your data

For existing FASTQs named `<sample>_R1.fastq[.gz]` and
`<sample>_R2.fastq[.gz]`, EMRYS can draft the strict manifests without guessing
biology. Every condition, replicate, and strandedness remains explicit; omit
`--execute` to preview without writing:

```sh
emrys init manifests \
  --output-dir "$EMRYS_OPERATOR_ROOT/emrys-manifest-drafts" \
  --fastq /data/control_1_R1.fastq.gz /data/control_1_R2.fastq.gz \
          /data/treated_1_R1.fastq.gz /data/treated_1_R2.fastq.gz \
  --sample control_1 control pair_1 forward \
  --sample treated_1 treatment pair_1 forward \
  --regions-file primary /data/targets.bed \
  --execute
```

The absent output receives `samples.tsv` and, only when declared,
`partitions.tsv`. Ambiguous names or missing assignments fail before creation.
This helper does not create a Project, infer conditions/cohorts, inspect FASTQ
contents, or replace full Project validation.

Generate one matched, create-absent starter set:

```sh
EMRYS_INPUT_DIR="$EMRYS_OPERATOR_ROOT/emrys-inputs"

emrys init local-pilot --output-dir "$EMRYS_INPUT_DIR"
emrys init local-pilot \
  --output-dir "$EMRYS_INPUT_DIR" \
  --execute

test -f "$EMRYS_INPUT_DIR/starter-set.manifest.tsv"
EMRYS_PROJECT_PATH="$EMRYS_INPUT_DIR/project.yaml"
```

The completion manifest is published last. Preserve a partial generated
directory without that manifest for inspection; choose a new absent directory
instead of rerunning over it. The manifest proves the initial starter
publication only; the expected edits below intentionally make its recorded
starter hashes historical rather than a current input attestation.

The generated layout is:

```text
emrys-inputs/
|-- project.yaml
|-- emrys.execution.yaml
|-- samples.tsv
|-- partitions.tsv
|-- runtime.tsv
|-- starter-set.manifest.tsv
`-- inputs/
    |-- reads/       # one explicit R1/R2 pair per manifest sample
    |-- reference/   # one matching materialized FASTA and GTF
    `-- regions/     # optional files used by regions_file partitions
```

Create and populate `inputs/` without replacing an earlier staging tree. Then
edit `project.yaml`, `samples.tsv`, and `partitions.tsv`:

```sh
test ! -e "$EMRYS_INPUT_DIR/inputs" &&
mkdir -m 700 "$EMRYS_INPUT_DIR/inputs" &&
mkdir -m 700 \
  "$EMRYS_INPUT_DIR/inputs/reads" \
  "$EMRYS_INPUT_DIR/inputs/reference" \
  "$EMRYS_INPUT_DIR/inputs/regions"
```

1. Give the Project stable reference, cohort, and analysis IDs; point it to the
   matching FASTA/GTF; select STAR-index parameters and analysis policy.
2. Give every sample an explicit R1/R2 FASTQ, condition, replicate, and
   strandedness declaration. Each of at least two replicate strata needs
   exactly one control and one treatment row. Pairing comes from `replicate`,
   not row order or sample names.
3. Select one or more nonoverlapping genomic partitions using contigs present
   in the reference. Start small for the first real-runtime check.
4. Keep the built-in direct resources, or edit `emrys.execution.yaml` and
   select it explicitly for reviewed resources or Slurm placement. Resource
   CLI flags override the selected profile.

The [configuration guide](configs/README.md) explains every field, threshold,
path rule, sample-pairing requirement, and runtime row. Relative paths resolve
from the Project file's directory—not the terminal's current directory.

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

Run Project validation and Doctor only on the intended workstation or inside
an interactive compute allocation. The two-phase storage qualification below
is mandatory for every path and may use a separate short allocation. If only
batch submission is available, do not move the data reads or runtime probes to
the login node: after finalizing storage, continue to the Slurm
execution-profile section. Its submit-host dry-run admits only placement;
after terminal confirmation or explicit noninteractive `--execute`, the compute
delegate performs Project admission, doctor, and Run planning inside the
allocation and stops before lifecycle mutation on failure.

Run the read-only intake validator first:

```sh
emrys validate project --project "$EMRYS_PROJECT_PATH"
```

Continue only after `Project validation: PASS`. It admits and
hashes the declared files, proves paired strata, checks FASTA/GTF contigs and
bounds, and checks region or regions-file bounds. FASTQ hashing streams in
bounded chunks, but time and I/O still scale with the declared read bytes. No
scientific executable is probed and no output is written.

Qualify the exact workspace and Step `00c` reference-sidecar storage before
doctor. Run the compute phase inside a short allocation on the intended compute
node, let that allocation end, then run the finalize phase from the durable
control context:

```sh
EMRYS_REFERENCE_FASTA=/absolute/path/from/project/to/reference.fa
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

The doctor safely re-admits the Project and source files plus the workspace
plan, checkout, locked workflow, tools, jar, R project/library, and namespaces:

```sh
emrys doctor local-pilot \
  --project "$EMRYS_PROJECT_PATH" \
  --workspace "$EMRYS_WORKSPACE_PATH" \
  --runtime-profile "$EMRYS_RUNTIME_PROFILE_PATH"
```

Continue only after:

```text
READY: local-pilot prerequisites passed.
```

Exit `1` prints one or more `BLOCKER` and `REMEDIATION` entries. Exit `2`
means the authored Project, profile, or path boundary is malformed or unsafe.
Doctor does not create the workspace, execute Snakemake or scientific tools,
load modules, or alter an input.

## 7. Review and confirm one immutable plan

With direct placement on a terminal, `emrys run` constructs and displays the
Run plan, then asks once whether to execute it:

```sh
emrys run \
  --project "$EMRYS_PROJECT_PATH" \
  --workspace "$EMRYS_WORKSPACE_PATH" \
  --runtime-profile "$EMRYS_RUNTIME_PROFILE_PATH" \
  --log-level verbose
```

Review the deterministic Run ID/root, pending and reusable work counts,
effective resources, and automatic reporting declaration. This walkthrough
requests verbose detail because it needs the Run root and resources; omit that
option for the concise normal view, or use `debug` for exact commands. Confirm
only after reviewing the displayed plan. Refusal, EOF, or interruption opens no
application log, writes nothing, and executes or submits nothing. In a
noninteractive context, omission of `--execute` retains that no-write behavior;
use `--execute` only when automation deliberately authorizes execution.

These direct commands use the built-in profile. If you changed the generated
profile to direct placement and edited its resources, add
`--execution-profile "$EMRYS_INPUT_DIR/emrys.execution.yaml"` to the command.

Record the exact Run root printed by this invocation for later inspection; it
is not transferred into a second execution command:

```sh
EMRYS_RUN_ROOT=/absolute/path/to/emrys-workspace/runs/run-DIGEST
```

The Run ID binds the immutable Analysis revision and Execution Plan. Formatting the
optional label or changing only Attempt placement does not change it.

## 8. Execute on a workstation or one compute node

Step `00c` creates or reuses `<reference-fasta>.fai` and
`<reference-stem>.dict` beside the external FASTA. Confirm that this directory
is the intended durable writable sidecar authority. A partial sidecar pair or
retained adjacent recovery state is a blocker; do not remove it merely to make
the run proceed.

### Workstation or interactive compute allocation

Run only on the intended compute host. The confirmed command in Section 7 is
the single direct invocation: it executes the exact displayed plan, preserves
its true exit, and opens one structured application log only after consent.

The application-log root defaults to
`$EMRYS_WORKSPACE_PATH/logs/application`. It records lifecycle diagnostics and
receipt observation but is not completion authority.

### One SLURM batch allocation

Use the generated execution profile. Path B already contains the Slurm shape;
Path A must replace its direct placement with the Slurm placement from
`configs/execution_profile.example.yaml`. Replace every site and scratch
placeholder, then review both Run-bound resources and Attempt-local placement:

```sh
EMRYS_EXECUTION_PROFILE_PATH="$EMRYS_INPUT_DIR/emrys.execution.yaml"
${EDITOR:-vi} "$EMRYS_EXECUTION_PROFILE_PATH"
```

Null account, partition, QOS, memory, or node-list values defer to site policy.
Module mode `none` loads nothing; `exact` requires an absolute initializer and
closed module roster. Values are literal—there is no `.env`, shell, or
environment interpolation. The scratch parent must be one real writable
compute-node directory.

Define the exact command once. On a terminal, calling it without extra
arguments admits the profile, prints a no-write placement plan without reading
the large inputs on the login node, and asks before submission.

```sh
emrys_slurm_run() {
  emrys run \
    --project "$EMRYS_PROJECT_PATH" \
    --workspace "$EMRYS_WORKSPACE_PATH" \
    --runtime-profile "$EMRYS_RUNTIME_PROFILE_PATH" \
    --execution-profile "$EMRYS_EXECUTION_PROFILE_PATH" \
    --log-level verbose \
    "$@"
}
emrys_slurm_run
```

Review the placement and answer yes to submit it once. For noninteractive
automation, invoke the function with `--execute` instead; do not run both forms:

```sh
emrys_slurm_run --execute
```

An accepted terminal confirmation or explicit `--execute` creates
`<workspace>/logs`, calls `sbatch` once, and prints exact `JOB_ID`, `OUT`, and
`ERR` values. The compute delegate re-admits the profile
digest, submit UID, private marker, and Slurm job ID; loads only declared
modules; creates and removes one private mode-`0700` scratch directory; runs
doctor; plans the immutable Run; and then enters the normal lifecycle. Ambient
`SBATCH_*` variables cannot alter the admitted submission. Keep the selected
profile bytes unchanged while the job is pending.

This remains the same one-host Snakemake backend inside one allocation, not
distributed execution. The scheduler job ID and placement are Attempt
provenance, never Run identity or completion authority.

The scheduler's stdout/stderr directory may use site-supported shared storage
for login-node inspection. That does **not** qualify the workspace or reference
sidecars. Those exact mutation roots need the final two-phase qualification
above and stable absolute paths. A passing receipt admits only that tested
site/path pair; an unqualified NFS, distributed, or node-local arrangement
remains unsupported.

## 9. Observe and inspect the run

For direct execution, the invoking terminal is the primary control stream and
the structured application log defaults beneath
`<workspace>/logs/application`. For Slurm, use the exact `JOB_ID`, `OUT`, and
`ERR` paths printed at submission. The Runbook owns the reusable
[stream-wait and accounting procedure](docs/operations/RUNBOOK.md#manual-stream-and-accounting-fallback).
Control-C stops a local `tail`; it does not cancel the allocation. Confirm
scheduler state separately from EMRYS completion evidence.

EMRYS inspection is read-only and derives state from immutable records rather
than `.snakemake` metadata. Run it only on a host where the exact workspace path
is available under the supported filesystem contract. A login node that can see
only the shared scheduler logs cannot inspect or collect a node-local workspace;
EMRYS does not copy results. Arrange a reviewed site-native
retention/transfer path before execution if the workspace will otherwise become
unreachable when the allocation ends.

Before inspecting from a new terminal, repeat Step 1's `cd`, `EMRYS_PY`, and
`emrys` function setup. For direct execution, use the Run root recorded from
the same Step 7 invocation. For Slurm, record it from the compute delegate's
`ERR` stream after planning; never infer it from the scheduler job ID or
workspace name. This locator is for later read-only inspection, not a
plan-to-execution handoff.

```sh
EMRYS_RUN_ROOT=/absolute/path/printed/by/emrys
emrys inspect local-pilot-run --run-root "$EMRYS_RUN_ROOT"
```

Inspection rehashes bound evidence, so run it at stage boundaries, after a long
quiet interval, or once execution ends—not in a tight loop. Owner task logs are
retained under
`<run-root>/attempts/<workflow-attempt-id>/tasks/<machine-key>/<scope-id>/`,
but they publish at the task's terminal boundary and are not the continuous
live-tail surface. Use the top-level control or Slurm stream while running.

Do not launch a second initial run against the same run root after a terminal
disconnect or uncertain exit. Inspect the existing run first.

## 10. Confirm completion and find the report

| Route | Result |
| --- | --- |
| Owner-local stage scheduler entry points | Native stage outputs and validation TSVs; no orchestration report or adoption |
| `emrys run` / `emrys resume` | A scientific Attempt through `cohort_slice`, followed by automatic reporting by default |
| `emrys run ... --no-report` / `emrys resume ... --no-report` | The same scientific Attempt and Results, with only downstream reporting skipped |
| `emrys report --run-root ...` | Read-only report plan or validated reuse; add `--execute` to generate reports independently |

The terminal scientific Attempt receipt is published and its Run lock released
before reporting starts. A reporting failure therefore returns a failure to the
operator but does not rewrite or negate the successful scientific receipt or
complete Results. Generate omitted reports independently by reviewing the
read-only plan and then adding `--execute`:

```sh
emrys report --run-root "$EMRYS_RUN_ROOT"
emrys report --run-root "$EMRYS_RUN_ROOT" --execute
```

EMRYS reuses an existing report bundle only after full validation. It generates
only when all reporting ledgers and Run-specific report locations are empty;
partial, corrupt, mismatched, or ambiguous state fails closed and is preserved.
Run a final inspection:

```sh
emrys inspect local-pilot-run --run-root "$EMRYS_RUN_ROOT"
```

Successful automatic completion prints:

```text
Run integrity: valid
Attempt outcome: succeeded
Scientific Results: complete
Reporting: complete
Recovery available: no
Results:
  Scientific report: /absolute/path/to/the/scientific-report.html
  Evidence report: /absolute/path/to/the/evidence-report.html
```

Inspection prints those locations whenever it independently admits the complete
HTML-report transaction. Copy the printed paths. If inspection does not print a
`Results:` block, do not infer locations from the run ID, run root, or a tree
search. A reporting failure does not erase complete scientific Results.

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
admission, display and figure policy, and independent report transaction. The
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
[single-invocation resume procedure](docs/operations/RUNBOOK.md#recurring-inspection-and-resume).
All other blocked states belong to
[troubleshooting](docs/operations/TROUBLESHOOTING.md).

## Final stop/go checklist

| Gate | GO | STOP |
| --- | --- | --- |
| Source and Python | Exact clean commit; `uv --version` works; `uv sync --locked --group workflow` succeeds | Wrong checkout, dirty tree, missing `uv`, or stale lock |
| Compute runtime | Canonical tools are observed on the intended compute node; guarded `r-check` passes | Login-only path, guessed module, wrong Java/R, or missing namespace |
| Storage | Final qualification covers the workspace and Step `00c` sidecar parents | Missing, failed, stale, or mismatched qualification |
| Inputs and plan | Direct: Project validation and Doctor pass before the no-write Run plan; Slurm: the explicit profile and no-submit placement plan are reviewed | Any blocker, malformed input/profile, or unreviewed placement |
| Execution | One terminal invocation is reviewed and confirmed; `--execute` is only the explicit automation path | Manual output adoption, login-node science work, or an uncertain existing Run root |

The full [troubleshooting matrix](docs/operations/TROUBLESHOOTING.md) owns
recovery detail. Standalone stages remain supported, but they do not create the
immutable run state required by automatic reporting.
