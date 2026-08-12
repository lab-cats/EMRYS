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

The lifecycle family includes an explicit run-lock record, an immutable
workflow attempt that binds its exact canonical workflow-config reference, and
a terminal attempt receipt with mutually consistent executor exit/signal,
blocker, message, verified-scope, reporting, and completion facts. The public
`load_json_object_bytes` parser exists so a caller can parse already admitted
descriptor bytes without reopening a pathname.

Owner tasks have a fixed producer-entry ledger beneath
`state/task-starts/<machine-key>/<scope-id>.json`. Each create-exclusive
`task-start` record binds the exact workflow attempt, workflow config, and task
dispatch admitted immediately before producer entry. Task attempts distinguish
pre-entry failures with a null start reference; every post-entry attempt and
verified task binds the published start record.

Reporting producers have a separate fixed ledger beneath
`state/reporting/<kind>/`: `start.json` binds the origin workflow attempt and
configuration before producer entry, while `verified.json` binds that marker
to a semantically revalidated receipt after receipt-last publication. The
three closed kinds are `artifact_index`, `run_summary`, and `html_report`.
