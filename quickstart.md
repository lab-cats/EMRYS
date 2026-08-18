# NORAD quickstart: fresh checkout to processed results

This is the single supported first-run sequence for taking either a deterministic
synthetic fixture or paired FASTQ data from a fresh checkout through runtime
admission, data ingestion, processing, inspection, and the automatic report.
Run scientific work only on the intended compute host. Every dry-run, doctor
result, scheduler job, and report has the evidence ceiling stated below.

## Plan and stop gates

| Phase | Operator action | Required result before continuing |
| --- | --- | --- |
| 1. Source | Clone, select one immutable commit, and install the locked Python environment | Clean detached commit and working `norad --help` |
| 2. Runtime | Provision exact scientific tools and restore/check the canonical R library outside workflow execution | Canonical compute-node paths and passing `r-check` |
| 3. Inputs | Generate a create-absent starter set, then stage FASTQ, FASTA, GTF, and optional regions files | Explicit request, paired sample rows, and nonoverlapping partitions |
| 4. Profile | Render a new runtime profile from the observed canonical paths | Complete create-absent runtime TSV |
| 5. Admission | Validate the request and finalize two-phase storage qualification | Request PASS and matching final storage receipt |
| 6. Readiness | Run doctor in the execution context | Exact `READY` result |
| 7. Plan | Run the full no-write workflow plan | Reviewed deterministic run ID, run root, and owner commands |
| 8. Process | Submit the generated single-allocation wrapper first with `NORAD_EXECUTE=0`, then unchanged with `1` | Terminal scheduler success plus verified NORAD task records |
| 9. Results | Inspect the run and retain its complete evidence tree | `local_pipeline_complete` and automatic HTML report |

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
git clone https://github.com/lab-cats/norad.git
cd norad
git fetch --tags --force

# Executable zero-context path: select the exact commit just cloned.
NORAD_REF="$(git rev-parse HEAD)"

# Optional project policy: replace NORAD_REF with a designated release tag or
# full commit before detaching.
git checkout --detach "$NORAD_REF"
git rev-parse HEAD
git status --short
```

Require empty status output and record the printed full commit with the
analysis. Using the cloned commit means **you selected a development snapshot**;
it does not make that snapshot a NORAD release or authorize a biological
claim. If your organization requires an approved release record, verify the
printed commit against that record before execution. NORAD's receipts bind the
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

This installs NORAD and locked Snakemake `9.25.1` into `.venv`. It does not
install scientific tools, R, or R packages, and it never relocks the project.

The onboarding commands in this guide intentionally use templates and policy
from this exact source checkout. Run them through this checkout's editable
`.venv`; a copied non-editable wheel by itself is not a standalone onboarding
bundle.

Create one controlled command in every terminal used for this checkout:

```sh
NORAD_REPO="$(pwd -P)"
NORAD_PY="$NORAD_REPO/.venv/bin/python"
norad() {
  "$NORAD_PY" -X pycache_prefix=/dev/null -I -m norad "$@"
}
norad --help
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
| Picard | `3.1.1` jar |
| bcftools | `1.21` |
| RSeQC | `infer_experiment.py` with a parseable RSeQC version |
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
targets actually observed there, and provision missing tools outside NORAD
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
NORAD_OPERATOR_ROOT=/absolute/path/to/operator-managed-storage
NORAD_WORKSPACE_PATH="$NORAD_OPERATOR_ROOT/norad-workspace"

test -d "$NORAD_OPERATOR_ROOT" &&
test -w "$NORAD_OPERATOR_ROOT" &&
test ! -e "$NORAD_WORKSPACE_PATH"
```

If that check fails, stop and choose the correct existing parent or a new
absent workspace. NORAD does not recursively create a missing workspace parent.

### Path A: deterministic synthetic science smoke

Generate the small input fixture directly outside the checkout. Both
initializer commands are dry-run-first and refuse an existing destination:

```sh
NORAD_INPUT_DIR="$NORAD_OPERATOR_ROOT/norad-synthetic-inputs"

norad init synthetic-local-pilot --output-dir "$NORAD_INPUT_DIR"
norad init synthetic-local-pilot \
  --output-dir "$NORAD_INPUT_DIR" \
  --execute

test -f "$NORAD_INPUT_DIR/fixture.manifest.json"
NORAD_REQUEST_PATH="$NORAD_INPUT_DIR/request.yaml"
```

The fixture has a deterministic 100 kb reference, matching GTF, one partition,
and four gzip-compressed paired libraries with 130 read pairs each. Its
engineered expectation is three Step `09` all-sites rows and one significant
computational row when the complete real-tool workflow succeeds. Those facts
are a smoke oracle only; they are not production, scientific-review, or
biological evidence.

If this synthetic run will use SLURM, also generate one separate launcher set.
Its request/manifests are unused for the synthetic run; only its reviewed
single-allocation wrapper is selected later:

```sh
NORAD_LAUNCHER_DIR="$NORAD_OPERATOR_ROOT/norad-slurm-launcher"
norad init local-pilot --output-dir "$NORAD_LAUNCHER_DIR"
norad init local-pilot \
  --output-dir "$NORAD_LAUNCHER_DIR" \
  --execute
NORAD_SLURM_WRAPPER="$NORAD_LAUNCHER_DIR/run-in-slurm.sh"
```

### Path B: ingest your data

Generate one matched, create-absent starter set:

```sh
NORAD_INPUT_DIR="$NORAD_OPERATOR_ROOT/norad-inputs"

norad init local-pilot --output-dir "$NORAD_INPUT_DIR"
norad init local-pilot \
  --output-dir "$NORAD_INPUT_DIR" \
  --execute

test -f "$NORAD_INPUT_DIR/starter-set.manifest.tsv"
NORAD_REQUEST_PATH="$NORAD_INPUT_DIR/request.yaml"
NORAD_SLURM_WRAPPER="$NORAD_INPUT_DIR/run-in-slurm.sh"
```

The completion manifest is published last. Preserve a partial generated
directory without that manifest for inspection; choose a new absent directory
instead of rerunning over it. The manifest proves the initial starter
publication only; the expected edits below intentionally make its recorded
starter hashes historical rather than a current input attestation.

The generated layout is:

```text
norad-inputs/
|-- request.yaml
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
edit `request.yaml`, `samples.tsv`, and `partitions.tsv`:

```sh
test ! -e "$NORAD_INPUT_DIR/inputs" &&
mkdir -m 700 "$NORAD_INPUT_DIR/inputs" &&
mkdir -m 700 \
  "$NORAD_INPUT_DIR/inputs/reads" \
  "$NORAD_INPUT_DIR/inputs/reference" \
  "$NORAD_INPUT_DIR/inputs/regions"
```

1. Give the request stable reference, cohort, and analysis IDs; point it to the
   matching FASTA/GTF; select STAR-index parameters and analysis policy.
2. Give every sample an explicit R1/R2 FASTQ, condition, replicate, and
   strandedness declaration. Each of at least two replicate strata needs
   exactly one control and one treatment row. Pairing comes from `replicate`,
   not row order or sample names.
3. Select one or more nonoverlapping genomic partitions using contigs present
   in the reference. Start small for the first real-runtime check.

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
NORAD_RUNTIME_PROFILE_PATH="$NORAD_INPUT_DIR/runtime.selected.tsv"

test ! -e "$NORAD_RUNTIME_PROFILE_PATH" && (
  set -C
  norad prepare local-pilot-runtime \
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
    > "$NORAD_RUNTIME_PROFILE_PATH"
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
whose `NORAD_EXECUTE=0` job runs the same validation, doctor, and no-write plan
inside its allocation.

Run the read-only intake validator first:

```sh
norad validate local-pilot-request --request "$NORAD_REQUEST_PATH"
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
NORAD_REFERENCE_FASTA=/absolute/path/from/request/to/reference.fa
norad inspect storage-qualification \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --reference-fasta "$NORAD_REFERENCE_FASTA" --phase compute
# Repeat the same command with --execute inside the allocation.
norad inspect storage-qualification \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --reference-fasta "$NORAD_REFERENCE_FASTA" --phase finalize
# Repeat the same command with --execute after the allocation has ended.
```

Doctor rejects missing, failed, stale, or mismatched final qualification. A
node-local workspace is not supported unless the same qualification establishes
its durable retention path.

## 6. Require full runtime `READY`

The doctor safely re-admits the request and source files plus the workspace
plan, checkout, locked workflow, tools, jar, R project/library, and namespaces:

```sh
norad doctor local-pilot \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
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

`norad run` is a dry run unless `--execute` is present:

```sh
norad run \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Review the deterministic run ID and run root, workflow-attempt identity,
expanded owner-job count, three reporting transactions, Snakemake command, and
each public owner producer/validator command. A successful plan ends by saying
that no workspace state was written.

Copy the exact run root printed by the plan:

```sh
NORAD_RUN_ROOT=/absolute/path/to/norad-workspace/runs/run-DIGEST
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
  NORAD_CONTROL_DIR="$(mktemp -d \
    "$NORAD_OPERATOR_ROOT/.norad-control.XXXXXX")" || exit 1
  NORAD_CONTROL_LOG="$NORAD_CONTROL_DIR/norad-run-control.log"
  printf 'Control log: %s\n' "$NORAD_CONTROL_LOG"
  norad run \
    --request "$NORAD_REQUEST_PATH" \
    --workspace "$NORAD_WORKSPACE_PATH" \
    --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH" \
    --execute 2>&1 | tee "$NORAD_CONTROL_LOG"
)
```

### One SLURM batch allocation

Use the executable `run-in-slurm.sh` published by `norad init local-pilot`.
The generated wrapper is the supported single-allocation starter: submission
mode validates every required value, requests one node/task, publishes exact
`%j` stream paths, and resubmits itself as the job body. The job initializes
modules, enters the selected checkout, runs input/runtime preflight, and then
uses the public local executor.

Bind the site's **actual** scheduler values, module mode, and writable compute
scratch parent. There are no portable defaults:

```sh
NORAD_LOG_DIR="$NORAD_OPERATOR_ROOT/norad-slurm-logs"
test ! -e "$NORAD_LOG_DIR" && mkdir -m 700 "$NORAD_LOG_DIR"

NORAD_SLURM_ACCOUNT=replace-with-site-account
NORAD_SLURM_PARTITION=replace-with-site-partition
NORAD_SLURM_QOS=replace-with-site-qos
NORAD_SLURM_CPUS=4
NORAD_SLURM_MEMORY=site-default
NORAD_SLURM_TIME=replace-with-reviewed-walltime
NORAD_SOURCE_CHECKOUT="$NORAD_REPO"
NORAD_PYTHON="$NORAD_PY"
NORAD_REQUEST="$NORAD_REQUEST_PATH"
NORAD_WORKSPACE="$NORAD_WORKSPACE_PATH"
NORAD_RUNTIME_PROFILE="$NORAD_RUNTIME_PROFILE_PATH"
NORAD_MODULE_MODE=none
NORAD_MODULE_INIT=
NORAD_MODULES=
NORAD_SCRATCH_PARENT=/absolute/writable/compute-scratch-parent
NORAD_EXECUTE=0

export NORAD_SLURM_ACCOUNT NORAD_SLURM_PARTITION NORAD_SLURM_QOS
export NORAD_SLURM_CPUS
export NORAD_SLURM_MEMORY NORAD_SLURM_TIME NORAD_LOG_DIR
export NORAD_SOURCE_CHECKOUT NORAD_PYTHON NORAD_REQUEST NORAD_WORKSPACE
export NORAD_RUNTIME_PROFILE NORAD_MODULE_MODE NORAD_MODULE_INIT NORAD_MODULES
export NORAD_SCRATCH_PARENT NORAD_EXECUTE

"$NORAD_SLURM_WRAPPER"
```

`NORAD_SLURM_MEMORY=site-default` emits no `--mem`; an explicit Slurm size
is passed exactly once. `NORAD_MODULE_MODE=none` requires empty module values
and uses the absolute runtime paths unchanged. Use `exact` only with a real
nonsymlink module-init file and a colon-separated exact module list.
`NORAD_SCRATCH_PARENT` must already be a real writable compute-node directory;
the job creates a private mode-`700` child, exports it as `TMPDIR`, logs its
filesystem/capacity, and removes it at exit. The wrapper installs nothing. The
wrapper passes `NORAD_SLURM_CPUS` only as an allocation assertion. The request
remains the sole resource-plan authority, and execution fails if its
`workflow_cores` exceeds the scheduler allocation.

The first submission uses `NORAD_EXECUTE=0`: it performs compute-context
preflight and prints the complete no-write workflow plan in the job log. Copy
the printed job ID, wait for both streams, and confirm scheduler exit plus the
plan. Copy the exact run root printed in that completed dry-run log into the
shell that will submit and inspect the execution:

```sh
NORAD_RUN_ROOT=/absolute/path/printed/by/the/dry-run/plan
case "$NORAD_RUN_ROOT" in
  /*/runs/run-*) ;;
  *) printf 'Invalid NORAD_RUN_ROOT: %s\n' "$NORAD_RUN_ROOT" >&2; false ;;
esac
export NORAD_RUN_ROOT
```

Do not infer this value from the job ID or workspace name. Only after the
sanity check succeeds should you submit the execution job with the otherwise
identical values:

```sh
NORAD_EXECUTE=1
export NORAD_EXECUTE
"$NORAD_SLURM_WRAPPER"
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
tail -n +1 -F /exact/path/to/norad-run-control.log
```

For a submitted SLURM job, run this from the login/head node. Wait for SLURM to
create both streams before tailing them. The loop also stops if the allocation
becomes terminal without publishing both paths, instead of waiting forever:

```sh
job_id=replace-with-printed-job-id
NORAD_LOG_DIR=/absolute/path/to/norad-slurm-logs

stdout="$NORAD_LOG_DIR/norad-local-pilot-$job_id.out"
stderr="$NORAD_LOG_DIR/norad-local-pilot-$job_id.err"
while [[ ! -e "$stdout" || ! -e "$stderr" ]]; do
  state="$(sacct -X -n -P -j "$job_id" --format=State 2>/dev/null |
    awk -F'|' 'NF {print $1; exit}')"
  case "$state" in
    BOOT_FAIL|CANCELLED|COMPLETED|DEADLINE|FAILED|NODE_FAIL|OUT_OF_MEMORY|PREEMPTED|REVOKED|SPECIAL_EXIT|TIMEOUT)
      printf 'Job %s became %s before both log streams appeared.\n' \
        "$job_id" "$state" >&2
      break
      ;;
  esac
  squeue -j "$job_id"
  sleep 2
done
if [[ -e "$stdout" && -e "$stderr" ]]; then
  tail -n +1 -F "$stdout" "$stderr"
else
  sacct -X -j "$job_id" \
    --format=JobID,JobName,State,ExitCode,Elapsed,NodeList
  false
fi
```

Press Control-C to stop `tail`; that does not cancel the job. Check scheduler
state separately:

```sh
squeue -j "$job_id"
sacct -X -j "$job_id" \
  --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
```

NORAD inspection is read-only and derives state from immutable records rather
than `.snakemake` metadata. Run it only on a host where the exact workspace path
is available under the supported filesystem contract. A login node that can see
only the shared scheduler logs cannot inspect or collect a node-local workspace;
the generated wrapper does not copy results. Arrange a reviewed site-native
retention/transfer path before execution if the workspace will otherwise become
unreachable when the allocation ends.

Before inspecting from a new terminal, repeat Step 1's `cd`, `NORAD_PY`, and
`norad` function setup, then export the exact `NORAD_RUN_ROOT` copied from the
dry-run plan. Tailing the scheduler streams requires only `job_id` and
`NORAD_LOG_DIR`; running NORAD requires the controlled checkout setup too.

```sh
norad inspect local-pilot-run --run-root "$NORAD_RUN_ROOT"
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
| Standalone stage wrappers | Native stage outputs and validation TSVs; no orchestration report or adoption |
| `norad run` | Attempts, verified records, artifact index, run summary, and automatic HTML report |
| `norad build report` | Rebuild from an existing canonical run summary; never adopt standalone outputs |

The reporting sequence is part of the orchestrated workflow. Run a final
inspection:

```sh
norad inspect local-pilot-run --run-root "$NORAD_RUN_ROOT"
```

Successful automatic completion prints:

```text
State: local_pipeline_complete
Local pipeline complete: yes
```

Compute the exact report path without searching the tree:

```sh
NORAD_RUN_ID="${NORAD_RUN_ROOT##*/}"
NORAD_REPORT_PATH="$NORAD_RUN_ROOT/products/report/$NORAD_RUN_ID/$NORAD_RUN_ID.run_report.html"
test -f "$NORAD_REPORT_PATH" && printf '%s\n' "$NORAD_REPORT_PATH"
```

Copy the self-contained HTML to a trusted workstation or open it with the
local browser allowed by your environment. The report is an evidence view of
the admitted run; its presence alone is not completion proof.

### Read the computational results

The report opens by default to `Computational results`, headed
`Computational results — not scientifically adjudicated`, with a prominent
matching notice. It shows Step `09` counts and thresholds, significant
candidates first, all candidates second, and then `Key per-sample QC`.

Both candidate views display at most 250 rows so a large run remains usable.
Each view states its full source row count and whether it was truncated, plus
the exact source path, SHA-256, and byte size. The native TSV is the complete
table. The renderer accepts only the exact complete primary-analysis Step `09`
all-sites/significant-sites/summary trio named by run-summary artifact records,
and only after re-admitting the exact all-pass Step `09` owner-validation
report. It does not search for a plausible filename, infer validation, or
recompute a missing result.

Use the run summary and report together:

- `candidate_count` is the Step `08` SNV universe that reached Step `09`.
- `successfully_tested_count` counts target-change candidates with usable
  paired counts and a nondegenerate CMH table.
- `call_status` explains each result: `not_tested`, `below_mean_dp`,
  `background_not_passed`, `fdr_not_met`, `effect_not_met`,
  `significant_up`, or `significant_down`.
- `DP__sample`, `AD__sample`, and `AF__sample` are per-sample depth, alternate
  depth, and alternate fraction.
- `mean_control_af`, `mean_treatment_af`, and
  `treatment_control_difference` show the direction and size of the observed
  mean allele-fraction change.
- `cmh_p_value` is the paired CMH p-value; `cmh_fdr_bh` is its global
  Benjamini-Hochberg adjustment; `common_odds_ratio` is the shared odds-ratio
  estimate across replicate strata.

Treat threshold-passing rows as computational candidates, not validated
editing sites. `FWD_like` and `REV_like` are fixed SAM-flag group labels; they
are not biological strand, sense, or antisense claims. Candidate review,
adjudication, and biological interpretation remain external work-process
records and never alter or promote NORAD's computational tables.

The complete native tables remain under:

```text
<run-root>/results/editing/<analysis-id>/<analysis-id>.cmh_all_sites.tsv
<run-root>/results/editing/<analysis-id>/<analysis-id>.cmh_significant_sites.tsv
<run-root>/results/editing/<analysis-id>/<analysis-id>.cmh_summary.tsv
<run-root>/results/editing/<analysis-id>/<analysis-id>.mutation_spectrum.tsv
<run-root>/results/editing/<analysis-id>/<analysis-id>.mutation_spectrum.pdf
<run-root>/results/editing/<analysis-id>/<analysis-id>.depth_delta.pdf
```

## 11. Keep the whole run root

Output presence is not the completion authority. Inspection re-admits records,
hashes, receipts, locks, task attempts, and semantic validation.

| Location | Durable contents |
| --- | --- |
| `<run-root>/contract/` | Normalized request, fixed profile, admitted runtime snapshot, reporting contracts/policy/inventory, workflow configs, and task dispatches. |
| `<run-root>/attempts/<workflow-attempt-id>/` | Attempt record, per-owner task attempts and terminal logs, and the attempt receipt published last. |
| `<run-root>/state/task-starts/` | Immutable producer-entry records. |
| `<run-root>/state/verified/` | Hash-bound successful owner-task records. |
| `<run-root>/state/reporting/` | Start and verified records for artifact index, run summary, and HTML report. |
| `<run-root>/results/` | Native scientific outputs, QC evidence, intermediates, and ranked-candidate products. |
| `<run-root>/products/artifact-summary/<run-id>/records/` | One canonical record per declared artifact, including explicit incomplete/unavailable states. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.artifacts.tsv` | Deterministic artifact index. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.artifact_receipt.tsv` | Artifact-index receipt, published last for that transaction. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Canonical machine-readable run summary. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | Tabular run-status summary. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC view. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary_receipt.tsv` | Run-summary receipt, published last. |
| `<run-root>/products/report/<run-id>/<run-id>.run_report.html` | Self-contained Jinja HTML report. |
| `<run-root>/products/report/<run-id>/<run-id>.run_summary.tsv` | Report-renderer summary table. |
| `<run-root>/products/report/<run-id>/<run-id>.report_outputs.tsv` | HTML-report output receipt, published last. |
| Beside the declared FASTA | Step `00c` `.fai` and `.dict`; the only owner outputs outside the run root. |

Locks, released-lock evidence, partials, backups, task logs, and failed attempts
are not disposable just because later outputs exist.

## 12. Resume safely

Resume only when inspection prints both `State: resume_available` and
`Resume available: yes`. Review the no-write resume plan:

```sh
norad resume \
  --run-root "$NORAD_RUN_ROOT" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Then execute that admitted plan:

```sh
norad resume \
  --run-root "$NORAD_RUN_ROOT" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH" \
  --execute
```

Only a verified failure or interruption **between** owner tasks is
automatically resumable. A completed run refuses resume. A scope that crossed
producer entry without verified completion is blocked; NORAD exposes no force,
unlock, cleanup, metadata-repair, or automatic owner retry. Preserve the whole
run root and follow [troubleshooting](docs/operations/TROUBLESHOOTING.md).

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

