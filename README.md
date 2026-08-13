# NORAD: CSU HPC RNA-seq and RNA-editing workflow

NORAD runs a fixed, source-checkout-bound RNA-seq and paired-CMH candidate-
ranking pipeline. One public control path admits explicit reads, references,
partitions, analysis policy, and tool identities; schedules thirteen automatic
scientific owners through Snakemake's local executor; validates each owner;
and publishes an artifact index, run summary, and self-contained Jinja HTML
report.

The automatic profile stops after Step `09`. Step `09c` scientific review is a
separate human-authorized activity, so an automatic pipeline report correctly
records `evidence_incomplete`. NORAD reports **CMH-ranked candidates**, not
validated editing sites.

## Prerequisites

You need:

- Git, Python `3.11` or newer, and a separately installed `uv` executable;
- GNU Bash, STAR, samtools, Java, GATK, Picard, bcftools, RSeQC, and R;
- the guarded NORAD `renv` project and required Step `08` R namespaces; and
- paired FASTQ files plus a reference FASTA and GTF.

The exact accepted versions and probes are listed in
[`configs/local_pilot_runtime.example.tsv`](configs/local_pilot_runtime.example.tsv).
Setup does not install or repair scientific tools or R packages. This local
pilot uses one local Snakemake core and does not require SLURM.

## 1. Clone and install the locked workflow

```sh
git clone https://github.com/lab-cats/norad.git
cd norad
uv sync --locked --group workflow
```

This installs NORAD and pinned Snakemake `9.25.1` into `.venv`. It does not
install STAR, GATK, Picard, RSeQC, bcftools, R, or SLURM. Keep the checkout
clean: the readiness check binds its exact Git commit and rejects tracked or
untracked changes. Store runtime profiles, input declarations, reads,
references, workspaces, and results outside the checkout.

## 2. Prepare one explicit request

Copy the matched structural starters to an operator-managed directory:

```sh
NORAD_INPUT_DIR=/absolute/path/to/norad-inputs
mkdir -p "$NORAD_INPUT_DIR"
cp configs/local_pilot_request.example.yaml "$NORAD_INPUT_DIR/"
cp configs/local_pilot_samples.example.tsv "$NORAD_INPUT_DIR/"
cp configs/local_pilot_partitions.example.tsv "$NORAD_INPUT_DIR/"
cp configs/local_pilot_runtime.example.tsv \
  "$NORAD_INPUT_DIR/local_pilot_runtime.tsv"
```

Edit those copies before continuing:

- In `local_pilot_request.example.yaml`, replace the reference, cohort, and
  analysis IDs; FASTA/GTF paths; STAR-index parameters; and analysis policy.
- In `local_pilot_samples.example.tsv`, declare every paired FASTQ, condition,
  strandedness value, and replicate. The fixed profile requires at least two
  strata, each with exactly one declared control and one declared treatment.
- In `local_pilot_partitions.example.tsv`, choose selectors that exist in the
  declared reference.
- In `local_pilot_runtime.tsv`, replace every executable, Picard jar, Rscript,
  `renv` project, and R-namespace probe placeholder with the exact selected
  path. Module names alone are not executable identities.

Relative input paths are resolved from the request file's directory, not the
shell's working directory. The tracked starters contain no reads or reference
and are not a runnable dataset. See the
[`configs` catalog](configs/README.md) for their exact structural boundary.

Set these shell variables to the edited files and a workspace outside the
checkout. The workspace may already be a real writable directory or may not
exist yet.

```sh
NORAD_REQUEST_PATH=/absolute/path/to/norad-inputs/local_pilot_request.example.yaml
NORAD_RUNTIME_PROFILE_PATH=/absolute/path/to/norad-inputs/local_pilot_runtime.tsv
NORAD_WORKSPACE_PATH=/absolute/path/to/norad-workspace
```

## 3. Check readiness

Run the read-only doctor:

```sh
.venv/bin/python -I -m norad doctor local-pilot \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Continue only after it prints `READY: local-pilot prerequisites passed.` Exit
`1` prints actionable blockers; exit `2` means an input or path boundary is
malformed or unsafe. The doctor does not create the workspace, run the
workflow, load modules, or install or repair anything.

## 4. Review the no-write plan

`norad run` is a strict dry-run unless `--execute` is present:

```sh
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Review the printed deterministic run ID, run root, workflow attempt, owner-job
count, three reporting transactions, Snakemake command, and exact public owner
commands. The matched four-sample, one-partition starter shape expands to 34
owner jobs. A successful dry-run ends with `no workspace state was written`.

## 5. Execute the admitted plan

Run the same request with the explicit mutation flag:

```sh
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run \
  --request "$NORAD_REQUEST_PATH" \
  --workspace "$NORAD_WORKSPACE_PATH" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH" \
  --execute
```

NORAD creates the printed run root only after admission. Do not launch a second
initial run against an existing run root; inspect it and, when NORAD says it is
safe, resume it instead.

Step `00c` is the deliberate output exception to the run-root boundary: it
creates or reuses `<reference-fasta>.fai` and `<reference-stem>.dict` beside
the external FASTA declared by the request. Before execution, confirm that
reference location is the intended durable sidecar authority and is writable;
do not point the request at a read-only or foreign-managed reference copy.

## 6. Inspect state and outputs

Copy the exact `Run root:` printed by `run`:

```sh
NORAD_RUN_ROOT=/absolute/path/to/norad-workspace/runs/run-DIGEST
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad inspect \
  local-pilot-run \
  --run-root "$NORAD_RUN_ROOT"
```

Inspection derives state from NORAD's immutable records, hashes, semantic
receipts, and locks. It does not trust `.snakemake` metadata, timestamps, or
mere output presence. A successful full run prints
`State: local_pipeline_complete` and `Local pipeline complete: yes`.

For run ID `<run-id>`, the final reporting products are:

```text
<run-root>/products/artifact-summary/<run-id>/<run-id>.artifacts.tsv
<run-root>/products/artifact-summary/<run-id>/<run-id>.artifact_receipt.tsv
<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary.json
<run-root>/products/artifact-summary/<run-id>/<run-id>.run_summary_receipt.tsv
<run-root>/products/report/<run-id>/<run-id>.run_report.html
<run-root>/products/report/<run-id>/<run-id>.run_summary.tsv
<run-root>/products/report/<run-id>/<run-id>.report_outputs.tsv
```

Each workflow attempt also retains its terminal receipt beneath
`<run-root>/attempts/<workflow-attempt-id>/attempt-receipt.json`. Native owner
outputs and validation evidence remain under the same run root except for the
explicit Step `00c` FASTA sidecars described above; none becomes disposable
merely because reporting products exist.

## 7. Resume only an admitted boundary

If inspection prints `State: resume_available` and `Resume available: yes`,
plan the resume first:

```sh
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume \
  --run-root "$NORAD_RUN_ROOT" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH"
```

Review the reusable and pending jobs, then execute the same safe plan:

```sh
.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume \
  --run-root "$NORAD_RUN_ROOT" \
  --runtime-profile "$NORAD_RUNTIME_PROFILE_PATH" \
  --execute
```

Only a failed or interrupted boundary between owner tasks is automatically
resumable. If inspection reports `blocked`, preserve the run, receipts, locks,
logs, partials, and backups and follow
[`TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md). NORAD deliberately
provides no force, unlock, automatic cleanup, or retry of an owner that crossed
producer entry without verified completion.

## What has been proven

Campaign B's fresh-clone proof included locked `uv` setup, which the final test
rechecked offline, plus the public doctor, dry-run, real Snakemake scheduling,
lifecycle and reporting transactions, controlled failure, inspection,
byte-preserving resume, and final outputs. Its scientific owners were
deterministic **no-science test doubles**. That proves the local control plane
and recovery boundary; it does not prove STAR, GATK, Picard, RSeQC, bcftools,
R, SLURM, a production dataset, or CSU execution.

A real execution uses the scientific tools declared in your admitted runtime
profile, but its evidence must be reported separately. Scheduler success,
generated files, or an HTML report alone does not establish scientific review
or biological interpretation. `FWD_like` and `REV_like` are mechanical labels,
not biological strand claims, and `biological_interpretation_ready` remains
reserved.

## Repository map

| Path | Purpose |
| --- | --- |
| [`configs/`](configs/README.md) | Matched local-pilot starters and other explicit public inputs. |
| [`workflow/`](workflow/README.md) | Fixed Snakemake projection and local executor profile. |
| [`src/norad/`](src/norad/README.md) | Installed command, scientific owners, contracts, evidence, and reporting code. |
| [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md) | Cross-cutting operator and maintainer commands. |
| [`docs/operations/TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md) | Failure classification and evidence-preserving recovery routes. |
| [`docs/architecture/`](docs/architecture/README.md) | Implemented system, ownership, and dependency views. |
| [`tests/`](tests/README.md) | Local engineering and explicitly bounded runtime evidence. |
| [`data/`](data/README.md), [`refs/`](refs/README.md), [`results/`](results/README.md), [`logs/`](logs/README.md) | Operator-managed inputs, references, generated results, and logs. |

Current evidence and blockers are recorded in
[`HANDOFF.md`](docs/operations/HANDOFF.md). Exact owner behavior belongs to the
adjacent owner `README.md` and `CONTRACT.md`; the
[`runbook`](docs/operations/RUNBOOK.md) routes cross-cutting operations.

Do not commit FASTQ, BAM, CRAM, VCF, production result tables, runtime logs,
credentials, restored runtimes, or environment caches. Before deleting ignored
data, references, results, or logs, prove their owner, active consumers,
recovery state, and retention requirements.
