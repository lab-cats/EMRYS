# `generate_partitioned_cohort_mpileup_VCFs` owner

Stage `07` uses admitted sample/partition manifests, orientation BAMs, and the
reference to publish paired mechanical-orientation mpileup VCFs plus a receipt
for each partition. Private [`producer.py`](producer.py) owns execution;
validation is `emrys validate partitioned-cohort-mpileup` through private
[`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns exact selection, inputs, outputs, publication,
recovery, validation, and evidence limits. The producer does not call variants,
and its VCFs are not validated editing sites or biological findings.
