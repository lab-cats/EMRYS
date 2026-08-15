# NORAD: CSU HPC RNA-seq and RNA-editing workflow

NORAD takes explicitly declared paired RNA-seq reads, a reference, cohort
pairing, analysis policy, and scientific-tool identities through a fixed
pipeline and produces validated owner outputs, a deterministic artifact index,
a run summary, QC views, and a self-contained HTML report.

The public `norad run` command currently uses Snakemake's **single-host local
executor with one core**. It does not submit SLURM jobs or distribute owners
across compute nodes. You may launch that local process on an appropriately
provisioned host or inside one allocation, but that does not turn it into
public SLURM orchestration.

The automatic profile ends after Step `09`. Step `09c` is separate,
human-authorized scientific review, so an otherwise successful automatic run
correctly reports `evidence_incomplete`. NORAD reports **CMH-ranked
candidates**, not validated RNA-editing sites or biological conclusions.

## Choose a starting point

- **Run the complete pipeline on your data:** follow the quickstart below. It
  covers intake, all automatic scientific owners, validation, artifact
  indexing, summary generation, and the HTML report.
- **Preview only the report:** after the locked install, run `make demo-report`
  and follow [`docs/demo/README.md`](docs/demo/README.md). It uses bundled
  reporting fixtures and does not run ingestion, STAR, GATK, Picard, RSeQC,
  bcftools, R analysis, or the full pipeline.

Release validation may use a separately generated real-tool synthetic dataset
outside the repository. It is not a hidden public mode or a checked-in
production dataset. The exact evidence completed at the current commit is
recorded in [`HANDOFF.md`](docs/operations/HANDOFF.md); do not infer a full
scientific-tool run from this quickstart alone.

## Quickstart

### 1. Install the locked Python workflow

Prerequisites are Git, GNU Make, Python `3.11` or newer, and a separately
installed `uv` executable:

```sh
git clone https://github.com/lab-cats/norad.git
cd norad
uv sync --locked --group workflow
```

This installs NORAD and the locked Snakemake `9.25.1` into `.venv`. It does
not install, download, repair, or load the scientific tools or R packages.

Define one controlled command for the current shell. Recreate it in each new
terminal:

```sh
NORAD_PY="$(pwd -P)/.venv/bin/python"
norad() {
  "$NORAD_PY" -X pycache_prefix=/dev/null -I -m norad "$@"
}
norad --help
```

The function keeps Python caches out of the checkout and uses isolated module
resolution. Keep local-pilot inputs, workspaces, scientific results, control
logs, and unmanaged runtimes outside the repository: the doctor binds the
exact Git commit and requires a clean checkout. The locked `.venv`, the
ignored `renv/library`, and the ignored `results/demo-report-jinja` preview are
the maintained setup/demo exceptions.

### 2. Provide the scientific runtime

Install or select these before continuing:

- GNU Bash, gunzip, STAR, samtools, Java, GATK, Picard, bcftools, RSeQC, and R;
- this exact source checkout as the guarded NORAD `renv` project, plus an
  existing canonical `renv` library; and
- the fixed Step `08` R namespaces at their lock-selected versions.

The authoritative accepted versions, probes, and R namespace versions are in
[`configs/local_pilot_runtime.example.tsv`](configs/local_pilot_runtime.example.tsv).
Notable fixed identities include STAR `2.7.11b`, samtools `1.19.2`, GATK
`4.6.1.0`, Picard `3.1.1`, bcftools `1.21`, R `4.6.1`, and the locked
Snakemake version above. The Java launcher must be canonical
`<JAVA_HOME>/bin/java` and Java `17` or newer. A module name is not sufficient:
the runtime profile admits canonical executable or jar paths, versions, and
SHA-256 identities. R namespaces are also bound to deterministic installed-
package tree hashes.

NORAD never installs a missing tool or restores `renv` during doctor or
execution. On a module-based system, select the modules first and put the
resulting absolute executable and jar targets in the runtime profile.

For a fresh checkout, explicitly restore and check its lock-selected R library
with the canonical Rscript you intend to admit:

```sh
RSCRIPT_BIN=/absolute/path/to/Rscript make r-restore
RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

Restoration is an operator-authorized network/package mutation; it is never
performed by doctor or execution. If a canonical library was provisioned
separately, skip restoration and select it explicitly when checking:

```sh
RENV_PATHS_LIBRARY=/absolute/path/to/canonical/library \
  RSCRIPT_BIN=/absolute/path/to/Rscript make r-check
```

In `local_pilot_runtime.tsv`, `renv_project` must resolve to this exact clean
checkout and `renv_library` to the exact library path that passed `r-check`.

### 3. Create an external, create-absent input set

Choose an existing writable operator directory outside the checkout. The input
directory and workspace below must not already exist:

```sh
NORAD_OPERATOR_ROOT=/absolute/path/to/operator-managed-storage
NORAD_INPUT_DIR="$NORAD_OPERATOR_ROOT/norad-inputs"
NORAD_WORKSPACE_PATH="$NORAD_OPERATOR_ROOT/norad-workspace"

test -d "$NORAD_OPERATOR_ROOT" &&
test -w "$NORAD_OPERATOR_ROOT" &&
test ! -e "$NORAD_INPUT_DIR" &&
test ! -e "$NORAD_WORKSPACE_PATH" &&
mkdir -m 700 "$NORAD_INPUT_DIR" &&
cp configs/local_pilot_request.example.yaml "$NORAD_INPUT_DIR/" &&
cp configs/local_pilot_samples.example.tsv "$NORAD_INPUT_DIR/" &&
cp configs/local_pilot_partitions.example.tsv "$NORAD_INPUT_DIR/" &&
cp configs/local_pilot_runtime.example.tsv \
  "$NORAD_INPUT_DIR/local_pilot_runtime.tsv"
```

If any command fails, stop and choose a new absent target; do not overwrite a
previously prepared request or workspace.

Edit the copied files:

- `local_pilot_request.example.yaml`: replace the reference, cohort, and
  analysis IDs; FASTA/GTF paths; STAR-index parameters; and analysis policy.
- `local_pilot_samples.example.tsv`: declare every paired FASTQ, condition,
  replicate, and strandedness value. The fixed profile requires at least two
  strata, each with exactly one sample matching the request's
  `analysis.control_condition` and one matching its
  `analysis.treatment_condition`, sharing a replicate value.
- `local_pilot_partitions.example.tsv`: select reference contigs that exist in
  the declared FASTA.
- `local_pilot_runtime.tsv`: replace only path placeholders and their coupled
  path arguments. Do not change the roster, check types, required flags,
  version expressions, ordinary probes, descriptions, or R package names.

Relative paths in the request resolve from the request file's directory, not
from the terminal's current directory. The tracked starters contain no reads
or reference and are not runnable data.

Set the durable paths once:

```sh
NORAD_REQUEST_PATH="$NORAD_INPUT_DIR/local_pilot_request.example.yaml"
NORAD_RUNTIME_PROFILE_PATH="$NORAD_INPUT_DIR/local_pilot_runtime.tsv"
```

Leave `NORAD_WORKSPACE_PATH` absent. Its immediate parent must remain a
canonical, writable real directory; NORAD does not recursively create a
missing parent.

### 4. Require a ready result

The doctor is read-only:

```sh
norad doctor local-pilot \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Continue only after it prints:

```text
READY: local-pilot prerequisites passed.
```

Exit `1` prints actionable blockers and remediation; exit `2` means an input
or path boundary is malformed or unsafe. Doctor does not create the workspace,
run the workflow, load modules, or install or repair anything.

`READY` is not a disk, memory, wall-time, or throughput estimate. Before
execution, capacity-plan for the declared libraries and verify free storage
and memory on the execution host. NORAD deliberately retains multiple BAM
generations, scientific intermediates, immutable logs, and recovery evidence.

### 5. Review the no-write plan

`norad run` is a strict dry-run unless `--execute` is present:

```sh
norad run \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Review the deterministic run ID and run root, workflow-attempt identity,
owner-job count, three reporting transactions, Snakemake command, and every
public owner command. A four-sample, two-stratum, one-partition request expands
to 34 owner jobs. A successful plan ends with `no workspace state was written`.

Copy the exact printed run root now; it is also the path used for monitoring:

```sh
NORAD_RUN_ROOT=/absolute/path/to/norad-workspace/runs/run-DIGEST
```

### 6. Execute once and retain the control stream

Step `00c` creates or reuses `<reference-fasta>.fai` and
`<reference-stem>.dict` beside the declared external FASTA. Confirm that this
reference directory is the intended durable sidecar authority and is writable.
A partial sidecar pair is rejected. Retained adjacent locks or staging paths
are recovery evidence; do not remove them to make a run proceed.

Write the live control stream inside a newly create-exclusive private
directory and preserve the pipeline exit through the pipe:

```sh
(
  set -o pipefail
  NORAD_CONTROL_DIR="$(mktemp -d "$NORAD_OPERATOR_ROOT/.norad-control.XXXXXX")" || exit 1
  NORAD_CONTROL_LOG="$NORAD_CONTROL_DIR/norad-run-control.log"
  printf 'Control log: %s\n' "$NORAD_CONTROL_LOG"
  norad run \
    --request "$NORAD_REQUEST_PATH" \
    --workspace "$NORAD_WORKSPACE_PATH" \
    --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH" \
    --execute 2>&1 | tee "$NORAD_CONTROL_LOG"
)
```

Do not submit a second initial run against the same run root, even if the
terminal disconnects or this command fails. Inspect the existing run first.

### 7. Monitor from another terminal

In a second terminal, follow the live top-level control stream:

```sh
tail -F /exact/control/log/path/printed/by/step-6
```

Inspection is read-only but intentionally re-admits completed task records and
hashes their bound inputs and outputs. Run it occasionally—at a stage boundary,
after a long quiet interval, or once the control command ends—not every few
seconds:

```sh
NORAD_RUN_ROOT=/absolute/path/to/norad-workspace/runs/run-DIGEST
norad inspect local-pilot-run --run-root "$NORAD_RUN_ROOT"
```

Owner task stdout and stderr are retained at
`<run-root>/attempts/<workflow-attempt-id>/tasks/<machine-key>/<scope-id>/`.
Those immutable task logs are published when that task reaches its terminal
attempt boundary; they are not reliable live files to tail while that owner is
still running. The retained `tee` stream is the continuous observation surface;
occasional `norad inspect` is the authoritative state check.

### 8. Confirm completion and open the report

Run one final inspection:

```sh
norad inspect local-pilot-run --run-root "$NORAD_RUN_ROOT"
```

A successful automatic run prints `State: local_pipeline_complete` and
`Local pipeline complete: yes`. Locate its self-contained report without
searching the tree:

```sh
NORAD_RUN_ID="${NORAD_RUN_ROOT##*/}"
NORAD_REPORT_PATH="$NORAD_RUN_ROOT/products/report/$NORAD_RUN_ID/$NORAD_RUN_ID.run_report.html"
test -f "$NORAD_REPORT_PATH" && printf '%s\n' "$NORAD_REPORT_PATH"
```

Without separately supplied and approved Step `09c` review evidence, expect
the report banner and run summary to say `evidence_incomplete`. That is the
correct scientific state, not a pipeline-execution failure.

## Output inventory

Keep the entire run root. Output presence alone is not completion; NORAD
inspection re-admits immutable records, hashes, semantic receipts, and locks.

| Location | Durable contents |
| --- | --- |
| `<run-root>/contract/` | Canonical normalized request, fixed profile, admitted runtime-profile snapshot, reporting contracts/policy/inventory, attempt workflow configs, and per-task dispatch records. |
| `<run-root>/attempts/<workflow-attempt-id>/` | Request and attempt records, per-owner task-attempt records plus terminal stdout/stderr logs, and `attempt-receipt.json` published last for the attempt. |
| `<run-root>/state/task-starts/` | Immutable producer-entry records. |
| `<run-root>/state/verified/` | Hash-bound successful owner-task records; a four-sample starter shape has 34 when complete. |
| `<run-root>/state/reporting/` | Start and verified records for artifact-index, run-summary, and HTML-report transactions. |
| `<run-root>/results/` | Native scientific outputs, validation reports, QC evidence, alignment/variant intermediates, and ranked-candidate products owned by Steps `00a`–`09`. |
| `<run-root>/products/artifact-summary/<run-id>/records/` | One canonical JSON artifact record per inventory entry, including explicit unavailable or incomplete states. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.artifacts.tsv` | Deterministic artifact index. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.artifact_receipt.tsv` | Artifact-index receipt, published last for that transaction. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Canonical machine-readable run summary. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | Tabular run-status summary. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC view. |
| `<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary_receipt.tsv` | Run-summary receipt, published last for that transaction. |
| `<run-root>/products/report/<run-id>/<run-id>.run_report.html` | Self-contained Jinja HTML report. |
| `<run-root>/products/report/<run-id>/<run-id>.run_summary.tsv` | Report-renderer summary table. |
| `<run-root>/products/report/<run-id>/<run-id>.report_outputs.tsv` | HTML-report output receipt, published last for that transaction. |
| Beside the declared FASTA | The explicit Step `00c` `.fai` and `.dict` sidecars; these are the only owner outputs outside the run root. |

Locks, released-lock evidence, partials, backups, task logs, and failed attempt
records are not disposable merely because later outputs or a report exist.

## Resume safely

Resume only when inspection prints both `State: resume_available` and
`Resume available: yes`. First review the no-write resume plan:

```sh
norad resume \
  --run-root "$NORAD_RUN_ROOT" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Then execute the exact admitted plan:

```sh
norad resume \
  --run-root "$NORAD_RUN_ROOT" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH" \
  --execute
```

Only a verified failed or interrupted boundary between owner tasks is
automatically resumable. A completed run refuses resume. If inspection says
`blocked`, preserve the run root, receipts, locks, logs, partials, sidecars,
and backups, then follow
[`TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md). NORAD intentionally
provides no force, unlock, metadata cleanup, or automatic retry after an owner
crossed producer entry without verified completion.

## Evidence and operating limits

- The public executor is source-checkout-bound, single-host, one-core, and
  local. It is not a public SLURM scheduler, multi-node workflow, or validated
  NFS/distributed-filesystem locking implementation.
- The workspace assumes one cooperative user on a POSIX local filesystem with
  working advisory `flock` and same-filesystem hard links.
- `READY` proves the declared local prerequisites passed their bounded probes;
  it does not prove a workflow or scientific result.
- A completed run establishes the exact admitted tools and artifacts for that
  run. Scheduler success, output presence, schema validity, or an HTML report
  alone does not establish scientific review or biological interpretation.
- `FWD_like` and `REV_like` are mechanical labels, not biological strand
  claims. `biological_interpretation_ready` remains reserved for a separately
  approved scientific policy and evidence package.

## Further guidance

| Need | Canonical guide |
| --- | --- |
| Input and runtime-profile details | [`configs/README.md`](configs/README.md) |
| Public local-pilot boundary | [`src/norad/orchestration/local_pilot/README.md`](src/norad/orchestration/local_pilot/README.md) |
| Cross-cutting operator commands | [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md) |
| Evidence-preserving diagnosis and recovery | [`docs/operations/TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md) |
| Reporting transactions and direct report commands | [`src/norad/reporting/README.md`](src/norad/reporting/README.md) |
| Architecture and owner map | [`docs/architecture/README.md`](docs/architecture/README.md) |
| Validation evidence and remaining gaps | [`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md) |
| Local test routes | [`tests/README.md`](tests/README.md) |

Do not commit FASTQ, BAM, CRAM, VCF, production result tables, runtime logs,
credentials, restored runtimes, or environment caches. Before deleting ignored
inputs, references, results, or logs, prove their owner, active consumers,
recovery state, and retention requirements.
