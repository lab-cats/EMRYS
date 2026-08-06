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
| Paired CMH ranking | [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md) |
| Scientific-review evidence | [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/assemble_scientific_review_evidence_package/README.md) |
| Runtime, reference, storage, and QC evidence | [`evidence`](../../src/norad/evidence/README.md) |
| Artifact schemas | [`artifact contracts`](../../src/norad/contracts/artifacts/README.md) |
| Artifact index, run summary, and reports | [`reporting`](../../src/norad/reporting/README.md) |
| Synthetic demonstration | [`demo`](../demo/README.md) |

Each owner README supplies supported help, dry-run, execute, scheduler, focused
test, diagnostics, and recovery routes when those surfaces exist. Its adjacent
`CONTRACT.md` owns exact inputs, outputs, checks, and evidence limits.

## Task status

Task cards are temporary specifications. Inspect the derived view:

```bash
./scripts/git_orchestration/task_status.py \
  --repo "$(git rev-parse --show-toplevel)"
```

Selection does not move or rewrite a card. Delete a card only when its work is
completed or retired. See the [workflow kernel](WORKFLOW.md) and
[task registry](../tasks/README.md).

## Local validation

Use focused tests during implementation:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
```

Run the complete local gate once against a final executable state:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks
```

Use serial or verbose diagnosis only when needed:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks VALIDATION_ARGS=--serial
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks VALIDATION_ARGS=--verbose
```

The coverage lane already runs the complete Python suite. A standalone
documentation package instead uses:

```bash
git diff --check
make -s documentation-check
git status --short
git diff --name-status
```

The documentation gate checks local document structure and mechanically
derived ownership. It deliberately does not validate links, anchors, diagrams'
inbound references, or relationships among cards.

## Explicit dependency setup

Restoration is an operator action and never occurs from compute, validation,
rendering, or scheduler code:

```bash
.venv/bin/python -m pip install -r requirements.txt
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
make quarto-restore
```

Guarded local R checks are:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

They opt into the repository library with `NORAD_USE_RENV=1`, disable automatic
snapshots and the `renv` sandbox, and establish local configured-environment
evidence only.

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
