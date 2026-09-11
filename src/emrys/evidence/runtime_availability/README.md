# Runtime availability

This owner checks the tools and files needed by a Project. Runtime discovery,
Doctor, and execution use the same probes for tool versions, R packages,
SHA-256 support, and path visibility. The coordinator owns readiness decisions
and the Project runtime inventory; this owner returns observations.

[`inspector.py`](inspector.py) admits exact profile bytes and returns their
hash with immutable checks and observations. A required check must pass in
the declared execution context. A context mismatch remains `blocked` for a
required check and `not_checked` for an optional one. The caller supplies the
context; inspection does not infer that a process is running on a compute node.

Observed locations remain `Path` or `None`. Tool and hash processes have a
30-second limit; R namespace loads have a 120-second limit. Timeouts fail without
retry. When the coordinator supplies the guarded R environment, loaded packages
must resolve to the selected library's exact package roots.

Use [Doctor and runtime discovery](../../../../docs/operations/RUNBOOK.md) for
Project readiness. The standalone runtime-report command and its TSV publisher
are retired. Existing reports, locks, temporary files, and predecessor files
remain operator evidence; retirement does not authorize their cleanup.

The [owner tests](../../../../tests/evidence/runtime_availability/test_runtime_availability.py)
cover profile admission and probe behavior. These observations establish the
checks performed, not successful workflow execution or scientific validity.
