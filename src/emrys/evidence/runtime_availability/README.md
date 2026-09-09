# Runtime-availability inspection owner

This owner checks the tools and files named by one runtime profile. Doctor
uses its read-only API to observe tool versions, R namespaces, hashes, and path
visibility. It does not install or repair dependencies, load modules, infer
context, or run the workflow.

## Use and outputs

The [profile example](../../../../configs/runtime_preflight.example.tsv) defines
the input shape. Select the context in which probes actually run, `local` or
`cluster_batch`. This example probes without publishing:

```bash
emrys debug runtime-availability \
  --profile /absolute/path/to/runtime_profile.tsv \
  --runtime-context local --output /absolute/existing/directory/runtime.tsv
```

Add `--execute` to publish the deterministic TSV. Exit zero means probing and
any requested publication completed; inspect the rows to see whether every
required check passed. A report is not cluster-execution proof.

## API and probe boundaries

[`inspector.py`](inspector.py) exposes `inspect_runtime_availability(...)`,
`RuntimeCheck`, and `RuntimeObservation`. The latter two are immutable values
defined in [`_runtime_model.py`](_runtime_model.py). Observed locations stay
`Path` or `None`; profile targets and serialized evidence keep their declared
text. Inspection itself returns observations without publishing them.

Tool/hash processes have a 30-second limit and R namespace loads a 120-second
limit. Timeouts fail without retry. Installed R packages must resolve to the
admitted canonical package tree, which rejects internal symlinks and special
files.

## Known publication limits

Lock creation writes and syncs the lock before returning its descriptor to the
publisher's cleanup handler. A write or sync failure can therefore leave both
the lock and an open descriptor. Failed predecessor restoration can leave a
`.previous` file after cleanup releases the lock. Finally, lock-removal
`OSError` is suppressed: the command can leave a lock without reporting that
failure, even after otherwise successful publication.

The [owner tests](../../../../tests/evidence/runtime_availability/test_runtime_availability.py)
characterize these gaps. Restoration or cleanup errors can change which failure
is reported; suppressing lock removal also preserves any earlier exception.
These statements describe current behavior, not a new diagnostic-priority rule.
Keep the report, lock, temporary, and predecessor paths after failure. None of
these states authorizes cleanup or establishes runtime readiness.
