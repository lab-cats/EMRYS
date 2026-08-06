# LOG-03 — Build two-sink logging foundation

## Objective

Implement the neutral logging foundation that separates concise console output
from complete operation-attempt durable logs.

## Why this exists

Per-script print edits would drift and could alter stream contracts. A small
foundation is needed before bounded domain adoption, but it must remain neutral
and avoid becoming a hidden orchestration framework.

## Fixed decisions

- Foundation code lives in the narrowest neutral target owner and never imports
  stages.

The following approved contract is binding implementation input for this card.
It is reproduced here so the foundation does not depend on compressed or
retired planning history for its semantics.

### Sinks, controls, and stream ownership

- Logging has two explicit sinks: a concise console for current-operator
  progress, results, warnings, and failures; and a complete application log for
  operation-attempt audit, debugging, and recovery.
- Adopted direct Python, shell, and R commands accept
  `--log-level normal|verbose|debug` and `--log-root PATH`. The corresponding
  environment controls are `NORAD_LOG_LEVEL` and `NORAD_LOG_ROOT`.
- Resolution order is command line, environment, then default. Make and SLURM
  surfaces use the environment controls. The outermost operation resolves each
  value once and propagates it explicitly; delegates do not reinterpret ambient
  values.
- `normal` is the default and there is no `quiet` level. Empty, unknown, or
  conflicting effective controls fail before log, output, lock, scratch, or
  compute side effects while preserving the entry point's established parse-exit
  mapping. A legacy alias requires an explicit parity-tested migration.
- Until an explicit state root exists, the default log root is
  `<repository-root>/logs/application`, derived from repository/package identity
  rather than caller CWD. An explicit root is absolute. Existing `--help`
  interfaces remain side-effect-free; help and parser diagnostics are command
  responses, not log events.
- stdout is reserved for a declared machine response. Human progress, warnings,
  errors, commands, paths, and recovery guidance use stderr. Commands without a
  machine response leave stdout empty apart from help. Machine files and
  payloads retain their bytes, paths, ordering, hashes, and transaction
  semantics. Validators preserve pure seven-column report bytes on stdout;
  semantic `status=fail` rows and command exits remain separate contract facts.
- A valid dry-run creates no application log. At `normal`, it prints the
  resolved non-secret command and essential plan to stderr; higher levels add
  context without changing execution.
- Log level changes console projection only. It never changes probes, checks,
  child flags, computation, artifacts, validation, locking, publication,
  rollback, cleanup, or exit behavior.

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

- One adopted execute, substantive validation/check, mutating maintenance
  action, or validation-gate invocation owns one application operation attempt.
  Help, control/parse failures, and valid dry-runs own none.
- The attempt begins after minimal safe log-control and scope validation but
  before semantic input validation, expensive work, workflow output directories,
  locks, or publication state. Execute-mode preflight failures are therefore
  recorded without authorizing other workflow side effects.
- The owner assigns `scope_kind` (initially `run`, `sample`, `cohort`,
  `reference`, `review`, `validation`, or `maintenance`), `scope_id`,
  `execution_attempt_id`, and `entrypoint`. The execution attempt is distinct
  from a logical run, orchestration attempt, transaction attempt, run token,
  PID, or SLURM job; those remain typed correlation fields.
- The path is
  `<log-root>/<scope_kind>-<scope_id>/<execution_attempt_id>/<entrypoint>.jsonl`.
- Local managed directories and files use modes `0700` and `0600`, subject to a
  stricter umask. Shared-cluster permissions require explicit policy and must
  not become world-accessible. The root is pinned once; managed descendants
  reject symlinks, unsafe identities, ownership/type changes, and existing
  attempts or files. Creation is exclusive; prior state is never truncated,
  appended to, or adopted.

Each UTF-8 JSON line contains at least:

```text
schema_version, timestamp_utc, monotonic_seconds, sequence,
severity, console_detail, entrypoint, component, scope_kind, scope_id,
execution_attempt_id, mode, phase, event, message, fields
```

Version 1 begins at `1.0.0`; timestamps are RFC 3339 UTC; sequence increases
strictly; and `fields` is typed context. `severity` is `debug`, `info`,
`warning`, or `error`; `console_detail` is `normal`, `verbose`, `debug`, or
`durable_only`. Raw or untrusted diagnostics may be `durable_only`; a separate
sanitized warning/error names the operation and log path. The opening event
records the effective console level and its resolution source. Progress and
results use `info`, internal diagnostics use `debug`, and NORAD-authored
warnings/errors are console-visible at `normal`. Validator semantic failure and
process exit remain separate typed facts.

Generated identity, timestamps, duration, and scheduler context make literal
log bytes nondeterministic. Cross-level tests compare a documented normalized
semantic projection with injected clock/identity context where supported. Only
contract-declared volatile non-log fields may be normalized; stable payload
bytes, scientific/data fields, hashes, states, ordering, and exits remain exact.

### Ownership, publication, and failure

- One operation file has one writer. Delegates provide structured events or
  classified diagnostics through a private channel and never append concurrently
  or create duplicate attempts. Declared child machine stdout continues
  unchanged to its consumer.
- Events are line-buffered and flushed per record, with synchronization at
  phase, failure, and recovery boundaries and before an existing receipt-last
  marker. The required final pre-receipt event is `publication_ready`; the
  receipt remains the authoritative completion marker. A post-receipt closing
  observation is best-effort and cannot change exit, rollback, or completed
  transaction state. Non-transactional success synchronizes a terminal event.
- Initialization, write, or sync failure before transaction completion follows
  the operation's established failure/rollback path and preserves locks,
  markers, backups, staging, and other recovery evidence. Interrupted attempts
  preserve partial logs. Catchable signals receive best-effort event, flush,
  and child cleanup while retaining established signal exits; uncatchable node,
  process, or storage loss may leave a partial record and never implies complete
  capture.

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
`<redacted>`; the environment is never dumped; commands are recorded only after
argument classification. Application logs are protected operational data, not
presumed-public sanitized records. NORAD does not automatically rotate,
truncate, compress, upload, or delete application logs. Creating a log never
promotes runtime, cluster, scientific, or biological evidence. Only an
explicitly authorized immutable copy with the required path, hash,
relationship, and evidence policy may satisfy an existing runtime- or
cluster-log role.

### Scheduler relationship

SLURM `logs/%x-%j.out` and `logs/%x-%j.err` remain scheduler-owned compatibility
and diagnostic streams, not application logs. Scheduler capture opens before
job execution and therefore retains its submit-path contract. Adopted jobs
receive resolved controls through exported environment, record job identity as
correlation metadata, and report the application-log path once to scheduler
stderr. Machine stdout reaches `.out`; human projection reaches `.err`. A
transport wrapper does not create a second attempt when the delegated semantic
operation already owns it.

## Blocked by

- [LOG-02](../COMPLETED/LOG-02-define-logging-contract.md) — Required: exact public logging semantics must be approved.
- [REVIEW-UX-03](../TODO/REVIEW-UX-03-review-usability-plan.md) — Required: all independent plan reviews must be incorporated.

## Completion unblocks

- [LOG-05](../TODO/LOG-05-activate-concise-default-logging.md) — Partially: every concrete `LOG-04-*` domain-adoption card must also complete before activation.

## Prerequisites

- `PLAN-02Z` must have created concrete, non-wildcard `LOG-04-*` adoption cards
  for all applicable domains.

## Required context

- Logging contract/inventory, target topology, public CLI and scheduler
  contracts, run/attempt identity, current ignored log paths, and failure tests.

## Questions owned by this card

- None.

## In scope

- Level parsing/validation, sink routing, durable context/identity, failure
  flush/tail behavior, neutral APIs, and independent foundation tests.

## Out of scope

- Migrating every stage, changing defaults, altering exits/artifacts, logging
  secrets, or implementing retention cleanup.

## Deliverables

- Neutral foundation, public API tests, and one representative adoption proving
  behavior invariance without broad rollout.

## Acceptance evidence

- Equivalent runs at every level preserve exact stable non-log artifacts,
  hashes, states, rollback, ordering, and exits. Contract-declared volatile
  receipt/output fields match under controlled or normalized comparison.
- Stream separation, severity/detail mapping, lossless diagnostic-byte
  encoding, sensitive `durable_only` child handling, sanitized failure tails,
  complete durable detail, interruption/failure flushing, and invalid-level
  behavior pass focused tests.

## Canonical documentation updates

- Current architecture, logging/local library README, `RUNBOOK.md` for exact
  interfaces, `TROUBLESHOOTING.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, and this
  card.

## Escalation conditions

- Stop if the foundation requires stage awareness, changes a machine stream,
  drops failure evidence, or introduces automatic log deletion.

## Completion record

Not started. Select this card for read-only planning; implementation requires
separate approval.
