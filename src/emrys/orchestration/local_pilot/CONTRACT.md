# Local-pilot intake contract

## Public onboarding boundary

`emrys init local-pilot --output-dir ABSENT` is dry-run-first and publishes one
external create-absent starter tree only with `--execute`. The parent must
already be a canonical real writable/searchable directory and the target must
not overlap the selected checkout. The owner reserves the output directory,
writes the matched Project, execution profile, sample, partition, and runtime
members create-exclusively, publishes the manifest last, and then re-admits
exact membership, regular-file types, modes, sizes, and bytes.
It never overwrites, adopts, installs, restores, selects reference data, or
guesses site-specific scheduler/tool values. Failure after reservation leaves
the partial directory for inspection with no claim that its manifest is valid.

`emrys validate project --project FILE` calls the canonical Project admission
with the tracked `emrys.profile.local_cmh.v2` contract, then reuses
the reference-contig and GTF-to-BED12 owners to require nonempty FASTA contigs,
usable exon transcript models, matching contig names, in-bounds transcript
coordinates, and in-bounds `region` or `regions_file` partition selectors. It
rechecks every reference/selector content snapshot after compatibility parsing.
It writes nothing and invokes no external tool. Success is input/configuration
compatibility evidence only, not readiness, execution, or scientific evidence.

`emrys prepare local-pilot-runtime` renders the tracked fixed runtime policy to
standard output without writing a file, probing a version, loading a module,
or installing software. Java, Picard jar, Rscript, and the `renv` library must
be explicit paths resolving to canonical real files/directories. The ordinary
command-line tools may be explicit;
an omitted tool is accepted only when the existing absolute PATH entries yield
one distinct resolved executable. Zero or multiple identities fail closed.
The helper changes editable paths and their dependent Picard/R-namespace probe
arguments only; the tracked check roster, expected versions, contexts,
required flags, and descriptions remain unchanged. Doctor owns the later
content binding and actual version/readiness probes.

`emrys init synthetic-local-pilot` uses the same external, dry-run-first,
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
interruption, or noninteractive omission of `--execute` does not submit, create
the workspace, or create logs. Confirmation or explicit `--execute` creates
the canonical `<workspace>/logs` directory, calls `sbatch` once with an exact
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
backend and one materialization/lifecycle contract. Focused equivalence with
fixed resources does not establish real scheduler/site execution,
allocation-sensitive parity, runtime/module portability, failure/recovery
parity, or report-publication parity. Per-owner Slurm scheduling, multi-node
execution, and all 16 stage/utility `.slurm` entry points remain available;
Steps `07` and `08` delegate to Python owners and the other 14 retain their
prior forms.

## Project admission and execution

`normalization.admit_project` is a read-only public Python boundary. It
uses the closed safe YAML loader, resolves paths against the Project directory,
reuses the public Step `08`/`09` manifest contracts, requires at least two
exact control/treatment strata, requires each paired FASTQ row to use one
matching compression mode, snapshots declared regular non-symlink inputs, and
validates the canonical execution contract. Duplicate keys, custom tags, merge
keys, globs, templates, environment/home interpolation, unknown fields, and
ambiguous paths fail admission. Project formatting and the optional human
label do not enter Analysis identity. `ProjectAdmission` retains immutable
source, canonical profile, and canonical construction bytes plus the canonical
Analysis revision. Its definition, profile, and construction mappings are fresh
disposable views and cannot mutate identity or historical compatibility bytes.

`doctor.inspect_local_pilot` and the grouped `emrys doctor local-pilot` route
are the read-only B5 setup boundary. They reuse Project admission plus the runtime-
availability owner's direct API, require the exact fixed local runtime roster
and policy fields before any probe, run R namespace probes with explicit
guarded `renv` variables, compare the selected Python/Snakemake identity, bind
admitted tool/jar bytes and installed R-package trees, and reject a workspace
overlapping the source checkout. The Java path must resolve to canonical
`<JAVA_HOME>/bin/java`; doctor, lifecycle, and GATK owner work share that
selected launcher after ambient JVM/GATK selectors are removed. An absent
workspace is admissible
only as one missing leaf beneath an existing canonical, real,
writable/searchable immediate parent; the doctor plans that leaf but never
creates it. The doctor neither installs nor repairs dependencies, loads
modules, mutates a run, executes Snakemake/scientific owners, or promotes
readiness into local-runtime, scheduler, cluster, scientific-review, or
biological evidence.
Ordinary executable and hash probes are bounded at 30 seconds. Each guarded R
namespace load has a separate 120-second bound and records elapsed/configured
timing in its diagnostic; timeouts remain readiness failures. The selected
`renv_library` is canonical and real, while one installed-package entry may
resolve through a cache symlink only when the loaded namespace and exact
canonical package-tree binding agree on its target.

The grouped `emrys run`, `emrys resume`, `emrys report`, and
`emrys inspect local-pilot-run`
routes are the supported control surface; their planning helpers are private
implementation details. `run` and `resume` require the controlled Python
invocation. With direct placement, a terminal builds and prints one frozen Run
plan, asks once, and executes that same object only after confirmation. Slurm
placement instead confirms the frozen submission plan described above; Run
planning occurs later inside the allocation. Refusal, EOF, or interruption
mutates nothing and opens no log; noninteractive omission of `--execute`
remains no-write, while `--execute` is the explicit automation path. Direct
planning reruns the Doctor, admits the authored Project again, derives the
deterministic Run identity, and prints concise Run identity, combined
pending/reusable work, and reporting information. Verbose output adds the Run
root, admitted Analysis and Execution-Plan identity, and
resources/allocation; debug output adds exact engine and task commands.
Slurm submission output instead adds placement detail, profile and stream paths
at verbose level, and the scheduler command at debug level.
Read-only Run inspection follows the same disclosure boundary: normal uses the
primary Run ID, verbose adds admitted Analysis, Execution Plan, and Attempt
identity plus effective execution facts, and debug adds canonical authority
paths/digests, verified output bindings, receipts, and task evidence.
Historical Runs are labeled and never receive fabricated successor identities.
The tracked four-sample, one-partition starter expands to 35 owner jobs; other
admitted sample/partition counts expand according to the fixed profile. The
control surface exposes no raw Snakemake flags, force, unlock, cleanup, retry,
plugin, or alternate-profile escape hatch.

Each executing Run Attempt owns exactly one application log under the selected
root, which defaults to `<workspace>/logs/application`; Slurm scheduler streams
live under `<workspace>/logs`. After minimal workspace/control admission, the
compute delegate and explicit direct `--execute` path open that log before
semantic planning; confirmed terminal direct execution opens it immediately
after consent and before lifecycle admission. The submission process and
unconfirmed plan own none. The log records publication readiness
before the authoritative Attempt receipt and observes the receipt only after
its durable commit. After initialization, log degradation cannot alter
lifecycle, receipt, recovery, or exit; the log is never completion authority.
After every required scientific/evidence task is verified, lifecycle releases
the Run lock and publishes the v2 Attempt receipt. Reporting then runs
automatically unless `run` or `resume` receives `--no-report`; it is separately
receipt-bound, creates no Run or Attempt, and cannot change the scientific
receipt. `emrys report --run-root RUN_ROOT` plans independently without writes
and generates only with `--execute`. Successful default run/resume reporting,
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
outputs. Existing verified records are reusable only after read-only schema,
identity, content, attempt, receipt, and semantic-report revalidation.

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
For a local-science attempt, those observations include a fresh semantic
admission of the final storage-qualification receipt for the attempt workspace
and the canonical normalized reference FASTA. The observed receipt path,
digest, qualification identifier, and qualified root identities must reproduce
the one immutable `storage_qualification` tool identity before and after the
child; copying the declared identity into the observed roster is not
admission.
SIGINT/SIGTERM is controlled from before mutex acquisition through durable
receipt or recovery disposition and is forwarded at most once to the delegated
process group. Terminal success, failure, interruption, or a diagnosed state
blocker may release the lock and publish a receipt only after that group is
proved absent. A missing terminal observation or inability to prove process-
group quiescence retains the public run lock and publishes no resumable
receipt. Bounded TERM then KILL escalation covers members that remain in the
original process group after the leader exits; SIGKILL, power loss, and a
descendant deliberately escaping the delegated session/group are excluded.

This implementation requires POSIX signal masking and a doctor-admitted final
storage-qualification receipt for the workflow parent and Step `00c` sidecar
parent. The two-phase compute/head probe must reconcile same-filesystem hard
links, advisory `flock` contention, atomic rename visibility, write/fsync,
numeric UID/GID access, mount identity, and post-allocation durability.
Network/distributed storage remains unsupported until that exact receipt
finalizes. A node-local root invisible after the allocation cannot qualify;
there is no implicit stage-in/stage-out or copy exception.

If attempt establishment fails after the public lock is acquired but before a
complete attempt record exists, lifecycle still atomically retains the lock as
`locks/released-<workflow-attempt-id>-run-lock.json`. That aggregate recovery
evidence is never auto-deleted; inspection treats it, the partial attempt
directory, or both as blocked state requiring explicit reconciliation.
The retained filename alone never proves reconciliation.

Only failed/interrupted scientific between-task boundaries are automatically resumable. Resume
requires the same run, profile, execution, source commit, executor, execution
mode, and ordered tool identities. The closed task-start ledger must prove that
every entered scope has a succeeded task-attempt and verified-task chain; an
unverified scope must have no start, though an exact receipt-bound pre-entry
failure may remain in an earlier attempt. Independent reporting state does not
gate scientific resume. Its fixed Snakemake arguments add
`--rerun-triggers input --ignore-incomplete`; this accepts already-admitted
EMRYS evidence despite engine metadata, but does not rerun or repair incomplete
owner state. Blocked attempts remain blocked: B4 defines no reconciliation
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
| `products/native/` | Nonfinal native workflow artifacts and owner QC/validation outputs required for evidence, reuse, and downstream computation. |
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

The B6 proof extends the B5 adapter evidence to a clean fresh clone with the
locked workflow environment. It exercises the top-level parser using explicit
repository-only no-science collaborators and leaves the shipped command default
unchanged, with no fake mode or raw-engine option. Separate clean-success and
controlled between-task failure/resume paths cover all 35 owner jobs, the three
downstream reporting transactions, byte-preserving reuse, final inspection, and
completed-run refusal. These are local structural/no-science workflow facts,
not real science-tool or cluster proof, completed scientific review, or
biological validation.
