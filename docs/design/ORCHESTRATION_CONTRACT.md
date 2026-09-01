# Local-pilot orchestration contract

This document is the binding architecture for EMRYS's current local Snakemake
backend. The orchestration contract package owns closed machine schemas,
canonical identities, reporting projection, and semantic all-pass admission.
The checked-in processing profile and one immutable selected analysis-module
tail compose the Run-specific graph. Each task delegates through one boundary
that publishes task-attempt and content-bound verified records. Lifecycle and
reporting owners publish durable entry,
Attempt, receipt, reporting, recovery, and read-only inspection evidence.
Project-aware Doctor, composed-profile materialization, and the dry-run-first
`run`, `resume`, `report`, and `inspect run` commands form the public control
surface. Scientific behavior remains with the applicable functional owner, and
exact semantic identities and artifact edges remain in
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md).

The transaction layer assumes a single-user, cooperative POSIX local workspace with working
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

1. A scientist authors one YAML Project definition containing a shared Dataset
   and Reference plus one or more named Analyses that reference ordered TSV
   manifests and stationary FASTQ/reference inputs.
2. EMRYS validates every named Analysis. `run` selects exactly one, then binds
   its immutable Analysis revision and one immutable Execution Plan.
3. A canonical Run binding commits those authorities and determines the
   successor `run_id`; existing `emrys.execution.v1` Runs retain their exact
   historical identity and bytes.
4. Direct public control prints concise Run identity, work, and reporting, then
   either enters that exact plan after terminal confirmation or stops without
   writing. Submit-host Slurm control similarly confirms one exact placement
   plan before one submission. Noninteractive omission of `--execute` remains
   no-write/no-submit; `--execute` is the explicit automation path. Verbose
   output adds the applicable Run root/resources or
   execution-profile/scheduler-stream detail.
5. Planning composes the checked-in processing profile through Step `08` with
   one explicitly admitted analysis-module tail containing one Step `09` task
   and optional Step `10` task, then projects that immutable DAG into Snakemake.
6. Each workflow task invokes one owner's public producer, that owner's public
   validator, and a generic semantic all-pass check.
7. A content-bound verified task record is published only after all three
   succeed.
8. After every required task is verified, lifecycle releases the Run lock and
   publishes a v2 workflow-attempt receipt last.
9. Public control then invokes the fixed artifact-index → run-summary → HTML
   transaction sequence by default. The selected module reporter owns bespoke
   scientific rendering while the EMRYS core owns evidence/operations output.
   `--no-report` disables only that downstream
   work, and `emrys report` can plan or generate it independently. Reporting is
   not a scientific stage and creates neither Run nor Attempt.
10. Inspection derives state from EMRYS contracts and records, never from
    Snakemake metadata alone.

There is no Project inbox, watcher, database, service, mutable plugin registry, or
automatic recovery subsystem in version 1.

## Authority matrix

| Subject | Authority | Explicit non-authority |
| --- | --- | --- |
| Scientific owner identity and direct artifact edges | [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) | Snakemake rule names, filenames, numeric aliases, and narrative order |
| Producer, validator, output, transaction, and recovery behavior | Applicable owner `README.md` and `CONTRACT.md` | Workflow rules and lifecycle records |
| Scientist intent | Admitted YAML Project definition plus referenced ordered TSV manifests | Caller working directory, environment discovery, filename inference, and globs |
| Immutable local-run identity | Successor Analysis-revision and Execution-Plan digests, including the computational resource declaration, committed by the canonical Run binding; exact `emrys.execution.v1` bytes for historical Runs | Project formatting, human Analysis name, Attempt placement/realization, workspace, host, reporting, scheduler identity, or Snakemake state |
| Run-specific membership and scope expansion | Versioned processing profile composed with the explicitly selected installed module descriptor | A universal Stage hierarchy, workflow language, mutable registry, or filesystem discovery |
| Scheduling | Attempt-local direct or whole-Run Slurm placement around Snakemake's local executor and static rule graph | A second scientific backend, distributed execution, scientific completion, recovery authority, or evidence promotion |
| Reusable task completion | EMRYS verified task record after owner validation and semantic all-pass gating | Process exit alone, output presence, timestamps, or `.snakemake/` metadata |
| Reporting identity | Explicit projection from the execution contract plus selected reporter-package and core-renderer identity in the report receipt | The reporting run contract or reporter identity as Analysis or Run identity |
| Run state | Immutable workflow-attempt records, verified task records, owner receipts/reports, and observed recovery state | A mutable status cache, log, rendered report, or scheduler state |
| Biological review and interpretation | External research work-process records | EMRYS orchestration, reports, or local computational completion |

Snakemake implements a checked projection of `STAGE_MAP.md`; it never becomes
a second semantic DAG authority. An exact workflow-profile test must compare
the implemented rule edges and scope expansion with the reviewed projection.

## Version 1 scope

The common selected profile contains:

- reference preparation through historical `00a`, `00b`, and `00c`;
- per-sample compute through `01`, `02`, `04`, `05`, and `06`;
- automatic per-sample evidence `02b` and `03`;
- fixed cohort transformation through `07` and `08`;
- one selected installed module with a typed Step `09` task and optional Step
  `10`; the built-in paired-CMH module retains ranking plus the post-Step09
  scientific-context projection;
- default downstream artifact indexing, canonical run-summary assembly, and
  separate self-contained scientific and evidence HTML reports; these can be
  disabled for execution or generated independently after successful science.

The bounded v1 module descriptor supplies closed configuration normalization,
typed artifact inputs/outputs, required existing runtime-check IDs, minimum
memory, and producer/validator plans. Selection authorizes that installed
in-process provider. Existing `TaskDispatch`, failure, validation,
publication, lock/rollback/recovery, signal, and logging semantics are fixed;
providers do not declare substitute trust or failure policy. V1 is single-core,
supports only the declared artifact kinds, and requires providers to be
installed and self-contained. Module-specific Python/R/native dependencies,
outside resources, richer resources, and their provisioning and independent
identity binding remain open under `ANALYSIS-02`.

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

## Intake and Project admission

### Authored inputs

The authored `emrys.project.v1` YAML carries only scientific intent and
explicit references:

- one shared sample manifest;
- one shared reference FASTA, GTF, and STAR-index policy; and
- one or more human-named Analyses, each with its partition manifest and either
  the complete inline built-in paired-CMH policy or an explicit module
  identifier plus module-owned closed `config`.

The public shape is:

```yaml
schema_version: emrys.project.v1
dataset:
  samples: samples.tsv
reference:
  fasta: reference/genome.fa
  gtf: reference/genome.gtf
  star_index:
    sjdb_overhang: 149
    genome_sa_index_nbases: 14
analyses:
  primary:
    partitions: partitions.tsv
    control_condition: EV
    treatment_condition: PUM1
    target_change: A>G
    min_sample_dp: 1
    mean_dp_threshold: 50
    fdr_threshold: 0.05
    common_or_threshold: 1.2
    absolute_difference_threshold: 0.005
    background_condition: null
    background_max_fraction: 0.01
  collaborator:
    module: example.differential
    partitions: partitions.tsv
    config:
      comparison: treatment-vs-control
```

Project validation, runtime discovery, and Doctor admit all named Analyses.
`emrys run --analysis NAME` selects one; omission is valid only when exactly
one exists. The mapping name is human selection metadata, not immutable
Analysis identity. Shared Dataset and Reference inputs are admitted once, and
repeated partition-manifest spellings are reused within the Project admission.
The retained request-v3 schema is private compatibility authority only for
exact historical resume; active Project commands reject it.

Execution uses one optional selected `emrys.execution-profile.v1` fragment.
Its computational declaration is Run-bound while placement is Attempt-local;
exact selection, precedence, and admission belong to the
[orchestration owner](../../src/emrys/orchestration/local_pilot/CONTRACT.md).

The effective computational declaration enters the successor Execution Plan
and therefore Run identity. Profile source, reporting memory, placement,
observed allocation, and scheduler job ID remain Attempt context. Changing
placement alone does not create a different Run.

Every project-v1 field except `background_condition` is required. Unknown
fields fail admission. The implementation may expose a schema-preserving
starter, but it may not supply hidden scientific defaults during admission;
the Project definition records the selected policy explicitly.

Repeated sample and partition records remain ordered TSV. The local CMH profile
adds admission requirements without silently tightening the general manifest
validator: `replicate` is required, every stratum has exactly one declared
control and one treatment, at least two complete strata exist, and pairing is
never inferred from sample names.

### Admission rules

Project admission must:

- use safe YAML loading, reject duplicate keys, custom tags, merge keys, globs,
  templates, and environment interpolation;
- resolve relative paths against the Project file's directory, never the
  caller's working directory;
- validate the base sample manifest plus the stricter profile requirements;
- preserve manifest row order;
- require explicit regular files and reject unsafe or unresolved path forms;
- compute SHA-256 for the Project source, manifests, every declared FASTQ, and the
  reference FASTA and GTF; and
- snapshot only the small Project source, manifests, profile, policy, and normalized
  contracts in their declared run- or attempt-specific locations. Raw reads and
  references remain stationary.

Content hashing is the minimum integrity needed for immutable identity and safe
resume. It is not a general acquisition or provenance program.

### Run authority and historical execution compatibility

A successor Run has exactly three canonical authority records:

| Record | Bound content |
| --- | --- |
| Analysis revision | Canonical, order-neutral sample and partition semantics; referenced-content hashes; and complete scientific policy |
| Execution Plan | Functional specification, implementation and tool identities, backend semantics, STAR-index policy, and pre-allocation computational-resource declaration |
| Run binding | The domain-separated binding of that Analysis revision to that Execution Plan |

Project formatting, Analysis names, authored locators, raw manifest bytes and
ordering, file sizes, and admission-time snapshots remain source or Attempt
provenance. They do not enter successor Run identity. Exact
`emrys.execution.v1` bytes remain authority only for historical Runs.

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
Project-source hash and bytes, selected human Analysis name, authored path strings, resolved
reporting-resource policy and execution-profile source provenance, placement,
observed outer allocation, and normalization tool identity—belongs to the
immutable workflow-attempt/config records. Reformatting an otherwise
equivalent Project definition, renaming an Analysis, or changing placement therefore does
not create a new scientific Run or demand different bytes at the same
canonical contract path.

Canonical authorities use UTF-8 JSON, sorted object keys, no insignificant
whitespace, no NaN/infinity, and SHA-256. Successor identity uses the
domain-separated Run composition over canonical Analysis-revision and
Execution-Plan digests; historical identity retains its existing envelope.
The human Analysis name selects intent but never identifies or overwrites a Run.

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
Every scientific Attempt has exactly one file-backed `storage_qualification`
identity. Lifecycle re-runs semantic qualification for the Attempt workspace
and canonical normalized reference before delegation and after the child exits,
and requires the resulting receipt identity to reproduce that immutable roster
entry. Direct placement accepts the current-host receipt created only by
explicit Doctor repair or the stronger two-phase compute/head receipt; Slurm
uses only the latter. Historical
Attempts without placement retain the two-phase requirement, and the narrower
direct evidence can never satisfy Slurm.

Each workflow attempt binds one canonical attempt-specific workflow-config
snapshot by relative path and SHA-256. That config binds every owner/scope
dispatch by absolute path and SHA-256, and the task runner admits the exact
expected digest before parsing or invoking a producer. Request snapshot,
attempt, config, dispatch, task-attempt, and verified-record identities therefore
form one explicit chain; neither a pathname nor mutable Snakemake parameters can
substitute for it.

New and historical Runs both retain the exact
`emrys.workflow-attempt.v1` record. Its request-era fields and the exact
`attempts/<workflow-attempt-id>/request.yaml` source snapshot remain unchanged
evidence metadata. For project-v1 that file contains the admitted Project
bytes; neither its filename nor those field names make request-v3 public.

On resume, a completed task keeps the exact predecessor dispatch reference
already bound in its verified record; only pending tasks receive new-attempt
dispatches. Changing producer, validator, input, output, or other dispatch
semantics invalidates reuse instead of asking Snakemake to infer compatibility.

The same canonical Analysis revision and Execution Plan map idempotently to the
same Run binding. Non-identity admission metadata may differ without changing
that mapping. A changed bound input content, reference content, scientific
policy, normalized workflow semantics, or computational resource declaration
creates a different Run. Formatting and sample/partition row order are
identity-neutral because admitted semantic rows are canonicalized before
identity is derived.

### Processing reuse across modules

Processing-only compatibility remains the exact Steps `00`–`06` boundary.
Its digest retains the processing graph, processing implementation and
toolchain identities, backend semantics, STAR-index policy, and Step `00`–`06`
resource semantics. It excludes the selected downstream analysis module and
whole-workflow resource caps that do not affect processing. A downstream Run
may therefore select a different admitted module only when that processing
digest and the existing sample/reference subset rules match. Source artifacts
remain stationary, immutable, and exact-size/hash bound; no provider may copy,
relabel, or adopt the source Run's evidence.

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
identity. Attempt materialization must derive explicit
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

The existing flat paired-CMH path publishes run-summary v2 and report-receipt
v4. An explicit module publishes run-summary v3, whose module-neutral policy
binding is only path, SHA-256, and size, and report-receipt v5, which binds the
analysis provider, reporter provider, and fixed core renderer separately.
Artifact-record v2 may use a null source commit only when exact installed
external-provider bytes are the recorded implementation authority.

The run-specific artifact inventory is also materialized deterministically
from the admitted composed profile, samples, partitions, and declared output paths
before compute. It is never discovered afterward by globbing the filesystem.
Generated native-output paths are relative to the immutable run root. The
stationary Step `00c` FASTA, FAI, and dictionary rows instead use normalized
absolute external paths because that owner publishes sidecars beside the
admitted FASTA. Reporting must therefore receive an explicit artifact source
root distinct from the admitted source checkout: the run root resolves
relative inventory paths, while checkout authority continues to bind producer
and renderer code. A workflow may not force the operator workspace beneath the
Git checkout to collapse those authorities.
The profile projects the common artifacts plus the selected module's declared
Step `09` and optional Step `10` outputs. The artifact-index transaction derives
its adapter registry and expected roster from that admitted profile; this is
dynamic indexing of existing immutable declarations, not a store, database,
service, or second authored manifest.
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

The canonical `project.yaml` parent contains immutable run directories:

```text
<project-root>/logs/
  emrys-local-pilot-<slurm-job-id>.out/.err
  application/                    default structured-log root
<project-root>/runs/<run-id>/
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
  results/                       editing, scientific-context, and report outputs
  products/native/               nonfinal native and validation outputs
  products/artifact-summary/     artifact index and run summary
  attempts/<workflow-attempt-id>/
    request.yaml                 exact admitted source snapshot: project-v1 for current Runs, request-v3 for historical Runs
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

The implemented `run` and `resume` interfaces construct and display one frozen
plan before mutation. A terminal asks once whether to proceed and executes that
same object only after confirmation. Refusal, EOF, or interruption writes and
submits nothing. In a noninteractive context, omission of `--execute` retains
the no-write/no-submit plan; `--execute` remains the explicit automation path.
Direct planning resolves readiness and identity and shows concise work and
reporting summaries. Verbose adds the Run root, resources/allocation, execution
profile, and scheduler streams; debug adds exact safe engine, scheduler, and
task commands.

For Slurm placement, terminal confirmation or explicit noninteractive
`--execute` uses only `<project-root>/logs` on the submit host, submits the
displayed placement once, and prints `JOB_ID`, `OUT`, and `ERR`. The compute
delegate re-admits the binding over exact profile-source bytes and effective
semantics, UID, marker, and canonical scheduler job ID before doctor, Run
planning, or lifecycle mutation. It owns the single application
log for the executing Attempt.

The public control surface owns that exact planning and materialization boundary; direct
manual Snakemake invocation is unsupported. `emrys doctor` is a distinct
Project-aware readiness report that derives Project, input, storage, runtime,
and execution status. Diagnosis, detail projection, help, preview, refusal,
EOF, and interruption before repair authority write nothing and open no log.
Its separate `--repair` operation is limited to the active checkout-owned
`.venv` and Project-owned `runtime/managed`, delegates locked dependency work
to `uv`, Pixi, and `renv`, records one maintenance application attempt, and
re-runs the full readiness report. It cannot alter declared inputs or silently
migrate an admitted site/user runtime profile; ambient and Project-local Pixi
configuration cannot redirect installation outside the owned root. The currently supported managed
target is Linux x86-64; advanced runtime/storage probes remain independently
available. Neither planning nor Doctor invokes scientific owner producers or
validators.

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
| Recovery | Available only for a failed/interrupted Attempt with incomplete scientific Results and no scientific or Run-integrity blocker; reporting state does not gate recovery |

The historical aggregate `state`, `resume_available`, and
`local_pipeline_complete` read-model accessors are retired after all current
callers migrated to these dimensions. Receipt-v1 retains its required
`local_pipeline_complete` field as historical schema evidence, not scientific
completion authority. Current lifecycle emits receipt v2, which removes both
receipt-v1 reporting fields and closes solely over the scientific Attempt.

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
- the exact closed task-start roster;
- the task-start, task-attempt, and verified-task identity chain;
- the verified-record schema and complete hash bindings;
- every declared native output and native receipt;
- the persisted validation report and all-pass result; and
- that every scope without verified completion has never published its durable
  producer-entry record.

Timestamp freshness and Snakemake completion metadata are insufficient. A
failed or missing recheck never causes automatic deletion or rerun over an
ambiguous output set. It yields `blocked` and routes to the applicable owner
recovery instructions. Version 1 supports only scientific between-task resume.
Once a scientific owner has crossed its durable start boundary, failure or
interruption is not automatically recoverable even when no output appears to
have been written. Version 1 does not automate owner-internal transaction
recovery. Downstream reporting never controls scientific resume; its own
partial transaction remains fail-closed and is not repaired or restarted.
Successor resume currently also requires the same normalized backend
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

Inspection reads the successor Run records or exact historical normalized contract,
the exact Attempt and task trees,
task-start and verified-task records, reporting start/completion records, owner
receipts and validation reports, and the aggregate run-lock evidence. It
reports pending, entered, verified, failed, resume-available, and blocked
scopes, plus the exact evidence ceiling. It never accepts a caller-supplied
residue list, infers EMRYS state from `.snakemake/`, or repairs what it
observes.

Reporting is invoked automatically after a successful full scientific Run but
remains a separate non-scientific domain. `run` and `resume` may disable it with
`--no-report`; `emrys report --run-root ...` performs the same admission and is
read-only unless `--execute` is present. Reporting creates no Run or Attempt and
cannot alter the successful v2 Attempt receipt. Each reporting transaction
follows the same irreversible entry policy. Its read-only preflight occurs
before `start.json`; the start is then published
before the execute command. `verified.json` is published only after the command
returns, the native receipt and full transaction are semantically re-admitted,
and the reporting owner's declared control namespace is clean. New generation
requires fully empty ledgers and output directories; complete transactions are
reused, while partial, corrupt, orphaned, symlinked, or concurrent state fails
closed without repair, overwrite, deletion, or adoption.

Automatic reporting shares the `run` or `resume` log. A standalone executing
`emrys report` operation owns a reporting log once generation starts; its
dry-run and complete-reuse paths own no durable log.

The terminal scientific receipt operation rechecks every required profile
scope and binds the ordered pre-entry diagnostic and task-start rosters before
publishing receipt v2. Receipt v1 remains exactly readable and a complete v1
report transaction may be reused, but v1 cannot originate new reports.
Scientific Results and reporting are derived separately and neither establishes
CSU execution, production-scale behavior, validated editing sites, or biological
readiness.

## Explicit deferrals

This contract makes no decision or implementation commitment for:

- a distinct Slurm scientific backend, multi-node execution, local Linux VM,
  CSU portability proof, scheduler accounting integration, or cluster runs;
- dependency installation or repair;
- synthetic-data generation or real science-tool execution;
- a generic assay, stage, plugin, or analysis registry;
- optional-stage and archival-success policy;
- in-code scientific approval or biological-readiness policy;
- public acquisition or a general provenance subsystem;
- logging adoption beyond the `run`/`resume` Attempt boundary and standalone
  executing report generation, or generic gate receipts; standalone report
  dry-run and reuse own no durable log;
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
