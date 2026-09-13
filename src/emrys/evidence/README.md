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
- [`reference_provenance/`](reference_provenance/README.md) optionally reconciles
  an explicitly declared reference bundle.

Use `emrys runtime discover` and `emrys doctor` for runtime readiness,
`emrys debug storage-qualification` for storage, and
`emrys reconcile reference-provenance` for reference reconciliation. Dry-run
may inspect or measure inputs but does not publish. Optional diagnostics do not
replace required Run checks. A file or zero exit alone does not prove readiness,
workflow completion, scientific review, or biological validity.
