# Canonical-BAM QC tests

Shell cases check the Step 02b producer; Python cases check its reports through
`python -I -m emrys validate canonical-bam-qc`. The private `validator.py` is
not a separate command. The [owner contract](../../../src/emrys/evidence/canonical_bam_qc/CONTRACT.md)
defines publication behavior and the risk of mixing files from different attempts.
These fixtures use mocked tools under the [shared evidence limits](../../README.md#evidence-limits).
