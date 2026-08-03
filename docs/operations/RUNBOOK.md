# Runbook

Operational guide for the NORAD / Novogene Remora RNA-seq pipeline.

This file owns exact supported commands and their immediate operator context.
Package delivery order and validation applicability belong to
[`TASK_DELIVERY.md`](TASK_DELIVERY.md#package-delivery).

Cluster promotion remains upstream-sequential: use only an approved current
job, dry-run, inspect, execute, inspect scheduler/log/output evidence, and
docpatch that evidence before promoting the next step. Do not run scaffolded
future jobs.

## Command index

- Orientation: [project locations](#project-locations),
  [demo and inspection](#demo--inspection-checklist),
  [cluster tools](#confirmed-cluster-tools--modules), and
  [cluster facts](#cluster-facts-and-quirks).
- Shared operations: [optional shell helpers](#optional-cluster-shell-helpers),
  [artifact and future helpers](#artifact-and-future-operational-helpers),
  [manual job checking](#manual-job-checking), and
  [cluster execution](#cluster-execution-pattern).
- Delivery: [concurrent worktrees](#concurrent-worktrees-and-serialized-integration),
  [manual fragment exchange](#manual-integration-fragment-exchange), and the
  [local validation gate](#local-validation-gate).
- Workflow: [contract and validation convention](#workflow-contract-and-validation-convention),
  [reference preparation](#reference-prep), [Step `01`](#step-01-star-alignment),
  [Step `02`](#step-02-canonical-sort-read-group-tagging-and-bam-indexing),
  [Step `02b`](#step-02b-bam-qc),
  [Step `03`](#step-03-rseqc-strandedness--orientation-inference),
  [Step `04`](#step-04-markduplicates),
  [Step `05`](#step-05-splitncigarreads),
  [Step `06`](#step-06-split-bam-by-read-orientation),
  [Step `07`](#step-07-bcftools-mpileup),
  [Step `08`](#step-08-vcf-preprocessing),
  [Step `09`](#step-09-cmh-editing-site-calling), and the
  [scientific validation gate](#post-step-09-scientific-validation-gate).
- Retained exceptions: [temporary Java workaround](#temporary-java-workaround)
  and [reference workflow alignment](#reference-workflow-alignment).

## Project Locations

Local repo:

```bash
/Users/elisteiger/dev/norad
```

Cluster repo:

```bash
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

Raw data symlink on cluster:

```bash
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs are under:

```bash
data/raw/novogene_remora/01.RawData/*.fq.gz
```

Manifest:

```bash
samples.tsv
```

Known samples:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

Conditions:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Note: `ABE_EV4` does not have an underscore before `4`.

## Demo / Inspection Checklist

Use this checklist for a short read-only project demo. These commands inspect the repo, docs, or existing outputs; they do not submit jobs.

1. Show repo state and docs:

```bash
git status --short
sed -n '1,90p' README.md
```

2. Show the tactical pipeline map:

```bash
sed -n '1,120p' docs/design/PIPELINE_PLAN.md
```

3. Show the sample manifest:

```bash
sed -n '1,20p' samples.tsv
```

4. Show proven output locations when present:

```bash
for path in \
  refs/novogene_star_index \
  refs/novogene_ref/genome.bed \
  refs/novogene_ref/genome.fa.fai \
  refs/novogene_ref/genome.dict \
  results/bam \
  results/qc/bam \
	  results/qc/strandedness \
	  results/markdup \
	  results/split_ncigar \
	  results/orientation \
	  results/qc/orientation
do
  if [ -e "$path" ]; then
    ls -ld "$path"
  else
    printf 'pending or unavailable here: %s\n' "$path"
  fi
done
```

5. Show Step `05` validation status and resolved temp-spill hardening:

```bash
squeue -u "$USER"
ls -ltr logs | tail
grep -n "SplitNCigarReads\|No space left on device\|tmp-dir\|java.io.tmpdir" \
  logs/norad-split-n-cigar-*.out logs/norad-split-n-cigar-*.err 2>/dev/null | tail -40
```

6. Show the dry-run/execute gate:

```bash
grep -n "EXECUTE\|--execute\|dry-run" \
  jobs/step_05_split_n_cigar_reads.slurm \
  scripts/step_05_split_n_cigar_reads.sh | head -60
```

Use the current [`HANDOFF.md` evidence boundary](HANDOFF.md#evidence-boundary)
when selecting and narrating demo surfaces. Tool availability, help text,
dry-runs, mocks, local fixtures, synthetic transactions, and rendered synthetic
reports must not be presented as production, cluster, scientific-review, or
biological evidence. Never demonstrate an artifact that the handoff does not
record as existing.

## Confirmed Cluster Tools / Modules

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
```

Known module behavior:

```text
sets PICARD=/cm/shared/apps/picard/picard/build/libs/picard.jar
may load java/17.0.10
```

Do not infer the effective Java runtime from the module name or `JAVA_HOME` alone. Step `04` logs and validates the selected executable's actual `java -version` before Picard starts.

Step `04` Java resolution order:

1. Use `JAVA_BIN_OVERRIDE`, when explicitly provided.
2. Use `$JAVA_HOME/bin/java`, only if that path exists and is executable.
3. Fall back to `command -v java`.

The wrapper then:

* verifies the selected Java path exists and is executable
* runs the selected executable with `-version`
* parses the actual major Java version
* fails clearly before Picard starts if the version is below 17

Step `04` logs should retain:

* compute-node name
* loaded modules
* `JAVA_HOME`
* selected Java executable
* actual `java -version`
* resolved Picard JAR
* resolved samtools executable

### Python And RSeQC

Known Python modules:

```bash
python39
python3
python314
```

RSeQC is available through the project virtual environment on the cluster:

```bash
.venv/bin/infer_experiment.py
```

Step `03` prefers that project executable when present and otherwise resolves:

```bash
infer_experiment.py
```

### GATK

GATK availability is confirmed on compute node `node002`:

```text
Java: OpenJDK 17.0.14
GATK: 4.6.1.0
GATK path: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
tool probe exit code: 0:0
```

Step `05` is implemented and cluster-proven across all six samples.

### bcftools

bcftools availability is confirmed on compute node `node002`:

```text
bcftools: 1.21
bcftools path: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
tool probe exit code: 0:0
```

Step `07` is implemented locally and locally tested with mocked bcftools. The executable probe above confirms tool availability only; no Step `07` cluster dry-run, execute run, or output evidence has been inspected. Step `07` is not cluster-proven.

### Local R And Unresolved Cluster Runtime

The signed Apple-silicon CRAN R `4.6.1` runtime is installed locally and the
guarded repository `renv` environment is locked to Bioconductor `3.23`. Local
runtime and package-environment checks pass. The Step `08` and Step `09`
real-R suites also pass locally without `SKIP` after the `step-09b1` fixes.
This is local fixture evidence only; see the local R section and
troubleshooting guide for the exact scope.

A supported R/Rscript path and compatible package library visible in the CSU
batch/compute environment remain unresolved. Local runtime evidence is not
cluster runtime evidence.

## Cluster Facts And Quirks

### First Login / Fresh Checkout

```bash
hostname
whoami
pwd
which sbatch
which squeue
which sinfo
squeue -u "$USER"
sinfo
module avail
module list
```

Create or enter the project checkout:

```bash
mkdir -p ~/norad
cd ~/norad
```

If the repository is not already cloned:

```bash
git clone https://github.com/Glen-Cocoa/norad.git .
```

After cloning or before running jobs:

```bash
git pull
git status --short
mkdir -p logs
```

Run a lightweight manifest-validation smoke job after cloning or pulling:

```bash
sbatch jobs/validate_manifest.slurm
```

### SLURM

Known partition behavior:

```text
short: about 3 hour max walltime
long: about 3 day max walltime
```

Most current development jobs use `short`. No special account setting has been required so far.

### Logs

Always create logs before submitting jobs:

```bash
mkdir -p logs
```

Jobs use:

```bash
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

### TMPDIR

Use:

```bash
TMPDIR=/tmp
```

Submit execute jobs like:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Known cluster warning:

```text
slurmstepd: error: TMPDIR [/local/tmp] is not writeable
slurmstepd: error: Setting TMPDIR to /tmp
```

This has not been fatal when the job itself logs `TMPDIR: /tmp`.

Exception: Step `05` GATK `SplitNCigarReads` must route Java/HTSJDK/GATK temp files to a per-run project-storage temp directory rather than relying on node-local `/tmp`.

### module list

`module list` writes to stderr. In scripts, use:

```bash
module list 2>&1 || true
```

## Optional Cluster Shell Helpers

The cluster shell is bash, not zsh.

Optional helpers may be installed in `~/.bashrc`:

```bash
norad       # cd to NORAD repo
nlogs       # show recent logs
sqme        # show user's SLURM queue
sj <jobid>  # sacct summary
sjtail <jobid>
sjcheck <jobid>
```

Recommended quick checks:

```bash
norad
sqme
nlogs
sjcheck <JOBID>
sjtail <JOBID>
```

If helpers are not installed, use the manual commands in the next section.

## Artifact And Future Operational Helpers

The commands below operate only on explicit inputs. They do not install
analysis software, discover production outputs, promote evidence state, delete
artifacts, or clear locks. For package availability and the approved roadmap,
consult `docs/design/PIPELINE_PLAN.md`.
Do not use a generic dispatcher or job array before the step-specific
validators and repeated operational need establish their contracts.

### Run The Explicit Runtime Preflight

```text
configs/runtime_preflight.example.tsv
scripts/runtime_preflight.py
tests/test_runtime_preflight.py
```

Copy the example to an explicit operator-controlled profile and replace its
illustrative targets and expectations. The exact tab-separated header is:

```text
check_id	check_type	runtime_context	required	target	probe_args	expected	description
```

Supported `check_type` contracts are:

- `tool_version`: executable target, JSON-array version arguments, and an
  expected output regular expression;
- `r_namespace`: R package target, a one-item JSON array naming the exact
  `Rscript`, and an expected package-version regular expression;
- `hash_utility`: executable target, one closed adapter
  (`python_hashlib`, `sha256sum`, or `shasum`), and `expected=sha256`;
- `path_visibility`: absolute target, one closed probe
  (`file_readable`, `directory_readable`, or `executable`), and matching
  `expected=readable` or `expected=executable`.

`runtime_context` is `local`, `cluster_batch`, or `any`; `required` is
lowercase `true` or `false`. The program does not detect SLURM or infer the
context. Declare `cluster_batch` only while actually running inside the
approved batch/compute environment.

Local dry-run:

```bash
.venv/bin/python scripts/runtime_preflight.py \
  --profile configs/runtime_preflight.example.tsv \
  --output results/qc/runtime/local.runtime_preflight.tsv \
  --runtime-context local
```

Dry-run parses the byte-stable profile and performs only context-applicable
read-only probes. It prints results but creates no output directory, lock,
temporary path, or report. Required cluster rows are `blocked` locally;
optional cluster rows are `not_checked`.

For an approved batch profile, first enter the actual allocated
batch/compute context, then run its dry-run with:

```bash
python3 scripts/runtime_preflight.py \
  --profile /explicit/path/to/csu.runtime_profile.tsv \
  --output results/qc/runtime/csu.runtime_preflight.tsv \
  --runtime-context cluster_batch
```

After inspecting the printed targets and statuses, create the explicit output
parent and publish:

```bash
mkdir -p results/qc/runtime
python3 scripts/runtime_preflight.py \
  --profile /explicit/path/to/csu.runtime_profile.tsv \
  --output results/qc/runtime/csu.runtime_preflight.tsv \
  --runtime-context cluster_batch \
  --execute
```

Execute mode requires an existing real output parent and a `.tsv` output
name. It rechecks the profile and atomically publishes one deterministic TSV
with this header:

```text
profile_sha256	runtime_context	check_id	check_type	target	required	status	observed	expected	detail
```

Statuses are `pass`, `fail`, `blocked`, or `not_checked`. A zero command exit
means the probes completed and the optional report publication succeeded; it
does not mean required rows passed. Inspect every required row explicitly.

A valid previous report with the same profile hash, context, and row count may
be replaced deterministically. Publication uses
`.<output_name>.lock`, run-token `.tmp` and `.previous` paths, validation
before replacement, and rollback. Never delete a foreign lock or hand-edit a
report to change its statuses.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_runtime_preflight.py
```

The tracked example and tests are local fixture evidence only. A future
all-pass CSU batch report establishes only the declared availability probes.
It does not execute Steps `07`-`09`, validate production inputs, or establish
runtime or cluster proof.

### Inventory Storage And Record Retention Policy

Use `configs/storage_roots.example.tsv` and
`configs/retention_policy.example.tsv` only as structural starting points.
Replace every illustrative path and pending approval through an
operator-controlled contract. The exact headers are:

```text
storage_id	path	required	purpose	quota_bytes_expected	notes
policy_id	storage_id	artifact_class	action	retention_days	approval_status	approved_by	approved_at	notes
```

Root paths must be absolute, traversal-free, and unique after resolution.
`quota_bytes_expected` is `NA` or a positive integer. Retention actions are
`retain`, `archive`, or `review_then_delete`; approval state is `approved`,
`pending`, or `rejected`. Approved rows require an approver and a canonical
non-future UTC time. The policy table records authorization state but is never
executed by this tool.

Read-only dry-run:

```bash
.venv/bin/python scripts/storage_inventory.py \
  --roots /explicit/path/to/storage_roots.tsv \
  --retention-policy /explicit/path/to/retention_policy.tsv \
  --output-root results/qc/storage
```

Dry-run parses the exact contracts and measures only the named roots. It does
not create the output root, locks, scratch paths, or stable reports. Symlinks
are counted but never followed. After inspection, create the explicit output
root and publish:

```bash
mkdir -p results/qc/storage
.venv/bin/python scripts/storage_inventory.py \
  --roots /explicit/path/to/storage_roots.tsv \
  --retention-policy /explicit/path/to/retention_policy.tsv \
  --output-root results/qc/storage \
  --execute
```

Execute mode publishes:

```text
results/qc/storage/
  storage_inventory.tsv
  retention_policy.tsv
  storage_retention_summary.tsv
```

The summary is last. It reports missing required roots, measurement errors,
approved/pending/rejected policy counts, roots without approved policy, and
overall status. A zero command exit means measurement and optional publication
completed; inspect `overall_status` and every row before relying on the
evidence. Publication requires an existing real output directory, refuses a
partial or invalid predecessor, and uses an owned lock, run-token staging and
backups, validation-before-publication, and rollback.

The tool never deletes, moves, archives, compresses, repairs, or cleans any
storage content. Production paths, quota values, and approvals remain
unresolved until an operator populates and inspects the contracts in the
appropriate CSU context.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_storage_inventory.py
```

### Reconcile Explicit Reference Provenance

Use `configs/reference_provenance.example.tsv` as the structural starting
point. Replace illustrative paths, hashes, and provenance values rather than
editing generated results. Dry-run:

```bash
.venv/bin/python scripts/reference_provenance.py \
  --inventory configs/reference_provenance.example.tsv \
  --base-dir . \
  --output-root results/qc/reference_provenance
```

The exact inventory header is:

```text
reference_id	artifact_id	role	path	required	expected_sha256	provenance_source	provenance_release	notes
```

Exactly one FASTA, FAI, DICT, GTF, BED12, STAR `chrName.txt`, and STAR
`chrLength.txt` row is required, plus at least one explicit additional STAR
index member. Relative paths resolve only against `--base-dir`; traversal,
globs, duplicate paths/IDs, symlinks, and implicit directory discovery are
rejected. `expected_sha256` is `NA` or an exact lowercase digest.

After inspecting the dry-run, create the explicit root and execute:

```bash
mkdir -p results/qc/reference_provenance
.venv/bin/python scripts/reference_provenance.py \
  --inventory /explicit/path/to/reference_provenance.tsv \
  --base-dir /explicit/reference/root \
  --output-root results/qc/reference_provenance \
  --execute
```

The tool publishes:

```text
results/qc/reference_provenance/<reference_id>/
  <reference_id>.reference_artifacts.tsv
  <reference_id>.reference_contigs.tsv
  <reference_id>.reference_summary.tsv
```

The summary is last. It records required missing files, hash mismatches,
invalid artifacts, FASTA contig count, exact ordered FAI/DICT/STAR agreement,
GTF/BED12 membership in the FASTA universe, and overall status. Execute mode
rechecks inventory and source snapshots, validates a complete predecessor,
uses an owned lock and run-token staging/backups, and rolls back replacement
failures.

The tool reads and reports only. It never creates sidecars, rebuilds STAR,
rewrites annotations, renames contigs, or establishes production/cluster
proof. Focused tests:

```bash
.venv/bin/python -m pytest -q tests/test_reference_provenance.py
```

### Validate `artifact-schema-v1`

Implemented locally at `5f4d3b4`:

```text
schemas/artifacts/v1/common.schema.json
schemas/artifacts/v1/artifact_record.schema.json
schemas/artifacts/v1/scientific_review_record.schema.json
schemas/artifacts/v1/run_summary.schema.json
schemas/artifacts/v1/report_receipt.schema.json
configs/artifact_inventory.example.tsv
scripts/validate_artifact_contracts.py
tests/fixtures/artifact_schema_v1/valid/
tests/test_artifact_schema_contracts.py
```

The shared common schema and four public record schemas use JSON Schema Draft
2020-12. The common schema retains its `v1` URN; artifact records remain
`1.0.0`; scientific-review, run-summary, and report-receipt documents are
`1.1.0`. The latter three advanced explicitly when their closed shapes gained
retained review/decision/limitation fields and report input-version
requirements. The example inventory contains 81 synthetic physical artifacts
across Steps `00a`-`09c`. It is a fixture contract, not a production
inventory. Every row names one explicit source path; multiple physical
artifacts may share one logical scope, whose rows must remain contiguous.

Validate the schemas and example inventory:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv
```

Validate each public example record:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --schema artifact-record \
  --document tests/fixtures/artifact_schema_v1/valid/artifact_record.json \
  --inventory configs/artifact_inventory.example.tsv

.venv/bin/python scripts/validate_artifact_contracts.py \
  --schema scientific-review-record \
  --document tests/fixtures/artifact_schema_v1/valid/scientific_review_record.json

.venv/bin/python scripts/validate_artifact_contracts.py \
  --schema run-summary \
  --document tests/fixtures/artifact_schema_v1/valid/run_summary.json

.venv/bin/python scripts/validate_artifact_contracts.py \
  --schema report-receipt \
  --document tests/fixtures/artifact_schema_v1/valid/report_receipt.json
```

Run the focused suite:

```bash
.venv/bin/python -m pytest -q tests/test_artifact_schema_contracts.py
```

The validator is read-only. It validates strict JSON, schema and semantic
coherence, canonical run-contract hashes, attempt/status/evidence
relationships, explicit normalized paths, and the exact seven-column
inventory contract. It never discovers pipeline outputs, expands a glob,
builds an artifact index, verifies production source files, renders a report,
or runs analysis. Combining `--inventory` with `--schema` performs record/
inventory reconciliation only for `artifact-record` and `run-summary`;
scientific-review and report-receipt records are validated without
`--inventory`.

The v1 contracts admit only `evidence_incomplete` and
`science_review_complete_exploratory`; readiness authorization remains null.
They reject `biological_interpretation_ready` until a separately approved
scientific-policy branch unlocks it. No adapter, generated
`results/artifacts/` transaction, run summary, report, production evidence,
cluster evidence, completed science review, or biological-readiness evidence
was created by this package.

### Build An `artifact-adapters-v1` Index

Implemented locally at `4dbd32d`:

```text
configs/artifact_run_contract.example.json
scripts/build_artifact_index.py
tests/fixtures/artifact_adapters_v1/build_fixture.py
tests/test_artifact_adapters.py
```

The adapter builder has 62 registered read-only adapters covering the 81
explicit Step `00a`-`09c` rows in the example inventory. It never discovers
sources by glob, invokes analysis engines, changes native outputs, or builds
the separate downstream canonical run summary.

Dry-run with explicit inputs:

```bash
.venv/bin/python scripts/build_artifact_index.py \
  --run-id RUN_ID \
  --run-contract configs/artifact_run_contract.example.json \
  --inventory configs/artifact_inventory.example.tsv \
  --output-root results/artifacts
```

Dry-run validates the run contract and inventory, inspects only the named
source paths, prints the transaction plan, and creates no stable output, lock,
or scratch path. The tracked JSON/inventory are synthetic examples; substitute
an explicitly prepared production run contract and inventory before any
production use.

Execute only after inspecting the dry-run:

```bash
.venv/bin/python scripts/build_artifact_index.py \
  --run-id RUN_ID \
  --run-contract RUN_CONTRACT_JSON \
  --inventory INVENTORY_TSV \
  --output-root results/artifacts \
  --execute
```

Successful execute mode publishes:

```text
results/artifacts/<run_id>/
  records/<artifact_id>.json
  <run_id>.artifacts.tsv
  <run_id>.artifact_receipt.tsv
```

The receipt is last. Its one row records the immutable six-field run contract,
current inventory path/hash, record/index hashes and counts, explicit
availability/completion rollups, the current `adapter_attempt_id`, its
superseded attempt, ordered attempt history, and
`transaction_state=complete`.

The six run-contract fields are:

```text
run_contract_sha256
sample_manifest_sha256
reference_contract_sha256
partition_manifest_sha256
primary_analysis_id
primary_analysis_policy_sha256
```

Changing any of the five identity components requires a new `run_id` and a
recomputed `run_contract_sha256`; attempting to bind an existing output-root
run ID to different immutable values fails. The inventory is revisionable
attempt metadata. Rebuilding the same run with a changed explicit inventory
validates the prior complete transaction and publishes a distinct superseding
adapter attempt.

Execute mode uses an owned regular lock plus run-token temporary and backup
paths, stable source snapshots, validation-before-publication, rollback, and
recovery safeguards. Do not delete a foreign lock, combine files across
attempts, or manufacture a receipt. If rollback/recovery is incomplete,
inspect every reported or remaining lock, final, temporary, backup,
quarantine, recovery-marker, and source path that is present before another
execute attempt. First-publication rollback has no prior receipt to restore,
a receipt is re-quarantined only when restored-transaction validation fails,
and the recovery marker is best-effort rather than guaranteed.

A complete receipt does not mean every expected source exists or is complete.
Missing, failed, incomplete, externally unavailable, and unknown evidence is
recorded rather than omitted. Adapter v1 populates implementation evidence but
always sets every generated record's local-testing, runtime-validation,
cluster-dry-run, and cluster-proof fields to `not_run`; it has no
native-validation import or promotion path.

Step `09c` science state is the separate supported propagation path. Both
science states require the complete 13-output summary-last scope,
plan/summary identity, all ten published evidence-category declarations, and
exact evidence-ID, payload, and count reconciliation. The
`evidence_incomplete` state may retain incomplete evidence, pending decisions
or adjudication, and no completion date. The
`science_review_complete_exploratory` state additionally requires every
required category to be complete or justified `not_applicable`, all required
decisions complete and recorded, exact equality between the selected and
adjudicated `(analysis_id, candidate_id)` identity sets, and a completion
date. Non-provisional orientation requires its complete audit and matching
completed decision. A source declaration of cluster proof additionally
requires a complete optional
`computational_validation` category, but artifact-record cluster fields still
remain `not_run`. The reserved ready state remains rejected.

Run the focused gates:

```bash
.venv/bin/python -m pytest -q tests/test_artifact_adapters.py
.venv/bin/python -m pytest -q \
  tests/test_artifact_schema_contracts.py \
  tests/test_artifact_adapters.py
```

Passing fixture tests establish only local adapter behavior. They do not
establish a production transaction, report, runtime or cluster proof,
completed production science review, or biological readiness.

### Build An `artifact-run-summary` Transaction

```text
scripts/build_run_summary.py
scripts/_run_summary_science.py
configs/report_table_approvals.example.tsv
tests/fixtures/artifact_run_summary_v1/build_fixture.py
tests/test_artifact_run_summary.py
```

The adapter output directory must already contain the exact complete
records/index/receipt transaction for `RUN_ID`. Dry-run:

```bash
.venv/bin/python scripts/build_run_summary.py \
  --run-id RUN_ID \
  --artifact-receipt \
    results/artifacts/RUN_ID/RUN_ID.artifact_receipt.tsv \
  --output-root results/artifacts
```

When a committed Step `09c` review exists, append these arguments to the
dry-run or execute command:

```bash
  --science-review-summary \
    results/scientific_validation/REVIEW_ID/REVIEW_ID.step09c_review_summary.tsv
```

The option is never discovered automatically. Omitting it is valid and keeps
science state `evidence_incomplete` with an explicit warning. Dry-run
validates the receipt, index, inventory, records, immutable run contract,
transaction-member hashes, ordering, attempt lineage, and optional Step `09c`
evidence without creating stable outputs, locks, or scratch paths. It carries
native-source hashes recorded by the adapter but does not rehash native Step
`00`-`09` sources.

To authorize exact Step `09c` TSVs for reporting, append:

```bash
  --report-table-approvals /explicit/path/to/report_table_approvals.tsv
```

This option is also never discovered. Omit it when no tables are approved. A
supplied file requires the exact committed Step `09c` summary, must contain at
least one data row, and uses this exact header:

```text
run_id	run_contract_sha256	table_id	artifact_id	role	title	path	sha256	row_count	display_row_limit	approval_status	approval_policy_version	approved_by	approved_at
```

Each row must be `approved`, bind to the current run ID and immutable
run-contract hash, and match one complete active-review Step `09c` TSV
artifact by adapter role, exact path, hash, and row count. It also records the
display-row limit (`NA` or a canonical nonnegative integer no greater than the
full row count), policy version, approver, and canonical non-future UTC
approval time. The closed roles are orientation/annotation audits, QC funnel,
replicate effects, sensitivity matrix, leave-one-pair-out, candidate
selection/adjudication, decisions, evidence index, and limitations.

Execute only after inspecting dry-run:

```bash
.venv/bin/python scripts/build_run_summary.py \
  --run-id RUN_ID \
  --artifact-receipt \
    results/artifacts/RUN_ID/RUN_ID.artifact_receipt.tsv \
  --output-root results/artifacts \
  --execute
```

Successful execute mode publishes:

```text
results/artifacts/<run_id>/
  <run_id>.run_summary.json
  <run_id>.run_summary.tsv
  <run_id>.qc_summary.tsv
  <run_id>.run_summary_receipt.tsv
```

The receipt is last. Canonical JSON is the report layer's single structured
entry point; the TSVs are deterministic artifact and QC views. Every expected
scope remains represented, including explicit missing, failed, incomplete,
and externally unavailable states. `summary_state=complete` describes the
committed four-file transaction, not evidence completeness. Omission of the
approval input produces `approved_report_tables: []`; a supplied manifest and
its authorized table snapshots are rechecked for the complete transaction.
The run-summary receipt TSV remains schema `1.0.0`; its canonical JSON
SHA-256 commits the approval-manifest descriptor and approved records.

Each execute-mode publication receives a distinct run-summary attempt ID under
the unchanged immutable run contract. Existing summary transactions must
validate before replacement. Publication uses an owned regular lock, run-token
temporary and backup paths, adapter transaction-member, optional Step `09c`,
approval manifest, and approved-table input rechecks, output-directory
identity checks, validation-before-publication, rollback, and recovery
safeguards. Never move or edit adapter transaction members, manufacture
receipts, combine attempts, delete a foreign lock, hand-edit canonical JSON,
or manually promote evidence status.

Run focused and combined checks:

```bash
.venv/bin/python -m pytest -q tests/test_artifact_run_summary.py
.venv/bin/python -m pytest -q \
  tests/test_artifact_schema_contracts.py \
  tests/test_artifact_adapters.py \
  tests/test_artifact_run_summary.py
```

Passing fixture tests establish only local summary-builder behavior. The
builder runs no analysis and establishes no runtime, cluster, scientific, or
biological validation.

### Restore Quarto And Render The Static Report Bundle

```text
scripts/restore_quarto.py
scripts/render_run_report.sh
scripts/render_run_report.py
scripts/render_run_report_bundle.py
reports/run_report.qmd
reports/run_report_pdf.qmd
reports/run_report.css
tests/test_quarto_restore.py
tests/test_report_html_v1.py
tests/test_report_exports_v1.py
tests/shell/test_render_run_report.sh
```

Restore Quarto deliberately before report testing or rendering:

```bash
make quarto-restore
```

The restore supports the official macOS Quarto `1.9.38` archive, verifies
SHA-256
`47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a`,
and publishes the checked executable at:

```text
.tools/quarto/1.9.38/bin/quarto
```

`.tools/` is ignored. Restore owns its lock/staging paths and publishes the
version directory atomically. It is the only report-layer command that may
download or install Quarto; the renderer never installs dependencies. An
already downloaded official archive can be supplied directly to
`scripts/restore_quarto.py --archive`, but it is still checksum-verified.

Install the pinned Python dependencies through the normal environment setup
before rendering. This includes the pure-Python PDF reader recorded in
`requirements.txt`; the renderer never installs it.

Default all-format dry-run:

```bash
scripts/render_run_report.sh \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto
```

Dry-run validates the canonical run-summary `1.1.0` document, Quarto, Pandoc,
Typst, PDF-reader and tracked-template identities, output state, and each
explicitly approved table's exact path, hash, row count, and display limit. It
creates no output directory, lock, scratch path, or report.

Execute only after inspecting the dry-run:

```bash
scripts/render_run_report.sh \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto \
  --execute
```

The wrapper accepts `--formats html`, `--formats pdf`, or `--formats all` and
defaults to `all`. It prefers
`.venv/bin/python`, falls back to `python3`, and treats an explicitly supplied
`PYTHON_BIN_OVERRIDE` as authoritative. Execute mode invokes only pinned
report tooling with document execution disabled and atomically publishes the
selected report formats plus the summary and receipt:

```text
results/reports/<run_id>/<run_id>.run_report.html
results/reports/<run_id>/<run_id>.run_report.pdf
results/reports/<run_id>/<run_id>.run_summary.tsv
results/reports/<run_id>/<run_id>.report_outputs.tsv
```

The HTML is self-contained and script-free. The PDF is structurally validated
and carries the exact scientific banner on every page. The summary TSV has one
stably ordered row per expected scope. The final receipt records canonical
report-receipt `1.1.0` records for every published member, including hashes,
sizes, media types, renderer identities, requested formats, and applicable
page counts. Every projection escapes input content, describes candidate rows
only as “CMH-ranked candidates,” and never promotes computational or
scientific state.

An owned regular `.<run_id>.report-bundle.lock`, run-token stage/backup paths,
stable-input and template rechecks, output validation, receipt-last
publication, rollback, signal cleanup, and retained recovery safeguards
protect replacement. A validated HTML-only predecessor can be upgraded.
Never delete a foreign lock or hand-edit a canonical run summary.

The run-summary producer populates approved records from the optional exact
manifest and emits an empty list when it is omitted.

Focused validation:

```bash
make report-test
```

Run `make quarto-restore` first. The target requires the real pinned renderer
and exercises deterministic rerendering. A passing target is local renderer
and synthetic-fixture evidence only.

### Generate The Populated Synthetic Demo Report

Restore Quarto and install the pinned report Python dependencies through the
normal explicit setup procedures before running the demo. The demo target
checks those dependencies and fails with setup guidance; it never downloads,
installs, or repairs them.

Generate the default HTML/PDF/summary/receipt bundle:

```bash
make demo-report
```

The target creates deterministic synthetic evidence content for a complete
81-artifact, 15-scope run, attaches all 11 supported approved scientific
tables, builds the canonical run summary, runs the report renderer in dry-run
mode, and only then executes it. Every invocation publishes through the normal
replacement transaction and receives new adapter, summary, and report attempt
identities.

The default bundle is:

```text
results/demo-report/reports/synthetic_full_run_demo/
├── synthetic_full_run_demo.run_report.html
├── synthetic_full_run_demo.run_report.pdf
├── synthetic_full_run_demo.run_summary.tsv
└── synthetic_full_run_demo.report_outputs.tsv
```

Intermediate synthetic inputs and canonical artifacts remain beneath
`results/demo-report/full-run-fixture/`. The complete `results/` tree is
ignored and must not be committed.

The HTML is self-contained and script-free. It opens Overview first, placing
status, CMH-ranked candidates, adjudication, and limitations near the top.
The remaining native disclosure categories group QC and orientation,
replicate/sensitivity evidence, review decisions, and provenance. The page has
a bounded reading width; wide tables scroll within keyboard-focusable regions.
The PDF remains linear and renders candidate evidence as compact readable
records.

Select a single report projection when needed:

```bash
make demo-report DEMO_REPORT_FORMATS=html
make demo-report DEMO_REPORT_FORMATS=pdf
```

Use a different ignored output root explicitly:

```bash
make demo-report DEMO_REPORT_ROOT=/explicit/ignored/demo-report
```

This is a synthetic exploratory demonstration. The banner remains
`EXPLORATORY / PROVISIONAL — NOT BIOLOGICALLY VALIDATED.` A complete
transaction, populated scientific tables, or
`science_review_complete_exploratory` fixture state does not establish
production execution, local or cluster runtime validation, completed
production scientific review, or biological readiness.

## Manual Job Checking

Recent logs:

```bash
ls -ltr logs | tail
```

SLURM accounting:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Tail logs:

```bash
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Live tail:

```bash
tail -F logs/<log-prefix>-<JOBID>.out logs/<log-prefix>-<JOBID>.err
```

Queue status:

```bash
squeue -j <JOBID>
squeue -u "$USER"
```

Watch an output directory while a job runs:

```bash
du -sh <output_dir>
ls -lh <output_dir>
```

## Concurrent Worktrees And Serialized Integration

The policy and authority model are in
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md). These commands do not authorize a
lane; use them only after an approved task plan and a canonical lane packet.
The first active-delivery use also requires the recorded post-`CONCURRENCY-01`
user strategy discussion.

### Verify The Canonical Integration Lane

Run in the primary worktree before recording or integrating lanes:

```bash
set -euo pipefail
cd /Users/elisteiger/dev/norad
test "$(pwd -P)" = '/Users/elisteiger/dev/norad'
test "$(git rev-parse --show-toplevel)" = '/Users/elisteiger/dev/norad'
norad_primary_branch=$(git branch --show-current)
test "$norad_primary_branch" = '<canonical-branch>'
norad_primary_status=$(git status --porcelain=v1)
test -z "$norad_primary_status"
git fetch origin \
  refs/heads/<canonical-branch>:refs/remotes/origin/<canonical-branch>
norad_primary_upstream_ref=$(
  git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
)
test "$norad_primary_upstream_ref" = 'origin/<canonical-branch>'
norad_primary_head=$(git rev-parse HEAD)
norad_primary_upstream=$(git rev-parse '@{upstream}')
test "$norad_primary_head" = "$norad_primary_upstream"
norad_primary_counts=$(git rev-list --left-right --count HEAD...'@{upstream}')
test "$norad_primary_counts" = $'0\t0'
git worktree list --porcelain
```

The resolved top level must be `/Users/elisteiger/dev/norad`, status must be
empty, and the ahead/behind result must be `0 0`. The fetch is integration-
owner-only network access and requires explicit authorization for the named
remote/ref; without it, equality is only against the last locally observed
remote-tracking state. Inspect any pre-existing worktree before assigning it;
do not treat a detached or preserved worktree as an available lane merely
because it is not on a branch.

### Publish A Lane Coordination Checkpoint

When another authoring or execution lane will rely on new packets, create a
fresh canonical descendant from the verified parent, update `HANDOFF.md` and
only directly required status links, then run `git diff --check` and the
complete documentation-only gate under
[Local Validation Gate](#local-validation-gate).

```bash
set -euo pipefail
cd /Users/elisteiger/dev/norad
norad_coordination_status=$(git status --porcelain=v1)
test -z "$norad_coordination_status"
git fetch origin \
  refs/heads/<latest-canonical-parent-branch>:refs/remotes/origin/<latest-canonical-parent-branch>
norad_coordination_parent=$(git rev-parse <verified-parent-sha>)
norad_coordination_remote_parent=$(
  git rev-parse origin/<latest-canonical-parent-branch>
)
test "$norad_coordination_parent" = "$norad_coordination_remote_parent"
norad_coordination_local_branch=$(
  git branch --list 'codex/<coordination-branch>'
)
test -z "$norad_coordination_local_branch"
norad_coordination_branch_status=0
git ls-remote --exit-code --heads \
  origin refs/heads/codex/<coordination-branch> || \
  norad_coordination_branch_status=$?
test "$norad_coordination_branch_status" -eq 2
git switch -c codex/<coordination-branch> <verified-parent-sha>

# Edit HANDOFF.md and only the exact status links required by the packets.
git diff --check
# Run the complete documentation-only gate below before staging.
git add docs/operations/HANDOFF.md <exact-status-link-paths>
git diff --cached --check
git commit -m 'docs: coordinate concurrent lanes'
norad_coordination_status=$(git status --porcelain=v1)
test -z "$norad_coordination_status"
git push -u origin codex/<coordination-branch>
norad_coordination_counts=$(
  git rev-list --left-right --count HEAD...'@{upstream}'
)
test "$norad_coordination_counts" = $'0\t0'
```

Fetch and push require explicit authorization for the exact remote and payload.
The final count must be `0 0`. This special documentation-only coordination
commit records active planning state; it does not complete a task or replace
the later implementation/test and docpatch commits. Provision relying lanes
only after the checkpoint is clean, pushed, and upstream-equal.

### Create And Verify A Candidate Lane

The default sibling root is `/Users/elisteiger/dev/norad-worktrees`. Replace
every placeholder with the exact values already recorded in `HANDOFF.md`. Do
not use `-f`, `-B`, an existing path, or an existing branch.

```bash
set -euo pipefail
mkdir -p /Users/elisteiger/dev/norad-worktrees
git check-ref-format --branch codex/<lane-id>
git cat-file -e '<exact-base-sha>^{commit}'
test ! -e /Users/elisteiger/dev/norad-worktrees/<lane-id>
norad_candidate_local_branch=$(git branch --list 'codex/<lane-id>')
test -z "$norad_candidate_local_branch"
git worktree add --lock \
  --reason 'NORAD concurrent lane <lane-id>' \
  -b codex/<lane-id> \
  /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  <exact-base-sha>
```

The assigned agent's first inspection uses the exact absolute path:

```bash
set -euo pipefail
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  rev-parse --show-toplevel)" = \
  '/Users/elisteiger/dev/norad-worktrees/<lane-id>'
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  branch --show-current)" = 'codex/<lane-id>'
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  rev-parse HEAD)" = '<exact-base-sha>'
norad_lane_status=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
    status --porcelain=v1
)
test -z "$norad_lane_status"
```

Top level, branch, and `HEAD` must exactly match the packet and status must be
empty. A lane does not switch branches, pull, merge, rebase, stash, clean,
reset, remove worktrees, or edit outside its reserved write set.

For an immutable-execution lane, first use an explicitly authorized fetch to
prove the recorded remote ref contains the execution commit. Then create a
locked detached worktree instead of a candidate branch:

```bash
set -euo pipefail
git fetch origin \
  refs/heads/<recorded-execution-remote-branch>:refs/remotes/origin/<recorded-execution-remote-branch>
git merge-base --is-ancestor \
  <exact-pushed-execution-sha> \
  origin/<recorded-execution-remote-branch>
test ! -e /Users/elisteiger/dev/norad-worktrees/<execution-lane-id>
git worktree add --lock \
  --reason 'NORAD immutable execution <execution-lane-id>' \
  --detach \
  /Users/elisteiger/dev/norad-worktrees/<execution-lane-id> \
  <exact-pushed-execution-sha>
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<execution-lane-id> \
  rev-parse HEAD)" = '<exact-pushed-execution-sha>'
norad_execution_status=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<execution-lane-id> \
    status --porcelain=v1
)
test -z "$norad_execution_status"
git -C /Users/elisteiger/dev/norad-worktrees/<execution-lane-id> \
  status --short --branch
```

The status header must report detached `HEAD`. Record the exact command or job,
request/input hashes, configuration/profile, output root, log path, start time,
and scheduler ID before execution. Do not switch, pull, commit, or reset that
worktree while its run is active.

### Inspect A Candidate Handoff

The lane hands off an immutable candidate SHA and a clean worktree. The
integration owner verifies it from the primary worktree:

```bash
set -euo pipefail
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  branch --show-current)" = 'codex/<lane-id>'
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  rev-parse HEAD)" = '<candidate-sha>'
norad_handoff_status=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
    status --porcelain=v1
)
test -z "$norad_handoff_status"
git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  merge-base --is-ancestor <recorded-base-sha> <candidate-sha>
test "$(git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  rev-list --count <recorded-base-sha>..<candidate-sha>)" -eq \
  <expected-commit-count>
git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  log --reverse --format='%H %s' <recorded-base-sha>..<candidate-sha>
git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  diff --check <recorded-base-sha> <candidate-sha>
git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
  diff --name-status <recorded-base-sha> <candidate-sha>
norad_handoff_untracked=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
    ls-files --others --exclude-standard
)
test -z "$norad_handoff_untracked"
```

Status and untracked output must be empty; the candidate must descend from the
recorded base; and every changed path and commit must match the packet. Use an
expected count of `1` for a documentation sidecar. Use `1` for an
implementation/test-only candidate or `2` when its exact second commit is the
separate coupled documentation draft. Inspect the ordered hashes and integrate
each recorded role explicitly; never cherry-pick only the tip of an unreviewed
range. Any movement after handoff invalidates the packet and freezes no write
authority.

### Manual Integration Fragment Exchange

The fragment schema is in [`docs/fragments/README.md`](../fragments/README.md),
and authority, validity, staleness, dispositions, and recovery are in
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md#integration-fragment-authority-and-lifecycle).
The standalone entry points and their complete interfaces are indexed in
[Git orchestration helpers](../../scripts/git_orchestration/README.md). They
mechanize checks and bounded Git operations; they do not select work, authorize
targets or publication, choose dispositions, compose canonical prose, or clean
recovery state.

These commands supplement the ordinary candidate workflow for exactly one
non-merge documentation-sidecar commit containing reserved deliverables plus
one fragment. An implementation candidate still uses the ordered
implementation/docpatch path below. Replace every placeholder from the
published packet and immutable handoff. The Python validators are read-only.
The shell entry points are dry-run by default: without `--execute` they
validate preconditions and print the proposed mutation without changing Git or
remote state. Inspect that result before repeating the identical invocation
with `--execute` under explicit authorization. Run any entry point with
`--help` for its complete interface.

First use
[`validate_fragment_candidate.py`](../../scripts/git_orchestration/validate_fragment_candidate.py)
to bind the candidate worktree, branch, one-commit ancestry, exact frozen diff,
all packet reservations, fragment shape, cleanliness, and immutable remote
source ref:

```bash
python3 scripts/git_orchestration/validate_fragment_candidate.py \
  --repo /absolute/candidate-worktree --branch codex/<candidate-branch> \
  --base <full-base-sha> --candidate <full-candidate-sha> \
  --fragment docs/fragments/<FRAGMENT-ID>.md \
  --expected-change A <reserved-deliverable-1> \
  --expected-change A docs/fragments/<FRAGMENT-ID>.md \
  --allowed-path <reserved-deliverable-1> \
  --allowed-path <unused-but-reserved-deliverable-2> \
  --allowed-path docs/fragments/<FRAGMENT-ID>.md
```

Repeat `--expected-change STATUS PATH` for every literal row in the frozen
handoff and `--allowed-path PATH` for every packet reservation, including
unused paths. Canonical target declarations are not candidate reservations.
A candidate without a fragment uses the ordinary handoff path. Any validation
failure invalidates the entire handoff: do not apply it or assign request
dispositions. Keep the old source immutable and obtain a replacement packet,
worktree, branch, frozen SHA, and handoff.

For each request, run
[`validate_fragment_target.py`](../../scripts/git_orchestration/validate_fragment_target.py)
against the latest clean, remotely equal canonical parent:

```bash
python3 scripts/git_orchestration/validate_fragment_target.py \
  --repo /absolute/canonical-worktree --branch codex/<canonical-branch> \
  --base <full-candidate-base-sha> --parent <full-canonical-parent-sha> \
  --owner <repository-relative-owner.md> \
  --mode 'existing anchor' --heading '## Literal heading' \
  --anchor <declared-github-anchor>
```

Use the request's declared mode: `existing anchor`,
`authorized-new anchor`, or `authorized-new owner`. Independently inspect
the printed target diff, current authorization, provenance, coupling, and
assumptions. Normal descendant advancement or an unrelated target edit is not
automatically stale; material drift is request-local, and unaffected separable
requests may continue.

Only the integration owner assigns terminal outcomes. Before finalization,
account for every request and every partial residual as required by
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md#terminal-disposition-records).
A `defer` must name an implemented, authorized destination, and package
`no-op` is not a request disposition. Prepare a regular, non-symlink commit-
message file outside the tracked write set. Keep its required `Fragment-*`
trailers contiguous at the end, with one disposition trailer per request and
the required accepted/residual subset trailers for every `partial`.

When the valid candidate must enter the canonical tree, first run
[`apply_fragment_candidate.sh`](../../scripts/git_orchestration/apply_fragment_candidate.sh)
without `--execute`, inspect its proposed cherry-pick, and then repeat it with
`--execute`:

```bash
scripts/git_orchestration/apply_fragment_candidate.sh \
  --candidate-repo /absolute/candidate-worktree \
  --candidate-branch codex/<candidate-branch> \
  --candidate <full-candidate-sha> --base <full-candidate-base-sha> \
  --fragment docs/fragments/<FRAGMENT-ID>.md \
  --expected-change A <reserved-deliverable-1> \
  --expected-change A docs/fragments/<FRAGMENT-ID>.md \
  --allowed-path <reserved-deliverable-1> \
  --allowed-path docs/fragments/<FRAGMENT-ID>.md \
  --canonical-repo /absolute/canonical-worktree \
  --canonical-branch codex/<canonical-branch> --parent <full-parent-sha>
```

Repeat both list options as above. The helper revalidates the frozen candidate
and both lane identities immediately before application. It aborts only a
normal cherry-pick conflict and proves restoration of the exact clean parent;
any other failure leaves recovery state for inspection.

After the integration owner routes accepted content into its canonical owners,
use
[`finalize_fragment_integration.sh`](../../scripts/git_orchestration/finalize_fragment_integration.sh)
to stage only the declared final paths, remove the fragment, and amend the
application commit from the reviewed message file. That file must declare
`Fragment-Package-Outcome: applied`:

```bash
scripts/git_orchestration/finalize_fragment_integration.sh \
  --repo /absolute/canonical-worktree --branch codex/<canonical-branch> \
  --parent <full-parent-sha> --applied <full-applied-sha> \
  --fragment docs/fragments/<FRAGMENT-ID>.md \
  --final-path <exact-final-path-1> --final-path <exact-final-path-2> \
  --message-file /absolute/path/<integration-id>.message \
  --integration-id <integration-id> \
  --source-repo /absolute/candidate-worktree \
  --source-sha <full-candidate-sha> \
  --source-ref refs/heads/codex/<candidate-branch> \
  --base <full-candidate-base-sha> --request-id <REQUEST-ID>
```

Repeat `--final-path` for the exact parent-to-result path set and
`--request-id` for every fragment request. Run dry-run first, then repeat with
`--execute`. The final tree must contain no candidate fragment; deletion
alone never substitutes for terminal disposition records.

If no accepted deliverable or routed canonical update changes the tree, do not
cherry-pick. Use
[`record_fragment_noop.sh`](../../scripts/git_orchestration/record_fragment_noop.sh)
to create the required empty integration commit from the exact parent:

```bash
scripts/git_orchestration/record_fragment_noop.sh \
  --candidate-repo /absolute/candidate-worktree \
  --candidate-branch codex/<candidate-branch> \
  --candidate <full-candidate-sha> --base <full-candidate-base-sha> \
  --fragment docs/fragments/<FRAGMENT-ID>.md \
  --expected-change A <reserved-deliverable-1> \
  --expected-change A docs/fragments/<FRAGMENT-ID>.md \
  --allowed-path <reserved-deliverable-1> \
  --allowed-path docs/fragments/<FRAGMENT-ID>.md \
  --canonical-repo /absolute/canonical-worktree \
  --canonical-branch codex/<canonical-branch> --parent <full-parent-sha> \
  --message-file /absolute/path/<integration-id>.message \
  --integration-id <integration-id> --request-id <REQUEST-ID>
```

Repeat the expected-change, allowed-path, and request-ID options for the frozen
handoff. Run dry-run first, then repeat with `--execute`. The message file
must declare `Fragment-Package-Outcome: no-op` and the same source, parent,
base, integration, and per-request provenance required for an applied package.

After either path, run the complete documentation gate and independent review
against the exact final commit. If either changes the commit, amend and repeat
both against the new tip. Then publish with
[`publish_exact_ref.sh`](../../scripts/git_orchestration/publish_exact_ref.sh)
using the invocation under
[Publish And Preserve Candidate State](#publish-and-preserve-candidate-state).
That helper rechecks the immutable source ref immediately before and after
canonical publication; source durability is part of closure.

If failure occurs after a successful cherry-pick, do not reset, clean, stash,
amend, delete, or overwrite recovery state. Record the pre-application parent,
branch, current `HEAD`, status, staged and unstaged diffs, and untracked paths;
preserve or lock the worktree; and restart only on a newly authorized branch
and worktree from that parent. The frozen remote source never moves.

### Integrate One Candidate At A Time

First repeat the canonical-lane verification and inspect the candidate diff.
Reclassify coupling against the latest canonical state. Do not integrate if a
write set now overlaps, an assumption changed, or the primary worktree is
dirty.

Every landing starts on a fresh, unpublished canonical descendant; never
cherry-pick onto the already-published parent branch. Fetch and later push only
with explicit authorization for the named remote and payload.

```bash
set -euo pipefail
cd /Users/elisteiger/dev/norad
norad_integration_status=$(git status --porcelain=v1)
test -z "$norad_integration_status"
git fetch origin \
  refs/heads/<latest-canonical-parent-branch>:refs/remotes/origin/<latest-canonical-parent-branch>
norad_integration_parent=$(git rev-parse <verified-parent-sha>)
norad_integration_remote_parent=$(
  git rev-parse origin/<latest-canonical-parent-branch>
)
test "$norad_integration_parent" = "$norad_integration_remote_parent"
norad_integration_local_branch=$(
  git branch --list 'codex/<integration-package-branch>'
)
test -z "$norad_integration_local_branch"
norad_integration_branch_status=0
git ls-remote --exit-code --heads \
  origin refs/heads/codex/<integration-package-branch> || \
  norad_integration_branch_status=$?
test "$norad_integration_branch_status" -eq 2
git switch -c codex/<integration-package-branch> <verified-parent-sha>
```

Apply one frozen, single-commit documentation candidate with source-SHA
provenance. A pending-link card sidecar and a coupled draft use the same local
path: nothing is published until the integration owner adds central links and
state, amends the still-unpushed commit into the one canonical documentation
package, and runs the complete documentation gate on that exact commit.

```bash
set -euo pipefail
git cherry-pick -x <documentation-candidate-sha>

# Add the exact integration-owner links/state required by this package.
git add <exact-integration-owner-paths>
git diff --check
git diff --cached --check
git commit --amend --no-edit
# Run the complete documentation-only gate below against the amended HEAD.
```

A self-contained independent sidecar must already contain a legitimate
reserved inbound reference and pass its candidate gate. A pending-link card is
only handoff-ready; the integration owner adds the link before the amend and
final gate. The `-x` provenance line survives the amend.

If the normal cherry-pick conflicts, preserve the candidate and inspect before
aborting. This recovery applies to normal cherry-pick only; this workflow does
not use `--no-commit` because Git 2.54 does not retain an abortable operation
for that mode.

```bash
git status --porcelain=v2
git diff --name-only --diff-filter=U
git diff --cc
git cherry-pick --abort
git status --porcelain=v1
```

Do not resolve a canonical-owner conflict opportunistically. Repair the lane
packet or return the governing task to planning.

An implementation candidate hands off exactly one tested implementation/test
commit and, optionally, one subsequent coupled documentation-draft commit.
Apply the implementation commit first:

```bash
git cherry-pick -x <implementation-and-test-commit-sha>
```

If independent documentation landed after its base, first enumerate every
intervening path:

```bash
git diff --name-status \
  <implementation-base-sha> \
  <latest-canonical-parent-sha>
```

Approve only exact, narrow, non-consuming documentation paths. Then compare
the tested candidate and integrated implementation across the whole repository
while excluding only that reviewed list—one exact pathspec per intervening
path:

```bash
git diff --exit-code \
  <implementation-and-test-commit-sha> \
  <integrated-implementation-sha> \
  -- . \
  ':(exclude,top)<approved-non-consuming-doc-path-1>' \
  ':(exclude,top)<approved-non-consuming-doc-path-2>'
```

Do not exclude a directory or wildcard. Computational evidence is reusable
only when the comparison is empty, the exclusion list exactly equals the
enumerated intervening paths, and each path is proven non-consuming
documentation. Any extra difference, conflict, or change to executable
configuration, dependencies, Make targets, schemas, fixtures, report
templates, or test behavior requires the applicable gate on the integrated
state.

After the implementation gate or valid reuse proof, apply the exact optional
documentation-draft commit normally, add integration-owner state, run the
combined documentation gate, and amend that still-local commit as the separate
canonical docpatch:

```bash
set -euo pipefail
git cherry-pick -x <coupled-documentation-draft-sha>
git add <exact-integration-owner-documentation-paths>
git diff --check
git diff --cached --check
git commit --amend --no-edit
# Run the complete documentation-only gate below against the amended HEAD.
```

If no draft commit exists, the integration owner authors and commits the
separate docpatch normally. Always run the documentation gate on the final
combined tree.

### Publish And Preserve Candidate State

Only the integration owner publishes the accepted canonical branch, with
explicit authorization for the exact remote and payload. Use
[`publish_exact_ref.sh`](../../scripts/git_orchestration/publish_exact_ref.sh)
to bind the clean branch, single parent, reviewed final SHA, expected current
remote state, and frozen source ref before an exact-SHA canonical push guarded
by an exact expected-remote lease:

```bash
scripts/git_orchestration/publish_exact_ref.sh \
  --repo /absolute/canonical-worktree \
  --branch codex/<canonical-integration-branch> \
  --parent <full-final-commit-parent-sha> --final <full-reviewed-final-sha> \
  --expected-remote <full-current-remote-sha-or-ABSENT> \
  --source-repo /absolute/candidate-worktree \
  --source-ref refs/heads/codex/<candidate-branch> \
  --source-sha <full-frozen-candidate-sha> \
  --fragment docs/fragments/<FRAGMENT-ID>.md \
  --integration-id <integration-id> --base <full-candidate-base-sha> \
  --outcome <applied-or-no-op> --request-id <REQUEST-ID>
```

Without `--execute`, the helper validates all preconditions and prints the
push without changing remote state. Inspect that dry-run, then repeat the
identical invocation with `--execute` under explicit publication authority.
Repeat `--request-id` for every fragment request. For `applied`, also repeat
`--final-path` for the exact parent-to-final path set; `no-op` accepts none.
The helper binds those IDs,
the integration ID, source, base, parent, and package outcome to parseable
trailers on the reviewed final commit. The remote canonical ref must still be
absent or equal its recorded SHA, and the frozen source ref must still equal
its recorded SHA. A successful execute must prove local, upstream, and remote
equality, zero ahead/behind, a clean worktree, and unchanged source
reachability before any lane or card closes. Preserve the immutable candidate
source ref by default. Git does not include an already-equal source ref in the
canonical push transaction, so a concurrent violation can be detected only by
the immediate post-push check. In that case the helper fails after canonical
publication: preserve both worktrees and refs, record the observed remote
state, and treat the package as a publication-recovery incident until an
operator restores durable source reachability and reruns the closure checks.

Candidate worktrees and branches remain locked by default. Optional worktree
retirement requires explicit operator authorization after accepted publication
and inspection proves the candidate has no dirty or unique work:

```bash
set -euo pipefail
norad_retirement_status=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
    status --porcelain=v1
)
test -z "$norad_retirement_status"
norad_retirement_untracked=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
    ls-files --others --exclude-standard
)
test -z "$norad_retirement_untracked"
norad_retirement_ignored=$(
  git -C /Users/elisteiger/dev/norad-worktrees/<lane-id> \
    ls-files --others --ignored --exclude-standard
)
test -z "$norad_retirement_ignored"
git worktree list --porcelain
git worktree unlock /Users/elisteiger/dev/norad-worktrees/<lane-id>
git worktree remove /Users/elisteiger/dev/norad-worktrees/<lane-id>
git show-ref --verify refs/heads/codex/<lane-id>
git worktree prune --dry-run --verbose
```

Never use `worktree remove --force`. The final `show-ref` proves the candidate
branch remains preserved; branch deletion is a separate explicit operator
decision.

## Local Validation Gate

Use focused tests while executable work is changing. Pytest's default capture
already withholds test stdout/stderr unless a test fails; add quiet progress
and short tracebacks:

```bash
cd /Users/elisteiger/dev/norad
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
```

Run the complete Phase `01b` publication-fault characterization set with:

```bash
cd /Users/elisteiger/dev/norad
.venv/bin/python -m pytest -q --tb=short \
  tests/libraries/test_validation_report.py \
  tests/test_reference_provenance.py \
  tests/test_runtime_preflight.py \
  tests/test_storage_inventory.py
```

Assertions whose names or comments say `characterizes` or `known gap` record
current unsafe failure states for later reviewed correction. A passing result
does not authorize deleting a lock, backup, stage, or foreign final and does
not establish that recovery is safe.

Run one complete computational gate against the final executable state before
the implementation/test commit. The coverage target already runs the complete
Python suite, so do not precede it with a duplicate uninstrumented full pytest
run.

The canonical gate runs static preflight first and then these de-duplicated
lanes:

- complete Python coverage and baseline comparison;
- shell contracts without the Python modules already covered above;
- repository-local R environment validation followed by guarded Step `08` and
  Step `09` real-R tests, sequentially within one lane;
- only the pinned real-Quarto/Typst report-runtime tests.

Run the default quiet gate with three top-level lane slots and two Python
workers:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks
```

The gate prints elapsed `PASS` lines and a final timing summary. Successful
temporary logs are deleted. If one polling batch observes one or more nonzero
lanes, each failed lane in that completed batch receives a retained log and,
in quiet mode, has its complete log replayed to stderr. The gate returns the
first such lane's status, then cancels and reaps still-running lane process
groups and removes their temporary logs. `SIGINT` returns `130`, terminates
descendants, and retains every running lane's log with its path printed to
stderr; interrupted logs are not replayed automatically.

Those retention rules apply to default or serial quiet mode. `--verbose`
streams each child's merged stdout/stderr live and creates no per-lane
temporary log to retain on failure or interruption.

Use the deterministic serial fallback to diagnose concurrency-specific
behavior:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript \
    make -s all-checks VALIDATION_ARGS=--serial
```

Stream complete lane output for an explicitly verbose run:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript \
    make -s all-checks VALIDATION_ARGS=--verbose
```

Record the machine-readable timing, result, and coverage summary at an
explicit ignored or temporary path when characterizing the gate:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript \
    make -s all-checks \
    VALIDATION_ARGS="--result-json /private/tmp/norad-validation.json"
```

`VALIDATION_JOBS` and `VALIDATION_PYTHON_WORKERS` may override the measured
defaults for an explicit characterization run. Each value must be between one
and four. Use `--serial` for the supported fallback rather than maintaining a
second command sequence. Do not discard a retained failed or interrupted log
until the applicable failure or interruption is understood.

The guarded-R lane uses `make local-real-r-test`, which opts into the
repository-local R library through the guarded environment below after
`make r-check` succeeds. Bare
`make real-r-test` is an ambient-runtime diagnostic: when `Rscript` is absent,
each runner reports `SKIP`, and when ambient Step `08` packages are absent it
fails. Neither a skip nor an ambient failure replaces the guarded semantic
gate. An explicit bad override fails; Step `09` itself uses base R only.

Select affected documentation and validation applicability through
[`TASK_DELIVERY.md`](TASK_DELIVERY.md#package-delivery) and the
[`TASK_START.md` impact route](TASK_START.md#documentation-impact-and-validation).
For a qualifying documentation-only patch or standalone package, run:

```bash
cd /Users/elisteiger/dev/norad
git diff --check
./scripts/git_orchestration/validate_documentation.py --repo "$PWD"
git status --short
git diff --name-status
```

The checker validates local paths and GitHub-style heading anchors, includes
untracked new documents, enforces task-card IDs/locations/headings/direct
dependencies, rejects hard-dependency cycles and orphan cards/diagrams, and
checks basic Mermaid source structure. It reads the repository globally but
normally emits one compact result, so it does not require loading the corpus
into agent context. It does not replace targeted semantic comparison of each
changed or otherwise affected diagram with its owning architecture document.

Classify the complete predecessor-to-final diff, including staged, unstaged,
and untracked paths before commit and exact commits afterward. Computational
Python, shell, R, and report-runtime suites are not applicable only when the
[`TASK_DELIVERY.md` documentation-only boundary](TASK_DELIVERY.md#package-delivery)
is satisfied. Before handoff or the next descendant, verify takeover state:

```bash
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
git rev-list --left-right --count HEAD...'@{upstream}'
git log --oneline --decorate -5
```

The status output must be empty and the left/right counts must be `0 0`.
`HANDOFF.md`, `PIPELINE_PLAN.md`, and `TODO.md` must agree on the active
package, evidence boundary, and exact next descendant.

### Python coverage baseline

Synchronizing the pinned Python dependencies is an explicit developer setup
action:

```bash
cd /Users/elisteiger/dev/norad
.venv/bin/python -m pip install -r requirements.txt
```

Tests, workflow scripts, validators, jobs, and report renderers do not run that
installation command. The measured parallel gate requires the exact
developer-only `pytest-xdist` and `execnet` versions in `requirements.txt`.
The serial fallback does not require xdist. Never install either package
globally or automatically from an ordinary test or validation target.

Measure the complete Python suite, trace configured Python subprocesses, and
compare the result with the reviewed baseline:

```bash
make python-coverage-check
```

Measurement writes only beneath the ignored `.coverage-work/` directory. The
machine-readable snapshot and policy are in
`tests/baselines/python_coverage.json`; the interpretation and public-contract
matrix are in `docs/design/TEST_BASELINE.md`.

Do not update the baseline merely to silence a regression. After inspecting
and approving a deliberate test/source change, regenerate the candidate,
review the exact JSON diff, and rerun the check:

```bash
make python-coverage-baseline-update
git diff -- tests/baselines/python_coverage.json
make python-coverage-check
```

The numerical baseline does not replace shell, guarded real-R, report-runtime,
transaction, recovery, or independent-oracle tests.

### Guarded local R environment

Local R setup is an explicit developer action:

```bash
cd /Users/elisteiger/dev/norad
RSCRIPT_BIN=/usr/local/bin/Rscript make r-restore
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
```

These targets activate the project library with `NORAD_USE_RENV=1`. The
tracked lock describes R `4.6.1`, Bioconductor `3.23`, the eight direct Step
`08` namespaces, and their transitive dependencies. The restore target uses
the configured release repositories and performs installation only when the
operator invokes it. Existing analysis scripts, compute wrappers, and the
report renderer never install R packages.

The guarded startup contract disables automatic snapshots and the `renv`
sandbox. The latter avoids a reproduced high-CPU directory-creation loop on
this macOS/R combination. Do not remove the guard or enable implicit package
mutation without a separately reviewed change.

The guarded environment gate requires:

```text
R 4.6.1 runtime and all required namespaces load
BiocManager::valid() passes against reachable current release metadata
renv::status() reports synchronization
headless PDF creation passes
Step 08 and Step 09 real-R suites pass without SKIP
```

The current result belongs in `HANDOFF.md`, not this command owner. Passing
these checks validates the guarded local environment and semantic fixtures.
It does not validate production data, establish CSU batch visibility, or make
Steps `08` or `09` cluster-proven.

## Cluster Execution Pattern

On local:

```bash
cd /Users/elisteiger/dev/norad
git status --short
git add <changed-files>
git commit -m "<stage implementation message>"
# after impact-directed documentation review and the repository-wide impact check:
git add <documentation-files>
git commit -m "step NN docpatch"
git diff --check
git status --short
git log --oneline -3
git push
```

Remote promotion is currently paused. After the complete local refactor
program reaches clean, pushed, upstream-equal `refactor-99-final-audit` and
remote work is explicitly resumed by new user direction, open a cluster
shell:

```bash
ssh csu-hpc
```

Then run the fail-closed checkout gate in that cluster shell:

```bash
set -euo pipefail

cd ~/norad
git fetch origin
validation_branch=validate-step-07
git switch "$validation_branch" ||
  git switch --track -c "$validation_branch" "origin/$validation_branch"
git pull --ff-only origin "$validation_branch"
test "$(git branch --show-current)" = "$validation_branch"
git rev-parse HEAD
test -z "$(git status --porcelain)"
mkdir -p logs
```

Set `validation_branch` to the exact active gate:

```text
validate-step-07
validate-step-08
validate-step-09
validate-step-09c-scientific-evidence
post09-targeted-reruns
```

Do not use an unqualified `git pull` and assume the checkout changed branches.
Record the branch and commit with the validation evidence before submitting.

Create and push each local descendant only after its predecessor is clean and
pushed:

```bash
set -euo pipefail

predecessor=refactor-99-final-audit
next_branch=validate-step-07

git switch "$predecessor"
git pull --ff-only origin "$predecessor"
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$predecessor")"
git log --oneline -3
git switch -c "$next_branch"
git push -u origin "$next_branch"
```

For later gates, use `validate-step-07` -> `validate-step-08` ->
`validate-step-09` -> `validate-step-09c-scientific-evidence` ->
`post09-targeted-reruns`. Never create the descendant before the predecessor's
inspected evidence/report docpatch, clean-history check, and push.

Dry-run:

```bash
sbatch jobs/<step>.slurm
```

Check dry-run:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Check execute job:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

Inspect outputs before declaring the step proven.

## Workflow contract and validation convention

The runbook retains exact setup, dry-run, execute, inspection, recovery, and
focused-validation commands. Functional responsibility, inputs, outputs,
consumers, exact validator checks, known asymmetries, and scientific limits
belong to the colocated contracts:

| Historical alias | Runbook commands | Functional contract |
| --- | --- | --- |
| `00a` | [STAR index](#step-00a-star-index) | [`construct_STAR_index`](../../src/norad/stages/construct_STAR_index/CONTRACT.md) |
| `00b` | [GTF to BED12](#step-00b-gtf-to-bed12) | [`convert_GTF_to_BED12`](../../src/norad/stages/convert_GTF_to_BED12/CONTRACT.md) |
| `00c` | [FASTA sidecars](#step-00c-gatk-reference-sidecars) | [`construct_FASTA_sidecars`](../../src/norad/stages/construct_FASTA_sidecars/CONTRACT.md) |
| `01` | [STAR alignment](#step-01-star-alignment) | [`align_RNA_reads_with_STAR`](../../src/norad/stages/align_RNA_reads_with_STAR/CONTRACT.md) |
| `02` | [canonical BAM](#step-02-canonical-sort-read-group-tagging-and-bam-indexing) | [`construct_canonical_BAM`](../../src/norad/stages/construct_canonical_BAM/CONTRACT.md) |
| `02b` | [BAM QC](#step-02b-bam-qc) | [`collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/CONTRACT.md) |
| `03` | [RSeQC orientation](#step-03-rseqc-strandedness--orientation-inference) | [`collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/CONTRACT.md) |
| `04` | [duplicate marking](#step-04-markduplicates) | [`mark_BAM_duplicates_with_Picard`](../../src/norad/stages/mark_BAM_duplicates_with_Picard/CONTRACT.md) |
| `05` | [split N cigar reads](#step-05-splitncigarreads) | [`split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_N_cigar_reads_with_GATK/CONTRACT.md) |
| `06` | [mechanical orientation](#step-06-split-bam-by-read-orientation) | [`partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/CONTRACT.md) |
| `07` | [cohort mpileup](#step-07-bcftools-mpileup) | [`generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md) |
| `08` | [candidate preprocessing](#step-08-vcf-preprocessing) | [`preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md) |
| `09` | [paired CMH ranking](#step-09-cmh-editing-site-calling) | [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md) |
| `09c` | [scientific review evidence](#post-step-09-scientific-validation-gate) | [`assemble_scientific_review_evidence_package`](../../src/norad/evidence/assemble_scientific_review_evidence_package/CONTRACT.md) |

Structured stage validators use explicit inputs and are dry-run by default.
Their runbook invocations show how to publish the explicit validation TSV with
`--execute`; a failed check remains report evidence and is distinct from
unsafe input, tool, CLI, or publication failure. Validators do not repair
native outputs, rerun their functional owner, promote evidence state, or alter
historical runtime status. Use each linked contract for its exact checks and
limits. Current evidence level and proven scope remain canonical in
[`HANDOFF.md`](HANDOFF.md#evidence-boundary).

For validators using the shared step-report publisher, execute mode requires
an existing real output parent, validates any predecessor, uses an owned lock
and run-token staging/backup paths, rechecks stable inputs, and attempts to
restore the predecessor on replacement failure. Publisher exception boundaries
are not uniform; use the transaction-specific entries in
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md#validation-publication-leaves-ambiguous-recovery-state)
when a lock, temporary, previous, final, or recovery state is ambiguous.

### Inline block disposition

Substantive inline shell remains only when it is an exact operator sequence or
has no tested executable owner. This classification prevents documentation
compression from becoming an untested code extraction:

| Disposition | Inline blocks | Boundary |
| --- | --- | --- |
| Tested executable owner exists; retain only operator ordering and invocation | Documentation/fragment validation, candidate application, finalization, no-op recording, and exact-ref publication | Interfaces live in [`scripts/git_orchestration/`](../../scripts/git_orchestration/README.md); authority, human review, conflict disposition, and recovery remain here and in `CONCURRENT_WORK.md`. |
| Retain as runbook-owned operator procedure | Demo presence loop; canonical/candidate/immutable-lane checks; coordination checkpoint; ordinary integration and retirement; cluster checkout/promotion; Step `07` and Step `09` scheduler/output inspection; Step `09c` reviewer workflow and rerun matrix | These blocks combine explicit human inspection, action-point safety, evidence interpretation, or recovery meaning not implemented by one helper. |
| Retain pending a separately tested extraction | Step `07` manifest-pair reconciliation, selector/FAI reconciliation, and manifest-named receipt/VCF census | Current validators cover related per-partition checks but not these exact whole-universe procedures. |
| Removed as validator-owned duplication | Step `08` manual partition/orientation ordering scan | [`validate_step_08_preprocessing_outputs.py`](../../scripts/validate_step_08_preprocessing_outputs.py) checks the complete ordered partition-by-orientation receipt; the explicit `25 × 2` acceptance remains below. |

## Reference Prep

Novogene reference source files:

```text
genome.fa.gz
genome.gtf.gz
genome_gene.fa.gz
```

Prepared reference paths:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

Reference notes:

```text
Genome: GRCh38-like
Chromosome naming: numeric-style, e.g. 1, 2, 3
Not chr1, chr2, chr3
```

FASTA and GTF chromosome naming match.

### Step 00a: STAR Index

Submit the mode-`0644` scheduler entry point from the repository root:

```bash
sbatch src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm
```

Submission executes the job implicitly; there is no dry-run or direct-execute
mode. Its hardcoded Novogene input and `refs/` output paths resolve from the
caller's working directory.

Output:

```bash
refs/novogene_star_index/
```

STAR index was built with:

```text
sjdbOverhang=149
```

because reads are 150 bp.

The structured Step `00a` validator is separate from the historical proof. It
reads one explicit STAR index, FASTA, GTF, path-resolution base, expected
overhang, and scope ID:

```bash
.venv/bin/python src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py \
  --scope-id novogene_ref \
  --index-dir refs/novogene_star_index \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --parameter-path-base . \
  --expected-sjdb-overhang 149 \
  --output results/qc/validation/00a/novogene_ref.validation.tsv
```

Dry-run writes no report. Inspect the exact checks in the
[`construct_STAR_index` contract](../../src/norad/stages/construct_STAR_index/CONTRACT.md#validation-interface),
then create the exact parent and add `--execute`:

```bash
mkdir -p results/qc/validation/00a
.venv/bin/python src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py \
  --scope-id novogene_ref \
  --index-dir refs/novogene_star_index \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --parameter-path-base . \
  --expected-sjdb-overhang 149 \
  --output results/qc/validation/00a/novogene_ref.validation.tsv \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py \
  tests/stages/construct_STAR_index/test_step_00a_build_novogene_star_index.py
```

### Step 00b: GTF To BED12

From the repository root, invoke the mode-`0755` producer directly or through
the exact repository interpreter with explicit GTF and BED paths:

```bash
src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py \
  --gtf refs/novogene_ref/genome.gtf \
  --bed refs/novogene_ref/genome.unsorted.bed

.venv/bin/python src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py \
  --gtf refs/novogene_ref/genome.gtf \
  --bed refs/novogene_ref/genome.unsorted.bed
```

From another working directory, either `cd` to the checkout or replace the
producer, GTF, and BED arguments with explicit absolute paths. The producer has
no dry-run and silently replaces its declared output; that behavior is a
characterized defect.

Submit the scheduler entry point from the intended checkout:

```bash
cd /Users/elisteiger/dev/norad
sbatch src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm
```

Submission executes implicitly and has no dry-run control. The job requires
`SLURM_SUBMIT_DIR`, changes to that directory, and honors the existing `GTF`,
`UNSORTED_BED`, `BED`, and `PYTHON_BIN` overrides. Intermediate and final BED
publication is nontransactional; preserve failure residue and scheduler logs
until ownership and recovery are explicit.

Outputs:

```bash
refs/novogene_ref/genome.unsorted.bed
refs/novogene_ref/genome.bed
```

Validated output:

```text
206,601 BED12 transcript records
```

The structured Step `00b` validator reads one explicit BED12 and source GTF:

```bash
.venv/bin/python src/norad/stages/convert_GTF_to_BED12/validate_step_00b_bed12.py \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv
```

Dry-run writes no report. Inspect the exact checks in the
[`convert_GTF_to_BED12` contract](../../src/norad/stages/convert_GTF_to_BED12/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/00b
.venv/bin/python src/norad/stages/convert_GTF_to_BED12/validate_step_00b_bed12.py \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/convert_GTF_to_BED12/test_gtf_to_bed12.py \
  tests/stages/convert_GTF_to_BED12/test_validate_step_00b_bed12.py \
  tests/stages/convert_GTF_to_BED12/test_step_00b_gtf_to_bed12.py
```

### Step 00c: GATK Reference Sidecars

From the repository root, run the final producer directly or through Bash with
the reference and all three tool paths explicit. Both forms are dry-run by
default:

```bash
src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /absolute/path/to/samtools \
  --gatk-bin /absolute/path/to/gatk \
  --java-bin /absolute/path/to/java

bash src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /absolute/path/to/samtools \
  --gatk-bin /absolute/path/to/gatk \
  --java-bin /absolute/path/to/java
```

Dry-run resolves the tool paths and prints the planned commands but invokes no
tool version or generation command and creates no directory, lock, temporary
path, FAI, or DICT. Add `--execute` only after inspecting the resolved command.
From another working directory, make the checkout, reference, and tool paths
absolute:

```bash
/absolute/path/to/norad/src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta /absolute/refs/genome.fa \
  --samtools-bin /absolute/path/to/samtools \
  --gatk-bin /absolute/path/to/gatk \
  --java-bin /absolute/path/to/java
```

The expected outputs for `refs/novogene_ref/genome.fa` are
`refs/novogene_ref/genome.fa.fai` and `refs/novogene_ref/genome.dict`. Step
`00c` uses a reference-level lock in execute mode, reuses each valid existing
sidecar, generates only a missing sidecar, and validates FAI/DICT contig-name
and length agreement. Step `05` consumes these sidecars but must not create or
repair them inside a per-sample job.

For scheduler use, SLURM opens the declared log paths before the job body runs.
Create `logs/`, change to the intended checkout, and submit the exact final job.
Omitting `EXECUTE` keeps the default dry run:

```bash
cd /path/to/norad
mkdir -p logs
sbatch --export=ALL,REFERENCE_FASTA=/absolute/refs/genome.fa,SAMTOOLS_BIN_OVERRIDE=/absolute/path/to/samtools,GATK_BIN_OVERRIDE=/absolute/path/to/gatk,JAVA_BIN_OVERRIDE=/absolute/path/to/java,TMPDIR=/absolute/path/to/tmp \
  src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.slurm
```

Real work uses the same explicit bindings plus `EXECUTE=1`:

```bash
cd /path/to/norad
mkdir -p logs
sbatch --export=ALL,REFERENCE_FASTA=/absolute/refs/genome.fa,SAMTOOLS_BIN_OVERRIDE=/absolute/path/to/samtools,GATK_BIN_OVERRIDE=/absolute/path/to/gatk,JAVA_BIN_OVERRIDE=/absolute/path/to/java,TMPDIR=/absolute/path/to/tmp,EXECUTE=1 \
  src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.slurm
```

The current CSU samtools/GATK defaults are site bindings rather than portable
defaults, and module setup is tolerated. Bash `3.2` can stop in default dry-run
before producer delegation because of the characterized empty-array expansion.
In execute mode, the wrapper checks only that the two declared output files are
nonempty; use the structured validator for content evidence.

The structured Step `00c` validator reads one explicit FASTA and its exact FAI
and DICT sidecars. Invoke its mode-`0644` file only through an explicit
interpreter:

```bash
.venv/bin/python src/norad/stages/construct_FASTA_sidecars/validate_step_00c_reference_sidecars.py \
  --scope-id novogene_ref \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --output results/qc/validation/00c/novogene_ref.validation.tsv
```

Dry-run writes no report. Inspect the exact checks in the
[`construct_FASTA_sidecars` contract](../../src/norad/stages/construct_FASTA_sidecars/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/00c
.venv/bin/python src/norad/stages/construct_FASTA_sidecars/validate_step_00c_reference_sidecars.py \
  --scope-id novogene_ref \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --output results/qc/validation/00c/novogene_ref.validation.tsv \
  --execute
```

The report contains exactly the five ordered `fasta_structure`,
`fai_structure`, `dict_structure`, `fai_contig_agreement`, and
`dict_contig_agreement` rows under the common seven-column validation contract.
It is reference-sidecar evidence, not an ad hoc BAM/reference comparison. A
content disagreement reports `status=fail`; it does not repair any input.

Focused validation:

```bash
bash tests/stages/construct_FASTA_sidecars/test_step_00c_prepare_gatk_reference.sh
.venv/bin/python -m pytest -q \
  tests/stages/construct_FASTA_sidecars/test_validate_step_00c_reference_sidecars.py \
  tests/test_slurm_wrapper_contracts.py
```

These are local fixture and mocked-wrapper checks. They do not prove real
samtools/GATK/Java execution, SLURM, cluster, production, scientific-review, or
biological readiness. Preserve a retained FAI with absent DICT after a nonzero
producer attempt as incomplete-attempt evidence; follow the
[Step `00c` troubleshooting routes](TROUBLESHOOTING.md#step-00c-faidict-validation-fails)
before any separately authorized cleanup or rerun.

## Step 01: STAR Alignment

From the repository root, run the final producer directly or through Bash with
all required arguments. Both forms are dry-run by default:

```bash
src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh \
  --sample-id ABE_EV_2 \
  --r1-fastq data/ABE_EV_2_R1.fastq.gz \
  --r2-fastq data/ABE_EV_2_R2.fastq.gz \
  --star-index refs/novogene_star_index \
  --output-dir results/star/ABE_EV_2 \
  --threads 8

bash src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh \
  --sample-id ABE_EV_2 \
  --r1-fastq data/ABE_EV_2_R1.fastq.gz \
  --r2-fastq data/ABE_EV_2_R2.fastq.gz \
  --star-index refs/novogene_star_index \
  --output-dir results/star/ABE_EV_2 \
  --threads 8
```

Dry-run still requires `STAR` on `PATH` and creates the declared output
directory. Inspect the printed command before adding `--execute`. From another
working directory, use the absolute checkout path plus absolute input and
output paths:

```bash
bash /absolute/path/to/norad/src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh \
  --sample-id ABE_EV_2 \
  --r1-fastq /absolute/data/ABE_EV_2_R1.fastq.gz \
  --r2-fastq /absolute/data/ABE_EV_2_R2.fastq.gz \
  --star-index /absolute/refs/novogene_star_index \
  --output-dir /absolute/results/star/ABE_EV_2 \
  --threads 8
```

Submit the scheduler entry point only from the intended checkout because it
delegates through caller-relative paths:

```bash
cd <checkout>
sbatch src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm
```

`EXECUTE=0` is the default, but its default bindings create placeholder FASTQ
files and an index directory. `EXECUTE=1` refuses those bindings. Real work
supplies all five overrides; threads come from `SLURM_CPUS_PER_TASK`:

```bash
cd <checkout>
SAMPLE_ID=ABE_EV_2 \
R1_FASTQ=/absolute/data/ABE_EV_2_R1.fastq.gz \
R2_FASTQ=/absolute/data/ABE_EV_2_R2.fastq.gz \
STAR_INDEX=/absolute/refs/novogene_star_index \
OUTPUT_DIR=/absolute/results/star/ABE_EV_2 \
EXECUTE=1 \
  sbatch src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm
```

The wrapper loads STAR `2.7.11b`, derives threads from the allocation, and
performs no independent output validation. Submission and mocked tests do not
prove scheduler, module, or cluster behavior.

Purpose:

```text
Align paired-end FASTQs to the STAR index and write coordinate-sorted BAM output.
```

Main output family:

```bash
results/star/<sample>/<sample>.Aligned.sortedByCoord.out.bam
```

Other STAR output families:

```bash
results/star/<sample>/<sample>.Log.final.out
results/star/<sample>/<sample>.Log.out
results/star/<sample>/<sample>.Log.progress.out
results/star/<sample>/<sample>.SJ.out.tab
```

Known alignment summaries:

| Sample | Approximate input reads | Unique mapping rate |
| ------ | ----------------------: | ------------------: |
| `ABE_EV_2` | 21.36 million | 58.50% |
| `ABE_EV_3` | 20.5 million | 82.95% |
| `ABE_EV4` | 26.6 million | 71.06% |
| `ABE_PUM1_2` | 21.1 million | 77.51% |
| `ABE_PUM1_3` | 23.2 million | 85.38% |
| `ABE_PUM1_4` | 22.5 million | 70.96% |

The structured Step `01` validator consumes the five exact output paths for
one sample:

```bash
.venv/bin/python src/norad/stages/align_RNA_reads_with_STAR/validate_step_01_star_alignment.py \
  --scope-id ABE_EV_2 \
  --bam results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --log-final results/star/ABE_EV_2/ABE_EV_2.Log.final.out \
  --log-out results/star/ABE_EV_2/ABE_EV_2.Log.out \
  --log-progress results/star/ABE_EV_2/ABE_EV_2.Log.progress.out \
  --sj-out results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab \
  --output results/qc/validation/01/ABE_EV_2.validation.tsv
```

Dry-run writes no report. Inspect the exact checks in the
[`align_RNA_reads_with_STAR` contract](../../src/norad/stages/align_RNA_reads_with_STAR/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/01
.venv/bin/python src/norad/stages/align_RNA_reads_with_STAR/validate_step_01_star_alignment.py \
  --scope-id ABE_EV_2 \
  --bam results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --log-final results/star/ABE_EV_2/ABE_EV_2.Log.final.out \
  --log-out results/star/ABE_EV_2/ABE_EV_2.Log.out \
  --log-progress results/star/ABE_EV_2/ABE_EV_2.Log.progress.out \
  --sj-out results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab \
  --output results/qc/validation/01/ABE_EV_2.validation.tsv \
  --execute
```

Focused validation:

```bash
bash tests/stages/align_RNA_reads_with_STAR/test_step_01_star_align.sh
.venv/bin/python -m pytest -q \
  tests/stages/align_RNA_reads_with_STAR/test_validate_step_01_star_alignment.py \
  tests/test_slurm_wrapper_contracts.py
```

Inspect the BAM, all three STAR logs, splice-junction table, scheduler logs, and
any partial direct-final output before deciding on a rerun. The
[`align_RNA_reads_with_STAR` owner README](../../src/norad/stages/align_RNA_reads_with_STAR/README.md)
owns diagnostics, recovery, rollback, and the local-only evidence ceiling.

## Step 02: Canonical Sort, Read-Group Tagging, And BAM Indexing

The producer resolves `samtools` only from `PATH`. From the repository root,
run its no-write dry plan directly or through explicit Bash:

```bash
src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8

bash src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8
```

Dry-run verifies the input and that samtools is on `PATH`, but invokes no
samtools command and creates no output directory, lock, scratch path, backup,
BAM, or BAI. After inspecting the plan, execute through either form:

```bash
src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8 \
  --execute

bash src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir results/bam/ABE_EV_2 \
  --threads 8 \
  --execute
```

From another CWD, use absolute producer, input, and output paths. Samtools
still resolves only from that process's `PATH`:

```bash
/absolute/path/to/norad/src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh \
  --sample-id ABE_EV_2 \
  --input-alignment /absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --output-dir /absolute/results/bam/ABE_EV_2 \
  --threads 8
```

Canonical outputs:

```bash
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
```

Read-group convention:

```text
ID=<sample_id>
SM=<sample_id>
LB=<sample_id>
PL=ILLUMINA
```

`LB=<sample_id>` is provisional until more specific library or lane metadata is recovered.

The structured Step `02` validator consumes one exact BAM/BAI pair and one
explicit samtools executable:

```bash
.venv/bin/python src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv
```

Dry-run writes no report. Inspect the exact checks and preserved asymmetries in
the [`construct_canonical_BAM` contract](../../src/norad/stages/construct_canonical_BAM/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/02
.venv/bin/python src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv \
  --execute
```

Repeat the same execute command to replace the owned report deterministically
after stable-input revalidation. From another CWD, make the interpreter,
validator, BAM, BAI, samtools executable, and output paths absolute; omitting
`--execute` remains the no-write journey:

```bash
/absolute/path/to/norad/.venv/bin/python \
  /absolute/path/to/norad/src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam /absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai /absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /absolute/path/to/samtools \
  --output /absolute/results/qc/validation/02/ABE_EV_2.validation.tsv
```

An `ERROR: unable to load NORAD BAM-validation owner at ...` diagnostic is a
checkout-integrity failure. Inspect private
`src/norad/libraries/bam_validation.py`; do not add `PYTHONPATH`, install a
package, invoke a helper CLI, or restore a legacy Step `02` path.

Focused validation:

```bash
bash tests/stages/construct_canonical_BAM/test_step_02_sort_index_bam.sh
.venv/bin/python -m pytest -q \
  tests/stages/construct_canonical_BAM/test_validate_step_02_canonical_bam.py \
  tests/libraries/test_bam_validation.py \
  tests/test_validate_step_04_mark_duplicates.py \
  tests/test_validate_step_05_split_ncigar.py \
  tests/test_slurm_wrapper_contracts.py
```

The wrapper delegates relative to the caller's CWD and ignores
`SLURM_SUBMIT_DIR`. Change to the intended checkout and create `logs/` before
submission. Dry-run exposes every binding explicitly:

```bash
cd /absolute/path/to/norad
mkdir -p logs
SAMPLE_ID=ABE_EV_2 \
INPUT_ALIGNMENT=/absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
OUTPUT_DIR=/absolute/results/bam/ABE_EV_2 \
THREADS=8 \
EXECUTE=0 \
  sbatch src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm
```

Execute:

```bash
cd /absolute/path/to/norad
mkdir -p logs
SAMPLE_ID=ABE_EV_2 \
INPUT_ALIGNMENT=/absolute/results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
OUTPUT_DIR=/absolute/results/bam/ABE_EV_2 \
THREADS=8 \
EXECUTE=1 \
  sbatch src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm
```

The wrapper forces `TMPDIR=/tmp`, creates `logs/` and `OUTPUT_DIR` even in
dry-run, strictly loads samtools `1.19.2`, and tolerates diagnostics only from
its two `module list` calls. Bash `3.2` can fail while expanding the empty
dry-run argument array before producer delegation. Its execute-mode post-check
only requires the BAM and BAI paths to be files. Mocked local tests do not prove
real scheduler, module, cluster, or samtools behavior.

Hardened execution flow:

```text
1. Create the output directory in execute mode.
2. Acquire the per-sample lock directory:
   results/bam/<sample>/.<sample>.step02.lock/
3. Sort the input alignment to a job-specific temporary BAM.
4. Run samtools addreplacerg with repeated -r arguments and -w.
5. Index the temporary read-group-tagged BAM.
6. Validate the temporary BAM and BAI.
7. Confirm existing canonical BAM/BAI are either both present or both absent.
8. Back up any existing canonical pair to job-specific backup paths.
9. Publish the replacement BAM and BAI to the stable canonical paths.
10. Revalidate the published canonical BAM and BAI.
11. Remove backups and the owned lock only after successful final validation.
```

Publication uses backup and rollback attempts, but the BAM/BAI pair is not one
indivisible atomic operation and complete restoration is not guaranteed. The
characterized failure-inside-rollback case fails final BAI publication and then
prior-BAM restoration. It returns nonzero and can leave only the prior BAI at
the canonical path while the BAM, both backups, owned lock, and run-token
scratch are absent. Preserve the pair directory, producer and scheduler
streams, every run-token temporary/backup path, and exact final/backup bytes
before a separately authorized recovery decision. Absence of a lock, backup,
receipt, or marker does not authorize deletion, adoption, or retry. Follow the
[Step `02` recovery route](TROUBLESHOOTING.md#step-02-canonical-bam-rollback-leaves-a-prior-bai-only-lockless-pair).

Validation checklist for each final canonical BAM:

```bash
module load samtools/1.19.2

sample=<sample_id>
bam="results/bam/$sample/$sample.sorted.bam"

samtools quickcheck "$bam"
samtools view -H "$bam" | grep '^@HD.*SO:coordinate'
samtools view -H "$bam" | grep '^@RG'

total_records="$(samtools view -c "$bam")"
tagged_records="$(samtools view -c -d "RG:$sample" "$bam")"

test "$total_records" -gt 0
test "$tagged_records" -eq "$total_records"
ls -lh "$bam" "$bam.bai"
```

Confirmed final canonical BAM sizes were approximately:

| Sample | BAM size |
| ------ | -------: |
| `ABE_EV_2` | 3.0 GB |
| `ABE_EV_3` | 2.0 GB |
| `ABE_EV4` | 2.9 GB |
| `ABE_PUM1_2` | 2.2 GB |
| `ABE_PUM1_3` | 2.1 GB |
| `ABE_PUM1_4` | 2.5 GB |

Historical resource observations from the pre-hardening `ABE_EV_2` Step `02` run:

```text
Elapsed: about 3 minutes 46 seconds
MaxRSS: about 6.8G
Output BAM: about 3.0G
Output BAI: about 3.3M
```

These observations are historical, not guaranteed resource requirements for future cohort runs.

Normal tool progress may appear on stderr. For example, samtools sort can emit:

```text
[bam_sort_core] merging from 4 files and 8 in-memory blocks...
```

## Step 02b: BAM QC

Script:

```bash
scripts/step_02b_bam_qc.sh
```

Job:

```bash
jobs/step_02b_bam_qc.slurm
```

Outputs:

```bash
results/qc/bam/<sample>.quickcheck.txt
results/qc/bam/<sample>.flagstat.txt
```

The structured Step `02b` validator reads those two persisted evidence files:

```bash
.venv/bin/python scripts/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv
```

Dry-run writes no report or reruns samtools. Inspect the exact checks in the
[`collect_canonical_BAM_QC_evidence` contract](../../src/norad/evidence/collect_canonical_BAM_QC_evidence/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/02b
.venv/bin/python scripts/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_02b_bam_qc.py
```

Dry-run:

```bash
sbatch jobs/step_02b_bam_qc.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_02b_bam_qc.slurm
```

Validation checklist:

```bash
sample=<sample_id>
cat "results/qc/bam/$sample.quickcheck.txt"
head -40 "results/qc/bam/$sample.flagstat.txt"
grep -E "in total|primary|secondary|mapped|properly paired|duplicates" \
  "results/qc/bam/$sample.flagstat.txt"
```

Important nuance: the current Step `02b` script creates the requested output directory before dry-run exit. It should not be described as side-effect-free.

Cluster PATH note: the first Step `02b` cohort attempt failed immediately because `samtools` was not found on `PATH`, despite module output listing `samtools/1.19.2`. The successful rerun prepended the known samtools bin directory:

```text
/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin
```

This is a cluster environment/PATH inconsistency, not a BAM/QC failure.

## Step 03: RSeQC Strandedness / Orientation Inference

Script:

```bash
bash scripts/step_03_infer_strandedness_and_orientation.sh
```

Job:

```bash
jobs/step_03_infer_strandedness_and_orientation.slurm
```

Output:

```bash
results/qc/strandedness/<sample>.infer_experiment.txt
```

The structured Step `03` validator reads one exact persisted RSeQC report:

```bash
.venv/bin/python scripts/validate_step_03_rseqc_orientation.py \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv
```

Dry-run writes no report. Inspect the exact checks and neutral-orientation
boundary in the
[`collect_RSeQC_paired_orientation_evidence` contract](../../src/norad/evidence/collect_RSeQC_paired_orientation_evidence/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/03
.venv/bin/python scripts/validate_step_03_rseqc_orientation.py \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_03_rseqc_orientation.py
```

Dry-run:

```bash
sbatch jobs/step_03_infer_strandedness_and_orientation.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_03_infer_strandedness_and_orientation.slurm
```

Validation checklist:

```bash
sample=<sample_id>
cat "results/qc/strandedness/$sample.infer_experiment.txt"
```

Confirmed result:

```text
All six Novogene Remora libraries are paired-end and reverse-stranded / first-strand-style.
```

Tool-specific examples:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

## Step 04: MarkDuplicates

Script:

```bash
bash scripts/step_04_mark_duplicates.sh
```

Job:

```bash
jobs/step_04_mark_duplicates.slurm
```

Inputs:

```bash
results/bam/<sample>/<sample>.sorted.bam
results/bam/<sample>/<sample>.sorted.bam.bai
```

Outputs:

```bash
results/markdup/<sample>/<sample>.markdup.bam
results/markdup/<sample>/<sample>.markdup.bam.bai
results/qc/markdup/<sample>.markdup.metrics.txt
```

The structured Step `04` validator reads the exact output triplet plus one
explicit samtools executable:

```bash
.venv/bin/python scripts/validate_step_04_mark_duplicates.py \
  --scope-id ABE_EV_2 \
  --bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --bai results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai \
  --metrics results/qc/markdup/ABE_EV_2.markdup.metrics.txt \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/04/ABE_EV_2.validation.tsv
```

Dry-run writes no report. Inspect the exact checks in the
[`mark_BAM_duplicates_with_Picard` contract](../../src/norad/stages/mark_BAM_duplicates_with_Picard/CONTRACT.md#validation-interface),
then create the output parent and add `--execute`:

```bash
mkdir -p results/qc/validation/04
.venv/bin/python scripts/validate_step_04_mark_duplicates.py \
  --scope-id ABE_EV_2 \
  --bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --bai results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam.bai \
  --metrics results/qc/markdup/ABE_EV_2.markdup.metrics.txt \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/04/ABE_EV_2.validation.tsv \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_04_mark_duplicates.py
```

Dry-run:

```bash
sbatch jobs/step_04_mark_duplicates.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_04_mark_duplicates.slurm
```

If a supported Java 17 executable is known, pass it explicitly:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,JAVA_BIN_OVERRIDE=/path/to/java \
  jobs/step_04_mark_duplicates.slurm
```

Validation checklist for promotion of each sample:

```bash
sample=<sample_id>
bam="results/markdup/$sample/$sample.markdup.bam"
metrics="results/qc/markdup/$sample.markdup.metrics.txt"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
samtools quickcheck "$bam"
samtools view -H "$bam" | grep '^@HD.*SO:coordinate'
samtools view -H "$bam" | grep '^@RG'
ls -lh "$bam" "$bam.bai" "$metrics"
```

Step `04` uses `REMOVE_DUPLICATES=false`; duplicate reads remain present with the duplicate flag set.

All six samples have duplicate-marked BAM, BAM index, Picard metrics, `samtools quickcheck: PASS`, retained `@HD SO:coordinate`, retained sample-specific `@RG`, and a populated Picard metrics row.

Confirmed final Step `04` outputs:

| Sample | Markdup BAM size | Metrics size |
| ------ | ---------------: | -----------: |
| `ABE_EV_2` | 3.1G | 16K |
| `ABE_EV_3` | 2.1G | 7.8K |
| `ABE_EV4` | 3.0G | 15K |
| `ABE_PUM1_2` | 2.3G | 12K |
| `ABE_PUM1_3` | 2.1G | 8.5K |
| `ABE_PUM1_4` | 2.5G | 13K |

Confirmed Step `04` runtime/resource observations:

| Sample | Runtime | MaxRSS |
| ------ | ------: | -----: |
| `ABE_EV_2` | 00:08:29 | 22,660,004K |
| `ABE_EV_3` | 00:06:06 | 23,912,380K |
| `ABE_EV4` | 00:08:52 | 23,287,592K |
| `ABE_PUM1_2` | 00:06:40 | 24,293,400K |
| `ABE_PUM1_3` | 00:06:33 | 24,341,032K |
| `ABE_PUM1_4` | 00:07:32 | 23,376,504K |

Confirmed MarkDuplicates metrics:

| Sample | Read pairs examined | Duplicate read pairs | Optical duplicate pairs | Percent duplication | Estimated library size |
| ------ | ------------------: | -------------------: | ----------------------: | ------------------: | ---------------------: |
| `ABE_EV_2` | 17,663,180 | 11,731,288 | 120,669 | 0.664166 | 6,327,403 |
| `ABE_EV_3` | 18,867,589 | 11,371,887 | 130,069 | 0.602721 | 8,397,468 |
| `ABE_EV4` | 23,240,508 | 19,860,628 | 177,257 | 0.854569 | 3,383,587 |
| `ABE_PUM1_2` | 19,087,654 | 13,522,128 | 128,791 | 0.708423 | 5,783,576 |
| `ABE_PUM1_3` | 21,657,503 | 14,809,440 | 150,924 | 0.683802 | 7,214,041 |
| `ABE_PUM1_4` | 19,424,683 | 16,348,986 | 132,657 | 0.841660 | 3,081,584 |

Duplication is high across the cohort and should be tracked as a library/QC feature, not treated as a pipeline failure. `ABE_EV4` and `ABE_PUM1_4` have the highest duplication; `ABE_EV_3` has the lowest duplication and largest estimated library size. The observed Step `04` memory range was about 22.7-24.3 GB MaxRSS; this is observed evidence, not a guaranteed resource requirement.

## Step 05: SplitNCigarReads

Expected tool:

```text
GATK SplitNCigarReads
```

GATK availability is confirmed on compute node `node002`: OpenJDK `17.0.14`, GATK `4.6.1.0`, path `/cm/shared/apps/gatk/gatk-4.6.1.0/gatk`; the tool probe completed successfully with exit code `0:0`.

Entry points:

```text
jobs/step_05_split_n_cigar_reads.slurm
scripts/step_05_split_n_cigar_reads.sh
tests/shell/test_step_05_split_n_cigar_reads.sh
```

Inputs:

```text
results/markdup/<sample_id>/<sample_id>.markdup.bam
results/markdup/<sample_id>/<sample_id>.markdup.bam.bai
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

The structured Step `05` validator consumes one exact output pair, the three
exact reference inputs, and one explicit samtools executable:

```bash
.venv/bin/python scripts/validate_step_05_split_ncigar.py \
  --scope-id ABE_EV_2 \
  --bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --bai results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam.bai \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/05/ABE_EV_2.validation.tsv
```

Dry-run writes no report. Inspect the exact output/reference checks in the
[`split_N_cigar_reads_with_GATK` contract](../../src/norad/stages/split_N_cigar_reads_with_GATK/CONTRACT.md#validation-interface),
then create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/05
.venv/bin/python scripts/validate_step_05_split_ncigar.py \
  --scope-id ABE_EV_2 \
  --bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --bai results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam.bai \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/05/ABE_EV_2.validation.tsv \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_05_split_ncigar.py
```

Outputs:

```text
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam
results/split_ncigar/<sample_id>/<sample_id>.split_ncigar.bam.bai
```

Dry-run:

```bash
sbatch jobs/step_05_split_n_cigar_reads.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_05_split_n_cigar_reads.slurm
```

Step `05` still follows the normal dry-run/execute submission pattern, but the GATK process must use a per-run project-storage temp directory. The hardened script passes that directory through:

```text
--java-options -Djava.io.tmpdir=...
--tmp-dir ...
TMPDIR
```

If a supported Java 17 executable is known, pass it explicitly:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,JAVA_BIN_OVERRIDE=/path/to/java \
  jobs/step_05_split_n_cigar_reads.slurm
```

Direct script dry-run with explicit cluster tools:

```bash
bash scripts/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools
```

Direct script execute with explicit cluster tools:

```bash
bash scripts/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --execute
```

Validation checklist for promotion of each sample:

```bash
sample=<sample_id>
bam="results/split_ncigar/$sample/$sample.split_ncigar.bam"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
samtools quickcheck "$bam"
samtools view -H "$bam" | grep '^@HD.*SO:coordinate'
samtools view -H "$bam" | grep '^@RG'
ls -lh "$bam" "$bam.bai"
```

Step `05` requires the Step `00c` sidecars, fails clearly if they are missing, and must not create shared reference sidecars inside per-sample jobs. It is dry-run by default, writes GATK output to run-token temporary paths in execute mode, validates the temporary BAM/BAI pair before publication, and rolls back an existing final pair if publication fails after backups begin.

The six-sample Step `05` output inspection with `tests/data_checks/validate_step05_outputs.sh` reported:

```text
PASS=6
PENDING_OR_RUNNING=0
FAIL=0
```

All six final Step `05` outputs have final BAM/BAI files, passing `samtools quickcheck`, `@HD` with `SO:coordinate`, sample-matching `@RG`, and no remaining Step `05` scratch files.

Confirmed final Step `05` output sizes:

| Sample | Split-N-cigar BAM size | BAI size |
| ------ | ---------------------: | -------: |
| `ABE_EV_2` | 4.4G | 2.0M |
| `ABE_EV_3` | 3.5G | 1.6M |
| `ABE_EV4` | 4.4G | 1.8M |
| `ABE_PUM1_2` | 3.7G | 1.6M |
| `ABE_PUM1_3` | 3.7G | 1.6M |
| `ABE_PUM1_4` | 3.8G | 1.8M |

The first `ABE_EV_2` cluster execute attempt confirmed that GATK reached useful traversal behavior: pass 1 completed and pass 2 started. It later failed during HTSJDK temporary spill/write/close behavior because `SortingCollection` temp files were written to node-local `/tmp` and hit `No space left on device`. Treat that failed attempt as resolved hardening context, not as current blocker language.

Failure cleanup now removes owned temp BAM/BAI files, alternate GATK-created sidecars, GATK temp directories, and owned locks.

## Step 06: Split BAM By Read Orientation

The [functional contract](../../src/norad/stages/partition_BAM_by_mechanical_read_orientation/CONTRACT.md)
owns the entry points, Step `05` inputs, five-file output set, flag grouping,
count reconciliation, and validator checks. `FWD_like` and `REV_like` are
mechanical read-orientation labels, not biological sense/antisense claims.

Dry-run:

```bash
sbatch jobs/step_06_split_bam_by_read_orientation.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_06_split_bam_by_read_orientation.slurm
```

Direct script dry-run with explicit cluster samtools:

```bash
scripts/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir results/orientation/ABE_EV_2 \
  --qc-dir results/qc/orientation \
  --threads 1 \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools
```

Direct script execute with explicit cluster samtools:

```bash
scripts/step_06_split_bam_by_read_orientation.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam \
  --output-dir results/orientation/ABE_EV_2 \
  --qc-dir results/qc/orientation \
  --threads 1 \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --execute
```

Validation checklist for rerun or spot inspection:

```bash
sample=<sample_id>
fwd="results/orientation/$sample/$sample.FWD_like.bam"
rev="results/orientation/$sample/$sample.REV_like.bam"
counts="results/qc/orientation/$sample.orientation_counts.tsv"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
samtools quickcheck "$fwd"
samtools quickcheck "$rev"
ls -lh "$fwd" "$fwd.bai" "$rev" "$rev.bai" "$counts"
cat "$counts"
```

Structured validation is explicit-input and dry-run-first:

```bash
.venv/bin/python scripts/validate_step_06_orientation_outputs.py \
  --scope-id "$sample" \
  --fwd-bam "$fwd" \
  --fwd-bai "$fwd.bai" \
  --rev-bam "$rev" \
  --rev-bai "$rev.bai" \
  --counts "$counts" \
  --output "results/qc/validation/06/$sample.validation.tsv"
```

After inspecting the five printed checks, rerun the same command with
`--execute`. Exact checks and limits remain in the linked contract.

All six Step `06` jobs completed `0:0`; `FWD_like` / `REV_like` BAM+BAI outputs were published for all six samples; `samtools quickcheck` passed silently; orientation counts TSVs were present; `assigned_fraction = 1.000000` and `unassigned_records = 0` for all six samples; and no Step `06` scratch files remained.

## Step 07: bcftools mpileup

No command in this section has yet produced inspected Step `07` cluster evidence. The prior compute-node probe confirmed bcftools `1.21` at `/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools` with exit code `0:0`; it did not validate this workflow.

Implemented files:

```text
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
configs/step_07_partitions.pilot.tsv
configs/step_07_partitions.primary_contigs.tsv
configs/step_07_partitions.example.tsv
```

Structured validation consumes one exact completed partition transaction and
is dry-run-first:

```bash
cohort=<cohort_id>
partition=<partition_id>
partition_dir="results/mpileup/$cohort/$partition"

.venv/bin/python scripts/validate_step_07_mpileup_outputs.py \
  --cohort-id "$cohort" \
  --partition-id "$partition" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --fwd-vcf "$partition_dir/$cohort.$partition.FWD_like.mpileup.vcf" \
  --rev-vcf "$partition_dir/$cohort.$partition.REV_like.mpileup.vcf" \
  --receipt "$partition_dir/$cohort.$partition.step07_outputs.tsv" \
  --output "results/qc/validation/07/${cohort}__${partition}.validation.tsv"
```

After inspecting the five printed checks, rerun the same command with
`--execute`. Exact checks and limits remain in the
[`generate_partitioned_cohort_mpileup_VCFs` contract](../../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/CONTRACT.md#validation-interface).

Partition manifest schema:

```text
partition_id    selector_type    selector_value
```

`region` passes `selector_value` to bcftools `-r`. `regions_file` passes it to `-R`; a relative regions-file path resolves from the partition manifest directory. The primary manifest is the declared correction universe. The separate one-row pilot manifest selects `pilot_1` at `1:1-100000`. Never replace either contract with a VCF glob.

Before any Step `07` dry-run, locate or deliberately provision the full
cluster `samples.tsv`. It is absent from the current Git checkout, and neither
its cluster-local persistence nor its current bytes have been inspected.
Update that full runtime manifest with the optional `replicate` column carrying
the approved Step `09` pairs:

```text
ABE_EV_2 / ABE_PUM1_2 -> 2
ABE_EV_3 / ABE_PUM1_3 -> 3
ABE_EV4  / ABE_PUM1_4 -> 4
```

Use `configs/step_09_pairs.NORAD_EV_PUM1.tsv` only as a reference while editing
the full manifest; it is not a runtime overlay. Validate the full manifest:

```bash
python scripts/validate_manifest.py --manifest samples.tsv
head -1 samples.tsv
sed -n '1,8p' configs/step_09_pairs.NORAD_EV_PUM1.tsv
sha256sum samples.tsv 2>/dev/null || shasum -a 256 samples.tsv
```

The generic validator permits empty optional `replicate` values, so also
assert that the runtime manifest's exact `(sample_id, condition, replicate)`
set matches the approved pairing reference:

```bash
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

The `diff` must be empty with exit status `0`.

This must happen before Step `07` because the manifest SHA-256 is embedded in
the Step `07` receipts, propagated into Step `08`, checked again by Step `09`,
and recorded in the Step `09` summary. If any Step `07` or Step `08` artifacts
were made from the pre-replicate manifest, regenerate them through the normal
upstream workflow; never edit receipt hashes to force a match.

If establishing this file requires adding or changing tracked repository
manifest/config content, stop before `validate-step-07` and create a separately
gated descendant such as `step-07a-runtime-manifest`. Commit the config and
validation change, run the full gate, make a separate docpatch, clean/push, and
create `validate-step-07` from that branch. Do not combine configuration
implementation with an evidence-only validation branch. If the runtime file
is a byte-identical cluster-local copy, record its path and SHA-256 as
validation evidence without fabricating an implementation commit.

Complete the remaining preflight before submission:

```bash
set -euo pipefail

test -z "$(git status --porcelain)"
mkdir -p logs
df -h .
quota -s 2>/dev/null || true
/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools --version
test -s refs/novogene_ref/genome.fa
test -s refs/novogene_ref/genome.fa.fai
test -s refs/novogene_ref/genome.gtf
command -v sha256sum >/dev/null || command -v shasum >/dev/null
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript make real-r-test
```

The exact `/supported/path/to/Rscript` must be visible in the same
compute-node/batch environment planned for Steps `08`-`09`. Run the displayed
test command inside an allocated compute-node or batch context; running it in
the login shell proves only the login-shell environment. Both real-R suites
must pass in the supported execution context; the Step `08` packages and
`sha256sum` or `shasum` must be available. Separately inspect all six samples'
`FWD_like` and `REV_like` BAM/BAI pairs (12 BAM/BAI pairs total), confirm the
reference/GTF identity, and record free-space/quota evidence. The dry-run
validates inputs but does not replace this operator inventory.

Before the first cluster dry-run, inspect the reference contigs and specifically confirm the tracked `MT` selector:

```bash
awk -F '\t' '$1 == "MT" { print }' refs/novogene_ref/genome.fa.fai
sed -n '1,30p' configs/step_07_partitions.primary_contigs.tsv
```

Assert every primary manifest selector appears exactly once in the FAI:

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

The script validates every selector against the FAI and will fail on spelling differences such as `chr1` versus `1`. The repository currently records the primary set as `1`-`22`, `X`, `Y`, and `MT`, but its exact compatibility with the cluster reference has not yet been inspected for Step `07`.

Direct cluster dry-run for the one-row pilot:

```bash
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.pilot.tsv \
  --partition-id pilot_1 \
  --orientation-root results/orientation \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-root results/mpileup \
  --bcftools-bin /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
```

Dry-run is the default and creates no output directory, lock, scratch path, VCF, or receipt. Inspect the resolved BAM order and both printed pipelines. Each orientation must pass all six manifest-ordered BAMs in one bcftools invocation. The preserved defaults are maximum depth `10000000`, skip indels, FORMAT `DP,AD,ADF,ADR,SP`, INFO `AD,ADF,ADR`, filter `INFO/AD[1-]>2 & MAX(FORMAT/DP)>20`, plain VCF output, and no `bcftools call`.

Planned pilot SLURM dry-run:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
PARTITION_MANIFEST=configs/step_07_partitions.pilot.tsv,\
PARTITION_ID=pilot_1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

Inspect scheduler state and both logs before execute mode:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -160 logs/norad-mpileup-<JOBID>.out
tail -160 logs/norad-mpileup-<JOBID>.err
```

Only after the pilot dry-run is clean, submit the pilot execute job:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
PARTITION_MANIFEST=configs/step_07_partitions.pilot.tsv,\
PARTITION_ID=pilot_1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

One primary chromosome is the next promotion gate:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv,\
PARTITION_ID=1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm

# after inspection of the dry-run job:
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv,\
PARTITION_ID=1 \
  jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

Do not submit the remaining primary partitions until the one-chromosome outputs pass inspection. Submit each declared partition explicitly; Step `07` does not add a job array or generic dispatcher. The wrapper's `long` partition and eight-hour, one-CPU request are provisional and have not been cluster-proven.

Record pilot and chromosome-1 elapsed time, maximum RSS, and both VCF sizes.
Use those observations to estimate the remaining storage requirement before
submitting the other 24 primary partitions.

Each successful partition publishes this complete set atomically:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

For the pilot, inspect the committed set:

```bash
cohort=NORAD_EV_PUM1
partition=pilot_1
out_dir="results/mpileup/$cohort/$partition"
fwd="$out_dir/$cohort.$partition.FWD_like.mpileup.vcf"
rev="$out_dir/$cohort.$partition.REV_like.mpileup.vcf"
receipt="$out_dir/$cohort.$partition.step07_outputs.tsv"
bcftools=/cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools

ls -lh "$fwd" "$rev" "$receipt"
"$bcftools" view -h "$fwd"
"$bcftools" view -h "$rev"
"$bcftools" query -l "$fwd"
"$bcftools" query -l "$rev"
"$bcftools" view -H "$fwd" | wc -l
"$bcftools" view -H "$rev" | wc -l
awk -F '\t' 'NR == 1 || NR <= 3 { print }' "$receipt"
```

Compare both `query -l` results exactly, line for line, with the `sample_id` order in `samples.tsv`. Reconcile the two observed record counts with the receipt. A header-only VCF is valid when its header and sample order validate and the receipt records `0`.

The receipt records cohort, partition selector, orientation, VCF path, both manifest hashes, sample count, and record count. It is published last and is the downstream commit marker. A VCF pair without its matching valid receipt is incomplete and must not be consumed.

Execute mode validates input BAM/BAI pairs, FASTA/FAI, selectors, VCF structure, sample order, record counts, and stable manifests. It uses an owned cohort/partition lock, run-token scratch paths, validation-before-publication, rollback, and owned cleanup. Do not delete a foreign lock or adopt an incomplete output set without first inspecting its owner and scheduler state.

Primary Step `07` exit gate:

```text
25 primary partition receipts
50 structurally valid primary VCFs
exact manifest-ordered six-sample columns in every VCF
one unchanged replicate-bearing sample-manifest hash
one unchanged primary partition-manifest hash
receipt record counts reconciled
all jobs COMPLETED 0:0 with logs and outputs inspected
no owned lock or run-token scratch residue
```

`pilot_1` adds one receipt and two VCFs under the output root, but it is
validation-only. Exclude it from the 25/50 totals and never include it in the
Step `08` correction universe.

Count only manifest-named primary outputs, never every file under the output
root:

```bash
set -euo pipefail

cohort=NORAD_EV_PUM1
partition_manifest=configs/step_07_partitions.primary_contigs.tsv
receipt_count=0
vcf_count=0

while IFS=$'\t' read -r partition_id selector_type selector_value; do
    [[ "$partition_id" == "partition_id" ]] && continue
    out_dir="results/mpileup/$cohort/$partition_id"
    receipt="$out_dir/$cohort.$partition_id.step07_outputs.tsv"
    test -s "$receipt"
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

This loop intentionally never reads the pilot manifest. Continue with the
per-file bcftools/sample-order, receipt-hash, selector, and record-count
validation; counts alone are not proof.

Cluster promotion order:

```text
Step 07 dry-run
-> pilot execute and output inspection
-> one primary chromosome execute and output inspection
-> remaining approved primary partitions and combined receipt inspection
-> Step 07 evidence docpatch
-> Step 08 runtime validation
-> Step 08 evidence docpatch
-> Step 09 runtime validation
-> Step 09 evidence docpatch
```

Remote promotion is paused during the approved local implementation sequence.
When it resumes, create validation branches only after the final local
validator branch is clean, docpatched, and pushed:

```text
refactor-99-final-audit
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Each validation branch receives its inspected evidence/status docpatch,
clean-status/history check, and push before the next branch is created.
Each remote validation branch must also regenerate the structured run summary
and consolidated HTML/PDF report in results storage after evidence inspection,
then record the report paths and hashes in its evidence docpatch. Cluster proof
and biological readiness remain independent.

## Step 08: VCF Preprocessing

No Step `08` cluster dry-run, execute job, log, or output evidence has been
inspected. Do not runtime-promote Step `08` before Step `07` is
cluster-proven.

Implemented files:

```text
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
jobs/step_08_vcf_preprocessing.slurm
tests/shell/test_step_08_vcf_preprocessing.sh
tests/r/run_step_08_vcf_preprocessing_tests.sh
tests/r/test_step_08_vcf_preprocessing.R
```

Structured validation consumes the exact published three-TSV transaction and
is dry-run-first:

```bash
.venv/bin/python scripts/validate_step_08_preprocessing_outputs.py \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --sites results/vcf_preprocessed/NORAD_EV_PUM1/NORAD_EV_PUM1.step08_sites.tsv \
  --inputs results/vcf_preprocessed/NORAD_EV_PUM1/NORAD_EV_PUM1.step08_inputs.tsv \
  --summary results/qc/vcf_preprocessing/NORAD_EV_PUM1.step08_summary.tsv \
  --output results/qc/validation/08/NORAD_EV_PUM1.validation.tsv
```

After inspecting the five printed checks, rerun the same command with
`--execute`. Exact checks and limits remain in the
[Step `08` contract](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md#validation-interface).

Runtime requirements:

```text
supported Rscript
VariantAnnotation
GenomicRanges
IRanges
S4Vectors
SummarizedExperiment
GenomeInfoDb
BiocGenerics
rtracklayer
sha256sum or shasum
```

The wrapper does not guess an R module or install packages. Record a supported
cluster executable/environment and pass it explicitly. `Rscript` resolution is
the CLI `--rscript-bin`, then `RSCRIPT_BIN_OVERRIDE`, then `Rscript` on
`PATH`. The R implementation defaults to
`scripts/step_08_vcf_preprocessing.R` and can be overridden with
`--r-script` or `STEP08_R_SCRIPT`.

Before the Step `08` dry-run, prove the exact batch-visible environment:

```bash
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript make real-r-test
```

Both Step `08` and Step `09` real-R fixture suites must pass. A missing
runtime/package or a `SKIP` does not satisfy this gate. Execute the command in
an allocated compute-node/batch context; a login-shell pass alone does not
prove batch visibility.

The direct production dry-run below hashes and validates the complete declared
input set. It is an interface/reference command for an allocated compute-node
context, not a login-node command. Use the SLURM dry-run below for cluster
promotion.

Direct dry-run:

```bash
scripts/step_08_vcf_preprocessing.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --rscript-bin /supported/path/to/Rscript
```

Dry-run is the default. It validates and prints the exact declared input set
and R command, invokes no R process, and creates no output directory, lock,
temporary file, or final output.

Only after Step `07` is cluster-proven and the supported R environment and
packages have passed the real-R fixtures, add execute mode:

The direct command below documents the shell interface. Run production-scale
execution through the SLURM wrapper; do not run it on the cluster login node.
Direct execute is limited to an explicitly allocated compute-node context or a
tiny approved fixture.

```bash
scripts/step_08_vcf_preprocessing.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step07-root results/mpileup \
  --annotation-gtf refs/novogene_ref/genome.gtf \
  --output-root results/vcf_preprocessed \
  --qc-root results/qc/vcf_preprocessing \
  --rscript-bin /supported/path/to/Rscript \
  --execute
```

SLURM dry-run:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_08_vcf_preprocessing.slurm
```

SLURM execute, only after the dry-run and prerequisites are inspected:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_08_vcf_preprocessing.slurm
```

Wrapper variables and defaults:

```text
COHORT_ID=NORAD_EV_PUM1
SAMPLE_MANIFEST=samples.tsv
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv
STEP07_ROOT=results/mpileup
ANNOTATION_GTF=refs/novogene_ref/genome.gtf
OUTPUT_ROOT=results/vcf_preprocessed
QC_ROOT=results/qc/vcf_preprocessing
RSCRIPT_BIN_OVERRIDE=<unset; defaults to Rscript on PATH>
STEP08_R_SCRIPT=scripts/step_08_vcf_preprocessing.R
EXECUTE=0
```

The current job requests the `long` partition, eight hours, and one CPU. Those
resources are provisional and have not been cluster-proven. The engine now
makes one additional bounded-memory streaming pass over each VCF before
`VariantAnnotation` parsing. During future runtime promotion, benchmark that
extra I/O on a representative pilot or chromosome-scale input set using an
isolated output namespace, and record input size, elapsed time, and maximum
RSS before relying on the full-universe resource request.

The [functional contract](../../src/norad/stages/preprocess_and_annotate_cohort_candidates/CONTRACT.md)
owns the complete partition/orientation barrier, bounded lexical and semantic
parsing, provisional orientation policy, three-output schemas, transaction
marker, and validator boundary. The policy is compatibility behavior, not a
biologically validated orientation claim.

Validation checklist after a future execute run:

```bash
cohort=NORAD_EV_PUM1
sites="results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv"
inputs="results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv"
summary="results/qc/vcf_preprocessing/$cohort.step08_summary.tsv"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
ls -lh "$sites" "$inputs" "$summary"
head -2 "$sites"
cat "$inputs"
cat "$summary"
```

Use the structured validator above for schemas, identities, ordering,
uniqueness, and count reconciliation. For the approved primary manifest,
additionally require exactly `50` data rows in
`step08_inputs.tsv` (`25` partitions by two orientations) in declared
partition order with `FWD_like` then `REV_like`. Require one
`COMPLETED 0:0` job, inspected logs, all three files, and no owned lock or
run-token scratch residue.

Execute mode owns a cohort lock, uses run-token temporary and backup paths,
validates before publication, and rolls back a prior complete set on failure.
The only valid preexisting state is all three outputs present or all three
absent. Publication order is sites table, summary, then the input receipt last
as the transaction commit marker.

## Step 09: CMH Editing-Site Calling

No Step `09` cluster dry-run, execute job, log, output table, plot, or
biological candidate result has been inspected. Do not runtime-promote this
step before Step `08` is cluster-proven.

Implemented files:

```text
scripts/step_09_cmh_editing_site_calling.sh
scripts/step_09_cmh_editing_site_calling.R
scripts/validate_step_09_cmh_outputs.py
jobs/step_09_cmh_editing_site_calling.slurm
tests/shell/test_step_09_cmh_editing_site_calling.sh
tests/r/run_step_09_cmh_tests.sh
tests/r/test_step_09_cmh_editing_site_calling.R
tests/test_validate_step_09_cmh_outputs.py
configs/step_09_pairs.NORAD_EV_PUM1.tsv
```

The structured Step `09` validator consumes the exact six native outputs and
their explicit Step `08`/manifest inputs without invoking R:

```bash
analysis=NORAD_EV_vs_PUM1
cohort=NORAD_EV_PUM1
analysis_dir="results/editing/$analysis"

.venv/bin/python scripts/validate_step_09_cmh_outputs.py \
  --analysis-id "$analysis" \
  --cohort-id "$cohort" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-sites \
    "results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv" \
  --step08-inputs \
    "results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv" \
  --all-sites "$analysis_dir/$analysis.cmh_all_sites.tsv" \
  --significant-sites "$analysis_dir/$analysis.cmh_significant_sites.tsv" \
  --summary "$analysis_dir/$analysis.cmh_summary.tsv" \
  --mutation-spectrum "$analysis_dir/$analysis.mutation_spectrum.tsv" \
  --mutation-spectrum-pdf "$analysis_dir/$analysis.mutation_spectrum.pdf" \
  --depth-delta-pdf "$analysis_dir/$analysis.depth_delta.pdf" \
  --output "results/qc/validation/09/$analysis.validation.tsv"
```

Dry-run writes no report. Inspect the seven checks and the explicit
non-recomputation limits in the
[`rank_cohort_candidates_with_paired_CMH` contract](../../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/CONTRACT.md#validation-interface),
then create the exact report parent and add `--execute`:

```bash
analysis=NORAD_EV_vs_PUM1
cohort=NORAD_EV_PUM1
analysis_dir="results/editing/$analysis"

mkdir -p results/qc/validation/09
.venv/bin/python scripts/validate_step_09_cmh_outputs.py \
  --analysis-id "$analysis" \
  --cohort-id "$cohort" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-sites \
    "results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv" \
  --step08-inputs \
    "results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv" \
  --all-sites "$analysis_dir/$analysis.cmh_all_sites.tsv" \
  --significant-sites "$analysis_dir/$analysis.cmh_significant_sites.tsv" \
  --summary "$analysis_dir/$analysis.cmh_summary.tsv" \
  --mutation-spectrum "$analysis_dir/$analysis.mutation_spectrum.tsv" \
  --mutation-spectrum-pdf "$analysis_dir/$analysis.mutation_spectrum.pdf" \
  --depth-delta-pdf "$analysis_dir/$analysis.depth_delta.pdf" \
  --output "results/qc/validation/09/$analysis.validation.tsv" \
  --execute
```

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_09_cmh_outputs.py
```

Runtime requirements:

```text
operator-validated Rscript
base R stats, graphics, and grDevices
sha256sum or shasum for the R engine
```

Step `09` does not install R, load a guessed module, or require Bioconductor.
The shell preflight can fall back to `python3` for SHA-256, but execute mode
still requires `sha256sum` or `shasum` because the R engine verifies hashes
independently.
The Step `08` package requirements remain separate. `Rscript` resolution is
CLI `--rscript-bin`, then `RSCRIPT_BIN_OVERRIDE`, then `Rscript` on `PATH`.
The R implementation defaults to the adjacent
`scripts/step_09_cmh_editing_site_calling.R` and may be overridden with
`--r-script` or `STEP09_R_SCRIPT`.

The full sample manifest is the only pairing source. Step `09` requires
`sample_id`, `r1_fastq`, `r2_fastq`, `strandedness`, `condition`, and
`replicate`; `notes` remains optional. Each replicate must contain exactly one
control and one treatment, both conditions must have identical replicate sets,
and at least two strata are required. Pairing is never inferred from names.

The direct production dry-run below parses and validates the production sites
table and receipt. It is an interface/reference command for an allocated
compute-node context, not a login-node command. Use the SLURM dry-run below for
cluster promotion.

Direct dry-run:

```bash
scripts/step_09_cmh_editing_site_calling.sh \
  --analysis-id NORAD_EV_vs_PUM1 \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-root results/vcf_preprocessed \
  --output-root results/editing \
  --rscript-bin /supported/path/to/Rscript
```

Dry-run is the default. It resolves the executable, validates the current
manifest/partition hashes, prints every manifest-defined pair, derives exactly:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
```

and validates the Step `08` sites table plus complete input receipt. This
includes receipt order,
cohort/sample counts, both manifest hashes, `FWD_like` then `REV_like` for
every declared partition, exact manifest-ordered `DP__`, `AD__`, and `AF__`
columns, candidate uniqueness, row counts, count/AF consistency, and
`orientation_policy=legacy_provisional_v1`. Dry-run prints the exact R command
but does not invoke R, acquire a lock, or create an output directory.

Default analysis:

```text
control: EV
treatment: PUM1
RNA change: A>G
minimum per-sample DP: 1
mean analysis DP: strictly >50
BH FDR: strictly <0.05
common OR: strictly >1.2 or <1/1.2
absolute treatment-control fraction difference: strictly >0.005
background condition: disabled
background maximum fraction when enabled: strictly <0.01
```

The optional background condition must differ from control and treatment. EV
must never be repurposed as a missing no-dox cohort.

Only after Step `08` is cluster-proven, the supported R environment passes both
real-R fixture suites, and the Step `09` dry-run is inspected, add execute mode:

The direct command below documents the shell interface. Run production-scale
execution through the SLURM wrapper; do not run it on the cluster login node.
Direct execute is limited to an explicitly allocated compute-node context or a
tiny approved fixture.

```bash
scripts/step_09_cmh_editing_site_calling.sh \
  --analysis-id NORAD_EV_vs_PUM1 \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-root results/vcf_preprocessed \
  --output-root results/editing \
  --rscript-bin /supported/path/to/Rscript \
  --execute
```

SLURM dry-run:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_09_cmh_editing_site_calling.slurm
```

SLURM execute, only after the dry-run and upstream gates are inspected:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,\
RSCRIPT_BIN_OVERRIDE=/supported/path/to/Rscript \
  jobs/step_09_cmh_editing_site_calling.slurm
```

Wrapper variables and defaults:

```text
ANALYSIS_ID=NORAD_EV_vs_PUM1
COHORT_ID=NORAD_EV_PUM1
SAMPLE_MANIFEST=samples.tsv
PARTITION_MANIFEST=configs/step_07_partitions.primary_contigs.tsv
STEP08_ROOT=results/vcf_preprocessed
OUTPUT_ROOT=results/editing
CONTROL_CONDITION=EV
TREATMENT_CONDITION=PUM1
RNA_REF=A
RNA_ALT=G
MIN_SAMPLE_DP=1
MEAN_DP_THRESHOLD=50
FDR_THRESHOLD=0.05
COMMON_OR_THRESHOLD=1.2
ABSOLUTE_DIFFERENCE_THRESHOLD=0.005
BACKGROUND_CONDITION=<empty; disabled>
BACKGROUND_MAX_FRACTION=0.01
RSCRIPT_BIN_OVERRIDE=<unset; defaults to Rscript on PATH>
STEP09_R_SCRIPT=scripts/step_09_cmh_editing_site_calling.R
EXECUTE=0
```

The current job requests the `long` partition, eight hours, and one CPU with no
explicit memory request. Those resources are provisional and have not been
cluster-proven.

For each successfully testable target candidate, the R engine builds
treatment/control by edited/unedited tables for every manifest-defined
replicate and runs two-sided
`mantelhaen.test(..., correct=TRUE, exact=FALSE)`. The common odds ratio is
treatment relative to control. BH is applied once across all successfully
tested target candidates from every partition and orientation before
mean-depth, background, FDR, or effect call filters.

The all-sites table retains non-target, missing-count, low-coverage, and
degenerate candidates. Exact status values are:

```text
test_status:
  not_target_change | missing_counts | low_coverage | degenerate_table | tested
call_status:
  not_tested | below_mean_dp | background_not_passed | fdr_not_met |
  effect_not_met | significant_up | significant_down
background_status:
  disabled | pass | missing_counts | low_coverage | fail_fraction
```

Successful execute mode publishes:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

The all-sites and significant tables have 42 fixed analysis/annotation fields
followed by manifest-ordered `DP__`, `AD__`, and `AF__` groups. The summary has
39 fixed provenance/count/threshold fields. The mutation table always emits
the 12 canonical substitutions. Both plots use a fixed 7-by-5-inch base-R
device, are signature/EOF validated, and include valid empty-input plots.

Validation checklist after a future execute run:

```bash
set -euo pipefail

analysis=NORAD_EV_vs_PUM1
out_dir="results/editing/$analysis"
all="$out_dir/$analysis.cmh_all_sites.tsv"
significant="$out_dir/$analysis.cmh_significant_sites.tsv"
summary="$out_dir/$analysis.cmh_summary.tsv"
spectrum="$out_dir/$analysis.mutation_spectrum.tsv"
spectrum_pdf="$out_dir/$analysis.mutation_spectrum.pdf"
depth_pdf="$out_dir/$analysis.depth_delta.pdf"

sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
ls -lh "$all" "$significant" "$summary" "$spectrum" "$spectrum_pdf" "$depth_pdf"
head -2 "$all"
head -2 "$significant"
cat "$summary"
cat "$spectrum"
test "$(head -c 5 "$spectrum_pdf")" = '%PDF-'
test "$(head -c 5 "$depth_pdf")" = '%PDF-'
tail -c 2048 "$spectrum_pdf" | grep -aFq -- '%%EOF'
tail -c 2048 "$depth_pdf" | grep -aFq -- '%%EOF'
```

Require all six files, exact schemas, a single summary row, 12 mutation rows,
preserved all-sites row order, a deterministic significant subset, reconciled
status/count totals, current input hashes, and `%PDF-` signatures. A
valid PDF must also contain its `%%EOF` marker near the end. A
header-only Step `08` sites table is valid: all-sites and significant remain
header-only, the summary has one row, the spectrum has 12 zero-count rows, and
both PDFs remain valid.

Also require the all-sites data-row count to equal the Step `08` sites data-row
count; significant-sites must be the exact ordered subset with
`significant_up` or `significant_down`; summary status totals and upstream
manifest/input hashes must reconcile; the default run must record background
disabled; the job must be `COMPLETED 0:0`; and no owned lock or run-token
scratch residue may remain.

Assert the row-count and exact-subset contract:

For production tables, run this full-table scan inside an allocated
compute-node/batch context, not on the login node.

```bash
set -euo pipefail

analysis=NORAD_EV_vs_PUM1
out_dir="results/editing/$analysis"
all="$out_dir/$analysis.cmh_all_sites.tsv"
significant="$out_dir/$analysis.cmh_significant_sites.tsv"
summary="$out_dir/$analysis.cmh_summary.tsv"
spectrum="$out_dir/$analysis.mutation_spectrum.tsv"
step08_sites="results/vcf_preprocessed/NORAD_EV_PUM1/NORAD_EV_PUM1.step08_sites.tsv"
step08_rows=$(awk 'END { print NR - 1 }' "$step08_sites")
all_rows=$(awk 'END { print NR - 1 }' "$all")
summary_rows=$(awk 'END { print NR - 1 }' "$summary")
spectrum_rows=$(awk 'END { print NR - 1 }' "$spectrum")

[[ "$all_rows" -eq "$step08_rows" ]]
[[ "$summary_rows" -eq 1 ]]
[[ "$spectrum_rows" -eq 12 ]]

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

The `diff` must be empty with exit status `0`. These checks supplement, rather
than replace, schema, hash, status-total, PDF, scheduler, log, lock, and scratch
inspection.

Execute mode atomically acquires:

```text
results/editing/<analysis>/.<analysis>.step09.lock/
```

It uses run-token temporary and backup paths, requires either all six stable
outputs or none, verifies immutable inputs before and after R, validates every
temporary file, publishes five non-summary files, then publishes the summary
last as the transaction commit marker. It revalidates final content and hashes.
A failed replacement restores the previous complete set.

If a foreign lock exists, inspect its `owner` file, SLURM state, logs, stable
outputs, and run-token scratch paths; never delete or adopt it blindly. If
rollback cannot restore a complete state, the script deliberately retains its
owned lock and any recovery evidence. Inspect the reported finals/backups and
perform an explicit operator recovery before another run.

## Post-Step 09: Scientific Validation Gate

Status:

```text
implemented locally at b674a31
Python and shell synthetic-fixture suites pass
production evidence and scientific review remain unavailable
not a rerun of CMH and not a biological interpretation engine
```

Implemented files:

```text
scripts/step_09c_scientific_validation.sh
scripts/step_09c_scientific_validation.py
configs/step_09c_review_plan.example.tsv
configs/step_09c_evidence_manifest.example.tsv
configs/step_09c_evidence_schemas/
tests/fixtures/step09c/build_fixture.py
tests/test_step_09c_scientific_validation.py
tests/shell/test_step_09c_scientific_validation.sh
```

The local dry-run-first Python/shell evidence package has this public
interface:

```bash
scripts/step_09c_scientific_validation.sh \
  --review-id REVIEW_ID \
  --sample-manifest SAMPLE_MANIFEST \
  --partition-manifest PARTITION_MANIFEST \
  --step08-sites STEP08_SITES \
  --step08-inputs STEP08_INPUTS \
  --step08-summary STEP08_SUMMARY \
  --step09-analysis-dir STEP09_ANALYSIS_DIR \
  --review-plan REVIEW_PLAN \
  --evidence-manifest EVIDENCE_MANIFEST \
  --output-root OUTPUT_ROOT

# add --execute only to publish validated evidence records
```

Dry-run validates the complete explicit input contract and prints the
resolved review, inputs, evidence, and output names. It does not create the
output directory, acquire a lock, write scratch paths, or publish stable
files. The tool has no SLURM wrapper and is not a production compute stage.

Execute mode publishes atomically under
`results/scientific_validation/<review_id>/`:

```text
<review_id>.step09c_review_plan.tsv
<review_id>.step09c_evidence_index.tsv
<review_id>.step09c_orientation_locus_audit.tsv
<review_id>.step09c_annotation_audit.tsv
<review_id>.step09c_qc_funnel.tsv
<review_id>.step09c_replicate_effects.tsv
<review_id>.step09c_sensitivity_matrix.tsv
<review_id>.step09c_leave_one_pair_out.tsv
<review_id>.step09c_candidate_selection.tsv
<review_id>.step09c_candidate_adjudication.tsv
<review_id>.step09c_decisions.tsv
<review_id>.step09c_limitations.tsv
<review_id>.step09c_review_summary.tsv
```

The summary is published last as the transaction marker. The package validates
and summarizes explicit evidence; it does not rerun CMH statistics, infer
reviewer decisions, or turn synthetic fixtures into production evidence.
Only schemas, examples, and synthetic fixtures are committed.

Execute-mode publication owns:

```text
results/scientific_validation/<review_id>/.<review_id>.step09c.lock
```

The lock is a regular metadata file created atomically with mode `0600`; it
records `review_id`, PID, run token, and creation date. It is not a lock
directory.

Publication uses run-token temporary and backup directories, validates every
staged TSV, rechecks all explicit input hashes before publication, requires
either all 13 stable outputs or none, backs up the previous complete set,
publishes the review summary last, and rolls back on failure. An incomplete
rollback retains the lock and recovery paths and attempts to write this
best-effort marker:

```text
results/scientific_validation/<review_id>/.<review_id>.step09c.<run_token>.RECOVERY.txt
```

A cleanup failure is reported with the owned paths that could not be removed;
it does not guarantee that the lock or any other recovery path remains. Never
infer a clean transaction from either error.

Keep these status dimensions independent:

```text
computational status:
  implementation / local tests / runtime blocking /
  cluster dry-run / cluster proof

overall science status:
  evidence_incomplete
  science_review_complete_exploratory

evidence category:
  missing / incomplete / complete / justified not_applicable

orientation:
  provisional / validated / replacement_required
```

`biological_interpretation_ready` is reserved and Step `09c` must reject it
until a separately approved policy branch unlocks explicit exit criteria.
Background, matched-DNA, orthogonal-evidence, annotation, threshold, and
adjudication decisions remain separate explicit dimensions.

Contract details tightened with the run-summary implementation:

* reviewer, decision-owner, and evidence-owner names retain human-readable
  text; machine IDs and policy versions remain safe IDs;
* complete or incomplete source evidence requires a date; source-free
  missing/not-applicable TSV rows use `NA` (or a valid date), and v1.1 JSON
  normalization maps `NA` to `null`;
* primary, superseded, and sensitivity analysis sets are disjoint, and each
  evidence category must use its declared analysis role;
* pending decisions cannot cite support; recorded decisions require complete
  or justified-not-applicable support; rerun booleans and scopes must agree;
* passed/failed/proven computational claims require their defined complete
  evidence roles; runtime and cluster roles additionally require explicit
  underlying paths/hashes; blocked/not-run states are not proof and must not
  receive invented claim evidence.

The tracked example review plan declares `local_test_status=not_run` because
it attaches no computational evidence. That review declaration is separate
from the repository's passing Step `09c` fixture tests; do not change a
review-plan status to match repository CI unless the matching evidence is
actually declared.

Review:

* library protocol, RSeQC, read flags, transcript strand, genomic/RNA alleles,
  and raw counts at predeclared plus-strand and minus-strand transcript loci
  under both current and inverted normalization policies;
* Novogene GTF path/identity/SHA-256 and delivery provenance, with exact
  release recorded if recoverable or explicitly accepted as unresolved, plus
  predeclared CDS, UTR, exon, intron, intergenic, overlap, and
  multi-transcript annotation semantics;
* the Step `07` -> Step `08` -> Step `09` count/status funnel by partition and
  orientation, mutation spectrum, orientation balance, and per-sample DP/AF;
* predeclared threshold sensitivity under distinct non-overwriting analysis
  IDs, per-replicate AF/delta,
  leave-one-pair-out behavior, the unweighted mean-sample-AF metric,
  replicate-direction discordance, `ABE_EV_2`, and replicate `4` duplication;
* deterministic top, discordant, and near-threshold candidate quality,
  bias, splice/repeat/multimapping/duplicate/indel, annotation, and
  polymorphism evidence;
* whether an eligible distinct background cohort exists and whether the
  strict all-sample `<0.01` rule is intended. Never use EV as no-dox.

Before inspecting concordance or rankings, freeze deterministic
locus/candidate selection, sample size, both orientations and plus/minus
transcript-strand coverage, sensitivity grid/decision thresholds, input
hashes, git commit, commands/scripts/software versions, reviewer/date/decision
owner, and current/superseded analysis IDs. Every sensitivity run preserves
the primary transaction; a testability/family change recomputes BH.

Record compact evidence tables, paths, hashes, reviewers, limitations,
matched-DNA availability, and decisions. A>G enrichment is supportive but does
not independently validate orientation. Candidate review/PI approval is not
orthogonal experimental validation. Close as
`science_review_complete_exploratory` when review is complete but results
remain provisional. Do not emit `biological_interpretation_ready` under the
current policy.

Keep production-derived audit/adjudication tables in approved results storage.
Commit only compact non-sensitive summaries, paths, hashes, and decisions
unless explicit approval permits tracking a safe fixture; never add full
biological result snapshots by default.

Local fixture gate:

```bash
.venv/bin/python -m pytest -q tests/test_step_09c_scientific_validation.py
bash tests/shell/test_step_09c_scientific_validation.sh
```

The active fixtures cover exact 13-file publication, side-effect-free dry-run,
incomplete and exploratory evidence, reserved-state rejection, unrelated-file
immunity, hash mutation, locks, cleanup, and rollback. A local fixture pass
means implemented and fixture-tested only. It does not establish a production
review, scheduler/runtime evidence, cluster proof, or biological readiness.

Rerun matrix:

```text
manifest / partition universe -> gated config/evidence package, then Steps 07-09
Step 07 filter / maximum depth
  -> contract/versioning decision plus distinct namespace or added provenance,
     then Steps 07-09
new background samples -> prove Steps 01-06 inputs, then Steps 07-09
background already in unchanged Step 08 columns -> new Step 09 analysis ID
GTF input -> Steps 08-09
orientation normalization policy
  -> Steps 08-09 contract/code/tests/docpatch, then Steps 08-09 runtime
supported Step 09 target / unchanged-manifest contrast or background /
  min-DP / defaults
  -> new analysis ID and recomputed BH over the applicable full family
CMH method/correction or testability logic
  -> Step 09 implementation/tests/docpatch, then new-ID runtime validation
FASTA or coordinates -> upstream reference/alignment impact review
manual adjudication labels -> no compute rerun
new automated filter -> separate implementation/test/docpatch package
```

## Temporary Java Workaround

Node-specific Java evidence is mixed: `node002` has Java 17 and worked for the GATK/bcftools probe, `node003` previously worked with Java 17 for Step `04`, and `node007` previously exposed Java 11 / a missing Java 17 path.

Do not:

* embed `node003` as a permanent default in the SLURM script
* describe node pinning as a pipeline architecture requirement
* assume any single working node will remain the long-term solution
* recommend copying a JDK from the head node or another compute node

Scripts should continue logging and validating the actual Java runtime instead of trusting module names or `JAVA_HOME` alone. The durable action is to report or clarify the inconsistent Java 17 installation with CSU HPC and identify a supported cluster-wide Java 17 executable or installation path.

## Reference Workflow Alignment

The uploaded/reference workflow sequence is:

```text
STAR alignment
-> MarkDuplicates
-> SplitNCigarReads
-> split BAM by read orientation
-> bcftools mpileup
-> VCF preprocessing
-> CMH editing-site calling
```

This repo is rebuilding that workflow in a cleaner SLURM/script/testable structure.
