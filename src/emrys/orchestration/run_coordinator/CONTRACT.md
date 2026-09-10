# Run-coordinator intake contract

The Run coordinator turns a scientist's Project into an immutable execution
plan. It manages direct or whole-Run Slurm execution, Attempts, inspection,
recovery, Results, scientific-worker execution and publication, and the request to
generate reports. Scientific algorithms, output contents and provenance,
validation meaning, report rendering, dependency solving,
and package installation remain with their owners. The
[current architecture](../../../../docs/architecture/ARCHITECTURE.md) defines
responsibility layers; the [runbook](../../../../docs/operations/RUNBOOK.md)
owns operator instructions; and the
[logging contract](../../../../docs/design/LOGGING_CONTRACT.md) owns application
log semantics.

## Public model and admission

The public model is `Project -> named Analysis -> immutable Run -> Results`.
Here, *admission* means validating an input or record and accepting its exact
identity and content for use:

- The authored `project.yaml` is mutable input. Admission snapshots its exact
  bytes and referenced manifests, normalizes scientific content, and produces
  immutable Project and Analysis revisions.
- An Analysis names one admitted scientific comparison and module
  configuration. Its name selects the Analysis and appears in Attempt metadata;
  the name does not contribute to its content-derived identity.
- A Run immutably binds one Analysis revision and one Execution Plan. Changing
  scientific intent or planned tasks creates another Run.
- Each execution or resume creates a new Attempt. It cannot mutate the Run.
- Results are the admitted final scientific artifacts beneath that Run.
  Reporting is a downstream transaction, not a scientific stage or completion
  authority.

Ordinary Project-aware commands read `project.yaml` in the current directory. Optional `--project` accepts one named Project directory or an
exact `project.yaml`; no parent-directory or global lookup occurs. The file's
parent is the Project root. Only current Project and Run contracts are accepted;
[version support](../../../../docs/design/decisions/platform-direction.md#version-support)
defines the boundary.

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

There is no site/global registry or profile scan. Packaged defaults apply first,
the selected profile overrides them, and resource CLI values have highest
precedence. Placement is Attempt-local provenance; the admitted scientific
computation and task roster remain Run authority.

New profiles reject `resources.reporting_memory_mb`, and the CLI no longer
accepts `--reporting-memory-mb`. This retired control never constrained report
execution. Remove it from a selected profile before a new Run or Attempt.
Resume carries only the computational policy into a new Attempt and does not
rewrite the immutable Run or its predecessor records. Normal implementation
installed-package identity checks still apply.

Planning composes the fixed common processing profile with the selected
analysis provider's admitted task tail, declared inputs/outputs, validation
reports, resources, and reporting projection. One immutable Attempt manifest
records the complete task plan and invokes the installed Snakemake backend. The
public surface exposes no raw engine force, unlock, cleanup, retry, plugin, or
alternate-workflow escape hatch.

Before creating a new Run, planning rejects processing dependencies that
disagree with the graph in the admitted installed package. Existing Runs
keep their retained profiles and require the same admitted implementation for resume. The shared source profile now defines executable processing
tasks, so changing its bytes invalidates reuse of earlier Processing results.

## Processing reuse and provider boundary

`run --through processing` creates a distinct Run containing Steps `00`–`06`
and all their prerequisites. It owns its Attempts
and evidence but has no applicable report and cannot later resume into a larger
plan.

`run --from-processing-run RUN` creates another same-Project Run. The source
must be a successful processing Run with an admitted receipt and compatible
Reference and processing rules. Its samples must contain every target Analysis
row with identical content. Reference paths may relocate only when the
admitted content remains identical; processing semantics may not change.
Reused artifacts remain at their source paths and are rebound by exact size,
hash, and source Run/Attempt identity; they are never copied, adopted, or
mutated. When the target uses fewer samples, EMRYS creates one private sample projection
bound to that Attempt; the scientist does not author a second manifest. Drift, missing state, incompatible
content, or incomplete evidence fails closed. The downstream Run owns Steps
`07` onward, its Attempts, Results, reports, and log.

An installed computation provider contributes closed normalized
configuration, typed artifacts, one Step `09` task, optional Step `10`, exact
dependencies, and minimum resources through the public analysis facade. A
separately selected report provider owns bespoke presentation. Neither creates
a second scheduler, workflow language, Artifact Store, mutable registry, or
scientific authority outside its declared tasks and artifacts.

## Task and Attempt lifecycle

The initial Run tree and each Attempt directory must be absent before creation.
Lifecycle holds a persistent advisory mutex while it revalidates the prepared
Attempt. It then publishes the Run lock, including its evidence, before writing
Attempt-specific inputs or records. A competing process
whose prepared state became stale while waiting exits before these writes and
leaves no new Attempt residue.

`attempts/<workflow-attempt-id>/attempt.json` is the sole immutable execution
manifest (`emrys.workflow-attempt.v2`). It contains shared runtime and workflow
settings once, plus task definitions keyed by owner and scope. Each definition
binds exact worker and validator commands, inputs, outputs, publication controls,
and its validation report. Fixed internal paths are derived from the Run,
Attempt, owner, and scope. Separate workflow-config and task-dispatch files are
not produced.

On resume, a verified task refers directly to its original Attempt manifest and
selects the original owner and scope. References cannot form chains, and reused
definitions cannot execute as new work. A changed plan requires a new Run;
resume creates a new Attempt without changing any predecessor.

Immediately before producer entry, the task publishes an immutable start record
binding its original manifest's path and exact hash. Its stdout and
stderr files are create-exclusive, no-follow, drained through EOF, byte- and
order-preserving within each stream, synchronized, hash-bound, and revalidated.
No ordering between streams is claimed.

A task publishes one immutable terminal attempt containing its status, commands,
input/output identities, native receipt, validation report, and log references.
After producer success, output admission, validator completion, and semantic
all-pass, it publishes a small verified marker containing only the terminal
attempt path and hash. Inspection follows that reference and rechecks the evidence. A pre-entry failure may
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
backend, installed package, runtime, tools, and storage evidence.
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

## Scientific worker execution

All first-party scientific tasks execute through this runner, including reference
construction, sample processing, cohort preprocessing, paired CMH, and scientific
context. Producers compute the scientific outputs, perform their native checks,
and write provenance. They receive explicit working destinations and scratch
space; they do not choose final working paths, acquire locks, publish results,
supervise process groups, or implement operational recovery. There is no separate
manager per producer. The independently useful `emrys convert gtf-to-bed12`
utility keeps its public conversion interface; the Run uses its normalization
code through a private worker entry point.

Task definitions bind working paths, final paths, publication order,
locks, old recovery locations, and any complete directory input. Working files
sit beside their final destination's parent, so publication can link large files
without a second copy. The runner creates these directories, captures streams,
and stops and reaps the worker's process group before attempting cleanup.
Only the current manifest and task-start formats are accepted. Existing files
are never migrated or rewritten; older Runs require their original software.

Before publication, the runner rechecks admitted inputs and the producer's
checked working files. It also rechecks inputs after linking, before native
commit and release of the rollback anchors. It publishes files exclusively in declared
order, with any native receipt last. The complete STAR index includes additional
regular native files, not just its fifteen required members; alignment binds
that entire input directory's membership and contents. Shared FAI/dictionary
sidecars retain their cross-Run lock. The Run reuses a complete unchanged pair
and still runs the independent validator; a partial pair is refused.

The independent validator and semantic all-pass gate run against final files
after native publication. Failure at that point preserves the committed native
outputs, validation report, and failed task evidence. A native receipt alone is
not verified task completion. Before native commit, rollback may remove only
files still proved to belong to this task by their retained working-file anchors.
An ambiguous identity, failed cleanup, or changed lock preserves remaining files
and recovery evidence for inspection. Old backup and staging residues are never
adopted or automatically deleted. These rules apply once here across the workers;
their contracts retain scientific checks, formats, and provenance requirements.

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
authority. Current-version resume validates earlier Attempts of the same Run;
it does not translate old-version records.

Inspection reports four independent states:

| Subject | Possible states |
| --- | --- |
| Run integrity | `valid`, `blocked` |
| Attempt | `not_started`, `running`, `succeeded`, `failed`, `interrupted`, `blocked` |
| Scientific Results | `incomplete`, `complete`, `blocked` |
| Reporting | `not applicable`, `incomplete`, `complete`, `blocked` |

Recovery availability is a separate fact. A successful processing-only Run has complete Results for its
plan and reporting is not applicable.

A successful full Run invokes reporting after scientific Attempt completion
unless `--no-report` is selected. `emrys report` can independently plan,
generate, or reuse the receipt-bound report transaction. Reporting failure or
regeneration cannot invalidate science and creates neither a Run nor an
Attempt. Result locations are shown only from a fully revalidated report
receipt; incomplete, failed, blocked, or dry-run state prints none.

Reporting has two transactions: build the result manifest, then render HTML.
The manifest contains artifact status, identities, validation results, and shared
Run and publication provenance. It is published last after the summary and QC
TSVs. There are no per-artifact record files, separate artifact index, or summary
receipt. HTML keeps its own publication receipt and the two existing reports.

## Run-root contract

The Run root is one durable, content-bound execution history. Preserve it as a
unit; an extracted result or report is not independently adopted as a completed
EMRYS Run.

| Location | Durable contents |
| --- | --- |
| `contract/` | Immutable Analysis, Execution Plan, Run, profile, runtime, and reporting inputs. |
| `attempts/<workflow-attempt-id>/` | One immutable Attempt manifest, task results and streams, and receipt published last. |
| `state/task-starts/` | Immutable producer-entry records. |
| `state/verified/` | Path/hash references to successful terminal task attempts. |
| `state/reporting/` | Start and verified records for reporting transactions. |
| `results/` | Sole scientist-facing Results authority; modules declare final paths beneath it. |
| `results/editing/` | Built-in paired-CMH candidate tables, summary, spectrum, and diagnostics. |
| `results/scientific_context/` | Built-in context, motif, population, enrichment, and receipt. |
| `results/reports/<run-id>/` | Self-contained scientific and evidence/operations reports, summary, and receipt published last. |
| `products/native/` | Nonfinal native artifacts and QC/validation evidence needed for resume or downstream work. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Authoritative reporting result manifest, published last. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | Tabular Run-status summary. |
| `products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC projection. |
| Beside the declared FASTA | Step `00c` `.fai` and `.dict`, the only owner outputs outside the Run root. |

Locks, released-lock evidence, partials, backups, streams, and failed Attempts
remain evidence even after later success. Existing data and evidence are never
migrated or deleted by record admission.
