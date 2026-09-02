# Evidence owners

Evidence owners collect or reconcile operational and mechanical observations;
they do not perform scientific analysis or promote biological claims.

- [`canonical_bam_qc/`](canonical_bam_qc/README.md) and
  [`rseqc_orientation/`](rseqc_orientation/README.md) are required graph
  operations `02b` and `03`.
- [`runtime_availability/`](runtime_availability/README.md) and
  [`storage_inventory/`](storage_inventory/README.md) supply readiness evidence
  consumed by Doctor; Slurm requires the stronger two-phase storage receipt.
- [`reference_provenance/`](reference_provenance/README.md), standalone runtime
  inspection, and storage inventory are optional diagnostics.

Technical routes remain under `emrys debug`; dry-run does not publish. One
physical owner may expose both a required direct API and an optional diagnostic,
but their evidence states are not interchangeable. Publication, path presence,
or command success alone never proves readiness, workflow completion,
scientific review, or biological validity.
