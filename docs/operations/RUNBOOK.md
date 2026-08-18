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
| Runtime, reference, storage, and QC evidence | [`evidence`](../../src/norad/evidence/README.md); runtime `inspect runtime-availability`; storage `inspect storage-inventory` and `inspect storage-qualification`; reference `reconcile reference-provenance` |
| Artifact schemas | [`artifact contracts`](../../src/norad/contracts/artifacts/README.md); installed route `python -I -m norad validate artifact-contracts` |
| Artifact index, run summary, and reports | [`reporting`](../../src/norad/reporting/README.md); `artifact-index` and `run-summary` are workflow-owned transaction commands, while `build report` is the operator-facing standalone rebuild |
| Synthetic demonstration | [`demo`](../demo/README.md) |

Each owner README supplies supported help, dry-run, execute, scheduler, focused
test, diagnostics, and recovery routes when those surfaces exist. Its adjacent
`CONTRACT.md` owns exact inputs, outputs, checks, and evidence limits.

## Local-pilot lifecycle routes

The complete first-run journey belongs to the
[Quickstart](../../quickstart.md). This runbook retains recurring operator
routes without duplicating its initialization, admission, and execution
walkthrough.

| Need | Canonical route |
| --- | --- |
| Create matched starters and choose synthetic or real inputs | [Quickstart: initialize and ingest](../../quickstart.md#3-initialize-and-ingest-synthetic-or-real-inputs) |
| Prepare the explicit runtime profile | [Quickstart: runtime profile](../../quickstart.md#4-prepare-one-explicit-runtime-profile) and [`configs/README.md`](../../configs/README.md) |
| Qualify storage and obtain runtime `READY` | [Quickstart: compatibility](../../quickstart.md#5-validate-data-compatibility-without-scientific-tools) and [runtime readiness](../../quickstart.md#6-require-full-runtime-ready) |
| Review and execute the fixed workflow | [Quickstart: plan and execution](../../quickstart.md#7-review-the-strict-no-write-plan) |
| Inspect run state or plan a supported resume | Commands below and the [local-pilot owner](../../src/norad/orchestration/local_pilot/README.md) |
| Diagnose blocked, partial, locked, or uncertain state | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |

The lifecycle-generated `run-in-slurm.sh` is the supported whole-run
single-allocation launcher. It runs NORAD's one-host local workflow inside one
approved compute-node allocation; it is not a distributed executor.
Owner-local `.slurm` files are separate supported scheduler entry points for
running one stage. They publish only that owner's native outputs and
validation evidence and never create or adopt an orchestrated run root.

### Recurring inspection and resume

Inspect state from NORAD's admitted records rather than `.snakemake` metadata:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad inspect \
  local-pilot-run \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST
```

Inspection is read-only. Rehashing bound evidence can be expensive, so run it
at meaningful boundaries rather than in a tight polling loop.

Resume is supported only when inspection reports both `State:
resume_available` and `Resume available: yes`. Review the no-write plan first:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume \
  --run-root /absolute/path/to/workspace/runs/run-DIGEST \
  --runtime-profile /absolute/path/to/local_pilot_runtime.tsv
```

Add `--execute` only after reviewing that exact plan. A scope that crossed
producer entry without verified completion remains blocked rather than being
retried or cleaned. A complete run refuses resume, and the public lifecycle
exposes no force, unlock, metadata-cleanup, or raw-engine bypass.

## Resource benchmarking

[`scripts/benchmark_stage_resources.py`](../../scripts/benchmark_stage_resources.py)
is an opt-in harness for comparing resource values on representative data. It
does not invent stage commands or discover inputs. Provide a closed manifest
containing exact setup, producer, and public validator argv arrays; use only
the placeholders `{value}` and `{trial_dir}` where the candidate value and
create-absent trial directory belong:

```yaml
schema_version: norad.resource-benchmark.v1
cases:
  - name: step01_threads
    values: [1, 2, 4]
    repetitions: 3
    setup_argv: null
    producer_argv:
      - /absolute/path/to/step_01_star_align.sh
      - --threads
      - "{value}"
      - --output-dir
      - "{trial_dir}/output"
      # include every other required owner argument explicitly
    validator_argv:
      - /absolute/path/to/python
      - -X
      - pycache_prefix=/dev/null
      - -I
      - -m
      - norad
      - validate
      - star-alignment
      # include exact trial output and validation arguments explicitly
```

Review the expanded commands without writing, then execute on the intended
compute host:

```bash
./scripts/benchmark_stage_resources.py \
  --manifest /absolute/path/to/benchmark.yaml \
  --output /absolute/path/to/absent-benchmark-results

./scripts/benchmark_stage_resources.py \
  --manifest /absolute/path/to/benchmark.yaml \
  --output /absolute/path/to/absent-benchmark-results \
  --execute
```

Each trial records exact logs, producer wall time, child-process peak RSS, and
validator status. `summary.tsv` marks the smallest resource value within five
percent of the fastest successful median. Apply that result only to the tested
dataset scale, runtime, machine, memory, and storage system; preserve the raw
trial tree with the resulting request resource plan.

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

## Dependency maintenance

The [Quickstart setup](../../quickstart.md#1-clone-and-install-the-locked-python-workflow)
owns first installation, and its
[runtime section](../../quickstart.md#2-provide-the-scientific-runtime) owns
initial scientific dependency preparation. Restoration or version changes are
explicit operator actions and never occur from workflow, validation,
rendering, or generated scheduler code.

`pyproject.toml` owns direct Python dependencies and `uv.lock` owns the exact
graph. A stale lock is an error, not permission to relock. Guarded local R
checks for an already selected canonical library are:

```bash
RENV_LIBRARY=/absolute/path/to/canonical/renv-library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
RENV_LIBRARY=/absolute/path/to/canonical/renv-library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make local-real-r-test
```

They establish local configured-environment evidence only. Run
`BiocManager::valid(checkBuilt = FALSE)` separately from a guarded project R
session only when an explicitly approved dependency-maintenance review needs
current online freshness evidence. Never restore, snapshot, update, or relock
merely to turn a freshness result green.

## Manual job inspection

For a lifecycle-generated one-allocation job, use the exact job ID and log
directory printed at submission. Wait for both `%j` streams, but stop waiting
if accounting shows a terminal allocation:

```bash
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

Control-C stops `tail`; it does not cancel the job. Inspect final scheduler
state separately:

```bash
squeue -j "$job_id"
sacct -X -j "$job_id" \
  --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Owner-local stage scheduler entry points use their owner-documented stream
paths rather than the whole-run naming above. In every case, bind checkout,
command, inputs, job ID, accounting, streams, native outputs, validation
record, and evidence ceiling to the same attempt. Empty stderr, `COMPLETED
0:0`, or visible output alone is not validation.

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
