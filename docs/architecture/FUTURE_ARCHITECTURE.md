# Future architecture

This document owns target-state constraints. It does not describe current
implementation, authorize work, or report delivery or evidence status. Current
truth remains in [`ARCHITECTURE.md`](ARCHITECTURE.md), roadmap order in
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md), and rationale in the
[`approved architecture decisions`](../design/DECISIONS.md#approved-architecture-direction-2026-07-31).

Canonical target diagrams:

- [modular pipeline](diagrams/future_modular_pipeline.mmd)
- [manifest and configuration contracts](diagrams/future_manifest_config_contracts.mmd)
- [reporting layer](diagrams/future_reporting_layer.mmd)

## Target principles

- Scientist-facing entry points use explicit, versioned requests and contracts.
- Semantic owners are independently understandable and testable.
- Inputs, outputs, validation records, reports, and receipts have deterministic
  identities and typed contracts.
- Run, attempt, scheduler, failure, rollback, and recovery state remains
  inspectable from the filesystem.
- Default interaction is concise while complete diagnostics remain durable.
- Local-fixture, real-runtime, cluster, scientific-review, and biological
  evidence remain distinct.
- Extension seams support typed preprocessing and analysis without claiming one
  universal DNA/RNA workflow.
- Dependencies, inputs, cleanup, repair, and evidence promotion are never
  implicit.

## Ownership, topology, and dependency direction

The target uses vertical functional-owner source homes and mirrored tests.
Native Python, shell, R, SLURM, schema, style, template, and fixture assets stay
with their owner; packaging is a separate concern. The exact tree, owner homes,
descriptor and schema placement, test mirrors, and allowed dependency direction
are canonical in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).

Exact semantic identities, typed external inputs, artifact edges, barriers, and
evidence branches are canonical in
[`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md). Numeric labels are
provenance aliases, not dependency order. An owner may consume neutral
contracts and libraries but never another functional owner's private
implementation. Orchestration follows declared DAG edges; it does not discover
upstream data from globs, filenames, or neighboring directories.

Shared code begins owner-local. It moves only after equivalent reuse is proven,
and then only to the narrowest neutral owner. Neutral code never depends on a
functional implementation; meaningfully different cross-language behavior may
remain separate. Approved shared seams are recorded in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#approved-neutral-shared-seams).

Any future physical move requires its own reviewed plan and must preserve the
allowed homes and dependency direction in `SOURCE_TOPOLOGY.md`.

## Intake, identity, attempts, and promotion

The V1 operational request is one versioned YAML document referencing one
versioned TSV sample manifest:

- YAML declares run policy, input/reference/partition identities, requested
  analysis and report behavior, and output/state roots.
- TSV declares repeated samples, pairing, replicate, condition, order, and read
  paths.

V1 accepts local paired FASTQ or FASTQ.GZ reads and registered FASTA/GTF
references. Public acquisition is outside this intake boundary.

Intake atomically claims one ready request, validates and resolves every
declared input, hashes and normalizes an immutable run contract, and creates an
inspectable attempt. An identical normalized contract identifies the same run;
a retry creates a new attempt; changed input or policy creates a new run. A
failed request retains failure and recovery evidence and remains resumable.

Computational success requires every currently required requested task,
validator, evidence assembly, and report to complete. Only then may request/run
metadata move to a completed or archive state. Raw inputs do not move
automatically. Exact YAML fields, directory names, optional-analysis success,
and archival policy require their own versioned contracts.

## Orchestration and inspectable state

Orchestration coordinates declared DAGs, contracts, run/attempt state,
scheduler materialization and submission, resume, and requested reports. It
does not own scientific algorithms or install dependencies. Its scheduler and
dependency boundaries are canonical in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#orchestration-and-scheduler-boundary).

State remains inspectable without a CLI. A maintainer can locate:

- the immutable normalized request and referenced manifest;
- run and attempt identities;
- resolved owner inputs, outputs, and contract versions;
- scheduler material and job identifiers;
- concise status and complete durable diagnostics;
- locks, staging, receipts, failures, rollback, and recovery evidence; and
- report-profile requests and publication receipts.

Transitions validate before publication and never infer success from file
presence alone.

## Source size and local context

Material changes above 600 lines trigger cohesion review; new files normally
remain below 600. Architectural work on a file above 1,000 lines requires a
decomposition plan or explicit justification. Files above 1,500 lines require
elimination during the active refactor or an explicit exception. These are
review thresholds, not arbitrary split points.

Mature owners supplement the global
[`TASK_START.md`](../operations/TASK_START.md) router with concise local
context covering purpose and boundaries, owned files, typed contracts,
upstream/downstream interfaces, direct and integration tests, safety and
recovery cautions, evidence limits, and canonical cross-cutting links.

## Reporting target

Reporting exposes at least two versioned projections:

- **science**: the future default, containing the minimum evidence needed to
  understand the run and data;
- **comprehensive**: the full diagnostic report.

Public names remain versioned interface decisions. The science field catalog
starts with evidence state, CMH-ranked findings, QC/filter funnel,
sensitivity/replicate evidence, decisions/limitations, and concise methods.
Every field has a plain-language title, description, authorized source, and
explicit missing/failure behavior using neutral scientific language.

One versioned, format-neutral view model feeds HTML and PDF so semantic content
stays aligned even when layout differs. Science HTML uses responsive records,
summaries, or another reviewed accessible presentation instead of horizontal
scrolling inside panels.

Both projections preserve explicit input/table authorization, deterministic
serialization, no-clobber behavior, stable-input rechecks, rollback, cleanup,
and receipt-last publication. Profile outputs coexist without overwriting
immutable bundles. Rendering is a projection: it does not install tools, run
analysis, discover inputs, or promote evidence.

## Logging target

Logging has two explicit sinks:

- **console**: concise progress, results, warnings, and failures for the current
  operator;
- **application log**: complete operation-attempt diagnostics for audit,
  debugging, and recovery.

The bounded current-output inventory remains in
[`TEST_BASELINE.md`](../design/TEST_BASELINE.md#log-01-current-output-and-log-inventory).
The rules below define the target, not current behavior.

### Controls and stream ownership

Adopted direct Python, shell, and R commands accept:

```text
--log-level normal|verbose|debug
--log-root PATH
```

The environment controls are `NORAD_LOG_LEVEL` and `NORAD_LOG_ROOT`.
Resolution is CLI, then environment, then default. Make and SLURM surfaces use
the environment controls. The outermost operation resolves each value once and
propagates it explicitly; delegated components do not reinterpret ambient
values.

`normal` is the default and there is no `quiet` level. Empty or unknown
effective controls fail before log, output, lock, scratch, or compute side
effects while preserving the entry point's established parse-exit mapping.
Legacy aliases require an explicit parity-tested migration, and conflicting
controls fail.

Until an explicit state root exists, the default application-log root is
`<repository-root>/logs/application`, derived from repository/package
identity rather than caller CWD. An explicit root is absolute. Existing
`--help` interfaces remain side-effect-free; help and parser diagnostics are
command responses, not log events.

stdout is reserved for a declared machine response. Human progress, warnings,
errors, commands, paths, and recovery guidance use stderr. Commands without a
machine response leave stdout empty apart from help. Machine files and payloads
retain their bytes, paths, ordering, hashes, and transaction semantics.
Validators preserve their pure seven-column report bytes on stdout while human
context moves to stderr; semantic `status=fail` rows and command exits remain
separate contract facts.

A valid dry-run creates no application log. At `normal`, it still prints the
resolved non-secret command and essential plan to stderr; higher levels add
context without changing execution. Logging level changes only console
projection, never probes, checks, child flags, computation, artifacts,
validation, locking, publication, rollback, cleanup, or exit behavior.

| Level | Console projection | Durable application log |
| --- | --- | --- |
| `normal` | operation identity, meaningful phases, result, evidence boundary, warnings, errors, and bounded failure summary | complete observed event set |
| `verbose` | `normal` plus resolved inputs/outputs, safe commands, declared hashes, versions, and publication plan | same event semantics |
| `debug` | `verbose` plus classified child diagnostics, internal checks, allowed environment context, timing, and recovery identities | same event semantics |

Machine payloads, binary streams, FASTQ/BAM/VCF content, large tables, and
report bytes are not copied into JSONL. Logs record role, path, hash, byte/row
count when available, and producer/consumer events. Invalid UTF-8 diagnostics
use sequenced `child_diagnostic_bytes` events with unbroken RFC 4648 base64,
byte count, SHA-256, stream, and component identity; bytes are never silently
replaced.

### Operation identity and event record

One adopted execute, substantive validation/check, mutating maintenance action,
or validation-gate invocation owns one application operation attempt. Help,
control/parse failures, and valid dry-runs own none. The attempt begins after
minimal safe log-control and scope validation but before semantic input
validation, expensive work, workflow output directories, locks, or publication
state, so execute-mode preflight failures are recorded without authorizing
other workflow side effects.

The owner assigns `scope_kind` (initially `run`, `sample`, `cohort`,
`reference`, `review`, `validation`, or `maintenance`), `scope_id`,
`execution_attempt_id`, and `entrypoint`. The execution attempt is distinct
from a logical run, orchestration attempt, transaction attempt, run token, PID,
or SLURM job. Those remain typed correlation fields.

```text
<log-root>/<scope_kind>-<scope_id>/<execution_attempt_id>/<entrypoint>.jsonl
```

Local managed directories and files use modes `0700` and `0600`, subject to
a stricter umask. Shared-cluster permissions require an explicit policy and
must not become world-accessible. The resolved root is pinned once; managed
descendants reject symlinks, unsafe identities, ownership/type changes, and
existing attempts or files. Creation is exclusive; prior state is never
truncated, appended to, or adopted.

Each UTF-8 JSON line contains at least:

```text
schema_version, timestamp_utc, monotonic_seconds, sequence,
severity, console_detail, entrypoint, component, scope_kind, scope_id,
execution_attempt_id, mode, phase, event, message, fields
```

Version 1 begins at `1.0.0`; timestamps are RFC 3339 UTC; sequence increases
strictly; and `fields` is typed context. `severity` is `debug`, `info`,
`warning`, or `error`. `console_detail` is `normal`, `verbose`,
`debug`, or `durable_only`. Raw or untrusted diagnostics may be
`durable_only`; a separate sanitized warning/error names the operation and
log path. The opening event records the effective console level and its
resolution source. Progress and results use `info`, internal diagnostics use
`debug`, and NORAD-authored warnings/errors are console-visible at `normal`.
Validator semantic failure and process exit remain separate typed facts.

Generated identity, timestamps, duration, and scheduler context make literal
log bytes nondeterministic. Cross-level tests compare a documented normalized
semantic projection with injected clock/identity context where supported.
Only contract-declared volatile non-log fields may be normalized; stable
payload bytes, scientific/data fields, hashes, states, ordering, and exits
remain exact.

### Ownership, publication, and failure

One operation file has one writer. Delegated components provide structured
events or classified diagnostics through a private channel and never append
concurrently or create duplicate attempts. Declared child machine stdout
continues unchanged to its consumer.

Events are line-buffered and flushed per record, with synchronization at phase,
failure, and recovery boundaries and before an existing receipt-last marker.
The required final pre-receipt event is `publication_ready`; the receipt
remains the authoritative completion marker. A post-receipt closing observation
is best-effort and cannot change exit, rollback, or completed transaction
state. Non-transactional success synchronizes a terminal event.

Initialization, write, or sync failure before transaction completion follows
the operation's established failure/rollback path and preserves locks, markers,
backups, staging, and other recovery evidence. Interrupted attempts preserve
partial logs. Catchable signals receive best-effort event, flush, and child
cleanup while retaining established signal exits; uncatchable node, process, or
storage loss may leave a partial record and never implies complete capture.

After an attempted operation fails, stderr ends with a bounded summary naming:

1. entry point, phase, and status;
2. scope, execution attempt, and application-log path;
3. owned lock, stage, backup, and recovery paths;
4. up to 20 console-safe events and 8 KiB, with explicit truncation; and
5. one established next action or runbook route.

If logging could not initialize, the summary states that no durable log exists.
`durable_only` content is never replayed; excluded diagnostics are represented
by a sanitized count and log pointer.

Fields and commands carry sensitivity metadata. Known secrets are rendered as
`<redacted>`; the environment is never dumped; commands are recorded only
after argument classification. Application logs are protected operational data,
not presumed-public sanitized records.

NORAD does not automatically rotate, truncate, compress, upload, or delete
application logs. Creating one never promotes runtime, cluster, scientific, or
biological evidence. Only an explicitly authorized immutable copy with the
required path, hash, relationship, and evidence policy may satisfy an existing
runtime- or cluster-log role.

### Scheduler relationship

SLURM `logs/%x-%j.out` and `logs/%x-%j.err` remain scheduler-owned
compatibility/diagnostic streams, not application logs. Scheduler capture opens
before job execution and therefore still requires its submit-path contract.
Adopted jobs receive resolved controls through exported environment, record job
identity as correlation metadata, and report the application-log path once to
scheduler stderr. Machine stdout reaches `.out`; human projection reaches
`.err`. A transport wrapper does not create a second attempt when the
delegated semantic operation already owns it.

## Analysis extension boundary

The target supports multiple typed preprocessing profiles and analysis modules;
it does not assume every DNA/RNA assay shares one preprocessing trunk. A
profile declares a DAG and typed artifacts. A module declares accepted artifact
types, configuration, runtime dependencies, outputs, validation, evidence
limits, and report projections. Exact owner shape and dependency direction are
canonical in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#analysis-module-contract).

A scientist-authored module is acceptable only with explicit inputs/outputs,
controlled working and state paths, dependency declaration, deterministic
identity, validation, provenance, failure semantics, and no automatic evidence
promotion. Trust may distinguish exploratory custom modules from reviewed,
registered modules. A generic loader, registry, universal module schema, or
optional-analysis success rule requires its own contract; clean typed branch
points do not imply those capabilities.

## Public reference and read acquisition

Acquisition follows this capability order:

1. local paired FASTQ/FASTQ.GZ plus registered reference;
2. NCBI reference acquisition and registration;
3. SRA read acquisition and materialization;
4. later ENA, GEO, or BAM support only for concrete use cases.

Reference adapters own accession/versioned FASTA/FNA sequences,
GTF/GFF3/GBFF annotations, hashes, and provenance. They never convert
references to FASTQ. Read adapters own sequencing-read archives and validated
materialization. The adapter families stay separate because identity, format,
transfer, cache, retry, storage, and provenance semantics differ.

## Installable control plane

Once internal interfaces are stable, an installable `norad` package may
provide thin validation, planning, run, status, resume, reporting, and owner
description interfaces. Public command names, versioning, build metadata,
distribution, and asset APIs require separate interface contracts.

The control plane follows
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#dependency-direction-summary),
does not reimplement external compute tools or bootstrap dependencies, and
includes required non-Python assets explicitly. Scheduler jobs are materialized
as immutable, run-bound resolved copies before submission so package updates
cannot mutate active runs.

## Documentation boundary

Durable target directories use concise `README.md` files. Parent indexes own
child purpose; child indexes own local detail. Opaque tables, schemas,
generated/lock state, and byte-sensitive artifacts receive adjacent
documentation rather than contract-changing inline comments. Code uses
language-native module documentation and only useful rationale, invariant,
safety, and scientific comments.

Documentation placement follows an audience and ownership map; relocation uses
a source-to-destination ledger. Automated documentation-health checks remain
read-only by default and require approval before repair.

## Evidence and safety boundary

No target component may infer evidence promotion from successful execution,
artifact presence, a scheduler exit, an application log, or a rendered report.
Scientific review and biological interpretation require their own explicit
contracts and authority. Automatic dependency restoration, stale-lock removal,
log/artifact cleanup, publication infrastructure, and biological-readiness
policy are separate capabilities, never incidental side effects.

These target constraints preserve the evidence boundaries in
[`AGENTS.md`](../../AGENTS.md). Diagrams and target paths are designs, not
proof that an implementation, migration, runtime, cluster execution, scientific
review, or biological result exists.
