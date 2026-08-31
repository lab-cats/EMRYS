# Local-pilot intake contract

## Public onboarding boundary

`emrys init project` is dry-run-first and publishes only with `--execute` into
one absent external root beneath a canonical writable/searchable parent. It
validates supplied strict manifests and referenced data, records the manifests'
admitted absolute paths without copying inputs, creates mode-`0700` `runs/`,
`logs/`, and `runtime/`, publishes generated `emrys.project.v1` `project.yaml` last,
then re-admits exact tree types, modes, sizes, and bytes before full Project
validation. No execution/runtime profile, Results, Run, Attempt, or log is
created. Failure
preserves the partial root and never overwrites or adopts it.

The canonical `project.yaml` parent is the Project root derived by ordinary
run and Doctor routes. Results exist only under `runs/<run-id>/results`.

`emrys validate project --project FILE` calls the canonical Project admission
with the tracked `emrys.profile.local_cmh.v2` contract, validates every named
Analysis, then reuses
the reference-contig and GTF-to-BED12 owners to require nonempty FASTA contigs,
usable exon transcript models, matching contig names, in-bounds transcript
coordinates, and in-bounds `region` or `regions_file` partition selectors. It
rechecks every reference/selector content snapshot after compatibility parsing.
It writes nothing and invokes no external tool. Success is input/configuration
compatibility evidence only, not readiness, execution, or scientific evidence.

`emrys runtime discover [--project FILE]` derives one Project and resolves the
active environment against the tracked fixed runtime policy. It loads no
module, installs nothing, and silently selects nothing: a missing or ambiguous
tool, jar, Python/Snakemake environment, R installation, library, or required
namespace fails closed. The default is a no-write inventory. `--execute`
publishes the admitted bytes only at `<project-root>/runtime/runtime.tsv` and
re-admits that file; it does not create another runtime identity or accept a
caller-selected output path. Any existing profile is preserved and fails
publication, including byte-identical content. Ordinary run, resume, and Doctor
routes derive the canonical profile from the Project. The generic
profile-driven `emrys inspect runtime-availability` route remains the advanced evidence
surface and does not establish the ordinary Project runtime authority.

`emrys init synthetic` uses the same external, dry-run-first,
create-absent publication policy. Its closed `--dataset-profile` selector
defaults to `smoke-v1` (130 pairs per library on 100 kb) and also admits
`production-like-v1` (100,000 pairs per library on 5 Mb). The larger profile
retains the exact engineered core while adding globally disjoint deterministic
neutral templates and an explicit deliberate-duplicate subset. Dry-run plans
either profile without generating its reference or FASTQs. Execute writes the
reference, annotation, four paired libraries, matched manifests, and explicit
metadata, validates its own Project before publishing `fixture.manifest.json`
last, and then re-admits the complete transaction. The metadata's expected
    three Step 09 computational candidates, one significant candidate, complete
    scientific Results through Step 10, and complete default reporting are
    deterministic synthetic expectations, not production
data, scientific review, or biological interpretation.

`emrys run` and `emrys resume` accept at most one explicitly selected closed
`emrys.execution-profile.v1` YAML fragment. The built-in base supplies
conservative resources and direct placement. An explicit fragment may replace
the Run-bound computational declaration and select Attempt-local direct or
Slurm placement; resource CLI flags have highest precedence. There is no
adjacent discovery or environment interpolation. Retired adjacent
`emrys.resources.yaml` or `emrys.launcher.yaml` files therefore fail closed
when no execution profile is selected.

Slurm placement submits the whole Run as exactly one node/task/allocation and
delegates back to the same grouped control path inside it. EMRYS constructs one
frozen submission plan; a terminal displays its placement summary and asks
before submitting that same object once. Refusal, EOF,
interruption, or noninteractive omission of `--execute` does not submit or
create logs. Confirmation or explicit `--execute` admits the canonical
`<project-root>/logs` directory, calls `sbatch` once with an exact
argument vector and stdin batch program, and prints `JOB_ID`, `OUT`, and `ERR`.
Ambient `SBATCH_*` and private transport variables are removed before
submission. Omitted account, partition, QOS, memory, and node-list fields defer
to site policy; explicit values are emitted once.

The private compute delegate requires the bound effective-profile digest,
submit UID, internal marker, and a positive `SLURM_JOB_ID` before module,
scratch, doctor, or workflow work. Module mode is closed to `none` or `exact`;
exact mode loads only its admitted initializer and roster. The delegate creates
one mode-`0700` directory below the admitted scratch parent, exports it as
`TMPDIR`, and removes it on exit. Doctor and resource/allocation resolution run
inside the allocation. The effective workflow totals must fit the observed
CPU and memory capacity.

Placement source/digest, Project source, and scheduler job ID are Attempt provenance,
not Run identity or completion authority. Direct and Slurm use one scientific
backend and one materialization/lifecycle contract. Hosted 130-pair
direct/disposable-single-node-Slurm execution proves matching immutable
authority, Attempt common fields/task roster, path-neutral science, and
symbolic resources. Each placement separately admits successful
receipt/reporting and one application log; effective allocation and scheduler
streams differ as intended. It does not establish the 100,000-pair case, institutional site/module
portability, failure/recovery parity, multi-node or production execution,
scientific review, or biological validation. Owner-local scheduler entry
points are retired; the private whole-Run batch bootstrap remains.

## Project admission and execution

`normalization.admit_project` is a read-only public Python boundary. It
admits the mutable authored file into an immutable `ProjectAdmission` snapshot,
uses the closed safe YAML loader, resolves paths against the Project directory,
reuses the public Step `08`/`09` manifest contracts, requires at least two
exact control/treatment strata, requires each paired FASTQ row to use one
matching compression mode, snapshots declared regular non-symlink inputs, and
validates the closed project-v1 contract. Shared Dataset and Reference inputs
are admitted once; every named Analysis separately binds its partition
semantics and policy, with repeated partition-manifest spellings cached during
that admission. Exact Project and manifest bytes remain parse/provenance
snapshots; canonical normalized scientific content is the order-neutral
Analysis identity authority. Duplicate keys, custom tags, merge
keys, globs, templates, environment/home interpolation, unknown fields, and
ambiguous paths fail admission. The Analysis mapping key is a human selector
and retained Attempt metadata; it does not enter the content-derived Analysis
identity. `ProjectAdmission` retains the immutable admitted source snapshot and all
immutable Analysis revisions; `ProjectAdmission.select_analysis()` selects by
name and permits omission only when exactly one Analysis exists. Active Project
commands reject request-v3. Its schema and admission path remain private solely
for exact historical resume compatibility.

`doctor.inspect_local_pilot` is the read-only internal readiness capability used
by Run and resume. The top-level `emrys doctor` route composes it into one
Project-aware readiness and explicit managed-repair boundary. They derive
`<project-root>/runtime/runtime.tsv`, reuse Project admission plus the runtime-
availability owner's direct API, require the exact fixed local runtime roster
and policy fields before any probe, run R namespace probes with explicit
guarded `renv` variables, compare the selected Python/Snakemake identity, bind
admitted tool/jar bytes and installed R-package trees, and reject a Project
root overlapping the source checkout. The Java path must resolve to canonical
`<JAVA_HOME>/bin/java`; doctor, lifecycle, and GATK owner work share that
selected launcher after ambient JVM/GATK selectors are removed. The Project
root must be canonical, real, writable, searchable, and external to the source
checkout. Diagnosis, detail projection, help, repair preview, refusal, EOF, and
interruption before repair authority write nothing and open no application
log. Diagnosis never loads modules, mutates a Run, executes
Snakemake/scientific owners, or promotes readiness into local-runtime,
scheduler, cluster, scientific-review, or biological evidence.

`emrys doctor --repair` separately plans the supported managed-runtime repair.
Terminal mutation requires confirmation; noninteractive mutation requires the
combined `--repair --execute`. Repair may create one Project-owned direct
storage receipt after bounded single-host probes. Managed-runtime repair
supports Linux x86-64 only, requires the active checkout-owned `.venv`, and
permits writes only to that environment and Project-owned `runtime/managed`,
plus create-absent publication of `runtime/runtime.tsv`. `uv`, Pixi, and `renv`
remain the package-solving and installation authorities. Doctor orchestrates
the selected storage/runtime actions, owns one maintenance application log
beginning after authority and before mutation, and re-runs complete Project
readiness afterward. A ready site/user profile is never overwritten, migrated,
or passed through package-manager repair; declared input files and workflow
outputs are outside repair ownership. Ambient Pixi configuration is disabled
and Project-local Pixi configuration is rejected so it cannot redirect managed
environments beyond that boundary.
The advanced storage-evidence command retains
`inspect storage-qualification --workspace PROJECT_ROOT`; this explicit
two-phase Slurm/site probe is not an ordinary Project/workspace choice.
Ordinary executable and hash probes are bounded at 30 seconds. Each guarded R
namespace load has a separate 120-second bound and records elapsed/configured
timing in its diagnostic; timeouts remain readiness failures. The selected
`renv_library` is canonical and real, while one installed-package entry may
resolve through a cache symlink only when the loaded namespace and exact
canonical package-tree binding agree on its target.

The grouped `emrys run`, `emrys resume`, `emrys report`, and
`emrys inspect run`
routes are the supported control surface; their planning helpers are private
implementation details. Their public model is
`Project -> named Analysis -> immutable Run -> Results`. `run --analysis NAME`
selects exactly one Analysis, with omission allowed only for a single-Analysis
Project. Resume takes an existing Run root and cannot change that selection.
`emrys run --through processing` creates a distinct immutable Execution Plan
and Run whose nonempty predecessor-closed stopping roster selects the
evidence-complete, all-sample Steps `00`–`06` closure. The fixed four-sample
fixture expands this closure to 31 owner tasks. The default remains the full Steps
`00`–`10` Analysis. Reporting is not applicable to a processing-boundary Run;
successful completion is terminal and not resumable. This slice establishes
the reusable processing authority. `run --from-processing-run RUN_ID` admits one
exact successful processing Run from the same Project and creates a distinct
complete downstream Run. The target plan binds the source Run, successful
workflow Attempt, and receipt; normalized samples, Reference, and execution
semantics must match exactly except the plan's source/stopping fields. Source
Steps `00`–`06` artifacts remain stationary and
content-bound, while the target executes and owns only Steps `07`–`10`, its
evidence, Results, reports, and log. Resume preserves the immutable source
relationship. No source task record is copied or adopted, and no Artifact Store
or second manifest authority is introduced. Authored subsets and generalized
modular downstream analyses remain ANALYSIS-01/ANALYSIS-02 work.
`run` and `resume` require the controlled Python invocation. With direct
placement, a terminal builds and prints one frozen Run
plan, asks once, and executes that same object only after confirmation. Slurm
placement instead confirms the frozen submission plan described above; Run
planning occurs later inside the allocation. Refusal, EOF, or interruption
mutates nothing and opens no log; noninteractive omission of `--execute`
remains no-write, while `--execute` is the explicit automation path. Direct
planning reruns the Doctor, admits the authored Project again, derives the
deterministic Run identity, and prints concise Run identity, combined
pending/reusable work within that Run, and reporting information. Verbose output
adds the Run root, admitted Analysis and Execution-Plan identity, and
resources/allocation; debug output adds exact engine and task commands.
Slurm submission output instead adds placement detail, profile and stream paths
at verbose level, and the scheduler command at debug level.
Read-only Run inspection follows the same disclosure boundary: normal uses the
primary Run ID, verbose adds admitted Analysis, Execution Plan, and Attempt
identity plus effective execution facts, and debug adds canonical authority
paths/digests, verified output bindings, receipts, and task evidence.
Historical Runs are labeled and never receive fabricated successor identities.
The fixed four-sample, one-partition synthetic fixture expands to 35 owner jobs
for the default full Run and 31 for the processing boundary; other admitted
sample/partition counts expand according to the fixed profile. The
control surface exposes no raw Snakemake flags, force, unlock, cleanup, retry,
plugin, or alternate-profile escape hatch.

Each executing Run Attempt owns exactly one application log under the selected
root, which defaults to `<project-root>/logs/application`; Slurm scheduler
streams live under `<project-root>/logs`. After minimal Project-root/control admission, the
compute delegate and explicit direct `--execute` path open that log before
semantic planning; confirmed terminal direct execution opens it immediately
after consent and before lifecycle admission. The submission process and
unconfirmed plan own none. The log records publication readiness
before the authoritative Attempt receipt and observes the receipt only after
its durable commit. After initialization, log degradation cannot alter
lifecycle, receipt, recovery, or exit; the log is never completion authority.
After every selected scientific/evidence task is verified, lifecycle releases
the Run lock and publishes the v2 Attempt receipt. For a full Run, reporting
then runs automatically unless `run` or `resume` receives `--no-report`; it is
separately receipt-bound, creates no Run or Attempt, and cannot change the
scientific receipt. A processing Run has no applicable reporting transaction.
`emrys report --run-root RUN_ROOT` plans independently without writes and
generates only with `--execute`. Successful default run/resume reporting,
successful independent generation or reuse, and completed final inspection
print a short `Results:` block with the scientific report first and evidence
report second. Those absolute locations are carried from the fully revalidated
report receipt; dry-run, failed, blocked, incomplete, or unverified state prints
no result locations. Inspection also prints one deterministic next supported
action derived from the separated Run, Attempt, Results, reporting, and recovery
domains; blocked evidence is preserved and never presented as resumable. The
dashboard does not derive or display result locations or recovery guidance.

`materialization.build_attempt_plan` is the sole production projection from
the fixed profile to owner commands, declared inputs/outputs, validation
reports, immutable task dispatches, reporting projections, workflow config,
and workflow-attempt record. Initial run skeleton creation is create-absent.
For successor Runs, the Attempt executor value comes from the admitted
immutable Execution Plan; historical Runs retain their fixed `local` value.
Lifecycle first holds the persistent zero-byte `locks/acquire.mutex` advisory
mutex and revalidates the exact prepared attempt under that serialization
boundary. The mutex is infrastructure, not run evidence. Only an admissible
current execute/resume then publishes the evidence-bearing aggregate run lock
before attempt-specific directories, dispatches, config, request snapshot, or
attempt record. A stale waiting contender exits before its materializer runs
and leaves no attempt, dispatch, config, or released-lock residue. Resume
retains only independently revalidated predecessor dispatches for verified
scopes and materializes new dispatches for the unentered remainder.

Every authored file path passes one lexical policy before access. Admission
opens the file without following a final symbolic link, verifies that the open
descriptor and pathname name the same inode before and after reading, and binds
the exact descriptor bytes. Project YAML, path-based profile JSON, and sample
and partition TSV parsing consume those admitted bytes without reopening the
pathname.

The neutral `emrys.contracts.orchestration.projection.project_reporting` API
deterministically derives the existing six-field artifact run contract and
explicit inventory bytes. Generated paths are run-root-relative; stationary
Step `00c` FASTA and sidecar paths may be absolute normalized external paths.
The projection does not discover files or promote reporting identity into
workflow identity.

The public `python -I -m emrys validate all-pass` route reads one explicit
owner-validation report and writes nothing. It requires the exact shared
seven-column validation header, at least one well-formed check row, the
declared step and scope on every row, unique nonempty `check_id` values, and
`status=pass` for every row.

Success exits `0` and reports the absolute lexical input path, SHA-256 of the
exact parsed bytes, row count, and ordered check IDs. A malformed, mismatched,
empty, or nonpassing report exits `1`; argument-usage errors exit `2`. The
checker publishes no receipt and does not infer success from validator exit,
output presence, Snakemake metadata, or timestamps.

The internal task module consumes one closed, run-contained dispatch. It binds
the canonical execution/profile snapshots and selected owner scope; captures
the exact public producer, validator, and semantic commands; rechecks inputs,
outputs, validation report, and native receipt; publishes an immutable task
attempt on admitted success or failure; and publishes a create-exclusive
verified-task record only on complete success. Only the exact Step `00c`
FAI/dictionary pair may be stationary external outputs, and its FASTA and
parent must be canonical before producer invocation. That pair may be reused
only when both files already exist as stable regular files; a partial pair is a
pre-entry failure. Reused bytes and file identities are rechecked across
producer execution, validation, semantic gating, and immediately before
verified-task publication. Every other native destination remains
create-absent.

After identity and owner-native preflight, the task boundary durably publishes
the fixed `state/task-starts/<machine>/<scope>.json` record immediately before
producer invocation and applies the binding [task-stream
rules](../../../../docs/design/ORCHESTRATION_CONTRACT.md#filesystem-layout):
create-exclusive/no-follow files, bounded draining through EOF, exact bytes and
order within each stream, fsync/close, descriptor/path identity, bounded hashes,
and post-attempt revalidation. No ordering between streams is claimed. A
post-start task attempt must bind that exact start record and end in a succeeded
task-attempt plus verified-task chain to be reusable.
If admission fails before start publication, the exact failed task attempt and
its two logs are retained as a bound pre-entry diagnostic; because the owner
never entered, a later attempt may retry that scope without erasing the earlier
record. An unexpected interruption after stream creation preserves available
partial bytes but publishes no terminal attempt or verified record. Every task
attempt binds both log paths and SHA-256 values; later mutation or truncation
blocks completion and resume. Log presence or content never establishes task
success.

Snakemake schedules only verified-task records. Native artifacts, validation
reports, receipts, logs, and recovery evidence are never disposable workflow
outputs. Within the same Run, existing verified records are reusable only after
read-only schema, identity, content, attempt, receipt, and semantic-report
revalidation.

The internal lifecycle owns aggregate serialization before Snakemake. It holds
the admitted advisory mutex from stale-attempt revalidation through receipt or
recovery publication. A create-exclusive run lock is acquired only after that
revalidation and before an exact absent attempt directory is created. Lock
release creates the exact absent attempt-local immutable
`released-run-lock.json` as a no-replace hard link to the owned public lock,
re-admits the shared inode and bytes, durably synchronizes the evidence, and
then rechecks and unlinks the public name while the advisory mutex remains
held. A colliding evidence name preserves both it and the public lock and fails
closed; no rename or replacement publication may overwrite foreign evidence.
Correctness assumes every sanctioned lifecycle writer holds the mutex.
Descriptor/path checks reject observed changes, but a hostile concurrent leaf
replacement in the narrow post-link, pre-unlink interval is outside the threat
model and invalidates the evidence. The retained inode and bytes are bound by
the terminal receipt published after release.
The attempt binds canonical
execution, profile, and attempt-local workflow-config bytes; the config
transitively binds each dispatch. The executor argument binds the exact reviewed
`workflow/Snakefile` and absolute checked-in local workflow profile beneath the
declared clean checkout, preventing run-directory profile shadowing. It invokes
Snakemake only as `<bound-python> -X pycache_prefix=/dev/null -I -m snakemake`;
the exact lexical venv
launcher, its stable executable target, Python version, Snakemake module
version, normalizer path, and config are admitted as one runtime identity.
Runtime source checkout and required-tool identities are observed before
mutation and again after the child exits. The subprocess environment removes
inherited noninteractive-shell startup hooks before Snakemake starts.
For a scientific Attempt, those observations include fresh semantic admission
of the placement-appropriate storage receipt for the Project root and canonical
normalized reference FASTA. Direct placement accepts the Doctor-owned
single-host receipt or the stronger final two-phase site receipt; Slurm
placement requires the latter.
The observed receipt path, digest, qualification identifier, and qualified root
identities must reproduce the one immutable `storage_qualification` tool
identity before and after the child; copying the declared identity into the
observed roster is not admission. Historical Attempts without placement retain
the two-phase requirement, and a direct receipt can never admit Slurm.
SIGINT/SIGTERM is controlled from before mutex acquisition through durable
receipt or recovery disposition and is forwarded at most once to the delegated
process group. Terminal success, failure, interruption, or a diagnosed state
blocker may release the lock and publish a receipt only after that group is
proved absent. A missing terminal observation or inability to prove process-
group quiescence retains the public run lock and publishes no resumable
receipt. Bounded TERM then KILL escalation covers members that remain in the
original process group after the leader exits; SIGKILL, power loss, and a
descendant deliberately escaping the delegated session/group are excluded.

This implementation requires POSIX signal masking and a Doctor-admitted
placement-appropriate receipt for the Project root and Step `00c` sidecar
parent. Direct qualification proves same-host hard links, advisory `flock`
contention, atomic rename visibility, and write/fsync under the current
host/UID/GID and exact root identities; it makes no cross-node or
post-allocation claim. Slurm's two-phase compute/head probe additionally
reconciles numeric access, mount identity, and post-allocation durability.
Network/distributed storage remains unsupported for Slurm until that exact
site receipt finalizes. A node-local root invisible after the allocation cannot
qualify Slurm; there is no implicit stage-in/stage-out or copy exception.

If attempt establishment fails after the public lock is acquired but before a
complete attempt record exists, lifecycle still atomically retains the lock as
`locks/released-<workflow-attempt-id>-run-lock.json`. That aggregate recovery
evidence is never auto-deleted; inspection treats it, the partial attempt
directory, or both as blocked state requiring explicit reconciliation.
The retained filename alone never proves reconciliation.

Only failed/interrupted scientific between-task boundaries are automatically
resumable. A successful processing-boundary Run is complete and cannot be
resumed into downstream work; that work requires a new Run. Resume requires
the same run, profile, execution, source commit, executor, execution
mode, and ordered tool identities. The closed task-start ledger must prove that
every entered scope has a succeeded task-attempt and verified-task chain; an
unverified scope must have no start, though an exact receipt-bound pre-entry
failure may remain in an earlier attempt. Independent reporting state does not
gate scientific resume. Its fixed Snakemake arguments add
`--rerun-triggers input --ignore-incomplete`; this accepts already-admitted
EMRYS evidence despite engine metadata, but does not rerun or repair incomplete
owner state. Blocked attempts remain blocked: the lifecycle defines no reconciliation
record that can supersede their historical ambiguity.

The contract package owns JSON parsing, validation, and canonical bytes;
inspection owns reusable direct-path admission for schema-named immutable
orchestration records. It reads the attempt chain, bound configs and receipts,
closed ledgers, verified content, and the live lock. Hash-bound, schema-free,
in-memory, mutation, and owner-specific semantics remain owner-local. Inspection
ignores `.snakemake/`, performs no repair, and treats deletion as a blocker
rather than inferring state from timestamps or output presence.

## Run-root output contract

The run root is one durable, content-bound execution history. Preserve it as a
unit; a copied result or report without its bound records is not adopted as a
completed EMRYS run.

| Location | Durable contents |
| --- | --- |
| `contract/` | Successor Analysis, Execution Plan, and Run records (or historical normalized execution), fixed profile, admitted runtime snapshot, reporting inputs, workflow configs, and task dispatches. |
| `attempts/<workflow-attempt-id>/` | Attempt record, owner-task attempts and terminal logs, and the attempt receipt published last. |
| `state/task-starts/` | Immutable producer-entry records. |
| `state/verified/` | Hash-bound successful owner-task records. |
| `state/reporting/` | Start and verified records for artifact index, run summary, and report publication. |
| `results/` | Scientist-facing results only. Current Runs contain `editing/`, `scientific_context/`, and `reports/`; scratch and nonfinal workflow products do not belong here. |
| `results/editing/` | Step `09` candidate tables, summary, mutation spectrum, and diagnostic PDFs. |
| `results/scientific_context/` | Step `10` candidate context, motif, population, enrichment, and receipt. |
| `results/reports/<run-id>/` | Self-contained scientific and evidence-and-operations reports, renderer summary TSV, and the report receipt published last. |
| `products/native/` | Nonfinal native workflow artifacts and owner QC/validation outputs required for evidence, same-Run resume, and selected downstream computation. |
| `products/artifact-summary/<run-id>/records/` | Canonical records for every declared artifact, including explicit incomplete or unavailable state. |
| `products/artifact-summary/<run-id>/<run-id>.artifacts.tsv` | Deterministic artifact index. |
| `products/artifact-summary/<run-id>/<run-id>.artifact_receipt.tsv` | Artifact-index receipt, published last for that transaction. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Canonical machine-readable run summary. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | Tabular run-status summary. |
| `products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC projection. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary_receipt.tsv` | Run-summary receipt, published last. |
| Beside the declared FASTA | Step `00c` `.fai` and `.dict`, the only owner outputs outside the run root. |

Locks, released-lock evidence, partials, backups, task logs, and failed attempts
are not disposable merely because a later output exists. Exact report-bundle
members and their receipt semantics belong to the
[`reporting` owner](../../reporting/README.md).

An exactly bound historical profile may retain a verified report transaction at
`products/report/<run-id>/`; that location is read-only historical evidence, not
a second current publication root. The changed fixed-profile bytes deliberately
produce new Run identities. Historical Runs remain inspectable, but current
Project admission does not make an old-layout Run automatically resumable. During
that read-only inspection, artifact-index, run-summary, and report ledgers use
their receipt-bound artifact roster and recorded producer identities rather
than today's producer registry, while the current checkout acts only as the
reader; current-profile validation and all publication paths retain strict
current-checkout attestation.

Every new or historical Attempt retains the exact
`emrys.workflow-attempt.v1` record shape. Its
`attempts/<workflow-attempt-id>/request.yaml` member stores the exact admitted
Project source under the established historical evidence name; the record's
request-era field names likewise remain evidence metadata rather than a public
request-v3 interface.

The clean fresh-clone proof exercises public control with the locked workflow
environment and explicit repository-only no-science collaborators. It leaves
the shipped command default unchanged, with no fake mode or raw-engine option.
Separate clean-success and
controlled between-task failure/resume paths cover all 35 owner jobs, the three
downstream reporting transactions, byte-preserving reuse, final inspection, and
completed-run refusal. These are local structural/no-science workflow facts,
not real science-tool or cluster proof, completed scientific review, or
biological validation.
