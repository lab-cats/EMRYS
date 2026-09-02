# Orchestration contracts

This neutral package owns the closed, versioned machine records for the
orchestration lifecycle, immutable successor Analysis/Execution-Plan/Run
authorities, historical execution compatibility, and deterministic reporting
projections. It does not normalize Project YAML, select a named Analysis, execute
workflow jobs, infer state, publish records, or implement a CLI.

The deliberate public Python API is `emrys.contracts.orchestration`. It loads
only the adjacent registered Draft 2020-12 schemas, validates strict JSON
objects, emits canonical identity JSON bytes and hashes, and applies the small
cross-field invariants that JSON Schema cannot express. Successor Run admission
binds the exact Analysis revision, Execution Plan, Run record, and profile;
historical `emrys.execution.v1` validation retains its exact profile-bound
reporting projection.

`emrys.project.v1` is the sole active scientist-authored schema. It defines one
shared Dataset and Reference plus one or more named Analyses, each with its own
partition manifest and either the existing flat paired-CMH policy or an
explicit installed `module` plus module-owned closed `config`. An Analysis may select a nonempty
set of Dataset samples by ID; omission selects the complete Dataset. The
application layer validates all Analyses and selects one for `run`; the human
mapping key and authored selection order are not part of the content-derived
Analysis identity. The request-v3 schema remains registered
only for private, exact historical-Run re-admission. It is not accepted by
active Project commands. The flat compatibility path builds Analysis revision
v1; an explicit module builds revision v2 from its stable module/interface
version and normalized scientific configuration. Provider installation facts
remain execution/provenance facts rather than scientific Analysis fields.

The checked-in `emrys.profile.local_cmh.v2` record is the processing-profile
base through Step `08`, not the complete collaborator-module registry.
Application planning composes it with one admitted module descriptor and binds
the exact immutable result into the Execution Plan. Processing compatibility
is separately derived through Steps `00`–`06`: it retains processing graph,
implementation/toolchain, backend, STAR policy, and processing-resource
semantics while excluding the selected downstream module and unrelated global
caps. This permits exact stationary cross-Run reuse across module selections
without changing source evidence.

The `execution-profile` selector validates the combined public authored profile:
its resource projection is Run-bound and its placement projection is
Attempt-local. The registered `resource-config` schema remains an internal and
historical dependency of that profile and of Run-bound resource identity; it is
not a separate public authored configuration. Neither projection is scientific
run intent, and this neutral package does not load YAML, inspect environment
variables, or choose precedence.

The lifecycle family includes an explicit run-lock record, an immutable
workflow attempt that binds its exact canonical workflow-config reference, and
a terminal attempt receipt with mutually consistent executor exit/signal,
blocker, message, and verified-scope facts. Current receipt v2 closes over the
scientific Attempt only; receipt v1 remains exactly readable with its historical
reporting/completion fields. The public
`load_json_object_bytes` parser exists so a caller can parse already admitted
descriptor bytes without reopening a pathname.

Both new and historical Runs retain the exact `emrys.workflow-attempt.v1`
record. Its request-era fields and bound `request.yaml` source snapshot are
unchanged evidence metadata; they do not expose request-v3 as a current public
configuration.

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
The artifact-index roster is derived from the admitted composed profile rather
than fixed Step `09`/`10` tables. Existing flat paired-CMH reporting retains
run-summary v2 and report-receipt v4; explicit modules use run-summary v3 and
report-receipt v5 so computation-provider, reporter-provider, and fixed core
renderer identities remain separately inspectable. Reporter identity never
enters Analysis or Run identity.
