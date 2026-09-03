# `collect_canonical_BAM_QC_evidence` owner

Evidence operation `02b` derives flagstat and canonical-BAM QC artifacts from
the admitted BAM/BAI pair. [`step_02b_bam_qc.sh`](step_02b_bam_qc.sh) is the
producer; validation is `emrys validate canonical-bam-qc` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, outputs, transaction, recovery,
validation, and evidence meaning. Passing QC rows does not establish sample
identity, alignment correctness, scientific review, or biological validity.
