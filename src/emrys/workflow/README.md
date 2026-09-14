# Workflow scheduling

[`Snakefile`](Snakefile) schedules the [common processing graph](contracts/README.md)
from the admitted installed package and the selected Analysis module.
New Run planning rejects processing dependencies that differ from that graph,
then freezes the combined plan. Existing Runs retain their profile bytes and
resume with the same fixed processing dependencies as before. Snakemake
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

[STAGE_MAP](../contracts/STAGE_MAP.md) defines producer identities and
artifact dependencies. The [run-coordinator contract](../orchestration/run_coordinator/CONTRACT.md)
defines materialization, completion, reuse, reporting, and recovery.

The graph reads the immutable Attempt manifest once and selects task definitions
through the task owner. Workers use the same task parser and resource-policy
owner. Verified tasks retain their original Attempt references on resume; pending
tasks must belong to the new Attempt. The named rules and dependency barriers
remain unchanged. Validating the graph does not replace identity and content
checks immediately before a task.
