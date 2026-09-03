# Application logging contract

The neutral
[application-logging owner](../../src/emrys/libraries/application_logging/README.md)
provides concise operator output and a protected durable record without
becoming computation, publication, recovery, or completion authority. The
current source-import boundary is recorded in
[`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md); accepted
future changes live only in the [findings matrix](../tasks/backlog_matrix.md).

## Ownership and adoption

One executing `run` or `resume`, independently generated report, or confirmed
`doctor --repair` operation owns one application attempt. Automatic reporting
continues in its Run attempt rather than opening another log. The Slurm
submission transport and delegated tasks own none; the compute-side Run owns
the attempt.

Initialization, validation, discovery, diagnosis, inspection, help, parse
failure, valid dry-run, report reuse, and any refusal before execution own no
application log. A command satisfies this contract only when its operation
owner and direct tests establish one-attempt ownership and output parity.
Delegates receive resolved controls and event context explicitly and never
open or append to the operation log.

## Sinks, controls, and streams

- Human progress, warnings, failures, Results, and recovery guidance use a
  concise stderr sink. Declared machine responses retain stdout unchanged.
- The complete observed event set uses one JSONL application log. Machine or
  binary payloads, FASTQ/BAM/VCF content, large tables, and report bytes are not
  copied into it; their roles, paths, hashes, and available sizes/counts may be
  recorded.
- Adopted commands accept `--log-level normal|verbose|debug` and
  `--log-root PATH`; `EMRYS_LOG_LEVEL` and `EMRYS_LOG_ROOT` are the environment
  forms. Precedence is command line, environment, then default, resolved once
  by the outer operation. `normal` is the default; there is no `quiet` level.
- Invalid, empty, or conflicting controls fail before log, lock, scratch,
  output, or compute side effects while preserving established parse exits.
- The default root is `<project-root>/logs/application`. Until an adopter has
  a Project root, it is `<repository-root>/logs/application`, derived from
  source/package identity rather than caller CWD. An explicit root is
  absolute.
- A valid dry-run creates no log. Levels change projection only, never probes,
  child flags, computation, artifacts, validation, locking, publication,
  rollback, cleanup, or exits.

| Level | Console projection | Durable log |
| --- | --- | --- |
| `normal` | Run identity, work/reporting summary, meaningful phases, verified Results, warnings, errors, log path, and bounded failure summary | complete observed event set |
| `verbose` | `normal` plus Run root, resources/allocation, profile, scheduler streams, and resolved operational paths | same event semantics |
| `debug` | `verbose` plus exact safe engine, scheduler, and task commands, classified child diagnostics, allowed environment context, timing, and recovery identities | same event semantics |

Invalid UTF-8 child diagnostics use sequenced `child_diagnostic_bytes` events
with unbroken RFC 4648 base64, byte count, SHA-256, stream, and component.
Never replace diagnostic bytes silently.

## Attempt boundary and record

After minimal log-control and scope admission, noninteractive execution opens
the log before semantic preflight or other side effects. A terminal direct Run
opens it only after confirmation and before lifecycle admission. Doctor opens
one `maintenance` attempt after repair confirmation and before its first
filesystem or package-manager mutation. A Slurm submitter opens none; the
compute delegate opens the Run attempt inside the allocation.

The owner assigns `scope_kind` (`run`, `sample`, `cohort`, `reference`,
`review`, `validation`, or `maintenance`), `scope_id`,
`execution_attempt_id`, and `entrypoint`. Execution-attempt identity is
distinct from logical Run, orchestration Attempt, run token, PID, and job ID.
A new Run may begin with `run:pending` scope and then record its resolved
immutable Run ID as event context.

The path is:

```text
<log-root>/<scope_kind>-<scope_id>/<execution_attempt_id>/<entrypoint>.jsonl
```

Managed directories and files use `0700` and `0600`, subject to a stricter
umask. The root is pinned once; symlinks, unsafe identities, ownership/type
changes, and existing attempt paths are rejected. Creation is exclusive: an
attempt never truncates, appends to, or adopts prior state.

Each UTF-8 JSON line contains at least:

```text
schema_version, timestamp_utc, monotonic_seconds, sequence,
severity, console_detail, entrypoint, component, scope_kind, scope_id,
execution_attempt_id, mode, phase, event, message, fields
```

Version 1 starts at `1.0.0`; timestamps are RFC 3339 UTC; sequence increases
strictly; and `fields` is typed context. `severity` is `debug`, `info`,
`warning`, or `error`; `console_detail` is `normal`, `verbose`, `debug`, or
`durable_only`. The opening event records the effective level and resolution
source. Untrusted durable-only diagnostics are paired with a sanitized console
warning and log pointer. Validator semantic failure and process exit remain
distinct facts.

Literal log bytes are nondeterministic because identity, time, duration, and
scheduler context vary. Parity tests compare a declared normalized semantic
projection, never normalize stable payloads, science/data fields, hashes,
states, ordering, or exits.

## Publication, failure, and sensitivity

One operation file has one writer. Delegates return structured events or
classified diagnostics through a private channel; child machine stdout remains
unchanged for its consumer.

Grouped Run execution records `analysis_started` before workflow execution,
`publication_ready` at the final pre-receipt boundary, and
`receipt_committed` only after receipt-last publication succeeds. Each line is
flushed; the writer synchronizes phase, failure, recovery, and pre-receipt
boundaries. A post-receipt observation is best-effort and cannot change the
receipt, rollback, exit, or committed state. Nontransactional success
synchronizes its terminal event.

Once open, a write, sync, observation, or close failure retains the partial
log, emits one fixed degradation warning, and disables further writes. Logging
failure never changes workflow execution, receipt bytes or status, rollback,
recovery, locks, or exit. Catchable signals receive a best-effort event, flush,
and established child cleanup; uncatchable loss may leave only a partial log.

After an attempted operation fails, stderr ends with a bounded summary naming:

1. entrypoint, phase, and status;
2. scope, execution attempt, and application-log path;
3. owned lock, stage, backup, and recovery paths;
4. at most 20 console-safe events and 8 KiB, with truncation stated; and
5. one supported next action or runbook route.

If initialization failed, the summary states that no durable log exists.
`durable_only` content is never replayed; only its sanitized count and log
pointer are shown.

Fields and commands carry sensitivity metadata. Known secrets render as
`<redacted>`; the environment is never dumped; commands are recorded only
after argument classification. Logs are protected operational data and are not
automatically rotated, truncated, compressed, uploaded, or deleted. A log
cannot promote runtime, scheduler, scientific, or biological evidence.

## Scheduler distinction

Slurm compatibility streams live under `<project-root>/logs` as
`emrys-local-pilot-%j.out` and `emrys-local-pilot-%j.err`; they are not
application logs. Submission dry-run creates neither those paths nor an
application log. The compute delegate receives the resolved controls, opens
the operation's one application attempt, records scheduler identity only as
correlation metadata, and projects human output to scheduler stderr.
