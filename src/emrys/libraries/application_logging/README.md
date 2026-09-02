# Application logging foundation

This neutral package provides resolved log controls, standard-library logging,
protected JSONL persistence, concise stderr projection, and redaction helpers.
It writes no machine stdout. Durable events and console fields are explicit;
secret values are discarded before inspection and large/binary payloads are
rejected.

One attempt owner create-exclusively opens the protected log, pins its path
identity, completes short/interrupted writes, and preserves partial logs.
Logging records lifecycle outcomes but never creates a receipt or changes
computation, publication, rollback, recovery, or exit authority.

Adopters are grouped `run`/`resume` execution (including automatic reporting),
standalone report generation, and confirmed `doctor --repair`. Planning,
refusal, reuse, validation, discovery, diagnosis, inspection, debug routes,
scheduler submission, and delegated tasks open no application log. The exact
two-sink and lifecycle contract remains in
[`LOGGING_CONTRACT.md`](../../../../docs/design/LOGGING_CONTRACT.md).
