# Runbook

This file contains genuinely cross-cutting NORAD commands. Exact producer,
validator, scheduler, test, diagnostic, and recovery commands live in the
adjacent README of the functional owner linked from the
[architecture index](../architecture/README.md).

Dry-runs, fixtures, availability probes, scheduler exits, and synthetic reports
do not establish production, cluster, scientific-review, or biological proof.
Execution, dependency restoration, cleanup, and publication require explicit
authority.

## Checkout and site orientation

Run from the intended checkout and record its identity:

```bash
git rev-parse --show-toplevel
pwd -P
git branch --show-current
git rev-parse HEAD
git status --short
```

Resolve the checkout and every data/runtime path in the intended login or
batch context. Never treat a remembered path, shell alias, module name, or
login-node `PATH` as current compute-node evidence.

Before scheduler work:

```bash
hostname
command -v sbatch
command -v squeue
sinfo
module list 2>&1 || true
mkdir -p logs
```

The login node is for Git, small transfers, editing, inspection, submission,
and small smoke checks. Never run `norad run --execute`, STAR, BAM processing,
mpileup, or R analysis there. The public local pilot runs inside one approved
compute-node allocation; individual owner operations may instead use the
owner-local `.slurm` entry points. Ordinary wrappers use `TMPDIR=/tmp`; the
Step `05` owner requires its documented project-storage temporary directory.

## Owner command routes

| Area | Exact command owner |
| --- | --- |
| Sample admission | [`sample_manifest_admission`](../../src/norad/ingestion/sample_manifest_admission/README.md) |
| Reference preparation and Steps `01`–`08` | [`stages`](../../src/norad/stages/README.md) |
| Paired CMH ranking | [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/paired_cmh_candidate_ranking/README.md) |
| Runtime, reference, storage, and QC evidence | [`evidence`](../../src/norad/evidence/README.md); runtime inspection route `python -I -m norad inspect runtime-availability`; storage inspection route `python -I -m norad inspect storage-inventory`; reference reconciliation route `python -I -m norad reconcile reference-provenance` |
| Artifact schemas | [`artifact contracts`](../../src/norad/contracts/artifacts/README.md); installed route `python -I -m norad validate artifact-contracts` |
| Artifact index, run summary, and reports | [`reporting`](../../src/norad/reporting/README.md); each installed build route requires explicit, distinct `--source-checkout` and `--artifact-source-root` authorities |
| Synthetic demonstration | [`demo`](../demo/README.md) |

Each owner README supplies supported help, dry-run, execute, scheduler, focused
test, diagnostics, and recovery routes when those surfaces exist. Its adjacent
`CONTRACT.md` owns exact inputs, outputs, checks, and evidence limits.

## Local-pilot readiness

For the first-time researcher journey from clone and matched starters through
outputs and safe resume, begin with the root [`README`](../../README.md).
This section remains the compact operator command reference.

Create the matched request/manifests/runtime/wrapper set in operator-managed
storage outside the checkout. Initialization is dry-run-first and the selected
output directory must be absent:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad init local-pilot \
  --output-dir /absolute/absent/input-directory
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad init local-pilot \
  --output-dir /absolute/absent/input-directory \
  --execute
```

The execute form publishes `request.yaml`, `samples.tsv`, `partitions.tsv`,
`runtime.tsv`, executable `run-in-slurm.sh`, then
`starter-set.manifest.tsv` last. [`configs/README.md`](../../configs/README.md)
owns every field and preparation rule. For a real-tool smoke fixture, use the
equivalent dry-run/execute pair with `init synthetic-local-pilot`; it publishes
its deterministic request/data and `fixture.manifest.json` last.

Before runtime probes, validate the selected input set without writing:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad validate \
  local-pilot-request --request /absolute/path/to/request.yaml
```

This streams file hashes, validates paired strata, reconciles FASTA/GTF
contigs/bounds, and checks partition-selector bounds. It runs no scientific
tool. Use it on the intended compute host, not a login node for a large input
set.

Prepare a fixed runtime profile to a new absent file with
`norad prepare local-pilot-runtime`. It requires explicit canonical Java,
Picard-jar, Rscript, and `renv`-library paths and accepts explicit `--bash`,
`--star`, `--samtools`, `--gatk`, `--bcftools`, `--infer-experiment`, and
`--gunzip` paths. Omitted ordinary tools are accepted only when `PATH` resolves
one distinct executable. The command prints TSV to stdout and performs no
version probe, file write, install, or repair; never redirect it over the
generated `runtime.tsv`.

After `uv sync --locked --group workflow`, separately authorized science-tool/R
setup, and runtime-profile preparation, inspect one request and workspace plan:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad doctor local-pilot \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

The doctor is always read-only. It does not run `uv`, restore `renv`, load
modules, create the workspace, or execute the workflow. Exit `0` means its
exact local readiness roster passed; exit `1` prints readiness blockers and
remediation; exit `2` means the request/profile/path boundary is malformed or
unsafe. A `READY` result establishes only those bounded probes in that exact
context; it does not establish workflow completion, sufficient capacity,
scientific review, or biological evidence.

## Local-pilot execution

After the readiness command returns `READY`, plan the complete fixed profile.
The default is a strict no-write dry-run that prints the deterministic run ID,
run root, immutable attempt identity, Snakemake argv, and every public owner
producer/validator command:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

Review that output, then execute the identical admitted request by adding
`--execute`:

Before execution, confirm that the declared reference FASTA directory is the
intended writable sidecar authority. Step `00c` deliberately creates or reuses
`<reference-fasta>.fai` and `<reference-stem>.dict` beside that external FASTA;
those two files are the only owner outputs outside the run root.
Even complete-pair reuse enters Step `00c` and transiently creates its adjacent
owner lock; generation may also create adjacent run-token staging paths.
Controlled success removes owned transient state. Retained lock/staging paths
are blocking recovery evidence, and a partial pre-existing pair is rejected
before producer entry.

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv \
  --execute
```

On a workstation or interactive compute allocation, retain the continuous
control stream and its true pipeline exit:

```bash
set -o pipefail
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run \
  --request /absolute/path/to/request.yaml \
  --workspace /absolute/path/to/workspace \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv \
  --execute 2>&1 | tee /absolute/path/to/private/norad-control.log
```

For scheduled execution, use the executable `run-in-slurm.sh` generated by
`norad init local-pilot`; do not maintain an untested copy of its job body. Bind
its required `NORAD_SLURM_ACCOUNT`, `NORAD_SLURM_PARTITION`,
`NORAD_SLURM_QOS`, `NORAD_SLURM_CPUS=1`, `NORAD_SLURM_MEMORY`,
`NORAD_SLURM_TIME`, existing `NORAD_LOG_DIR`, checkout/Python/request/workspace/
runtime-profile paths, real module-init file, and colon-separated module list.
Submit first with `NORAD_EXECUTE=0`. Inside that allocation the generated body
loads modules, validates the request, runs doctor, and prints the no-write plan
in that order. Confirm the job, streams, and plan, then resubmit the same values
with `NORAD_EXECUTE=1`.

This is one local process inside an allocation, not distributed NORAD or public
SLURM orchestration. Create the declared log directory before invoking the
wrapper; SLURM opens its streams before the job body runs. The wrapper prints
the exact job ID and
`$NORAD_LOG_DIR/norad-local-pilot-$job_id.{out,err}` paths.
Shared scheduler streams may be suitable for head-node tailing without making
the NORAD workspace safe. The workspace and Step `00c` reference-sidecar
transaction root still require durable local POSIX `flock` and same-filesystem
hard-link semantics. If only unvalidated NFS/distributed storage is available
for those mutation roots, stop; job allocation is not filesystem validation.

From the login node, wait until both `%j` streams exist, then tail them:

```bash
job_id=123456
NORAD_LOG_DIR=/absolute/path/to/norad-slurm-logs
while [[ ! -e "$NORAD_LOG_DIR/norad-local-pilot-$job_id.out" ||
         ! -e "$NORAD_LOG_DIR/norad-local-pilot-$job_id.err" ]]; do
  squeue -j "$job_id"
  sleep 2
done
tail -n +1 -F \
  "$NORAD_LOG_DIR/norad-local-pilot-$job_id.out" \
  "$NORAD_LOG_DIR/norad-local-pilot-$job_id.err"
```

Control-C stops `tail` but does not cancel the job. Confirm state independently
with `squeue`, `sacct`, and NORAD inspection. Run NORAD inspection only where
the exact workspace path is available under the supported filesystem contract;
shared scheduler logs alone do not expose a node-local workspace, and the
generated wrapper performs no result transfer. Owner task logs publish at their
terminal task boundary; the retained top-level stream is the live-tail surface.

Inspect state from NORAD evidence rather than `.snakemake` metadata:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad inspect \
  local-pilot-run \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST
```

Only a failed or interrupted between-task boundary is automatically resumable.
Plan resume first, then repeat with `--execute` after reviewing the commands:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv

.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv \
  --execute
```

A scope that crossed producer entry without verified completion is blocked,
not automatically retried or cleaned. A completed run refuses resume and a
second initial run refuses the existing run root. The public commands expose no
force, unlock, metadata-cleanup, alternate-profile, or raw engine options.
Current execution is source-checkout-bound and local. The B6 fresh-clone proof
and any later real-tool or batch demonstrations have different evidence
ceilings. Consult [`HANDOFF.md`](HANDOFF.md) for the exact current commit,
commands, artifacts, and evidence; do not infer them from this runbook.

## Task status

The backlog is coarse and execution cards are created just in time. Inspect the
derived view:

```bash
./scripts/git_orchestration/task_status.py \
  --repo "$(git rev-parse --show-toplevel)"
```

Selection adds a temporary JIT card under `docs/tasks/cards/`; completion or
pause removes it. See the [workflow kernel](WORKFLOW.md) and [task
registry](../tasks/README.md).

## Local validation

Use focused tests during implementation:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
```

For package metadata, wheel isolation, installed commands, and resources:

```bash
uv lock --check
uv sync --locked --check
.venv/bin/python -m pytest -q tests/test_package_distribution.py
```

For shell and SLURM behavior without replaying Python validator suites:

```bash
make -s shell-test
```

The complete gate performs the same read-only environment check before starting
its validation lanes. A mismatch stops with instructions to run the explicit
`uv sync --locked` restoration command; validation never synchronizes the
environment itself.

Run the complete local gate once against a final executable state:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks
```

Use serial or verbose diagnosis only when needed:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks VALIDATION_ARGS=--serial
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks VALIDATION_ARGS=--verbose
```

The assembled gate has five evidence lanes. Static preflight runs first and
owns configuration, documentation, syntax, compilation, and manifest checks.
Python coverage then owns Python behavior, branch/subprocess coverage, and
Jinja HTML reporting while excluding the isolated-wheel and SLURM-wrapper
suites. The wheel lane owns installed-package integrity. The shell/SLURM lane
owns shell behavior and scheduler-wrapper contracts. Guarded real R remains
separate because Python and shell substitutes do not execute R semantics.
Independent lanes run with bounded concurrency after preflight; `--serial`
selects one top-level lane and one Python worker.

Quiet successes discard their temporary logs. A failed, interrupted, or
peer-cancelled lane retains its log and prints its location; first failure
terminates the other running process groups and preserves the failing status.
The gate emits a human summary only. It has no machine-result artifact because
none had an active consumer.

A standalone documentation package instead uses:

```bash
git diff --check
make -s documentation-check
git status --short
git diff --name-status
```

The documentation gate checks local document structure, mechanically derived
ownership, compact backlog dependencies, and JIT-card structure. It does not
validate general Markdown links, anchors, or diagrams' inbound references.

These checks establish local structural/test evidence only. Guarded R adds
real local runtime evidence for its named fixtures. Neither result establishes
CSU scheduler execution, production artifacts, scientific review, validated
editing sites, or biological interpretation. Use focused checks per approved
slice and run the assembled gate once after the final executable state is
settled; rerun it only for a concrete failure-driven reason.

## Explicit dependency setup

Restoration is an operator action and never occurs from compute, validation,
rendering, or scheduler code:

```bash
uv sync --locked
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
make lint
```

`pyproject.toml` owns direct runtime and developer dependencies, and `uv.lock`
owns their exact resolved graph. `uv sync --locked` includes the `dev` group and
installs the project itself into `.venv`; a stale lock is an error rather than
permission to relock. Provision `uv` separately—repository setup does not
download or install it.

Guarded local R checks are:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

They opt into the repository library with `NORAD_USE_RENV=1`, disable automatic
snapshots and the `renv` sandbox, and establish local configured-environment
evidence only.

`r-check` treats the reviewed `renv.lock` as the reproducibility authority; it
does not require every package to match the newest version advertised by an
upstream repository. Run `BiocManager::valid(checkBuilt = FALSE)` separately
from a guarded project R session when an explicitly authorized dependency
maintenance review needs current online freshness evidence. Never restore,
snapshot, or update the lock merely to turn a freshness result green.

## Manual job inspection

```bash
ls -ltr logs | tail
squeue -u "$USER"
squeue -j <JOBID>
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

While a job runs, inspect only its declared output root. Bind the checkout,
command, inputs, job ID, accounting, stdout/stderr, outputs, validation record,
and evidence ceiling to the same attempt. Empty stderr, `COMPLETED 0:0`, or
visible output alone is not validation.

## Cluster execution and promotion

Operate only from an explicitly approved clean commit and input set:

```bash
cd <approved-checkout>
git branch --show-current
git rev-parse HEAD
test -z "$(git status --porcelain=v1)"
mkdir -p logs
```

Then:

1. Open the owner README and bind every explicit input, tool, manifest, output
   root, and execution mode.
2. Inspect its dry-run or preflight when supported.
3. Submit or execute only under the approved authority.
4. Inspect scheduler accounting, logs, native outputs, owner validation rows,
   locks, staging, backups, and recovery state together.
5. Record commit, command/job ID, input identities and hashes, outputs and
   hashes, validator result, and evidence ceiling before downstream promotion.

Promotion is upstream-sequential. Never delete a foreign lock, mix attempts,
hand-edit a receipt, infer completion from a marker alone, or advance a
downstream owner before required upstream evidence passes. Use
[troubleshooting](TROUBLESHOOTING.md) before cleanup or retry.
