# Runtime availability

This owner checks the tools and files needed by a Project. Runtime discovery,
Doctor, and execution use the same probes for tool versions, R packages,
SHA-256 support, and path visibility. The coordinator owns readiness decisions
and the Project runtime inventory; this owner returns observations.

[`inspector.py`](inspector.py) reads the Project inventory as two TSV columns,
`check_id` and `target`, with one absolute path for each of 12 runtime choices.
The installed policy derives all 26 fixed checks, including Python and Java
aliases, Picard arguments, and the selected R launcher. The installed package
supplies the R project path. Doctor adds the selected analysis module's declared
dependencies; execution reconstructs those same checks from the Run-bound
analysis policy. Probe rules are never copied into the inventory.

Inspection binds the exact inventory bytes and returns immutable observations.
Every check is required and runs in the process that requested it. Direct and
Slurm execution use the same probes; scheduler placement is checked by the
coordinator. The inventory cannot select optional checks or alternate contexts.

Observed locations remain `Path` or `None`. Tool and hash processes have a
30-second limit; R namespace loads have a 120-second limit. Timeouts fail without
retry. The coordinator always supplies the guarded R environment, and loaded
packages must resolve to the selected library's exact package roots. SHA-256
probing uses the selected Python interpreter; executable paths are absolute.
Custom analysis dependencies still support executables, R namespaces, files
and package trees through these same checks.

Use [Doctor and runtime discovery](../../../../docs/operations/RUNBOOK.md) for
Project readiness. The standalone runtime-report command and its TSV publisher
are retired. Existing reports, locks, temporary files, and predecessor files
remain operator evidence; retirement does not authorize their cleanup.

The [owner tests](../../../../tests/evidence/runtime_availability/test_runtime_availability.py)
cover path-choice admission and probe behavior. These observations establish the
checks performed, not successful workflow execution or scientific validity.
