# Evidence tests

This directory owns local protection for evidence collection, reconciliation,
availability, and inventory owners.

- [`canonical_bam_qc/`](canonical_bam_qc/README.md)
  and
  [`rseqc_orientation/`](rseqc_orientation/README.md)
  protect numbered mechanical-evidence operations.
- [`reference_provenance/`](reference_provenance/README.md),
  [`runtime_availability/`](runtime_availability/README.md), and
  [`storage_inventory/`](storage_inventory/README.md) protect cross-cutting
  operational evidence tools.

Commands, transaction behavior, and precise evidence meanings remain with the
[production evidence owners](../../src/norad/evidence/README.md). Tests in one
child do not raise or substitute for another child's evidence state. Candidate
review, adjudication, and biological interpretation remain external research
work processes rather than test-owned pipeline states.
