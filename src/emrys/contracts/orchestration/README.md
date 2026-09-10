# Orchestration contracts

`emrys.contracts.orchestration` defines registered schemas, canonical JSON,
hashes, and consistency rules for Project, Analysis, immutable Execution Plan
and Run, Attempt, task, lock, receipt, and reporting records. It validates
records and parses closed JSON and YAML; it does not choose an Analysis, run work, infer state,
publish records, or provide a CLI. The artifact-inventory owner reads fixed
processing tasks and artifact ownership from the admitted installed package's
shipped profile. A retained Run profile cannot redefine those implementation
facts. The [Run-coordinator contract](../../orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns new-Run and resume admission.

Scientists author `emrys.project.v1`: one Dataset and Reference, with named
Analyses. An Analysis uses either the flat paired-CMH form or an installed
module's validated configuration. Both forms normalize into one module policy
and Analysis revision. Planning combines the validated module descriptor with
the fixed processing profile before freezing Run identity. Steps `00`–`06`
have a separate compatibility identity so their unchanged artifacts can be
reused without sharing downstream identity. That identity binds the shipped
processing profile's complete bytes because they now define executable tasks;
changing that file requires new Processing results. Execution profiles separate
Run-bound resources from Attempt-local placement.

Each Attempt manifest contains exact tools/runtime, workflow settings, and task
definitions. Task starts bind that manifest once; logs, terminal task results,
and verified markers remain separate execution evidence. Reporting records its own starts and verified
results for the run manifest and HTML. Scientific receipts exclude reporting.
Each task has one terminal result and a verified marker that binds that result.
The registry admits the current forms only; current releases have no obligation
to inspect, resume, or regenerate Runs from older versions under the
[version-support policy](../../../../docs/design/decisions/platform-direction.md#version-support).
Execution and reuse recheck file-backed and installed-package identities and
reject drift.
