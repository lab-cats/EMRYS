# Run-coordinator intake contract

This private application owner connects the scientist-facing Project model to
immutable Run planning, direct or whole-Run Slurm execution, Attempt lifecycle,
inspection, recovery, Results, and reporting. Scientific algorithms, native
artifact publication, validation meaning, report rendering, dependency solving,
and package installation remain with their owners. The
[current architecture](../../../../docs/architecture/ARCHITECTURE.md) defines
responsibility layers; the [runbook](../../../../docs/operations/RUNBOOK.md)
owns operator instructions; and the
[logging contract](../../../../docs/design/LOGGING_CONTRACT.md) owns application
log semantics.

## Public model and admission

The public model is `Project -> named Analysis -> immutable Run -> Results`:

- The authored `project.yaml` is mutable input. Admission snapshots its exact
  bytes and referenced manifests, normalizes scientific content, and produces
  immutable Project and Analysis revisions.
- An Analysis names one admitted scientific comparison and module
  configuration. Its map key is a human selector and Attempt metadata, not
  content-derived identity.
- A Run immutably binds one Analysis revision and one Execution Plan. Changing
  scientific intent or planned tasks creates another Run.
- Each execution or resume creates a new Attempt. It cannot mutate the Run.
- Results are the admitted final scientific artifacts beneath that Run.
  Reporting is a downstream transaction, not a scientific stage or completion
  authority.

Ordinary Project-aware commands derive the exact current directory's
`project.yaml`. Optional `--project` accepts one named Project directory or an
exact `project.yaml`; no parent-directory or global lookup occurs. The file's
parent is the Project root. Active commands reject request-v3; its closed
schema survives only to read exact historical Runs.

Admission uses a closed safe YAML loader, resolves paths against the Project
root, and binds regular non-symlink file bytes through descriptor/path identity
checks before and after reading. Duplicate keys, custom tags, merge keys,
globs, templates, environment/home interpolation, unknown fields, and ambiguous
paths fail. Shared Dataset and Reference inputs are admitted once; each named
Analysis separately binds its partition, comparison, target, thresholds, and
selected installed providers. Omitted Analysis selection is valid only when
the Project contains exactly one Analysis.

Run selectors accept the deterministic two-word human name, full Run ID, or a
unique ID prefix. With no selector, the sole Run is selected; an interactive
terminal offers an exact choice when several exist. Automation must provide an
unambiguous selector. EMRYS never infers the latest Run. The human name is
presentation only; the content-derived Run ID remains authority.

## No-write and publication boundaries

`emrys init PROJECT_NAME` is dry-run-first and publishes only with `--execute`
into an absent child of the current canonical writable/searchable directory.
It validates referenced inputs without copying them, creates Project-owned
`runs/`, `logs/`, `runtime/`, and `runtime/profiles/` with mode `0700`, and
publishes `project.yaml` last. Failure preserves the partial root and never
overwrites or adopts it. Success re-admits the published tree's exact types,
modes, sizes, and bytes.

`emrys validate` re-admits every selected Analysis and its reference,
annotation, sample, and partition compatibility. It invokes no external tool
and writes nothing. Runtime discovery is also dry-run-first; publication writes
one create-absent `<project-root>/runtime/runtime.tsv`. Doctor diagnosis and
repair follow the durable boundaries in
[`execution-evidence-and-reporting.md`](../../../../docs/design/decisions/execution-evidence-and-reporting.md):
diagnosis is read-only, while confirmed repair mutates only declared
EMRYS-owned locations through existing package managers and requalifies.

For direct placement, `run` and `resume` construct and display one frozen plan,
then ask once before executing that same object. Refusal, EOF, interruption, or
noninteractive omission of `--execute` writes nothing, submits nothing, and
opens no application log. `--execute` is the explicit automation path.

For Slurm placement, the terminal instead confirms one frozen submission plan
before its single `sbatch` call. Submission owns no Run attempt or application
log. Ambient `SBATCH_*` and private transport variables are removed; omitted
site fields remain site policy rather than being fabricated. The private
compute delegate validates its exact profile binding,
submitter identity, and positive scheduler job ID inside the allocation before
module, scratch, Doctor, or workflow work. It uses one owned scratch directory,
removes it on exit, loads only an explicitly admitted module
initializer/roster, and delegates to the same grouped Run path. Scheduler
streams and job identity are operational provenance, never scientific or
completion authority.

## Profiles and immutable planning

`run` and `resume` accept at most one closed
`emrys.execution-profile.v1` fragment:

- omission reads `<project-root>/runtime/profiles/default.yaml`;
- `--profile NAME` reads exactly
  `<project-root>/runtime/profiles/NAME.yaml`; and
- an absolute `--profile PATH` reads that exact file.

There is no site/global registry or profile scan. Resource CLI values have
highest precedence. Placement is Attempt-local provenance; the admitted
scientific computation and task roster remain Run authority.

Planning composes the fixed common processing profile with the selected
analysis provider's admitted task tail, declared inputs/outputs, validation
reports, resources, and reporting projection. It materializes one immutable
dispatch per task and invokes the sole source-bound Snakemake backend. The
public surface exposes no raw engine force, unlock, cleanup, retry, plugin, or
alternate-workflow escape hatch.

## Processing reuse and provider boundary

`run --through processing` creates a distinct Run ending at the complete
predecessor-closed Steps `00`-`06` processing boundary. It owns its Attempts
and evidence but has no applicable report and cannot later resume into a larger
plan.

`run --from-processing-run RUN` creates another same-Project Run. The source
must be a successful processing Run with an admitted receipt, compatible
Reference and processing semantics, and samples that exactly contain the
target Analysis rows and content. Reference paths may relocate only when the
admitted content remains identical; processing semantics may not change.
Reused artifacts remain at their source paths and are rebound by exact size,
hash, and source Run/Attempt identity; they are never copied, adopted, or
mutated. A proper subset uses one private Attempt-bound sample projection, not
a second scientist-authored manifest. Drift, missing state, incompatible
content, or incomplete evidence fails closed. The downstream Run owns Steps
`07` onward, its Attempts, Results, reports, and log.

An installed computation provider contributes closed normalized
configuration, typed artifacts, one Step `09` task, optional Step `10`, exact
dependencies, and minimum resources through the public analysis facade. A
separately selected report provider owns bespoke presentation. Neither creates
a second scheduler, workflow language, Artifact Store, mutable registry, or
scientific authority outside its declared tasks and artifacts.

## Task and Attempt lifecycle

Initial Run structure and each Attempt directory are create-absent. Lifecycle
holds the persistent advisory acquisition mutex while it revalidates the
prepared Attempt, then publishes the evidence-bearing aggregate Run lock before
Attempt-specific dispatch, config, or record state. A stale waiting contender
exits before materialization and leaves no new Attempt residue.

Each closed dispatch binds the admitted Execution Plan, composed profile,
owner scope, exact public producer and validator commands, declared inputs and
outputs, runtime/tool identities, and validation report. Immediately before
producer entry, the task publishes an immutable start record. Its stdout and
stderr files are create-exclusive, no-follow, drained through EOF, byte- and
order-preserving within each stream, synchronized, hash-bound, and revalidated.
No ordering between streams is claimed.

A task publishes an immutable failed or succeeded attempt after entry and a
verified-task record only after producer success, output and native-receipt
admission, validator completion, and semantic all-pass. A pre-entry failure may
retain its exact bound diagnostics without marking the scope entered, so a
later Attempt may retry it. Unexpected interruption after stream creation may
leave partial diagnostics but no terminal or verified record. Log presence or
content never establishes success.

Snakemake schedules only verified-task targets. Native artifacts, validation
reports, receipts, streams, and recovery evidence are not disposable engine
outputs. Same-Run reuse requires fresh schema, identity, content, Attempt,
receipt, and semantic-report admission. The only stationary outputs outside a
Run are the exact Step `00c` FAI/dictionary pair beside their canonical FASTA;
partial or changed pairs fail before owner entry.

The Attempt binds canonical Project, Execution Plan, composed-profile,
workflow-config, backend, source checkout, runtime, tools, and storage evidence.
Source/runtime/tool identity is checked before mutation and after delegated
execution. Direct placement requires an admitted same-host storage receipt;
Slurm requires the stronger two-phase head/compute-node receipt. Neither
permits implicit staging or copying.

Lifecycle retains its Run lock until the delegated process group is proved
absent and terminal success, failure, interruption, or blocker evidence is
durable. Catchable termination is forwarded at most once, with bounded TERM
then KILL escalation. If lock release is safe, the exact lock inode and bytes
are retained as immutable released-lock evidence and bound by the Attempt
receipt. Ambiguous release, process-group state, collision, or partial
establishment keeps the public lock or recovery residue and publishes no
resumable success.

After every selected task is verified, the scientific Attempt receipt is
published last. Application logging follows the separate logging contract and
cannot change task, receipt, rollback, recovery, or exit authority.

## Resume, inspection, Results, and reporting

Only a failed or interrupted scientific between-task boundary is automatically
resumable. Resume must preserve the same Run, source, Execution Plan, profile,
backend, execution mode, and ordered tool identities. Every entered task must
have a complete succeeded-attempt/verified chain; every retryable unentered
scope must lack a start record. Successful processing Runs are complete, and
blocked ambiguity requires explicit reconciliation rather than inference or
cleanup.

Inspection is read-only. It admits the immutable record chain, live lock,
receipts, verified content, Results, reporting, and recovery state without
using timestamps, raw output presence, task logs, or `.snakemake/` as
authority. Historical Runs are never rewritten or assigned successor
identities. The version-aware compatibility path may resume only an explicitly
supported historical layout whose current Project, retained request/execution
and profile, source/runtime/tool identities, and prior evidence re-admit
exactly; it does not make any other old layout resumable.

Public state has four separate domains: Run integrity is `valid|blocked`;
Attempt is `not_started|running|succeeded|failed|interrupted|blocked`;
scientific Results is `incomplete|complete|blocked`; and reporting is
`not applicable|incomplete|complete|blocked`. Recovery availability is a
separate fact. A successful processing-only Run has complete Results for its
plan and reporting is not applicable.

A successful full Run invokes reporting after scientific Attempt completion
unless `--no-report` is selected. `emrys report` can independently plan,
generate, or reuse the receipt-bound report transaction. Reporting failure or
regeneration cannot invalidate science and creates neither a Run nor an
Attempt. Result locations are shown only from a fully revalidated report
receipt; incomplete, failed, blocked, or dry-run state prints none.

## Run-root contract

The Run root is one durable, content-bound execution history. Preserve it as a
unit; an extracted result or report is not independently adopted as a completed
EMRYS Run.

| Location | Durable contents |
| --- | --- |
| `contract/` | Immutable Analysis, Execution Plan, Run, profile, runtime, reporting projection, workflow configs, and task dispatches. |
| `attempts/<workflow-attempt-id>/` | Attempt record, task attempts and streams, and receipt published last. |
| `state/task-starts/` | Immutable producer-entry records. |
| `state/verified/` | Hash-bound successful task records. |
| `state/reporting/` | Start and verified records for reporting transactions. |
| `results/` | Sole scientist-facing Results authority; modules declare final paths beneath it. |
| `results/editing/` | Built-in paired-CMH candidate tables, summary, spectrum, and diagnostics. |
| `results/scientific_context/` | Built-in context, motif, population, enrichment, and receipt. |
| `results/reports/<run-id>/` | Self-contained scientific and evidence/operations reports, summary, and receipt published last. |
| `products/native/` | Nonfinal native artifacts and QC/validation evidence needed for resume or downstream work. |
| `products/artifact-summary/<run-id>/records/` | Canonical record for every declared artifact, including unavailable or incomplete state. |
| `products/artifact-summary/<run-id>/<run-id>.artifacts.tsv` | Deterministic artifact index. |
| `products/artifact-summary/<run-id>/<run-id>.artifact_receipt.tsv` | Artifact-index receipt published last. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Canonical machine-readable Run summary. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | Tabular Run-status summary. |
| `products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC projection. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary_receipt.tsv` | Run-summary receipt published last. |
| Beside the declared FASTA | Step `00c` `.fai` and `.dict`, the only owner outputs outside the Run root. |

Locks, released-lock evidence, partials, backups, streams, and failed Attempts
remain evidence even after later success. Historical report locations and
request-era field names remain read-only evidence, not additional current
publication roots or public configuration interfaces.
