# Runtime-preflight tests

This directory directly protects runtime-profile admission, read-only probes,
deterministic results, publication, rollback, and CLI failure behavior for the
[runtime-preflight owner](../../../src/norad/evidence/runtime_preflight/README.md).

Mocked probe results establish only local contract behavior. They do not prove
that CSU modules ran, dependencies are usable in batch, or the workflow
executes correctly on a cluster or in production.
