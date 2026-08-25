# Application logging foundation

This neutral package implements the compact foundation defined by the
[`application logging contract`](../../../../docs/design/LOGGING_CONTRACT.md).
It uses Python's standard `logging` API for collaborators while one protected
owner serializes a complete JSONL attempt log before projecting concise human
output to stderr. It never writes machine stdout.

```python
from emrys.libraries.application_logging import (
    AttemptIdentity,
    event,
    field,
    open_attempt_log,
    resolve_log_controls,
)

controls = resolve_log_controls(
    source_checkout=source_checkout,
    cli_level=arguments.log_level,
    cli_root=arguments.log_root,
)
attempt = open_attempt_log(
    controls=controls,
    identity=AttemptIdentity("run", run_id, execution_attempt_id, "emrys-run"),
    mode="execute",
    component="orchestration",
)
log = attempt.logger(component="alignment", phase="execute")
log.info(
    "Alignment completed.",
    extra=event(
        "alignment_completed",
        fields={"sample_count": field(sample_count, console=True)},
    ),
)
```

`add_log_arguments()` installs the unresolved `--log-level` and `--log-root`
leaf options. `resolve_log_controls()` applies command line, environment, then
repository-derived defaults without filesystem side effects. Resolved controls
carry the exact two-variable environment projection required by delegates.

`normal`, `verbose`, and `debug` affect only stderr projection. Every admitted
event remains durable; `durable_only` never reaches the console. `field()`
requires explicit console visibility and discards secret values before
inspection. Large or binary payloads are rejected as ordinary fields.

The custom storage code is deliberately narrow. It creates
`<log-root>/<scope>-<id>/<execution-attempt>/<entrypoint>.jsonl` exclusively,
uses protected modes, rejects symlink/adoption races, pins path identity,
completes interrupted or short writes, synchronizes declared boundaries, and
preserves partial logs.

The attempt owner exposes publication, receipt-failure recovery,
nontransactional terminal, failure, interrupt, and post-receipt boundaries.
Reserved lifecycle events cannot be forged through standard logger extras.
Receipt publication remains authoritative; logging never creates a receipt or
changes scientific, transaction, recovery, or exit semantics.

`helpers.py` contains the small pure mechanisms for classified command and
selected-environment capture, exact invalid-byte diagnostics, bounded failure
summaries, and explicit SLURM correlation. Production command and wrapper
adoption belongs to `LOG-05`; this package does not configure a root logger,
capture unrelated namespaces, rotate or delete logs, or claim cluster,
scientific, or biological evidence.
