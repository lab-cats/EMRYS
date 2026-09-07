# Orchestration contracts

`emrys.contracts.orchestration` owns the closed schemas, canonical JSON, hashes,
and cross-record invariants for Project, Analysis, immutable Execution Plan and
Run, Attempt, task, lock, receipt, and reporting-ledger records. It does not
load YAML, choose an Analysis or profile, execute work, infer state, publish
records, or implement a CLI.

`emrys.project.v1` is the scientist-authored contract: one Dataset and Reference
plus named Analyses. An Analysis may use the flat paired-CMH compatibility form
or an installed module with closed module-owned configuration. The historical
request-v3 schema remains registered only for exact old-Run admission.

The admitted module descriptor is composed onto the fixed processing profile
before Run identity is frozen. Processing compatibility through Steps `00`–`06`
is calculated separately so stationary artifacts can be reused without sharing
downstream identity. The authored execution profile separates Run-bound
resources from Attempt-local placement.

Attempts bind exact tool/runtime identities, immutable configuration, logs,
task-start records, task attempts, and verified tasks. Reporting has separate
start/verified ledgers for artifact index, run summary, and HTML report. Current
scientific receipts exclude reporting; existing historical records retain their
registered semantics. File-backed and installed-package identities are
rechecked at the execution and reuse boundaries and fail closed on drift.
