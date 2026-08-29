# Local-pilot orchestration contract

This document is the binding architecture for EMRYS's first local Snakemake
pilot. B2 implements its closed machine schemas, read-only request normalizer,
reporting projection, and semantic all-pass checker. B3 implements the fixed
local-CMH profile, static fourteen-scientific-owner-rule Snakemake graph, local executor profile,
and generic task boundary that publishes task attempts and content-bound
verified records. B4 implements the three reporting rules and the
internal durable producer-entry, immutable-attempt, terminal-receipt,
between-task-resume, and
read-only-inspection APIs for an already materialized run. B5 implements the
read-only doctor, fixed-profile production materializer, and public dry-run-
first `run`, `resume`, and `inspect local-pilot-run` adapter. No real science-
tool execution has been proven. Current
scientific behavior remains with the
applicable functional owner, and exact semantic identities and artifact edges remain in
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md).

B4 assumes a single-user, cooperative POSIX local workspace with working
advisory `flock` and same-filesystem hard links. It rejects admitted symlink
components, observed leaf substitution, late leaf collisions, unstable bytes,
and open rosters. All sanctioned lifecycle writers hold the acquisition mutex.
It is not a defense against a hostile process replacing a lock leaf in the
narrow post-link, pre-unlink interval, concurrently renaming ancestors, or
changing mount namespaces. Such interference invalidates the evidence boundary
and requires external isolation and explicit reconciliation, never automatic
repair. NFS, network/distributed filesystems, and cluster filesystem semantics
are unproved and unsupported until separate site validation.

The implementation is deliberately source-checkout-bound and uses one local
Snakemake scientific backend. Direct and single-node Slurm placement are
selected through one execution profile and the same `emrys run`/`resume`
control path. Slurm submits the whole Run around that backend; it is not a
second application executor. A distinct Slurm-aware backend, multi-node
execution, a local Linux VM, CSU portability, and an installed standalone
control plane remain later decisions.

## Design outcome

The local pilot has one explicit path:

1. An operator authors one YAML request that references ordered TSV manifests
   and stationary FASTQ/reference inputs.
2. EMRYS validates and normalizes those inputs, then binds one immutable
   Analysis revision and one immutable Execution Plan.
3. A canonical Run binding commits those authorities and determines the
   successor `run_id`; existing `emrys.execution.v1` Runs retain their exact
   historical identity and bytes.
4. Direct public planning prints concise Run identity, work, and reporting
   without writing. A submit-host Slurm dry-run instead prints concise placement
   without building a Run or submitting. Verbose output adds the applicable Run
   root/resources or execution-profile/scheduler-stream detail; `--execute`
   either enters the direct lifecycle or submits that lifecycle into one Slurm
   allocation.
5. One fixed CMH workflow profile projects the semantic DAG into Snakemake.
6. Each workflow task invokes one owner's public producer, that owner's public
   validator, and a generic semantic all-pass check.
7. A content-bound verified task record is published only after all three
   succeed.
8. Required verified tasks automatically feed the existing artifact-index,
   run-summary, and Jinja HTML-report owners. Reporting is not a scientific
   stage.
9. A workflow-attempt receipt is published last. Inspection derives state from
   EMRYS contracts and records, never from Snakemake metadata alone.

There is no request inbox, watcher, database, service, plugin registry, or
automatic recovery subsystem in version 1.

## Authority matrix

| Subject | Authority | Explicit non-authority |
| --- | --- | --- |
| Scientific owner identity and direct artifact edges | [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) | Snakemake rule names, filenames, numeric aliases, and narrative order |
| Producer, validator, output, transaction, and recovery behavior | Applicable owner `README.md` and `CONTRACT.md` | Workflow rules and lifecycle records |
| Operator intent | Admitted YAML request plus referenced ordered TSV manifests | Caller working directory, environment discovery, filename inference, and globs |
| Immutable local-run identity | Successor Analysis-revision and Execution-Plan digests, including the computational resource declaration, committed by the canonical Run binding; exact `emrys.execution.v1` bytes for historical Runs | Request formatting, human label, Attempt placement/realization, workspace, host, reporting, scheduler identity, or Snakemake state |
| Fixed pilot membership and scope expansion | Versioned local CMH workflow profile | A generic registry or automatic owner discovery |
| Scheduling | Attempt-local direct or whole-Run Slurm placement around Snakemake's local executor and static rule graph | A second scientific backend, distributed execution, scientific completion, recovery authority, or evidence promotion |
| Reusable task completion | EMRYS verified task record after owner validation and semantic all-pass gating | Process exit alone, output presence, timestamps, or `.snakemake/` metadata |
| Reporting identity | Explicit projection from the execution contract into the existing artifact run contract | The reporting run contract as a complete execution identity |
| Run state | Immutable workflow-attempt records, verified task records, owner receipts/reports, and observed recovery state | A mutable status cache, log, rendered report, or scheduler state |
| Biological review and interpretation | External research work-process records | EMRYS orchestration, reports, or local computational completion |

Snakemake implements a checked projection of `STAGE_MAP.md`; it never becomes
a second semantic DAG authority. An exact workflow-profile test must compare
the implemented rule edges and scope expansion with the reviewed projection.

## Version 1 scope

The only selected profile is the current paired-CMH workflow:

- reference preparation through historical `00a`, `00b`, and `00c`;
- per-sample compute through `01`, `02`, `04`, `05`, and `06`;
- automatic per-sample evidence `02b` and `03`;
- cohort/analysis work through `07`, `08`, `09`, and the post-Step09
  scientific-context projection `10`;
- artifact indexing, canonical run-summary assembly, and separate
  self-contained scientific and evidence HTML reports.

The `02b` and `03` evidence branches do not gate downstream scientific compute,
but the local profile requires them before workflow completion. Step `10`
projects the completed Step `09` candidate transaction onto one exact indexed
reference and one registered PUM motif; it does not reopen alignments, alter
candidate calls, discover motifs, or perform biological review. Biological
review and interpretation are not owner tasks, artifacts, or completion
states. Step `09`'s two diagnostic PDFs remain native analysis artifacts; this
does not reintroduce a PDF report format.

The first pilot uses only public owner commands and a clean admitted source
checkout. It imports no peer-private Python implementation. Repository shell
and R producer assets are not currently installed package data, so wheel-only
execution is outside this version.

## Intake and normalization

### Authored inputs

The authored YAML request carries only run intent and explicit references:

- request schema version and an optional human label;
- fixed workflow profile identity;
- sample-manifest and partition-manifest paths;
- reference FASTA and GTF paths;
- cohort and primary-analysis identities;
- the complete inline Step `09` analysis policy.

Version 3 uses this closed top-level shape, encoded by the request schema
without adding discovery or extension fields:

```yaml
schema_version: emrys.request.v3
label: optional-human-label
profile: emrys.profile.local_cmh.v2
sample_manifest: samples.tsv
partition_manifest: partitions.tsv
reference:
  id: declared-reference-id
  fasta: reference/genome.fa
  gtf: reference/genome.gtf
  star_index:
    sjdb_overhang: 149
    genome_sa_index_nbases: 14
cohort_id: declared-cohort-id
analysis:
  id: declared-analysis-id
  control_condition: EV
  treatment_condition: PUM1
  rna_ref: A
  rna_alt: G
  min_sample_dp: 1
  mean_dp_threshold: 50
  fdr_threshold: 0.05
  common_or_threshold: 1.2
  absolute_difference_threshold: 0.005
  background_condition: null
  background_max_fraction: 0.01
```

Execution uses one optional explicit `emrys.execution-profile.v1` fragment.
The built-in base supplies conservative resources and direct placement. The
profile combines workflow-wide cores/memory, per-stage concurrency, threads,
and computational/reporting memory with an Attempt-local direct or Slurm
placement request. CLI resource overrides have highest precedence. EMRYS does
not discover adjacent configuration; retired adjacent resource/launcher files
fail closed when no explicit profile is selected.

The effective computational declaration enters the successor Execution Plan
and therefore Run identity. Profile source, reporting memory, placement,
observed allocation, and scheduler job ID remain Attempt context. Changing
placement alone does not create a different Run.

Every field except `label` and `background_condition` is required. Unknown
fields fail admission. The implementation may expose a schema-preserving
starter, but it may not supply hidden scientific defaults during normalization;
the request records the selected policy explicitly.

Repeated sample and partition records remain ordered TSV. The local CMH profile
adds admission requirements without silently tightening the general manifest
validator: `replicate` is required, every stratum has exactly one declared
control and one treatment, at least two complete strata exist, and pairing is
never inferred from sample names.

### Admission rules

Normalization must:

- use safe YAML loading, reject duplicate keys, custom tags, merge keys, globs,
  templates, and environment interpolation;
- resolve relative paths against the request file's directory, never the
  caller's working directory;
- validate the base sample manifest plus the stricter profile requirements;
- preserve manifest row order;
- require explicit regular files and reject unsafe or unresolved path forms;
- compute SHA-256 for the request, manifests, every declared FASTQ, and the
  reference FASTA and GTF; and
- snapshot only the small request, manifests, profile, policy, and normalized
  contracts in their declared run- or attempt-specific locations. Raw reads and
  references remain stationary.

Content hashing is the minimum integrity needed for immutable identity and safe
resume. It is not a general acquisition or provenance program.

### Run authority and historical execution contract

The canonical JSON contract contains at least:

| Component | Bound content |
| --- | --- |
| Contract | Schema identifier and version |
| Profile | Profile ID, version, and digest that binds its rule/owner-contract projection |
| Samples | Ordered normalized rows, resolved mate paths, sizes, and content hashes |
| Partitions | Ordered normalized selectors and manifest hash |
| Reference | Resolved FASTA/GTF paths, sizes, hashes, declared reference identity, and explicit STAR-index parameters |
| Analysis | Cohort ID, primary-analysis ID, and complete policy digest |
| Identity envelope | The exact versioned identity fields above and their canonical digest |

New-format Runs persist canonical `analysis.json`, `execution-plan.json`, and
`run.json`; the Run binding is committed last and is the sole successor Run
authority. Successor Runs do not persist `normalized.json` or an execution
projection. Workflow and task admission consume exact `run.json` bytes.
Reporting inputs are identity-neutral, Attempt-owned projections beneath
`contract/reporting-inputs/<workflow-attempt-id>/`, and the origin workflow
config binds each exact path and SHA-256. The existing
`execution_contract_sha256` field is format-aware: it binds exact `run.json`
bytes for successor Attempts and exact `emrys.execution.v1` bytes for
historical Attempts.

Historical `normalized.json` contains deterministic normalized run content and
its explicit identity envelope and remains byte-for-byte readable and
resumable. Non-identity admission metadata—the original
request hash and bytes, human label, authored path strings, resolved
reporting-resource policy and execution-profile source provenance, placement,
observed outer allocation, and normalization tool identity—belongs to the
immutable workflow-attempt/config records. Reformatting an otherwise
equivalent request, changing its label, or changing placement therefore does
not create a new scientific Run or demand different bytes at the same
canonical contract path.

Canonical authorities use UTF-8 JSON, sorted object keys, no insignificant
whitespace, no NaN/infinity, and SHA-256. Successor identity uses the
domain-separated Run composition over canonical Analysis-revision and
Execution-Plan digests; historical identity retains its existing envelope.
The human label never selects or overwrites a Run.

Workspace, output root, source-checkout path and commit, placement, host,
resource resolution, reporting resources, scratch, exact required-tool
identities, timestamps, PIDs, and scheduler identifiers are Attempt context.
The successor Attempt executor and computational resource declaration are read
from the immutable Execution Plan. Attempt placement records the exact profile
source/digest, request, and optional Slurm job ID; historical allocation records
without placement fields remain readable. File-backed tool identities
bind the authored path, canonical target, observed version, and SHA-256;
admitted runtime directories bind their authored and canonical paths. Each
fixed `r_*` identity binds the observed namespace version, exact canonical
installed-package root, and deterministic tree SHA-256 over sorted entry kind,
relative path, permission mode, size, and regular-file bytes. A package entry
may be a `renv` cache symlink to a canonical real target, but symbolic links and
special entries inside each resolved fixed `r_*` namespace tree fail admission.
Only the admitted `renv_project` and `renv_library` directory identities have
null digests. These fields do not change the scientific run identity. Version 1
automatic resume nevertheless requires the same clean source commit, profile
digest, and ordered exact required-tool identities, then re-admits those paths
and bytes; otherwise the run becomes blocked pending an explicit compatibility
or new-profile decision.
Every local-science attempt has exactly one file-backed
`storage_qualification` identity. Lifecycle re-runs semantic qualification for
the attempt workspace and canonical normalized reference before delegation and
after the child exits, and requires the resulting receipt identity to reproduce
that immutable roster entry.

Each workflow attempt binds one canonical attempt-specific workflow-config
snapshot by relative path and SHA-256. That config binds every owner/scope
dispatch by absolute path and SHA-256, and the task runner admits the exact
expected digest before parsing or invoking a producer. Request snapshot,
attempt, config, dispatch, task-attempt, and verified-record identities therefore
form one explicit chain; neither a pathname nor mutable Snakemake parameters can
substitute for it.

On resume, a completed task keeps the exact predecessor dispatch reference
already bound in its verified record; only pending tasks receive new-attempt
dispatches. Changing producer, validator, input, output, or other dispatch
semantics invalidates reuse instead of asking Snakemake to infer compatibility.

The same identity envelope maps idempotently to the same Run. Non-identity
admission metadata may differ without changing that mapping. A changed bound
input, manifest order, reference, scientific policy, workflow-profile digest,
or computational resource declaration creates a different Run.

## Reporting projection

The current artifact `run_contract` contains only:

- sample-manifest SHA-256;
- reference-contract SHA-256;
- partition-manifest SHA-256;
- primary-analysis ID;
- primary-analysis-policy SHA-256; and
- the canonical digest of those five components.

It does not bind raw FASTQ content, exact reference files, or the workflow
profile. It therefore remains a reporting projection, not the orchestration
identity. Normalization must materialize an explicit
`reference_contract.json`, `primary_analysis_policy.json`, and
`reporting_run_contract.json` from the execution contract. The reference
projection binds its schema version, declared reference ID, normalized
FASTA/GTF paths, sizes and hashes, and STAR-index parameters. The policy
projection binds the complete normalized Step `09` policy. Their canonical
hashes populate the corresponding existing reporting fields; the exact
manifest snapshot hashes populate the manifest fields; and the existing
five-component canonical digest becomes `run_contract_sha256`. The projection
records both execution and reporting digests and their relationship. Artifact
schema version 1 and its historical `step_id` fields remain unchanged until a
separately approved schema migration.

The run-specific artifact inventory is also materialized deterministically
from the admitted profile, samples, partitions, and declared output paths
before compute. It is never discovered afterward by globbing the filesystem.
Generated native-output paths are relative to the immutable run root. The
stationary Step `00c` FASTA, FAI, and dictionary rows instead use normalized
absolute external paths because that owner publishes sidecars beside the
admitted FASTA. Reporting must therefore receive an explicit artifact source
root distinct from the admitted source checkout: the run root resolves
relative inventory paths, while checkout authority continues to bind producer
and renderer code. A workflow may not force the operator workspace beneath the
Git checkout to collapse those authorities.
The profile projects current computational artifacts through Step `10`.
Successful reporting transactions do not create biological evidence, and the
run-summary state or required-missing count is not the workflow completion
Boolean.

## Identity vocabulary

| Identifier | Meaning |
| --- | --- |
| `run_id` | Successor domain-separated Run-binding identity, or the preserved deterministic `emrys.execution.v1` identity for a historical Run |
| `workflow_attempt_id` | One execute or resume invocation for a run |
| `task_attempt_id` | One public owner invocation within a workflow attempt |
| Owner run token | Existing owner-local staging/publication identity |
| Artifact attempt ID | Existing reporting artifact-attempt vocabulary |
| `execution_attempt_id` | Future application-log identity defined by [`LOGGING_CONTRACT.md`](LOGGING_CONTRACT.md) |
| Scheduler job ID | Attempt-local outer-allocation correlation; never Run identity or completion authority |

Workflow and task attempt IDs use
`workflow-YYYYMMDDTHHMMSSZ-<32 lowercase hex>` and
`task-YYYYMMDDTHHMMSSZ-<32 lowercase hex>` respectively. Their embedded UTC
second matches the declared creation/start time and the suffix supplies 128
random bits.

These identities are never aliases. In particular, a workflow attempt is not
an artifact attempt, owner run token, application-log attempt, PID, or future
scheduler job. They are never derived from a PID or used as scientific
identity.

## Filesystem layout

One operator-selected workspace contains immutable run directories:

```text
<workspace>/logs/
  emrys-local-pilot-<slurm-job-id>.out/.err
  application/                    default structured-log root
<workspace>/runs/<run-id>/
  contract/
    samples.tsv
    partitions.tsv
    profile.json
    analysis.json                    successor only
    execution-plan.json              successor only
    run.json                         successor only
    normalized.json                  historical only
    reporting-inputs/<workflow-attempt-id>/
      reference_contract.json         successor only
      primary_analysis_policy.json    successor only
      reporting_run_contract.json     successor only
      artifact_inventory.tsv          successor only
    reference_contract.json           historical only
    primary_analysis_policy.json      historical only
    reporting_run_contract.json       historical only
    artifact_inventory.tsv            historical only
    workflow-configs/<workflow-attempt-id>.json
    dispatch/<workflow-attempt-id>/<machine-key>/<scope-id>.json
  results/                       owner-native outputs and validation reports
  products/                      artifact index, run summary, and two HTML reports
  attempts/<workflow-attempt-id>/
    request.yaml                 exact authored request for this invocation
    attempt.json
    tasks/<machine-key>/<scope-id>/
      task-attempt.json
      stdout.log
      stderr.log
    released-run-lock.json       immutable evidence of outer-lock release
    attempt-receipt.json
  state/task-starts/<machine-key>/<scope-id>.json
  state/verified/<machine-key>/<scope-id>.json
  state/reporting/<transaction-kind>/
    start.json
    verified.json
  locks/run.lock
  .snakemake/
```

Exact native result paths remain profile projections of owner contracts; the
layout above does not rename owner outputs. Contract snapshots and terminal
records are create-exclusive and immutable. A convenience status projection
may be regenerated, but is never authority. `.snakemake/` is disposable engine
metadata and is never a reporting input or EMRYS completion record.

Task stdout/stderr files are opaque command-stream captures for diagnosis; they
are distinct from the Run Attempt application log defined by
[`LOGGING_CONTRACT.md`](LOGGING_CONTRACT.md). After durable task-start
publication, the task boundary opens separate create-exclusive, no-follow
descriptors and drains each child
stream through EOF in bounded chunks. Bytes and order are exact within each
stream; no stdout/stderr interleaving order is claimed. Before task-attempt
publication, both files are fsynced and closed, and bounded pathname hashing
must match the retained descriptor device, inode, size, modification time, and
change time. Each task attempt binds both complete captures by canonical path
and SHA-256; later mutation invalidates that evidence, while log presence or
content never establishes success or promotion. An unexpected interruption may
leave exact partial captures without a task-attempt record; they are post-entry
diagnostic evidence, not completion proof.

## Planning and mutation boundary

The implemented `run` and `resume` interfaces are read-only by default. Their
plan admits the execution profile and reports placement without submitting or
creating workspace, contract, Attempt, logs, locks, or owner outputs. Direct
planning then resolves readiness and identity and shows concise work and
reporting summaries. Verbose adds the Run root, resources/allocation, execution
profile, and scheduler streams; debug adds exact safe engine, scheduler, and
task commands. Execution requires one explicit `--execute` control.

For Slurm placement, `--execute` creates only `<workspace>/logs` on the submit
host, submits once, and prints `JOB_ID`, `OUT`, and `ERR`. The compute delegate
re-admits its profile digest, UID, marker, and scheduler job ID before doctor,
Run planning, or lifecycle mutation. It owns the single application log for
the executing Attempt.

The B5 adapter owns that exact planning and materialization boundary; direct
manual Snakemake invocation is unsupported. A doctor is a distinct read-only
readiness report and never installs or repairs dependencies. Neither planning
nor doctor invokes owner producers or validators.

## Workflow task boundary

One Snakemake job owns one functional-owner scope. Producer and validator are
not separate DAG nodes. A job performs, in order:

1. immutable identity, dispatch, input, and declared-destination preflight;
2. durable create-exclusive publication of the scope's task-start record;
3. protected create-exclusive opening of the task's separate stdout/stderr
   captures;
4. the owner's public producer command, including its owner-local no-clobber
   and recovery-residue preflight;
5. structural admission of the declared native output set;
6. the owner's public validator in execute mode;
7. a generic parser requiring the exact seven-column validation header, at
   least one declared row, and `status=pass` for every row;
8. stable-input rechecks;
9. stream fsync/close, bounded stable hashing, and immutable task-attempt
   publication; and
10. atomic publication of the verified task record.

Validators may publish `status=fail` rows and still exit zero. Consequently,
producer exit, validator exit, and semantic report status are three distinct
facts. A job fails after preserving the validation report when any fact is not
successful.

The task-start record is published only after all read-only orchestration
preflight succeeds and immediately before the first producer call. It binds
the run, execution, profile, workflow attempt, workflow config, exact dispatch,
task attempt, owner, scope, and owner run token. Once this boundary is crossed,
the scope is considered entered: a missing, failed, interrupted, malformed, or
otherwise incomplete post-entry chain is `blocked` and is never automatically
retried in version 1. A scope with no start record remains pending and may be
run by a later attempt.

A failed read-only preflight may retain one attempt-local diagnostic record and
its stdout/stderr captures with `task_start_record=null`, no command execution,
and no native mutation claim. The terminal workflow receipt binds that exact
pre-entry record so deleting it cannot erase history. Because no producer-entry
record exists, a later attempt may retry the scope after the read-only blocker
is corrected. This pre-entry shape is distinct from every post-entry failure.

The verified task record is the rule's scheduling output. Native scientific
outputs, validation reports, receipts, backups, and recovery evidence are not
declared disposable Snakemake outputs. This prevents the engine from deleting
evidence after a failed job. Do not use `directory()` for native result roots,
`temp()` for evidence, or empty `touch()` files as completion proof.

Each verified record binds:

- schema version, `run_id`, execution-contract digest, profile digest, owner
  machine key, scope, workflow attempt, and task attempt;
- exact public commands and exits;
- declared input identities and hashes;
- native output paths, sizes, and hashes;
- native receipt identity when the owner has one;
- validation-report path and hash; and
- `all_pass=true` only after parsing the complete report.

It means only that the local workflow may reuse the declared owner result under
the compatibility rules. It is not an owner-native receipt, cluster proof,
scientific review, or biological validation.

Verified records are create-exclusive. A pre-existing record must validate as
the exact reusable result or the run blocks; an attempt never truncates,
rewrites, or silently replaces one.

## Lifecycle and state

Inspection derives independent read-only dimensions rather than editing one
aggregate state in place:

| Dimension | Derived values and authority |
| --- | --- |
| Run integrity | `valid` or `blocked` from immutable Run/Attempt relationships and owned lock/chain evidence |
| Attempt outcome | `not_started`, `running`, `succeeded`, `failed`, `interrupted`, or `blocked`; complete admitted scientific work is successful independently of downstream reporting |
| Scientific Results | `incomplete`, `complete`, or `blocked` from the exact required verified-task roster and its evidence |
| Reporting | `incomplete`, `complete`, or `blocked` from the three independent reporting ledgers and semantic receipts |
| Recovery | Available only for a failed/interrupted Attempt with incomplete scientific Results and no blocker |

The historical aggregate `state`, `resume_available`, and
`local_pipeline_complete` read-model accessors are retired after all current
callers migrated to these dimensions. Receipt-v1 retains its required
`local_pipeline_complete` field as historical schema evidence, not scientific
completion authority.

A workflow attempt begins with an immutable `attempt.json` and ends with one
receipt published last as `succeeded`, `failed`, `interrupted`, or `blocked`.
Attempts form a linear supersession chain. A terminal attempt is never reopened,
and a completed run refuses another execute or resume operation.

Attempt admission is serialized by a persistent canonical zero-byte advisory
mutex beneath `locks/`. That mutex is benign infrastructure, not attempt or
recovery evidence. EMRYS holds it while revalidating the exact prepared
execute/resume request; only a still-current request may publish `run.lock` or
attempt-specific state. A contender that waited behind a completing attempt
therefore exits without contaminating the completed or resumable run.

The lifecycle process handles an ordinary signal by stopping delegated work,
preserving task and owner state, and proving a between-task boundary when
possible. It publishes the attempt-local immutable
`released-run-lock.json` with a create-exclusive hard link to the owned public
run lock, verifies and synchronizes the shared inode and bytes, rechecks and
unlinks the public name while the cooperative-writer mutex remains held, then
publishes an `interrupted` receipt last and binds that release evidence. A
colliding evidence path is never overwritten. Receipt publication is
signal-masked as one POSIX commit boundary: a signal already recorded becomes
part of the interrupted receipt, while a signal arriving during or after a
successful receipt commit reaches the prior ambient handler only after the
receipt is durable. A nonterminal attempt left by SIGKILL, power loss, or an
unproved delegated process-group termination is not guessed complete or
automatically repaired. Quiescence ambiguity retains the public run lock and
publishes no resumable receipt; a proven-quiescent child plus diagnosed state
blockers may instead release evidence and publish a blocked receipt.
Aggregate release evidence retained before an attempt record exists is not
self-authenticating. Inspection keeps it as a blocker until a separate
reconciliation contract validates its bytes, ownership, and relationship to
the absent attempt; a matching filename alone is never enough.

Snakemake automatic retries are zero. EMRYS version 1 does not expose automatic
`--unlock`, `--cleanup-metadata`, `--forceall`, `--rerun-incomplete`, or blind
force controls.

### Resume

Resume always creates a new workflow attempt. A prior verified task may be
reused only after EMRYS rechecks:

- the execution contract and profile digest;
- the clean source checkout plus every exact required-tool authored path,
  canonical target, version, and file digest or admitted directory identity;
- the exact closed task-start and reporting-start rosters;
- the task-start, task-attempt, and verified-task identity chain;
- the verified-record schema and complete hash bindings;
- every declared native output and native receipt;
- the persisted validation report and all-pass result; and
- that every scope without verified completion has never published its durable
  producer-entry record.

Timestamp freshness and Snakemake completion metadata are insufficient. A
failed or missing recheck never causes automatic deletion or rerun over an
ambiguous output set. It yields `blocked` and routes to the applicable owner
recovery instructions. Version 1 supports only between-task resume. Once an
owner or reporting producer has crossed its durable start boundary, failure or
interruption is not automatically recoverable even when no output appears to
have been written. Version 1 does not automate owner-internal transaction
recovery. Successor resume currently also requires the same normalized backend
projection as its predecessor. Identity-neutral projection changes, including
content-equivalent input relocation, remain same-Run targets but are rejected
until an Attempt-local projection can preserve the complete origin-evidence
chain.

This ledger is automatic-rerun authority, not a claim that inspection can
globally prove the absence of every file a manual or foreign invocation might
leave behind. Each pending owner still performs its existing no-clobber and
recovery-residue preflight when it first enters. If that check refuses foreign
state, the already-entered scope becomes blocked with preserved diagnostics;
the orchestrator never deletes or bypasses the state.

The internal resume invocation uses exactly `--rerun-triggers input` plus
`--ignore-incomplete`, and only after the independent checks above succeed.
Pinned Snakemake characterization requires the latter when an interrupted job
left a fully EMRYS-validated output marked incomplete in disposable engine
metadata. This fixed internal flag does not admit an unverified output, erase
metadata, force a rule, or become an operator-exposed recovery control. Initial
execution never uses it.

## Lock ordering and ownership

The fixed acquisition order is:

1. EMRYS persistent advisory acquisition mutex;
2. EMRYS evidence-bearing run/workflow-attempt lock;
3. Snakemake work-directory lock; and
4. delegated owner-local publication lock.

No path may acquire these in reverse order. The outer lifecycle process owns
aggregate attempt state; jobs write only their task-local records. Existing
owner locks keep their current authority. EMRYS never breaks an owner lock,
deletes recovery residue, or considers a lock stale because time elapsed.

The run lock records run, workflow attempt, process, host, creation time, and an
unpredictable owner token. Terminalization never conditionally unlinks its
public pathname before preserving evidence. It creates the exact absent
attempt-local `released-run-lock.json` as a no-replace hard link, validates and
synchronizes the shared inode and bytes, rechecks the public path, unlinks it
under the cooperative-writer mutex, and publishes the terminal receipt last.
A colliding evidence destination is never overwritten. Observed public-path
changes fail closed, but hostile replacement in the narrow post-link,
pre-unlink interval is outside the cooperative threat model. Every terminal
receipt binds its released-lock evidence; missing, moved, malformed, or
mismatched evidence makes inspection report `blocked`. Owner recovery state
remains untouched.

## Inspection and completion

Inspection reads the normalized contract, exact attempt and task trees,
task-start and verified-task records, reporting start/completion records, owner
receipts and validation reports, and the aggregate run-lock evidence. It
reports pending, entered, verified, failed, resume-available, and blocked
scopes, plus the exact evidence ceiling. It never accepts a caller-supplied
residue list, infers EMRYS state from `.snakemake/`, or repairs what it
observes.

Reporting is invoked automatically by a full Run but remains a separate
non-scientific domain. Each reporting transaction follows the same irreversible
entry policy. Its normal read-only dry-run occurs before `start.json`; the
start is then published
before the execute command. `verified.json` is published only after the command
returns, the native receipt and full transaction are semantically re-admitted,
and the reporting owner's declared control namespace is clean. A reporting
start without that completion evidence blocks resume.

The terminal receipt operation must recheck every required profile scope, bind
the ordered pre-entry diagnostic and task-start rosters, and admit all three reporting
start-to-verification chains before publishing the workflow-attempt receipt.
The legacy combined receipt still records this transaction for compatibility.
Scientific Results and reporting are derived separately and neither establishes
CSU execution, production-scale behavior, validated editing sites, or biological
readiness.

## Explicit deferrals

B0 makes no decision or implementation commitment for:

- a distinct Slurm scientific backend, multi-node execution, local Linux VM,
  CSU portability proof, scheduler accounting integration, or cluster runs;
- dependency installation or repair;
- synthetic-data generation or real science-tool execution;
- a generic assay, stage, plugin, or analysis registry;
- optional-stage and archival-success policy;
- in-code scientific approval or biological-readiness policy;
- public acquisition or a general provenance subsystem;
- logging adoption beyond the `run`/`resume` Attempt boundary or generic gate
  receipts;
- automatic stale-lock cleanup or owner recovery;
- artifact-schema migration or installed workflow assets;
- a wheel-only control plane; or
- Nox.

Current profile membership and semantic edges live in the workflow and
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md); exact admission,
failure, and recovery behavior stays with each owner contract and test suite.
Accepted changes and their acceptance live in the
[findings matrix](../tasks/backlog_matrix.md). Implemented commands belong in
the runbook and owner documentation only after their exact behavior is proven.
