# Evidence tests

This directory owns local protection for three distinct evidence roles:

- **Pipeline evidence owners:** [`canonical_bam_qc/`](canonical_bam_qc/README.md)
  and [`rseqc_orientation/`](rseqc_orientation/README.md) protect required
  graph operations `02b` and `03`.
- **Required readiness:** [`runtime_availability/`](runtime_availability/README.md)
  and the storage-qualification cases under
  [`storage_inventory/`](storage_inventory/README.md) protect direct results
  consumed by doctor.
- **Optional diagnostics:**
  [`reference_provenance/`](reference_provenance/README.md), storage inventory,
  and the manual runtime probe protect operator inspection without becoming
  workflow completion authority.

Commands, transaction behavior, and precise evidence meanings remain with the
[production evidence owners](../../src/emrys/evidence/README.md). Tests in one
source owner may protect both a doctor-consumed API and a separate optional
diagnostic route; those roles remain distinct. Tests in one child do not raise
or substitute for another child's evidence state. Candidate
review, adjudication, and biological interpretation remain external research
work processes rather than test-owned pipeline states.
