# Runtime-availability inspection owner

[`inspector.py`](inspector.py) owns `inspect_runtime_availability(...)` and
`emrys debug runtime-availability`. It admits an explicit profile, performs
read-only tool-version, R-namespace, hash, and path-visibility probes, and
returns deterministic observations without publication. Doctor consumes this
API directly.

Dry-run probes but writes nothing; `--execute` publishes the requested TSV.
Exit zero means probing/publication completed, not that required checks passed.
Tool/hash processes have a 30-second bound and R namespace loads a 120-second
bound; timeouts fail and are not retried. Installed R packages must resolve to
the admitted canonical package tree, whose internal symlinks and special files
are rejected.

This owner does not infer context, install or repair dependencies, load modules,
or execute the workflow. Preserve report, lock, temporary, and predecessor
paths after publication failure; known cleanup/restoration gaps remain defects,
not proof of readiness or cluster execution.
