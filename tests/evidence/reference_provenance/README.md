# Reference-provenance tests

These local fixtures check declared inventories, artifact and contig agreement,
deterministic output, publication, rollback, and CLI failures for the
[reference-provenance owner](../../../src/emrys/evidence/reference_provenance/README.md).
They call `python -I -m emrys reconcile reference-provenance`; private
`reconciler.py` functions are used only to inject failures. The suite neither
selects nor repairs a reference and produces no production reference report.
