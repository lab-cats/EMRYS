# Storage inventory and qualification tests

These tests cover two [storage-owner](../../../src/emrys/evidence/storage_inventory/README.md)
outputs: optional inventory of declared roots, measurements, and retention policy;
and required compute/finalize qualification whose final receipt Doctor reads.
Both suites check input rejection, deterministic output, publication, rollback,
and CLI failures.

Synthetic filesystem cases neither qualify a production path nor verify its
inventory or retention policy. They authorize no retention action.
