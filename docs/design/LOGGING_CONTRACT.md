# Application logging contract

This is the binding cross-cutting application logging contract. The neutral
foundation is implemented by the
[application-logging owner](../../src/emrys/libraries/application_logging/README.md).
The complete retained-operation roster is executing `run` and `resume`, their
automatic reporting in the same log, standalone report generation, and
confirmed `emrys doctor --repair`. A Run execute owns exactly one compute-side
application attempt; scheduler submission transport and valid dry-run own none.
The roster and direct/Slurm success plus controlled failure-and-resume parity
are complete under `LOG-05` in the
[findings matrix](../tasks/backlog_matrix.md). A command implements this
contract only when its owner documentation and direct tests say so. Foundation
code remains stage-independent and never imports a stage.

## Adoption boundary

Production adoption is evaluated at one semantic application-operation
boundary, not independently at every leaf command, compatibility facade,
transport, or scheduler wrapper. The accepted outer operation owns exactly one
application attempt and resolves controls once. Retained delegates receive the
resolved controls and event context explicitly and do not open a second attempt.
For scheduled run-coordinator execution, the compute-side `run`/`resume` delegate is
that operation; submission is transport only. Automatic reporting continues in
that Run log, while standalone reporting opens one log only when generation
begins. For Doctor, only confirmed repair is the operation; readiness diagnosis
is not a durable diagnostic lifecycle.

All other current public operations own no application log: Project and
synthetic/manifest initialization, validation, runtime discovery and profile
publication, Doctor diagnosis/preview/refusal, Run or report planning/refusal,
complete report reuse, inspection, debug inspection, and scheduler submission.
Their admitted outputs or direct command diagnostics remain authoritative.
Delegated scientific tasks retain their task streams and evidence beneath the
outer Run operation and do not open additional application logs.

Each bounded adoption package satisfies the operation, ownership, placement,
projection, stream, and parity admission conditions in its owner documentation
and direct tests. An explicitly approved transitional compatibility operation
may adopt the foundation for bounded support but does not satisfy final
retained-operation coverage. An unapproved retiring surface is out of scope;
closure remains governed by the
[matrix adoption guard](../tasks/backlog_matrix.md#log-05-adoption-and-closure-guard).

Every implementation slice that touches a retained applicable operation must
record its `LOG-05` disposition. If the slice changes that operation's human
output or durable diagnostic path, adoption belongs in the same vertical slice
unless the operation is explicitly classified as not applicable or retiring.
The slice must not introduce an interim logger, log format, wrapper-owned
attempt, or second console convention. A thin retained shell bootstrap passes
the accepted operation context through and does not become another logging
owner.

The packaged-Python production-import roster is mechanically guarded. Changing
it is part of the adopter's approved slice and must update the current
[source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md), owner contract,
and direct tests together. The static import ratchet does not establish semantic
one-attempt ownership, output preservation, wrapper adoption, or Local/SLURM
parity; owner and integration tests must do so. It also does not select public
nouns, classes, commands, state vocabulary, filesystem layout, or scheduler
policy before their own bounded decisions.

## Sinks, controls, and streams

- Two sinks are explicit: a concise console for current-operator progress,
  results, warnings, and failures; and a complete application log for attempt
  audit, debugging, and recovery.
- Adopted Python, shell, and R commands accept `--log-level
  normal|verbose|debug` and `--log-root PATH`; the environment forms are
  `EMRYS_LOG_LEVEL` and `EMRYS_LOG_ROOT`. Resolution is command line,
  environment, then default, resolved once by the outer operation and passed to
  delegates explicitly.
- `normal` is the default; there is no `quiet`. Empty, unknown, or conflicting
  controls fail before log, output, lock, scratch, or compute side effects while
  preserving established parse exits. A legacy alias requires parity-tested
  migration.
- Grouped `run`/`resume`, standalone report generation, and confirmed Doctor
  repair default to
  `<project-root>/logs/application`. Until a
  state root exists for another adopter, its default is
  `<repository-root>/logs/application`, derived from repository/package
  identity rather than caller CWD. An explicit root is absolute. Help and
  parser diagnostics remain side-effect-free command responses.
- stdout is reserved for declared machine responses. Human progress, warnings,
  errors, commands, paths, and recovery guidance use stderr. Stable machine
  bytes, paths, ordering, hashes, transactions, and validator seven-column
  output remain exact; semantic failed rows and process exits stay distinct.
- Valid dry-run creates no application log. Direct `run`/`resume` planning at
  `normal` prints the essential Run/work/reporting plan to stderr; a submit-host
  Slurm dry-run prints only concise placement. `verbose` adds applicable
  Run-root/resource/allocation or execution-profile/scheduler-stream detail;
  `debug` adds exact safe engine, scheduler, and task commands. Levels do not
  change probes, child flags, computation, artifacts, validation, locking,
  publication, rollback, cleanup, or exits.

| Level | Console projection | Durable log |
| --- | --- | --- |
| `normal` | Run identity and work/reporting summary; meaningful phases; verified Results/evidence; warnings, errors, durable log path, and bounded failure summary | complete observed event set |
| `verbose` | `normal` plus Run root, resources/allocation, execution profile, scheduler streams, and other resolved operational paths | same event semantics |
| `debug` | `verbose` plus exact safe engine/scheduler/task commands, classified child diagnostics, allowed environment context, timing, and recovery identities | same event semantics |

Machine payloads, binary streams, FASTQ/BAM/VCF content, large tables, and
report bytes are not copied to JSONL. Record roles, paths, hashes, and available
byte/row counts. Invalid UTF-8 diagnostics use sequenced
`child_diagnostic_bytes` events with unbroken RFC 4648 base64, byte count,
SHA-256, stream, and component; never replace bytes silently.

## Attempt identity and record

- One executing `run` or `resume`, standalone report-generation operation, or
  confirmed Doctor repair owns one application attempt. Help, CLI parse
  failures, invalid log controls, invalid execution-profile/delegate context,
  inadmissible workspace scope, and valid dry-runs own none.
- The attempt begins after minimal log-control and scope validation but before
  semantic input validation, expensive work, output directories, locks, or
  publication, so execute preflight failures are logged without authorizing
  other side effects.
- A terminal direct `run` or `resume` plan is not an adopted execution Attempt
  until the user confirms it. Planning and refusal therefore own no log.
  Confirmation passes that exact frozen plan into execution and opens the
  application log before lifecycle admission; explicit noninteractive
  `--execute` retains the log-before-semantic-preflight behavior above.
- Doctor diagnosis and repair preview own no attempt. Terminal repair
  opens one `maintenance` attempt only after confirmation and before its first
  filesystem or package-manager mutation; noninteractive mutation requires
  `--repair --execute`. The log binds any direct-storage receipt and the exact
  package managers/packaged Pixi inputs when runtime work is selected, records
  each action, and terminalizes only after complete Project requalification.
  Logging cannot authorize input mutation or migration/mutation of a ready
  site/user runtime profile.
- Terminal Slurm placement confirms a frozen submission plan, not a Run plan,
  and owns no application log. Its private compute delegate constructs the Run
  and opens the application log inside the allocation.
- The owner assigns `scope_kind` (`run`, `sample`, `cohort`, `reference`,
  `review`, `validation`, or `maintenance` initially), `scope_id`,
  `execution_attempt_id`, and `entrypoint`. Execution attempt is distinct from
  logical run, orchestration/transaction attempt, run token, PID, and job ID. A
  new grouped Run uses provisional `run:pending` scope until planning resolves
  the immutable Run ID, which is then recorded as event context.
- The path is
  `<log-root>/<scope_kind>-<scope_id>/<execution_attempt_id>/<entrypoint>.jsonl`.
  Managed directories/files use `0700`/`0600` subject to stricter umask. Pin the
  root once; reject symlinks, unsafe identities, ownership/type changes, and
  existing attempt paths. Create exclusively; never truncate, append to, or
  adopt prior state.

Each UTF-8 JSON line contains at least:

```text
schema_version, timestamp_utc, monotonic_seconds, sequence,
severity, console_detail, entrypoint, component, scope_kind, scope_id,
execution_attempt_id, mode, phase, event, message, fields
```

Version 1 begins at `1.0.0`; timestamps are RFC 3339 UTC; sequence increases
strictly; `fields` is typed context. `severity` is `debug`, `info`, `warning`,
or `error`; `console_detail` is `normal`, `verbose`, `debug`, or
`durable_only`. Untrusted diagnostics may be durable-only, paired with a
sanitized console warning and log path. The opening event records effective
level and resolution source. Validator semantic failure and process exit remain
separate typed facts.

Literal log bytes are nondeterministic because identity, time, duration, and
scheduler context vary. Cross-level tests compare a declared normalized
semantic projection with injected clock/identity where supported. Only
contract-declared volatile non-log fields may normalize; stable payloads,
scientific/data fields, hashes, states, order, and exits remain exact.

## Ownership, publication, and failure

- One operation file has one writer. Delegates return structured events or
  classified diagnostics through a private channel and never append
  concurrently or create duplicate attempts. Child machine stdout remains
  unchanged for its consumer.
- Grouped `run`/`resume` records `analysis_started` before workflow execution,
  `publication_ready` at the final pre-receipt boundary, and
  `receipt_committed` only after receipt-last publication succeeds.
- Flush each line, synchronize at phase/failure/recovery boundaries and before
  an existing receipt-last marker, and emit `publication_ready` as the final
  pre-receipt event. The receipt remains authoritative completion. A
  post-receipt observation is best-effort and cannot change exit, rollback, or
  committed state. Nontransactional success synchronizes a terminal event.
- Initialization failure is fail-fast before semantic planning. Once an attempt
  log is open, a write, sync, post-receipt observation, or close failure retains
  the partial log, emits one fixed degradation warning, and disables further log
  writes. It never changes workflow execution, authoritative receipt bytes or
  status, rollback, recovery, locks, or exit. The operation's own failure still
  follows established behavior and preserves markers, backups, staging, and
  recovery evidence. Interrupted attempts preserve partial logs. Catchable
  signals get best-effort event, flush, and child cleanup with established
  exits; uncatchable loss may leave a partial record and never implies capture.

After an attempted operation fails, stderr ends with a bounded summary naming:

1. entry point, phase, and status;
2. scope, execution attempt, and application-log path;
3. owned lock, stage, backup, and recovery paths;
4. at most 20 console-safe events and 8 KiB, with explicit truncation; and
5. one established next action or runbook route.

If initialization failed, state that no durable log exists. Never replay
`durable_only` content; report its sanitized count and log pointer.

Fields and commands carry sensitivity metadata. Render known secrets as
`<redacted>`, never dump the environment, and record commands only after
argument classification. Logs are protected operational data, not presumed
public. EMRYS does not automatically rotate, truncate, compress, upload, or
delete them. A log never promotes runtime, cluster, scientific, or biological
evidence. Only an authorized immutable copy with required path, hash,
relationship, and evidence policy may satisfy an existing runtime/cluster role.

## Scheduler relationship

Grouped `run`/`resume` writes scheduler-owned compatibility and diagnostic
streams beneath `<project-root>/logs` as `emrys-local-pilot-%j.out` and
`emrys-local-pilot-%j.err`; they are not application logs. The submission
transport owns no application attempt. Its compute-side delegate receives the
resolved controls, opens the operation's single attempt, records job identity
as correlation metadata, and sends human projection to scheduler stderr.
Submission dry-run creates neither the scheduler log directory nor an
application log.
