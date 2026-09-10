# Evidence owners

These tools record operational and mechanical observations. They do not perform
scientific analysis or turn observations into biological claims.

- [`canonical_bam_qc/`](canonical_bam_qc/README.md) and
  [`rseqc_orientation/`](rseqc_orientation/README.md) are required Run operations
  `02b` and `03`. Their input files determine when they can run; the historical
  numbers do not impose an execution sequence.
- [`runtime_availability/`](runtime_availability/README.md) and
  [`storage_inventory/`](storage_inventory/README.md) supply readiness evidence
  consumed by Doctor; Slurm requires the stronger two-phase storage receipt.
- [`reference_provenance/`](reference_provenance/README.md) and standalone runtime
  inspection are optional diagnostics.

Runtime and storage diagnostics use `emrys debug`; reference reconciliation uses
`emrys reconcile reference-provenance`. Dry-run may inspect or measure inputs
but does not publish. An owner can supply both a required Run API and an optional
diagnostic: success in one does not imply success in the other. A published file
or zero exit alone does not prove readiness, workflow completion, scientific
review, or biological validity.
