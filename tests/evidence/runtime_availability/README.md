# Runtime-availability tests

These tests check runtime profiles and the read-only probes used by
[runtime availability](../../../src/emrys/evidence/runtime_availability/README.md).
They preserve tool and package checks, context handling, bounded execution,
path visibility, and the observations consumed by Doctor and the coordinator.

Whole-Run scheduler/runtime agreement is checked by the coordinator's synthetic
driver. Mocked probes cannot establish that CSU modules ran or dependencies work
in batch. Tests solely for the retired standalone report publisher are removed.
