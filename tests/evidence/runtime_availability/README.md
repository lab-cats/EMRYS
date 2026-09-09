# Runtime-availability tests

These tests check runtime profiles, read-only probes, deterministic results,
publication, rollback, and CLI failures for
[runtime availability](../../../src/emrys/evidence/runtime_availability/README.md).
They cover both `emrys debug runtime-availability` and the result Doctor consumes;
the standalone command is diagnostic. Whole-Run scheduler/runtime agreement is
checked by the coordinator's real-synthetic driver.

Injected failures document existing lock-acquisition, incomplete-restoration,
and suppressed lock-cleanup defects; they do not approve those defects. Mocked
probes cannot establish that CSU modules ran or dependencies work in batch.
