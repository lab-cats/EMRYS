# Artifact-index internals

This private package decomposes the artifact-index implementation behind
[`build_artifact_index.py`](../build_artifact_index.py). The public script path
remains the CLI and compatibility facade used by run-summary reporting and the
artifact contract tests.

The modules keep observed responsibilities separate: exact contract loading,
models and rosters, explicit adapter registration, text and binary readers,
inspection, named native/scientific reconciliation, record and receipt
assembly, context construction, and published-transaction validation.
Stage-specific rules remain in their named reconciliation modules; this
package is not a generic stage framework.

Publication, locking, signal handling, rollback, and recovery remain in the
public facade so its existing fault-injection and caller contracts keep the
same patchable bindings. These internals do not change artifact schemas,
serialized bytes, source discovery policy, evidence states, or publication
order.
