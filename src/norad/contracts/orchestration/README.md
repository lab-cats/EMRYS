# Orchestration contracts

This neutral package owns the closed, versioned machine records for the B0
local-pilot lifecycle and the deterministic projection into the existing
artifact reporting contract. It does not normalize YAML requests, execute
workflow jobs, infer state, publish records, or implement a CLI.

The deliberate public Python API is `norad.contracts.orchestration`. It loads
only the adjacent registered Draft 2020-12 schemas, validates strict JSON
objects, emits canonical identity JSON bytes and hashes, and applies the small
cross-field invariants that JSON Schema cannot express. Complete execution
validation requires the exact profile record so all four reporting projection
references can be reconstructed and compared.

The optional `resource-config` and `launcher-config` selectors validate authored
configuration fragments before their application owners layer them over
packaged defaults. Resource configuration controls the one-host workflow budget;
launcher configuration controls the outer single-allocation submission. Neither
configuration is scientific run intent, and this neutral package does not load
YAML, inspect environment variables, or choose precedence.

The lifecycle family includes an explicit run-lock record, an immutable
workflow attempt that binds its exact canonical workflow-config reference, and
a terminal attempt receipt with mutually consistent executor exit/signal,
blocker, message, verified-scope, reporting, and completion facts. The public
`load_json_object_bytes` parser exists so a caller can parse already admitted
descriptor bytes without reopening a pathname.

Workflow attempts bind an ordered exact required-tool roster. Each file-backed
identity records its name, observed version, authored path, canonical resolved
path, and SHA-256; a null digest is allowed only for the specifically admitted
canonical `renv` project/library directories. Lifecycle admission rechecks the
same targets and bytes before execution, after execution, and before resume.
Each fixed `r_*` identity instead binds its observed namespace version, exact
canonical installed-package root, and a deterministic tree SHA-256 over sorted
entry kind, relative path, permission mode, size, and regular-file bytes.
Symbolic links and special entries are rejected; only the `renv_project` and
`renv_library` directory identities retain null digests.
Readiness also requires the existing selected R library to contain the pinned
`renv` package before any R process starts. The shared guarded selector removes
ambient shell and R startup hooks, disables `renv` autoloading, and checks that
required namespaces resolve under that library; planning never restores,
bootstraps, installs, or downloads dependencies.

Owner tasks have a fixed producer-entry ledger beneath
`state/task-starts/<machine-key>/<scope-id>.json`. Each create-exclusive
`task-start` record binds the exact workflow attempt, workflow config, and task
dispatch admitted immediately before producer entry. Task attempts distinguish
pre-entry failures with a null start reference; every post-entry attempt and
verified task binds the published start record. Every task attempt also binds
both captured streams as relative-path/SHA-256 record references; inspection
and verified-task reuse re-read the exact log bytes.

The only stationary output exception is the exact Step `00c` FASTA-sidecar
pair. Readiness requires its FASTA to be canonical and readable and its real
parent to be readable, writable, and searchable without creating an access
probe. The task boundary rechecks that access immediately before publishing
`task-start`; permission drift retains a failed pre-entry attempt and bound
logs but enters no producer and creates no sidecar residue.

Reporting producers have a separate fixed ledger beneath
`state/reporting/<kind>/`: `start.json` binds the origin workflow attempt and
configuration before producer entry, while `verified.json` binds that marker
to a semantically revalidated receipt after receipt-last publication. The
three closed kinds are `artifact_index`, `run_summary`, and `html_report`.
