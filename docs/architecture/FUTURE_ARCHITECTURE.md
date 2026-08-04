# Future architecture

This document owns target-state topology and future constraints. It does not
describe the current flat repository as already migrated, authorize a task, or
track branch/test/runtime status. Current implementation truth remains in
[`ARCHITECTURE.md`](ARCHITECTURE.md); roadmap order remains in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); rationale remains
in the
[`approved architecture decisions`](../design/DECISIONS.md#approved-architecture-direction-2026-07-31).

Canonical future diagrams:

- [`diagrams/future_roadmap_sequence.mmd`](diagrams/future_roadmap_sequence.mmd)
- [`diagrams/future_modular_pipeline.mmd`](diagrams/future_modular_pipeline.mmd)
- [`diagrams/future_manifest_config_contracts.mmd`](diagrams/future_manifest_config_contracts.mmd)
- [`diagrams/future_reporting_layer.mmd`](diagrams/future_reporting_layer.mmd)

## Target qualities

- scientist-facing entry points with explicit versioned requests and contracts;
- semantic stages that are independently understandable and testable;
- typed, immutable inputs/outputs at every stage and analysis branch;
- deterministic identities, artifacts, validation records, reports, and
  publication receipts;
- concise default interaction plus complete durable diagnostic evidence;
- filesystem-inspectable run, attempt, scheduler, failure, and recovery state;
- independent local-fixture, real-runtime, cluster, scientific-review, and
  biological-interpretation evidence;
- extension seams that do not overclaim one universal DNA/RNA workflow;
- no implicit dependency installation, input discovery, cleanup, or repair.

## Target source and test topology

The target is a vertical, owner-local source and mirrored-test topology, not a
claim that every asset is Python or that current executable source has already
moved. Preprocessing stages, first-class analyses, evidence operations, and
neutral application domains have distinct homes. Native shell, R, SLURM,
schema, style, template, and fixture assets remain with their functional owner;
packaging is a later concern.

The exact target tree, every functional-owner home, descriptor serialization,
schema-placement rule, non-Python asset owner, test mirror, and allowed
dependency direction are owned by
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md). Reporting
now occupies its final source, asset, and mirrored-test owners; other approved
flat assets remain current truth until their separately bounded migrations
land.

## Stage identity, DAG, and black-box boundary

The exact display titles, public slugs, frozen machine keys, historical
aliases, typed external inputs, direct artifact edges, evidence branches, and
barriers are owned by
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md). Numeric aliases remain
provenance only; the DAG, not lexical or historical order, defines dependency.

A stage may depend on neutral contracts/libraries but never import another
stage's implementation. Orchestration navigates only declared DAG edges and
contracts. No stage discovers upstream data by glob, filename convention, or a
neighbor's private directory. Failures identify the stage, run, attempt,
contract, and next safe operator action without hiding filesystem state.

## Direct migration model

The hybrid flat/target repository is temporary scaffolding, never an end
state. Each bounded migration moves one owner directly to its final home,
preserves its behavior and evidence contracts, and removes any strictly
necessary legacy wrapper after named callers and parity obligations close.

The exact wrapper criteria, caller order, language/asset parity matrix,
rollback boundaries, removal criteria, and reusable card checklist are owned
by
[`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md).

## Intake, identity, attempts, and promotion

The target V1 operational intake will use one versioned YAML request that
references one versioned TSV sample manifest:

- YAML: run policy, explicit input/reference/partition identities, requested
  current analysis/report behavior, and output/state roots;
- TSV: repeated sample rows, explicit pairing/replicate/condition/order, and
  read paths.

V1 accepts local paired FASTQ or FASTQ.GZ reads plus registered FASTA/GTF
reference inputs. It does not acquire public data.

The ingestion boundary atomically claims one ready request before execution,
validates and resolves every declared input, hashes and normalizes an immutable
run contract, and creates an inspectable attempt. An identical normalized
contract identifies the same run; a retry creates a new attempt; changed input
or policy creates a new run. A failed request remains resumable with its failure
and recovery evidence.

Target V1 computational success will require the request's currently required
tasks, validators, evidence assembly, and requested report to complete. Only
then may request/run metadata be promoted to a completed/archive state. Raw
inputs do not move automatically. Current `data/raw` is a storage convention
for pre-staged data, not the future intake queue or state machine.

Exact YAML fields and operational directory names remain open. Future
required/optional analysis success and archival rules are deliberately separate
from the V1 design.

## Orchestration and filesystem-inspectable state

The orchestration layer owns DAG planning, declared contract resolution, run
and attempt state, scheduler submission/materialization, resume decisions, and
requested report coordination. It does not own scientific algorithms or install
dependencies.

Run state must remain inspectable from explicit files and directories even if a
future CLI is unavailable. At minimum, a maintainer must be able to locate:

- the immutable normalized request and referenced manifest;
- run and attempt identities;
- resolved stage inputs/outputs and contract versions;
- scheduler submission material and job IDs when applicable;
- concise status plus complete durable logs;
- locks, staging, receipts, failure, rollback, and recovery evidence;
- report profile requests and published report receipts.

State transitions use explicit validation-before-publication and never infer
success from file presence alone.

## Shared libraries and dependency direction

Code starts local and moves only after proven equivalent reuse justifies the
narrowest neutral owner. Neutral libraries and contracts never depend on
functional implementations; independent or meaningfully different cross-
language behavior may remain duplicated. The exact dependency-direction rules
and catch-all prohibitions are owned by
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#library-boundary).

Completed `LIB-02F` approves two concrete narrow seams. Public Step `08`, Step
`09`, and Step `09c` artifact/table contracts converge bottom-up under the
neutral `scientific_evidence` contract owner, while review policy/publication
and reporting projection remain owner-local. Exact FASTA/FAI/DICT contig
parsing converges under the neutral `reference_contigs` library, while each
consumer retains its own agreement, evidence, CLI, and publication behavior.
The exact targets and prohibited scope are fixed in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#approved-neutral-shared-seams).

## Source-size and local-context constraints

Material changes above 600 lines trigger cohesion review; new files normally
stay below 600. Architectural work on a file above 1,000 lines requires a
decomposition plan or explicit justification. Files above 1,500 lines require
elimination during the active refactor or an explicit exception. These are
review thresholds, not instructions to split at arbitrary line boundaries.

Every mature stage/domain supplements the global
[`task-start router`](../operations/TASK_START.md) with local maintainer
context containing:

- purpose and scientific/operational boundary;
- file map and local ownership;
- typed input/output contracts;
- direct upstream/downstream interfaces;
- focused, independent, and integration test locations;
- safety, failure, recovery, and evidence cautions;
- links to canonical cross-cutting decisions and commands.

This context reduces routine repository-wide reading. Phase boundaries trigger
renewed ownership, interface, acceptance, and diff assessment. Cross-cutting
changes, contradictions, unknown revisions, and scientific, evidence, safety,
recovery, or public-contract uncertainty broaden inspection according to
impact; they do not impose an unrelated fixed corpus.

## Reporting target

Reporting exposes at least two versioned projections:

- science: the future default, containing the minimum evidence a scientist
  needs to understand the run and data;
- comprehensive: the retained full diagnostic report.

Exact public names and flags remain open until the current report is
characterized. The science field catalog begins with evidence state,
CMH-ranked findings, QC/filter funnel, sensitivity/replicate evidence,
decisions/limitations, and concise methods. Every field has a plain-language
title, description, authorized source, missing/failure behavior, and neutral
scientific language.

One versioned format-neutral view model feeds HTML and PDF so their semantic
content remains aligned. Layout may differ by medium. The science HTML view
does not place horizontal scrolling inside panels; wide information becomes
responsive records, summaries, or another reviewed accessible presentation.

Both profiles preserve explicit-input/table authorization, deterministic
serialization, no-clobber, stable-input rechecks, rollback, cleanup, and
receipt-last publication. Profile outputs coexist without overwriting existing
immutable bundles. Rendering remains a projection and never installs tools,
runs analysis, discovers inputs, or promotes evidence.

## Logging target

The target has two explicit sinks with different jobs:

- console: concise progress, results, warnings, and failures for the current
  operator;
- application log: complete operation-attempt diagnostic detail for audit,
  debugging, and recovery.

The complete current-behavior evidence is in the
[`LOG-01` inventory](../design/TEST_BASELINE.md#log-01-current-output-and-log-inventory).
This section is the version-1 target contract. It does not change current
output or activate a new default by itself.

### Public controls and resolution

Adopted direct Python, shell, and R commands accept these long options without
short aliases:

```text
--log-level normal|verbose|debug
--log-root PATH
```

The corresponding environment controls are `NORAD_LOG_LEVEL` and
`NORAD_LOG_ROOT`. Direct commands resolve CLI, then environment, then the
default; only the effective source is validated. Make and SLURM surfaces use
the environment controls rather than pretending to accept command-line flags.
The outermost adopted NORAD operation resolves both values once and propagates
the resolved values explicitly. Delegated components do not reinterpret a
different ambient value.

The default level is `normal`; there is no `quiet` level. An explicitly empty
or unknown effective level, or an empty/invalid effective root, fails before
log, output, lock, scratch, or compute side effects. Each entry point preserves
its established parse-error exit mapping. The current
`tests/tools/run_validation.py --verbose` continues unchanged until that
orchestrator's separately approved adoption. Because it streams complete merged
child diagnostics, adoption may migrate it only as a deprecated alias for
`--log-level debug`, not `verbose`; conflicting explicit controls fail. This is
an intentional, parity-tested migration rather than a repository-wide alias or
a claim that current and target streams are identical.

The current-tree default root is `<repository-root>/logs/application`, resolved
from repository/package identity rather than caller CWD. A future control
plane passes its configured state-root location explicitly. An explicit root
must be absolute; relative roots are invalid rather than CWD-dependent.
`--help` remains
side-effect-free on stdout where an entry point already owns that interface;
LOG-02 does not add help to the R environment utilities that currently reject
arguments. Existing parser/error output and exit mappings remain per-entry-
point contracts. Help and parser diagnostics are command responses, not log
events.

### Streams, severity, and detail

stdout is reserved for a command's declared primary machine response. Human
progress, warnings, errors, commands, paths, and recovery guidance use stderr.
A command with no declared stdout response leaves stdout empty apart from
`--help`. Explicit machine files retain their bytes, paths, hashes, ordering,
and transaction semantics.

A valid dry-run creates no application log. Because its purpose is inspection,
`normal` still prints the exact resolved non-secret command and essential plan
to stderr; verbose/debug add context without changing the command. A declared
machine preview may use stdout. The thirteen validators eventually emit pure
seven-column report bytes on stdout and move human context to stderr, while
preserving the existing distinction between semantic `status=fail` rows and
operational command errors, including established exit behavior.

Severity and console detail are independent:

| Public level | Human stderr content | Durable application log |
| --- | --- | --- |
| `normal` | operation/log identity, meaningful phases, primary results, evidence boundary, warnings, errors, and bounded failure summary | every event observed by the unchanged operation |
| `verbose` | `normal` plus resolved inputs/outputs, safe commands, declared hashes, tool/module versions, and publication plan | the same event set, apart from selected-level metadata |
| `debug` | `verbose` plus classified child diagnostics, internal-check results, allowed environment context, timings, lock/run-token/stage/backup identities, and cleanup detail | the same event set, apart from selected-level metadata |

Console-eligible NORAD warning/error projections reach stderr at every level;
raw sensitive or untrusted child events follow the `durable_only` rule below.
A level never enables extra probes, checks, child flags, computation, or
publication branches. It changes only the console projection; commands,
artifacts, schemas, hashes, receipts, evidence, validation, locking,
publication, rollback, cleanup, and exits remain unchanged.

Primary machine payloads, binary streams, FASTQ/BAM/VCF content, large tables,
and report bytes are not duplicated into JSONL. Their path, role, hash, byte or
row count when available, and producer/consumer event are recorded instead.
Diagnostic streams are handled as bytes: valid UTF-8 becomes text. An invalid
chunk uses event `child_diagnostic_bytes` with `encoding="base64"`, RFC 4648
`data_base64` without line breaks, `byte_count`, `sha256`, and stream/component
identity; large chunks may be split into sequenced events. No byte is silently
replaced. Declared machine stdout bypasses diagnostic capture.

### Operation identity and durable record

An adopted execute, substantive validation/check, mutating maintenance, or
validation-gate invocation owns one application operation attempt. Help,
parser/control failures, and valid dry-runs do not. The attempt starts after
minimal safe log-control and scope identity validation but before semantic
input validation, expensive work, workflow output directories, workflow locks,
or publication state. Execute-mode input/preflight failures are therefore
recorded without authorizing other workflow side effects.

The owning operation assigns:

- `scope_kind`: initially `run`, `sample`, `cohort`, `reference`, `review`,
  `validation`, or `maintenance`;
- `scope_id`: the existing explicit scope ID or a fixed action identity;
- `execution_attempt_id`: a new filesystem-safe unique operation identity;
- `entrypoint`: the single public operation owner.

`execution_attempt_id` is not a logical run ID, orchestration run-attempt ID,
artifact/report transaction attempt ID, run token, PID, or SLURM job ID. Those
identities remain distinct typed correlation fields when applicable. The path
is:

```text
<log-root>/<scope_kind>-<scope_id>/<execution_attempt_id>/<entrypoint>.jsonl
```

The local default creates managed directories/files with modes `0700` and
`0600`, subject to a more restrictive umask. Shared-cluster permissions require
an explicit future state-root policy and may never become world-accessible by
accident. An explicitly configured root is resolved and pinned once; managed
descendants reject symlinks, non-directories, ownership changes, unsafe IDs,
and existing attempts/files. The writer uses exclusive creation and never
truncates, appends to, or adopts prior state.

Every line is one versioned UTF-8 JSON event containing at least:

```text
schema_version, timestamp_utc, monotonic_seconds, sequence,
severity, console_detail, entrypoint, component, scope_kind, scope_id,
execution_attempt_id, mode, phase, event, message, fields
```

Version 1 begins at `1.0.0`. `timestamp_utc` is RFC 3339 UTC, `sequence` is
strictly increasing within the file, and `fields` is typed context rather than
an encoded prose dump. Optional correlation fields include logical run and run-
attempt identities, transaction identities, and scheduler metadata. The
opening event records the selected console level and its resolution source.

`severity` is exactly `debug`, `info`, `warning`, or `error`.
`console_detail` is exactly `normal`, `verbose`, `debug`, or `durable_only` and
names the minimum console projection; `durable_only` never reaches the console.
Progress/results are `info`, internal diagnostic observations are `debug`, and
NORAD-authored attention/failure events are `warning`/`error` with at least
`normal` detail. Raw or untrusted child diagnostics retain their classified
severity but may be `durable_only` when they are not safe for console display;
the owner emits a separate sanitized `normal` warning/error with the operation
context and log path. A validator `status=fail` row records an `error` event,
but severity does not determine process exit: the validator's established
possible exit zero and the row's semantic failure remain separate typed facts.

Timestamps, generated identity, duration, and scheduler context make bytes
intentionally nondeterministic. Cross-level tests compare a documented
normalized semantic projection rather than literal log equality. Paired runs
use isolated equivalent roots plus injected clock/identity/scheduler context
where supported. For an existing producer without injection, its contract must
name the exact volatile non-log fields—such as generated IDs, timestamps,
elapsed values, or temporary paths—that normalization excludes. Stable payload
bytes, scientific/data fields, declared hashes, states, ordering, and exits
remain exact; no field may be normalized merely because levels disagree.

### Ownership, publication, and faults

One operation file has one writer. Delegated components never append to it.
The owner captures classified child diagnostics or accepts structured events
through an explicit private adapter/channel; exact transport belongs to
`LOG-03`. Cross-language or nested wrappers must not create duplicate attempts
or permit concurrent append. Child machine stdout continues to its declared
consumer unchanged.

Events are line-buffered and flushed after each record. The owner additionally
syncs at phase, failure, and recovery boundaries and before an existing
receipt-last transaction marker. The final required pre-receipt event records
`publication_ready`, not success. The receipt remains the authoritative
transaction-completion marker. A post-receipt closing observation is
best-effort only: its failure cannot undo a completed transaction, change the
exit, or trigger rollback. Non-transactional operations sync a terminal event
before returning success.

A required initialization/write/sync failure before transaction completion
enters the operation's established failure/rollback path without deleting or
normalizing locks, markers, backups, staging, or other recovery evidence. A
failed or interrupted owned attempt preserves its partial log. Catchable
signals receive best-effort event/flush/descendant cleanup while preserving
the established signal exit. `SIGKILL`, node loss, and storage loss remain
environment-deferred and may leave an explicitly partial final event or file.

### Failure summary, security, retention, and evidence

After an attempted operation fails, stderr ends with:

1. an actionable line naming entry point, phase, and status;
2. scope/execution-attempt identity and the application-log path;
3. owned lock/stage/backup/recovery paths requiring inspection;
4. the latest console-eligible, sanitized warning/error/recovery events, bounded
   jointly to 20 events and 8 KiB with an explicit truncation marker; and
5. one established next action or runbook link when available.

The complete log is not replayed by default. Verbose/debug may already have
projected more context, but the terminal block remains bounded. If log
initialization failed, stderr states that no durable log exists and names only
the requested/resolved root that is safe to disclose.
Failure-tail selection honors sensitivity metadata and `console_detail`; raw
`durable_only` content is never replayed. When relevant diagnostics are
excluded, the tail substitutes a sanitized count and durable-log pointer.

Structured fields and rendered commands use explicit sensitivity metadata.
The logger never dumps the environment; known secret values become
`<redacted>` everywhere. Exact commands are logged only after their arguments
are classified. No credential-specific option or committed credential literal
was identified by LOG-01's bounded static inspection, but runtime arguments,
paths, URLs, renderer output, and arbitrary third-party diagnostics may still
contain sensitive material. Application logs are therefore protected
operational data, not assumed sanitized public records.

NORAD does not automatically rotate, truncate, compress, upload, or delete
application logs. Retention and reviewed cleanup are explicit operator actions.
Creating a log never promotes runtime, cluster, scientific, or biological
evidence. A separately authorized, preserved, immutable copy may satisfy an
existing `runtime_log` or `cluster_log` role only with its required exact path,
hash, relationship, and evidence policy; application logging alone never does.

### Scheduler relationship

SLURM `logs/%x-%j.out` and `logs/%x-%j.err` remain conditional scheduler-owned
capture for compatibility and cluster diagnosis. They are not application logs
and do not satisfy the operation-attempt contract. Actual scheduler capture,
accounting, and retention remain environment-deferred. Current relative capture
requires the submit-CWD/pre-created `logs/` contract to succeed; an in-job
directory creation is too late for scheduler stream opening.

An adopted SLURM operation receives resolved controls through its exported
environment, records job identity as correlation metadata, and emits the
application attempt/path once to scheduler stderr. Declared machine stdout
reaches scheduler `.out`; human projection reaches `.err`. A transport wrapper
does not create a second application log when its delegated semantic operation
already owns the attempt.

### Scenario matrix

| Scenario | stdout | stderr | Application log | Required invariant |
| --- | --- | --- | --- | --- |
| established `--help` | usage | empty unless help fails | none | zero exit; no filesystem side effects; no new help mode implied |
| parse/control error | empty | usage plus actionable error | none | established parse exit; no work/log/output side effects |
| valid dry-run | declared machine preview, if any | exact command/plan plus selected detail | none | validation, probes, and inspection remain; no execution, publication, application log, or expensive scientific computation |
| execute at `normal` | declared machine result only | concise phases/result/warnings/errors | complete JSONL | non-log behavior equals other levels |
| execute at `verbose`/`debug` | same machine bytes | richer projection | same normalized event semantics | no extra probes or branches |
| execute input/preflight failure | no success claim | bounded actionable failure | retained partial JSONL | no workflow side effect beyond owned log/recovery |
| validator semantic failure | pure `status=fail` report rows | human failure context | complete operation log | existing validator status/exit semantics preserved |
| child with data stdout | unchanged declared data flow | parent human projection | metadata plus classified diagnostics | no data duplication or pipeline-exit change |
| transactional failure | no partial success claim | bounded recovery block | retained partial JSONL | established rollback/lock/exit behavior preserved |
| receipt publication | declared result only | concise result | required `publication_ready`; optional close | receipt remains authoritative completion marker |
| catchable signal | no success claim | bounded interruption block | flushed partial JSONL when possible | descendants/recovery follow existing contract |
| uncatchable loss | no success claim | not guaranteed | explicitly possibly partial | never overclaim complete capture |
| SLURM operation | declared machine output in `.out` | human output/path in `.err` | separate JSONL | scheduler/application roles remain distinct |
| validation multi-failure | optional result document only | plural failures plus bounded tail | one complete operation log | first propagated status and lane cleanup remain stable |
| log fault/path collision | no success claim | actionable storage/no-clobber error | none or preserved partial | prior files untouched; pre-receipt failure is fail-closed |
| evidence use | unchanged | no promotion claim | ordinary operational log | explicit copy/hash/role policy required separately |

### Foundation and adoption inputs

`LOG-03` owns the neutral foundation and one representative, initially opt-in
adoption. It must independently test control precedence, transitional
validation `--verbose` preservation/migration, stdout purity, severity/detail
mapping, normalized level-independent event semantics, deterministic
clock/identity injection, identity/schema/ordering, permissions, safe-root/no-
clobber behavior, single-writer child capture, base64 non-UTF-8 handling,
redaction, sensitive `durable_only` child handling, sanitized failure-tail
bounds, receipt ordering, catchable-signal and log-I/O faults, and exact stable
plus explicitly normalized volatile non-log equivalence across levels.

Later adoption planning uses LOG-01 to cover Python transaction/report and
validator producers; shell workflows and delegated R engines; SLURM, Make, and
the validation orchestrator; and restore/maintenance/operational checks. LOG-02
does not create `LOG-04-*` cards, implement a logger, migrate an entry point, or
authorize cleanup. Current defaults remain unchanged until reviewed foundation,
adoption, and `LOG-05` activation packages complete.

## Analysis extension boundary

The long-term architecture supports multiple typed preprocessing profiles and
multiple typed analysis modules. It does not assume every DNA/RNA assay shares
one preprocessing trunk. A profile declares a DAG and produces typed artifacts;
an analysis module declares accepted artifact types, configuration, runtime
dependencies, outputs, validation, evidence limits, and report projections.

The current CMH analysis may become the first built-in module. A scientist-
authored R module is feasible only with explicit inputs/outputs, controlled
working/state paths, dependency declaration, deterministic identity,
validation, provenance, failure semantics, and no automatic evidence promotion.
Future trust may distinguish exploratory custom modules from registered modules.

No generic loader, registry, universal module schema, alternate assay, or
optional-analysis success state belongs in the current refactor. Current work
only preserves clean typed branch points.

## Public reference and read acquisition

Public acquisition remains future-only and follows this priority:

1. local paired FASTQ/FASTQ.GZ plus registered reference;
2. NCBI reference acquisition and registration;
3. SRA read acquisition/materialization;
4. later ENA, GEO, or BAM support if concrete use cases justify them.

Reference adapters handle accession/versioned FASTA/FNA sequences and
GTF/GFF3/GBFF annotations plus hashes/provenance. They never convert references
to FASTQ. Read adapters handle sequencing-read archives such as SRA and may
materialize validated FASTQ. The adapters remain separate because identity,
format, transfer, cache, retry, storage, and provenance semantics differ.

## Later installable control plane

After internal interfaces stabilize, an installable `norad` package may expose
a thin operational interface for validation, planning, run, status, resume,
reporting, and stage description. Command names are illustrative until a
separate public-interface design is approved.

The control plane coordinates contracts, DAG, scheduler, filesystem state, and
reports. It does not reimplement external compute tools or bootstrap R/system
dependencies. Packaging must explicitly include required non-Python assets.
Scheduler jobs are materialized as immutable, run-bound resolved copies before
submission so an installed package update cannot mutate an active run's job.

Versioning, wheel/build metadata, asset APIs, and public distribution are
deliberately deferred until the architecture and behavior contracts settle.

## Documentation and skill boundary

Target directories use concise `README.md` files where durable. Parent READMEs
explain child purpose but child READMEs own local detail. Opaque table, schema,
generated, lock, and byte-sensitive artifacts receive adjacent documentation,
not embedded comments that change their contract.

`docs/reference/GLOSSARY.md` will own abbreviations and project-specific terms.
Code files will carry conventional language-native module/header documentation
and only useful why/invariant/safety/scientific comments. Documentation cleanup
requires an audience map and source-to-destination ledger before relocation.

No `docs/skills` directory is planned. Once these practices are implemented and
proven, a proper documentation-health skill may audit deterministic structure
and semantic responsibility drift. It remains read-only by default and requires
approval before repair.

## Deferred capabilities and guardrails

The following remain outside the current repo-spanning refactor task set unless
a separate future card, live plan, and approval say otherwise:

- analysis-module registry and custom-analysis execution;
- public reference/read acquisition;
- installable/public package distribution;
- optional-analysis success and request archival;
- generic dispatchers and job arrays;
- targeted-rerun orchestration;
- publication infrastructure;
- automatic dependency restoration;
- automatic stale-lock deletion, log cleanup, or artifact cleanup;
- policy capable of unlocking biological readiness.

Every future capability enters through explicit contracts and preserves the
evidence boundaries in `AGENTS.md`. Target diagrams are constraints, not proof
that an implementation or migration exists.
