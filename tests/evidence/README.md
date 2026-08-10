# Evidence tests

This directory owns local protection for evidence collection, reconciliation,
availability, inventory, and review-package owners.

- [`canonical_bam_qc/`](canonical_bam_qc/README.md)
  and
  [`rseqc_orientation/`](rseqc_orientation/README.md)
  protect numbered mechanical-evidence operations.
- [`assemble_scientific_review_evidence_package/`](assemble_scientific_review_evidence_package/README.md)
  protects the Step 09c evidence package and recovery boundary.
- [`reference_provenance/`](reference_provenance/README.md),
  [`runtime_preflight/`](runtime_preflight/README.md), and
  [`storage_inventory/`](storage_inventory/README.md) protect cross-cutting
  operational evidence tools.

Commands, transaction behavior, and precise evidence meanings remain with the
[production evidence owners](../../src/norad/evidence/README.md). Tests in one
child do not raise or substitute for another child's evidence state.
