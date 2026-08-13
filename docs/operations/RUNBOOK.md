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

Known CSU checkout locations are `~/norad` and
`/mnt/stor-pool-01/users/2609214/norad`. Verify site paths in the intended login
or batch context; never treat a remembered path as current evidence.

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
and small smoke checks. Heavy work belongs in owner-local `.slurm` entry points.
Ordinary wrappers use `TMPDIR=/tmp`; the Step `05` owner requires its documented
project-storage temporary directory.

## Owner command routes

| Area | Exact command owner |
| --- | --- |
| Sample admission | [`sample_manifest_admission`](../../src/norad/ingestion/sample_manifest_admission/README.md) |
| Reference preparation and Steps `01`–`08` | [`stages`](../../src/norad/stages/README.md) |
| Paired CMH ranking | [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/paired_cmh_candidate_ranking/README.md) |
| Scientific-review package assembly | [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/scientific_review_package/README.md); installed route `python -I -m norad assemble scientific-review-package` |
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

Copy [`configs/local_pilot_runtime.example.tsv`](../../configs/local_pilot_runtime.example.tsv)
outside the checkout or to an explicitly managed local path, then replace every
placeholder with the exact controlled Python/Snakemake and SHA-256 launcher,
Bash, gunzip, scientific executable or jar, Rscript, canonical checkout/renv
project, existing renv library, and R-namespace selection. File-backed runtime
identities are bound by authored path, canonical target, version, and SHA-256;
do not fabricate a missing renv library.
After `uv sync --locked --group workflow` and the separately authorized science
tool/R setup, inspect one request and workspace plan:

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
unsafe. This does not establish real-tool, scheduler, cluster, scientific-
review, or biological evidence.

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
exercised this sequence through real Snakemake, lifecycle, and reporting with
deterministic no-science owner doubles. It did not run the real scientific
tools or establish local real-tool or cluster evidence.

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
