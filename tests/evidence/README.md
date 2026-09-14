# Evidence tests

The suites cover three different uses of evidence:

- [BAM QC](canonical_bam_qc/README.md) and [RSeQC](rseqc_orientation/README.md)
  check the required workflow operations `02b` and `03`.
- [Runtime availability](runtime_availability/README.md) and
  [storage qualification](storage_inventory/README.md) check results that Doctor
  requires before execution.
- [Reference provenance](reference_provenance/README.md) and the standalone
  runtime probe check optional operator diagnostics.

One source owner can provide both a required Doctor check and an optional
command. Tests keep those roles separate: passing one does not substitute for
another or prove workflow completion. Commands and exact behavior belong to the
[production evidence owners](../../src/emrys/evidence/README.md); the common
[test evidence limits](../README.md#evidence-limits) apply.
