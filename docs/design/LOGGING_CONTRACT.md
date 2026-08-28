# Application logging contract

This is the binding cross-cutting application logging contract. The neutral
foundation is implemented by the
[application-logging owner](../../src/emrys/libraries/application_logging/README.md),
but no production command or scheduler wrapper currently adopts it. That rollout
remains `LOG-05` in the [findings matrix](../tasks/backlog_matrix.md). A command
implements this contract only when its owner documentation and direct tests say
so. Foundation code remains stage-independent and never imports a stage.

## Adoption boundary

Production adoption is evaluated at one semantic application-operation
boundary, not independently at every leaf command, compatibility facade,
transport, or scheduler wrapper. The accepted outer operation owns exactly one
application attempt and resolves controls once. Retained delegates receive the
resolved controls and event context explicitly and do not open a second attempt.

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
- Until a state root exists, the default is
  `<repository-root>/logs/application`, derived from repository/package
  identity rather than caller CWD. An explicit root is absolute. Help and
  parser diagnostics remain side-effect-free command responses.
- stdout is reserved for declared machine responses. Human progress, warnings,
  errors, commands, paths, and recovery guidance use stderr. Stable machine
  bytes, paths, ordering, hashes, transactions, and validator seven-column
  output remain exact; semantic failed rows and process exits stay distinct.
- Valid dry-run creates no application log. At `normal` it prints the resolved
  nonsecret command and essential plan to stderr. Higher levels add context
  without changing probes, child flags, computation, artifacts, validation,
  locking, publication, rollback, cleanup, or exits.

| Level | Console projection | Durable log |
| --- | --- | --- |
| `normal` | identity, meaningful phases, result, evidence boundary, warnings, errors, bounded failure summary | complete observed event set |
| `verbose` | `normal` plus resolved inputs/outputs, safe commands, declared hashes, versions, publication plan | same event semantics |
| `debug` | `verbose` plus classified child diagnostics, allowed environment context, timing, recovery identities | same event semantics |

Machine payloads, binary streams, FASTQ/BAM/VCF content, large tables, and
report bytes are not copied to JSONL. Record roles, paths, hashes, and available
byte/row counts. Invalid UTF-8 diagnostics use sequenced
`child_diagnostic_bytes` events with unbroken RFC 4648 base64, byte count,
SHA-256, stream, and component; never replace bytes silently.

## Attempt identity and record

- One adopted execute, substantive validation/check, mutating maintenance
  action, or validation-gate invocation owns one application attempt. Help,
  parse/control failures, and valid dry-runs own none.
- The attempt begins after minimal log-control and scope validation but before
  semantic input validation, expensive work, output directories, locks, or
  publication, so execute preflight failures are logged without authorizing
  other side effects.
- The owner assigns `scope_kind` (`run`, `sample`, `cohort`, `reference`,
  `review`, `validation`, or `maintenance` initially), `scope_id`,
  `execution_attempt_id`, and `entrypoint`. Execution attempt is distinct from
  logical run, orchestration/transaction attempt, run token, PID, and job ID.
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
- Flush each line, synchronize at phase/failure/recovery boundaries and before
  an existing receipt-last marker, and emit `publication_ready` as the final
  pre-receipt event. The receipt remains authoritative completion. A
  post-receipt observation is best-effort and cannot change exit, rollback, or
  committed state. Nontransactional success synchronizes a terminal event.
- Initialization, write, or sync failure before completion follows established
  failure/rollback behavior and preserves locks, markers, backups, staging, and
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

SLURM `logs/%x-%j.out` and `logs/%x-%j.err` remain scheduler-owned compatibility
and diagnostic streams, not application logs. They open before job execution
and retain the submit-path contract. Adopted jobs receive resolved controls via
exported environment, record job identity as correlation metadata, and report
the application-log path once to scheduler stderr. Machine stdout reaches
`.out`; human projection reaches `.err`. A transport wrapper does not create a
second attempt when its delegated semantic operation already owns one.
