# Local-pilot orchestration contract

This document is the binding architecture for NORAD's first local Snakemake
pilot. B2 implements its closed machine schemas, read-only request normalizer,
reporting projection, and semantic all-pass checker. B3 implements the fixed
local-CMH profile, static thirteen-scientific-owner-rule Snakemake graph, local executor profile,
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
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md).

B4 assumes a single-user, cooperative local workspace. It rejects admitted
symlink components, leaf substitution, late leaf collisions, and unstable
bytes or closed rosters, but it is not a defense against a hostile process
concurrently renaming ancestor directories or changing mount namespaces. Such
interference invalidates the evidence boundary and requires external isolation
and explicit reconciliation, never automatic repair.

The first implementation is deliberately source-checkout-bound and local. A
SLURM executor, a local Linux VM, CSU execution, and an installed standalone
control plane are later decisions. Deferral is not rejection.

## Design outcome

The local pilot has one explicit path:

1. An operator authors one YAML request that references ordered TSV manifests
   and stationary FASTQ/reference inputs.
2. NORAD validates and normalizes those inputs into one immutable canonical
   JSON execution contract with an explicit identity envelope.
3. The identity-envelope digest determines one immutable `run_id`.
4. The public dry-run prints the complete fixed command plan without creating
   the workspace; `--execute` acquires the aggregate lock and publishes the
   immutable attempt/config/dispatch set.
5. One fixed CMH workflow profile projects the semantic DAG into Snakemake.
6. Each workflow task invokes one owner's public producer, that owner's public
   validator, and a generic semantic all-pass check.
7. A content-bound verified task record is published only after all three
   succeed.
8. Required verified tasks feed the existing artifact-index, run-summary, and
   Jinja HTML-report owners.
9. A workflow-attempt receipt is published last. Inspection derives state from
   NORAD contracts and records, never from Snakemake metadata alone.

There is no request inbox, watcher, database, service, plugin registry, or
automatic recovery subsystem in version 1.

## Authority matrix

| Subject | Authority | Explicit non-authority |
| --- | --- | --- |
| Scientific owner identity and direct artifact edges | [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md) | Snakemake rule names, filenames, numeric aliases, and narrative order |
| Producer, validator, output, transaction, and recovery behavior | Applicable owner `README.md` and `CONTRACT.md` | Workflow rules and lifecycle records |
| Operator intent | Admitted YAML request plus referenced ordered TSV manifests | Caller working directory, environment discovery, filename inference, and globs |
| Immutable local-run identity | Canonical normalized execution contract and its SHA-256 digest | Request formatting, human label, workspace, executor, host, or Snakemake state |
| Fixed pilot membership and scope expansion | Versioned local CMH workflow profile | A generic registry or automatic owner discovery |
| Scheduling | Snakemake's local executor and static rule graph | Scientific completion, recovery authority, or evidence promotion |
| Reusable task completion | NORAD verified task record after owner validation and semantic all-pass gating | Process exit alone, output presence, timestamps, or `.snakemake/` metadata |
| Reporting identity | Explicit projection from the execution contract into the existing artifact run contract | The reporting run contract as a complete execution identity |
| Run state | Immutable workflow-attempt records, verified task records, owner receipts/reports, and observed recovery state | A mutable status cache, log, rendered report, or scheduler state |
| Scientific review | Separately invoked Step `09c` owner and explicit reviewer declarations | Automatic orchestration or local computational completion |

Snakemake implements a checked projection of `STAGE_MAP.md`; it never becomes
a second semantic DAG authority. An exact workflow-profile test must compare
the implemented rule edges and scope expansion with the reviewed projection.

## Version 1 scope

The only selected profile is the current paired-CMH workflow:

- reference preparation through historical `00a`, `00b`, and `00c`;
- per-sample compute through `01`, `02`, `04`, `05`, and `06`;
- automatic per-sample evidence `02b` and `03`;
- cohort/analysis work through `07`, `08`, and `09`;
- artifact indexing, canonical run-summary assembly, and one self-contained
  HTML report.

The `02b` and `03` evidence branches do not gate downstream scientific compute,
but the local profile requires them before workflow completion. Step `09c` is
not automatic: the final report must show its evidence as absent or incomplete
until a separately authorized review package is assembled. Step `09`'s two
diagnostic PDFs remain native analysis artifacts; this does not reintroduce a
PDF report format.

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
- cohort and primary-analysis identities; and
- the complete inline Step `09` analysis policy.

Version 1 uses this closed top-level shape, encoded by the B2 request schema
without adding discovery or extension fields:

```yaml
schema_version: norad.request.v1
label: optional-human-label
profile: norad.profile.local_cmh.v1
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

### Normalized execution contract

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

`normalized.json` contains only deterministic normalized run content and its
explicit identity envelope. Non-identity admission metadata—the original
request hash and bytes, human label, authored path strings, and normalization
tool identity—belongs to the immutable workflow-attempt record. Reformatting
an otherwise equivalent request or changing its label therefore does not
create a new scientific run or demand different bytes at the same canonical
contract path.

Canonical identity-envelope serialization uses UTF-8 JSON, sorted object keys,
no insignificant whitespace, no NaN/infinity, and SHA-256. The full digest is
stored in the contract and the first implementation uses
`run-<64 lowercase hex>` as the `run_id`. The human label never selects or
overwrites a run.

Workspace, output root, source-checkout path and commit, executor, host,
resources, scratch, observed tool versions, timestamps, PIDs, and future
scheduler identifiers are attempt context. They do not change the scientific
run identity. Version 1 automatic resume nevertheless requires the same clean
source commit, profile digest, and observed required-tool versions; otherwise
the run becomes blocked pending an explicit compatibility or new-profile
decision.

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

The same identity envelope maps idempotently to the same run. Non-identity
admission metadata may differ without changing that mapping. A changed bound
input, manifest order, reference, scientific policy, or profile digest creates
a different run.

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
It retains the existing expected Step `09c` reporting rows even though Step
`09c` is excluded from automatic execution. Their absent sources remain
explicitly missing/incomplete in the artifact index, run summary, and report.
Successful reporting transactions do not make those artifacts present, and
the run-summary `summary_state` or required-missing count is not the workflow
completion Boolean.

## Identity vocabulary

| Identifier | Meaning |
| --- | --- |
| `run_id` | Deterministic immutable normalized execution contract |
| `workflow_attempt_id` | One execute or resume invocation for a run |
| `task_attempt_id` | One public owner invocation within a workflow attempt |
| Owner run token | Existing owner-local staging/publication identity |
| Artifact attempt ID | Existing reporting artifact-attempt vocabulary |
| `execution_attempt_id` | Future application-log identity defined by [`LOGGING_CONTRACT.md`](LOGGING_CONTRACT.md) |
| Scheduler job ID | Future executor correlation only |

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
<workspace>/runs/<run-id>/
  contract/
    samples.tsv
    partitions.tsv
    profile.json
    normalized.json
    reference_contract.json
    primary_analysis_policy.json
    reporting_run_contract.json
    artifact_inventory.tsv
    workflow-configs/<workflow-attempt-id>.json
    dispatch/<workflow-attempt-id>/<machine-key>/<scope-id>.json
  results/                       owner-native outputs and validation reports
  products/                      artifact index, run summary, and HTML report
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
metadata and is never a reporting input or NORAD completion record.

Task stdout/stderr files are complete opaque command-stream captures for
diagnosis. They are not the future structured application logs defined by
`LOGGING_CONTRACT.md`. Each task-attempt record binds both captures by canonical
path and SHA-256; their presence or content never establishes task success or
evidence promotion, but later mutation invalidates that task evidence.

## Planning and mutation boundary

The implemented `run` and `resume` interfaces are read-only by default. Their plan
resolves and validates inputs, computes identity, reports the exact source and
tool context, shows the fixed DAG/resources/commands, and lists blockers without
creating the workspace, contract, attempt, logs, locks, or owner outputs.
Execution requires one explicit `--execute` control.

The B5 adapter owns that exact planning and materialization boundary; direct
manual Snakemake invocation is unsupported. A doctor is a distinct read-only
readiness report and never installs or repairs dependencies. Neither planning
nor doctor invokes owner producers or validators.

## Workflow task boundary

One Snakemake job owns one functional-owner scope. Producer and validator are
not separate DAG nodes. A job performs, in order:

1. immutable identity, dispatch, input, and declared-destination preflight;
2. durable create-exclusive publication of the scope's task-start record;
3. the owner's public producer command, including its owner-local no-clobber
   and recovery-residue preflight;
4. structural admission of the declared native output set;
5. the owner's public validator in execute mode;
6. a generic parser requiring the exact seven-column validation header, at
   least one declared row, and `status=pass` for every row;
7. stable-input rechecks; and
8. atomic publication of the verified task record.

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

The run state is derived rather than edited in place:

| Derived run state | Required facts |
| --- | --- |
| `prepared` | Immutable contract exists; no workflow attempt has begun |
| `running` | Exactly one nonterminal attempt demonstrably owns the run lock through a live lifecycle process |
| `resume_available` | Latest attempt failed or was interrupted; every entered owner/reporting scope has a complete revalidated start-to-verification chain, every remaining scope has no start record, and compatibility checks pass |
| `blocked` | Identity is incompatible; the lock, attempt, task-start, reporting-start, or completion roster is malformed; or any entered scope lacks complete verified evidence |
| `local_pipeline_complete` | Latest attempt receipt binds every required task-start and verified task plus complete start-to-verification chains for the artifact-index, run-summary, and HTML-report transactions |

A workflow attempt begins with an immutable `attempt.json` and ends with one
receipt published last as `succeeded`, `failed`, `interrupted`, or `blocked`.
Attempts form a linear supersession chain. A terminal attempt is never reopened,
and a completed run refuses another execute or resume operation.

Attempt admission is serialized by a persistent canonical zero-byte advisory
mutex beneath `locks/`. That mutex is benign infrastructure, not attempt or
recovery evidence. NORAD holds it while revalidating the exact prepared
execute/resume request; only a still-current request may publish `run.lock` or
attempt-specific state. A contender that waited behind a completing attempt
therefore exits without contaminating the completed or resumable run.

The lifecycle process handles an ordinary signal by stopping delegated work,
preserving task and owner state, and proving a between-task boundary when
possible. It publishes the attempt-local immutable
`released-run-lock.json` with a create-exclusive hard link to the owned public
run lock, verifies and synchronizes the shared inode and bytes, removes only
the still-owned public name, then publishes an `interrupted` receipt last and
binds that release evidence. A colliding evidence path is never overwritten. A
nonterminal attempt left by an unhandled crash
or power loss is not guessed complete or automatically repaired. If live lock
ownership and an unentered-or-fully-verified boundary cannot be proved,
inspection reports it as
blocked for explicit reconciliation.

Snakemake automatic retries are zero. NORAD version 1 does not expose automatic
`--unlock`, `--cleanup-metadata`, `--forceall`, `--rerun-incomplete`, or blind
force controls.

### Resume

Resume always creates a new workflow attempt. A prior verified task may be
reused only after NORAD rechecks:

- the execution contract and profile digest;
- clean source-checkout and required-tool compatibility;
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
recovery.

This ledger is automatic-rerun authority, not a claim that inspection can
globally prove the absence of every file a manual or foreign invocation might
leave behind. Each pending owner still performs its existing no-clobber and
recovery-residue preflight when it first enters. If that check refuses foreign
state, the already-entered scope becomes blocked with preserved diagnostics;
the orchestrator never deletes or bypasses the state.

The internal resume invocation uses exactly `--rerun-triggers input` plus
`--ignore-incomplete`, and only after the independent checks above succeed.
Pinned Snakemake characterization requires the latter when an interrupted job
left a fully NORAD-validated output marked incomplete in disposable engine
metadata. This fixed internal flag does not admit an unverified output, erase
metadata, force a rule, or become an operator-exposed recovery control. Initial
execution never uses it.

## Lock ordering and ownership

The fixed acquisition order is:

1. NORAD run/workflow-attempt lock;
2. Snakemake work-directory lock; and
3. delegated owner-local publication lock.

No path may acquire these in reverse order. The outer lifecycle process owns
aggregate attempt state; jobs write only their task-local records. Existing
owner locks keep their current authority. NORAD never breaks an owner lock,
deletes recovery residue, or considers a lock stale because time elapsed.

The run lock records run, workflow attempt, process, host, creation time, and an
unpredictable owner token. Terminalization never conditionally unlinks its
public pathname: it atomically renames the still-owned lock to the exact absent
attempt-local `released-run-lock.json`, validates and synchronizes that retained
evidence, and publishes the terminal receipt last. A foreign replacement at the
public lock path is never removed. Every terminal receipt binds its released
lock evidence; missing, moved, malformed, or mismatched evidence makes
inspection report `blocked`. Owner recovery state remains untouched.

## Inspection and completion

Inspection reads the normalized contract, exact attempt and task trees,
task-start and verified-task records, reporting start/completion records, owner
receipts and validation reports, and the aggregate run-lock evidence. It
reports pending, entered, verified, failed, resume-available, and blocked
scopes, plus the exact evidence ceiling. It never accepts a caller-supplied
residue list, infers NORAD state from `.snakemake/`, or repairs what it
observes.

Each reporting transaction follows the same irreversible entry policy. Its
normal read-only dry-run occurs before `start.json`; the start is then published
before the execute command. `verified.json` is published only after the command
returns, the native receipt and full transaction are semantically re-admitted,
and the reporting owner's declared control namespace is clean. A reporting
start without that completion evidence blocks resume.

The final completion operation must recheck every required profile scope, bind
the ordered pre-entry diagnostic and task-start rosters, and admit all three reporting
start-to-verification chains before publishing the workflow-attempt receipt.
`local_pipeline_complete` means real or fixture local execution only as
identified by the admitted inputs. It does not establish CSU execution,
production-scale behavior, completed Step `09c` scientific review, validated
editing sites, or biological readiness.

## Explicit deferrals

B0 makes no decision or implementation commitment for:

- SLURM, a local Linux VM, CSU profiles, scheduler accounting, or cluster runs;
- dependency installation or repair;
- synthetic-data generation or real science-tool execution;
- a generic assay, stage, plugin, or analysis registry;
- optional-stage and archival-success policy;
- automatic Step `09c` execution or scientific-review completion;
- biological-readiness policy;
- public acquisition or a general provenance subsystem;
- application logging implementation or generic gate receipts;
- automatic stale-lock cleanup or owner recovery;
- artifact-schema migration or installed workflow assets;
- a wheel-only control plane; or
- Nox.

Owner-admission dispositions and proof targets live in
[`ORCHESTRATION_READINESS.md`](ORCHESTRATION_READINESS.md); proof-sized package
order and acceptance live in [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
Implemented commands belong in the runbook and owner documentation only after
their exact behavior is proven.
