# Reference-provenance tests

This directory directly protects declared-inventory admission, artifact and
contig reconciliation, deterministic outputs, publication, rollback, and CLI
failure behavior for the
[reference-provenance owner](../../../src/norad/evidence/reference_provenance/README.md).
The public command under test is
`python -I -m norad reconcile reference-provenance`; `reconciler.py` remains a
private fault-injection surface.

The suite uses local fixtures. Passing it neither selects or repairs a
reference nor supplies a production reference report or cluster proof.
