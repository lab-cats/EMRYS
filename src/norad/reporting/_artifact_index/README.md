# Artifact-index internals

This private package decomposes the artifact-index implementation behind
[`build_artifact_index.py`](../build_artifact_index.py). The public script path
remains the CLI and compatibility facade used by run-summary reporting and the
artifact contract tests.

The modules keep observed responsibilities separate: exact contract loading,
models and rosters, explicit adapter registration, text and binary readers,
inspection, named native/scientific reconciliation, record and receipt
assembly, context construction, receipt-last publication, and
published-transaction validation.
Stage-specific rules remain in their named reconciliation modules; this
package is not a generic stage framework.

[`publication.py`](publication.py) owns the transaction coordinator, rollback,
recovery, and cleanup order. Lock, signal, filesystem, validation, and input
recheck operations remain live bindings on the public facade; the coordinator
calls through that facade so existing fault-injection and caller contracts stay
patchable. These internals do not change artifact schemas, serialized bytes,
source discovery policy, evidence states, or publication order.
