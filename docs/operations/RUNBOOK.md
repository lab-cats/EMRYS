# Runbook

Operational guide for the NORAD / Novogene Remora RNA-seq pipeline.

This project is developed locally and executed at full scale on the CSU SLURM cluster.

Core workflow rule:

```text
create stage branch from latest clean docpatched predecessor
-> implement only that stage
-> focused and complete local validation
-> implementation commit
-> reread required docs and repository-wide docpatch
-> documentation-only commit
-> clean status/history and push
-> create the next descendant stage branch
```

Cluster promotion is a later upstream-sequential gate: pull the completed branch, dry-run, execute the approved scope, inspect scheduler/log/output evidence, and docpatch that evidence before promoting the next step. Do not skip gates. Do not run scaffolded future jobs. Keep the pipeline boring.

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

Step `05` is cluster-proven across all six samples after final split-N-cigar BAM/BAI validation.

6. Show the dry-run/execute gate:

```bash
grep -n "EXECUTE\|--execute\|dry-run" \
  jobs/step_05_split_n_cigar_reads.slurm \
  scripts/step_05_split_n_cigar_reads.sh | head -60
```

Step `07` source and mocked local-test evidence may be inspected during the
demo, but do not claim or demonstrate real Step `07` VCFs because no cluster
run has been validated. Step `08` and Step `09` source and fake-R wrapper tests
may also be inspected. Their real-R suites now execute locally without `SKIP`,
and pass with synthetic fixtures. Neither step has production or cluster
output evidence. Step `09c` source, dry-run output, example contracts, and
synthetic Python/shell fixtures may also be inspected. Do not present its
fixture transaction as a production scientific review or demonstrate Step
`09` as a biological result. The implemented `artifact-schema-v1` schemas,
explicit synthetic inventory, read-only validator, and focused tests may also
be shown. The implemented `artifact-adapters-v1` help text, dry-run, and
synthetic focused tests may also be shown, but not as a production artifact
index. The implemented `artifact-run-summary` help text, side-effect-free
dry-run, and synthetic four-file fixture transaction may also be shown. The
implemented report-bundle help text, side-effect-free dry-run, pinned Quarto
restore receipt, synthetic HTML/PDF/summary-TSV/receipt transaction, and exact
report-table approval producer contract may be shown, but not as a production
report or scientific approval. The runtime-preflight help text, tracked
example profile, local dry-run, and focused tests may also be shown, but not as
a CSU batch report or runtime proof. No production run summary, approval
manifest, report, or batch preflight exists, and none of these packages is
production-output, cluster, or scientific evidence.

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

## Local Validation Gate

Run from the local repo root before each implementation or documentation commit:

```bash
cd /Users/elisteiger/dev/norad

git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
.venv/bin/python -m compileall scripts tests
.venv/bin/python -m pytest
make shell-test
RSCRIPT_BIN=/usr/local/bin/Rscript make r-check
RSCRIPT_BIN=/usr/local/bin/Rscript make local-real-r-test
make report-test
git status --short
git diff --name-status
```

The complete local gate uses `make local-real-r-test`, which opts into the
repository-local R library through the guarded environment below. Bare
`make real-r-test` is an ambient-runtime diagnostic: when `Rscript` is absent,
each runner reports `SKIP`, and when ambient Step `08` packages are absent it
fails. Neither a skip nor an ambient failure replaces the guarded semantic
gate. An explicit bad override fails; Step `09` itself uses base R only.

Commit implementation/tests first. Then reread the required project documents,
perform the repository-wide documentation consistency pass, rerun this gate,
and make the separate documentation-only commit. A documentation-only package
runs the gate and uses one documentation commit. Require a clean worktree and
inspect history before pushing or creating the next descendant stage branch.

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
# after the required document reread and repository-wide docpatch:
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

Job:

```bash
jobs/step_00a_build_novogene_star_index.slurm
```

Output:

```bash
refs/novogene_star_index/
```

STAR index was built with:

```text
sjdbOverhang=149
```

because reads are 150 bp.

Status:

```text
cluster-proven
```

The structured Step `00a` validator is separate from the historical proof. It
reads one explicit STAR index, FASTA, GTF, path-resolution base, expected
overhang, and scope ID:

```bash
.venv/bin/python scripts/validate_step_00a_star_index.py \
  --scope-id novogene_ref \
  --index-dir refs/novogene_star_index \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --parameter-path-base . \
  --expected-sjdb-overhang 149 \
  --output results/qc/validation/00a/novogene_ref.validation.tsv
```

Dry-run prints five checks without writing: all 15 required STAR members,
`genomeFastaFiles` identity, `sjdbGTFfile` identity, exact ordered FASTA/index
contig names and lengths, and `sjdbOverhang`. Relative paths recorded in
`genomeParameters.txt` resolve only against the explicit
`--parameter-path-base`.

After inspection, create the exact parent and add `--execute`:

```bash
mkdir -p results/qc/validation/00a
.venv/bin/python scripts/validate_step_00a_star_index.py \
  --scope-id novogene_ref \
  --index-dir refs/novogene_star_index \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --parameter-path-base . \
  --expected-sjdb-overhang 149 \
  --output results/qc/validation/00a/novogene_ref.validation.tsv \
  --execute
```

The exact seven-column report is read-only and deterministic. Check failures
are published as evidence; command success means validation and optional
publication completed, not that every check passed. Publication requires an
existing real parent, validates any predecessor, uses an owned lock and
run-token staging/backup paths, rechecks inputs, and rolls back replacement
failure. The `step00a_validation_report_v1` adapter preserves a failed check as
a failed artifact/scope in the canonical summary and consolidated reports; it
does not alter historical cluster status.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_00a_star_index.py
```

### Step 00b: GTF To BED12

Script:

```bash
scripts/gtf_to_bed12.py
```

Job:

```bash
jobs/step_00b_gtf_to_bed12.slurm
```

Outputs:

```bash
refs/novogene_ref/genome.unsorted.bed
refs/novogene_ref/genome.bed
```

Validated output:

```text
206,601 BED12 transcript records
```

Status:

```text
cluster-proven
```

The structured Step `00b` validator reads one explicit BED12 and source GTF:

```bash
.venv/bin/python scripts/validate_step_00b_bed12.py \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv
```

Dry-run reports exact 12-column structure, deterministic coordinate sorting,
block geometry, transcript-name uniqueness, and byte-for-byte agreement with
the deterministic exon normalization performed by `gtf_to_bed12.py`. It does
not create an output path. After inspection, create the parent and add
`--execute`:

```bash
mkdir -p results/qc/validation/00b
.venv/bin/python scripts/validate_step_00b_bed12.py \
  --scope-id novogene_ref \
  --bed12 refs/novogene_ref/genome.bed \
  --source-gtf refs/novogene_ref/genome.gtf \
  --output results/qc/validation/00b/novogene_ref.validation.tsv \
  --execute
```

The validator never rewrites the BED or GTF. Check failures remain explicit
evidence, and the `step00b_validation_report_v1` adapter carries the resulting
failed scope into the canonical summary and HTML/PDF reports without changing
historical cluster state. Publication uses the same exact output-name,
predecessor-validation, lock, stable-input, staging, backup, and rollback
contract as Step `00a`.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_00b_bed12.py
```

### Step 00c: GATK Reference Sidecars

Script:

```bash
scripts/step_00c_prepare_gatk_reference.sh
```

Job:

```bash
jobs/step_00c_prepare_gatk_reference.slurm
```

Purpose:

```text
Create and validate the FASTA index and sequence dictionary required by GATK.
```

Expected outputs:

```bash
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.dict
```

Expected validation evidence:

```text
Ad hoc sidecar prep completed with exit code 0:0.
FAI contigs: 194
DICT contigs: 194
BAM header contigs: 194
Reference/BAM SQ check: PASS
```

Dry-run:

```bash
sbatch jobs/step_00c_prepare_gatk_reference.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/step_00c_prepare_gatk_reference.slurm
```

Direct script dry-run with explicit cluster tools:

```bash
scripts/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
```

Direct script execute with explicit cluster tools:

```bash
scripts/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --execute
```

Status:

```text
cluster-proven
```

Step `00c` formalizes the prep required before Step `05` execute-mode validation. It is dry-run by default, uses a reference-level lock in execute mode, reuses valid existing sidecars, generates only missing sidecars, and validates `.fai`/`.dict` contig-name and length agreement. Step `05` treats these files as prerequisites, fails clearly if they are missing, and must not silently create shared reference sidecars inside per-sample jobs.

The structured Step `00c` validator reads one explicit FASTA and its exact FAI
and DICT sidecars:

```bash
.venv/bin/python scripts/validate_step_00c_reference_sidecars.py \
  --scope-id novogene_ref \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --output results/qc/validation/00c/novogene_ref.validation.tsv
```

Dry-run validates FASTA, FAI, and DICT structure and exact ordered contig-name
and length agreement without creating output. After inspection, create the
parent and add `--execute`:

```bash
mkdir -p results/qc/validation/00c
.venv/bin/python scripts/validate_step_00c_reference_sidecars.py \
  --scope-id novogene_ref \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --output results/qc/validation/00c/novogene_ref.validation.tsv \
  --execute
```

The validator is read-only. Failed checks remain explicit evidence, and the
`step00c_validation_report_v1` adapter propagates the failed scope into the
canonical summary and HTML/PDF reports without changing historical cluster
state. Publication uses the same predecessor-validation, owned-lock,
stable-input, staging, backup, and rollback contract as Steps `00a` and `00b`.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_00c_reference_sidecars.py
```

## Step 01: STAR Alignment

Script:

```bash
scripts/step_01_star_align.sh
```

Job:

```bash
jobs/step_01_star_align.slurm
```

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

Status:

```text
complete and cluster-proven across all six samples
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
.venv/bin/python scripts/validate_step_01_star_alignment.py \
  --scope-id ABE_EV_2 \
  --bam results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --log-final results/star/ABE_EV_2/ABE_EV_2.Log.final.out \
  --log-out results/star/ABE_EV_2/ABE_EV_2.Log.out \
  --log-progress results/star/ABE_EV_2/ABE_EV_2.Log.progress.out \
  --sj-out results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab \
  --output results/qc/validation/01/ABE_EV_2.validation.tsv
```

Dry-run verifies that every explicit output is nonempty, checks the BAM/BGZF
container signature, parses unique `Log.final.out` key/value rows, requires
the unique/multimapping/too-many-loci percentages to be valid values from zero
through 100, and validates every nonempty splice-junction row as nine columns
with valid coordinates and counts. It creates no report. After inspection,
create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/01
.venv/bin/python scripts/validate_step_01_star_alignment.py \
  --scope-id ABE_EV_2 \
  --bam results/star/ABE_EV_2/ABE_EV_2.Aligned.sortedByCoord.out.bam \
  --log-final results/star/ABE_EV_2/ABE_EV_2.Log.final.out \
  --log-out results/star/ABE_EV_2/ABE_EV_2.Log.out \
  --log-progress results/star/ABE_EV_2/ABE_EV_2.Log.progress.out \
  --sj-out results/star/ABE_EV_2/ABE_EV_2.SJ.out.tab \
  --output results/qc/validation/01/ABE_EV_2.validation.tsv \
  --execute
```

Failed checks remain report evidence. The `step01_validation_report_v1`
adapter carries the sample scope into canonical summaries and HTML/PDF reports
without changing historical cluster state. The validator never runs STAR or
modifies its outputs.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_01_star_alignment.py
```

## Step 02: Canonical Sort, Read-Group Tagging, And BAM Indexing

Script:

```bash
scripts/step_02_sort_index_bam.sh
```

Job:

```bash
jobs/step_02_sort_index_bam.slurm
```

Status:

```text
hardened and cluster-proven across all six samples
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
.venv/bin/python scripts/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv
```

Dry-run checks BAM/BAI container signatures, `samtools quickcheck -v`, one
coordinate-sorted `@HD`, one sample-matching `@RG` with both `ID` and `SM`,
and equality between all alignment records and records carrying the matching
RG tag. It does not create a report. After inspection, create the parent and
add `--execute`:

```bash
mkdir -p results/qc/validation/02
.venv/bin/python scripts/validate_step_02_canonical_bam.py \
  --scope-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --bai results/bam/ABE_EV_2/ABE_EV_2.sorted.bam.bai \
  --samtools-bin /explicit/path/to/samtools \
  --output results/qc/validation/02/ABE_EV_2.validation.tsv \
  --execute
```

The validator never sorts, indexes, or edits alignments. Its
`step02_validation_report_v1` adapter carries pass/fail evidence into the
canonical summary and consolidated reports without changing historical
cluster state.

Focused validation:

```bash
.venv/bin/python -m pytest -q tests/test_validate_step_02_canonical_bam.py
```

Dry-run:

```bash
sbatch jobs/step_02_sort_index_bam.slurm
```

Execute:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 \
  jobs/step_02_sort_index_bam.slurm
```

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

Publication uses rollback protection, but the BAM/BAI pair is not a single indivisible atomic operation. If a failure occurs after backups begin, Step `02` restores the previous complete canonical pair. If no prior pair existed, it removes any partially published canonical outputs.

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

Status:

```text
implemented and refreshed across all six final hardened Step 02 BAMs
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

Dry-run requires the exact quickcheck PASS marker, unique flagstat total and
mapped rows, nonnegative combined QC-passed/QC-failed counts, and
`mapped <= total`. It does not invoke samtools or create a report. After
inspection, create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/02b
.venv/bin/python scripts/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv \
  --execute
```

The `step02b_validation_report_v1` adapter propagates this persisted evidence
without rerunning QC or changing historical cluster state.

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
scripts/step_03_infer_strandedness_and_orientation.sh
```

Job:

```bash
jobs/step_03_infer_strandedness_and_orientation.slurm
```

Status:

```text
cluster-proven across all six samples
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

Dry-run requires exactly one finite value from zero through one for the
failed-to-determine fraction and each of RSeQC's two paired-orientation
labels. It requires their sum to equal one within the explicit default
tolerance of `0.001`. It preserves the mechanical labels and does not infer a
biological strand. After inspection, create the parent and add `--execute`:

```bash
mkdir -p results/qc/validation/03
.venv/bin/python scripts/validate_step_03_rseqc_orientation.py \
  --scope-id ABE_EV_2 \
  --infer-report results/qc/strandedness/ABE_EV_2.infer_experiment.txt \
  --output results/qc/validation/03/ABE_EV_2.validation.tsv \
  --execute
```

The `step03_validation_report_v1` adapter propagates the explicit evidence
without rerunning RSeQC or changing historical cluster/biological state.

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
scripts/step_04_mark_duplicates.sh
```

Job:

```bash
jobs/step_04_mark_duplicates.slurm
```

Status:

```text
cluster-proven across all six samples
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

Dry-run checks BAM/BAI container signatures, quickcheck, coordinate sort
order, one preserved sample-matching read group, and exactly one Picard metrics
row with nonnegative examined pairs, duplicate pairs no greater than examined,
and a finite duplication fraction from zero through one. After inspection,
create the output parent and add `--execute`:

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

The validator does not mark/remove duplicates or modify the BAM pair. The
`step04_validation_report_v1` adapter propagates explicit evidence without
changing historical cluster or scientific state.

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

Status:

```text
implemented and cluster-proven across all six samples
```

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

Dry-run checks BAM/BAI containers, quickcheck, coordinate sorting, preserved
sample read group, and exact ordered FASTA/FAI/DICT contig-name/length
agreement. After inspection, create the parent and add `--execute`:

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

The validator never invokes GATK, repairs reference sidecars, or modifies the
BAM pair. Its `step05_validation_report_v1` adapter propagates only the
declared evidence.

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
scripts/step_05_split_n_cigar_reads.sh \
  --sample-id ABE_EV_2 \
  --input-bam results/markdup/ABE_EV_2/ABE_EV_2.markdup.bam \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-dir results/split_ncigar/ABE_EV_2 \
  --gatk-bin /cm/shared/apps/gatk/gatk-4.6.1.0/gatk \
  --samtools-bin /cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools
```

Direct script execute with explicit cluster tools:

```bash
scripts/step_05_split_n_cigar_reads.sh \
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

Status:

```text
cluster-proven across all six samples
```

Entry points:

```text
jobs/step_06_split_bam_by_read_orientation.slurm
scripts/step_06_split_bam_by_read_orientation.sh
tests/shell/test_step_06_split_bam_by_read_orientation.sh
```

Old reference workflow used samtools flags similar to:

```text
FWD_like = samtools -f 99 plus samtools -f 147
REV_like = samtools -f 83 plus samtools -f 163
```

These are mechanical read-orientation flag groups. `samtools view -f FLAG` means a read has all bits in `FLAG`; it is not exact flag equality. Do not assume `FWD_like` / `REV_like` labels directly equal biological sense/antisense.

Step `06` consumes the Step `05` output contract:

```text
results/split_ncigar/<sample>/<sample>.split_ncigar.bam
results/split_ncigar/<sample>/<sample>.split_ncigar.bam.bai
```

Expected output contract:

```text
results/orientation/<sample>/<sample>.FWD_like.bam
results/orientation/<sample>/<sample>.FWD_like.bam.bai
results/orientation/<sample>/<sample>.REV_like.bam
results/orientation/<sample>/<sample>.REV_like.bam.bai
results/qc/orientation/<sample>.orientation_counts.tsv
```

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

The counts TSV includes `input_records`, per-flag counts for `99`, `147`, `83`, and `163`, merged `fwd_like_records` and `rev_like_records`, `assigned_records`, `unassigned_records`, and `assigned_fraction`.

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

After inspecting the five printed checks, publish with the same command plus
`--execute`. The validator reads only the declared two BAM/BAI pairs and
counts TSV. It checks container signatures, the exact one-row counts contract,
the `99 + 147` and `83 + 163` mechanical group sums, assigned/unassigned
arithmetic, and the recorded assigned fraction. It never invokes samtools,
splits reads, creates indexes, changes orientation labels, or promotes local
evidence to runtime, cluster, scientific, or biological status.

All six Step `06` jobs completed `0:0`; `FWD_like` / `REV_like` BAM+BAI outputs were published for all six samples; `samtools quickcheck` passed silently; orientation counts TSVs were present; `assigned_fraction = 1.000000` and `unassigned_records = 0` for all six samples; and no Step `06` scratch files remained.

## Step 07: bcftools mpileup

Status:

```text
implemented locally
locally tested with mocked bcftools
real-bcftools runtime and cluster validation pending
not cluster-proven
```

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

After inspecting the five printed checks, publish with the same command plus
`--execute`. The validator reads only the declared manifests, FAI, two VCFs,
and receipt. It reconciles receipt structure, VCF sample columns, selector
membership, manifest hashes/order, paths, and record counts without invoking
bcftools or promoting real-runtime or cluster state.

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

After inspecting the five printed checks, publish with the same command plus
`--execute`. The validator uses the existing Step `08` semantic contracts to
reconcile exact headers, manifest and annotation identity, ordered
partition-orientation inputs, candidate uniqueness/sample fields, AF/count
arithmetic, and the one-row summary. It never invokes R, discovers Step `07`
inputs, changes native outputs, or promotes runtime, cluster, scientific, or
biological state.

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

Step `08` constructs the exact partition-manifest cross-product with
`FWD_like` and `REV_like`; it never globs VCFs. It requires each partition's
Step `07` receipt and named two-orientation VCF pair, validates receipt/VCF
paths and SHA-256 hashes, declared/observed record counts, both manifest
hashes, and exact sample-manifest VCF column order. It also rejects overlapping
partition selectors, duplicate partition-independent candidate IDs, and
inputs that change during the run.

Before semantic VCF parsing, the R implementation streams the raw records in
bounded chunks and validates the lexical values and expected widths of every
consumed `FORMAT/DP`, `FORMAT/AD`, and present `INFO/AD` field. This prevents a
malformed token from being coerced into a parsed numeric value by
`VariantAnnotation`. An AD value may be a single `.` when the whole vector is
missing; otherwise its width must equal REF plus every ALT.
The semantic parse then expands multiallelic records by ALT index, extracts the
matching alternate AD, counts and excludes symbolic and non-SNV alleles, and
fails on missing FORMAT/INFO definitions, malformed or negative counts,
one-sided missing DP/AD, AD greater than DP, or sample/count inconsistencies.
Partition-overlap rejection was already correct and its fixture now asserts
the expected failure reason. Header-only VCFs remain valid when their receipts
and zero counts reconcile.

The provisional mapping is:

```text
orientation_policy=legacy_provisional_v1
FWD_like -> legacy neg -> compatible + transcripts -> complement genomic REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain genomic REF/ALT
```

This is legacy compatibility behavior, not a biologically validated
orientation policy.

Successful execute mode publishes:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The sites table has fixed genomic/RNA/annotation metadata followed by
manifest-ordered `DP__<sample>`, `AD__<sample>`, and `AF__<sample>` columns.
The input receipt has one row per declared partition/orientation, in partition
manifest order with `FWD_like` then `REV_like`, and records input hashes and
observed/supported/skipped/published counts. The summary reconciles those
counts across the cohort.

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

Require all three outputs, exact schemas, the declared number/order of receipt
rows, correct sample column groups, stable hashes, globally unique candidate
IDs, and the invariants:

```text
observed ALT = supported SNV + skipped symbolic + skipped non-SNV
published candidate count = supported SNV count
each summary allele/count total = the matching input-receipt column sum
summary published candidate count = sites-table row count
```

For the approved primary manifest, require exactly `50` data rows in
`step08_inputs.tsv` (`25` partitions by two orientations) in declared
partition order with `FWD_like` then `REV_like`. Require one
`COMPLETED 0:0` job, inspected logs, all three files, and no owned lock or
run-token scratch residue.

Assert the exact partition/orientation sequence:

```bash
awk -F '\t' '
    FNR == NR {
        if (FNR > 1) {
            partition[++partition_count] = $1
        }
        next
    }
    FNR == 1 {
        for (i = 1; i <= NF; i++) {
            if ($i == "partition_id") partition_column = i
            if ($i == "orientation") orientation_column = i
        }
        if (!partition_column || !orientation_column) exit 1
        next
    }
    {
        row = FNR - 1
        expected_partition = partition[int((row + 1) / 2)]
        expected_orientation = (row % 2 ? "FWD_like" : "REV_like")
        if ($partition_column != expected_partition ||
            $orientation_column != expected_orientation) exit 1
    }
    END {
        if (partition_count != 25 || row != 50) exit 1
        print "step08_input_rows=" row
    }
' configs/step_07_partitions.primary_contigs.tsv "$inputs"
```

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

Dry-run snapshots every declared regular non-symlink input and prints seven
checks without writing. It verifies four exact TSV headers; six
analysis-bound basenames under one parent and six distinct physical files;
safe analysis/cohort identity and `legacy_provisional_v1`; the complete
ordered Step `08` candidate universe; target/test/call, depth, AF, and
enabled-background semantics recomputed from immutable counts; type/range
validation of the reported CMH fields; global BH recomputation from reported
p-values; the exact significant subset; summary paths/hashes/pairings/counts;
the canonical 12-SNV spectrum; and both PDF containers. It does not
independently recompute the CMH statistic, p-value, common odds ratio, or
count-table estimability from DP/AD counts.

After inspecting every row, create the exact report parent and add
`--execute`:

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

Readable semantic disagreements publish `status=fail` evidence and retain a
zero command exit when publication succeeds. Missing, empty, symlinked, or
nonregular inputs and unsafe publication state fail closed without a report.
The `step09_validation_report_v1` adapter carries the seven rows into the
canonical summary and consolidated HTML/PDF reports without changing native
outputs or promoting runtime, cluster, scientific, or biological state.

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
