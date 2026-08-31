# Runbook

This file contains genuinely cross-cutting EMRYS commands. Exact producer,
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
```

The login node is for Git, small transfers, editing, inspection, submission,
and small smoke checks. Never confirm or explicitly execute a directly placed
Run, STAR, BAM processing, mpileup, or R analysis there. The supported
scheduler path is whole-Run Slurm placement, which runs scientific work inside
one approved compute-node allocation and retains owner-specific temporary-space
policy inside the workflow.

## Owner command routes

| Area | Exact command owner |
| --- | --- |
| Sample admission | [`sample_manifest_admission`](../../src/emrys/ingestion/sample_manifest_admission/README.md) |
| Reference preparation and Steps `01`–`08` | [`stages`](../../src/emrys/stages/README.md) |
| Paired CMH ranking | [`rank_cohort_candidates_with_paired_CMH`](../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md) |
| Runtime, reference, storage, and QC evidence | [`evidence`](../../src/emrys/evidence/README.md); runtime `inspect runtime-availability`; storage `inspect storage-inventory` and `inspect storage-qualification`; reference `reconcile reference-provenance` |
| Artifact schemas | [`artifact contracts`](../../src/emrys/contracts/artifacts/README.md); installed route `python -I -m emrys validate artifact-contracts` |
| Artifact index, run summary, and reports | [`reporting`](../../src/emrys/reporting/README.md); the public independent route is `emrys report --run-root ...`, while low-level builders are private implementation and developer-fixture surfaces |

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
| Create a Project root around synthetic or real inputs | [Quickstart: initialize and ingest](../../quickstart.md#3-initialize-and-ingest-synthetic-or-real-inputs) |
| Discover and admit the active runtime | [Quickstart: runtime discovery](../../quickstart.md#4-discover-and-admit-the-runtime) and [`configs/README.md`](../../configs/README.md) |
| Qualify storage, diagnose Project readiness, or repair the managed runtime | [Quickstart: compatibility](../../quickstart.md#5-validate-data-compatibility-without-scientific-tools) and [Doctor](../../quickstart.md#6-diagnose-readiness-and-optionally-repair-the-managed-runtime) |
| Review and execute the fixed workflow | [Quickstart: plan and execution](../../quickstart.md#7-review-and-confirm-one-immutable-plan) |
| Inspect run state or plan a supported resume | Commands below and the [local-pilot owner](../../src/emrys/orchestration/local_pilot/README.md) |
| Diagnose blocked, partial, locked, or uncertain state | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |

`emrys run` and `emrys resume` are the whole-Run execution surface. With no
`--execution-profile`, they execute directly with the built-in conservative
resources. An explicit profile can place the same one-host workflow inside one
Slurm allocation; it is not a distributed executor:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys run \
  --project /absolute/path/to/project.yaml \
  --analysis ANALYSIS_NAME \
  --execution-profile /absolute/path/to/emrys.execution.yaml
```

The public model is `Project -> named Analysis -> immutable Run -> Results`.
Project validation, runtime discovery, and Doctor validate all named Analyses;
Doctor and `run` select exactly one readiness/execution context. `--analysis`
may be omitted only when the Project defines one Analysis. Its human name
selects the Analysis but does not enter the content-derived Analysis revision
or Run identity. Resume starts from an
existing Run root, so it reuses the selected Analysis recorded by that Run and
does not accept a new Analysis choice.

On a terminal, direct placement prints one frozen Run plan and asks whether to
execute it. Slurm placement instead prints its placement summary and asks
whether to submit that frozen submission plan once; the Run plan is constructed
inside the allocation. Refusal, EOF, or interruption writes and submits
nothing. Use `--execute` only for deliberate noninteractive automation.
Accepted Slurm submission prints exact `JOB_ID`, `OUT`, and `ERR` values. Setup
creates `runs/`, `logs/`, and `runtime/` beneath the `project.yaml` parent;
scheduler and application logs use its `logs/` tree. Run, resume, and Doctor
derive the admitted `runtime/runtime.tsv` from that Project. Only the advanced
`inspect storage-qualification --workspace PROJECT_ROOT ...` retains the
explicit two-phase Slurm/site probe; run and Doctor derive the target. Direct
placement instead consumes Doctor's Project-owned single-host receipt.

`emrys doctor --project /absolute/path/to/project.yaml` is the top-level
readiness route. Diagnosis is side-effect-free; `--log-level verbose` and
`--log-level debug` reveal progressively more retained operational evidence. A
missing direct-storage admission or incomplete EMRYS-managed runtime can be
previewed with `--repair`. Terminal confirmation or explicit noninteractive
`--repair --execute` publishes only the Project-owned direct receipt and, when
needed, delegates locked installation to `uv`, Pixi, and `renv` within the
active checkout-owned `.venv` and Project-owned `runtime/managed`. One
maintenance log spans mutation and requalification. Repair preserves a ready
site/user runtime profile, declared inputs, and workflow outputs. Managed
runtime repair currently targets Linux x86-64; use `runtime discover` for an
institution-provided environment.
Reporting runs automatically after scientific work and remains a separate,
receipt-last transaction rather than a scientific stage. The scientific
Attempt ends before reporting begins. `--no-report` disables only downstream
reporting and leaves the scientific Attempt unchanged. `emrys report` can
regenerate or reuse reporting independently from a completed scientific Run.

Owner-local scheduler entry points are retired. Standalone owner commands
remain expert direct routes and never create or adopt an orchestrated Run;
supported scheduled scientific execution uses grouped whole-Run Slurm
placement.

### Recurring inspection and resume

Inspect state from EMRYS's admitted records rather than `.snakemake` metadata:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys inspect \
  run \
  --run-root /absolute/project/runs/run-DIGEST
```

Inspection is read-only. Rehashing bound evidence can be expensive, so run it
at meaningful boundaries rather than in a tight polling loop.
The normal view uses the primary Run ID and scientific outcome. Add
`--detail verbose` for admitted Analysis, Execution Plan, and Attempt identity
plus effective execution facts; use `--detail debug` only when exact authority
paths/digests, verified output bindings, receipt evidence, or task commands are
needed. Historical Runs are labeled rather than assigned successor identities.

Resume is supported only when inspection reports incomplete scientific Results,
a failed or interrupted Attempt, and `Recovery available: yes`:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys resume \
  --run-root /absolute/project/runs/run-DIGEST
```

Without an explicit execution profile, resume reuses the predecessor's
symbolic computational resources and places the new Attempt directly. Select
an explicit profile to request Slurm placement. Resource CLI overrides have
highest precedence. Direct placement displays reusable and pending work, then
asks once before execution. Slurm placement confirms the submission first;
reusable and pending work is displayed later inside the allocation.
`--execute` skips only the applicable prompt for automation. A scope that
crossed producer entry without verified completion remains blocked rather than
being retried or cleaned. A complete run refuses resume, and the public
lifecycle exposes no force, unlock, metadata-cleanup, or raw-engine bypass.

Generate reports independently only for a completed scientific Run. The first
command is read-only; add `--execute` after reviewing its plan:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys report \
  --run-root /absolute/project/runs/run-DIGEST
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys report \
  --run-root /absolute/project/runs/run-DIGEST \
  --execute
```

Validated complete reports are reused. Partial, corrupt, orphaned, mismatched,
or concurrent reporting state fails closed and is preserved; the public route
does not overwrite, adopt, delete, or repair it. Reporting failure does not
rewrite a successful scientific Attempt receipt or make Results incomplete.

## Resource benchmarking

[`scripts/benchmark_stage_resources.py`](../../scripts/benchmark_stage_resources.py)
is an opt-in harness for comparing resource values on representative data. It
does not invent stage commands or discover inputs. Provide a closed manifest
containing exact setup, producer, and public validator argv arrays; use only
the placeholders `{value}` and `{trial_dir}` where the candidate value and
create-absent trial directory belong:

```yaml
schema_version: emrys.resource-benchmark.v1
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
      - emrys
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
trial tree with the resulting execution-profile resource plan.

## Task selection

The [findings matrix](../tasks/backlog_matrix.md) is the only durable backlog.
Select one accepted item or state one explicitly bounded objective, obtain the
required authority, and follow the [workflow kernel](WORKFLOW.md). The
[task-planning guide](../tasks/README.md) explains the matrix, temporary
architecture campaign, and terminal disposition rules.

## Local validation

Use focused tests during implementation:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
```

The static preflight includes a fast, read-only check of the current Python
source-import graph. Run it directly while changing owner boundaries:

```bash
.venv/bin/python tests/tools/source_dependencies.py --repo "$PWD"
```

This check covers statically declared Python imports, recognized literal
standard-library dynamic import forms, the exact current CLI composition
roster, and exact transitional edges. It does not perform general
dynamic-import data-flow inference or establish runtime/control invocation,
shell or R relationships, artifact/evidence flow, scheduler behavior, or
scientific correctness.

For package metadata, wheel isolation, installed commands, and resources:

```bash
uv lock --check
uv sync --locked --check
.venv/bin/python -m pytest -q tests/test_package_distribution.py
```

For direct shell-owner behavior without replaying Python validator suites:

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
Jinja HTML reporting while excluding the isolated-wheel suite. The wheel lane
owns installed-package integrity. The shell lane owns direct shell-owner
behavior. Python coverage owns whole-Run submission and transport contracts,
and selected real-synthetic lanes supply hosted scheduler evidence. Guarded real R remains
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
ownership, retired-document guards, and standalone Mermaid source shape. It
does not validate general Markdown links, anchors, or diagrams' inbound
references.

These checks establish local structural/test evidence only. Guarded R adds
real local runtime evidence for its named fixtures. Neither result establishes
CSU scheduler execution, production artifacts, scientific review, validated
editing sites, or biological interpretation. Use focused checks per approved
slice and run the assembled gate once after the final executable state is
settled; rerun it only for a concrete failure-driven reason.

### GitHub Actions Phase 1 CI

The tracked [Phase 1 workflow](../../.github/workflows/ci.yml) runs its ordinary
lanes for pull requests targeting `master`, pushes to `master`, and merge-queue
candidates. Its long lanes run separately: the complete Python 3.11 suite and
the 130-pair real synthetic E2E run nightly. The 100,000-pair profile is a
weekly or explicitly selected scale gate, not a per-change architecture gate.
Manual dispatch selects the maintained long lanes and rejects an empty
selection. The workflow token has read-only repository access and every
external action is pinned to an immutable commit. Superseded ordinary runs for
the same ref are cancelled; scheduled and manually selected long runs have
unique, non-cancelling groups.

Python 3.14 is the primary development and pull-request runtime. Every pull
request runs the complete behavioral inventory under branch coverage as four
duration-balanced shards. Each shard collects the whole inventory, records its
exact selection, uses xdist work stealing within the runner, and streams the
50 slowest timings. The merge check rejects missing, duplicate, stale, or
inconsistently planned receipts before combining coverage and applying the
reviewed baseline.

Python 3.11 remains supported. Pull requests run a bounded 3.11 compilation,
wheel, installed CLI, and manifest smoke. Nightly runs and manual dispatches
that select `python311` additionally run the complete behavioral inventory as
four receipt-verified 3.11 shards; they do not duplicate the Python 3.14
coverage measurement.

The assembled local `make -s all-checks` authority remains unchanged in
meaning. CI executes its non-overlapping owners as independent checks so a
slow R restore or shell lane cannot serialize the Python suite:

- `Static, lint, docs, and wheel` runs the serial preflight and installed-wheel
  owner.
- `Python 3.14 complete suite and coverage policy` aggregates the four
  complete-suite coverage shards and the isolated subprocess probes.
- `Shell owner contracts` runs direct shell owners; Python and selected real-synthetic lanes cover whole-Run submission and parity.
- `Guarded R fixtures` restores the exact R 4.6.1 environment and runs the
  guarded R owner.
- `Managed golden path (Python 3.14)` creates a separate ordinary clone, lets
  Doctor provision the locked Project runtime, and runs the real `smoke-v1`
  Project through complete direct Results and automatic reports. Focused
  lifecycle tests retain the injected failure/resume proof.
- `Workflow lint` verifies the tracked Actions workflows with a
  checksum-verified `actionlint` binary. Its external ShellCheck and Pyflakes
  integrations remain disabled because Phase 1 does not establish either as a
  new repository policy.

The scheduled real synthetic lane restores the checked-in Linux lock for STAR,
Samtools, GATK, BCFtools, Picard, and RSeQC, restores the exact R and Python
authorities separately, and configures one disposable real Slurm node on the
GitHub-hosted runner. It executes the public workflow through Slurm
execution-profile placement and retains runtime, scheduler, transcript,
partial-state, and result evidence even when a selected profile fails. Its
scientific oracle separately requires all 35 owner jobs, Step 10, and the
three-row/one-significant-row Step 09 result; its reporting oracle then requires
all three downstream transactions and both HTML reports.

The workflow bootstrap may download explicitly selected dependencies, but the
ordinary validation commands themselves remain non-restoring. A green ordinary
Phase 1 run establishes clean GitHub-hosted Ubuntu engineering evidence,
guarded fixture R evidence in its dedicated lane, and a fresh-clone,
Doctor-managed, real-tool direct synthetic result. A green selected synthetic
lane additionally establishes the named locked real-tool, single-node Slurm
synthetic workflow result on that hosted runner. Neither establishes CSU or
distributed-filesystem behavior, production-data execution, scientific review,
biological validation, or biological interpretation.

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

### Live whole-run dashboard

For a lifecycle-generated one-allocation job, the CSU preview dashboard can
show bounded live scheduler, stage, sample, and resource-plan observations:

```bash
# Discover the newest admissible current-user EMRYS wrapper job.
make dashboard

# Select one job explicitly; optionally bind its exact log directory too.
make dashboard JOB_ID=replace-with-printed-job-id
make dashboard \
  JOB_ID=replace-with-printed-job-id \
  LOG_DIR=/absolute/path/to/emrys-slurm-logs

# The default is 30 seconds; values below five seconds are rejected.
make dashboard DASHBOARD_REFRESH=15
```

Automatic selection queries only the current user's live jobs and the most
recent seven days of Slurm accounting, considers at most 50 root allocation
IDs, and admits the first candidate whose scheduler metadata and exact
`emrys-local-pilot-<job-id>.out/.err` pair can be proved. It does not walk or
glob shared storage. `LOG_DIR` without `JOB_ID` is ambiguous and rejected; when
Slurm declares the stream paths, an explicit `LOG_DIR` must agree with them.
The selected directory and streams must be current-user-owned, readable, real
directory or regular-file entries with no symlinked path.

Press `1` or `o` for the overview, `2` or `d` for details, or `Tab` to switch
views. Press `r` to refresh immediately and `q` to quit; quitting the dashboard
does not cancel the allocation. The details view also accepts arrow or `j`/`k`
scrolling and Page Up/Page Down.

The dashboard reads scheduler metadata and only newly appended stream bytes.
It never changes the workflow, run root, logs, scheduler job, or reports, and
it does not derive or display result locations. Its status, inferred progress,
and timing are not completion or evidence authority. After the allocation
reaches a terminal state, inspect accounting and run the final EMRYS inspection
using the exact run root printed by the control stream:

```bash
.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys inspect \
  run \
  --run-root /absolute/project/runs/run-DIGEST
```

A successful run or resume, and a completed inspection, supply verified result
locations. If no `Results:` block is printed, do not construct or search for
report paths. Admitted owner records establish scientific Results; separately
validated reporting ledgers establish report completion. Use the manual stream
procedure below when dashboard discovery is unavailable or when exact raw
scheduler streams are required.

### Manual stream and accounting fallback

For a whole-Run Slurm placement, use the exact job ID and log directory printed
at submission. The default directory is `<project-root>/logs`. Wait for both `%j`
streams, but stop waiting if accounting shows a terminal allocation:

```bash
job_id=replace-with-printed-job-id
EMRYS_LOG_DIR=/absolute/path/to/emrys-slurm-logs
stdout="$EMRYS_LOG_DIR/emrys-local-pilot-$job_id.out"
stderr="$EMRYS_LOG_DIR/emrys-local-pilot-$job_id.err"

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

For every whole-Run job, bind checkout, command, inputs, job ID, accounting,
streams, native outputs, validation record, and evidence ceiling to the same
attempt. Empty stderr, `COMPLETED 0:0`, or visible output alone is not
validation.

## Cluster execution and promotion

Operate only from an explicitly approved clean commit and input set:

```bash
cd <approved-checkout>
git branch --show-current
git rev-parse HEAD
test -z "$(git status --porcelain=v1)"
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
