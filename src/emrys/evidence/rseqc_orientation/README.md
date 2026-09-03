# `collect_RSeQC_paired_orientation_evidence` owner

Evidence operation `03` runs the admitted RSeQC orientation probe and publishes
its mechanical fraction evidence. The repository producer is
[`step_03_infer_strandedness_and_orientation.sh`](step_03_infer_strandedness_and_orientation.sh);
validation is `emrys validate rseqc-orientation` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact inputs, outputs, transaction, recovery,
validation, and evidence meaning. Fractions do not select transcript strand,
sense/antisense policy, or biological interpretation.
