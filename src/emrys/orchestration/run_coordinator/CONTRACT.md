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

The immutable repair plan supplies one runtime-work summary for preview,
execution and the existing `repair_started` diagnostic. It distinguishes a
currently verified selected runtime without manager work, preparation of a
missing managed inventory, and checking/updating tools selected by a retained
managed inventory. Missing inventory does not imply absent tools or a fresh
installation. Manager plans retain the exact `package-output.log` path;
only package-manager output identifies actual package reuse or changes.
These descriptions add no probes, inferred cache admission or skipped checks.

Doctor reports invocation timing separately from admission. The total spans
entry through return/exception and explicitly includes operator confirmation
time; verbose/debug output shows precise phase elapsed seconds. An
invocation-local collector receives best-effort observations from the shared
progress owner without removing or reusing any input checks. Approved maintenance
buffers all phases until controlling work and the claim-release decision finish,
then flushes `doctor_phase_timing` events once before its existing terminal log
event. A failed timing write cannot disrupt package-output handling. The final
invocation total is console-only after that log
closes. Read-only diagnosis and delegated compute create no second log.
Slurm submission-to-return wait is not an isolated queue-time measurement.
After that timer ends, an ordinary return or submission error may trigger one
bounded, optional `sacct` query through the existing scheduler observer. The
recorded submission callback carries job ID and optional cluster to the collector;
no response-recorded identity means no query. Numeric ownership, exact root ID,
cluster, planned name, unique record and both maintenance streams must match.
The query requests UTC dates using `TZ`/`SLURM_TIME_FORMAT`; unsupported accounting
fields, unknown dates and inconsistent values remain unavailable diagnostics.
Only a terminal, non-restarted, non-suspended record with ordered dates and
consistent elapsed time supplies submitted-to-start wait, eligible queue wait
and allocation wall time. Admitted dates/counters remain separate from those
derived intervals. Wall time includes launch overhead, not just computation.
The collector buffers `doctor_scheduler_timing` in the same maintenance log at
the outcome boundary above, and its normal console summary escapes limitations.
The summary also exposes the admitted accounting state, source and scheduler
exit status, so cancellation and compute failure remain distinguishable even
when waited `sbatch` exits nonzero. These are observations: an accounting
`COMPLETED` record cannot replace a submission/client failure or qualify storage.
Accounting lookup has its own phase outside submission-to-return waiting; no
polling, runtime probe, new log, receipt or admission authority is introduced.
Process-control exceptions during submission skip the lookup entirely.
Ordinary observation failures leave work, receipts and exits controlling;
process-control exceptions retain cancellation semantics. These timings do not
measure read bytes, process-tree memory or scientific performance.

The same collector retains passing runtime diagnostics at each actual fresh
Doctor inspection/discovery return. It shares the failure diagnostic field
projection and flushes `runtime_check_passed` packets after phase timings at the
same outcome boundary. A returned Slurm result is not captured again as a new
observation. Packets retain their actual Doctor phase and execution context;
their log timestamp is the later flush time. Head maintenance retains its own
observations without treating delegated compute checks as head observations.
Verbose/debug diagnosis prints escaped passing details without creating a log.
Existing immediate failure diagnostics and qualification identities are unchanged.

Managed repair opens its diagnostic log before acquiring the private durable
`runtime/maintenance.lock` claim, then re-admits the plan before manager work.
The shared ownership primitive pins a canonical no-follow parent, synchronizes
the claim and directory, and checks exact ownership/content before release.
Doctor retains claims on failed/interrupted acquisition or repair. It releases
only after successful requalification and before recording success. A failed
directory synchronization after release can leave no claim pathname but still
reports failure. Existing claims block another managed repair; age, host or PID
absence never clears them. Verification-only plans do not acquire a claim.
Reporting uses the same primitive with its existing owned-partial cleanup
policy. This maintenance exclusion alone does not freeze runtime content or establish
cross-Project sharing; an immutable expected-content seal and fresh borrower
qualification remain necessary.

Explicit `runtime discover --from-project DONOR` supplies that sharing route.
Preview probes and prepares an expected-content seal without publication;
`--execute` claims the donor, rechecks its inventory/content, exclusively
publishes `runtime/shared.json`, releases the exact claim, freshly checks the
borrower selection and exclusively publishes the borrower's inventory. An
already sealed donor is read-only. Failure preserves surviving claims/seals;
borrower publication failure cannot undo a donor seal. Donor managed repair
refuses any seal object at planning and re-admission, including a stale plan
under its maintenance claim. Verification-only operations remain available.
The [runtime owner](../../evidence/runtime_availability/README.md#sealed-managed-runtime-reuse)
defines the closed seal/selector formats and fixed-content boundary. The exact
selector is retained through Run/Attempt inventories; borrower admission still
checks its own Python/package, Analysis, storage, and allocation contexts.

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
`request.json` uses `emrys.submission-request.v3` and retains UTC creation time,
numeric submitter UID, command, absolute Project, requested Run/Analysis,
resolved application-log root, profile binding, exact delegate arguments, and
scheduler stream patterns. This is correlation context, not a Run/Attempt or
current scheduler-status record. The context and containing directory entries
are synchronized before invoking `sbatch`; failure preserves partial records
and prevents that invocation.

The request UUID is chosen before submission planning and confirmation. The
same frozen token appears in `submission-<uuid>` and both scheduler stream
patterns, `emrys-local-pilot-<uuid>-%j.out` and `.err`. A v2 reader requires
both patterns to match that exact request directory. Distinct requests therefore
keep distinct stream destinations even if Slurm reuses a job number. Legacy
v1 contexts remain readable diagnostic records, but their shared `%j` paths do
not supply request identity. Doctor's private qualification streams are unchanged.

The shared transport requires a transcript destination, opens private raw
`sbatch.stdout`/`sbatch.stderr` files, and synchronizes their directory before
launch. Ordinary submission does not add
`--wait`; Doctor retains its waited first-response/callback ordering. Early
stdin closure still collects scheduler exit/error detail. An interrupted,
malformed, rejected, or unconfirmed response remains retained without retry.
The existing stdout response is the sole recorded scheduler response; there is
no second job-ID/status file. These records do not prove that a Run was created,
that a job still exists, or that cancellation or recovery is safe.

Ordinary submission carries its frozen request token through the existing
private batch delegate context. The shell checks it before site initialization
and keeps it read-only; malformed or orphan token context is refused. The one
workflow/report application log records a durable-only `submission_context`
event with exact token, profile binding and Project root before preparation.
Opening scheduler metadata and later candidate Run/Attempt events remain
distinct diagnostics. This adds no application log to the submitter, no
secondary state store, and no association or cancellation authority by itself.

Project inspection without a Run selector enumerates all retained requests
before the existing Run selection. It never chooses the newest request. The
shared writer/reader validates the closed context and a 64 KiB canonical JSON
limit; the reader requires canonical, current-UID-owned directories/files and
stable bounded reads. Missing, malformed, oversized or changing records remain
partial/unconfirmed observations or explicit read failures. It reads at most
4096 stderr bytes and admits only a bounded, newline-terminated canonical
response as a recorded job/cluster. Metadata and excerpts are terminal-escaped.
Neither the response nor record timestamps establish acceptance, current state,
Run association or process absence. No scheduler query or file write occurs.
A Project with no Runs still displays its request roster successfully;
explicit Run selection retains its existing missing/ambiguous selection errors.

`inspect --submission REQUEST` selects one exact retained directory name or
absolute path, mutually exclusive with a Run selector. The ordinary roster
does not query the scheduler. The selected request's v2/v3 binding uses a shared
stdlib-only scheduler owner: exact root ID, numeric UID, cluster and both frozen
stream paths must agree in one complete metadata row. New v3 requests also
retain and compare the exact scheduler job name, derived from the same request
token as the streams; v2 retains its previous observation shape. A successful empty queue
query may fall back to duplicate-aware terminal accounting; a failed queue
query cannot. Each of at most two commands has the existing ten-second timeout.
Admitted replies are capped at 64 KiB; subprocess capture memory itself is not
strictly bounded. Legacy, partial, mismatched, malformed, duplicate or unsupported
metadata stays `UNKNOWN`. State, queue reason and accounting exit status are
escaped observations, never Run association, scientific success or recovery
authority. The existing dashboard uses the same extracted identity/accounting
mechanics and still loads directly under isolated system Python.

Selected inspection additionally reads one bounded application scope from the
request's retained custom log root: `run-pending` for new Runs or the exact
requested Run scope for resume/report. It rechecks the closed request and raw
response, then admits complete JSONL snapshots with matching envelope, opening
job ID and one second-record token/profile/Project context. Exactly one match
is required. The reader caps directory enumeration at 128 applications, each
log at 1 MiB and aggregate log reads at 8 MiB, plus one oversize-detection byte.
It rejects changing, noncanonical,
unowned, linked, truncated or ambiguous evidence rather than guessing from time.
Default roster inspection performs no application-log scan.

The final admitted `attempt_failed` or `attempt_interrupted` event supplies a
recorded application outcome and its exact phase to static inspection, watch and
Run-log rows. An unfinished log has no recorded outcome. The reader uses the
same admitted bytes and preserves preparation candidates and independent Run
admission; a recorded application failure is neither a Run-state transition nor
recovery authority. In particular, an interruption's recorded `interrupt` phase
does not establish whether preparation or workflow execution had begun.

Preparation/reporting-start events supply recorded candidates only. Existing
Run and profile admission validates the candidate's immutable identity; Run or
resume additionally admits the exact historical Attempt, its bound Project
request snapshot, operation, workspace, Slurm ID and selected profile digest.
The existing byte-reader injection enforces 4 MiB per authority file and
16 MiB aggregate authority reads, plus one oversize-detection byte. Stable
directory/file snapshots are checked again before returning. A failed candidate admission retains only the exact
log and recorded candidate; changed scanned evidence clears the association.
The result does not admit the Attempt chain, locks, receipts, Tasks or Results,
and cannot prove workflow entry, liveness, completion or recovery eligibility.
The public view offers exact Run inspection for that broader evidence.

Explicit `inspect RUN` also searches one application root, selected by the
shared `--log-root` / `EMRYS_LOG_ROOT` / Project-default precedence. The root-only
selector neither opens a writer nor changes a request's frozen log root;
`--log-root` without an explicit Run or with `--submission` is refused before
queries. An implicit Run picker and the ordinary roster perform no log search.
Run contracts do not retain custom historical log roots.

The same reader scans `run-pending` and the exact Run scope, sharing aggregate
limits, stable namespace checks, JSONL preparation parsing and retained
Run/Attempt admission with request inspection. It admits the selected Run once
and each distinct historical Attempt once per scan. Run/resume logs bind the
recorded operation, Project request and Attempt; standalone reporting binds
only the Run. For Run/resume logs, recorded Slurm context, when present, must
match the retained Attempt. All matches remain diagnostic associations,
including multiple logs for one Attempt; no unique writer, newest log or current
scheduler state follows.

Malformed siblings or exhausted limits leave the scan unknown while preserving
independently rechecked matches. Failed reads consume their reserved allowance;
global snapshot drift or unexpected reader failure clears all matches. Missing
roots and preparation events cannot supply guessed paths. Static and watch
views share this result; explicit verification refresh rebuilds application
streams, revokes lost associations and preserves independently admitted Task
streams. Diagnostic read failure never grants or replaces scientific authority.

`inspect --watch` keeps one selection fixed and uses the same pure Task,
milestone, reporting and elapsed projection as static inspection. Existing
Run admission runs initially and on explicit verification refresh; its date
and any failure remain visible. Application association is also dated and is
distinct from the Run's latest Attempt. A timer cannot promote historical
evidence to current progress or recovery eligibility. Run-only views cannot
derive current scheduler identity from an unbound recorded job ID.

The installed view shares the legacy overview/detail renderer and diagnostic
parser. Sample lanes, peer timing, stage context, progress history, activity,
errors, scheduler resources and historical accounting remain available.
Reported Job stats define invocation counts; absent totals remain unknown.
Generic current analysis-owner rules and historical named rules are recognized.
Parsed log completion cannot supply scientific completion or Run authority.

`--job-id [JOB_ID]` selects a raw scheduler view without Project admission;
omitting the ID uses bounded current-user discovery. A watch with no explicit
selection and no current Project also discovers through that same owner.
Explicit IDs do not rediscover on failure. `--log-dir` supplies a historical
scheduler root; command-line selectors outrank the legacy environment defaults.
`--offline` requires an exact ID and both explicit owned regular streams and
issues no scheduler query. Raw selection rejects Project, Run, request, log-root
and action combinations, and never derives Run admission from a parsed path.

One daemon worker coalesces read-only refreshes. Painting performs no I/O.
`--refresh` defaults to 30 seconds and rejects intervals below five seconds.
Timers update scheduler diagnostics and full workflow streams plus one bounded
selected tail; explicit refresh rechecks association and full Run evidence.
A terminal scheduler result is retained with its original date until explicit
refresh. Exact-request resources come from the same admitted root record;
batch usage additionally requires local binding before and after the sample.
Root and usage dates reflect their actual replies, not later proof-query time.
Missing usage preserves root state and reports usage unknown.

The shared diagnostic reader pins canonical directory/file identities, ownership,
regular-file type and generation. It reads captured sizes in bounded chunks,
retains the full consumed trace, and clears history on failed admission or
replacement/truncation. Each stream has at most one bounded-wait daemon read;
closing cannot admit another read or publish a late result. Full-history memory
is proportional to consumed trace bytes. Initial selection remains synchronous;
quitting the opened view does not wait for blocked reads.
Search-only directory access is sufficient on macOS and Linux; no directory
listing permission is required. Both installed and standalone views retain actual
trace observation dates and label pending or unavailable reads. A standalone
snapshot with an incomplete stream read prints its diagnostics and exits 1.

Legacy overview/detail navigation uses `1`/`o`, `2`/`d` and Tab; arrows, `j`/`k`,
Page Up/Down and Home/`g` scroll. `3`/`v` selects dated evidence/logs and `[`/`]`
cycles streams. Action keys cannot replace navigation keys. `NO_COLOR` suppresses
status colors. `--snapshot`, noninteractive or dumb terminals emit one plain,
dated snapshot; `--detail` remains the static-inspection selector. Ordinary
watch creates no operational action, persistent cache or additional log.

Interactive `--watch --actions` offers `p` for a Run's ordinary resume plan and
confirmation, `b` for its report preview, or `s` for an exact request's stop
preview. The presentation closes its worker, discards pending refreshes, leaves
the alternate screen and restores the terminal and discards pending keys before invoking the existing
Control handler once on the main thread. An active read may finish,
but no resulting snapshot is consumed and no refresh is restarted. There is
no automatic return to watch or concurrent action loop.

Only the exact resolved Project and Run/request selector are captured. The
ordinary parser and defaults are constructed after leaving the view. Run
handoffs select the default profile; neither report nor stop receives
`--execute`. Resume retains its explicit confirmation. Fresh planning,
preview/confirmation, lifecycle locking and recovery
admission remain authoritative; cached inspection never supplies a plan or
predecessor. Slurm retains its existing compute-side scientific admission and
possible unnecessary allocation under a concurrent resume. A request handoff
never infers a Run from an association; stop freshly checks that retained
request and scheduler identity. Noninteractive action mode is refused.

Diagnostic suffixes use the existing no-follow byte reader with 64 KiB and
256-line bounds. Directory, UID and descriptor/path checks reject unsafe or
changing streams. Rotation/truncation clears previous content rather than
concatenating generations. Current tail bytes are unverified diagnostics even
when the path came from a previously admitted content reference. Task tails
come from admitted terminal records or expected paths derived from an admitted
start. Both start origin and content reference are required. Start publication
precedes stream opening, so path derivation proves neither existence nor
liveness. Missing/unadmitted starts supply no derived stream. The original standalone entry point remains until institutional replacement
validation and coordinated retirement.

The existing dashboard's shared scheduler observer requires an exact canonical
root job ID and current numeric UID. It rejects missing/mismatched/duplicate
identity, including accounting duplicates, and never substitutes `USER` or
`LOGNAME` for UID proof. Refresh also checks selected stream paths; unavailable
or ambiguous metadata yields `UNKNOWN`, and usage must name the exact batch
step. Accounting selection and state observation share one parser. Even a
matching job ID/UID/path does not establish a durable request's submission or
cluster identity, nor prove process absence, EMRYS completion, or safe recovery.

`stop --submission REQUEST` uses the same exact retained-request selector as
inspection, with Project context and no bare job-ID form. Its default is a
no-write preview; `--execute` admits only complete v3 request identity and a
current matching scheduler observation. A terminal target needs no cancellation.
Nonterminal targets require a stable canonical executable and a confirmed plain
`scancel` release at least 23.11.6, where owner/name/ID filtering occurs together
at the controller. The plan freezes target, cluster, client binding, arguments
and environment; `SCANCEL_*` and `SLURM_CLUSTERS` overrides are removed.

Before mutation, the existing maintenance-log owner synchronizes the exact
target/client/arguments intent. The shared transport creates private raw output
files through one pinned canonical current-owned directory descriptor and
synchronizes that directory. Request, scheduler and client identities are
rechecked before the sole `scancel --ctld --clusters=CLUSTER --name=NAME --me ID`
invocation. It uses ordinary whole-job cancellation with no custom signal,
step target, retry, bulk form or ID-only fallback. Raw stdout/stderr remain next
to the maintenance JSONL, outside the closed submission-request directory.

The client has a ten-second timeout. Normal return, nonzero exit or timeout is
followed by one fresh exact scheduler observation; process-control interruption
preserves diagnostics and unwinds without additional queries. Command exit zero
means the request was processed, not that the target matched or all processes
stopped. Missing identity or uncertain output remains unconfirmed. Run receipts,
locks, Task records and recovery admission are untouched; this command cannot
promise resume or reconstruct missing terminal evidence.

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

Packaged resources restore the historical six-library EV/PUM1 policy: 12 workflow
cores, 524288 MiB and the retained per-stage concurrency, thread and memory
allowances. Initial Viking placement requests 256 CPUs on one exclusive node
for 12 hours, with site-default allocation memory. Workflow budgets and scheduler
requests remain separate; actual allocation admission still verifies capacity.
Existing explicit Project overrides and immutable Run policies are preserved.

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

Before submission planning, the final effective profile also checks known Slurm
CPU and explicit memory reservations using those same predicates. Diagnostics
name the reservation separately from observed allocation. Placement-only resume
applies the retained policy first; no extra predecessor read or default-policy
comparison is introduced. Doctor repair planning and profile authoring use the
same check before approval/write. Omitted memory remains unknown for both shared
and exclusive requests. A reservation check discards its numeric projection:
retained symbols and actual allocation admission remain unchanged.

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
For Steps `00a`, `00c`, `01`, `02`, `04`, and `05`, command construction freezes
`floor(stage_memory_mb * 4 / 5)` from the resolved task allowance into the
internal worker argument `--native-memory-mb`. STAR receives byte limits for
index generation and BAM sorting; samtools' unsorted-input fallback receives
the native allowance divided by its declared sorting threads, rounded down in
MiB; Picard and GATK receive a Java maximum heap in MiB. Other stages retain
their existing commands. Planning rejects a native allowance below 1 MiB
(below 1 MiB per sorting thread for Step `02`) before publishing a Run.
The remaining allowance provides overhead headroom, not a hard process-RSS
limit or a guarantee that a workload fits. Increasing an admitted stage budget
increases these native limits; faster execution still depends on the workload.
The existing profile is the only resource authority, with no additional
operator setting. Changed resources create a distinct Run; existing immutable
Runs retain their policies and normal implementation-identity checks.
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
manifest (`emrys.workflow-attempt.v4`). It contains shared runtime and workflow
settings once, plus task definitions keyed by owner and scope. Each definition
binds exact worker and validator commands, inputs, outputs, publication controls,
and its validation report. Fixed internal paths are derived from the Run,
Attempt, owner, and scope. Separate workflow-config and task-dispatch files are
not produced.

On resume, a verified task refers directly to its original Attempt manifest and
selects the original owner and scope. References cannot form chains, and reused
definitions cannot execute as new work. Pending definitions belong to the new
Attempt and freeze a nullable `retry_task_attempt_record`: null for an unentered
scope, otherwise the exact latest positive abort for that scope. Retained Step
07 work and retries keep the original selected-sample manifest path and bytes;
resume never recreates missing historical inputs. A changed plan requires a new Run; resume creates a new Attempt
without changing any predecessor.

Graph construction shares decoded original manifests across task definitions.
Each worker decodes its selected manifest at startup and retains exact-byte
rechecks. Inspection and reuse reload evidence independently; there is no shared
mutable cache. The [recorded scale probe](../../../../docs/history/validation-evidence.md#immutable-attempt-manifest-scale-probe)
shows that fewer planning files can increase per-task decoding cost; it does
not establish a workflow speedup.

Immediately before producer entry, the task publishes `emrys.task-start.v3` at
`attempts/<workflow-attempt-id>/tasks/<owner>/<scope>/task-start.json`, binding
its original manifest, Run lock and complete input snapshots. Every retry has
its own start; the aggregate `state/task-starts` path is no longer admitted.
Its stdout and
stderr files are create-exclusive, no-follow, drained through EOF, byte- and
order-preserving within each stream, synchronized, hash-bound, and revalidated.
No ordering between streams is claimed.

A task publishes one immutable terminal attempt (`emrys.task-attempt.v4`)
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

A failed entered Task may record `abort_closure: linux-task-prepublication.v1`
only when the fresh Linux worker positively reaps every command descendant,
no native publication invocation has begun, original input bytes and directory
membership remain unchanged, all native destinations/output directories,
validation reports and verified markers are absent, and existing owned cleanup
and directory synchronization succeed. Reused preexisting FAI/DICT pairs do not
qualify. The proof rechecks input identities and origin authority before and
after cleanup and immediately before terminal publication. Hashing and
revalidation remain interruptible; only the existing exclusive record write
masks Task signals. Failed proof leaves the closure field null. Ambiguous
writer state continues to preserve owned work and locks.

The same history owner admits all per-Attempt starts and terminal results,
checks frozen retry references in supersession order, and projects both complete
histories into `emrys.attempt-receipt.v3`. A nonblocked receipt requires every
entered Task to have a positive abort or a verified result. Historical closure
admission does not require outputs to remain absent after a successful retry;
fresh resume planning separately checks current inputs, destinations and
residue. Lifecycle repeats the frozen plan under the Run lock, the backend
admits the complete history, and a resuming Task reuses the same history policy
for its own scope before entry. A stale or omitted retry reference is refused.

This requires trusted workers to keep relevant computation and writes within
their descendants and supplied owned paths, without preexisting-service or
remote delegation, as required by the [provider contract](../../analyses/README.md).
Structural admission is not a filesystem or network sandbox. Worker loss,
missing workflow finalization, blocked receipts, postpublication failures and
old record formats remain ineligible. A durable Task abort without a complete
terminal workflow receipt does not authorize resume.

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

The native command runner records HUP/INT/TERM without throwing while it owns
the spawned group, including the interval between spawn and PGID registration.
It stops and reaps that group before restoring the outer Task handlers and
raising interruption. Repeated signals cannot interrupt bounded TERM/KILL
cleanup; child execution receives these signals unblocked. Closed stream pipes
do not establish process completion.

The fresh Linux Task CLI additionally enables child-subreaper behavior before
entry and binds it explicitly to both native command runners. It requires one
thread, no preexisting child and normal SIGCHLD handling. The same bounded
cleanup loop signals unreaped direct children and reaps adopted descendants,
including children that create separate sessions. This path uses fresh child
identities instead of a numeric process-group target. A child worklist supplies
signal targets only; closure requires the registered main child's outcome and
`ECHILD` from a wait that includes Linux clone children. Observation, ownership,
signaling or reaping failures remain typed ambiguity. Inline callers and
non-Linux workers retain the process-group boundary. This proves no absence of
work delegated to unrelated preexisting services or remote processes.

The outer workflow gives native cleanup its bounded grace period. Any forced
workflow SIGKILL, including a leader observed as killed externally, remains
ambiguous even if the outer group is absent: a separately owned native session
may survive. Lifecycle retains the Run lock and publishes no Attempt receipt.
Typed native-group ambiguity also dominates replacement exceptions during Task
handler restoration. A short masked decision revokes native workspace cleanup
authority before signals are unmasked; filesystem cleanup remains interruptible.
These rules do not reconcile a lost Task worker. If the surviving workflow exits
normally with native blockers, lifecycle may release the Run lock and publish a
blocked receipt while preserving native locks and workspaces. That receipt
supplies no descendant-closure or postentry-retry authority. A worker that lacks
the Linux subreaper boundary cannot prove absence outside its owned group.

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
2. Create the workspace and run the producer with that owned scratch directory
   as its working directory, so incidental relative files share its cleanup
   boundary. Frozen file arguments remain absolute. Validators and semantic
   all-pass keep the Run-root working directory. Stop and reap native execution
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

A failed or interrupted scientific Attempt is resumable only after all entered
Tasks have verified results or positive prepublication abort closure. Resume
preserves the same Run, source, Execution Plan, profile, backend, execution mode
and ordered tool identities. An unentered scope has no start; an entered pending
scope binds its latest closed abort and freshly satisfies retry readiness.
Successful processing Runs are complete. Missing finalization or blocked
ambiguity remains preserved and ineligible for automatic retry.

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
| Reporting admission | `not applicable`, `incomplete`, `complete`, `blocked` |

The independent Run-lock observation distinguishes no lock, a local live owner,
remote ownership unverified, a local process that is not live, and invalid or
ambiguous lock state. Host/process observations follow structural lock/Attempt
binding admission; an unbound PID is never probed as an owner. Admitted owner
observations show the recorded host and scheduler ID, without treating those
records as proof of current remote liveness. Remote/ambiguous/dead ownership
continues to block Run admission and recovery. Inspection does not contact a
remote host, remove locks, or infer scientific success from scheduler state.

Scientific task observations reuse the same admitted inspection snapshot at
every display level. Counts distinguish verified completion, verification not
admitted, an admitted start with completion unverified, and no admitted start.
Debug rows use those labels and include retained start references. An admitted
start is evidence of entry, not proof that a worker is still running. No
admitted start can reflect missing or invalid evidence, so it never establishes
that work did not run. These observations add no file reads and change no
Run/Results blockers, recovery decisions or verified-content checks.

The same snapshot retains diagnostic terminal Task-attempt observations from
each admitted Attempt tree, in chain order per Task scope. These require the
existing record and exact log-content checks; a postentry observation must also
match the already admitted start reference and its originating Attempt. Failed
preentry records keep the existing later-start ordering guard. Missing, changed
or malformed records/logs are excluded, with their existing blockers preserved.
Normal output counts these recorded attempts. Verbose/debug output shows their
recorded outcome, original Attempt, record path and content-bound stdout/stderr
paths, with escaped diagnostics. A recorded `succeeded` outcome alone cannot
admit verified scientific completion, Results or recovery. The projection adds
no log reads and does not replace verified Task records or receipt authority.

Recovery availability is a separate fact. A successful processing-only Run has complete Results for its
plan and reporting is not applicable.

A successful full Run invokes reporting after scientific Attempt completion
unless `--no-report` is selected. `emrys report` can independently plan,
generate, or reuse the receipt-bound report transaction. Reporting failure or
regeneration cannot invalidate science and creates neither a Run nor an
Attempt. Result locations are shown only from a fully revalidated report
receipt; incomplete, failed, blocked, or dry-run state prints none.

Normal inspection also shows each reporting transaction's admitted evidence:
`No admitted start`, `Started; completion unverified`, or `Verified complete`.
The same table appears once at every detail level. A start records transaction
entry, not a currently live reporter; reporting begins after the scientific
Attempt releases its Run lock. Output presence cannot replace the completion
record. Incomplete/invalid reporting retains its admission blockers, while
scientific Attempt/Results observations remain separate.

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
| `attempts/<workflow-attempt-id>/` | One immutable Attempt manifest, per-Task starts/results/streams, and receipt published last. |
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
