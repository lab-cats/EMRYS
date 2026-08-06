# Runbook

Supported cross-cutting commands for operating and validating NORAD. Run commands
from the repository root unless a section says otherwise. Functional behavior,
stage-local invocations, and known defects belong to the adjacent owner
[`README.md`](../../src/norad/stages/README.md) and `CONTRACT.md`; current runtime
and evidence state belongs to [`HANDOFF.md`](HANDOFF.md#evidence-boundary).

Dry runs, help text, mocks, fixtures, availability probes, and synthetic reports
are not production, cluster, scientific-review, or biological evidence. Add an
execute flag, submit a job, replace an output, install a dependency, or publish a
Git ref only when that exact action is authorized. Preserve ambiguous locks,
partials, backups, logs, and recovery markers until ownership and state are known.

## Command index

- Start: [project locations](#project-locations),
  [demo and inspection](#demo--inspection-checklist),
  [cluster tools](#confirmed-cluster-tools--modules), and
  [cluster facts](#cluster-facts-and-quirks).
- Operate: [runtime and evidence helpers](#artifact-and-future-operational-helpers),
  [job inspection](#manual-job-checking), and
  [cluster execution](#cluster-execution-pattern).
- Develop: [concurrent work](#concurrent-worktrees-and-serialized-integration),
  [fragment exchange](#manual-integration-fragment-exchange), and
  [local validation](#local-validation-gate).
- Workflow: [task lifecycle](#inspect-or-change-task-lifecycle),
  [owner routing](#workflow-contract-and-validation-convention),
  [reference preparation](#reference-prep), [Steps `01`-`09`](#step-01-star-alignment),
  and [scientific review](#post-step-09-scientific-validation-gate).

## Project Locations

Resolve the active checkout rather than assuming a caller-specific local path:

```bash
git rev-parse --show-toplevel
pwd -P
git branch --show-current
git rev-parse HEAD
git status --short
```

Known CSU checkout locations are `~/norad` and
`/mnt/stor-pool-01/users/2609214/norad`. The known raw-data link is
`data/raw/novogene_remora` ->
`/mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data`, with FASTQs beneath
`01.RawData/`. Verify these site paths in the intended login, batch, or compute
context before relying on them.

Repository-relative operator roots are described by the local indexes:
[`configs/`](../../configs/README.md), [`data/`](../../data/README.md),
[`refs/`](../../refs/README.md), [`logs/`](../../logs/README.md), and
[`results/`](../../results/README.md).

## Demo / Inspection Checklist

This read-only checklist orients a configured user without claiming that an
output exists:

```bash
git status --short
sed -n '1,140p' README.md
sed -n '1,180p' src/norad/contracts/STAGE_MAP.md
sed -n '1,20p' configs/samples.example.tsv

for path in refs results logs; do
  if [ -e "$path" ]; then
    ls -ld "$path"
  else
    printf 'unavailable here: %s\n' "$path"
  fi
done
```

Use [`HANDOFF.md`](HANDOFF.md#evidence-boundary) before narrating current
evidence. For a populated synthetic report, use the
[demo-report procedure](#generate-the-populated-synthetic-demo-report); its
provisional banner and evidence ceiling are part of the demonstration.

## Confirmed Cluster Tools / Modules

These are site bindings used by current wrappers, not portable environment
guarantees. Probe them in the exact execution context. The structured
[runtime preflight](#run-the-explicit-runtime-preflight) records explicit
expectations; the manual smoke job only logs availability.

### STAR

```bash
module load star/2.7.11b
STAR --version
```

### samtools

```bash
module load samtools/1.19.2
samtools --version
```

### bedtools

```bash
module load bedtools/2.31.1
bedtools --version
```

### Picard And Java

```bash
module load picard/3.1.1
printf 'PICARD=%s\nJAVA_HOME=%s\n' "${PICARD:-}" "${JAVA_HOME:-}"
java -version
```

Do not infer Java from a module name or `JAVA_HOME`. Step `04` resolves
`JAVA_BIN_OVERRIDE`, then an executable `$JAVA_HOME/bin/java`, then `java` on
`PATH`, and rejects an observed major version below 17 before Picard starts.
Use the [Step `04` owner](#step-04-markduplicates) for its exact invocation.

### Python And RSeQC

Known site module names are `python39`, `python3`, and `python314`. Step `03`
prefers `.venv/bin/infer_experiment.py` relative to the invocation directory,
then `infer_experiment.py` on `PATH`. Outside the checkout root, pass an
explicit absolute `--infer-experiment-bin`.

```bash
.venv/bin/infer_experiment.py --version
```

### GATK

```bash
gatk --version
```

Current wrappers expect GATK `4.6.1.0` and Java 17. A successful version probe
does not validate Step `05` inputs or execution.

### bcftools

```bash
/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools --version
```

Availability does not establish Step `07` dry-run, execute, output, or cluster
proof.

### Local R And Unresolved Cluster Runtime

Use the [guarded local-R procedure](#guarded-local-r-environment) for the
repository environment. Use the runtime preflight inside an approved batch or
compute allocation to establish cluster visibility. Local R evidence is not
cluster R evidence; current results and unresolved runtime facts belong in
[`HANDOFF.md`](HANDOFF.md#evidence-boundary).

## Cluster Facts And Quirks

### First Login / Fresh Checkout

Inspect the site and scheduler before doing work:

```bash
hostname
whoami
pwd
command -v sbatch
command -v squeue
command -v sinfo
squeue -u "$USER"
sinfo
module avail
module list
```

For a new checkout:

```bash
git clone https://github.com/Glen-Cocoa/norad.git ~/norad
cd ~/norad
git status --short
mkdir -p logs
```

For an existing checkout, use the explicitly approved branch/ref and update
method; do not use an unqualified pull as evidence that the intended ref is
checked out. The lightweight manifest smoke job is:

```bash
mkdir -p logs
sbatch src/norad/ingestion/sample_manifest_admission/validate_manifest.slurm
```

### SLURM

Known site limits are approximately three hours for `short` and three days for
`long`. Treat each wrapper's resource request as its current declared request,
not a measured guarantee. Submit owner-local `.slurm` files from the intended
checkout; there is no root `jobs/` directory.

### Logs

Create the scheduler log directory before submission:

```bash
mkdir -p logs
```

Wrappers normally declare:

```text
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

### TMPDIR

For ordinary wrappers:

```bash
TMPDIR=/tmp
```

The site may warn that `/local/tmp` is not writable before falling back to
`/tmp`. Confirm the job's observed value in its log. Step `05` is the exception:
its Java/HTSJDK/GATK spill must use the owner-documented per-run project-storage
temporary directory.

### module list

`module list` writes to stderr. In a script:

```bash
module list 2>&1 || true
```

## Optional Cluster Shell Helpers

The cluster shell is Bash. Local aliases such as `norad`, `nlogs`, `sqme`,
`sj <jobid>`, `sjtail <jobid>`, and `sjcheck <jobid>` are conveniences only.
The portable commands are in [Manual Job Checking](#manual-job-checking).

## Artifact And Future Operational Helpers

These tools operate only on explicit inputs. They do not discover production
outputs, install analysis software, clear locks, repair artifacts, or promote
evidence. Dry-run is the default where stated; inspect it before `--execute`.
Transaction-specific recovery routes are in
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

### Run The Explicit Runtime Preflight

Prepare a site-specific copy of
[`configs/runtime_preflight.example.tsv`](../../configs/runtime_preflight.example.tsv).
The profile declares tool-version, R-namespace, hash-utility, or absolute-path
visibility probes for `local`, `cluster_batch`, or `any`.

Local dry-run:

```bash
.venv/bin/python src/norad/evidence/runtime_preflight/runtime_preflight.py \
  --profile configs/runtime_preflight.example.tsv \
  --output results/qc/runtime/local.runtime_preflight.tsv \
  --runtime-context local
```

Approved batch/compute dry-run, then publication:

```bash
python3 src/norad/evidence/runtime_preflight/runtime_preflight.py \
  --profile /explicit/path/to/csu.runtime_profile.tsv \
  --output results/qc/runtime/csu.runtime_preflight.tsv \
  --runtime-context cluster_batch

mkdir -p results/qc/runtime
python3 src/norad/evidence/runtime_preflight/runtime_preflight.py \
  --profile /explicit/path/to/csu.runtime_profile.tsv \
  --output results/qc/runtime/csu.runtime_preflight.tsv \
  --runtime-context cluster_batch \
  --execute
```

Exit zero means probes and optional publication completed, not that required
rows passed. Inspect every `pass`, `fail`, `blocked`, and `not_checked` row.
Focused protection:

```bash
.venv/bin/python -m pytest -q tests/evidence/runtime_preflight/test_runtime_preflight.py
```

The separate diagnostic-only scheduler probe is:

```bash
mkdir -p logs
sbatch src/norad/evidence/runtime_preflight/tool_check.slurm
```

### Inventory Storage And Record Retention Policy

Replace the illustrative paths and approvals in
`configs/storage_roots.example.tsv` and
`configs/retention_policy.example.tsv`. The tool measures named roots without
following symlinks and records policy state; it never performs a retention
action.

```bash
.venv/bin/python src/norad/evidence/storage_inventory/storage_inventory.py \
  --roots /explicit/path/to/storage_roots.tsv \
  --retention-policy /explicit/path/to/retention_policy.tsv \
  --output-root results/qc/storage

mkdir -p results/qc/storage
.venv/bin/python src/norad/evidence/storage_inventory/storage_inventory.py \
  --roots /explicit/path/to/storage_roots.tsv \
  --retention-policy /explicit/path/to/retention_policy.tsv \
  --output-root results/qc/storage \
  --execute
```

Execute mode publishes `storage_inventory.tsv`, `retention_policy.tsv`, then
`storage_retention_summary.tsv`. Exit zero does not mean `overall_status`
passed. Focused protection:

```bash
.venv/bin/python -m pytest -q tests/evidence/storage_inventory/test_storage_inventory.py
```

### Reconcile Explicit Reference Provenance

Replace the illustrative values in
`configs/reference_provenance.example.tsv`. Relative paths resolve only from
the explicit base directory; the tool does not discover, repair, regenerate,
rename, or normalize reference artifacts.

```bash
.venv/bin/python src/norad/evidence/reference_provenance/reference_provenance.py \
  --inventory configs/reference_provenance.example.tsv \
  --base-dir . \
  --output-root results/qc/reference_provenance

mkdir -p results/qc/reference_provenance
.venv/bin/python src/norad/evidence/reference_provenance/reference_provenance.py \
  --inventory /explicit/path/to/reference_provenance.tsv \
  --base-dir /explicit/reference/root \
  --output-root results/qc/reference_provenance \
  --execute
```

The per-reference summary is published last. Inspect missing files, hash
mismatches, contig agreement, annotations, and `overall_status` explicitly.

```bash
.venv/bin/python -m pytest -q tests/evidence/reference_provenance/test_reference_provenance.py
```

### Validate `artifact-schema-v1`

Validate schemas and the synthetic example inventory:

```bash
.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
```

Validate one explicit public document with the applicable schema:

```bash
.venv/bin/python src/norad/contracts/artifacts/validate_artifact_contracts.py \
  --schema artifact-record \
  --document /explicit/path/to/artifact_record.json \
  --inventory /explicit/path/to/artifact_inventory.tsv
```

Supported schema selectors are `artifact-record`, `scientific-review-record`,
`run-summary`, and `report-receipt`. The validator is read-only and does not
discover sources, build an index, render a report, or promote evidence.

```bash
.venv/bin/python -m pytest -q tests/contracts/artifacts/test_artifact_schema_contracts.py
```

### Build An `artifact-adapters-v1` Index

Dry-run with an explicit run contract and inventory:

```bash
.venv/bin/python src/norad/reporting/build_artifact_index.py \
  --run-id RUN_ID \
  --run-contract RUN_CONTRACT_JSON \
  --inventory INVENTORY_TSV \
  --output-root results/artifacts
```

After inspection, repeat with `--execute`. Successful publication creates
`records/<artifact_id>.json`, `<run_id>.artifacts.tsv`, and the receipt last:

```bash
.venv/bin/python src/norad/reporting/build_artifact_index.py \
  --run-id RUN_ID \
  --run-contract RUN_CONTRACT_JSON \
  --inventory INVENTORY_TSV \
  --output-root results/artifacts \
  --execute
```

Changing an immutable run-contract identity requires a new `run_id`. A complete
receipt commits the adapter transaction; it does not mean every declared source
exists or is complete. Never combine attempts, manufacture a receipt, or delete
a foreign lock.

```bash
.venv/bin/python -m pytest -q tests/reporting/test_artifact_adapters.py
```

### Build An `artifact-run-summary` Transaction

The adapter transaction must already be complete. Dry-run:

```bash
.venv/bin/python src/norad/reporting/build_run_summary.py \
  --run-id RUN_ID \
  --artifact-receipt results/artifacts/RUN_ID/RUN_ID.artifact_receipt.tsv \
  --output-root results/artifacts
```

Append an explicit committed Step `09c` summary when one exists:

```text
--science-review-summary results/scientific_validation/REVIEW_ID/REVIEW_ID.step09c_review_summary.tsv
```

Append `--report-table-approvals /explicit/path/to/report_table_approvals.tsv`
only for an inspected approval manifest. Neither optional input is discovered.
Execute by repeating the dry-run with `--execute`. The canonical JSON, summary
TSV, QC TSV, and receipt-last transaction are written beneath the same run
directory. `summary_state=complete` describes transaction completeness, not
scientific completeness.

```bash
.venv/bin/python -m pytest -q tests/reporting/test_artifact_run_summary.py
```

### Restore Quarto And Render The Static Report Bundle

Dependency restoration is an explicit setup action:

```bash
make quarto-restore
```

The restore verifies the pinned official Quarto archive and publishes beneath
ignored `.tools/`. The renderer never downloads or installs dependencies.
Dry-run, then execute:

```bash
src/norad/reporting/render_run_report.sh \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto

src/norad/reporting/render_run_report.sh \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto \
  --execute
```

Use `--formats html`, `--formats pdf`, or `--formats all` (default). The bundle
publishes selected formats, summary, and receipt last. A rendered bundle
projects only its validated inputs and does not promote their evidence state.

```bash
make report-test
```

Run `make quarto-restore` first. Passing report tests is local synthetic
renderer evidence only.

### Generate The Populated Synthetic Demo Report

After explicit dependency setup:

```bash
make demo-report
```

Optional projections and ignored output root:

```bash
make demo-report DEMO_REPORT_FORMATS=html
make demo-report DEMO_REPORT_FORMATS=pdf
make demo-report DEMO_REPORT_ROOT=/explicit/ignored/demo-report
```

The default bundle is under
`results/demo-report/reports/synthetic_full_run_demo/`. Everything beneath
`results/` is ignored and must not be committed. The demo is deterministic,
synthetic, exploratory, and provisional; it is not production execution,
completed production review, or biological validation.

## Manual Job Checking

```bash
ls -ltr logs | tail
squeue -u "$USER"
squeue -j <JOBID>
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
tail -F logs/<log-prefix>-<JOBID>.out logs/<log-prefix>-<JOBID>.err
```

While a job runs, inspect only its declared output root:

```bash
du -sh <output_dir>
ls -lh <output_dir>
```

Scheduler success alone is not output validation. Bind logs, accounting,
inputs, commit, command, and outputs to the same attempt.

## Inspect Or Change Task Lifecycle

The [`task registry`](../tasks/README.md#lifecycle-rules) owns state semantics,
completion criteria, and legacy compatibility. Inspect the deterministic view:

```bash
./scripts/git_orchestration/task_status.py \
  --repo "$(git rev-parse --show-toplevel)"
```

New cards use `docs/tasks/cards/<CARD-ID>-<slug>.md`. When lifecycle itself
changes, edit the card's exact `State:` field and completion record inside the
semantic package, then inspect it:

```bash
rg -n '^State:|^## Completion record' \
  docs/tasks/cards/<CARD-ID>-<slug>.md
git diff -- docs/tasks/cards/<CARD-ID>-<slug>.md
git diff --check
make -s documentation-check
```

Do not move a card for selection, pause, resume, or completion. A legacy card's
explicit state overrides its directory, so a real lifecycle change does not
require path or inbound-link repair. Do not edit a `review` card's candidate
until an approved correction returns it to `planned`. `UNREFINED` proposals are
not selectable cards.

## Concurrent Worktrees And Serialized Integration

[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md) owns authority, lane packets,
coupling, handoff, and recovery. Verify identity and cleanliness before any
candidate operation:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git worktree list --porcelain
```

Do not infer that a worktree is available from its name. Do not switch, pull,
merge, rebase, stash, reset, clean, unlock, remove, amend, or publish another
lane. Preserve a frozen candidate and any failure state until the integration
owner decides its disposition.

### Verify The Canonical Integration Lane

The canonical owner verifies the exact path, branch, clean status, upstream,
local/remote SHA, and ahead/behind result required by the active lane packet.
Network fetch and publication require authority for the named ref. Equality
against a stale local remote-tracking ref is not remote verification.

### Manual Integration Fragment Exchange

The fragment schema is in [`docs/fragments/README.md`](../fragments/README.md),
authority is in
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md#integration-fragment-authority-and-lifecycle),
and tested command interfaces are indexed by
[`scripts/git_orchestration/README.md`](../../scripts/git_orchestration/README.md).

Use the tools in this order:

1. `validate_fragment_candidate.py` binds the frozen candidate, base, exact
   diff, reservations, fragment, and source ref.
2. `validate_fragment_target.py` checks each declared canonical target; the
   integration owner reviews drift and assigns every request a disposition.
3. `apply_fragment_candidate.sh` runs dry first, then with `--execute` to apply
   a valid candidate, or `record_fragment_noop.sh` records a true no-change
   outcome.
4. `finalize_fragment_integration.sh` runs dry first, then with `--execute` to
   stage only declared final paths, remove the fragment, and bind reviewed
   disposition trailers.
5. Run the complete applicable gate, then use `publish_exact_ref.sh` dry first
   and with `--execute` only under publication authority.

Inspect each complete interface before use:

```bash
python3 scripts/git_orchestration/validate_fragment_candidate.py --help
python3 scripts/git_orchestration/validate_fragment_target.py --help
scripts/git_orchestration/apply_fragment_candidate.sh --help
scripts/git_orchestration/finalize_fragment_integration.sh --help
scripts/git_orchestration/record_fragment_noop.sh --help
scripts/git_orchestration/publish_exact_ref.sh --help
```

If application or finalization fails, do not reset, clean, stash, amend, delete,
or overwrite the recovery state. Record the parent, branch, `HEAD`, status,
staged and unstaged diffs, untracked paths, and source ref; preserve or lock the
worktree and follow the helper diagnostic.

## Local Validation Gate

Use focused tests while an executable surface is changing:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
```

Run one complete computational gate against the final executable tree. The
coverage lane already runs the complete Python suite; do not duplicate it with
an uninstrumented full pytest run.

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks
```

The gate runs static preflight, complete Python coverage, shell contracts,
guarded local R plus real-R Step `08`/`09` tests, and pinned report-runtime
tests. Diagnose concurrency-specific behavior serially or stream an explicitly
verbose run:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript \
  make -s all-checks VALIDATION_ARGS=--serial

RSCRIPT_BIN=/usr/local/bin/Rscript \
  make -s all-checks VALIDATION_ARGS=--verbose
```

Record a machine-readable result at an ignored or temporary path when needed:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript \
  make -s all-checks \
  VALIDATION_ARGS="--result-json /private/tmp/norad-validation.json"
```

Retain and inspect any failed or interrupted lane log. `SIGINT` returns `130`
and the gate reports retained running-lane logs. A failure in one lane does not
erase passing evidence from another, but the aggregate gate remains non-green.

For a qualifying documentation-only package under
[`TASK_DELIVERY.md`](TASK_DELIVERY.md#default-delivery):

```bash
git diff --check
make -s documentation-check
git status --short
git diff --name-status
```

The documentation target delegates to
`scripts/git_orchestration/validate_documentation.py`. It checks paths, anchors,
task-card paths, states, schemas and dependencies, orphan diagrams, and basic
Mermaid structure, including untracked documents. Task cards do not require an
external inbound status link. The gate does not replace semantic review of
affected architecture or scientific content.

### Python coverage baseline

Dependency synchronization is an explicit developer setup action:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Measure and compare the complete Python suite:

```bash
make python-coverage-check
```

Do not update the baseline to silence a regression. For an approved source/test
change, regenerate, inspect the JSON diff, and recheck:

```bash
make python-coverage-baseline-update
git diff -- tests/baselines/python_coverage.json
make python-coverage-check
```

The numerical baseline does not replace shell, guarded-R, report-runtime,
transaction, recovery, or independent-oracle tests.

### Guarded local R environment

R restoration is an explicit developer action:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

These targets opt into the repository library with `NORAD_USE_RENV=1`. The
guard disables automatic snapshots and the `renv` sandbox. `r-check` verifies
the declared runtime/namespaces, release validity, lock synchronization, and
headless PDF support; `local-real-r-test` runs guarded Step `08` and Step `09`
semantic fixtures. Passing establishes local configured-environment evidence
only, not production data, batch visibility, cluster proof, or scientific
review.

## Cluster Execution Pattern

Cluster promotion is upstream-sequential. Operate from one explicitly approved
commit and input set; do not submit a downstream owner until the predecessor's
outputs and evidence have been inspected.

```bash
cd <approved-checkout>
git branch --show-current
git rev-parse HEAD
test -z "$(git status --porcelain=v1)"
mkdir -p logs
```

Then:

1. Open the applicable owner-local `README.md` below and bind every explicit
   input, executable, manifest, output root, and execution mode.
2. Run the owner's dry-run or submit `EXECUTE=0` where supported.
3. Inspect the resolved plan, scheduler state, stdout/stderr, inputs, space,
   and any dry-run residue allowed by that owner's contract.
4. Submit or invoke execute mode only under its authorization.
5. Inspect scheduler accounting, native outputs, owner validator dry-run, and
   the published validation record. Exit zero may coexist with failed evidence
   rows or characterized stale-output defects.
6. Record commit, command/job ID, input/config hashes, logs, output paths and
   hashes, validator result, and evidence ceiling before promotion.

Use [Manual Job Checking](#manual-job-checking) for scheduler inspection and
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) before any cleanup or retry. Never
delete a foreign lock, mix attempts, hand-edit a receipt, or infer transaction
completion from summary visibility alone.

## Workflow contract and validation convention

The canonical graph is [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md).
Each owner README provides supported root/arbitrary-CWD, dry-run, execute,
scheduler, focused-test, diagnostics, and recovery routes; its adjacent
contract owns inputs, outputs, exact checks, and evidence limits.

| Alias | Operator owner | Functional contract |
| --- | --- | --- |
| `00a` | [`construct_STAR_index`](../../src/norad/stages/construct_STAR_index/README.md) | [`CONTRACT`](../../src/norad/stages/construct_STAR_index/CONTRACT.md) |
| `00b` | [`convert_GTF_to_BED12`](../../src/norad/stages/convert_GTF_to_BED12/README.md) | [`CONTRACT`](../../src/norad/stages/convert_GTF_to_BED12/CONTRACT.md) |
| `00c` | [`construct_FASTA_sidecars`](../../src/norad/stages/construct_FASTA_sidecars/README.md) | [`CONTRACT`](../../src/norad/stages/construct_FASTA_sidecars/CONTRACT.md) |
| `01` | [`align_RNA_reads_with_STAR`](../../src/norad/stages/align_RNA_reads_with_STAR/README.md) | [`CONTRACT`](../../src/norad/stages/align_RNA_reads_with_STAR/CONTRACT.md) |
| `02` | [`construct_canonical_BAM`](../../src/norad/stages/construct_canonical_BAM/README.md) | [`CONTRACT`](../../src/norad/stages/construct_canonical_BAM/CONTRACT.md) |
| `02b` | [`collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/README.md) | [`CONTRACT`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/CONTRACT.md) |
| `03` | [`collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/README.md) | [`CONTRACT`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/CONTRACT.md) |
| `04` | [`mark_BAM_duplicates_with_Picard`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/README.md) | [`CONTRACT`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/CONTRACT.md) |
| `05` | [`split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_N_cigar_reads_with_GATK/README.md) | [`CONTRACT`](../../src/norad/stages/split_N_cigar_reads_with_GATK/CONTRACT.md) |
| `06` | [`partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/README.md) | [`CONTRACT`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/CONTRACT.md) |
| `07` | [`generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/README.md) | [`CONTRACT`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md) |
| `08` | [`preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/README.md) | [`CONTRACT`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md) |
| `09` | [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md) | [`CONTRACT`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md) |
| `09c` | [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/assemble_scientific_review_evidence_package/README.md) | [`CONTRACT`](../../src/norad/evidence/assemble_scientific_review_evidence_package/CONTRACT.md) |

Structured validators are dry-run by default. Their exit zero means checks ran
and optional publication completed; inspect the report rows. They do not repair
native outputs, rerun producers, or promote evidence.

### Inline block disposition

Only three cross-owner checks remain inline because no closer tested owner
implements their whole-universe comparison: Step `07` manifest pairing, Step
`07` selector/output census, and Step `09` full-table subset reconciliation.
All per-owner producer, scheduler, validator, and recovery commands route to
the adjacent README above.

## Reference Prep

Reference preparation has three independent owners. Establish and record source
provenance before generating or replacing an index, BED12 annotation, FAI, or
dictionary. Use the reference-provenance helper for the complete declared
bundle; do not infer compatible identities from filenames.

### Step 00a: STAR Index

[`construct_STAR_index`](../../src/norad/stages/construct_STAR_index/README.md)
embeds its producer in a scheduler file and executes on submission; it has no
dry-run mode:

```bash
mkdir -p logs
sbatch src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm
```

The job resolves hardcoded Novogene inputs and `refs/` outputs from the caller's
working directory. Inspect those exact paths before submission.

### Step 00b: GTF To BED12

Use the exact producer, validator, scheduler, and focused-test commands in the
[`convert_GTF_to_BED12` owner](../../src/norad/stages/convert_GTF_to_BED12/README.md).

### Step 00c: GATK Reference Sidecars

Use the exact dry-run-first producer, validator, scheduler, and recovery route
in the
[`construct_FASTA_sidecars` owner](../../src/norad/stages/construct_FASTA_sidecars/README.md).

## Step 01: STAR Alignment

Use the [`align_RNA_reads_with_STAR` owner](../../src/norad/stages/align_RNA_reads_with_STAR/README.md).
Its producer may leave direct final-directory residue after failure; preserve
the complete attempt for diagnosis.

## Step 02: Canonical Sort, Read-Group Tagging, And BAM Indexing

Use the [`construct_canonical_BAM` owner](../../src/norad/stages/construct_canonical_BAM/README.md).
Treat an incomplete BAM/BAI pair or failed restoration as ambiguous state.

## Step 02b: BAM QC

Use the
[`collect_canonical_BAM_QC_evidence` owner](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/README.md).
This is non-gating evidence; producer or scheduler exit zero does not make a
stale or incomplete pair current.

## Step 03: RSeQC Strandedness / Orientation Inference

Use the
[`collect_RSeQC_paired_orientation_evidence` owner](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/README.md).
Its evidence describes observed read orientation; it does not select a
biological strandedness policy.

## Step 04: MarkDuplicates

Use the [`mark_BAM_duplicates_with_Picard` owner](../../src/norad/stages/mark_BAM_duplicates_with_Picard/README.md).
Verify the actual selected Java executable/version and Picard JAR in the same
attempt's logs.

## Step 05: SplitNCigarReads

Use the [`split_N_cigar_reads_with_GATK` owner](../../src/norad/stages/split_N_cigar_reads_with_GATK/README.md).
Its project-storage temp route is required; do not substitute generic `/tmp`
without a reviewed contract change.

## Step 06: Split BAM By Read Orientation

Use the
[`partition_BAM_by_mechanical_read_orientation` owner](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/README.md).
The split is mechanical and does not validate transcript-strand interpretation.

## Step 07: bcftools mpileup

Use the exact dry-run, scheduler, validator, and transaction commands in the
[`generate_partitioned_cohort_mpileup_VCFs` owner](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/README.md).
The pilot manifest is validation-only; the primary manifest declares the
correction universe. Never replace either contract with a VCF glob.

The runtime sample manifest must match the approved pairing reference exactly:

```bash
python src/norad/ingestion/sample_manifest_admission/validate_manifest.py \
  --manifest samples.tsv

diff -u \
  <(tail -n +2 configs/step_09_pairs.NORAD_EV_PUM1.tsv | LC_ALL=C sort) \
  <(awk -F '\t' '
      NR == 1 {
          for (i = 1; i <= NF; i++) {
              if ($i == "sample_id") sample_column = i
              if ($i == "condition") condition_column = i
              if ($i == "replicate") replicate_column = i
          }
          if (!sample_column || !condition_column || !replicate_column) exit 1
          next
      }
      {
          if ($sample_column == "" || $condition_column == "" ||
              $replicate_column == "") exit 1
          print $sample_column "\t" $condition_column "\t" $replicate_column
      }
  ' samples.tsv | LC_ALL=C sort)
```

The `diff` must be empty. Assert that each primary selector appears exactly once
in the reference FAI:

```bash
awk -F '\t' '
    FNR == NR {
        if (FNR > 1) {
            if ($2 != "region" || required[$3]++) exit 1
            required_count++
        }
        next
    }
    { fai_count[$1]++ }
    END {
        if (required_count != 25) exit 1
        for (contig in required) {
            if (fai_count[contig] != 1) {
                print "FAI mismatch for " contig > "/dev/stderr"
                exit 1
            }
        }
        print "primary_fai_contigs=" required_count
    }
' configs/step_07_partitions.primary_contigs.tsv \
  refs/novogene_ref/genome.fa.fai
```

After every manifest-named primary partition has independently validated,
count only that declared universe:

```bash
set -euo pipefail
cohort=NORAD_EV_PUM1
partition_manifest=configs/step_07_partitions.primary_contigs.tsv
receipt_count=0
vcf_count=0

while IFS=$'\t' read -r partition_id selector_type selector_value; do
    [[ "$partition_id" == "partition_id" ]] && continue
    out_dir="results/mpileup/$cohort/$partition_id"
    test -s "$out_dir/$cohort.$partition_id.step07_outputs.tsv"
    for orientation in FWD_like REV_like; do
        test -s "$out_dir/$cohort.$partition_id.$orientation.mpileup.vcf"
        vcf_count=$((vcf_count + 1))
    done
    receipt_count=$((receipt_count + 1))
done < "$partition_manifest"

[[ "$receipt_count" -eq 25 ]]
[[ "$vcf_count" -eq 50 ]]
printf 'primary_receipts=%s primary_vcfs=%s\n' "$receipt_count" "$vcf_count"
```

Counts supplement per-partition validation, sample-order, selector, hash,
record-count, scheduler/log, lock, and scratch inspection; they are not proof
by themselves.

## Step 08: VCF Preprocessing

Use the
[`preprocess_and_annotate_cohort_candidates` owner](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/README.md).
Run only after the complete declared Step `07` primary universe and the guarded
R environment are available in the intended execution context.

## Step 09: CMH Editing-Site Calling

Use the exact producer, guarded-R, scheduler, validator, and recovery commands
in the
[`rank_cohort_candidates_with_paired_CMH` owner](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md).
The output is CMH-ranked cohort candidates, not validated editing sites.

After owner validation, perform the full-table row and exact-subset scan in an
allocated compute/batch context for production tables:

```bash
set -euo pipefail
analysis=NORAD_EV_vs_PUM1
out_dir="results/editing/$analysis"
all="$out_dir/$analysis.cmh_all_sites.tsv"
significant="$out_dir/$analysis.cmh_significant_sites.tsv"
summary="$out_dir/$analysis.cmh_summary.tsv"
spectrum="$out_dir/$analysis.mutation_spectrum.tsv"
step08_sites="results/vcf_preprocessed/NORAD_EV_PUM1/NORAD_EV_PUM1.step08_sites.tsv"

[[ "$(awk 'END { print NR - 1 }' "$all")" -eq \
   "$(awk 'END { print NR - 1 }' "$step08_sites")" ]]
[[ "$(awk 'END { print NR - 1 }' "$summary")" -eq 1 ]]
[[ "$(awk 'END { print NR - 1 }' "$spectrum")" -eq 12 ]]

diff -u \
  <(awk -F '\t' '
      NR == 1 {
          for (i = 1; i <= NF; i++) {
              if ($i == "call_status") call_column = i
          }
          if (!call_column) exit 1
          print
          next
      }
      $call_column == "significant_up" ||
      $call_column == "significant_down" { print }
  ' "$all") \
  "$significant"
```

The `diff` must be empty. Also require the owner validator, exact schemas and
hashes, reconciled status totals, two structurally complete PDFs, scheduler
`COMPLETED 0:0`, inspected logs, and no unexplained lock or run-token residue.

## Post-Step 09: Scientific Validation Gate

Use the dry-run-first explicit evidence package and recovery procedure in the
[`assemble_scientific_review_evidence_package` owner](../../src/norad/evidence/assemble_scientific_review_evidence_package/README.md).
It packages declared reviewer evidence; it does not rerun CMH, infer decisions,
authenticate execution metadata, or grant biological readiness.

Keep computational state, evidence-category state, orientation state, and
overall science state separate. The only current overall science states are
`evidence_incomplete` and `science_review_complete_exploratory`;
`biological_interpretation_ready` remains reserved and rejected.

Rerun routing that is not encoded by one owner:

```text
manifest or partition universe -> gated config/evidence change, then Steps 07-09
Step 07 filter or maximum depth -> contract/version decision, then Steps 07-09
new background samples -> prove their Steps 01-06 inputs, then Steps 07-09
background already in unchanged Step 08 columns -> new Step 09 analysis ID
GTF input -> Steps 08-09
orientation normalization policy -> reviewed Steps 08-09 contract/code, then runtime
Step 09 target/contrast/background/threshold defaults -> new analysis ID and full-family BH
CMH method, correction, or testability -> Step 09 implementation, then new-ID runtime
FASTA or coordinates -> upstream reference/alignment impact review
manual adjudication labels -> no compute rerun
new automated filter -> separate implementation and test package
```

Production audit and adjudication tables stay in approved results storage.
Commit only approved compact summaries, paths, hashes, decisions, and
limitations.

## Temporary Java Workaround

Cluster Java availability has varied by node. Do not pin a node as a permanent
default, copy a JDK between nodes, or infer the runtime from a module name.
Continue logging and validating the selected executable's `java -version`.
The durable resolution is a CSU-supported cluster-wide Java 17 path.

## Reference Workflow Alignment

The implemented semantic route is:

```text
reference preparation -> STAR alignment -> canonical BAM
-> MarkDuplicates -> SplitNCigarReads -> mechanical orientation partition
-> cohort mpileup -> VCF preprocessing -> paired CMH ranking
-> explicit scientific-review evidence -> report projection
```

Use [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) for exact required
and optional edges. Historical numeric aliases are navigation labels, not the
machine-readable architecture.
