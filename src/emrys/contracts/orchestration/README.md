# Orchestration contracts

`emrys.contracts.orchestration` defines registered schemas, canonical JSON,
hashes, and consistency rules for Project, Analysis, immutable Execution Plan
and Run, Attempt, task, lock, receipt, and reporting records. It validates
records; it does not load YAML, choose an Analysis, run work, infer state,
publish records, or provide a CLI. The artifact-inventory owner reads fixed
processing tasks and artifact ownership from the admitted source checkout's
shipped profile. A retained Run profile cannot redefine those implementation
facts. The [Run-coordinator contract](../../orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns new-Run and resume admission.

Scientists author `emrys.project.v1`: one Dataset and Reference, with named
Analyses. An Analysis uses either the flat paired-CMH compatibility form or an
installed module's validated configuration. Request-v3 remains only for reading
exact historical Runs. Planning combines the validated module descriptor with
the fixed processing profile before freezing Run identity. Steps `00`–`06`
have a separate compatibility identity so their unchanged artifacts can be
reused without sharing downstream identity. That identity binds the shipped
processing profile's complete bytes because they now define executable tasks;
changing that file requires new Processing results. Execution profiles separate
Run-bound resources from Attempt-local placement.

Attempts bind exact tools/runtime, immutable configuration, logs, task starts,
task attempts, and verified tasks. Reporting records its own starts and verified
results for the artifact index, summary, and HTML. Current scientific receipts
exclude reporting; historical records retain their registered meaning. The
public `attempt-receipt` validator accepts historical v1 and current v2 through
the same registry as higher-level validation. Execution and reuse recheck
file-backed and installed-package identities and reject drift.
