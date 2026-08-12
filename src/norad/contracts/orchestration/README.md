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
