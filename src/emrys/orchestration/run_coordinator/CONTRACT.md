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
Both Project initialization routes accept `--site viking`; the existing default
profile then contains the built-in Viking placement rather than direct placement.
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
EMRYS-owned locations through existing package managers and requalifies. Normal
Doctor runs on the head node. For Slurm placement, repair installs there,
submits bound compute runtime/storage checks and finalizes storage on the head
node. `--compute` is the explicit advanced allocation route; it cannot finalize
head-node evidence. A prior storage receipt alone does not qualify a changed
runtime. Each automatic repair has one maintenance log; its compute checks
retain scheduler streams without opening another application attempt.

Head storage finalization failures name the accepted qualification job and retain
the escaped storage or operating-system cause in the existing maintenance log.
Interruption remains an interruption. Published compute/final storage evidence
is preserved after a failure. The final readiness observation must still match
the confirmed execution profile and admitted Project/package/runtime binding;
newly changed but individually admissible inputs cannot turn this invocation
into successful verification.

Named Project initialization displays input hashing, compatibility checking,
and post-publication verification through the existing elapsed-time presenter.
It explains the complete input reads before they begin. Preview runs only the
first two phases and writes nothing; creation retains all three checks in their
existing order. Progress adds no percentage estimate, persistent state, or
authority to remove a partial or published Project after interruption.

Named initialization's no-write preview shows the admitted built-in Analysis,
explicit sample/mate and biological assignments, input/region identities, and
normalized scientific choices. Its quoted replay command selects the same Python
interpreter and exact Projects parent and supplies every collected answer.
The later creation re-admits current inputs; the preview is not a frozen-input
promise. Existing `--execute` behavior remains unchanged. Unsupported Project
schema diagnostics retain their original detail and identify guided current
setup; no legacy field translation or YAML-only import is performed.

Doctor labels a plan with package-manager actions as repair and verification;
a plan without those actions is verification. Plan, confirmation, progress,
and terminal messages use that distinction. Package action labels are carried
with the exact command/environment pairs consumed by both preview and execution.
The managers determine which packages are reused or changed. Verification
repeats admission at its existing input, mutation, and host boundaries; it does
not install packages or treat a prior successful check as current evidence.
Existing CLI flags, maintenance log modes/event IDs, refusals, and exits remain
unchanged. Slurm-stage elapsed time includes queue waiting and compute work.

Doctor's domain summary distinguishes absent default runtime inventory
(`NOT PREPARED`), inspected runtime check failures (`CHECKS FAILED`), unqualified
storage (`NOT QUALIFIED`), and an inadmissible execution profile (`NOT ADMITTED`).
Storage's summary does not infer that missing or invalid evidence is fresh setup.
Exact blockers remain visible as execution requirements. Malformed/explicitly
missing runtime inventories retain their input errors, and inability to perform
the requested maintenance still reports `DOCTOR BLOCKED`. This presentation
changes no readiness, repair, logging, or execution authority.

Failed runtime checks retain their identity, target, expected/observed values,
probe detail, host, inventory digest, and qualification phase before a repair
aborts. Head-side discovery and requalification write `runtime_check_failed`
events to the existing maintenance log; normal output names failed checks and
that exact log path. Automatic compute failures write JSON-escaped details to
the parent's scheduler stderr even when the failure prevents qualification
binding. Read-only diagnosis creates no log; verbose/debug output includes the
same detail. Diagnostic persistence remains best-effort and cannot admit a
failed inventory or change qualification exits. The existing required Snakemake
check also performs bounded empty-workflow startup in private disposable scratch,
using the selected interpreter in the calling environment. It runs no study
task and changes no Project/Run state. Thus head diagnosis, compute qualification,
and execution preflight exercise backend initialization at their own boundaries;
a successful head check alone does not establish compute-node readiness.

For direct placement, `run` and `resume` construct and display one frozen plan,
then ask once before executing that same object. Refusal, EOF, interruption, or
noninteractive omission of `--execute` writes nothing, submits nothing, and
opens no application log. `--execute` is the explicit automation path.

For Slurm placement, the terminal instead confirms one frozen submission plan
before its single `sbatch` call. Submission owns no Run attempt or application
log. Ambient `SBATCH_*` and private transport variables are removed; omitted
site fields remain site policy rather than being fabricated. The explicit
batch export list preserves the submitter's `LOGNAME`, `USER`, `LNAME`, and
`USERNAME` by name for Python/Snakemake's display-name lookup, including on
compute nodes without a passwd entry. These values are not identity authority;
the numeric UID checks remain authoritative. The private
compute delegate validates its exact profile binding,
submitter identity, and positive scheduler job ID inside the allocation before
module, scratch, Doctor, or workflow work. It uses one owned scratch directory,
removes it on exit, loads only an explicitly admitted module
initializer/roster, and delegates to the same grouped Run path. Scheduler
streams and job identity are operational provenance, never scientific or
completion authority.

The shared transport retains the failing operation and underlying OS error,
and includes bounded, escaped scheduler diagnostics. A canonical returned job
ID establishes acceptance even if the scheduler command then exits nonzero;
that error retains the known ID and stream paths. In waited qualification,
`sbatch --wait` returns the job's exit status and maps signal termination to 1,
so a nonzero exit alone cannot distinguish failed execution from cancellation.
Without a canonical ID, acceptance remains unconfirmed. Invalid responses
remain errors and never trigger automatic resubmission. Doctor retains its
existing private submission transcripts; Run/resume/report preserve the shared
transport error at their public failure boundary without repeated translation.

After approval and before ordinary Run/resume/report submission, Control creates
one private `logs/submission-<uuid>/` request directory. Its immutable
`request.json` uses `emrys.submission-request.v1` and retains UTC creation time,
numeric submitter UID, command, absolute Project, requested Run/Analysis,
resolved application-log root, profile binding, exact delegate arguments, and
scheduler stream patterns. This is correlation context, not a Run/Attempt or
current scheduler-status record. The context and containing directory entries
are synchronized before invoking `sbatch`; failure preserves partial records
and prevents that invocation.

The shared transport opens private raw `sbatch.stdout`/`sbatch.stderr` files and
synchronizes their directory before launch. Ordinary submission does not add
`--wait`; Doctor retains its waited first-response/callback ordering. Early
stdin closure still collects scheduler exit/error detail. An interrupted,
malformed, rejected, or unconfirmed response remains retained without retry.
The existing stdout response is the sole recorded scheduler response; there is
no second job-ID/status file. These records do not prove that a Run was created,
that a job still exists, or that cancellation or recovery is safe.

The existing dashboard's shared scheduler observer requires an exact canonical
root job ID and current numeric UID. It rejects missing/mismatched/duplicate
identity, including accounting duplicates, and never substitutes `USER` or
`LOGNAME` for UID proof. Refresh also checks selected stream paths; unavailable
or ambiguous metadata yields `UNKNOWN`, and usage must name the exact batch
step. Accounting selection and state observation share one parser. Even a
matching job ID/UID/path does not establish a durable request's submission or
cluster identity, nor prove process absence, EMRYS completion, or safe recovery.

## Profiles and immutable planning

Allocation observation preserves CPU affinity and declared Slurm CPU limits.
Memory uses host physical RAM constrained by the observed cgroup limits and
any declared Slurm memory limit. When Slurm omits memory metadata, the same
process-visible ceiling applies to partial-node and whole-node allocations;
no extra workflow budget or exclusive allocation is required. The recorded
source identifies the unspecified Slurm limit. This ceiling is not a memory
reservation or a measurement of currently free RAM on a shared node.

`doctor`, `run`, `resume`, and `report` accept at most one closed
`emrys.execution-profile.v1` fragment:

- omission reads `<project-root>/runtime/profiles/default.yaml`;
- `--profile NAME` reads exactly
  `<project-root>/runtime/profiles/NAME.yaml`; and
- an absolute `--profile PATH` reads that exact file.

Doctor carries the selected source through repair, compute qualification, and
head finalization. Its confirmed profile binding is rechecked at execution
boundaries, including the final readiness observation; changing it requires a
new invocation and review. An unavailable or invalid explicit selection is
`NOT ADMITTED` and never falls back to the Project default. Profile selection
does not select a different runtime inventory or skip runtime/storage checks.

Standalone report execution also reads the default profile and uses the same
Slurm transport; its preview is local and read-only. A preview that proposes
new reports admits its selected profile before showing submission settings;
already-complete reports require no new submission profile. Automatic reporting stays
in the Run's existing allocation. Initial Viking selection changes placement
only, not the scientific resource policy or Run identity.

One pure formatter on the admitted execution profile supplies Doctor and
Run/resume/report submission summaries. It shows requested nodes and exclusivity,
allocation CPUs/time/memory and site fields, plus declared workflow and stage
limits. It performs no allocation query. Omitted memory and host selection stay
unknown; no exclusivity request leaves sharing to site policy. Numeric ceilings
are configured limits, not observed RAM or measured demand. Compute admission
still resolves actual capacity, and direct Run planning retains its separate
observed-allocation display. The confirmed submission uses the same frozen
profile; a later separate invocation reads and admits its own selected profile.

There is no site/global registry or profile scan. Packaged defaults apply first,
the selected profile overrides them, and resource CLI values have highest
precedence. Placement is Attempt-local provenance; the admitted scientific
computation and task roster remain Run authority.

Profile admission rejects provably impossible declared relationships before
allocation: stage concurrency times threads cannot exceed workflow cores;
known stage memory totals cannot exceed known workflow memory; multiple
concurrent tasks cannot each claim the entire workflow memory budget. The
existing computational-resource owner enforces these same predicates during
actual allocation resolution. Explicit CLI corrections apply before relationship
checks. `allocation` and `workflow` aliases remain symbolic in retained policy;
unknown capacity is neither guessed nor materialized into a Run. This early
declaration check does not equate scheduler reservations with observed capacity.

`emrys profile create NAME` previews one named Project profile and writes only
with `--execute`. It requires explicit built-in site or direct/Slurm placement,
reuses existing resource flags, and admits the exact candidate bytes through
the same parser and policy owner as file selection. It reads the Project
definition and execution settings, not scientific inputs, runtime, or capacity.
The existing canonical profile directory and absent destination are required;
exclusive publication and final binding admission preserve existing profiles
and reject changed parents or defaults. Partial publication after a failure is
retained. Placement-only authoring remains a fragment, preserving resume policy;
explicit resource overrides save the complete reviewed computational policy.

Admission retains whether computational resources were explicitly authored;
merged defaults cannot reconstruct that choice when resuming. Slurm resource
selection in the parent process and Run planning in the compute process check
the predecessor at different times. A cached parent result cannot replace the
child's admission.

New profiles reject `resources.reporting_memory_mb`, and the CLI no longer
accepts `--reporting-memory-mb`. This retired control never constrained report
execution. Remove it from a selected profile before a new Run or Attempt.
Resume carries only the computational policy into a new Attempt and does not
rewrite the immutable Run or its predecessor records. Normal implementation
installed-package identity checks still apply.

Planning combines the common processing profile and the selected analysis
provider's tasks, inputs, outputs, validation, resources, and reporting projection.
In `materialization.py`, `_tasks` resolves scopes and final/working paths;
`_task_commands` translates one processing owner's admitted facts into ordered
producer arguments, validator arguments, and inputs. Its caller immediately
names these three results. STAR directories, shared reference files, sample and
partition inputs, and guarded R commands retain their distinct construction.
One immutable Attempt manifest supplies the installed Snakemake backend.
The public surface exposes no engine force, unlock, cleanup, retry, plugin,
or alternate-workflow escape hatch.

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

Task HUP/INT/TERM handlers remain installed through terminal task evidence
publication. Each terminal attempt or verified-task record defers those signals
only while its exclusive publication runs; input/output hashing and revalidation
remain interruptible. Pending signals are delivered after that record boundary,
and the caller's original handlers and signal mask are restored. An ambient
mask that blocks task signals is refused before task mutation.

The terminal attempt and verified-task reference are separate records. An
interruption between them preserves an incomplete, blocked chain; completing
one record does not fabricate the other. Uncatchable termination and uncertain
writer-group absence can still leave preserved ambiguous state. A stopped
Snakemake process group does not prove that an independent native process group
has stopped, and this boundary grants no new resume or reconciliation authority.

The initial Run tree and each Attempt directory must be absent before creation.
Lifecycle holds a persistent advisory mutex while it revalidates the prepared
Attempt. It then publishes the Run lock, including the admitted manifest's hash,
before writing Attempt-specific inputs or records. Snakemake and workers check
the manifest against that independently published lock before task entry. A competing process
whose prepared state became stale while waiting exits before these writes and
leaves no new Attempt residue.

`attempts/<workflow-attempt-id>/attempt.json` is the sole immutable execution
manifest (`emrys.workflow-attempt.v3`). It contains shared runtime and workflow
settings once, plus task definitions keyed by owner and scope. Each definition
binds exact worker and validator commands, inputs, outputs, publication controls,
and its validation report. Fixed internal paths are derived from the Run,
Attempt, owner, and scope. Separate workflow-config and task-dispatch files are
not produced.

On resume, a verified task refers directly to its original Attempt manifest and
selects the original owner and scope. References cannot form chains, and reused
definitions cannot execute as new work. Pending definitions belong to the new
Attempt; retained Step 07 work keeps its original selected-sample manifest and
content binding. A changed plan requires a new Run; resume creates a new Attempt
without changing any predecessor.

Graph construction shares decoded original manifests across task definitions.
Each worker decodes its selected manifest at startup and retains exact-byte
rechecks. Inspection and reuse reload evidence independently; there is no shared
mutable cache. The [recorded scale probe](../../../../docs/history/validation-evidence.md#immutable-attempt-manifest-scale-probe)
shows that fewer planning files can increase per-task decoding cost; it does
not establish a workflow speedup.

Immediately before producer entry, the task publishes an immutable start record
binding its original manifest's path and exact hash. Its stdout and
stderr files are create-exclusive, no-follow, drained through EOF, byte- and
order-preserving within each stream, synchronized, hash-bound, and revalidated.
No ordering between streams is claimed.

A task publishes one immutable terminal attempt (`emrys.task-attempt.v3`)
containing its status, commands, input/output identities, validation report,
and log references. Scientific receipt files are ordinary declared outputs,
covered by the same content checks and publication rules as other results.
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

All first-party scientific tasks use the runner: reference construction, sample
and cohort processing, paired CMH, and scientific context. Producers compute
outputs, perform native checks, and write provenance into explicit working and
scratch paths. The runner owns those paths, locks, processes, streams, publication,
and recovery; no producer manager is needed. GTF-to-BED12's private worker shares
normalization with Project and BED12 validation.

`task.run_task` keeps the execution and failure sequence together:

1. Recheck the plan, lock, inputs, and existing destinations; record entry and
   open the task streams. Task definitions bind final/working paths, publication
   order, locks, recovery locations, and complete directory inputs.
2. Create the workspace and run the producer. Stop and reap its process group
   before cleanup. Working files share the destination filesystem, allowing
   publication by links without copying large outputs.
3. Validate and publish. Preprocessing (Step `08`) and paired CMH (Step `09`)
   validate working files and pass semantic checks before publication. Other
   owners publish first, then independently validate final files and require
   semantic all-pass. `_NativePublication` handles exclusive links in declared
   order, with any native receipt last. Input and working-file checks precede
   linking; inputs are checked again before commit releases the rollback anchors.
4. Recheck inputs, outputs, validation evidence, and stream identities; publish
   the terminal record and then its verified reference. Track phase results
   separately so failure records describe work actually reached. A native receipt
   alone never proves task completion.

Before native commit, rollback removes only outputs still bound to this task's
working files. After commit, validation failure preserves native outputs and
failed evidence. Uncertain identity, cleanup, writer state, or lock ownership
preserves recovery files. Old backups/staging are never adopted or deleted.
Only current manifest/start formats are accepted; older Runs need their original
software and existing records are not rewritten.

STAR publication includes additional regular native files beyond the fifteen
required members; alignment binds the full directory's membership and contents.
FAI/dictionary sidecars keep their cross-Run lock: reuse requires a complete
unchanged pair and still runs independent validation; partial pairs are refused.
Worker contracts own their scientific checks, formats, and provenance rules.

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
| Run admission | `valid`, `blocked` |
| Attempt | `not_started`, `running`, `succeeded`, `failed`, `interrupted`, `blocked` |
| Scientific Results | `incomplete`, `complete`, `blocked` |
| Reporting | `not applicable`, `incomplete`, `complete`, `blocked` |

The independent Run-lock observation distinguishes no lock, a local live owner,
remote ownership unverified, a local process that is not live, and invalid or
ambiguous lock state. Host/process observations follow structural lock/Attempt
binding admission; an unbound PID is never probed as an owner. Admitted owner
observations show the recorded host and scheduler ID, without treating those
records as proof of current remote liveness. Remote/ambiguous/dead ownership
continues to block Run admission and recovery. Inspection does not contact a
remote host, remove locks, or infer scientific success from scheduler state.

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
| `results/reports/<run-id>/` | Self-contained scientific and evidence/operations reports, and receipt published last. |
| `products/native/` | Nonfinal native artifacts and QC/validation evidence needed for resume or downstream work. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Authoritative reporting result manifest, published last. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | One row per artifact: identity, source, completion, warnings and errors. |
| `products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC projection. |
| Beside the declared FASTA | Step `00c` `.fai` and `.dict`, the only owner outputs outside the Run root. |

Locks, released-lock evidence, partials, backups, streams, and failed Attempts
remain evidence even after later success. Existing data and evidence are never
migrated or deleted by record admission.
