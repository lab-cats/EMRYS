# Workflow scheduling

[`Snakefile`](Snakefile) schedules the exact graph stored in an immutable Run.
Planning combines the [common processing graph](contracts/README.md) with one
validated Analysis module and freezes the result before execution. Snakemake
runs the named producers; their contracts define scientific behavior and the
Run coordinator decides whether their results count as complete.

A full Run executes common Steps `00`–`08`, the module's Step `09`, and optional
Step `10`. Reporting follows outside Snakemake. `emrys run --through processing`
stops after evidence-complete Steps `00`–`06`; a new downstream Run may reuse
those compatible immutable results.

The [local engine profile](profiles/local/README.md) runs every job on one host:
a workstation or a single Slurm allocation. Run planning supplies capacity and
task resources. Use `emrys run` and `emrys resume`, not bare Snakemake or direct
profile invocation.

[STAGE_MAP](../src/emrys/contracts/STAGE_MAP.md) defines producer identities and
artifact dependencies. The [run-coordinator contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md)
defines materialization, completion, reuse, reporting, and recovery.

The graph reads dispatches through `task.load_dispatch` and resource records
through `resource_policy.admit_resource_policy_record`, the same owners used by
execution and resume. Workflow-specific checks still bind each dispatch to its
Run, task scope, and Attempt. The named rules and dependency barriers remain
unchanged; validating a graph does not replace checks immediately before a task.
