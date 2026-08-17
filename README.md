# NORAD: evidence-bound RNA-seq candidate workflow

NORAD is an evidence-bound workflow for paired-end RNA-seq alignment, QC,
mechanical read-orientation partitioning, cohort mpileup, candidate annotation,
and paired CMH ranking. You provide declared reads, a matching FASTA/GTF
reference, paired experimental strata, genomic partitions, analysis thresholds,
and exact scientific-tool identities. NORAD produces validated native outputs,
an immutable task history, a deterministic artifact index, a machine-readable
run summary, QC tables, and a self-contained HTML report.

NORAD is alpha research software, not a clinical or diagnostic system. It is
not a general RNA-seq expression workflow: it does not demultiplex, trim or
quality-filter reads, merge technical lanes, quantify transcripts, test
differential expression, discover samples, or infer experimental pairing.
Provide analysis-ready paired FASTQs and author the intended design explicitly.

The automatic workflow produces **CMH-ranked computational candidates**. It
does not prove that a candidate is an RNA-editing site, infer biological strand
from the mechanical orientation labels, or make a biological conclusion.
Candidate review, adjudication, and biological interpretation are external
work-process records. NORAD does not model them as pipeline steps, gates,
artifacts, or completion states.

## What happens to the data

| Step | Scope | Operation | Principal result |
| --- | --- | --- | --- |
| `00a` | Reference | Build and validate a STAR genome index. | STAR index directory |
| `00b` | Reference | Convert the declared GTF deterministically to BED12. | BED12 annotation |
| `00c` | Reference | Create or re-admit the FASTA index and sequence dictionary. | `.fai` and `.dict` beside the FASTA |
| `01` | Each sample | Align paired reads with STAR. | Coordinate-sorted STAR BAM |
| `02` | Each sample | Construct and validate a canonical BAM/BAI pair. | Canonical BAM and index |
| `02b` | Each sample | Collect flagstat, quickcheck, and alignment QC evidence. | QC evidence branch |
| `03` | Each sample | Measure paired-read orientation with RSeQC. | Orientation evidence branch |
| `04` | Each sample | Mark duplicates with Picard. | Duplicate-marked BAM, BAI, and metrics |
| `05` | Each sample | Apply GATK `SplitNCigarReads`. | Split BAM and BAI |
| `06` | Each sample | Partition reads into legacy mechanical flag groups. | `FWD_like` and `REV_like` BAM/BAI pairs |
| `07` | Each partition | Run cohort bcftools mpileup for both mechanical groups. | Two VCFs and a bound receipt |
| `08` | Cohort | Normalize SNV candidates, attach per-sample counts and GTF overlaps. | Candidate, input-receipt, and QC tables |
| `09` | Analysis | Perform paired two-sided CMH tests and global BH correction. | All-sites, significant-sites, summary, spectrum, and plots |
| Reporting | Run | Index artifacts, assemble the run summary, and render HTML. | Report plus receipt-last publication |

Steps `02b` and `03` are required QC leaves but do not gate downstream
scientific computation. External review or adjudication may use NORAD's
computational outputs and provenance, but it is not part of `norad run`.

The fixed graph contains `3 + 7S + P + 2` scientific-owner jobs for `S`
samples and `P` genomic partitions. The four-sample, one-partition starter
therefore expands to 34 jobs, followed by three reporting transactions.

## Supported execution boundary

Read this before installing:

- The public runtime target is a Linux/POSIX host with Python `3.11` or newer,
  Git, GNU Make, `uv`, and the scientific runtime listed below.
- The workflow uses Snakemake's **single-host local executor**. It defaults to
  the request's explicit resource plan: `workflow_cores` declares total CPU
  capacity, `sample_concurrency` bounds concurrent sample owners, and
  `step_threads` assigns threads only to Steps `00a`, `01`, `02`, `06`, and
  `08`. NORAD neither submits SLURM jobs nor distributes work across nodes.
- Run it on a suitably provisioned Linux workstation, or run the same local
  process inside **one** batch allocation on **one** compute node. Never run the
  scientific workflow on a cluster login/head node; use that node only to
  clone, edit, transfer small files, submit, inspect, and tail logs.
- One cooperative user and a POSIX local filesystem with working advisory
  `flock` and same-filesystem hard links are required for the workspace and
  reference-sidecar transactions. NFS and other network/distributed-filesystem
  locking semantics are not currently supported or claimed, even when a site
  happens to provide them.
- Local-pilot inputs, workspace, control logs, and results stay outside the Git
  checkout. The locked ignored `.venv/`, the default ignored `renv/library/`,
  and the report-only demo's ignored `results/demo-report-jinja/` are sanctioned
  checkout-local exceptions; an already provisioned R library may instead be
  selected explicitly. The doctor requires tracked checkout content to be clean
  and binds its exact commit and installed package bytes.
- NORAD does not download data, install tools, load modules, restore R
  packages, estimate capacity, force retries, delete locks, or repair outputs.

Capacity depends on reference size, read count, and selected partitions. Plan
for the STAR index and several BAM generations per sample, plus orientation
BAMs, VCFs, logs, and immutable recovery evidence. Before a real run, inspect
the input size and destination capacity on the execution host:

```sh
du -sh /absolute/path/to/norad-inputs/inputs
df -h /absolute/path/to/operator-managed-storage
free -h
```

`free` is Linux-specific. `READY` confirms bounded admission checks only; it is
not a memory, storage, wall-time, throughput, scheduler, or science estimate.
For an unfamiliar reference or cohort, begin with a small declared region and
representative samples before authorizing the full analysis.

## Choose a first run

- **Synthetic installation check:** use `norad init synthetic-local-pilot` in
  Path A below. It creates small explicit inputs outside the repository and
  still requires the real admitted scientific runtime. A synthetic result
  demonstrates that exact runtime and request, not production or biological
  validity.
- **Your data:** follow the full quickstart below and replace every starter
  identity and path with your own declared inputs.
- **Report-only preview:** run `make demo-report` after installation and follow
  [`docs/demo/README.md`](docs/demo/README.md). This renders bundled reporting
  fixtures and does not execute ingestion, STAR, samtools, GATK, Picard,
  RSeQC, bcftools, R analysis, or the workflow.

The exact validation evidence at the current commit is recorded in
[`HANDOFF.md`](docs/operations/HANDOFF.md). A demo, dry run, synthetic fixture,
successful job, or report must not be promoted beyond the evidence it actually
establishes.

## Quickstart: clone to an admitted plan

### 1. Clone and install the locked Python workflow

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

Install that ref's locked Python workflow:

```sh
uv sync --locked --group workflow
```

This installs NORAD and locked Snakemake `9.25.1` into `.venv`. It does not
install the scientific tools or R packages.

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

### 2. Provide the scientific runtime

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
SHA-256 identities. An environment-module name is not sufficient. On a
cluster, load the selected modules inside the batch job and ensure the same
absolute targets are visible there; head-node availability does not establish
compute-node availability.

The exact clean checkout is also the guarded `renv` project. It requires an
existing canonical R library with the lock-selected `renv` and Step `08`
namespaces. Explicitly restoring packages is a separate operator-authorized
mutation:

```sh
RSCRIPT_BIN=/absolute/path/to/Rscript make r-restore
RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

If an approved canonical library already exists, do not restore another one:

```sh
RENV_PATHS_LIBRARY=/absolute/path/to/canonical/renv-library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

Doctor and execution never restore, bootstrap, install, download, or repair a
runtime.

### 3. Initialize either synthetic or real inputs

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

#### Path A: deterministic synthetic science smoke

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

#### Path B: your data

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

### 4. Prepare one explicit runtime profile

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

### 5. Validate data compatibility without scientific tools

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

### 6. Require full runtime `READY`

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

### 7. Review the strict no-write plan

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

## Execute on a workstation or one compute node

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

Bind the site's **actual** account, partition, QOS, memory, time, module-init
file, and module names. There are no portable defaults for these values:

```sh
NORAD_LOG_DIR="$NORAD_OPERATOR_ROOT/norad-slurm-logs"
test ! -e "$NORAD_LOG_DIR" && mkdir -m 700 "$NORAD_LOG_DIR"

NORAD_SLURM_ACCOUNT=replace-with-site-account
NORAD_SLURM_PARTITION=replace-with-site-partition
NORAD_SLURM_QOS=replace-with-site-qos
NORAD_SLURM_CPUS=4
NORAD_SLURM_MEMORY=replace-with-reviewed-memory
NORAD_SLURM_TIME=replace-with-reviewed-walltime
NORAD_SOURCE_CHECKOUT="$NORAD_REPO"
NORAD_PYTHON="$NORAD_PY"
NORAD_REQUEST="$NORAD_REQUEST_PATH"
NORAD_WORKSPACE="$NORAD_WORKSPACE_PATH"
NORAD_RUNTIME_PROFILE="$NORAD_RUNTIME_PROFILE_PATH"
NORAD_MODULE_INIT=/absolute/real/path/to/modules-init.sh
NORAD_MODULES=module/name:second/module:third/module
NORAD_EXECUTE=0

export NORAD_SLURM_ACCOUNT NORAD_SLURM_PARTITION NORAD_SLURM_QOS
export NORAD_SLURM_CPUS
export NORAD_SLURM_MEMORY NORAD_SLURM_TIME NORAD_LOG_DIR
export NORAD_SOURCE_CHECKOUT NORAD_PYTHON NORAD_REQUEST NORAD_WORKSPACE
export NORAD_RUNTIME_PROFILE NORAD_MODULE_INIT NORAD_MODULES NORAD_EXECUTE

"$NORAD_SLURM_WRAPPER"
```

`NORAD_MODULES` is a colon-separated list of the exact site modules required
to expose the authored runtime. `NORAD_MODULE_INIT` must be the site's real,
nonsymlink module initialization file. The wrapper rejects commas/newlines and
unsafe module identifiers; it never installs a missing module or tool. The
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

The scheduler's stdout/stderr directory may use the site's supported shared
storage so it can be tailed from the login node. That does **not** qualify the
NORAD workspace or the reference-sidecar directory for network-filesystem
locking. Those mutation roots must satisfy the local POSIX `flock` and
same-filesystem hard-link boundary above, remain durable for the complete run,
and retain their absolute paths. If the cluster offers only unvalidated
NFS/distributed storage for those roots, the public local pilot is not yet a
supported execution path there; stop rather than treating a successful
allocation as filesystem proof.

## Observe the run from another terminal

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

## Confirm completion and find the report

Run a final inspection:

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

## Keep the whole run root

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

## Resume safely

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

## First-run blocker map

| Symptom | Meaning and next action |
| --- | --- |
| `norad` imports from another path | Recreate `NORAD_PY` from this checkout and use the isolated invocation. Do not add `PYTHONPATH`. |
| Checkout is dirty | Review and finish or move tracked edits; doctor binds an exact clean commit. Do not hide relevant changes. |
| Runtime tool is absent or wrong | Install/select it outside NORAD, load modules in the execution context, then update the explicit runtime path. Do not weaken the expected version. |
| Tool exists on login but doctor fails in batch | Probe and author the compute-node-visible canonical path inside the same module environment used by the batch job. |
| R namespace or `renv` library is missing | Perform separately authorized `renv` restoration or select an existing checked canonical library; doctor will not bootstrap it. |
| Request path or TSV is rejected | Correct exact field names, tabs, safe IDs, explicit paths, pairing, and conditions using the [configuration guide](configs/README.md). |
| Workspace parent is rejected | Use an existing canonical writable parent and a single absent child leaf outside the checkout. |
| Reference sidecar pair is partial | Preserve FASTA, FAI, DICT, adjacent locks, and staging. Establish ownership before any recovery; do not regenerate one member ad hoc. |
| SLURM log never appears | Create its parent before `sbatch`, then inspect `squeue`/`sacct` and the exact `%j` path. |
| Inspection says `blocked` | Preserve all evidence and route the failing scope through the owner-specific recovery guide. Do not rerun the initial command. |
| Report labels results `not scientifically adjudicated` | Expected: the report presents computational candidates and provenance only. Keep any external review or interpretation records separate from the run. |

The full [troubleshooting matrix](docs/operations/TROUBLESHOOTING.md) covers
safe evidence preservation and every owner.

## Glossary

| Term | Meaning in NORAD |
| --- | --- |
| `AD` | Alternate-allele read depth reported for one sample/candidate. |
| `AF` | Alternate fraction, normally `AD / DP`, for one sample/candidate. |
| `DP` | Total read depth used for the candidate calculation. |
| Candidate | A computationally represented SNV row. It is not automatically an editing site. |
| CMH | Cochran-Mantel-Haenszel test combining paired replicate strata while retaining their pairing. |
| FDR / BH | Benjamini-Hochberg-adjusted p-value across the tested target-change candidates. |
| Stratum / replicate | One manifest identifier pairing exactly one control and one treatment sample. |
| Common odds ratio | CMH effect estimate shared across the paired strata; values above `1` favor treatment enrichment and below `1` favor control, subject to the declared thresholds. |
| `FWD_like`, `REV_like` | Legacy mechanical SAM-flag groups; not biological strand labels. |
| Computational call | A Step `09` threshold classification such as `significant_up`; still pending scientific adjudication. |
| External review or adjudication | A research work process that may reference NORAD outputs but is not a NORAD step, gate, artifact, or completion state. |
| Create-absent / no-clobber | Publication that requires the destination not to exist and refuses replacement or adoption. |
| Receipt-last | The transaction receipt is published only after its declared payload has been checked; the receipt still must be semantically re-admitted. |
| Run root | The immutable/evidence-bearing directory for one deterministic normalized run ID. |

## Further guidance

| Need | Canonical guide |
| --- | --- |
| Every input and runtime-profile field | [`configs/README.md`](configs/README.md) |
| Public local-pilot boundary | [`src/norad/orchestration/local_pilot/README.md`](src/norad/orchestration/local_pilot/README.md) |
| Compact operator commands | [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md) |
| Evidence-preserving recovery | [`docs/operations/TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md) |
| Optional external scientific-evaluation checklist | [`docs/reference/EXTERNAL_SCIENTIFIC_EVALUATION.md`](docs/reference/EXTERNAL_SCIENTIFIC_EVALUATION.md) |
| Reporting transactions and direct report build | [`src/norad/reporting/README.md`](src/norad/reporting/README.md) |
| Architecture and complete owner DAG | [`docs/architecture/README.md`](docs/architecture/README.md) |
| Current validation evidence and remaining gaps | [`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md) |
| Local test routes | [`tests/README.md`](tests/README.md) |

## License

NORAD is **source-available**, not open-source software. You may use and modify
NORAD without charge for academic, nonprofit, research, and internal commercial
work. You may also commercialize the scientific data, results, reports,
visualizations, interpretations, discoveries, and other outputs produced using
NORAD, and you may charge for research, compute, or analysis services that
deliver those outputs.

You may not sell NORAD itself, including through paid rebranding, licensing, or
sublicensing, or by offering NORAD or substantially equivalent NORAD
functionality as a paid hosted or managed product or service. The complete
terms in [`LICENSE`](LICENSE) control. Third-party software, tools, data, and
references retain their own terms; see [`NOTICE`](NOTICE) and
[`LICENSES/`](LICENSES/).

Do not commit FASTQ, BAM, CRAM, VCF, production result tables, logs,
credentials, restored tools/libraries, or caches. Before deleting ignored data,
results, locks, or logs, establish their owner, active consumers, recovery
state, and retention requirements.
