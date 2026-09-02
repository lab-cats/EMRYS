# Runtime-availability tests

This directory directly protects runtime-profile admission, read-only probes,
deterministic results, publication, rollback, and CLI failure behavior for the
[runtime-availability owner](../../../src/emrys/evidence/runtime_availability/README.md)
and its grouped route `emrys debug runtime-availability`.
The local-pilot doctor separately consumes the owner's direct admitted
inspection result as required readiness. The standalone inspector remains an
operator diagnostic. Whole-Run scheduler/runtime parity belongs to the
local-pilot real-synthetic driver rather than this owner.
Fault-injection cases retain the known lock-acquisition, incomplete-restoration,
and suppressed lock-cleanup boundaries rather than approving them.

Mocked probe results establish only local contract behavior. They do not prove
that CSU modules ran, dependencies are usable in batch, or the workflow
executes correctly on a cluster or in production.
